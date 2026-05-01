# CLIENT_IMPL — Client Implementation Specification（客戶端實作規格書）
<!-- 對應 SDLC Layer 4：Implementation Engineering -->
<!-- 本文件回答：「設計意圖如何轉成具體的客戶端代碼結構？」 -->
<!-- 上游：EDD（架構） + VDD（視覺） + ANIM（動畫） + AUDIO（音效） -->
<!-- 下游：開發人員直接依此文件實作，無需再做設計決策 -->
<!--
⚠️ 範圍說明：本文件覆蓋 C 端客戶端（Cocos Creator / Unity / React / HTML5 等）。
   Vue3 Admin 後台不在本文件範圍內，見 docs/ADMIN_IMPL.md。
   若 EDD §3.3 _ADMIN_FRAMEWORK 偵測到 Vue3 Admin，gen agent 應跳過本文件
   並確認 ADMIN_IMPL.md 已生成。
-->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | CLIENT_IMPL-{{PROJECT_CODE}}-{{YYYYMMDD}} |
| **專案名稱** | {{PROJECT_NAME}} |
| **客戶端引擎／框架** | {{CLIENT_ENGINE}}（Cocos Creator / Unity WebGL / React / Vue / HTML5） |
| **引擎版本** | {{ENGINE_VERSION}} |
| **目標平台** | {{TARGET_PLATFORM}}（Web / iOS / Android / Desktop） |
| **文件版本** | v1.0 |
| **狀態** | DRAFT / IN_REVIEW / APPROVED |
| **作者** | {{AUTHOR}} |
| **日期** | {{DATE}} |
| **上游 EDD** | [EDD.md](EDD.md) |
| **上游 VDD** | [VDD.md](VDD.md)（若有） |
| **上游 ANIM** | [ANIM.md](ANIM.md)（若有） |
| **上游 AUDIO** | [AUDIO.md](AUDIO.md)（若有） |

---

## Change Log

| 版本 | 日期 | 作者 | 變更摘要 |
|------|------|------|---------|
| v1.0 | {{DATE}} | {{AUTHOR}} | 初稿 |

---

## §1 客戶端概覽（Client Overview）

### §1.1 引擎 / 框架選型說明

| 項目 | 規格 |
|------|------|
| **引擎 / 框架** | {{CLIENT_ENGINE}} |
| **版本** | {{ENGINE_VERSION}} |
| **語言** | {{LANGUAGE}}（TypeScript / C# / JavaScript） |
| **建置工具** | {{BUILD_TOOL}}（Webpack / Vite / Cocos Build / Unity Build） |
| **目標平台** | {{TARGET_PLATFORM}} |
| **最低瀏覽器 / OS 支援** | {{MIN_SUPPORT}} |

### §1.2 選型理由

{{CLIENT_ENGINE_RATIONALE}}

### §1.3 與後端整合方式

| 整合點 | 方式 |
|--------|------|
| API 呼叫 | {{API_INTEGRATION}}（REST / GraphQL / WebSocket） |
| 認證 | {{AUTH_METHOD}} |
| 資料同步 | {{DATA_SYNC_METHOD}} |

---

## §2 專案結構（Project Structure）

### §2.1 目錄結構

```
{{PROJECT_DIR_TREE}}
```

<!-- Cocos Creator 範例：
assets/
  scenes/         ← .scene 場景文件
  prefabs/        ← Prefab 預製體
  scripts/        ← TypeScript 組件
  resources/      ← 動態載入資源
  bundles/        ← Asset Bundle 分包
  textures/       ← 圖片資源
  audio/          ← 音效資源
  animations/     ← AnimationClip
  spine/          ← Spine 骨骼動畫
-->

<!-- React / Vue 範例：
src/
  components/     ← UI 組件
  pages/          ← 頁面組件（路由對應）
  store/          ← 狀態管理
  hooks/          ← 自訂 hooks（React）/ composables（Vue）
  assets/         ← 靜態資源
  services/       ← API 呼叫層
  styles/         ← 全域樣式
-->

### §2.2 命名規範

| 類型 | 規範 | 範例 |
|------|------|------|
| **場景 / 頁面** | {{SCENE_NAMING}} | `GameMain.scene` / `HomePage.tsx` |
| **組件 / 腳本** | {{COMPONENT_NAMING}} | `PlayerController.ts` / `GameCard.vue` |
| **圖片資源** | {{TEXTURE_NAMING}} | `ui_btn_play_normal.png` |
| **音效資源** | {{AUDIO_NAMING}} | `sfx_coin_collect.mp3` |
| **動畫** | {{ANIM_NAMING}} | `player_run_loop.anim` |
| **Prefab / 組件** | {{PREFAB_NAMING}} | `EnemyBase.prefab` |

---

## §3 場景 / 頁面 / 視圖結構（Scene & View Architecture）

<!-- ════════════════════════════════════════════════
     §3 因引擎不同，結構差異最大的章節
     gen.md 會依 CLIENT_ENGINE 展開對應版本
     ════════════════════════════════════════════════ -->

### §3.1 場景 / 頁面清單

