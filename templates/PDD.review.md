---
doc-type: PDD
target-path: docs/PDD.md
reviewer-roles:
  primary: "資深 UX/UI Expert（PDD 審查者）"
  primary-scope: "PRD 對齊、Wireframe 完整性、Design Token 定義、Interaction Design 具體度、Accessibility"
  secondary: "資深 Frontend Expert"
  secondary-scope: "CSS 實作可行性、Breakpoint 系統、Component 可重用性、設計系統一致性"
  tertiary: "資深 QA Expert"
  tertiary-scope: "Responsive 測試覆蓋、Visual Regression 可行性、互動狀態完整性"
quality-bar: "前端工程師拿到 PDD 後，不需詢問設計師，能直接從 Design Token 建構 CSS 系統、從 Wireframe 實作所有 Screen、從 Interaction Design 實作所有互動狀態。"
upstream-alignment:
  - field: P0 User Stories 覆蓋
    source: PRD.md §5 User Stories
    check: PDD 的每個 P0 US 是否有對應的 Screen 或 Component 規格（§5 Screen Specs）
  - field: 使用者角色
    source: PRD.md §3.2 Personas
    check: PDD §2.0 Personas 是否與 PRD §3.2 一致，設計決策是否以 PRD Persona 為依據
  - field: 目標平台
    source: BRD.md §目標平台
    check: PDD Platform Scope Declaration 是否涵蓋 BRD 定義的所有目標平台
---

# PDD Review Items

本檔案定義 `docs/PDD.md` 的審查標準。由 `/reviewdoc PDD` 讀取並遵循。
審查角色：三角聯合審查（資深 UX/UI Expert + 資深 Frontend Expert + 資深 QA Expert）
審查標準：「假設公司聘請一位 10 年以上資深前端架構師兼設計系統專家，以最嚴格的業界標準進行 PDD 驗收審查。」

---

## Review Items

### Layer 1: PRD 對齊（由 UX/UI Expert 主審，共 4 項）

#### [CRITICAL] 1 — P0 US 無對應 Screen
**Check**: PRD §5 中每個 P0 User Story 是否在 PDD §5 Screen Specifications 中有對應的 Screen 規格？逐一對照 PRD US 清單，列出所有無對應 Screen 的 P0 US。
**Risk**: P0 功能無 Screen 規格，前端工程師無設計依據，P0 功能入口在產品中無法呈現，直接影響 Sprint 1 交付。
**Fix**: 為每個缺漏的 PRD P0 US 補充對應 Screen 規格（至少包含：用途、進入方式、Layout 結構、元件清單、互動規格）；在 §1.2 PRD 需求對應表中建立完整的 US → Screen 對應索引。

#### [CRITICAL] 2 — User Flow 缺少 Error Path
**Check**: PDD §4 User Flows 是否包含錯誤流程（§4.3 錯誤流程）？錯誤流程是否覆蓋：API 失敗（Toast/Error Page）、驗證錯誤（Inline Error）、無權限（導向授權頁）、空狀態（Empty State）？只有 Happy Path 視為 CRITICAL。
**Risk**: 錯誤情境 UI 設計缺失，前端工程師各自實作不一致的錯誤狀態，用戶在異常情境下體驗割裂，且 QA 無法驗收錯誤處理行為。
**Fix**: 補充 §4.3 錯誤流程 Mermaid flowchart，至少覆蓋四類錯誤情境；並在 §5 各 Screen 的元件清單中補充 Error State 的視覺描述。

#### [HIGH] 3 — IA 存在孤立節點
**Check**: §3.1 Sitemap 和 §4 User Flows 中是否有頁面/模組無法從其他頁面到達（孤立節點）？使用有向圖邏輯逐一驗證每個 Screen 是否有至少一個入口路徑。
**Risk**: 孤立節點表示用戶無法透過正常導覽到達該頁面，功能無法被使用，或需要依賴外部連結（書籤/直連 URL），嚴重影響功能可達性。
**Fix**: 為每個孤立節點補充至少一個入口（來源頁面 → 孤立節點的觸發條件）；若確實是 Deep Link Only 的頁面，在文件中明確標注並說明進入方式。

