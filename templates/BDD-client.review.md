---
doc-type: BDD-client
target-path: features/client/（Client BDD Feature Files 目錄）
reviewer-roles:
  primary: "資深 Frontend QA Expert（Client BDD 審查者）"
  primary-scope: "Client-side test coverage、E2E flow completeness、visual regression、cross-platform testing"
  secondary: "資深 Frontend Engineer"
  secondary-scope: "Playwright/Jest 實作可行性、Component test quality、Mock strategy"
  tertiary: "資深 UX Expert"
  tertiary-scope: "User journey coverage、accessibility testing、responsive testing"
quality-bar: "QA 工程師拿到 Client BDD files，能直接跑 E2E 測試，覆蓋所有 P0 Screen Flows，且 Playwright/Jest 命令可直接執行。"
upstream-alignment:
  - field: FRONTEND Screen 清單
    source: docs/FRONTEND.md §4 Screen 清單
    check: E2E scenarios 覆蓋所有 P0 Screens（至少 Happy Path + 一個 Error Flow）
  - field: PRD P0 User Stories
    source: PRD.md §User Story 清單
    check: Client scenarios 對應每個 PRD P0 US 的驗收標準（AC）
  - field: test-plan E2E 策略
    source: docs/test-plan.md §11 E2E Test Plan
    check: Client BDD 的執行方式和覆蓋範圍與 test-plan §11 一致
---

# BDD-client Review Items

本檔案定義 `features/client/`（Client BDD Feature Files 目錄）的審查標準。由 `/reviewdoc BDD-client` 讀取並遵循。
審查角色：三角聯合審查（資深 Frontend QA Expert + 資深 Frontend Engineer + 資深 UX Expert）
審查標準：「假設公司聘請一位 15 年前端測試資深顧問，以最嚴格的業界標準進行 Client BDD Feature Files 驗收審查。」

---

## Review Items

### Layer 1: E2E Flow 覆蓋率（由 Frontend QA Expert 主審，共 5 項）

