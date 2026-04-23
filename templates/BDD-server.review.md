---
doc-type: BDD-server
target-path: features/（Server BDD Feature Files 目錄）
reviewer-roles:
  primary: "資深 BDD Expert / QA Architect（Server BDD 審查者）"
  primary-scope: "Gherkin 語法正確性、Scenario 覆蓋率、Given-When-Then 品質、業務語言清晰度"
  secondary: "資深 Backend Engineer"
  secondary-scope: "Step Definition 可實作性、API 對齊、資料庫操作合理性"
  tertiary: "資深 QA Expert"
  tertiary-scope: "Edge Case 覆蓋、錯誤路徑、邊界條件、Tag 策略"
quality-bar: "任何後端工程師拿到 BDD feature files，能直接實作 Step Definitions，所有 API P0 endpoints 都有對應的 BDD scenarios。"
upstream-alignment:
  - field: API P0 Endpoints
    source: API.md §2 Endpoints
    check: BDD scenarios 必須覆蓋所有 P0 Endpoints（至少 Happy Path + 一個 Error Path）
  - field: PRD P0 User Stories
    source: PRD.md §User Story 清單
    check: 每個 PRD P0 US 是否有對應的 Feature Scenario（至少一個 Happy Path scenario）
  - field: test-plan BDD 策略
    source: docs/test-plan.md §11 E2E Test Plan
    check: BDD scenario 範圍與 test-plan 中定義的 E2E 覆蓋策略一致
---

# BDD-server Review Items

本檔案定義 `features/`（Server BDD Feature Files 目錄）的審查標準。由 `/reviewdoc BDD-server` 讀取並遵循。
審查角色：三角聯合審查（資深 BDD Expert / QA Architect + 資深 Backend Engineer + 資深 QA Expert）
審查標準：「假設公司聘請一位 15 年 BDD 資深顧問，以最嚴格的業界標準進行 Server BDD Feature Files 驗收審查。」

---

## Review Items

### Layer 1: Gherkin 語法品質（由 BDD Expert 主審，共 5 項）

#### [CRITICAL] 1 — Scenario 缺少 @TC-ID tag
**Check**: 每個 Scenario 是否有 `@TC-E2E-{MODULE}-{SEQ}-{CASE}` 格式的 tag？tag 必須與 test-plan RTM 的 TC-ID 完全對應（大小寫、分隔符號一致）。逐一掃描所有 .feature 檔案的每個 Scenario，列出缺失 tag 的 Scenario 名稱及所在檔案行號。
**Risk**: 缺少 @TC-ID tag，BDD 測試報告無法與 RTM 追溯對應，CI 無法自動驗證 TC 覆蓋率，測試管理工具（Xray、Zephyr）無法同步狀態。
**Fix**: 為每個缺少 tag 的 Scenario 補充對應的 @TC-E2E-{MODULE}-{SEQ}-{CASE} tag，tag 值必須與 test-plan RTM 完全一致。

#### [HIGH] 2 — Given/When/Then 語義錯誤
**Check**: Given/When/Then 是否語義正確？Given = 前置條件（描述狀態，非操作動詞）；When = 觸發動作（每個 Scenario 只有一個 When）；Then = 可驗證的結果（可觀察的輸出或狀態變化）。逐一審查每個 Step，列出 Given 中含操作動詞（click、submit、call、send）、或 When 含多個操作、或 Then 只有「系統不報錯」等無意義結果的 Scenario。
**Risk**: Gherkin 語義錯誤，Step Definitions 難以對應業務意圖，維護者修改 Step 時容易引入錯誤，非技術人員無法理解測試意圖，BDD 失去活文件價值。
**Fix**: 重寫語義不清的 Step：Given 改為描述前置狀態（「系統中已存在…」「用戶已具備…」），When 確保每個 Scenario 只有一個觸發動作，Then 描述可觀察的業務結果（「回應應包含…」「資料庫應更新…」）。

#### [HIGH] 3 — Step 過度技術化
**Check**: Step Description 是否包含技術細節（SQL 查詢語法、HTTP status code 數字、JSON path 表達式、DB Table 名稱、內部方法呼叫名稱）？BDD Steps 應描述業務行為而非技術實作。逐一列出含技術細節的 Step 及所在檔案行號。
**Risk**: 技術化 Step 讓非技術利害關係人無法閱讀驗收情境，BDD 失去活文件價值；技術細節暴露也使 Step 與實作緊耦合，重構時大量 Step 需要同步修改。
**Fix**: 將技術化 Step 改寫為業務語言（「訂單狀態應變更為已付款」取代「HTTP 200 且 DB orders.status = 'paid'」）；技術細節移至 Step Definitions 中實作。

