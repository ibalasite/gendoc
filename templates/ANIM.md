---
doc-type: ANIM
output-path: docs/ANIM.md
layer: 設計層
condition: client_type != none
upstream:
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/EDD.md
  - docs/VDD.md
  - docs/FRONTEND.md
---

# 動畫特效設計文件（Animation & VFX Design Document）
<!-- Version: {{VERSION}} | Status: {{STATUS}} | DOC-ID: ANIM-{{PROJECT}}-{{DATE}} -->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | ANIM-{{PROJECT}}-{{DATE}} |
| **文件名稱** | 動畫特效設計文件（Animation & VFX Design Document） |
| **文件版本** | {{VERSION}} |
| **狀態** | {{STATUS}} |
| **作者** | {{AUTHOR}} |
| **日期** | {{DATE}} |
| **適用引擎** | {{ENGINE}} （Cocos Creator / Unity / HTML5 PixiJS / CSS + GSAP） |
| **上游文件** | IDEA.md · BRD.md · PRD.md · EDD.md · VDD.md · FRONTEND.md |
| **審閱者** | 技術動畫師、VFX 技術工程師、效能工程師 |

---

## Change Log

| 版本 | 日期 | 作者 | 變更摘要 |
|------|------|------|---------|
| v1.0 | {{DATE}} | {{AUTHOR}} | 初版 |

---

## §1 動畫設計目標

### §1.1 設計目標

| 目標 | 描述 |
|------|------|
| **視覺回饋目標** | {{VISUAL_FEEDBACK_GOAL}} |
| **品牌動態識別** | {{MOTION_BRANDING}} |
| **效能目標** | {{PERF_GOAL}}（目標裝置 60fps，中低階裝置 30fps） |

### §1.2 動畫設計原則

- **即時回饋**：操作 ≤ 100ms 啟動動畫，讓用戶感知系統響應
- **引導視線**：動畫方向引導用戶注意力，不干擾主要操作
- **效能優先**：所有特效必須在目標裝置維持 {{TARGET_FPS}}fps 以上
- {{CUSTOM_PRINCIPLE}}

### §1.3 動畫分級（Priority）

| 等級 | 說明 | 範例 |
|------|------|------|
| P0 | 核心體驗動畫，必須實作 | 角色動作、勝負演出、核心互動 |
| P1 | 增強體驗動畫，正式版實作 | 場景過渡、粒子特效 |
| P2 | 錦上添花動畫，資源允許實作 | 環境細節、裝飾動效 |

---

## §2 骨骼動畫清單（Skeletal Animation）

> 適用 Cocos Creator Spine / DragonBones、Unity Animator、HTML5 Spine-runtimes

| ID | 角色/物件 | 動畫名稱 | 觸發條件 | 循環 | 過渡動畫 | 時長（幀） | 優先級 | 資產路徑 |
|----|---------|---------|---------|------|---------|----------|-------|---------|
| SKEL-001 | {{CHARACTER}} | idle | 待機狀態 | Y | — | {{FRAMES}} | P0 | `animations/{{CHAR}}/{{CHAR}}.skel` |
| SKEL-002 | {{CHARACTER}} | walk | 移動中 | Y | idle→walk 3幀 | {{FRAMES}} | P0 | `animations/{{CHAR}}/{{CHAR}}.skel` |
| SKEL-003 | {{CHARACTER}} | attack | 攻擊觸發 | N | idle→attack 2幀 | {{FRAMES}} | P0 | `animations/{{CHAR}}/{{CHAR}}.skel` |
| SKEL-004 | {{CHARACTER}} | die | HP = 0 | N | 不可打斷 | {{FRAMES}} | P0 | `animations/{{CHAR}}/{{CHAR}}.skel` |
| SKEL-005 | {{CHARACTER}} | win | 勝利條件達成 | N | — | {{FRAMES}} | P1 | `animations/{{CHAR}}/{{CHAR}}.skel` |

### §2.1 骨骼動畫狀態機

