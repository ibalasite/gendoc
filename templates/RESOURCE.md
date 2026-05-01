---
doc-type: RESOURCE
output-path: docs/RESOURCE.md
upstream-docs:
  - docs/FRONTEND.md   # 前端框架選型、客戶端引擎
  - docs/EDD.md        # §3.3 技術棧（引擎/語言/框架決策）
  - docs/PRD.md        # 功能需求（資源使用場景）
  - docs/PDD.md        # §4 UI 設計（動畫、音效、視覺風格）
version: "{{RESOURCE_DOC_VERSION}}"
last-updated: "{{LAST_UPDATED_DATE}}"
---

# {{PROJECT_NAME}} — Frontend / Client Resource List

> **用途**：本文件列出所有前端 / 客戶端資源的清單，包含動畫、音效、視覺資產、字型、3D 模型等。  
> 確保任何選擇的客戶端引擎（Unity / Cocos / React / Vue / Flutter 等）所需的資源規格均有明確定義。  
> 此文件與 `docs/FRONTEND.md`、`docs/EDD.md §3.3` 保持一致。

---

## Change Log

| 版本 | 日期 | 作者 | 修改說明 |
|------|------|------|---------|
| {{VERSION}} | {{DATE}} | {{AUTHOR}} | {{CHANGE}} |

---

## §1 文件目的與範圍

**目的**：定義所有前端 / 客戶端資源規格，確保：
- 設計師、工程師、技術美術在同一份清單下協作
- 資源規格（解析度、格式、壓縮方式、命名規則）標準化
- 效能預算（記憶體、包體大小、載入時間）可追蹤

**範圍**：本文件涵蓋以下資源類型：
- 動畫資源（Anim / Spine / Skeleton）
- 音效資源（Audio / BGM / SFX）
- 視覺資源（Texture / Sprite / UI Atlas）
- 字型資源（Font）
- 3D 模型（Mesh / Prefab，若適用）
- 影片資源（Video，若適用）
- 本地化資源（i18n string table，若適用）

**不涵蓋**：程式碼、API 規格、資料庫 Schema。

---

## §2 客戶端引擎與資源系統

| 項目 | 規格 |
|------|------|
| 客戶端引擎 | {{CLIENT_ENGINE}}（Unity 6 / Cocos Creator 3.x / React / Vue 3 / Flutter 等）|
| 資源管理方式 | {{ASSET_MANAGEMENT}}（Unity Addressables / Cocos Bundle / CDN Static / 自研 Asset Loader）|
| 資源打包工具 | {{BUILD_TOOL}}（TexturePacker / Spine / Unity AssetBundle / webpack 等）|
| 預設資源路徑 | `{{ASSET_BASE_PATH}}`（如 `assets/` / `Resources/` / `StreamingAssets/` / CDN 根路徑）|
| 資源版本控制 | {{VERSIONING}}（Git LFS / DVC / S3 Versioning / CDN Cache Busting）|

---

## §3 Animation 資源清單（ANIM）

<!-- 若無動畫需求，填入「本專案無動畫資源需求」並略過本節 -->

### §3.1 動畫技術選型

| 動畫類型 | 工具 / 格式 | 引擎整合方式 |
|---------|------------|------------|
| UI 動畫 | {{UI_ANIM_TOOL}}（如 Spine / DoTween / CSS Animation / Lottie）| {{UI_ANIM_INTEGRATION}} |
| 角色動畫 | {{CHAR_ANIM_TOOL}}（如 Unity Animator / Cocos Skeleton / Spine）| {{CHAR_ANIM_INTEGRATION}} |
| 過場動畫 | {{CUTSCENE_TOOL}}（如 Unity Timeline / Video / Lottie）| {{CUTSCENE_INTEGRATION}} |

### §3.2 動畫資源規格

