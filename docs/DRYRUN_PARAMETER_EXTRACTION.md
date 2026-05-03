---
title: DRYRUN 參數提取規則
date: 2026-05-04
version: 1.0
status: 實作規範
---

# DRYRUN 參數提取規則

## 概述

dryrun_core.py 的 `extract_parameters()` 方法需從 Phase A 文件中提取四個核心參數，作為推導 Phase B 各 step 規格的基礎。本文檔定義每個參數的提取方法、正規表示式、fallback 邏輯與驗證規則。

---

## 核心原則

1. **無硬編碼預設值**：若參數無法提取，使用明確的 fallback（記錄於 MANIFEST.md），不得以無來源的推測值填補
2. **可追蹤性**：每個提取結果必須記錄其來源（檔案名、章節、行號）以供審查
3. **容錯優雅**：若上游文件缺失，回傳 `0` 並標記 `source: "missing"` 而非 exception
4. **跨版本穩定性**：使用 markdown heading 級別與內容模式（而非行號）來定位內容

---

## 參數 1：entity_count

### 定義
系統中定義的 entity/class 總數。來自 EDD.md 的資料模型部分。

### 提取方法

#### 來源文件：`docs/EDD.md`
#### 目標位置：
- 主位置：§4.4 Class Inventory（若存在）
- 備選位置：§5.5 Data Model（§5.5.1 Entity Definition 小節）

#### 提取規則

**步驟 1：定位章節**
```bash
# 查找 §4.4 或 §5.5 標題
grep -n "^## .*4.4.*Class.*Inventory\|^## .*5.5.*Data.*Model" docs/EDD.md
```

**步驟 2：提取 entity 列表**

假設該章節包含一個 markdown 表格或列表，格式為：
```
### Entities / Classes
| Class Name | Module | Description |
|---|---|---|
| User | auth | 使用者帳號 |
| Game | core | 遊戲局 |
...
```

或者列表格式：
```
- `User` (auth module): 使用者帳號
- `Game` (core module): 遊戲局
...
```

**提取命令：**
```bash
# 方式 A：表格計數（跳過 header 和分隔符）
entity_count=$(awk '/^## .*Class.*Inventory/,/^##/' docs/EDD.md | \
  grep -E "^\s*\|\s*\`?[A-Z][a-zA-Z0-9]*\`?" | \
  grep -v "^[|:-]" | \
  wc -l)

# 方式 B：列表計數（符合 "- `ClassName`" 或 "- ClassName" 模式）
entity_count=$(awk '/^## .*Class.*Inventory/,/^##/' docs/EDD.md | \
  grep -E "^\s*-\s+\`?[A-Z][a-zA-Z0-9]*\`?" | \
  wc -l)

# 若兩者都無匹配，嘗試計算所有 ### SubEntity 小標題
entity_count=$(awk '/^## .*\(Data Model|Class.*Inventory\)/,/^##/' docs/EDD.md | \
  grep -c "^### [A-Z]")
```

**步驟 3：驗證與 fallback**

- 若 entity_count ≥ 1 且 ≤ 200，接受該值
- 若 entity_count = 0：
  - 檢查是否章節存在但為空（返回 `0`，標記 source: "empty_section"）
  - 檢查是否 EDD.md 根本不存在（返回 `0`，標記 source: "missing_file"）
  - 檢查 §5.5 下是否有任何小標題 `###` 作為 entity（若有，計數）
- 若 entity_count > 200：標記異常，使用conservative fallback（見下文）

#### Fallback 值
| 條件 | Fallback | 記錄 |
|------|----------|------|
| EDD.md 不存在 | `3` | `entity_count: 3 (fallback: missing_file)` |
| 章節存在但無 entity 定義 | `3` | `entity_count: 3 (fallback: empty_section)` |
| 提取異常（>200 或匹配失敗） | `3` | `entity_count: 3 (fallback: extraction_failed)` |

#### 輸出格式（dryrun_core.py 記錄於 MANIFEST.md）
```
**entity_count**: 10 (source: docs/EDD.md §5.5.1, line 45-89)
```

---

## 參數 2：rest_endpoint_count

### 定義
系統暴露的 REST API endpoint 總數（唯一 HTTP method + path 組合）。來自 PRD.md 和/或 EDD.md。

