---
doc-type: RESOURCE
output-path: docs/RESOURCE.md
upstream-docs:
  required:
    - docs/VDD.md
  recommended:
    - docs/ANIM.md
    - docs/AUDIO.md
expert-roles:
  gen:
    - "Asset Production Planner / 資產生產規劃師：負責從 VDD.md 推導視覺資產清單（§1），確認每個角色設計、UI 場景、圖示集均有對應的 RES-IMG 行，並依 VDD 風格描述產出初版 prompt"
    - "Animation Asset Coordinator / 動畫資產協調師：負責從 ANIM.md 推導動態資產清單（§2），確認每個 SKEL-xxx 骨骼動畫和 VFX-xxx 粒子特效均有對應的 RES-ANIM 行"
    - "Audio Asset Coordinator / 音效資產協調師：負責從 AUDIO.md 推導音效資產清單（§3），確認每個 BGM-xxx 和 SFX-xxx 均有對應的 RES-BGM / RES-SFX 行"
quality-bar: "VDD §4 所有角色均有 RES-IMG 行；ANIM.md 所有 SKEL/VFX 均有 RES-ANIM 行（若存在）；AUDIO.md 所有 BGM/SFX 均有 RES-BGM/RES-SFX 行（若存在）；所有 file_size_budget 非空白且符合平台預算；status=needed 以外的資產 prompt 非空白；無裸 placeholder；§5 授權章節涵蓋所有資產 ID，license_type 非空白"
---

# RESOURCE.gen.md — AI 資產生產訂單生成規則

依 VDD.md、ANIM.md、AUDIO.md 的設計規格，推導並生成結構化 AI 資產生產訂單。

---

## Iron Rule

**Iron Law**：生成任何 RESOURCE.md 之前，必須先讀取 `RESOURCE.md`（骨架結構）和 `RESOURCE.gen.md`（本規則）。

生成時**依序執行**每個 Step，不得跳過或合並執行。每個 Step 完成後再進行下一個。

---

## 上游文件讀取規則

### 必讀上游鏈

| 文件 | 必讀章節 | 用途 |
|------|---------|------|
| `VDD.md` | §4 角色設計、§5 UI 視覺系統、§6 場景/背景（若有）| **主要輸入**：推導需要哪些視覺資產（角色立繪、UI 背景、圖示），並提取風格描述作為 prompt 的基底 |
| `ANIM.md`（若存在）| §2 骨骼動畫清單（SKEL-xxx）、§5 粒子特效清單（VFX-xxx）| 動態資產清單的來源；每個 SKEL/VFX 對應一個 RES-ANIM 行 |
| `AUDIO.md`（若存在）| §2 BGM 清單（BGM-xxx）、§3 SFX 清單（SFX-xxx）| 音效資產清單的來源；每個 BGM/SFX 對應一個 RES 行 |

### 文件存在性偵測

```bash
# 必讀文件
[ -f "docs/VDD.md" ] || echo "❌ docs/VDD.md 不存在，無法生成 §1"

# 選讀文件（不存在則跳過對應章節）
[ -f "docs/ANIM.md" ] && echo "✅ ANIM.md 存在，生成 §2" || echo "⚠️ ANIM.md 不存在，§2 填入略過說明"
[ -f "docs/AUDIO.md" ] && echo "✅ AUDIO.md 存在，生成 §3" || echo "⚠️ AUDIO.md 不存在，§3 填入略過說明"
```

---

## 上游衝突偵測規則

在讀取上游文件後、執行各 Step 生成內容之前，Gen Agent 必須套用以下規則處理衝突與增量更新。

### 名稱對齊規則

| 衝突情境 | 處理方式 |
|---------|---------|
| VDD 角色名與 ANIM 骨骼動畫名不一致（如 VDD 稱「hero」，ANIM 稱「warrior」）| 以 **VDD 角色名**為準作為 `檔名` 和 `output_path`；將 ANIM 的骨骼動畫名記入 `description`（格式：`ANIM SKEL 對應名稱：{ANIM 名稱}`）|
| AUDIO BGM/SFX 名稱與 RESOURCE.md 既有行不一致 | 以 **AUDIO.md 原始 ID**（BGM-xxx / SFX-xxx）為 description 補充說明，檔名依 AUDIO.md 規格 |

