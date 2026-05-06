---
name: gendoc-repair
description: 把不完整的目標專案補到與 gendoc-auto + gendoc-flow 從頭執行完全一致的狀態。三部分內容驅動 Gate：① pre-DRYRUN 文件品質（存在 + 章節數 ≥ template）② .gendoc-rules/*.json 存在 ③ post-DRYRUN 輸出存在性 — 三者全 ✅ 才進 Branch B，否則 Branch A 修補後重跑 DRYRUN。State 只作參考，不作 Gate 判斷依據。
version: 5.1.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Skill
  - Agent
---

# gendoc-repair

```
Input:   當前目錄的 .gendoc-state-*.json
Output:  驗證報告 + 自動補跑所有不足的 step
Purpose: 把任何不完整的目標專案補到與 gendoc-auto + gendoc-flow 從頭執行完全一致的狀態
```

---

## Step -1：版本自動更新 + SPAWNED_SESSION 偵測

```bash
[ -n "$OPENCLAW_SESSION" ] && _SPAWNED="true" || _SPAWNED="false"
echo "SPAWNED_SESSION: $_SPAWNED"
[[ "$_SPAWNED" == "true" ]] && echo "[SPAWNED] 跳過互動提問，強制 full-auto 模式"

source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

if [[ -d "$GENDOC_DIR/.git" ]]; then
  bash "$GENDOC_DIR/setup" upgrade 2>/dev/null \
    && echo "[R-00] ✅ gendoc 已是最新版" \
    || echo "[R-00] ⚠️ upgrade 失敗，繼續執行"
else
  echo "[R-00] ⚠️ 找不到 gendoc runtime，跳過版本更新"
fi
```

---

## 呼叫 gendoc-shared

立即用 **Skill tool** 呼叫 `gendoc-shared`。等 Skill tool 回傳後才繼續 Step 0，在此之前不得執行任何後續步驟。

---

## Step 0：讀取 State File + Pipeline

```bash
source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

# State file（在目標專案目錄，gendoc-shared 已確保存在）
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")

# Pipeline（從 GENDOC_TEMPLATES，不讀目標專案目錄）
_PIPELINE_FILE="$GENDOC_TEMPLATES/pipeline.json"
```

```python
import json, os

_state_file = os.environ.get('_STATE_FILE') or \
    next(iter(__import__('glob').glob('.gendoc-state-*.json')), '.gendoc-state.json')
state = json.load(open(_state_file, encoding='utf-8'))

_CLIENT_TYPE     = state.get('client_type', '').strip()
_HAS_ADMIN       = str(state.get('has_admin_backend', '')).strip().lower()
_COMPLETED       = set(state.get('completed_steps', []))

pipeline_file = os.path.expandvars('$GENDOC_TEMPLATES/pipeline.json')
pipeline = json.load(open(pipeline_file, encoding='utf-8'))
steps = pipeline.get('steps', [])

print(f"[Step 0] State: {_state_file}")
print(f"[Step 0] client_type={_CLIENT_TYPE} has_admin={_HAS_ADMIN}")
print(f"[Step 0] completed_steps: {len(_COMPLETED)} 個")
print(f"[Step 0] Pipeline: {len(steps)} steps")
```

---

## Step 1：前置驗證

```bash
# BRD.md 必須存在（沒有 BRD 則無法繼續）
if [[ ! -f "docs/BRD.md" ]] || [[ ! -s "docs/BRD.md" ]]; then
  echo "[ABORT] docs/BRD.md 不存在或為空，無法執行 repair。"
  echo "[Hint]  請先執行 /gendoc-auto 或手動提供 BRD.md"
  exit 1
fi
echo "[R-01] ✅ docs/BRD.md 存在且非空"
```

---

## Step 2：三部分內容驅動 Gate 判斷

> **設計原則**：Gate 完全以文件內容為依據，state（completed_steps）只作參考輸出，不影響 Gate 結果。
> 三個條件缺一不可：① pre-DRYRUN 品質 ② rules 完整性 ③ post-DRYRUN 存在性。

```python
import re, glob as _glob, json, os

# ── Helper Functions（在 Gate 定義，Branch A/B 共用）──────────────────────

def _eval_condition(cond, client_type, has_admin):
    """回傳 True 表示此 step 在當前 client_type/has_admin 下應執行"""
    if not cond or cond == 'always':
        return True
    ct  = client_type.strip().lower()
    adm = has_admin.strip().lower() in ('true', '1', 'yes')
    if cond == 'client_type != none':        return ct not in ('', 'api-only')
    if cond == 'client_type != api-only':    return ct != 'api-only'
    if cond == 'client_type == api-only':    return ct == 'api-only'
    if cond == 'client_type == game':        return ct in ('unity', 'cocos', 'game')
    if cond == 'has_admin_backend':          return adm
    return True

def _output_complete(step, tmpl_dir=''):
    """回傳 (exists: bool, complete: bool, reason: str)
    - (False, False, reason) : 主要輸出不存在或目錄為空
    - (True,  False, reason) : 存在但 ## 章節數 < template 要求
    - (True,  True,  '')     : 存在且完整
    """
    outputs     = step.get('output', [])
    output_glob = step.get('output_glob', '')

    if output_glob:
        for pattern in output_glob.split('|'):
            if not _glob.glob(pattern.strip()):
                return False, False, f'output_glob 無匹配：{pattern.strip()}'
        return True, True, ''

    if not outputs:
        return False, False, '無輸出定義'

    for path in outputs:
        if path.endswith('/'):
            if not os.path.isdir(path.rstrip('/')) or not os.listdir(path.rstrip('/')):
                return False, False, f'目錄缺失或空：{path}'
        else:
            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                return False, False, f'檔案缺失或空：{path}'

    # Section completeness check（比對 ## 章節數 vs template）
    if tmpl_dir:
        sid       = step['id']
        tmpl_file = os.path.join(tmpl_dir, f'{sid}.md')
        for path in outputs:
            if path.endswith('.md') and os.path.isfile(path) and os.path.isfile(tmpl_file):
                exp = len(re.findall(r'^## ', open(tmpl_file, encoding='utf-8').read(), re.MULTILINE))
                act = len(re.findall(r'^## ', open(path,      encoding='utf-8').read(), re.MULTILINE))
                if exp > 0 and act < exp:
                    return True, False, f'章節不完整：{act}/{exp} 個 ## 章節（{path}）'
                break
    return True, True, ''

def _output_exists(step):
    """只回傳存在性布林（供 B-1 使用）"""
    exists, _, _ = _output_complete(step)
    return exists

# ── 找出 DRYRUN 分界 ──────────────────────────────────────────────────────

_dryrun_idx = next((i for i, s in enumerate(steps) if s['id'] == 'DRYRUN'), None)
if _dryrun_idx is None:
    print("[ABORT] pipeline.json 中找不到 DRYRUN step")
    raise SystemExit(1)

_pre_dryrun_steps  = steps[:_dryrun_idx]
_post_dryrun_steps = steps[_dryrun_idx + 1:]
_tmpl_dir          = os.environ.get('GENDOC_TEMPLATES', '')

# ── Gate ①：pre-DRYRUN 文件品質掃描 ─────────────────────────────────────
# 每個適用的 pre-DRYRUN step：文件必須存在 且 ## 章節數 ≥ template 要求
# 完全不看 completed_steps；文件內容是唯一真相。

print("\n[Gate-①] 掃描 pre-DRYRUN 文件品質...")
_pre_ok    = True
_pre_fails = []   # [(sid, reason), ...]

for step in _pre_dryrun_steps:
    sid  = step['id']
    cond = step.get('condition', 'always')
    if not _eval_condition(cond, _CLIENT_TYPE, _HAS_ADMIN):
        print(f"[Gate-①] ⏭️  {sid} — 條件不符，略過")
        continue
    exists, complete, reason = _output_complete(step, tmpl_dir=_tmpl_dir)
    if exists and complete:
        print(f"[Gate-①] ✅ {sid}")
    else:
        label = "缺失" if not exists else "章節不完整"
        print(f"[Gate-①] ❌ {sid} — {label}（{reason}）")
        _pre_ok = False
        _pre_fails.append((sid, reason))

# ── Gate ②：.gendoc-rules/*.json 完整性 ──────────────────────────────────
# DRYRUN 正常完成的標誌：rules 目錄必須存在且有至少一個 json 檔。
# 注意：即使 DRYRUN 在 completed_steps，rules 缺失代表 DRYRUN 未正確完成。

_rules_files = _glob.glob('.gendoc-rules/*.json')
_rules_ok    = len(_rules_files) > 0
print(f"\n[Gate-②] .gendoc-rules/*.json：{'✅ ' + str(len(_rules_files)) + ' 個' if _rules_ok else '❌ 不存在（DRYRUN 未正確完成）'}")

# ── Gate ③：post-DRYRUN 輸出存在性 ───────────────────────────────────────
# 只檢查輸出是否存在（不做品質驗證，Branch B 負責）。
# 任何一個適用的 post-DRYRUN step 輸出缺失 → Gate③ FAIL。

print("\n[Gate-③] 掃描 post-DRYRUN 輸出存在性...")
_post_ok    = True
_post_fails = []   # [(sid, reason), ...]

for step in _post_dryrun_steps:
    sid  = step['id']
    cond = step.get('condition', 'always')
    if not _eval_condition(cond, _CLIENT_TYPE, _HAS_ADMIN):
        print(f"[Gate-③] ⏭️  {sid} — 條件不符，略過")
        continue
    exists, _, reason = _output_complete(step)   # 不帶 tmpl_dir → 只看存在性
    if exists:
        print(f"[Gate-③] ✅ {sid}")
    else:
        print(f"[Gate-③] ❌ {sid} — {reason}")
        _post_ok = False
        _post_fails.append((sid, reason))

# ── Gate 最終判斷 ─────────────────────────────────────────────────────────

_GATE = _pre_ok and _rules_ok and _post_ok

print(f"\n[Gate] ① pre-DRYRUN 品質={'✅' if _pre_ok else '❌'} "
      f"② rules={'✅' if _rules_ok else '❌'} "
      f"③ post-DRYRUN 存在={'✅' if _post_ok else '❌'}")

if _GATE:
    print(f"[Gate] ✅ BRANCH B — 三項全部通過，DRYRUN 不需重跑")
else:
    fail_reasons = []
    if not _pre_ok:    fail_reasons.append(f"pre-DRYRUN {len(_pre_fails)} 個文件不合格")
    if not _rules_ok:  fail_reasons.append(".gendoc-rules/ 缺失")
    if not _post_ok:   fail_reasons.append(f"post-DRYRUN {len(_post_fails)} 個輸出缺失")
    print(f"[Gate] ⚙️  BRANCH A — {' / '.join(fail_reasons)}")
    print(f"       （state 參考：completed_steps 有 {len(_COMPLETED)} 個，僅供日誌，不影響 Gate）")
```

---

## Branch A：補齊 DRYRUN 上游 + 執行 DRYRUN

> **進入條件**：Gate = False（Gate ①②③ 任一不通過）
> **關鍵原則**：Gate 已完成掃描，Branch A 直接使用結果，不重複掃描。

### A-1：確認需補跑的 pre-DRYRUN step 清單

```python
# Gate-① 掃描結果直接使用，無需重新掃描
_a_missing = [sid for sid, _ in _pre_fails]
print(f"\n[A-1] 需補跑 {len(_a_missing)} 個 pre-DRYRUN step：{_a_missing}")
for sid, reason in _pre_fails:
    print(f"      ❌ {sid}：{reason}")
```

### A-2：補跑缺失的 DRYRUN 前 Step

```python
_any_pre_rebuilt = False  # 記錄是否有 pre-DRYRUN step 被重建
```

對 `_a_missing` 中的每個 `step_id`，依序執行：

```
用 Skill tool 呼叫 gendoc-flow，args="--only {step_id}"
等待回傳後繼續下一個 step。
Skill 呼叫成功（step 重建完成）→ _any_pre_rebuilt = True
Skill 呼叫失敗 → 記錄失敗原因，繼續下一個（不中止）。
```

### A-3：執行 DRYRUN

```python
# ── 強制無效化：若 A-2 有任何 pre-DRYRUN step 被重建 ──────────────────────
# 上游文件被重建 → DRYRUN 量化基線過時 → 刪除所有 rules + 重置 DRYRUN state。
# 不論 rules 是否存在，一律強制重跑 DRYRUN，確保下游 step 的品質閘門基於最新文件。
if _any_pre_rebuilt:
    import glob as _g2
    _stale_rules = _g2.glob('.gendoc-rules/*.json')
    for _rf in _stale_rules:
        os.remove(_rf)
    print(f"[A-3] ♻️  pre-DRYRUN step 已重建：刪除 {len(_stale_rules)} 個 stale rules")

    # State file：移除 DRYRUN，讓 state 與未做 DRYRUN 一致
    _sf_list = _g2.glob('.gendoc-state-*.json')
    if _sf_list:
        _sd = json.load(open(_sf_list[0], encoding='utf-8'))
        _cs = _sd.get('completed_steps', [])
        if 'DRYRUN' in _cs:
            _cs.remove('DRYRUN')
            _sd['completed_steps'] = _cs
            import datetime as _dt
            _sd['last_updated'] = _dt.datetime.now(
                _dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            _tmp = _sf_list[0] + '.tmp'
            with open(_tmp, 'w', encoding='utf-8') as _fp:
                json.dump(_sd, _fp, indent=2, ensure_ascii=False)
            os.replace(_tmp, _sf_list[0])
            print(f"[A-3] ♻️  state file：DRYRUN 已從 completed_steps 移除（state 等同未執行）")

    _rules_ok = False  # 強制後續判斷為 must-run

# ── DRYRUN 執行判斷：內容驅動，不看 state ─────────────────────────────────
# 需要重跑的條件（任一成立即跑）：
#   ① Gate-① 有 pre-DRYRUN step 失敗（_pre_fails 非空）
#   ② Gate-② .gendoc-rules/ 缺失（_rules_ok = False）
#   ③ A-2 重建了任何 pre-DRYRUN step（_any_pre_rebuilt = True → 已強制 _rules_ok = False）
# 注意：即使 DRYRUN 在 completed_steps，只要 rules 缺失就必須重跑。
_should_run_dryrun = bool(_pre_fails) or not _rules_ok
```

若 `_should_run_dryrun = True`，執行：

```
用 Skill tool 呼叫 gendoc-gen-dryrun
等待回傳。
```

若 `_should_run_dryrun = False`（pre-DRYRUN 全部合格 且 .gendoc-rules/ 已存在），跳過 DRYRUN，直接進入 A-4。

DRYRUN 執行後，驗證 `.gendoc-rules/*.json` 是否生成：

```python
import glob as _glob
_rules_after = _glob.glob('.gendoc-rules/*.json')
if not _rules_after:
    print("[ABORT] DRYRUN 執行後仍找不到 .gendoc-rules/*.json，無法繼續 Branch B")
    raise SystemExit(1)
print(f"[A-3] ✅ DRYRUN 完成，生成 {len(_rules_after)} 個 rules 檔案")
```

### A-4：銜接 Branch B

DRYRUN 成功後，繼續執行 **Branch B**（DRYRUN 後的所有 step 驗證 + 補跑）。

---

## Branch B：驗證 DRYRUN 後的所有 Step + 補跑（最多 3 輪）

> **進入條件**：Gate = True（三項全部通過）或 Branch A 已完成 DRYRUN（A-4 銜接）

### B-0：初始化

```python
import json, os, glob as _glob

# 重讀 .gendoc-rules/ 目錄（Branch A 可能剛跑完 DRYRUN，需重讀最新結果）
_rules_dir = '.gendoc-rules'
_rules_map = {}  # {step_id: dict}
for f in _glob.glob(f'{_rules_dir}/*.json'):
    sid = os.path.basename(f).replace('-rules.json', '').upper()
    try:
        _rules_map[sid] = json.load(open(f, encoding='utf-8'))
    except Exception:
        _rules_map[sid] = {}

# per-step 重試狀態（取代全局 _MAX_ROUNDS）
_MAX_PER_STEP    = 3                 # 每個 step 最多失敗幾次
_fail_count      = {}                # {step_id: int}  累計失敗次數
_permanently_failed = []             # [(sid, layer, details)]  已放棄
_done            = []                # [sid]  已通過

# pending：condition 成立的 post-DRYRUN steps（依 pipeline.json 順序）
_pending = [
    s for s in _post_dryrun_steps
    if _eval_condition(s.get('condition', 'always'), _CLIENT_TYPE, _HAS_ADMIN)
]
print(f"[Branch B] 待處理 {len(_pending)} 個 steps：{[s['id'] for s in _pending]}")
```

### B-1：三層 FAIL 偵測函式

```python
import glob as _glob_b1, os as _os_b1
from datetime import datetime as _dt

def _get_mtime(path_pattern: str):
    """回傳符合 pattern 的所有檔案中最大 mtime；無檔案時回傳 None。"""
    matched = _glob.glob(path_pattern, recursive=True)
    if not matched:
        return None
    vals = [os.path.getmtime(p) for p in matched if os.path.isfile(p)]
    return max(vals) if vals else None

def _get_oldest_output_mtime(output_spec):
    """回傳輸出集的最小 mtime（最舊輸出檔）；無輸出時回傳 None。"""
    if isinstance(output_spec, str):
        output_spec = [output_spec]
    mtimes = []
    for pattern in output_spec:
        for p in _glob.glob(pattern, recursive=True):
            if os.path.isfile(p):
                mtimes.append(os.path.getmtime(p))
    return min(mtimes) if mtimes else None

def _check_step_l1_mtime(step) -> tuple:
    """Layer 1（special_skill only）：mtime Stale 檢查（Makefile 語意）

    回傳 (is_stale: bool, reason: str)。
    is_stale=True  → 短路補跑，不檢查 L2/L3
    is_stale=False → 繼續 L2/L3
    輸出不存在     → is_stale=True（觸發補跑，L2 不需重複判斷）
    """
    trigger_files = step.get('input', [])
    if not trigger_files:
        trigger_files = _glob.glob('docs/*.md')

    newest_input = None
    for pattern in trigger_files:
        m = _get_mtime(pattern)
        if m is not None:
            newest_input = max(newest_input or 0, m)

    if newest_input is None:
        return False, "觸發集無檔案，略過 L1"

    output_spec = step.get('output', [])
    oldest_output = _get_oldest_output_mtime(output_spec)

    if oldest_output is None:
        return True, "輸出不存在（STALE）"

    if newest_input > oldest_output:
        in_dt  = _dt.fromtimestamp(newest_input).strftime('%H:%M:%S')
        out_dt = _dt.fromtimestamp(oldest_output).strftime('%H:%M:%S')
        return True, f"輸入較新（input={in_dt} > output={out_dt}）"

    return False, "FRESH"


def _check_step_l2(step):
    """Layer 2（原 L1）：輸出檔案/目錄是否存在且完整（章節數 >= template）

    [R3-C] special_skill step：優先讀取 special_completed state（比 file-existence 更可靠）
    HTML step：額外比對 docs/*.md 數量 vs docs/pages/*.html 數量
    PROTOTYPE step：必須確認 docs/pages/prototype/index.html 存在
    """
    sid = step.get('id', '')
    special_sk = step.get('special_skill', '')

    # special_skill step：優先使用 special_completed 判斷（不依賴 completed_steps）
    if special_sk:
        # 讀取 state file 中的 special_completed
        _state_files = _glob.glob('.gendoc-state-*.json') or ['.gendoc-state.json']
        try:
            _state = json.load(open(_state_files[0], encoding='utf-8'))
            if _state.get('special_completed', {}).get(sid, False):
                # special_completed=True 但仍需確認輸出物實際存在
                pass  # 繼續做文件存在性確認
        except Exception:
            pass

    # HTML step：動態計數比對（不依賴 _output_complete 的目錄存在性）
    if sid == 'HTML' or 'gendoc-gen-html' in special_sk:
        expected_html = len(_glob.glob('docs/*.md'))
        actual_html = len([f for f in _glob.glob('docs/pages/*.html')
                           if os.path.basename(f) != 'index.html'])
        index_ok = os.path.isfile('docs/pages/index.html')
        if not index_ok or actual_html < expected_html:
            return False  # MD/HTML 數量不符 → 需補跑
        return True

    # PROTOTYPE step：必須確認 prototype/index.html 存在
    if sid == 'PROTOTYPE' or 'gendoc-gen-prototype' in special_sk:
        return os.path.isfile('docs/pages/prototype/index.html')

    exists, complete, _ = _output_complete(step)  # 復用 A-1 定義的函式（含 section check）
    return exists and complete

def _check_step_l3(step):
    """Layer 3（原 L2）：rules.json 量化品質門檻是否達標

    讀取 .gendoc-rules/{step_id.lower()}-rules.json 的 min_* 閾值，
    與實際輸出檔的內容比對。回傳 (passed: bool, details: list[str])
    rules.json 不存在 → PASS（不阻擋）
    """
    sid = step['id']
    rules_file = f'{_rules_dir}/{sid.lower()}-rules.json'

    if not os.path.isfile(rules_file):
        # 此 step 無 rules.json → 只看 L1
        return True, []

    try:
        rules = json.load(open(rules_file, encoding='utf-8'))
    except Exception:
        return True, []  # 無法讀取 → 不阻擋

    if not rules:
        return True, []

    # 讀取主輸出檔內容（單一 .md 檔）
    outputs = step.get('output', [])
    doc_text = ''
    for path in outputs:
        if path.endswith('.md') and os.path.isfile(path):
            doc_text = open(path, encoding='utf-8', errors='ignore').read()
            break

    if not doc_text:
        # 目錄型輸出（special_skill step）→ 呼叫專屬計量函式
        sk = step.get('special_skill', '')
        if os.path.isfile(rules_file):
            return _check_directory_step(step, rules, sk)
        return True, []

    failed_checks = []
    for key, threshold in rules.items():
        if not isinstance(threshold, int) or threshold <= 0:
            continue
        # 基於 key 名稱選擇計數方法
        actual = _count_metric(doc_text, key)
        if actual < threshold:
            failed_checks.append(
                f"{key}: 需要 ≥{threshold}，實際 ={actual}"
            )

    return (len(failed_checks) == 0), failed_checks


def _count_metric(text: str, key: str) -> int:
    """根據 metric key 名稱從文件中計算實際數量。

    常見 key 模式（來自 pipeline.json spec_rules）：
    - min_*_sections / min_*_count → 計算對應的 ## 標題數
    - min_api_endpoints / min_endpoint_count → 計算 HTTP method 出現次數
    - min_ac_count / min_acceptance_criteria → 計算 AC 條目
    - min_entity_count → 計算 Entity/Table 定義數
    - min_test_case_count → 計算測試案例數
    """
    import re
    text_lower = text.lower()
    k = key.lower()

    # HTTP endpoint 相關
    if 'endpoint' in k or 'api_count' in k:
        return len(re.findall(r'\b(GET|POST|PUT|PATCH|DELETE)\b', text))

    # Section / heading 相關
    if 'section' in k or 'chapter' in k:
        return len(re.findall(r'^#{1,3} .+', text, re.MULTILINE))

    # Acceptance criteria
    if 'ac_count' in k or 'acceptance' in k:
        return len(re.findall(r'^\s*[-*]\s*(AC|Given|When|Then|接受|驗收)', text, re.MULTILINE | re.IGNORECASE))

    # Table count — 計算 SCHEMA.md 中的獨立 table 塊數（每張 table 恰好一條 separator row）
    # 對應 DRYRUN 語義：min_table_count = max(3, entity_count)
    if 'table_count' in k:
        return len(re.findall(r'^\|[\s\-:|]+\|', text, re.MULTILINE))

    # Entity / Schema heading count
    if 'entity' in k or 'schema' in k:
        return len(re.findall(r'^#{1,3} .*(Entity|Table|Schema|資料表)', text, re.MULTILINE | re.IGNORECASE))

    # Test case
    if 'test_case' in k or 'test_count' in k:
        return len(re.findall(r'^\s*[-*|]\s*(TC|Test Case|測試案例)', text, re.MULTILINE | re.IGNORECASE))

    # Use case / User story
    if 'use_case' in k or 'user_story' in k or 'story_count' in k:
        return len(re.findall(r'^\s*(As a|As an|身為|身份)', text, re.MULTILINE | re.IGNORECASE))

    # 其他 count → 計算文件中的 ## heading 數（保守估計）
    if 'count' in k or 'num_' in k or 'min_' in k:
        return len(re.findall(r'^## .+', text, re.MULTILINE))

    return 0


def _check_directory_step(step, rules, special_skill):
    """驗證目錄型 step（special_skill）是否符合 rules.json 的精確期望值。
    驗證語義：actual >= expected（精確值是計算基準，多可少不行）。
    回傳 (passed: bool, details: list[str])
    """
    failed = []
    sk = special_skill.lower() if special_skill else ''

    if 'gendoc-gen-html' in sk or step.get('id', '') == 'HTML':
        # HTML：計算 docs/*.md 數 vs docs/pages/*.html 數（排除 index.html）
        expected = rules.get('expected_html_files', 0)
        actual = len([f for f in _glob.glob('docs/pages/*.html')
                      if os.path.basename(f) != 'index.html'])
        if isinstance(expected, int) and expected > 0 and actual < expected:
            failed.append(f"expected_html_files: 需 ≥{expected}，實際 ={actual}")

    elif 'gendoc-gen-contracts' in sk or step.get('id', '') == 'CONTRACTS':
        # CONTRACTS：openapi.yaml paths 數 + schemas/*.json 數
        ec = rules.get('expected_contract_count', 0)
        es = rules.get('expected_schema_count', 0)
        # 計算 openapi.yaml 中的 paths entry 數
        oapi_files = _glob.glob('docs/blueprint/contracts/openapi.yaml') + \
                     _glob.glob('docs/blueprint/contracts/*.yaml')
        actual_paths = 0
        for f in oapi_files:
            content = open(f, encoding='utf-8', errors='ignore').read()
            actual_paths += len([l for l in content.split('\n')
                                 if l.strip() and l.startswith('  /') and ':' in l])
        actual_schemas = len(_glob.glob('docs/blueprint/contracts/schemas/*.json'))
        if isinstance(ec, int) and ec > 0 and actual_paths < ec:
            failed.append(f"expected_contract_count: 需 ≥{ec}，實際 ={actual_paths}")
        if isinstance(es, int) and es > 0 and actual_schemas < es:
            failed.append(f"expected_schema_count: 需 ≥{es}，實際 ={actual_schemas}")

    elif 'gendoc-gen-mock' in sk or step.get('id', '') == 'MOCK':
        # MOCK：main.py @app. decorator 數 + data/*.json 數
        er = rules.get('expected_mock_route_count', 0)
        ed = rules.get('expected_mock_data_count', 0)
        mock_main = 'docs/blueprint/mock/main.py'
        actual_routes = 0
        if os.path.isfile(mock_main):
            content = open(mock_main, encoding='utf-8', errors='ignore').read()
            actual_routes = len([l for l in content.split('\n') if '@app.' in l])
        actual_data = len(_glob.glob('docs/blueprint/mock/data/*.json'))
        if isinstance(er, int) and er > 0 and actual_routes < er:
            failed.append(f"expected_mock_route_count: 需 ≥{er}，實際 ={actual_routes}")
        if isinstance(ed, int) and ed > 0 and actual_data < ed:
            failed.append(f"expected_mock_data_count: 需 ≥{ed}，實際 ={actual_data}")

    elif 'gendoc-gen-prototype' in sk or step.get('id', '') == 'PROTOTYPE':
        # PROTOTYPE：index.html + prototype.css + prototype.js 必須存在
        ep = rules.get('expected_screen_count', 0)
        required_files = ['docs/pages/prototype/index.html',
                          'docs/pages/prototype/prototype.css',
                          'docs/pages/prototype/prototype.js']
        missing = [f for f in required_files if not os.path.isfile(f)]
        if missing:
            failed.append(f"prototype 必要檔案缺失：{missing}")
        if isinstance(ep, int) and ep > 0:
            # 計算 docs/pages/prototype/ 下 HTML 頁面數（route 數）
            actual_screens = len(_glob.glob('docs/pages/prototype/**/*.html', recursive=True))
            if actual_screens < ep:
                failed.append(f"expected_screen_count: 需 ≥{ep}，實際 ={actual_screens}")

    elif 'gendoc-gen-diagrams' in sk or step.get('id', '') == 'UML':
        # UML：雙層驗證（type coverage + variable-count）
        # Layer A：mandatory 單檔 + class 組
        mandatory = [
            'docs/diagrams/use-case.md',
            'docs/diagrams/object-snapshot.md',
            'docs/diagrams/communication.md',
            'docs/diagrams/component.md',
            'docs/diagrams/deployment.md',
            'docs/diagrams/er-diagram.md',
            'docs/diagrams/class-domain.md',
            'docs/diagrams/class-application.md',
            'docs/diagrams/class-infra-presentation.md',
        ]
        missing_mandatory = [f for f in mandatory if not os.path.isfile(f)]
        if missing_mandatory:
            failed.append(f"UML mandatory 圖缺失（{len(missing_mandatory)} 個）：{missing_mandatory}")
        # Layer B：variable-count types
        seq_exp = rules.get('expected_sequence_count', 0)
        act_exp = rules.get('expected_activity_count', 0)
        st_exp  = rules.get('expected_state_count', 0)
        cls_exp = rules.get('expected_class_files', 3)
        seq_act = len(_glob.glob('docs/diagrams/sequence-*.md'))
        act_act = len(_glob.glob('docs/diagrams/activity-*.md'))
        st_act  = len(_glob.glob('docs/diagrams/state-machine-*.md'))
        cls_act = len(_glob.glob('docs/diagrams/class-*.md'))
        if isinstance(seq_exp, int) and seq_exp > 0 and seq_act < seq_exp:
            failed.append(f"expected_sequence_count: 需 ≥{seq_exp}，實際 ={seq_act}")
        if isinstance(act_exp, int) and act_exp > 0 and act_act < act_exp:
            failed.append(f"expected_activity_count: 需 ≥{act_exp}，實際 ={act_act}")
        if isinstance(st_exp, int) and st_exp > 0 and st_act < st_exp:
            failed.append(f"expected_state_count: 需 ≥{st_exp}，實際 ={st_act}")
        if isinstance(cls_exp, int) and cls_exp > 0 and cls_act < cls_exp:
            failed.append(f"expected_class_files: 需 ≥{cls_exp}，實際 ={cls_act}")

    return (len(failed) == 0), failed