### 提取方法

#### 來源文件：
- 優先：`docs/PRD.md` 的 REST API 需求部分
- 備選：`docs/EDD.md` 的 API 設計部分

#### 目標位置：
- 主位置：PRD.md §2 User Stories with API Mapping 或 §3 Functional Requirements
- 備選位置：EDD.md §5.1 API Specification

#### 提取規則

**步驟 1：掃描 endpoint 定義**

假設 PRD 中包含類似以下格式：
```
### API Requirements
- GET /api/users
- GET /api/users/{id}
- POST /api/users
- PUT /api/users/{id}
- DELETE /api/users/{id}
- GET /api/games
- POST /api/games/{gameId}/players
...
```

或表格格式：
```
| Method | Path | Description |
|--------|------|---|
| GET | /api/users | 列取使用者 |
| POST | /api/users | 新增使用者 |
...
```

**提取命令：**
```bash
# 方式 A：尋找 "METHOD /path" 模式（含大括號參數）
rest_endpoint_count=$(grep -Eo "(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) /[a-zA-Z0-9/_\{\}-]*" docs/PRD.md | \
  sort -u | \
  wc -l)

# 方式 B：表格中 Method + Path 的組合計數
rest_endpoint_count=$(awk '/^### API Requirements/,/^##/' docs/PRD.md | \
  grep -E "^\s*\|(GET|POST|PUT|DELETE|PATCH)" | \
  awk '{print $2, $4}' | \
  sort -u | \
  wc -l)

# 方式 C：若 EDD 存在，檢查 EDD §5.1
if [[ -f docs/EDD.md ]]; then
  edd_endpoints=$(grep -Eo "(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) /[a-zA-Z0-9/_\{\}-]*" docs/EDD.md | sort -u | wc -l)
  [[ $edd_endpoints -gt $rest_endpoint_count ]] && rest_endpoint_count=$edd_endpoints
fi
```

**步驟 2：去重與計數**

- 同一個 HTTP method + path 組合只計算一次（例如 `GET /api/users` 在文件中出現多次仍只算 1）
- 不同 method 作用在同一 path 視為不同 endpoint（例如 `GET /api/users` 和 `POST /api/users` 計為 2）

**步驟 3：驗證與 fallback**

- 若 rest_endpoint_count ≥ 1 且 ≤ 500，接受該值
- 若 rest_endpoint_count = 0：
  - 檢查 PRD.md 是否缺失（返回 fallback）
  - 檢查章節是否存在但無 endpoint 定義（可能是 API-only 專案，未在 PRD 寫詳細 endpoint）
- 若 rest_endpoint_count > 500：可能是掃描規則過於寬鬆，手動調整

#### Fallback 值
| 條件 | Fallback | 記錄 |
|------|----------|------|
| PRD.md 不存在或無 API 部分 | `5` | `rest_endpoint_count: 5 (fallback: missing_api_section)` |
| 章節存在但無 endpoint 定義 | `5` | `rest_endpoint_count: 5 (fallback: empty_api_section)` |
| 提取失敗或異常 | `5` | `rest_endpoint_count: 5 (fallback: extraction_failed)` |

#### 輸出格式
```
**rest_endpoint_count**: 12 (source: docs/PRD.md §3.2 API Requirements, 12 unique endpoints found)
```

---

## 參數 3：user_story_count

### 定義
系統中定義的 user story/用戶需求總數。來自 PRD.md。

### 提取方法

#### 來源文件：`docs/PRD.md`

#### 目標位置：
- 主位置：§2 User Stories 或 §3 Functional Requirements
- 備選位置：附錄中的 User Story 列表

#### 提取規則

**步驟 1：定位 user story 章節**

```bash
# 尋找標題
grep -n "^## .*User Stories\|^## .*Functional Requirements\|^## .*需求" docs/PRD.md | head -1
```

**步驟 2：提取 user story 定義**

假設使用者故事採用標準格式：
```
### US-001: User Registration
As a new user, I want to create an account, so that I can access the system.

Acceptance Criteria:
- AC1: Email validation
- AC2: Password strength check

### US-002: User Login
As a registered user, I want to login with email and password...
```