### 增量更新規則

當 **重新生成** RESOURCE.md（已有內容）時：

1. **已有 `approved` 或 `generated` 狀態的行**：只新增，不刪除、不覆蓋。若上游對應設計已移除，在 `description` 加上 `⚠️ 上游設計已移除，請確認是否廢棄`，status 保持不變。
2. **已有 `needed` 或 `prompt_ready` 狀態的行**：若上游設計規格有異動，可更新 `prompt`、`dimensions`、`file_size_budget` 欄位；`ID` 和 `output_path` 不變。
3. **新增的上游項目**：在對應章節末端追加新行，ID 延續既有最大流水號 +1。

### 設計遺漏提示規則

| 遺漏情境 | 處理方式 |
|---------|---------|
| VDD §4 有角色，但 ANIM.md 無對應骨骼動畫（角色在 ANIM.md 完全未出現）| 在 §2 對應 RES-ANIM 行的 `description` 中標注：`⚠️ VDD §4 定義此角色，但 ANIM.md 無對應骨骼動畫，請確認動畫規格是否已規劃` |
| VDD §4 有角色，ANIM.md 只有部分狀態（如缺少 dead 動畫）| 在 `description` 補充：`⚠️ ANIM.md 缺少 {狀態名稱} 動畫，請確認是否需要生成` |

---

## 引擎 / 平台偵測規則

在執行 Step 1-A 和 Step 2-A 前，先偵測目標引擎並對應推薦 source_tool，後續 Step 統一引用此表，不再重複偵測。

| 引擎 / 平台 | 偵測依據（EDD/ARCH 關鍵字） | 圖片推薦 source_tool | 動畫推薦 source_tool | 特效推薦 source_tool |
|------------|--------------------------|--------------------|--------------------|-------------------|
| **Unity** | `unity`、`Unity Engine`、`.unity` | Midjourney v6 / DALL-E 3 | Spine（`.skel`）/ Unity Animator | Unity ShaderGraph / Unity ParticleSystem |
| **Cocos Creator** | `cocos`、`CocosCreator`、`.fire` | Midjourney v6 / DALL-E 3 | DragonBones（`.json`）/ Spine | Cocos ParticleSystem / Shadertoy |
| **Web** | `web`、`browser`、`Phaser`、`PixiJS`、`Three.js` | Midjourney v6 / DALL-E 3 | Lottie / CSS Animation / GSAP | PixiJS Particles / Shadertoy |
| **Unreal Engine** | `unreal`、`Unreal Engine`、`.uproject` | Midjourney v6 | Unreal Motion Capture / Sequencer | Niagara ParticleSystem |
| **Godot** | `godot`、`.tscn`、`.gd` | Midjourney v6 / DALL-E 3 | Godot AnimationPlayer / Spine | Godot ParticleSystem2D |
| **未偵測到** | — | 留空，由人工確認 | 留空，由人工確認 | 留空，由人工確認 |

> **引用方式**：Step 1-A `source_tool` 欄位 → 查此表的「圖片推薦」；Step 2-A `source_tool` → 查「動畫推薦」；Step 2-B `source_tool` → 查「特效推薦」。

---

## Step 1：讀取 VDD.md，建立視覺資產清單（§1）

### 1-A：提取角色設計（VDD §4）

1. 讀取 `VDD.md §4 角色設計`，列出所有角色（hero、NPC、monster、boss 等）。
2. 對每個角色生成至少一個 RES-IMG 行：
   - `ID`：`RES-IMG-{NNN}`（三位流水號）
   - `檔名`：`{角色英文名}_{狀態}.png`（如 `hero_idle.png`）
   - `type`：`image`
   - `source_tool`：依引擎偵測規則表的「圖片推薦 source_tool」欄填入（詳見本文件引擎/平台偵測規則表）；若引擎未偵測到，則依 VDD 視覺風格補充：2D 卡通 → Midjourney v6；像素風 → Stable Diffusion；3D 寫實 → Midjourney v6 / DALL-E 3
   - `prompt`：依 VDD 風格描述生成第一版英文 prompt（格式：`{角色描述}, {風格}, {構圖}, {背景}, {質感}, {解析度}`）
   - `dimensions`：依 VDD §4 角色尺寸規格填入；若未定義預設 `512x512 px`
   - `file_size_budget`：手遊預設 ≤ 2 MB；Web 預設 ≤ 200 KB；依 EDD 平台調整
   - `status`：`needed`
   - `output_path`：`assets/images/{角色類別}/{檔名}`
   - `description`：角色用途說明 + 特殊注意事項（如需透明背景）

