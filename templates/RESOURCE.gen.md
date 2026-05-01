---
doc-type: RESOURCE
output-path: docs/RESOURCE.md
upstream-docs:
  required:
    - docs/FRONTEND.md
    - docs/EDD.md
    - docs/PRD.md
  recommended:
    - docs/PDD.md
    - docs/ARCH.md
expert-roles:
  gen:
    - "Technical Artist / 技術美術：負責動畫（§3）、視覺資源（§5）、3D 模型（§7）的規格設計；從 FRONTEND.md 提取引擎選型，確保格式相容性"
    - "Game/App Audio Engineer / 音效工程師：負責音效（§4）的格式、取樣率、大小規格；確保行動端壓縮率合理"
    - "Frontend Performance Engineer / 前端效能工程師：負責效能預算（§10）；從 EDD.md §10 Performance 章節提取容量目標，確保包體和記憶體在平台限制內"
quality-bar: "所有資源類型（ANIM/AUDIO/VDD/FONT）均有規格說明；每個資源均有 ID + 優先級 + 狀態；§10 效能預算所有類型均有上限；若資源類型不適用，有明確「略過」說明；§2 引擎選型與 FRONTEND.md 一致"
---

# RESOURCE.gen.md — Frontend / Client Resource List 生成規則

依 FRONTEND.md、EDD.md、PRD.md、PDD.md 的需求，生成完整的前端 / 客戶端資源清單。

---

## Iron Rule

**Iron Law**：生成任何 RESOURCE.md 之前，必須先讀取 `RESOURCE.md`（骨架結構）和 `RESOURCE.gen.md`（本規則）。

生成時**依序執行**每個 Step，不得跳過或合並執行。每個 Step 完成後再進行下一個。

---

## 上游文件讀取規則

### 必讀上游鏈

| 文件 | 必讀章節 | 用途 |
|------|---------|------|
| `FRONTEND.md` | §2 技術選型、§3 架構、§4 Screen 清單 | **主要輸入**：確認 `client_engine`（Unity/Cocos/Web 等）→ 決定資源格式（.fbx vs .gltf, .ogg vs .mp3 等）|
| `EDD.md` | §3.3 技術棧、§3.5 環境矩陣、§10 效能規格 | 平台（iOS/Android/PC/Web）→ 決定壓縮格式和包體限制；效能目標 → §10 效能預算 |
| `PRD.md` | §功能清單、§User Stories | 功能需求 → 確認哪些資源類型是必要的（是否有動畫 / 音效 / 影片）|
| `PDD.md`（若存在）| §4 UI 設計、§5 互動設計、§6 視覺風格 | UI 視覺規格 → 字型選型、Atlas 設計、UI 動畫需求 |

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- `FRONTEND.md` 的 `client_engine` vs `EDD.md §3.3` 的技術棧（是否一致）
- `PRD.md` 功能需求（若有語音功能 → 音效必須涵蓋 Voice 類型）
- `PDD.md §6` 視覺風格（若有 3D 場景 → 必須有 §7 3D 模型清單）

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並在對應章節說明。

---

## Step 1：確認客戶端引擎與資源系統（§2）

1. 讀取 `FRONTEND.md §2`（技術選型）或 `.gendoc-state.json` 的 `client_engine` 欄位。
2. 填入 §2 資源規格表：
   - `client_engine`（引擎名稱 + 版本）
   - `ASSET_MANAGEMENT`（Unity Addressables / Cocos Bundle / webpack / CDN 等）
   - `BUILD_TOOL`（TexturePacker / Spine / webpack / vite 等）
   - `ASSET_BASE_PATH`（引擎預設資源路徑）
   - `VERSIONING`（Git LFS / S3 Versioning / CDN Cache Busting 等）

**引擎 → 資源系統對照：**

| 引擎 | 資源管理 | 預設路徑 |
|------|---------|---------|
| Unity | Addressables | `Assets/` |
| Cocos Creator | Bundle | `assets/` |
| React / Vue（Web）| CDN / webpack | `public/assets/` |
| Flutter | pubspec assets | `assets/` |
| React Native | Metro Bundler | `src/assets/` |
| 其他 | 依引擎文件 | 依引擎預設 |

