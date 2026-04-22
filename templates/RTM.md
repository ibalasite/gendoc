# RTM — Requirements Traceability Matrix（需求追溯矩陣）
<!-- SDLC Quality Engineering — Layer 8：Traceability & Coverage Audit -->
<!-- 對應學術標準：IEEE 29148 (Requirements Engineering)；業界：NASA RTM / ISTQB Traceability Matrix -->
<!-- 回答：每條需求是否有對應的設計、實作、測試？測試覆蓋率是否完整？ -->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | RTM-{{PROJECT_CODE}}-{{YYYYMMDD}} |
| **專案名稱** | {{PROJECT_NAME}} |
| **文件版本** | v1.0 |
| **狀態** | DRAFT / IN_REVIEW / APPROVED |
| **作者（QA Lead）** | {{AUTHOR}} |
| **日期** | {{DATE}} |
| **上游 PRD** | [PRD.md](PRD.md) |
| **上游 EDD** | [EDD.md](EDD.md) |
| **上游 API** | [API.md](API.md) |
| **上游 Test Plan** | [test-plan.md](test-plan.md) |
| **上游 BDD** | [BDD.md](BDD.md) |
| **審閱者** | {{QA_LEAD}}, {{ENGINEERING_LEAD}}, {{PRODUCT_MANAGER}} |
| **核准者** | {{EXECUTIVE_SPONSOR}} |

---

## Change Log

| 版本 | 日期 | 作者 | 變更摘要 |
|------|------|------|---------|
| v1.0 | {{DATE}} | {{AUTHOR}} | 初稿 |

---

## §0 什麼是 RTM？（給非技術讀者的說明）

> RTM（Requirements Traceability Matrix，需求追溯矩陣）是一份表格，用來確認：
>
> **「每一條需求，都有對應的程式碼在實作它，也有測試在驗證它。」**
>
> 你可以把它想成一份「檢核清單」：
> - 左側是業務需求（BRD/PRD 寫下的「要做什麼」）
> - 中間是程式設計（EDD 寫下的「哪個 Class、哪個方法」）
> - 右側是測試（Test Plan 寫下的「如何驗證」）
>
> 如果某一行沒有對應的測試 → 代表有需求沒被測試覆蓋，這是風險。
> 如果某一個測試沒有對應的需求 → 代表有多餘的測試，需要評估是否刪除。
>
> RTM 是 QA 與 PM 之間的共同語言，讓雙方都能快速確認「品質是否達標」。

---

## §1 Summary Statistics（統計摘要）

> 本節提供整體覆蓋率快照。每次更新 RTM 內容後，請同步更新此區塊的數字。

| 指標 | 數量 | 備註 |
|------|------|------|
| **總需求數（Requirements）** | {{TOTAL_REQUIREMENTS}} | 來自 PRD Must-have + Should-have |
| **總 User Story 數** | {{TOTAL_USER_STORIES}} | 來自 PRD §3 |
| **總 Class 數** | {{TOTAL_CLASSES}} | 來自 EDD §6 Class Diagram |
| **總 Method 數** | {{TOTAL_METHODS}} | 統計所有 RTM 列中的 Method |
| **總 Test Case 數** | {{TOTAL_TEST_CASES}} | Unit + Integration + E2E 全加總 |
| **Unit Test 數** | {{TOTAL_UNIT_TESTS}} | TC- 開頭 |
| **Integration Test 數** | {{TOTAL_INTEGRATION_TESTS}} | IT- 開頭 |
| **E2E Test 數** | {{TOTAL_E2E_TESTS}} | E2E- 開頭 |
| **需求覆蓋率** | {{REQ_COVERAGE}}% | 有測試覆蓋的需求 ÷ 總需求數 |
| **Method 覆蓋率** | {{METHOD_COVERAGE}}% | 有測試覆蓋的 Method ÷ 總 Method 數 |
| **PASS 率** | {{PASS_RATE}}% | 狀態為 PASS 的 TC ÷ 總 TC 數 |
| **FAIL 數** | {{FAIL_COUNT}} | 狀態為 FAIL（需立即處理）|
| **TODO 數** | {{TODO_COUNT}} | 尚未撰寫的測試（需排期）|