3. 若角色有多個狀態（idle、walk、attack、dead）→ 各生成一行。
4. 若角色是 Spine/DragonBones 骨骼動畫，image 資源為 spritesheet → `type` 改為 `image`，`dimensions` 填入 atlas 尺寸。

### 1-B：提取 UI 視覺系統（VDD §5）

1. 讀取 `VDD.md §5 UI 視覺系統`，列出主要 UI 場景或 UI 套件。
2. 對每個主要 UI 場景背景生成 1 行：
   - `ID`：延續 §4 的流水號（如 §4 用到 RES-IMG-012，§5 從 RES-IMG-013 開始）
   - `type`：`image`
   - `description`：`{場景名稱} UI 背景圖`
3. UI 圖示集（icon set）視為 1 組 → 生成 1 行（dimensions 填入單個圖示尺寸，description 說明共幾個圖示）。
4. 若有 splash screen / loading screen → 各生成 1 行。

### 1-C：提取場景/背景（VDD §6，若存在）

1. 讀取 `VDD.md §6 場景/背景設計`（若章節存在）。
2. 對每個場景背景生成 1 行：
   - `type`：`image`
   - `dimensions`：依設備解析度（手遊 1080×1920、橫屏 1920×1080；Web 依 breakpoint）

---

## Step 2：讀取 ANIM.md，建立動態資產清單（§2）

若 `docs/ANIM.md` **不存在**，在 §2 填入：
```
> 本專案無動態資產需求（docs/ANIM.md 不存在），略過本節。
```
然後跳到 Step 3。

若 `docs/ANIM.md` **存在**：

### 2-A：骨骼動畫資產（ANIM §2 SKEL-xxx）

1. 讀取 `ANIM.md §2 骨骼動畫清單`，列出所有 `SKEL-xxx` 項目。
2. 對每個 SKEL-xxx 生成一個 RES-ANIM 行：
   - `ID`：`RES-ANIM-{NNN}`
   - `檔名`：`{anim名稱}.{格式}`（如 `hero_idle.skel` 或 `hero_idle.json`）
   - `type`：`animation`
   - `source_tool`：依引擎偵測規則表的「動畫推薦 source_tool」欄填入（詳見本文件引擎/平台偵測規則表）
   - `prompt`：骨骼動畫通常需要人工製作，填入 `N/A — 委外製作或使用動作擷取（Motion Capture）`；若可用 AI 工具（如 Cascadeur）則填入動作描述
   - `dimensions`：`{幀數}f × {fps}fps`（如 `24f × 30fps`）
   - `file_size_budget`：依 ANIM.md 規格（預設 ≤ 2 MB/動畫）

### 2-B：粒子特效資產（ANIM §5 VFX-xxx）

1. 讀取 `ANIM.md §5 粒子特效清單`（若章節存在），列出所有 `VFX-xxx` 項目。
2. 對每個 VFX-xxx 生成一個 RES-ANIM 行：
   - `type`：`particle`
   - `source_tool`：Unity ParticleSystem / Cocos ParticleSystem / PixiJS Particles / Shadertoy；或 AI 工具（如 Runway Gen-2 for VFX reference）
   - `prompt`：粒子特效的視覺描述（如 `golden sparkle explosion, 60fps, transparent background, game VFX style`）
   - `dimensions`：特效貼圖尺寸（如 `512x512 px spritesheet, 8x8 frames`）

---

## Step 3：讀取 AUDIO.md，建立音效資產清單（§3）

若 `docs/AUDIO.md` **不存在**，在 §3 填入：
```
> 本專案無音效資產需求（docs/AUDIO.md 不存在），略過本節。
```
然後跳到 Step 3.5。

