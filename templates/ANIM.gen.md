---
doc-type: ANIM
output-path: docs/ANIM.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md     # UX 設計流程 → 動畫觸發時機、目標平台渲染能力
  - docs/VDD.md     # 視覺設計系統 → 運動語言、easing 函數、品牌色
  - docs/EDD.md
  - docs/FRONTEND.md
quality-bar: "§2 所有 P0 角色/物件都有完整骨骼動畫狀態機；§4 所有 P0 UI 互動（按鈕縮放/面板滑入/數值跳動）均有 Tween 記錄，起始值/結束值為具體數值（含 OFF_SCREEN/ON_SCREEN 位置已依目標解析度計算），三引擎 Easing 欄（Cocos/Unity/HTML5）均已填寫；§5 粒子特效最大粒子數已填具體值；§7 引擎設定代碼可直接複製使用；§8 資產命名規範完整；§9 所有效能指標填具體數值且有 LOD 策略；§10 測試清單覆蓋幀率/記憶體/跨平台；§1.2 第4條 {{CUSTOM_PRINCIPLE}} 已替換為具體設計原則；無裸 placeholder"
---

# ANIM.gen.md — 動畫特效設計文件生成規則

依 PRD + EDD + VDD + FRONTEND 產出 ANIM.md，涵蓋骨骼動畫、幀動畫、Tween、粒子特效、Shader、引擎設定、效能預算。

---

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。

**Iron Law**：生成任何 ANIM.md 之前，必須先讀取 `ANIM.md`（結構）和 `ANIM.gen.md`（本規則）。

---

## 全域禁止裸 Placeholder 規則

**所有 §1~§10 及 Document Control 的 `{{PLACEHOLDER}}` 均必須替換為具體值，不得保留任何未填欄位。**

常見遺漏欄位（特別注意）：
- **§1**：`{{VISUAL_FEEDBACK_GOAL}}`、`{{PERF_GOAL}}`、`{{TARGET_FPS}}` 等設計目標欄位必須填入具體描述和數值。
- **§1.2 第4條**：`{{CUSTOM_PRINCIPLE}}` 必須替換為符合專案特色的具體設計原則（例如「角色受傷使用 Camera Shake 替代閃紅效果」）；不得原樣保留此 placeholder。
- **§4**：`{{OFF_SCREEN}}`、`{{ON_SCREEN}}` 必須依 BRD 目標解析度計算出實際座標（如 `y: -1920`）；三引擎 Easing 對照欄（Cocos / Unity / HTML5）均須填寫具體 easing 名稱。
- **§6**：{{SHADER_NAME}}、{{RENDER_QUEUE}}、{{GPU_INSTANCING}} 等 Shader 技術規格中的 placeholder 必須替換為實際 Shader 名稱、渲染佇列設定和 GPU Instancing 開關。

若任何 placeholder 未替換，生成結果視為不通過品質門（Quality Gate）。

---

## 專家角色（Expert Roles）

| 角色 | 負責章節 | 專業要求 |
|------|---------|---------|
| 資深技術動畫師（Senior Technical Animator） | §1, §2, §3, §4, §5 | 10 年遊戲動畫經驗，熟悉 Spine/DragonBones 骨骼動畫、Unity Animator 狀態機、GSAP Tween 設計 |
| VFX 技術工程師（VFX Technical Engineer） | §5, §6, §7 | 深度熟悉 Cocos ParticleSystem、Unity VFX Graph、PixiJS Particles、GLSL/Shader Graph 開發 |
| 效能工程師（Performance Engineer） | §9, §10 | 移動端 GPU 效能優化、Draw Call 合批、LOD 策略、Profiler 分析 |

---

## 上游文件讀取規則

### 必讀上游鏈（依優先順序）

