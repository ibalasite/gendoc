# BDD-server — Server BDD Feature File Template
<!-- 對應學術標準：Cucumber / Gherkin Specification；對應業界：API Contract Testing, ATDD -->
<!-- 本文件定義後端 BDD .feature 檔案的規範結構 -->
<!-- 上游：PRD（AC 清單）+ API.md（Endpoint 清單）→ 本文件 → features/<module>/*.feature -->
<!-- 與 BDD-client 的職責邊界：Server BDD = API 行為 + 業務邏輯；Client BDD = UI E2E 行為 -->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | BDD-SERVER-{{PROJECT_SLUG}}-{{YYYYMMDD}} |
| **專案名稱** | {{PROJECT_NAME}} |
| **文件版本** | v1.0 |
| **狀態** | DRAFT / IN_REVIEW / APPROVED |
| **作者（QA Lead / Tech Lead）** | {{AUTHOR}} |
| **日期** | {{DATE}} |
| **上游 PRD** | [PRD.md](PRD.md) §{{PRD_SECTION}} |
| **上游 API** | [API.md](API.md) — 所有 Endpoint |
| **審閱者** | {{QA_LEAD}}, {{BACKEND_LEAD}} |

> **Convention（強制規範）**：每個 PRD AC 至少 2 Scenarios（正常路徑 + 錯誤路徑）；所有 API Endpoint 有 @contract Scenario；6 個 HTTP 錯誤碼（401/403/404/409/422/429）有對應 Error Scenario；禁止 UI 操作滲入 Step。

---

## 1. Server BDD 定位（在測試金字塔中）

```
           ▲ E2E / UI Tests（由 BDD-client 負責）
           │
          ▲▲▲ Server BDD / Acceptance Tests  ← 本文件範疇
          │││  features/<module>/*.feature
          │││  驗證 API 行為、業務邏輯、資料持久化
          │││
         ▲▲▲▲▲ Integration Tests
         │
        ▲▲▲▲▲▲▲ Unit Tests
```

**Server BDD 的正確使用位置：**
- DO：驗收 API Endpoint 的行為（HTTP 狀態碼、回應結構）
- DO：驗收業務邏輯（業務規則違反、角色授權）
- DO：驗收資料持久化（背景狀態設置，非 DB 直接查詢）
- DON'T：不包含 UI 操作（點擊、頁面跳轉）
- DON'T：不重複 Unit Tests（函式邏輯、算法細節）

---

## 2. Feature File 命名規範

### 2.1 Path Pattern

```
features/{domain}/{resource}_{action}.feature
```

### 2.2 命名範例

| PRD 功能 | Domain | File Path |
|---------|--------|-----------|
| 使用者登入 | auth | `features/auth/user_login.feature` |
| 使用者註冊 | auth | `features/auth/user_registration.feature` |
| 訂單建立 | orders | `features/orders/order_create.feature` |
| 訂單查詢 | orders | `features/orders/order_list.feature` |
| 商品搜尋 | catalog | `features/catalog/product_search.feature` |
| 密碼重設 | auth | `features/auth/password_reset.feature` |

### 2.3 Tag Taxonomy

| Tag | 意義 | 執行頻率 |
|-----|------|---------|
| `@smoke` | 最小可用性驗證，每次部署必跑 | 每次 deploy |
| `@regression` | 完整回歸測試套件 | PR merge / 夜間 |
| `@p0` | 核心業務路徑，阻塞性缺陷 | 每次 deploy |
| `@p1` | 重要功能，高優先 | PR merge |
| `@api` | 純 API 層測試 | 對應 CI job |
| `@contract` | API 契約測試 Scenario | 每次 deploy |
| `@TC-E2E-{MODULE}-{SEQ}-{CASE}` | RTM 追溯 tag | — |

---

## 3. Standard Feature File Template

以下為完整 Server BDD feature file 結構：

```gherkin
# features/{domain}/{resource}_{action}.feature
# 來源：PRD §{{FEATURE_NAME}}，AC-1～AC-N
# 上游 API：API.md §{{ENDPOINT}}
# DOC-ID: BDD-SERVER-{{PROJECT_SLUG}}-{{YYYYMMDD}}

@{domain} @{priority_tag}
Feature: {{功能名稱（與 PRD 功能標題一致）}}
  作為 {{角色（who）}}
  我希望 {{功能描述（what）}}
  以便 {{業務目的（why）}}

  # ─── 共用前置條件 ───────────────────────────────────────
  Background:
    Given 資料庫已初始化（clean state）
    And {{必要的測試資料：描述業務狀態而非 DB 操作}}

  # ─── 正常路徑（來自 PRD AC-1 正常流程）─────────────────
  @p0 @smoke @contract @TC-E2E-{MODULE}-{SEQ}-001
  Scenario: {{正常路徑描述，使用業務語言}}
    Given {{系統當前狀態（前置條件，描述狀態非操作）}}
    And {{補充前置條件（選填）}}
    When {{使用者或系統執行的單一動作}}
    Then {{可觀測的業務結果（具體、可測試）}}
    And {{補充斷言（選填）}}

  # ─── 錯誤路徑（來自 PRD AC-2 錯誤流程）─────────────────
  @p0 @regression @TC-E2E-{MODULE}-{SEQ}-002
  Scenario: {{錯誤路徑描述}}
    Given {{初始狀態}}
    When {{觸發錯誤的動作}}
    Then {{預期的錯誤回應（業務語言描述錯誤類型）}}

  # ─── 401 未認證 ──────────────────────────────────────────
  @p0 @regression @contract @TC-E2E-{MODULE}-{SEQ}-003
  Scenario: 未提供 Token 時拒絕存取
    Given 使用者未經認證（無有效 Token）
    When 使用者嘗試執行 {{操作}}
    Then 系統拒絕存取並回應「未認證」錯誤

  # ─── 403 無權限 ──────────────────────────────────────────
  @p0 @regression @contract @TC-E2E-{MODULE}-{SEQ}-004
  Scenario: 角色不符時拒絕操作
    Given 使用者已認證但角色為 {{低權限角色}}
    When 使用者嘗試執行 {{需要高權限的操作}}
    Then 系統拒絕並回應「無操作權限」錯誤

  # ─── 邊界條件（來自 PRD AC-N 邊界）──────────────────────
  @p0 @regression @TC-E2E-{MODULE}-{SEQ}-005
  Scenario Outline: {{邊界條件描述}}
    Given {{初始狀態}}
    When {{使用者輸入或提供 "<input_value>"}}
    Then {{預期結果是 "<expected_result>"}}

    Examples:
      | input_value | expected_result        |
      | ""          | 錯誤：必填欄位          |
      | "a" * 256   | 錯誤：超過最大長度限制  |
      | "valid"     | 操作成功               |
```

---

## 4. Error Catalog Template（必備 6 個 HTTP 錯誤碼）

每個 Feature 必須涵蓋以下 HTTP 錯誤碼的 Scenario（以業務語言描述，非技術語言）：

```gherkin
  # ─── 401 Unauthorized ────────────────────────────────────
  @p0 @regression @contract
  Scenario: Token 無效或過期時拒絕存取
    Given Token 已過期
    When 使用者嘗試執行任何需要認證的操作
    Then 系統回應「認證失敗，請重新登入」

  # ─── 403 Forbidden ───────────────────────────────────────
  @p0 @regression @contract
  Scenario: 無操作權限時拒絕執行
    Given 使用者已登入但角色不具備所需權限
    When 使用者嘗試執行受限操作
    Then 系統回應「無操作權限」

  # ─── 404 Not Found ───────────────────────────────────────
  @p0 @regression @contract
  Scenario: 操作不存在的資源時回應資源不存在
    Given 系統中不存在 ID 為 "99999" 的資源
    When 使用者嘗試操作該資源
    Then 系統回應「資源不存在」

  # ─── 409 Conflict ────────────────────────────────────────
  @p0 @regression @contract
  Scenario: 建立重複資源時回應衝突
    Given 系統中已存在 {{唯一識別符}} 為 "{{existing_value}}" 的資源
    When 使用者再次以相同 {{唯一識別符}} 建立資源
    Then 系統回應「資源已存在，無法重複建立」

  # ─── 422 Unprocessable ───────────────────────────────────
  @p0 @regression @contract
  Scenario: 違反業務規則時回應業務錯誤
    Given {{業務前置條件}}
    When 使用者嘗試執行違反業務規則的操作（{{具體規則說明}}）
    Then 系統回應「業務規則違反：{{具體規則說明}}」

  # ─── 429 Rate Limit ──────────────────────────────────────
  @p0 @regression
  Scenario: 超過速率限制時觸發限流
    Given 同一 IP 或用戶在短時間內已達到速率限制
    When 使用者再次發出請求
    Then 系統回應「請求過於頻繁，請稍後再試」並提供重試等待時間
```

---

## 5. Contract Testing Template

每個 API.md Endpoint 的 Contract Scenario 結構：

```gherkin
  @p0 @contract @smoke
  Scenario: POST /{{api-path}} 成功回應包含必要欄位
    Given {{必要的前置狀態}}
    When 系統呼叫 {{操作描述}} API
    Then 系統確認操作成功
    And 回應包含 {{必要欄位 1}}
    And 回應包含 {{必要欄位 2}}
```

注意：Contract Scenario 的 Then 步驟需驗證回應結構，但使用業務語言（「回應包含有效 Token」而非「回應 access_token 欄位不為空」）。

---

## 6. 完整範例（AUTH 模組）

```gherkin
# features/auth/user_login.feature
# 來源：PRD §使用者認證，AC-1～AC-4

@auth @p0
Feature: 使用者登入
  作為已註冊的使用者
  我希望使用 Email 和密碼登入
  以便取得系統存取權限

  Background:
    Given 資料庫已初始化
    And 已有啟用中的使用者 email="valid@example.com"

  @smoke @contract @TC-E2E-AUTH-001-001
  Scenario: 以正確認證資訊成功登入
    When 使用者以正確的 email 和密碼登入
    Then 系統確認登入成功
    And 系統回應包含有效的存取憑證（access_token）
    And 系統回應包含刷新憑證（refresh_token）

  @regression @TC-E2E-AUTH-001-002
  Scenario: 以錯誤密碼登入時回應認證失敗
    When 使用者以正確 email 但錯誤密碼登入
    Then 系統回應「帳號或密碼不正確」
    And 系統不回應任何憑證

  @regression @TC-E2E-AUTH-001-003
  Scenario: 以不存在的 Email 登入時回應認證失敗
    When 使用者以未註冊的 email 登入
    Then 系統回應「帳號或密碼不正確」

  @regression @TC-E2E-AUTH-001-004
  Scenario: 帳號被停用後無法登入
    Given 使用者帳號已被停用
    When 使用者以正確認證資訊嘗試登入
    Then 系統回應「帳號已停用，請聯繫管理員」

  @regression @TC-E2E-AUTH-001-005
  Scenario Outline: 格式錯誤的輸入被拒絕
    When 使用者以 email="<email>" 和 password="<password>" 登入
    Then 系統回應「輸入格式錯誤」

    Examples:
      | email               | password  |
      |                     | Secure123 |
      | notanemail          | Secure123 |
      | valid@example.com   |           |

  @regression @TC-E2E-AUTH-001-006
  Scenario: 連續多次失敗登入後觸發速率限制
    Given 同一來源已連續多次登入失敗超過限制次數
    When 使用者再次嘗試登入
    Then 系統回應「嘗試次數過多，請稍後再試」
```
