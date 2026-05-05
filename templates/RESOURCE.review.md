---
reviewer-roles:
  - "Asset Production Planner / 資產生產規劃師：主審 §1 VDD 視覺資產覆蓋完整性、§2 ANIM 動態資產覆蓋完整性、§3 AUDIO 音效資產覆蓋完整性"
  - "Performance Budget Auditor / 效能預算審查員：主審所有 file_size_budget 欄位，確認數值符合平台限制（手遊 ≤ 2MB/texture、Web ≤ 200KB/image、BGM ≤ 5MB、SFX ≤ 500KB、VO ≤ 1MB、骨骼動畫 ≤ 2MB、粒子貼圖 ≤ 512KB）"
  - "AI Prompt Quality Reviewer / AI Prompt 品質審查員：主審 prompt 欄位是否有具體且可用的生成提示詞，確認非 needed 狀態的資產均有 prompt"
quality-bar: "VDD §4 所有角色均有 RES-IMG 行；VDD §5 所有主要 UI 場景均有 RES-IMG 行；VDD §6 場景/背景資產若 §6 存在，每個場景均有 RES-IMG 行；ANIM.md 所有 SKEL/VFX 均有 RES-ANIM 行（若存在）；AUDIO.md 所有 BGM/SFX/VO 均有 RES-BGM/RES-SFX/RES-VO 行（若存在）；所有 file_size_budget 非空白且符合平台預算；status=needed 以外的資產 prompt 非空白；output_path 與 repo 實際目錄結構一致；無裸 placeholder；同前綴 ID 無重複（RES-IMG-001 不重複出現）；§5 授權章節涵蓋所有資產 ID，license_type 非空白"
pass-conditions:
  - "CRITICAL 數量 = 0"
  - "Self-Check：template 所有 ## 章節（≥7 個）均存在且有實質內容"
  - "所有資源清單有具體規格（無 N/A 錯誤標記）"
upstream-alignment:
  - "VDD.md §4 角色清單 → RESOURCE.md §1 RES-IMG 行（一對一對應）"
  - "VDD.md §5 UI 視覺系統 → RESOURCE.md §1 UI 場景 RES-IMG 行（UI 背景圖一對一對應；圖示集 1 組對 1 行，description 須含圖示數量與單個尺寸）"
  - "VDD.md §6 場景/背景設計 → RESOURCE.md §1 RES-IMG 行（每個場景一對一對應，若 §6 存在）"
  - "ANIM.md §2 SKEL-xxx 清單 → RESOURCE.md §2 RES-ANIM 行（一對一對應，若 ANIM.md 存在）"
  - "ANIM.md §5 VFX-xxx 清單 → RESOURCE.md §2 RES-ANIM 行（一對一對應，type=particle，若存在）"
  - "AUDIO.md §2 BGM-xxx 清單 → RESOURCE.md §3 RES-BGM 行（一對一對應，若 AUDIO.md 存在）"
  - "AUDIO.md §3 SFX-xxx 清單 → RESOURCE.md §3 RES-SFX 行（一對一對應，若 AUDIO.md 存在）"
  - "AUDIO.md VO 清單 → RESOURCE.md §3 RES-VO 行（一對一對應，若有 VO）"
  - "RESOURCE.md §1/§2/§3 所有資產行 → RESOURCE.md §5 授權與來源管理（每個資產 ID 均有對應授權記錄）"
---

# RESOURCE.review.md — AI 資產生產訂單審查標準

---

## 審查角色分工

| 角色 | 審查重點 |
|------|---------|
| Asset Production Planner | §1（VDD 角色 + UI 覆蓋）、§2（ANIM SKEL/VFX 覆蓋）、§3（AUDIO BGM/SFX/VO 覆蓋）|
| Performance Budget Auditor | 所有行的 file_size_budget 欄位（§1/§2/§3）|
| AI Prompt Quality Reviewer | 所有行的 prompt 欄位（§1/§2/§3）|

---

## 審查項目總覽