若 `docs/AUDIO.md` **存在**：

### 3-A：BGM 資產（AUDIO §2 BGM-xxx）

1. 讀取 `AUDIO.md §2 BGM 清單`，列出所有 `BGM-xxx`。
2. 對每個 BGM-xxx 生成一個 RES-BGM 行：
   - `ID`：`RES-BGM-{NNN}`
   - `檔名`：`bgm_{名稱}.{格式}`（如 `bgm_main_theme.ogg`）
   - `type`：`bgm`
   - `source_tool`：Suno v3 / Udio / Mubert / 委外製作
   - `prompt`：音樂風格描述（如 `epic orchestral RPG main theme, 120bpm, loop-friendly, adventure and hope mood, 2 minutes`）
   - `dimensions`：音效秒數（如 `120s`）
   - `file_size_budget`：依 AUDIO.md 規格（預設 BGM ≤ 5 MB）

### 3-B：SFX 資產（AUDIO §3 SFX-xxx）

1. 讀取 `AUDIO.md §3 SFX 清單`（或對應章節），列出所有 `SFX-xxx`。
2. 對每個 SFX-xxx 生成一個 RES-SFX 行：
   - `ID`：`RES-SFX-{NNN}`
   - `type`：`sfx`
   - `source_tool`：ElevenLabs SFX / Freesound / Adobe Audition / 自製 / Foley
   - `prompt`：音效描述（如 `short sword slash whoosh, metallic, impact, game SFX, 0.5 seconds`）
   - `dimensions`：`{秒數}s`（如 `0.5s`）
   - `file_size_budget`：依 AUDIO.md 規格（預設 SFX ≤ 500 KB）

### 3-C：VO 語音資產（若有）

若 AUDIO.md 有 VO（Voice Over）清單：
- `type`：`vo`
- `source_tool`：ElevenLabs / Azure TTS / 人聲錄音委外
- `ID`：`RES-VO-{NNN}`

---

## Step 3.5：生成 §4 Review Checklist

依據上游文件存在性，動態調整 §4 Review Checklist 各項目：

1. **ANIM.md 相關項目**：
   - 若 `docs/ANIM.md` **不存在**，在以下兩項後面加上後綴 `（N/A — ANIM.md 不存在）`：
     - `§2 ANIM 動態資產：ANIM.md 所有 SKEL-xxx 均有對應 RES-ANIM 行（若 ANIM.md 存在）`
     - `§2 ANIM 動態資產：ANIM.md 所有 VFX-xxx 均有對應 RES-ANIM 行（若 ANIM.md 存在）`
   - 若 `docs/ANIM.md` **存在**，保留項目原文（不加後綴）。

2. **AUDIO.md 相關項目**：
   - 若 `docs/AUDIO.md` **不存在**，在以下兩項後面加上後綴 `（N/A — AUDIO.md 不存在）`：
     - `§3 AUDIO 音效資產：AUDIO.md 所有 BGM-xxx 均有對應 RES-BGM 行（若 AUDIO.md 存在）`
     - `§3 AUDIO 音效資產：AUDIO.md 所有 SFX-xxx 均有對應 RES-SFX 行（若 AUDIO.md 存在）`
   - 若 `docs/AUDIO.md` **存在**，保留項目原文（不加後綴）。

3. **其餘 Checklist 項目**：直接保留 template 原文，不作任何修改。

---

## Step 3.8：生成 §5 授權與來源管理

依據 §1/§2/§3 已生成的資產清單，為每個資產行建立對應的授權記錄：

1. **擷取所有資產 ID 和 source_tool**：掃描 §1、§2、§3 中所有已填入的資產行（排除 template 範例 placeholder 行），記錄 `ID`、`檔名`、`source_tool`。

