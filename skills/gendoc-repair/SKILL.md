---
name: gendoc-repair
description: 把不完整的目標專案補到與 gendoc-auto + gendoc-flow 從頭執行完全一致的狀態。二元 Gate：.gendoc-rules/*.json 存在且 DRYRUN 在 completed_steps → Branch B 驗證補跑；否則 → Branch A 補齊上游再跑 DRYRUN 後銜接 Branch B。
version: 4.0.0
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

## Step 2：二元 Gate 判斷

```python
import glob as _glob, json, os

# Gate 條件：.gendoc-rules/*.json 存在 且 DRYRUN 已在 completed_steps
_rules_files = _glob.glob('.gendoc-rules/*.json')
_dryrun_done = 'DRYRUN' in _COMPLETED

_GATE = len(_rules_files) > 0 and _dryrun_done

if _GATE:
    print(f"[Gate] ✅ BRANCH B — .gendoc-rules/ 有 {len(_rules_files)} 個檔案，DRYRUN 已完成")
else:
    reasons = []
    if not _rules_files:
        reasons.append(".gendoc-rules/*.json 不存在")
    if not _dryrun_done:
        reasons.append("DRYRUN 不在 completed_steps")
    print(f"[Gate] ⚙️  BRANCH A — {' / '.join(reasons)}")
```

---

## Branch A：補齊 DRYRUN 上游 + 執行 DRYRUN

> **進入條件**：Gate = False（.gendoc-rules/ 不存在 或 DRYRUN 未在 completed_steps）

### A-1：掃描 DRYRUN 前各 Step 的輸出狀態

```python
import json, os, glob as _glob

def _eval_condition(cond, client_type, has_admin):
    """回傳 True 表示此 step 應執行"""
    if not cond or cond == 'always':
        return True
    ct = client_type.strip().lower()
    adm = has_admin.strip().lower() in ('true', '1', 'yes')

    if cond == 'client_type != none':
        return ct not in ('', 'api-only')
    if cond == 'client_type != api-only':
        return ct != 'api-only'
    if cond == 'client_type == api-only':
        return ct == 'api-only'
    if cond == 'client_type == game':
        return ct in ('unity', 'cocos', 'game')
    if cond == 'has_admin_backend':
        return adm
    return True  # unknown condition → include

def _output_complete(step, tmpl_dir=''):
    """回傳 (exists: bool, complete: bool, reason: str)
    - (False, False, reason) : 主要輸出不存在
    - (True,  False, reason) : 存在但章節不完整（需重建）
    - (True,  True,  '')     : 存在且完整
    """
    import re
    outputs = step.get('output', [])
    output_glob = step.get('output_glob', '')

    if output_glob:
        for pattern in output_glob.split('|'):
            pattern = pattern.strip()
            if not _glob.glob(pattern):
                return False, False, f'output_glob 無匹配：{pattern}'
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

    # Section completeness check（只對單一 .md 檔輸出有效）
    if tmpl_dir:
        sid = step['id']
        tmpl_file = os.path.join(tmpl_dir, f'{sid}.md')
        for path in outputs:
            if path.endswith('.md') and os.path.isfile(path) and os.path.isfile(tmpl_file):
                expected_h2 = len(re.findall(r'^## ', open(tmpl_file, encoding='utf-8').read(), re.MULTILINE))
                actual_h2   = len(re.findall(r'^## ', open(path,     encoding='utf-8').read(), re.MULTILINE))
                if expected_h2 > 0 and actual_h2 < expected_h2:
                    return True, False, f'章節不完整：{actual_h2}/{expected_h2} 個 ## 章節（{path}）'
                break  # 只比對第一個 .md 輸出

    return True, True, ''

def _output_exists(step):
    """向下相容封裝：只回傳布林值，供 B-1 _check_step_l1 使用"""
    exists, complete, _ = _output_complete(step)
    return exists and complete

# 找出 DRYRUN 的 index
_dryrun_idx = next((i for i, s in enumerate(steps) if s['id'] == 'DRYRUN'), None)
if _dryrun_idx is None:
    print("[ABORT] pipeline.json 中找不到 DRYRUN step")
    raise SystemExit(1)

# 掃描 DRYRUN 前的所有 step
_pre_dryrun = steps[:_dryrun_idx]
_a_missing = []  # 需要補跑的 step id list

for step in _pre_dryrun:
    sid  = step['id']
    cond = step.get('condition', 'always')

    if not _eval_condition(cond, _CLIENT_TYPE, _HAS_ADMIN):
        print(f"[A-1] ⏭️  {sid} — 條件不符（{cond}），略過")
        continue

    _tmpl_dir = os.environ.get('GENDOC_TEMPLATES', '')
    exists, complete, reason = _output_complete(step, tmpl_dir=_tmpl_dir)
    if exists and complete:
        print(f"[A-1] ✅ {sid} — 輸出完整")
    elif exists and not complete:
        print(f"[A-1] ⚠️  {sid} — 輸出存在但不完整（{reason}），標記重建")
        _a_missing.append(sid)
    else:
        print(f"[A-1] ❌ {sid} — 輸出缺失（{reason}），需補跑")
        _a_missing.append(sid)

print(f"\n[A-1] 需補跑 {len(_a_missing)} 個 DRYRUN 前 step：{_a_missing}")
```

### A-2：補跑缺失的 DRYRUN 前 Step

```python
_dryrun_needs_rerun = False  # 任何 pre-DRYRUN step 重建後，DRYRUN 必須重跑
```

對 `_a_missing` 中的每個 `step_id`，依序執行：

```
用 Skill tool 呼叫 gendoc-flow，args="--only {step_id}"
等待回傳後繼續下一個 step。
Skill 呼叫成功（step 重建完成）→ _dryrun_needs_rerun = True
Skill 呼叫失敗 → 記錄失敗原因（不更新 _dryrun_needs_rerun），繼續下一個（不中止）。
```

### A-3：執行 DRYRUN

```python
# 判斷是否需要（重）跑 DRYRUN：
# 1. DRYRUN 從未完成（not _dryrun_done）
# 2. 有任何 pre-DRYRUN step 被重建（_dryrun_needs_rerun = True）
_should_run_dryrun = _dryrun_needs_rerun or not _dryrun_done
```

若 `_should_run_dryrun = True`，執行：

```
用 Skill tool 呼叫 gendoc-gen-dryrun
等待回傳。
```

若 `_should_run_dryrun = False`（DRYRUN 已完成且無 step 重建），跳過 DRYRUN，直接進入 A-4。

DRYRUN 完成後，檢查 `.gendoc-rules/*.json` 是否已生成：

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

> **進入條件**：Gate = True 或 Branch A 已完成 DRYRUN

### B-0：初始化

```python
import json, os, glob as _glob

# 重讀 .gendoc-rules/ 目錄
_rules_dir = '.gendoc-rules'
_rules_map = {}  # {step_id: dict}
for f in _glob.glob(f'{_rules_dir}/*.json'):
    sid = os.path.basename(f).replace('-rules.json', '').upper()
    try:
        _rules_map[sid] = json.load(open(f, encoding='utf-8'))
    except Exception:
        _rules_map[sid] = {}

# 找出 DRYRUN 後的所有 step
_dryrun_idx = next((i for i, s in enumerate(steps) if s['id'] == 'DRYRUN'), None)
_post_dryrun = steps[_dryrun_idx + 1:]

_MAX_ROUNDS = 3
_round_failures = {}  # {round: [step_id, ...]}
```

### B-1：兩層 FAIL 偵測函式

```python
def _check_step_l1(step):
    """Layer 1：輸出檔案/目錄是否存在且完整（章節數 >= template）"""
    exists, complete, _ = _output_complete(step)  # 復用 A-1 定義的函式（含 section check）
    return exists and complete

def _check_step_l2(step):
    """Layer 2：rules.json 品質門檻是否達標

    讀取 .gendoc-rules/{step_id.lower()}-rules.json 的 min_* 閾值，
    與實際輸出檔的內容比對。回傳 (passed: bool, details: list[str])
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

    # Entity / Table / Schema
    if 'entity' in k or 'table_count' in k or 'schema' in k:
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

### B-2：執行驗證 + 補跑迴圈

```python
for _round in range(1, _MAX_ROUNDS + 1):
    print(f"\n{'='*60}")
    print(f"[Branch B] Round {_round}/{_MAX_ROUNDS} — 驗證 DRYRUN 後各 Step")
    print(f"{'='*60}")

    _fail_this_round = []

    for step in _post_dryrun:
        sid  = step['id']
        cond = step.get('condition', 'always')

        # 1. 條件過濾
        if not _eval_condition(cond, _CLIENT_TYPE, _HAS_ADMIN):
            print(f"[B-2] ⏭️  {sid} — 條件不符（{cond}），略過")
            continue

        # 2. L1：輸出存在性檢查
        if not _check_step_l1(step):
            print(f"[B-2] ❌ {sid} — L1 FAIL：輸出缺失或空白")
            _fail_this_round.append((sid, 'L1', ['輸出檔案缺失或空白']))
            continue

        # 3. L2：rules.json 品質門檻
        l2_ok, l2_details = _check_step_l2(step)
        if not l2_ok:
            print(f"[B-2] ❌ {sid} — L2 FAIL：")
            for d in l2_details:
                print(f"          {d}")
            _fail_this_round.append((sid, 'L2', l2_details))
            continue

        print(f"[B-2] ✅ {sid} — L1+L2 通過")

    # 所有步驟都通過 → 完成
    if not _fail_this_round:
        print(f"\n[Branch B] ✅ Round {_round} 全部通過，repair 完成！")
        _round_failures[_round] = []
        break

    print(f"\n[Branch B] Round {_round} 發現 {len(_fail_this_round)} 個 FAIL：")
    for sid, layer, details in _fail_this_round:
        print(f"  [{layer}] {sid}: {'; '.join(details)}")

    _round_failures[_round] = [sid for sid, _, _ in _fail_this_round]

    # 補跑每個 FAIL 的 step（每輪都補跑，包括第 3 輪；單一失敗不中止）
    print(f"\n[Branch B] 開始補跑 {len(_fail_this_round)} 個 step...")
    for sid, layer, _ in _fail_this_round:
        print(f"[Branch B] ▶ 補跑 {sid}（{layer} FAIL）")
        # 用 Skill tool 呼叫 gendoc-flow --only {sid}
        # 等待回傳，失敗則記錄繼續
```

**每個 step 補跑指令（在上面迴圈的「補跑」位置執行）：**

```python
# 先從 pipeline 查出此 step 是否為 special_skill
_step_def = next((s for s in steps if s['id'] == sid), {})
_special_sk = _step_def.get('special_skill', '')

if _special_sk:
    # ⚠️ ENFORCEMENT：special_skill step 補跑只允許用 Skill() 呼叫其 special_skill
    # 禁止使用 Write/Edit/Bash 直接在 output 目錄建立或補充檔案
    print(f"[Branch B] ▶ {sid} 為 special_skill（{_special_sk}），必須且只能呼叫 Skill(\"{_special_sk}\")")
    # 用 Skill tool 呼叫 {_special_sk}（不傳 args；各 special_skill skill 自行讀 pipeline）
    # 等待回傳。
    # 呼叫返回後：依 pipeline.json output 欄位確認預期路徑是否存在
    _expected_outputs = _step_def.get('output', [])
    _output_ok = all(
        (os.path.isdir(p.rstrip('/')) and os.listdir(p.rstrip('/'))) if p.endswith('/')
        else (os.path.isfile(p) and os.path.getsize(p) > 0)
        for p in _expected_outputs
    ) if _expected_outputs else False
    if not _output_ok:
        print(f"[WARN] {sid} Skill 呼叫後輸出路徑仍不存在，不寫入 special_completed，告知使用者需手動介入")
    # 不得改用 Write/Edit/Bash 補生成
else:
    # 標準 step：呼叫 gendoc-flow --only {sid}
    # 用 Skill tool 呼叫 gendoc-flow，args="--only {sid}"
    # 等待回傳。
    # 若 Skill tool 回傳失敗 → 印出 [WARN] {sid} 補跑失敗，繼續下一個 step。
    pass
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
        l1_ok = _check_step_l1(step)
        l2_ok, _ = _check_step_l2(step) if l1_ok else (False, [])
        if not (l1_ok and l2_ok):
            _final_fail.append(sid)
    last_fails = _final_fail
```

```python
print("\n" + "="*60)
print("[gendoc-repair] 最終報告")
print("="*60)

if not last_fails:
    print("✅ 所有 step 通過 L1+L2 驗證，專案已完整。")
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
7. **最多 3 輪重試** — 超過後報告失敗原因，不無限迴圈