```

### B-2：執行驗證 + 補跑迴圈（per-step 獨立重試）

> ⚠️ **強制繼續規則（Claude 執行時必須嚴格遵守，違反即為錯誤）：**
> 1. 一個 step 失敗後**立即補跑**，補跑完後**繼續本輪下一個 step**，不得停止
> 2. 一個 step 達到 `_MAX_PER_STEP` 次失敗後移入 `_permanently_failed`，不再補跑、不再驗證
> 3. 即使某個 step（如 PROTOTYPE、HTML）執行時間很長，完成後仍必須繼續
> 4. Branch B 全部 step 的 `_pending` 清空前，任何「修復完成」「任務完成」的輸出都是錯誤的
> 5. 每補跑完一個 step，必須立即印出 `[B-2] 繼續下一個 step...` 再執行下一個

```python
_round = 0
while _pending:
    _round += 1

    # 安全閥：防止演算法異常無限循環（R-5）
    if _round > _MAX_PER_STEP:
        print(f"[Branch B] ⚠️  已達安全閥上限（{_MAX_PER_STEP} 輪），強制終止剩餘 {len(_pending)} 個 step")
        for step in _pending:
            _permanently_failed.append((step['id'], 'SAFETY', ['超過安全閥輪次上限']))
        break

    print(f"\n{'='*60}")
    print(f"[Branch B] Round {_round} — 驗證 {len(_pending)} 個 pending steps")
    print(f"{'='*60}")

    _next_pending = []

    for step in _pending:
        sid = step['id']

        # L1：mtime Stale 檢查（僅 special_skill 步驟）
        if step.get('special_skill'):
            l1_stale, l1_reason = _check_step_l1_mtime(step)
            if l1_stale:
                print(f"[B-2] ❌ {sid} — L1 STALE：{l1_reason}")
                _fail_count[sid] = _fail_count.get(sid, 0) + 1
                if _fail_count[sid] < _MAX_PER_STEP:
                    print(f"[B-2] ▶ 補跑 {sid}（第 {_fail_count[sid]} 次失敗）→ Skill('gendoc-flow', args='--only {sid}')")
                    # 用 Skill tool 呼叫 gendoc-flow，args="--only {sid}"；失敗時印 [WARN] 繼續
                    _next_pending.append(step)
                else:
                    print(f"[B-2] ☠️  {sid} — 達到上限（{_MAX_PER_STEP} 次），永久放棄")
                    _permanently_failed.append((sid, 'L1', [l1_reason]))
                print(f"[B-2] 繼續下一個 step...")
                continue
            print(f"[B-2]    {sid} — L1 FRESH：{l1_reason}")

        # L2：輸出存在性檢查
        if not _check_step_l2(step):
            print(f"[B-2] ❌ {sid} — L2 FAIL：輸出缺失或空白")
            _fail_count[sid] = _fail_count.get(sid, 0) + 1
            if _fail_count[sid] < _MAX_PER_STEP:
                print(f"[B-2] ▶ 補跑 {sid}（第 {_fail_count[sid]} 次失敗）→ Skill('gendoc-flow', args='--only {sid}')")
                # 用 Skill tool 呼叫 gendoc-flow，args="--only {sid}"；失敗時印 [WARN] 繼續
                _next_pending.append(step)
            else:
                print(f"[B-2] ☠️  {sid} — 達到上限（{_MAX_PER_STEP} 次），永久放棄")
                _permanently_failed.append((sid, 'L2', ['輸出檔案缺失或空白']))
            print(f"[B-2] 繼續下一個 step...")
            continue

        # L3：rules.json 量化品質門檻
        l3_ok, l3_details = _check_step_l3(step)
        if not l3_ok:
            print(f"[B-2] ❌ {sid} — L3 FAIL：")
            for d in l3_details:
                print(f"          {d}")
            _fail_count[sid] = _fail_count.get(sid, 0) + 1
            if _fail_count[sid] < _MAX_PER_STEP:
                print(f"[B-2] ▶ 補跑 {sid}（第 {_fail_count[sid]} 次失敗）→ Skill('gendoc-flow', args='--only {sid}')")
                # 用 Skill tool 呼叫 gendoc-flow，args="--only {sid}"；失敗時印 [WARN] 繼續
                _next_pending.append(step)
            else:
                print(f"[B-2] ☠️  {sid} — 達到上限（{_MAX_PER_STEP} 次），永久放棄")
                _permanently_failed.append((sid, 'L3', l3_details))
            print(f"[B-2] 繼續下一個 step...")
            continue

        # 通過 L1+L2+L3
        print(f"[B-2] ✅ {sid} — L1+L2+L3 通過")
        _done.append(sid)

    _pending = _next_pending

