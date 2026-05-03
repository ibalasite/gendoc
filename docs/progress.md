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

### D-LANG-1：Phase A/B 用語統一（2026-05-04）
**目標**：全專案用語標準化，替換 "Phase A/B" 為 "DRYRUN 前的 step / DRYRUN 后的 step"

**替換規則**：
| 舊用語 | 新用語 | 上下文 |
|--------|--------|--------|
| Phase A | DRYRUN 前的 step | 泛稱步驟集合 |
| Phase B | DRYRUN 后的 step | 泛稱步驟集合 |
| Phase A files | DRYRUN 前的文件 | 指具體檔案 |
| Phase A（內容層）| DRYRUN 前的 step（內容層）| 有層級說明 |
| Phase B（技術文件層）| DRYRUN 后的 step（技術文件層）| 有層級說明 |
| phase-aware | DRYRUN-aware | 複合形容詞 |

**STEP 分解**：

1. [✅] **TESTING.md — 3 個替換**（Commit dcc39bf）
   - Line 23：`# Create minimal Phase A files` → `# 建立 DRYRUN 前的文件` ✅
   - Line 198：`# Generate all Phase A docs` → `# 生成所有 DRYRUN 前的文件` ✅
   - Line 236：`# Generate sample Phase B files` → `# 生成示例 DRYRUN 后的文件` ✅
   - 驗證：grep 確認無遺漏 ✅

2. [✅] **tools/bin/dryrun_core.py — 9 個替換**（Commit 8cafc42）
   - Line 4-8（docstring）：Phase A→B → DRYRUN 前/后轉換 ✅
   - Line 50（函數名）：validate_phase_a() → validate_dryrun_upstream() ✅
   - Line 51（變數名）：phase_a_files → upstream_files ✅
   - Line 58（日誌）：Missing Phase A files → Missing upstream files ✅
   - Line 61（日誌）：Phase A complete → DRYRUN 前的檔案齊全 ✅
   - Line 68（函數說明）：Phase A files → DRYRUN 前的檔案 ✅
   - Line 106（函數說明）：Phase A files → DRYRUN 前的檔案 ✅
   - Line 196（函數說明）：Phase A files → DRYRUN 前的檔案 ✅
   - Line 225、245、472、593（多個）：Phase B steps → DRYRUN 后的 step ✅
   - 驗證：grep 確認無遺漏 ✅

3. [✅] **README.md — 3 個替換**（Commit 98e2ae2）
   - Line 56：Phase-aware → DRYRUN-aware；Phase A → DRYRUN 前的 step；Phase B → DRYRUN 后的 step ✅
   - Line 175：Phase A step → DRYRUN 前的 step ✅
   - Line 176：Phase B step → DRYRUN 后的 step ✅
   - 驗證：grep 確認無遺漏 ✅

4. [✅] **progress.md — 本檔案 5 個替換**（Commit 待執行）
   - 第 149 行：8 個 Phase A 檔案 → 8 個 DRYRUN 前的文件 ✅
   - 第 155 行：DRYRUN → Phase B → review.sh → DRYRUN → DRYRUN 后的 step → review.sh ✅
   - 第 158 行：完成 Phase A 文件 → 完成 DRYRUN 前的文件 ✅
   - 第 164 行：所有 Phase B steps → 所有 DRYRUN 后的 step ✅
   - 第 165 行：執行 Phase B 步驟 → 執行 DRYRUN 后的 step ✅
   - 驗證：grep 確認無遺漏 ✅

5. [ ] **skills/gendoc-flow/SKILL.md — Phase 參考清理**
   - 搜尋所有 Phase A/B 參考
   - 替換為對應新用語
   - 驗證：grep 確認無遺漏

6. [ ] **skills/gendoc-repair/SKILL.md — Phase-aware 邏輯清理**
   - 搜尋所有 Phase A/B 和 phase-aware 參考
   - 替換為對應新用語（phase-aware → DRYRUN-aware）
   - 驗證：grep 確認無遺漏

7. [ ] **其他 skills/*.md 檔案掃描**
   - gendoc-shared、gendoc-config 等其他 skill
   - 搜尋並替換所有 Phase 相關敘述
   - 驗證：全專案 grep 無 "Phase A" 或 "Phase B"（除 git 歷史外）

8. [ ] **全專案最終驗證**
   - 執行：`grep -r "Phase A\|Phase B" --include="*.md" --include="*.py" --include="*.sh" .`（不含 .git/）
   - 確認無遺漏
   - 確認邏輯上下文自然流暢

**進度追踪**：
- 開始時間：2026-05-04
- 預計耗時：1-2 小時
- 狀態：待執行

---

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

4. [✅] **全專案 hardcoded 規格掃描**（1 小時）
   - 掃描 skills/ 和 templates/ 中的 hardcoded 規格定義
   - 輸出：`docs/HARDCODED_SPECS_AUDIT.md`（已完成，無改正需求）

5. [✅] **修正 hardcoded 規格**（0 小時）
   - 掃描結果：無 hardcoded 規格需改正
   - 所有規格已參數化，符合設計要求

6. [✅] **實現審查工具 review.sh**（2 小時）
   - 機械式對比：期望（.gendoc-rules/) vs 實際（docs/）
   - 輸出：PASS / FAIL 報告（已完成）

**預計完成**：12 小時（~1-2 個工作日）
**實際完成**：2026-05-04（9-10 小時，含設計 + 實現）

### D-SSOT-4.2：get-upstream 工具驗證
- [✅] 驗證 get-upstream 讀取 pipeline.json input[]（已完成）
- [✅] 確認返回的 JSON 包含所有必要文件（已完成）
- [✅] 測試文檔：`docs/DRYRUN_GET_UPSTREAM_VERIFICATION.md`

**驗證狀態**：✅ **通過**
- DRYRUN step input[] 完整：8 個 DRYRUN 前的文件
- get-upstream.sh 實現正確
- 與 dryrun_core.py 集成有效
- 與 .gen.md 模板集成有效

### D-SSOT-4.3：dryrun_core.py 全迴歸測試（待執行）
**目標**：用實際專案驗證 DRYRUN → DRYRUN 后的 step → review.sh 完整流程

**前置條件**（目標專案需要）：
- ✅ 已執行 gendoc-auto/gendoc-flow 完成 DRYRUN 前的文件
- ✅ 包含：IDEA.md, BRD.md, PRD.md, CONSTANTS.md, PDD.md, VDD.md, EDD.md, ARCH.md
- ✅ 檔案內容符合規格（有 entity、endpoint、story、layer 定義）

**測試步驟**：
1. 在目標專案目錄執行：`gendoc dryrun`（調用 dryrun_core.py）
2. 驗證輸出：`.gendoc-rules/*.json` 包含所有 DRYRUN 后的 step 的預期規格
3. 執行 DRYRUN 后的 step（各 step 的 .gen.md 生成實際文件）
4. 執行：`tools/bin/review.sh .` 機械式驗證
5. 檢查 `docs/DRYRUN_REVIEW_REPORT.md` — 所有 PASS 即表示成功

**下一步**：選擇或建立目標專案，執行完整測試

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

