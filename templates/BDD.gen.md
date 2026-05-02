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
  - docs/FRONTEND.md  # Layer 6 — 前端元件架構（Client BDD Screen 對應）
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
| `FRONTEND.md`（若存在）| §4 Screen 清單、§5 Component Architecture | Client BDD @ui Scenario 的 Screen 名稱和元件邊界來自 FRONTEND；確保 E2E Scenario Given/When/Then 與實際 Screen 對應 |

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
| `@ha` | 高可用性驗證 Scenario | Pod Failover / DB Failover / Graceful Shutdown（必填）|
| `@failover` | 故障切換驗證 Scenario | 元件故障自動恢復的 E2E 驗證 |
| `@chaos` | 混沌工程 Scenario | 強制終止 Pod / 注入延遲 / 模擬 DB 故障（夜間 CI）|
| `@admin` | Admin 後台功能 Scenario | has_admin_backend=true 時必填 |
| `@rbac` | 角色權限控制 Scenario | RBAC 邊界測試（Admin 角色隔離、Permission 邊界）|
| `@audit` | 稽核日誌驗證 Scenario | 高風險操作 AuditLog 記錄完整性驗證 |

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

## §16 HA BDD 生成步驟

> **觸發時機**：每次生成 BDD 時必須執行（HA 測試是 MVP 必要驗收標準，不是 Future Scope）。

### 步驟

1. 讀取 `EDD.md §3.6`（HA/SPOF/SCALE/BCP 架構規格）：
   - §3.6.1 SPOF 分析表 → 確認每個元件的 Min Replicas 和 Failover 機制
   - §3.6.4 BCP 場景 → 確認 5 個故障情境的 RTO 目標
   - §3.6.5 Graceful Shutdown → 確認 5 步驟流程和 ≤30s 目標

2. 讀取 `test-plan.md §3.6`（HA/Failover/Chaos Tests）：
   - §3.6.1 Integration Test 表 → 確認各元件的測試步驟
   - §3.6.2 E2E Chaos BDD → 確認已規劃的 HA 場景清單

3. 生成 `features/ha/` 目錄下的 4 個 HA Feature 檔案：
   - `features/ha/api_pod_failover.feature` — Pod Failover + Graceful Shutdown（參考 §16.1）
   - `features/ha/db_failover.feature` — DB Primary Failover + Replica Lag（參考 §16.2）
   - `features/ha/redis_failover.feature` — Redis Sentinel Failover（參考 §16.3）
   - `features/ha/worker_idempotency.feature` — Worker 冪等性（參考 §16.4）

4. 每個 HA Scenario 必須：
   - 使用 `@ha` tag（必填）
   - Failover 類型加 `@failover`；混沌注入類型加 `@chaos`
   - Given 含具體 replica 數量和負載（e.g., 2 個 Pod，每秒 10 req）
   - Then 含可驗證的 RTO 數字（e.g., ≤ 30s / ≤ 60s）和 5XX 錯誤率上限

5. 驗證：`@ha` tagged Scenario 總數 ≥ 3 個（Pod Failover / DB Failover / Graceful Shutdown 三個最低必備）。

---

## §17 Admin BDD 生成步驟

> **觸發條件**：讀取 state 中 `has_admin_backend` 欄位；若為 `true` 則執行，否則在 BDD.md §17 填入「本專案無 Admin 後台，跳過 §17」。

```bash
_HAS_ADMIN=$(python3 -c "import json; print(json.load(open('.gendoc-state.json')).get('has_admin_backend', 'false'))")
```

### 若 has_admin_backend=true，執行步驟

1. 讀取 `docs/ADMIN_IMPL.md`（若存在）或 `API.md §Admin` 相關章節：
   - RBAC 角色定義（super_admin / operator / content_manager 等）
   - Admin API Endpoints 清單（/admin/api/v1/ 前綴）
   - AuditLog 欄位規格（actor_id / action_type / resource_type / resource_id / ip / timestamp）

2. 生成 `features/admin/` 目錄下的 2 個 Admin Feature 檔案：
   - `features/admin/admin_auth.feature` — Admin 認證 + RBAC（參考 §17.1）
   - `features/admin/admin_audit.feature` — 稽核日誌完整性驗證（參考 §17.2）

3. 每個 Admin Scenario 必須：
   - 使用 `@admin` tag（必填）
   - 認證類加 `@auth`；RBAC 邊界類加 `@rbac`；稽核日誌類加 `@audit`
   - RBAC 場景：每個 Admin 角色至少有一個「被拒絕存取」的 403 Scenario
   - Audit 場景：驗證所有高風險操作（delete / ban / role_change）均寫入完整 AuditLog

4. 驗證：
   - `@admin @rbac` tagged Scenario ≥ 2 個（每個 Admin 角色邊界各一個）
   - `@admin @audit` tagged Scenario ≥ 2 個（覆蓋高風險操作和不可竄改性）

---

## §18 Spring Modulith BDD 生成步驟

> **觸發條件**：永遠執行（Spring Modulith 是本系統的架構前提）。

### 18.1 推導跨 BC Dependency Pair

```bash
# 從 ARCH §4 服務邊界表或 EDD §3.4 讀取所有 BC 清單
# 識別跨 BC 依賴關係（Domain Event Publisher → Consumer）
# 每對 (source_bc, target_bc) = 一個 dependency pair
```

