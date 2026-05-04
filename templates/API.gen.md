---
doc-type: API
output-path: docs/API.md
upstream-docs:
  ssot-source: "templates/pipeline.json step.API.input[]"
  core-inputs:
    - docs/EDD.md        # API 設計、認證/授權規格
    - docs/CONSTANTS.md  # 速率限制、頁面大小、超時等常量
  description: |
    核心上游由 get-upstream 工具讀取並返回 JSON。
    API.gen.md 從 JSON 提取相關內容進行 API 設計。
quality-bar: "每個 PRD P0 功能都有對應 Endpoint；所有 Endpoint 有完整 Request/Response Schema；認證、分頁、錯誤碼說明完整；§11 API Paradigm Decision 已填寫；§12 OpenAPI 3.1 YAML 已生成；§17 SLO 目標已定義"
---

# API.gen.md — API 文件生成規則

依 EDD + PRD 產出 OpenAPI 風格的 API.md，涵蓋所有端點與 Schema 定義。

---

## 步驟 0：量化規格讀取 + get-upstream 呼叫

### 步驟 0a：讀取 .gendoc-rules/API-rules.json 的量化規格（DRYRUN 產出）

**[強制]** 在開始生成前，**必須**讀取 `.gendoc-rules/API-rules.json` 中定義的量化規格（由 DRYRUN 步驟生成）：

```bash
# 讀取 API step 的量化規格
if [[ -f ".gendoc-rules/API-rules.json" ]]; then
  _MIN_ENDPOINT_COUNT=$(jq -r '.quantitative_specs.min_endpoint_count // 0' ".gendoc-rules/API-rules.json")
  _MIN_H2_SECTIONS=$(jq -r '.quantitative_specs.min_h2_sections // 0' ".gendoc-rules/API-rules.json")
  _REQUIRED_SECTIONS=$(jq -r '.content_specs.required_sections[]?' ".gendoc-rules/API-rules.json")
else
  echo "⚠️  WARNING: .gendoc-rules/API-rules.json 不存在（DRYRUN 未執行）"
  echo "           假設 min_endpoint_count = 12（預設值），系統會按此生成"
  _MIN_ENDPOINT_COUNT=12
  _MIN_H2_SECTIONS=5
fi

echo "[API Gen] 量化規格從 DRYRUN 讀取："
echo "  min_endpoint_count: $_MIN_ENDPOINT_COUNT"
echo "  min_h2_sections: $_MIN_H2_SECTIONS"
```

**含義**：目標 API.md 必須包含至少 `_MIN_ENDPOINT_COUNT` 個完整的 endpoint 定義（格式：`#### (HTTP_METHOD) /path`）。

### 步驟 0b：呼叫 get-upstream 讀取上游檔案

在開始 API 設計前，讀取所有定義在 `pipeline.json` API step 的 `input[]` 檔案：

```bash
# 呼叫 get-upstream 讀取 API step 的 input 檔案
_UPSTREAM_JSON=$(tools/bin/get-upstream --step API --output json 2>&1)

if [[ $? -ne 0 ]]; then
  echo "ERROR: get-upstream failed for API step"
  echo "$_UPSTREAM_JSON" >&2
  exit 1
fi

# 解析 JSON 並提取檔案內容（供後續步驟使用）
# 結構：{"step": "API", "inputs": {"docs/EDD.md": "content...", "docs/CONSTANTS.md": "content..."}}
```

---

## Iron Rule：使用 get-upstream 提供的檔案

所有 API 設計邏輯必須基於 `get-upstream` 返回的 JSON 中的檔案內容。
不得讀取本地檔案或使用預設值，除非該檔案在 JSON 中明確標記為缺失。

---

## 上游檔案讀取規則（從 get-upstream JSON 提取）

### 必讀上游鏈（依優先順序）

| 文件 | 必讀章節 | 用途 |
|------|---------|------|
| `IDEA.md`（若存在）| 全文 | 了解產品願景——API 命名風格和業務語意必須反映 IDEA 的業務概念 |
| `BRD.md` | 業務需求、使用者角色 | API 的權限設計需與 BRD 的使用者角色對應 |
| `PRD.md` | 所有 P0/P1 功能及 AC | API Endpoint 必須覆蓋所有功能的 AC |
| `PDD.md`（若存在）| UI 互動流程、畫面欄位 | API 的 Response Schema 需支援 PDD 的畫面欄位與分頁需求 |
| `EDD.md` | §3（架構）、§4（Security）| API 的認證/授權必須與 EDD §4 保持嚴格一致 |
| `ARCH.md` | 元件邊界、Service 介面 | API Endpoint 的歸屬和 Service 分層必須與 ARCH 一致 |

