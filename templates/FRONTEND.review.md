---
doc-type: FRONTEND
target-path: docs/FRONTEND.md
reviewer-roles:
  primary: "Frontend Expert（資深前端架構師，精通 Cocos Creator / HTML5 / Unity WebGL / React / Vue）"
  primary-scope: "技術選型合理性、畫面流程完整性、API 整合正確性、跨平台相容性、效能預算、測試策略覆蓋"
  secondary: "UX Expert（資深 UX Designer）"
  secondary-scope: "§4 畫面清單完整性、Navigation Map 合理性、§5 組件層次、§8 自適應策略、Loading/Empty/Error 狀態覆蓋"
  tertiary: "QA Expert（資深 QA Engineer）"
  tertiary-scope: "§10 測試策略完整性、E2E 流程覆蓋、Visual Regression 設定、Cross-browser 覆蓋、§12 安全性"
quality-bar: "資深前端架構師能直接依此文件開始 Sprint 1，不需再問任何技術決策問題。"
pass-conditions:
  - "CRITICAL 數量 = 0"
  - "Self-Check：template 所有 ## 章節（≥18 個）均存在且有實質內容"
  - "§7.2 狀態管理三條 Iron Rule 均已完整實作（Zustand 型別 + queryKey 工廠 + Token 存儲策略）"
upstream-alignment:
  - field: Breakpoint 數值
    source: PDD Design Token
    check: §8.1 CSS 變數是否與 PDD Design Token 完全一致（若 PDD 存在）
  - field: API Endpoint 清單
    source: API.md §2
    check: §6.1 矩陣是否覆蓋 API.md 所有 P0 Endpoint
  - field: Auth Token 策略
    source: EDD §4 安全設計
    check: §6.2 Token 儲存方式是否與 EDD §4 一致
  - field: PRD User Stories
    source: PRD.md
    check: §4.1 是否每個 PRD P0 功能都有對應 Screen
  - field: 目標平台
    source: BRD.md
    check: §3.1 是否每個 BRD 目標平台都出現在支援矩陣
  - field: Core Web Vitals 目標
    source: EDD §10.5（若存在）
    check: §11.2 效能目標是否與 EDD SLO 一致
---

# FRONTEND Review Items

本檔案定義 `docs/FRONTEND.md` 的審查標準。由 `/reviewdoc FRONTEND` 讀取並遵循。
審查角色：三角聯合審查（Frontend Expert + UX Expert + QA Expert）
審查標準：「假設公司聘請一位 10 年以上資深前端架構師，以交付可直接實作的工程設計文件為標準進行驗收。」

---

## Review Items

### Layer 1: 技術選型完整性（由 Frontend Expert 主審，共 5 項）

#### [CRITICAL] 1 — §2.1 Framework Selection 存在裸 Placeholder
**Check**: §2.1 Framework Selection 表格中是否有任何 `{{PLACEHOLDER}}` 格式的未替換值？核心框架、語言、建構工具、套件管理的版本和選型理由是否都已填寫具體內容？逐一列出空白 placeholder。
**Risk**: 框架未確定，前端工程師無法開始環境建置，Sprint 1 無法啟動。
**Fix**: 依 BRD/IDEA 推斷並填入具體框架名稱 + 版本 + 選型理由，不得保留 `{{PLACEHOLDER}}`。

#### [CRITICAL] 2 — §4.2 Navigation Map 缺少 Auth Guard 路徑
**Check**: §4.2 Mermaid stateDiagram 是否包含「未登入訪問受保護路由 → 重定向到 Login Screen」的路徑？若 PRD 有登入需求但 Navigation Map 沒有 Auth Guard 轉換，視為 CRITICAL。
**Risk**: 前端工程師實作 Router Guard 時無設計依據，可能漏掉保護路由，造成未授權訪問。
**Fix**: 在 Navigation Map 加入從受保護 Screen 指向 Login Screen 的 Auth Guard 轉換箭頭（標注「未登入 → redirect Login」）。

#### [HIGH] 3 — §6.2 Auth Token 策略與 EDD 不一致
**Check**: §6.2 Token 儲存位置是否與 EDD §4 認證設計完全一致？若 EDD 指定 JWT Bearer Token，§6.2 是否說明 memory-only 策略（避免 XSS）？若 EDD 指定 httpOnly Cookie，§6.2 是否使用 Cookie 儲存？
**Risk**: Token 儲存策略矛盾，造成前後端 auth flow 不通，或安全漏洞（localStorage 儲存 JWT 可被 XSS 竊取）。
**Fix**: 以 EDD §4 認證設計為準，修正 §6.2 Token 儲存策略使其完全一致。