#### [MEDIUM] 4 — P1 US 無設計考量
**Check**: PRD P1 User Story 在 PDD 中是否有設計考量說明？可以是 Low-fi Wireframe 說明、Component 清單、或 §1.2 PRD 需求對應表的明確標注。完全忽略 P1 且無任何說明視為 MEDIUM。
**Risk**: P1 功能 UI 未納入設計，Sprint 2+ 實作時需要臨時補充設計，影響設計一致性和版本間的視覺連貫性。
**Fix**: 在 §1.2 PRD 需求對應表補充所有 P1 US 的設計回應（可以是「待 Sprint 2 細化」的簡要說明）；為有 UI 複雜度的 P1 功能補充基本的 Component 清單。

---

### Layer 2: Design Token 完整性（由 Frontend Expert 主審，共 4 項）

#### [CRITICAL] 5 — Design Token 不完整
**Check**: §9.3 Design Tokens 是否包含以下必要類別？
- Color：Primitive（色彩 scale）+ Semantic（primary/secondary/error/warning/success/surface/text）
- Typography：font-family、font-size（scale）、font-weight、line-height
- Spacing：4px 為基礎的 scale（4/8/16/24/32/48）
- Radius：至少 sm/md/lg 三個層次
缺少任一類別視為 CRITICAL。
**Risk**: Design Token 不完整，前端工程師各自硬編碼數值，設計系統碎片化，主題切換（Light/Dark）或品牌更新時需要全面重構。
**Fix**: 補充缺漏的 Token 類別；確保三層架構完整（Primitive → Semantic → Component）；Semantic Token 至少定義 `color-action-primary`、`color-feedback-error`、`color-surface-default`、`color-text-primary` 四個核心語意 Token。

#### [HIGH] 6 — Dark Mode Token 未定義
**Check**: §9.4 Dark Mode Token Mapping 是否存在且完整？每個 Semantic Token 是否都有 Light / Dark 兩組值定義？是否有 WCAG 對比度驗證數值？
**Risk**: Dark Mode Token 缺失，前端工程師各自實作深色主題，造成顏色不一致；或上線前才發現深色主題下的 WCAG 對比度不符合規定。
**Fix**: 補充 §9.4 Dark Mode Token Mapping 表格，為每個 Semantic Color Token 定義 Light 和 Dark 值，並填入實際對比度數值（使用 WCAG Contrast Checker 驗算）。

#### [HIGH] 7 — Breakpoint 系統不完整或與平台不符
**Check**: §7.1 Breakpoints 是否涵蓋所有必要斷點（320 / 375 / 768 / 1024 / 1440 / 1920px）？各斷點是否說明 Layout 策略變化（單欄/雙欄/多欄、導覽類型變化）？若 BRD 目標平台包含行動裝置，是否有 Mobile-First 聲明？
**Risk**: Breakpoint 系統不完整，前端工程師無 Responsive 實作依據；或 Breakpoint 定義與 FRONTEND.md 的 CSS 實作不一致，導致設計與實作差異。
**Fix**: 補充完整的 Breakpoint 表格（含 Mobile S 320px 到 Desktop XL 1920px）；為每個 Breakpoint 說明 Layout 策略和導覽形式的變化；Mobile / Tablet / Desktop 的關鍵元件響應行為需在 §7.2 完整列出。

