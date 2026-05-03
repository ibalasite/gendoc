# gendoc DRYRUN 規格推導引擎 進度追蹤

**目標**：實現 Phase A → Phase B 的統一量化檢查框架，每個 Phase B step 的 review 環節由 AI Finding + Shell Finding（來自 DRYRUN 規格）合併驅動。

**總步驟數**：17 個實現任務 + 5 個測試驗證 = 22 個

**狀態**：進行中 🔄

---

## 整體架構圖

```
Phase A 完成（IDEA~ARCH）
    ↓
gendoc-gen-dryrun skill（TASK-D1～D5）
├─ Step 1：結構化讀取 + 計算 20 個量化指標
├─ Step 2：推導 31 個 step 的規格邏輯
├─ Step 3：驗證完整性
├─ Step 4：生成 MANIFEST.md
└─ Step 5：提交 state file（無檔案污染）
    ↓
Phase B 執行（API~HTML）
    ↓
每個 STEP 的 Review（TASK-F1～F4）
├─ AI Review → AI Finding
├─ review.sh（~/.claude/tools/bin/）→ Shell Finding
├─ Merge Findings → Combined Finding
└─ AI Fix based on Combined Finding
```

---

## TASK-D：DRYRUN 核心實現（5 步驟）

### TASK-D1：DRYRUN Step 1 — 結構化讀取 + 量化計算

**目標**：讀取 IDEA ~ ARCH 8 份文件，提取 20 個量化指標

**實現內容**（完成）：
- ✅ Python 實現：`skills/gendoc-gen-dryrun/dryrun_core.py` (DRYRUNEngine 類)
- ✅ 讀取並 grep 提取所有 20 個指標：
  - IDEA.md：persona_count
  - BRD.md：moscow_p0_count、kpi_count
  - PRD.md：user_story_count、feature_count、use_case_count、total_ac_count
  - CONSTANTS.md：constant_count
  - PDD.md：screen_count、flow_count、total_component_count
  - VDD.md：design_token_count、color_count
  - EDD.md：entity_count、relationship_count、rest_endpoint_count、domain_count
  - ARCH.md：layer_count、service_count、nfr_count
- ✅ 構建內存 JSON 結構，無文件輸出

**驗收標準**：
- ✅ 所有 20 個指標正確提取（slot 項目驗證通過）
- ✅ grep 邏輯驗證成功（與實際文件內容對齊）
- ✅ 指標結構完整且可序列化

**狀態**：`[x] 已完成` — Commit: 136fd6d

---

### TASK-D2：DRYRUN Step 2 — 規格推導

**目標**：為 31 個後續 step 推導規格邏輯

**實現內容**（完成）：
- ✅ `dryrun_core.py` 的 `derive_specifications()` 方法
- ✅ 為每個 step 計算三層規格：
  - `quantitative_specs`（min_endpoint_count、min_table_count 等）
  - `content_mapping`（entity_coverage、user_story_coverage 等）
  - `cross_file_validation`（entity_parity、endpoint_mapping 等）
- ✅ 規格推導邏輯示例（已實現）：
  - API.min_endpoint_count = max(5, rest_endpoint_count)
  - SCHEMA.min_table_count = max(3, entity_count)
  - FRONTEND.min_component_count = max(3, total_component_count)
  - test-plan.min_h2_sections = layer_count + 4
  - BDD-server.min_scenario_count = ceil(user_story_count × 0.8)

**驗收標準**：
- ✅ 31 個 step 的規格都已推導（slot 驗證：31 steps）
- ✅ 規格邏輯基於 20 個量化指標（與上游文件內容對應）
- ✅ 無遺漏（所有 31 steps 均有三層規格）

**狀態**：`[x] 已完成` — Commit: 136fd6d

---

### TASK-D3：DRYRUN Step 3 — 嵌入 State File

**目標**：將規格邏輯存儲到 `.gendoc-state-*.json` 的 `step_specifications` 欄位

