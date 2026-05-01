---
doc-type: PDD
output-path: docs/PDD.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
quality-bar: "含 User Personas（≥2 個）、User Journey Map（5 階段）、JTBD（3 類）、Service Blueprint、WCAG 2.1 AA 合規矩陣（12 準則）、Dark Mode Token Mapping（≥13 tokens）、Motion Design Spec（easing 函數 + prefers-reduced-motion）、Engineering Handoff Checklist（含 Figma link + ≥4 states per interactive component）、Design Token 三層架構；所有章節均需有具體內容，不得留空或填 placeholder。"
---

# PDD 生成規則

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## 上游讀取規則

- `docs/IDEA.md`：了解產品核心概念、目標市場與初始假設
- `docs/BRD.md`：了解業務需求、成功指標與範疇定義
- `docs/PRD.md`：主要輸入，偵測 Client 類型，讀取 User Personas、User Stories、AC

**注意**：PDD 不讀取 EDD.md（EDD 是 PDD 的下游，DB Schema 需依照 PDD 畫面欄位設計）

### docs/req/ 素材關聯讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與 PDD 相關的檔案。
對每個存在的 `docs/req/` 檔案，讀取全文，結合 Appendix C「應用於」欄位標有「PDD §」的段落，作為生成 PDD 對應章節（UI 設計、畫面欄位、互動流程）的補充依據。優先採用素材原文描述，而非 AI 推斷。若無引用，靜默跳過。

---

## Client 類型偵測

讀取 `docs/PRD.md`，依以下優先順序偵測 Client 類型：

1. PRD 中明確提到 Unity / UnityEngine → `unity`
2. PRD 中明確提到 Cocos Creator / cc.Node → `cocos`
3. PRD 中明確提到 Canvas / WebGL / Phaser / PixiJS → `html5-game`
4. PRD 中有 UI Component / 前端 / React / Vue / SPA → `web-saas`
5. 純 API / CLI / 後端服務，無 UI → `none`（不生成 PDD）

---

## Platform Scope Declaration

在 PDD 文件最開頭（Document Control 前）寫入：

```markdown
<!-- ⚠️ Platform Scope — 本文件適用範圍 -->
- [x] Web（Browser）
- [ ] iOS Native
- [ ] Android Native
- [ ] Desktop App
- [ ] Game UI
```

依偵測結果勾選對應平台。

---

## 章節結構（所有 Client 類型通用基礎）

Document Control + Platform Scope Declaration 之後，依序包含：

- §1 Design Brief（§1.1 設計目標 + §1.2 PRD 需求對應 + §1.3 Design Principles；Client 技術棧偵測結果記錄於 Platform Scope Declaration）
- §2 User Research Summary（§2.0 User Personas 5-field 卡片 + §2.4 User Journey Map 5 階段情緒圖 + §2.5 JTBD + §2.6 Service Blueprint 5 層視角）
- §3 Information Architecture（§3.1 Sitemap 樹狀圖 + §3.2 導覽模式 + §3.3 Content Priority F/Z Pattern）
- §4 User Flows（§4.1 主流程 Happy Path + §4.2 替代流程 + §4.3 錯誤流程；含 Mermaid stateDiagram-v2）
- §5 Screen Specifications（每畫面的 Component 清單 + Wireframe 說明 + Props/States）
- §6 Interaction Design（含 §6.1.1 Motion Design Spec：easing 函數 + prefers-reduced-motion、§6.5 Micro-interaction Catalog、§6.6 Gesture & Touch Design、§6.7 Haptic Feedback Design）
- §7 Responsive & Adaptive Design（7 斷點 + 元件行為矩陣）
- §8 Accessibility（A11y）Specifications（§8.4 WCAG 2.1 AA 合規矩陣 12 準則 + 工具鏈）
- §9 Design System Reference（§9.3 Design Token 三層架構 + §9.4 Dark Mode Token Mapping 13 Token 含 WCAG 對比度 + §9.5 Client Class Diagram）
- §10 Copy & Content Design（§10.1 Tone of Voice + §10.2 關鍵文案清單 + §10.3 i18n 字串清單）
- §11 Prototype & Validation Plan（§11.1 Prototype 連結 + §11.2 設計驗證計畫）
- §12 Open Questions（設計待解問題）
- §13 Engineering Handoff Specification（Figma Handoff Checklist + Usability Testing Protocol）
- §14 References（含效能預算 Core Web Vitals 目標：LCP/INP/CLS + JS Bundle Budget）
- §15 Approval Sign-off（Design Lead + PM + Engineering Lead 簽核表）
- Appendix：BDD 連結、Screen Inventory