### §1.1 覆蓋率視覺化

```mermaid
pie title Test Case Distribution
    "Unit Tests" : {{TOTAL_UNIT_TESTS}}
    "Integration Tests" : {{TOTAL_INTEGRATION_TESTS}}
    "E2E Tests" : {{TOTAL_E2E_TESTS}}
```

```mermaid
pie title Test Status Distribution
    "PASS" : {{PASS_COUNT}}
    "FAIL" : {{FAIL_COUNT}}
    "IN_PROGRESS" : {{IN_PROGRESS_COUNT}}
    "TODO" : {{TODO_COUNT}}
    "SKIP" : {{SKIP_COUNT}}
```

---

## §2 Status 狀態碼說明

| 狀態 | 說明（中文）| Meaning（English）| 行動 |
|------|------------|-------------------|------|
| `TODO` | 測試尚未撰寫 | Test not yet written | 排入 Sprint backlog |
| `IN_PROGRESS` | 測試撰寫中 | Test being developed | 確認完成日期 |
| `PASS` | 測試通過 | Test passing in CI | 無需行動 |
| `FAIL` | 測試失敗 | Test failing in CI | 立即建立 bug ticket |
| `SKIP` | 測試暫緩（有原因）| Test deliberately skipped | 記錄跳過原因，定期 review |

---

## §3 Unit Test RTM — 需求 → 程式碼 → 單元測試

> **什麼是 Unit Test？**（給非技術讀者）
>
> Unit Test 是測試程式碼裡最小的單位：一個「方法（Method）」或「函式（Function）」。
> 就像測試一台機器的每個零件是否正常運作，而不是測試整台機器。
>
> 每個 Method 至少要有 3 種情境的測試：
> - **成功情境（Success Path）**：正常情況下，輸入對的資料，結果是否正確？
> - **錯誤情境（Error Path）**：輸入錯誤資料時，系統是否正確拒絕並回傳錯誤？
> - **邊界情境（Boundary）**：輸入極端值（空字串、最大值、負數）時，系統是否穩定？

### §3.1 欄位說明

| 欄位 | 說明 |
|------|------|
| **Req-ID** | 需求編號，對應 PRD AC（例：RQ-001） |
| **User Story** | 使用者故事編號（例：US-001） |
| **Class** | 實作此需求的 Class 名稱 |
| **Method** | 具體的方法名稱（含參數簡述） |
| **TC-ID** | 測試案例編號（TC-XXX）|
| **情境描述** | 這個測試在測什麼 |
| **情境類型** | Success / Error / Boundary |
| **Test Type** | Unit / Integration / E2E |
| **Status** | TODO / IN_PROGRESS / PASS / FAIL / SKIP |

### §3.2 Unit Test 追溯表

