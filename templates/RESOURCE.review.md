---
reviewer-roles:
  - "Asset Production Planner / 資產生產規劃師：主審 §1 VDD 視覺資產覆蓋完整性、§2 ANIM 動態資產覆蓋完整性、§3 AUDIO 音效資產覆蓋完整性"
  - "Performance Budget Auditor / 效能預算審查員：主審所有 file_size_budget 欄位，確認數值符合平台限制（手遊 ≤ 2MB/texture、Web ≤ 200KB/image、BGM ≤ 5MB、SFX ≤ 500KB）"
  - "AI Prompt Quality Reviewer / AI Prompt 品質審查員：主審 prompt 欄位是否有具體且可用的生成提示詞，確認非 needed 狀態的資產均有 prompt"
quality-bar: "VDD §4 所有角色有 RES-IMG 行；ANIM SKEL/VFX 所有項目有 RES-ANIM 行（若存在）；所有 file_size_budget 符合平台限制；非 needed 狀態資產的 prompt 非空白；output_path 與 repo 結構一致；無裸 placeholder"
upstream-alignment:
  - "VDD.md §4 角色清單 → RESOURCE.md §1 RES-IMG 行（一對一對應）"
  - "VDD.md §5 UI 視覺系統 → RESOURCE.md §1 UI 場景 RES-IMG 行"
  - "ANIM.md §2 SKEL-xxx 清單 → RESOURCE.md §2 RES-ANIM 行（一對一對應，若 ANIM.md 存在）"
  - "ANIM.md §5 VFX-xxx 清單 → RESOURCE.md §2 RES-ANIM 行（type=particle，若存在）"
  - "AUDIO.md §2 BGM-xxx 清單 → RESOURCE.md §3 RES-BGM 行（若 AUDIO.md 存在）"
  - "AUDIO.md §3 SFX-xxx 清單 → RESOURCE.md §3 RES-SFX 行（若 AUDIO.md 存在）"
---

# RESOURCE.review.md — AI 資產生產訂單審查標準

---

## 審查角色分工

| 角色 | 審查重點 |
|------|---------|
| Asset Production Planner | §1（VDD 角色 + UI 覆蓋）、§2（ANIM SKEL/VFX 覆蓋）、§3（AUDIO BGM/SFX 覆蓋）|
| Performance Budget Auditor | 所有行的 file_size_budget 欄位（§1/§2/§3）|
| AI Prompt Quality Reviewer | 所有行的 prompt 欄位（§1/§2/§3）|

---

## 審查項目總覽

| # | 嚴重度 | 審查點 | 涉及章節 |
|---|--------|--------|---------|
| 01 | CRITICAL | VDD §4 角色缺少 RES-IMG 行 | §1 |
| 02 | CRITICAL | ANIM SKEL/VFX 項目缺少 RES-ANIM 行 | §2 |
| 03 | CRITICAL | file_size_budget 空白或超過平台限制 | §1/§2/§3 |
| 04 | HIGH | prompt 欄位空白（非 needed 狀態） | §1/§2/§3 |
| 05 | HIGH | output_path 與 repo 目錄結構不一致 | §1/§2/§3 |
| 06 | MEDIUM | ID 有重複（同前綴 ID 出現兩次） | 全文 |
| 07 | MEDIUM | 有裸 placeholder（`{{...}}`）未替換 | 全文 |
| 08 | LOW | source_tool 欄位空白（status=needed 除外） | §1/§2/§3 |

---

### Layer 1: VDD 視覺資產覆蓋完整性（CRITICAL）

#### [CRITICAL] 01 — VDD §4 角色設計缺少 RES-IMG 行

**Check**：讀取 `docs/VDD.md §4 角色設計`，列出所有角色（hero、NPC、monster 等）。逐一確認 RESOURCE.md §1 是否有對應的 `RES-IMG-xxx` 行。任何 VDD §4 角色沒有對應 RES-IMG 行視為 CRITICAL。

**Risk**：缺少資產清單的角色在開發後期才被發現遺漏，設計師需要臨時插單生成，影響 milestone 交付；且 prompt 無版本控制，後期補做的資產與已有資產風格不一致。

**Fix**：對照 VDD §4 角色清單，在 RESOURCE.md §1 補充缺失角色的 RES-IMG 行。每個角色至少有：idle 狀態立繪（若為 2D）或 T-Pose 渲染圖（若為 3D）。依 VDD 風格描述生成第一版 prompt。

---

### Layer 2: ANIM 動態資產覆蓋完整性（CRITICAL）

#### [CRITICAL] 02 — ANIM.md SKEL/VFX 項目缺少 RES-ANIM 行

**Check**：若 `docs/ANIM.md` 存在，讀取其 `§2 骨骼動畫清單`（SKEL-xxx）和 `§5 粒子特效清單`（VFX-xxx）。逐一確認 RESOURCE.md §2 是否有對應的 `RES-ANIM-xxx` 行。任何 SKEL-xxx 或 VFX-xxx 沒有對應 RES-ANIM 行視為 CRITICAL。

若 ANIM.md 不存在，確認 §2 有明確的「略過說明」→ 不視為 CRITICAL。

**Risk**：動畫資產（骨骼動畫源檔、粒子貼圖）是開發最長的資產，若規劃遺漏，在整合測試前才被發現，將造成 2-4 週的延誤。