---

## Key Fields — Web SaaS / HTML5

### §1 Client 技術棧

- 確認前端框架（React / Vue / Svelte / Vanilla JS）
- 狀態管理方案
- Build 工具（Vite / Webpack）
- CSS 方案（CSS Modules / Tailwind / styled-components）

### §2 User Personas（5-field 卡片）

每個 Persona 生成詳細卡片：

| 欄位 | Persona A | Persona B |
|------|-----------|-----------|
| 姓名 | <AI 推斷的代表性名字> | <AI 推斷> |
| 年齡 / 職業 | <基於 PRD Persona 資料> | <基於 PRD> |
| 技術熟悉度 | <低 / 中 / 高> | <低 / 中 / 高> |
| 使用情境 | <具體情境描述> | <具體情境描述> |
| 核心目標 | <基於 PRD User Story> | <基於 PRD> |
| 主要痛點 | <來自 BRD §2> | <來自 BRD §2> |
| 成功時感受 | <情感描述> | <情感描述> |
| 代表引言 | 「<假設語錄>」 | 「<假設語錄>」 |

### §2.4 User Journey Map（5 階段）

| 階段 | 觸達 | 探索 | 使用 | 達成目標 | 回訪 |
|------|------|------|------|---------|------|
| 用戶行動 | <具體行動，基於 PRD UX Flow> | <行動> | <行動> | <行動> | <行動> |
| 想法 | <心理狀態> | <心理狀態> | <心理狀態> | <心理狀態> | <心理狀態> |
| 情緒 | 😐 中性 | 😟 擔憂 | 😊 滿意 | 😁 開心 | 😊 滿意 |
| 痛點 | <痛點（來自 BRD）> | <痛點> | - | - | - |
| 機會點 | <設計機會> | <設計機會> | <設計機會> | - | - |
| 接觸點 | 廣告/SEO | 首頁/Landing | <核心功能頁面> | <成功頁面> | 通知/Email |

### §2.5 Jobs to Be Done（JTBD）

核心 Job Statement：
> 當 [<基於 PRD 的使用情境>] 時，我希望能 [<核心功能目標>]，
> 讓我能夠 [<達成的業務價值>]。

| Job Type | Job Statement | 現有解法（競品）| 不滿意程度（1-5）|
|----------|--------------|--------------|----------------|
| Functional | <基於 PRD P0 功能的 Job> | <競品現有解法> | <AI 推斷 4-5> |
| Emotional | <情感性 Job（如「感覺有掌控感」）> | <現有解法> | <3-4> |
| Social | <社交性 Job（如「向同事展示效率」）> | <現有解法> | <3-4> |

### §2.6 Service Blueprint（5 層視角）

| 行動類型 | 進入系統 | 核心功能使用 | 完成任務 |
|---------|---------|-----------|---------|
| **用戶行動** | 訪問首頁 | <核心操作，基於 PRD Happy Path> | 確認成功 |
| **前台 UI** | 登入頁面 | <關鍵畫面名稱> | 成功提示頁 |
| **後台流程** | Auth Service | <對應 EDD 服務層> | 結果儲存 |
| **支援系統** | OAuth / JWT | <資料庫 / 快取> | 通知服務 |
| **實體證據** | URL / 書籤 | <操作截圖 / 確認信> | 報告 / 回執 |

### §4 User Flows（主流程 / 替代流程 / 錯誤流程）

**§4.1 主流程 Happy Path**（Mermaid stateDiagram-v2）：
- 涵蓋 PRD 每個 User Story 的主要頁面流程
- 使用 Mermaid stateDiagram-v2，每個狀態對應真實畫面名稱

**§4.2 替代流程 + §4.3 錯誤流程**：
- 錯誤狀態、Loading 狀態都要有
- 每條 transition 都要標示觸發事件
- **禁止** 在 transition label 使用 `<br/>`（`stateDiagram-v2` 不支援，Safari/Firefox 破圖）；換行說明移到 `note right of STATE` 區塊

### §5 Screen Specifications（UI Component / Screen 清單）

- 每個 Screen 名稱 + 路由
- 每個 Component：名稱、用途、Props 清單、States（Default / Hover / Focus / Disabled / Error）

### §9 Design System Reference（Design Tokens）