#### [LOW] 8 — Shadow/Animation Token 缺失
**Check**: §9.3 是否定義 Shadow Token（至少 sm/md/lg 三個 elevation 層次）和 Animation Token（duration-fast/normal/slow + ease-out/ease-in-out）？影響視覺一致性，但 LOW 優先。
**Risk**: Shadow 和 Animation 無 Token，工程師各自填入數值，造成產品各處的陰影深度和動畫速度不一致；`duration-fast` / `duration-normal` 未定義則 §6.1 Motion Design 的規格無法落地。
**Fix**: 在 §9.3 補充 Shadow Token（sm: `0 1px 3px ...`、md: `0 2px 8px ...`、lg: `0 8px 24px ...`）和 Animation Token（duration-fast: 150ms、duration-normal: 300ms、duration-slow: 500ms）。

---

### Layer 3: Screen 規格完整性（由 UX/UI Expert 主審，共 4 項）

#### [CRITICAL] 9 — 互動元件缺少完整 State 定義
**Check**: 每個互動型元件（Button、Input、Modal、Dropdown、Checkbox、Toggle）是否有完整的 State 矩陣？必要狀態：default / hover / active / focus / disabled / loading / error。§5 Screen 元件清單中缺少任何必要狀態的互動元件視為 CRITICAL。
**Risk**: State 缺失導致前端工程師自行補充未定義的狀態，造成跨元件視覺不一致；QA 無法驗收；Accessibility 的 focus state 缺失直接違反 WCAG 2.4.7。
**Fix**: 為每個互動型元件補充完整的 State 矩陣，說明每個 State 的視覺表現（顏色 Token 引用、透明度、游標樣式）；Focus State 必須包含 2px 以上的外框樣式。

#### [HIGH] 10 — Empty State / Loading State 設計缺失
**Check**: §6.3 空狀態設計是否覆蓋四種基本情境（首次使用無資料、搜尋無結果、網路離線、錯誤狀態）？§6.4 Loading States 是否定義三種主要情境（頁面初次載入 Skeleton、分頁加載、按鈕 Loading State）？缺少任一組合視為 HIGH。
**Risk**: 狀態設計缺失，前端工程師各自實作不一致的空狀態和載入態，用戶在網路異常或資料為空時看到空白頁面，嚴重影響 UX 品質和用戶信任感。
**Fix**: 補充 §6.3 四種空狀態（說明文字、圖示建議、CTA）和 §6.4 三種載入態規格；Skeleton Screen 需說明與真實內容的骨架對應關係，避免 Layout Shift。

#### [HIGH] 11 — Screen 缺少互動規格
**Check**: §5 每個 Screen 的「互動規格」表格是否填寫完整？是否有 Screen 的互動規格表格為空白或只有一行？互動規格應包含：觸發條件、動作、動畫效果、持續時間（ms）。
**Risk**: 互動規格缺失，前端工程師憑猜測實作互動邏輯（動畫時間、觸發條件），驗收時頻繁返工，延誤交付；動畫時間不一致破壞產品整體感。
**Fix**: 為每個 Screen 補充互動規格表格，至少覆蓋主要 CTA 的點擊行為、頁面間導覽動畫、表單提交回饋三類互動；每條規格必須有具體的動畫時間（ms）。

#### [MEDIUM] 12 — Client Class Diagram 缺失或結構錯誤
**Check**: §9.5 Client Class Diagram 是否存在且依平台選用正確圖示（Web：Clean Architecture 四層；Unity：MonoBehaviour 架構；Cocos：ccclass 架構）？類別間的繼承（空心三角）和組合（實心菱形）關係箭頭是否正確？
**Risk**: Class Diagram 缺失或錯誤，前端工程師不清楚 Component 的架構層次和依賴關係，容易設計出耦合過高的元件；QA 無法追蹤每個 Class 對應的測試文件。
**Fix**: 依目標平台補充對應的 Class Diagram（§9.5.1 Web / §9.5.2 Unity / §9.5.3 Cocos）；確保依賴方向正確（Presentation → Application → Domain ← Infrastructure）；補充 §9.5.4 Class → Test Traceability 表格。

---

### Layer 4: Interaction Design（由 UX/UI Expert + Frontend Expert 聯合審查，共 3 項）