| # | 嚴重度 | 審查點 | 涉及章節 |
|---|--------|--------|---------|
| 01 | CRITICAL | VDD §4 角色缺少 RES-IMG 行 | §1 |
| 01-B | HIGH | VDD §5 UI 視覺系統缺少 RES-IMG 行 | §1 |
| 01-C | MEDIUM | VDD §6 場景/背景設計缺少 RES-IMG 行（若 §6 存在）| §1 |
| 02 | CRITICAL | ANIM SKEL/VFX 項目缺少 RES-ANIM 行 | §2 |
| 03 | CRITICAL | AUDIO BGM/SFX/VO 缺少對應 RES 行 | §3 |
| 04 | CRITICAL | file_size_budget 空白或超過平台限制 | §1/§2/§3 |
| 05 | HIGH | prompt 欄位空白（非 needed 狀態） | §1/§2/§3 |
| 06 | HIGH | output_path 與 repo 目錄結構不一致 | §1/§2/§3 |
| 07 | MEDIUM | ID 有重複（同前綴 ID 出現兩次） | 全文 |
| 08 | HIGH | 有裸 placeholder（`{{...}}`）未替換（file_size_budget 除外） | 全文 |
| 09 | LOW | source_tool 欄位空白（status=needed 除外） | §1/§2/§3 |
| 09-B | MEDIUM | source_tool 與偵測到的引擎/平台不符 | §1/§2/§3 |
| 10 | MEDIUM | §5 授權章節不完整（資產 ID 缺少授權記錄或 license_type 空白）| §5 |
| 11 | LOW | §4 Checklist 中 N/A 後綴套用是否正確（ANIM.md / AUDIO.md / VDD §6 不存在時）| §4 |

---

### Layer 1: VDD 視覺資產覆蓋完整性（CRITICAL）

#### [CRITICAL] 01 — VDD §4 角色設計缺少 RES-IMG 行

**Check**：讀取 `docs/VDD.md §4 角色設計`，列出所有角色（hero、NPC、monster 等）。逐一確認 RESOURCE.md §1 是否有對應的 `RES-IMG-xxx` 行。任何 VDD §4 角色沒有對應 RES-IMG 行視為 CRITICAL。

**Risk**：缺少資產清單的角色在開發後期才被發現遺漏，設計師需要臨時插單生成，影響 milestone 交付；且 prompt 無版本控制，後期補做的資產與已有資產風格不一致。

**Fix**：對照 VDD §4 角色清單，在 RESOURCE.md §1 補充缺失角色的 RES-IMG 行。每個角色至少有：idle 狀態立繪（若為 2D）或 T-Pose 渲染圖（若為 3D）。依 VDD 風格描述生成第一版 prompt。

---

#### [HIGH] 01-B — VDD §5 UI 視覺系統缺少 RES-IMG 行

**Check**：讀取 `docs/VDD.md §5 UI 視覺系統`，列出所有主要 UI 場景（主頁、戰鬥、商城、設定等）及 UI 圖示集。逐一確認 RESOURCE.md §1 是否有對應的 RES-IMG 行：
- 每個主要 UI 場景背景圖應有 1 行（type=image，description 含「UI 背景圖」字樣）
- UI 圖示集應有 1 行（type=image，description 說明圖示數量）
- 若有 splash screen / loading screen → 各應有 1 行

任何 VDD §5 列出的 UI 場景或圖示集沒有對應 RES-IMG 行視為 HIGH。

**Risk**：UI 資產遺漏規劃時，工程師整合階段才發現缺少背景圖或圖示，需臨時插入生成任務，且與主角色資產的 prompt 風格無法保持一致（因為規劃時缺少統一的 prompt 基底），導致 UI 視覺風格碎片化。

**Fix**：對照 VDD §5 場景列表，在 RESOURCE.md §1 補充缺失的 UI 背景 RES-IMG 行。UI 圖示集作為一個群組生成 1 行，description 中說明圖示總數（如「主選單圖示集，共 24 個，48×48 px 每個圖示」）。同時更新 §4 Review Checklist，確認此項目已記錄。

---

#### [MEDIUM] 01-C — VDD §6 場景/背景設計缺少 RES-IMG 行（若 §6 存在）

**Check**：若 `docs/VDD.md §6 場景/背景設計` 章節存在，讀取其場景清單（地圖背景、關卡場景、過場背景等）。逐一確認 RESOURCE.md §1 是否有對應的 `RES-IMG-xxx` 行（`type=image`，`dimensions` 依目標設備解析度）。若 VDD.md §6 不存在，本項目略過。

**Risk**：場景/背景資產遺漏規劃時，開發整合階段才發現背景圖缺少生產訂單，需要臨時補單，且 prompt 風格基底可能與角色資產不一致，導致整體視覺風格碎片化。

**Fix**：對照 VDD §6 場景清單，在 RESOURCE.md §1 末尾補充缺失場景的 RES-IMG 行。`dimensions` 依目標設備填入（手遊直版 1080×1920、橫版 1920×1080；Web 依 breakpoint 填入）。

---

### Layer 2: ANIM 動態資產覆蓋完整性（CRITICAL）