```
Color: Primary / Secondary / Error / Warning / Success / Neutral
Typography: H1~H6 / Body / Caption（字型、大小、行高）
Spacing: 4px 基準 Grid System
Border Radius / Shadow / Transition Duration
```

### §7 響應式 Breakpoints

- 320（Mobile S）/ 375（Mobile M）/ 768（Tablet）/ 1024（Desktop S）/ 1440（Desktop L）
- 每個 Breakpoint 的 Layout 策略

### §8 Accessibility 規範

- WCAG 2.1 AA 對比度要求
- keyboard navigation 支援
- ARIA label 規範
- Screen Reader 測試重點

### §6.5 Micro-interaction Catalog

| 觸發器 | 規則 | 回饋 | 迴圈 |
|--------|------|------|------|
| 按鈕點擊 | 僅在可點擊狀態下觸發 | Scale 0.95 + 顏色加深 | 放開後 150ms 恢復 |
| 表單送出成功 | 所有 AC 通過後 | Checkmark 動畫 + Green Toast | 3s 後 Toast 消失 |
| 表單送出失敗 | 驗證未通過 | Inline 紅色錯誤訊息 + Shake 動畫 | 用戶修正後恢復 |
| 數值計數器 | 點擊 +/- 按鈕 | 數字翻動動畫（150ms）| 達到上下限時 disable |
| 載入中 | API 呼叫期間 | Skeleton Screen（非 Spinner）| 資料回傳後漸入 |
| 喜愛/收藏 | 點擊心形按鈕 | Heart fill + 爆炸粒子效果 | 再次點擊取消 |
| 刪除確認 | 點擊刪除 | Shake + 確認對話框 | 確認後 Collapse 動畫 |
| <基於 PRD 特有功能> | <規則> | <回饋> | <迴圈> |

### §6.6 Gesture & Touch Design（若有 Mobile 需求）

若 PRD 包含 Mobile 或 PWA 需求，生成以下規格：

| 手勢 | 觸發條件 | 動作回應 | 視覺回饋 | 衝突處理 |
|------|---------|---------|---------|---------|
| 單指點擊 | 點擊互動元件 | 主要操作 | Ripple Effect | 無 |
| 長按 | 600ms 持壓 | Context Menu 出現 | Haptic + Scale 略大 | 優先於點擊 |
| 左右滑動 | 水平位移 > 30px | 切換卡片/Tab | Translate + Fade | 阻止垂直滾動 |
| 下拉更新 | 從頂部向下拉 > 60px | 觸發資料刷新 | Pull 動畫 + Spinner | 頁面到頂才啟用 |
| Pinch Zoom | 雙指縮放 | 縮放圖片/地圖 | Scale Transform | 僅特定元件啟用 |

最小觸控目標：44×44px（iOS HIG / Material Design 規範）

### §14 References（含效能預算）

**效能預算（Core Web Vitals 目標）**：
- LCP < 2.5s / INP < 200ms / CLS < 0.1
- JS Bundle < 300kb gzipped
- 圖片最大尺寸 / format（AVIF / WebP）

**References**：列出設計參考來源（Figma link、設計規範、競品分析報告等）。

### §13 Engineering Handoff Specification

#### §13.1 Figma Handoff Checklist（開發前必須全部完成）

- [ ] 所有畫面均有 Default / Hover / Focus / Disabled / Error 5 種狀態
- [ ] 空狀態（Empty State）已設計
- [ ] Loading / Skeleton 狀態已設計
- [ ] 所有 Design Token 已命名並與開發命名對齊
- [ ] Mobile / Desktop Breakpoint 均已設計
- [ ] 動畫規格（timing / easing curve）已標注
- [ ] 圖示已 Export 為 SVG 或加入 Icon Library
- [ ] 文案已最終定稿（無 Lorem Ipsum）
- [ ] Accessibility Annotation（焦點順序、ARIA 標注）已完成
- [ ] 與工程師完成 Design Review 同步

#### §9.3 Design Token 三層架構

```
Layer 1 — Primitive（原始值）：
  color-blue-500: #3B82F6
  font-size-16: 16px
  space-4: 4px

Layer 2 — Semantic（語意，引用 Primitive）：
  color-action-primary → color-blue-500
  color-feedback-error → color-red-500
  spacing-component-gap → space-4

Layer 3 — Component（元件，引用 Semantic）：
  button-primary-bg → color-action-primary
  button-primary-padding → spacing-component-gap
```