| ID | 名稱 | 說明 | 觸發條件 |
|----|------|------|---------|
| {{SCENE_ID}} | {{SCENE_NAME}} | {{SCENE_DESC}} | {{SCENE_TRIGGER}} |

### §3.2 主場景 / 主頁面結構

<!-- [ENGINE_SPECIFIC_STRUCTURE] -->
{{MAIN_SCENE_STRUCTURE}}

### §3.3 場景 / 頁面切換邏輯

| 來源 | 目標 | 觸發事件 | 過渡效果 |
|------|------|---------|---------|
| {{FROM_SCENE}} | {{TO_SCENE}} | {{TRIGGER_EVENT}} | {{TRANSITION}} |

---

## §4 資源規範（Asset Pipeline）

### §4.1 資源目錄結構

```
{{ASSET_DIR_STRUCTURE}}
```

### §4.2 資源命名規範

| 資源類型 | 前綴 / 後綴規則 | 範例 |
|---------|--------------|------|
| UI 按鈕 | `ui_btn_{name}_{state}` | `ui_btn_play_normal.png` |
| 角色貼圖 | `char_{name}_{action}` | `char_hero_idle.png` |
| 背景 | `bg_{scene}_{layer}` | `bg_game_sky.png` |
| 特效貼圖 | `fx_{name}` | `fx_explosion_01.png` |
| 音效 | `sfx_{category}_{name}` | `sfx_ui_click.mp3` |
| 背景音樂 | `bgm_{scene}` | `bgm_main_menu.mp3` |
| 動畫 | `anim_{character}_{action}` | `anim_hero_run.anim` |

### §4.3 資源載入策略

<!-- [ENGINE_SPECIFIC_LOADING] -->

| 資源類型 | 載入方式 | 時機 | 備注 |
|---------|---------|------|------|
| {{ASSET_TYPE}} | {{LOAD_METHOD}} | {{LOAD_TIMING}} | {{NOTES}} |

### §4.4 資源 Budget

| 類型 | 上限 | 備注 |
|------|------|------|
| 單張貼圖 | {{MAX_TEXTURE_SIZE}} | 超出需切圖集 |
| 音效（SFX） | {{MAX_SFX_SIZE}} | 建議 OGG 格式 |
| 背景音樂 | {{MAX_BGM_SIZE}} | 串流播放 |
| 總包體大小 | {{MAX_BUNDLE_SIZE}} | 首包 + 分包 |

---

## §5 動畫整合規格（Animation Integration）

<!-- 上游：ANIM.md -->

### §5.1 動畫清單

| 動畫 ID | 名稱 | 對象 | 時長 | 循環 | 觸發條件 |
|--------|------|------|------|------|---------|
| {{ANIM_ID}} | {{ANIM_NAME}} | {{TARGET}} | {{DURATION}} | {{LOOP}} | {{TRIGGER}} |

### §5.2 動畫觸發事件對應表

<!-- [ENGINE_SPECIFIC_ANIMATION] -->

| 遊戲事件 / UI 事件 | 觸發的動畫 | 實作方式 |
|-----------------|-----------|---------|
| {{GAME_EVENT}} | {{ANIM_NAME}} | {{IMPL_METHOD}} |

### §5.3 動畫狀態機（State Machine）

<!-- 若有複雜狀態切換，描述狀態機設計 -->

```
{{ANIMATION_STATE_MACHINE}}
```

### §5.4 動畫效能規範

| 規範 | 上限 | 說明 |
|------|------|------|
| 同屏同時播放動畫數 | {{MAX_CONCURRENT_ANIMS}} | |
| 單個 Spine/Animator 骨骼數 | {{MAX_BONES}} | |
| AnimationClip 最長時長 | {{MAX_CLIP_DURATION}} | 超出需分段 |

---

## §6 音效整合規格（Audio Integration）

<!-- 上游：AUDIO.md -->

### §6.1 音效清單

| 音效 ID | 名稱 | 類型 | 檔案 | 觸發條件 | 音量 | 循環 |
|--------|------|------|------|---------|------|------|
| {{AUDIO_ID}} | {{AUDIO_NAME}} | SFX/BGM/UI | {{FILE}} | {{TRIGGER}} | {{VOLUME}} | {{LOOP}} |

### §6.2 音效觸發事件對應表

<!-- [ENGINE_SPECIFIC_AUDIO] -->

| 遊戲事件 / UI 事件 | 播放音效 | 停止音效 | 實作方式 |
|-----------------|---------|---------|---------|
| {{GAME_EVENT}} | {{PLAY_SFX}} | {{STOP_SFX}} | {{IMPL_METHOD}} |

### §6.3 音效管理架構

<!-- [ENGINE_SPECIFIC_AUDIO_MANAGER] -->

{{AUDIO_MANAGER_DESIGN}}

### §6.4 音效效能規範

| 規範 | 上限 |
|------|------|
| 同時播放音效數 | {{MAX_CONCURRENT_SFX}} |
| 音效預載快取大小 | {{AUDIO_CACHE_SIZE}} |

---

## §7 視覺特效整合規格（VFX Integration）

<!-- 上游：VDD.md -->

### §7.1 特效清單