| Req-ID | User Story | Class | Method | TC-ID | 情境描述 | 情境類型 | Test Type | Status |
|--------|-----------|-------|--------|-------|---------|---------|-----------|--------|
| RQ-001 | US-001 | `AuthService` | `login(email, password)` | TC-001 | 正確帳密登入成功，回傳 JWT token | Success | Unit | `PASS` |
| RQ-001 | US-001 | `AuthService` | `login(email, password)` | TC-002 | 密碼錯誤，回傳 401 Unauthorized | Error | Unit | `PASS` |
| RQ-001 | US-001 | `AuthService` | `login(email, password)` | TC-003 | 帳號不存在，回傳 404 Not Found | Error | Unit | `PASS` |
| RQ-001 | US-001 | `AuthService` | `login(email, password)` | TC-004 | email 為空字串，回傳 422 驗證失敗 | Boundary | Unit | `PASS` |
| RQ-001 | US-001 | `AuthService` | `login(email, password)` | TC-005 | 帳號已停用，回傳 403 Forbidden | Error | Unit | `IN_PROGRESS` |
| RQ-002 | US-001 | `AuthService` | `logout(userId)` | TC-006 | 有效 session 登出成功，token 失效 | Success | Unit | `PASS` |
| RQ-002 | US-001 | `AuthService` | `logout(userId)` | TC-007 | 無效 token 登出，靜默成功（冪等）| Boundary | Unit | `PASS` |
| RQ-003 | US-002 | `AuthService` | `refreshToken(refreshToken)` | TC-008 | 有效 refresh token 換新 access token | Success | Unit | `TODO` |
| RQ-003 | US-002 | `AuthService` | `refreshToken(refreshToken)` | TC-009 | 過期 refresh token，回傳 401 | Error | Unit | `TODO` |
| RQ-003 | US-002 | `AuthService` | `refreshToken(refreshToken)` | TC-010 | refresh token 格式錯誤（亂碼），回傳 400 | Boundary | Unit | `TODO` |
| RQ-004 | US-003 | `UserService` | `createUser(dto)` | TC-011 | 合法資料建立用戶成功 | Success | Unit | `PASS` |
| RQ-004 | US-003 | `UserService` | `createUser(dto)` | TC-012 | email 重複，回傳 409 Conflict | Error | Unit | `PASS` |
| RQ-004 | US-003 | `UserService` | `createUser(dto)` | TC-013 | email 格式不合法，回傳 422 | Boundary | Unit | `FAIL` |
| RQ-004 | US-003 | `UserService` | `createUser(dto)` | TC-014 | 名稱超過 255 字元，回傳 422 | Boundary | Unit | `TODO` |
| RQ-005 | US-003 | `UserService` | `updateUser(userId, dto)` | TC-015 | 部分更新（PATCH）成功 | Success | Unit | `TODO` |
| RQ-005 | US-003 | `UserService` | `updateUser(userId, dto)` | TC-016 | userId 不存在，回傳 404 | Error | Unit | `TODO` |
| RQ-005 | US-003 | `UserService` | `updateUser(userId, dto)` | TC-017 | dto 為空物件，維持原資料不變 | Boundary | Unit | `TODO` |
| {{RQ-ID}} | {{US-ID}} | `{{ClassName}}` | `{{methodName}}({{params}})` | {{TC-ID}} | {{情境描述}} | {{類型}} | Unit | `{{Status}}` |

---

## §4 Integration Test RTM — API 端點追溯

> **什麼是 Integration Test？**（給非技術讀者）
>
> Integration Test 是把多個零件組合起來，測試它們「一起工作」的結果是否正確。
> 具體來說，就是透過 HTTP 請求呼叫 API，確認從入口到資料庫的整條路是通的。
>
> 例如：呼叫「登入 API」，測試系統是否真的把密碼比對、產生 token、寫入資料庫這些步驟都正確串在一起。
>
> **命名規則**：Integration Test ID 以 `IT-` 為前綴。

### §4.1 欄位說明

| 欄位 | 說明 |
|------|------|
| **API-ID** | API 端點編號，對應 API.md（例：API-001）|
| **HTTP Method + Path** | 完整端點（例：`POST /auth/login`）|
| **IT-ID** | Integration Test 編號（IT-XXX）|
| **情境描述** | 這個測試在測什麼 |
| **預期 HTTP Status** | 預期的 HTTP 回應碼 |
| **情境類型** | Success / Error / Boundary |
| **Status** | TODO / IN_PROGRESS / PASS / FAIL / SKIP |

### §4.2 Integration Test 追溯表

