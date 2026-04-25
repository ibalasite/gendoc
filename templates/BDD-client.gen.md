---
doc-type: BDD-client
output-path: features/client/（多個 .feature 檔案）
output-glob: features/client/*.feature
multi-file: true
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md
  - docs/FRONTEND.md
  - docs/EDD.md
  - docs/AUDIO.md    # 若存在：音效觸發事件 → 按鈕點擊/場景切換 音訊行為 scenario
  - docs/ANIM.md     # 若存在：動畫狀態清單 → 進場/離場/載入動畫 scenario
  - docs/test-plan.md
quality-bar: "所有 PRD P0 AC 有對應 Client BDD Scenario（UI Happy Path + Error Flow）；所有 FRONTEND.md P0 Screen Flow 有 E2E Scenario 覆蓋；無後端業務邏輯驗證（DB 狀態、業務計算）出現在 Then 步驟；可直接用 Playwright / Cypress 執行"
gen-expert: "資深 Frontend QA Expert + E2E Automation Specialist（10 年以上 Playwright / Cypress BDD 經驗）"
---

# BDD-client.gen.md — Client BDD Feature Files 生成規則

依 PRD 每個驗收標準（AC）、FRONTEND.md 每個 Screen Flow，自動生成完整的 Client BDD Feature Files（Gherkin 格式）。
輸出目錄：`features/client/`（每個 PRD 功能或 Screen 模組 → 一個 .feature 檔案）。

**職責邊界（與 BDD-server 區分）：**
- Client BDD = E2E UI 行為、畫面顯示 / 隱藏、用戶操作流程、視覺狀態轉換、跨 Screen 旅程
- 禁止包含 DB 資料驗證、後端業務計算、API 合約細節（那是 BDD-server 的責任）
- Client BDD 的 Then 步驟只驗證 UI 可觀測狀態（畫面文字、元件狀態、路由跳轉）

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
| `IDEA.md`（若存在）| 全文 | 了解產品願景，E2E 場景的業務語言需反映 IDEA 業務概念 |
| `BRD.md` | 業務目標、驗收標準 | Feature 標題的業務語意來自 BRD |
| `PRD.md` | 所有功能 AC | **主要輸入**：每個 AC → 至少 1 UI Happy Path + 1 Error Flow |
| `PDD.md`（若存在）| §4 功能需求、§6 互動設計、§7 UI Flow | **E2E 步驟主要來源**：Given/When/Then 的 UI 操作步驟來自 PDD 互動流程 |
| `FRONTEND.md`（若存在）| §4 Screen 清單、§5 Component Architecture | **Screen 對應**：確保 E2E Scenario Given/When/Then 與實際 Screen 名稱對應 |
| `EDD.md` | §4 Security（Auth Flow）| 確認登入 / 登出 / Token 刷新的 UI Flow |
| `test-plan.md` | §3.3 E2E Plan、§9 Risk Matrix | Smoke 標記；Risk=High 功能 Scenario 加倍 |

若某文件不存在，靜默跳過，依既有流程繼續。

### FRONTEND.md 特別讀取規則

若 `docs/FRONTEND.md` 存在：
- 讀取 **§4 Screen 清單**：P0 Screen 全部必須有 E2E Scenario（Happy Path + Error Flow）
- 讀取 **§5 Component Architecture**：了解關鍵 UI 元件名稱，Given/When/Then 使用一致命名
- 讀取 **§3 Design System / Responsive Breakpoints**：了解需要覆蓋的裝置/解析度範圍

若 FRONTEND.md 不存在（僅後端服務）：
- 依 PRD 功能生成 API Client 層 E2E 測試，不包含 UI 元件描述

### test-plan.md 特別讀取規則

若 `docs/test-plan.md` 存在，額外讀取：
- **§3.3 E2E / BDD Tests**：確認 E2E 工具（Playwright / Cypress）、Browser Matrix、Critical User Flow 清單
  → 清單中標記為 `Smoke: Y` 的 Flow 必須生成 `@smoke` tag Scenario
- **§9 Risk-Based Testing Matrix**：Risk Level = High 的功能，Scenario 數量加倍
- **§15 RTM（若存在 TC-ID）**：生成的 Scenario tag 補充對應 TC-ID（格式：`@TC-E2E-{MODULE}-{SEQ}-{CASE}`）

### IDEA.md Appendix C 素材讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與 E2E 相關的檔案。
結合 Appendix C「應用於」欄位標有「BDD §」或「E2E §」的段落，作為生成 Client Scenario 的補充依據。
若無引用，靜默跳過。

---

## 多檔案生成規則

**一個 PRD 功能或 Screen 模組 → 一個 .feature 檔案**，輸出到 `features/client/` 目錄。

命名規則：
```
features/client/{domain}/{screen}_{flow}.feature
```

範例：
| 功能 / Screen | Domain | 輸出路徑 |
|-------------|--------|---------|
| 登入頁 E2E | auth | `features/client/auth/login_flow.feature` |
| 註冊頁 E2E | auth | `features/client/auth/registration_flow.feature` |
| 訂單清單頁 | orders | `features/client/orders/order_list_view.feature` |
| 商品詳情頁 | catalog | `features/client/catalog/product_detail_view.feature` |
| 結帳 E2E Flow | checkout | `features/client/checkout/checkout_flow.feature` |

**[AI 指令]** 生成每個 .feature 檔案時，使用 Write 工具逐一寫入，並輸出：
```
GENERATED_FILE: features/client/{domain}/{name}.feature
```
最後彙總所有生成的檔案清單。

---

## Gherkin 格式規範

### 標準結構

```gherkin
# features/client/<domain>/<screen>_<flow>.feature
# 來源：PRD §<功能名稱> + FRONTEND.md §4 Screen <N>，AC-1～AC-N

Feature: <Screen / Flow 名稱（與 PRD / FRONTEND 一致）>
  作為 <角色>
  我希望 <能夠 / 看到>
  以便 <目的>

  Background:
    Given 使用者已開啟應用程式
    And <必要的前置 UI 狀態>

  # ─── UI Happy Path ────────────────────────────────────
  @p0 @smoke @ui @TC-E2E-{MODULE}-{SEQ}-001
  Scenario: <UI 正常操作流程（業務語言）>
    Given <UI 初始狀態（頁面 / 元件當前狀態）>
    When <使用者執行的 UI 操作>
    Then <UI 可觀測的結果（文字、元件狀態、路由變化）>
    And <補充 UI 斷言>

  # ─── UI Error Flow ────────────────────────────────────
  @p0 @regression @ui @TC-E2E-{MODULE}-{SEQ}-002
  Scenario: <UI 錯誤流程（業務語言）>
    Given <UI 初始狀態>
    When <使用者輸入無效資料或觸發錯誤>
    Then <UI 顯示錯誤提示（具體文字或元件狀態）>

  # ─── 邊界條件 ─────────────────────────────────────────
  @p1 @regression @ui @TC-E2E-{MODULE}-{SEQ}-003
  Scenario Outline: <UI 邊界條件描述>
    Given <UI 初始狀態>
    When <使用者在輸入欄位輸入 "<input_value>">
    Then <UI 顯示 "<expected_ui_state>">

    Examples:
      | input_value | expected_ui_state      |
      | ""          | 顯示「此欄位為必填」    |
      | " "         | 顯示「不可輸入空白」    |
      | "valid"     | 欄位驗證通過，按鈕啟用  |
```

### Step 語義規範（UI 層）

| Step | 規範 | 反面範例（禁止）|
|------|------|----------------|
| Given | 描述 UI **初始狀態**（頁面 / 元件） | `Given 資料庫已有用戶` |
| When | 描述使用者的 **UI 操作**（點擊、輸入、滑動）| `When 呼叫 POST /api/login` |
| Then | 描述 UI **可觀測的狀態變化**（文字、元件可見性、路由）| `Then 資料庫記錄已更新` |

**禁止在 Client BDD 中出現：**
- DB 狀態驗證（「Then 資料庫記錄已更新」）
- HTTP 狀態碼（「Then 回應狀態碼為 200」）
- 後端業務計算結果（「Then 帳戶餘額扣除了手續費」）
- API 端點路徑（`/api/v1/users`）

---

## Screen Flow 覆蓋規則

若 `docs/FRONTEND.md` 存在，每個 **P0 Screen** 必須有對應的 .feature 覆蓋：
1. **主要 Happy Path**：使用者完整走過 Screen 主要功能
2. **至少一個 Error Flow**：輸入驗證失敗 / 網路錯誤 / 無資料狀態
3. **Auth Guard**：未登入用戶被重導到登入頁

若 FRONTEND.md 不存在，依 PRD 功能列表生成對應 Client 測試檔案。

---

## Multi-Screen E2E Journey Scenario

跨多個 Screen 的核心用戶旅程（Critical User Journey）需要有完整流程 Scenario：

```gherkin
# features/client/journeys/checkout_journey.feature

Feature: 購物結帳完整旅程
  作為已登入的用戶
  我希望從選擇商品到完成付款
  以便順利購買商品

  @p0 @smoke @ui @TC-E2E-CHECKOUT-001
  Scenario: 完整結帳旅程 — 信用卡付款
    Given 使用者已登入並在商品清單頁
    When 使用者點擊商品「A」並加入購物車
    And 使用者前往購物車頁面
    And 使用者點擊「結帳」
    And 使用者在付款頁填入有效信用卡資訊
    And 使用者點擊「確認付款」
    Then 頁面跳轉到訂單確認頁
    And 畫面顯示「訂單已成功建立」
    And 顯示訂單編號
```

---

## Visual Regression Testing（VRT）規則

若 `docs/test-plan.md` §14 或 FRONTEND.md 有 UI 需求，核心頁面必須有 VRT 覆蓋：

**VRT 工具選型（依 EDD lang_stack）：**
- Playwright 截圖比對（本地開發，輕量）
- Chromatic（Storybook 整合，組件層）
- Percy（CI 整合，視覺差異報告）

**必須提供 VRT 覆蓋的頁面（最低要求）：**
- 首頁（Homepage）
- 登入頁（Login）
- 核心業務頁面（來自 FRONTEND.md P0 Screen 清單）

---

## Tag 策略

| Tag | 用途 | 規則 |
|-----|------|------|
| `@p0` | Must-have 功能 Scenario | PRD P0 AC 全部標記 |
| `@p1` | Should-have 功能 Scenario | PRD P1 AC 全部標記 |
| `@smoke` | 核心主要路徑 Scenario | Critical Flow Happy Path |
| `@regression` | 完整回歸測試 | 所有 Scenario 均標記 |
| `@ui` | UI / E2E 測試 | 所有 Client BDD Scenario 標記 |
| `@vrt` | Visual Regression Testing | 有截圖比對的 Scenario |
| `@TC-E2E-{MODULE}-{SEQ}-{CASE}` | RTM 追溯 tag | 與 test-plan RTM 完全一致 |

---

## 禁止模式（Anti-patterns）

**後端邏輯滲入（CRITICAL）：**
- 禁止 Then 步驟驗證 DB 狀態、業務計算結果、API 合約細節
- Client BDD 只驗證 UI 可觀測狀態

**假斷言（CRITICAL）：**
- 禁止 Then 步驟為空或僅含 `# TODO`
- 禁止 `Then 操作成功`（過於模糊）
- 必須具體描述 UI 狀態（「顯示成功訊息」、「按鈕變為 disabled」、「頁面跳轉到 /dashboard」）

**隔離性破壞（HIGH）：**
- 禁止 Scenario 依賴其他 Scenario 的 UI 狀態殘留
- 每個 Scenario 必須能獨立執行（使用 Background 設置初始 UI 狀態）

**Step 語義錯誤（HIGH）：**
- Given 不得含操作動詞（click、fill、navigate）
- When 每個 Scenario 最多一個主要動作
- Then 不得驗證後端資料

---

## Self-Check Checklist（生成前必查）

- [ ] 每個 PRD P0 功能至少有一個 Client .feature 檔
- [ ] 每個 PRD P0 AC 有對應的 UI Happy Path + Error Flow Scenario
- [ ] FRONTEND.md 的所有 P0 Screen 有 E2E Scenario 覆蓋
- [ ] 所有 Then 步驟只驗證 UI 可觀測狀態（無 DB / API / 業務計算驗證）
- [ ] 無 HTTP 狀態碼、SQL、API 路徑出現在 Given/When/Then
- [ ] 邊界條件使用 Scenario Outline + Examples Table
- [ ] `@smoke` 已標記核心 Critical Flow 主要路徑 Scenario
- [ ] `@ui` 已標記所有 Client BDD Scenario
- [ ] Risk Level = High 的功能（test-plan.md §9）Scenario 數量已加倍
- [ ] test-plan.md RTM 的 TC-ID 已補充至 Scenario tag（`@TC-E2E-*`）
- [ ] 跨 Screen 的核心用戶旅程（Critical User Journey）有完整 Scenario
- [ ] VRT 覆蓋核心頁面（首頁、登入頁、P0 業務頁面）
- [ ] Background 設定 clean UI 初始狀態，確保 Scenario 獨立執行
- [ ] 所有 `[UPSTREAM_CONFLICT]` 標記均已處理或說明
- [ ] 每個 .feature 檔案都輸出了 `GENERATED_FILE: features/client/{path}` 紀錄

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

> **讀取 lang_stack 方式**：`python3 -c "import json; print(json.load(open('.gendoc-state.json')).get('lang_stack','unknown'))"`

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| 所有 Feature 齊全 | PRD §User Stories 每個 Story 至少有一個對應 Feature 檔案 | 補充缺失 Feature |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | Given/When/Then 步驟使用符合 state.lang_stack 的 UI 框架術語 | 修正至一致 |
| 數值非 TBD/N/A | 等待時間、元素 id/class 等填有實際值 | 從 PDD.md 對應畫面提取 |
| UI 元素具體 | 步驟中的 UI 元素非「某按鈕」，而是具體的 id/class/label | 從 PDD §畫面設計 提取具體值 |
| Happy Path + Error | 每個 Feature 至少有 1 個 happy path Scenario 和 1 個錯誤 Scenario | 補充缺失 Scenario |
