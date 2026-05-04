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
if [[ ! -f "docs/BRD.md" ]]; then
  echo "[ABORT] docs/BRD.md 不存在，無法執行 repair。"
  echo "[Hint]  請先執行 /gendoc-auto 或手動提供 BRD.md"
  exit 1
fi
echo "[R-01] ✅ docs/BRD.md 存在"
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

def _output_exists(step):
    """回傳 True 表示 step 的主要輸出已存在且非空"""
    outputs = step.get('output', [])
    output_glob = step.get('output_glob', '')

    if output_glob:
        # output_glob 格式：path1|path2
        for pattern in output_glob.split('|'):
            pattern = pattern.strip()
            if not _glob.glob(pattern):
                return False
        return True

    for path in outputs:
        if path.endswith('/'):
            # 目錄：檢查目錄存在且有檔案
            if not os.path.isdir(path.rstrip('/')) or not os.listdir(path.rstrip('/')):
                return False
        else:
            # 單一檔案：存在且非空
            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                return False
    return bool(outputs)

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

    if _output_exists(step):
        print(f"[A-1] ✅ {sid} — 輸出存在")
    else:
        print(f"[A-1] ❌ {sid} — 輸出缺失，需補跑")
        _a_missing.append(sid)

print(f"\n[A-1] 需補跑 {len(_a_missing)} 個 DRYRUN 前 step：{_a_missing}")
```

### A-2：補跑缺失的 DRYRUN 前 Step

對 `_a_missing` 中的每個 `step_id`，依序執行：

```
用 Skill tool 呼叫 gendoc-flow，args="--only {step_id}"
等待回傳後繼續下一個 step。
單一 step 失敗 → 記錄失敗原因，繼續下一個（不中止）。
```

### A-3：執行 DRYRUN

所有 DRYRUN 前的 step 補跑完後（無論有無失敗），執行：

```
用 Skill tool 呼叫 gendoc-gen-dryrun
等待回傳。
```

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
    """Layer 1：輸出檔案/目錄是否存在且非空"""
    return _output_exists(step)  # 復用 A-1 定義的函式

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
        # 輸出不是單一 .md（e.g., 目錄型 step）→ 只看 L1
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

    # 補跑每個 FAIL 的 step（繼續，不中止）
    if _round < _MAX_ROUNDS:
        print(f"\n[Branch B] 開始補跑 {len(_fail_this_round)} 個 step...")
        for sid, layer, _ in _fail_this_round:
            print(f"[Branch B] ▶ 補跑 {sid}（{layer} FAIL）")
            # 用 Skill tool 呼叫 gendoc-flow --only {sid}
            # 等待回傳，失敗則記錄繼續
    else:
        # 已達最大輪次，不再補跑
        pass
```

**每個 step 補跑指令（在上面迴圈的「補跑」位置執行）：**

```
用 Skill tool 呼叫 gendoc-flow，args="--only {sid}"
等待回傳。
若 Skill tool 回傳失敗 → 印出 [WARN] {sid} 補跑失敗，繼續下一個 step。
```

### B-3：最終報告

```python
print("\n" + "="*60)
print("[gendoc-repair] 最終報告")
print("="*60)

all_rounds = sorted(_round_failures.keys())
last_fails  = _round_failures.get(max(all_rounds), []) if all_rounds else []

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
