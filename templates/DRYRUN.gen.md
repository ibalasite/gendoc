---
doc-type: DRYRUN
version: 1.0.0
description: Pipeline Execution Manifest 生成規則 — 在所有文件生成之前執行，計算量化錨點、決定條件步驟、並為每個 active step 生成對應的 rules JSON
expert-roles:
  - Pipeline Analyst：讀取 pipeline.json 和 state 文件，決定哪些步驟啟用、哪些跳過
  - Quantitative Rules Architect：從上游文件計算量化錨點，推導每個步驟的最低品質門檻
allowed-tools:
  - Read
  - Write
  - Bash
upstream-docs:
  input-files: templates/pipeline.json input[] array (DRYRUN step)
  description: |
    DRYRUN step's input[] array in pipeline.json specifies which DRYRUN 前的 step files
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

### 1-A. 初始化環境變數（載入 gendoc 運行路徑）

```bash
# 載入 gendoc 環境變數，設定 GENDOC_TOOLS 等路徑
source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

# 驗證 GENDOC_TOOLS 已設定
if [[ -z "$GENDOC_TOOLS" ]]; then
  echo "ERROR: GENDOC_TOOLS not set" >&2
  exit 1
fi
```

### 1-B. 呼叫 get-upstream 讀取 DRYRUN 的 input 檔案

```bash
# 呼叫 $GENDOC_TOOLS/get-upstream.sh 讀取 DRYRUN step 定義的所有 input 檔案
# 返回 JSON：{"step": "DRYRUN", "timestamp": "...", "inputs": {"docs/IDEA.md": "content", ...}}
_UPSTREAM_JSON=$("$GENDOC_TOOLS/get-upstream.sh" --step DRYRUN --output json 2>&1)

if [[ $? -ne 0 ]]; then
  echo "ERROR: get-upstream failed with:"
  echo "$_UPSTREAM_JSON" >&2
  exit 1
fi
```

### 1-C. 驗證 get-upstream 成功

```bash
# 驗證 get-upstream 返回的 JSON 格式正確
python3 << 'VERIFY_EOF'
import json
import sys

try:
    data = json.loads("""$_UPSTREAM_JSON""")
    inputs = data.get('inputs', {})
    print(f"✅ get-upstream 返回成功，讀取 {len(inputs)} 個檔案")
    for fname in inputs.keys():
        print(f"   - {fname}")
except Exception as e:
    print(f"❌ JSON 解析失敗：{e}", file=sys.stderr)
    sys.exit(1)
VERIFY_EOF
```

> **設計說明**：
> - 檔案清單（input[]）由 pipeline.json DRYRUN step 定義，是單一真相來源
> - get-upstream 工具負責讀取檔案並返回 JSON
> - 後續計算由 dryrun_core.py 統一執行（見 Step 6）
> - DRYRUN 不執行上游衝突偵測；若存在矛盾，由各自的 review 步驟處理

---

## Step 2：量化錨點計算與規格推導（由 dryrun_core.py 執行）

**步驟說明**：所有量化計算、條件判斷、rules JSON 生成均由 dryrun_core.py 完成，包括：
- Step 2 中的四個量化錨點計算（entity_count, rest_endpoint_count, user_story_count, arch_layer_count）
- Step 3 中的 Active / Skipped 步驟決定（依 pipeline.json 條件邏輯）
- Step 4 中的 .gendoc-rules/ 目錄與 rules JSON 生成
- Step 5 中的量化規則公式套用

dryrun_core.py 實現細節詳見 `tools/bin/dryrun_core.py` 源代碼。本 .gen.md 檔案在 Step 6 呼叫該核心引擎。

---

## Step 6：調用 dryrun_core.py 生成規格（核心執行）

**目的**：執行 dryrun_core.py 完成以下核心任務：
1. 重新讀取 get-upstream 的輸出
2. 提取四個量化錨點（entity_count, rest_endpoint_count, user_story_count, arch_layer_count）
3. 依 pipeline.json 的 spec_rules 推導每個 active step 的量化門檻
4. 生成 `.gendoc-rules/*.json` 文件
5. 生成 `docs/MANIFEST.md` 並填入所有計算值

```bash
# 調用 dryrun_core.py（使用 GENDOC_TOOLS 路徑）
# dryrun_core.py 期望當前目錄（target project）作為第一個位置參數
# 以及 state file 路徑作為第二個位置參數
STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1)

if [[ -z "$STATE_FILE" ]]; then
  echo "ERROR: .gendoc-state-*.json not found in current directory" >&2
  exit 1
fi

python3 "$GENDOC_TOOLS/dryrun_core.py" "$(pwd)" "$STATE_FILE" 2>&1

if [[ $? -ne 0 ]]; then
  echo "ERROR: dryrun_core.py execution failed" >&2
  exit 1
fi

echo "✅ dryrun_core.py 執行完成"
```

**檢查輸出**：
- `docs/MANIFEST.md` 應已生成
- `.gendoc-rules/` 目錄應含多個 `<step-id>-rules.json`

---

## Step 3：舊步驟參考（已由 dryrun_core.py 統一執行）

以下舊步驟已由 dryrun_core.py 統一執行，本文件保留作為參考文檔：
- 舊 Step 2：量化錨點計算（entity_count, rest_endpoint_count 等）
- 舊 Step 3：Active / Skipped 步驟決定
- 舊 Step 4：.gendoc-rules/ 生成
- 舊 Step 5：量化規則公式套用
- 舊 Step 6：MANIFEST.md 生成

---

##
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

## Step 6：調用 dryrun_core.py 生成規格（核心執行）

**目的**：執行 dryrun_core.py 完成以下核心任務：
1. 重新讀取 get-upstream 的輸出
2. 提取四個量化錨點（entity_count, rest_endpoint_count, user_story_count, arch_layer_count）
3. 依 pipeline.json 的 spec_rules 推導每個 active step 的量化門檻
4. 生成 `.gendoc-rules/*.json` 文件
5. 生成 `docs/MANIFEST.md` 並填入所有計算值

```bash
# 調用 dryrun_core.py（使用 GENDOC_TOOLS 路徑）
# dryrun_core.py 期望當前目錄（target project）作為第一個位置參數
# 以及 state file 路徑作為第二個位置參數
STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1)

if [[ -z "$STATE_FILE" ]]; then
  echo "ERROR: .gendoc-state-*.json not found in current directory" >&2
  exit 1
fi

python3 "$GENDOC_TOOLS/dryrun_core.py" "$(pwd)" "$STATE_FILE" 2>&1

if [[ $? -ne 0 ]]; then
  echo "ERROR: dryrun_core.py execution failed" >&2
  exit 1
fi

echo "✅ dryrun_core.py 執行完成"
```

**檢查輸出**：
- `docs/MANIFEST.md` 應已生成
- `.gendoc-rules/` 目錄應含多個 `<step-id>-rules.json`

---

## Step 4：Quality Gate 自我檢查

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
