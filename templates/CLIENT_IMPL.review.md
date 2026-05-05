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
  - §5 動畫觸發表格有至少 3 條觸發事件（若 ANIM.md 存在）
  - §6 音效觸發表格有至少 3 條觸發事件（若 AUDIO.md 存在）
  - §4.4 資源 Budget 四欄均有具體數字（不允許「待定」）
  - §9.3 離線/弱網三場景策略已填入（非裸 {{OFFLINE_STRATEGY}}）
  - §10 效能規範有具體數字
upstream-alignment:
  - EDD.md §3.3 客戶端引擎
  - ANIM.md 動畫清單
  - AUDIO.md 音效清單
  - VDD.md 特效清單
  - ARCH.md §API端點清單 → §9 API 整合規格
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

**Check**：
1. `CLIENT_IMPL.md §1.1 CLIENT_ENGINE` 是否與 `EDD.md §3.3 客戶端引擎` 完全一致？
2. `ENGINE_VERSION` 欄位是否填入具體版本號（例如 Cocos Creator 3.8.x、Unity 2022.3 LTS、React 18.x），而非留裸佔位符或泛稱「最新版」？
3. §2–§7 中的代碼範例 API 是否與 `ENGINE_VERSION` 一致？（例如 Cocos 3.x 應使用 `cc.assetManager` 而非已棄用的 `cc.loader`；Unity 2022.3 使用 URP / Addressables 2.x；React 18.x 使用 `createRoot` 而非 `ReactDOM.render`）

**Risk**：引擎不一致或版本號缺失 → 所有引擎專用章節（場景結構、資源載入、AudioManager）全部錯誤，且不同大版本間 API 差異極大（尤其 Cocos 2.x → 3.x），代碼範例無法直接使用。

**Fix**：讀取 EDD.md §3.3，將 `CLIENT_ENGINE` 和 `ENGINE_VERSION` 欄位更正為完全一致的具體值；逐一檢查 §2–§7 代碼範例中的 API，依版本替換為正確的引擎 API。

---

### [CRITICAL] 0-B — §3.2 場景 / 視圖結構非空

**Check**：`§3.2` 是否有具體的樹狀結構（Node 樹 / Component 樹 / DOM 結構）？不允許「{{MAIN_SCENE_STRUCTURE}}」裸佔位符或「待補」。

**Risk**：§3.2 空白 → 開發人員無法得知場景怎麼組織，等同文件未完成。

**Fix**：依偵測到的 CLIENT_ENGINE，生成對應格式的樹狀結構（至少主場景 / 主頁面的完整層級）。

---

### [CRITICAL] 0-C — 無裸 {{PLACEHOLDER}}

**Check**：全文件是否有未填入的 `{{UPPERCASE}}` 佔位符（不含「格式範例佔位符：...」說明型）？

**Risk**：裸佔位符 → 開發人員看到未完成的欄位，不知道填什麼，文件可信度下降；與 quality-bar「所有 §章節無裸 {{PLACEHOLDER}}」等同 CRITICAL 條件。

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

### [HIGH] 0-E — §10 效能規範有具體數字

**Check**：§10.1–§10.3 是否所有 `{{TARGET_FPS}}`, `{{LCP}}`, `{{MAX_BUNDLE}}` 等數字欄位都已填入？

**Risk**：無具體數字 → 開發人員不知道優化目標，無法進行效能測試；§10 效能規範屬 quality-bar 必要條件，數字空缺等同文件未完成。

**Fix**：依引擎類型填入合理預設值（遊戲：60fps；Web：LCP < 2.5s；首包 < 200KB）。

---

### [HIGH] 0-F — §4.4 資源 Budget 有具體數字

**Check**：§4.4 資源 Budget 表格的「單張貼圖」「音效（SFX）」「背景音樂」「總包體大小」欄位是否都已填入具體數字（不允許「待定」或裸佔位符）？

**Risk**：無具體 Budget → 美術資源無從控制規格，包體超限時才發現已難以修復。

**Fix**：依引擎填入對應預設值（參見 gen.md §4.4 資源 Budget 生成規則），確認 §4.4 每欄均有具體數字。

---

### [HIGH] 0-G — §8 UI 狀態機完整性

**Check**：
1. §8.1 UI 狀態清單是否有 ≥ 3 個狀態（且必須包含 Loading、Error、NetworkLost）？
2. §8.3 Loading / Error / Network Lost 各列的「逾時處理（TIMEOUT）」和「重試策略（RETRY）」欄位是否已填入具體策略（非裸佔位符）？

