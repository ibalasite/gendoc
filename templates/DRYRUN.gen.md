---
doc-type: DRYRUN
version: 1.0.0
description: Pipeline Execution Manifest 生成規則 — 在所有文件生成之前執行，計算量化錨點、決定條件步驟、並為每個 active step 生成對應的 rules JSON
expert-roles:
  - Pipeline Analyst：讀取 pipeline.json 和 state 文件，決定哪些步驟啟用、哪些跳過
  - Quantitative Rules Architect：從上游文件計算量化錨點，推導每個步驟的最低品質門檻
upstream-docs:
  input-files: templates/pipeline.json input[] array (DRYRUN step)
  description: |
    DRYRUN step's input[] array in pipeline.json specifies which Phase A files
    are needed (IDEA, BRD, PRD, CONSTANTS, PDD, VDD, EDD, ARCH).
    get-upstream reads these from the target project and returns JSON with file contents.
    Metric extraction logic (grep patterns) remains in dryrun.gen.md §2.
  always-required:
    - templates/pipeline.json    # Contains input[] definitions for DRYRUN (SSOT)
    - .gendoc-state.json         # client_type, has_admin_backend for conditional logic
    - tools/bin/get-upstream.sh  # File reader tool
quality-bar:
  - docs/MANIFEST.md 已生成，所有 {{PLACEHOLDER}} 均已替換（無殘留 placeholder）
  - .gendoc-rules/ 目錄已建立，每個 active step 均有對應的 <step-id>-rules.json
  - 量化錨點（entity_count / rest_endpoint_count / user_story_count / arch_layer_count）均為真實計算值（非預設值 0）
  - Active / Skipped 步驟清單與 pipeline.json 條件邏輯完全一致
  - 所有 rules JSON 的量化門檻公式已套用錨點數值（非 {{PLACEHOLDER}}）
---

# DRYRUN 生成規則

## Iron Rule：流水線前置執行

> **Iron Law**：生成任何 MANIFEST.md 之前，必須先讀取 `DRYRUN.md`（結構骨架）和 `DRYRUN.gen.md`（本生成規則）。
> **禁止保留 Bare Placeholder**：輸出的 docs/MANIFEST.md 中不得含任何 `{{...}}` 格式的未替換 placeholder。若任何上游文件缺少必要值，必須停止生成並向使用者報告缺失項目。

