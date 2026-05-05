---
doc-type: AUDIO
target-path: docs/AUDIO.md
reviewer-roles:
  primary: "音效設計專家（Senior Audio Designer，10 年遊戲/互動音效設計，熟悉 BGM/SFX/VO 設計與情感目標）"
  primary-scope: "§1 設計目標完整性、§2 BGM 場景覆蓋、§3 SFX 事件覆蓋、§4 VO 清單、§5 觸發邏輯無歧義"
  secondary: "技術音效工程師（Technical Audio Engineer，精通 Cocos AudioEngine / Unity AudioMixer / Web Audio API / Howler.js）"
  secondary-scope: "§6 引擎設定代碼正確性、§7 資產規格與命名規範、§8 載入策略合理性、§9 效能預算達成可行性"
  tertiary: "QA 音效測試員（Audio QA，熟悉跨平台音效相容性驗證）"
  tertiary-scope: "§10 測試清單完整性、§5 互斥規則完備性、§1.3 平台限制正確性"
quality-bar: "專業音效工程師可直接依此文件完成全部音效實作與整合，不需再問任何技術決策問題。"
upstream-alignment:
  - field: 引擎版本與 API
    source: FRONTEND.md §2
    check: §6 代碼範例的 API 是否與 FRONTEND.md 確認的引擎版本一致
  - field: P0 互動事件覆蓋
    source: PRD.md User Stories
    check: §3 SFX 清單是否覆蓋 PRD 所有 P0 User Story 中的互動觸發事件
  - field: 目標平台
    source: BRD.md
    check: §1.3 是否為 BRD 每個目標平台都填寫了音效格式和頻道限制
  - field: BGM 場景對應
    source: PRD.md 功能流程
    check: §2 BGM 清單是否為每個主要 PRD 場景填寫了對應 BGM
  - field: VO 觸發事件
    source: PRD.md / 腳本文件
    check: §4 每條 VO 的觸發條件是否精確對應 PRD 或腳本文件中定義的事件名稱，無模糊描述或裸 placeholder
  - field: 載入策略對齊
    source: EDD.md §4 / FRONTEND.md §7
    check: §8 各類音效的載入時機與載入方式是否與 EDD.md §4 資源管理設計及 FRONTEND.md §7 資源管理策略一致
  - field: 目標平台 codec 與頻道上限
    source: PDD.md §2 §4
    check: §1.3 目標平台音效限制表中，各平台的 codec 格式與同時播放頻道上限是否與 PDD.md §2 目標平台及 §4 裝置規格所定義的限制一致
  - field: 音效時機與視覺動畫時序同步
    source: VDD.md
    check: §5.2 觸發條件矩陣中各音效的觸發時機（進入、事件、離開）是否與 VDD.md 定義的視覺動畫時序同步，確保音效與視覺特效在同一幀觸發
---

# AUDIO Review Items

本檔案定義 `docs/AUDIO.md` 的審查標準。由 `/reviewdoc AUDIO` 讀取並遵循。
審查角色：三角聯合審查（音效設計專家 + 技術音效工程師 + QA 音效測試員）
審查標準：「假設公司聘請一位 10 年以上音效工程師，以可直接完成音效實作為標準進行驗收。」

> **注意**：含 `.5` 後綴的 Layer（如 Layer 3.5、Layer 6.5）和 item（如 item 17.5）為後續輪次補充插入，不影響原有核心序號體系，引用時以完整帶後綴編號為準。

---

## Review Items

### Layer 0: Document Control（由音效設計專家主審）

#### [HIGH] 0 — Document Control 未填寫具體值
**Check**: Document Control 區塊的 VERSION、STATUS、AUTHOR、DATE、ENGINE 五個欄位是否均已填寫具體值，無裸 placeholder（如 `{{VERSION}}`、`{{AUTHOR}}` 等未替換的佔位符）？ENGINE 是否填入確切引擎名稱與版本（如「Cocos Creator 3.8.2」而非「{{ENGINE}}」）？
**Risk**: Document Control 含裸 placeholder 表示文件未完成初始化，後續審查無法確認版本與責任人，造成版本管理混亂。
**Fix**: 填入 VERSION（依專案版本）、STATUS（Draft/Review/Approved）、AUTHOR（負責人姓名）、DATE（今日日期，格式 YYYY-MM-DD）、ENGINE（確切引擎名稱與版本）。

---

### Layer 1: 設計目標完整性（由音效設計專家主審）