---

## Step 2：ANIM 動畫資源（§3）

1. 讀取 `PDD.md §5 互動設計`（若有動畫互動）和 `PRD.md`（若有「動畫」「過場」「角色」相關需求）。
2. 判斷動畫類型：
   - 若有 UI 動畫 → 依引擎選型填入工具（Unity DoTween / CSS Animation / Lottie / Spine）
   - 若有角色動畫 → 依引擎選型填入 Skeleton / Animator 工具
   - 若有過場動畫 → 填入 Timeline / Video / Lottie
3. 若無任何動畫需求 → 在 §3 填入「本專案無動畫資源需求，略過本節」並繼續下一 Step。
4. 填入 §3.2 規格（幀率 / 最大時長 / 格式 / 大小限制 / 命名規則）。
5. 生成 §3.3 動畫清單（≥ 3 個資源，含優先級和狀態欄位）。

**引擎 → 動畫格式對照：**

| 引擎 | UI 動畫 | 角色動畫 |
|------|---------|---------|
| Unity | DoTween / Animator | `.anim` + Humanoid Rig |
| Cocos | Tween / Skeleton | `.json` Spine / DragonBones |
| Web | CSS Animation / Framer Motion / Lottie | Lottie JSON / CSS Keyframe |
| Flutter | AnimationController | Rive / Lottie |

---

## Step 3：AUDIO 音效資源（§4）

1. 讀取 `PRD.md`（是否有「音效」「背景音樂」「語音」相關需求）。
2. 判斷音效類型：
   - 若有 BGM → 填入 BGM 工具和規格
   - 若有 SFX → 填入 SFX 工具和規格
   - 若有語音 Voice → 在 §4.1 增加 Voice 行
3. 若無任何音效需求 → 在 §4 填入「本專案無音效資源需求，略過本節」。
4. 填入 §4.2 規格（格式 / 取樣率 / 位元深度 / 大小限制 / 命名規則）。
5. 生成 §4.3 音效清單（≥ 3 個資源，含 BGM 和 SFX 各至少 1 個）。

**平台 → 音效格式推薦：**

| 平台 | BGM | SFX |
|------|-----|-----|
| iOS / Android | `.ogg`（Android）/ `.caf`（iOS）| `.wav` |
| Web | `.ogg` + `.mp3`（fallback）| `.ogg` / `.mp3` |
| PC（Unity）| `.ogg` | `.wav` |
| 通用 | `.ogg`（壓縮率最佳）| `.wav`（低延遲）|

---

## Step 4：視覺資源 Texture / Sprite / Atlas（§5）

1. 讀取 `PDD.md §4 UI 設計`（頁面清單、元件清單）和 `EDD.md §3.5`（目標平台）。
2. 依目標平台填入 §5.1 壓縮格式：
   - iOS：ASTC 6×6（高品質）/ ASTC 8×8（更小包體）
   - Android：ETC2（通用）/ ASTC（現代設備）
   - Web：WebP（AVIF fallback）
   - PC：BC7 / BC1（DXT1）
3. 生成 §5.2 UI 資源清單（依 PDD 頁面清單提取，≥ 5 個 UI 資源）。
4. 若有角色 / 場景 Sprite → 生成 §5.3 Sprite 清單。

---

## Step 5：Font 字型資源（§6）

1. 讀取 `PDD.md §6 視覺風格`（字型規格）或 `EDD.md §3.3`（多語言支援）。
2. 生成 §6 字型清單（≥ 2 個字型，含授權欄位）：
   - 主字型（正文）
   - 標題字型（若與正文不同）
   - 若有多語言支援 → 各語系字型各一行
3. **授權必填**：每個字型的授權欄位必須填寫（OFL / 商業授權 / 自製）；禁止填寫「待確認」。

---

## Step 6：3D 模型、影片、本地化（§7、§8、§9）

逐一判斷是否需要：

