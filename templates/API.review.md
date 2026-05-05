---
doc-type: API
target-path: docs/API.md
reviewer-roles:
  primary: "資深 API Design Expert（API 審查者）"
  primary-scope: "RESTful 設計規範、HTTP 語意正確性、Request/Response Schema 完整性、Error Code 設計、Authentication 設計、Versioning 策略"
  secondary: "資深 Backend Engineer"
  secondary-scope: "實作可行性、效能考量、分頁設計、資料驗證、SQL N+1 問題預防"
  tertiary: "資深 Security Expert"
  tertiary-scope: "Authentication/Authorization 設計、OWASP API Top 10、Rate Limiting、輸入驗證、敏感資料保護"
quality-bar: "前端工程師和後端工程師各自閱讀 API.md 後，能直接開始實作，零歧義，所有 Request/Response Schema 清楚，Error 處理明確。"
pass-conditions:
  - "CRITICAL 數量 = 0"
  - "Self-Check：template 所有 ## 章節（≥21 個）均存在且有實質內容"
  - "每個 endpoint block 含 Possible Errors 表格"
  - "§12 OpenAPI 3.1 YAML 已生成"
upstream-alignment:
  - field: PRD P0 功能 → API Endpoint 覆蓋率
    source: PRD.md §功能清單 / User Stories
    check: API.md 的 Endpoint 是否覆蓋所有 PRD P0 User Story 的操作需求
  - field: EDD 認證設計 → API Auth 機制
    source: EDD.md §安全設計
    check: API.md 的 Auth 方式（Bearer/Cookie/OAuth）是否與 EDD 安全設計章節完全一致
  - field: EDD SLO → API 效能目標
    source: EDD.md §SLO/SLI
    check: API.md §Observability/SLO 的延遲目標是否與 EDD SLO 完全對齊
  - field: ARCH 服務邊界 → API 路由設計
    source: ARCH.md §服務邊界 / §API Gateway
    check: API 的 Endpoint 路由分組是否符合 ARCH 定義的服務邊界（不跨越服務邊界的 Endpoint 應分拆）
---

# API Review Items

本檔案定義 `docs/API.md` 的審查標準。由 `/reviewdoc API` 讀取並遵循。
審查角色：三角聯合審查（資深 API Design Expert + 資深 Backend Engineer + 資深 Security Expert）
審查標準：「假設公司聘請一位 10 年以上資深 API 架構師，以最嚴格的業界標準進行 API 文件驗收審查。」

---

## Review Items

### Layer 1: REST 設計規範（由 API Design Expert 主審，共 5 項）

#### [CRITICAL] 1 — URL 命名違反 RESTful 規範
**Check**: 所有 Endpoint 的 URL 是否使用名詞複數（`/users`，非 `/getUsers` 或 `/user`）？路徑是否全小寫 kebab-case（`/order-items`，非 `/orderItems`）？是否有動詞出現在資源路徑中（如 `/createOrder`）？逐一列出不符合規範的路徑。
**Risk**: URL 命名不一致，前後端工程師對路由產生混淆，生成 SDK 或 OpenAPI spec 時命名衝突，維護成本倍增。
**Fix**: 依 RESTful 資源導向設計原則重命名：URL 使用名詞複數、kebab-case，狀態變更操作改用 HTTP method 表達（如 `POST /orders/{id}/cancel`）。

#### [CRITICAL] 2 — HTTP Method 語義錯誤
**Check**: `GET` 是否只用於查詢（無副作用）？`POST` 是否只用於建立或執行非冪等動作？`PUT` 是否用於完整替換？`PATCH` 是否用於部分更新？`DELETE` 是否只用於刪除？列出所有 HTTP Method 使用不當的 Endpoint（如 `GET /users/delete`、`POST /users/search` 包含大量 body）。
**Risk**: HTTP Method 語義錯誤導致 Cache 行為異常（GET 有副作用被 CDN 快取）、冪等性假設被破壞、前端工程師整合時行為不可預期。
**Fix**: 依 RFC 7231 修正每個 Endpoint 的 HTTP Method；大型查詢改用 `POST /resources/search`（保留 GET 語義純粹性）。

