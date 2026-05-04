---
title: gendoc 開發進度與待辦清單
merged: 2026-05-04（docs/progress.md + logic/progress.md 合併）
---

# gendoc 開發進度與待辦清單

---

## ✅ 已完成里程碑（按時間）

### 2026-04-26
- **GENDOC_QUALITY_AUDIT**：全 pipeline 品質審計，識別 6 大類問題（Pipeline 結構缺失 / 版本漂移 / State 管理 / 審查迴圈盲點 / Context 超限 / AI 可實作性）

### 2026-05-01
- **VIOLATION_AUDIT**：20 項架構違規清查（P2/P3/P4/D 類），P3 主要 skill 違規已修正
- **PIPELINE_ADMIN_PLAN 草稿**：pipeline.json → YAML 提案（未採用，後續保留 JSON 格式）

### 2026-05-03
- **D-SSOT-1.1** pipeline.json 新增 metrics[] 陣列（commit ce42ddb）
- **D-SSOT-1.2** pipeline.json 新增 spec_rules（commit ce42ddb）
- **D-SSOT-2.1** dryrun_core.py `_load_pipeline()`（commit 4196bbe）
- **D-SSOT-2.2** `extract_metrics()` 動態化，移除 hardcode（commit 4196bbe）
- **D-SSOT-2.3** `derive_specifications()` 動態化（commit 4196bbe）
- **R-3.1~3.4** review.sh 4 種檢查模式（quantitative / content_mapping / cross_file / all），99 行 → 355 行（commit e8ebbc5）
- **R1-V1** `validate_completeness()`（commit 99861bd）
- **R2-V1** `validate_spec_quality()`（commit 99861bd）
- **R4-V1** review_integration.sh 升級，AI + Shell findings 合併去重（commit eeca5ba）
- **D-DOC-1~5** README / PRD / 代碼文檔字串更新（commits b74e465~a18e594）
- **D-SSOT-3.1** pipeline.json 清理：刪除 metrics[] + condition_syntax，各 step 加 input[]（commit d0a9ed1）

### 2026-05-04（上半）
- **D-SSOT-3.2** get-upstream.sh 工具，160+ 行，支援章節篩選（commit a87bc94）
- **D-SSOT-3.3** DRYRUN.gen.md 整合 get-upstream（commit ebff0b2）
- **D-SSOT-3.4** API / SCHEMA / FRONTEND.gen.md 整合 get-upstream（commit d7e22e7）
- **D-SSOT-3.5 邏輯修復**：發現並修復 derive_specifications() 硬編碼分支 + pipeline.json 規格字串格式統一（commits b1e4f9d, 6709e5f）；dryrun_core.py 659 → 509 行，SSOT 遵循度 70% → 100%
- **Pipeline input/output 驗證**：修復 9 個 step input[]、1 個 output[]、ALIGN 系列擴展（commits f2104c2, 51ecb59, e4daa6e）
- **INTEGRATION_GUIDE TASK-F1~F4**：review_integration.sh 整合進 gendoc-flow Phase D-2 review loop（已確認在 SKILL.md line 962）
- **gendoc-flow --only 單步模式**：已實作（SKILL.md line 126）

### 2026-05-04（下半）
- **D-LANG-1** 全專案用語統一：Phase A/B → DRYRUN 前/后的 step，46 個替換，8 個檔案（commits dcc39bf, 8cafc42, 98e2ae2, 13d75e7, 17974a3, 9f90977）
- **HA/SPOF M-01~M-05 修改**（已確認）：IDEA.md Q4 → DAU/PCU；ARCH.md Phase 演進 → HA 基線；ARCH.md Min Replicas ≥ 2 強制標注；ARCH.md cost optimization 加 HA 注意事項
- **CA/SOLID + HA/SM HC-1~HC-5 全 pipeline 審計**：EDD §3.1b CA+SOLID 錨點、ARCH/test-plan/API/SCHEMA/DEVELOPER_GUIDE 下游對齊補完（session 2026-05-04）
- **README / PRD 14 項過時資訊修正**：pipeline.json structure、dryrun_core.py 範例、validation layers、skills 表、版本號等（commit f9c5163）

---

## ⏳ 待執行（合理該做未做）

### P0：全迴歸測試（D-SSOT-4.3）
**需要一個有完整 DRYRUN 前的文件的目標專案**

```bash
# 目標專案需有：IDEA / BRD / PRD / CONSTANTS / PDD / VDD / EDD / ARCH
# 測試步驟：
1. /gendoc-flow DRYRUN              # 執行 DRYRUN
2. 驗證 .gendoc-rules/*.json 無 {{PLACEHOLDER}}
3. /gendoc-flow API                 # 執行 API 步驟
4. 比對 API.md vs .gendoc-rules/API-rules.json
5. tools/bin/review.sh .            # 機械式驗證
6. 驗證 get-upstream.sh 返回正確 JSON
```

動態適應測試（D-SSOT-3.2）：
- [ ] 新增虛擬 metric → DRYRUN 自動提取
- [ ] 新增虛擬 DRYRUN 后的 step → 自動生成 spec_rules
- [ ] 新增虛擬 DRYRUN 前的 step → extract_parameters() 自動感知

