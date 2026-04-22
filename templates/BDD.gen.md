---
doc-type: BDD
output-path: docs/BDD.md
features-dir: docs/features/
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md
  - docs/EDD.md
  - docs/ARCH.md
  - docs/API.md
  - docs/SCHEMA.md
  - docs/test-plan.md
quality-bar: "每個 PRD AC 至少有一個 Scenario（正常路徑 + 錯誤路徑）；所有 API Endpoint 均有 @contract tagged Scenario；邊界條件使用 Scenario Outline；所有 Then 斷言具體且可測試；無技術語言滲入 Given/When/Then；6 個 HTTP 錯誤碼（401/403/404/409/422/429）均有對應 Error Scenario"
---

# BDD.gen.md — BDD Feature Files 生成規則

依 PRD 每個驗收標準（AC），自動生成完整的 BDD Feature Files（Gherkin 格式）。
每個 PRD AC 對應至少 2 個 Scenario（正常路徑 + 錯誤路徑），
邊界條件使用 Scenario Outline + Examples Table。

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
| `IDEA.md`（若存在）| 全文 | 了解產品願景——BDD Scenario 的業務語言需反映 IDEA 的業務概念 |
| `BRD.md` | 業務目標、驗收標準 | Feature 標題的業務語意來自 BRD |
| `PRD.md` | 所有功能 AC | **主要輸入**：每個 AC → 至少 1 正常路徑 + 1 錯誤路徑 Scenario |
| `PDD.md`（若存在）| §4 功能需求、§6 互動設計 | UI/E2E BDD（@ui tag）的 Given/When/Then 步驟來自 PDD 互動流程 |
| `EDD.md` | §5 BDD 設計、§4 Security | 確認已規劃的 Scenario 結構和認證流程 |
| `ARCH.md` | §3 元件架構 | 確認 Contract Testing 的 Provider/Consumer 邊界 |
| `API.md` | 所有 Endpoint、Request/Response | **@contract tag**：每個 API Endpoint 必須有對應 BDD Scenario |
| `SCHEMA.md` | 資料模型 | Background 的資料初始化步驟（Given 的 clean state 設計）|
| `test-plan.md` | §3.3 E2E/BDD、§9 Risk Matrix | Smoke 標記（Risk=High 的功能 Scenario 數量加倍）|

若某文件不存在，靜默跳過，依既有流程繼續。

### test-plan.md 特別讀取規則

若 `docs/test-plan.md` 存在，額外讀取以下章節：
- **§3.3 E2E / BDD Tests**：確認 E2E 工具（Playwright/Cypress 等）、Browser Matrix、Critical User Flow 清單
  → 清單中標記為 `Smoke: Y` 的 Flow 必須生成 `@smoke` tag Scenario
- **§9 Risk-Based Testing Matrix**：Risk Level = High 的功能，Scenario 數量需加倍（至少 2× 正常路徑 + 2× 錯誤路徑 + 1× 邊界 Scenario Outline）
- **§15 RTM（若存在 TC-ID）**：生成的 Gherkin Scenario 的 tag 補充對應 TC-ID（格式：`@TC-XXX-001`）

### IDEA.md Appendix C 素材讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與 BDD 相關的檔案。
對每個存在的 `docs/req/` 檔案，讀取全文，結合 Appendix C「應用於」欄位標有「BDD §」的段落，
作為生成 BDD Feature Scenarios（驗收條件、Given/When/Then）的補充依據。
優先採用素材原文描述，而非 AI 推斷。若無引用，靜默跳過。

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- PRD 的 AC vs API.md 的 Endpoint（是否有 AC 無對應 API）
- EDD §5 的 BDD 設計 vs PRD 的 AC（是否有 Scenario 設計但無對應 AC）
- PDD 的 UI 流程 vs PRD 的 AC（是否有 UI 互動步驟未被任何 AC 覆蓋）

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並說明影響的 Scenario 範圍。

---

## Feature 拆分規則

**一個 PRD 功能 → 一個 .feature 檔案**

命名規則：
- PRD 功能「使用者登入」→ `docs/features/auth/user_login.feature`
- PRD 功能「訂單查詢」→ `docs/features/orders/list_orders.feature`
- 依功能模組分子目錄

**AC 解析規則：**
尋找 PRD 中格式為 `- [ ] AC-N：` 的行，配對到上方最近的 `### 功能N` 或 `## 功能N` 標題，
建立 Feature → AC 對應清單。

---

## Gherkin 格式規範

### 標準結構

