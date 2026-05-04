---
title: RULES_JSON_SCHEMA
description: .gendoc-rules/*.json 統一格式標準（SSOT）
version: 1.0.0
---

# .gendoc-rules/*.json 統一格式標準

## 概述

所有 `.gendoc-rules/<step-id>-rules.json` 檔案遵循此統一格式。該格式由 `dryrun_core.py` 生成，是所有 review 工具和生成器的單一真相來源（SSOT）。

## 根層結構（必須）

```json
{
  "quantitative_specs": { ... },
  "content_mapping": { ... },
  "cross_file_validation": { ... }
}
```

所有 step 都包含上述三層，但可以是空物件 `{}`。

---

## 第一層：quantitative_specs（量化規格）

數字型門檻，用於驗證文件中的具體數量指標。

### 支援的欄位

| 欄位名 | 類型 | 說明 | 檢驗邏輯 |
|--------|------|------|---------|
| `min_h2_sections` | int | 最少 `##` 級標題數 | `grep "^## " doc.md \| wc -l >= min_h2_sections` |
| `min_endpoint_count` | int | 最少 REST endpoint 數 | `grep "^#### (GET\|POST\|...) /" doc.md \| wc -l >= min_endpoint_count` |
| `min_table_count` | int | 最少表格行數 | 根據 step 類型 |
| `min_scenario_count` | int | 最少 Scenario 數（BDD） | `grep "Scenario:" feature.feature \| wc -l >= min_scenario_count` |
| `min_paragraph_words` | int | 最少段落字數 | 每個段落 >= 此值 |

### 範例

```json
{
  "quantitative_specs": {
    "min_h2_sections": 5,
    "min_endpoint_count": 18,
    "min_paragraph_words": 30
  }
}
```

---

## 第二層：content_mapping（內容映射）

字符型內容檢查，驗證文件中是否包含必要的章節、關鍵字等。

### 支援的欄位

| 欄位名 | 類型 | 說明 |
|--------|------|------|
| `required_sections` | array[string] | 必須出現的章節名稱 |
| `required_keywords` | array[string] | 必須出現的關鍵字 |
| `section_keywords` | object | 按章節要求的關鍵字 |

### 範例

```json
{
  "content_mapping": {
    "required_sections": [
      "API Overview",
      "Authentication",
      "Error Codes",
      "Rate Limiting",
      "Endpoints"
    ],
    "required_keywords": [
      "REST",
      "GET",
      "POST",
      "PUT",
      "DELETE",
      "Authentication",
      "Rate Limit"
    ]
  }
}
```

---

## 第三層：cross_file_validation（跨文件驗證）

定義該文件與上游/下游文件的依賴關係。

### 支援的欄位

| 欄位名 | 類型 | 說明 |
|--------|------|------|
| `upstream` | array[string] | 上游依賴的 step ID |
| `downstream` | array[string] | 下游依賴的 step ID |

### 範例

```json
{
  "cross_file_validation": {
    "upstream": ["EDD", "ARCH", "PRD"],
    "downstream": ["SCHEMA", "test-plan", "CONTRACTS"]
  }
}
```

---

## review.sh 查詢規則

review.sh 按以下優先序查詢 rules.json：

```bash
# 優先級 1：嵌套結構（推薦）
.quantitative_specs.min_endpoint_count
.quantitative_specs.min_h2_sections
.quantitative_specs.min_table_count
.quantitative_specs.min_scenario_count

# 優先級 2：content_mapping
.content_mapping.required_sections
.content_mapping.required_keywords
```

---

## 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 1.0.0 | 2026-05-04 | 初版：定義三層嵌套結構 |