| API-ID | HTTP Method + Path | IT-ID | 情境描述 | 預期 Status | 情境類型 | Status |
|--------|-------------------|-------|---------|------------|---------|--------|
| API-001 | `POST /auth/login` | IT-001 | 正確帳密，回傳 200 + JWT token | 200 OK | Success | `PASS` |
| API-001 | `POST /auth/login` | IT-002 | request body 缺少 email 欄位，回傳 400 | 400 Bad Request | Boundary | `PASS` |
| API-001 | `POST /auth/login` | IT-003 | 密碼錯誤，回傳 401 | 401 Unauthorized | Error | `PASS` |
| API-001 | `POST /auth/login` | IT-004 | Content-Type 非 JSON，回傳 415 | 415 Unsupported Media Type | Boundary | `TODO` |
| API-002 | `POST /auth/logout` | IT-005 | 帶有效 Bearer token 登出，回傳 204 | 204 No Content | Success | `PASS` |
| API-002 | `POST /auth/logout` | IT-006 | 無 Authorization header，回傳 401 | 401 Unauthorized | Error | `PASS` |
| API-003 | `POST /auth/refresh` | IT-007 | 有效 refresh token，回傳 200 + 新 access token | 200 OK | Success | `TODO` |
| API-003 | `POST /auth/refresh` | IT-008 | 過期 refresh token，回傳 401 | 401 Unauthorized | Error | `TODO` |
| API-004 | `POST /users` | IT-009 | 合法 payload 建立用戶，回傳 201 + user object | 201 Created | Success | `PASS` |
| API-004 | `POST /users` | IT-010 | email 已存在，回傳 409 | 409 Conflict | Error | `PASS` |
| API-004 | `POST /users` | IT-011 | payload 驗證失敗，回傳 422 + 欄位錯誤清單 | 422 Unprocessable Entity | Boundary | `FAIL` |
| API-005 | `GET /users/:id` | IT-012 | 取得存在的用戶，回傳 200 + user object | 200 OK | Success | `PASS` |
| API-005 | `GET /users/:id` | IT-013 | userId 不存在，回傳 404 | 404 Not Found | Error | `PASS` |
| API-005 | `GET /users/:id` | IT-014 | userId 格式非 UUID，回傳 400 | 400 Bad Request | Boundary | `TODO` |
| API-006 | `PATCH /users/:id` | IT-015 | 部分更新成功，回傳 200 + 更新後 user | 200 OK | Success | `TODO` |
| API-006 | `PATCH /users/:id` | IT-016 | 無權限更新他人資料，回傳 403 | 403 Forbidden | Error | `TODO` |
| {{API-ID}} | `{{METHOD}} {{/path}}` | {{IT-ID}} | {{情境描述}} | {{Status Code}} | {{類型}} | `{{Status}}` |

---

## §5 E2E Test RTM — 使用者畫面追溯

> **什麼是 E2E Test？**（給非技術讀者）
>
> E2E（End-to-End，端到端）Test 是模擬真實用戶操作瀏覽器或 App 的測試。
> 就像雇一個測試員，從頭到尾把整個功能走一遍，確認用戶體驗是完整且正確的。
>
> 例如：打開登入頁面 → 填入帳號密碼 → 點擊登入按鈕 → 確認進入主頁。
> 這整個流程就是一個 E2E Test。
>
> **命名規則**：E2E Test ID 以 `E2E-` 為前綴。

### §5.1 欄位說明

| 欄位 | 說明 |
|------|------|
| **SC-ID** | 畫面編號，對應 PDD.md 的 Screen ID（例：SC-001）|
| **Screen Name** | 畫面名稱（例：LoginScreen）|
| **E2E-ID** | E2E Test 編號（E2E-XXX）|
| **情境描述** | 這個測試在走什麼用戶流程 |
| **情境類型** | Happy Path / Error Path / Edge Case |
| **Tool** | 使用的自動化工具（例：Playwright / Cypress）|
| **Status** | TODO / IN_PROGRESS / PASS / FAIL / SKIP |

### §5.2 E2E Test 追溯表

