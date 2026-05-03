---
title: Pipeline Input/Output 完整性驗證報告
date: 2026-05-04
version: 1.0
status: 需要修復
---

# Pipeline Input/Output 驗證報告

根據詳細掃描所有 step 的 `.gen.md` upstream-docs 與 `pipeline.json` input[] 欄位的對比分析。

---

## 執行摘要

| 類別 | 數量 | 影響 | 優先度 |
|------|------|------|--------|
| 🔴 **完全錯誤**（input 與 gen.md 無關） | 1 | input 無法提供所需資料 | **P0：立即修復** |
| ⚠️ **關鍵遺漏**（缺少 gen.md required 文件） | 4 | 直接破壞 gate-check | **P1：高優先度** |
| ℹ️ **一般遺漏**（缺少累積上游文件） | 9 | 影響 AI 補讀邏輯 | P2：中優先度 |
| 📦 **Output 宣告遺漏**（副產品未記錄） | 2 | 下游 input 無法讀取 | **P1：修復** |

---

## 問題詳單與修復方案

### 🔴 P0：完全錯誤（立即修復）

#### 1. RESOURCE 的 input 完全錯誤

**目前状態：**
```json
{
  "id": "RESOURCE",
  "input": ["docs/EDD.md", "docs/ARCH.md"]
}
```

**正確應為：**
```json
{
  "id": "RESOURCE",
  "input": ["docs/VDD.md", "docs/ANIM.md", "docs/AUDIO.md"]
}
```

**原因：**  
RESOURCE.gen.md 的生成邏輯是「從 VDD 推導視覺資產、從 ANIM 推導骨骼動畫資產、從 AUDIO 推導音效資產清單」。EDD/ARCH 與此邏輯無直接關係。

**受影響的 skill 調用：**  
當 gendoc-flow 執行 RESOURCE step 時，`get-upstream --step RESOURCE` 會收到 EDD+ARCH 內容，但 RESOURCE.gen.md 期望的是 VDD+ANIM+AUDIO，導致資產生成失敗。

**修復位置：**  
`/Users/tobala/projects/gendoc/templates/pipeline.json` line ~430-433

---

### ⚠️ P1：關鍵遺漏（gen.md required → pipeline 未列）

#### 2. CICD 遺漏 LOCAL_DEPLOY.md

**目前状態：**
```json
{
  "id": "CICD",
  "input": ["docs/EDD.md", "docs/ARCH.md"]
}
```

**應補充：**
```json
{
  "id": "CICD",
  "input": ["docs/EDD.md", "docs/ARCH.md", "docs/LOCAL_DEPLOY.md"]
}
```

**根據：**  
CICD.gen.md quality-bar: 「§4 Make targets 必須與 LOCAL_DEPLOY.md §6 完全一致（character-by-character）」

**修復位置：**  
`/Users/tobala/projects/gendoc/templates/pipeline.json` line ~645-648

---

#### 3. DEVELOPER_GUIDE 遺漏 CICD.md 和 runbook.md

**目前状態：**
```json
{
  "id": "DEVELOPER_GUIDE",
  "input": ["docs/EDD.md", "docs/LOCAL_DEPLOY.md"]
}
```

**應補充：**
```json
{
  "id": "DEVELOPER_GUIDE",
  "input": ["docs/EDD.md", "docs/LOCAL_DEPLOY.md", "docs/CICD.md", "docs/runbook.md"]
}
```

**根據：**  
DEVELOPER_GUIDE.gen.md required 欄位明確列出三件套：LOCAL_DEPLOY + CICD + runbook。§2 CI/CD 診斷章節直接讀取 CICD.md 的 §4 Shared Make targets 和 §8 Gitea。

**修復位置：**  
`/Users/tobala/projects/gendoc/templates/pipeline.json` line ~669-672

---

#### 4. BDD-client 遺漏 PRD.md

**目前状態：**
```json
{
  "id": "BDD-client",
  "input": ["docs/PDD.md", "docs/FRONTEND.md"]
}
```

**應補充：**
```json
{
  "id": "BDD-client",
  "input": ["docs/PRD.md", "docs/PDD.md", "docs/FRONTEND.md"]
}
```