| 規格項目 | 要求 |
|---------|------|
| 幀率（Frame Rate）| {{ANIM_FPS}}（如 24fps / 30fps / 60fps）|
| 最大動畫時長 | {{MAX_ANIM_DURATION}}（如 ≤ 5s for UI 動畫）|
| 檔案格式 | {{ANIM_FORMAT}}（如 `.skel` + `.atlas` / `.anim` / `.json`）|
| 單檔大小限制 | {{ANIM_SIZE_LIMIT}}（如 ≤ 2MB）|
| 命名規則 | `{{ANIM_NAMING_CONVENTION}}`（如 `char_hero_idle.skel`）|

### §3.3 動畫資源清單

| 資源 ID | 名稱 | 類型 | 觸發場景 | 優先級 | 狀態 |
|---------|------|------|---------|-------|------|
| ANIM-001 | {{ANIM_001_NAME}} | {{TYPE}} | {{TRIGGER_SCENE}} | P0 | TODO |
| ANIM-002 | {{ANIM_002_NAME}} | {{TYPE}} | {{TRIGGER_SCENE}} | P1 | TODO |
| {{ANIM_ID}} | {{NAME}} | {{TYPE}} | {{TRIGGER}} | {{PRIORITY}} | {{STATUS}} |

---

## §4 Audio 資源清單（AUDIO）

<!-- 若無音效需求，填入「本專案無音效資源需求」並略過本節 -->

### §4.1 音效技術選型

| 音效類型 | 工具 / 格式 | 引擎整合方式 |
|---------|------------|------------|
| 背景音樂（BGM）| {{BGM_TOOL}}（如 Unity AudioSource / Cocos AudioClip / Web Audio API）| {{BGM_INTEGRATION}} |
| 音效（SFX）| {{SFX_TOOL}} | {{SFX_INTEGRATION}} |
| 語音（Voice）| {{VOICE_TOOL}}（若有對話語音）| {{VOICE_INTEGRATION}} |

### §4.2 音效資源規格

| 規格項目 | BGM | SFX |
|---------|-----|-----|
| 檔案格式 | {{BGM_FORMAT}}（如 `.ogg` / `.mp3`）| {{SFX_FORMAT}}（如 `.wav` / `.ogg`）|
| 取樣率 | {{BGM_SAMPLE_RATE}}（如 44100 Hz）| {{SFX_SAMPLE_RATE}}（如 22050 Hz）|
| 位元深度 | {{BGM_BIT_DEPTH}}（如 16-bit）| {{SFX_BIT_DEPTH}}（如 16-bit）|
| 單檔大小限制 | {{BGM_SIZE_LIMIT}}（如 ≤ 5MB）| {{SFX_SIZE_LIMIT}}（如 ≤ 500KB）|
| 命名規則 | `{{BGM_NAMING}}`（如 `bgm_main_theme.ogg`）| `{{SFX_NAMING}}`（如 `sfx_btn_click.ogg`）|

### §4.3 音效資源清單

| 資源 ID | 名稱 | 類型 | 觸發場景 | 循環 | 優先級 | 狀態 |
|---------|------|------|---------|------|-------|------|
| AUDIO-001 | {{AUDIO_001_NAME}} | BGM | {{TRIGGER}} | Yes | P0 | TODO |
| AUDIO-002 | {{AUDIO_002_NAME}} | SFX | {{TRIGGER}} | No | P0 | TODO |
| {{AUDIO_ID}} | {{NAME}} | {{TYPE}} | {{TRIGGER}} | {{LOOP}} | {{PRIORITY}} | {{STATUS}} |

---

## §5 Texture / Sprite / UI Atlas 資源清單（VDD）

### §5.1 視覺資源規格

