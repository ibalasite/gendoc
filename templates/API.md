# API — API 設計文件

## Document Control

| 欄位 | 值 |
|------|-----|
| Document ID | `API-{{PROJECT_SLUG}}-{{YYYYMMDD}}` |
| Version | `{{VERSION}}` |
| Status | Draft / In Review / Approved / Deprecated |
| Classification | Internal / Confidential |
| Owner | Backend Lead / API Guild |
| **Owning Bounded Context / Service** | **{{BC_NAME}}**（對應 ARCH §4 / EDD §3.4；本 API 的唯一發布服務） |
| Created | {{YYYYMMDD}} |
| Last Updated | {{YYYYMMDD}} |
| Upstream EDD | [docs/EDD.md](docs/EDD.md) |
| Upstream PRD | [docs/PRD.md](docs/PRD.md) |
| OpenAPI Spec | [docs/openapi.yaml](docs/openapi.yaml) |
| Changelog | [See §13 Changelog](#13-api-changelog) |

## Change Log

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | {{YYYYMMDD}} | {{AUTHOR}} | Initial draft |

---

## 1. 概述

| 項目 | 值 |
|------|-----|
| Base URL (Production) | `https://api.{{DOMAIN}}.com` |
| Base URL (Staging) | `https://api-staging.{{DOMAIN}}.com` |
| Base URL (Development) | `http://localhost:{{PORT}}` |
| API 版本 | `v1`（URL prefix：`/api/v1/`） |
| 認證方式 | Bearer Token（JWT）/ API Key（Service-to-Service） |
| 資料格式 | `application/json`（UTF-8） |
| 時間格式 | ISO 8601，UTC（`2024-01-01T00:00:00Z`） |
| ID 格式 | UUID v4 |

### 1.1 設計原則

- RESTful 資源導向設計，URL 使用名詞複數（`/users`，非 `/getUsers`）
- 冪等性：GET、PUT、DELETE 皆為冪等操作
- 向後相容：新欄位以 additive 方式加入，不移除或重命名現有欄位
- 所有狀態變更操作須攜帶 `Idempotency-Key` 標頭
- **Service Encapsulation（Spring Modulith HC-2）**：本 API 是其 Bounded Context（`{{BC_NAME}}`）的**唯一對外介面**；其他 BC 的服務不得直接存取本 BC 的 DB Schema；API Response 欄位名稱**不得直接暴露 DB 欄位名稱**作為穩定合約（必須有 DTO/View Model 層隔離，DB 欄位重命名不能影響 API Contract）

### 1.2 Bounded Context 歸屬（HC-2）

> 此節宣告本 API 文件所覆蓋的 Bounded Context 範圍。每個 BC 有且僅有一份 API 文件（單一職責）；跨 BC 呼叫需透過對方 BC 的 API 文件中定義的端點。

| Bounded Context | Path Prefix | Owning Team | Owned DB Schema（對應 SCHEMA.md） |
|-----------------|------------|------------|----------------------------------|
| {{BC_NAME_1}} | `/api/v1/{{bc1_prefix}}/` | {{TEAM_NAME_1}} | `{{schema_1}}`: `{{table_a}}`, `{{table_b}}` |
| {{BC_NAME_2}} | `/api/v1/{{bc2_prefix}}/` | {{TEAM_NAME_2}} | `{{schema_2}}`: `{{table_c}}`, `{{table_d}}` |

*（每個 BC 一列；Path Prefix 必須與 §3 的 BC 分組標題一致；Owned DB Schema 必須與 ARCH.md §4.0 映射表一致）*

---

## 2. 通用規範

### 2.1 Standard Request Headers

所有 API 請求必須包含以下標頭：

| 標頭 | 格式 | 必填 | 說明 |
|------|------|------|------|
| `Authorization` | `Bearer <jwt_token>` | 是（認證端點除外） | JWT access token |
| `Content-Type` | `application/json` | POST/PATCH/PUT | 請求 body 格式 |
| `Accept` | `application/json` | 建議 | 可接受的回應格式 |
| `X-Request-ID` | UUID v4 | 建議 | 追蹤用唯一請求 ID；若未提供，伺服器自動產生 |
| `Idempotency-Key` | UUID v4 | POST/PATCH/DELETE 必填 | 防重複提交；伺服器快取 24 小時 |
| `X-API-Version` | `2024-01-01` | 否 | 日期式版本 pin，用於跨版本相容 |
| `Accept-Language` | `zh-TW`, `en-US` | 否 | 錯誤訊息語系；預設 `zh-TW` |

**範例：**
```http
POST /api/v1/orders HTTP/1.1
Host: api.{{DOMAIN}}.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
Idempotency-Key: 7d793037-a076-4c05-9a70-b7e8b2e3c4f5
X-API-Version: 2024-01-01
Accept-Language: zh-TW
```

### 2.2 Standard Response Headers

所有 API 回應必定包含以下標頭：

| 標頭 | 格式 | 說明 |
|------|------|------|
| `X-Request-ID` | UUID v4 | Echo 回請求的 Request ID（或伺服器產生）|
| `X-RateLimit-Limit` | integer | 當前時間窗口的請求上限 |
| `X-RateLimit-Remaining` | integer | 當前時間窗口的剩餘請求次數 |
| `X-RateLimit-Reset` | Unix timestamp | 速率限制重置的時間點（秒） |
| `X-Response-Time` | `<ms>ms` | 伺服器處理時間，例如 `42ms` |
| `Content-Type` | `application/json; charset=utf-8` | 回應格式 |

**範例：**
```http
HTTP/1.1 200 OK
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1704067200
X-Response-Time: 38ms
Content-Type: application/json; charset=utf-8
```

### 2.3 Standard Response Body

**成功（單一資源）：**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "範例資源",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**成功（列表資源）：**
```json
{
  "success": true,
  "data": [
    { "id": "uuid-1", "name": "資源 A" },
    { "id": "uuid-2", "name": "資源 B" }
  ],
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T00:00:00Z",
    "pagination": {
      "total": 100,
      "page": 1,
      "limit": 20,
      "has_next": true,
      "next_cursor": "eyJpZCI6InV1aWQtMjAifQ=="
    }
  }
}
```

**失敗：**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_RESOURCE_FIELD_REQUIRED",
    "message": "欄位驗證失敗",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T00:00:00Z",
    "docs_url": "https://docs.{{DOMAIN}}.com/errors/VALIDATION_RESOURCE_FIELD_REQUIRED",
    "details": [
      { "field": "email", "message": "Email 格式不正確", "code": "INVALID_FORMAT" }
    ]
  }
}
```

### 2.4 HTTP Status Code

| 情境 | Status | 說明 |
|------|--------|------|
| 查詢成功 | 200 OK | 回傳資源或列表 |
| 建立成功 | 201 Created | 含 Location header 指向新資源 |
| 非同步任務接受 | 202 Accepted | 任務已排隊，非即時完成 |
| 無內容 | 204 No Content | 刪除成功，無回應 body |
| 部分成功 | 207 Multi-Status | Batch 操作部分成功 |
| 參數錯誤 | 400 Bad Request | 格式錯誤、缺少必填欄位 |
| 未認證 | 401 Unauthorized | Token 無效或過期 |
| 無權限 | 403 Forbidden | 已認證但無操作權限 |
| 找不到 | 404 Not Found | 資源不存在 |
| 方法不允許 | 405 Method Not Allowed | HTTP method 不支援 |
| 衝突 | 409 Conflict | 資源已存在，違反唯一性約束 |
| 格式正確但邏輯失敗 | 422 Unprocessable Entity | 欄位驗證失敗 |
| 速率超限 | 429 Too Many Requests | 含 Retry-After header |
| 伺服器錯誤 | 500 Internal Server Error | 含 request_id 供追蹤 |
| 服務不可用 | 503 Service Unavailable | 含 Retry-After header |

### 2.5 Pagination — 游標式（Cursor-Based）

適用情境：高頻更新列表、大資料集、無限捲動。

**Request：**
```http
GET /api/v1/{{RESOURCE}}?limit=20&cursor=eyJpZCI6InV1aWQtMjAifQ==&direction=next
```

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `limit` | integer | 否 | 每頁筆數，預設 20，最大 100 |
| `cursor` | string | 否 | Base64 編碼的游標，首頁省略 |
| `direction` | `next`\|`prev` | 否 | 翻頁方向，預設 `next` |

**Response：**
```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "pagination": {
      "limit": 20,
      "has_next": true,
      "has_prev": true,
      "next_cursor": "eyJpZCI6InV1aWQtNDAifQ==",
      "prev_cursor": "eyJpZCI6InV1aWQtMSJ9"
    }
  }
}
```

### 2.6 Pagination — 位移式（Offset-Based）

適用情境：需要跳頁、固定頁碼顯示的 admin 介面。

**Request：**
```http
GET /api/v1/{{RESOURCE}}?page=3&limit=20&sort=created_at&order=desc
```

| 參數 | 類型 | 必填 | 說明 | 預設 |
|------|------|------|------|------|
| `page` | integer | 否 | 頁碼（1 起始） | 1 |
| `limit` | integer | 否 | 每頁筆數（最大 100） | 20 |
| `sort` | string | 否 | 排序欄位 | `created_at` |
| `order` | `asc`\|`desc` | 否 | 排序方向 | `desc` |

**Response：**
```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "pagination": {
      "total": 243,
      "page": 3,
      "limit": 20,
      "total_pages": 13,
      "has_next": true,
      "has_prev": true
    }
  }
}
```

### 2.7 Versioning Strategy

本 API 採用 **URL 路徑版本化**（`/api/v1/`、`/api/v2/`）。

| 規則 | 說明 |
|------|------|
| Breaking change | 必須升主版號（v1 → v2） |
| Non-breaking addition | 可在現有版本以 additive 方式加入 |
| 棄用通知 | 至少提前 **90 天**以 `Deprecation` + `Sunset` header 通知 |
| 舊版本維護 | 主版號升級後，舊版本維護期至少 **180 天** |

**棄用 Response Headers：**
```http
Deprecation: Sat, 01 Jun 2024 00:00:00 GMT
Sunset: Mon, 01 Dec 2025 00:00:00 GMT
Link: <https://docs.{{DOMAIN}}.com/migration/v2>; rel="successor-version"
```

---

## 3. Endpoints

> **組織原則（Spring Modulith HC-2）**：本節所有 Endpoint 依所屬 Bounded Context 分組，每個 BC 為一個一級子章節（`### BC: {{BC_NAME}}`）。BC 邊界與 §1.2 Bounded Context 歸屬表一致；每個 Endpoint 只屬於一個 BC；Endpoint Path Prefix 必須對應其 Owning BC（例：`/api/v1/members/` → `member BC`）。