| SC-ID | Screen Name | E2E-ID | 情境描述 | 情境類型 | Tool | Status |
|-------|------------|-------|---------|---------|------|--------|
| SC-001 | `LoginScreen` | E2E-001 | 輸入正確帳密 → 點登入 → 跳轉至 Dashboard | Happy Path | Playwright | `PASS` |
| SC-001 | `LoginScreen` | E2E-002 | 輸入錯誤密碼 → 顯示錯誤提示，留在登入頁 | Error Path | Playwright | `PASS` |
| SC-001 | `LoginScreen` | E2E-003 | 不填任何欄位直接送出 → 顯示必填欄位錯誤 | Edge Case | Playwright | `PASS` |
| SC-001 | `LoginScreen` | E2E-004 | 「忘記密碼」連結可正常點擊並跳轉 | Happy Path | Playwright | `TODO` |
| SC-002 | `RegisterScreen` | E2E-005 | 填寫完整資料 → 送出 → 收到驗證 email 提示 | Happy Path | Playwright | `IN_PROGRESS` |
| SC-002 | `RegisterScreen` | E2E-006 | email 格式錯誤 → 即時驗證錯誤訊息出現 | Error Path | Playwright | `TODO` |
| SC-002 | `RegisterScreen` | E2E-007 | 使用已存在的 email 註冊 → 顯示「Email 已被使用」| Error Path | Playwright | `TODO` |
| SC-003 | `DashboardScreen` | E2E-008 | 登入後進入 Dashboard，顯示用戶名稱 | Happy Path | Playwright | `PASS` |
| SC-003 | `DashboardScreen` | E2E-009 | 直接訪問 /dashboard URL（未登入）→ 重導至登入頁 | Edge Case | Playwright | `PASS` |
| SC-004 | `ProfileScreen` | E2E-010 | 更新個人資料 → 儲存 → 顯示成功通知 | Happy Path | Playwright | `TODO` |
| SC-004 | `ProfileScreen` | E2E-011 | 上傳超過限制大小的頭像 → 顯示檔案大小錯誤 | Error Path | Playwright | `TODO` |
| {{SC-ID}} | `{{ScreenName}}` | {{E2E-ID}} | {{情境描述}} | {{類型}} | {{Tool}} | `{{Status}}` |

---

## §6 Req-ID ↔ Test-ID 快查索引

> 此表提供雙向查找：從需求找測試，或從測試找需求。適合 PM 和 QA 快速確認覆蓋狀況。

| Req-ID | 需求摘要 | 對應所有 TC/IT/E2E | 總測試數 | PASS | FAIL | TODO |
|--------|---------|-------------------|---------|------|------|------|
| RQ-001 | 用戶登入功能 | TC-001, TC-002, TC-003, TC-004, TC-005, IT-001, IT-002, IT-003, IT-004, E2E-001, E2E-002, E2E-003 | 12 | 9 | 0 | 3 |
| RQ-002 | 用戶登出功能 | TC-006, TC-007, IT-005, IT-006 | 4 | 4 | 0 | 0 |
| RQ-003 | Token 刷新功能 | TC-008, TC-009, TC-010, IT-007, IT-008 | 5 | 0 | 0 | 5 |
| RQ-004 | 建立用戶帳號 | TC-011, TC-012, TC-013, TC-014, IT-009, IT-010, IT-011, E2E-005, E2E-006, E2E-007 | 10 | 4 | 2 | 4 |
| RQ-005 | 更新用戶資料 | TC-015, TC-016, TC-017, IT-015, IT-016, E2E-010, E2E-011 | 7 | 0 | 0 | 7 |
| {{RQ-ID}} | {{需求摘要}} | {{TC/IT/E2E list}} | {{N}} | {{N}} | {{N}} | {{N}} |

---

## §7 FAIL 缺陷追蹤快查

> 所有狀態為 `FAIL` 的測試必須在此登記，並建立對應的 Bug Ticket。

| TC/IT/E2E ID | 失敗摘要 | 嚴重度 | Bug Ticket | 負責人 | 預計修復日期 |
|-------------|---------|--------|-----------|--------|------------|
| TC-013 | createUser — email 格式驗證未套用 regex | P1 HIGH | PROJ-{{TICKET_NUM}} | {{DEVELOPER}} | {{DATE}} |
| IT-011 | POST /users — 422 response body 缺少 field errors | P2 MEDIUM | PROJ-{{TICKET_NUM}} | {{DEVELOPER}} | {{DATE}} |
| {{TC-ID}} | {{失敗摘要}} | {{嚴重度}} | {{Ticket}} | {{負責人}} | {{日期}} |

---

## §8 CSV Export（機器可讀格式）

> 本節提供與上方表格相同的資料，以 CSV 格式呈現，方便匯入 Jira、Notion、Google Sheets、或測試管理工具（例：TestRail、Zephyr）。
>
> 複製以下 CSV 內容，存為 `rtm-{{PROJECT_CODE}}-{{YYYYMMDD}}.csv` 後即可直接匯入。

