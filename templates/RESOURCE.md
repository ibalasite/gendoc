---
doc-type: RESOURCE
output-path: docs/RESOURCE.md
upstream-docs:
  - docs/VDD.md    # 視覺設計：角色、UI 色彩系統、圖示風格
  - docs/ANIM.md   # 動畫設計：骨骼動畫清單、粒子特效清單（若存在）
  - docs/AUDIO.md  # 音效設計：BGM/SFX/VO 清單（若存在）
version: "{{RESOURCE_DOC_VERSION}}"
last-updated: "{{LAST_UPDATED_DATE}}"
---

# {{PROJECT_NAME}} — AI 資產生產訂單（RESOURCE）

> **用途**：本文件為結構化 AI 資產生產清單，列出所有需要透過 AI 工具（Midjourney、DALL-E、Suno、Udio、ElevenLabs 等）或委外製作的視覺、動態、音效資產。  
> 每一行代表一個獨立的生產任務，包含生成提示詞（Prompt）、效能預算（file_size_budget）與交付路徑。  
> 設計師確認 prompt 後即可直接送入 AI 生成工具。
>
> **上游來源**：本文件由 `docs/VDD.md`、`docs/ANIM.md`、`docs/AUDIO.md` 推導生成。修改設計規格請先更新對應設計文件，再重新生成本文件。

---

## Change Log

| 版本 | 日期 | 作者 | 修改說明 |
|------|------|------|---------|
| {{VERSION}} | {{DATE}} | {{AUTHOR}} | {{CHANGE}} |

---

## 欄位說明

| 欄位 | 說明 |
|------|------|
| `ID` | 資產唯一識別碼（RES-IMG-001、RES-ANIM-001、RES-SFX-001） |
| `檔名` | 最終交付檔案名稱（含副檔名，如 `hero_idle.png`） |
| `type` | `image` / `animation` / `particle` / `shader` / `bgm` / `sfx` / `vo` / `video` / `font` |
| `source_tool` | 生成工具（Midjourney v6 / DALL-E 3 / Stable Diffusion XL / Suno v3 / Udio / ElevenLabs / 手繪委外 / 購買授權）|
| `prompt` | 直接可用的生成提示詞（語言依 source_tool 決定，英文為主）。**type=shader 的 prompt 描述視覺效果（非圖像生成 prompt），可參考 ShaderGraph 效果名稱**。|
| `dimensions` | 圖片用 WxH px；音效用秒數；動畫用「幀數×fps」|
| `file_size_budget` | 效能預算上限（如 ≤ 200 KB、≤ 2 MB）|
| `status` | `needed` / `prompt_ready` / `generating` / `generated` / `approved` / `rejected` |
| `output_path` | 資產在 repo 中的最終交付路徑（如 `assets/images/hero/hero_idle.png`）|
| `description` | 用途說明與設計注意事項 |

---

## §1 VDD 視覺資產清單（圖片 / 圖示 / 插畫）

> **上游**：`docs/VDD.md §4 角色設計` + `docs/VDD.md §5 UI 視覺系統` + `docs/VDD.md §6 場景/背景設計`（若存在）  
> 每個 VDD 角色、UI 元件、場景背景均應有對應的 RES-IMG 行（§6 若有場景定義則一同納入）。

| ID | 檔名 | type | source_tool | prompt | dimensions | file_size_budget | status | output_path | description |
|----|------|------|------------|--------|-----------|-----------------|--------|-------------|-------------|
| RES-IMG-001 | {{IMG_001_FILENAME}} | image | {{IMG_001_TOOL}} | {{IMG_001_PROMPT}} | {{IMG_001_DIMENSIONS}} | {{IMG_001_BUDGET}} | needed | {{IMG_001_PATH}} | {{IMG_001_DESC}} |
| RES-IMG-002 | {{IMG_002_FILENAME}} | image | {{IMG_002_TOOL}} | {{IMG_002_PROMPT}} | {{IMG_002_DIMENSIONS}} | {{IMG_002_BUDGET}} | needed | {{IMG_002_PATH}} | {{IMG_002_DESC}} |
| {{RES_IMG_ID}} | {{FILENAME}} | image | {{TOOL}} | {{PROMPT}} | {{DIMENSIONS}} | {{BUDGET}} | needed | {{PATH}} | {{DESC}} |

<!-- 生成規則：從 VDD §4 提取每個角色（hero、NPC、monster 等）各生成至少 1 行；從 VDD §5 提取每個主要 UI 場景（主頁、戰鬥、商城等）各生成 1 行背景圖；UI 圖示集視為 1 組，生成 1 行；若 VDD §6 存在，每個場景背景各生成 1 行。 -->

