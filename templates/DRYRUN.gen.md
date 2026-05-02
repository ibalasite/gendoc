---
doc-type: DRYRUN
version: 1.0.0
description: Pipeline Execution Manifest 生成規則 — 在所有文件生成之前執行，計算量化錨點、決定條件步驟、並為每個 active step 生成對應的 rules JSON
expert-roles:
  - Pipeline Analyst：讀取 pipeline.json 和 state 文件，決定哪些步驟啟用、哪些跳過
  - Quantitative Rules Architect：從上游文件計算量化錨點，推導每個步驟的最低品質門檻
upstream-docs:
  required:
    - docs/EDD.md       # 計算 entity_count 和 rest_endpoint_count
    - docs/PRD.md       # 計算 user_story_count
    - docs/ARCH.md      # 計算 arch_layer_count
  also-read:
    - templates/pipeline.json    # 步驟清單與條件定義
    - .gendoc-state.json         # client_type、has_admin_backend 等 session config
quality-bar:
  - docs/MANIFEST.md 已生成，所有 {{PLACEHOLDER}} 均已替換（無殘留 placeholder）
  - .gendoc-rules/ 目錄已建立，每個 active step 均有對應的 <step-id>-rules.json
  - 量化錨點（entity_count / rest_endpoint_count / user_story_count / arch_layer_count）均為真實計算值（非預設值 0）
  - Active / Skipped 步驟清單與 pipeline.json 條件邏輯完全一致
  - 所有 rules JSON 的量化門檻公式已套用錨點數值（非 {{PLACEHOLDER}}）
---

# DRYRUN 生成規則

## Iron Rule：流水線前置執行

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

## Step 1：讀取上游文件

依序讀取以下文件（若不存在則靜默跳過，但必須在日誌中記錄缺失）：

```
1. docs/EDD.md        — 提取 entity_count 和 rest_endpoint_count
2. docs/PRD.md        — 提取 user_story_count
3. docs/ARCH.md       — 提取 arch_layer_count
4. templates/pipeline.json  — 提取步驟清單與條件定義
5. .gendoc-state.json       — 提取 client_type 和 has_admin_backend
```

若 `docs/EDD.md` 不存在，`entity_count` 和 `rest_endpoint_count` 使用預設值 0，並在 MANIFEST.md 的對應欄位標注 `（EDD 尚未生成，請重新執行 DRYRUN）`。

---

## Step 2：計算量化錨點（bash 命令）

以下命令在目標專案根目錄執行，計算 §2.1 System Parameters 的四個量化錨點。

### 2-A. entity_count（EDD classDiagram 中的 class 數量）

```bash
_ENTITY_COUNT=$(grep -c '^\s*class ' docs/EDD.md 2>/dev/null || echo 0)
echo "entity_count=${_ENTITY_COUNT}"
```

> 計算 `docs/EDD.md` 中所有以 `class ` 開頭的行（含前導空白），對應 Mermaid classDiagram 的 entity 定義。

---

### 2-B. rest_endpoint_count（REST 端點數量）

```bash
_REST_COUNT=$(grep -cE '(<<REST>>|<<Interface>>|HTTP[[:space:]]*(GET|POST|PUT|DELETE|PATCH))' docs/EDD.md 2>/dev/null || echo 0)
# 若計算結果 < 5，使用 fallback 值 10（避免過低的門檻無意義）
if [ "${_REST_COUNT}" -lt 5 ]; then _REST_COUNT=10; fi
echo "rest_endpoint_count=${_REST_COUNT}"
```

> 優先比對 `<<REST>>`、`<<Interface>>`、`HTTP GET/POST/PUT/DELETE/PATCH` 等標記。若比對結果過少（< 5），代表 EDD 尚未完整定義 REST 介面，改用保守預設值 10。

---

### 2-C. user_story_count（PRD User Story 數量）

