---
doc-type: FRONTEND
output-path: docs/FRONTEND.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md
  - docs/VDD.md     # Layer 3.5 — 視覺設計系統（Design Token 直接引用、資產 URL、元件視覺規格）
  - docs/EDD.md
  - docs/ARCH.md    # Layer 5a — 元件邊界、BFF 模式、Service 名稱
  - docs/API.md
quality-bar: "§2 平台選型與 BRD 目標平台一致；§4 每個 PRD User Story 都有對應 Screen；§6 每個 Screen 的 API 呼叫矩陣已填寫；§8 Breakpoint 與 PDD Design Token 一致；§10 E2E 覆蓋所有 P0 Screen Flow；§11 Core Web Vitals 目標已定義；§12 CSP 配置已填寫；無裸 placeholder"
---

# FRONTEND.gen.md — Frontend Design Document 生成規則

依 PRD + PDD + API 產出 FRONTEND.md，涵蓋前端技術選型、畫面流程、API 整合、跨平台相容性、測試策略。

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
| `IDEA.md`（若存在）| 全文 | 了解產品性質——判斷適合 Web App、Game（Cocos/Unity）或混合模式 |
| `BRD.md` | 目標平台、使用者裝置需求 | 決定 §2 平台選型（Web/Mobile/Desktop/Game）和 §3 相容性矩陣 |
| `PRD.md` | 所有 User Stories 和 AC、P0/P1/P2 功能分類 | 推斷 §4 畫面清單和 Navigation Map |
| `PDD.md`（若存在）| UI 互動設計、Design Token、組件規格 | §5 Component Architecture 對齊 PDD，§8 Breakpoint 必須與 PDD Design Token 完全一致 |
| `VDD.md`（若存在）| §3 Brand Identity、§6 Design Tokens、§7 Asset Pipeline | **最重要的視覺上游**：Design Token 系統（CSS 變數命名/值）直接實作於 §8；資產 URL 規格影響 §6 API 整合；元件視覺規格（圓角、陰影、動畫 Easing）影響 §5 Component Architecture |
| `EDD.md` | §3 架構（前後端分離/SSR/SSG）、§4 安全設計 | §12 CSP 配置、§6 Token 管理策略必須與 EDD 一致 |
| `ARCH.md` | §3 元件架構、Service 邊界、BFF/API Gateway 模式 | §2 平台選型的 BFF 層設計、§5 Component 邊界與 Service 名稱必須與 ARCH 一致 |
| `API.md` | 所有 Endpoint（§2）、認證方式（§1）、Response Schema（§3） | §6 Screen × API 矩陣必須覆蓋 API.md 的所有 P0 Endpoint |

### IDEA.md Appendix C 素材讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與 Frontend 相關的檔案。
對每個存在的 `docs/req/` 檔案，結合 Appendix C「應用於」欄位標有「FRONTEND §」的段落，
作為生成 FRONTEND 對應章節的補充依據（尤其是目標平台需求和 UX 研究素材）。
優先採用素材原文描述，而非 AI 推斷。若無引用，靜默跳過。

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- VDD Design Token（§6 Token 命名/值）vs FRONTEND §8 CSS variables（是否完全一致）
- VDD Asset Pipeline（§7 資產格式規格）vs §6 API 整合的資產 URL 格式（是否衝突）
- PDD Design Token（breakpoints）vs FRONTEND §8 CSS variables（是否一致）
- PRD 功能列表 vs §4 Screen 清單（是否有 US 無對應 Screen）
- API.md Endpoint 清單 vs §6 Screen × API 矩陣（是否有 Endpoint 無對應 Screen）
- EDD 認證方式 vs §6.2 Auth Token 管理策略（是否衝突）

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並依衝突解決機制處理。

---

## 前端技術推斷規則

### 框架選型推斷

依 BRD 和 IDEA 的產品描述自動推斷：

| 產品特徵 | 推薦技術方案 |
|---------|------------|
| 遊戲（2D/物理引擎/大量動畫） | Cocos Creator 3.x |
| 3D 遊戲 / WebGL 體驗 | Unity WebGL 或 Cocos Creator 3D |
| 管理後台 / 資料密集 | React + TypeScript 或 Vue 3 + TypeScript |
| 行銷網站 / 內容站 | Next.js（SSG/SSR） |
| 純 Web App（SPA） | React / Vue 3 / Svelte |
| 跨平台 App（iOS+Android+Web） | React Native + React Web 或 Flutter |
| 輕量嵌入式小工具 | 原生 JavaScript / Web Components |