#### [HIGH] 4 — §2.2 平台選型與 BRD 不一致
**Check**: §2.2 平台選型表格是否涵蓋 BRD 中所有目標平台（Web/Mobile/Desktop/Game）？若 BRD 提及「遊戲」或 Cocos Creator 但 §2.2 只列 React，視為 HIGH。
**Risk**: 選型遺漏關鍵目標平台，導致後期需要重構或追加 platform port，浪費工程資源。
**Fix**: 對應 BRD 每個目標平台填入對應的技術方案，不得遺漏 BRD 明確要求的平台。

#### [MEDIUM] 5 — §2.3 核心相依套件少於 5 個
**Check**: §2.3 是否至少列出 5 個核心相依套件？是否包含 HTTP Client、State Management、Router、Form Validation？若有 UI Component Library 需求但未列出，亦為 finding。
**Risk**: 套件清單不完整，前端工程師可能在環境建置時各自選用不同版本，造成相依版本衝突。
**Fix**: 補充至少 5 個核心套件，明確指定版本，確保 HTTP Client / State / Router / Form 四類均覆蓋。

---

### Layer 2: 畫面流程完整性（由 UX Expert + Frontend Expert 聯合審查，共 6 項）

#### [CRITICAL] 6 — §4.1 PRD P0 功能無對應 Screen
**Check**: PRD 的每個 P0 User Story（或 Epic）是否都能在 §4.1 Screen 清單中找到對應 Screen？列出所有缺少對應 Screen 的 P0 功能。
**Risk**: P0 功能的 UI 入口缺失，前端無法實作對應功能，直接影響 P0 交付。
**Fix**: 為每個缺少對應的 P0 功能新增 Screen，補充路由和 PRD US 對應。

#### [HIGH] 7 — §4.2 Navigation Map 畫面轉換不完整
**Check**: §4.2 Navigation Map 是否涵蓋 §4.1 所有 Screen？每條轉換箭頭是否都有觸發條件說明（「點擊 XX」「操作成功」「條件 X」）？是否包含至少一條錯誤路徑（如「操作失敗 → 停留」）？
**Risk**: Navigation Map 不完整，前端工程師實作 Router 時遺漏 Screen 間的連接，造成導航死路或功能不可達。
**Fix**: 補充缺少的 Screen 轉換路徑和觸發條件；加入至少一條錯誤/失敗路徑。

#### [HIGH] 8 — §6.1 Screen × API 矩陣未覆蓋所有 P0 Endpoint
**Check**: 對照 API.md §2 的 P0 Endpoint 清單，§6.1 矩陣是否每個 P0 Endpoint 都出現至少一次？列出缺失的 Endpoint。
**Risk**: P0 API 未映射到任何 Screen，該 API 的前端整合在 Sprint 中無人負責，造成功能缺口。
**Fix**: 為每個缺失的 P0 Endpoint 補充對應的 Screen、觸發時機和失敗處理。

#### [HIGH] 9 — §6.3 Loading/Empty/Error 狀態設計不完整
**Check**: §6.3 是否涵蓋「列表（Loading Skeleton + Empty State + Error Toast）」「詳情（Loading Skeleton + Error Page）」「表單送出（Button Loading + Inline Error）」三種資料類型的三種狀態？缺少任一組合視為 HIGH。
**Risk**: 狀態缺失造成使用者在網路異常或資料為空時看到空白頁面或無反應，嚴重影響 UX 品質。
**Fix**: 補充缺少的狀態設計，確保三種資料類型 × 三種狀態均已定義。

#### [MEDIUM] 10 — §5.2 組件規格缺少 PDD 對應
**Check**: §5.2 組件表格的「對應 PDD」欄是否都已填寫具體章節（§3.2 等）或明確標注「PDD 未定義」？若有組件留空，視為 MEDIUM。
**Risk**: 組件與 PDD 設計無連結，前端工程師在實作時無 UI spec 依據，造成視覺不一致。
**Fix**: 逐一填寫 PDD 章節引用，或標注「PDD 未定義，由前端工程師自行設計」。

#### [MEDIUM] 11 — §4.1 Screen 清單缺少路由或 Scene 資訊
**Check**: §4.1 每個 Screen 的「路由 / Scene」欄是否都已填寫具體值（Web App 路徑 `/path/:id`，Cocos 的 Scene 名稱，Unity 的 Scene name）？是否有 `{{ROUTE}}` 未替換的 placeholder？
**Risk**: 缺少路由資訊，前端工程師無法建立 Router 配置，或 Cocos/Unity 工程師不清楚 Scene 命名。
**Fix**: 為每個 Screen 填入具體的路由路徑或 Scene 名稱，確保無裸 placeholder。

---

### Layer 3: 跨平台相容性（由 Frontend Expert 主審，共 4 項）