#### §13.2 Usability Testing Protocol

| 階段 | 方法 | 時機 | 參與者 | 成功標準 |
|------|------|------|--------|---------|
| Concept Test | 5-second Test | Wireframe 完成後 | 5人（目標 Persona）| 核心概念理解率 ≥ 80% |
| Prototype Test | Task-based Test | High-fi 完成後 | 5人 | Task Completion ≥ 80%；SUS ≥ 68 |
| Beta Test | Unmoderated Remote | 上線前 Beta | 20人 | CSAT ≥ 4.0/5.0 |

#### §13.3 A/B Test Design Template

| 欄位 | 內容 |
|------|------|
| 假設 | 若 [設計變更]，則 [指標] 將提升 [幅度]，因為 [理由] |
| 控制組（A） | 現有設計 |
| 實驗組（B） | <待測試的設計變體> |
| 主要指標 | <CTR / Task Completion Rate / CSAT>（p < 0.05）|
| 護欄指標 | Error Rate（不得上升）|
| 最小樣本量 | <N>（統計功效 80%，顯著水準 5%）|
| 測試時長 | 最少 2 週 |

---

## Key Fields — Unity 遊戲

### §2 WYSIWYG 設計原則（必填）

> 所有 UI 元件必須直接存在於 `.unity` Scene 或 `.prefab`，美術打開 Unity Editor 立即看到完整畫面，不允許 script 以 `new GameObject()` 動態生成 UI。

- **靜態 UI 元件**（Button、Text、Image、Panel）：直接在 Scene Hierarchy 預置
- **動態元件**（牌、玩家座位）：用 `.prefab` 資產，script 以 `Instantiate(prefab, parent)` 複製
- **Placeholder slot**：在 Scene 中放空 `GameObject`（`SetActive(false)` in Awake），命名如 `CardSlot_0`
- **禁止模式**：`new GameObject()` for UI、`setPosition()` for layout

**三層 script 架構**（不生成 SceneBuilder / 不動態建 UI）：
- `SceneWiring.cs`：只做 `transform.Find()` 找 UI ref + `Button.onClick.AddListener` 接線
- `UIController.cs`：`MonoBehaviour`，state 更新 + `DOTween` / coroutine 動畫
- `GameBootstrap.cs`：DI 配線 + Canvas Scaler 確認，掛在 Canvas 根節點

### §3 自適應 UI 規範（必填）

策略：`Canvas Scaler — Scale With Screen Size`（寬固定，高隨螢幕比例伸縮）

Canvas Scaler 設定：
```
UI Scale Mode: Scale With Screen Size
Reference Resolution: 1080 × 1920（直式 Portrait）
Screen Match Mode: Match Width Or Height
Match: 0（Match Width — 寬固定，高自動）
```

每個 UI section-level 物件必須設好 `RectTransform` 錨點，包含 Background（全拉伸）、TitleArea（頂部橫拉）、TableArea（全拉伸含 offsets）、HUDPanel（底部橫拉）、BettingPanel / ResultPanel（螢幕置中）。

### §4 Splash Screen 移除（必填）

- `ProjectSettings/ProjectSettings.asset`：`m_ShowUnitySplashScreen: 0`、`m_SplashScreenLogos: []`
- 非 Pro 授權：在 BootScene 加 `SplashSkip.cs`，Awake 立即跳轉

### §5 Scene Architecture Design（必填）

生成完整 Scene 清單與 Canvas Hierarchy，供後續 bake 使用，命名規則不得省略。

### §6 UI Component 清單

| GameObject 路徑 | 類型 | 說明 | 美術可替換 |
|----------------|------|------|:--------:|
| TitleArea/TitleText | TextMeshProUGUI | 遊戲名稱 | ✓ |
| HUDPanel/BalanceText | TextMeshProUGUI | 餘額顯示 | ✓ |
| （依 PRD 完整列出） | | | |

---

## Key Fields — Cocos Creator 遊戲

### §2 WYSIWYG 設計原則（必填）

> 所有 UI 節點必須直接 bake 進 `.scene` JSON，美術打開 Cocos Editor 立即看到完整畫面，不允許 script 動態生成 UI。

- **靜態 UI 節點**：Label、Button、Background、Panel 全部 pre-bake 進 `.scene`
- **動態元件**：以 `.prefab` 存檔，script 用 `instantiate(prefab)` 複製
- **禁止模式**：`new Node()` for UI、`addComponent(Label)` for layout