### §8.1 Unit Test CSV

```csv
RTM_Type,Req_ID,User_Story,Class,Method,TC_ID,Description,Scenario_Type,Test_Type,Status
Unit,RQ-001,US-001,AuthService,login(email password),TC-001,正確帳密登入成功 回傳 JWT token,Success,Unit,PASS
Unit,RQ-001,US-001,AuthService,login(email password),TC-002,密碼錯誤 回傳 401 Unauthorized,Error,Unit,PASS
Unit,RQ-001,US-001,AuthService,login(email password),TC-003,帳號不存在 回傳 404 Not Found,Error,Unit,PASS
Unit,RQ-001,US-001,AuthService,login(email password),TC-004,email 為空字串 回傳 422 驗證失敗,Boundary,Unit,PASS
Unit,RQ-001,US-001,AuthService,login(email password),TC-005,帳號已停用 回傳 403 Forbidden,Error,Unit,IN_PROGRESS
Unit,RQ-002,US-001,AuthService,logout(userId),TC-006,有效 session 登出成功 token 失效,Success,Unit,PASS
Unit,RQ-002,US-001,AuthService,logout(userId),TC-007,無效 token 登出 靜默成功（冪等）,Boundary,Unit,PASS
Unit,RQ-003,US-002,AuthService,refreshToken(refreshToken),TC-008,有效 refresh token 換新 access token,Success,Unit,TODO
Unit,RQ-003,US-002,AuthService,refreshToken(refreshToken),TC-009,過期 refresh token 回傳 401,Error,Unit,TODO
Unit,RQ-003,US-002,AuthService,refreshToken(refreshToken),TC-010,refresh token 格式錯誤（亂碼）回傳 400,Boundary,Unit,TODO
Unit,RQ-004,US-003,UserService,createUser(dto),TC-011,合法資料建立用戶成功,Success,Unit,PASS
Unit,RQ-004,US-003,UserService,createUser(dto),TC-012,email 重複 回傳 409 Conflict,Error,Unit,PASS
Unit,RQ-004,US-003,UserService,createUser(dto),TC-013,email 格式不合法 回傳 422,Boundary,Unit,FAIL
Unit,RQ-004,US-003,UserService,createUser(dto),TC-014,名稱超過 255 字元 回傳 422,Boundary,Unit,TODO
Unit,RQ-005,US-003,UserService,updateUser(userId dto),TC-015,部分更新（PATCH）成功,Success,Unit,TODO
Unit,RQ-005,US-003,UserService,updateUser(userId dto),TC-016,userId 不存在 回傳 404,Error,Unit,TODO
Unit,RQ-005,US-003,UserService,updateUser(userId dto),TC-017,dto 為空物件 維持原資料不變,Boundary,Unit,TODO
```

### §8.2 Integration Test CSV

```csv
RTM_Type,API_ID,HTTP_Method,Path,IT_ID,Description,Expected_Status,Scenario_Type,Status
Integration,API-001,POST,/auth/login,IT-001,正確帳密 回傳 200 + JWT token,200,Success,PASS
Integration,API-001,POST,/auth/login,IT-002,request body 缺少 email 欄位 回傳 400,400,Boundary,PASS
Integration,API-001,POST,/auth/login,IT-003,密碼錯誤 回傳 401,401,Error,PASS
Integration,API-001,POST,/auth/login,IT-004,Content-Type 非 JSON 回傳 415,415,Boundary,TODO
Integration,API-002,POST,/auth/logout,IT-005,帶有效 Bearer token 登出 回傳 204,204,Success,PASS
Integration,API-002,POST,/auth/logout,IT-006,無 Authorization header 回傳 401,401,Error,PASS
Integration,API-003,POST,/auth/refresh,IT-007,有效 refresh token 回傳 200 + 新 access token,200,Success,TODO
Integration,API-003,POST,/auth/refresh,IT-008,過期 refresh token 回傳 401,401,Error,TODO
Integration,API-004,POST,/users,IT-009,合法 payload 建立用戶 回傳 201 + user object,201,Success,PASS
Integration,API-004,POST,/users,IT-010,email 已存在 回傳 409,409,Error,PASS
Integration,API-004,POST,/users,IT-011,payload 驗證失敗 回傳 422 + 欄位錯誤清單,422,Boundary,FAIL
Integration,API-005,GET,/users/:id,IT-012,取得存在的用戶 回傳 200 + user object,200,Success,PASS
Integration,API-005,GET,/users/:id,IT-013,userId 不存在 回傳 404,404,Error,PASS
Integration,API-005,GET,/users/:id,IT-014,userId 格式非 UUID 回傳 400,400,Boundary,TODO
Integration,API-006,PATCH,/users/:id,IT-015,部分更新成功 回傳 200 + 更新後 user,200,Success,TODO
Integration,API-006,PATCH,/users/:id,IT-016,無權限更新他人資料 回傳 403,403,Error,TODO
```