```
{{CHARACTER}} 動畫狀態機：
idle ←→ walk
idle → attack → idle（播完自動回 idle）
任意狀態 → die（不可打斷）
die → （遊戲邏輯處理，不自動轉換）
win（只有 idle 狀態可觸發）
```

### §2.2 骨骼動畫技術規格

| 規格 | 值 | 說明 |
|------|---|------|
| 骨骼節點數上限 | {{MAX_BONES}} | 超過此數影響效能 |
| 圖集尺寸 | {{ATLAS_SIZE}} | 建議 2048×2048 以內 |
| 動畫幀率 | {{FPS}} fps | 與遊戲幀率一致 |
| Premultiplied Alpha | {{PMA}} | Cocos 建議開啟 |
| Mesh 頂點數（單角色） | ≤ {{MAX_VERTICES}} | — |

---

## §3 幀動畫清單（Frame Animation）

| ID | 名稱 | 觸發條件 | 幀數 | 幀率(fps) | 循環 | 優先級 | 圖集路徑 |
|----|------|---------|------|----------|------|-------|---------|
| FRAME-001 | {{NAME}} | {{TRIGGER}} | {{FRAMES}} | {{FPS}} | Y/N | P0 | `textures/anim/{{NAME}}/` |

---

## §4 Tween / 緩動動畫清單

| ID | 名稱 | 目標物件 | 屬性 | 起始值 | 結束值 | 時長(ms) | Easing | 觸發條件 | 優先級 |
|----|------|---------|------|-------|-------|---------|--------|---------|-------|
| TWN-001 | 按鈕點擊縮放 | Button | scale | 1.0 | 0.9 → 1.0 | 150 | Bounce.Out | onTouchStart | P0 |
| TWN-002 | 面板滑入 | Panel | y | {{OFF_SCREEN}} | {{ON_SCREEN}} | 300 | Cubic.Out | panel show | P0 |
| TWN-003 | 數字跳動 | ScoreLabel | string | 舊分數 | 新分數 | 800 | Linear | 得分事件 | P1 |

---

## §5 粒子特效清單（Particle VFX）

| ID | 名稱 | 觸發條件 | 最大粒子數 | 存活時間(ms) | 循環 | 優先級 | 資產路徑 |
|----|------|---------|----------|------------|------|-------|---------|
| PTL-001 | {{NAME}} 命中特效 | 攻擊命中 | {{MAX_PARTICLES}} | {{LIFETIME}} | N | P0 | `particles/{{NAME}}.plist` |
| PTL-002 | 金幣散落 | 收集金幣 | {{MAX_PARTICLES}} | {{LIFETIME}} | N | P1 | `particles/coin_burst.plist` |
| PTL-003 | 環境粉塵 | 場景常駐 | {{MAX_PARTICLES}} | ∞ | Y | P2 | `particles/dust_ambient.plist` |

### §5.1 粒子特效技術規格

| 規格 | 值 | 說明 |
|------|---|------|
| 全局粒子數上限 | {{GLOBAL_PARTICLE_LIMIT}} | 超過此數自動 LOD 降級 |
| 單特效最大粒子 | {{SINGLE_VFX_LIMIT}} | 防止單一特效耗盡預算 |
| 粒子材質 Atlas | {{PARTICLE_ATLAS_SIZE}} | 所有粒子貼圖打包至同一圖集 |

---

## §6 Shader 特效清單

| ID | 名稱 | 適用對象 | Shader 類型 | 觸發條件 | 引擎 | 優先級 |
|----|------|---------|-----------|---------|------|-------|
| SHD-001 | 溶解消失 | 角色消亡 | Fragment | HP = 0 動畫末幀 | Cocos/Unity | P0 |
| SHD-002 | 描邊高亮 | 可選取物件 | Outline Post | hover/selected | Cocos/Unity/HTML5 | P1 |
| SHD-003 | 全屏閃光 | 勝利演出 | Full-screen Flash | win event | 全引擎 | P1 |
| SHD-004 | 模糊暫停遮罩 | 暫停介面背景 | Gaussian Blur | pause | 全引擎 | P2 |