#### [HIGH] 4 — Scenario 原子性違規（每個 Scenario 只測一件事）
**Check**: 每個 Scenario 是否只驗證一個業務行為？逐一審查 Then 步驟數量，若單個 Scenario 的 Then 步驟超過 3 個且涵蓋多個不相關的業務結果（如同時驗證「訂單建立」和「通知發送」和「庫存扣減」），視為違規；列出 Then 步驟 ≥ 4 且跨多個業務關注點的 Scenario。
**Risk**: Scenario 測試多件事，When 觸發後任一 Then 失敗時，無法快速定位是哪個業務行為出問題，Debug 效率降低；也讓 Scenario 命名無法精確描述測試意圖。
**Fix**: 將複合 Scenario 拆分為多個聚焦的 Scenario，每個 Scenario 的 Then 只驗證一個核心業務結果，並更新 @TC-ID tag。

#### [MEDIUM] 5 — Background 濫用
**Check**: Background 中是否包含非所有 Scenario 都需要的步驟（如特定角色的身份設定、特定資料的前置條件）？逐一核對 Background 中的每個 Step，確認是否真正被所有 Scenario 共用，列出只被部分 Scenario 需要的 Background Steps。
**Risk**: Background 包含非共用步驟，部分 Scenario 因不必要的前置條件增加執行時間，且讀者難以理解某 Scenario 究竟需要哪些前置條件，降低可讀性。
**Fix**: 將非共用的前置條件從 Background 移到各自需要的 Scenario 的 Given 步驟中；Background 只保留真正所有 Scenario 都需要的最小前置條件集合。

---

### Layer 2: Scenario 覆蓋率（由 QA Architect + QA Expert 聯合審查，共 5 項）

