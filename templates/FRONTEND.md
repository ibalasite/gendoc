# FRONTEND — Frontend Design Document (FDD)
<!-- SDLC Frontend Layer — Frontend Architecture, Screen Flow, Cross-platform Compatibility -->
<!-- 對應角色：Frontend Expert -->
<!-- 回答：前端用什麼技術？畫面怎麼流？跨平台如何相容？如何與 API 整合？如何測試？ -->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | FRONTEND-{{PROJECT_CODE}}-{{YYYYMMDD}} |
| **專案名稱** | {{PROJECT_NAME}} |
| **文件版本** | v1.0 |
| **狀態** | DRAFT / IN_REVIEW / APPROVED |
| **作者** | {{AUTHOR}}（Frontend Expert） |
| **日期** | {{DATE}} |
| **上游 API** | [API.md](API.md) |
| **上游 PDD** | [PDD.md](PDD.md) |
| **審閱者** | {{UX_LEAD}}, {{QA_LEAD}} |

---

## Change Log

| 版本 | 日期 | 作者 | 變更摘要 |
|------|------|------|---------|
| v1.0 | {{DATE}} | {{AUTHOR}} | 初稿 |

---

## 1. Overview & Purpose

<!-- 一段話說明前端技術方案的核心決策與範圍 -->

{{FRONTEND_OVERVIEW}}

**適用對象**：前端工程師、QA、UX Designer、Tech Lead
**不包含**：後端 API 實作、K8s 部署（見 EDD / LOCAL_DEPLOY）

---

## 2. Frontend Tech Stack

### 2.1 Framework Selection

| 項目 | 選型 | 版本 | 選型理由 |
|------|------|------|---------|
| **核心框架** | {{FRONTEND_FRAMEWORK}} | {{VERSION}} | {{REASON}} |
| **語言** | {{LANGUAGE}} | {{VERSION}} | {{REASON}} |
| **建構工具** | {{BUILD_TOOL}} | {{VERSION}} | {{REASON}} |
| **套件管理** | {{PACKAGE_MANAGER}} | {{VERSION}} | {{REASON}} |

### 2.2 平台選型

<!-- 根據 BRD 目標平台選擇：Cocos Creator / HTML5 / Unity WebGL / 純 JS/TS -->

| 客戶端類型 | 技術方案 | 適用情境 |
|-----------|---------|---------|
| {{CLIENT_TYPE_1}} | {{TECH_SOLUTION_1}} | {{USE_CASE_1}} |
| {{CLIENT_TYPE_2}} | {{TECH_SOLUTION_2}} | {{USE_CASE_2}} |

### 2.3 核心相依套件

| 套件 | 用途 | 版本 |
|------|------|------|
| {{PACKAGE_1}} | {{PURPOSE_1}} | {{VERSION_1}} |
| {{PACKAGE_2}} | {{PURPOSE_2}} | {{VERSION_2}} |
| {{PACKAGE_3}} | {{PURPOSE_3}} | {{VERSION_3}} |

---

## 3. Target Platforms & Compatibility Matrix

### 3.1 平台支援矩陣

| 平台 | 支援等級 | 最低版本 | 備註 |
|------|---------|---------|------|
| Web（Chrome） | P0-Must | {{MIN_VERSION}} | |
| Web（Firefox） | P0-Must | {{MIN_VERSION}} | |
| Web（Safari） | P0-Must | {{MIN_VERSION}} | |
| Web（Edge） | P1-Should | {{MIN_VERSION}} | |
| iOS Safari | {{SUPPORT_LEVEL}} | iOS {{MIN_IOS}} | |
| Android Chrome | {{SUPPORT_LEVEL}} | Android {{MIN_ANDROID}} | |
| {{PLATFORM_N}} | {{SUPPORT_LEVEL}} | {{MIN_VERSION}} | |

**支援等級定義**：
- **P0-Must**：必須完全相容，任何功能差異為 Critical Bug
- **P1-Should**：目標相容，輕微 UI 差異可接受
- **P2-Nice**：盡力相容，功能降級可接受
- **Not Supported**：明確不支援，顯示「請使用支援的瀏覽器」提示

### 3.2 螢幕尺寸支援