| 特效 ID | 名稱 | 類型 | 觸發時機 | 觸發條件 | 生命週期 |
|--------|------|------|---------|---------|---------|
| {{VFX_ID}} | {{VFX_NAME}} | {{VFX_TYPE}} | {{TIMING}} | {{TRIGGER}} | {{LIFECYCLE}} |

### §7.2 特效觸發對應表

<!-- [ENGINE_SPECIFIC_VFX] -->

| 遊戲事件 / UI 事件 | 播放特效 | 特效實作方式 |
|-----------------|---------|-----------|
| {{GAME_EVENT}} | {{VFX_NAME}} | {{IMPL_METHOD}} |

### §7.3 特效效能規範

| 規範 | 上限 |
|------|------|
| 同屏同時播放特效數 | {{MAX_CONCURRENT_VFX}} |
| 單個粒子系統最大粒子數 | {{MAX_PARTICLES}} |

---

## §8 UI Flow 狀態機（UI State Machine）

### §8.1 UI 狀態清單

| 狀態 ID | 名稱 | 說明 | 顯示的 UI 元素 |
|--------|------|------|--------------|
| {{UI_STATE_ID}} | {{UI_STATE_NAME}} | {{UI_STATE_DESC}} | {{VISIBLE_UI}} |

### §8.2 狀態切換規則

| 當前狀態 | 事件 | 下一狀態 | 副作用（動畫/音效） |
|---------|------|---------|-----------------|
| {{FROM_STATE}} | {{EVENT}} | {{TO_STATE}} | {{SIDE_EFFECTS}} |

### §8.3 Loading / Error 狀態處理

| 狀態 | 顯示方式 | 逾時處理 | 重試策略 |
|------|---------|---------|---------|
| Loading | {{LOADING_UI}} | {{TIMEOUT}} | {{RETRY}} |
| Error | {{ERROR_UI}} | — | {{ERROR_RETRY}} |
| Network Lost | {{NETWORK_UI}} | — | {{RECONNECT}} |

---

## §9 API 整合規格（API Integration）

### §9.1 API 呼叫清單

| API | 觸發時機 | 請求 | 回應處理 | 錯誤處理 |
|-----|---------|------|---------|---------|
| {{API_NAME}} | {{TRIGGER}} | {{REQUEST}} | {{RESPONSE_HANDLER}} | {{ERROR_HANDLER}} |

### §9.2 狀態同步策略

| 資料類型 | 同步方式 | 頻率 / 事件 | 衝突處理 |
|---------|---------|-----------|---------|
| {{DATA_TYPE}} | {{SYNC_METHOD}} | {{FREQUENCY}} | {{CONFLICT}} |

### §9.3 離線 / 弱網處理

{{OFFLINE_STRATEGY}}

---

## §10 效能規範（Performance Budget）

### §10.1 渲染效能

| 指標 | 目標 | 最低可接受 |
|------|------|----------|
| FPS（遊戲場景） | {{TARGET_FPS}} fps | {{MIN_FPS}} fps |
| 初始載入時間 | < {{LOAD_TIME}} s | < {{MAX_LOAD_TIME}} s |
| 場景切換時間 | < {{SCENE_SWITCH}} ms | — |
| LCP（Web） | < {{LCP}} ms | — |
| TTI（Web） | < {{TTI}} ms | — |

### §10.2 記憶體 Budget

| 類型 | 上限 |
|------|------|
| 總記憶體使用 | < {{MAX_MEMORY}} MB |
| 紋理記憶體 | < {{MAX_TEXTURE_MEM}} MB |
| 音效緩衝 | < {{MAX_AUDIO_MEM}} MB |

### §10.3 Bundle / 包體 Budget

| Bundle 類型 | 大小上限 | 說明 |
|-----------|---------|------|
| 首包（Entry） | < {{ENTRY_BUNDLE}} KB | 首屏可見前完成載入 |
| 主遊戲包 | < {{MAIN_BUNDLE}} MB | |
| 各分包 | < {{SUB_BUNDLE}} MB | |

---

## §11 測試規範（Test Specification）

### §11.1 單元測試範圍

| 模組 | 測試重點 | 覆蓋率目標 |
|------|---------|----------|
| {{MODULE}} | {{TEST_FOCUS}} | {{COVERAGE}}% |

### §11.2 整合測試清單

| 測試場景 | 前置條件 | 預期結果 |
|---------|---------|---------|
| {{TEST_SCENARIO}} | {{PRECONDITION}} | {{EXPECTED}} |

### §11.3 效能測試條件

| 測試項目 | 工具 | 通過條件 |
|---------|------|---------|
| FPS 壓力測試 | {{PERF_TOOL}} | > {{MIN_FPS}} fps |
| 首包載入 | Lighthouse / 自訂 | < {{MAX_LOAD_TIME}} s |
| 記憶體洩漏 | {{MEM_TOOL}} | 無洩漏 |

---

## §12 已知限制與技術債（Known Limitations）

| 項目 | 說明 | 影響 | 預計解決版本 |
|------|------|------|------------|
| {{LIMITATION}} | {{DESC}} | {{IMPACT}} | {{TARGET_VERSION}} |