### §6.1 Shader 技術規格

**Cocos Creator：**
```glsl
// 範例：Outline Shader（Effect 檔案位於 effects/outline.effect）
CCEffect %{
  techniques:
    - passes:
        - vert: vs_main
          frag: fs_main
          properties:
            outlineColor: { value: [1.0, 0.5, 0.0, 1.0], editor: { type: color } }
            outlineWidth: { value: 0.02 }
}%
```

**Unity（URP Shader Graph）：**
- Shader 資產路徑：`Assets/Shaders/{{SHADER_NAME}}.shadergraph`
- 渲染隊列：{{RENDER_QUEUE}}
- 支援 GPU Instancing：{{GPU_INSTANCING}}

**HTML5（GLSL + PixiJS Filter）：**
```javascript
class OutlineFilter extends PIXI.Filter {
  constructor(thickness = 1, color = 0xff8800) {
    super(vertSrc, fragSrc, { thickness, color: PIXI.utils.hex2rgb(color) });
  }
}
```

---

## §7 引擎特定設定

### §7.1 Cocos Creator

| 設定項 | 值 | 說明 |
|-------|---|------|
| 動畫系統 | `cc.Tween` / `cc.Animation` / Spine | 依動畫類型選擇 |
| 批次渲染 | 開啟 Dynamic Atlas | 同材質自動合批 |
| Spine 快取模式 | `SHARED_CACHE` | 多個相同骨骼角色共用快取 |
| 粒子系統 | `cc.ParticleSystem` | 2D 粒子；3D 用 `Particle System 3D` |
| 預製件動畫池 | 開啟物件池 | 高頻特效避免頻繁建立/銷毀 |

**Tween 管理規範：**
```typescript
// ✅ 正確：離開場景時清除 Tween
onDestroy() {
  cc.Tween.stopAllByTarget(this.node);
}

// ❌ 錯誤：忘記停止 Tween 導致空指標
```

### §7.2 Unity

| 設定項 | 值 | 說明 |
|-------|---|------|
| 動畫系統 | Animator + Timeline | 狀態機用 Animator，過場用 Timeline |
| Particle System | Built-in / VFX Graph | 2D 用 Built-in；URP/HDRP 用 VFX Graph |
| 動畫壓縮 | Optimal | 自動壓縮，節省記憶體 |
| GPU Skinning | 開啟 | 移動平台 CPU → GPU 卸載 |
| Culling Mode | Based on Renderers | 不在視野不更新動畫 |

**Animator 狀態機命名規範：**
```
Layer 0（Base Layer）：移動/待機等基礎動畫
Layer 1（Override）：攻擊、受傷等上半身動畫（Weight = 1）
```

### §7.3 HTML5（PixiJS + GSAP + CSS）

| 場景 | 技術 | 備註 |
|------|------|------|
| Sprite 骨骼動畫 | Spine-pixi / DragonBones-pixi | 需引入對應 runtime |
| 幀動畫 | `PIXI.AnimatedSprite` | 從 TextureAtlas 建立 |
| Tween 緩動 | GSAP `gsap.to()` | 統一使用 GSAP，不混用 TweenMax/Lite |
| CSS 過渡 | CSS `transition` / `@keyframes` | 只用於 UI 元素，不用於遊戲物件 |
| 粒子 | `pixi-particles` | 使用 Particle Designer 格式設定檔 |

```javascript
// GSAP 動畫範例（統一風格）
gsap.to(panel, {
  y: 0,
  duration: 0.3,
  ease: 'cubic.out',
  onComplete: () => panel.emit('show:complete'),
});
```

---

## §8 動畫資產規格與命名規範

### §8.1 命名規範

