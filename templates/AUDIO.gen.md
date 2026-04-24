---
doc-type: AUDIO
output-path: docs/AUDIO.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md     # 目標平台（iOS/Android/Web）→ 音訊 codec/格式選擇
  - docs/VDD.md     # 視覺設計語言 → 音效與視覺事件時序對齊（情緒、氛圍）
  - docs/EDD.md
  - docs/FRONTEND.md
quality-bar: "§2 每個主要場景都有對應 BGM；§3 所有 P0 User Story 觸發的互動都有對應 SFX；§4 若有劇情/教學則每條 VO 觸發條件精確到事件名稱且無裸 placeholder；§5 音效觸發邏輯完整無歧義；§6 引擎設定代碼可直接複製使用；§7 資產命名符合規範；§8 載入策略與 EDD.md/FRONTEND.md 一致；§9 效能預算已填具體數值；§10 測試清單覆蓋 §3 所有 SFX；無裸 placeholder"
---

# AUDIO.gen.md — 音效設計文件生成規則

依 PRD + EDD + FRONTEND 產出 AUDIO.md，涵蓋 BGM/SFX/VO 完整清單、音效觸發邏輯、引擎特定設定、資產規格與效能預算。

---

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材也必須全部關聯讀取。

**Iron Law**：生成任何 AUDIO.md 之前，必須先讀取 `AUDIO.md`（結構）和 `AUDIO.gen.md`（本規則）。

---

## 專家角色（Expert Roles）

| 角色 | 負責章節 | 專業要求 |
|------|---------|---------|
| 資深音效設計師（Senior Audio Designer） | §1, §2, §3, §4, §5 | 10 年遊戲/互動音效設計，熟悉情感設計、聲景設計、循環音樂剪輯 |
| 技術音效工程師（Technical Audio Engineer） | §6, §7, §8, §9 | 深度熟悉 Cocos AudioEngine、Unity AudioMixer、Web Audio API、Howler.js 整合實作 |
| QA 音效測試員（Audio QA） | §10 | 熟悉音效壓力測試、跨平台音效相容性驗證、記憶體洩漏偵測 |

---

## 全域規則（Global Invariant）

生成完成的 AUDIO.md 中不得出現任何未替換的 `{{PLACEHOLDER}}`（Document Control、Change Log 及 §1～§10 全部章節）。

唯一例外：VO 文本尚未確定時，允許使用 `[TBD-腳本確認中]` 標注，但禁止保留原始 `{{TEXT}}`、`{{TRIGGER}}`、`{{LANG}}` 等裸 placeholder。

生成代理必須在完成全部章節後執行一次全文掃描，確認無裸 placeholder 殘留後方可輸出。

---

## 上游文件讀取規則

### 必讀上游鏈（依優先順序）

| 文件 | 必讀章節 | 用途 |
|------|---------|------|
| `IDEA.md`（若存在）| 全文 | 了解產品性質——判斷是遊戲、互動應用或純 Web；推斷音效風格（卡通/寫實/電子/古典） |
| `BRD.md` | 目標平台、使用者裝置 | 確定 §1.3 目標平台音效限制（iOS/Android/Web/PC 各別格式與頻道限制） |
| `PRD.md` | 所有 User Stories 與 AC、P0/P1/P2 分類 | §3 SFX 清單必須覆蓋所有 P0 User Story 中提到的互動事件；§2 BGM 場景對應 PRD 功能流程 |
| `EDD.md` | §2 技術棧、§4 安全設計 | 確認引擎（Cocos/Unity/Web）→ 決定 §6 引擎設定章節重點；音效資源載入策略與 EDD 資源管理對齊 |
| `FRONTEND.md`（若存在）| §2 平台選型、§4 畫面清單、§7 資源管理 | **最重要的上游**：確認確切使用的引擎版本和音效 API；畫面清單 → BGM 切換時機；資源管理策略 → §8 載入策略 |

### 引擎偵測規則

讀取完 EDD.md 和 FRONTEND.md 後，執行引擎偵測：

```
if FRONTEND.md §2 包含 "Cocos Creator" → 重點展開 §6.1 Cocos 設定，其他引擎章節標注「不適用本專案」
if FRONTEND.md §2 包含 "Unity" → 重點展開 §6.2 Unity 設定
if FRONTEND.md §2 包含 "HTML5" / "PixiJS" / "Phaser" / "Web" → 重點展開 §6.3 HTML5 設定
if 無法偵測 → 三個引擎設定章節全部展開（通用版）
```

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- FRONTEND.md 引擎版本 vs §6 代碼範例 API（是否與該引擎版本相符）
- BRD.md 目標平台 vs §1.3 平台限制表（是否每個目標平台都有對應行）
- PRD P0 互動事件 vs §3.1/§3.2 SFX 清單（是否每個 P0 事件都有對應 SFX-ID）
- PRD/腳本文件中定義的 VO 觸發事件 vs §4 VO 清單的觸發條件欄位（是否每條 VO 的觸發條件精確對應文件中事件名稱，而非模糊描述）
- EDD.md §4 資源管理設計 + FRONTEND.md §7 資源管理策略 vs §8 載入策略（各類音效的載入時機與載入方式是否一致）