```gherkin
# docs/features/<module>/<feature_name>.feature
# 來源：PRD §<功能名稱>，AC-1～AC-N

Feature: <功能名稱（與 PRD 一致）>
  作為 <角色>
  我希望 <功能>
  以便 <目的>

  # ─── 正常路徑 ───────────────────────────────────────────
  Scenario: <正常路徑描述>（來自 AC-1 正常流程）
    Given <初始狀態（Given 必須是系統當前狀態）>
    And <補充前置條件>
    When <使用者執行的動作>
    Then <預期結果（必須具體、可測試）>
    And <補充斷言>

  # ─── 錯誤路徑 ───────────────────────────────────────────
  Scenario: <錯誤路徑描述>（來自 AC-2 錯誤流程）
    Given <初始狀態>
    When <使用者執行了不合法的動作>
    Then <預期錯誤回應（具體 HTTP 碼 / 訊息）>

  # ─── 邊界條件 ───────────────────────────────────────────
  Scenario Outline: <邊界條件描述>（來自 AC-3 邊界）
    Given <初始狀態>
    When <使用者輸入 "<input_value>">
    Then <預期結果是 "<expected_result>">

    Examples:
      | input_value        | expected_result |
      | ""                 | 錯誤：必填欄位   |
      | "a"                | 錯誤：長度不足   |
      | "valid@email.com"  | 成功建立         |
      | "a" * 256          | 錯誤：超過最大長度|
```

### Scenario 命名原則

- Scenario 名稱用**業務語言**，不用技術語言
  - 正確：`成功以有效 Email 和密碼登入`
  - 錯誤：`POST /auth/login returns 200`
- Given 描述**狀態**，不描述動作
  - 正確：`Given 使用者已完成帳號註冊`
  - 錯誤：`Given 使用者呼叫了 POST /api/v1/users`
- Then 斷言**可觀測的結果**
  - 正確：`Then 使用者收到 access_token 和 refresh_token`
  - 錯誤：`Then 程式沒有報錯`

### 共用 Step Definitions（Background）

若多個 Scenario 有相同前置，使用 Background：

```gherkin
Background:
  Given 資料庫已初始化（clean state）
  And 已有測試使用者：email="test@example.com"，password="Test1234!"
```

Background 步驟不得超過 5 個；若超過，應拆分 Feature 或改用 Scenario Outline。

---

## Scenario 數量規則

**基本規則（每個 AC）：**
- 至少 1 個正常路徑 Scenario
- 至少 1 個錯誤路徑 Scenario
- 有邊界條件時使用 Scenario Outline

**Risk Level = High 的功能（來自 test-plan.md §9）：**
- 至少 2× 正常路徑 Scenario
- 至少 2× 錯誤路徑 Scenario
- 至少 1× 邊界 Scenario Outline

---

## Tag 策略

| Tag | 用途 | 規則 |
|-----|------|------|
| `@p0` | Must-have 功能 Scenario | PRD P0 AC 全部標記 |
| `@p1` | Should-have 功能 Scenario | PRD P1 AC 全部標記 |
| `@smoke` | 核心主要路徑 Scenario | Critical Flow Happy Path 標記 |
| `@regression` | 完整回歸測試 Scenario | 所有 Scenario 均可標記 |
| `@ui` | UI/E2E 測試 Scenario | PDD 互動流程 Scenario 標記 |
| `@api` | API 測試 Scenario | API 驗證 Scenario 標記 |
| `@contract` | API 契約測試 Scenario | 每個 API Endpoint 必須有對應 @contract Scenario |
| `@TC-XXX-001` | RTM 追溯 tag | 與 test-plan.md §15 RTM 的 TC-ID 對應 |

---

## Error Scenario Catalog 生成規則

每個 Feature 必須涵蓋以下 HTTP 錯誤碼的 Scenario（6 個均必備）：

| HTTP 碼 | 場景 | 必備 Scenario 描述 |
|---------|------|-------------------|
| 401 | 未認證 | Token 無效或過期時拒絕存取 |
| 403 | 無權限 | 角色不符時拒絕操作 |
| 404 | 資源不存在 | 操作不存在的資源 |
| 409 | 衝突 | 建立重複資源 |
| 422 | 業務規則違反 | 違反業務邏輯（含具體說明）|
| 429 | Rate Limit | 超過速率限制 |

---

## Contract Testing 規則