| 類別 | 尺寸範圍 | 代表裝置 | 支援等級 |
|------|---------|---------|---------|
| Mobile S | 320px–375px | iPhone SE | {{SUPPORT_LEVEL}} |
| Mobile L | 376px–428px | iPhone 14 | {{SUPPORT_LEVEL}} |
| Tablet | 768px–1024px | iPad | {{SUPPORT_LEVEL}} |
| Desktop | 1280px–1440px | MacBook | {{SUPPORT_LEVEL}} |
| Wide | 1920px+ | 4K Monitor | {{SUPPORT_LEVEL}} |

### 3.3 Feature Detection vs User Agent

<!-- 說明偵測策略：優先用 Feature Detection（如 Modernizr），非 UA sniffing -->

{{FEATURE_DETECTION_STRATEGY}}

---

## 4. Screen Flow & Navigation Architecture

### 4.1 畫面清單

| Screen ID | 名稱 | 路由 / Scene | 對應 PRD US |
|-----------|------|------------|------------|
| SCR-001 | {{SCREEN_NAME}} | {{ROUTE}} | US-{{US_ID}} |
| SCR-002 | {{SCREEN_NAME}} | {{ROUTE}} | US-{{US_ID}} |

### 4.2 Navigation Map（Mermaid）

```mermaid
stateDiagram-v2
    [*] --> SCR-001_Launch
    SCR-001_Launch --> SCR-002_Home : 登入成功
    SCR-001_Launch --> SCR-001_Launch : 登入失敗（顯示錯誤）
    SCR-002_Home --> SCR-003_Detail : 點擊項目
    SCR-002_Home --> SCR-004_Settings : 設定圖示
    SCR-003_Detail --> SCR-002_Home : Back
    SCR-004_Settings --> SCR-002_Home : Back
```

### 4.3 Deep Link / URL Scheme

| 路由 | 對應 Screen | 參數 | Guard |
|------|------------|------|-------|
| `/` | SCR-002_Home | — | 需登入 |
| `/{{ENTITY}}/{{ID}}` | SCR-003_Detail | id: string | 需登入 |
| `/settings` | SCR-004_Settings | — | 需登入 |

### 4.4 Auth Guard 規則

<!-- 哪些路由需要 Token？Token 過期後導向何處？ -->

{{AUTH_GUARD_RULES}}

---

## 5. Component Architecture

### 5.1 Component 層次（Atomic Design）

```
App
├── Layout
│   ├── NavBar
│   ├── Sidebar
│   └── Footer
├── Pages（對應 Screen）
│   ├── {{PAGE_1}}
│   └── {{PAGE_2}}
├── Organisms（業務組件）
│   ├── {{ORGANISM_1}}
│   └── {{ORGANISM_2}}
├── Molecules（複合組件）
│   ├── {{MOLECULE_1}}
│   └── {{MOLECULE_2}}
└── Atoms（基礎元件）
    ├── Button
    ├── Input
    ├── Icon
    └── Typography
```

### 5.2 共用 UI 組件規格

| Component | Props | States | 對應 PDD |
|-----------|-------|--------|---------|
| Button | variant, size, disabled, loading | default/hover/active/disabled/loading | §PDD_SECTION |
| Input | type, label, error, placeholder | default/focus/error/disabled | §PDD_SECTION |
| {{COMPONENT}} | {{PROPS}} | {{STATES}} | {{PDD_REF}} |

### 5.3 組件通訊策略

<!-- Props down / Events up / Global State / Context API / Signals / EventBus -->

| 場景 | 通訊方式 | 理由 |
|------|---------|------|
| 父→子資料傳遞 | Props | 單向資料流 |
| 子→父事件 | Events/Callbacks | 解耦 |
| 跨層級共享狀態 | {{STATE_SOLUTION}} | {{REASON}} |
| 全域 UI 狀態 | {{GLOBAL_STATE_TOOL}} | {{REASON}} |

---

## 6. API Integration Map

### 6.1 Screen × API Endpoint 矩陣

| Screen | API Endpoint | Method | 時機 | 失敗處理 |
|--------|-------------|--------|------|---------|
| SCR-001_Login | `POST /api/v1/auth/login` | POST | 點擊登入 | 顯示錯誤 Toast |
| SCR-002_Home | `GET /api/v1/{{RESOURCE}}` | GET | 頁面載入 | 顯示 Empty State |
| {{SCREEN}} | `{{ENDPOINT}}` | {{METHOD}} | {{TRIGGER}} | {{ERROR_HANDLING}} |