**Risk**：缺少錯誤狀態 → 網路異常時無 fallback UI，使用者看到空白畫面。

**Fix**：在 §8.1 補充 Loading、Error、NetworkLost 三個狀態；在 §8.3 補充逾時秒數（如 10s）和重試策略（如「最多 3 次，間隔 2s 指數退避」）。

---

### [HIGH] 0-H — §9 API 整合有具體內容

**Check**：
1. §9.1 API 呼叫清單是否有 ≥ 1 條具體 API（非裸 `{{API_NAME}}` 佔位符）？
2. §9.3 離線 / 弱網處理是否已填入具體策略（非裸 `{{OFFLINE_STRATEGY}}`）？

**Risk**：API 清單空白 → 開發人員不知道需要整合哪些後端端點；離線策略缺失 → 弱網環境崩潰無 fallback。

**Fix**：從 ARCH.md 或 EDD §4 提取至少 1 條 API 端點；§9.3 填入離線 / 弱網處理策略（可參照 §9.3 格式提示表格）。

---

### [MEDIUM] 0-I — §5.1 / §6.1 / §7.1 清單非空（若上游存在）

**Check**：若 ANIM.md / AUDIO.md / VDD.md 存在，對應的 §5.1 動畫清單 / §6.1 音效清單 / §7.1 特效清單是否有至少 1 條具體條目（非裸佔位符）？

**Risk**：清單空白但上游有資料 → 開發人員需重新查找上游文件，CLIENT_IMPL.md 失去整合價值。

**Fix**：從對應上游文件提取清單條目填入；若上游文件確實不存在，在章節頂部加「<!-- 上游 ANIM.md / AUDIO.md / VDD.md 不存在，本章節留空 -->」標注。

---

### [MEDIUM] 0-J — §11.2 整合測試清單有具體場景

**Check**：§11.2 整合測試清單是否有 ≥ 3 條具體測試場景（含前置條件和預期結果），而非裸佔位符？

**Risk**：測試清單空白 → QA 無法依文件執行測試，品質無從保障。

**Fix**：從 EDD 功能模組推斷至少 3 個端到端整合場景（如：載入流程、API 呼叫錯誤回復、場景切換音效觸發）。

---

### [MEDIUM] 0-K — §5.2 / §6.2 / §7.2 觸發表各有具體條目

**Check**：§5.2 動畫觸發事件表格是否有 ≥ 3 條具體條目（若 ANIM.md 存在）？§6.2 音效觸發事件表格是否有 ≥ 3 條？§7.2 特效觸發對應表是否有 ≥ 3 條？

**Risk**：觸發表空白 → 開發人員無法得知哪些事件需要播放音效 / 特效，容易遺漏。

**Fix**：從 AUDIO.md / VDD.md 提取觸發條目；若上游不存在，填入至少 3 條推斷的代表性觸發場景（如：按鈕點擊 → sfx_ui_click、勝利事件 → sfx_win 等）。

---

### [MEDIUM] 0-L — §5.3 / §5.4 / §6.4 / §7.3 效能與狀態機規格完整性

**Check**：
1. §5.3 是否有具體的狀態轉換圖或文字圖（非裸 `{{ANIMATION_STATE_MACHINE}}` 佔位符）？
2. §5.4 同屏動畫數上限、骨骼/層數上限是否均有具體數字？
3. §6.4 同時播放 SFX 上限、音效快取大小是否均有具體數字？
4. §7.3 同屏特效數上限、粒子數上限是否均有具體數字？

**Risk**：裸 Placeholder 或缺少數字 → 開發人員無從得知效能限制與狀態機設計，無法實作與測試；動畫狀態機缺失尤其影響遊戲類專案的邏輯正確性。

**Fix**：補充具體數字或狀態圖，參照 gen.md §5.3 / §5.4 / §6.4 / §7.3 生成規則填入對應引擎的預設值。

---

### [LOW] 0-M — §12 已知限制有填入

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

> **通過判定**：`passed: true` 當且僅當 finding 中無 CRITICAL 項；有任何 CRITICAL 項則 `passed: false`（HIGH 項記錄但不阻止通過，需在下一輪追蹤修復）。

```
REVIEW_RESULT:
  step_id: CLIENT_IMPL  # pipeline 步驟唯一識別碼，固定填 CLIENT_IMPL
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


---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/CLIENT_IMPL.md`，提取所有 `^## ` heading（含條件章節），共約 14 個
2. 讀取 `docs/CLIENT_IMPL.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
