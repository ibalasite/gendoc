---
name: CLIENT_IMPL Review Rules
reviewer-roles:
  - Client Architect（主審：整體結構完整性、引擎一致性）
  - Engine Specialist（依偵測引擎：Cocos / Unity / React / Vue / HTML5 各自審查）
  - Performance Reviewer（效能 Budget 審查）
quality-bar: |
  - ENGINE 一致性：所有章節的實作細節均與 CLIENT_ENGINE 一致，無混用
  - 無裸 {{PLACEHOLDER}}
  - §3 有具體場景 / Node 樹結構
  - §5–§7 觸發表格有具體條目
  - §10 效能規範有具體數字
upstream-alignment:
  - EDD.md §3.3 客戶端引擎
  - ANIM.md 動畫清單
  - AUDIO.md 音效清單
  - VDD.md 特效清單
---

# CLIENT_IMPL Review Rules

---

## Review Protocol

1. **先讀 §1.1** 確認 `CLIENT_ENGINE`
2. **依引擎**執行對應的 Engine-Specific 審查項目（§3–§7）
3. **再執行**通用審查項目（§1–§2, §8–§12）
4. CRITICAL 未通過 → 停止後續低優先級審查，先要求修復

---

## Layer 0：通用審查項目（所有引擎）

### [CRITICAL] 0-A — ENGINE 欄位一致性

**Check**：`CLIENT_IMPL.md §1.1 CLIENT_ENGINE` 是否與 `EDD.md §3.3 客戶端引擎` 完全一致？

**Risk**：引擎不一致 → 所有引擎專用章節（場景結構、資源載入、AudioManager）全部錯誤，無法直接使用。

**Fix**：讀取 EDD.md §3.3，將 `CLIENT_ENGINE` 欄位更正為完全一致的值（包括版本號）。

---

### [CRITICAL] 0-B — §3.2 場景 / 視圖結構非空

**Check**：`§3.2` 是否有具體的樹狀結構（Node 樹 / Component 樹 / DOM 結構）？不允許「{{MAIN_SCENE_STRUCTURE}}」裸佔位符或「待補」。

**Risk**：§3.2 空白 → 開發人員無法得知場景怎麼組織，等同文件未完成。

**Fix**：依偵測到的 CLIENT_ENGINE，生成對應格式的樹狀結構（至少主場景 / 主頁面的完整層級）。

---

### [HIGH] 0-C — 無裸 {{PLACEHOLDER}}

**Check**：全文件是否有未填入的 `{{UPPERCASE}}` 佔位符（不含「格式範例佔位符：...」說明型）？

**Risk**：裸佔位符 → 開發人員看到未完成的欄位，不知道填什麼，文件可信度下降。

**Fix**：逐一填入具體值，或加上「格式範例佔位符：<說明>」說明型。

---

### [HIGH] 0-D — §4.3 資源載入策略符合引擎

**Check**：§4.3 的資源載入方式是否使用了正確的引擎 API？
- Cocos：`cc.assetManager.loadBundle` / `resources.load`
- Unity：`Addressables.LoadAssetAsync` / `Resources.Load`
- React/Vue：`React.lazy` / `defineAsyncComponent` / `import()`
- HTML5：`new Image()` / Web Audio API `decodeAudioData`

**Risk**：使用錯誤的 API → 代碼無法運作。

**Fix**：依 CLIENT_ENGINE 替換為正確的引擎載入 API。

---

### [MEDIUM] 0-E — §10 效能規範有具體數字

**Check**：§10.1–§10.3 是否所有 `{{TARGET_FPS}}`, `{{LCP}}`, `{{MAX_BUNDLE}}` 等數字欄位都已填入？

**Risk**：無具體數字 → 開發人員不知道優化目標，無法進行效能測試。

**Fix**：依引擎類型填入合理預設值（遊戲：60fps；Web：LCP < 2.5s；首包 < 200KB）。

---

### [LOW] 0-F — §12 已知限制有填入

**Check**：§12 是否至少有 1 條已知限制或技術債（或明確標注「暫無」）？

**Risk**：完全跳過此章節 → 讀者不知道是真的沒有限制，還是沒有思考過。

**Fix**：從上游文件提取技術風險，或填入「暫無已知限制（首版）」。

---

## Layer 1：Cocos Creator 專用審查項目

> 僅當 `CLIENT_ENGINE = Cocos Creator` 時執行

### [CRITICAL] CC-1 — Node 樹使用 Cocos 格式

**Check**：§3.2 的樹狀結構是否使用 Cocos Node 命名（`cc.Node`, `cc.Sprite`, `cc.Label`, `cc.Button`, `AnimationComponent`, `cc.ParticleSystem`）？

**Risk**：使用 React/HTML 格式的結構 → 開發人員無法直接對應 Cocos 的 Hierarchy 面板。

**Fix**：將 §3.2 改為 Cocos Node 樹格式，標注每個 Node 的主要 Component。