| 文件 | 必讀章節 | 用途 |
|------|---------|------|
| `IDEA.md`（若存在）| 全文 | 確認產品類型（動作遊戲/休閒遊戲/Web App）→ 決定動畫豐富程度和特效風格 |
| `BRD.md` | 目標平台、目標裝置 | 決定 §9 效能預算基準（低階 Android = 嚴格預算；PC/主機 = 寬鬆）；確認是否需要多解析度 Spine 圖集 |
| `PRD.md` | 所有 User Stories、P0/P1/P2 功能 | §2 骨骼動畫必須覆蓋所有 P0 角色的所有狀態；§4 Tween 必須覆蓋所有 P0 UI 互動 |
| `EDD.md` | §2 技術棧、§3 架構 | 確認引擎（Cocos/Unity/HTML5）→ 決定 §7 展開哪個引擎設定章節；確認資源管理策略 |
| `VDD.md`（若存在）| §3 Brand Identity、§4 Motion Design、§6 Design Token | **最重要的視覺上游**：Motion Easing 函數（§4）直接對應 §4 Tween Easing；Lottie/CSS Animation 定義的動畫時長規格必須反映在 §4 |
| `FRONTEND.md`（若存在）| §2 平台選型、§5 Component 架構 | 確認引擎具體版本、Spine runtime 版本（必須與 FRONTEND.md 一致）；Component 邊界決定動畫由誰負責觸發 |

### 引擎偵測規則

讀取完 EDD.md 和 FRONTEND.md 後：

```
if FRONTEND.md 包含 "Cocos Creator" → 重點展開 §7.1 Cocos 設定，標注其他引擎「不適用本專案」
  - 確認 Cocos Creator 版本（2.x 用 cc.tween；3.x 用 tween()）
  - 確認 Spine 版本（需與 Cocos 版本匹配的 Spine runtime）
if FRONTEND.md 包含 "Unity" → 重點展開 §7.2 Unity 設定
  - 確認 Unity 版本（決定使用 Animator/Timeline 還是 VFX Graph）
  - 確認渲染管線（Built-in/URP/HDRP → 影響 Shader 開發方式）
if FRONTEND.md 包含 "HTML5" / "PixiJS" / "Phaser" → 重點展開 §7.3 HTML5 設定
  - 確認 PixiJS 版本（v7/v8 API 差異）
  - 確認 GSAP 版本（ScrollTrigger 等插件）
if 無法偵測 → 三個引擎章節全部展開
```

### 上游衝突偵測

- VDD §4 Motion Easing vs §4 Tween Easing（是否使用相同的 easing 函數名稱）
- FRONTEND.md Spine 版本 vs §2 骨骼動畫格式（.skel vs .json，runtime 版本要匹配）
- BRD 最低目標裝置 vs §9 效能預算（預算是否在低階裝置可達成）
- PRD P0 角色列表 vs §2 骨骼動畫清單（是否每個 P0 角色都有完整動畫狀態）
- **EDD.md 技術棧（WebGL vs Canvas 2D）vs §6 Shader 清單**：若 EDD.md 確認渲染技術為 Canvas 2D（不含 WebGL），則 §6 不得列入依賴 WebGL 的自訂 Shader。此時 §6 應改為「本專案不支援自訂 Shader，使用引擎內建濾鏡替代（如 PixiJS 內建 BlurFilter、ColorMatrixFilter 等）」。

---

## 生成步驟

### Step 1：確認動畫風格與引擎

1. 從 IDEA.md 推斷動畫風格（卡通誇張 / 寫實流暢 / 機械精確 / 極簡）
2. 從 VDD.md §4 提取 Motion Design 規格（Easing 函數、標準時長）
3. 從 FRONTEND.md 確認引擎和版本
4. 填入 §1.1 設計目標（包含具體的目標 fps）
5. 填入 §1.2 設計原則（保留預設 3 條，依專案特色添加第 4 條）

**§1.3 動畫分級填寫：**
- P0 = PRD P0 功能中有動畫的部分（核心遊戲循環）
- P1 = PRD P1 功能的動畫（增強體驗）
- P2 = 裝飾性動效（資源允許）

### Step 2：骨骼動畫清單（§2）