2. **依 source_tool 推導 license_type**：

   | source_tool 關鍵字 | 推導 license_type |
   |-------------------|-----------------|
   | Midjourney / DALL-E / Stable Diffusion / Suno / Udio / ElevenLabs SFX / ElevenLabs（含 TTS/VO）/ Unity ShaderGraph / Azure TTS | `AI-generated` |
   | Freesound CC0 / CC0 授權來源 | `CC0` |
   | 購買授權 / purchased / 授權圖庫 | `purchased` |
   | 委外製作 / commissioned / 手繪委外 / 人聲錄音委外 / Foley | `commissioned` |
   | Spine / Spine Animate / DragonBones（委外製作）| `commissioned` |
   | Spine / Spine Animate / DragonBones（自製）| `internal` |
   | 自製 / internal / 公司自有 | `internal` |
   | 未知或留空 | 留空，在備註欄標記 `⚠️ 需人工確認授權` |

3. **填寫 license_ref**：
   - `AI-generated` / `CC0`：填入 `N/A` 或工具官方授權條款 URL（如 `https://docs.midjourney.com/docs/terms-of-service`）
   - `purchased`：填入授權證明編號或採購單號（如 `PO-2024-001`）；若尚未取得，填入 `⚠️ 待補充授權證明`
   - `commissioned`：填入委外合約編號（如 `CONTRACT-2024-ART-001`）；若尚未簽約，填入 `⚠️ 待補充委外合約`
   - `internal`：填入 `N/A`

4. **整合進 §5 表格**：依 §1 → §2 → §3 的 ID 順序，逐行填入 §5 授權表格。確保 §1/§2/§3 每一個資產 ID 在 §5 都有對應行。

---

## Step 4：Quality Gate 自我檢核

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| VDD 角色覆蓋 | VDD §4 每個角色都有 ≥ 1 個 RES-IMG 行 | 補充缺失角色的 RES-IMG 行 |
| VDD UI 覆蓋 | VDD §5 每個主要 UI 場景都有 ≥ 1 個 RES-IMG 行 | 補充缺失場景的 RES-IMG 行 |
| ANIM 覆蓋 | 若 ANIM.md 存在，每個 SKEL-xxx 和 VFX-xxx 都有對應的 RES-ANIM 行 | 補充缺失的 RES-ANIM 行 |
| AUDIO 覆蓋 | 若 AUDIO.md 存在，每個 BGM-xxx 和 SFX-xxx 都有對應的 RES 行 | 補充缺失的 RES 行 |
| file_size_budget 完整 | 所有行的 file_size_budget 欄位均有具體數值（非空白、非 TBD）| 依平台標準填入預設值 |
| prompt 完整 | 所有非 `needed` 狀態的行，prompt 欄位非空白 | 補充 prompt 描述 |
| output_path 合理 | 所有 output_path 與 repo 實際目錄結構一致 | 確認 repo 目錄結構後修正 |
| 無裸 placeholder | 所有 `{{...}}` 欄位已替換（除 template 範例行）| 逐行補全 |
| ID 唯一 | 同前綴 ID 無重複（RES-IMG-001 不重複出現）| 重新編號衝突 ID |
| §5 授權覆蓋 | §1/§2/§3 所有資產 ID 均在 §5 有對應行，license_type 非空白 | 補充缺失的 §5 授權行 |

---

## 常用 AI 工具與 Prompt 格式速查

| 工具 | 適用資產 | Prompt 格式 |
|------|---------|------------|
| Midjourney v6 | 角色立繪、背景、UI 概念 | `{主體}, {風格關鍵字}, {光線}, {構圖}, {解析度} --ar {比例} --v 6` |
| DALL-E 3 | 圖示、UI 元素、卡通風格 | 自然語言描述，明確說明「白色/透明背景」、「flat icon style」等 |
| Stable Diffusion XL | 像素風、特定風格高度客製化 | `{主體}, {LoRA model}, {negative prompt}, {steps}` |
| Suno v3 | BGM、音樂 | `{風格}, {bpm}, {情境}, {時長}, {是否循環}` |
| Udio | BGM、音樂 | `{樂器}, {情境}, {情緒}, {時長}` |
| ElevenLabs SFX | 音效（sfx）| `{動作描述}, {環境}, {時長}, {強度}` |
| Freesound (CC0) | 環境音、一般 SFX | 搜尋關鍵字 + 確認 CC0 授權 |
| Spine Animate | 骨骼動畫 | N/A（動畫師直接製作或委外）|
| DragonBones | 骨骼動畫（Cocos）| N/A（同 Spine，工具直接製作）|