### BC: {{BC_NAME_1}} Endpoints

> **Owning BC**：{{BC_NAME_1}} | **Path Prefix**：`/api/v1/{{bc1_prefix}}/` | **Owned Tables**：`{{schema_1}}`: `{{table_a}}`, `{{table_b}}`

### 3.1 {{RESOURCE_NAME}}（{{資源中文名稱}}）

> 資源描述：{{一句話說明此資源的業務語義}}

#### `GET /api/v1/{{RESOURCE}}`

列出資源列表。支援游標式與位移式分頁（透過 `cursor` 或 `page` 參數切換）。

**Query Parameters：**

| 參數 | 類型 | 必填 | 說明 | 預設 |
|------|------|------|------|------|
| `page` | integer | 否 | 頁碼（offset 模式） | 1 |
| `limit` | integer | 否 | 每頁筆數（最大 100） | 20 |
| `cursor` | string | 否 | 游標（cursor 模式，與 page 互斥） | — |
| `sort` | string | 否 | 排序欄位 | `created_at` |
| `order` | `asc`\|`desc` | 否 | 排序方向 | `desc` |
| `filter[status]` | string | 否 | 依狀態過濾 | — |

**Response 200：**
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "範例資源",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "request_id": "req-uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "pagination": {
      "total": 100,
      "page": 1,
      "limit": 20,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

#### `GET /api/v1/{{RESOURCE}}/:id`

取得單一資源。

**Path Parameters：**

| 參數 | 類型 | 說明 |
|------|------|------|
| `id` | UUID v4 | 資源 ID |