#### [CRITICAL] 02 — ANIM.md SKEL/VFX 項目缺少 RES-ANIM 行

**Check**：若 `docs/ANIM.md` 存在，讀取其 `§2 骨骼動畫清單`（SKEL-xxx）和 `§5 粒子特效清單`（VFX-xxx）。逐一確認 RESOURCE.md §2 是否有對應的 `RES-ANIM-xxx` 行。任何 SKEL-xxx 或 VFX-xxx 沒有對應 RES-ANIM 行視為 CRITICAL。

若 ANIM.md 不存在，確認 §2 有明確的「略過說明」→ 不視為 CRITICAL。

**Risk**：動畫資產（骨骼動畫源檔、粒子貼圖）是開發最長的資產，若規劃遺漏，在整合測試前才被發現，將造成 2-4 週的延誤。

**Fix**：對照 ANIM.md 的 SKEL-xxx / VFX-xxx 清單，在 RESOURCE.md §2 補充缺失的 RES-ANIM 行。骨骼動畫 `type=animation`，粒子特效 `type=particle`。

---

### Layer 3: AUDIO 音效資產覆蓋完整性（CRITICAL）

#### [CRITICAL] 03 — AUDIO BGM/SFX/VO 覆蓋驗證

**Check**：若 `docs/AUDIO.md` 存在，讀取其 BGM 清單（BGM-xxx）、SFX 清單（SFX-xxx）及 VO 清單（若有）。逐一確認 RESOURCE.md §3 是否有對應的 `RES-BGM-xxx`、`RES-SFX-xxx`、`RES-VO-xxx` 行。任何 BGM-xxx、SFX-xxx 或 VO 項目沒有對應 RES 行視為 CRITICAL。

若 AUDIO.md 不存在，確認 §3 有明確的「略過說明」→ 不視為 CRITICAL。

**Risk**：音效資產（BGM、SFX、VO）缺漏規劃時，開發後期才發現需要額外委外製作或 AI 生成，造成 1-3 週延誤；且後期補做的音效在品質和風格上難以與既有資產保持一致，影響玩家沉浸感。

**Fix**：對照 AUDIO.md 的 BGM-xxx / SFX-xxx / VO 清單，在 RESOURCE.md §3 補充缺失的 RES-BGM / RES-SFX / RES-VO 行。依 RESOURCE.gen.md Step 3 的欄位規則填入 source_tool、prompt、dimensions、file_size_budget。

---

### Layer 4: 效能預算（CRITICAL）

#### [CRITICAL] 04 — file_size_budget 空白或超過平台限制

**Check**：逐行掃描 §1/§2/§3 所有資產行的 `file_size_budget` 欄位。以下任一情況視為 CRITICAL：
- 欄位為空白、TBD、或 placeholder（`{{...}}`）
- 圖片資產（type=image）超過：手遊 > 2 MB / Web > 200 KB（關鍵路徑）或 > 1 MB（懶加載）
- 音樂資產（type=bgm）超過：> 5 MB
- 音效資產（type=sfx）超過：> 500 KB
- 動畫資產（type=animation）超過：> 2 MB per animation file
- 粒子資產（type=particle）超過：> 512 KB
- 語音資產（type=vo）超過：> 1 MB

**Risk**：無效能預算上限時，設計師生成高解析度資產（如 4K PNG × 50 張），最終打包後發現 App 超過平台大小限制（iOS OTA ≤ 200MB）或首屏載入超時（Web FCP > 3s），需全部重新生成並壓縮。

> **Note**: `file_size_budget` 超限直接影響平台上架資格和遊戲載入時間，屬業務關鍵問題，故列為 CRITICAL。

**Fix**：依目標平台填入具體數值：
- 手遊（iOS/Android）圖片：`≤ 2 MB`；UI 圖示：`≤ 200 KB`
- Web 圖片：`≤ 200 KB`（關鍵路徑）/ `≤ 1 MB`（懶加載）
- BGM：`≤ 5 MB`；SFX：`≤ 500 KB`；VO：`≤ 1 MB`
- 動畫 source（.skel/.json）：`≤ 2 MB`；粒子貼圖：`≤ 512 KB`

---

### Layer 5: Prompt 品質（HIGH）

#### [HIGH] 05 — prompt 欄位空白（非 needed 狀態）

**Check**：逐行掃描 §1/§2/§3 所有資產行。若 `status` 為 `prompt_ready`、`generating`、`generated`、`approved`，則 `prompt` 欄位必須非空白。若 `status=needed` 則允許 prompt 空白。任何非 needed 狀態的 prompt 空白視為 HIGH。