**實現內容**（完成）：
- ✅ `dryrun_core.py` 的 `embed_in_state_file()` 方法
- ✅ 結構化 state file：
  ```json
  {
    "step_specifications": {
      "API": {
        "quantitative_specs": { "min_endpoint_count": 23, ... },
        "content_mapping": { "entity_coverage": "All 26 EDD entities...", ... },
        "cross_file_validation": { "entity_parity": "...", ... }
      },
      "SCHEMA": { ... },
      ... (31 steps)
    },
    "dryrun_metadata": {
      "extraction_timestamp": "2026-05-03T...",
      "extracted_metrics_count": 20,
      "derived_step_specs_count": 31,
      "phase_a_version": "v2.0.0"
    }
  }
  ```
- ✅ 不生成獨立 `.gendoc-specs/` 目錄（零污染）
- ✅ 所有規格嵌入 state file，無分散檔案

**驗收標準**：
- ✅ state file 包含 31 個 step 的完整規格（slot 驗證：31 steps 均已嵌入）
- ✅ JSON 格式驗證通過（Python json.dumps 成功）
- ✅ 無文件污染目標項目（只修改 state file）

**狀態**：`[x] 已完成` — Commit: 136fd6d

---

### TASK-D4：DRYRUN Step 4 — 驗證完整性

**目標**：確認 31 個規格都已計算，無遺漏

**實現內容**：
- 檢查 `step_specifications` 是否包含 31 個 key
- 檢查每個規格是否有 quantitative_specs、content_mapping、cross_file_validation 三部分

**驗收標準**：
- [ ] 所有 31 個 step 都有規格
- [ ] 每個規格都有必要欄位

**狀態**：`[ ] 待實現`

---

### TASK-D5：DRYRUN Step 5 — 生成 MANIFEST.md + 提交

**目標**：生成執行清單，記錄量化基線與工具使用方式

**實現內容**：
- 生成 `docs/MANIFEST.md`（見 PRD §7.7）
- 記錄：
  - §1 量化基線表
  - §2 規格儲存位置
  - §3 review.sh 使用方式（簽名、參數、示例）
  - §4 規格邏輯示例
- Git commit：`gen-dryrun: specification logic embedded in state file`

**驗收標準**：
- [ ] MANIFEST.md 生成正確
- [ ] Git commit 成功

**狀態**：`[ ] 待實現`

---

## TASK-R：review.sh 統一工具實現（6 步驟）

### TASK-R1：review.sh 核心架構

**目標**：實現 ~400 行 parameterized bash 腳本

**位置**：`~/.claude/skills/gendoc/tools/bin/review.sh`（runtime）、`~/projects/gendoc/tools/bin/review.sh`（authority）

**簽名**：
```bash
review.sh --step API --specs-from-state .gendoc-state-*.json --target-file docs/API.md
```

**參數**：
- `--step STEP_ID`（必須）
- `--specs-from-state STATE_FILE`（必須）
- `--target-file TARGET_FILE`（必須）
- `--check MODE`（可選，預設 all）：quantitative / content_mapping / cross_file / all
- `--output-format FORMAT`（可選，預設 json）：json / text
- `--strict`（可選）：warning 視為 error

**實現內容**：
- 參數解析與驗證
- 從 state file 提取該 step 的規格
- 初始化 findings JSON 陣列
- Helper 函數：add_finding、log_*

**驗收標準**：
- [ ] 參數解析完整
- [ ] state file 讀取正確
- [ ] 基礎架構可運行

**狀態**：`[ ] 待實現`

---

### TASK-R2：量化檢查模式實現

**目標**：`--check quantitative` 檢查所有數值型門檻

**實現內容**：
- run_quantitative_checks()：
  - check_quantitative_min_endpoint()
  - check_quantitative_min_table()
  - check_quantitative_min_component()
  - check_quantitative_min_section()
  - check_quantitative_min_entity()
  - （每個 step 類型有對應檢查）
- 每個檢查函數：
  - 從 target file grep 實際數量
  - 與規格比對
  - 生成 finding（若失敗）

**驗收標準**：
- [ ] 至少 5 種量化檢查可運行
- [ ] grep 邏輯正確
- [ ] finding 格式正確