1. 從 PRD.md 提取所有有動畫需求的角色和物件
2. 為每個 P0 角色填寫完整的動畫狀態機（至少：idle / walk 或等效 / 主要行動 / die 或結束狀態）
3. 每條記錄必須填寫：
   - ID：`SKEL-{三位數序號}`
   - 幀數：從美術規格或預估（idle 60~90 幀，attack 20~40 幀，die 40~60 幀）
   - 資產路徑：依 §8.2 目錄結構填寫（不得裸 placeholder）
4. §2.1 骨骼動畫狀態機：為每個有多狀態的角色畫出完整轉換圖（ASCII 格式）
5. §2.2 技術規格：
   - 骨骼節點數：Cocos 建議 ≤ 50；Unity 建議 ≤ 100；HTML5 建議 ≤ 30
   - 圖集尺寸：首選 2048×2048；複雜角色可用多張但需說明
   - 是否開啟 Premultiplied Alpha（Cocos Spine 建議開啟）

**若專案無骨骼動畫（純 Web App）：**
§2 填「本專案無骨骼動畫需求」，跳過此節。

### Step 3：幀動畫清單（§3）

從 PRD 和 IDEA 提取需要幀動畫的物件（爆炸特效、硬幣旋轉、角色非骨骼動畫等）。
幀數建議：簡單迴圈 8~12 幀；複雜動作 16~24 幀。
若無幀動畫，§3 填「本專案使用骨骼動畫替代幀動畫」或「無幀動畫需求」。

**禁止裸 Placeholder（Strict）**：§3 每條記錄的名稱、幀數、幀率、圖集路徑必須填入具體值，不得保留 `{{NAME}}`、`{{FRAMES}}`、`{{FPS}}` 等 placeholder。

### Step 4：Tween / 緩動動畫清單（§4）

**必須覆蓋（P0 UI 動畫，不得省略）：**
- 按鈕點擊縮放（scale 1.0 → 0.9 → 1.0，Bounce.Out，150ms）
- 主要面板的出現/消失（slide 或 fade，Cubic.Out，250~350ms）
- 數值跳動（金幣/分數，Linear，600~1000ms）

**從 VDD.md §4 提取（若存在）：**
- VDD 定義的 Easing 函數名稱 → §4 Easing 欄直接引用
- VDD 定義的動畫時長規格 → §4 時長欄使用相同數值

**Easing 命名統一規範（對應 §4 表格三個引擎欄位）：**

§4 表格包含四個 Easing 相關欄位，填寫規則如下：

| 欄位名 | 填寫規則 | 範例（Back.Out 語義） |
|--------|---------|---------------------|
| Easing（語義名） | 語言無關的語義名稱，供 VDD 對照 | `Back.Out` |
| Cocos Easing | `cc.easing.xxx`（Cocos Creator 2.x/3.x 共用） | `cc.easing.backOut` |
| Unity Easing（DOTween） | `Ease.OutXxx` | `Ease.OutBack` |
| HTML5 Easing（GSAP） | GSAP 字串形式 | `"back.out"` |

- 若本專案只使用單一引擎，非本引擎欄位填「不適用」。
- 若多引擎並存（如 Cocos 遊戲場景 + HTML5 行銷頁），三欄均須填寫。
- VDD.md §4 定義的語義 easing 名稱應填入「Easing（語義名）」欄，各引擎具體名稱由此映射而來。

**禁止裸 Placeholder（Strict）**：§4 每條記錄的起始值與結束值必須填具體數值。特別是含 `{{OFF_SCREEN}}`、`{{ON_SCREEN}}` 的欄位，必須依 BRD 目標解析度計算出實際座標數值（如 `y: -1920` 表示解析度 1920 高度時螢幕外起始位置），不得保留 placeholder。

### Step 5：粒子特效清單（§5）

