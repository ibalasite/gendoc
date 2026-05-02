---
name: gendoc-gen-dryrun
description: DRYRUN step — 讀取 EDD/PRD/ARCH 計算量化基線，生成 docs/MANIFEST.md 和所有 .gendoc-rules/*.json；不跑 review loop
version: 1.0.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Agent
---

# gendoc-gen-dryrun — Pipeline Dryrun & Rule Generation

```
Input:   當前目錄的 .gendoc-state.json + docs/{EDD,PRD,ARCH}.md
Output:  docs/MANIFEST.md（人類可讀的執行清單）
         .gendoc-rules/*.json（每個 step 的機械式驗證規則）
Purpose: 為後續每個 step 的 gate-check.sh 提供量化錨點，讓 review 有確定性基線
```

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 0：環境初始化

```bash
_CWD="$(pwd)"
_DOCS_DIR="${_CWD}/docs"
_RULES_DIR="${_CWD}/.gendoc-rules"
_MANIFEST="${_DOCS_DIR}/MANIFEST.md"

mkdir -p "$_RULES_DIR"
mkdir -p "$_DOCS_DIR"

# 讀取 state file
_STATE_FILE=$(ls "$_CWD"/.gendoc-state-*.json 2>/dev/null | head -1 || echo "")
[[ -z "$_STATE_FILE" && -f "$_CWD/.gendoc-state.json" ]] && _STATE_FILE="$_CWD/.gendoc-state.json"

if [[ -z "$_STATE_FILE" ]]; then
  echo "❌ 找不到 .gendoc-state.json，請先執行 /gendoc-auto 初始化"
  exit 1
fi

_CLIENT_TYPE=$(python3 -c "import json; d=json.load(open('$_STATE_FILE')); print(d.get('client_type',''))" 2>/dev/null || echo "")
_HAS_ADMIN=$(python3 -c "import json; d=json.load(open('$_STATE_FILE')); print('true' if d.get('has_admin_backend') else 'false')" 2>/dev/null || echo "false")

# 尋找 pipeline.json（local-first）
_PIPELINE_LOCAL="${_CWD}/templates/pipeline.json"
_PIPELINE_GLOBAL="${HOME}/.claude/gendoc/templates/pipeline.json"
if [[ -f "$_PIPELINE_LOCAL" ]]; then
  _PIPELINE="$_PIPELINE_LOCAL"
elif [[ -f "$_PIPELINE_GLOBAL" ]]; then
  _PIPELINE="$_PIPELINE_GLOBAL"
else
  echo "❌ 找不到 pipeline.json"
  exit 1
fi

echo "[DRYRUN] CWD：$_CWD"
echo "[DRYRUN] client_type：${_CLIENT_TYPE:-（未設定）}"
echo "[DRYRUN] has_admin_backend：$_HAS_ADMIN"
echo "[DRYRUN] rules dir：$_RULES_DIR"
```

---

## Step 1：讀取上游文件 + 計算量化基線

```bash
# 確認上游文件存在
for _F in "docs/EDD.md" "docs/PRD.md" "docs/ARCH.md"; do
  [[ -f "${_CWD}/${_F}" ]] && echo "[OK] $_F" || echo "[WARN] $_F 不存在（將使用預設值）"
done

# ── 2-A：EDD entity count（classDiagram 中 class 定義數）
_ENTITY_COUNT=$(grep -c '^\s*class ' "${_CWD}/docs/EDD.md" 2>/dev/null || echo "5")
[[ "$_ENTITY_COUNT" -lt 3 ]] && _ENTITY_COUNT=5

# ── 2-B：EDD REST endpoint count
_REST_COUNT=$(grep -cE '(<<REST>>|<<Interface>>|HTTP\s*(GET|POST|PUT|DELETE|PATCH))' "${_CWD}/docs/EDD.md" 2>/dev/null || echo "10")
[[ "$_REST_COUNT" -lt 5 ]] && _REST_COUNT=10

# ── 2-C：PRD user story count
_US_COUNT=$(grep -cE '^(## |### )US-' "${_CWD}/docs/PRD.md" 2>/dev/null || echo "10")
[[ "$_US_COUNT" -lt 3 ]] && _US_COUNT=10

# ── 2-D：ARCH layer count（Tech Stack table non-header rows）
_ARCH_LAYER_COUNT=$(grep -c '^| [A-Za-z]' "${_CWD}/docs/ARCH.md" 2>/dev/null || echo "4")
[[ "$_ARCH_LAYER_COUNT" -lt 4 ]] && _ARCH_LAYER_COUNT=4

# ── 2-E：BDD scenario target = ceil(US_COUNT × 0.8)
_BDD_MIN=$(python3 -c "import math; print(max(3, math.ceil(${_US_COUNT} * 0.8)))" 2>/dev/null || echo "8")

echo "[DRYRUN] entity_count=${_ENTITY_COUNT}  rest_count=${_REST_COUNT}  us_count=${_US_COUNT}  arch_layers=${_ARCH_LAYER_COUNT}  bdd_min=${_BDD_MIN}"
```

---

## Step 2：確定 active steps（條件過濾）

**[AI 指令]** 用 Python 讀取 pipeline.json，套用與 gendoc-flow 相同的條件過濾邏輯，列出本次執行的 active/skipped steps：

```python
import json
pipeline = json.load(open("${_PIPELINE}", encoding="utf-8"))
client_type = "${_CLIENT_TYPE}"
has_admin = "${_HAS_ADMIN}" == "true"

active_steps = []
skipped_steps = []

for step in pipeline.get("steps", []):
    sid = step.get("id", "")
    cond = step.get("condition", "always")
    skip = False

    if cond == "client_type != api-only" and client_type == "api-only":
        skip = True
    elif cond == "client_type == api-only" and client_type != "api-only":
        skip = True
    elif cond == "client_type != none" and client_type in ("none", ""):
        skip = True
    elif cond == "client_type == game" and client_type != "game":
        skip = True
    elif cond == "has_admin_backend" and not has_admin:
        skip = True

    if skip:
        skipped_steps.append(sid)
    else:
        active_steps.append({"id": sid, "step": step})
```

輸出 active_steps 清單，供 Step 3 使用。

---

## Step 3：生成各 step 的 .gendoc-rules/*.json

**[AI 指令]** 對每個 active step，計算量化規則，用 **Write 工具**寫入 `.gendoc-rules/<step-id>-rules.json`。

規則計算邏輯（依 step_id）：

| step_id | output_files | min_h2_sections | 特殊量化規則 | required_sections |
|---------|-------------|-----------------|-------------|-------------------|
| IDEA | docs/IDEA.md | 3 | — | ["Problem Statement", "Target Users", "Core Value"] |
| BRD | docs/BRD.md | 5 | — | ["Business Objectives", "Stakeholders", "Success Metrics"] |
| PRD | docs/PRD.md | 5 | — | ["User Stories", "Acceptance Criteria", "Out of Scope"] |
| CONSTANTS | docs/CONSTANTS.md | 3 | — | ["Business Rules", "System Parameters"] |
| PDD | docs/PDD.md | 4 | — | ["Product Vision", "Feature List", "Roadmap"] |
| VDD | docs/VDD.md | 3 | — | ["Design Principles", "Visual Language"] |
| EDD | docs/EDD.md | 8 | — | ["Domain Model", "Service Architecture", "Data Flow"] |
| ARCH | docs/ARCH.md | 5 | — | ["Architecture Overview", "Tech Stack", "Component Design"] |
| API | docs/API.md | 6 | min_endpoint_count=${_REST_COUNT} | ["API Overview", "Authentication", "Endpoints", "Error Codes"] |
| SCHEMA | docs/SCHEMA.md | 5 | min_table_count=${_ENTITY_COUNT} | ["Overview", "Tables", "Indexes", "Migration"] |
| FRONTEND | docs/FRONTEND.md | 4 | — | ["Page Structure", "Component Design", "State Management"] |
| AUDIO | docs/AUDIO.md | 3 | — | ["Audio Architecture", "Sound Events"] |
| ANIM | docs/ANIM.md | 3 | — | ["Animation System", "State Machine"] |
| CLIENT_IMPL | docs/CLIENT_IMPL.md | 4 | — | ["Technology Stack", "Project Structure", "Build Process"] |
| ADMIN_IMPL | docs/ADMIN_IMPL.md | 4 | — | ["Admin Architecture", "Feature Modules", "Access Control"] |
| RESOURCE | docs/RESOURCE.md | 3 | — | ["Infrastructure Overview", "Resource Allocation"] |
| UML | docs/diagrams/ (multi_file) | 3 per file | min_file_count=9 | — |
| test-plan | docs/test-plan.md | ${_ARCH_LAYER_COUNT_PLUS2} | — | ["Test Objectives", "Test Scope", "Test Cases"] |
| BDD-server | features/server/ (multi_file) | — | min_scenario_count=${_BDD_MIN} | — |
| BDD-client | features/client/ (multi_file) | — | min_scenario_count=${_BDD_MIN} | — |
| RTM | docs/RTM.md | 3 | min_row_count=${_US_COUNT} | ["Requirements", "Test Cases", "Coverage"] |
| runbook | docs/runbook.md | 4 | — | ["Deployment", "Incident Response", "Rollback"] |
| LOCAL_DEPLOY | docs/LOCAL_DEPLOY.md | 5 | — | ["Prerequisites", "Setup Steps", "Verification"] |
| CICD | docs/CICD.md | 6 | — | ["Pipeline Overview", "Jenkinsfile", "PR Gate", "ArgoCD"] |
| DEVELOPER_GUIDE | docs/DEVELOPER_GUIDE.md | 5 | — | ["Daily Scenarios", "CI/CD Diagnosis", "Quick Reference"] |
| UML-CICD | docs/diagrams/ (multi_file, cicd) | — | min_file_count=5 | — |
| ALIGN | docs/ALIGN-REPORT.md | 3 | — | ["Alignment Issues", "Cross-Document Gaps"] |
| CONTRACTS | docs/contracts/ (multi_file) | 3 per file | — | — |
| MOCK | docs/mock-data/ (multi_file) | — | — | — |
| PROTOTYPE | docs/prototype/ (multi_file) | — | — | — |
| HTML | docs/pages/ (multi_file) | — | min_file_count=3 | — |

通用 anti_fake_rules（所有 step 都套用）：

```json
[
  {"type": "no_placeholder_strings", "pattern": "\\{\\{[A-Z_]+\\}\\}"},
  {"type": "no_duplicate_paragraphs", "min_char_length": 150},
  {"type": "min_section_words", "min_words": 30},
  {"type": "no_trivial_entity_names"}
]
```

**Write 工具示範（API step）：**

```json
{
  "step_id": "API",
  "step_name": "API Design Document",
  "output_files": [
    {
      "path": "docs/API.md",
      "must_exist": true,
      "must_not_be_empty": true,
      "min_h2_sections": 6,
      "min_endpoint_count": 10,
      "required_sections": ["API Overview", "Authentication", "Endpoints", "Error Codes"],
      "no_bare_placeholders": true,
      "min_words_per_section": 30
    }
  ],
  "anti_fake_rules": [
    {"type": "no_placeholder_strings", "pattern": "\\{\\{[A-Z_]+\\}\\}"},
    {"type": "no_duplicate_paragraphs", "min_char_length": 150},
    {"type": "no_trivial_entity_names"}
  ]
}
```

> 注意：`_REST_COUNT`、`_ENTITY_COUNT`、`_US_COUNT`、`_ARCH_LAYER_COUNT` 必須填入 Step 1 計算的實際數值，不得保留為字串 placeholder。

---

## Step 4：生成 docs/MANIFEST.md

**[AI 指令]** 讀取 `templates/DRYRUN.md` 作為骨架，將所有 `{{PLACEHOLDER}}` 替換為實際值，用 **Write 工具**寫入 `docs/MANIFEST.md`。

替換對照表：

| Placeholder | 實際值 |
|-------------|--------|
| `{{GENERATED_DATE}}` | 今日 ISO 8601 date |
| `{{PIPELINE_VERSION}}` | pipeline.json 的 `version` 欄位 |
| `{{CLIENT_TYPE}}` | `_CLIENT_TYPE` |
| `{{HAS_ADMIN_BACKEND}}` | `_HAS_ADMIN` |
| `{{ACTIVE_STEPS_COUNT}}` | active steps 數量 |
| `{{SKIPPED_STEPS_COUNT}}` | skipped steps 數量 |
| `{{ENTITY_COUNT}}` | `_ENTITY_COUNT` |
| `{{REST_ENDPOINT_COUNT}}` | `_REST_COUNT` |
| `{{USER_STORY_COUNT}}` | `_US_COUNT` |
| `{{ARCH_LAYER_COUNT}}` | `_ARCH_LAYER_COUNT` |

§3 Mandatory Steps Checklist → 用 active_steps 清單填入，Status 全設為 `PENDING`（後續 step 完成後由 gendoc-flow 更新）。

§4 Per-Step Completeness Standards → 用各 step 的 rules.json 中的 quantitative rules 填入。

§2.2 Active Conditional Steps → 用 skipped_steps 和 active_steps 的條件欄位填入。

---

## Step 5：commit 並輸出完成信號

```bash
_NOW=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
_RULES_COUNT=$(ls "${_RULES_DIR}"/*.json 2>/dev/null | wc -l | tr -d ' ')

# commit MANIFEST.md + 所有 rules files
git add docs/MANIFEST.md .gendoc-rules/
git commit -m "docs(gendoc)[DRYRUN]: gen — 生成 MANIFEST.md + ${_RULES_COUNT} 個 gate rules 文件

Entity-Count: ${_ENTITY_COUNT}
REST-Count: ${_REST_COUNT}
US-Count: ${_US_COUNT}
Arch-Layers: ${_ARCH_LAYER_COUNT}
Active-Steps: <active_steps_count>
Skipped-Steps: <skipped_steps_count>"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  DRYRUN 完成                                                  ║"
echo "╠══════════════════════════════════════════════════════════════╣"
printf "║  MANIFEST.md  : docs/MANIFEST.md                            ║\n"
printf "║  Rules files  : %d 個 .gendoc-rules/*.json                   ║\n" "${_RULES_COUNT}"
printf "║  Entity count : %-10s                                   ║\n" "${_ENTITY_COUNT}"
printf "║  REST count   : %-10s                                   ║\n" "${_REST_COUNT}"
printf "║  US count     : %-10s                                   ║\n" "${_US_COUNT}"
printf "║  Arch layers  : %-10s                                   ║\n" "${_ARCH_LAYER_COUNT}"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "STEP_COMPLETE: DRYRUN"
```

---

## 注意事項

1. **DRYRUN 本身不跑 review→fix loop**（pipeline.json 中標記 `special_skill`，gendoc-flow 直接跳過 review）
2. **rules.json 中的量化數值一旦生成即為基線**，不隨後續 step 重新計算（除非重跑 DRYRUN）
3. **gate-check.sh 讀取 .gendoc-rules/ 的規則**，在每個 step 的 review loop 第一輪前自動執行
4. **若 EDD/PRD/ARCH 不存在**，使用保守預設值（不因缺少上游文件而中斷），但在 MANIFEST.md 的 §2.1 備注「⚠️ 預設值（上游文件未找到）」
5. **Multi-file steps**（UML、BDD、HTML 等）的 rules.json 使用 output_glob 替代 path