若 BRD 明確指定技術，以 BRD 為準，不覆蓋。

### 測試框架推斷

| 核心框架 | Unit Test | E2E | Visual Regression |
|---------|-----------|-----|------------------|
| React | Jest + React Testing Library | Playwright | Percy 或 Chromatic |
| Vue | Vitest + Vue Test Utils | Playwright | Percy |
| Cocos Creator | Cocos 內建測試 / Jest | Playwright（Web build） | 截圖比對 |
| Unity WebGL | Unity Test Runner | Playwright（build 後） | 截圖比對 |
| Vanilla JS | Jest / Vitest | Playwright | — |

---

## §1 Overview 生成規則

必須在一段話（3-5 句）說明：
- 產品前端技術方案的核心選擇（框架 + 平台）
- 主要支援的目標平台
- 與後端 API 的整合方式
- 文件範圍（包含和不包含）

---

## §2 Frontend Tech Stack 生成規則

### §2.1 Framework Selection 表格

依推斷規則填入以下欄位（不得保留 `{{PLACEHOLDER}}`）：
- 核心框架（含版本 + 選型理由）
- 語言（TypeScript 優先；若 Cocos 或 Unity，說明語言版本）
- 建構工具（Vite / webpack / Cocos Editor / Unity Editor）
- 套件管理（npm / yarn / pnpm）

### §2.2 平台選型

依 BRD 目標平台填寫。若 BRD 提及「遊戲」或 Cocos，必須出現 Cocos Creator 行；
若提及「跨平台」，必須說明 iOS/Android 覆蓋策略。

### §2.3 核心相依套件

至少列出 5 個套件，包含：
- HTTP Client（axios / fetch wrapper）
- State Management（Zustand / Pinia / Redux Toolkit）
- Router（React Router / Vue Router / Cocos Scene Manager）
- Form Validation（React Hook Form / Vee-validate / Zod）
- UI Component Library（若有）

---

## §3 Target Platforms & Compatibility Matrix 生成規則

### §3.1 平台支援矩陣

依 BRD 目標平台填入支援等級：
- P0-Must：BRD 明確列出的必要平台
- P1-Should：BRD 提及但非強制的平台
- P2-Nice：BRD 未提及但常見的平台

若 BRD 未指定，預設 P0: Chrome + Firefox + Safari + Edge，P1: iOS Safari + Android Chrome。

最低版本推斷規則：
- 若 EDD 有指定，以 EDD 為準
- 若無，預設 Chrome/Firefox/Edge 最近 2 大版，Safari iOS 14+，Android 10+

### §3.2 螢幕尺寸支援

若 PDD 有 Responsive Design 說明，以 PDD 為準；否則使用 FRONTEND.md 預設 5 檔。

---

## §4 Screen Flow & Navigation Architecture 生成規則

### §4.1 畫面清單

**必填規則**：
- 依 PRD 每個 User Story 推斷對應 Screen（P0 功能必須有 Screen）
- Screen ID 格式：`SCR-001`，三位數字遞增
- 路由格式：Web App 使用 `/path/:id`；Cocos 使用 Scene 名稱；Unity 使用 Scene name
- 每個 Screen 必須對應至少一個 PRD User Story（`US-XXX`）

**最小 Screen 清單**（即使 PRD 未明確，也必須包含）：
- 若有認證功能：Login Screen（SCR-001）
- 若有清單展示：List/Home Screen
- 若有詳情查看：Detail Screen
- 若有設定：Settings Screen

### §4.2 Navigation Map（Mermaid）

使用 `stateDiagram-v2` 語法，覆蓋：
- 所有 §4.1 Screen 的轉換關係
- 每條轉換箭頭必須標注觸發條件（點擊按鈕、登入成功、操作完成等）
- 錯誤路徑（如登入失敗 → 停留在 Login Screen）
- Auth Guard 路徑（未登入訪問受保護路由 → 重定向到 Login）

### §4.3 Deep Link / URL Scheme

若為 Web App（非 Cocos/Unity），必須填寫每個 Screen 的路由和 Guard 狀態。

### §4.4 Auth Guard 規則

明確說明：Token 儲存方式（須與 §6.2 一致）、過期後行為、Refresh Token 策略。

---

## §5 Component Architecture 生成規則

### §5.1 Component 層次

依 §4 Screen 清單推斷：
- 每個 Screen 對應一個 Page Component
- 跨 Screen 重用的 UI 元素升級為 Organism 或 Molecule
- 基礎 Atoms 必須至少包含：Button、Input、Icon、Typography