### 6.2 Auth Token 管理

| 項目 | 設計 |
|------|------|
| Token 儲存位置 | {{STORAGE}}（localStorage / sessionStorage / httpOnly Cookie） |
| Token 刷新策略 | {{REFRESH_STRATEGY}} |
| 過期處理 | {{EXPIRY_HANDLING}} |
| Logout 清除項目 | {{CLEAR_LIST}} |

### 6.3 Loading / Skeleton 狀態設計

| 資料類型 | Loading 呈現 | 空資料呈現 | 錯誤呈現 |
|---------|------------|----------|---------|
| 列表 | Skeleton List（N 列） | Empty State + CTA | Error Toast + Retry |
| 詳情 | Skeleton Card | — | Error Page |
| 表單送出 | Button Loading | — | Inline Error |

### 6.4 Request / Response 攔截器

<!-- Axios Interceptor / Fetch Wrapper / 統一錯誤處理 -->

{{INTERCEPTOR_DESIGN}}

---

## 7. State Management Design

### 7.1 Global State Schema

```typescript
interface AppState {
  auth: {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
  };
  ui: {
    theme: 'light' | 'dark';
    locale: string;
    isLoading: boolean;
  };
  {{DOMAIN_STATE}}: {
    // 依業務域定義
  };
}
```

### 7.2 State 分層規則

| 狀態類型 | 管理方式 | 範例 |
|---------|---------|------|
| Server State | {{SERVER_STATE_TOOL}} | API 資料快取 |
| Global Client State | {{GLOBAL_STATE_TOOL}} | 登入狀態、主題 |
| Local UI State | Component local state | Modal 開關 |
| URL State | Router params/query | 篩選條件、分頁 |
| Form State | {{FORM_STATE_TOOL}} | 表單欄位值 |

### 7.3 Cache 與持久化

| 資料 | 持久化策略 | TTL | 清除時機 |
|------|----------|-----|---------|
| User Profile | localStorage | Session | Logout |
| {{CACHE_DATA}} | {{STRATEGY}} | {{TTL}} | {{CLEAR_TRIGGER}} |

---

## 8. Responsive Design & Adaptive Layout

### 8.1 Breakpoint 系統

```css
/* 與 PDD Design Token 一致 */
--bp-mobile-s:  320px;
--bp-mobile-l:  375px;
--bp-tablet:    768px;
--bp-desktop:   1280px;
--bp-wide:      1920px;
```

### 8.2 Layout Grid 規格

| Breakpoint | Columns | Gutter | Margin |
|-----------|---------|--------|--------|
| Mobile | 4 | 16px | 16px |
| Tablet | 8 | 24px | 32px |
| Desktop | 12 | 32px | 48px |
| Wide | 12 | 40px | auto |

### 8.3 自適應策略

<!-- Mobile First / Desktop First；哪些元件在小螢幕隱藏或收合 -->

| 元件 | Mobile | Tablet | Desktop |
|------|--------|--------|---------|
| NavBar | Hamburger Menu | Hamburger Menu | Full Nav |
| Sidebar | Hidden（Drawer） | Collapsible | Always Visible |
| {{COMPONENT}} | {{MOBILE_BEHAVIOR}} | {{TABLET_BEHAVIOR}} | {{DESKTOP_BEHAVIOR}} |

### 8.4 Fluid Typography

```css
--text-body:    clamp(14px, 1.5vw, 16px);
--text-heading: clamp(20px, 3vw, 32px);
--text-display: clamp(28px, 5vw, 56px);
```

---

## 9. Cross-Platform Compatibility

### 9.1 Feature Parity Matrix

| 功能 | Web | iOS Safari | Android Chrome | {{PLATFORM}} |
|------|-----|-----------|----------------|--------------|
| {{FEATURE_1}} | ✅ | ✅ | ✅ | {{STATUS}} |
| {{FEATURE_2}} | ✅ | ⚠️ 降級 | ✅ | {{STATUS}} |
| WebSocket | ✅ | ✅ | ✅ | {{STATUS}} |
| WebGL | ✅ | ✅ | ⚠️ 部分 | {{STATUS}} |

**圖例**：✅ 完整支援 ｜ ⚠️ 降級/workaround ｜ ❌ 不支援

