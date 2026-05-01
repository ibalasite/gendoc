---
reviewer-roles:
  - "Technical Artist / 技術美術：審查動畫（§3）、視覺資源（§5）、3D 模型（§7）規格是否符合目標引擎和平台要求"
  - "Audio Engineer / 音效工程師：審查音效（§4）的格式、取樣率、大小限制是否合理"
  - "Frontend Performance Engineer / 效能工程師：審查效能預算（§10）是否符合平台限制，總包體是否可接受"
  - "IP/Legal Reviewer / 智財法務：審查字型（§6）授權是否合法，資源來源是否合規"
quality-bar: "所有資源類型（ANIM/AUDIO/VDD/FONT）均有規格說明或明確略過聲明；§10 效能預算所有數值均有填寫；§6 字型授權欄位均非空白；§2 引擎選型與 FRONTEND.md 一致；無裸 placeholder"
upstream-alignment:
  - "FRONTEND.md §2 client_engine → RESOURCE.md §2 引擎一致性"
  - "EDD.md §10 效能規格 → RESOURCE.md §10 效能預算數值來源"
  - "PDD.md §4/§5/§6 → RESOURCE.md §3/§4/§5/§6 資源對應"
---

# RESOURCE.review.md — Frontend / Client Resource List 審查標準

---

## 審查角色分工

| 角色 | 審查重點 |
|------|---------|
| Technical Artist | §2（引擎一致）、§3（動畫規格）、§5（視覺規格）、§7（3D 模型規格）|
| Audio Engineer | §4（音效規格）、§10（Audio 效能預算）|
| Performance Engineer | §10（整體效能預算）、§5.1（壓縮格式）、總包體限制 |
| IP/Legal | §6（字型授權）、資源來源合規性 |

---

## 審查項目總覽

| # | 嚴重度 | 審查點 | 涉及章節 |
|---|--------|--------|---------|
| 01 | CRITICAL | §2 引擎選型與 FRONTEND.md 不一致 | §2 |
| 02 | CRITICAL | §6 字型授權欄位空白或 TBD | §6 |
| 03 | CRITICAL | §10 效能預算缺失或全為 TBD | §10 |
| 04 | CRITICAL | 有裸 placeholder（`{{...}}`）未替換 | 全文 |
| 05 | HIGH | 資源類型（ANIM/AUDIO/VDD/FONT）缺少任一且無略過說明 | §3-§6 |
| 06 | HIGH | §10 總包體超過平台限制（iOS ≤ 200MB / Android ≤ 150MB）| §10 |
| 07 | HIGH | 壓縮格式未依目標平台填入（全用通用 PNG / WAV）| §5.1, §4.2 |
| 08 | HIGH | 資源清單優先級或狀態欄位空白 | §3.3, §4.3, §5.2 等 |
| 09 | MEDIUM | 動畫格式與目標引擎不相容 | §3.1 |
| 10 | MEDIUM | 資源 ID 有重複（ANIM-001 出現兩次）| §3.3, §4.3 等 |
| 11 | MEDIUM | §11 命名規則與清單資源實際命名不符 | §11, §3-§9 |
| 12 | LOW | 命名規則僅列前綴，未提供完整範例 | §11 |

---

### Layer 1: 引擎一致性與上游對齊（由 Technical Artist 主審，共 2 項）

#### [CRITICAL] 01 — §2 引擎選型與 FRONTEND.md 不一致
**Check**: RESOURCE.md §2 中的 `client_engine` 是否與 `docs/FRONTEND.md §2 技術選型` 或 `.gendoc-state.json` 的 `client_engine` 欄位完全一致？若不一致視為 CRITICAL（引擎不同 → 資源格式全部錯誤）。
**Risk**: 引擎不一致會導致所有資源格式選型錯誤（如 Unity 用 `.skel` 但 Cocos 需要 `.json`；Web 需要 WebP 但 Unity PC 需要 BC7）。工程師按此文件準備資源後發現格式不相容，需要全部重新轉換，延誤 2-4 週。
**Fix**: 讀取 FRONTEND.md §2 或 state 文件，將 §2 的引擎名稱 + 版本更正為與上游一致。同步更新 §3/§4/§5 的格式選型（因為格式依賴引擎）。