```
格式：{LAYER}_{MODULE}_{NAME}_{VARIANT}
範例：
  char_hero_idle_v1           ← 骨骼動畫檔名（不含副檔名）
  fx_hit_spark                ← 特效節點名稱
  anim_ui_panel_slidein       ← 幀動畫名稱
  ptl_coin_burst              ← 粒子特效設定檔
  shd_outline_selected        ← Shader 資產名稱
```

| 前綴 | 類型 |
|------|------|
| `char_` | 角色動畫 |
| `env_` | 環境/場景動畫 |
| `ui_` | UI 動畫 |
| `fx_` | 特效（非粒子） |
| `ptl_` | 粒子特效 |
| `shd_` | Shader |

### §8.2 資產目錄結構

```
assets/animations/          （骨骼動畫）
├── characters/
│   └── {{CHAR_NAME}}/
│       ├── {{CHAR_NAME}}.skel   （Spine）
│       ├── {{CHAR_NAME}}.atlas
│       └── {{CHAR_NAME}}.png
├── ui/                      （UI 幀動畫圖集）
└── env/                     （環境動畫）

assets/effects/             （特效）
├── particles/
│   └── *.plist / *.json
└── shaders/
    └── *.effect / *.shader

assets/textures/            （圖集）
└── spritesheets/
    └── {{MODULE}}_atlas.png + .plist
```

---

## §9 效能預算

| 指標 | 目標值 | 警戒值 | 量測方式 |
|------|-------|-------|---------|
| 幀率 | {{TARGET_FPS}} fps | < {{WARN_FPS}} fps | 目標裝置 Profiler |
| Draw Call（含特效） | ≤ {{MAX_DC}} | > {{WARN_DC}} | 引擎 Profiler |
| 全局粒子數 | ≤ {{MAX_PARTICLES}} | > {{WARN_PARTICLES}} | Profiler |
| 骨骼節點數（單角色） | ≤ {{MAX_BONES}} | > {{WARN_BONES}} | 美術規格 |
| 動畫記憶體（骨骼圖集） | ≤ {{ANIM_MEM}}MB | > {{ANIM_WARN}}MB | Profiler |
| Shader Pass 數 | ≤ {{SHADER_PASS}} | > {{SHADER_WARN}} | 減少 overdraw |

### §9.1 LOD（Level of Detail）策略

| 裝置等級 | 判斷條件 | 調整項目 |
|---------|---------|---------|
| 高階 | RAM ≥ 4GB + GPU 分數 ≥ {{HIGH_GPU}} | 全特效，最高粒子數 |
| 中階 | RAM 2-4GB | 關閉 P2 特效，粒子數減半 |
| 低階 | RAM < 2GB | 關閉所有粒子，Shader 降級至基礎版 |

---

## §10 測試清單

| ID | 測試項目 | 方法 | 通過條件 |
|----|---------|------|---------|
| ANIM-T-001 | 所有 P0 骨骼動畫狀態機轉換 | 遍歷 §2.1 所有路徑 | 無卡動、無跳幀 |
| ANIM-T-002 | 高頻觸發特效不超過粒子預算 | 壓力測試：10 個同屏特效 | Profiler 粒子數 ≤ §9 上限 |
| ANIM-T-003 | 目標裝置幀率 | 在最低規格裝置執行完整場景 | ≥ {{MIN_FPS}} fps |
| ANIM-T-004 | 場景切換無殘留 Tween/粒子 | 切換場景後檢查 Profiler | 無記憶體洩漏，粒子歸零 |
| ANIM-T-005 | Shader 特效在各平台顯示正確 | iOS / Android / Web Chrome 截圖對比 | 視覺一致，無黑塊/花屏 |
| ANIM-T-006 | 動畫暫停/恢復 | 暫停→背景→恢復 | 動畫從暫停點繼續，無跳動 |
| ANIM-T-007 | Draw Call 預算 | Profiler 量測戰鬥場景最繁忙幀 | DC ≤ §9 目標值 |
| ANIM-T-008 | 低階裝置 LOD 降級生效 | 模擬低階裝置（限制 RAM） | P2 特效正確關閉，fps 達標 |