- 每個 API.md 中定義的 Endpoint 必須有至少一個 `@contract` tagged Scenario
- Contract Testing 追溯矩陣必須建立（BDD Scenario → API Endpoint → HTTP Method → 回應碼）
- `@contract` Scenario 的 Then 步驟必須驗證具體的 HTTP 狀態碼和回應結構

---

## Test Data Management 規則

- 使用 Factory 動態建立 Test Data（不得 hardcode 真實 PII）
- AfterScenario / Background 清理機制確保測試資料不累積
- 測試帳號使用 @example.com 或 @test.internal 網域
- 禁止：hardcode 真實 email/phone/身分證號
- 禁止：測試 Scenario 依賴其他 Scenario 的資料殘留
- 禁止：直接使用生產環境帳號

---

## Visual Regression Testing（VRT）規則

若 `docs/test-plan.md` §14 或產品有 UI 需求，核心頁面必須有 VRT 覆蓋：

**VRT 工具選型（依產品需求選擇）：**
- Playwright 截圖比對（本地開發，輕量）
- Chromatic（Storybook 整合，組件層）
- Percy（CI 整合，視覺差異報告）
- BackstopJS（靜態 HTML，頁面層）

**必須提供 VRT 覆蓋的頁面（最低要求）：**
- 首頁（Homepage）
- 登入頁（Login）
- 核心業務頁面（來自 PDD 主要畫面）

**CI/CD 整合規範：**
- GitHub Actions workflow 包含 VRT 步驟
- 失敗時上傳 VRT report artifact
- 視覺差異需 PR Review 核准後才能合併

---

## Mutation Testing 規則

高風險核心業務模組必須配置 Mutation Testing：

**工具選型（依 lang_stack）：**
- JavaScript/TypeScript：Stryker
- Python：mutmut
- Java：PIT（Pitest）
- 其他：對應語言的主流 mutation testing 工具

**目標：**
- Mutation Score ≥ 70%（核心業務模組）
- 禁止弱測試模式：「只驗證有呼叫」的弱斷言（使用具體 expect 值）

**CI 整合策略：**
- 在 Nightly CI 或 Release Gate 執行
- 低於目標 Mutation Score 觸發告警

---

## 完整範例（AUTH 模組）

```gherkin
# docs/features/auth/user_login.feature
# 來源：PRD §使用者認證，AC-1～AC-4

Feature: 使用者登入
  作為已註冊的使用者
  我希望使用 Email 和密碼登入
  以便取得 API 存取權限

  Background:
    Given 資料庫已初始化
    And 已有啟用中的使用者 email="valid@example.com"，password="Secure123!"
    And 資料庫中密碼以 bcrypt（cost=12）儲存

  @p0 @smoke @contract @TC-AUTH-001
  Scenario: 以正確 Email 和密碼成功登入
    When 使用者以 email="valid@example.com"，password="Secure123!" 呼叫 POST /api/v1/auth/login
    Then 回應狀態碼為 200
    And 回應含 access_token（JWT 格式）
    And 回應含 refresh_token
    And access_token 的 expires_in 為 3600

  @p0 @regression @TC-AUTH-002
  Scenario: 以錯誤密碼登入失敗
    When 使用者以 email="valid@example.com"，password="WrongPass!" 呼叫 POST /api/v1/auth/login
    Then 回應狀態碼為 401
    And 回應的 error.code 為 "INVALID_CREDENTIALS"
    And 回應不含任何 token

  @p0 @regression @TC-AUTH-003
  Scenario: 以不存在的 Email 登入失敗
    When 使用者以 email="notexist@example.com"，password="Any123!" 呼叫 POST /api/v1/auth/login
    Then 回應狀態碼為 401
    And 回應的 error.code 為 "INVALID_CREDENTIALS"

  @p0 @regression @TC-AUTH-004
  Scenario: 帳號被停用後無法登入
    Given 使用者帳號 status="inactive"
    When 使用者以正確 email 和 password 登入
    Then 回應狀態碼為 403
    And 回應的 error.code 為 "ACCOUNT_INACTIVE"

  @p0 @regression @TC-AUTH-005
  Scenario Outline: 格式錯誤的輸入被拒絕
    When 使用者以 email="<email>"，password="<password>" 登入
    Then 回應狀態碼為 400
    And 回應含 error.code="VALIDATION_ERROR"

    Examples:
      | email              | password  |
      |                    | Secure123 |
      | notanemail         | Secure123 |
      | valid@example.com  |           |

  @p0 @regression @TC-AUTH-006
  Scenario: 同一 IP 連續 10 次失敗登入後觸發 Rate Limit
    Given 同一 IP 已失敗登入 10 次（含本次 = 11 次）
    When 使用者再次以任意 email 和 password 登入
    Then 回應狀態碼為 429
    And 回應含 Retry-After header
```