1. 從 IDEA/PRD 提取所有需要粒子特效的事件（攻擊命中、收集、勝利、環境）
2. 為每個特效填入最大粒子數（必須是具體數值，非 placeholder）：
   - 命中/爆炸：50~200 粒子
   - 收集（金幣/道具）：20~50 粒子
   - 環境（粉塵/雨/雪）：100~500 粒子（循環，低 LOD 降至 30~100）
3. §5.1 全局粒子數上限：
   - 移動端低階裝置：≤ 200
   - 移動端中高階：≤ 500
   - PC/Web：≤ 1000
4. 粒子材質圖集：建議所有粒子貼圖打包至 `effects/particle_atlas.png`（2048×2048）

**若專案無粒子特效（純 Web UI App）：**
§5 填「本專案無粒子特效需求，使用 CSS animation 替代」。

### Step 6：Shader 特效清單（§6）

從 EDD/FRONTEND 確認是否支援自訂 Shader：
- Cocos Creator 2.x/3.x：支援 Effect 檔案
- Unity：支援 Shader Graph（URP/HDRP）
- HTML5：支援 GLSL Fragment Shader（PixiJS Filter / Three.js ShaderMaterial）

常見 Shader 特效（依專案需求選用）：
- 描邊高亮（Outline）：UI hover / 可選取物件
- 溶解（Dissolve）：角色消亡 / 場景切換
- 閃光（Flash）：受傷 / 勝利演出
- 模糊（Gaussian Blur）：暫停遮罩 / 景深

**§6.1 Shader 代碼範例規範：**
- 只展開與本專案引擎對應的 Shader 代碼
- 代碼必須是完整可用的最小範例（不得只有偽代碼）
- 標注資產路徑（不得裸 placeholder）

**若無 Shader 需求：**
§6 填「本專案不使用自訂 Shader，所有特效透過引擎內建功能實現」。

### Step 7：引擎特定設定（§7）

依偵測到的引擎展開對應子章節（其他引擎標注「不適用本專案」）：

**§7.1 Cocos Creator：**
- 填入具體 Cocos Creator 版本（2.x 或 3.x → API 有差異）
- Dynamic Atlas 設定（開啟條件：SFX 圖集 < 512×512 可合批）
- Spine 快取模式選擇（SHARED_CACHE vs REALTIME）
- Tween 代碼範例必須與 §4 清單中的首個 Tween 一致

**§7.2 Unity：**
- Animator 層次結構（Base Layer + Override Layer）
- VFX Graph vs Particle System 選擇依據
- Culling Mode 設定（強制填入）

**§7.3 HTML5：**
- PixiJS 版本（v7.x 或 v8.x）
- GSAP 版本與使用的 plugin 列表
- CSS animation 適用範圍（僅 UI，不用於 Canvas 內）

### Step 8：資產規格與命名（§8）

1. §8.1 命名規範：確認 MODULE 已替換為專案實際模組名稱
2. §8.2 目錄結構：
   - Cocos：`assets/animations/`, `assets/effects/`
   - Unity：`Assets/Animations/`, `Assets/Effects/`
   - HTML5：`public/animations/`, `public/effects/`

### Step 9：效能預算（§9）

**必須填入具體數值（不得保留 placeholder）：**

| 指標 | Cocos 移動端 | Unity 移動端 | HTML5 |
|------|------------|------------|-------|
| 目標 fps | 60（中高階）/ 30（低階） | 60（中高階）/ 30（低階） | 60（Chrome）/ 30（iOS Safari） |
| Draw Call | ≤ 50 | ≤ 80 | ≤ 30（canvas ctx 呼叫） |
| 全局粒子數 | ≤ 300 | ≤ 500 | ≤ 200 |
| 骨骼節點數 | ≤ 50/角色 | ≤ 100/角色 | ≤ 30/角色 |
| 動畫記憶體 | ≤ 100MB | ≤ 150MB | ≤ 80MB |

§9.1 LOD 策略：必須填寫三個裝置等級（高/中/低），填入判斷條件和具體降級項目。

### Step 10：測試清單（§10）