**根據：**  
BDD-client.gen.md 必讀上游鏈表格，第一項即是「PRD.md — 主要輸入：將每個 AC 轉為至少 1 Happy Path + 1 Error Flow scenario」。PRD 的 AC 是 BDD-client scenario 的核心驅動力，遺漏會導致場景不完整。

**修復位置：**  
`/Users/tobala/projects/gendoc/templates/pipeline.json` line ~543-546

---

#### 5. SCHEMA 遺漏 PDD.md

**目前状態：**
```json
{
  "id": "SCHEMA",
  "input": ["docs/EDD.md", "docs/CONSTANTS.md"]
}
```

**應補充：**
```json
{
  "id": "SCHEMA",
  "input": ["docs/EDD.md", "docs/CONSTANTS.md", "docs/PDD.md"]
}
```

**根據：**  
SCHEMA.gen.md quality-bar: 「DB 欄位必須覆蓋所有 PDD 定義的顯示欄位，不得遺漏 PDD 欄位」。PDD 是決定「數據庫應該有哪些欄位」的直接輸入。

**修復位置：**  
`/Users/tobala/projects/gendoc/templates/pipeline.json` line ~271-274

---

### 📦 P1：Output 宣告遺漏（副產品未記錄）

#### 6. DRYRUN 的 .gendoc-rules/ 目錄未宣告

**目前状態：**
```json
{
  "id": "DRYRUN",
  "output": ["docs/MANIFEST.md"],
  "multi_file": false
}
```

**應改為：**
```json
{
  "id": "DRYRUN",
  "output": ["docs/MANIFEST.md", ".gendoc-rules/"],
  "output_glob": ".gendoc-rules/*.json",
  "multi_file": true
}
```

**原因：**  
DRYRUN 生成 .gendoc-rules/ 目錄下的多個 JSON 檔案（API-rules.json, SCHEMA-rules.json 等），這些文件是後續所有 step 的 gate-check 依據。若未在 pipeline.json output 中宣告，其他 step 無法透過 pipeline 明確找到此資訊。

**修復位置：**  
`/Users/tobala/projects/gendoc/templates/pipeline.json` line ~187-190

**附註：**  
UML step 也會生成 `docs/diagrams/class-inventory.md`，作為 test-plan 和 RTM 的直接輸入，但目前 pipeline output 只宣告了 `docs/diagrams/`，class-inventory.md 未單獨列出。建議保持現狀（glob 已覆蓋）。

---

## 一般遺漏清單（P2：中優先度）

以下 step 的 input 缺少「累積上游文件」（gen.md Iron Rule 允許，但不完整）：

| Step | 目前 input[] | gen.md 建議補充 | 原因 | 優先度 |
|------|------------|----------------|------|--------|
| **EDD** | PRD, CONSTANTS | +IDEA, +BRD, +PDD, +VDD | Pass-A 讀取這些文件提取業務規格 | P2 |
| **ARCH** | EDD | +IDEA, +BRD, +PRD, +PDD, +VDD | 系統整體約束來自全部需求層文件 | P2 |
| **API** | EDD, CONSTANTS | +PRD（AC 覆蓋）, +PDD（Response Schema） | PRD AC 應與 API endpoint 1-to-1 對應 | P2 |
| **FRONTEND** | PDD, VDD, CONSTANTS | +PRD, +EDD, +API | Screen×API 矩陣、Auth Flow 等 | P2 |
| **AUDIO** | EDD, ARCH | +FRONTEND（引擎版本） | gen.md quality-bar 直接讀取 | P2 |
| **ANIM** | EDD, ARCH | +FRONTEND（引擎版本）, +VDD（easing） | 同上 | P2 |
| **CLIENT_IMPL** | EDD, FRONTEND | +VDD, +ANIM, +AUDIO, +ARCH | gen.md front-matter 明確列出 | P2 |
| **ADMIN_IMPL** | EDD, API | +ARCH, +SCHEMA, +CONSTANTS | gen.md required 區塊 | P2 |
| **test-plan** | PRD, EDD, SCHEMA | +ARCH, +API, +FRONTEND | 需讀 FRONTEND 確定 E2E 覆蓋範圍 | P2 |