若使用 Cocos Creator，替換為 Node 層次（Scene / Prefab / Component）；
若使用 Unity，替換為 Hierarchy（Canvas / Panel / Prefab）。

### §5.2 共用 UI 組件規格

必須填寫所有 PDD 中定義的組件；若 PDD 不存在，至少填寫 Button 和 Input 兩個組件。
`對應 PDD` 欄位必須填寫具體章節引用（如 `§PDD 3.2`）或標注「PDD 未定義」。

### §5.3 組件通訊策略

依框架推斷通訊方案：
- React：Props / Callbacks / Zustand / Context API
- Vue：Props / Emits / Pinia / provide/inject
- Cocos：Props / EventTarget / Singleton Manager
- Unity：UnityEvent / ScriptableObject / EventBus

---

## §6 API Integration Map 生成規則

### §6.1 Screen × API Endpoint 矩陣

**覆蓋規則**：
- 讀取 API.md §2 所有 Endpoint
- 依每個 Endpoint 的業務語意，推斷觸發該 API 的 Screen
- 每個 P0 API Endpoint 必須在矩陣中出現至少一次
- 失敗處理必須明確（Toast / Empty State / Error Page / Retry）

**必填的失敗處理模式**：
- GET（列表）：Empty State + CTA
- GET（詳情）：Error Page（含返回按鈕）
- POST/PATCH（表單）：Inline Error + Button 恢復可點
- DELETE：Toast 確認成功/失敗

### §6.2 Auth Token 管理

必須與 EDD §4 認證設計完全一致：
- 若 EDD 使用 JWT + httpOnly Cookie：TOKEN 儲存選 httpOnly Cookie
- 若 EDD 使用 Bearer Token：說明 memory-only 策略（不存 localStorage）
- Refresh Token 策略：401 interceptor 自動 refresh 一次，失敗後 redirect to Login

### §6.4 Request / Response 攔截器

必須包含：
- Request 攔截：自動注入 Authorization header
- Response 攔截：統一處理 401（refresh/redirect）、500（Toast + 上報 Sentry）
- 提供 pseudo-code 或代碼片段說明攔截器實作

---

## §7 State Management Design 生成規則

### §7.1 Global State Schema

必須定義 TypeScript interface，包含：
- `auth`：user / token / isAuthenticated
- `ui`：theme / locale / isLoading（至少這三個）
- 業務域 State（至少一個，依 PRD 主要資源命名）

### §7.2 State 分層規則

依框架推斷工具：
- React：Server State = TanStack Query；Global = Zustand；Form = React Hook Form
- Vue：Server State = TanStack Query 或 Pinia with fetchData；Global = Pinia；Form = VeeValidate

### §7.3 Cache 與持久化

至少填寫：User Profile（localStorage, Session）和一個業務資料的快取策略。

---

## §8 Responsive Design & Adaptive Layout 生成規則

### §8.1 Breakpoint 系統

**關鍵規則**：CSS 變數值必須與 PDD 的 Design Token 完全一致。
若 PDD 不存在，使用 FRONTEND.md 預設值。
若 PDD 定義了不同的 breakpoint 值，以 PDD 為準並在此說明來源。

### §8.3 自適應策略

至少填寫 NavBar 和 Sidebar 的三個 breakpoint 行為。
每個自適應行為必須明確（不得寫「根據設計決定」）。

---

## §9 Cross-Platform Compatibility 生成規則

### §9.1 Feature Parity Matrix

依 §3.1 平台矩陣，列出所有 P0 平台的功能支援狀態。
特別需要填寫以下功能的支援狀態：
- WebSocket / SSE（若 PRD 有即時通知）
- WebGL / Canvas（若使用 Cocos/Unity 或有圖表）
- PWA / Service Worker（若有離線功能）
- Push Notification（若 PRD 有通知需求）
- File API（若有上傳功能）

### §9.2 Platform-Specific Workarounds

必須至少填寫 iOS Safari 的常見問題（autoplay、100vh bug、position:fixed keyboard shift）。
若使用 Cocos/Unity，必須填寫 WebGL 記憶體限制和 iOS Safari 相容性 workaround。

---

## §10 Frontend Test Strategy 生成規則

### §10.2 Unit Test 規範

依 §2 框架推斷測試工具（見技術推斷規則表）。
覆蓋率目標不得低於：Component 80%、Hook/Service 90%、Utils 95%。

### §10.3 E2E 測試覆蓋