#### [CRITICAL] 1 — §1 設計目標含裸 Placeholder
**Check**: §1.1 情感目標、沉浸感策略、品牌音效識別是否有 `{{PLACEHOLDER}}` 未替換？§1.3 目標平台表是否覆蓋 BRD 所有目標平台？所有平台的格式和頻道數是否填入具體數值？
**Risk**: 音效工程師無法判斷音效風格，導致實作與設計預期嚴重偏差。
**Fix**: 依 IDEA/BRD 填入具體的情感風格描述（如「輕快卡通，以鋼片琴和木琴為主調，SFX 使用誇張的彈性音效」）；§1.3 逐平台填寫具體頻道數和格式。

#### [HIGH] 2 — §1.2 設計原則缺少引擎特定約束
**Check**: §1.2 設計原則是否包含針對本專案引擎的具體限制（如「Cocos Creator 最多 32 個 AudioSource 同時啟用」）？
**Risk**: 開發者過度使用音效頻道，導致運行時音效截斷。
**Fix**: 補充引擎特定的同時播放限制說明。

---

### Layer 2: BGM 清單完整性（由音效設計專家主審）

#### [CRITICAL] 3 — §2 BGM 清單未覆蓋主要場景
**Check**: 從 PRD.md 提取所有主要場景（大廳、戰鬥、勝利、失敗等）。§2 BGM 清單是否為每個 P0 場景填寫至少 1 條 BGM？是否有 BGM 記錄的檔案路徑為裸 placeholder？
**Risk**: 進入場景後無 BGM，嚴重影響遊戲/應用體驗。
**Fix**: 補充缺漏場景的 BGM 記錄；替換裸 placeholder 為符合 §7.1 命名規範的具體路徑。

#### [HIGH] 4 — §2.1 BGM 切換規則缺失或不完整
**Check**: §2.1 是否列出所有主要場景之間的切換路徑？淡入/淡出時間是否填具體毫秒數？
**Risk**: 場景切換時 BGM 突然停止或爆音。
**Fix**: 補充缺漏的切換路徑，填入具體時間值。

---

### Layer 3: SFX 清單完整性（由音效設計專家主審）

#### [CRITICAL] 5 — §3 SFX 未覆蓋 P0 互動事件
**Check**: 從 PRD.md 提取所有 P0 User Story 中涉及的互動動作（點擊、攻擊、收集、勝利等）。§3.1 + §3.2 合計是否為每個 P0 互動動作填寫對應 SFX-ID？
**Risk**: P0 功能缺少音效回饋，用戶操作感受差，QA 將阻擋上線。
**Fix**: 逐一比對 PRD P0 功能，補充缺漏的 SFX 記錄。

#### [HIGH] 6 — §3 SFX 最大同播數缺失
**Check**: §3.1、§3.2 和 §3.3 的「最大同播數」欄位是否全部填寫具體數字？是否有空白或 placeholder？§3.3 Ambient 環境音效的最大同播數是否 ≤ 2？
**Risk**: 高頻觸發時音效疊加超出引擎頻道上限，導致音效截斷或雜音；環境音效同時播放過多加劇頻道耗盡。
**Fix**: 所有 SFX 必須填入最大同播數（按鈕 = 1，攻擊命中 ≤ 3，爆炸 ≤ 2，§3.3 Ambient ≤ 2）。

#### [MEDIUM] 7 — §3 SFX 優先級分配不合理
**Check**: 是否有非核心 SFX 設定了 CRITICAL 優先級？是否有核心互動（攻擊命中、勝利）設定了 LOW 優先級？
**Risk**: 重要音效被低優先級音效搶佔頻道，核心體驗受損。
**Fix**: 依 §5.1 定義重新分配優先級。

---

### Layer 3.5: 語音／旁白清單完整性（由音效設計專家主審）

#### [HIGH] 3.5 — §4 語音／旁白清單缺失或含裸 Placeholder
**Check**: §4 是否明確聲明「本專案無語音/旁白設計」或提供完整的 VO 清單？若有 VO 清單：是否存在裸 `{{TEXT}}`、`{{TRIGGER}}`、`{{LANG}}` 等未替換的 placeholder（允許 `[TBD-腳本確認中]` 但須標注）？觸發條件是否精確到事件名稱（而非模糊描述）？多語言 VO 是否每種語言各有獨立行？優先級欄位是否填寫（CRITICAL / HIGH / MEDIUM）？
**Risk**: VO 記錄缺失導致旁白靜音；觸發條件模糊導致工程師實作偏差；多語言版本遺漏。
**Fix**: 補充缺漏的 VO 記錄，或明確標注「無 VO」；替換裸 placeholder 為實際文本或 `[TBD-腳本確認中]`；觸發條件精確至事件名；多語言各條獨立行；補充優先級欄位。