### IDEA.md Appendix C 素材讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與 API 相關的檔案。
對每個存在的 `docs/req/` 檔案，讀取全文，結合 Appendix C「應用於」欄位標有「API §」的段落，
作為生成 API 對應章節（Endpoint 定義、Request/Response Schema、認證方式）的補充依據。
優先採用素材原文描述，而非 AI 推斷。若無引用，靜默跳過。

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- EDD 的認證規格 vs ARCH 的 API Gateway 設計（e.g., JWT HS256 vs RS256）
- PRD 的功能 AC vs EDD 的 API 設計（是否有 AC 無對應 Endpoint）
- PDD 的 UI 欄位需求 vs EDD 的 Response Schema（是否有欄位 UI 需要但 API 未回傳）

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並依衝突解決機制處理。

---

## 文件結構規則

生成內容必須涵蓋 `templates/API.md` 的所有章節，包含：
Document Control、Standard Headers、Error Code Registry、認證、Rate Limiting（3 層）、
Idempotency、Webhooks CloudEvents+HMAC、Batch 207、File Upload、API Paradigm Decision、
OpenAPI 3.1 YAML 完整規格、API Changelog、Review Checklist、
API Versioning & Deprecation Policy（§15）、Client SDK & Code Generation（§16）、API Observability & SLO（§17）。

---

## §0 快速概覽生成規則

必須包含：
- Base URL（生產環境 + 本地）
- 協議（HTTPS 強制）
- 認證方式（`Authorization: Bearer <JWT>` 除公開端點外均需要）
- 回應格式（`application/json`）
- 時區（所有時間欄位均為 UTC，ISO 8601 格式）
- 分頁策略（Cursor-based，`?after=<cursor>&limit=20`）
- 版本（v1 路徑前綴，向下相容保證）

---

## §4 Authentication（認證）生成規則

必須包含以下完整說明：
- 取得 Token（POST /api/v1/auth/login）：Request Body + Response 200 結構
- 使用 Token（Authorization: Bearer header）
- Refresh Token（POST /api/v1/auth/refresh）
- Rate Limit 設定（Auth endpoints：10 req/min/IP；API endpoints：100 req/min/user）

---

## §3 Endpoints（端點列表）生成規則

**BC 分組規則（Spring Modulith HC-2，必填）**：

1. 讀取 EDD §3.4 Bounded Context Map，識別所有 BC 及其 Path Prefix
2. 在 §3 中為每個 BC 建立一個 `### BC: {BC_NAME} Endpoints` 子章節，包含：
   - `**Owning BC**`、`**Path Prefix**`、`**Owned Tables**` 三個標注行
   - Owned Tables 必須與 ARCH.md §4.0 API-BC-Schema 映射表一致
3. 將每個 Endpoint 放入其對應 BC 的子章節中（Path Prefix 對應原則）
4. **驗證規則**：
   - 所有 Endpoint 都有 BC 歸屬（無孤立 Endpoint）
   - 不同 BC 的 Endpoint Path Prefix 不重疊（無跨 BC Path 混淆）
   - 每個 BC 子章節在 §3 中的順序與 §1.2 Bounded Context 歸屬表的順序一致

依 PRD 功能逐一列出每個 Endpoint，每個端點必須包含：

**必填欄位：**
- 功能說明（來自 PRD）
- 認證要求（需要 JWT / 公開）
- 權限（`<role>:read` / `<role>:write`）
- Request Body 表格（欄位、型別、必填、說明含長度限制/格式要求/範圍/精度）
- Request Body JSON 範例
- Response 成功碼（含 JSON 範例）
- 錯誤回應表格（HTTP Code、Error Code、說明）

**標準錯誤碼覆蓋（每個 Endpoint 至少含）：**