#### [CRITICAL] 3 — HTTP Status Code 語義不正確
**Check**: 每個 Endpoint 的 Response Status Code 是否語義正確？常見錯誤：建立成功回 `200`（應回 `201`）、刪除成功回 `200`（應回 `204`）、業務規則失敗回 `500`（應回 `422`）、未授權回 `400`（應回 `401`）。逐一審查每個 Endpoint 的所有 Status Code。
**Risk**: Status Code 語義錯誤導致前端無法依 Status Code 實作差異化 UX，QA 自動化測試的斷言失效，Monitoring 的錯誤率統計失真。
**Fix**: 對照 §2.4 HTTP Status Code 語義表，修正每個 Endpoint 的 Response Status Code；201 建立後加上 `Location` header。

#### [HIGH] 4 — PATCH 端點語義不明確
**Check**: 每個 `PATCH` Endpoint 是否明確說明「只更新傳入欄位（Partial Update）」？Request Body 說明是否清楚標注「所有欄位選填，但至少一個欄位須提供」？有無說明未傳入欄位的行為（保持原值）？
**Risk**: PATCH 語義不明確，前端工程師誤認為需要傳入完整資源，造成意外覆蓋未修改欄位（如以 `null` 覆蓋原值），引發難以追蹤的資料損毀問題。
**Fix**: 在每個 PATCH Endpoint 說明中明確標注「Partial Update：僅更新請求 Body 中包含的欄位，未傳入欄位保持原值不變」。

#### [MEDIUM] 5 — URL 路徑參數設計不一致
**Check**: 路徑參數（Path Parameters）型別是否一致（統一使用 UUID v4 或統一使用整數 ID）？是否有部分 Endpoint 使用 `id`、部分使用 `userId`、部分使用 `user_id` 等不一致命名？逐一列出不一致的參數命名。
**Risk**: 路徑參數命名不一致，SDK 自動生成時產生混亂，前端工程師撰寫共用工具函式（如 `buildUrl`）時難以統一處理。
**Fix**: 統一路徑參數命名規則（建議 `:id`、`:userId`、`:orderId`，使用 camelCase 且與 Response Schema 欄位名一致）並在 §1 設計原則中聲明。

---

### Layer 2: Request/Response Schema 完整性（由 API Design Expert + Backend Engineer 聯合審查，共 5 項）

#### [CRITICAL] 6 — Endpoint 缺少完整 Request/Response Schema
**Check**: 每個 Endpoint 是否有完整的 Request Body Schema（欄位名稱、型別、必填/選填、驗證規則、範例值）和 Response Schema（所有欄位定義含說明）？特別檢查：必填欄位是否明確標注（`*` 或說明）？驗證規則（如 `minLength: 3`、`maxLength: 255`）是否定義？
**Risk**: Schema 缺失，前端工程師無法確認 API 介面，Contract Test 無法撰寫，整合期頻繁出現欄位名稱或型別不符，每次都需要後端工程師解答。
**Fix**: 為每個缺少 Schema 的 Endpoint 補充完整的 JSON 結構定義，必填欄位標注，驗證規則列表；建議同步更新 `docs/openapi.yaml`。

#### [CRITICAL] 7 — PRD P0 功能無對應 Endpoint
**Check**: 對照 PRD.md 的 P0 User Stories（若 PRD 存在），每個 P0 功能所需的資料操作（查詢、建立、更新、刪除）是否都在 API.md 有對應 Endpoint？列出所有缺漏的 P0 Endpoint 及其 PRD User Story 來源。
**Risk**: P0 功能缺乏 API Endpoint，前端工程師 Sprint 中無法整合，直接造成 P0 交付失敗，且在整合測試時才發現，修復成本極高。
**Fix**: 為每個缺少對應的 P0 功能補充完整 Endpoint（含路徑、HTTP Method、Schema、錯誤碼）；標注對應的 PRD User Story 編號。

#### [HIGH] 8 — 列表型 Endpoint 缺少分頁策略
**Check**: 所有列表型 `GET /resources` Endpoint 是否說明分頁策略（Cursor-based 或 Offset-based）？是否有分頁參數定義（`cursor`/`after` 或 `page`/`limit`）？Response 是否包含分頁 Meta（`has_next`、`total` 等）？
**Risk**: 分頁策略未定義，前端工程師各自假設分頁格式，無限捲動（Cursor）與頁碼（Offset）混用；資料量增長後無分頁的 API 直接全表返回，造成效能災難。
**Fix**: 為每個列表型 GET Endpoint 補充分頁參數說明；在 API.md 頂部聲明全局分頁策略（大資料集建議 Cursor-based，Admin 頁碼可用 Offset-based）。

