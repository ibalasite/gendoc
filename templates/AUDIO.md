---
doc-type: AUDIO
output-path: docs/AUDIO.md
layer: 設計層
condition: client_type != none
upstream:
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/EDD.md
  - docs/FRONTEND.md
---

# 音效設計文件（Audio Design Document）
<!-- Version: {{VERSION}} | Status: {{STATUS}} | DOC-ID: AUDIO-{{PROJECT}}-{{DATE}} -->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | AUDIO-{{PROJECT}}-{{DATE}} |
| **文件名稱** | 音效設計文件（Audio Design Document） |
| **文件版本** | {{VERSION}} |
| **狀態** | {{STATUS}} |
| **作者** | {{AUTHOR}} |
| **日期** | {{DATE}} |
| **適用引擎** | {{ENGINE}} （Cocos Creator / Unity / HTML5 Web Audio / Howler.js） |
| **上游文件** | IDEA.md · BRD.md · PRD.md · EDD.md · FRONTEND.md |
| **審閱者** | 音效設計師、技術音效工程師 |

---

## Change Log

| 版本 | 日期 | 作者 | 變更摘要 |
|------|------|------|---------|
| v1.0 | {{DATE}} | {{AUTHOR}} | 初版 |

---

## §1 音效設計目標與情感設定

### §1.1 設計目標

| 目標 | 描述 |
|------|------|
| **情感目標** | {{EMOTIONAL_GOAL}} |
| **沉浸感策略** | {{IMMERSION_STRATEGY}} |
| **品牌音效識別** | {{AUDIO_BRANDING}} |

### §1.2 音效設計原則

- {{PRINCIPLE_1}}
- {{PRINCIPLE_2}}
- {{PRINCIPLE_3}}

### §1.3 目標平台音效限制

| 平台 | 同時播放上限 | 格式限制 | 備註 |
|------|------------|---------|------|
| iOS | {{IOS_CHANNELS}} | {{IOS_FORMAT}} | {{IOS_NOTE}} |
| Android | {{ANDROID_CHANNELS}} | {{ANDROID_FORMAT}} | {{ANDROID_NOTE}} |
| Web（Chrome/Firefox/Safari） | {{WEB_CHANNELS}} | {{WEB_FORMAT}} | {{WEB_NOTE}} |
| PC / Mac | {{PC_CHANNELS}} | {{PC_FORMAT}} | {{PC_NOTE}} |

---

## §2 BGM 清單（背景音樂）

| ID | 名稱 | 場景/狀態 | 時長（秒） | 循環 | 淡入（ms） | 淡出（ms） | 檔案路徑 | 備註 |
|----|------|---------|----------|------|----------|----------|---------|------|
| BGM-001 | {{NAME}} | {{SCENE}} | {{DURATION}} | Y/N | {{FADE_IN}} | {{FADE_OUT}} | `audio/bgm/{{FILENAME}}.mp3` | {{NOTE}} |

### §2.1 BGM 切換規則

```
狀態A（{{STATE_A}}）→ 淡出 {{FADE_MS}}ms → 靜默 {{SILENT_MS}}ms → 淡入 → 狀態B（{{STATE_B}}）
```

---

## §3 SFX 清單（音效）

### §3.1 UI 音效

| ID | 名稱 | 觸發事件 | 優先級 | 可打斷 | 最大同播數 | 檔案路徑 |
|----|------|---------|-------|-------|----------|---------|
| SFX-UI-001 | {{NAME}} | {{EVENT}} | {{PRIORITY}} | Y/N | {{MAX_INSTANCES}} | `audio/sfx/ui/{{FILENAME}}.mp3` |

### §3.2 遊戲/互動 音效

| ID | 名稱 | 觸發事件 | 優先級 | 可打斷 | 最大同播數 | 檔案路徑 |
|----|------|---------|-------|-------|----------|---------|
| SFX-GAME-001 | {{NAME}} | {{EVENT}} | {{PRIORITY}} | Y/N | {{MAX_INSTANCES}} | `audio/sfx/game/{{FILENAME}}.mp3` |

### §3.3 環境音效（Ambient）

| ID | 名稱 | 場景 | 循環 | 音量 | 檔案路徑 |
|----|------|------|------|------|---------|
| SFX-AMB-001 | {{NAME}} | {{SCENE}} | Y/N | {{VOLUME}} | `audio/sfx/ambient/{{FILENAME}}.mp3` |

---

## §4 語音／旁白清單（Voice / VO）

| ID | 名稱 | 文本內容 | 觸發條件 | 語言 | 檔案路徑 |
|----|------|---------|---------|------|---------|
| VO-001 | {{NAME}} | {{TEXT}} | {{TRIGGER}} | {{LANG}} | `audio/vo/{{LANG}}/{{FILENAME}}.mp3` |

