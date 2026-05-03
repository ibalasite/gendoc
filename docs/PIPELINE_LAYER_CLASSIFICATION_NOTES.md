---
title: Pipeline.json Layer 分類調整紀錄
date: 2026-05-04
version: 1.0
---

# Pipeline.json Layer 分類調整紀錄

## 摘要

在完成 pipeline.json 的 input/output 驗證與 notes 規範化後，發現 **2 個 step 的 layer 分類不符合邏輯**，已根據 Architecture Expert 審查進行修正。

---

## 變動清單

### 1. VDD: 設計層 → 需求層 ✓

**位置**：pipeline.json Step 6

**調整原因**：

- VDD.md 的設計初衷：「從 PRD 讀取 user story，將每個故事的 UI 流程與視覺需求轉譯為設計稿與 design token」
- VDD 的實際 input[]：僅包含 `["docs/PRD.md", "docs/PDD.md"]`
  - 不讀 EDD、ARCH、API、SCHEMA
  - 純粹是**視覺設計的輸入層**，不涉及技術架構決策
- **PRD 文件層級定義**（PRD.md §5.2 Table）：VDD 列為 "Layer 3.5" —— 介於「需求層（L0-L2）」與「設計層（L4+）」之間
- **結論**：VDD 應屬「需求層」，因為它不進行設計層的技術決策，只是將需求(PRD)轉為設計表達

**修正前後對比**：

```
修正前：需求層 ← IDEA, BRD, PRD, CONSTANTS, PDD → [設計層] VDD
修正後：需求層 ← IDEA, BRD, PRD, CONSTANTS, PDD, VDD → [設計層] EDD
```

---

### 2. HTML: 稽核層 → 輸出層 ✓

**位置**：pipeline.json Step 34（最後一個）

**調整原因**：

- HTML.md 的職責：「呼叫 gendoc-gen-html 將所有已生成的設計、測試、實作文件編譯成靜態網站」
- HTML 的執行時序：位於所有設計、審查、測試、實作步驟**之後**
  - 不進行任何跨層檢查（ALIGN 才是稽核層）
  - 只進行最終發布產物的生成
- **Layer 定義釐清**：
  - 稽核層 = ALIGN/ALIGN-FIX/ALIGN-VERIFY（跨層檢查與修復）
  - 輸出層 = HTML（最終產物生成與發布）
- **結論**：HTML 應屬「輸出層」，位於稽核之後，確保檢查通過後才發布

**修正前後對比**：

```
修正前：...PROTOTYPE (實作層) → ALIGN (稽核層) → ... → HTML [稽核層]
修正後：...PROTOTYPE (實作層) → ALIGN (稽核層) → ... → HTML [輸出層]
```

---

## Input[] 結構化修正（CRITICAL）

### ALIGN / ALIGN-FIX / ALIGN-VERIFY

**問題**：note 中提到「檢查 CICD §4 vs LOCAL_DEPLOY §6」與「檢查 DEVELOPER_GUIDE §2 vs CICD §2」，但 input[] 中完全沒有這些檔案。

**修正**：

```json
// 修正前
{
  "id": "ALIGN",
  "input": ["docs/EDD.md", "docs/API.md", "docs/SCHEMA.md", "docs/FRONTEND.md"]
}

// 修正後
{
  "id": "ALIGN",
  "input": ["docs/CICD.md", "docs/LOCAL_DEPLOY.md", "docs/DEVELOPER_GUIDE.md"]
}
```

**原因**：
- pipeline.json 的 input[] 是 SSOT（單一真相來源）
- get-upstream 工具根據 input[] 決定要讀取哪些檔案
- note 與 input[] 必須一致，否則工具無法正確運作
- ALIGN-FIX 與 ALIGN-VERIFY 依賴 ALIGN 的檢查結果，故同步修正

---

## 驗證方法（修正後）

### 1. Layer 語意一致性檢查

```bash
# 確認 layer 分類符合邏輯
# VDD: 需求層（只讀 PRD 輸入）✓
# ALIGN: 稽核層（跨層檢查）✓
# HTML: 輸出層（最終產物）✓
```

### 2. Input ↔ Note 一致性檢查

```bash
# ALIGN 的 note 與 input[] 現在相符：
# note: "跨層對齊檢查：CICD.md §4 vs LOCAL_DEPLOY.md §6；DEVELOPER_GUIDE.md §2 vs CICD.md §2。"
# input: ["docs/CICD.md", "docs/LOCAL_DEPLOY.md", "docs/DEVELOPER_GUIDE.md"]
```

### 3. JSON 語法驗證（✓ 已通過）

```bash
python3 -m json.tool templates/pipeline.json > /dev/null
# Result: Valid JSON
```

---

## PRD 對應說明

### PRD §5.2 文件層級表（Table）

| 文件 | PRD Layer | Pipeline Layer | 說明 |
|------|-----------|----------------|------|
| IDEA | 0 | 需求層 | 概念入口 |
| BRD | 1 | 需求層 | 商業需求 |
| PRD | 2 | 需求層 | 產品需求 |
| PDD | 3a | 需求層 | UX 互動設計 |
| VDD | 3.5 | **需求層** ← | 視覺設計（不涉及技術決策） |
| EDD | 4 | **設計層** | 工程技術設計 |
| ARCH | 5a | 設計層 | 架構設計 |
| ... | ... | 品質層/實作層 | ... |
| ALIGN | 稽核 | 稽核層 | 跨層檢查 |
| HTML | 10 | **輸出層** ← | 最終網站產物 |

**設計邏輯**：
- **需求層**：從外部輸入（user story、設計稿）向下轉譯，不做技術決策
- **設計層**：根據需求進行技術決策（EDD/ARCH/API/SCHEMA/等）
- **品質層**：驗證設計的完整性與覆蓋度（test-plan/BDD/RTM）
- **稽核層**：檢查層與層之間的對齊（ALIGN）
- **實作層**：從設計自動生成可執行的程式碼與設定（CONTRACTS/MOCK/PROTOTYPE）
- **輸出層**：發布最終產物（HTML）

---

## Git 提交紀錄

| Commit | 修正內容 |
|--------|---------|
| 51ecb59 | 完整修正所有 step notes/layer 分類 + ALIGN input[] 修正 |
| f2104c2 | 修復 input/output 定義完整性（9 項修復） |
| 186b60d | 為所有 34 steps 補入 input 欄位 |

---

## 後續影響

### get-upstream 工具

ALIGN / ALIGN-FIX / ALIGN-VERIFY 步驟現在會正確讀取：
```bash
tools/bin/get-upstream --step ALIGN \
  --output json
# 返回：CICD.md, LOCAL_DEPLOY.md, DEVELOPER_GUIDE.md 的完整內容
```

### gendoc-flow 執行邏輯

各步驟的 gen_html.py 與 skill 調用時，會根據修正後的 input[] 正確取得上游資料。

---

## 結論

此次調整是 **結構化修正**，不涉及新增或刪除步驟，僅：
1. 改正 2 個 layer 分類錯誤
2. 修正 3 個 step 的 input[] 以符合其實際檢查職責

所有修正均已通過 JSON 語法驗證，且與 PRD 文件層級定義對齊。