#### [HIGH] 9 — 列表型 Endpoint 缺少排序與過濾參數
**Check**: 列表型 `GET /resources` Endpoint 是否定義排序參數（`sort`、`order`）和過濾參數（`filter[status]`、`filter[created_at]` 等）？是否說明允許的排序欄位列表（防止任意欄位排序造成全表掃描）？
**Risk**: 無排序/過濾參數定義，前端工程師自行發明參數格式，後端工程師實作時各自解釋，造成參數格式不統一；允許任意欄位排序可能引發 DB 效能問題。
**Fix**: 為列表型 Endpoint 補充排序與過濾參數規格，明確列出允許的排序欄位；建議統一使用 `filter[field]=value` 格式並在設計原則中聲明。

#### [MEDIUM] 10 — Response Schema 含不必要的敏感欄位
**Check**: 所有 Response Schema 是否包含不應返回前端的敏感欄位（`password_hash`、`internal_token`、第三方服務 API Key、內部追蹤 ID）？逐一審查每個 Endpoint 的 Response Schema 欄位清單。
**Risk**: 敏感欄位出現在 Response 中，攻擊者透過正常 API 呼叫即可取得密碼 Hash 或系統內部憑證，降低攻擊難度，且符合 OWASP API3:2023（Excessive Data Exposure）漏洞。
**Fix**: 審查所有 Response Schema，移除敏感欄位（`password_hash`、`*_token`、`internal_*`），並在後端 Serializer 層確保不被序列化輸出。

---

### Layer 3: 認證與授權（由 Security Expert 主審，共 4 項）

#### [CRITICAL] 11 — Endpoint Auth 需求未標示
**Check**: 每個 Endpoint 是否明確標示認證需求（需要 JWT Bearer Token 或公開 Endpoint）？是否有 Endpoint 既未標示需要認證，也未說明是公開 API？逐一確認每個 Endpoint 的認證標示。
**Risk**: Auth 需求未標示，前端工程師可能遺漏 Authorization Header，QA 無法設計未授權存取拒絕的測試；上線後出現匿名使用者存取受保護資源的安全漏洞（OWASP API1:2023）。
**Fix**: 為每個 Endpoint 加上認證標示（`🔒 需要 JWT Bearer Token` / `🌐 公開 Endpoint`）；在 §1 說明全局認證策略，例外（公開 Endpoint）逐一列出並說明理由。

#### [CRITICAL] 12 — Auth 設計與上游（EDD/ARCH）不一致
**Check**: API.md 的認證方式（Bearer Token / httpOnly Cookie / OAuth2 PKCE / API Key）是否與 EDD §安全設計章節完全一致？Token 儲存建議是否與 EDD 一致？若 EDD 不存在，API 的 Auth 設計是否自洽（§4 Auth Flow 與各 Endpoint 標示一致）？
**Risk**: Auth 方式不一致，前端依 API.md 實作 Bearer Token，後端依 EDD 實作 Cookie，整合測試時整個 Auth Flow 全部失敗，需要全面返工。
**Fix**: 以 EDD 安全設計為準，修正 API.md 的 Auth 說明；同步更新頂部全局 Auth 說明、各 Endpoint 的 curl 範例、以及 §4 Auth Flow 圖。

#### [HIGH] 13 — RBAC 權限模型定義不完整
**Check**: 若 PRD 或 EDD 定義了多個角色（如 `admin`、`editor`、`viewer`），API.md 是否為每個 Endpoint 說明允許操作的角色？是否有 RBAC 矩陣（Role × Endpoint 的可操作關係）？是否說明 403 Forbidden 的觸發條件？
**Risk**: RBAC 定義不完整，後端工程師各自解釋哪個角色可以操作哪個 Endpoint，造成實作不一致；QA 無法設計角色越權測試（OWASP API5:2023 Broken Function Level Authorization）。
**Fix**: 補充 RBAC 矩陣（Role × Endpoint），明確說明每個 Endpoint 允許的角色；在 §4 補充 Role 說明表（Role / 說明 / 可操作範圍）。