### 9.2 Platform-Specific Workarounds

| 問題 | 影響平台 | Workaround | 測試驗證方式 |
|------|---------|-----------|------------|
| Safari autoplay 限制 | iOS Safari 14 以下 | 需使用者互動後才能播放 | {{TEST_METHOD}} |
| {{ISSUE}} | {{PLATFORM}} | {{WORKAROUND}} | {{TEST_METHOD}} |

### 9.3 Progressive Enhancement

<!-- 基礎功能（所有平台）→ 增強功能（現代瀏覽器） -->

| 功能層級 | 適用平台 | 實作方式 |
|---------|---------|---------|
| Baseline | 所有 P0 平台 | {{BASELINE_IMPL}} |
| Enhanced | 現代瀏覽器 | {{ENHANCED_IMPL}} |
| Cutting-edge | Chrome 最新版 | {{CUTTING_EDGE_IMPL}} |

---

## 10. Frontend Test Strategy

### 10.1 測試金字塔

```
         ┌─────────────┐
         │  E2E Tests  │  (Playwright / Cypress)
         │  5–10%      │  Critical User Flows
    ┌────┴─────────────┴────┐
    │  Integration Tests    │  (API Mock + Component)
    │  20–30%               │  Screen-level Interactions
┌───┴───────────────────────┴───┐
│  Unit Tests                   │  (Jest / Vitest)
│  60–70%                       │  Components, Utils, Hooks
└───────────────────────────────┘
```

### 10.2 Unit Test 規範

| 測試類型 | 框架 | 覆蓋率目標 | 對應 BDD Tag |
|---------|------|----------|------------|
| Component | {{COMPONENT_TEST_TOOL}} | 80%+ | @unit |
| Hook / Service | {{UNIT_TEST_TOOL}} | 90%+ | @unit |
| Utils | {{UNIT_TEST_TOOL}} | 95%+ | @unit |

### 10.3 E2E 測試覆蓋

| 流程 | 工具 | 覆蓋 Screen | 優先度 |
|------|------|------------|-------|
| 登入流程 | {{E2E_TOOL}} | SCR-001 | P0 |
| 主要功能流程 | {{E2E_TOOL}} | SCR-002~SCR-003 | P0 |
| {{FLOW}} | {{E2E_TOOL}} | {{SCREENS}} | {{PRIORITY}} |

### 10.4 Visual Regression

| 工具 | 快照目標 | 閾值 |
|------|---------|------|
| {{VISUAL_TEST_TOOL}} | 關鍵 Screens × 3 Breakpoints | <0.1% diff |

### 10.5 Cross-browser 自動化

| 工具 | 涵蓋瀏覽器 | CI 觸發條件 |
|------|-----------|-----------|
| {{CROSS_BROWSER_TOOL}} | Chrome, Firefox, Safari, Edge | PR merge |

---

## 11. Performance Budget

### 11.1 Bundle Size 上限

| 資源 | 上限（gzip） | 超出時行動 |
|------|------------|----------|
| 首頁 JS（initial chunk） | 150KB | 強制 code split |
| CSS | 30KB | 提取 critical CSS |
| 圖片（單張） | 200KB | 轉 WebP / AVIF |
| 總 initial load | 350KB | 拆包 / lazy load |

### 11.2 Core Web Vitals 目標

| 指標 | 目標 | 測量工具 |
|------|------|---------|
| LCP | < 2.5s | Lighthouse / WebPageTest |
| INP | < 200ms | Chrome UX Report |
| CLS | < 0.1 | Lighthouse |
| FCP | < 1.5s | Lighthouse |
| TBT | < 200ms | Lighthouse |

### 11.3 Asset 最佳化規則

| 資源類型 | 最佳化策略 |
|---------|----------|
| 圖片 | WebP 優先，fallback PNG；`loading="lazy"`；明確 width/height |
| 字型 | `font-display: swap`；subset；預載關鍵字型 |
| 影片 | 非必要不自動播放；poster 圖 |
| JS | Tree-shaking；Dynamic import；Preload 關鍵 chunk |

---

## 12. Frontend Security

### 12.1 XSS 防護