**必填 E2E 流程**：
- 所有 P0 Screen Flow（依 §4.2 Navigation Map 提取）
- 登入 + 主要功能 + 登出 流程必定包含

工具預設 Playwright（除非 BRD 指定其他）。

### §10.4 Visual Regression

若 PDD 存在（有明確 UI 設計），必須定義 Visual Regression 測試，閾值 < 0.1% diff。

---

## §11 Performance Budget 生成規則

### §11.1 Bundle Size 上限

使用 FRONTEND.md 預設值（首頁 JS 150KB gzip，CSS 30KB，圖片 200KB，總計 350KB）。
若 BRD 有特殊效能要求（如「首屏 < 1s」），對應調整上限值。

### §11.2 Core Web Vitals

使用 FRONTEND.md 預設目標（LCP < 2.5s, INP < 200ms, CLS < 0.1, FCP < 1.5s, TBT < 200ms）。
若 EDD 定義了前端效能 SLO，以 EDD 為準。

---

## §12 Frontend Security 生成規則

### §12.2 Content Security Policy

**關鍵規則**：CSP 配置必須包含實際的 API Domain（來自 EDD 或 API.md Base URL）。
`{{API_DOMAIN}}` 不得保留為空 placeholder，必須填入真實 domain 或開發時的 localhost。
`{{CDN_DOMAIN}}` 若使用 CDN 必須填入；若無，移除該行。

### §12.3 敏感資料處理

必須說明 Access Token 儲存策略（須與 §6.2 完全一致）。

---

## §13 Build & Bundle Configuration 生成規則

### §13.1 Build 目標

依 §2 框架填入實際的 build 指令（不得保留 `{{CMD}}` placeholder）：
- React/Vite：`vite`, `vite build --mode staging`, `vite build`
- React/CRA：`react-scripts start`, `react-scripts build`
- Next.js：`next dev`, `next build`
- Cocos Creator：Editor build 或 CLI 指令
- Unity：Unity CLI build 指令

### §13.2 環境變數

至少填寫 API Base URL 和一個 Feature Flag 變數（若有）。
注意 `⚠️` 警告說明必須保留（前端環境變數為公開值）。

---

## §14 Internationalization 生成規則

若 BRD 明確說明「僅繁體中文」，可精簡 §14，只留 zh-TW Locale 並說明「現階段不支援多語系」。
若 BRD 有多語系需求，必須填寫所有語言的 Locale 表格和 i18n 工具選型。

---

## §15 Appendix 生成規則

### §15.1 前端資料夾結構

依 §2 框架調整：
- Cocos Creator：使用 Cocos 標準結構（assets/scripts/scenes/prefabs）
- Unity：使用 Unity 標準結構（Assets/Scripts/Scenes/Prefabs）
- React/Vue：使用 FRONTEND.md 預設的 src/ 結構

### §15.2 Git Commit 規範

保持 FRONTEND.md 的 `feat(frontend):`、`fix(frontend):` 格式不變。

---

## 生成前自我檢核清單

- [ ] §2.1 Framework Selection 無裸 placeholder，框架版本已填寫
- [ ] §3.1 每個 BRD 目標平台都出現在支援矩陣中
- [ ] §4.1 每個 PRD P0 功能都有對應 Screen
- [ ] §4.2 Navigation Map 使用 `stateDiagram-v2`，涵蓋所有 Screen 的轉換路徑
- [ ] §4.2 Navigation Map 包含 Auth Guard 路徑（未登入 → Login）
- [ ] §5.2 每個 PDD 定義的組件都有對應行
- [ ] §6.1 每個 API.md P0 Endpoint 都出現在 Screen × API 矩陣中
- [ ] §6.2 Token 管理策略與 EDD §4 認證設計一致
- [ ] §6.4 攔截器設計包含 401 自動 refresh 邏輯
- [ ] §8.1 Breakpoint CSS 變數與 PDD Design Token 完全一致（若 PDD 存在）
- [ ] §9.2 至少一條 iOS Safari 相容性 Workaround
- [ ] §10.3 E2E 覆蓋所有 P0 Screen Flow
- [ ] §11.2 Core Web Vitals 目標已全部填寫（LCP/INP/CLS/FCP/TBT）
- [ ] §12.2 CSP 配置中 API Domain 已填入真實值，非裸 placeholder
- [ ] §13.1 Build 指令已填入，非 `{{CMD}}` placeholder
- [ ] 所有 `[UPSTREAM_CONFLICT]` 標記均已處理或說明
- [ ] 無未替換的 `{{PLACEHOLDER}}` 格式佔位符