| 規格項目 | 要求 |
|---------|------|
| 最大 Texture 解析度 | {{MAX_TEXTURE_RES}}（如 2048×2048 / 4096×4096）|
| 壓縮格式（行動端）| {{MOBILE_COMPRESS}}（如 ETC2 / ASTC 6×6）|
| 壓縮格式（桌機 / Web）| {{DESKTOP_COMPRESS}}（如 BC7 / WebP）|
| Atlas 最大尺寸 | {{ATLAS_SIZE}}（如 2048×2048）|
| 命名規則 | `{{TEXTURE_NAMING}}`（如 `ui_btn_primary.png`）|
| 顏色空間 | {{COLOR_SPACE}}（如 sRGB / Linear）|

### §5.2 UI 資源清單

| 資源 ID | 名稱 / 路徑 | 尺寸（px）| 格式 | Atlas 歸屬 | 優先級 | 狀態 |
|---------|------------|---------|------|-----------|-------|------|
| TEX-001 | {{TEX_001_NAME}} | {{WxH}} | PNG | {{ATLAS}} | P0 | TODO |
| TEX-002 | {{TEX_002_NAME}} | {{WxH}} | PNG | {{ATLAS}} | P0 | TODO |
| {{TEX_ID}} | {{NAME}} | {{SIZE}} | {{FORMAT}} | {{ATLAS}} | {{PRIORITY}} | {{STATUS}} |

### §5.3 角色 / 場景 Sprite 清單（若適用）

| 資源 ID | 名稱 / 路徑 | 解析度（px）| LOD 層數 | 優先級 | 狀態 |
|---------|------------|----------|---------|-------|------|
| SPRITE-001 | {{SPRITE_001_NAME}} | {{RES}} | {{LOD}} | P0 | TODO |

---

## §6 Font 字型資源清單

| 字型 ID | 字型名稱 | 格式 | 授權 | 使用場景 | 子集化（Subsetting）| 狀態 |
|---------|---------|------|------|---------|-------------------|------|
| FONT-001 | {{FONT_001_NAME}} | {{FORMAT}}（TTF / OTF / WOFF2）| {{LICENSE}} | {{USE_CASE}} | {{SUBSET}} | TODO |
| FONT-002 | {{FONT_002_NAME}} | {{FORMAT}} | {{LICENSE}} | {{USE_CASE}} | {{SUBSET}} | TODO |

> **授權注意**：所有商用字型必須確認授權範圍（OFL / 商業授權 / 嵌入允許）；禁止使用未授權字型。

---

## §7 3D 模型資源清單（若適用）

<!-- 若無 3D 模型需求，填入「本專案無 3D 模型資源需求」並略過本節 -->

### §7.1 3D 資源規格

| 規格項目 | 要求 |
|---------|------|
| 匯入格式 | {{MESH_FORMAT}}（如 `.fbx` / `.gltf` / `.obj`）|
| 最大面數（Polygon Count）| {{MAX_POLY}}（如 ≤ 50,000 tri / model for 行動端）|
| UV 展開 | {{UV_SPEC}}（如 UV1 for Albedo，UV2 for Lightmap）|
| Skeleton / Rig 格式 | {{RIG_FORMAT}} |
| 命名規則 | `{{MESH_NAMING}}`（如 `char_hero.fbx`）|

### §7.2 3D 模型清單

| 資源 ID | 名稱 | 面數（tri）| LOD 層數 | 動畫 Rig | 優先級 | 狀態 |
|---------|------|-----------|---------|---------|-------|------|
| MESH-001 | {{MESH_001_NAME}} | {{POLY}} | {{LOD}} | {{RIG}} | P0 | TODO |

---

## §8 Video 影片資源清單（若適用）

<!-- 若無影片需求，填入「本專案無影片資源需求」並略過本節 -->

| 資源 ID | 名稱 | 解析度 | 格式 | 時長 | 觸發場景 | 壓縮方式 | 優先級 | 狀態 |
|---------|------|-------|------|------|---------|---------|-------|------|
| VIDEO-001 | {{VIDEO_001_NAME}} | {{RES}} | MP4（H.264）| {{DURATION}} | {{TRIGGER}} | {{COMPRESS}} | P1 | TODO |

---