#### [HIGH] 14 — Rate Limiting 規則缺失或無業務依據
**Check**: API.md 是否定義 Rate Limiting 規則？若有，是否包含：限制層級（Per-User / Per-IP / Per-Endpoint）、具體數值（如 `1000 req/min`）、業務依據（為何設定此數值）、超限回應格式（含 `Retry-After`）？只說「有 Rate Limiting」無具體數值視為 HIGH。
**Risk**: Rate Limiting 數值無業務依據可能設定過嚴（正常使用者被限流，UX 差）或過寬（無法抵禦惡意濫用，防護失效）；無超限回應格式定義，前端無法實作重試邏輯。
**Fix**: 補充 Rate Limiting 規格表（Endpoint 分組 / 限制對象 / 數值 / 業務依據 / 超限 Response 格式，含 `429` 與 `Retry-After` 說明）。

---

### Layer 4: 錯誤處理（由 API Design Expert + Backend Engineer 聯合審查，共 4 項）

#### [CRITICAL] 15 — 回應碼完整性（條件式驗證）
**Check**: 回應碼完整性（條件式驗證）
- 需要認證的 endpoint：必須定義 401（未認證）和 403（無權限）
- 有速率限制的 endpoint：必須定義 429（Too Many Requests）
- 所有 endpoint：必須定義 500（伺服器錯誤）和至少一個 2XX 成功碼
- Public endpoint（無需認證）：無須定義 401/403，但需說明「此 endpoint 為公開存取，無需認證」

**Risk**: 遺漏回應碼導致客戶端無法正確處理錯誤狀態，或對 public endpoint 誤加認證錯誤碼造成語義錯誤。

**Fix**: 逐一檢查每個 endpoint 的認證要求，依條件補充或移除回應碼定義；public endpoint 須在描述欄位加入「公開存取」說明。

#### [HIGH] 16 — Error Response 格式不一致
**Check**: 所有 Endpoint 的 Error Response 是否使用統一的 Envelope 格式（`success: false`、`error.code`、`error.message`、`error.request_id`）？是否有部分 Endpoint 回傳 `{ "message": "..." }` 而其他回傳 `{ "error": { "code": "..." } }`？列出格式不一致的 Endpoint。
**Risk**: 錯誤格式不一致，前端需要針對每個 Endpoint 撰寫不同的錯誤解析邏輯，QA 的錯誤斷言 Code 無法共用，整體整合複雜度倍增。
**Fix**: 在 API.md §5 定義統一 Error Response Envelope，並確認所有 Endpoint 的錯誤範例均符合；建立 Error Code Registry 集中管理所有業務錯誤碼。

#### [HIGH] 17 — 業務規則 Error Code 缺失（422 未定義）
**Check**: 是否有 Endpoint 涉及業務規則限制（如「餘額不足」「超出配額」「狀態不允許轉換」）但缺少 `422` 錯誤碼說明或業務 Error Code（如 `INSUFFICIENT_BALANCE`、`QUOTA_EXCEEDED`）？逐一確認有業務邏輯的 Endpoint。
**Risk**: 業務規則錯誤未定義專屬 Error Code，前端收到 `422` 時無法判斷具體原因，使用者看到通用錯誤訊息而非有意義的提示，UX 品質差且難以 Debug。
**Fix**: 為每個有業務規則限制的 Endpoint 補充 `422` 錯誤碼，在 Error Code Registry 定義業務專屬的 `error.code`（如 `RESOURCE_STATE_CONFLICT`、`QUOTA_EXCEEDED`）並說明觸發條件。

#### [MEDIUM] 18 — Error Code Registry 缺失或不完整
**Check**: API.md 是否有 Error Code Registry（統一的錯誤碼清單）？各 Endpoint 分散定義錯誤碼而無集中 Registry 視為 MEDIUM。Registry 是否包含：`code`（全大寫底線）、HTTP Status、說明、觸發條件？
**Risk**: 無 Error Code Registry，前端和 QA 無法快速查找所有可能的錯誤碼，容易出現重複定義或命名不一致，跨 Endpoint 的錯誤處理邏輯難以抽象共用。
**Fix**: 在 API.md 補充 Error Code Registry 章節，列出所有業務錯誤碼；各 Endpoint 引用 Registry 中的 `code` 而非重複定義，確保 code 唯一且格式統一（`DOMAIN_ENTITY_REASON`）。