**§7 3D 模型**：
- 讀取 `EDD.md §3.3`（是否有 3D 渲染引擎選型）或 `PRD.md`（是否有「3D 場景」「AR / VR」需求）
- 若需要 → 填入 §7.1 規格 + §7.2 清單（≥ 3 個模型）
- 若不需要 → 填入「本專案無 3D 模型資源需求，略過本節」

**§8 影片**：
- 讀取 `PRD.md`（是否有「過場動畫（影片）」「教學影片」需求）
- 若需要 → 填入 §8 清單
- 若不需要 → 填入「本專案無影片資源需求，略過本節」

**§9 本地化**：
- 讀取 `.gendoc-state.json` 的 `locales` 欄位或 `PRD.md`（是否有多語言需求）
- 若需要 → 填入 §9.1 規格 + §9.2 字串示例（≥ 5 個字串 ID）
- 若不需要 → 填入「本專案僅支援單語言，略過本節」

---

## Step 7：效能預算（§10）

1. 讀取 `EDD.md §10`（效能規格）或 `EDD.md §3.5`（目標平台和設備等級）。
2. 依平台和設備等級填入各類型的記憶體上限、包體大小上限、載入時間上限。
3. **總包體限制**（必填，不得為 TBD）：
   - iOS App Store OTA：≤ 200MB（超過需 Wi-Fi 下載提示）
   - Google Play：≤ 150MB（超過需 APK Expansion）
   - Web（首次載入）：≤ 5MB（核心資源）+ 按需載入
   - PC：依遊戲類型（Casual ≤ 500MB，AAA ≤ 50GB）
4. 確認 §10 所有行均有數值（不得有 TBD / 待確認）。

---

## Step 8：命名規則總覽（§11）與 Review Checklist（§12）

1. 確認 §11 命名規則前綴與實際清單（§3-§9）中的命名一致。
2. 逐項確認 §12 Review Checklist 所有項目。

---

## 生成前自我檢核清單

- [ ] §2 引擎選型與 `FRONTEND.md` 的 `client_engine` 一致
- [ ] §3 動畫：若有需求，至少 3 個資源；若無需求，明確標注「略過」
- [ ] §4 音效：若有需求，BGM + SFX 各至少 1 個資源；若無需求，明確標注「略過」
- [ ] §5 視覺資源：壓縮格式依目標平台填入（非通用 PNG 格式）
- [ ] §6 字型：每個字型授權已填寫（非空白）
- [ ] §7-§9：若無需求，均有明確「略過」說明
- [ ] §10 效能預算：所有資源類型均有數值（不得有 TBD）
- [ ] §11 命名規則與清單資源命名一致
- [ ] 所有資源 ID 格式：`TYPE-NNN`（如 ANIM-001）
- [ ] 所有資源均有優先級（P0/P1/P2/P3）和狀態（TODO/In Progress/Done）

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| §2 引擎一致性 | RESOURCE.md §2 的 `client_engine` 與 FRONTEND.md / state 的 `client_engine` 值完全一致 | 修正 §2 引擎欄位 |
| 資源類型覆蓋 | ANIM / AUDIO / VDD / FONT 四種類型均有內容，或有明確「略過」說明 | 補充缺失類型或填入略過說明 |
| 效能預算完整 | §10 所有資源類型的記憶體上限、包體大小上限均有具體數值 | 從 EDD.md §10 提取填入 |
| 無裸 placeholder | 所有 `{{...}}` 欄位均已替換為具體值或有「略過」說明 | 逐欄補全 |
| 字型授權已填 | §6 每個字型的授權欄位非空白、非 TBD | 確認授權後填入 |
| 資源 ID 唯一 | 同類型 ID 無重複（ANIM-001 不重複出現）| 重新編號衝突 ID |
| 狀態欄位有值 | 每個資源的狀態欄位為 TODO / In Progress / Done 之一 | 補充狀態 |
| 總包體有上限 | §10 「總包體（初始下載）」有具體 MB 數值，符合目標平台限制 | 填入平台對應包體限制 |
