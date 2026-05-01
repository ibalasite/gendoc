---
name: CLIENT_IMPL Gen Rules
upstream-docs:
  - docs/EDD.md
  - docs/VDD.md
  - docs/ANIM.md
  - docs/AUDIO.md
  - docs/ARCH.md
output-path: docs/CLIENT_IMPL.md
quality-bar: |
  - 所有 §章節無裸 {{PLACEHOLDER}}（允許「格式範例佔位符：...」說明型）
  - §3 場景 / 頁面結構有具體的 Node 樹 / Component 樹（非空白）
  - §5 動畫觸發表格有至少 3 條觸發事件（若有 ANIM.md）
  - §6 音效觸發表格有至少 3 條觸發事件（若有 AUDIO.md）
  - §4 資源 Budget 有具體數字（非「待定」）
  - §10 效能規範有具體目標值
  - CLIENT_ENGINE 欄位已填入且與 EDD.md §3.3 一致
---

# CLIENT_IMPL Gen Rules

## Iron Law

**生成 CLIENT_IMPL.md 之前，必須先讀取 `CLIENT_IMPL.md`（結構）和本 `CLIENT_IMPL.gen.md`（生成規則）。**
**絕對不允許在未讀取上游文件（EDD / VDD / ANIM / AUDIO）的情況下生成。**

> **Admin 後台排除規則**：
> 若 `docs/EDD.md §3.3` 的 `_CLIENT_ENGINE` 為純 Admin/Vue3 後台（`_ADMIN_FRAMEWORK` 存在但無獨立 C 端前台），
> 則本 CLIENT_IMPL.md **不生成**，輸出說明：「本專案客戶端為 Vue3 Admin 後台，
> 已由 ADMIN_IMPL.md 涵蓋，CLIENT_IMPL.md 不適用，跳過。」
> 若同時有 C 端前台和 Admin 後台，則僅描述 C 端前台，不涵蓋 Admin 後台。

---

## 專家角色

| 角色 | 職責 |
|------|------|
| **Client Architect** | 主導者；讀取所有上游文件，決定 CLIENT_ENGINE，指揮各引擎專家 |
| **Cocos Creator Engineer** | CLIENT_ENGINE=Cocos 時：場景結構、Component、Bundle、Spine、AudioSource |
| **Unity WebGL Engineer** | CLIENT_ENGINE=Unity 時：GameObject 層級、MonoBehaviour、AudioMixer、Particle |
| **React Engineer** | CLIENT_ENGINE=React 時：Component 樹、Zustand/Redux、React Router、動畫庫 |
| **Vue Engineer** | CLIENT_ENGINE=Vue 時：SFC 組件樹、Pinia/Vuex、Vue Router、composables |
| **HTML5 Engineer** | CLIENT_ENGINE=HTML5 時：DOM 結構、純 CSS/JS、Web Audio API、Canvas/WebGL |

---

## Key Fields 提取表

| 欄位 | 來源 | 提取位置 | 不得留裸 {{}} |
|------|------|---------|------------|
| `CLIENT_ENGINE` | EDD.md | §3.3「客戶端引擎（若有）」| ✅ 必填 |
| `ENGINE_VERSION` | EDD.md | §3 技術棧表格 | ✅ 必填 |
| `TARGET_PLATFORM` | EDD.md | §3 技術棧 | ✅ 必填 |
| `PROJECT_NAME` | EDD.md | Document Control | ✅ 必填 |
| `LANGUAGE` | EDD.md | §3 技術棧 | ✅ 必填 |
| `BUILD_TOOL` | EDD.md | §3 建置工具 | ✅ 必填 |
| `API_INTEGRATION` | EDD.md / ARCH.md | §4 API 設計 | ✅ 必填 |
| 場景 / 頁面清單 | EDD.md / PDD.md | §5 功能模組 | ✅ 必填 |
| 動畫清單 | ANIM.md | §動畫清單章節 | ✅ 若有 ANIM.md |
| 音效清單 | AUDIO.md | §音效清單章節 | ✅ 若有 AUDIO.md |
| 特效清單 | VDD.md | §特效 / 粒子章節 | ✅ 若有 VDD.md |

---

## Step 0：ENGINE 偵測

讀取 EDD.md §3.3「客戶端引擎（若有）」欄位，設定 `_CLIENT_ENGINE`：