§10 預設 8 個測試案例全部保留，依專案補充：
- 每個骨骼動畫角色補一條「狀態機轉換完整性」測試
- 若有 Shader，補「各平台 Shader 顯示對比」測試

---

### Step 11：State Machine Transition Table + TypeScript Class Skeleton（AI Gencode 必要元素，強制）

> **目的**：ANIM.md 的文字描述不足以讓 AI codegen 工具生成正確的 Phaser/遊戲引擎動畫程式碼；必須補充結構化的 transition table 和 class skeleton，供 AI 直接參照生成。

在 ANIM.md 的 `## §11 AI Gencode 參考骨架` 章節（新建）生成以下內容：

**11.1 State Machine Transition Table**

從 §2（骨骼動畫）和 §3（幀動畫）的狀態說明提取所有 state，建立 transition table：

| From State | Trigger Event | To State | Guard Condition | Duration / Timing |
|-----------|--------------|---------|----------------|------------------|
| `idle` | `onClick` / `onTouch` | `interacting` | — | 立即 |
| `interacting` | `animationComplete` | `idle` | 300ms 後 | 自動 |
| `idle` | `battleStart` | `battle_enter` | arena session active | 立即 |
| `battle_enter` | `animationComplete` | `battle_active` | — | 600ms 後 |
| `battle_active` | `battleEnd(win)` | `level_up` | win flag = true | 立即 |
| `battle_active` | `battleEnd(lose)` | `idle` | win flag = false | 立即 |
| `idle` | `neglectCheck` | `neglect` | last_trained > NEGLECT_THRESHOLD_DAYS | 立即 |
| （依實際 PRD 場景繼續補充…）| | | | |

**11.2 Engine-Aware Class Skeleton（依 CLIENT_ENGINE 分支）**

> **生成規則**：讀取 `.gendoc-state.json` 的 `client_engine` 欄位，依引擎選擇對應骨架。

**CLIENT_ENGINE = Phaser（Phaser 3）**：

```typescript
// ── AnimationStateMachine ─────────────────────────────────────────
// 依 ANIM.md §11.1 Transition Table 實作；每個 state 對應一個引擎 anim key
// key 命名規則：從 ANIM.md §3 幀動畫清單讀取（不硬碼 key 格式）

// AnimState = §11.1 所有 "From State" + "To State" 的聯集（從 Transition Table 讀取）
type AnimState = /* 從 §11.1 Transition Table 讀取，例如：*/
  | 'idle' | 'interacting' | 'battle_enter' | 'battle_active' | 'level_up' | 'neglect';

interface AnimTransitionEvent {
  // type = §11.1 所有 "Trigger Event" 的聯集（從 Transition Table 讀取）
  type: string;
  payload?: Record<string, unknown>;
}

class AnimationStateMachine {
  private current: AnimState = 'idle';
  private sprite: Phaser.GameObjects.Sprite;
  private scene: Phaser.Scene;
  private entityKey: string;  // 動畫 key prefix（從 §3 幀動畫清單讀取）

  constructor(sprite: Phaser.GameObjects.Sprite, scene: Phaser.Scene, entityKey: string) {
    this.sprite = sprite;
    this.scene  = scene;
    this.entityKey = entityKey;
    this.playAnim(this.current);
  }

  dispatch(event: AnimTransitionEvent): void {
    // 依 §11.1 Transition Table 逐行實作（每個 From+Trigger → To 的映射）
    // Guard Condition 對應 if 判斷；Duration 對應 delayedCall 或 animationComplete 事件
    // 範例結構（以 §11.1 第一行為例，其餘行照此模式展開）：
    // if (this.current === 'idle' && event.type === 'onClick') {
    //   this.current = 'interacting';
    //   this.playAnim('interacting');
    // }
  }

  private playAnim(state: AnimState): void {
    // key 格式從 §3 幀動畫清單讀取（FRAME-xxx 的「動畫名稱」欄）
    this.sprite.play(`${this.entityKey}-${state}`, true);
  }

  get currentState(): AnimState { return this.current; }
}
```