---

### Layer 5: 效能與擴展性（由 Backend Engineer 主審，共 4 項）

#### [HIGH] 19 — 冪等性設計缺失
**Check**: 狀態變更 Endpoint（`POST` 建立、`PATCH` 更新、`DELETE` 刪除）是否說明冪等性設計（`Idempotency-Key` Header 或業務唯一鍵）？是否說明重複請求的回應行為（返回第一次結果，不重複執行）？列出未說明冪等性的狀態變更 Endpoint。
**Risk**: 無冪等性設計，用戶在網路不穩時重試請求，可能造成重複建立訂單、重複付款等資料一致性問題，且難以在不影響使用者的情況下排查。
**Fix**: 為 `POST`/`PATCH`/`DELETE` Endpoint 補充 `Idempotency-Key` 說明（Header 格式、TTL、重複請求的回應行為）；在 §1 設計原則中聲明冪等性策略。

#### [HIGH] 20 — Webhook 設計缺失（若系統有事件通知需求）
**Check**: 若 PRD 或 EDD 定義了事件通知需求（如「訂單狀態變更通知第三方」「資料處理完成回調」），API.md 是否定義 Webhook 規格（事件類型清單、Payload 格式、HMAC 簽署驗證方式、重試策略）？若有事件通知需求但 Webhook 章節缺失，視為 HIGH。
**Risk**: Webhook 設計缺失，接入方不知道如何驗證 Webhook 來源，容易偽造事件通知（Security）；無重試策略導致事件遺失（Reliability）。
**Fix**: 補充 Webhook 規格：事件類型清單（`resource.created`/`updated`/`deleted`）、CloudEvents 格式 Payload、HMAC-SHA256 簽署驗證（含驗證 Code 範例）、指數退避重試策略（最多 3 次）、Dead Letter Queue。

#### [HIGH] 21 — OpenAPI 3.1 Spec 缺失或不完整
**Check**: API.md 是否包含完整的 OpenAPI 3.1 YAML（含 `paths`、`components/schemas`、`securitySchemes`）或明確指向 `docs/openapi.yaml`？若只有文字說明無 YAML 定義，且無 `docs/openapi.yaml` 引用，視為 HIGH。
**Risk**: 無 OpenAPI 規格，無法自動生成 SDK 和 Mock Server，QA 工具（Postman / Insomnia）無法匯入，Contract Test 無法自動化，整個 API 測試流程退化為手動。
**Fix**: 補充 OpenAPI 3.1 YAML（至少覆蓋所有 P0 Endpoint 的 `paths` + `components/schemas` + `securitySchemes`）；使用 Spectral lint 驗證 YAML 語法後提交。

#### [MEDIUM] 22 — API Versioning 策略未定義
**Check**: API.md 是否說明版本控制策略（URL prefix `v1` / Date Header / Query Param）？是否說明 Breaking Change 定義（移除欄位、更改型別等）、廢棄通知機制（`Deprecation`+`Sunset` header）、舊版維護期限？
**Risk**: 無 Versioning 策略，未來需要 Breaking Change 時無法平滑遷移，要麼強制所有客戶端同步升版，要麼永久維護舊版行為，技術負債持續累積。
**Fix**: 在 §1 或獨立章節補充 Versioning 策略說明（建議 URL prefix：`/api/v1/`）、Breaking Change 定義、廢棄政策（至少 90 天通知期）、Migration Guide 格式。

---

### Layer 6: 安全性（由 Security Expert 主審，共 3 項）

#### [CRITICAL] 23 — 輸入驗證規則缺失
**Check**: POST/PATCH Endpoint 的 Request Body 欄位是否定義了完整的驗證規則？常見缺失：字串長度限制（`minLength`/`maxLength`）、數值範圍（`min`/`max`）、枚舉值（`enum`）、格式約束（`email`/`url`/`uuid`）、必填標注。逐一審查每個 Endpoint 的 Request 欄位驗證規則。
**Risk**: 缺少輸入驗證規則，後端工程師各自實作驗證邏輯（或遺漏），導致無效資料進入系統；缺乏驗證規則文件，QA 無法設計邊界值測試；符合 OWASP API6:2023（Unrestricted Access to Sensitive Business Flows）。
**Fix**: 為每個 Request Body 欄位補充完整驗證規則（型別、必填、長度/範圍/格式限制），建議統一使用 JSON Schema 格式定義並加入 OpenAPI spec。