**三層 script 架構**（不生成 EditorSceneSetup）：
- `SceneWiring.ts`：只做 `getChildByName()` + Button 接線，不建節點
- `UIController.ts`：cc.Component，狀態更新 + `instantiate` + `tween`
- `GameBootstrap.ts`：DI 配線 + `view.setDesignResolutionSize`

### §3 自適應 UI 規範（必填）

策略：`FIXED_WIDTH`（寬固定 720，高隨螢幕比例自動伸縮）

```json
{
  "general": { "designWidth": 720, "designHeight": 1280, "fitWidth": false, "fitHeight": true },
  "splashScreen": { "totalTime": 0, "autoFit": true, "logo": null }
}
```

每個 section-level 節點必須有 `cc.Widget`（`_alignMode: 2` ON_WINDOW_RESIZE）。

### §6 Splash Screen 移除（必填）

- `settings/v2/packages/project.json`：`splashScreen.totalTime: 0`、`logo: null`
- `build-templates/web-desktop/index.html`：CSS 隱藏 `.powered-by-cocos`

---

## Section Rules

### §8.4 WCAG 2.1 AA 合規矩陣（12 準則）

以下 12 個標準均須涵蓋（M=Mandatory, R=Recommended）：

| # | 準則 | 類型 |
|---|------|------|
| 1.1.1 | Non-text Content | M |
| 1.4.3 | Contrast Minimum | M |
| 1.4.4 | Resize Text | M |
| 1.4.11 | Non-text Contrast | M |
| 2.1.1 | Keyboard | M |
| 2.4.3 | Focus Order | M |
| 2.4.7 | Focus Visible | M |
| 3.1.1 | Language of Page | M |
| 3.3.1 | Error Identification | M |
| 3.3.2 | Labels or Instructions | M |
| 4.1.2 | Name, Role, Value | M |
| 1.4.10 | Reflow | R |

測試工具：axe-core、Lighthouse ≥ 95、VoiceOver（Mac）、NVDA（Windows）

### §9.4 Dark Mode Token Mapping

至少 13 個 semantic token，每個 Token 有 Light + Dark 兩組值（無 hardcode hex），含 WCAG 對比度值。

### §6.1.1 Motion Design Spec

提供 easing 函數（cubic-bezier）+ duration + prefers-reduced-motion 替代方案。

### §10 Copy & Content Design

- §10.1 Tone of Voice
- §10.2 關鍵文案清單
- §10.3 i18n 字串清單

---

## Self-Check Checklist（生成前自我核查）

- [ ] Platform Scope Declaration 已聲明
- [ ] §1.2 PRD 需求對應表：PRD REQ-ID → PDD 對應章節的映射表是否已建立？
- [ ] §1.3 Design Principles：至少 3 條設計原則是否已明確定義？
- [ ] §2 User Personas：每個 Persona 有完整卡片（姓名/職業/技術度/使用頻率/決策角色）；至少 2 個
- [ ] §2 User Journey Map：5 階段（認知/考慮/採用/使用/推薦），含情緒曲線 + 痛點 + 機會點
- [ ] §2 JTBD：Functional + Emotional + Social 三類任務均已描述
- [ ] §3 Information Architecture：Sitemap 樹狀圖（§3.1）+ 導覽模式說明（§3.2）+ Content Priority（F/Z Pattern, §3.3）是否已生成？
- [ ] §6.1.1 Motion Design Spec：已提供 easing 函數（cubic-bezier）+ duration + prefers-reduced-motion 替代方案
- [ ] §6.7 Haptic Feedback Design：觸覺回饋設計是否已說明（Native App 才需要；Web 可標記 N/A）？
- [ ] §8.4 WCAG 2.1 AA 合規矩陣：12 個標準均已涵蓋
- [ ] §9.3 Design Token 三層架構（Primitive / Semantic / Component）已建立
- [ ] §9.4 Dark Mode Token Mapping：至少 13 個 semantic token，含 WCAG 對比度值
- [ ] §9.4 每個 Token 有 Light + Dark 兩組值（無 hardcode hex）
- [ ] §10 Copy & Content Design：Tone of Voice（§10.1）+ 關鍵文案清單（§10.2）+ i18n 字串清單（§10.3）是否已生成？
- [ ] §11 Prototype & Validation Plan：Prototype 連結（§11.1）+ 設計驗證計畫（§11.2）是否已填寫？
- [ ] §12 Open Questions：設計待解問題是否已列出？
- [ ] §13 Engineering Handoff Checklist：包含 Figma link、Component 狀態數（≥4 states per interactive component）
- [ ] §13 Design QA 驗收標準：有明確的通過/失敗標準
- [ ] §15 Approval Sign-off：Design Lead + PM + Engineering Lead 的簽核表是否已建立？
- [ ] User Journey Map 已完成
- [ ] JTBD（3 個 Job 類型）已定義
- [ ] Service Blueprint 已生成
- [ ] Engineering Handoff Checklist 已完成

