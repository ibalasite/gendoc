---
title: gendoc 開發進度追蹤
date: 2026-05-04
version: 1.0
---

# gendoc 開發進度追蹤

## 最近完成（2026-05-04）

### Pipeline.json 結構化修正
- ✅ **input/output 完整性驗證**（Commit f2104c2）
  - 修復 9 個 step 的 input[] 定義
  - 修復 1 個 step 的 output[] 定義（DRYRUN）
  - 與 29 個 .gen.md 檔案對比驗證

- ✅ **Layer 分類與 Note 規範化**（Commit 51ecb59）
  - VDD：設計層 → 需求層（符合實際職責）
  - HTML：稽核層 → 輸出層（符合執行順序）
  - 精簡所有 notes，移除重複敘述

- ✅ **ALIGN 的 input[] 關鍵修正**（Commit e4daa6e）
  - ALIGN/ALIGN-FIX/ALIGN-VERIFY：擴展 input[] 為完整上游清單
  - 解決「只讀三個文件」導致全局對齐檢查不完整的問題

### 設計文件
- ✅ **PIPELINE_INPUT_VALIDATION_REPORT.md**：完整的 input/output 對比分析
- ✅ **PIPELINE_LAYER_CLASSIFICATION_NOTES.md**：layer 調整說明與 PRD 對應
- ✅ **DRYRUN_CORE_IMPLEMENTATION_PLAN.md**：DRYRUN 雙層驗證架構 + 6 個實作 STEP
- ✅ **PRD §7.7**：完整改寫 DRYRUN 設計（雙層獨立驗證）

---

## 進行中 → 下一步（D-SSOT-4.X 系列）

### D-SSOT-4.1：DRYRUN 核心實作
**目標**：完成 dryrun_core.py，實現雙層獨立驗證

**STEP 分解**（per DRYRUN_CORE_IMPLEMENTATION_PLAN.md）：
1. [✅] **參數提取規則設計**（1 小時）
   - 定義 entity_count、rest_endpoint_count、user_story_count、arch_layer_count 提取方法
   - 輸出：`docs/DRYRUN_PARAMETER_EXTRACTION.md`（已完成）

2. [✅] **規格推導公式設計**（2 小時）
   - 定義所有 Phase B steps 的期望規格公式
   - 輸出：`docs/DRYRUN_SPEC_FORMULAS.md`（已完成）

3. [✅] **實現 dryrun_core.py**（3 小時）
   - `_load_upstream()`：調用 get-upstream（已實現）
   - `extract_parameters()`：提取 4 個核心參數（已實現）
   - `derive_specifications()`：推導期望規格（已實現）
   - `generate_rules_json()`：輸出 .gendoc-rules/*.json（已實現）
   - `main()` 流程：更新執行流程（已實現）

4. [ ] **全專案 hardcoded 規格掃描**（1 小時）
   - 掃描 skills/ 和 templates/ 中的 hardcoded 規格定義
   - 輸出：`docs/HARDCODED_SPECS_AUDIT.md`

5. [ ] **修正 hardcoded 規格**（2 小時）
   - 將所有 hardcoded 值改為讀 DRYRUN 輸出 或 pipeline.json
   - 確保所有 step 不自行定義最小值

6. [ ] **實現審查工具 review.sh**（2 小時）
   - 機械式對比：期望（.gendoc-rules/) vs 實際（docs/）
   - 輸出：PASS / FAIL 報告

**預計完成**：12 小時（~1-2 個工作日）

### D-SSOT-4.2：get-upstream 工具驗證
- [ ] 測試 get-upstream 對修正後 pipeline.json input[] 的讀取
- [ ] 確認返回的 JSON 包含所有必要文件

### D-SSOT-4.3：dryrun_core.py 全迴歸測試
- [ ] 用一個實際專案跑完整流程：DRYRUN → Phase B → review.sh
- [ ] 驗證期望 vs 實際一致性

---

## PRD 清理項目（後續）

PRD 中仍存在關於「metrics[] 在 pipeline.json」的舊說法，需要後續清理：

| 位置 | 舊說法 | 改正 |
|------|--------|------|
| v3.4 變更記錄 | metrics[] 在 pipeline.json | metrics 只在 dryrun_core.py |
| §7.7 Input 段落 | 列出 metrics[] JSON 結構 | 改為只列 input[] 和 output[] |
| 新增節點工作流 | 「新增 metrics[]」 | 改為「DRYRUN 自動推導」 |
| 檢查清單 | pipeline.json metrics 驗證 | 改為 DRYRUN 輸出驗證 |

**優先度**：低（核心設計已改正，文字清理可後續完成）

---

## 已知限制與設計決策

### 設計決策 1：metrics 位置
- ✅ **已確認**：metrics 提取規則在 dryrun_core.py 中（不在 pipeline.json）
- **理由**：DRYRUN 推導邏輯獨立於 pipeline.json，確保設計清晰

### 設計決策 2：雙層驗證
- ✅ **已確認**：上游推導 + 下游實現 + 審查對比
- **理由**：同一數字來自兩條獨立路徑，能發現問題

### 設計決策 3：audit layer 例外
- ✅ **已確認**：ALIGN/ALIGN-FIX/ALIGN-VERIFY/HTML 不需推導規格
- **理由**：這些 steps 的職責是審查或發布，無「內容規格」

---

## 檔案清單

| 檔案 | 狀態 | 備註 |
|------|------|------|
| `templates/pipeline.json` | ✅ 完成 | 34 steps，input/output/layer/note 完整 |
| `docs/PIPELINE_INPUT_VALIDATION_REPORT.md` | ✅ 完成 | 驗證報告 |
| `docs/PIPELINE_LAYER_CLASSIFICATION_NOTES.md` | ✅ 完成 | layer 調整說明 |
| `docs/DRYRUN_CORE_IMPLEMENTATION_PLAN.md` | ✅ 完成 | 6 step 實作計畫 |
| `docs/PRD.md §7.7` | ✅ 完成 | 新設計改寫 |
| `docs/DRYRUN_PARAMETER_EXTRACTION.md` | ⏳ 待實現 | D-SSOT-4.1 STEP 1 |
| `docs/DRYRUN_SPEC_FORMULAS.md` | ⏳ 待實現 | D-SSOT-4.1 STEP 2 |
| `tools/bin/dryrun_core.py` | 🔧 部分完成 | 需完成 extract_parameters() 等 |
| `docs/HARDCODED_SPECS_AUDIT.md` | ⏳ 待實現 | D-SSOT-4.1 STEP 4 |
| `tools/bin/review.sh` | ⏳ 待實現 | D-SSOT-4.1 STEP 6 |

---

## 關鍵里程碑

| 里程碑 | 狀態 | 日期 |
|--------|------|------|
| Pipeline.json 結構驗證完成 | ✅ | 2026-05-04 |
| DRYRUN 設計確認（雙層驗證） | ✅ | 2026-05-04 |
| DRYRUN core 實作完成 | ⏳ | ~2026-05-05 |
| 全專案 hardcoded 規格修正完成 | ⏳ | ~2026-05-05 |
| 審查工具實現完成 | ⏳ | ~2026-05-06 |
| 全迴歸測試通過 | ⏳ | ~2026-05-06 |