---

## 生成步驟

### Step 1：確認音效風格與引擎

填入 Document Control：PROJECT 填專案代號（用於 DOC-ID，如 `PROJ-ALPHA`）、VERSION 依專案版本、STATUS 設 Draft、AUTHOR 填負責人、DATE 填今日日期（格式 YYYY-MM-DD）、ENGINE 依偵測結果填入確切引擎名稱與版本。注意 DOC-ID 由 `AUDIO-{{PROJECT}}-{{DATE}}` 構成，必須同時替換 PROJECT 和 DATE 兩個 placeholder。

1. 從 IDEA.md 推斷音效情感風格（卡通輕快 / 史詩壯闊 / 清新自然 / 電子科技 / 其他）
2. 從 FRONTEND.md 確認確切引擎名稱與版本
3. 填入 §1.1 設計目標、§1.2 設計原則
4. 填入 §1.3 目標平台音效限制（依 BRD 目標平台逐行填寫具體數值）

**§1.3 填寫規範：**
- iOS 同時播放：建議 16 頻道（Web Audio API）或 32 頻道（AVAudioEngine）
- Android：建議 16 頻道（AudioTrack）
- Web：依瀏覽器，Chrome 建議 ≤ 32 個 AudioContext 節點
- 格式：iOS/Android 主 .mp3，Web 主 .webm 備 .mp3

### Step 2：BGM 清單（§2）

1. 從 PRD.md §4（或等效的功能流程）提取所有主要場景/狀態
2. 每個主要場景必須有至少 1 條 BGM 記錄（P0 場景），次要場景至少 1 條（P1）
3. 為每條 BGM 填寫：
   - ID：`BGM-{三位數序號}`
   - 檔案路徑：依 §7.3 目錄結構填寫（不得裸 placeholder）
   - 淡入/淡出時間：依場景情感激烈程度決定（戰鬥場景 200ms，大廳 500ms，過場 1000ms）
4. 填寫 §2.1 BGM 切換規則（每個場景切換路徑至少一條）

### Step 3：SFX 清單（§3）

**§3.1 UI 音效（必須覆蓋）：**
- 按鈕點擊（onTouchStart/onClick）
- 按鈕 hover（若適用 Web/PC）
- 介面開啟/關閉（panel show/hide）
- 確認/取消操作
- 錯誤提示

**§3.2 遊戲/互動音效：**
從 PRD.md 提取所有 P0 User Story 中的互動動作，逐一對應一個 SFX-ID。
每條記錄必須填寫：觸發事件（精確到 event 名稱）、優先級（CRITICAL/HIGH/MEDIUM/LOW）、最大同播數。

**§3.3 環境音效：**
依場景數量，每個場景評估是否需要環境音（遊戲場景建議加入）。

**SFX 填寫規範：**
- 優先級：影響戰鬥勝負 → CRITICAL；技能音效 → HIGH；UI 互動 → MEDIUM；背景 → LOW
- 最大同播數：爆炸/命中類 ≤ 3，按鈕 ≤ 1，BGM 永遠 = 1，§3.3 環境音（Ambient）≤ 2

### Step 4：VO 清單（§4）

若 IDEA/PRD 中有劇情引導、教學旁白、角色對話，則填寫 §4。
若無，§4 填「本專案無語音/旁白設計（純音效）」並跳過。

**VO 填寫規範：**

1. **ID 格式**：`VO-{三位數序號}`，從 VO-001 開始遞增，不得跳號。
2. **文本內容**：從 PRD/腳本逐句提取原文，保留完整語句。若文本尚未確定，標注 `[TBD-腳本確認中]`，禁止使用裸 `{{TEXT}}` placeholder。
3. **觸發條件**：必須精確到事件名稱（如 `onTutorialStep1Enter`、`onCutsceneStart`），不得寫模糊描述（如「進入教學」）。
4. **語言碼**：使用 ISO 639-1 雙字母代碼（`zh`、`en`、`ja`、`ko`、`fr` 等）。
5. **多語言規則**：每種語言的同一條 VO 獨立成一行，ID 相同但語言碼不同（如 VO-001 zh、VO-001 en）。
6. **優先級**：
   - 教學旁白、劇情必播 VO → `CRITICAL`（不得被任何 SFX 打斷）
   - 一般角色提示、劇情旁白 → `HIGH`（可打斷低優先級 SFX）
   - 可選/重複性提示 VO → `MEDIUM`

### Step 5：音效觸發邏輯（§5）

1. 依 §3.1 音效優先級，填寫 §5.1 優先級表（直接使用預設值，依專案調整 CRITICAL/HIGH 的具體定義）
2. 依 PRD 主要場景，為每個場景填寫 §5.2 觸發條件矩陣（至少覆蓋 3 個主要場景）
3. 填寫 §5.3 互斥規則（使用預設規則，如有特殊規則另行添加）