#### [HIGH] 13 — Motion Design 規格缺失或不完整
**Check**: §6.1 Motion Design 是否定義了以下必要內容？
- 頁面進場/退場動畫（規格含 easing function + duration）
- Modal / Dropdown 開啟/關閉動畫
- Toast / Notification 出現動畫
- `prefers-reduced-motion` 替代方案（每個動畫都需要有對應的 reduced-motion 版本）
缺少 reduced-motion 替代方案視為 HIGH finding。
**Risk**: Motion Design 規格不完整，前端工程師各自填入數值，動畫速度和緩動函數不一致；缺少 reduced-motion 支援直接違反 WCAG 2.3.3，影響前庭障礙用戶。
**Fix**: 補充 §6.1.1 Motion Design Specification，為每種動畫類型定義 easing function + duration；為每個動畫補充 `prefers-reduced-motion` 替代規格（通常替換為 `opacity` 淡入淡出）。

#### [HIGH] 14 — Micro-interaction 未定義
**Check**: §6.5 Micro-interaction Catalog 是否存在且覆蓋產品中的關鍵微互動？至少應包含：表單送出成功的視覺回饋、按讚/收藏的動畫回饋、計數器增減的邊界提示、Toggle 切換的即時回饋四類。完全缺失 §6.5 視為 HIGH。
**Risk**: Micro-interaction 未定義，前端工程師各自實作或直接忽略，造成用戶操作後缺乏即時回饋感，降低產品的精緻度和用戶信心。
**Fix**: 補充 §6.5 Micro-interaction Catalog，依照「觸發器 → 規則 → 回饋 → 迴圈」四元素框架，為每個關鍵微互動填入完整規格。

#### [MEDIUM] 15 — Feedback 機制規格不完整
**Check**: §6.2 回饋機制是否覆蓋三種時間維度（0-100ms 即時回饋、100ms-1s 短期回饋、> 1s 長期回饋）？是否有長時間操作（> 3s）但只定義了即時回饋（按鈕 Loading）而缺少進度反饋說明？
**Risk**: 長時間操作缺少進度反饋，用戶不確定系統是否在工作，容易重複觸發操作或放棄等待，導致數據損壞或重複提交。
**Fix**: 為所有可能超過 3 秒的操作（文件上傳、批次處理、長時間 API 呼叫）補充進度反饋規格（Progress Bar + 百分比文字 / 分段完成提示）；說明超時後的 UX 處理方式。

---

### Layer 5: Accessibility 與 Responsive（由 QA Expert 主審，共 3 項）

#### [CRITICAL] 16 — WCAG 2.1 AA Checklist 缺失
**Check**: §8.4 WCAG 2.1 AA Compliance Matrix 是否存在且逐項勾選（不接受「已符合 WCAG 標準」的空泛聲明）？是否覆蓋六大核心準則：1.1.1 非文字內容、1.3.1 資訊與關係、1.4.3 對比度、2.1.1 鍵盤操作、3.3.1 錯誤識別、4.1.2 名稱角色值？
**Risk**: 整段聲明無法追蹤具體合規項目，無障礙問題在 QA 或上線後才被發現，修改成本高；部分地區（歐盟 EAA、美國 Section 508）有法律合規要求。
**Fix**: 補充 §8.4 WCAG 2.1 AA Compliance Matrix，逐項標注「實作方式」和「測試方法」；M（強制）項目必須在 MVP 上線前通過；補充 §8.3 可及性測試計畫（工具 + 測試時機）。

#### [HIGH] 17 — 色彩對比度未驗證
**Check**: §9.3 / §9.4 中 Primary/Secondary 文字色與背景色的對比度數值是否有明確記錄？正文是否達 WCAG AA 標準（4.5:1）、大字（18px+）是否達 3:1？UI 元件邊框（按鈕邊框、輸入框邊框）是否達 3:1（WCAG 1.4.11）？未提供對比度數值視為 HIGH finding。
**Risk**: 對比度不足影響視障和低視力用戶閱讀；在 Dark Mode 下對比度問題尤為常見（設計師在 Light Mode 下驗證後未重新驗算 Dark Mode）。
**Fix**: 使用 WCAG 對比度工具（WebAIM Contrast Checker / Figma Contrast Plugin）逐一驗算，在 §9.4 Dark Mode Token 表格的 WCAG 對比度欄位填入實際計算值；不達標的 Token 值需調整。