---

## 禁止模式（Anti-patterns）

生成的 Feature Files 必須避免以下模式：

**技術語言滲入（CRITICAL）：**
- 禁止在 Given/When/Then 出現 SQL、class 名稱、HTTP 狀態碼數字（改用業務語言描述）
- 除非是 `@contract` tag 的 API Scenario，否則不暴露 HTTP 細節

**假斷言（CRITICAL）：**
- 禁止 Then 步驟為空或僅含 `# TODO`
- 禁止 `Then 程式沒有報錯` 或 `Then 操作成功`（過於模糊）
- 必須使用可驗證的具體值（欄位值、狀態碼、訊息內容）

**弱測試模式（HIGH）：**
- 禁止「只驗證有呼叫」：`Then 方法 A 被呼叫了`
- 必須驗證具體的業務結果

**隔離性破壞（HIGH）：**
- 禁止 Scenario 依賴其他 Scenario 的執行順序
- 每個 Scenario 必須能獨立執行

---

## 推斷規則

### Feature 推斷
- PRD 每個功能章節（`## 功能N` 或 `### 功能N`）→ 一個 .feature 檔案
- PRD 功能的 AC 清單 → 對應 Scenario 清單

### Scenario 推斷
- AC 正常流程 → 正常路徑 Scenario（含 `@smoke` 若為 Critical Flow）
- AC 錯誤描述 → 錯誤路徑 Scenario（含對應 HTTP 錯誤碼）
- AC 有範圍/格式限制 → 邊界條件 Scenario Outline（含 Examples Table）

### Tag 推斷
- PRD P0 功能 → `@p0` tag
- PRD P1 功能 → `@p1` tag
- Critical User Flow（來自 PRD §6 或 test-plan.md §3.3）→ 加 `@smoke` tag
- API.md 中的每個 Endpoint → 至少一個 `@contract` tag Scenario
- test-plan.md §15 RTM 中有 TC-ID → 加 `@TC-XXX-001` tag

---

## 生成前自我檢核清單

- [ ] 每個 PRD P0 功能至少有一個 .feature 檔
- [ ] 每個 PRD AC 至少有一個 Scenario（正常路徑）
- [ ] 每個 PRD AC 有對應的錯誤路徑 Scenario
- [ ] 邊界條件（空值、超長、並發等）使用 Scenario Outline
- [ ] 所有 Then 斷言為**具體且可測試**（無模糊語言）
- [ ] 無技術語言滲入 Given/When/Then（不暴露實作細節）
- [ ] 所有 API endpoint（來自 API.md）均有對應的 `@contract` tagged BDD Scenario
- [ ] Contract Testing 追溯矩陣已建立（BDD Scenario → API Endpoint → HTTP Method → 回應碼）
- [ ] 每個 Feature 有 AfterScenario / Background 清理機制，不依賴其他 Scenario 的資料殘留
- [ ] Test Data 使用 Factory 動態建立，禁止 hardcode 真實 PII
- [ ] `@contract` tag 已標記所有 API 契約測試 Scenario
- [ ] §8 Error Scenario Catalog：6 個 HTTP 錯誤碼（401/403/404/409/422/429）均有對應的 Error Scenario
- [ ] `@smoke` tag 已標記核心 Critical Flow 的主要路徑 Scenario
- [ ] Risk Level = High 的功能（來自 test-plan.md §9）Scenario 數量已加倍
- [ ] test-plan.md §15 RTM 的 TC-ID 已補充至對應 Scenario tag
- [ ] §9 Client-Side BDD：UI / E2E 測試的 BDD 場景（@ui tag）是否有範例說明？
- [ ] §14 Visual Regression Testing：核心頁面（首頁/登入/結帳）的 VRT Playwright 測試是否有範例？
- [ ] §14 VRT CI/CD：GitHub Actions workflow 是否包含 VRT 步驟（失敗時上傳 report artifact）？
- [ ] §15 Mutation Testing：高風險核心業務模組是否已配置 Stryker/mutmut，目標 Mutation Score ≥70%？
- [ ] §15 弱測試模式：確認生成的測試避免「只驗證有呼叫」的弱斷言（使用具體 expect 值）？
- [ ] 所有 `[UPSTREAM_CONFLICT]` 標記均已處理或說明