## §9 本地化資源（i18n String Table，若適用）

<!-- 若無多語言需求，填入「本專案僅支援單語言，略過本節」 -->

### §9.1 本地化規格

| 項目 | 規格 |
|------|------|
| 支援語系 | {{LOCALES}}（如 zh-TW / en-US / ja-JP）|
| 字串格式 | {{I18N_FORMAT}}（如 JSON / CSV / XLIFF / PO）|
| 字型替換策略 | {{FONT_SWAP}}（不同語系使用不同字型）|
| 複數規則 | {{PLURAL_RULE}}（ICU MessageFormat 或各語言語法）|

### §9.2 字串清單（部分示例）

| 字串 ID | 中文（zh-TW）| 英文（en-US）| 備注 |
|---------|-------------|-------------|------|
| STR-001 | {{ZH_TW_TEXT}} | {{EN_US_TEXT}} | {{NOTE}} |
| {{STR_ID}} | {{TEXT}} | {{TEXT}} | {{NOTE}} |

---

## §10 效能預算（Performance Budget）

| 資源類型 | 記憶體上限 | 包體大小上限 | 載入時間上限（首次）|
|---------|-----------|------------|------------------|
| Texture / Atlas | {{TEX_MEMORY_LIMIT}} | {{TEX_PACKAGE_LIMIT}} | {{TEX_LOAD_TIME}} |
| Audio（BGM）| {{BGM_MEMORY_LIMIT}} | {{BGM_PACKAGE_LIMIT}} | {{BGM_LOAD_TIME}} |
| Audio（SFX 合計）| {{SFX_MEMORY_LIMIT}} | {{SFX_PACKAGE_LIMIT}} | — |
| Animation | {{ANIM_MEMORY_LIMIT}} | {{ANIM_PACKAGE_LIMIT}} | {{ANIM_LOAD_TIME}} |
| 3D Mesh（若適用）| {{MESH_MEMORY_LIMIT}} | {{MESH_PACKAGE_LIMIT}} | {{MESH_LOAD_TIME}} |
| **總包體（初始下載）**| — | **≤ {{INITIAL_DOWNLOAD_LIMIT}}**（如 100MB）| ≤ {{INITIAL_LOAD_TIME}} |

---

## §11 資源命名規則總覽

| 前綴 | 資源類型 | 命名範例 |
|------|---------|---------|
| `anim_` | 動畫 | `anim_char_hero_idle.skel` |
| `bgm_` | 背景音樂 | `bgm_main_theme.ogg` |
| `sfx_` | 音效 | `sfx_btn_click.wav` |
| `tex_` | 貼圖 | `tex_ui_bg_lobby.png` |
| `sprite_` | 角色/場景精靈 | `sprite_char_hero_001.png` |
| `font_` | 字型 | `font_noto_sans_tc.otf` |
| `mesh_` | 3D 模型 | `mesh_char_hero.fbx` |
| `video_` | 影片 | `video_intro_cutscene.mp4` |
| `i18n_` | 本地化字串 | `i18n_zh_tw.json` |

---

## §12 Review Checklist

- [ ] 所有資源 ID 唯一，命名符合 §11 規則
- [ ] 每個資源均有明確的優先級（P0 / P1 / P2 / P3）和狀態（TODO / In Progress / Done）
- [ ] §10 效能預算：所有資源類型均有記憶體和包體限制
- [ ] §2 引擎選型與 `docs/FRONTEND.md` 中的 `client_engine` 一致
- [ ] §6 字型授權欄位均已填寫（非空白）
- [ ] §3 動畫 / §4 音效 / §5 視覺資源：若無需求，已明確標注「本專案無 XXX 資源需求」
- [ ] §7 3D 模型 / §8 影片 / §9 本地化：若無需求，已明確標注跳過
- [ ] 資源總包體（§10）不超過平台 / 市場限制（iOS App Store ≤ 200MB OTA，Google Play ≤ 150MB 免 expansion）