**Risk**：設計師拿到清單後，發現 prompt 是空的，需要自己撰寫提示詞，失去 AI 輔助規劃的效益；且不同設計師撰寫的 prompt 風格不一致，生成結果無法保持視覺連貫性。

**Fix**：依 VDD 的視覺風格描述，為每個非 needed 狀態的資產補充具體 prompt。英文為主（Midjourney/DALL-E/Suno 均優先支援英文）。格式參考 RESOURCE.gen.md 的「常用 AI 工具與 Prompt 格式速查」表。

---

### Layer 6: 交付路徑（HIGH）

#### [HIGH] 06 — output_path 與 repo 目錄結構不一致

**Check**：抽查 §1/§2/§3 中至少 20% 的 output_path，確認路徑格式是否與實際 repo 目錄結構一致。典型不一致案例：
- 使用 `src/assets/` 但 repo 實際根目錄為 `assets/`
- 使用 Windows 反斜線路徑（`assets\images\hero.png`）
- 路徑不含副檔名（`assets/images/hero` 而非 `assets/images/hero.png`）

**Risk**：路徑不一致導致工程師整合時需要手動修正每個路徑，且若已有 CI/CD 自動複製腳本依賴此路徑，會觸發 404 或找不到資源。

**Fix**：確認 repo 根目錄的資源存放規範（通常在 EDD §3 或 ARCH §8 有定義），統一更正所有 output_path 的格式。

---

### Layer 7: 清單完整性（HIGH / MEDIUM / LOW）

#### [MEDIUM] 07 — 資產 ID 有重複

**Check**：同前綴的 ID 是否有重複（如 `RES-IMG-001` 出現兩次）？任何同前綴重複 ID 視為 MEDIUM。

**Risk**：重複 ID 在資產管理工具中造成混淆，工程師加載資源時可能加載錯誤版本。

**Fix**：重新編號衝突 ID，確保同前綴 ID 順序連續無重複（RES-IMG-001, 002, 003...）。

#### [HIGH] 08 — 有裸 placeholder 未替換

**Check**：全文是否有任何未替換的 `{{...}}` placeholder（如 `{{IMG_001_FILENAME}}`）？除 template 範例行外，任何未替換的 placeholder 視為 HIGH。**注意**：`file_size_budget` 欄位的 placeholder 已由審查項目 04（CRITICAL）以更高優先級涵蓋；本項目 08 掃描時應報告除 `file_size_budget` 之外的裸 placeholder 殘留（如 `prompt`、`output_path`、`檔名` 等欄位含 `{{...}}`），這些欄位的 placeholder 嚴重影響資產的可用性。

**Risk**：工程師或設計師拿到含 placeholder 的清單，不知道實際規格，各自猜測填入，導致資產規格不一致；特別是 `prompt` 或 `output_path` 含 placeholder 時，資產無法直接送入 AI 工具或整合進 repo，嚴重影響生產流程。

**Fix**：逐行掃描（排除 `file_size_budget` 欄位，已由 04 處理），所有其他欄位的 `{{...}}` placeholder 替換為具體值或「N/A — 委外製作」等明確說明。

#### [LOW] 09 — source_tool 欄位空白（非 needed 狀態）

**Check**：若 `status` 不是 `needed`，`source_tool` 欄位是否已填入具體工具名稱？空白視為 LOW。

**Risk**：設計師不知道用哪個工具生成，可能選擇不適合該資產類型的工具（如用 DALL-E 生成需要 loop-friendly 的 BGM → 工具完全不適用）。

**Fix**：依資產類型填入推薦工具。圖片 → Midjourney v6；BGM → Suno v3 / Udio；SFX → ElevenLabs SFX / Freesound；動畫 → 委外製作 / Spine Animate。

#### [MEDIUM] 09-B — source_tool 與偵測到的引擎/平台不符

**Check**：從 `docs/EDD.md` 或 `docs/ARCH.md` 偵測目標引擎（Unity / Cocos Creator / Web / Unreal Engine / Godot）。再掃描 §1/§2/§3 所有資產行的 `source_tool` 欄位，對照 `RESOURCE.gen.md` 的「引擎 / 平台偵測規則」表，確認推薦值是否符合目標引擎。

典型不符案例：
- Web 專案的動畫 source_tool 填入 `Spine(.skel)` → Web 引擎應使用 `Lottie / CSS Animation / GSAP`
- Cocos Creator 專案的特效 source_tool 填入 `Unity ShaderGraph` → Cocos 應使用 `Cocos ParticleSystem / Shadertoy`
- Unreal Engine 專案的動畫 source_tool 填入 `Lottie` → Unreal 應使用 `Unreal Motion Capture / Sequencer`
- Godot 專案的特效 source_tool 填入 `Unity ParticleSystem` → Godot 應使用 `Godot ParticleSystem2D`