1. 讀取 `docs/ARCH.md §4`（或 `docs/EDD.md §3.4`）：提取所有 Bounded Context 名稱及其相互依賴的 Domain Event 清單
2. 建立 dependency pair 表：`{source_bc} --[{EventName}]--> {target_bc}`

### 18.2 生成 Module Isolation 場景（HC-5 DAG 驗證）

對每個 BC 生成一個冷啟動場景：

```
# features/{bc_name}/isolation/{bc_name}_cold_start.feature
@modulith @module-isolation @p0 @api
Feature: {BCName} 模組冷啟動隔離驗證
  Scenario: 僅啟動 {BCName} 模組時能獨立運行
    Given 僅啟動 {BCName} Bounded Context，其他 BC 以 stub 替代
    When 執行 {BCName} 的核心業務操作
    Then 業務流程完成，無任何對其他 BC 的直接 DB 存取錯誤
    And 所有跨 BC 呼叫均透過 Public Interface 或 Mock Event Bus
```

### 18.3 生成 Domain Event Contract 場景（HC-3 驗證）

對每個跨 BC dependency pair 生成 2 個場景：

1. **Producer Contract**（`features/cross-module/event/{event_name_snake}_producer.feature`）：
   - `@event-contract @modulith @p0 @api`
   - 驗證觸發動作 → 正確發布 Event → Schema Version 合規

2. **Consumer Contract**（`features/cross-module/event/{event_name_snake}_consumer.feature`）：
   - `@event-contract @modulith @p0 @api`
   - 驗證接收 Event → 業務狀態更新 → 無直接 DB 跨 BC 存取

### 18.4 生成 Cross-Module Public Interface 場景（HC-2 驗證）

對每個跨 BC HTTP 呼叫生成一個場景（`features/cross-module/api/{source_bc}_calls_{target_bc}.feature`）：
- `@cross-module @modulith @p1 @api`
- When 步驟呼叫 `{TargetBC}` 的 Public REST API，不直接操作其 Repository

### 18.4 驗收標準

- `@modulith @module-isolation` Scenario 數量 = BC 數量（每個 BC ≥ 1）
- `@event-contract` Scenario 數量 = dependency pair 數量 × 2（Producer + Consumer）
- `@cross-module` Scenario 數量 ≥ dependency pair 數量
- 所有以上 Scenario 存入 `features/cross-module/` 或 `features/{bc}/isolation/` 目錄

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
- [ ] Feature 目錄結構使用 `features/{bounded-context}/{domain}/` 兩層路徑（HC-1 合規）
- [ ] 每個跨 BC 依賴（來自 ARCH §4）有對應的 `@event-contract` 場景（Producer + Consumer 各一）
- [ ] 每個 Bounded Context 有至少一個 `@module-isolation` 冷啟動驗證場景（HC-5 DAG 驗證）
- [ ] 無 Scenario 在模組 A 的 step 中直接操作模組 B 的 DB 資料（HC-1 違規）
- [ ] 所有 `@cross-module` 場景的 When 步驟指向對方 BC 的 Public Service Interface，不直接呼叫其 Repository（HC-2 合規）

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

> **讀取 lang_stack 方式**：`python3 -c "import json; print(json.load(open('.gendoc-state.json')).get('lang_stack','unknown'))"`

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| 所有 Feature 齊全 | PRD §User Stories 每個 Story 至少有一個對應 Feature 檔案 | 補充缺失 Feature |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | 使用符合 state.lang_stack 的 BDD 框架格式（Cucumber / Behave / Gherkin） | 修正至一致 |
| 數值非 TBD/N/A | 所有 Scenario 的 And/Given/Then 條件含有具體數值 | 從 PRD/API 提取填入 |
| 上游術語對齊 | 步驟中的術語與 PRD/API/SCHEMA 定義一致 | 修正術語 |
| 測試資料規格 | 每個 Feature 的 Background 或 Examples 有具體測試資料（非通用假資料） | 補充業務語義測試資料 |
| HA BDD 覆蓋 | `features/ha/` 目錄存在且 @ha tagged Scenario ≥ 3 個（Pod Failover / DB Failover / Graceful Shutdown）| 依 §16 生成缺失 HA Feature |
| HA Then 具體 RTO | 所有 @ha Scenario 的 Then 含具體 RTO 數字（≤ 30s / ≤ 60s）和 5XX 錯誤率上限 | 補充具體 RTO 值 |
| Admin BDD 覆蓋 | has_admin_backend=true 時：features/admin/ 存在，@admin @rbac ≥ 2 + @admin @audit ≥ 2 | 依 §17 生成缺失 Admin Feature |
| Admin RBAC 邊界 | 每個 Admin 角色至少有一個「403 拒絕存取」Scenario | 補充 RBAC 邊界測試 |
| Modulith 架構 BDD | `features/architecture/` 目錄存在，@modulith @p0 Scenario ≥ 4 個（HC-1 schema isolation + HC-2 cross-module + HC-3 event-contract + HC-5 DAG）| 依 §18 生成缺失 Modulith Feature |
| Event Contract 覆蓋 | @event-contract Scenario 覆蓋 EDD §4.6 所有 Domain Events 的跨 BC consumer | 補充缺失的 event contract Scenario |
| Module Isolation 場景 | @module-isolation Scenario 覆蓋所有 BC（每個 BC ≥ 1 個冷啟動驗證場景）| 依 §18.1 / §18.2 補充 |