#### [CRITICAL] 6 — PRD P0 US 無對應 Feature
**Check**: 每個 PRD P0 User Story 是否至少有一個 Feature 對應（含至少一個 Happy Path Scenario）？逐一核對 PRD §User Story 清單與 features/*.feature 的 Feature 標題和 Scenario 描述，列出無對應 Feature 的 US-ID 及 PRD 章節位置。
**Risk**: PRD P0 US 無 Feature 覆蓋，核心業務驗收情境未被 BDD 描述，PRD AC 的驗收依賴手動測試，無法自動化驗證 P0 功能是否正常運作。
**Fix**: 為每個缺漏的 PRD P0 US 補充對應的 .feature 檔案（含 Feature 說明、至少一個 Happy Path Scenario 和對應的 @TC-ID tag）。

#### [CRITICAL] 7 — P0 API Endpoint 無 BDD Scenario 覆蓋
**Check**: API.md 中所有 P0 API Endpoints 是否在 features/ 中有對應的 Scenario（至少 Happy Path + 一個 Error Path）？逐一對比 API.md §2 P0 Endpoints（Method + Path）與 features/*.feature 的 When 步驟，列出無 Scenario 覆蓋的 Endpoint。
**Risk**: P0 API Endpoints 無 BDD Scenario，API 合約的驗收依賴 Integration Test 而非業務語言描述，PRD/API 與測試之間的可追溯性斷裂。
**Fix**: 為每個缺少 Scenario 的 P0 Endpoint 建立對應的 Feature 和至少兩個 Scenario（Happy Path + 一個 Error Path）。

#### [HIGH] 8 — Error/Boundary Scenario 缺失
**Check**: 每個 Feature 是否有至少一個 Error Scenario（API 回應非 200、業務規則違反）和一個 Boundary Scenario（邊界值輸入、空輸入、最大長度輸入）？逐一核對每個 Feature 的 Scenario 清單，列出只有 Happy Path 的 Feature 名稱及所在檔案。
**Risk**: 只有 Happy Path 的 BDD，無法驗證系統在錯誤情境和邊界條件下的行為，Error Handling 和 Input Validation 邏輯無法通過 BDD 驗收，上線後容易出現未預期的 500 錯誤。
**Fix**: 為每個缺少 Error/Boundary Scenario 的 Feature 補充至少一個 Error Scenario 和一個 Boundary Scenario，並更新 RTM。

#### [HIGH] 9 — Scenario Outline 使用缺失
**Check**: 若有多個 Scenario 只有輸入值不同（Step 描述相同，僅數值或狀態值差異），是否使用 `Scenario Outline + Examples` 表格？逐一識別重複的 Step 描述（差異只在數值），列出應改用 Scenario Outline 的 Scenario 組及所在檔案。
**Risk**: 重複的 Scenario（差異只在數值）增加維護成本：修改 Step 描述時需同時修改多個 Scenario；也讓 .feature 檔案冗長，降低可讀性。
**Fix**: 將重複的 Scenario 合併為 `Scenario Outline + Examples` 表格格式，每個輸入組合一行 Examples 記錄，並保留各自的 @TC-ID tag（在 Examples 表格中加列 tc_id）。

#### [MEDIUM] 10 — RTM TC-ID 全覆蓋落差
**Check**: test-plan RTM 中所有 `TC-E2E-*` TC-ID 是否都出現在 features/*.feature 的 @tag 中？逐一對比 RTM 的 TC-E2E 清單與所有 .feature 檔案的 @tag，列出 RTM 有但 features/ 缺少的 TC-ID。
**Risk**: RTM TC-ID 在 features/ 中找不到對應 @tag，表示 RTM 規劃的測試案例尚未被 BDD 實作，覆蓋率統計虛高（RTM 顯示已規劃但實際無 BDD Scenario）。
**Fix**: 為每個在 RTM 有但 features/ 缺少的 TC-E2E ID 補充對應的 Scenario（含 @tag），或在 RTM 中說明該 TC 改為其他方式覆蓋。

---

### Layer 3: Scenario 品質（由 Backend Engineer + QA Expert 聯合審查，共 5 項）

#### [HIGH] 11 — 非同步操作缺少等待步驟
**Check**: 若業務流程有非同步操作（Email 發送、Background Job、Event 消費、Webhook 回調），Scenario 是否有對應的等待/驗證步驟（如「Then 系統應在 5 秒內發送確認郵件」「And 訂單處理 Job 應在背景完成」）？逐一識別含非同步操作的 Scenario，列出缺少等待步驟的情況。
**Risk**: 非同步操作無等待步驟，測試執行時非同步任務尚未完成即進行 Then 驗證，導致 Flaky Test（有時通過有時失敗），CI 結果不可信。
**Fix**: 為每個非同步操作的 Scenario 補充等待步驟（含超時時間），並在 Step Definitions 中實作輪詢或事件等待邏輯（建議：polling with timeout，而非 sleep）。

#### [HIGH] 12 — WebSocket Scenario 缺失（若適用）
**Check**: 若 EDD/ARCH 設計包含 WebSocket 功能，是否有 `@websocket` tag 的 Scenario 覆蓋 WebSocket 連線建立、訊息發送/接收、斷線重連、心跳機制情境？逐一核對 EDD/ARCH WebSocket 功能點與 features/ 的 @websocket Scenario 清單。
**Risk**: WebSocket Scenario 缺失，WebSocket 相關功能（即時推播、雙向通訊）無 BDD 驗收情境，生產環境 WebSocket 問題無法在測試階段發現。
**Fix**: 為每個 EDD/ARCH WebSocket 功能點補充對應的 Scenario（含 @websocket tag），覆蓋連線 / 訊息 / 斷線三種基本情境。

#### [HIGH] 13 — .feature 檔案命名不一致
**Check**: feature 檔案命名是否遵循統一規範（統一使用 `{module}.feature` 或 `{us-id}-{description}.feature`，全部小寫、使用連字號分隔）？逐一掃描 features/ 目錄下所有 .feature 檔案名稱，列出不符合命名規範的檔案。
**Risk**: 命名規則混用（部分用 `Auth.feature`、部分用 `US-001-user-login.feature`），工程師無法快速定位特定功能的 .feature 檔案，也難以自動化批次處理。
**Fix**: 選定統一命名規範並重命名所有違規 .feature 檔案；在 test-plan 中補充命名規範說明。

#### [MEDIUM] 14 — Feature 文件說明缺失或純技術描述
**Check**: 每個 .feature 檔案是否有 `Feature:` 說明行（一句話業務目的描述，非技術描述）？逐一掃描所有 .feature 檔案的 `Feature:` 行，列出只有技術描述（「測試 UserController」）而無業務說明（「用戶透過電子郵件和密碼登入系統以存取個人資料」）的檔案。
**Risk**: Feature 說明缺失或只有技術描述，.feature 檔案無法作為活文件（Living Documentation）向非技術利害關係人傳達業務意圖。
**Fix**: 為每個缺少業務說明的 .feature 補充 Feature 描述行，以業務語言描述此功能的用戶價值（誰、做什麼、為什麼）。

#### [MEDIUM] 15 — Step 定義語義重複
**Check**: 是否有語義相同但文字不同的 Step（如「使用者登入」vs「用戶已登入」vs「登入成功」）？逐一審查所有 .feature 檔案的 Step，識別語義重複但文字不同的 Step 組合，列出重複的 Step 及所在檔案。
**Risk**: Step 語義重複，Step Definitions 需要維護多個相同功能的定義，修改時容易遺漏部分版本，導致不一致的測試行為和重複的維護工作。
**Fix**: 統一語義重複的 Step 描述，選定一個標準化版本並在所有 .feature 檔案中一致使用，刪除多餘的 Step Definitions。

---

### Layer 4: Tag 策略與組織（由 QA Expert 主審，共 3 項）

#### [HIGH] 16 — @smoke tag 範圍過大
**Check**: `@smoke` tag 的 Scenario 數量是否合理（建議 ≤ 20 個，執行時間 ≤ 5 分鐘）？是否有明確的 Smoke Test 選取標準（如「P0 功能 Happy Path」）？逐一統計 @smoke Scenario 數量，列出若超過 20 個的情況。
**Risk**: @smoke 標記過多的 Scenario，Smoke Test 執行時間超出快速驗證的意義（5 分鐘），導致部署後快速反饋失效，或工程師為節省時間而跳過 Smoke Test。
**Fix**: 定義 @smoke 選取標準（如「每個 P0 功能的一個 Happy Path Scenario」），將 @smoke 數量控制在 ≤ 20 個，超出的改為 @regression。

#### [MEDIUM] 17 — @regression / @critical Tag 策略不一致
**Check**: 除 @TC-ID 和 @smoke 之外的 tag（@regression、@critical、@auth、@payment 等業務域 tag）是否有一致的使用策略說明？是否有 tag 被濫用（如 @critical 標記了全部 Scenario）？逐一審查所有 @tag 的使用情況，識別無策略或定義不明的 tag。
**Risk**: 無策略的 tag 導致 CI `--tag=@critical` 執行超出預期數量，tag 失去篩選功能，也讓 tag 的語意對新加入工程師不明確。
**Fix**: 定義 tag 使用策略文件（說明每個 tag 的選取標準、預期數量上限），並依策略修正現有 tag 的使用。

#### [LOW] 18 — Step Definitions 骨架缺失
**Check**: 是否有對應的 Step Definitions 骨架檔案（.steps.ts / .steps.py / .steps.go / .steps.java）對應每個 .feature 檔案？骨架檔案需包含所有 Step 的函式簽名（可以是空實作，但函式必須存在且 Step 正則表達式對應）。逐一核對每個 .feature 是否有對應的 .steps 骨架檔案。
**Risk**: 無 Step Definitions 骨架，BDD 框架執行時所有 Step 顯示 undefined/pending 狀態，工程師需從零開始撰寫 Step Definitions，增加實作成本且容易遺漏 Step。
**Fix**: 為每個 .feature 檔案生成對應的 Step Definitions 骨架（使用 BDD 框架的 `--dry-run --format snippets` 自動生成），確保所有 Step 有對應的函式簽名。

---

### Layer 5: 上游對齊（由 QA Architect 通盤審查，共 2 項）

#### [HIGH] 19 — SCHEMA 資料持久化 Scenario 缺失
**Check**: 對於會修改資料庫狀態的 P0 API（POST / PUT / DELETE），是否有 Scenario 驗證資料持久化結果（「Then 系統中應存在一筆 X 記錄，包含 Y 欄位」）？逐一核對 SCHEMA.md 的關鍵實體與對應的寫入操作 Scenario，列出缺少持久化驗證的 Scenario。
**Risk**: 寫入操作的 Scenario 只驗證 API 回應而不驗證持久化，DB 寫入邏輯的 Bug（如部分欄位未寫入、事務未提交）無法被 BDD 驗收。
**Fix**: 為每個 P0 寫入操作的 Scenario 補充持久化驗證的 Then 步驟（以業務語言描述，技術細節在 Step Definitions 實作）。

#### [LOW] 20 — 裸 Placeholder
**Check**: 是否有 `{{PLACEHOLDER}}` 格式未替換（Module 名稱、TC-ID 範例、Step 描述範例、測試資料值）？逐一掃描所有 .feature 檔案，列出所有裸 placeholder 及其所在檔案和行號。
**Risk**: 裸 placeholder 的 Scenario 或 Step 描述讓 BDD 框架無法正確解析，導致 Step 匹配失敗或 Scenario 名稱顯示模板字符串。
**Fix**: 替換所有裸 placeholder 為真實的 Module 名稱、TC-ID 或 Step 描述；若暫時無法確定，加上 `# TODO: 待填入` 注釋說明。