```bash
# 偵測邏輯（AI 解析 EDD.md）
if EDD §3.3 包含 "Cocos Creator"  → _CLIENT_ENGINE = "Cocos Creator"
if EDD §3.3 包含 "Unity"          → _CLIENT_ENGINE = "Unity WebGL"
if EDD §3.3 包含 "React"          → _CLIENT_ENGINE = "React"
if EDD §3.3 包含 "Vue"            → _CLIENT_ENGINE = "Vue"
if EDD §3.3 包含 "HTML5" 或 為空  → _CLIENT_ENGINE = "HTML5"
```

若 EDD.md §3.3 不存在或未填：
→ 查找 EDD.md §3 技術棧表格中任何「前端 / 客戶端」相關欄位
→ 若仍無法判斷，設為 `HTML5`（最保守預設），並在文件開頭加 `<!-- WARNING: CLIENT_ENGINE 未明確指定，預設 HTML5 -->`

---

## Step 1：讀取所有上游文件

1. **EDD.md**（必讀）— 提取：CLIENT_ENGINE、技術棧、API 設計、模組清單
2. **VDD.md**（選讀）— 提取：特效清單、視覺規格
3. **ANIM.md**（選讀）— 提取：動畫清單、狀態機設計
4. **AUDIO.md**（選讀）— 提取：音效清單、分類與觸發規格
5. **ARCH.md**（選讀）— 提取：整體架構、API 端點清單

上游文件不存在時：對應章節使用「格式範例佔位符」並標注來源缺失，繼續生成。

---

## Step 2：§1 客戶端概覽生成規則

- `CLIENT_ENGINE`：從 Step 0 取得，直接填入
- `ENGINE_VERSION`：從 EDD §3 技術棧提取；若不存在，填「請確認版本」
- `TARGET_PLATFORM`：從 EDD 提取；遊戲預設「Web（HTML5）」
- `LANGUAGE`：Cocos→TypeScript；Unity→C#；React/Vue→TypeScript；HTML5→JavaScript
- `BUILD_TOOL`：Cocos→「Cocos Builder」；Unity→「Unity Build」；React→「Vite / CRA」；Vue→「Vite」；HTML5→「手動 / Parcel」
- `API_INTEGRATION`：從 EDD §4 或 ARCH.md 提取；若無，推斷為 REST

---

## Step 3：§2 專案結構生成規則（5-way engine routing）

### Cocos Creator 路由

```
assets/
  scenes/          ← 各場景 .scene 文件（從 EDD 功能模組推斷）
  prefabs/
    ui/            ← UI 元素 Prefab
    gameplay/      ← 遊戲玩法 Prefab
    effects/       ← 特效 Prefab
  scripts/
    managers/      ← GameManager / AudioManager / UIManager
    gameplay/      ← 遊戲邏輯組件
    ui/            ← UI 組件
    utils/         ← 工具類
  resources/       ← 需動態載入的資源（cc.resources.load）
  bundles/
    core/          ← 核心資源（首包之外）
    level_{N}/     ← 各關卡分包
  textures/
    ui/
    characters/
    backgrounds/
    effects/
  audio/
    bgm/
    sfx/
    ui/
  animations/
  spine/
```

命名規範：
- 場景：`PascalCase.scene`（e.g. `GameMain.scene`）
- Script：`PascalCase.ts`（e.g. `PlayerController.ts`）
- Prefab：`PascalCase.prefab`（e.g. `EnemyBase.prefab`）
- 貼圖：`snake_case.png`（前綴：`ui_` / `char_` / `bg_` / `fx_`）

### Unity WebGL 路由

```
Assets/
  Scenes/          ← 各場景 .unity
  Scripts/
    Managers/      ← GameManager / AudioManager / SceneLoader
    Gameplay/
    UI/
    Utils/
  Prefabs/
    UI/
    Gameplay/
    Effects/
  Resources/       ← 需 Resources.Load 的資源
  Addressables/    ← 若用 Addressable Asset System
  Audio/
    Music/
    SFX/
  Textures/
  Animations/
  Materials/
  Shaders/
```

命名規範：
- 場景：`PascalCase.unity`
- Script：`PascalCase.cs`
- Prefab：`PascalCase.prefab`
- Asset：`PascalCase` 或 `snake_case`（依團隊慣例）

### React 路由

```
src/
  pages/           ← 路由對應頁面組件（/home → HomePage.tsx）
  components/
    common/        ← 通用 UI 組件
    layout/        ← 佈局組件
    feature/       ← 功能組件（按功能分組）
  store/           ← Zustand stores 或 Redux slices
  hooks/           ← 自訂 hooks
  services/        ← API 呼叫（axios / fetch）
  assets/
    images/
    audio/
    fonts/
  styles/
    global.css
    tokens.css
  utils/
  constants/
  types/           ← TypeScript 型別定義
```