或者使用表格格式：
```
| Story ID | Title | As a... | I want... | So that... |
|----------|-------|---------|-----------|------------|
| US-001 | User Registration | new user | create account | access system |
...
```

**提取命令：**
```bash
# 方式 A：計算 "### US-*" 或 "### Story-*" 小標題
user_story_count=$(awk '/^## .*User Stories/,/^##[^#]/' docs/PRD.md | \
  grep -c "^### .*US-[0-9]\|^### .*Story-[0-9]")

# 方式 B：計算包含 "As a" 的行數（粗略估計）
user_story_count=$(grep -c "^As a " docs/PRD.md)

# 方式 C：表格計數（跳過 header）
user_story_count=$(awk '/^## .*User Stories/,/^##/' docs/PRD.md | \
  grep -E "^\|.*US-[0-9]|^\|.*Story-[0-9]" | \
  grep -v "^|.*ID.*|" | \
  wc -l)
```

**步驟 3：驗證與 fallback**

- 若 user_story_count ≥ 1 且 ≤ 500，接受該值
- 若 user_story_count = 0：
  - 檢查 PRD.md 是否缺失
  - 檢查 User Stories 章節是否為空（可能是 API-only 專案，無前端 UI 故事）
  - 檢查是否故事在附錄或其他位置（手動掃描）

#### Fallback 值
| 條件 | Fallback | 記錄 |
|------|----------|------|
| PRD.md 不存在或無 User Stories 章節 | `20` | `user_story_count: 20 (fallback: missing_us_section)` |
| User Stories 章節存在但為空 | `20` | `user_story_count: 20 (fallback: empty_us_section)` |
| 提取失敗 | `20` | `user_story_count: 20 (fallback: extraction_failed)` |

#### 輸出格式
```
**user_story_count**: 18 (source: docs/PRD.md §2 User Stories, 18 stories found)
```

---

## 參數 4：arch_layer_count

### 定義
系統架構中定義的層級/服務邊界總數。來自 ARCH.md。

### 提取方法

#### 來源文件：`docs/ARCH.md`

#### 目標位置：
- 主位置：§3 Architecture Overview 或 §2 Layered Architecture
- 備選位置：§4 Microservices Boundaries

#### 提取規則

**步驟 1：判定架構類型並定位**

```bash
# 檢查是否為分層架構（N-Tier）或微服務
if grep -q "Layered\|Layer\|N-Tier\|N-tier\|分層" docs/ARCH.md; then
  arch_type="layered"
  # 尋找層級定義
  layer_lines=$(grep -n "^### .*Layer\|^### .*層" docs/ARCH.md | wc -l)
elif grep -q "Microservices\|Micro-service\|微服務" docs/ARCH.md; then
  arch_type="microservices"
  # 尋找服務邊界定義
  layer_lines=$(grep -n "^### .*Service\|^### .*服務" docs/ARCH.md | wc -l)
else
  arch_type="unknown"
  layer_lines=0
fi
```

**步驟 2：提取層級/服務定義**

假設 ARCH 包含：
```
## 3. Architecture Overview

### Presentation Layer
描述前端層、API Gateway 等

### Business Logic Layer
描述核心業務邏輯層

### Data Access Layer
描述資料存取層

### Infrastructure Layer
描述基礎設施層（監控、日誌等）
```

或微服務架構：
```
## 4. Microservices Boundaries

### User Service
- 負責使用者管理

### Game Service
- 負責遊戲邏輯

### Payment Service
- 負責支付流程
```

**提取命令：**
```bash
# 方式 A：計算 "### ... Layer" 或 "### ... Service" 的小標題
arch_layer_count=$(grep -c "^### .*Layer\|^### .*層\|^### .*Service\|^### .*服務" docs/ARCH.md)

# 方式 B：若無明確小標題，計算同級別的二級標題
if [[ $arch_layer_count -eq 0 ]]; then
  # 取得首個 ## 後的所有 ### 直到下一個 ##
  arch_layer_count=$(awk '/^## .*Architecture|^## .*Microservices/,/^## [^#]/' docs/ARCH.md | \
    grep -c "^### ")
fi
```

**步驟 3：驗證與 fallback**