---

## §5 音效觸發邏輯（狀態機）

### §5.1 音效優先級定義

| 優先級 | 數值 | 說明 | 範例 |
|-------|------|------|------|
| CRITICAL | 10 | 不可打斷，必播 | 勝利/失敗 jingle |
| HIGH | 7 | 可打斷低優先級 | 技能音效 |
| MEDIUM | 5 | 一般互動音效 | 按鈕點擊 |
| LOW | 2 | 環境音、BGM | 背景環境 |

### §5.2 觸發條件矩陣

```
遊戲狀態：{{STATE}}
├─ 進入  → 播放 {{BGM_ID}}（淡入 {{FADE_IN}}ms）
├─ {{EVENT_1}} → 播放 {{SFX_ID_1}}
├─ {{EVENT_2}} → 播放 {{SFX_ID_2}}（if 靜音 → skip）
└─ 離開  → 淡出 {{BGM_ID}}（{{FADE_OUT}}ms）
```

### §5.3 音效互斥規則

| 規則 | 說明 |
|------|------|
| BGM 唯一 | 同一時間只播放一條 BGM，切換時必須先淡出 |
| SFX 同 ID 打斷 | 同一 SFX 再次觸發時，打斷前一個實例（避免疊音） |
| VO 隊列 | 語音依隊列順序播放，不同時播放多條 |

---

## §6 音效引擎設定

### §6.1 Cocos Creator（AudioEngine / AudioSource）

```typescript
// 初始化音效管理器
const audioMgr = AudioManager.getInstance();
audioMgr.setBGMVolume({{BGM_VOLUME}});    // 0.0 ~ 1.0
audioMgr.setSFXVolume({{SFX_VOLUME}});    // 0.0 ~ 1.0
audioMgr.setMaxChannels({{MAX_CHANNELS}}); // 建議 16~24

// BGM 播放（帶淡入）
audioMgr.playBGM('audio/bgm/{{FILENAME}}', {{FADE_IN_SEC}});

// SFX 播放
audioMgr.playSFX('audio/sfx/{{FILENAME}}');
```

**AudioSource 元件設定：**

| 參數 | 值 | 說明 |
|------|---|------|
| `loop` | {{LOOP}} | BGM 設 true，SFX 設 false |
| `playOnAwake` | false | 由程式控制，不自動播放 |
| `volume` | {{VOLUME}} | 初始音量 |

### §6.2 Unity（AudioMixer / AudioSource）

```
AudioMixer 結構：
Master
├── BGM_Group（volume: {{BGM_VOLUME}}dB）
│   └── BGM_Snapshot_{{STATE}}
├── SFX_Group（volume: {{SFX_VOLUME}}dB）
│   ├── SFX_UI
│   └── SFX_Game
└── VO_Group（volume: {{VO_VOLUME}}dB）
```

```csharp
// BGM 淡切（CrossFade）
AudioManager.Instance.CrossFadeBGM("BGM_{{STATE}}", fadeDuration: {{FADE_SEC}}f);

// SFX 播放
AudioManager.Instance.PlaySFX(SFXType.{{SFX_ENUM}});
```

**Snapshot 切換：**

| Snapshot | 觸發時機 | Reach Time（sec） |
|---------|---------|-----------------|
| `Normal` | 正常遊戲狀態 | {{REACH_TIME}} |
| `Pause` | 遊戲暫停 | {{REACH_TIME}} |
| `LowHP` | 血量低於 30% | {{REACH_TIME}} |

### §6.3 HTML5（Web Audio API / Howler.js）

```javascript
// Howler.js 初始化
const bgmSound = new Howl({
  src: ['audio/bgm/{{FILENAME}}.webm', 'audio/bgm/{{FILENAME}}.mp3'],
  loop: true,
  volume: {{BGM_VOLUME}},
  autoplay: false,
  preload: true,
  html5: {{USE_HTML5_STREAMING}},  // 大檔案串流用 true
});

// SFX Sprite（合併音效以減少 HTTP 請求）
const sfxSprite = new Howl({
  src: ['audio/sfx/sprite.webm', 'audio/sfx/sprite.mp3'],
  sprite: {
    btn_click: [0, 300],      // [offset_ms, duration_ms]
    btn_hover: [400, 200],
    // ... 依 SFX 清單填入
  },
});
```

**Web Audio Context 解鎖（iOS/Chrome 要求用戶互動）：**

```javascript
// 必須在首次用戶點擊後呼叫
document.addEventListener('click', () => {
  if (Howler.ctx?.state === 'suspended') Howler.ctx.resume();
}, { once: true });
```

---