if not _pending:
    print(f"\n[Branch B] ✅ 所有 pending steps 已結算（{len(_done)} 通過，{len(_permanently_failed)} 永久失敗）")
```

### B-3：最終驗證 + 報告

```python
# 判斷是否有任一輪全部通過（break 路徑）
_all_passed_early = any(v == [] for v in _round_failures.values())

if _all_passed_early:
    last_fails = []
else:
    # 3 輪都有 FAIL，且第 3 輪已補跑 → 再做最終掃描（只驗，不補跑）
    _final_fail = []
    for step in _post_dryrun:
        sid  = step['id']
        cond = step.get('condition', 'always')
        if not _eval_condition(cond, _CLIENT_TYPE, _HAS_ADMIN):
            continue
        l1_stale = False
        if step.get('special_skill'):
            l1_stale, _ = _check_step_l1_mtime(step)
        l2_ok = _check_step_l2(step) if not l1_stale else False
        l3_ok, _ = _check_step_l3(step) if l2_ok else (False, [])
        if l1_stale or not l2_ok or not l3_ok:
            _final_fail.append(sid)
    last_fails = _final_fail
```

```python
print("\n" + "="*60)
print("[gendoc-repair] 最終報告")
print("="*60)

if not last_fails:
    print("✅ 所有 step 通過 L1+L2+L3 驗證，專案已完整。")