#### [CRITICAL] 12 — §3.1 BRD 目標平台未出現在支援矩陣
**Check**: BRD 中明確列出的每個目標平台是否都出現在 §3.1 支援矩陣中？若 BRD 提及 iOS/Android 但矩陣未列，視為 CRITICAL。
**Risk**: 目標平台缺漏，QA 無相容性測試依據，上線後才發現目標平台功能異常。
**Fix**: 補充缺少的目標平台行，填入支援等級和最低版本。

#### [HIGH] 13 — §9.2 缺少 iOS Safari 相容性 Workaround
**Check**: §9.2 是否至少包含一條 iOS Safari 的相容性問題和 workaround？常見問題：`100vh` bug、`position:fixed` + 虛擬鍵盤偏移、autoplay 限制、Safari WebGL 支援限制（若使用 Cocos/Unity）。若 iOS Safari 為 P0 平台但 §9.2 完全沒有 iOS Safari 條目，視為 HIGH。
**Risk**: iOS Safari 相容問題未事先記錄，前端工程師在 iOS 測試時才發現並臨時 patch，造成品質不穩定。
**Fix**: 補充至少一條 iOS Safari 相關的已知問題和對應 workaround（可包含 `100vh` → `window.innerHeight` workaround）。

#### [HIGH] 14 — §8.1 Breakpoint 與 PDD Design Token 不一致
**Check**: 若 PDD 存在且定義了 Design Token（breakpoints/spacing），§8.1 的 CSS 變數值是否與 PDD 完全一致？逐一比對數值，列出不一致的項目。
**Risk**: Breakpoint 不一致導致前端實作的 Layout 與 PDD 設計稿的 Responsive 行為不符，需要反覆修正。
**Fix**: 以 PDD Design Token 的值為準，修正 §8.1 所有不一致的數值。

#### [MEDIUM] 15 — §9.1 Feature Parity Matrix 關鍵功能未填寫
**Check**: §9.1 是否針對 PRD 中涉及的特殊 Web API（WebSocket / WebGL / Service Worker / Push Notification / File API）填寫了跨平台支援狀態？若有相關功能但 Matrix 保留空白，視為 MEDIUM。
**Risk**: 關鍵功能的跨平台支援狀態未確認，可能在特定平台上靜默失效，QA 也無測試依據。
**Fix**: 依 PRD 功能列出所有用到的特殊 Web API，逐一確認各 P0 平台的支援狀態並填入 Matrix。

---

### Layer 4: 效能與安全（由 Frontend Expert + QA Expert 聯合審查，共 5 項）

#### [CRITICAL] 16 — §12.2 CSP 配置含裸 Placeholder
**Check**: §12.2 CSP 配置中的 `{{API_DOMAIN}}`、`{{CDN_DOMAIN}}`、`{{FONT_CDN}}` 是否都已替換為真實 domain？若有任何裸 placeholder，視為 CRITICAL。
**Risk**: CSP 含裸 placeholder，無法直接部署；或前端工程師使用含佔位符的 CSP，導致 CSP 無效，XSS 風險未緩解。
**Fix**: 替換所有裸 placeholder 為真實 domain（API domain 來自 API.md Base URL 或 EDD）；若使用無 CDN，移除相關 directive。

#### [HIGH] 17 — §12.1/§12.3 敏感資料處理缺少 Token 策略說明
**Check**: §12.3 是否明確說明 Access Token 的儲存策略，且與 §6.2 完全一致？是否明確禁止 `localStorage` 儲存 JWT（或說明為何在此場景下可接受）？
**Risk**: Token 儲存策略不明確，前端工程師可能因便利性選用不安全的 localStorage，造成 XSS 竊取 Token 風險。
**Fix**: 確保 §12.3 Access Token 說明與 §6.2 一致，明確標注禁止行為和正確處理方式。

#### [HIGH] 18 — §11.2 Core Web Vitals 目標缺失
**Check**: §11.2 是否填寫了 LCP、INP、CLS、FCP、TBT 全部 5 個指標的具體目標值？若有任何指標留空或保留 `{{TARGET}}` placeholder，視為 HIGH。
**Risk**: 效能目標不明確，前端工程師無優化方向，QA 無效能驗收標準，上線後效能問題無基準可判斷。
**Fix**: 填入所有 5 個 Core Web Vitals 目標值，若 EDD 有對應 SLO 以 EDD 為準，否則使用 FRONTEND.md 預設目標。

#### [HIGH] 19 — §13.1 Build 指令含裸 Placeholder
**Check**: §13.1 的 Development / Staging / Production 三個環境的 Build 指令是否都已替換為真實命令？是否有 `{{DEV_CMD}}` 等裸 placeholder？
**Risk**: Build 指令不明確，前端工程師和 CI/CD 配置無法直接使用，需要人工查閱推斷。
**Fix**: 替換所有裸 placeholder 為依框架推斷的具體指令（如 `vite`、`vite build --mode staging`、`vite build`）。