### P1：TESTING.md T1~T5 測試套件執行
- [ ] T1 Unit tests：metric extraction / spec derivation
- [ ] T2 Functional tests：review.sh 各模式
- [ ] T3 Integration tests：dryrun + review.sh + flow
- [ ] T4 E2E tests：full pipeline
- [ ] T5 Regression tests：不破壞現有功能

### P1：ha-spof-modification-plan.md M-06 以後項目驗收
已確認 M-01~M-05 完成，尚未驗證 M-06 以後的修改是否全部套用。
建議掃描 ha-spof-modification-plan.md 完整清單，逐項 grep 驗證。

### P2：GENDOC_QUALITY_AUDIT 2026-04-26 殘留問題
原審計 6 大類中，部分已修復（Pipeline 結構、UML、BDD 等），需重新過一遍確認：
- [ ] D 類：審查迴圈架構盲點（跨文件視角）— review.sh 整合後是否已解決？
- [ ] F 類：AI 可實作性標準強制閉環驗證 — RTM 追蹤是否完整？

### P2：RULES_JSON_SCHEMA.md 對齊驗證
RULES_JSON_SCHEMA.md 定義 3 層結構（quantitative_specs / content_mapping / cross_file_validation），但 D-SSOT-3.5 後 pipeline.json spec_rules 已改為 flat key/value。
需確認 dryrun_core.py 實際輸出的 .gendoc-rules/*.json 格式是否與 RULES_JSON_SCHEMA.md 一致，或更新 schema 說明。

### P3：VIOLATION_AUDIT P2 系列（install 讀本地）
P2-1~P2-7：install.sh / install.py / gendoc-session-update 在 git pull 後讀本地 working tree 安裝。
目前 setup 流程 git pull → 從本地複製到 ~/.claude/ 是可接受的設計（非嚴格違規），但 D1 local-first pipeline.json 已確認為刻意設計，無需修改。
建議：在 CLAUDE.md 補注 P2 系列為「已知設計決策，非違規」，關閉此追蹤。

---

## 不合時宜文件列表（logic/ 目錄）

> 以下文件已完成其歷史使命，內容已被後續工作取代或對應實作已完成，可考慮歸檔或刪除。

| 文件 | 原用途 | 不合時宜原因 |
|------|--------|-------------|
| `logic/DRYRUN_CORE_IMPLEMENTATION_PLAN.md` | D-SSOT-4.1 實作計畫 | 計畫已全部執行完成 |
| `logic/DRYRUN_API_VERIFICATION.md` | SSOT 邏輯驗證報告 | 問題已修復（commits b1e4f9d, 6709e5f） |
| `logic/DRYRUN_GET_UPSTREAM_VERIFICATION.md` | get-upstream 驗證報告 | 工具已實作並整合，驗證完成 |
| `logic/HARDCODED_SPECS_AUDIT.md` | hardcoded 規格掃描 | 掃描完成，無問題，已無追蹤價值 |
| `logic/PIPELINE_INPUT_VALIDATION_REPORT.md` | pipeline input[] 驗證 | 修復已套用（commits f2104c2 等） |
| `logic/PIPELINE_LAYER_CLASSIFICATION_NOTES.md` | layer 分類調整紀錄 | 調整已套用（commit 51ecb59） |
| `logic/IMPLEMENTATION_VERIFICATION_REPORT.md` | 實作驗證彙整 | 被 docs/progress.md 的完整記錄取代 |
| `logic/MODIFICATION_CHECKLIST_v17.md` | 第 2 輪 17 項審計清單 | 執行完成，Phase A/B 術語替換已全部完成 |
| `logic/GENDOC_FLOW_SINGLE_STEP_DESIGN.md` | --only 單步模式設計 | 功能已實作（gendoc-flow SKILL.md line 126） |
| `logic/PIPELINE_ADMIN_PLAN.md` | pipeline.json → YAML 提案 | 提案未採用（保留 JSON 格式），設計已分歧 |

---

## 仍有參考價值的 logic/ 文件（建議保留）

| 文件 | 保留原因 |
|------|---------|
| `logic/DRYRUN_PARAMETER_EXTRACTION.md` | extract_parameters() 7 個方法的規格說明，dryrun_core.py 的設計依據 |
| `logic/DRYRUN_SPEC_FORMULAS.md` | derive_specifications() 公式定義，審查 .gendoc-rules 內容的依據 |
| `logic/RULES_JSON_SCHEMA.md` | .gendoc-rules/*.json 格式標準（⚠️ 需確認與當前 flat format 對齊） |
| `logic/TESTING.md` | T1~T5 測試套件計畫，待執行 |
| `logic/currentanalysis.md` | 2026-05-03 專案方向分析，仍有策略參考價值 |
| `logic/GENDOC_QUALITY_AUDIT.md` | 2026-04-26 品質審計，部分問題可能仍未完全解決 |
| `logic/ha-spof-modification-plan.md` | M-06 以後修改項目需逐項驗收 |
| `logic/VIOLATION_AUDIT.md` | P2 系列建議補注為已知設計決策後可關閉 |
| `logic/gendoc-redesign-decisions.md` | 早期改版決策紀錄，有歷史上下文價值 |
| `logic/INTEGRATION_GUIDE.md` | F1~F4 已整合，但仍可作為 review loop 架構說明參考 |
| `logic/CLIENT.md` | gendoc HTML 文件站前端設計草稿（DRAFT v1.0），待決定是否繼續推進 |