若有遺漏，自行補齊後再寫入檔案。

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

> **讀取 lang_stack 方式**：`python3 -c "import json; print(json.load(open('.gendoc-state.json')).get('lang_stack','unknown'))"`

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| 所有 §章節齊全 | 對照 PDD.md 章節清單，無缺失章節 | 補寫缺失章節 |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | UI 框架/元件庫與 state.lang_stack 及 FRONTEND.md 一致 | 修正至一致 |
| 數值非 TBD/N/A | 所有尺寸、間距、字型大小、動畫時長填有實際數字 | 從 VDD §Typography/Spacing 提取填入 |
| 上游術語對齊 | 畫面名稱、流程步驟與 PRD §User Stories 一致 | 以 PRD 為準修正 |
| 使用者流程完整 | 每個主要 User Story 有對應的畫面流程圖（Mermaid flowchart），無斷點 | 補充缺失的流程節點 |

---

## Admin Portal 條件步驟（has_admin_backend=true 時執行）

```bash
_HAS_ADMIN=$(python3 -c "import json; d=json.load(open('.gendoc-state.json')); print('1' if d.get('has_admin_backend', False) else '0')" 2>/dev/null || echo "0")
echo "HAS_ADMIN: ${_HAS_ADMIN}"
```

若 `_HAS_ADMIN == "1"`，生成 PDD.md § 15 Admin Portal 產品設計章節：

**生成指引（逐節）：**

**§ 15.1 Admin Portal 定位與使用情境**
- 讀取 PRD.md § 19 Admin Backend Requirements（若已生成）→ 提取角色定義與存取方式
- 若 PRD § 19 尚未生成，從 PRD.md 的業務描述推斷 Admin 使用情境
- User Story 必須覆蓋 PRD § 19.4 的所有 Admin AC（至少 4 個 Stories）
- 讀取 EDD.md § 3.3 `_ADMIN_FRAMEWORK` 填入技術棧欄位

**§ 15.2 Admin Information Architecture**
- 讀取 ADMIN_IMPL.md § 4 路由設計（若已生成）→ 直接對應選單結構
- 若 ADMIN_IMPL 尚未生成，依 PRD § 19.3 業務功能清單推斷導覽節點
- 動態選單節點依 PRD § 19.3 的 P0 業務模組逐一列出

**§ 15.3 Admin 核心頁面 Wireframe 描述**
- 5 個固定頁面（登入 / Dashboard / 用戶管理 / 角色管理 / 稽核日誌）必須覆蓋
- 業務管理頁依 PRD § 19.3 展開（每個 P0 業務模組一個頁面描述）
- 每個頁面描述必須包含：Layout 結構 + 關鍵元件 + 主要互動行為

**§ 15.4 Admin UX 設計決策**
- 至少 5 條設計決策，每條含「決策 / 說明 / 理由」三欄
- 讀取 EDD.md § 3.3 `_ADMIN_FRAMEWORK` 確認技術棧，與決策保持一致

若 `_HAS_ADMIN == "0"`：
在 § 15 寫入：「本專案無 Admin 後台需求（has_admin_backend=false），略過 § 15 Admin Portal 設計章節。」

**Admin Portal 生成品質檢查（has_admin_backend=true 時追加至 Quality Gate）：**
- [ ] § 15.1 User Story 覆蓋 PRD § 19.4 所有 AC（若 PRD § 19 存在）
- [ ] § 15.2 IA 選單節點已依 PRD § 19.3 業務模組展開（無遺漏）
- [ ] § 15.3 5 個固定頁面均有 Wireframe 描述（登入/Dashboard/用戶/角色/稽核）
- [ ] § 15.4 至少 5 條 UX 設計決策，稽核日誌唯讀決策必含
- [ ] § 15.1 技術棧欄位與 EDD § 3.3 `_ADMIN_FRAMEWORK` 一致