- 若 arch_layer_count ≥ 2 且 ≤ 50，接受該值（通常 N-Tier 有 3-5 層）
- 若 arch_layer_count < 2：
  - 檢查 ARCH.md 是否缺失
  - 檢查架構定義是否在其他位置（例如 EDD.md §3）
  - 視為簡單架構，使用 fallback

#### Fallback 值
| 條件 | Fallback | 記錄 |
|------|----------|------|
| ARCH.md 不存在 | `4` | `arch_layer_count: 4 (fallback: missing_file)` |
| 無層級定義或過於簡略 | `4` | `arch_layer_count: 4 (fallback: simple_architecture)` |
| 提取失敗 | `4` | `arch_layer_count: 4 (fallback: extraction_failed)` |

#### 輸出格式
```
**arch_layer_count**: 5 (source: docs/ARCH.md §3 Architecture Overview, 5 layers: Presentation, Business Logic, Data Access, Infrastructure, Cross-cutting Concerns)
```

---

## 第五參數（可選）：admin_feature_count

### 定義
系統中 Admin 相關功能數量（僅當 `has_admin_backend == true` 時提取）。來自 EDD.md。

### 提取方法

#### 觸發條件
- 檢查 `.gendoc-state.json` 中 `has_admin_backend` 字段是否為 `true`
- 若為 `false` 或 `null`，跳過此參數，記錄 `admin_feature_count: N/A (reason: has_admin_backend=false)`

#### 提取規則

若觸發，查找 EDD.md 中的 Admin 相關 entity/feature 定義：
```bash
# 計算 Admin-related entity
admin_count=$(grep -Ei "admin|管理" docs/EDD.md | grep "^###" | wc -l)
```

#### Fallback 值
```
admin_feature_count: 5 (fallback: default admin features)
```

---

## 提取流程（dryrun_core.py 中的 extract_parameters 實作）

```python
def extract_parameters(self):
    """
    從上游文件提取四個核心參數。
    返回：{
        "entity_count": int,
        "rest_endpoint_count": int,
        "user_story_count": int,
        "arch_layer_count": int,
        "admin_feature_count": int or None,
        "metadata": {
            "entity_count_source": "docs/EDD.md §5.5.1",
            "entity_count_extracted_at": "line 45-89",
            "rest_endpoint_count_source": "docs/PRD.md §3.2",
            ...
        }
    }
    """
    
    # Step 1: 讀取上游文件（藉由 _load_upstream()）
    upstream_content = self._load_upstream()
    
    # Step 2: 逐一提取參數
    params = {}
    
    # 2.1 entity_count
    params["entity_count"] = self._extract_entity_count(upstream_content)
    
    # 2.2 rest_endpoint_count
    params["rest_endpoint_count"] = self._extract_rest_endpoint_count(upstream_content)
    
    # 2.3 user_story_count
    params["user_story_count"] = self._extract_user_story_count(upstream_content)
    
    # 2.4 arch_layer_count
    params["arch_layer_count"] = self._extract_arch_layer_count(upstream_content)
    
    # 2.5 admin_feature_count（若適用）
    params["admin_feature_count"] = self._extract_admin_feature_count(upstream_content)
    
    # Step 3: 記錄提取來源（供 MANIFEST.md）
    params["metadata"] = {
        "extraction_timestamp": datetime.now().isoformat(),
        "total_fallback_count": count_fallback_params(params),
        "extraction_success_rate": calculate_success_rate(params)
    }
    
    return params
```

---

## 檢查清單

- [ ] 四個參數的提取規則已定義
- [ ] 每個參數的 fallback 邏輯清晰
- [ ] 提取命令（bash/python）可在目標專案中執行
- [ ] 輸出格式便於 MANIFEST.md 記錄
- [ ] 測試用例已準備（對應實際專案的幾個示例）

---

## 相關檔案

| 檔案 | 用途 |
|------|------|
| `templates/pipeline.json` | DRYRUN step 的 input[] 定義 |
| `docs/DRYRUN_SPEC_FORMULAS.md` | 參數如何用於推導規格（下一個 STEP） |
| `tools/bin/dryrun_core.py` | 實作此提取規則 |
| `docs/MANIFEST.md` | 記錄提取結果（輸出檔） |