---

### Layer 4: 音效觸發邏輯（由音效設計專家主審）

#### [MEDIUM] 7.5 — §5.1 優先級數值與 §3 SFX 分配一致性
**Check**: §5.1 定義的優先級數值（CRITICAL=10、HIGH=7、MEDIUM=5、LOW=2）是否與 §3.1/§3.2/§3.3 中每條 SFX 的優先級欄位語義一致？例如：§3.1 中標注 MEDIUM 的 SFX，其實際搶佔行為是否符合 §5.1 的 MEDIUM 定義（數值 5，一般互動音效）？
**Risk**: 優先級定義與清單脫節，導致音效搶佔邏輯混亂——低優先級音效覆蓋高優先級 VO，或 CRITICAL 音效被 MEDIUM 事件錯誤打斷。
**Fix**: 核對 §5.1 定義的每個優先級數值，與 §3.1/§3.2/§3.3 全部 SFX 的優先級欄位逐一比對，確保命名與數值語義一致。

#### [CRITICAL] 8 — §5.2 觸發條件矩陣覆蓋不足
**Check**: §5.2 是否為所有主要遊戲狀態/場景（至少 3 個）填寫觸發條件矩陣？每個矩陣是否包含「進入」「主要事件」「離開」三個時機？
**Risk**: 音效觸發邏輯不完整，開發者需要猜測，導致實作與設計不一致。
**Fix**: 補充缺漏場景的觸發矩陣。

#### [HIGH] 9 — §5.3 音效互斥規則不完整
**Check**: §5.3 是否包含 BGM 唯一性、SFX 同 ID 打斷、VO 隊列 三條基礎規則？是否有針對本專案的特殊互斥規則（如「戰鬥 BGM 播放時靜音環境音」）？
**Risk**: 多音效同時播放超出引擎頻道，或 VO 衝突疊加。
**Fix**: 補充缺漏的互斥規則。

---

### Layer 5: 引擎設定正確性（由技術音效工程師主審）

#### [CRITICAL] 10 — §6 引擎設定代碼含裸 Placeholder 或 API 錯誤
**Check**: §6 展開的引擎設定代碼中是否有 `{{PLACEHOLDER}}`？代碼中的音量、頻道數、路徑是否都是具體值？代碼 API 是否與 FRONTEND.md 確認的引擎版本一致（如 Cocos 2.x 用 `cc.audioEngine`，3.x 用 `AudioSource` Component）？
**Risk**: 代碼直接複製後無法運行，工程師需要猜測 API。
**Fix**: 替換所有 placeholder 為具體值；確認 API 與引擎版本匹配。

#### [HIGH] 11 — §6.3 HTML5 缺少 Web Audio Context 解鎖代碼
**Check**（僅適用 HTML5 專案）：§6.3 是否包含 Web Audio Context 解鎖代碼（監聽首次用戶點擊後 resume AudioContext）？
**Risk**: iOS Safari / Chrome 要求用戶互動後才允許播放音頻，缺少解鎖代碼導致 iOS 上完全無聲。
**Fix**: 在 §6.3 補充標準的 `AudioContext.resume()` 解鎖代碼。

---

### Layer 6: 資產規格與命名（由技術音效工程師主審）

#### [HIGH] 12 — §7 資產命名不符規範
**Check**: §2/§3/§4 清單中的所有「檔案路徑」是否符合 §7.1 命名規範（前綴/模組/描述格式）？是否有大寫字母、空格、特殊字元（統一用 `_` 分隔）？
**Risk**: 檔案命名不一致，工程師和美術之間溝通成本高；跨平台路徑錯誤。
**Fix**: 統一使用小寫 + 底線，補充不符規範的命名。

#### [HIGH] 13 — §7.2 格式規格缺少 HTML5 WebM
**Check**（HTML5 專案）：§7.2 格式表是否包含 `.webm` 格式（Chrome 優先格式）？是否有 `.mp3` 備用（Safari/iOS 相容）？
**Risk**: 缺少 webm → Chrome 效能下降；缺少 mp3 備用 → iOS Safari 無法播放。
**Fix**: 補充 HTML5 音效的雙格式規格。

