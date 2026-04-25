---
doc-type: BDD-server
output-path: features/（多個 .feature 檔案）
output-glob: features/*.feature
multi-file: true
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/EDD.md
  - docs/ARCH.md
  - docs/API.md
  - docs/SCHEMA.md
  - docs/test-plan.md
quality-bar: "所有 PRD P0 AC 有對應 Server BDD Scenario（正常路徑 + 錯誤路徑）；所有 API Endpoint 有 @contract Scenario；6 個 HTTP 錯誤碼（401/403/404/409/422/429）有對應 Error Scenario；無 UI 操作或前端細節滲入 Step；無假斷言（Then 必須具體且可測試）"
gen-expert: "資深 Backend QA Architect（10 年以上 BDD + API Contract Testing 經驗）"
---

# BDD-server.gen.md — Server BDD Feature Files 生成規則

依 PRD 每個驗收標準（AC）、API.md 每個 Endpoint，自動生成完整的 Server BDD Feature Files（Gherkin 格式）。
輸出目錄：`features/`（每個 PRD 功能 → 一個 .feature 檔案）。

**職責邊界（與 BDD-client 區分）：**
- Server BDD = API 層行為、業務邏輯、資料持久化、認證授權、Contract Testing
- 禁止包含 UI 操作、畫面跳轉、元件顯示等前端行為（那是 BDD-client 的責任）

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
| `IDEA.md`（若存在）| 全文 | 了解產品願景，BDD 業務語言需反映 IDEA 業務概念 |
| `BRD.md` | 業務目標、驗收標準 | Feature 標題的業務語意來自 BRD |
| `PRD.md` | 所有功能 AC | **主要輸入**：每個 AC → 至少 1 正常路徑 + 1 錯誤路徑 Scenario |
| `EDD.md` | §4 Security、§5 BDD 設計、§3 lang_stack | 確認認證流程（JWT/OAuth）和已規劃的 Scenario 結構 |
| `ARCH.md` | §3 元件架構 | 確認 Contract Testing 的 Provider/Consumer 邊界 |
| `API.md` | 所有 Endpoint、Request/Response | **@contract tag**：每個 API Endpoint 必須有對應 BDD Scenario |
| `SCHEMA.md` | 資料模型 | Background 的資料初始化步驟（Given 的 clean state 設計）|
| `test-plan.md` | §3.3 E2E/BDD、§9 Risk Matrix | Smoke 標記（Risk=High 的功能 Scenario 數量加倍）|

若某文件不存在，靜默跳過，依既有流程繼續。

### test-plan.md 特別讀取規則

若 `docs/test-plan.md` 存在，額外讀取：
- **§3.3 E2E / BDD Tests**：確認 BDD 工具（Cucumber/Behave/Godog 等）、Critical User Flow 清單
  → 清單中標記為 `Smoke: Y` 的 Flow 必須生成 `@smoke` tag Scenario
- **§9 Risk-Based Testing Matrix**：Risk Level = High 的功能，Scenario 數量加倍（至少 2× 正常 + 2× 錯誤 + 1× 邊界）
- **§15 RTM（若存在 TC-ID）**：生成的 Scenario tag 補充對應 TC-ID（格式：`@TC-E2E-{MODULE}-{SEQ}-{CASE}`）

### IDEA.md Appendix C 素材讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與 BDD 相關的檔案。
結合 Appendix C「應用於」欄位標有「BDD §」的段落，作為生成 Scenario 的補充依據。
若無引用，靜默跳過。

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- PRD 的 AC vs API.md 的 Endpoint（是否有 AC 無對應 API）
- EDD §5 的 BDD 設計 vs PRD 的 AC（是否有 Scenario 設計但無對應 AC）

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並說明影響的 Scenario 範圍。

---

## 多檔案生成規則

**一個 PRD 功能 → 一個 .feature 檔案**，輸出到 `features/` 目錄。

命名規則：
```
features/{domain}/{resource}_{action}.feature
```

範例：
| PRD 功能 | Domain | 輸出路徑 |
|---------|--------|---------|
| 使用者登入 | auth | `features/auth/user_login.feature` |
| 使用者註冊 | auth | `features/auth/user_registration.feature` |
| 訂單建立 | orders | `features/orders/order_create.feature` |
| 訂單查詢 | orders | `features/orders/order_list.feature` |
| 商品搜尋 | catalog | `features/catalog/product_search.feature` |

**[AI 指令]** 生成每個 .feature 檔案時，使用 Write 工具逐一寫入，並輸出：
```
GENERATED_FILE: features/{domain}/{name}.feature
```
最後彙總所有生成的檔案清單。

---

## Gherkin 格式規範

### 標準結構

```gherkin
# features/<domain>/<resource>_<action>.feature
# 來源：PRD §<功能名稱>，AC-1～AC-N

Feature: <功能名稱（與 PRD 一致）>
  作為 <角色>
  我希望 <功能>
  以便 <目的>

  Background:
    Given 資料庫已初始化（clean state）
    And <必要的測試資料>

  # ─── 正常路徑 ───────────────────────────────────────────
  @p0 @smoke @contract @TC-{MODULE}-{SEQ}-001
  Scenario: <正常路徑描述（業務語言）>
    Given <系統初始狀態（非操作動詞）>
    When <使用者或系統執行的單一動作>
    Then <可觀測的業務結果（具體、可測試）>
    And <補充斷言>

  # ─── 錯誤路徑 ───────────────────────────────────────────
  @p0 @regression @TC-{MODULE}-{SEQ}-002
  Scenario: <錯誤路徑描述>
    Given <初始狀態>
    When <觸發錯誤的動作>
    Then <預期的錯誤回應（含具體錯誤碼 / 訊息）>

  # ─── 邊界條件 ───────────────────────────────────────────
  @p0 @regression @TC-{MODULE}-{SEQ}-003
  Scenario Outline: <邊界條件描述>
    Given <初始狀態>
    When <使用者輸入 "<input_value>">
    Then <預期結果是 "<expected_result>">

    Examples:
      | input_value | expected_result |
      | ""          | 錯誤：必填欄位  |
      | "invalid"   | 錯誤：格式不合  |
```

### Step 語義規範

| Step | 規範 | 反面範例（禁止）|
|------|------|----------------|
| Given | 描述**狀態**，非操作動詞 | `Given 呼叫了 POST /users` |
| When | 每個 Scenario **只有一個 When** | `When 先呼叫 A，再呼叫 B` |
| Then | **可觀測的業務結果**（具體值）| `Then 程式沒有報錯` |

---

## Scenario 數量規則

**基本規則（每個 AC）：**
- 至少 1 個正常路徑 Scenario
- 至少 1 個錯誤路徑 Scenario
- 有邊界條件時使用 Scenario Outline + Examples Table

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
| `@smoke` | 核心主要路徑 Scenario | Critical Flow Happy Path |
| `@regression` | 完整回歸測試 Scenario | 所有 Scenario 均標記 |
| `@api` | API 層測試 Scenario | 後端 API Scenario |
| `@contract` | API 契約測試 | 每個 API Endpoint 必須有一個 |
| `@TC-E2E-{MODULE}-{SEQ}-{CASE}` | RTM 追溯 tag | 與 test-plan RTM 完全一致 |

---

## Error Scenario Catalog（必備 6 個 HTTP 錯誤碼）

每個 Feature 必須涵蓋以下 HTTP 錯誤碼的 Scenario：

| HTTP 碼 | 場景 | 必備 Scenario |
|---------|------|--------------|
| 401 | 未認證 | Token 無效或過期時拒絕存取 |
| 403 | 無權限 | 角色不符時拒絕操作 |
| 404 | 資源不存在 | 操作不存在的資源 |
| 409 | 衝突 | 建立重複資源 |
| 422 | 業務規則違反 | 違反業務邏輯（含具體說明）|
| 429 | Rate Limit | 超過速率限制 |

---

## Contract Testing 規則

- API.md 中每個 Endpoint 必須有至少一個 `@contract` tagged Scenario
- `@contract` Scenario 的 Then 步驟必須驗證具體的 HTTP 狀態碼和回應結構
- Contract Testing 追溯矩陣需建立（BDD Scenario → API Endpoint → HTTP Method → 回應碼）

---

## Test Data Management 規則

- 使用 Factory 動態建立 Test Data（禁止 hardcode 真實 PII）
- AfterScenario / Background 清理機制確保 clean state
- 測試帳號使用 `@example.com` 或 `@test.internal` 網域
- 禁止：測試 Scenario 依賴其他 Scenario 的資料殘留
- 禁止：直接使用生產環境帳號

---

## 禁止模式（Anti-patterns）

**技術語言滲入（CRITICAL）：**
- 禁止在 Given/When/Then 出現 SQL 語法、class 名稱
- 除 `@contract` Scenario 外，不暴露 HTTP 狀態碼數字（用業務語言描述）

**假斷言（CRITICAL）：**
- 禁止 Then 步驟為空或僅含 `# TODO`
- 禁止 `Then 程式沒有報錯`（過於模糊）

**前端邏輯滲入（HIGH）：**
- 禁止在 Server BDD 中描述 UI 元素（按鈕、頁面跳轉、視覺狀態）
- 所有 UI 層驗收場景由 BDD-client 負責

**隔離性破壞（HIGH）：**
- 禁止 Scenario 依賴其他 Scenario 的執行順序
- 每個 Scenario 必須能獨立執行

---

## Self-Check Checklist（生成前必查）

- [ ] 每個 PRD P0 功能至少有一個 .feature 檔
- [ ] 每個 PRD AC 至少有一個 Scenario（正常路徑 + 錯誤路徑）
- [ ] 邊界條件使用 Scenario Outline + Examples Table
- [ ] 所有 Then 斷言具體且可測試（無模糊語言）
- [ ] 無 UI 操作或前端細節滲入 Step（頁面跳轉、按鈕點擊等）
- [ ] 所有 API.md Endpoint 有對應的 `@contract` tagged Scenario
- [ ] Contract Testing 追溯矩陣已建立
- [ ] 6 個 HTTP 錯誤碼（401/403/404/409/422/429）均有對應的 Error Scenario
- [ ] `@smoke` 已標記核心 Critical Flow 主要路徑 Scenario
- [ ] Risk Level = High 的功能（test-plan.md §9）Scenario 數量已加倍
- [ ] test-plan.md RTM 的 TC-ID 已補充至對應 Scenario tag（`@TC-E2E-*`）
- [ ] Background 清理機制確保 clean state
- [ ] Test Data 使用 Factory 動態建立，禁止 hardcode 真實 PII
- [ ] 所有 `[UPSTREAM_CONFLICT]` 標記均已處理或說明
- [ ] 每個 .feature 檔案都輸出了 `GENERATED_FILE: features/{path}` 紀錄

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| API 覆蓋率 | API.md 每個 endpoint 至少有一個對應 Scenario | 補充缺失 Scenario |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | HTTP 方法、路徑、Content-Type 與 API.md 定義一致 | 以 API.md 為準修正 |
| 數值非 TBD/N/A | 回應碼、Payload 欄位填有實際值 | 從 API.md 對應定義填入 |
| 測試資料真實 | 請求體範例非 "string" / 1 / true，使用符合業務語義的真實格式 | 替換為業務語義資料 |
| 錯誤路徑覆蓋 | 每個 endpoint 至少有 1 個錯誤 Scenario（4XX/5XX） | 補充錯誤 Scenario |