命名規範：
- 頁面 / 組件：`PascalCase.tsx`
- Hook：`useCamelCase.ts`
- Store：`useCamelCaseStore.ts`
- Service：`camelCaseService.ts`
- CSS Module：`ComponentName.module.css`

### Vue 路由

```
src/
  views/           ← 路由對應頁面（router-view）
  components/
    common/
    layout/
    feature/
  stores/          ← Pinia stores
  composables/     ← 可複用邏輯（useXxx.ts）
  services/        ← API 呼叫層
  assets/
    images/
    audio/
    fonts/
  styles/
    global.scss
    variables.scss
  utils/
  constants/
  types/
  router/          ← Vue Router 設定
```

命名規範：
- View / Component：`PascalCase.vue`
- Composable：`useCamelCase.ts`
- Store：`useCamelCaseStore.ts`

### HTML5 路由

```
src/
  index.html
  pages/           ← 多頁面（若有）
  js/
    main.js
    game.js        ← 核心邏輯
    ui.js
    audio.js
    utils.js
  css/
    main.css
    animations.css
  assets/
    images/
    audio/
    fonts/
  lib/             ← 第三方庫（Howler.js / PixiJS 等）
```

---

## Step 4：§3 場景 / 頁面 / 視圖結構生成規則

從 EDD.md §5 功能模組 / PDD 頁面流程提取場景清單，填入 §3.1 表格。

### §3.2 主場景 / 頁面結構（5-way 展開）

#### Cocos Creator：

生成每個主要場景的 Node 樹，格式：

```
[場景名稱] Node 樹：
Canvas
  ├── UILayer（Layer: UI）
  │     ├── TopBar（cc.Node + UITransform）
  │     │     ├── lblScore（cc.Label）
  │     │     └── btnPause（cc.Button）
  │     └── Popup（cc.Node + cc.BlockInputEvents）
  ├── GameLayer（Layer: Default）
  │     ├── Player（cc.Node + PlayerController.ts）
  │     │     ├── Body（cc.Sprite + AnimationComponent）
  │     │     └── AttackEffect（cc.ParticleSystem）
  │     └── Enemies（cc.Node 容器）
  └── BgLayer（Layer: Background）
        └── Background（cc.TiledMap 或 cc.Sprite）
```

規則：
- 每個 Node 標注主要 Component
- 有腳本的 Node 標注 `.ts` 文件名
- 粒子系統 / 特效標注在對應 Node 下

#### Unity WebGL：

```
Scene Hierarchy：
[Scene: GameMain]
  ── GameManager（GameManager.cs）
  ── AudioManager（AudioManager.cs）
  ── UIRoot（Canvas, CanvasScaler）
  │    ├── HUD（HUDController.cs）
  │    │    ├── ScoreText（TextMeshProUGUI）
  │    │    └── PauseButton（Button）
  │    └── PopupPanel（PopupManager.cs）
  ── GameWorld
  │    ├── Player（PlayerController.cs, Rigidbody2D, Animator）
  │    │    └── AttackVFX（ParticleSystem）
  │    └── EnemySpawner（EnemySpawner.cs）
  └── Environment
       └── TileMap（Tilemap, TilemapRenderer）
```

#### React：

```
頁面 / 組件樹：
<App>（App.tsx, React Router v6）
  <Layout>（Layout.tsx）
  │  <Header>（Header.tsx）
  │  <Outlet />（Router Outlet）
  │    ├── <HomePage>（pages/HomePage.tsx）
  │    │    ├── <HeroBanner>（components/HeroBanner.tsx）
  │    │    └── <FeatureGrid>（components/FeatureGrid.tsx）
  │    └── <GamePage>（pages/GamePage.tsx）
  │         ├── <GameCanvas>（components/GameCanvas.tsx）
  │         └── <GameHUD>（components/GameHUD.tsx）
  └── <Footer>（Footer.tsx）
```

#### Vue：

```
視圖 / 組件樹：
<App>（App.vue, Vue Router）
  <RouterView />
    ├── <HomeView>（views/HomeView.vue）
    │    ├── <HeroBanner>（components/HeroBanner.vue）
    │    └── <FeatureList>（components/FeatureList.vue）
    └── <GameView>（views/GameView.vue）
         ├── <GameCanvas>（components/GameCanvas.vue）
         └── <GameHUD>（components/GameHUD.vue）
```

#### HTML5：