---

### [HIGH] CC-2 — §4 有 Asset Bundle 分包規劃

**Check**：§4.1 目錄結構是否包含 `bundles/` 目錄，且 §4.3 載入策略有區分「首包」和「分包」？

**Risk**：沒有分包規劃 → 遊戲首次載入時間過長（Web 平台尤其嚴重）。

**Fix**：在 §4.1 加入 `assets/bundles/` 分包結構，§4.3 補充 `cc.assetManager.loadBundle` 異步載入策略。

---

### [HIGH] CC-3 — §6.3 有 AudioManager（cc.AudioSource 管理）

**Check**：§6.3 是否描述了基於 `cc.AudioSource` 的 AudioManager 架構，且有 BGM / SFX 分離管理？

**Risk**：沒有 AudioManager → 每個場景重複音效邏輯，BGM 在場景切換時中斷。

**Fix**：在 §6.3 補充 Cocos AudioManager.ts 設計（cc.AudioSource pool、跨場景保活策略）。

---

### [MEDIUM] CC-4 — §5.2 動畫觸發使用正確事件機制

**Check**：§5.2 是否使用 `cc.EventTarget` / `this.node.on()` / `AnimationClip.events` 事件機制，而非直接函數呼叫？

**Risk**：直接呼叫方式 → 緊耦合，無法在動畫中間插入觸發點。

**Fix**：更新 §5.2 觸發方式為事件驅動（`node.emit` / `node.on`）。

---

### [MEDIUM] CC-5 — §7 特效使用 Prefab + Object Pool

**Check**：§7.2 特效觸發方式是否提到 `cc.instantiate(prefab)` + `node.destroy()` 或 Object Pool？

**Risk**：每次特效都 `new cc.Node()` → GC 抖動，遊戲卡頓。

**Fix**：在 §7.2 補充使用 Prefab 實例化 + Object Pool 回收說明。

---

## Layer 2：Unity WebGL 專用審查項目

> 僅當 `CLIENT_ENGINE = Unity WebGL` 時執行

### [CRITICAL] UN-1 — §3.2 使用 Unity Hierarchy 格式

**Check**：§3.2 是否使用 `[Scene: Name]` + `GameObject (Component.cs)` 格式，而非 cc.Node 或 HTML DOM 格式？

**Risk**：格式錯誤 → 開發人員無法對應 Unity Hierarchy 面板。

**Fix**：改為 Unity GameObject 層級格式，標注 MonoBehaviour 腳本。

---

### [HIGH] UN-2 — §6.3 有 AudioMixer 設計

**Check**：§6.3 是否描述了 AudioMixer 的分組（Master / BGM / SFX），以及音量控制的 `AudioMixer.SetFloat` 實作？

**Risk**：沒有 AudioMixer → 無法獨立控制 BGM / SFX 音量，無法做淡入淡出。

**Fix**：在 §6.3 補充 AudioMixer Group 設計和 AudioManager.cs Singleton 架構。

---

### [HIGH] UN-3 — §4.3 提及 Addressable Asset System（或 Resources）

**Check**：§4.3 是否說明了動態資源載入使用 `Addressables` 或 `Resources.Load`？

**Risk**：WebGL 包體過大 → 首次載入超過 10MB，使用者放棄。

**Fix**：在 §4.3 補充 Addressable Remote Group 或 Resources 動態載入策略。

---

### [MEDIUM] UN-4 — §5.2 動畫觸發使用 Animator.SetTrigger / SetBool

**Check**：§5.2 是否使用正確的 Animator 參數觸發方式？

**Fix**：更新為 `animator.SetTrigger("name")` / `animator.SetFloat("speed", val)` 模式。

---

## Layer 3：React 專用審查項目

> 僅當 `CLIENT_ENGINE = React` 時執行

### [CRITICAL] RE-1 — §3.2 使用 JSX 組件樹格式

**Check**：§3.2 是否使用 `<ComponentName>` JSX 格式，而非 cc.Node 或 HTML DOM 格式？每個組件是否標注對應 `.tsx` 文件路徑？

**Risk**：格式錯誤 → 開發人員無法建立組件文件。

**Fix**：改為 JSX 組件樹格式，標注文件路徑（e.g. `components/GameCard.tsx`）。

---

### [HIGH] RE-2 — §2.1 有 pages/ + components/ + store/ 分層

**Check**：§2.1 目錄結構是否有明確的 `pages/`（路由）、`components/`（可複用 UI）、`store/`（狀態管理）三層分離？

**Risk**：沒有分層 → 大型項目難以維護，路由頁面和業務邏輯混在一起。

**Fix**：補充三層目錄結構，說明各目錄的職責範圍。

---

### [HIGH] RE-3 — §4.3 有 Code Splitting（React.lazy）

**Check**：§4.3 是否提到路由頁面使用 `React.lazy` + `Suspense` 懶加載？

**Risk**：沒有 Code Splitting → Entry Bundle 過大，TTI 超標。