#### [CRITICAL] 1 — PRD P0 AC 無 Client BDD Scenario
**Check**: PRD P0 功能的每條 Acceptance Criteria（AC）是否都有對應的 Client BDD Scenario（Happy Path + Error Path）？逐一核對 PRD §AC 清單與 features/client/*.feature 的 Scenario，列出缺漏的 AC 條目及其 PRD 位置（章節 + AC 編號）。
**Risk**: PRD AC 無 Scenario 覆蓋，Product Owner 定義的驗收標準無法自動化驗證，發布時無法確認產品是否達到 AC 要求，需依賴手動驗收，增加發布風險。
**Fix**: 為每個缺漏的 PRD P0 AC 補充對應的 Client BDD Scenario（含 Happy Path、至少一個 Error Scenario），並更新 test-plan RTM。

#### [CRITICAL] 2 — P0 Screen Flow 無 E2E Scenario 覆蓋
**Check**: FRONTEND.md §4 Screen 清單中所有 P0 Screen Flow（包含主要 Happy Path 和 Auth Flow）是否每個都有對應的 E2E Scenario？逐一核對 FRONTEND.md §4 Screen 清單與 features/client/*.feature，列出缺少 E2E Scenario 覆蓋的 P0 Screen Flow。
**Risk**: P0 Screen Flow 無 E2E Scenario，關鍵用戶旅程（登入流程、核心功能流程）無自動化驗收，Screen Flow 設計變更時無法自動偵測回歸問題，發布前品質無保障。
**Fix**: 為每個缺少覆蓋的 P0 Screen Flow 補充對應的 Scenario，描述用戶在各畫面之間的操作流程和視覺狀態轉換。

#### [HIGH] 3 — Client BDD 重複測試後端邏輯
**Check**: Client BDD Scenario 是否只測試 UI 行為（畫面元素顯示/隱藏、用戶操作流程、視覺狀態變化）而非後端業務邏輯（DB 資料正確性、業務計算結果、資料持久化）？逐一審查每個 Scenario 的 Then 步驟，列出含後端邏輯驗證的 Scenario（如「資料庫記錄已更新」「後端已記錄日誌」）。
**Risk**: Client BDD 與 Server BDD 職責重疊，相同的後端邏輯被重複測試，浪費測試執行時間；且 Client BDD 直接驗證後端狀態需要特殊的 DB 存取配置，增加 CI 複雜度。
**Fix**: 重寫含後端邏輯的 Then 步驟，改為驗證 UI 層的可觀察狀態（「畫面顯示成功訊息」取代「資料庫記錄已更新」）；後端邏輯驗證保留在 Server BDD（features/）。

#### [HIGH] 4 — Error Path + Empty State Scenario 缺失
**Check**: 每個 P0 Screen 是否有對應的 Error State Scenario（API 呼叫失敗 → 畫面顯示錯誤訊息）和 Empty State Scenario（無資料時顯示空狀態畫面）？逐一核對每個 P0 Screen 的 Scenario 清單，列出只有 Happy Path 的 Screen 名稱。
**Risk**: 只有 Happy Path 的 Client BDD，無法驗證錯誤狀態和空狀態下的 UI 行為，Error Handling 和 Empty State 設計出現 Bug 時無法被自動化測試捕捉。
**Fix**: 為每個缺少 Error/Empty Scenario 的 P0 Screen 補充至少一個 Error State Scenario（含錯誤訊息顯示驗證）和一個 Empty State Scenario（含空狀態畫面驗證）。

#### [MEDIUM] 5 — client_type 工具一致性
**Check**: features/client/ 的測試格式是否與 lang_stack/client_type 一致（web 類型應使用 Playwright/Cypress 格式；Cocos/Unity 類型應使用截圖比對或平台工具格式）？逐一確認 .feature 檔案的 Step 描述是否符合 client_type 的工具能力範圍（如 Playwright 無法操作 Cocos Canvas）。
**Risk**: BDD 格式與 client_type 不一致，Step Definitions 無法使用對應工具實作，導致 BDD 測試無法執行，交付工程師後需從頭重寫 Step Definitions。
**Fix**: 依 client_type 調整 .feature 檔案的 Step 描述格式，確保 Step 可以用對應工具（Playwright / Cypress / 平台工具）實作。

---

### Layer 2: Test 可執行性（由 Frontend Engineer 主審，共 4 項）

#### [CRITICAL] 6 — Step Definitions 骨架缺失（web 類型）
**Check**: 若 client_type=web，是否有 `.steps.ts`（Playwright）或 `.steps.js`（Cypress）骨架檔案對應每個 .feature 檔案？骨架檔案需包含所有 Step 的函式簽名（可為空實作，但 Step 正則表達式必須對應）。逐一核對每個 .feature 是否有對應的 .steps 骨架檔案。
**Risk**: 無 Step Definitions 骨架，Playwright/Cypress 執行時所有 Step 顯示 undefined 狀態，.feature 無法執行，交付給工程師時需從零實作所有 Step Definitions，增加實作成本。
**Fix**: 為每個 .feature 檔案生成對應的 .steps.ts/.steps.js 骨架（使用 `cucumber-js --dry-run --format snippets` 自動生成），確保所有 Step 有對應的函式簽名。

#### [HIGH] 7 — 視覺狀態驗證缺失
**Check**: Client BDD 是否驗證 UI 視覺狀態（Loading Skeleton 顯示、Error State 元素出現、Empty State 內容、Toast 通知顯示/消失、Modal 開啟/關閉）？逐一審查每個 Scenario 的 Then 步驟，列出只驗證資料而未驗證 UI 元件視覺狀態的 Scenario。
**Risk**: 只驗證資料而不驗證 UI 狀態，UI 元件的視覺反饋（Loading 動畫、Error 提示、Empty State 設計）出現 Bug 時無法被自動化測試捕捉，影響用戶體驗品質。
**Fix**: 為每個涉及非同步操作或狀態變化的 Scenario 補充 UI 視覺狀態驗證步驟（Loading → Loaded 狀態轉換、Error State 元素顯示、Empty State 內容）。

#### [HIGH] 8 — Mock 策略未定義
**Check**: features/client/ 或 Step Definitions 是否說明 API Mock 策略（使用 Playwright route interception / MSW / cy.intercept）？若 Client BDD 需要後端 API 但完全無 Mock 策略說明，且無法連接真實 Staging 環境，視為 finding。
**Risk**: 無 Mock 策略，Client BDD 在 CI 環境中因無法連接後端 API 而全部失敗，或每次執行依賴真實後端的可用性，導致 Flaky Test。
**Fix**: 補充 API Mock 策略說明（選用工具、哪些 Endpoint 需要 Mock、Mock 資料的維護位置），並在 Step Definitions 骨架中加入 Mock setup 範例。

#### [MEDIUM] 9 — Scenario 命名規範不一致
**Check**: Client BDD Scenario 命名是否一致（推薦格式：動詞 + 受詞 + 結果，如「點擊登入按鈕後顯示錯誤訊息」「輸入無效 Email 後表單顯示驗證提示」）？逐一審查所有 Scenario 名稱，列出不符合動詞 + 受詞 + 結果格式的命名。
**Risk**: Scenario 命名不一致，BDD 測試報告中的 Scenario 清單可讀性低，利害關係人難以從測試報告中理解每個測試的業務意圖。
**Fix**: 依動詞 + 受詞 + 結果格式重命名不符合規範的 Scenario，確保 Scenario 名稱清楚描述用戶操作和預期結果。

---

### Layer 3: Cross-browser + Responsive Testing（由 Frontend QA Expert + Frontend Engineer 聯合審查，共 4 項）

#### [HIGH] 10 — @responsive tag 缺失
**Check**: 涉及響應式佈局（不同螢幕尺寸顯示不同 UI 元素、欄位排列變化、導覽選單收折）的 Scenario 是否有 `@responsive` tag，且 Scenario 包含多個 Breakpoint 的驗證步驟（375px / 768px / 1440px）？逐一識別涉及響應式行為的 Scenario，列出缺少 @responsive tag 的情況及所在檔案。
**Risk**: 響應式 Scenario 無 @responsive tag，CI 無法選擇性執行跨 Breakpoint 測試，響應式 Bug（如 Mobile 版 UI 破版、導覽選單無法展開）無法被自動化捕捉。
**Fix**: 為每個涉及響應式行為的 Scenario 補充 @responsive tag，並在 Scenario 中加入多個 Breakpoint 的驗證步驟（375 / 768 / 1440 三種寬度）。

#### [HIGH] 11 — @a11y tag 缺失
**Check**: 涉及鍵盤操作（Tab 鍵導覽、Enter/Space 觸發）、屏幕閱讀器支援（aria-label、aria-describedby）、顏色對比度（WCAG 2.1 AA 標準）的 Scenario 是否有 `@a11y` tag？逐一識別涉及無障礙功能的 Scenario，列出缺少 @a11y tag 的情況。
**Risk**: 無障礙 Scenario 缺失或無 @a11y tag，WCAG 2.1 AA 合規性無法通過自動化測試驗證，可能導致法規合規風險和用戶排斥問題。
**Fix**: 為每個涉及無障礙功能的 Scenario 補充 @a11y tag，確保鍵盤導覽、ARIA 屬性、色彩對比度三個核心面向有 Scenario 覆蓋。

#### [MEDIUM] 12 — Cross-browser @safari tag 缺失
**Check**: 涉及 Safari 特定問題（iOS Safari 100vh 計算問題、autoplay 限制、position:fixed 在軟鍵盤彈出時的行為、WebGL 支援限制）的 Scenario 是否有 @safari tag，並在 Step 中說明是 Browser-specific 的驗證情境？逐一識別含 cross-browser 行為差異的 Scenario。
**Risk**: Safari 特定問題的 Scenario 無 @safari tag，無法選擇性在 Safari 環境執行，導致 Safari Bug（100vh 破版、autoplay 被阻擋）無法被針對性測試，上線後才發現。
**Fix**: 為每個 Safari-specific 的 Scenario 補充 @safari tag，並在 Step Definitions 中使用 Browser Context 過濾確保只在 Safari 環境執行對應驗證。

#### [MEDIUM] 13 — @performance tag 缺失
**Check**: 涉及頁面效能（首屏載入時間、LCP 驗收、Core Web Vitals 目標）的 Scenario 是否有 `@performance` tag？逐一識別含效能驗收標準的 Scenario（如「頁面應在 2 秒內完成載入」），列出缺少 @performance tag 的情況。
**Risk**: 效能 Scenario 無 @performance tag，CI 無法選擇性執行效能測試（效能測試通常需要獨立環境和較長執行時間），導致效能測試被跳過或影響其他測試的執行時間。
**Fix**: 為每個涉及效能目標的 Scenario 補充 @performance tag，並確認 Scenario 的效能目標數字與 EDD §10.5 SLO 和 test-plan §13 一致。

---

### Layer 4: 上游對齊（由 Frontend QA Expert 通盤審查，共 4 項）

#### [HIGH] 14 — test-plan E2E 策略與 Client BDD 不一致
**Check**: test-plan.md §11 E2E Test Plan 中定義的 E2E 覆蓋清單（列舉的 P0 Screen Flow）是否都有對應的 Client BDD Scenario？逐一對比 test-plan §11 的 E2E 條目與 features/client/ 的 Scenario 清單，列出 test-plan 有但 features/client/ 缺少的項目。
**Risk**: test-plan 與 Client BDD 不一致，表示計劃的 E2E 覆蓋未被實作，QA Lead 看到的覆蓋率數字不反映真實狀態。
**Fix**: 依 test-plan §11 的 E2E 清單補充缺少的 Client BDD Scenario，或在 test-plan 中更新說明改變的覆蓋策略。

#### [HIGH] 15 — features/client/ 目錄結構混亂
**Check**: 是否按 Screen 或 Feature 分子目錄（如 `features/client/auth/`、`features/client/home/`），而非所有 .feature 檔案平鋪在 `features/client/` 同一目錄？逐一確認目錄結構是否反映 FRONTEND.md §4 的 Screen 層級。
**Risk**: 所有 .feature 平鋪在同一目錄，隨 Screen 數量增加難以管理，也無法利用目錄結構快速定位特定 Screen 的測試，CI 無法按 Screen 粒度選擇性執行測試。
**Fix**: 依 FRONTEND.md §4 的 Screen 分類，將 .feature 檔案移至對應的子目錄（`features/client/{screen-name}/`）；每個子目錄應有一個對應的 README 說明該目錄的測試範圍。

#### [MEDIUM] 16 — @mobile tag 濫用
**Check**: `@mobile` tag 的 Scenario 是否只在需要 Touch 行為（Swipe、Pinch-to-zoom、Long Press）或 Mobile-specific 互動（iOS Safari 100vh 問題、底部導覽列）時使用？是否有大量非 Mobile-specific 的 Scenario 被標記 @mobile（如純文字顯示的 Scenario）？
**Risk**: 濫用 @mobile tag 導致 CI 執行 Mobile 模式測試時運行大量不必要的 Scenario，增加 CI 時間；也讓 @mobile 失去識別真正 Mobile-specific 問題的意義。
**Fix**: 審查所有 @mobile tag 的 Scenario，移除非 Mobile-specific 的 @mobile tag，只在 Touch 行為或 Mobile-specific 互動的 Scenario 保留 @mobile tag。

#### [LOW] 17 — 裸 Placeholder
**Check**: 是否有 `{{PLACEHOLDER}}` 格式未替換（Screen 名稱、AC 描述、元件選擇器、測試資料值、URL 路徑等）？逐一掃描所有 .feature 檔案，列出所有裸 placeholder 及其所在檔案和行號。
**Risk**: 裸 placeholder 的 Scenario 或 Step 描述讓 Playwright/Cypress 的 Step 匹配失敗，或顯示模板字符串而非真實業務描述，測試無法執行。
**Fix**: 替換所有裸 placeholder 為真實的 Screen 名稱、AC 描述或測試資料值；若暫時無法確定，加上 `# TODO: 待填入` 注釋說明。

---

### Layer 5: Gherkin 語法品質（由 Frontend QA Expert 主審，共 2 項）

#### [HIGH] 18 — Given/When/Then Client 語義錯誤
**Check**: Client BDD 的 Given/When/Then 是否正確對應 UI 行為語義？Given = UI 初始狀態（「畫面顯示登入表單」「用戶已在首頁」）；When = 用戶操作（「用戶點擊提交按鈕」「用戶輸入無效 Email」）；Then = 可觀察的 UI 結果（「表單顯示驗證錯誤訊息」「畫面跳轉至首頁」）。逐一列出 UI 語義不正確的 Step 及所在檔案。
**Risk**: Client BDD Step 語義錯誤，Step Definitions 難以用 Playwright/Cypress 實作對應的 UI 互動，維護者在實作時需要猜測業務意圖，增加實作錯誤風險。
**Fix**: 重寫語義不清的 Client Step：Given 描述 UI 初始狀態，When 描述具體的用戶互動操作（點擊、輸入、滑動），Then 描述可觀察的 UI 狀態變化或畫面跳轉。