#### [MEDIUM] 14 — §7.3 目錄結構與 EDD 不一致
**Check**: §7.3 音效資產目錄（如 `assets/audio/`）是否與 EDD 或 FRONTEND.md 中定義的資產根目錄一致？
**Risk**: 美術資產放錯目錄，引擎讀取失敗。
**Fix**: 對齊 EDD/FRONTEND.md 的資產目錄定義。

---

### Layer 6.5: 音效載入策略合理性（由技術音效工程師主審）

#### [HIGH] 6.5 — §8 音效載入策略不合理或含空白欄位
**Check**: §8 是否有任何欄位（載入時機、載入方式、記憶體策略）為空白或含裸 placeholder？BGM 是否設定為串流或背景非同步載入（符合 FRONTEND.md 資源管理策略）？SFX P0 核心音效是否設定為啟動時預載常駐記憶體？VO 是否設定為按需下載並在播放完畢後釋放？載入策略是否與 EDD.md / FRONTEND.md §7 資源管理策略一致？
**Risk**: 策略不一致導致音效靜音（未預載就觸發）或 OOM（大型 BGM 常駐記憶體）；VO 按需下載但未釋放造成記憶體堆積。
**Fix**: 對照 EDD.md / FRONTEND.md 逐行修正 §8；BGM 首場景改為應用啟動後背景預載，其他場景改為進場前非同步預載；SFX P0 改為啟動時預載；VO 補充「播放完畢即釋放」策略；所有空白欄位補充具體策略描述。

---

### Layer 7: 效能預算（由技術音效工程師 + QA 主審）

#### [CRITICAL] 15 — §9 效能預算含裸 Placeholder
**Check**: §9 所有欄位（頻道數、CPU 占用、包體積、記憶體）是否都填寫了具體數值？是否有 `{{PLACEHOLDER}}` 未替換？
**Risk**: 沒有效能預算，工程師和 QA 無法判斷音效是否超出規格，效能問題在上線前無法被發現。
**Fix**: 依 §6 偵測到的引擎和 BRD 目標裝置，填入具體數值。

#### [HIGH] 16 — §9 未針對低階裝置定義限制
**Check**: §9 是否針對 BRD 最低目標裝置（如入門級 Android）提供了音效降級方案（如減少同時播放頻道、不預載大型 BGM）？
**Risk**: 低階裝置音效 OOM 或 CPU 超載。
**Fix**: 補充低階裝置的音效降級策略。

---

### Layer 8: 測試清單完整性（由 QA 主審）

#### [HIGH] 17 — §10 測試未覆蓋所有 SFX
**Check**: §10 測試數量是否 ≥ §3 SFX 數量 + 8 個基礎測試案例？是否每個 SFX-ID 都有對應的「觸發驗證」測試（驗證音效正確播放，無 404）？
**Risk**: SFX 資產缺失或命名錯誤在測試階段被忽略，上線後靜音。
**Fix**: 補充缺漏的 SFX 觸發驗證測試。

#### [HIGH] 17.5 — §10 缺少 VO 記憶體釋放測試
**Check**: 若 §4 含 VO 記錄，§10 是否包含至少 1 條「VO 播放完畢後記憶體正確釋放（無殘留 AudioBuffer）」的測試案例？
**Risk**: VO 播放後 AudioBuffer 未釋放，長期運行導致 OOM（記憶體不足崩潰）。
**Fix**: 補充 VO 記憶體釋放測試案例，驗證每條 VO 播放完畢後 AudioBuffer 已被正確回收（可透過 Memory Profiler 或 DevTools Memory 面板確認無殘留實例）。

#### [HIGH] 18 — §10 iOS 首次播放解鎖測試遭刪除
**Check**: §10 是否保留了 AUD-T-005 iOS 首次播放解鎖測試（gen agent 不得刪除此預置測試）？
**Risk**: iOS 特有的 Web Audio Context 鎖定機制未被測試覆蓋，上線後 iOS 用戶完全無聲，且此測試為必要預置，刪除後需人工補回。
**Fix**: 確認 AUD-T-005「iOS Safari 首次點擊後 BGM/SFX 正常播放」測試案例存在於 §10 清單中；若缺失，立即補充。


---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/AUDIO.md`，提取所有 `^## ` heading（含條件章節），共約 12 個
2. 讀取 `docs/AUDIO.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