### Step 6：引擎設定（§6）

依 Step 1 偵測到的引擎，展開對應子章節：

**§6.1 Cocos Creator（若適用）：**
- 填入具體的音量初始值（BGM 建議 0.8，SFX 建議 1.0）
- 填入 maxChannels（建議 16~24）
- 填入 BGM 淡入時間（秒，與 §2.1 一致）
- AudioSource 元件設定表使用實際值

**§6.2 Unity（若適用）：**
- AudioMixer 樹必須反映 §3 的分組（BGM/SFX_UI/SFX_Game/VO）
- Snapshot 表列出 PRD 中提到的所有遊戲狀態

**§6.3 HTML5（若適用）：**
- Howler.js 代碼範例必須填入真實的 src 路徑（依 §7.3 目錄結構）
- SFX Sprite 的 sprite 物件必須包含 §3.1 所有 UI 音效的 offset/duration
- 必須包含 Web Audio Context 解鎖代碼（iOS/Chrome 強制要求）

### Step 7：資產規格與命名（§7）

1. §7.1 命名規範：確認範例符合本專案的模組命名（MODULE 替換為實際模組名）
2. §7.2 格式規格：確認 HTML5 專案包含 .webm 主格式（Safari 需要 .mp3 備用）
3. §7.3 目錄結構：根據引擎偵測結果，從下表選取對應的資產根目錄，並確保 §2/§3/§4 所有清單的「檔案路徑」均以此根目錄為前綴：

   | 引擎 | 資產根目錄 |
   |------|----------|
   | Cocos Creator 3.x | `assets/audio/` |
   | Cocos Creator 2.x | `resources/audio/` |
   | Unity（Resources.Load 方式） | `Assets/Resources/Audio/` |
   | Unity（AssetBundle 方式） | `Assets/Audio/` |
   | HTML5（Vite / CRA / Next.js 等前端框架） | `public/audio/` 或 `src/assets/audio/`（依前端框架約定） |

   **所有清單路徑必須使用此處確認的根目錄，不得保留通用 placeholder。**

### Step 8：載入策略（§8）

依 FRONTEND.md §7 資源管理策略，填寫 §8：
- 若有 AssetBundle/資源包 → BGM 按場景打包
- 若用 CDN → VO 按語言分包，BGM 串流

### Step 9：效能預算（§9）

**必須填入具體數值，不得保留 placeholder：**
- 同時播放頻道數：Cocos/Unity 建議 16~24；Web Audio 建議 ≤ 32
- 音效 CPU 佔用：移動端 ≤ 5%；PC/Web ≤ 3%
- 音效首包體積：≤ 5MB（P0 核心音效）；完整包 ≤ 20MB
- BGM 記憶體：單條 ≤ 10MB（解碼後 PCM）
- 總音效記憶體：≤ 50MB（常駐預載）

若有特殊需求（電影級音效），可放寬並說明原因。

### Step 10：測試清單（§10）

§10 預設 8 個測試案例（AUD-T-001 至 AUD-T-008）必須全部保留，不得刪除。其中 AUD-T-005（iOS Safari 首次點擊後 BGM/SFX 正常播放）為平台相容性必備測試，即使專案不主打 iOS 也必須保留。依 §3 SFX 清單補充：
- 每個 SFX-ID 補一條「觸發驗證」測試（AUD-T-00N）
- 若有 VO，補一條「VO 播放完畢後 AudioBuffer 正確釋放（無殘留實例）」測試，通過條件為透過 Memory Profiler 或 DevTools Memory 面板確認播放後無殘留 AudioBuffer 實例

---

## 品質門（Quality Gate）

生成完 AUDIO.md 後，執行以下自我檢查：

| 檢查項 | 標準 |
|-------|------|
| BGM 覆蓋 | 每個 PRD 主場景有 BGM 對應 |
| SFX 覆蓋 | 每個 PRD P0 互動事件有 SFX-ID |
| 引擎設定代碼 | 代碼中無裸 placeholder，音量/頻道/路徑均已填具體值 |
| 效能預算 | §9 所有欄位填具體數值，無 `{{PLACEHOLDER}}` |
| 命名規範 | 所有 ID 符合 BGM-xxx / SFX-UI-xxx / SFX-GAME-xxx / VO-xxx 格式 |
| 測試清單 | §10 測試數 ≥ §3 SFX 數量 + 8 個基礎測試 |
| VO 覆蓋 | 若 PRD 含劇情/教學，§4 每條 VO 的觸發條件精確到事件名稱，無裸 {{TEXT}}/{{TRIGGER}}/{{LANG}} placeholder；無 VO 則明確標注「本專案無語音/旁白設計」 |

若任何檢查未通過，在 AUDIO.md 末尾附加警告區塊：
```markdown
> ⚠️ AUDIO 品質警告：[列出未通過的檢查項，說明原因]
```