**Fix**：在 §4.3 補充 `React.lazy(() => import('./pages/GamePage'))` 路由懶加載策略。

---

### [MEDIUM] RE-4 — §5.2 動畫庫選型有說明

**Check**：§5.2 是否明確說明使用哪個動畫庫（Framer Motion / GSAP / CSS Modules / CSS-in-JS），且觸發方式一致？

**Fix**：統一說明動畫庫選型並給出觸發範例。

---

### [MEDIUM] RE-5 — §10 有 LCP / TTI / Bundle 具體目標

**Check**：§10.1 是否有 LCP、TTI 目標；§10.3 是否有 Entry Bundle 大小限制？

**Fix**：填入 LCP < 2.5s、TTI < 3.5s、Entry Bundle < 200KB gzip 等 Web 標準目標值。

---

## Layer 4：Vue 專用審查項目

> 僅當 `CLIENT_ENGINE = Vue` 時執行

### [CRITICAL] VU-1 — §3.2 使用 Vue SFC 組件樹格式

**Check**：§3.2 是否使用 `<ComponentName.vue>` 格式？是否標注 `views/`（路由）和 `components/`（可複用）的區別？

**Risk**：格式錯誤 → 開發人員無法建立 `.vue` 文件。

**Fix**：改為 Vue SFC 組件樹格式，區分 view（頁面）和 component（可複用組件）。

---

### [HIGH] VU-2 — §2.1 有 stores/（Pinia）+ composables/ 分層

**Check**：§2.1 是否有 `stores/`（Pinia 狀態管理）和 `composables/`（可複用邏輯）目錄？

**Risk**：沒有明確的狀態管理層 → 響應式狀態散落各組件，難以除錯。

**Fix**：補充 `stores/` 和 `composables/` 目錄及其職責說明。

---

### [HIGH] VU-3 — §4.3 有 defineAsyncComponent 懶加載

**Check**：§4.3 是否提到使用 `defineAsyncComponent` 或 `import()` 做路由組件懶加載？

**Fix**：補充 Vue Router 的 `component: () => import('./views/GameView.vue')` 懶加載策略。

---

### [MEDIUM] VU-4 — §5.2 動畫使用 Vue Transition 或明確動畫庫

**Check**：§5.2 是否說明 Vue `<Transition>` / `<TransitionGroup>` 的使用時機，或指定動畫庫？

**Fix**：說明 `<Transition name="slide">` + CSS class 或 GSAP 整合方式。

---

## Layer 5：HTML5 專用審查項目

> 僅當 `CLIENT_ENGINE = HTML5` 時執行

### [CRITICAL] H5-1 — §3.2 使用 DOM 結構格式

**Check**：§3.2 是否使用 HTML element 層級格式（`<div id>` / `<canvas>` / `<section>`），而非組件樹或 Node 樹格式？

**Risk**：格式錯誤 → 開發人員不知道實際 DOM 結構。

**Fix**：改為 HTML DOM 層級格式，標注每個元素的 ID / class 和用途。

---

### [HIGH] H5-2 — §6.3 使用 Web Audio API 或 Howler.js

**Check**：§6.3 是否說明使用 `Web Audio API`（AudioContext）或 `Howler.js`，而非直接用 `<audio>` 標籤（後者有嚴重的瀏覽器限制）？

**Risk**：直接用 `<audio>` → 移動瀏覽器播放限制、無法做音量漸變、多音效同播問題。

**Fix**：更新 §6.3 為 Web Audio API 或 Howler.js 架構設計。

---

### [HIGH] H5-3 — §4.3 有 Preload Manager 設計

**Check**：§4.3 是否說明了圖片和音效的預載機制（`new Image()` + `onload` 計數，或 Preload Manager class）？

**Risk**：沒有預載 → 遊戲開始後資源仍在載入，出現空白 / 無聲。

**Fix**：在 §4.3 補充 Preload Manager 設計（Queue + Progress Callback 模式）。

---

### [MEDIUM] H5-4 — §5.2 動畫觸發使用 rAF 或 Web Animations API

**Check**：§5.2 是否使用 `requestAnimationFrame` 遊戲循環或 `element.animate()` Web Animations API，而非 setTimeout？

**Fix**：更新觸發方式為 `requestAnimationFrame` 或 `element.animate()`。

---

## Review Output Format

```
REVIEW_RESULT:
  step_id: CLIENT_IMPL
  type: CLIENT_IMPL
  round: {round}
  finding_total: N
  critical: N
  high: N
  medium: N
  low: N
  passed: true|false
  findings:
    - id: F-{N:02d}
      severity: CRITICAL|HIGH|MEDIUM|LOW
      item_ref: "[層] 審查項 ID — 標題"
      section: "§X.Y"
      issue: "具體問題描述（引用文件內容）"
      fix_guide: "Fix 指引（來自本 review.md 對應 item 的 Fix 段落）"
```
