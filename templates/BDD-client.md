# BDD-client — Client BDD Feature File Template
<!-- 對應學術標準：Cucumber / Gherkin Specification；對應業界：E2E Testing, UI Acceptance Testing -->
<!-- 本文件定義前端 E2E BDD .feature 檔案的規範結構 -->
<!-- 上游：PRD（AC 清單）+ FRONTEND.md（Screen 清單）→ 本文件 → features/client/<screen>/*.feature -->
<!-- 與 BDD-server 的職責邊界：Client BDD = UI E2E 行為；Server BDD = API 行為 + 業務邏輯 -->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | BDD-CLIENT-{{PROJECT_SLUG}}-{{YYYYMMDD}} |
| **專案名稱** | {{PROJECT_NAME}} |
| **文件版本** | v1.0 |
| **狀態** | DRAFT / IN_REVIEW / APPROVED |
| **作者（Frontend QA Lead）** | {{AUTHOR}} |
| **日期** | {{DATE}} |
| **上游 PRD** | [PRD.md](PRD.md) §{{PRD_SECTION}} |
| **上游 FRONTEND** | [FRONTEND.md](FRONTEND.md) §4 Screen 清單 |
| **審閱者** | {{FRONTEND_QA_LEAD}}, {{FRONTEND_LEAD}} |
| **E2E 工具** | {{Playwright / Cypress / Selenium}} |

> **Convention（強制規範）**：每個 PRD P0 AC 至少 1 Client Scenario（UI Happy Path + Error Flow）；所有 FRONTEND P0 Screen 有 E2E 覆蓋；禁止在 Then 步驟驗證 DB 狀態或後端業務邏輯；Scenario 必須能獨立執行。

---

## 1. Client BDD 定位（在測試金字塔中）

```
           ▲ Client BDD / E2E Tests  ← 本文件範疇
           │  features/client/<screen>/*.feature
           │  驗證 UI 行為、Screen Flow、用戶旅程
           │
          ▲▲▲ Server BDD / API Tests（由 BDD-server 負責）
          │││
         ▲▲▲▲▲ Integration Tests
         │
        ▲▲▲▲▲▲▲ Unit Tests
```

**Client BDD 的正確使用位置：**
- DO：E2E 用戶旅程（跨多個 Screen 的完整流程）
- DO：UI 行為驗收（元件顯示 / 隱藏、輸入驗證提示）
- DO：Auth Flow（未登入重導、登出跳轉）
- DO：Responsive Breakpoint 關鍵行為差異
- DON'T：不驗證 DB 狀態、業務計算、API 合約
- DON'T：不重複 Server BDD（後端邏輯）

---

## 2. Feature File 命名規範

### 2.1 Path Pattern

```
features/client/{domain}/{screen}_{flow}.feature
```

### 2.2 命名範例

| 功能 / Screen | Domain | File Path |
|-------------|--------|-----------|
| 登入頁 E2E | auth | `features/client/auth/login_flow.feature` |
| 註冊頁 E2E | auth | `features/client/auth/registration_flow.feature` |
| 訂單清單頁 | orders | `features/client/orders/order_list_view.feature` |
| 商品詳情頁 | catalog | `features/client/catalog/product_detail_view.feature` |
| 購物車頁 | checkout | `features/client/checkout/cart_view.feature` |
| 結帳完整旅程 | journeys | `features/client/journeys/checkout_journey.feature` |

### 2.3 Tag Taxonomy

| Tag | 意義 | 執行頻率 |
|-----|------|---------|
| `@smoke` | 最小可用性驗證（核心 Screen Happy Path）| 每次 deploy |
| `@regression` | 完整回歸測試套件 | PR merge / 夜間 |
| `@p0` | 核心 P0 Screen，阻塞性缺陷 | 每次 deploy |
| `@p1` | 重要 Screen，高優先 | PR merge |
| `@ui` | UI / E2E 測試標記（全部 Client BDD 均標記）| 對應 E2E job |
| `@vrt` | Visual Regression Testing | 夜間 |
| `@mobile` | 行動裝置特定 Scenario | 對應 mobile job |
| `@TC-E2E-{MODULE}-{SEQ}-{CASE}` | RTM 追溯 tag | — |

---

## 3. Standard Feature File Template

以下為完整 Client BDD feature file 結構：

```gherkin
# features/client/{domain}/{screen}_{flow}.feature
# 來源：PRD §{{FEATURE_NAME}} + FRONTEND.md §4 Screen {{N}}，AC-1～AC-N
# DOC-ID: BDD-CLIENT-{{PROJECT_SLUG}}-{{YYYYMMDD}}

@ui @{domain} @{priority_tag}
Feature: {{Screen / Flow 名稱（與 PRD / FRONTEND 一致）}}
  作為 {{角色（who）}}
  我希望 {{在 UI 上能夠做到的事}}
  以便 {{業務目的（why）}}

  # ─── 共用前置條件 ─────────────────────────────────────
  Background:
    Given 使用者已開啟應用程式
    And {{必要的 UI 初始狀態（頁面已載入 / 用戶已登入）}}

  # ─── UI Happy Path（來自 PRD AC-1 正常流程）────────────
  @p0 @smoke @ui @TC-E2E-{MODULE}-{SEQ}-001
  Scenario: {{UI 正常操作流程（業務語言）}}
    Given {{UI 初始狀態（頁面當前狀態）}}
    And {{補充 UI 前置條件（選填）}}
    When {{使用者執行的 UI 操作（點擊 / 輸入 / 滑動）}}
    Then {{UI 可觀測的結果（文字顯示 / 元件狀態 / 路由變化）}}
    And {{補充 UI 斷言（選填）}}

  # ─── UI Error Flow（來自 PRD AC-2 錯誤流程）────────────
  @p0 @regression @ui @TC-E2E-{MODULE}-{SEQ}-002
  Scenario: {{UI 錯誤流程（業務語言）}}
    Given {{UI 初始狀態}}
    When {{使用者輸入無效資料或觸發錯誤}}
    Then {{UI 顯示錯誤提示（具體文字或元件狀態）}}

  # ─── Auth Guard ────────────────────────────────────────
  @p0 @regression @ui @TC-E2E-{MODULE}-{SEQ}-003
  Scenario: 未登入用戶被重導到登入頁
    Given 使用者未登入
    When 使用者嘗試存取受保護的 {{Screen 名稱}}
    Then 頁面重導到登入頁
    And 登入後重導回原 {{Screen 名稱}}

  # ─── 邊界條件 ──────────────────────────────────────────
  @p1 @regression @ui @TC-E2E-{MODULE}-{SEQ}-004
  Scenario Outline: {{UI 邊界條件描述}}
    Given {{UI 初始狀態}}
    When {{使用者在輸入欄位輸入 "<input_value>"}}
    Then {{UI 顯示 "<expected_ui_state>"}}

    Examples:
      | input_value | expected_ui_state            |
      | ""          | 顯示「此欄位為必填」的錯誤提示 |
      | " "         | 顯示「不可輸入空白」的錯誤提示 |
      | "valid"     | 欄位驗證通過，提交按鈕啟用     |
```

---

## 4. Multi-Screen E2E Journey Template

跨多個 Screen 的核心用戶旅程 Scenario：

```gherkin
# features/client/journeys/{journey_name}.feature
# 來源：PRD §{{核心用戶旅程}} + FRONTEND.md §4 關鍵 Screen Flow

@ui @p0 @smoke
Feature: {{核心用戶旅程名稱}}
  作為 {{角色}}
  我希望完成 {{完整的業務流程}}
  以便 {{業務目的}}

  Background:
    Given 使用者已登入並在 {{起始 Screen}} 頁面

  @TC-E2E-JOURNEY-{SEQ}-001
  Scenario: {{旅程名稱}} — 完整成功路徑
    Given 使用者在 {{Screen 1}} 頁面
    When 使用者 {{操作 1}}
    And 使用者在 {{Screen 2}} 頁面 {{操作 2}}
    And 使用者確認 {{最終操作}}
    Then 頁面跳轉到 {{完成 Screen}}
    And 畫面顯示 {{成功確認訊息}}

  @TC-E2E-JOURNEY-{SEQ}-002
  Scenario: {{旅程名稱}} — 中途放棄返回
    Given 使用者在 {{Screen 2}} 頁面
    When 使用者點擊「取消」或返回
    Then 頁面返回到 {{Screen 1}}
    And 使用者輸入的資料 {{保留 / 清除（依設計決定）}}
```

---

## 5. Visual Regression Testing Template

核心頁面的 VRT Scenario：

```gherkin
  @vrt @p0
  Scenario: {{Screen 名稱}} — 視覺外觀符合設計稿
    Given 使用者在 {{Screen 名稱}} 頁面
    When 頁面已完整載入
    Then 頁面視覺外觀與設計稿一致（截圖比對）

  @vrt @p1 @mobile
  Scenario: {{Screen 名稱}} — 行動裝置視覺外觀
    Given 使用者以行動裝置解析度（375×667）檢視 {{Screen 名稱}}
    When 頁面已完整載入
    Then 頁面在行動裝置上正確顯示（無元素溢出、無排版錯誤）
```

---

## 6. 完整範例（登入頁 E2E）

```gherkin
# features/client/auth/login_flow.feature
# 來源：PRD §使用者認證 + FRONTEND.md §4 Screen 01 — 登入頁，AC-1～AC-4

@ui @auth @p0
Feature: 登入頁 E2E 流程
  作為未認證的使用者
  我希望在登入頁輸入帳號密碼
  以便進入系統並使用功能

  Background:
    Given 使用者已開啟應用程式並在登入頁

  @smoke @TC-E2E-AUTH-UI-001-001
  Scenario: 以正確帳號密碼成功登入
    Given 使用者在登入頁並填入有效的 Email 和密碼
    When 使用者點擊「登入」按鈕
    Then 頁面跳轉到儀表板（Dashboard）
    And 頁面顯示使用者名稱於頂部導覽列

  @regression @TC-E2E-AUTH-UI-001-002
  Scenario: 輸入錯誤密碼時顯示錯誤訊息
    Given 使用者在登入頁輸入有效 Email 但錯誤密碼
    When 使用者點擊「登入」按鈕
    Then 頁面顯示「帳號或密碼不正確，請重試」錯誤提示
    And 密碼欄位清空
    And 頁面停留在登入頁

  @regression @TC-E2E-AUTH-UI-001-003
  Scenario: 未登入直接存取受保護頁面時重導
    Given 使用者未登入
    When 使用者直接存取「訂單管理」頁面
    Then 頁面重導到登入頁
    And URL 含有原目標頁面的重導參數

  @regression @TC-E2E-AUTH-UI-001-004
  Scenario Outline: 空白輸入欄位時顯示必填提示
    Given 使用者在登入頁
    When 使用者 "<leave_field>" 為空並點擊「登入」
    Then 畫面顯示 "<error_message>"
    And 頁面停留在登入頁

    Examples:
      | leave_field | error_message         |
      | Email 欄位  | Email 為必填欄位       |
      | 密碼欄位    | 密碼為必填欄位         |

  @vrt @TC-E2E-AUTH-UI-001-005
  Scenario: 登入頁視覺外觀符合設計稿
    Given 使用者在登入頁
    When 頁面已完整載入
    Then 頁面視覺外觀與設計稿一致（截圖比對）
```