| HTTP Code | Error Code | 說明 |
|-----------|-----------|------|
| 400 | `VALIDATION_ERROR` | 輸入格式錯誤（回傳 `errors` 陣列）|
| 401 | `UNAUTHORIZED` | Token 無效或過期 |
| 403 | `FORBIDDEN` | 無此操作權限 |
| 404 | `NOT_FOUND` | 資源不存在（GET/PATCH/DELETE 端點）|
| 409 | `CONFLICT` | 資源已存在（POST 端點）|
| 422 | `BUSINESS_RULE_VIOLATION` | 業務規則違反（含 `message` 說明）|
| 429 | `RATE_LIMITED` | 超過速率限制 |
| 500 | `INTERNAL_ERROR` | 系統錯誤（不揭露內部訊息）|

**列表查詢（GET collection）必須使用 Cursor-based 分頁：**
- Query Parameters 表格（after、limit、filter 篩選參數）
- Response 含 pagination 物件（next_cursor、has_more、total_count=null）

**PATCH 端點：**
- 只更新傳入的欄位（Partial Update）
- 說明冪等性（相同請求重複執行結果相同）
- Soft Delete 子端點：PATCH /:id/delete → Response 204（無 body）

---

## §2 通用規範（Standard Conventions）生成規則

必須定義以下三個共用 Schema：

**Envelope（成功回應）：**
```json
{
  "data": { ... },
  "meta": { "request_id": "uuid" }
}
```

**Error Envelope：**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "errors": [
      { "field": "email", "message": "Invalid email format" }
    ],
    "request_id": "uuid"
  }
}
```

**Pagination（Cursor-based）：**
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJ...",
    "has_more": true,
    "total_count": null
  }
}
```
注意：`next_cursor` 為 base64 encoded，內含時間戳或 ID；`total_count` 大資料集不提供，避免全表掃描。

---

## §1 概述（Overview）補充規則 — API 序列圖

**覆蓋規則（必須遵守）：**

API 序列圖聚焦 **Client ↔ API 層**互動視角；服務內部詳細協作見 EDD §4.5.4（不得矛盾）。

**最低張數 = §3 中所有 POST / PATCH / PUT / DELETE Mutation Endpoint 數量**

- 每個 Mutation Endpoint 必須有一張獨立的 `sequenceDiagram`，包含 Happy Path + Error Path
- GET / List 端點可合併為 1 張代表性序列（若數量 > 5，選最複雜的 1 張）
- 若 Mutation Endpoint 數量 > 10，可依業務域（Domain）合併（同域相同操作類型可共用 1 張）

**每張序列圖必須包含：**

**Happy Path：**
- 涵蓋 JWT 驗證 → 業務規則檢查 → DB 寫入 → 成功回應
- 參與者：Client、API Gateway、Auth Service、Domain Service、Repository、PostgreSQL（+ Redis / MessageQueue 若有用到）

**Error Path（每張至少 2 個）：**
- 1 個業務規則違反：標注 422 VALIDATION_ERROR / 409 CONFLICT 等，展示從哪一層拋出
- 1 個系統錯誤：標注 503 SERVICE_UNAVAILABLE 或 TIMEOUT，展示 fallback / Circuit Breaker 行為
- 若有認證保護，加入 401 UNAUTHORIZED 路徑

**非同步操作：**
- 若寫入後觸發 Message Queue，使用 `par [async]` 塊標注事件類型和 Queue 名稱
- 重試機制使用 `loop [retry N times]` 塊標注

**上下游一致性聲明（必須在 §1 開頭寫入）：**
```
本文件的 API 序列圖描述 Client 視角的 HTTP 請求-回應。
同一業務操作的服務內部詳細流程，見 docs/EDD.md §4.5.4。
若兩份文件描述同一操作，以下優先級解決矛盾：
  1. 若 Client 操作無效（400/401），以本文件回應規格為準
  2. 若 Server 內部流程有異，以 EDD 為準
  3. 若兩者皆不明確，標記 [UPSTREAM_CONFLICT] 並提交 ADR
```

---

## §5 Error Handling（錯誤處理）生成規則

依 API.md §5 Error Handling 產出：
- §5.1 Error Response Schema：標準 Error Envelope（含 code / message / errors / request_id）
- §5.2 Error Code Registry：所有業務錯誤碼列表（HTTP Code + Error Code + 說明 + 範例）
- 確保每個 Endpoint 的錯誤碼表（§3）引用此處的 Registry