## §7 音效資產規格與命名規範

### §7.1 命名規範

```
格式：{TYPE}_{MODULE}_{DESC}_{VARIANT}.{EXT}
範例：
  bgm_lobby_main_v1.mp3
  sfx_ui_btn_click.mp3
  sfx_game_explosion_large.mp3
  vo_tutorial_step01_zh.mp3
```

| 前綴 | 類型 | 範例 |
|------|------|------|
| `bgm_` | 背景音樂 | `bgm_battle_main.mp3` |
| `sfx_ui_` | UI 音效 | `sfx_ui_confirm.mp3` |
| `sfx_game_` | 遊戲音效 | `sfx_game_hit_001.mp3` |
| `sfx_amb_` | 環境音 | `sfx_amb_ocean.mp3` |
| `vo_` | 語音 | `vo_tutorial_01_zh.mp3` |

### §7.2 格式與壓縮規格

| 類型 | 主格式 | 備用格式 | 位元率 | 取樣率 | 聲道 | 備註 |
|------|-------|---------|-------|-------|------|------|
| BGM | `.mp3` | `.ogg` | 128 kbps | 44.1 kHz | 立體聲 | iOS 優先 mp3 |
| SFX（短） | `.mp3` | `.ogg` | 96 kbps | 44.1 kHz | 單聲道 | < 3 秒 |
| SFX（長/環境） | `.mp3` | `.ogg` | 128 kbps | 44.1 kHz | 立體聲 | ≥ 3 秒 |
| VO | `.mp3` | — | 64 kbps | 22.05 kHz | 單聲道 | 語音壓縮 |
| HTML5 SFX Sprite | `.webm` | `.mp3` | 96 kbps | 44.1 kHz | 單聲道 | 主 webm，備 mp3 |

### §7.3 資產目錄結構

```
assets/audio/              （或依引擎調整路徑）
├── bgm/
│   └── bgm_*.mp3
├── sfx/
│   ├── ui/
│   ├── game/
│   └── ambient/
└── vo/
    ├── zh/
    └── en/
```

---

## §8 音效載入策略

| 類型 | 載入時機 | 載入方式 | 記憶體策略 |
|------|---------|---------|----------|
| BGM（首場景） | 應用啟動後背景預載 | 串流（html5: true）/ 背景載入 | 場景切換時卸載舊 BGM |
| BGM（其他場景） | 進場景前預載 | 背景非同步 | 進場景完成後才可播放 |
| SFX（P0 核心） | 啟動時預載 | 打包進資源包 | 常駐記憶體 |
| SFX（P1/P2） | 首次觸發前 | 懶載入 + cache | 超過 LRU 上限則卸載 |
| VO | 對話觸發前 | 按需下載 | 播放完畢即釋放 |

---

## §9 效能預算

| 指標 | 目標值 | 警戒值 | 說明 |
|------|-------|-------|------|
| 同時播放頻道數 | ≤ {{MAX_CHANNELS}} | > {{WARN_CHANNELS}} | 含 BGM + SFX + VO |
| 單幀音效 CPU 占用 | < {{CPU_BUDGET}}% | > {{CPU_WARN}}% | 在目標裝置量測 |
| 音效資源包體積 | < {{BUNDLE_SIZE}}MB | > {{BUNDLE_WARN}}MB | 首包中的音效資源 |
| BGM 記憶體 | < {{BGM_MEM}}MB | — | 單條 BGM 解碼後 |
| 總音效記憶體 | < {{TOTAL_AUDIO_MEM}}MB | — | 常駐預載音效總量 |

---

## §10 測試清單

| ID | 測試項目 | 方法 | 通過條件 |
|----|---------|------|---------|
| AUD-T-001 | BGM 切換無爆音 | 手動測試各場景切換 | 無明顯爆音、過渡自然 |
| AUD-T-002 | SFX 高頻觸發不疊音 | 快速連點 > 10 次 | 不超過 maxInstances 上限 |
| AUD-T-003 | 靜音設定持久化 | 關閉後重啟 | 靜音狀態正確恢復 |
| AUD-T-004 | 音量設定持久化 | 調整音量後重啟 | 音量值正確恢復 |
| AUD-T-005 | iOS 首次播放解鎖 | iOS Safari 測試 | 點擊後 BGM/SFX 正常播放 |
| AUD-T-006 | 背景切換靜音 | 切至背景 App | BGM 暫停，恢復時繼續播放 |
| AUD-T-007 | 弱網環境音效載入 | 模擬 3G 網路 | Loading 顯示正確，不 crash |
| AUD-T-008 | 所有 SFX 觸發覆蓋 | 依 §3 清單逐一觸發 | 每條音效正確播放，無 404 |