**Phaser Scene Lifecycle（具體版，依 §3 幀動畫清單 + CONSTANTS.md 填值）**：

```typescript
// src/game/scenes/{EntityName}Scene.ts

function preloadAssets(this: Phaser.Scene, entityKey: string): void {
  // 逐一讀取 ANIM.md §3 幀動畫清單，為每個 FRAME-xxx 生成 load 呼叫
  // frameWidth / frameHeight 從 CONSTANTS.md 的 SPRITE_CONFIG（或等效常數）讀取
  this.load.spritesheet(
    `${entityKey}-idle`,                          // FRAME-xxx 的「動畫名稱」
    `assets/sprites/${entityKey}/idle.png`,       // FRAME-xxx 的「圖集路徑」
    { frameWidth: SPRITE_W, frameHeight: SPRITE_H }  // 從 CONSTANTS.md 讀取，不硬碼數字
  );
  // （§3 每條記錄生成一行 this.load.spritesheet）
}

function createScene(this: Phaser.Scene, entityKey: string): AnimationStateMachine {
  // 逐一讀取 ANIM.md §3 幀動畫清單，為每個 FRAME-xxx 生成 anims.create 呼叫
  this.anims.create({
    key: `${entityKey}-idle`,
    frames: this.anims.generateFrameNumbers(`${entityKey}-idle`, { start: 0, end: IDLE_FRAMES - 1 }),
    frameRate: IDLE_FPS,  // 從 CONSTANTS.md 讀取（FRAME-xxx 的「幀率」欄）
    repeat: -1,           // loop 欄位 = true → -1；false → 0
  });
  // （§3 每條記錄生成一個 anims.create 塊）

  const sprite = this.add.sprite(this.scale.width / 2, this.scale.height / 2, `${entityKey}-idle`);
  return new AnimationStateMachine(sprite, this, entityKey);
}

function updateScene(_scene: Phaser.Scene, sm: AnimationStateMachine): void {
  // 通常為空（狀態機為 event-driven）
  // 若 PRD 有 idle timeout 功能：在此計時並 dispatch neglectCheck 事件
  // sm.tickIdleTimeout(this.game.loop.delta);  // 閾值從 CONSTANTS.md 讀取
}
```

**CLIENT_ENGINE = Cocos Creator（2.x / 3.x）**：

```typescript
// AnimationController.ts（cc.Component）
@ccclass('AnimationController')
export class AnimationController extends cc.Component {
  private _current: string = 'idle';

  playAnim(state: string): void {
    // Cocos 2.x：this.getComponent(cc.Animation).play(state);
    // Cocos 3.x：this.getComponent(animation.Animation).play(state);
    // state key = ANIM.md §3 幀動畫清單的「動畫名稱」欄
  }
}
```

**CLIENT_ENGINE = Unity（WebGL build）**：

```csharp
// AnimationController.cs（MonoBehaviour）
public class AnimationController : MonoBehaviour {
  private Animator _animator;
  private string _current = "idle";

  void Awake() { _animator = GetComponent<Animator>(); }

  public void PlayAnim(string state) {
    // state = ANIM.md §3 幀動畫清單的「動畫名稱」欄
    _animator.SetTrigger(state);
    _current = state;
  }
}
```

---

**11.3 程序生成資產演算法骨架（觸發條件：PRD 含「程序生成」「procedural」關鍵字）**

> **觸發條件**：PRD 含「procedural generation」「程序生成」「pixel art generated」「seeded random」等關鍵字時強制生成此節。

必須包含以下 4 個要素：

1. **輸入規格**：seed（唯一識別符 hash）+ palette（色票陣列來源，引用 VDD design tokens）
2. **演算法核心**：seeded-RNG 策略 + 填色邏輯 + 對稱/鏡像策略（如 PRD 要求對稱）
3. **輸出格式**：依 lang_stack 選擇（TypeScript → Canvas ImageData；Java → BufferedImage；Python → PIL.Image）
4. **Test Vector**：≥ 2 組 seed + palette → 預期 pixel 結果（可貼入 .test.ts）