#### [MEDIUM] 18 — Responsive 關鍵元件行為缺漏
**Check**: §7.2 是否覆蓋所有 P0 Screen 的關鍵元件在三種尺寸（Mobile / Tablet / Desktop）的響應行為？特別檢查：導覽（Tab Bar / Drawer / Side Nav 的切換邏輯）、Modal（Bottom Sheet vs 對話框）、表格（卡片式 vs 完整表格）三類元件。
**Risk**: 關鍵元件的 Responsive 行為未定義，前端工程師各自判斷，造成不同斷點的 Layout 不一致；QA 無 Responsive 測試依據。
**Fix**: 為所有 P0 Screen 的關鍵元件補充 Mobile / Tablet / Desktop 三種響應行為說明；若某些元件在所有斷點行為相同，明確標注「無響應式變化」。

---

### Layer 6: 文件完整性（由技術文件角度通盤審查，共 3 項）

#### [HIGH] 19 — Mermaid 流程圖語法錯誤
**Check**: PDD 中所有 Mermaid 圖（§3.1 Sitemap、§4.1-4.3 User Flows、§9.5 Class Diagram）是否語法正確？常見錯誤：節點 ID 含特殊字元或空格、箭頭語法 `-->` 拼錯、缺少引號的標籤、stateDiagram 中的 `[*]` 使用不當。列出所有語法疑似錯誤的圖和位置。
**Risk**: 語法錯誤的 Mermaid 圖在渲染時顯示為原始文字或空白，前端工程師無法閱讀設計意圖；Class Diagram 錯誤導致架構理解偏差。
**Fix**: 逐一修正語法錯誤；節點 ID 只使用英數字和底線；帶空格或特殊字元的標籤使用引號包裹；Mermaid Live Editor 驗證後再提交。

#### [MEDIUM] 20 — 裸 Placeholder
**Check**: 是否有 `{{PLACEHOLDER}}` 格式未替換的空白佔位符？重點掃描：§Document Control（DOC-ID / Figma 連結 / 審閱者）、§9.3 Token 的 `#{{HEX}}` 值、§5 Screen 的 `{{COMPONENT_1}}`、§13.2 元件交付規格的 `{{LINK}}`。
**Risk**: 裸 placeholder 留存，前端工程師無法確認文件的完整性，需要人工追問設計師；Figma 連結缺失是最常見的阻塞問題，前端無法取得精確尺寸和 Export 素材。
**Fix**: 替換所有裸 placeholder 為真實值；Figma 連結必須在文件 APPROVED 前填入；若暫時無法確定，改為 `（待確認：描述說明）` 格式。

#### [LOW] 21 — 設計稿連結缺失
**Check**: §Document Control 中的 Figma 設計稿連結是否填寫？§5 各 Screen Spec 末尾的 Figma Frame 連結是否填寫（`{{FIGMA_FRAME_LINK}}`）？§13.2 元件交付規格的 Figma 連結是否填寫？
**Risk**: 設計稿連結缺失，前端工程師在實作細節（間距、字型大小、陰影、圖示尺寸）時無法自助查閱，需要反覆詢問設計師，降低工程自主性和交付效率。
**Fix**: 補充 §Document Control 中的 Figma File URL；在 §5 每個 Screen 末尾加入對應 Frame 的直連 Figma 連結；§13.2 元件交付規格填入各元件的 Figma Frame 連結。

---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/PDD.md`，提取所有 `^## ` heading（含條件章節），共約 20 個
2. 讀取 `docs/PDD.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