#### [HIGH] 24 — 敏感操作缺少額外授權保護
**Check**: 高風險操作（大量資料刪除、帳號停權、財務操作、管理員功能）是否有額外的授權保護（如 2FA 確認、操作理由記錄、Audit Log）？是否有任何高風險 Endpoint 僅依賴普通 JWT 即可執行，無額外授權層？
**Risk**: 高風險操作缺少額外保護，若 JWT 遭竊（XSS/MITM），攻擊者可立即執行破壞性操作；無 Audit Log 導致安全事件後無法追溯操作者。
**Fix**: 為高風險 Endpoint 補充額外授權說明（如管理員二次確認、`X-Admin-Reason` Header 必填、操作記入 Audit Log）；在 §4 Authorization 補充高風險操作的保護設計。

#### [HIGH] 25 — File Upload Endpoint 缺少安全限制
**Check**: 若有 File Upload Endpoint，是否定義了：允許的 MIME 類型白名單（非黑名單）、單檔大小上限、病毒掃描說明、儲存位置（不得直接暴露 Web 路徑）、URL 過期機制？缺少任一關鍵限制視為 HIGH。
**Risk**: File Upload 缺少安全限制，攻擊者可上傳惡意腳本（WebShell）、超大檔案（DoS）；直接暴露儲存路徑可能洩露系統架構；符合 OWASP API4:2023（Unrestricted Resource Consumption）。
**Fix**: 為 File Upload Endpoint 補充完整安全規格（MIME 白名單、大小上限、病毒掃描流程、CDN Signed URL / 有效期機制）；確認上傳路徑不直接映射到 Web Server 目錄。

---

### Layer 7: 上游對齊與文件完整性（由 API Design Expert 主審，共 2 項）

#### [HIGH] 26 — curl 範例無法執行（含裸 Placeholder）
**Check**: 每個 Endpoint 的 curl 範例是否完整可執行（含 Base URL、必要 Header、範例 Body）？是否有 `{{PLACEHOLDER}}` 格式未替換（`{{DOMAIN}}`、`{{TOKEN}}`、`{{API_KEY}}`）？含裸 placeholder 的 curl 範例視為 HIGH。
**Risk**: 無法執行的 curl 範例讓工程師無法快速驗證 API，每個 Endpoint 都需要手動拼裝請求；裸 placeholder 讓 Onboarding 工程師無法直接使用文件，需要人工詢問。
**Fix**: 替換所有裸 placeholder 為真實的 Staging 環境值（Base URL / 範例 Token 格式說明）；若安全考量無法寫入，改為說明「請向後端工程師申請測試用 Token（Slack: #backend）」。

#### [LOW] 27 — 裸 Placeholder 掃描
**Check**: 文件中是否有 `{{PLACEHOLDER}}` 格式未替換的空白佔位符（`{{DOMAIN}}`、`{{RESOURCE}}`、`{{RESOURCE_UPPER}}`、`{{YYYYMMDD}}`、`{{AUTHOR}}`）？逐一掃描全文，列出所有裸 placeholder 及其位置（章節）。注意：格式範例型 placeholder（如 `{{RESOURCE_NAME}}`）若有說明則允許；純空白無說明的才是 finding。
**Risk**: 裸 placeholder 讓工程師無法直接使用 API 文件，需要人工詢問填寫缺漏值，失去文件自動生成的價值。
**Fix**: 對每個裸 placeholder，依上游文件或業務設定填入真實值；若真的無法確定，改為 `（待確認：描述）` 說明而非保留 `{{PLACEHOLDER}}`。

---

### Layer 8: UML 圖完整性（由 API Design Expert 主審，共 1 項）