else:
    print(f"⚠️  達到最大重試輪次（{_MAX_ROUNDS}），以下 step 仍未通過：")
    for sid in last_fails:
        print(f"   ❌ {sid}")
    print()
    print("[Hint] 手動排查方式：")
    for sid in last_fails:
        print(f"   /gendoc-flow --only {sid}")
    print()
    print("可能原因：")
    print("  1. 上游文件品質不足，導致該 step 無法生成合格內容")
    print("  2. client_type / has_admin_backend 設定與實際需求不符")
    print("  3. 需要人工檢視並補充上游文件（BRD、PRD、EDD、ARCH）")
```

---

## 工具使用規則

| 情境 | 工具 |
|------|------|
| 補跑單一 step | `Skill("gendoc-flow", args="--only {step_id}")` |
| 執行 DRYRUN | `Skill("gendoc-gen-dryrun")` |
| 初始化 state file | 由 gendoc-shared 負責（Step -1 後呼叫） |
| 讀取 pipeline.json | `$GENDOC_TEMPLATES/pipeline.json`（不讀 `$_CWD/templates/`） |
| 讀取 state file | `.gendoc-state-*.json`（當前目錄） |

---

## 設計原則（禁止事項）

1. **不詢問使用者**是否要執行 repair — 使用者觸發即代表確認
2. **不依賴 completed_steps** 判斷 Branch B 的哪些 step 需要重做（避免舊格式 state 相容性問題）
3. **不重新實作** gendoc-flow、gendoc-gen-dryrun 的邏輯 — 只呼叫它們
4. **不讀** `$_CWD/templates/` — pipeline 只從 `$GENDOC_TEMPLATES` 讀取
5. **不直接修改** `~/.claude/skills/` — 只修改 `~/projects/gendoc/skills/`
6. **單 step 失敗不中止** — 記錄失敗，繼續下一個 step
7. **L1 mtime 不詢問使用者** — mtime 比對是機械判斷，STALE 立即短路補跑，無需確認
8. **L1 觸發集從 pipeline.json 讀取** — `input[]` 為空時隱式展開為 `docs/*.md`，零硬編碼
9. **沒有獨立 Phase C** — mtime 檢查已整合為 Branch B L1，AI 無法跳過
10. **最多 3 輪重試** — 超過後報告失敗原因，不無限迴圈