#### [HIGH] 02 — §2 資源系統關鍵欄位缺失
**Check**: §2 表格中，`ASSET_MANAGEMENT`（資源管理方式）、`ASSET_BASE_PATH`（資源路徑）是否已填入具體值（非 placeholder 或「待確認」）？
**Risk**: 工程師不知道資源放在哪裡 → 每人自行決定路徑 → 路徑不一致導致打包失敗 / 找不到資源。
**Fix**: 依引擎選型查表（Unity→Addressables/Assets/，Cocos→Bundle/assets/，Web→CDN/public/assets/）填入具體值。

---

### Layer 2: 字型授權與合規（由 IP/Legal 主審，共 2 項）

#### [CRITICAL] 02 — §6 字型授權欄位空白或 TBD
**Check**: §6 字型清單中每個字型的「授權」欄位是否已填寫具體授權類型（OFL / 商業授權 / 嵌入允許 / 自製）？任一欄位為空白、「待確認」、TBD 視為 CRITICAL。
**Risk**: 使用未確認授權的字型進行商業發行 → 版權侵權風險。部分商業字型明確禁止在應用程式中嵌入（如 Helvetica Neue 系列），若使用可能面臨法律責任和應用程式下架。
**Fix**: 確認每個字型的授權條款後填入。優先使用 OFL（SIL Open Font License）字型（如 Noto Sans / Inter / Source Han Sans）；商業字型確認授權書後填入「商業授權（含嵌入）」。

#### [MEDIUM] 03 — 資源來源欄位未追蹤
**Check**: §3-§9 資源清單是否有「來源」欄位或說明（自製 / 第三方 / 授權購買 / 免費 CC0）？缺少來源追蹤視為 MEDIUM。
**Risk**: 無法追蹤第三方資源的授權狀態；若使用了有版權的素材（如付費音效庫的試聽版），可能在發行時被要求下架。
**Fix**: 在資源清單中增加「來源」欄位，標注每個資源的獲取方式（自製/Freesound/Adobe Stock/Unity Asset Store/etc）和授權類型。

---

### Layer 3: 效能預算（由 Performance Engineer 主審，共 3 項）

#### [CRITICAL] 03 — §10 效能預算缺失或全為 TBD
**Check**: §10 效能預算表格中，是否所有資源類型（Texture / Audio / Animation / 3D Mesh / 總包體）均有具體的記憶體上限和包體大小上限？任何欄位為 TBD / 空白 / placeholder 視為 CRITICAL。
**Risk**: 沒有效能預算，美術人員無量化標準，可能產出超規格資源（如 4K 貼圖 × 100 張 = 包體爆炸）；直到打包完成才發現體積超出平台限制，需要全部重新處理。
**Fix**: 依 `EDD.md §10`（效能規格）和目標平台的資料（iOS App Store ≤ 200MB OTA，Android Play ≤ 150MB，Web 首次載入 ≤ 5MB）填入具體數字。

#### [HIGH] 04 — 總包體超過平台限制
**Check**: §10「總包體（初始下載）」的值是否超過目標平台的應用程式大小限制？iOS > 200MB 或 Android > 150MB 視為 HIGH。
**Risk**: App Store / Google Play 對超過大小限制的應用程式有特殊要求（iOS 需要 Wi-Fi 提示，Android 需要 APK Expansion Packs），可能影響下載轉換率和用戶體驗。
**Fix**: 識別最大的資源類型，採用更積極的壓縮（提高 ASTC 壓縮比、降低音效取樣率、對 BGM 使用串流）或將資源改為按需下載（CDN + Dynamic Loading）。

#### [HIGH] 05 — 壓縮格式未依目標平台填入
**Check**: §5.1 壓縮格式是否依目標平台填入（iOS → ASTC，Android → ETC2 / ASTC，Web → WebP，PC → BC7）？若所有平台均填「PNG」或格式欄為空視為 HIGH。
**Risk**: 使用未壓縮 PNG 的貼圖佔用 GPU 記憶體約為 ASTC 的 4-8 倍；行動端記憶體溢出（OOM）會導致應用程式崩潰。
**Fix**: 依目標平台選擇對應的 GPU 壓縮格式；若需多平台支援，使用引擎的自動壓縮功能（Unity Texture Override / Cocos Platform Specific Override）。