#### [HIGH] 28 — 缺少對應的 Sequence Diagram
**Check**: 對照 `docs/diagrams/` 目錄，每個 P0 Endpoint 是否有對應的 Sequence Diagram（`docs/diagrams/sequence-*.md`）？確認方式：逐一列出 API.md 的 P0 Endpoint，搜尋是否有對應的 `sequence-{flow}.md`（如 POST /auth/login → sequence-login.md）。無對應 Sequence Diagram 的 P0 Endpoint 視為 HIGH。
**Risk**: 缺少 Sequence Diagram，工程師在實作時沒有「訊息傳遞時序」的視覺指引，各層之間的呼叫順序只能靠口頭溝通，容易造成 Controller 直接呼叫 Repository（跳過 Service 層）、Cache 操作順序錯誤、事件發布時機不一致等架構缺陷，且難以在 Code Review 中被發現。
**Fix**: 執行 `/gendoc-gen-diagrams` 自動生成所有 Endpoint 的 Sequence Diagram；或手動為每個 P0 Endpoint 在 EDD §4.5.4 補充對應的 sequenceDiagram 程式碼塊，再由 gen-diagrams 提取。每張 Sequence Diagram 必須包含：Controller → Service → Repository → DB 完整呼叫鏈，以及 Happy Path 和至少 2 個 Error Path（使用者不存在、驗證失敗等）。


---

### Layer 9: HA / Resilience 設計（由 Backend Engineer 主審，共 5 項）

#### [CRITICAL] 29 — 端點 Timeout 未定義
**Check**: §2 通用規範或各端點說明中，是否明確定義每個 API 呼叫的 Timeout（含 Server-side response timeout 與 client-side read timeout）？若無任何 Timeout 定義，視為 CRITICAL。
**Risk**: 沒有 Timeout 的服務在依賴項（DB、Cache、第三方 API）出現延遲時，請求會無限等待，佔用 thread pool，最終導致整個服務不可用（典型的 cascading failure 模式）。
**Fix**: 在 §2 通用規範補充 Timeout 表格（連線建立 Timeout / 讀取 Timeout / 端點最大響應時間），並在效能敏感端點說明中標注個別 Timeout 值（從 EDD §效能需求推算）。

#### [HIGH] 30 — 重試策略未定義
**Check**: §2 或端點說明是否定義客戶端重試策略？包含：可重試的 HTTP 狀態碼（503/429/502）、不可重試碼（400/401/403）、最大重試次數、Exponential Backoff + Jitter 算法說明？缺少以上任一項視為 HIGH。
**Risk**: 未定義重試策略，客戶端開發者自行實作：有人不重試、有人線性重試（Thundering Herd）、有人無限重試（DDoS 自家服務），導致 failover 後更難恢復。
**Fix**: 在 §2 補充重試策略規格（可重試狀態碼 / 最大次數 / Backoff 公式 / Jitter 必要性說明）；POST 等非冪等端點的重試必須搭配 `Idempotency-Key`。

#### [HIGH] 31 — Circuit Breaker 策略未說明
**Check**: 對於呼叫外部服務的 API 端點（DB、Cache、第三方 API、微服務間呼叫），是否說明 Circuit Breaker 行為（fallback 回應、半開狀態逾時、錯誤率門檻）？若架構涉及微服務間呼叫或第三方依賴而完全無 Circuit Breaker 說明，視為 HIGH。
**Risk**: 沒有 Circuit Breaker，單一依賴項故障會傳播至所有呼叫者，導致整個請求鏈超時並最終令上層服務也不可用（cascading failure）。
**Fix**: 在 §17 Observability 或 §2 通用規範補充 Circuit Breaker 設計：觸發條件（5 秒錯誤率 > 50%）、開啟後的 fallback 回應（503 + Retry-After）、半開探測間隔（30s）。

#### [HIGH] 32 — 冪等性設計未涵蓋重試場景
**Check**: §7 Idempotency 是否說明：所有 POST 端點必須接受 `Idempotency-Key`（含有效期）？重複請求時是否回傳相同結果（而非再次執行）？`Idempotency-Key` 的儲存策略（Redis TTL）？缺少儲存策略或有效期視為 HIGH。
**Risk**: 客戶端在網路重試時重複執行 POST 操作（重複下單、重複付款、重複建立資源），造成資料異常且難以偵測。
**Fix**: 補充 §7 Idempotency：`Idempotency-Key` header 說明（UUID v4、有效期 24h）、Redis 儲存設計（key TTL / 請求結果快取）、重複請求偵測後的回應方式（HTTP 200 + 原始結果）。