**Fix**：對照 ANIM.md 的 SKEL-xxx / VFX-xxx 清單，在 RESOURCE.md §2 補充缺失的 RES-ANIM 行。骨骼動畫 `type=animation`，粒子特效 `type=particle`。

---

### Layer 3: 效能預算（CRITICAL）

#### [CRITICAL] 03 — file_size_budget 空白或超過平台限制

**Check**：逐行掃描 §1/§2/§3 所有資產行的 `file_size_budget` 欄位。以下任一情況視為 CRITICAL：
- 欄位為空白、TBD、或 placeholder（`{{...}}`）
- 圖片資產（type=image）超過：手遊 > 2 MB / Web > 200 KB
- 音樂資產（type=bgm）超過：> 5 MB
- 音效資產（type=sfx）超過：> 500 KB
- 動畫資產（type=animation）超過：> 2 MB per animation file

**Risk**：無效能預算上限時，設計師生成高解析度資產（如 4K PNG × 50 張），最終打包後發現 App 超過平台大小限制（iOS OTA ≤ 200MB）或首屏載入超時（Web FCP > 3s），需全部重新生成並壓縮。

**Fix**：依目標平台填入具體數值：
- 手遊（iOS/Android）圖片：`≤ 2 MB`；UI 圖示：`≤ 200 KB`
- Web 圖片：`≤ 200 KB`（關鍵路徑）/ `≤ 1 MB`（懶加載）
- BGM：`≤ 5 MB`；SFX：`≤ 500 KB`；VO：`≤ 1 MB`
- 動畫 source（.skel/.json）：`≤ 2 MB`；粒子貼圖：`≤ 512 KB`

---

### Layer 4: Prompt 品質（HIGH）

#### [HIGH] 04 — prompt 欄位空白（非 needed 狀態）

**Check**：逐行掃描 §1/§2/§3 所有資產行。若 `status` 為 `prompt_ready`、`generating`、`generated`、`approved`，則 `prompt` 欄位必須非空白。若 `status=needed` 則允許 prompt 空白。任何非 needed 狀態的 prompt 空白視為 HIGH。

**Risk**：設計師拿到清單後，發現 prompt 是空的，需要自己撰寫提示詞，失去 AI 輔助規劃的效益；且不同設計師撰寫的 prompt 風格不一致，生成結果無法保持視覺連貫性。

**Fix**：依 VDD 的視覺風格描述，為每個非 needed 狀態的資產補充具體 prompt。英文為主（Midjourney/DALL-E/Suno 均優先支援英文）。格式參考 RESOURCE.gen.md 的「常用 AI 工具與 Prompt 格式速查」表。

---

### Layer 5: 交付路徑（HIGH）

#### [HIGH] 05 — output_path 與 repo 目錄結構不一致

**Check**：抽查 §1/§2/§3 中至少 20% 的 output_path，確認路徑格式是否與實際 repo 目錄結構一致。典型不一致案例：
- 使用 `src/assets/` 但 repo 實際根目錄為 `assets/`
- 使用 Windows 反斜線路徑（`assets\images\hero.png`）
- 路徑不含副檔名（`assets/images/hero` 而非 `assets/images/hero.png`）

**Risk**：路徑不一致導致工程師整合時需要手動修正每個路徑，且若已有 CI/CD 自動複製腳本依賴此路徑，會觸發 404 或找不到資源。

**Fix**：確認 repo 根目錄的資源存放規範（通常在 EDD §3 或 ARCH §8 有定義），統一更正所有 output_path 的格式。

---

### Layer 6: 清單完整性（MEDIUM / LOW）

#### [MEDIUM] 06 — 資產 ID 有重複

**Check**：同前綴的 ID 是否有重複（如 `RES-IMG-001` 出現兩次）？任何同前綴重複 ID 視為 MEDIUM。

**Risk**：重複 ID 在資產管理工具中造成混淆，工程師加載資源時可能加載錯誤版本。

**Fix**：重新編號衝突 ID，確保同前綴 ID 順序連續無重複（RES-IMG-001, 002, 003...）。

#### [MEDIUM] 07 — 有裸 placeholder 未替換

**Check**：全文是否有任何未替換的 `{{...}}` placeholder（如 `{{IMG_001_FILENAME}}`）？除 template 範例行外，任何未替換的 placeholder 視為 MEDIUM。

**Risk**：工程師或設計師拿到含 placeholder 的清單，不知道實際規格，各自猜測填入，導致資產規格不一致。

**Fix**：逐行掃描，所有 `{{...}}` placeholder 替換為具體值或「N/A — 委外製作」等明確說明。

#### [LOW] 08 — source_tool 欄位空白（非 needed 狀態）

**Check**：若 `status` 不是 `needed`，`source_tool` 欄位是否已填入具體工具名稱？空白視為 LOW。

**Risk**：設計師不知道用哪個工具生成，可能選擇不適合該資產類型的工具（如用 DALL-E 生成需要 loop-friendly 的 BGM → 工具完全不適用）。

**Fix**：依資產類型填入推薦工具。圖片 → Midjourney v6；BGM → Suno v3 / Udio；SFX → ElevenLabs SFX / Freesound；動畫 → 委外製作 / Spine Animate。