```bash
_US_COUNT=$(grep -c '^## US-\|^### US-' docs/PRD.md 2>/dev/null || echo 0)
echo "user_story_count=${_US_COUNT}"
```

> 計算 `docs/PRD.md` 中所有以 `## US-` 或 `### US-` 開頭的標題，對應 PRD 的 User Story ID 命名規範。

---

### 2-D. arch_layer_count（ARCH Tech Stack 層數）

```bash
# 取 ARCH.md §3 Tech Stack 表格的非標頭列數（最小值 4）
_ARCH_LAYER_COUNT=$(awk '/## §3|^## 3 |^# §3/{found=1} found && /^\|[^-]/{count++} END{print (count<4)?4:count}' docs/ARCH.md 2>/dev/null || echo 4)
echo "arch_layer_count=${_ARCH_LAYER_COUNT}"
```

> 掃描 ARCH.md §3 附近的 Markdown 表格，計算非標頭列（即非 `|---|` 分隔列）的數量，代表技術棧的分層數。若文件不存在或解析失敗，使用最小值 4（Presentation / Application / Domain / Infrastructure）。

---

### 2-E. client_type 和 has_admin_backend（從 state 文件讀取）

```bash
_CLIENT_TYPE=$(jq -r '.client_type // "api-only"' .gendoc-state.json 2>/dev/null || echo "api-only")
_HAS_ADMIN=$(jq -r '.has_admin_backend // "false"' .gendoc-state.json 2>/dev/null || echo "false")
echo "client_type=${_CLIENT_TYPE}"
echo "has_admin_backend=${_HAS_ADMIN}"
```

> 若 `.gendoc-state.json` 不存在，使用最保守的預設值：`client_type=api-only`、`has_admin_backend=false`。

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
      "no_bare_placeholders": true
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

### 所有其他步驟（未列出的 always 步驟）

```
min_h2_sections   = 3
  # 最低預設值，確保文件有實質章節結構
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

4. 更新 §4 Per-Step Completeness Standards 表格的量化欄位：
   - API 的 `min_endpoint_count` 欄填入 `max(${_REST_COUNT}, 5)` 計算結果
   - SCHEMA 的 `min_table_count` 欄填入 `max(${_ENTITY_COUNT}, 3)` 計算結果
   - test-plan 的 `min_h2_sections` 欄填入 `${_ARCH_LAYER_COUNT} + 2` 計算結果
   - RTM 的 `min_row_count` 欄填入 `${_US_COUNT}` 值
   - BDD-server 的 `min_scenario_count` 欄填入 `ceil(${_US_COUNT} × 0.8)` 計算結果
   - `{{ARCH_LAYER_COUNT_PLUS_2}}` 替換為實際值
   - 其他殘留 placeholder 均替換為對應計算值

5. 輸出至 `docs/MANIFEST.md`（覆蓋舊版，若存在）

---

## Step 7：Quality Gate 自我檢查

生成完成後，對輸出執行以下 5 項自我檢查，任一未通過則自動修正後重新生成：

| 檢查項 | 命令 / 方法 | 通過條件 |
|--------|------------|---------|
| **1. 無殘留 placeholder** | `grep -n '{{' docs/MANIFEST.md` | 輸出為空（無任何 `{{` 殘留） |
| **2. .gendoc-rules/ 完整性** | `ls .gendoc-rules/*.json \| wc -l` | 文件數 = Active Steps Count（每個 active step 均有 rules JSON） |
| **3. 量化錨點非零** | 檢查 MANIFEST.md §2.1 四個錨點值 | 四個值均為正整數（非 0，除非上游文件確實為空） |
| **4. 條件步驟一致性** | 比對 §2.2 表格與 pipeline.json 條件邏輯 | 所有 Y/N 判斷符合 Step 3 的條件邏輯 |
| **5. rules JSON 語法正確** | `for f in .gendoc-rules/*.json; do jq . "$f" > /dev/null; done` | 所有 JSON 語法合法（jq 無 parse error） |

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