**設計說明：**  
pipeline.json 採用「最小直接依賴」原則（直接上游），而各 gen.md 聲明的是「完整上游鏈」。當 `get-upstream` 只讀 pipeline 中列出的最小依賴時，gen.md 的 Iron Rule 允許「上游不存在則靜默略過」。由於 gendoc-flow 中多數 step 由 AI subagent 執行（而非全部自動化），AI 會自行補讀其他檔案，所以一般遺漏的實際影響較小——但為了 pipeline SSOT 的完整性，這些也應該補充。

---

## 修復優先順序建議

1. **立即（同一個 commit）**：
   - RESOURCE input 改為 VDD+ANIM+AUDIO
   - CICD input 補 LOCAL_DEPLOY
   - DEVELOPER_GUIDE input 補 CICD+runbook
   - BDD-client input 補 PRD
   - SCHEMA input 補 PDD

2. **隨後（可視為第二個 commit）**：
   - DRYRUN 的 output 改為宣告 .gendoc-rules/ 並設 multi_file=true

3. **後續優化（可考慮）**：
   - 補充 P2 的累積上游文件，提升 pipeline.json SSOT 完整度

---

## 驗證步驟（修復後）

修復完 pipeline.json 後，應執行：

1. **語法驗證**：
   ```bash
   python3 -m json.tool templates/pipeline.json > /dev/null && echo "JSON valid"
   ```

2. **get-upstream 測試**：
   在某個目標專案中測試修復後的 get-upstream 呼叫：
   ```bash
   tools/bin/get-upstream --step RESOURCE --output json
   tools/bin/get-upstream --step CICD --output json
   # ... 其他修復過的 step
   ```
   確認返回的 JSON 包含所有預期的檔案。

3. **用 Architecture Expert agent 驗證**：
   在 pipeline.json 修復完成後，應請專家驗證：
   - input/output 映射是否形成有向無環圖（DAG）
   - 依賴順序是否合理
   - 是否有遺漏的跨步驟隱性依賴

---

## 檔案位置參考

| 檔案 | 位置 | 修復內容 |
|------|------|---------|
| pipeline.json | `/Users/tobala/projects/gendoc/templates/pipeline.json` | 修改 5 個 step 的 input[] + 1 個 step 的 output[] |
| 各 step gen.md | `/Users/tobala/projects/gendoc/templates/*.gen.md` | 無需修改（已正確定義上游）|
| 驗證參考 | 上方「問題詳單」中每個問題的「根據」欄 | 來源文件與行號 |

---

## 關鍵設計決策（需確認）

### 設計決策 1：CONSTANTS step 的 Deprecated 狀態

目前 pipeline.json 保留 CONSTANTS step，但 CONSTANTS.gen.md 標記為 DEPRECATED（功能已由 EDD Pass-0 接管，即 EDD.gen.md §2.1）。

**建議：** 保留 CONSTANTS step 以兼容舊專案，但在 DRYRUN.gen.md 中加註「若 CONSTANTS 已由 EDD Pass-0 生成，可跳過獨立 step」。

### 設計決策 2：gen.md 中「累積上游」vs pipeline.json 中「最小依賴」

當前設計是 pipeline.json 記錄「直接依賴」（get-upstream 需要的核心檔案），而 gen.md 聲明「完整上游鏈」（包含補充讀取）。

**建議：** 此設計合理，保持現狀。修復 P1 問題後，管理員可根據專案演進逐步補充 P2 中的累積上游文件。

---

## 下一步

- [ ] 修復 pipeline.json 的 5 個 P1 input 問題
- [ ] 修復 pipeline.json 的 DRYRUN output 宣告
- [ ] 測試 get-upstream 對修復後的 pipeline 的讀取結果
- [ ] 用 Architecture Expert 驗證修復後的依賴圖
- [ ] 更新 progress.md 「input/output 驗證」章節為「已完成」

---

**報告生成日期：** 2026-05-04  
**驗證方法：** 掃描所有 29 個 .gen.md 檔案，與 pipeline.json v4.0 對比  
**掃描範圍：** input[] + output[] 欄位完整性、multi_file 標記、副產品宣告  
**驗證工具：** code-explorer agent + 手工詳細對比