---

## §2 ANIM 動態資產清單（動畫 / 粒子 / Shader）

> **上游**：`docs/ANIM.md §2 骨骼動畫清單` + `docs/ANIM.md §5 粒子特效清單`（若存在）  
> 每個 ANIM.md SKEL-xxx 骨骼動畫和 VFX-xxx 粒子特效均應有對應的 RES-ANIM 行。

| ID | 檔名 | type | source_tool | prompt | dimensions | file_size_budget | status | output_path | description |
|----|------|------|------------|--------|-----------|-----------------|--------|-------------|-------------|
| RES-ANIM-001 | {{ANIM_001_FILENAME}} | animation | {{ANIM_001_TOOL}} | {{ANIM_001_PROMPT}} | {{ANIM_001_DIMENSIONS}} | {{ANIM_001_BUDGET}} | needed | {{ANIM_001_PATH}} | {{ANIM_001_DESC}} |
| RES-ANIM-002 | {{ANIM_002_FILENAME}} | particle | {{ANIM_002_TOOL}} | {{ANIM_002_PROMPT}} | {{ANIM_002_DIMENSIONS}} | {{ANIM_002_BUDGET}} | needed | {{ANIM_002_PATH}} | {{ANIM_002_DESC}} |
| RES-SHADER-001 | {{SHADER_001_FILENAME}} | shader | Unity ShaderGraph / Shadertoy | dissolve transition shader, edge glow with noise UV distortion, expose alpha mask parameter | N/A | {{SHADER_001_BUDGET}} | needed | {{SHADER_001_PATH}} | {{SHADER_001_DESC}} |
| {{RES_ANIM_ID}} | {{FILENAME}} | {{ANIM_TYPE}} | {{TOOL}} | {{PROMPT}} | {{DIMENSIONS}} | {{BUDGET}} | needed | {{PATH}} | {{DESC}} |

<!-- 生成規則：ANIM.md 的每個 SKEL-xxx → 對應一個 animation 資產行；每個 VFX-xxx → 對應一個 particle 資產行；若無 ANIM.md，填入「本專案無動態資產需求，略過本節」。 -->

---

## §3 AUDIO 音效資產清單（BGM / SFX / VO）

> **上游**：`docs/AUDIO.md §2 BGM 清單` + `docs/AUDIO.md §3 SFX 清單` + `docs/AUDIO.md VO 清單`（若存在）  
> 每個 AUDIO.md BGM-xxx 均應有對應的 RES-BGM 行；每個 SFX-xxx 均應有對應的 RES-SFX 行；若有 VO → 每個 VO 項目均應有對應的 RES-VO 行。

| ID | 檔名 | type | source_tool | prompt | dimensions | file_size_budget | status | output_path | description |
|----|------|------|------------|--------|-----------|-----------------|--------|-------------|-------------|
| RES-BGM-001 | {{BGM_001_FILENAME}} | bgm | {{BGM_001_TOOL}} | {{BGM_001_PROMPT}} | {{BGM_001_DURATION}}s | {{BGM_001_BUDGET}} | needed | {{BGM_001_PATH}} | {{BGM_001_DESC}} |
| RES-SFX-001 | {{SFX_001_FILENAME}} | sfx | {{SFX_001_TOOL}} | {{SFX_001_PROMPT}} | {{SFX_001_DURATION}}s | {{SFX_001_BUDGET}} | needed | {{SFX_001_PATH}} | {{SFX_001_DESC}} |
| RES-VO-001 | {{VO_001_FILENAME}} | vo | {{VO_001_TOOL}} | {{VO_001_PROMPT}} | {{VO_001_DURATION}}s | {{VO_001_BUDGET}} | needed | {{VO_001_PATH}} | {{VO_001_DESC}} |
| {{RES_AUDIO_ID}} | {{FILENAME}} | {{AUDIO_TYPE}} | {{TOOL}} | {{PROMPT}} | {{DURATION}}s | {{BUDGET}} | needed | {{PATH}} | {{DESC}} |

<!-- 生成規則：AUDIO.md 的每個 BGM-xxx → RES-BGM 行；每個 SFX-xxx → RES-SFX 行；若有 VO → RES-VO 行；若無 AUDIO.md，填入「本專案無音效資產需求，略過本節」。 -->

---

## §4 Review Checklist