**TypeScript 骨架範例**（lang_stack = TypeScript 時）：

```typescript
// src/game/utils/proceduralAsset.ts

// seeded LCG（Linear Congruential Generator）— seed 固定 → 結果固定
function seededRng(seed: number): () => number {
  let s = seed;
  return () => { s = (1664525 * s + 1013904223) & 0xFFFFFFFF; return (s >>> 0) / 0xFFFFFFFF; };
}

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

// 主函式：依 seed 生成 {W}×{H} px 圖案（W/H 從 CONSTANTS.md 讀取）
export function generateProceduralAsset(
  seed: number,
  palette: string[],  // 色票陣列，來自 VDD.md design tokens
  width: number,      // 從 CONSTANTS.md 讀取（不硬碼）
  height: number
): ImageData {
  const data = new Uint8ClampedArray(width * height * 4);
  const rng  = seededRng(seed);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < Math.ceil(width / 2); x++) {  // 左半邊生成，右半邊鏡像
      const colorIdx = Math.floor(rng() * palette.length);
      const [r, g, b] = hexToRgb(palette[colorIdx]);
      const setPixel = (px: number) => {
        const i = (y * width + px) * 4;
        data[i] = r; data[i+1] = g; data[i+2] = b; data[i+3] = 255;
      };
      setPixel(x);
      setPixel(width - 1 - x);  // 左右鏡像
    }
  }
  return new ImageData(data, width, height);
}

// Test Vector（直接貼入 proceduralAsset.test.ts）：
// generateProceduralAsset(0, ['#000000', '#FFFFFF'], 4, 2)
//   seed=0, rng序列: [0.000..., ...]  → pixel[0,0] = #000000
// generateProceduralAsset(42, ['#FF0000', '#0000FF'], 4, 2)
//   seed=42 → 依 LCG 公式計算第一個 rng() → 決定 pixel[0,0] 顏色
```

---

## 品質門（Quality Gate）

| 檢查項 | 標準 |
|-------|------|
| 骨骼動畫覆蓋 | PRD P0 角色/物件全部有 §2 記錄 |
| 幀動畫覆蓋 | §3 每條記錄的名稱/幀數/幀率/圖集路徑均填具體值；或聲明本專案無幀動畫需求 |
| Tween 覆蓋 | §4 所有 P0 UI 互動（按鈕縮放/面板滑入/數值跳動）均有 Tween 記錄，起始值/結束值為具體數值（含 OFF_SCREEN/ON_SCREEN 位置已依目標解析度計算），三引擎 Easing 欄均已填寫或標注「不適用」 |
| 粒子數量 | §5 每條特效填具體最大粒子數 |
| 引擎代碼 | §7 代碼無裸 placeholder，版本/路徑均已填具體值 |
| 效能預算 | §9 所有欄位填具體數值，LOD 三級已定義 |
| 命名規範 | 所有 ID 符合 SKEL-xxx / FRAME-xxx / TWN-xxx / PTL-xxx / SHD-xxx 格式 |
| AI Gencode — Transition Table | §11.1 Transition Table 存在；所有 PRD P0 狀態均有對應行；Duration/Timing 填具體值 |
| AI Gencode — engine-aware Class Skeleton | §11.2 骨架使用 CLIENT_ENGINE 對應的具體 API 呼叫（Phaser: anims.create；Cocos: Animation；Unity: Animator）；dispatch() 含依 §11.1 展開的骨架注釋；無裸 TODO |
| AI Gencode — 程序生成骨架（game + procedural）| PRD 含程序生成關鍵字時：§11.3 存在；含 seededRng 函式 + 主生成函式 + ≥ 2 組 test vector |

若任何檢查未通過，在 ANIM.md 末尾附加警告區塊：
```markdown
> ⚠️ ANIM 品質警告：[列出未通過的檢查項，說明原因]
```