### §8.3 E2E Test CSV

```csv
RTM_Type,SC_ID,Screen_Name,E2E_ID,Description,Scenario_Type,Tool,Status
E2E,SC-001,LoginScreen,E2E-001,輸入正確帳密 → 點登入 → 跳轉至 Dashboard,Happy Path,Playwright,PASS
E2E,SC-001,LoginScreen,E2E-002,輸入錯誤密碼 → 顯示錯誤提示 留在登入頁,Error Path,Playwright,PASS
E2E,SC-001,LoginScreen,E2E-003,不填任何欄位直接送出 → 顯示必填欄位錯誤,Edge Case,Playwright,PASS
E2E,SC-001,LoginScreen,E2E-004,「忘記密碼」連結可正常點擊並跳轉,Happy Path,Playwright,TODO
E2E,SC-002,RegisterScreen,E2E-005,填寫完整資料 → 送出 → 收到驗證 email 提示,Happy Path,Playwright,IN_PROGRESS
E2E,SC-002,RegisterScreen,E2E-006,email 格式錯誤 → 即時驗證錯誤訊息出現,Error Path,Playwright,TODO
E2E,SC-002,RegisterScreen,E2E-007,使用已存在的 email 註冊 → 顯示「Email 已被使用」,Error Path,Playwright,TODO
E2E,SC-003,DashboardScreen,E2E-008,登入後進入 Dashboard 顯示用戶名稱,Happy Path,Playwright,PASS
E2E,SC-003,DashboardScreen,E2E-009,直接訪問 /dashboard URL（未登入）→ 重導至登入頁,Edge Case,Playwright,PASS
E2E,SC-004,ProfileScreen,E2E-010,更新個人資料 → 儲存 → 顯示成功通知,Happy Path,Playwright,TODO
E2E,SC-004,ProfileScreen,E2E-011,上傳超過限制大小的頭像 → 顯示檔案大小錯誤,Error Path,Playwright,TODO
```

### §8.4 Summary Statistics CSV

```csv
Metric,Value,Note
Total_Requirements,{{TOTAL_REQUIREMENTS}},PRD Must-have + Should-have
Total_User_Stories,{{TOTAL_USER_STORIES}},From PRD §3
Total_Classes,{{TOTAL_CLASSES}},From EDD Class Diagram
Total_Methods,{{TOTAL_METHODS}},All methods in RTM
Total_Test_Cases,{{TOTAL_TEST_CASES}},Unit + Integration + E2E
Total_Unit_Tests,{{TOTAL_UNIT_TESTS}},TC- prefix
Total_Integration_Tests,{{TOTAL_INTEGRATION_TESTS}},IT- prefix
Total_E2E_Tests,{{TOTAL_E2E_TESTS}},E2E- prefix
Requirement_Coverage_Pct,{{REQ_COVERAGE}},Requirements with test coverage / total
Method_Coverage_Pct,{{METHOD_COVERAGE}},Methods with test coverage / total
Pass_Rate_Pct,{{PASS_RATE}},PASS count / total test cases
Fail_Count,{{FAIL_COUNT}},Immediate action required
Todo_Count,{{TODO_COUNT}},Need scheduling
```

---

*RTM 文件應在每次 Sprint 結束後同步更新，並在 Release 前確認所有 Must-have 需求的 PASS 率達 100%。*