**Response 200：**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "範例資源",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "meta": {
    "request_id": "req-uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Response 404：**
```json
{
  "success": false,
  "error": {
    "code": "{{RESOURCE_UPPER}}_NOT_FOUND",
    "message": "資源不存在",
    "request_id": "req-uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "docs_url": "https://docs.{{DOMAIN}}.com/errors/{{RESOURCE_UPPER}}_NOT_FOUND"
  }
}
```

---

#### `POST /api/v1/{{RESOURCE}}`

建立新資源。此端點為非冪等操作，**必須攜帶 `Idempotency-Key`**。

**Request Headers（額外必填）：**
```http
Idempotency-Key: 7d793037-a076-4c05-9a70-b7e8b2e3c4f5
```

**Request Body：**
```json
{
  "name": "string（必填，1–255 字）",
  "description": "string（選填，最長 2000 字）",
  "status": "active | inactive（選填，預設 active）"
}
```

**驗證規則：**

| 欄位 | 規則 |
|------|------|
| `name` | 必填，非空字串，1–255 字元 |
| `description` | 選填，最長 2000 字元 |
| `status` | 選填，枚舉值：`active`、`inactive`，預設 `active` |

**Response 201：**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "新資源",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "meta": {
    "request_id": "req-uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Response Headers（201）：**
```http
Location: /api/v1/{{RESOURCE}}/550e8400-e29b-41d4-a716-446655440000
```

**Response 422：**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_{{RESOURCE_UPPER}}_FIELD_REQUIRED",
    "message": "欄位驗證失敗",
    "request_id": "req-uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "docs_url": "https://docs.{{DOMAIN}}.com/errors/VALIDATION_{{RESOURCE_UPPER}}_FIELD_REQUIRED",
    "details": [
      { "field": "name", "message": "必填欄位不可為空", "code": "FIELD_REQUIRED" }
    ]
  }
}
```

---

#### `PATCH /api/v1/{{RESOURCE}}/:id`

部分更新資源（Partial Update）。所有欄位選填，但至少一個欄位須提供。攜帶 `Idempotency-Key`。

**Request Body：**（所有欄位選填，至少一個）
```json
{
  "name": "string（選填）",
  "description": "string（選填）",
  "status": "active | inactive（選填）"
}
```

**Response 200：** 回傳更新後的完整資源（格式同 GET /:id Response 200）

**Response 409（衝突）：**
```json
{
  "success": false,
  "error": {
    "code": "{{RESOURCE_UPPER}}_NAME_CONFLICT",
    "message": "資源名稱已存在",
    "request_id": "req-uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "docs_url": "https://docs.{{DOMAIN}}.com/errors/{{RESOURCE_UPPER}}_NAME_CONFLICT"
  }
}
```

---

#### `DELETE /api/v1/{{RESOURCE}}/:id`

軟刪除資源（設定 `deleted_at`，不實際移除記錄）。攜帶 `Idempotency-Key`。

**Response 204：** No Content（成功刪除，無 body）

**Response 404：** 資源不存在（格式同 GET /:id Response 404）

---

## 4. Authentication & Authorization

### 4.1 JWT 結構

```
Header.Payload.Signature
```

**Header：**
```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "key-id-2024-01"
}
```

**Payload：**
```json
{
  "sub": "user-uuid",
  "iss": "https://auth.{{DOMAIN}}.com",
  "aud": "https://api.{{DOMAIN}}.com",
  "exp": 1704070800,
  "iat": 1704067200,
  "jti": "jwt-unique-id",
  "scope": "read:orders write:orders",
  "roles": ["user", "admin"]
}
```

**Signature：** RS256（私鑰簽署，公鑰驗證）。JWKs 端點：`https://auth.{{DOMAIN}}.com/.well-known/jwks.json`

### 4.2 Token 生命週期

| Token 類型 | 有效期 | 儲存建議 |
|-----------|--------|---------|
| `access_token` | 1 小時 | Memory（不寫入 localStorage） |
| `refresh_token` | 7 天 | HttpOnly Cookie |

### 4.3 OAuth2 授權流程（Authorization Code + PKCE）

```mermaid
sequenceDiagram
    participant User
    participant Client
    participant AuthServer as Auth Server
    participant API

    User->>Client: 點擊登入
    Client->>Client: 產生 code_verifier + code_challenge (S256)
    Client->>AuthServer: GET /authorize?response_type=code&code_challenge=...
    AuthServer->>User: 顯示登入頁面
    User->>AuthServer: 輸入帳密
    AuthServer->>Client: 302 redirect?code=AUTH_CODE
    Client->>AuthServer: POST /token {code, code_verifier}
    AuthServer->>Client: {access_token, refresh_token}
    Client->>API: Authorization: Bearer <access_token>
    API->>Client: 200 OK + 資料
```