| 風險點 | 防護措施 |
|-------|---------|
| 動態 HTML 插入 | 禁用 `innerHTML`；必要時用 DOMPurify sanitize |
| 使用者輸入渲染 | 框架自動 escape（React/Vue JSX）；禁用 `dangerouslySetInnerHTML` |
| URL 參數渲染 | `encodeURIComponent()` 統一處理 |

### 12.2 Content Security Policy（CSP）

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-{RANDOM}' {{CDN_DOMAIN}};
  style-src 'self' 'unsafe-inline' {{FONT_CDN}};
  img-src 'self' data: https:;
  connect-src 'self' {{API_DOMAIN}};
  frame-src 'none';
  object-src 'none';
```

### 12.3 敏感資料處理

| 資料類型 | 禁止行為 | 正確處理 |
|---------|---------|---------|
| Access Token | 不存 localStorage（XSS 可竊） | httpOnly Cookie 或 memory only |
| 個資 | 不 console.log | 脫敏後才 log |
| 信用卡號 | 不暫存 | 僅透過 PCI DSS 合規第三方 |

---

## 13. Build & Bundle Configuration

### 13.1 Build 目標與指令

| 環境 | 指令 | 輸出目錄 | Source Map |
|------|------|---------|-----------|
| Development | `{{DEV_CMD}}` | `dist/dev` | 完整 |
| Staging | `{{STAGING_CMD}}` | `dist/staging` | External |
| Production | `{{PROD_CMD}}` | `dist/prod` | None |

### 13.2 環境變數規範

| 變數名稱 | 用途 | Dev 值 | Prod 值 |
|---------|------|--------|--------|
| `{{ENV_VAR_1}}` | API Base URL | `http://localhost:{{PORT}}` | `https://api.{{DOMAIN}}` |
| `{{ENV_VAR_2}}` | Feature Flag | `true` | `false` |

> ⚠️ 所有前端環境變數為**公開值**，嚴禁包含 API Secret、Private Key 等敏感資訊。

### 13.3 Code Splitting 策略

| 分割點 | 觸發方式 | 預載條件 |
|-------|---------|---------|
| Route-based | Dynamic import per page | 主要路由 prefetch |
| Feature-based | Dynamic import heavy libs | 使用者 hover 時 prefetch |
| Vendor chunk | SplitChunksPlugin | — |

---

## 14. Internationalization（i18n）

### 14.1 語言支援

| Locale | 語言 | 預設 | RTL |
|--------|------|------|-----|
| `zh-TW` | 繁體中文 | ✅ | ❌ |
| `en` | English | ❌ | ❌ |
| `{{LOCALE}}` | {{LANGUAGE}} | ❌ | {{RTL}} |

### 14.2 Translation Key 結構

```json
{
  "common": {
    "ok": "確認",
    "cancel": "取消",
    "loading": "載入中..."
  },
  "{{screen_id}}": {
    "title": "{{TITLE}}",
    "{{key}}": "{{VALUE}}"
  }
}
```

### 14.3 日期 / 數字格式

| 類型 | 格式化方式 | 範例 |
|------|----------|------|
| 日期 | `Intl.DateTimeFormat` | `2024/01/15` (zh-TW) |
| 貨幣 | `Intl.NumberFormat` | `NT$ 1,200` |
| 相對時間 | `Intl.RelativeTimeFormat` | `3 分鐘前` |

---

## 15. Appendix

### 15.1 前端資料夾結構

```
src/
├── components/          # 共用組件（Atoms/Molecules/Organisms）
│   ├── ui/              # 基礎 UI（Button, Input, Icon）
│   └── {{feature}}/     # 業務組件
├── pages/               # Page Components（對應路由）
├── hooks/               # Custom Hooks
├── services/            # API 呼叫層
├── stores/              # Global State
├── utils/               # 純函式工具
├── types/               # TypeScript 型別定義
├── styles/              # Global CSS / Design Tokens
├── locales/             # i18n JSON
└── assets/              # 靜態資源
```

### 15.2 Git Commit 規範（Frontend）

```
feat(frontend): 新增 {{SCREEN_NAME}} 畫面
fix(frontend): 修正 {{COMPONENT}} 在 Safari 的相容性問題
refactor(frontend): 重構 {{COMPONENT}} 使用 Composition API
test(frontend): 補充 {{COMPONENT}} 的 unit test
perf(frontend): 優化 {{SCREEN}} 首屏載入（LCP -0.5s）
```

---