任何 source_tool 使用目標引擎不支援的格式或工具，視為 MEDIUM。

**Risk**：使用引擎不支援的格式生成資產，整合時需要格式轉換甚至全部重做，影響 milestone 交付；且跨引擎格式（如 `.skel` 在 Web 環境）可能完全無法直接使用，造成資產浪費。

**Fix**：對照 `RESOURCE.gen.md` 引擎/平台偵測規則表，將不符合的 `source_tool` 修正為目標引擎的推薦值（詳見表格「圖片推薦 source_tool」/「動畫推薦 source_tool」/「特效推薦 source_tool」欄），並在 `description` 中說明修正原因（如 `source_tool 由 Spine(.skel) 修正為 Lottie，因目標引擎為 Web`）。

---

### Layer 8: §5 授權章節完整性（MEDIUM）

#### [MEDIUM] 10 — §5 授權章節不完整

**Check**：逐一確認以下三項：
1. §1/§2/§3 中所有資產 ID 均在 §5 授權表格中有對應行（一對一）。
2. 所有 §5 授權行的 `license_type` 欄位非空白（不得為 `{{...}}` 或空值）。
3. `license_type` 為 `purchased`、`commissioned`、`CC-BY` 或 `CC-BY-SA` 的授權行，`license_ref` 欄位已填入具體的授權證明、合約編號或來源連結（非 `N/A`、非空白、非 placeholder）。

**Risk**：授權資訊不明確導致法律風險；purchased / commissioned 資產若無合約編號，發生著作權糾紛時無法舉證，可能造成商業損失或下架風險；CC-BY / CC-BY-SA 資產若未填入原創者姓名標示來源連結，違反授權條款的姓名標示義務，亦有法律風險。

**Fix**：
- 缺少 §5 行：從 §1/§2/§3 補充缺失的資產 ID，依 source_tool 推導 license_type。
- license_type 空白：依 source_tool 判斷並填入（AI 工具 → AI-generated；Freesound CC0 → CC0；CC-BY 來源 → CC-BY；CC-BY-SA 來源 → CC-BY-SA；購買 → purchased；委外 → commissioned）。
- purchased / commissioned 缺少 license_ref：標記 `⚠️ 待補充授權證明 / 委外合約` 並通知相關人員跟進。
- CC-BY / CC-BY-SA 缺少 license_ref：填入原始作品來源連結和原創者姓名（如 `https://freesound.org/people/xxx/sounds/yyy/ by UserName`）；若無法取得，標記 `⚠️ 待補充姓名標示來源連結` 並通知相關人員跟進。

---

### Layer 9: §4 Checklist N/A 後綴正確性（LOW）

#### [LOW] 11 — §4 Checklist 中 N/A 後綴是否正確套用

**Check**：確認 RESOURCE.md §4 Review Checklist 中，與 ANIM.md、AUDIO.md 或 VDD §6 相關的審查項目是否依文件存在性正確標記：
- 若 `docs/ANIM.md` **不存在**，§4 中所有 ANIM 相關項目應附有「（N/A — ANIM.md 不存在）」後綴。
- 若 `docs/AUDIO.md` **不存在**，§4 中所有 AUDIO 相關項目應附有「（N/A — AUDIO.md 不存在）」後綴。
- 若 `docs/VDD.md §6` **不存在**，§4 中「§1 VDD 視覺資產：VDD.md §6 所有場景均有對應 RES-IMG 行（若 VDD.md §6 存在）」應附有「（N/A — VDD.md §6 不存在）」後綴。
- 若相關文件**存在**，對應審查項目不應有 N/A 後綴。

**Risk**：使用者看到未加 N/A 後綴的審查項目，不知道這些項目可以略過（因為對應文件不存在），可能誤以為有漏填，造成困惑或不必要的追問。

**Fix**：依目前 docs/ 目錄下 ANIM.md、AUDIO.md 是否存在及 VDD.md §6 是否存在，手動為 §4 中對應項目補充「（N/A — ANIM.md 不存在）」、「（N/A — AUDIO.md 不存在）」或「（N/A — VDD.md §6 不存在）」後綴；若文件已存在則移除錯誤的 N/A 後綴。


---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/RESOURCE.md`，提取所有 `^## ` heading（含條件章節），共約 7 個
2. 讀取 `docs/RESOURCE.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