**狀態**：`[ ] 待實現`

---

### TASK-R3：內容映射檢查模式實現

**目標**：`--check content_mapping` 檢查涵蓋範圍

**實現內容**：
- run_content_mapping_checks()：
  - check_entity_endpoint_coverage()
  - check_user_story_traceability()
  - check_constant_usage()
  - （每個 step 類型有對應檢查）
- 邏輯：
  - 從規格讀取應涵蓋的項目清單
  - 檢查 target file 中是否都被提及
  - 計算覆蓋率

**驗收標準**：
- [ ] 至少 3 種內容映射檢查可運行
- [ ] 覆蓋率計算正確

**狀態**：`[ ] 待實現`

---

### TASK-R4：交叉檢查模式實現

**目標**：`--check cross_file` 檢查一致性

**實現內容**：
- run_cross_file_checks()：
  - check_entity_parity()
  - check_relationship_mapping()
  - check_moscow_coverage()
  - （每個 step 類型有對應檢查）
- 邏輯：
  - 驗證相關 step 間的一致性（entity_count、layer_count、us_count 等）

**驗收標準**：
- [ ] 至少 3 種交叉檢查可運行
- [ ] 一致性邏輯正確

**狀態**：`[ ] 待實現`

---

### TASK-R5：Finding 輸出與格式化

**目標**：JSON/text 格式輸出，統一 finding 結構

**實現內容**：
- format_json_output()：完整 finding JSON + summary
- format_text_output()：人類可讀格式
- Finding JSON 結構：
  ```json
  {
    "id": "API-QUANT-001",
    "type": "error",
    "source": "quantitative_check",
    "severity": "critical",
    "message": "...",
    "expected": "...",
    "actual": "...",
    "suggested_fix": "..."
  }
  ```
- Summary 計數：total / critical / high / medium / low / pass / fail

**驗收標準**：
- [ ] JSON 格式符合規範
- [ ] text 格式可讀
- [ ] summary 計數正確

**狀態**：`[ ] 待實現`

---

### TASK-R6：review.sh 測試與部署

**目標**：review.sh 可執行、所有模式可測試

**實現內容**：
- 在 DRYRUN 後自動測試 review.sh：
  ```bash
  ~/.claude/skills/gendoc/tools/bin/review.sh --step API \
    --specs-from-state .gendoc-state-*.json \
    --target-file docs/API.md \
    --check all --output-format json
  ```
- 驗證輸出是否正確 JSON

**驗收標準**：
- [ ] review.sh 可成功運行
- [ ] 輸出格式正確
- [ ] 無 runtime error

**狀態**：`[ ] 待實現`

---

## TASK-F：gendoc-flow 整合（4 步驟）

### TASK-F1：修改 review 步驟調用 review.sh

**目標**：gendoc-flow 的 review 環節調用 review.sh 並捕獲 shell finding

**實現內容**：
- 修改 `skills/gendoc-flow/SKILL.md` Step 的 review 邏輯：
  ```bash
  _REVIEW_TOOL="${HOME}/.claude/skills/gendoc/tools/bin/review.sh"
  
  _SHELL_FINDINGS=$("$_REVIEW_TOOL" \
    --step "$_STEP_ID" \
    --specs-from-state "$_STATE_FILE" \
    --target-file "$_OUTPUT_FILE" \
    --output-format json)
  ```
- 檢查 review.sh 是否存在（若不存在，skip shell finding）

**驗收標準**：
- [ ] review.sh 成功調用
- [ ] 捕獲 shell finding JSON
- [ ] 無 runtime error

**狀態**：`[ ] 待實現`

---

### TASK-F2：實現 Finding 合併邏輯

**目標**：AI Finding + Shell Finding → Combined Finding List

**實現內容**：
- merge_findings()：
  - 輸入：AI finding list + shell finding list
  - 去重（相同 id 只保留一份，若重複則保留 severity 更高的）
  - 排序（按 severity：critical → high → medium → low）
  - 輸出：Combined Finding List
- 合併後的 finding 格式保持統一