```
DOM 結構（index.html）：
<body>
  <div id="app">
    <div id="loading-screen"><!-- Loading UI --></div>
    <canvas id="game-canvas"><!-- 遊戲主畫布 --></canvas>
    <div id="ui-overlay">
      <div id="hud"><!-- 血量/分數 HUD --></div>
      <div id="menu"><!-- 主選單 --></div>
      <div id="popup"><!-- 彈出視窗 --></div>
    </div>
    <audio id="bgm-player"></audio><!-- 背景音樂 -->
  </div>
</body>
```

---

## Step 5：§4 資源載入策略生成規則（5-way）

#### Cocos Creator：

| 資源類型 | 載入方式 | 時機 |
|---------|---------|------|
| 核心 UI（首屏）| 場景同步載入（build-in） | 場景加載時自動 |
| 遊戲 Prefab | `cc.assetManager.loadBundle` + `bundle.load` | 進入遊戲場景前 |
| 特效 Prefab | `resources.load` 或 Bundle 預載 | 遊戲開始前 Preload |
| 關卡資源 | 對應 Level Bundle 異步載入 | 進入關卡 loading 畫面時 |
| 音效 SFX | `resources.load<cc.AudioClip>` 並快取 | 場景初始化時批量預載 |
| BGM | `resources.load<cc.AudioClip>` 串流播放 | 場景進入時 |

#### Unity WebGL：

| 資源類型 | 載入方式 | 時機 |
|---------|---------|------|
| 場景資源 | `SceneManager.LoadSceneAsync` | 轉場 Loading 時 |
| 動態 Prefab | `Addressables.LoadAssetAsync<GameObject>` | 進入場景前 |
| 音效 | `AudioClip` 引用（Inspector） | AudioManager.Start() |
| 遠端資源 | `Addressables` Remote Group | 首次啟動後台下載 |

#### React / Vue：

| 資源類型 | 載入方式 | 時機 |
|---------|---------|------|
| 首屏資源 | `import`（打包進 Entry Bundle）| 頁面加載 |
| 圖片 | `<img loading="lazy">` 或 React 動態 import | 可見時 |
| 頁面組件 | `React.lazy` / Vue `defineAsyncComponent` | 路由切換時 |
| 音效 | Howler.js `new Howl({src})` | 用戶首次互動後 |
| 大型第三方庫 | Dynamic `import()` | 功能觸發時 |

#### HTML5：

| 資源類型 | 載入方式 | 時機 |
|---------|---------|------|
| 圖片 | `new Image()` preload 或 `loading="lazy"` | 遊戲開始前批量預載 |
| 音效 | `new Audio()` 或 Web Audio API `fetch` + `decodeAudioData` | 用戶互動後 |
| Sprite Sheet | JSON + Canvas | 遊戲循環前 |

---

## Step 6：§5 動畫整合規格生成規則（5-way）

若 ANIM.md 存在，提取所有動畫條目填入 §5.1 表格。

### 觸發實作（§5.2）5-way：

#### Cocos Creator：
```typescript
// 觸發範例：事件驅動
this.node.on('enemy-defeated', () => {
    const anim = this.getComponent(Animation);
    anim.play('player_victory');
});
// 或狀態機（cc.AnimationStateMachine）
```

#### Unity WebGL：
```csharp
// Animator 觸發
animator.SetTrigger("Jump");
animator.SetBool("IsRunning", true);
// 或 Timeline 事件
playableDirector.Play();
```

#### React：
```typescript
// Framer Motion
<motion.div animate={{ x: 100 }} transition={{ duration: 0.5 }} />
// 或 GSAP
gsap.to(ref.current, { duration: 0.5, x: 100 });
// 或 CSS class toggle
setIsAnimating(true);
```

#### Vue：
```typescript
// Vue Transition
<Transition name="slide-fade">
// GSAP in composable
const { triggerAnim } = useAnimation();
// CSS class
animClass.value = 'active';
```

#### HTML5：
```javascript
// CSS class toggle
element.classList.add('animate-in');
// requestAnimationFrame loop
requestAnimationFrame(gameLoop);
// Web Animations API
element.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 500 });
```

---

## Step 7：§6 音效整合規格生成規則（5-way）

若 AUDIO.md 存在，提取所有音效條目填入 §6.1 表格。

### AudioManager 架構（§6.3）5-way：