---

## §6 Rate Limiting（速率限制）生成規則

依 API.md §6 Rate Limiting 產出：
- §6.1 限制層級：定義 IP 層、使用者層、全局層三層限制
- §6.2 Burst 容許機制：説明短暫突發請求的容許策略
- §6.3 429 Response 格式：回應標頭（Retry-After、X-RateLimit-* 系列）+ 回應 Body

---

## §7 Idempotency（冪等性）生成規則

依 API.md §7 Idempotency 產出：
- §7.1 設計原則：說明哪類操作必須實作冪等性（POST 建立資源、Webhook 重試）
- §7.2 需要冪等的端點清單：來自 §3 Endpoints，標注哪些端點需要 `Idempotency-Key` header
- §7.3 伺服器行為：Key 儲存時間（建議 24h）、重複請求的回應策略
- §7.4 Key 規範：格式（UUID v4）+ header 名稱（`Idempotency-Key`）

---

## §8 Webhooks 生成規則（若有）

若產品設計包含 Webhook，必須說明：
- POST 目標 URL 格式
- 簽署驗證（HMAC-SHA256）：`X-Signature: sha256=<HMAC-SHA256(secret, raw_body)>`
- 驗證代碼範例（Python）
- 重試策略（指數退避：1m, 5m, 30m, 2h, 1d；超過 5 次失敗 → 停用並通知）

---

## §9 Batch Operations 生成規則

若產品需要批次操作：
- 批次端點：`POST /<resource>/batch`
- 回應碼：207 Multi-Status
- 說明每個子請求的獨立成功/失敗結構

---

## §10 File Upload 生成規則

若產品需要檔案上傳：
- 說明 multipart/form-data 方式
- 說明 S3 presigned URL 模式（推薦用於大檔案）
- 說明檔案大小限制、允許格式

---

## §11 API Paradigm Decision 生成規則

必須提供完整的 API 設計決策說明：
- REST vs GraphQL vs gRPC 比較表（適用場景、優缺點）
- 本產品選擇的 API 範式
- 決策依據（結合 PRD 的功能需求和 EDD 的技術架構）

---

## §12 OpenAPI 3.1 Specification 生成規則

必須生成完整 YAML 規格，包含：
- `openapi: 3.1.0`
- `info`（title、version、description）
- `servers`（生產 + 本地）
- `paths`（至少覆蓋所有 §3 定義的 Endpoint）
- `components/schemas`（所有 Request/Response Schema）
- `components/responses`（標準錯誤回應）：
  - `Unauthorized`（401）
  - `ValidationError`（400）
  - `NotFound`（404）
  - `TooManyRequests`（429）
- `components/securitySchemes`（BearerAuth JWT）

---

## §13 API Changelog 生成規則

建立版本歷史記錄表格：

| 版本 | 日期 | 變更說明 | 破壞性變更 |
|------|------|---------|-----------|
| v1.0.0 | YYYY-MM-DD | 初始版本 | — |

---

## §14 API Review Checklist 生成規則

完整品質 Checklist，涵蓋：
- 命名一致性（RESTful 規範）
- 錯誤碼標準化
- 認證覆蓋完整性
- 分頁策略正確性
- Rate Limiting 設定
- 冪等性設計
- 文件完整性

---

## §15 API Versioning & Deprecation Policy 生成規則

必須定義：
- 版本廢棄流程：Deprecation headers（`Deprecation: true`、`Sunset: <date>`）
- Migration Guide 提供時程
- 向下相容保證期限（建議至少 6 個月）

---

## §16 Client SDK & Code Generation 生成規則

必須提供至少 1 種語言的 SDK 生成說明：
- 使用 `openapi-generator-cli` 生成指令
- 生成目標（TypeScript/Python/Go 等，依 EDD 技術棧選擇）
- 生成後的使用範例

---

## §17 API Observability & SLO 生成規則

必須定義具體量化目標：

| SLO 指標 | 目標值 | 來源 |
|---------|--------|------|
| 可用性（Availability） | ≥ 99.9% | EDD §10.5 或預設 |
| P95 回應時間 | < 300ms | EDD §10.5 或預設 |
| P99 回應時間 | < 500ms | EDD §10.5 或預設 |
| Error Rate | < 0.1% | EDD §10.5 或預設 |