- [ ] §1 VDD 視覺資產：VDD.md §4 所有角色均有對應 RES-IMG 行
- [ ] §1 VDD 視覺資產：VDD.md §5 所有主要 UI 場景背景圖及 UI 圖示集均有對應 RES-IMG 行（圖示集含圖示數量與單個尺寸說明）
- [ ] §1 VDD 視覺資產：VDD.md §6 所有場景均有對應 RES-IMG 行（若 VDD.md §6 存在）
- [ ] §2 ANIM 動態資產：ANIM.md 所有 SKEL-xxx 均有對應 RES-ANIM 行（若 ANIM.md 存在）
- [ ] §2 ANIM 動態資產：ANIM.md 所有 VFX-xxx 均有對應 RES-ANIM 行（若 ANIM.md 存在）
- [ ] §3 AUDIO 音效資產：AUDIO.md 所有 BGM-xxx 均有對應 RES-BGM 行（若 AUDIO.md 存在）
- [ ] §3 AUDIO 音效資產：AUDIO.md 所有 SFX-xxx 均有對應 RES-SFX 行（若 AUDIO.md 存在）
- [ ] §3 AUDIO 語音資產：AUDIO.md 所有 VO 項目均有對應 RES-VO 行（若 AUDIO.md 含 VO 清單）
- [ ] 所有 `file_size_budget` 欄位有具體數值（非空白），符合平台限制（手遊圖片 ≤ 2 MB；Web 圖片 ≤ 200 KB（關鍵路徑）/ ≤ 1 MB（懶加載）；BGM ≤ 5 MB；SFX ≤ 500 KB；VO ≤ 1 MB；骨骼動畫 ≤ 2 MB；粒子貼圖 ≤ 512 KB）
- [ ] 所有 `prompt` 欄位：`prompt_ready` / `generating` / `generated` / `approved` 狀態的資產 prompt 非空白
- [ ] 所有 `output_path` 與實際 repo 目錄結構一致
- [ ] 無裸 placeholder（`{{...}}`）殘留（除本 template 範例行外）
- [ ] 同前綴 ID 無重複（RES-IMG-001 不重複出現，RES-ANIM/RES-BGM/RES-SFX/RES-VO 同理）
- [ ] §5 授權管理：所有 §1/§2/§3 資產 ID 均在 §5 有對應授權記錄
- [ ] §5 授權管理：purchased / commissioned / CC-BY / CC-BY-SA 資產已填入 license_ref（授權證明、合約編號或姓名標示來源連結）
- [ ] 所有資產 source_tool 與目標引擎/平台一致（參照 RESOURCE.gen.md 引擎/平台偵測規則表，如 Unity → Spine/.skel；Web → Lottie/CSS Animation；Cocos Creator → DragonBones/.json；Unreal → Unreal Motion Capture；Godot → Godot AnimationPlayer）

---

## §5 授權與來源管理（License & Source Tracking）

> **用途**：記錄每個資產的授權類型與來源參考，供法務審查與合規使用。  
> 適用於 §1 VDD 視覺資產、§2 ANIM 動態資產、§3 AUDIO 音效資產所有類型。

| ID | 檔名 | license_type | license_ref | 備註 |
|----|------|-------------|------------|------|
| RES-IMG-001 | hero_idle.png | AI-generated | https://docs.midjourney.com/docs/terms-of-service | §1 主角立繪，Midjourney v6 生成 |
| RES-ANIM-001 | hero_idle.skel | commissioned | CONTRACT-001 | §2 骨骼動畫委外製作，合約編號 CONTRACT-001 |
| RES-BGM-001 | bgm_main_theme.ogg | purchased | PO-2024-001 | §3 主題曲購買授權，採購單號 PO-2024-001 |
| {{RES_ID}} | {{FILENAME}} | {{LICENSE_TYPE}} | {{LICENSE_REF}} | {{NOTES}} |

**license_type 常用值**：
- `AI-generated` — AI 工具生成，版權歸屬依各工具授權條款
- `CC0` — 公有領域，無限制使用
- `CC-BY` — 創用 CC 姓名標示
- `CC-BY-SA` — 創用 CC 姓名標示-相同方式分享
- `purchased` — 購買授權（需附授權證明）
- `commissioned` — 委外製作（需附委外合約）
- `internal` — 自製原創，版權歸屬公司

<!-- 生成規則：從 §1/§2/§3 的每個資產行擷取 ID 和檔名，依 source_tool 推導 license_type（AI 工具生成 → AI-generated；Freesound CC0 → CC0；購買 → purchased；委外 → commissioned；ElevenLabs SFX / TTS 生成 → AI-generated；人聲錄音委外 → commissioned；Azure TTS → AI-generated；自製 / 公司自有 / Spine 自製 / DragonBones 自製 → internal）。 -->