**驗收標準**：
- [ ] 去重邏輯正確
- [ ] 排序邏輯正確
- [ ] 輸出 finding list 可被 AI fix 使用

**狀態**：`[ ] 待實現`

---

### TASK-F3：修改 AI Fix 使用合併 Finding

**目標**：AI fix 接收 Combined Finding List 作為修復指導

**實現內容**：
- 修改 AI fix 的 prompt，包含合併的 finding list：
  ```
  You have the following issues to fix:
  
  CRITICAL:
  - API-QUANT-001: endpoint count insufficient...
  
  HIGH:
  - API-CONTENT-001: Entity coverage incomplete...
  
  Fix all CRITICAL and HIGH findings.
  Reference the evidence in each finding.
  ```
- AI 同時考慮 AI review 建議與量化要求

**驗收標準**：
- [ ] AI fix prompt 包含 combined finding
- [ ] AI 能理解並執行修復

**狀態**：`[ ] 待實現`

---

### TASK-F4：修改 gate-check 邏輯

**目標**：gate-check 判斷基於 combined finding 的 severity

**實現內容**：
- gate-check 邏輯：
  ```bash
  _CRITICAL_COUNT=$(echo "$_MERGED_FINDINGS" | jq '[.[] | select(.severity=="critical")] | length')
  _HIGH_COUNT=$(echo "$_MERGED_FINDINGS" | jq '[.[] | select(.severity=="high")] | length')
  
  if (( _CRITICAL_COUNT > 0 || _HIGH_COUNT > 0 )); then
    return "BLOCKED"  # 觸發 AI fix
  else
    return "PASS"     # 步驟通過
  fi
  ```

**驗收標準**：
- [ ] gate-check 邏輯正確
- [ ] BLOCKED / PASS 決策正確
- [ ] 能正確觸發 AI fix 或通過

**狀態**：`[ ] 待實現`

---

## TASK-T：測試與驗證（5 步驟）

### TASK-T1：DRYRUN 單元測試

**目標**：驗證 DRYRUN 5 步驟各項正確

**測試內容**：
- Test-D1：量化指標提取正確性（與實際文件對比）
- Test-D2：規格推導邏輯正確性（31 個 step 規格都符合預期）
- Test-D3：完整性驗證正確性
- Test-D4：MANIFEST.md 生成正確性
- Test-D5：state file 結構正確性

**驗收標準**：
- [ ] 所有 5 項測試通過

**狀態**：`[ ] 待實現`

---

### TASK-T2：review.sh 功能測試

**目標**：驗證 review.sh 各檢查模式正確

**測試內容**：
- Test-R1：quantitative 模式（5+ 種檢查）
- Test-R2：content_mapping 模式（3+ 種檢查）
- Test-R3：cross_file 模式（3+ 種檢查）
- Test-R4：all 模式（所有檢查）
- Test-R5：JSON/text 輸出格式
- Test-R6：finding 結構正確性

**驗收標準**：
- [ ] 所有 6 項功能測試通過

**狀態**：`[ ] 待實現`

---

### TASK-T3：gendoc-flow 整合測試

**目標**：驗證 gendoc-flow 的 review 環節完整流程

**測試內容**：
- Test-F1：review.sh 調用成功
- Test-F2：AI finding + shell finding 合併正確
- Test-F3：gate-check 決策正確
- Test-F4：AI fix 基於 combined finding 執行

**驗收標準**：
- [ ] 所有 4 項整合測試通過

**狀態**：`[ ] 待實現`

---

### TASK-T4：端到端測試（完整 Phase B 執行）

**目標**：整個 Phase B（API~HTML）執行，驗證每個 step 的雙層檢查生效

**測試場景**：
- 建立測試項目（含完整 Phase A 輸出）
- 執行 DRYRUN，生成規格
- 執行 gendoc-flow Phase B
- 驗證每個 step 都有 AI + Shell finding
- 驗證 AI fix 基於合併 finding 修復成功

**驗收標準**：
- [ ] Phase B 完整執行
- [ ] 每個 step 都有雙層檢查
- [ ] finding 合併正確
- [ ] AI fix 成功