必須包含：
- Error Budget 計算方式（月可用秒數 × (1 - SLO)）
- 告警閾值定義
- 監測工具說明（APM + 基礎設施監控）

---

## 推斷規則

### Endpoint 推斷與系統化生成

**[強制流程]** 依序執行以下邏輯，確保生成的 endpoint 數量 ≥ `_MIN_ENDPOINT_COUNT`：

**第一層：PRD 功能覆蓋（基礎層）**
- PRD 每個 P0/P1 功能 → 推斷必要的 CRUD 操作
- 規則：
  - P0 功能若涉及「查詢」→ 至少 1 個 GET endpoint
  - P0 功能若涉及「新建」→ 至少 1 個 POST endpoint
  - P0 功能若涉及「修改」→ 至少 1 個 PATCH endpoint
  - P0 功能若涉及「刪除」→ 至少 1 個 DELETE endpoint
- **計數**：統計所有 PRD P0 功能推斷出的 endpoint，記為 `_COUNT_FROM_PRD`

**第二層：UX 交互補充（體驗層）**
- PDD 每個畫面 → 推斷所需的 GET API（欄位對齊）
- 規則：
  - 列表畫面 → GET /{resource} 查詢端點（含分頁 query 參數）
  - 詳情畫面 → GET /{resource}/:id 端點
  - 編輯畫面 → PATCH /{resource}/:id 端點
- **計數**：統計新增的 endpoint，記為 `_COUNT_FROM_PDD`

**第三層：系統功能補充（系統層）**
- EDD 認證設計 → 系統認證/登出 endpoint
  - POST /v1/auth/login（公開）
  - POST /v1/auth/refresh（已認證）
  - POST /v1/auth/logout（已認證）
  - 共 3 個
- EDD Admin 後台 → Admin 管理 endpoint（若 has_admin_backend=true）
  - GET /v1/admin/users（查詢用戶）
  - GET /v1/admin/users/:id（查詢詳情）
  - DELETE /v1/admin/users/:id（刪除用戶）
  - 共 3 個
- **計數**：統計系統級 endpoint，記為 `_COUNT_FROM_SYSTEM`

**終局驗證**：
```python
_TOTAL_ENDPOINT_COUNT = _COUNT_FROM_PRD + _COUNT_FROM_PDD + _COUNT_FROM_SYSTEM

if _TOTAL_ENDPOINT_COUNT < _MIN_ENDPOINT_COUNT:
    # 缺口分析：需要補充 (_MIN_ENDPOINT_COUNT - _TOTAL_ENDPOINT_COUNT) 個 endpoint
    # 補充策略：
    #  1. 查找 PRD 中遺漏的功能（高優先級）
    #  2. 查找 EDD 中遺漏的技術設計（例如：export/import、webhook、通知等）
    #  3. 補充業務管理端點（filter/search、bulk operations 等）
    
    echo "[WARNING] Endpoint count: $TOTAL_ENDPOINT_COUNT < min requirement $_MIN_ENDPOINT_COUNT"
    echo "[Action] 補充 $(( _MIN_ENDPOINT_COUNT - _TOTAL_ENDPOINT_COUNT )) 個 endpoint"
    echo "[Detail] 建議補充的 endpoint："
    echo "  - 若 PRD 涉及批量操作 → POST /{resource}/bulk"
    echo "  - 若 PRD 涉及篩選/搜尋 → GET /{resource}/search 或 GET /{resource}?filter=..."
    echo "  - 若 EDD 有 webhook → POST /webhooks，GET /webhooks/:id"
    echo "  - 若 Admin 有角色管理 → GET/POST /v1/admin/roles"
fi
```

### Endpoint 推斷（基礎規則，無特殊備註）
- PDD 每個畫面 → 推斷所需的 GET API（欄位對齊）
- EDD 認證設計 → 決定哪些 Endpoint 需要 JWT

### 分頁推斷
- 列表類資源一律使用 Cursor-based 分頁（非 OFFSET）
- 大資料集不提供 `total_count`（避免全表掃描）

### 權限推斷
- BRD 定義的使用者角色 → 對應 Endpoint 的 `<role>:read`/`<role>:write` 權限

