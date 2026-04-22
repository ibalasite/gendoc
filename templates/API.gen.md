---
doc-type: API
output-path: docs/API.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md
  - docs/EDD.md
  - docs/ARCH.md
quality-bar: "每個 PRD P0 功能都有對應 Endpoint；所有 Endpoint 有完整 Request/Response Schema；認證、分頁、錯誤碼說明完整；§11 API Paradigm Decision 已填寫；§12 OpenAPI 3.1 YAML 已生成；§17 SLO 目標已定義"
---

# API.gen.md — API 文件生成規則

依 EDD + PRD 產出 OpenAPI 風格的 API.md，涵蓋所有端點與 Schema 定義。

---

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## 上游文件讀取規則

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

## §1 認證生成規則

必須包含以下完整說明：
- 取得 Token（POST /api/v1/auth/login）：Request Body + Response 200 結構
- 使用 Token（Authorization: Bearer header）
- Refresh Token（POST /api/v1/auth/refresh）
- Rate Limit 設定（Auth endpoints：10 req/min/IP；API endpoints：100 req/min/user）

---

## §2 Endpoint 列表生成規則

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

## §3 共用 Schema 定義生成規則

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

## §4 API 呼叫序列圖生成規則

- 依 PRD 的主要使用情境，繪製 **1～3 個**代表性的 API 呼叫序列
- 使用 Mermaid `sequenceDiagram` 語法
- 必須包含以下兩種序列：

**讀取操作序列：**
- 涵蓋 JWT 驗證 → Cache Hit/Miss → DB 查詢流程
- 參與者：Client、API Gateway、Auth Service、Domain Service、PostgreSQL、Redis

**寫入操作序列：**
- 涵蓋 Schema validation → 業務規則檢查 → Repository → DB INSERT 流程
- 參與者：Client、API Handler、Service、Repository、PostgreSQL

---

## §5 Webhook 生成規則（若有）

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
- `paths`（至少覆蓋所有 §2 定義的 Endpoint）
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

### Endpoint 推斷
- PRD 每個功能 → 推斷 CRUD 操作需求
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

- [ ] 每個 PRD P0 功能都有對應 Endpoint（至少一個）
- [ ] 所有 Endpoint 有完整 Request / Response Schema
- [ ] 每個 Endpoint 有錯誤碼說明（至少 400、401、500）
- [ ] 認證說明完整（取得 / 使用 / 刷新 / Rate Limit）
- [ ] §4 有至少 1 個 API 序列圖（Mermaid sequenceDiagram）
- [ ] 使用 Cursor-based 分頁（非 OFFSET）
- [ ] §11 API Paradigm Decision 已填寫（REST/GraphQL/gRPC 比較 + 本產品決策 + 決策依據）
- [ ] §12 OpenAPI 3.1 YAML 規格已生成（至少 1 個資源的完整 YAML：paths/components/schemas/responses）
- [ ] §12 components/responses 已定義標準錯誤回應（Unauthorized/ValidationError/NotFound/TooManyRequests）
- [ ] §9 Batch Operations：批次端點（POST /batch，207 Multi-Status）是否已定義？
- [ ] §10 File Upload：檔案上傳端點（multipart/form-data + S3 presigned URL 模式）是否已說明？
- [ ] §13 API Changelog：版本歷史記錄是否已建立？
- [ ] §14 API Review Checklist：完整 API 品質 Checklist 是否已過一遍？
- [ ] §15 API Versioning & Deprecation Policy：版本廢棄流程（Deprecation headers + Sunset date + Migration Guide）是否已定義？
- [ ] §16 Client SDK & Code Generation：至少 1 種語言的 SDK 生成指令（openapi-generator-cli）是否已說明？
- [ ] §17 API Observability & SLO：可用性/P95/P99/錯誤率 SLO 目標是否已定義？Error Budget 計算是否已包含？
- [ ] 所有 `[UPSTREAM_CONFLICT]` 標記均已處理或說明
- [ ] 無未替換的佔位符（`<待填>` 等）