#### [MEDIUM] 20 — §11.1 Bundle Size 上限未依框架調整
**Check**: §11.1 的 Bundle Size 上限是否與 §2.1 選定的框架/技術方案匹配？若選用 Cocos Creator 或 Unity WebGL，初始 Bundle 通常遠大於 Web App 的 150KB 預設，預設值不適用。若框架對應的 Bundle 大小和預設值顯著不符但文件未調整，視為 MEDIUM。
**Risk**: 效能預算設定不合理，造成 CI Bundle Size 檢查不斷誤報，或標準過鬆導致實際效能問題被忽視。
**Fix**: 依實際框架特性調整 Bundle Size 上限；若使用 Cocos/Unity，替換為 WebGL build size 的上限並說明分包策略。

---

### Layer 5: 測試策略（由 QA Expert 主審，共 4 項）

#### [HIGH] 21 — §10.3 E2E 未覆蓋所有 P0 Screen Flow
**Check**: §10.3 E2E 測試覆蓋列表是否包含 §4.2 Navigation Map 中所有 P0 Screen Flow（包含主要 Happy Path 和 Auth Flow）？列出缺失的 P0 流程。
**Risk**: P0 Flow 未被 E2E 覆蓋，上線前無自動化迴歸測試，破壞性變更無法被提前發現。
**Fix**: 為每個 P0 Screen Flow 補充 E2E 測試條目，包含流程名稱、工具、覆蓋 Screen 清單和優先度標記。

#### [HIGH] 22 — §10.2 覆蓋率目標低於最低標準
**Check**: §10.2 的覆蓋率目標是否符合最低標準：Component 80%、Hook/Service 90%、Utils 95%？若有任何類型的目標低於標準，視為 HIGH。
**Risk**: 測試覆蓋率目標過低，無法作為 CI Quality Gate，程式碼品質無保障。
**Fix**: 將覆蓋率目標調整至至少達到最低標準（Component 80%、Hook/Service 90%、Utils 95%）。

#### [MEDIUM] 23 — §10.5 Cross-browser 自動化缺少 CI 觸發條件
**Check**: §10.5 是否明確說明 Cross-browser 測試的 CI 觸發條件（PR merge / 每日排程 / Release branch）？若留白或寫「手動執行」，視為 MEDIUM。
**Risk**: Cross-browser 測試無自動化觸發，容易被忽略跳過，相容性問題積累到版本末才發現。
**Fix**: 填寫具體的 CI 觸發條件（建議：PR merge 觸發 Chrome + Safari，每日排程觸發 Full Matrix）。

#### [MEDIUM] 24 — §10.4 Visual Regression 未定義閾值
**Check**: §10.4 是否定義了 Visual Regression 的接受閾值（diff < X%）？若有定義測試工具但閾值欄位為空，視為 MEDIUM。
**Risk**: Visual Regression 無通過標準，CI 無法自動判斷截圖差異是否可接受，每次需人工審查。
**Fix**: 填入具體閾值（建議 < 0.1% diff）；若選用 Percy/Chromatic，說明 Baseline 更新策略。

---

### Layer 6: 文件完整性（由技術文件角度通盤審查，共 2 項）

#### [HIGH] 25 — 裸 Placeholder 掃描（核心欄位）
**Check**: 掃描文件中所有 `{{PLACEHOLDER}}` 格式的字串。重點掃描：§2.1（框架/版本）、§4.1（路由）、§6.1（API Endpoint）、§12.2（CSP domain）、§13.1（Build 指令）。列出所有未替換的裸 placeholder 及其位置（章節）。
**Risk**: 含裸 placeholder 的設計文件無法直接使用，工程師需逐一人工填寫，失去文件的自動化生成價值。
**Fix**: 對每個裸 placeholder，依上游文件推斷並填入真實值；若真的無法確定，加上 `（待確認：描述）` 說明而非保留 `{{PLACEHOLDER}}`。

#### [LOW] 26 — §7 / §15 技術說明過於泛化
**Check**: §7.1 Global State Schema 的 `{{DOMAIN_STATE}}` 是否有填入業務域的具體資料結構（至少一個業務域，如 `items`、`orders`、`players`）？§15.1 資料夾結構的 `{{feature}}` 是否有替換為真實業務域名稱？
**Risk**: 業務域 State 和資料夾結構保留泛化佔位符，前端工程師無法直接參考建立 State 結構。
**Fix**: 依 PRD 主要業務資源（如 `products`、`users`）填入至少一個具體的業務域 State 定義和資料夾名稱。


---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/FRONTEND.md`，提取所有 `^## ` heading（含條件章節），共約 18 個
2. 讀取 `docs/FRONTEND.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