#### [CRITICAL] 33 — Graceful Shutdown 行為未定義
**Check**: API 文件是否定義或引用 EDD §3.6 中的 Graceful Shutdown 行為？包含：pod 終止信號（SIGTERM）後不再接受新請求、in-flight 請求最多等待 N 秒（推薦 ≤ 30s）完成後才退出、Load Balancer 已移除該 pod 的流量後才開始 drain？若完全無說明視為 CRITICAL。
**Risk**: 沒有 Graceful Shutdown，每次 pod 重啟（deploy/scale/節點驅逐）都會造成部分請求 502/503，在 canary 或 rolling update 期間尤其明顯。
**Fix**: 在 §2 通用規範補充「Graceful Shutdown 承諾」段落，並引用 EDD §3.6 HA Architecture 的 SIGTERM 處理流程；或在 §17 SLO 補充「每次 Deploy 期間 SLO 維持 99.9%」的實現說明（Graceful Shutdown + Readiness Probe 配置）。

---

### Layer 10: Spring Modulith BC 對齊（由 Software Architect 主審，共 3 項）

#### [CRITICAL] BC-01 — §3 Endpoints 未依 Bounded Context 分組（HC-2）
**Check**: API.md §3 中，Endpoints 是否以 `### BC: {BC_NAME} Endpoints` 格式分組？是否每個 BC（來自 EDD §3.4）均有對應的子章節？是否有 Endpoint 歸屬曖昧（跨 BC 共用 Path Prefix，如 `/api/v1/orders` 同時包含 OrderBC 和 PaymentBC 的 Endpoint）？任一缺失視為 CRITICAL。
**Risk**: 無 BC 分組，工程師無法一眼識別某個 Endpoint 屬於哪個 BC；Code Review 中無法機械式驗證 HC-2（跨 BC 呼叫只能透過公開 Endpoint，不能直接呼叫內部類別）；API 文件和 ARCH §4.0 映射表脫節，BC 邊界形同虛設。
**Fix**: 將 §3 所有 Endpoint 依 EDD §3.4 Bounded Context Map 重新分組，格式：`### BC: {BC_NAME} Endpoints（Path Prefix: /api/v1/{bc_slug}）`；確認各 BC 的 Path Prefix 不重疊；若某 BC 無直接對外 Endpoint，在子章節標注「此 BC 無直接 API，跨 BC 互動透過 Domain Event」。

#### [HIGH] BC-02 — 跨 BC 呼叫端點未標注（HC-2）
**Check**: 是否有任何 Endpoint 的業務邏輯需要呼叫其他 BC 的資料（如 OrderBC 的 `/api/v1/orders/{id}` 回傳中包含 UserBC 的 user_name）？此類端點是否在文件中明確標注「呼叫 {BC_NAME} 的 {Endpoint}」或「讀取 {BC_NAME} 發布的 {Domain_Event}」？若有跨 BC 資料依賴但未標注來源，視為 HIGH。
**Risk**: 未標注跨 BC 依賴，開發者不知道此端點在某個 BC 不可用時的行為（是應該 fallback 還是 503？）；也無法在測試時正確 mock 依賴的 BC。
**Fix**: 在跨 BC 依賴的端點文件中補充「Cross-BC Dependencies」欄位：列出依賴的 BC 名稱、呼叫方式（同步 API 或 Domain Event）、降級策略（依賴 BC 不可用時的 fallback 行為）。

#### [MEDIUM] BC-03 — §14 HA 核查清單未涵蓋 Domain Event 冪等性
**Check**: §14 HA 核查清單中，是否包含「Event Consumer 冪等性」項目（同一 Domain Event 被消費兩次時，業務結果不重複執行）？若 API.md 中有 Event-Driven 相關端點（Webhook、Event Listener）但核查清單未提及冪等性，視為 MEDIUM。
**Risk**: Event Consumer 不冪等，在 MQ 的 At-least-once 投遞語義下，重複投遞會觸發重複業務操作（重複付款、重複建立資源）。
**Fix**: 在 §14 HA 核查清單補充「Event Consumer 冪等性：消費前先查 `processed_event_id`，已處理則直接 ACK 不執行業務邏輯」；引用 EDD §3.4 Domain Event Schema 的 `event_id` 欄位。


---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/API.md`，提取所有 `^## ` heading（含條件章節），共約 21 個
2. 讀取 `docs/API.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