**狀態**：`[ ] 待實現`

---

### TASK-T5：回歸測試（現有功能不破壞）

**目標**：驗證 DRYRUN 與 gendoc-flow 改動不破壞現有功能

**測試內容**：
- 沒有 DRYRUN 規格的舊項目（.gendoc-state-*.json 無 step_specifications）仍可運行
- review.sh 不存在時 gendoc-flow 仍可運行（skip shell finding）
- 現有文件生成邏輯不變

**驗收標準**：
- [ ] 向後相容性通過

**狀態**：`[ ] 待實現`

---

## 整體進度面板

| Task ID | 任務 | 狀態 | 開始日期 | 完成日期 |
|---------|------|------|--------|--------|
| TASK-D1 | DRYRUN Step 1：量化計算 | `[ ] 待` | — | — |
| TASK-D2 | DRYRUN Step 2：規格推導 | `[ ] 待` | — | — |
| TASK-D3 | DRYRUN Step 3：嵌入 state | `[ ] 待` | — | — |
| TASK-D4 | DRYRUN Step 4：驗證完整性 | `[ ] 待` | — | — |
| TASK-D5 | DRYRUN Step 5：生成 MANIFEST | `[ ] 待` | — | — |
| TASK-R1 | review.sh 核心架構 | `[ ] 待` | — | — |
| TASK-R2 | review.sh 量化檢查 | `[ ] 待` | — | — |
| TASK-R3 | review.sh 內容映射 | `[ ] 待` | — | — |
| TASK-R4 | review.sh 交叉檢查 | `[ ] 待` | — | — |
| TASK-R5 | review.sh finding 輸出 | `[ ] 待` | — | — |
| TASK-R6 | review.sh 測試與部署 | `[ ] 待` | — | — |
| TASK-F1 | gendoc-flow 調用 review.sh | `[ ] 待` | — | — |
| TASK-F2 | Finding 合併邏輯 | `[ ] 待` | — | — |
| TASK-F3 | AI fix 使用合併 finding | `[ ] 待` | — | — |
| TASK-F4 | gate-check 邏輯改造 | `[ ] 待` | — | — |
| TASK-T1 | DRYRUN 單元測試 | `[ ] 待` | — | — |
| TASK-T2 | review.sh 功能測試 | `[ ] 待` | — | — |
| TASK-T3 | gendoc-flow 整合測試 | `[ ] 待` | — | — |
| TASK-T4 | 端到端測試 | `[ ] 待` | — | — |
| TASK-T5 | 回歸測試 | `[ ] 待` | — | — |

---

## 實現順序建議

**依賴關係**：
```
TASK-D1 → TASK-D2 → TASK-D3 → TASK-D4 → TASK-D5
(並行) TASK-R1 → TASK-R2/R3/R4 → TASK-R5 → TASK-R6
(並行) TASK-F1 → TASK-F2 → TASK-F3 → TASK-F4
                                            ↓
                            TASK-T1/T2/T3/T4/T5
```

**建議實施順序**（按依賴關係平行化）：

1. **第 1 週**：TASK-D1～D5（DRYRUN 核心）+ TASK-R1（review.sh 架構）
2. **第 2 週**：TASK-R2～R6（review.sh 實現）+ TASK-F1（gendoc-flow 調用）
3. **第 3 週**：TASK-F2～F4（gendoc-flow 整合）+ TASK-T1（DRYRUN 測試）
4. **第 4 週**：TASK-T2～T5（全面測試）

---

## 重要設計決策

- **不生成 31 個獨立 shell script**：改為一個統一的 review.sh，參數化傳遞規格
- **規格存儲在 state file 中**：無 .gendoc-specs/ 目錄，不污染目標項目
- **tools/bin/review.sh 從 runtime 調用**：所有工具在 ~/.claude/ 中，項目邊界明確
- **雙層檢查合併**：AI finding + shell finding 在 gendoc-flow 中合併，供 AI fix 使用

---

**最後更新**：2026-05-03  
**下次更新預計**：第一個 TASK 完成時