---

### Layer 4: 資源規格完整性（由 Technical Artist 主審，共 4 項）

#### [CRITICAL] 04 — 有裸 placeholder 未替換
**Check**: 全文是否有任何未替換的 `{{...}}` placeholder（如 `{{ANIM_001_NAME}}`、`{{CLIENT_ENGINE}}`）？任何未替換的 placeholder 視為 CRITICAL。
**Risk**: 工程師或美術依據此文件準備資源時，看到 placeholder 不知道實際規格，各自猜測填入，導致資源規格不一致。
**Fix**: 逐節掃描，所有 `{{...}}` placeholder 替換為具體值或「略過」說明。

#### [HIGH] 05 — 資源類型缺少且無略過說明
**Check**: §3（動畫）、§4（音效）、§5（視覺）、§6（字型）四個章節是否均有內容？若某章節既無資源清單，也無「本專案無 XXX 資源需求，略過本節」的說明，視為 HIGH（可能是生成時漏掉）。
**Risk**: 審查者和工程師無法判斷是「確認不需要」還是「生成時漏掉了」，導致重複確認工作。
**Fix**: 為缺失章節補充資源清單（若有需求）或填入明確的略過聲明。

#### [HIGH] 06 — 資源清單優先級或狀態欄位空白
**Check**: §3.3、§4.3、§5.2、§5.3、§7.2 等資源清單表格中，每行是否均有填寫「優先級」（P0/P1/P2/P3）和「狀態」（TODO/In Progress/Done）？任一為空白視為 HIGH。
**Risk**: 沒有優先級，美術人員不知道先做哪些資源；沒有狀態，PM 無法追蹤資源進度，可能在 milestone 前才發現關鍵資源未完成。
**Fix**: 所有資源依 PRD 功能優先級填入 P0/P1/P2/P3；初始狀態統一填 TODO。

#### [MEDIUM] 07 — 動畫格式與目標引擎不相容
**Check**: §3.1 動畫工具 / 格式是否與 §2 引擎選型相容？（如 Unity 用 Spine 格式 `.skel` 是合法的，但如果 §2 是 Cocos Creator 但 §3 填 `.anim`（Unity 格式）則不相容）
**Risk**: 格式不相容的動畫資源無法被引擎載入，需要整批轉換，可能延誤 1-2 週。
**Fix**: 查表（RESOURCE.gen.md 引擎 → 動畫格式對照）後修正格式選型。

---

### Layer 5: 清單完整性（由 Technical Artist 通盤審查，共 3 項）

#### [MEDIUM] 08 — 資源 ID 有重複
**Check**: 同類型的資源 ID 是否有重複（如 `ANIM-001` 出現兩次）？任何同類型重複 ID 視為 MEDIUM。
**Risk**: 重複 ID 會在資源管理工具（Addressables / Bundle）中造成衝突，可能載入錯誤資源或資源載入失敗。
**Fix**: 重新編號衝突的 ID，確保同類型 ID 順序連續無重複。

#### [MEDIUM] 09 — §11 命名規則與清單資源命名不符
**Check**: §11 命名規則中定義的前綴（如 `anim_`），是否與 §3.3 動畫清單中的資源命名一致？若清單中有 `char_hero_idle.skel`（缺少 `anim_` 前綴）視為 MEDIUM。
**Risk**: 命名規則不一致導致工程師在實際命名時產生困惑，各自遵循不同規則，後期重命名成本高。
**Fix**: 統一補充前綴，確保所有清單資源命名符合 §11 定義的規則。

#### [LOW] 10 — §11 命名規則範例不完整
**Check**: §11 中每個前綴是否都有提供完整的命名範例（包含前綴 + 功能描述 + 序號 + 副檔名）？
**Risk**: 若僅有前綴無範例，不同美術人員對「如何組合」的理解不同，導致實際命名千奇百怪。
**Fix**: 補充每個前綴的完整命名範例（如 `anim_char_hero_idle.skel`、`sfx_btn_click_001.wav`）。