### 4.4 Token 刷新流程

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGci..."
}
```

**Response 200：**
```json
{
  "access_token": "eyJhbGci...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

**Response 401（refresh_token 過期）：**
```json
{
  "success": false,
  "error": {
    "code": "AUTH_REFRESH_TOKEN_EXPIRED",
    "message": "Refresh token 已過期，請重新登入",
    "request_id": "req-uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 4.5 API Key（Service-to-Service）

機器對機器場景使用靜態 API Key，透過 `X-API-Key` 標頭傳遞：

```http
X-API-Key: sk_live_{{API_KEY}}
```

- API Key 不得出現在 URL query string（會被記錄於 access log）
- 生產環境 API Key 透過 Vault / Secret Manager 注入，不得寫入程式碼
- API Key 應設定 IP allowlist 及 scope 限制

### 4.6 Role-Based Access Control (RBAC)

| Role | 說明 | 可操作範圍 |
|------|------|-----------|
| `viewer` | 唯讀使用者 | GET only |
| `editor` | 一般使用者 | GET, POST, PATCH |
| `admin` | 管理員 | 全部 + DELETE |
| `service` | 服務帳號 | 依 scope 定義 |

---

## 5. Error Handling

### 5.1 Error Response Schema

所有錯誤回應遵循統一格式：

```json
{
  "success": false,
  "error": {
    "code": "DOMAIN_ENTITY_REASON",
    "message": "人類可讀的錯誤描述（依 Accept-Language）",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T00:00:00Z",
    "docs_url": "https://docs.{{DOMAIN}}.com/errors/DOMAIN_ENTITY_REASON",
    "details": [
      {
        "field": "欄位名稱",
        "message": "欄位層級錯誤說明",
        "code": "FIELD_LEVEL_ERROR_CODE",
        "value": "使用者提供的無效值（敏感資訊除外）"
      }
    ]
  }
}
```

錯誤碼格式：`DOMAIN_ENTITY_REASON`（全大寫底線分隔）

### 5.2 Error Code Registry

| 錯誤碼 | HTTP Status | 說明 |
|--------|------------|------|
| `AUTH_TOKEN_INVALID` | 401 | JWT 格式錯誤或簽名無效 |
| `AUTH_TOKEN_EXPIRED` | 401 | Access token 已過期 |
| `AUTH_REFRESH_TOKEN_EXPIRED` | 401 | Refresh token 已過期，需重新登入 |
| `AUTH_INSUFFICIENT_SCOPE` | 403 | Token scope 不足以執行此操作 |
| `AUTH_ROLE_FORBIDDEN` | 403 | 使用者角色無此操作權限 |
| `VALIDATION_FIELD_REQUIRED` | 422 | 必填欄位缺失 |
| `VALIDATION_FIELD_INVALID_FORMAT` | 422 | 欄位格式不符（如 email、uuid） |
| `VALIDATION_FIELD_TOO_LONG` | 422 | 欄位超過最大長度限制 |
| `VALIDATION_FIELD_OUT_OF_RANGE` | 422 | 數值超出允許範圍 |
| `VALIDATION_ENUM_INVALID` | 422 | 枚舉值不在允許列表中 |
| `{{RESOURCE_UPPER}}_NOT_FOUND` | 404 | 指定資源不存在 |
| `{{RESOURCE_UPPER}}_ALREADY_EXISTS` | 409 | 資源已存在（違反唯一性約束） |
| `{{RESOURCE_UPPER}}_STATE_CONFLICT` | 409 | 資源當前狀態不允許此操作 |
| `RATE_LIMIT_EXCEEDED` | 429 | 請求頻率超限 |
| `IDEMPOTENCY_KEY_CONFLICT` | 409 | Idempotency-Key 已存在但請求 body 不同 |
| `BATCH_PARTIAL_FAILURE` | 207 | Batch 操作部分成功 |
| `FILE_SIZE_EXCEEDED` | 400 | 上傳檔案超過大小限制 |
| `FILE_TYPE_NOT_ALLOWED` | 400 | 檔案類型不在允許清單中 |
| `INTERNAL_SERVER_ERROR` | 500 | 伺服器內部錯誤，request_id 供追蹤 |
| `SERVICE_UNAVAILABLE` | 503 | 服務暫時不可用，含 Retry-After |

---

## 6. Rate Limiting

### 6.1 限制層級

| 層級 | 限制對象 | 限制規則 |
|------|---------|---------|
| Per-User | 已認證使用者 UUID | 1,000 req / 1 min（一般 API） |
| Per-IP | 客戶端 IP | 200 req / 1 min（匿名請求） |
| Per-Endpoint（認證） | IP + 端點 | 10 req / 1 min（`/auth/*`） |
| Per-Endpoint（高代價） | User + 端點 | 20 req / 1 min（Export、Batch） |
| Service Account | API Key | 10,000 req / 1 min |

### 6.2 Burst 容許機制

在短時間內允許超過平均速率，但不超過 burst 上限：

| 端點類型 | 平均速率 | Burst 上限 |
|---------|---------|-----------|
| 一般 API | 1,000/min | 200/10s |
| 認證 API | 10/min | 3/10s |

### 6.3 429 Response 格式

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067260
Retry-After: 42
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "請求頻率超限，請於 42 秒後重試",
    "request_id": "req-uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "docs_url": "https://docs.{{DOMAIN}}.com/errors/RATE_LIMIT_EXCEEDED",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_at": "2024-01-01T00:01:00Z",
      "retry_after_seconds": 42
    }
  }
}
```

---

## 7. Idempotency

### 7.1 設計原則

Idempotency-Key 確保相同請求在網路重試時不會產生重複副作用。

### 7.2 哪些端點必須使用

| HTTP Method | 狀態變更 | 是否必填 |
|-------------|---------|---------|
| `POST` | 建立資源 | **必填** |
| `PATCH` | 修改狀態 | **必填** |
| `DELETE` | 刪除資源 | **必填** |
| `GET` | 查詢 | 不需要 |

### 7.3 伺服器行為

1. 收到請求時，以 `Idempotency-Key` 為索引查詢快取
2. 若快取命中 → 直接回傳原始 Response（不重複執行邏輯）
3. 若快取未命中 → 執行業務邏輯，將結果存入快取（TTL 24 小時）
4. 若相同 key 但 request body 不同 → 回傳 `409 IDEMPOTENCY_KEY_CONFLICT`

### 7.4 Key 規範

```http
Idempotency-Key: 7d793037-a076-4c05-9a70-b7e8b2e3c4f5
```

- 格式：UUID v4（Client 自行產生）
- 生命週期：24 小時（超過後可重用，視為新請求）
- 每個 Idempotency-Key 僅對應單一使用者 + 端點組合

---

## 8. Webhooks

> 若本系統不需要 Webhook，可移除此章節。

### 8.1 事件類型

| 事件 | 說明 | 觸發時機 |
|------|------|---------|
| `{{RESOURCE}}.created` | 資源建立 | POST 成功後 |
| `{{RESOURCE}}.updated` | 資源更新 | PATCH 成功後 |
| `{{RESOURCE}}.deleted` | 資源刪除 | DELETE 成功後 |
| `{{RESOURCE}}.status_changed` | 狀態異動 | 狀態流轉時 |

### 8.2 Payload 格式（CloudEvents 標準）

```json
{
  "specversion": "1.0",
  "type": "com.{{DOMAIN}}.{{RESOURCE}}.created",
  "source": "https://api.{{DOMAIN}}.com/api/v1/{{RESOURCE}}",
  "id": "event-uuid",
  "time": "2024-01-01T00:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "id": "resource-uuid",
    "name": "資源名稱",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### 8.3 簽名驗證（HMAC-SHA256）

每次 Webhook 請求附帶簽名 Header：

```http
X-Webhook-Signature: sha256=abc123...
X-Webhook-Timestamp: 1704067200
```

**驗證方式（Node.js 範例）：**
```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, timestamp, secret) {
  const tolerance = 300; // 5 分鐘容許誤差
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - parseInt(timestamp)) > tolerance) {
    throw new Error('Webhook timestamp out of tolerance');
  }
  const expectedSig = crypto
    .createHmac('sha256', secret)
    .update(`${timestamp}.${payload}`)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(`sha256=${expectedSig}`),
    Buffer.from(signature)
  );
}
```

### 8.4 重試策略

| 嘗試次數 | 延遲（指數退避） |
|---------|----------------|
| 第 1 次 | 立即 |
| 第 2 次 | 30 秒後 |
| 第 3 次 | 5 分鐘後 |
| 超過 3 次 | 標記為失敗，推入 Dead Letter Queue |

- HTTP 2xx 視為成功，其餘觸發重試
- 重試期間保持相同 `id`（事件冪等性）

---

## 9. Batch Operations

### 9.1 批次建立

```http
POST /api/v1/{{RESOURCE}}/batch
Idempotency-Key: batch-uuid
Content-Type: application/json

{
  "items": [
    { "name": "資源 A", "status": "active" },
    { "name": "資源 B", "status": "inactive" },
    { "name": "", "status": "invalid-status" }
  ]
}
```

- 單次最多 **100 筆**
- 採用 **Partial Success**：部分失敗不影響其餘項目

**Response 207 Multi-Status：**
```json
{
  "success": true,
  "data": {
    "succeeded": 2,
    "failed": 1,
    "results": [
      { "index": 0, "status": 201, "data": { "id": "uuid-a", "name": "資源 A" } },
      { "index": 1, "status": 201, "data": { "id": "uuid-b", "name": "資源 B" } },
      {
        "index": 2,
        "status": 422,
        "error": {
          "code": "VALIDATION_FIELD_REQUIRED",
          "message": "name 為必填欄位",
          "details": [{ "field": "name", "message": "必填欄位不可為空" }]
        }
      }
    ]
  },
  "meta": { "request_id": "req-uuid", "timestamp": "2024-01-01T00:00:00Z" }
}
```

### 9.2 批次刪除

```http
DELETE /api/v1/{{RESOURCE}}/batch
Idempotency-Key: batch-delete-uuid
Content-Type: application/json

{
  "ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

**Response 207：** 同批次建立格式，每筆結果 status 為 `204`（成功）或錯誤碼

---

## 10. File Upload

### 10.1 單檔上傳

```http
POST /api/v1/{{RESOURCE}}/:id/attachments
Authorization: Bearer <token>
Idempotency-Key: upload-uuid
Content-Type: multipart/form-data; boundary=---boundary

---boundary
Content-Disposition: form-data; name="file"; filename="document.pdf"
Content-Type: application/pdf

<binary data>
---boundary
Content-Disposition: form-data; name="description"

上傳說明文字
---boundary--
```

**限制：**

| 項目 | 限制 |
|------|------|
| 單檔大小 | 最大 **50 MB** |
| 允許格式 | `image/jpeg`, `image/png`, `image/webp`, `application/pdf`, `text/csv` |
| 同時上傳數量 | 最多 **5 個** `multipart` part |
| 病毒掃描 | 非同步執行（`status` 初始為 `scanning`） |

**Response 202（已接受，掃描中）：**
```json
{
  "success": true,
  "data": {
    "id": "attachment-uuid",
    "status": "scanning",
    "filename": "document.pdf",
    "size_bytes": 204800,
    "mime_type": "application/pdf",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "meta": { "request_id": "req-uuid", "timestamp": "2024-01-01T00:00:00Z" }
}
```

**掃描完成後（透過 Webhook `attachment.ready`）：**
```json
{
  "id": "attachment-uuid",
  "status": "ready",
  "url": "https://cdn.{{DOMAIN}}.com/attachments/attachment-uuid/document.pdf",
  "expires_at": "2024-07-01T00:00:00Z"
}
```

**掃描失敗（偵測到惡意內容）：**
```json
{
  "id": "attachment-uuid",
  "status": "rejected",
  "reason": "VIRUS_DETECTED"
}
```

---

## 11. API Paradigm Decision（API 範式決策）

| 評估維度 | REST | GraphQL | gRPC |
|---------|:----:|:-------:|:----:|
| 瀏覽器 / 公開客戶端 | ✅ 最佳 | ✅ 良好 | ❌ 受限 |
| 靈活的資料查詢（避免 over/under-fetching）| ❌ 弱 | ✅ 最佳 | ❌ 弱 |
| 即時 / Streaming | ⚠️ SSE/WebSocket | ⚠️ Subscription | ✅ 最佳 |
| 服務間通訊（高效能）| ❌ 效率較低 | ❌ 效率較低 | ✅ 最佳 |
| 型別安全 + 程式碼生成 | ⚠️ OpenAPI | ⚠️ SDL | ✅ 最佳 |
| 生態系與工具成熟度 | ✅ 最成熟 | ✅ 成熟 | ✅ 成熟 |
| 快取支援 | ✅ HTTP 原生快取 | ⚠️ 需自訂 | ❌ 需自訂 |

**本產品決策：{{CHOSEN_PARADIGM}}**

**決策依據：** {{DECISION_RATIONALE}}

**備選考量（若需要）：**
- 若需要服務間高效通訊 → 引入 gRPC for internal services
- 若前端需要靈活查詢 → 引入 GraphQL layer（BFF Pattern）
- 即時功能 → {{REALTIME_APPROACH}}（SSE / WebSocket / Long-Polling）

---

## 12. OpenAPI 3.1 Specification Example（規格範本）

> 完整 OpenAPI 規格維護於 `docs/openapi.yaml`。以下展示單一資源（`{{RESOURCE}}`）的標準規格範本，供所有端點遵循。

```yaml
# docs/openapi.yaml — 完整 OpenAPI 3.1 規格
openapi: "3.1.0"
info:
  title: "{{APP_NAME}} API"
  version: "{{API_VERSION}}"
  description: "{{APP_DESCRIPTION}}"
  contact:
    name: "{{TEAM_NAME}}"
    email: "{{TEAM_EMAIL}}"
  license:
    name: "{{LICENSE}}"

servers:
  - url: "https://api.{{DOMAIN}}/v1"
    description: "Production"
  - url: "https://staging-api.{{DOMAIN}}/v1"
    description: "Staging"

security:
  - BearerAuth: []

paths:
  /{{RESOURCE_PLURAL}}:
    get:
      summary: "List {{RESOURCE_PLURAL}}"
      operationId: "list{{ResourcePascal}}"
      tags: ["{{ResourcePascal}}"]
      parameters:
        - name: page
          in: query
          schema: { type: integer, minimum: 1, default: 1 }
        - name: per_page
          in: query
          schema: { type: integer, minimum: 1, maximum: 100, default: 20 }
        - name: sort
          in: query
          schema: { type: string, enum: [created_at_asc, created_at_desc, updated_at_desc] }
        - name: filter[status]
          in: query
          schema: { type: string, enum: [active, inactive, pending] }
      responses:
        "200":
          description: "Success"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/{{ResourcePascal}}ListResponse"
        "401": { $ref: "#/components/responses/Unauthorized" }
        "429": { $ref: "#/components/responses/TooManyRequests" }

    post:
      summary: "Create {{RESOURCE}}"
      operationId: "create{{ResourcePascal}}"
      tags: ["{{ResourcePascal}}"]
      parameters:
        - name: Idempotency-Key
          in: header
          required: false
          schema: { type: string, format: uuid }
          description: "Idempotency key for safe retries (UUID v4)"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Create{{ResourcePascal}}Request"
      responses:
        "201":
          description: "Created"
          headers:
            Location:
              schema: { type: string }
              description: "URL of created resource"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/{{ResourcePascal}}Response"
        "400": { $ref: "#/components/responses/ValidationError" }
        "401": { $ref: "#/components/responses/Unauthorized" }
        "409": { $ref: "#/components/responses/Conflict" }
        "422": { $ref: "#/components/responses/UnprocessableEntity" }
        "429": { $ref: "#/components/responses/TooManyRequests" }

  /{{RESOURCE_PLURAL}}/{id}:
    get:
      summary: "Get {{RESOURCE}} by ID"
      operationId: "get{{ResourcePascal}}"
      tags: ["{{ResourcePascal}}"]
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/{{ResourcePascal}}Response"
        "404": { $ref: "#/components/responses/NotFound" }

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    {{ResourcePascal}}:
      type: object
      required: [id, created_at, updated_at]
      properties:
        id:
          type: string
          format: uuid
          readOnly: true
          example: "550e8400-e29b-41d4-a716-446655440000"
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true
        # {{RESOURCE_FIELDS}}

    {{ResourcePascal}}Response:
      type: object
      required: [success, data]
      properties:
        success: { type: boolean, example: true }
        data:
          $ref: "#/components/schemas/{{ResourcePascal}}"

    {{ResourcePascal}}ListResponse:
      type: object
      required: [success, data, meta]
      properties:
        success: { type: boolean, example: true }
        data:
          type: array
          items:
            $ref: "#/components/schemas/{{ResourcePascal}}"
        meta:
          $ref: "#/components/schemas/PaginationMeta"

    PaginationMeta:
      type: object
      properties:
        total: { type: integer, example: 1234 }
        page: { type: integer, example: 1 }
        per_page: { type: integer, example: 20 }
        total_pages: { type: integer, example: 62 }

  responses:
    Unauthorized:
      description: "Authentication required or token invalid"
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
          example:
            success: false
            error: { code: "AUTH_TOKEN_INVALID", message: "Token is expired or invalid" }

    ValidationError:
      description: "Request validation failed"
      content:
        application/json:
          example:
            success: false
            error:
              code: "VALIDATION_FIELD_REQUIRED"
              message: "Validation failed"
              details: [{ field: "email", message: "is required" }]

    NotFound:
      description: "Resource not found"
    TooManyRequests:
      description: "Rate limit exceeded"
      headers:
        Retry-After: { schema: { type: integer } }
        X-RateLimit-Limit: { schema: { type: integer } }
        X-RateLimit-Remaining: { schema: { type: integer } }
    Conflict:
      description: "Duplicate request or resource conflict"
    UnprocessableEntity:
      description: "Semantic validation error"
```

---

## 13. API Changelog

| 版本 | 日期 | Breaking Changes | 新功能 | 棄用（Deprecated） |
|------|------|-----------------|--------|-------------------|
| v1.0 | {{YYYYMMDD}} | — | 初始版本發布 | — |
| v1.1 | — | — | — | — |
| v2.0 | — | — | — | v1 全面棄用（Sunset: TBD） |

> Breaking Change 定義：移除欄位、更改欄位類型、更改 HTTP method、更改端點路徑、更改認證機制。

---

## 14. API Review Checklist

在 API 設計完成並進入 In Review 狀態前，須逐項確認：

### 命名與結構
- [ ] URL 使用名詞複數（`/users`，非 `/getUser`）
- [ ] URL 路徑全小寫 kebab-case（`/user-profiles`）
- [ ] Request/Response 欄位名稱一致使用 `snake_case`
- [ ] 布林欄位有明確語義前綴（`is_active`、`has_permission`）
- [ ] 時間欄位統一使用 ISO 8601 UTC 格式（`_at` 後綴）

### Response 一致性
- [ ] 所有端點回應遵循標準 Envelope（`success`, `data`, `meta`）
- [ ] 錯誤碼格式統一（`DOMAIN_ENTITY_REASON`）
- [ ] 所有錯誤回應包含 `request_id`、`timestamp`、`docs_url`
- [ ] 列表端點支援分頁（cursor 或 offset）

### 安全性
- [ ] 所有非公開端點要求 JWT 或 API Key
- [ ] 權限設計遵循最小權限原則（RBAC scope 定義明確）
- [ ] 所有狀態變更端點要求 `Idempotency-Key`
- [ ] 認證端點有嚴格 Rate Limiting（防暴力破解）
- [ ] 回應不洩露內部系統資訊（stack trace、SQL 語句、內部路徑）
- [ ] 敏感欄位（密碼、Token）不出現在 Response body 或 Log

### 版本與相容性
- [ ] Breaking change 有版本升號計畫
- [ ] 棄用端點標有 `Deprecation` + `Sunset` header
- [ ] OpenAPI spec（`docs/openapi.yaml`）已同步更新

### 文件完整性
- [ ] 每個端點有完整的 Request/Response 範例
- [ ] 所有錯誤碼已收錄於 §5.2 Error Code Registry
- [ ] Rate Limiting 規則已於 §6 明確說明
- [ ] Webhook 事件類型（若有）已於 §8 定義

### HA / Resilience（必查，所有端點）
- [ ] 每個端點的 Timeout 已於 §2 或端點說明中明確定義（非 0 / 非無限）
- [ ] 客戶端重試策略已定義（最大次數、Exponential Backoff、Jitter）
- [ ] 重試端點的冪等性已於 §7 標注（POST 需 Idempotency-Key）

### Bounded Context 封裝（Spring Modulith HC-2，必查）
- [ ] Document Control「Owning BC / Service」已填入具體服務名稱（非 placeholder）
- [ ] §1.1 Service Encapsulation 原則已確認：本 API 是本 BC 的唯一對外介面
- [ ] API Response 使用 DTO/View Model 層，欄位名稱與 DB 欄位名稱解耦（DB 欄位可重命名不影響 API Contract）
- [ ] 無端點依賴其他 BC 的 DB Table（所有跨 BC 資料存取已透過對方 BC 的 API 端點或 Domain Event）
- [ ] 若本服務獨立部署（其他 BC 以 stub 取代），本 API 所有端點仍可正常返回 2XX（冷啟動測試通過）
- [ ] Rate Limiting 含 503/429 + Retry-After header，客戶端不盲目 retry
- [ ] 關鍵外部呼叫（DB、Cache、第三方 API）有 Circuit Breaker 說明
- [ ] 所有端點在服務 downscale / pod 重啟期間有 Graceful Shutdown 行為定義（in-flight request ≤ 30s 完成後才終止）

---

## 15. API Versioning & Deprecation Policy

### 15.1 版本策略

| 策略 | 說明 |
|------|------|
| 版本格式 | URL Path Versioning：`/api/v{N}/` |
| 並行版本數 | 最多同時維護 2 個主版本（Current + Previous） |
| 版本生命週期 | Major: 24 個月 LTS / Minor: 12 個月 / Patch: 滾動更新 |
| Breaking Change 定義 | 移除欄位、改變型別、移除 Endpoint、改變 HTTP Method |
| Non-Breaking Change | 新增可選欄位、新增 Endpoint、新增 HTTP Status Code |

### 15.2 Deprecation 流程

```mermaid
stateDiagram-v2
    [*] --> Active : 發佈新版本
    Active --> Deprecated : 宣告廢棄（發送 Deprecation Notice）
    Deprecated --> Sunset : 寬限期結束（最少 6 個月）
    Sunset --> Removed : 正式移除
    Removed --> [*]
```

**Deprecation 通知機制：**

1. **Response Header**（立即生效）：
   ```
   Deprecation: true
   Sunset: Sat, 01 Jan 2027 00:00:00 GMT
   Link: <https://api.example.com/api/v2/resource>; rel="successor-version"
   Warning: 299 - "This endpoint is deprecated. Please migrate to /api/v2/"
   ```

2. **Developer Portal 公告**：廢棄前 6 個月發布遷移指南
3. **Email 通知**：寄送給所有活躍 API Key 持有者
4. **Dashboard 警示**：Developer Portal 顯示廢棄計時器

### 15.3 版本遷移指南格式

```markdown
## Migration Guide: v1 → v2

### Breaking Changes

| v1 Endpoint | v2 Endpoint | 變更說明 |
|-------------|-------------|---------|
| `POST /api/v1/users` | `POST /api/v2/members` | 資源重命名：users → members |
| `GET /api/v1/orders?page=1` | `GET /api/v2/orders?after=<cursor>` | 分頁改為 Cursor-based |

### Request Body Changes

| 欄位 | v1 | v2 | 說明 |
|------|-----|-----|------|
| `user_name` | string | — | 移除（改為 `first_name` + `last_name`） |
| `first_name` | — | string (required) | 新增必填欄位 |
| `last_name` | — | string (required) | 新增必填欄位 |

### Timeline

- **2026-01-01**：v2 發佈，v1 開始廢棄期
- **2026-07-01**：v1 回應加入 Deprecation headers
- **2027-01-01**：v1 正式停止服務（Sunset）
```

### 15.4 語義化版本（Semantic Versioning）

```
MAJOR.MINOR.PATCH
│     │     └── Bug fixes, 不影響 API 行為
│     └──────── 新功能（向下相容）
└────────────── Breaking changes（需要新版本路徑）
```

---

## 16. Client SDK & Code Generation

### 16.1 SDK 生成策略

| 語言 | 工具 | 輸出路徑 | 維護策略 |
|------|------|---------|---------|
| TypeScript/JavaScript | `openapi-generator-cli` | `sdk/typescript/` | Auto-generated + 手動 wrapper |
| Python | `openapi-generator-cli` | `sdk/python/` | Auto-generated + 手動 wrapper |
| Go | `oapi-codegen` | `sdk/go/` | Auto-generated |
| Java | `openapi-generator-cli` | `sdk/java/` | Auto-generated |

### 16.2 SDK 生成指令

```bash
# 生成 TypeScript SDK
npx @openapitools/openapi-generator-cli generate \
  -i docs/openapi.yaml \
  -g typescript-axios \
  -o sdk/typescript \
  --additional-properties=withSeparateModelsAndApi=true,modelPropertyNaming=camelCase

# 生成 Python SDK
openapi-generator-cli generate \
  -i docs/openapi.yaml \
  -g python \
  -o sdk/python \
  --additional-properties=packageName={{PROJECT_SLUG}}_client

# 驗證 OpenAPI 規格
npx @stoplight/spectral-cli lint docs/openapi.yaml --ruleset .spectral.yaml
```

### 16.3 SDK 使用範例

**TypeScript：**

```typescript
import { Configuration, AuthApi, ResourceApi } from '@{{org}}/{{project}}-sdk';

const config = new Configuration({
  basePath: process.env.API_BASE_URL,
  accessToken: async () => await getAccessToken(),
});

const authApi = new AuthApi(config);
const resourceApi = new ResourceApi(config);

// 登入
const { data: tokens } = await authApi.login({
  loginRequest: { email: 'user@example.com', password: 'secret' }
});

// 取得資源清單（自動分頁）
const { data: result } = await resourceApi.listResources({ limit: 20 });
```

**Python：**

```python
from {{project}}_client import ApiClient, Configuration, AuthApi, ResourceApi
from {{project}}_client.exceptions import ApiException

config = Configuration(host=os.getenv("API_BASE_URL"))
config.access_token = get_access_token()

with ApiClient(config) as client:
    auth_api = AuthApi(client)
    resource_api = ResourceApi(client)

    try:
        tokens = auth_api.login({"email": "user@example.com", "password": "secret"})
        resources = resource_api.list_resources(limit=20)
    except ApiException as e:
        logger.error(f"API error {e.status}: {e.reason}")
```

### 16.4 Spectral Linting 規則（API 品質門禁）

```yaml
# .spectral.yaml
extends: ["spectral:oas"]
rules:
  operation-success-response: error
  operation-operationId: error
  operation-description: warn
  info-contact: warn
  no-$ref-siblings: error
  typed-enum: error
  # 自定義規則：所有端點必須有 security 定義
  operation-security-defined:
    given: "$.paths[*][*]"
    then:
      field: "security"
      function: "defined"
    severity: error
    message: "All operations must define security requirements"
```

---

## 17. API Observability & SLO

### 17.1 API 可觀測性設計

```mermaid
graph LR
    Client -->|Request| API_GW[API Gateway]
    API_GW -->|Trace| Jaeger
    API_GW -->|Metric| Prometheus
    API_GW -->|Log| Loki
    Prometheus -->|Alert| AlertManager
    Jaeger -->|Trace| Grafana
    Loki -->|Log| Grafana
```

### 17.2 標準 Observability Headers

每個 API 請求和回應必須包含：

**Request Headers（客戶端提供）：**

| Header | 說明 | 範例 |
|--------|------|------|
| `X-Request-ID` | 客戶端生成的請求唯一 ID（UUID v4） | `550e8400-e29b-41d4-a716-446655440000` |
| `X-Correlation-ID` | 跨服務追蹤 ID（由 API Gateway 傳播） | `corr-abc123` |
| `X-Client-Version` | 客戶端 SDK/App 版本 | `2.1.0` |

**Response Headers（服務器返回）：**

| Header | 說明 | 範例 |
|--------|------|------|
| `X-Request-ID` | Echo 回客戶端的 Request-ID | `550e8400-...` |
| `X-Response-Time` | 服務處理時間（毫秒） | `45ms` |
| `X-RateLimit-Limit` | 當前速率限制上限 | `100` |
| `X-RateLimit-Remaining` | 剩餘請求配額 | `87` |
| `X-RateLimit-Reset` | 速率限制重置時間（Unix timestamp） | `1704067200` |

### 17.3 SLO 定義

| SLO 指標 | 目標 | 測量窗口 | 警報閾值 |
|---------|------|---------|---------|
| 可用性（Availability） | ≥ 99.9% | 30 天滾動 | < 99.5% |
| P50 延遲 | ≤ 100ms | 5 分鐘 | > 150ms |
| P95 延遲 | ≤ 500ms | 5 分鐘 | > 800ms |
| P99 延遲 | ≤ 2000ms | 5 分鐘 | > 3000ms |
| 錯誤率（5xx） | ≤ 0.1% | 5 分鐘 | > 0.5% |
| 成功率（2xx） | ≥ 99.5% | 5 分鐘 | < 99% |

### 17.4 Error Budget 計算

```
月度錯誤預算 = (1 - SLO目標) × 月度總請求數
範例（99.9% 可用性，月度 10M 請求）：
  錯誤預算 = 0.001 × 10,000,000 = 10,000 次允許失敗
  每日預算 = 10,000 / 30 ≈ 333 次/天
```

---

## 18. Admin API（條件章節）
<!-- 觸發條件：has_admin_backend=true；否則略過此章節 -->

> **觸發條件**：`has_admin_backend=true` 時填寫，否則標注「本專案無 Admin 後台，跳過 §18」。
> Admin API 使用獨立前綴 `/admin/api/v1/`，所有端點需攜帶 Admin JWT Token。

### 18.0 Admin API 基礎規範

| 項目 | 值 |
|------|-----|
| Base URL | `/admin/api/v1/` |
| 認證 | `Authorization: Bearer <admin_jwt>` |
| Admin JWT 有效期 | 15 分鐘（從 CONSTANTS.md `ADMIN_ACCESS_TOKEN_TTL` 讀取） |
| 特殊 Header | `X-Admin-ID`（由 API Gateway 注入，后端信任） |
| 稽核 | 所有 POST/PATCH/PUT/DELETE 操作自動寫入 AuditLog |
| Rate Limit | 嚴格：100 req/min per Admin User |

### 18.1 Admin 認證端點

#### `POST /admin/api/v1/auth/login`

Admin 登入（獨立於 C 端用戶登入）。

**Request Body：**
```json
{
  "username": "admin@example.com",
  "password": "{{ADMIN_PASSWORD}}",
  "totp_code": "{{6_DIGIT_TOTP}}"  // super_admin 強制
}
```

**Response 200：**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "admin_id": "uuid",
  "roles": ["super_admin"],
  "permissions": ["user.list", "user.delete", "role.assign", "audit.export"],
  "expires_in": 900
}
```

**Response 403（MFA 未通過）：**
```json
{ "code": "ADMIN_MFA_REQUIRED", "message": "TOTP verification failed" }
```

---

#### `POST /admin/api/v1/auth/refresh`

Admin Token 刷新。

**Request Body：** `{ "refresh_token": "..." }`  
**Response：** 同 login（僅返回新 access_token + 有效期）

---

#### `POST /admin/api/v1/auth/logout`

登出（使 Refresh Token 失效）。

---

### 18.2 用戶管理端點

| Method | Path | 說明 | 所需 Permission |
|--------|------|------|----------------|
| GET | `/admin/api/v1/users` | 用戶列表（支援搜尋/分頁/篩選） | `user.list` |
| GET | `/admin/api/v1/users/:id` | 用戶詳情（含 PII，寫 AuditLog） | `user.view` |
| PATCH | `/admin/api/v1/users/:id/status` | 啟用/停用用戶 | `user.update` |
| POST | `/admin/api/v1/users/:id/reset-password` | 強制重設密碼 | `user.update` |
| DELETE | `/admin/api/v1/users/:id` | 刪除用戶（軟刪除，需二次確認） | `user.delete` |

**`GET /admin/api/v1/users` Query Parameters：**

| 參數 | 類型 | 說明 |
|------|------|------|
| `q` | string | 關鍵字搜尋（email/username） |
| `status` | `active\|disabled\|deleted` | 用戶狀態篩選 |
| `created_from` | ISO8601 | 建立時間起始 |
| `created_to` | ISO8601 | 建立時間終止 |
| `page` | int | 頁碼（offset-based） |
| `page_size` | int | 每頁筆數（max: 100） |

---

### 18.3 角色管理端點

| Method | Path | 說明 | 所需 Permission |
|--------|------|------|----------------|
| GET | `/admin/api/v1/roles` | 角色列表 | `role.list` |
| GET | `/admin/api/v1/roles/:id` | 角色詳情（含 Permission 清單） | `role.view` |
| POST | `/admin/api/v1/roles` | 建立角色 | `role.create` |
| PATCH | `/admin/api/v1/roles/:id` | 更新角色（名稱/描述/Permissions） | `role.update` |
| DELETE | `/admin/api/v1/roles/:id` | 刪除角色（不得刪除 super_admin） | `role.delete` |
| GET | `/admin/api/v1/permissions` | 所有可用 Permission 清單 | `role.list` |
| POST | `/admin/api/v1/admin-users/:id/roles` | 為 Admin 用戶分配角色 | `role.assign` |
| DELETE | `/admin/api/v1/admin-users/:id/roles/:role_id` | 移除 Admin 用戶角色 | `role.assign` |

---

### 18.4 稽核日誌端點

| Method | Path | 說明 | 所需 Permission |
|--------|------|------|----------------|
| GET | `/admin/api/v1/audit-logs` | 稽核日誌列表（支援分頁/篩選） | `audit.view` |
| GET | `/admin/api/v1/audit-logs/:id` | 稽核日誌詳情 | `audit.view` |
| GET | `/admin/api/v1/audit-logs/export` | 導出 CSV（非同步，返回 job_id） | `audit.export` |

**`GET /admin/api/v1/audit-logs` Query Parameters：**

| 參數 | 類型 | 說明 |
|------|------|------|
| `actor_id` | UUID | 操作者 Admin ID |
| `action_type` | string | 操作類型（user.delete 等） |
| `resource_type` | string | 資源類型（user/role/config） |
| `from` | ISO8601 | 時間起始 |
| `to` | ISO8601 | 時間終止 |
| `page` | int | 頁碼 |
| `page_size` | int | 最大 200 |

---

### 18.5 業務管理端點（依 PRD §19.3 擴展）

> 依專案 PRD §19.3 Admin 功能模組需求，補充以下業務管理端點：

| Method | Path | 說明 | 所需 Permission |
|--------|------|------|----------------|
| {{METHOD}} | `/admin/api/v1/{{RESOURCE}}` | {{DESCRIPTION}} | `{{PERMISSION}}` |

---

*文件維護者：{{AUTHOR}} | 審閱者：{{REVIEWER}} | 最後更新：{{YYYYMMDD}}*