#### Cocos Creator：
```typescript
// AudioManager.ts（全局單例）
// - bgmSource: cc.AudioSource（背景音樂，loop=true）
// - sfxPool: Map<string, cc.AudioClip>（音效快取）
// - playBGM(name: string): void
// - playSFX(name: string): void
// - stopAll(): void
// - setVolume(type: 'bgm'|'sfx', vol: number): void
```

#### Unity WebGL：
```csharp
// AudioManager.cs（Singleton）
// AudioMixer 分組：Master / BGM / SFX
// - PlayBGM(AudioClip clip)
// - PlaySFX(string clipName)
// - SetVolume(string group, float vol)
```

#### React / Vue：
```typescript
// useAudio composable / hook（Howler.js）
// const { play, stop, setVolume } = useAudio()
// Howl 實例快取：Map<string, Howl>
// BGM：loop: true, html5: true（串流）
// SFX：preload: true, pool: 5
```

#### HTML5：
```javascript
// AudioManager（Web Audio API）
// - audioCtx: AudioContext
// - gainNode: GainNode（音量控制）
// - bgmBuffer / sfxBuffers: Map<string, AudioBuffer>
// - play(name, loop): AudioBufferSourceNode
```

---

## Step 8：§7 VFX 整合規格生成規則（5-way）

若 VDD.md 存在，提取特效 / 粒子章節內容。

#### Cocos Creator：
- 特效類型：cc.ParticleSystem、Spine 骨骼動畫、cc.Tween 組合動畫
- 觸發：`cc.instantiate(prefab)` + `node.setParent(effectLayer)`
- 回收：`node.destroy()` 或 Object Pool

#### Unity WebGL：
- 特效類型：ParticleSystem、Shader Graph、VFX Graph
- 觸發：`Instantiate(vfxPrefab, position, rotation)` 或 Object Pool
- 回收：`ParticleSystem.Stop()` + `Destroy(go, lifetime)`

#### React / Vue：
- 特效類型：CSS Animation、Canvas 粒子（tsparticles / particles.js）、Lottie
- 觸發：state change → className / `useEffect` → Canvas API
- 說明：非遊戲框架的「特效」主要為 UI 動效，使用 CSS 或輕量庫

#### HTML5：
- 特效類型：Canvas 粒子系統（手寫或 particles.js）、CSS Animation
- 觸發：game event → `particleSystem.emit(x, y, type)`

---

## Step 9：§8–§12 共用生成規則

### §8 UI Flow 狀態機
- 從 EDD / PDD 的功能模組清單推斷 UI 狀態
- Loading、Error、NetworkLost 必須包含（不可省略）

### §9 API 整合
- 從 ARCH.md 或 EDD §4 提取 API 端點清單
- 每個 API 必須有觸發時機、錯誤處理策略

### §10 效能規範
- Cocos/Unity 遊戲：FPS 目標通常 30/60fps；包體首包 < 5MB
- React/Vue Web：LCP < 2.5s；Bundle < 200KB（gzip）；TTI < 3.5s
- HTML5 遊戲：首包 < 3MB；60fps canvas loop

### §11 測試規範
- 所有引擎：至少列出 3 個整合測試場景

### §12 已知限制
- 若上游文件有明確提到技術限制，提取並列入

---

## Self-Check Checklist

生成完成後，逐項驗證：

- [ ] **ENGINE-01** `CLIENT_ENGINE` 欄位已填入且與 EDD.md §3.3 一致（非佔位符）
- [ ] **ENGINE-02** §2.1 目錄結構符合偵測到的引擎慣例（非通用模板）
- [ ] **SCENE-01** §3.1 場景 / 頁面清單有至少 3 條具體場景（來自 EDD 或 PDD）
- [ ] **SCENE-02** §3.2 有具體的 Node 樹 / Component 樹 / DOM 結構（非「待補」）
- [ ] **ANIM-01** §5.1 動畫清單有具體條目（若 ANIM.md 存在）
- [ ] **ANIM-02** §5.2 觸發事件表格有至少 3 條（若 ANIM.md 存在）
- [ ] **AUDIO-01** §6.1 音效清單有具體條目（若 AUDIO.md 存在）
- [ ] **AUDIO-02** §6.3 AudioManager 架構符合偵測引擎（非通用）
- [ ] **VFX-01** §7.1 特效清單有具體條目（若 VDD.md 存在）
- [ ] **PERF-01** §10 效能規範有具體數字（非「待定」）
- [ ] **ASSET-01** §4.3 資源載入策略符合偵測引擎（非通用）
- [ ] **NOPLACEHOLDER** 全文件無裸 `{{PLACEHOLDER}}`（無說明的空白佔位符）