### Response Schema 推斷
- PDD 畫面欄位 → Response Schema 必須包含所有顯示欄位
- 不得有 PDD 需要但 API 未回傳的欄位

---

## 生成前自我檢核清單

### 量化規格驗證（必填，DRYRUN 依據）

- [ ] **Endpoint 數量達標**：
  ```bash
  ENDPOINT_COUNT=$(grep -c "^#### " docs/API.md || echo "0")
  MIN_REQUIRED=$(jq -r '.quantitative_specs.min_endpoint_count' .gendoc-rules/API-rules.json)
  # ✓ 條件：ENDPOINT_COUNT ≥ MIN_REQUIRED
  # ✗ 否則：補充缺失 endpoint（見「推斷規則」第三層補充策略）
  ```
- [ ] **H2 章節達標**：
  ```bash
  H2_COUNT=$(grep -c "^## " docs/API.md || echo "0")
  MIN_REQUIRED=$(jq -r '.quantitative_specs.min_h2_sections' .gendoc-rules/API-rules.json)
  # ✓ 條件：H2_COUNT ≥ MIN_REQUIRED
  ```
- [ ] **必要章節齊全**（來自 .gendoc-rules/API-rules.json 的 content_specs.required_sections）：
  ```bash
  for section in "API Overview" "Authentication" "Error Codes" "Rate Limiting" "Endpoints"; do
    grep -q "^## $section" docs/API.md || echo "missing: $section"
  done
  ```

### 內容品質驗證

- [ ] 每個 PRD P0 功能都有對應 Endpoint（至少一個）
- [ ] 所有 Endpoint 有完整 Request / Response Schema
- [ ] 每個 Endpoint 有錯誤碼說明（至少 400、401、500）
- [ ] 認證說明完整（取得 / 使用 / 刷新 / Rate Limit）
- [ ] §1 序列圖張數 ≥ §3 中 Mutation Endpoint（POST/PATCH/PUT/DELETE）總數
- [ ] 每張序列圖含 Happy Path + ≥ 2 個 Error Path（業務錯誤 + 系統錯誤）
- [ ] 非同步操作使用 par [async] 塊，重試使用 loop [retry] 塊
- [ ] §1 開頭有「上下游一致性聲明」段落
- [ ] 使用 Cursor-based 分頁（非 OFFSET）
- [ ] §11 API Paradigm Decision 已填寫（REST/GraphQL/gRPC 比較 + 本產品決策 + 決策依據）
- [ ] §12 OpenAPI 3.1 YAML 規格已生成（至少 1 個資源的完整 YAML：paths/components/schemas/responses）
- [ ] §12 components/responses 已定義標準錯誤回應（Unauthorized/ValidationError/NotFound/TooManyRequests）
- [ ] §5 Error Code Registry：所有業務錯誤碼已列出
- [ ] §6 Rate Limiting：三層速率限制（IP / User / Global）已定義
- [ ] §7 Idempotency：需冪等的端點已列出，Idempotency-Key 規範已說明
- [ ] §9 Batch Operations：批次端點（POST /batch，207 Multi-Status）是否已定義？
- [ ] §10 File Upload：檔案上傳端點（multipart/form-data + S3 presigned URL 模式）是否已說明？
- [ ] §13 API Changelog：版本歷史記錄是否已建立？
- [ ] §14 API Review Checklist：完整 API 品質 Checklist 是否已過一遍？
- [ ] §15 API Versioning & Deprecation Policy：版本廢棄流程（Deprecation headers + Sunset date + Migration Guide）是否已定義？
- [ ] §16 Client SDK & Code Generation：至少 1 種語言的 SDK 生成指令（openapi-generator-cli）是否已說明？
- [ ] §17 API Observability & SLO：可用性/P95/P99/錯誤率 SLO 目標是否已定義？Error Budget 計算是否已包含？
- [ ] 所有 `[UPSTREAM_CONFLICT]` 標記均已處理或說明
- [ ] 無未替換的佔位符（`<待填>` 等）

---

### Null vs Absent Field 語意聲明（強制）

API.md 中每個 Response DTO，必須在欄位表格中增加「Nullable」欄位，並區分：
- `null`：欄位存在於 JSON response，但值為 `null`（顯式空）
- `absent`：欄位不出現在 JSON response（完全省略）
- `required`：欄位永遠存在且非 null