DRYRUN 是 gendoc pipeline 的**第零步**，在任何文件生成之前執行。
它的輸出（docs/MANIFEST.md 和 .gendoc-rules/*.json）是後續所有 gate-check 的依據。

**禁止在 DRYRUN 之前執行任何文件生成步驟。**
若發現 docs/MANIFEST.md 不存在或 .gendoc-rules/ 目錄不存在，gendoc-flow 必須先執行 DRYRUN，再繼續其他步驟。

---

## 專家角色說明

本步驟由兩個並行專家角色協作完成：

**Pipeline Analyst（流水線分析師）**
- 讀取 `templates/pipeline.json` 取得所有步驟定義
- 讀取 `.gendoc-state.json`（或等效 state 文件）取得 `client_type` 和 `has_admin_backend`
- 依條件邏輯決定每個步驟的 Active Y/N 狀態
- 計算 Active Steps Count 和 Skipped Steps Count

**Quantitative Rules Architect（量化規則架構師）**
- 執行 Step 2 的 bash 命令，從上游文件提取數字
- 依 Step 5 的公式推導每個步驟的量化門檻
- 生成 .gendoc-rules/*.json 文件
- 填充 docs/MANIFEST.md 的所有量化欄位

---

## Step 1：讀取上游文件（使用 get-upstream）

**SSOT 原則**：不在 dryrun.gen.md 中硬編碼檔案清單，而是從 `templates/pipeline.json` 的 DRYRUN step `input[]` 陣列讀取。`get-upstream` 工具負責讀取檔案並返回 JSON。

### 1-A. 呼叫 get-upstream 讀取 DRYRUN 的 input 檔案

```bash
# 呼叫 get-upstream 讀取 DRYRUN step 定義的所有 input 檔案
# 返回 JSON：{"step": "DRYRUN", "timestamp": "...", "inputs": {"docs/IDEA.md": "content", ...}}
_UPSTREAM_JSON=$(tools/bin/get-upstream --step DRYRUN --output json 2>&1)

if [[ $? -ne 0 ]]; then
  echo "ERROR: get-upstream failed with:"
  echo "$_UPSTREAM_JSON" >&2
  exit 1
fi
```

### 1-B. 解析 JSON 並提取各檔案內容

```bash
# 使用 Python 從返回的 JSON 中提取各檔案內容
# 儲存到變數供後續步驟使用（Step 2 中的 grep 操作）
_INPUT_DATA=$(python3 << 'PYTHON_EOF'
import json
import sys

input_json = sys.stdin.read()
data = json.loads(input_json)

# 將所有 input 檔案內容存成字典，供後續 grep 操作使用
inputs = data.get('inputs', {})

# 列出所有已讀取的檔案（用於檢查）
for file_spec in inputs.keys():
    print(f"FOUND: {file_spec}")

# 將整個 inputs dict 轉為 bash 可用的格式
# （在下一段 bash 中會解析）
print("\n# INPUTS_START")
print(json.dumps(inputs, ensure_ascii=False))
print("# INPUTS_END")
PYTHON_EOF
)

# 提取 JSON 部分
_INPUTS_JSON=$(echo "$_INPUT_DATA" | sed -n '/# INPUTS_START/,/# INPUTS_END/{/# INPUTS_/!p;}')
```

### 1-C. 同時讀取 state 文件（條件判斷用）

```bash
# 讀取 .gendoc-state.json 用於條件判斷（client_type, has_admin_backend 等）
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1)
if [[ -f "$_STATE_FILE" ]]; then
  CLIENT_TYPE=$(python3 -c "import json; print(json.load(open('$_STATE_FILE')).get('client_type', 'unknown'))")
  HAS_ADMIN=$(python3 -c "import json; print(json.load(open('$_STATE_FILE')).get('has_admin_backend', False))")
else
  echo "WARNING: State file not found, using defaults"
  CLIENT_TYPE="api-only"
  HAS_ADMIN="false"
fi
```

> **設計說明**：
> - 檔案清單（input[]）由 pipeline.json DRYRUN step 定義，是單一真相來源
> - get-upstream 工具負責讀取檔案並返回 JSON
> - dryrun.gen.md §2 負責從該 JSON 中提取度量指標（grep 邏輯保持不變）
> - DRYRUN 不執行上游衝突偵測；若存在矛盾，由各自的 review 步驟處理

---

## Step 2：計算量化錨點

**步驟說明**：Step 1 已透過 get-upstream 讀取所有上游檔案並存入 `_INPUTS_JSON`。
本步驟從該 JSON 提取各檔案內容，執行相同的 grep 操作以計算量化錨點。

### 2-A. entity_count（EDD classDiagram 中的 class 數量）

```bash
# 從 _INPUTS_JSON 中提取 EDD 內容，執行 grep
_EDD_CONTENT=$(python3 -c "import json, sys; data=json.loads('''$_INPUTS_JSON'''); print(data.get('docs/EDD.md', ''))")
_ENTITY_COUNT=$(echo "$_EDD_CONTENT" | grep -c '^\s*class ' 2>/dev/null || echo 0)
echo "entity_count=${_ENTITY_COUNT}"
```

> 計算 EDD 內容中所有以 `class ` 開頭的行（含前導空白），對應 Mermaid classDiagram 的 entity 定義。

---

### 2-B. rest_endpoint_count（REST 端點數量）

```bash
# 從 _INPUTS_JSON 中提取 EDD 內容
_EDD_CONTENT=$(python3 -c "import json, sys; data=json.loads('''$_INPUTS_JSON'''); print(data.get('docs/EDD.md', ''))")
_REST_COUNT=$(echo "$_EDD_CONTENT" | grep -cE '(<<REST>>|<<Interface>>|HTTP[[:space:]]*(GET|POST|PUT|DELETE|PATCH))' 2>/dev/null || echo 0)
# 若計算結果 < 5，使用 fallback 值 10
if [ "${_REST_COUNT}" -lt 5 ]; then _REST_COUNT=10; fi
echo "rest_endpoint_count=${_REST_COUNT}"
```

> 優先比對 `<<REST>>`、`<<Interface>>`、`HTTP GET/POST/PUT/DELETE/PATCH` 等標記。
> 若結果過少（< 5），代表 EDD 尚未完整定義 REST 介面，使用保守預設值 10。

---

### 2-C. user_story_count（PRD User Story 數量）

```bash
# 從 _INPUTS_JSON 中提取 PRD 內容
_PRD_CONTENT=$(python3 -c "import json, sys; data=json.loads('''$_INPUTS_JSON'''); print(data.get('docs/PRD.md', ''))")
_US_COUNT=$(echo "$_PRD_CONTENT" | grep -c '^## US-\|^### US-' 2>/dev/null || echo 0)
echo "user_story_count=${_US_COUNT}"
```

> 計算 PRD 內容中所有以 `## US-` 或 `### US-` 開頭的標題，對應 PRD 的 User Story ID 命名規範。

---

### 2-D. arch_layer_count（ARCH Tech Stack 層數）

```bash
# 從 _INPUTS_JSON 中提取 ARCH 內容
_ARCH_CONTENT=$(python3 -c "import json, sys; data=json.loads('''$_INPUTS_JSON'''); print(data.get('docs/ARCH.md', ''))")
# 掃描表格的非標頭列數（最小值 4）
_ARCH_LAYER_COUNT=$(echo "$_ARCH_CONTENT" | awk '/## §3|^## 3 |^# §3/{found=1} found && /^\|[^-]/{count++} END{print (count<4)?4:count}' 2>/dev/null || echo 4)
echo "arch_layer_count=${_ARCH_LAYER_COUNT}"
```

> 掃描 ARCH 內容中 §3 附近的 Markdown 表格，計算非標頭列的數量。
> 若計算失敗，使用最小值 4（Presentation / Application / Domain / Infrastructure）。

---

### 2-E. client_type 和 has_admin_backend（從 Step 1-C 取得）

這些值已在 Step 1-C 中讀取並儲存為 `$CLIENT_TYPE` 和 `$HAS_ADMIN`，無需重複讀取。

```bash
echo "client_type=${CLIENT_TYPE}"
echo "has_admin_backend=${HAS_ADMIN}"
```

> 若 `.gendoc-state.json` 不存在，Step 1-C 已設定保守預設值：
> `client_type=api-only`、`has_admin_backend=false`。

---

## Step 3：決定 Active / Skipped 步驟

讀取 `templates/pipeline.json` 的 `steps` 陣列，依以下條件邏輯逐步判斷：

| pipeline.json condition | 啟用條件 |
|------------------------|---------|
| `always` | 永遠啟用 |
| `client_type != none` | `_CLIENT_TYPE` 不等於 `"none"` 時啟用 |
| `client_type == game` | `_CLIENT_TYPE` 等於 `"game"` 時啟用 |
| `client_type != api-only` | `_CLIENT_TYPE` 不等於 `"api-only"` 時啟用 |
| `has_admin_backend` | `_HAS_ADMIN` 等於 `"true"` 時啟用 |

對每個步驟，將計算結果記錄為 `Y`（Active）或 `N`（Skipped），填入 MANIFEST.md §2.2 表格。

統計：
- `ACTIVE_STEPS_COUNT` = Y 的步驟總數
- `SKIPPED_STEPS_COUNT` = N 的步驟總數

---

## Step 4：生成 .gendoc-rules/ 目錄與 rules JSON

為每個 Active 步驟生成對應的 `<step-id>-rules.json` 至 `.gendoc-rules/` 目錄。

**目錄建立：**

```bash
mkdir -p .gendoc-rules
```

**rules JSON 格式：**

```json
{
  "step_id": "<步驟 ID，如 API>",
  "step_name": "<步驟名稱，如 API Design Document>",
  "output_files": [
    {
      "path": "<輸出檔案路徑，如 docs/API.md>",
      "must_exist": true,
      "min_h2_sections": <最少 ## 標題數，整數>,
      "min_endpoint_count": <最少 endpoint 數，整數，不適用填 0>,
      "min_table_count": <最少 Markdown 表格數，整數，不適用填 0>,
      "min_scenario_count": <最少 BDD Scenario 數，整數，不適用填 0>,
      "min_row_count": <最少表格列數（非標頭），整數，不適用填 0>,
      "required_sections": ["<必要章節關鍵字 1>", "<必要章節關鍵字 2>"],
      "no_bare_placeholder": true
    }
  ],
  "anti_fake_rules": [
    "no_bare_placeholder",
    "min_section_words_30",
    "<視步驟類型加入 no_duplicate_paragraphs_150、required_keywords_per_section、no_trivial_entity_names>"
  ]
}
```

**生成原則：**
- `step_id` 和 `path` 直接取自 `pipeline.json` 對應 step 的 `id` 和 `output` 欄位
- 量化欄位（`min_endpoint_count` 等）依 Step 5 的公式計算，不得殘留 `{{PLACEHOLDER}}`
- 所有 Skipped 步驟不生成 rules JSON
- `output_files` 為陣列；multi_file=true 的步驟（如 UML、BDD-server）每個 glob 模式為一個 entry，`path` 填 glob 字串

---

## Step 5：量化規則公式（逐步驟）

以下公式套用 Step 2 計算所得的量化錨點，得出每個步驟的具體門檻數值。

### API.md

```
min_endpoint_count = max(_REST_COUNT, 5)
min_h2_sections    = 5
required_sections  = ["API Overview", "Authentication", "Endpoints", "Error Codes", "Rate Limiting"]
anti_fake_rules    += ["required_keywords_per_section"]
  # Authentication 章節必須含 "Bearer" 或 "API Key"
  # Error Codes 章節必須含 "4xx" 或 "5xx"
```

### SCHEMA.md

```
min_table_count   = max(_ENTITY_COUNT, 3)
min_h2_sections   = 4
required_sections = ["Overview", "Tables", "Indexes", "Migration"]
anti_fake_rules   += ["no_trivial_entity_names"]
```

### test-plan.md

```
min_h2_sections   = _ARCH_LAYER_COUNT + 2
  # +2 = Test Objectives + Test Scope 兩個基礎章節
  # 範例：_ARCH_LAYER_COUNT=4 → min_h2_sections=6
required_sections = ["Test Objectives", "Test Scope", "Unit Test", "Integration Test", "E2E Test", "Coverage Target"]
```

### RTM.md

```
min_row_count     = _US_COUNT
  # RTM 的需求列數必須 ≥ US 數量，確保每個 US 都有追溯條目
min_h2_sections   = 4
anti_fake_rules   += ["no_duplicate_paragraphs_150"]
```

### BDD-server（features/*.feature）

```
min_scenario_count = ceil(_US_COUNT * 0.8)
  # 80% 的 US 必須有對應的 Server BDD Scenario
  # 範例：_US_COUNT=10 → min_scenario_count=8
required_sections  = ["Feature", "Scenario", "Given", "When", "Then"]
anti_fake_rules    += ["required_keywords_per_section"]
```

### BDD-client（features/client/*.feature，若 Active）

```
min_scenario_count = ceil(_US_COUNT * 0.6)
  # 60% 的 US 必須有對應的 Client E2E Scenario
required_sections  = ["Feature", "Scenario", "Given", "When", "Then"]
```

### EDD.md

```
min_h2_sections   = 8
  # §1-§21 共 21 個主章，但至少 8 個實質章節必須存在
required_sections = ["技術棧", "資料模型", "API 設計", "安全", "HA", "觀測性", "Capacity Planning", "UML"]
anti_fake_rules   += ["no_duplicate_paragraphs_150", "no_trivial_entity_names"]
```

### ARCH.md

```
min_h2_sections   = 6
  # 5 → 6：新增 §7.1 Shared State Isolation（HC-4）後，ARCH.md 實際 ## 章節數增加
required_sections = ["架構目標", "架構模式", "系統元件", "安全架構", "擴展策略", "Shared State"]
anti_fake_rules   += ["no_duplicate_paragraphs_150"]
```

### runbook.md

```
min_h2_sections   = 4
required_sections = ["Incident", "診斷", "修復", "Escalation"]
```

### CONTRACTS（openapi.yaml）

```
path_count = max(_REST_COUNT, 5)
required_sections = ["paths", "components", "info"]
```

### MOCK（mock server）

```
endpoint_count = max(_REST_COUNT, 5)
```

### PROTOTYPE（docs/pages/prototype/）

```
min_screen_count = 3  # index.html 存在且 ≥ 3 個 Screen 頁面
```

### IDEA.md

```
min_h2_sections   = 3
anti_fake_rules   += ["no_trivial_entity_names"]
  # Persona 名稱和業務概念不得為 FooBar 等虛假命名
```

### BRD.md

```
min_h2_sections   = 5
anti_fake_rules   += ["min_section_words_30"]
  # MoSCoW 表格含 P0/P1/P2/Out 四分類；KPI 含具體數字
```

### PRD.md

```
min_h2_sections   = 6
anti_fake_rules   += ["no_trivial_entity_names"]
  # US 名稱和 AC 描述不得為虛假占位；NFR 數字不得為「TBD」
```

### CONSTANTS.md

```
min_h2_sections   = 3
  # 至少 5 個常數條目（依 §4 要求）；每條含 name/value/unit/source/note
```

### PDD.md（若 Active）

```
min_h2_sections   = 4
anti_fake_rules   += ["min_section_words_30"]
  # 至少 3 個 Screen；每個 Screen 含欄位清單
```

### VDD.md（若 Active）

```
min_h2_sections   = 4
  # 至少 5 個 Design Token；Color Palette 不得為空
```

### FRONTEND.md（若 Active）

```
min_h2_sections   = 4
  # 至少 3 個 Component；E2E 覆蓋範圍不得為空
```

### AUDIO.md（若 Active）

```
min_h2_sections   = 3
  # BGM/SFX 清單至少各 1 項；音效觸發邏輯不得為空
```

### ANIM.md（若 Active）

```
min_h2_sections   = 3
  # 至少 3 個動畫定義；效能預算不得為空
```

### CLIENT_IMPL.md（若 Active）

```
min_h2_sections   = 4
  # 場景結構已定義；資源載入策略不得為空
```

### ADMIN_IMPL.md（若 Active）

```
min_h2_sections   = 4
anti_fake_rules   += ["no_trivial_entity_names"]
  # RBAC 角色 ≥ 2；路由清單不得為空
```

### RESOURCE.md（若 Active）

```
min_h2_sections   = 3
  # 資產條目 ≥ 5；每條含 ID/檔名/type/prompt
```

### LOCAL_DEPLOY.md

```
min_h2_sections   = 4
  # API Server replica ≥ 2；docker-compose 命令可執行
```

### CICD.md

```
min_h2_sections   = 4
  # Pipeline stages ≥ 3；Secret 注入策略不得為空
```

### DEVELOPER_GUIDE.md

```
min_h2_sections   = 3
  # 日常操作命令 ≥ 5 條；Make targets 不得為空
```

### ALIGN（docs/ALIGN_REPORT.md）

```
min_h2_sections   = 3
  # CRITICAL 問題數 = 0；HIGH 問題數 = 0（或已全部 FIX）
```

### 所有其他步驟（UML / UML-CICD / HTML / 未列出的步驟）

```
min_h2_sections   = 3
  # 最低預設值，確保文件有實質章節結構；
  # 這些步驟多為 multi_file 或特殊格式，主要依靠 §4 量化規則驗收
```

---

## Step 6：生成 docs/MANIFEST.md

從 `templates/DRYRUN.md` skeleton 複製結構，填入 Step 2-5 計算所得的所有值：

1. 將 Document Control 表格中的所有 `{{PLACEHOLDER}}` 替換：
   - `{{GENERATED_DATE}}` → 今日日期（YYYY-MM-DD）
   - `{{PIPELINE_VERSION}}` → `templates/pipeline.json` 的 `version` 欄位值
   - `{{EDD_VERSION}}` → `docs/EDD.md` Document Control 表格中的版本號（若不存在填 `N/A`）
   - `{{CLIENT_TYPE}}` → `_CLIENT_TYPE`
   - `{{HAS_ADMIN_BACKEND}}` → `_HAS_ADMIN`
   - `{{ACTIVE_STEPS_COUNT}}` → Active 步驟總數
   - `{{SKIPPED_STEPS_COUNT}}` → Skipped 步驟總數

2. 填入 §2.1 System Parameters 表格：
   - `{{ENTITY_COUNT}}` → `_ENTITY_COUNT`
   - `{{REST_ENDPOINT_COUNT}}` → `_REST_COUNT`
   - `{{USER_STORY_COUNT}}` → `_US_COUNT`
   - `{{ARCH_LAYER_COUNT}}` → `_ARCH_LAYER_COUNT`

3. 填入 §2.2 Active Conditional Steps 表格，每個步驟填入 `Y` 或 `N`

4. 填入 §3 Mandatory Steps Checklist 狀態欄：DRYRUN 執行時點所有步驟尚未執行，將所有 `{{*_STATUS}}` placeholder（共 20 個：IDEA_STATUS / BRD_STATUS / PRD_STATUS / CONSTANTS_STATUS / EDD_STATUS / ARCH_STATUS / API_STATUS / SCHEMA_STATUS / UML_STATUS / TEST_PLAN_STATUS / BDD_SERVER_STATUS / RTM_STATUS / RUNBOOK_STATUS / LOCAL_DEPLOY_STATUS / CICD_STATUS / DEVELOPER_GUIDE_STATUS / UML_CICD_STATUS / ALIGN_STATUS / CONTRACTS_STATUS / HTML_STATUS）替換為 `PENDING`。

5. 更新 §4 Per-Step Completeness Standards 表格的量化欄位：
   - API 的 `min_endpoint_count` 欄填入 `max(${_REST_COUNT}, 5)` 計算結果
   - SCHEMA 的 `min_table_count` 欄填入 `max(${_ENTITY_COUNT}, 3)` 計算結果
   - test-plan 的 `min_h2_sections` 欄填入 `${_ARCH_LAYER_COUNT} + 2` 計算結果
   - RTM 的 `min_row_count` 欄填入 `${_US_COUNT}` 值
   - BDD-server 的 `min_scenario_count` 欄填入 `ceil(${_US_COUNT} × 0.8)` 計算結果
   - BDD-client（若 Active）的 `min_scenario_count` 欄填入 `ceil(${_US_COUNT} × 0.6)` 計算結果
   - `{{ARCH_LAYER_COUNT_PLUS_2}}` 替換為實際值
   - 其他殘留 placeholder 均替換為對應計算值

6. 輸出至 `docs/MANIFEST.md`（覆蓋舊版，若存在）

---

## Step 7：Quality Gate 自我檢查

生成完成後，對輸出執行以下 6 項自我檢查，任一未通過則自動修正後重新生成：

| 檢查項 | 命令 / 方法 | 通過條件 |
|--------|------------|---------|
| **1. 無殘留 placeholder** | `grep -n '{{' docs/MANIFEST.md` | 輸出為空（無任何 `{{` 殘留） |
| **2. .gendoc-rules/ 完整性** | `ls .gendoc-rules/*.json \| wc -l` | 文件數 = Active Steps Count（每個 active step 均有 rules JSON） |
| **3. 量化錨點非零** | 檢查 MANIFEST.md §2.1 四個錨點值 | 四個值均為正整數（非 0，除非上游文件確實為空） |
| **4. 條件步驟一致性** | 比對 §2.2 表格與 pipeline.json 條件邏輯 | 所有 Y/N 判斷符合 Step 3 的條件邏輯 |
| **5. rules JSON 語法正確** | `for f in .gendoc-rules/*.json; do jq . "$f" > /dev/null; done` | 所有 JSON 語法合法（jq 無 parse error） |
| **6. 上游文件完整性** | 確認 §2.1 四個錨點值 | 若 entity_count=0 或 user_story_count=0，MANIFEST.md §2.1 對應欄位含 WARNING 標注（非靜默輸出 0） |

若檢查項 1 失敗（發現殘留 placeholder），必須逐行修正後重新生成，不得跳過。
若檢查項 5 失敗（JSON 語法錯誤），必須修正對應的 rules JSON 文件。

---

## Quality Gate（最終驗收標準）

| 驗收項 | 標準 |
|--------|------|
| docs/MANIFEST.md 存在 | 文件存在且可讀取 |
| 無殘留 placeholder | `grep -c '{{' docs/MANIFEST.md` = 0 |
| .gendoc-rules/ 完整 | Active step 數 = rules JSON 文件數 |
| 量化錨點已計算 | entity_count + rest_endpoint_count + user_story_count + arch_layer_count 均為有效正整數 |
| rules JSON 合法 | 所有 .gendoc-rules/*.json 通過 `jq .` 語法驗證 |