| 欄位 | 型別 | 必填 | Nullable | 若為 null 語意 |
|-----|------|------|---------|-------------|
| orderId | UUID | required | no | — |
| deliveredAt | DateTime | absent if not delivered | yes（null = 未配送） | 訂單尚未送達 |
| cancelledReason | String | absent if not cancelled | yes | 訂單未取消 |
| discountAmount | Decimal | optional | yes（null = 無折扣） | 0 折扣 vs 無折扣欄位不同 |

**禁止**：nullable 欄位無說明（工程師無法判斷 null 是錯誤還是合法值）；absent 欄位未標注

### Validation Error Priority Matrix（強制，若 API 有多欄位驗證）

API.md 中的每個請求 endpoint，必須聲明多欄位同時驗證失敗時的錯誤回傳規則：

**規則 A — 第一個失敗即返回**（fail-fast）：
```json
{ "code": "VALIDATION_ERROR", "field": "email", "message": "Invalid email format" }
```

**規則 B — 全部驗證，一次回傳所有錯誤**（collect-all）：
```json
{
  "code": "VALIDATION_ERROR",
  "errors": [
    {"field": "email", "message": "Invalid email format"},
    {"field": "password", "message": "Password too short (min 8 chars)"}
  ]
}
```

每個 POST/PUT/PATCH endpoint 必須標注採用哪個規則：
| Endpoint | 驗證策略 | 排序規則（若 collect-all） |
|---------|---------|----------------------|
| POST /orders | collect-all | 按欄位在 request body 中的宣告順序 |
| POST /auth/login | fail-fast | — |

**禁止**：endpoint 無驗證策略標注；多欄位 endpoint 依賴工程師自行決定

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

> **讀取 lang_stack 方式**：`python3 -c "import json; print(json.load(open('.gendoc-state.json')).get('lang_stack','unknown'))"`

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| 所有 §章節齊全 | 對照 API.md 章節清單，無缺失章節 | 補寫缺失章節 |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | Request/Response 格式、認證方式與 state.lang_stack 一致 | 修正至一致 |
| 數值非 TBD/N/A | Rate limit、Timeout、Payload 大小上限填有實際數字 | 從 EDD 效能需求推算填入 |
| 上游術語對齊 | 資源名稱、欄位名稱與 SCHEMA.md 表格欄位一致 | 以 SCHEMA.md 為準修正 |
| 回應碼完整性 | 需認證 endpoint 有 401/403；有限速有 429；所有 endpoint 有 500 和至少一個 2XX | 依條件補充缺失回應碼 |
| 範例值真實 | 所有 example 欄位使用真實格式（非 "string" / "1" / "test"） | 替換為符合業務語義的範例值 |
| HA Resilience 覆蓋 | §14 HA 核查清單 6 項全部回答（Timeout/Retry/冪等/RateLimit CB/Graceful Shutdown）| 補充缺失說明 |
| Admin API 完整性（條件） | has_admin_backend=true 時：§18 Admin API 覆蓋 auth/users/roles/audit-logs 全部端點 | 補充缺失端點 |

### Admin Backend 條件步驟（has_admin_backend=true 時執行）

```python
_has_admin = state.get("has_admin_backend", False)
if _has_admin:
    # 生成 §18 Admin API 章節
    # §18.0: 填寫 Admin API 基礎規範（Base URL/認證/限速/稽核）
    # §18.1: 生成 Admin 認證端點（login/refresh/logout，含 TOTP 支援）
    # §18.2: 生成用戶管理端點（列表/詳情/停用/重設密碼/刪除）
    # §18.3: 生成角色管理端點（角色 CRUD + Permission 分配 + 角色授權）
    # §18.4: 生成稽核日誌端點（列表/詳情/CSV 導出）
    # §18.5: 依 PRD §19.3 業務模組補充業務管理端點
    # Token TTL 常數從 CONSTANTS.md 讀取（ADMIN_ACCESS_TOKEN_TTL）
    # 確認所有端點都有 Permission 欄位（格式：module.action）
else:
    # §18 寫入：「本專案無 Admin 後台（has_admin_backend=false），略過 §18。」
```
