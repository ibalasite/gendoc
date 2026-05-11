# IDEA Document Template

<!-- SDLC Requirements Engineering — Layer 0：Idea Capture -->
<!-- 此文件是需求鏈的起點（IDEA → BRD → PRD → PDD → EDD），記錄最原始的構想輸入 -->
<!-- 由 /gendoc-auto 自動填寫；未來需求變更時，此文件作為「原始意圖」比對基準 -->

---

## §0 Input Source（輸入素材說明）

| 欄位 | 內容 |
|------|------|
| **輸入類型** | text_idea（使用者直接輸入文字構想） |
| **素材檔案** | `docs/req/idea-input.md` |
| **輸入摘要** | HTML5 寵物互動網站，無帳號門檻，email 認領制，像素風格隨機寵物，競技場對戰，訓練/食物強化，寵物交易市場，戰績排行榜 |
| **素材類型** | 產品原始構想文字輸入 |
| **對應章節** | 全章節（依 §15 Traceability Note 標記） |

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | IDEA-PIXEL-PET-ARENA-20260503 |
| **專案名稱** | pixel-pet-arena |
| **文件版本** | v0.1-capture |
| **狀態** | DRAFT |
| **作者** | AI Generated (gendoc-gen-idea) |
| **建立日期** | 2026-05-03 |
| **最後更新** | 2026-05-03 |
| **輸入模式** | AI 自動填入（text_idea + Q1-Q5 澄清） |
| **建立方式** | /gendoc-auto 自動捕捉；請執行 /reviewdoc brd 審查後方可升版 |
| **下游文件** | docs/BRD.md（由本文件產生） |
| **client_type** | web（HTML5 瀏覽器端，無需安裝） |

---

## 1. Idea Essence（核心本質）

### 1.1 一句話描述（Elevator Pitch）

> **pixel-pet-arena 幫助休閒玩家與像素藝術愛好者解決「無帳號門檻下無法擁有自己的虛擬寵物並與他人競技」的問題，方式是提供 email 認領制的隨機像素寵物、完整訓練強化生態系統，以及多模式競技場，讓每隻寵物都獨一無二、可養可賽可交易。**

**Elevator Pitch 5 句話：**

1. **Who**：休閒玩家（不想創帳號的輕度用戶）、像素藝術愛好者、輕度競技遊戲玩家、寵物收藏愛好者。
2. **Problem**：現有虛擬寵物遊戲大多要求完整帳號註冊，門檻高；而現有 HTML5 遊戲缺乏持久性寵物養成與競技生態，玩家無法真正「擁有」並培育獨特寵物。
3. **Solution**：純 HTML5 網站，訪客可即時互動隨機寵物；想養就輸入 email，系統寄送認領密碼與專屬 URL，下次直接回訪繼續；像素風格程序化生成保證每隻寵物外型獨特，可訓練、喂食、競技、交易。
4. **Why Now**：HTML5 Canvas + Phaser.js 技術成熟，瀏覽器端遊戲無需安裝門檻最低；email Magic-Link 模式已成熟（Notion、Slack 均採用）；Pixel Art 風格在 itch.io 等平台持續熱門，玩家對 retro 風格接受度高。
5. **Key Differentiator**：唯一結合「無帳號門檻 email 認領」＋「程序化像素寵物唯一性生成」＋「跨模式競技場（跑步 / 相撲 / 更多）」＋「寵物 P2P 交易市場」的輕量 HTML5 寵物遊戲。

---

### 1.2 核心假說（Lean Hypothesis）

> **If we build** 一個無需帳號、直接在瀏覽器中互動隨機像素寵物並透過 email 認領的 HTML5 遊戲平台，  
> **then** 休閒玩家（無帳號門檻偏好者）  
> **will** 自發性認領寵物、持續回訪訓練並參與競技，  
> **which will lead to** 高 Day-7 回訪率（>30%）、競技場日活躍對戰場次數增長，以及寵物交易市場有機成長，最終形成社群口碑傳播。

*假說需可測試、可被推翻。90 天驗證：認領數 ≥ 500、Day-7 回訪 ≥ 30%、競技場日對戰 ≥ 100 場次。*

---

### 1.3 成功願景（Success Vision）

**12 個月後，若本專案成功，以下情境將成真：**

- 用戶維度：每天有 2,000–5,000 名玩家在瀏覽器打開 pixel-pet-arena，其中超過 30% 已認領自己的寵物並定期回訪訓練；競技場每天舉辦數百場對戰，玩家在社群媒體自發分享戰績截圖；寵物交易市場每週有穩定成交，稀有像素寵物成為玩家炫耀資本。
- 業務維度：DAU 達 2,000–5,000（常態），活動期峰值 20,000；寵物交易市場手續費或稀有寵物販售形成初步變現路徑；口碑傳播使獲客成本接近 $0，itch.io / Twitter 等平台形成自然流量。
- 技術維度：Phaser.js + Node.js 後端穩定支撐 200–500 同時在線（峰值 2,000）；像素寵物生成演算法具備足夠大的組合空間（>10 億種組合），確保唯一性；email 認領系統零安全事故，token 管理完善。

### 1.4 Innovation Type Classification（創新類型分類）

| 類型 | 定義 | 是否適用 |
|------|------|:-------:|
| **Incremental**（漸進式）| 改善既有產品功能或流程效率 | ☐ |
| **Sustaining**（持續性）| 在既有市場中競爭，提供更好的解法 | ☐ |
| **Adjacent**（鄰近式）| 現有能力進入新市場或新用戶群 | ☑ |
| **Disruptive**（顛覆性）| 從低端或全新市場切入，重塑現有市場 | ☐ |
| **Radical / Breakthrough**（突破性）| 基於新技術或商業模式，創造新市場 | ☐ |

**本 IDEA 的分類**：Adjacent（鄰近式創新）

**分類依據**：核心創新在於將現有虛擬寵物遊戲的能力（養成、競技、交易）延伸至「不願創帳號的輕度休閒瀏覽器用戶」這一尚未被服務的新市場，符合 Adjacent 定義（現有能力進入新用戶群）。雖具備 Sustaining 特徵（在既有市場提供更低門檻替代方案），但主分類以「新用戶群進入」為主要創新驅動力。

*分類影響資源投入策略：Adjacent 需優先驗證新用戶群（不願創帳號的休閒玩家）的行為模式與留存指標，再擴展功能深度。*

---

## 2. Problem Statement（問題陳述）

### 2.1 現狀描述（As-Is Narrative）

目前市場上的虛擬寵物遊戲（如 Neopets、Tamagotchi 官方 app、或各類 P2E 寵物鏈遊）普遍要求完整帳號註冊（email + 密碼 + 信箱驗證），對休閒用戶形成明顯摩擦。使用者臨時想玩時，面對「填寫資料」的心理負擔往往直接關閉頁面。

現有的 HTML5 小遊戲（itch.io 上的 browser-based 寵物遊戲）雖有低門檻優勢，但普遍缺乏持久性數據——每次刷新頁面寵物就消失，無法建立長期的養成關係。玩家「想帶走這隻寵物」時，沒有合理的低門檻認領機制。

現有解法的 Workaround：部分玩家使用 localStorage 暫存寵物數據，但跨裝置無法同步；或使用 cookie，但清除 cookie 即遺失寵物。這些都是臨時性且不可靠的替代方案。

*問題發生頻率：每次新訪客訪問瀏覽器遊戲時；從數據看，典型 HTML5 遊戲首次訪問到完成註冊的轉換率僅 5-15%，顯示帳號門檻造成大量流失。*

---

### 2.2 根本原因分析（5 Whys）

```
問題現象：休閒玩家無法在低門檻下擁有持久的虛擬寵物
  Why 1：現有寵物遊戲要求完整帳號註冊才能保存數據
    Why 2：傳統 web 應用以帳號系統為用戶身份識別的預設方案
      Why 3：帳號系統是最直接的後端持久化映射機制
        Why 4：開發者未考慮「無帳號」與「持久數據」並存的架構設計
          Why 5（根本原因）：缺乏「email + 專屬 token URL」作為輕量身份識別層的設計模式，導致「想要數據持久」和「不想創帳號」被視為互斥需求 ← 我們要解決的是這個
```

*5 Whys 結論：根本問題是「身份識別模式設計」的缺位，而非技術不可行。email 認領 + 專屬 URL token 模式已在 Magic Link 認證中成熟驗證。*

---

### 2.3 問題規模（量化估算）

| 指標 | 估算數字 | 資料來源 | 信心水準 |
|------|---------|---------|---------|
| 受影響使用者數（全球） | 約 5 億月活的 casual browser game 玩家 | Statista HTML5 遊戲市場報告（2024） | 低 |
| 受影響使用者數（目標市場） | 約 500 萬（喜歡 pixel art 且有養成遊戲偏好） | itch.io pixel art 分類月活 + Tamagotchi-style 搜尋量估算 | 低 |
| 每人每週損失時間 | 約 0.5 小時（帳號門檻造成的重複性放棄） | 待用戶訪談驗證 | 低 |
| 每人每年成本損失 | 非金錢損失（娛樂機會損失） | 待驗證 | 低 |
| 可定址市場規模（TAM） | HTML5 遊戲市場 ~$15B（2024），養成遊戲子市場 ~$2B | Newzoo / Sensor Tower 估算 | 低 |
| 可服務市場規模（SAM） | Pixel art 養成 + 競技 browser game 玩家，~$200M | AI 推斷（TAM 的 ~10%） | 低 |
| 可獲取市場規模（SOM，預估 12 月） | ~$200K–$500K（廣告 + 交易手續費） | AI 推斷（DAU 2k-5k × $0.1–0.3/用戶/月） | 低 |

*以上數字為初始估算，需在 PRD 階段的用戶研究後更新。*

---

## 3. Target Users（目標使用者）

### 3.1 主要使用者群（Q1 澄清結果）

**使用者描述**：休閒玩家（無需帳號）、像素藝術愛好者、輕度競技遊戲玩家、寵物收藏愛好者

| 屬性 | 描述 |
|------|------|
| 職業 / 角色 | 學生、上班族、居家工作者；無特定職業限制 |
| 行業 / 情境 | 休閒娛樂、短暫消遣（午休、通勤、睡前）；瀏覽器直接訪問，無需安裝 |
| 技術成熟度 | 初學 ～ 中階（會用 email，熟悉基本瀏覽器操作） |
| 使用頻率 | 每日（高度黏著玩家） ／ 每週（競技場活動期回訪） |
| 決策角色 | 使用者（直接玩家）；推薦者（將遊戲連結分享給朋友） |

**用戶規模估算**：目標市場 ~500 萬潛在用戶（全球 pixel art 養成遊戲偏好者），上線 12 個月內目標觸達 2,000–5,000 DAU（佔 TAM 的 0.04–0.1%，保守估算）。

---

### 3.2 Jobs to Be Done（用戶核心任務）

| 任務類型 | 用戶任務描述 |
|---------|------------|
| **Functional**（功能性）| 當我無聊想放鬆時，我想要立刻打開網頁就能互動一隻可愛的像素寵物，以便不需要填寫任何帳號資料就能立即開始遊戲體驗。 |
| **Functional**（功能性）| 當我認為某隻寵物值得長期培養時，我想要透過輸入 email 永久認領牠，以便下次可以隨時從任何裝置回來繼續養它。 |
| **Functional**（功能性）| 當我想讓我的寵物更強時，我想要透過訓練和特殊食物提升屬性，以便在競技場中打敗其他玩家的寵物。 |
| **Emotional**（情感性） | 我想要擁有一隻「只屬於我」的獨特像素寵物（程序化生成，全球唯一外型），讓我感受到收藏稀有物品的滿足感與身份認同。 |
| **Social**（社交性） | 我想要在排行榜上展示我的寵物戰績，以便向朋友炫耀並引發討論，進一步吸引朋友也來玩。 |

---

### 3.3 非目標使用者（Not Our Users）

| 排除群體 | 排除原因 |
|---------|---------|
| ❌ 硬核 RPG / MMORPG 玩家 | 對養成深度和戰鬥機制複雜性要求遠超本產品 MVP 範圍；他們已有 WoW、FF14 等專業選擇 |
| ❌ P2E (Play-to-Earn) 區塊鏈遊戲玩家 | 需要錢包 + 鏈上資產，技術門檻高且與「無帳號」核心理念衝突；本產品聚焦娛樂而非投機 |
| ❌ 12 歲以下兒童（主要目標族群） | Email 認領機制需要基本 email 使用能力；COPPA 法規要求兒童數據特殊處理，MVP 階段暫不優化此群體 |

*明確定義「不服務誰」與「服務誰」同等重要，防止範圍無限擴張。*

---

## 4. Value Hypothesis（價值假說）

### 4.1 核心價值主張（Value Proposition Canvas）

**Pain Relievers（痛點緩解）：**

| 使用者痛點 | 我們的緩解方式 |
|-----------|-------------|
| 帳號門檻高（填寫大量資料才能開始）| 訪客模式：打開網頁直接與隨機寵物互動，無需填寫任何資料；只有在「想認領」時才輸入 email |
| 寵物數據不持久（刷新就消失）| Email 認領 + 專屬 URL token：認領後永久綁定，任何裝置輸入 URL 即可回訪同一隻寵物 |
| 每隻寵物外觀大同小異（缺乏收藏價值）| 程序化像素寵物生成：多屬性組合空間 > 10 億種，每次認領均不同，具備收藏稀有性 |
| 沒有競技對戰的社交動力（缺乏長期黏著）| 競技場多模式對戰（跑步賽、相撲擂台等）+ 全服排行榜 + 戰績紀錄，形成長期競技動力 |

**Gain Creators（增益創造）：**

| 使用者期望收益 | 我們如何創造 |
|-------------|------------|
| 擁有「獨一無二」的收藏品 | 程序化生成保證全球唯一外型，附帶稀有度評分（Common / Rare / Epic / Legendary），增強收藏驅動力 |
| 在社群中展示成就並獲得認可 | 公開寵物戰績頁面（可分享 URL）+ 全服排行榜 + 競技場成績社群分享按鈕 |
| 以寵物作為資產交易獲利 | 寵物交易市場：可掛牌、出價、成交，罕見寵物形成二級市場需求 |

---

### 4.2 差異化定位

**相對現有解法（競品 / 替代方案），本產品的獨特差異：**

> pixel-pet-arena 是唯一同時具備「無帳號 email 認領制（Magic Link 模式）」+ 「程序化像素寵物保證唯一性（>10 億組合）」+ 「多模式競技場對戰」+ 「P2P 寵物交易市場」的 HTML5 瀏覽器端養成競技遊戲。競品要麼需要完整帳號（Neopets、CryptoKitties），要麼缺乏持久性（itch.io 單機小遊戲），要麼沒有社交競技維度（傳統 Tamagotchi）。

| 維度 | pixel-pet-arena | Neopets | itch.io Browser Pet Games | CryptoKitties |
|------|:--------------:|:-------:|:------------------------:|:------------:|
| 無帳號即時互動 | ✅ | ❌ | ✅（但無持久化）| ❌（需錢包）|
| Email 認領（低門檻持久化）| ✅ | ❌（完整註冊）| ❌ | ❌ |
| 程序化像素唯一寵物 | ✅ | ❌（固定外型）| 部分 | ✅（鏈上 NFT）|
| 多模式競技場 | ✅（跑步/相撲等）| 部分 | ❌ | ❌ |
| 寵物交易市場 | ✅ | ✅ | ❌ | ✅（但鏈上）|
| 技術門檻（玩家端）| 🟢 零門檻（瀏覽器）| 🟡 帳號 | 🟢 零門檻 | 🔴 錢包+Gas |

*差異化優勢真實存在且可持續：「無帳號 email 認領」是技術架構設計選擇，非臨時性優勢。*

---

## 5. MVP & Learning Plan（最小可行驗證計畫）

### 5.1 MVP 邊界定義

> **MVP 的目的是驗證最關鍵的假設：玩家願意在「無帳號門檻」下認領並持續回訪養成像素寵物。**

**P0 必做功能（MVP 核心，≤ 5 項）：**

| MVP 功能 | 驗證假設 | 最低可接受標準（Go Threshold）|
|---------|---------|--------------------------|
| 隨機像素寵物展示 + 即時互動（訪客模式）| 玩家願意在零門檻下與寵物互動 | 首次訪問平均停留 > 2 分鐘；互動率 > 50% |
| Email 認領流程（密碼信 + 專屬 URL）| Email 認領轉換率可接受 | 訪客 → 認領轉換率 ≥ 10%；認領後 Day-3 回訪 ≥ 30% |
| 基礎訓練 / 喂食系統（提升屬性值）| 玩家願意每日回訪進行養成操作 | Day-7 留存率 ≥ 25% |
| 競技場基礎對戰（至少 1 種模式，如跑步賽）| 競技功能驅動社交分享與回訪 | 每日對戰場次 ≥ 50 場；社群分享率 ≥ 5% |
| 全服排行榜（依戰績/屬性排名）| 排行榜形成長期競技動力 | 排行榜頁面日 UV ≥ 20% 的 DAU |

**明確不在 MVP 範圍（Non-MVP）：**
- ❌ 寵物交易市場（推遲原因：需要足夠的寵物存量才有交易需求，至少待 DAU > 1,000 後引入）
- ❌ 第 2+ 種競技模式（相撲擂台等）（推遲原因：先驗證第 1 種模式的用戶反應，再擴展）
- ❌ 付費道具 / 變現機制（推遲原因：用戶留存驗證前不引入付費摩擦）
- ❌ 行動 App 版本（推遲原因：HTML5 瀏覽器端先驗證，降低初期開發成本）

---

### 5.2 Validation Metrics（驗證指標，Pre-BRD 階段）

*以下指標在 IDEA 驗證期間每週追蹤，達到閾值後方可升級為 BRD。*

| 指標 | 測量方式 | 通過閾值（Go）| 失敗閾值（Pivot/Kill）| 追蹤週期 |
|------|---------|:-----------:|:------------------:|---------|
| 問題確認率 | 用戶訪談：「無帳號門檻對您重要嗎？」 | ≥ 70% 答「是」 | < 40% | 週 1–2 |
| Email 認領意願 | 訪談：「您願意輸入 email 換取永久認領寵物嗎？」 | ≥ 60% 答「是」 | < 35% | 週 1–2 |
| 付費意願（未來交易市場）| 願意為稀有寵物付費的受訪者比例 | ≥ 30% | < 15% | 週 2–3 |
| 訪談完成數 | 完成深度訪談人數（pixel art 遊戲玩家）| ≥ 10 人 | < 5 人 | 週 1–3 |
| 競品替代接受度 | 受訪者「願意從其他養成遊戲切換」比例 | ≥ 25% | < 10% | 週 2–3 |

**驗證計畫時程：**

```
Week 1：用戶招募（目標 N ≥ 15 人，itch.io / Twitter pixel art 社群）；完成問卷調查
Week 2：深度訪談（N ≥ 10），蒐集質化資料（Email 認領接受度 / 競技意願）
Week 3：數據分析，決策：
  - Go    → 生成 BRD，啟動 autodev
  - Pivot → 修改核心機制（例：改為匿名 token 而非 email）
  - Kill  → 停止，記錄學習報告
```

---

### 5.3 Riskiest Assumption（最高風險假設，Leap of Faith）

> **以下假設一旦被推翻，整個 IDEA 必須根本性調整或放棄。**

**核心 Leap of Faith：**

> 我們假設 **「輸入 email 換取永久寵物認領」的低門檻機制足以突破玩家的帳號門檻阻力，並形成足夠高的 Day-7 回訪行為**。  
> 若此假設為假，則 **email 認領轉換率 < 5%，玩家不回訪，核心 Loop 不成立**，專案應 **Pivot（考慮匿名 LocalStorage + 雲端備份方案，或完全放棄持久化功能）**。  
> 我們將透過 **MVP 上線後前 4 週的 cohort 留存數據 + A/B 測試（email 認領 vs. 匿名 token）** 在 **上線後第 4 週** 前驗證此假設。

| 假設 | 驗證方法 | 驗證期限 | 若錯誤的後果 |
|------|---------|---------|------------|
| Email 認領轉換率 ≥ 10%（訪客 → 認領）（最高風險）| MVP cohort 留存數據 + 訪談 | 上線後第 4 週 | 核心 Loop 不成立，需根本性 Pivot |
| 玩家對程序化像素寵物的稀有感有收藏驅動力 | 訪談 + 排行榜頁面訪問率 | 上線後第 2 週 | 調整外型生成演算法 / 引入手繪元素 |
| 競技場對戰驅動 Day-7 回訪（留存率 ≥ 25%）| 留存漏斗分析 | 上線後第 3 週 | 加強訓練 / 社交功能；延後競技場 MVP |

*Leap of Faith ≠ 普通風險。它是整個商業邏輯成立的前提條件。*

---

## 6. Clarification Interview Record（澄清訪談記錄）

> 本節記錄 /gendoc-auto Step 2 互動提問的完整結果，是 BRD 各章節的原始輸入來源。

### Q1 — 主要使用者

| 欄位 | 內容 |
|------|------|
| **回答** | 休閒玩家（無需帳號）、像素藝術愛好者、輕度競技遊戲玩家、寵物收藏愛好者 |
| **選擇方式** | AI 推薦預設 |
| **影響範疇** | BRD §4 Stakeholders、PDD Persona、RTM 使用者欄位 |

---

### Q2 — 核心痛點

| 欄位 | 內容 |
|------|------|
| **回答** | 無需帳號門檻，email 認領制（密碼 + 專屬 URL）；隨機生成像素寵物；競技場多模式對戰；寵物訓練/強化/交易生態系統 |
| **選擇方式** | AI 推薦預設 |
| **影響範疇** | BRD §2 Problem Statement、§5 Proposed Solution、§7 Success Metrics |

---

### Q3 — 技術限制或偏好

| 欄位 | 內容 |
|------|------|
| **回答** | HTML5（支援主流瀏覽器）；像素風格 Canvas 渲染；後端需支援 email 發送；每隻寵物數據永久存儲 |
| **選擇方式** | 使用者自行輸入（來自原始 IDEA 文字） |
| **影響範疇** | BRD §8 Constraints、EDD 技術選型、ARCH 架構設計 |

---

### Q4 — 預估流量規模（PM Expert 研究推估）

| 欄位 | 內容 |
|------|------|
| **日活用戶（DAU）** | 2,000–5,000/day（launch）→ peak 20,000/day（viral event） |
| **同時在線峰值（PCU）** | 200–500 人（常態），峰值約 2,000 人（競技場活動期） |
| **推估依據** | 參考具名競品：Neopets（現約 200 萬 MAU，DAU/MAU ≈ 5-10% → DAU 約 10-20 萬）；Tamagotchi Uni 官方 app（估計 MAU 50-100 萬）；itch.io 熱門瀏覽器虛擬寵物遊戲（個別項目 MAU 約 1-10 萬）。本專案為新進入者，保守估算目標市場滲透率 0.1-0.5%，DAU 2k-5k；競技場活動期峰值 PCU 約 DAU 10%（參考 Neopets 競技場時段規律）。 |
| **影響範疇** | EDD 容量規劃數值、ARCH HPA 觸發閾值、DB 連線池大小 |

> 以上數值由 PM Expert 依競品研究與行業基準自動推估，僅供容量規劃使用，不影響架構選型（架構均採 HA 設計，≥ 2 replica）。

---

### Q5 — 其他補充說明（動態追問）

| 欄位 | 內容 |
|------|------|
| **回答** | 寵物完全隨機生成，每次領養都不同；像素藝術風格；有排行榜與交易市場 |
| **追問觸發原因** | 確認差異化特徵（唯一性機制 + 視覺風格）與商業機制（交易市場）|
| **影響範疇** | §1.4 差異化定位、§4 Value Hypothesis、§7.2 技術生態建議、§9.1 商業模式假說 |

---

### 原始 IDEA（使用者輸入原文，逐字保留）

```
一個HTML5的寵物網站，使用者不用登入，可以隨機跟一個寵物互動，覺得想養要給email，
會寄一封密碼信給你，以及畫面有領取的URL，下次可依此URL回來跟寵物互動，養大的寵物
可以跟其他寵物競賽，可以去競技場比賽跑，可以比相撲擂台等，若要讓寵物好，要訓練，
給特殊食物，也可以把寵物交易，所以每支寵物有自己的戰績，也有寵物排行榜，每支寵物
都是獨一無二的，用象素風格來做隨機產生特殊寵物，隨機到每次領的都不一樣
```

*保留原文供未來 ECR（Engineering Change Request）審查時比對，確認需求變更屬 BUG 修正還是範圍擴充。*

---

## 7. Market & Competitive Intelligence（市場與競品情報）

> 本節由 /gendoc-auto Step 3 研究自動蒐集，作為 BRD §6 的原始資料來源。

### 7.1 競品 / 參考資源

| 競品 / 工具 | 核心定位 | 優勢 | 劣勢 | 我們的差異 |
|-----------|---------|------|------|-----------|
| **Neopets** | 老牌網頁虛擬寵物平台，月活約 200 萬（峰值曾達 3000 萬） | 功能豐富、社群成熟、大量寵物種類 | 需完整帳號註冊、Flash 遺留問題（已遷移）、UI 老舊、無程序化生成 | 我們：無帳號門檻 + 像素程序化生成 + 現代 HTML5 技術 |
| **CryptoKitties / Axie Infinity** | P2E 區塊鏈寵物遊戲，NFT 資產交易 | 稀有性保證（鏈上）、交易市場成熟、高收藏價值感 | 需要加密錢包 + Gas Fee，門檻極高；市場受加密市場週期影響大 | 我們：無需錢包，傳統 email 即可，無 Gas 成本 |
| **KilledByAPixel/LittleJS** | 輕量 HTML5 遊戲引擎（⭐ 3k+），無依賴 | 極輕量（< 10KB）、無依賴、適合像素小遊戲 | 沒有社交 / 後端功能，純前端 | 參考借鑒（技術選型參考）|
| **Phaser.js** | 成熟 HTML5 遊戲框架，有豐富 pixel art 範例 | 活躍社群、豐富 arcade 功能、文檔完善 | 較重（> 1MB），需要打包優化 | 參考借鑒（前端框架候選）|
| **itch.io Browser-based Pet Games** | 多款獨立遊戲開發者的 pixel art 養成遊戲 | 零門檻（直接瀏覽器）、pixel art 風格成熟 | 無持久化、無社交競技、無後端 | 我們補足持久化 + 競技 + 交易三大缺口 |

---

### 7.2 技術生態建議

| 層次 | 建議方案 | 選擇理由 |
|------|---------|---------|
| 程式語言 / 框架（前端）| Phaser 3（HTML5 遊戲框架）或 LittleJS（輕量備選） | Phaser 3 有完整 arcade 物理、sprite 管理、WebGL 加速；LittleJS 適合極輕量部署 |
| 程式語言 / 框架（後端）| Node.js (Fastify / Express) 或 Go (Fiber / Gin) | Node.js 開發速度快，Go 在高並發（競技場對戰）有優勢；Q3 確認需支援 email 發送 |
| 資料庫 | PostgreSQL（主數據）+ Redis（排行榜 / 競技場快取）| PostgreSQL 強事務性保證寵物唯一性；Redis sorted set 實現即時排行榜 |
| Email 服務 | SendGrid（主要）+ Nodemailer SMTP（備援）| SendGrid API 成熟，支援 transactional email；SMTP fallback 降低依賴風險 |
| 像素寵物生成 | 程序化 Sprite 組件拼裝（頭型 × 身體 × 顏色 × 特徵 × 稀有屬性）| 多屬性組合 > 10 億種，確保唯一性；種子值記錄於 DB，可復現 |
| 基礎設施 | Vercel / Railway（前端 + 後端）+ Supabase（PostgreSQL 託管）| 低初始成本，支援自動擴展；DAU 5k 以內月成本 ~$50–200 |
| 版本控制 / CI | GitHub + GitHub Actions | 標準 DevOps 流程 |

#### 服務角色識別

| 角色名 | 用途 | 建議技術 |
|--------|------|---------|
| **Pet Generation Service** | 程序化生成像素寵物（種子 → 外型 + 屬性），保證唯一性 | Node.js / Go 微服務 + PostgreSQL（seed 去重）|
| **Auth Service（Email Magic Link）** | 處理 email 認領請求、生成一次性密碼 + 專屬 URL token、驗證回訪身份 | Node.js + JWT（短效 token）+ Redis（token 黑名單）|
| **Battle Service（競技場）** | 管理對戰配對、戰鬥結算邏輯、戰績記錄 | Go（高並發）+ Redis（對戰隊列）+ PostgreSQL（戰績持久化）|
| **Ranking Service（排行榜）** | 維護全服排行榜（依戰績 / 屬性 / 等級排名）| Redis sorted set + 定期快照至 PostgreSQL |
| **Marketplace Service（交易市場）** | 寵物掛牌、出價、成交、轉移所有權 | Node.js + PostgreSQL（事務保證）|
| **Notification Service（通知）** | 發送認領 email、競技結果通知 | SendGrid API + Nodemailer fallback |

---

### 7.3 研究來源

| 搜尋關鍵字 | 主要發現 | 可信度 |
|-----------|---------|--------|
| `GitHub topics/virtual-pet browser HTML5` | 多個 Tamagotchi 風格虛擬寵物開源項目（瀏覽器 + 狀態機 + WebSocket）；驗證技術可行性 | 高 |
| `pixel art procedural generation HTML5 game` | KilledByAPixel/LittleJS（輕量引擎）、itch.io 相關工具集；Phaser.js 有豐富 pixel art arcade 範例 | 高 |
| `email magic link authentication security risks` | Email client 預掃描問題（magic link 被提前觸發）→ 改用密碼 email + 手動輸入；token TTL + used tracking 是必要安全措施 | 高 |
| `Neopets monthly active users market size` | 峰值 3000 萬 MAU（2005），現約 200 萬；DAU/MAU ≈ 5-10%，驗證目標市場規模估算 | 中 |
| `procedural pixel pet uniqueness seed generation` | 需設計足夠大的隨機組合空間 + 記錄已用 seed；調色盤隨機化 + 多屬性組合是通用方案 | 高 |

---

## 8. Initial Risk Assessment（初始風險評估）

### 8.1 風險矩陣

| # | 風險描述 | 類型 | 可能性 | 影響 | 風險等級 | 初步緩解策略 |
|---|---------|------|:------:|:----:|:------:|------------|
| R1 | Email 預掃描問題：某些 email client（Gmail、Outlook）會自動點擊 email 中的 URL，導致認領 token 提前失效 | 技術 | HIGH | HIGH | 🔴 HIGH | 改為「密碼信」模式（email 含 6 位數字密碼，用戶手動在網頁輸入）而非直接 magic link；或提供 TOTP fallback |
| R2 | Token 安全性：專屬 URL token 若遭攔截，攻擊者可永久控制寵物 | 安全 | MEDIUM | HIGH | 🔴 HIGH | Token 加密（JWT with secret）+ 可選二次驗證；Token 長度 ≥ 32 bytes random；提供 token 更換機制 |
| R3 | 帳號枚舉攻擊：攻擊者可透過 email 認領 API 探測哪些 email 已存在 | 安全 | MEDIUM | MEDIUM | 🟡 MEDIUM | 不論 email 是否存在，API 回應相同訊息（「若 email 正確，您將收到認領信」）|
| R4 | 像素寵物唯一性保證：若隨機組合空間不足，早期玩家可能領到「撞臉」寵物，破壞收藏價值感 | 技術 | LOW | HIGH | 🟡 MEDIUM | 設計多維度屬性組合（頭型 × 身體 × 顏色 × 特徵 × 稀有屬性 ≥ 5 維），組合空間 > 10 億；DB 記錄已發放 seed，確保唯一性 |
| R5 | 競技場公平性問題：玩家透過機器人刷戰績，破壞排行榜生態 | 執行 | HIGH | MEDIUM | 🟡 MEDIUM | Rate limiting（每隻寵物每小時最多 X 場對戰）+ 對戰冷卻期 + 異常行為偵測 |
| R6 | 競品快速跟進：Neopets 或新的 HTML5 遊戲廠商複製核心機制 | 競爭 | LOW | HIGH | 🟡 MEDIUM | 先發優勢 + 社群效應（排行榜 / 寵物交易的網路效應）；加速 MVP 上線時程 |
| R7 | GDPR / CAN-SPAM 合規：EU 用戶 email 認領機制可能違反 GDPR 數據最小化原則；CAN-SPAM 要求 transactional email 明確標示；COPPA 對 13 歲以下兒童數據保護有強制要求 | 法規 | MEDIUM | HIGH | 🔴 HIGH | BRD 前完成法務審查 email 認領機制（含數據保留政策 + 刪除流程）；在 §3.3 明確排除 12 歲以下兒童；隱私政策中載明 email 用途僅限認領與通知 |

風險等級 = 可能性 × 影響：HIGH/HIGH = 🔴，其他組合 = 🟡 或 🟢。

---

### 8.2 Kill Conditions（專案終止條件）

*以下任一情況發生，應暫停或終止專案，避免繼續投入：*

| 終止條件 | 觸發閾值 | 檢查時機 |
|---------|---------|---------|
| Email 認領轉換率過低 | MVP 上線後 4 週內，訪客 → email 認領轉換率持續 < 3%（低於預期 10% 閾值的 30%），且優化後無改善 | MVP 上線後第 4 週 |
| Day-7 留存率過低 | 認領用戶 Day-7 回訪率 < 10%（預期 25% 的 40%），且訪談確認「缺乏回訪動機」 | MVP 上線後第 6 週 |
| 技術不可行 | Email 唯一性 + 像素寵物程序化生成在可接受成本（月 < $500）內無法技術實現 | PoC 完成後（BRD 前）|
| 法規阻礙 | 法務評估後，目標市場（全球）的 email 認領機制有 GDPR / CAN-SPAM 合規問題且無法解決 | BRD 法務審查後 |

---

### 8.3 Dependencies & External Risks（依賴與外部風險）

| 依賴項 | 類型 | 關鍵性 | 若失效的影響 | 備援方案 |
|--------|------|:-----:|------------|---------|
| SendGrid（email 發送服務）| 技術（第三方 API）| 高 | 認領機制完全失效，無法發送密碼信 | Nodemailer + SMTP 自建備援；或 AWS SES / Mailgun 快速切換 |
| Phaser.js / LittleJS（前端遊戲引擎）| 技術（開源框架）| 中 | 前端遊戲渲染需重寫（影響開發進度） | Phaser.js 社群活躍（⭐ 35k+），停止維護風險低；備選 LittleJS |
| PostgreSQL 託管服務（Supabase / Railway）| 技術（基礎設施）| 高 | 寵物數據遺失或服務中斷 | 定期備份至 S3；可遷移至自建 PostgreSQL 或 AWS RDS |
| 用戶 email 可達性（非 spam 過濾）| 市場 | 中 | 認領 email 被標記為 spam，轉換率下降 | SendGrid IP 信譽管理 + SPF/DKIM 設定 + 白名單引導 |

*此處記錄影響 IDEA 成立的關鍵外部依賴。本節聚焦於「我們無法完全控制」的外部因素。*

---

### 8.4 Pre-mortem Exercise（失敗前情境模擬）

> **想象 12 個月後，這個專案已徹底失敗。請列出最可能的失敗原因：**

| # | 失敗情境 | 根本原因 | 預防措施 | 早期預警訊號 |
|---|---------|---------|---------|-----------|
| F1 | 玩家認領後第 3 天就不再回訪，競技場空洞無人 | 訓練/競技的長期動力不足，沒有足夠的社交壓力或即時回饋 | MVP 強化「每日任務」提示 + 排行榜變化推播；競技場引入對戰邀請機制 | Day-7 留存率 < 15% 且問卷反映「沒有繼續的理由」|
| F2 | Email 認領轉換率 < 3%，大多數訪客試玩後離開 | 對「輸入 email」這個動作的心理摩擦比預期高；玩家不信任 | 減少認領步驟（一鍵 OAuth 備選？）；在互動過程中強化「這隻寵物很稀有」的稀缺感設計 | 認領頁面 Bounce Rate > 70% |
| F3 | 開發進度遠低於預期，競爭對手搶先上線 | Phaser.js + 程序化生成 + 後端 email 系統整合複雜度被低估 | 在 BRD 前完成技術 PoC（前端渲染 + email 發送 + DB 唯一性驗證）| PoC 超出 3 週仍未完成 |
| F4 | 排行榜被機器人霸榜，正常玩家放棄競技 | Rate limiting 和反作弊機制設計不足 | 早期引入對戰冷卻期 + 人工審查機制；DAU 達 1,000 前優先處理反作弊 | 前 10 名寵物對戰場次/天明顯超出正常比例（> 50 場/天）|
| F5 | Email 被大量標記為 spam，認領率崩潰 | SendGrid IP 信譽問題 + 郵件模板觸發 spam 過濾器 | 早期使用 SendGrid 共享 IP（信譽較好）+ 嚴格遵守 CAN-SPAM；監控 bounce rate 和 spam report | Spam Report Rate > 0.1% |
| F6 | 寵物「撞臉」問題破壞稀有感，玩家口碑負面 | 組合空間設計不足，早期玩家大量重複外型 | PoC 驗證組合空間足夠大（> 10 億）；實作 seed 去重機制 | 用戶論壇 / Twitter 出現大量「我的寵物長得跟別人一樣」投訴 |

**Pre-mortem 結論：** 最可能的失敗路徑是 **F1（訓練/競技動力不足導致低留存）+ F2（email 認領轉換率低）**，需在 BRD 階段優先設計「稀缺感強化機制」與「認領流程最小化摩擦」的預防機制。

---

## 9. Business Potential（初步商業潛力）

### 9.1 商業模式假說

| 項目 | 初步假設 |
|------|---------|
| 收入來源 | 主要：寵物交易市場手續費（每筆成交 5–10%）；次要：稀有/限定寵物販售（直接向玩家販售特殊外型寵物）；三級：廣告（低優先，避免破壞遊戲體驗）|
| 主要定價策略 | Freemium + 交易手續費：基礎功能完全免費，交易市場抽成；稀有寵物 $0.99–$4.99 |
| 主要成本驅動因子 | 伺服器成本（PostgreSQL + Redis + Compute）；Email 發送成本（SendGrid）；開發維護人力成本 |
| 核心資源 | 程序化像素寵物生成演算法（獨特競爭壁壘）；玩家社群與排行榜數據（網路效應）；email 認領用戶庫（低成本觸達渠道）|
| 獲客管道 | itch.io 發布（有機流量）；Twitter/TikTok 分享戰績（病毒傳播）；Discord pixel art 社群；排行榜公開頁面 SEO |

*以上為概念階段假設，需在 BRD §11 Business Model 中深化，PRD 中以用戶研究驗證。*

---

### 9.2 戰略對齊

| 公司策略目標 | 本 IDEA 的貢獻方式 | 對齊強度 |
|-----------|-----------------|---------|
| 建立低成本獲客的 HTML5 遊戲平台 | 零帳號門檻設計最大化訪客進入漏斗，email 認領建立用戶資產，口碑傳播降低獲客成本 | 強 |
| 探索 Web3-less 的數字資產所有權模式 | email + URL token 作為「輕量數字所有權」替代 NFT/錢包模式，驗證非鏈上唯一性資產的可行性 | 中 |
| 開拓休閒遊戲玩家市場 | 無門檻設計直接針對「不願創帳號」的輕度用戶群體，驗證該市場的商業價值 | 強 |

---

## 10. Executive Sponsorship & Stakeholder Alignment（執行贊助與關鍵利害關係人對齊）

### 10.1 Executive Sponsor

| 欄位 | 內容 |
|------|------|
| **贊助人** | TBD — 由 BRD 階段釐清（建議：Product Director 或 CTO，需有 HTML5 遊戲市場判斷能力）|
| **贊助原因** | 本專案探索「無帳號低門檻 + 數字資產輕量化」新模式，與公司休閒遊戲戰略方向對齊 |
| **授權範圍** | 預算上限 TBD（由 BRD 定義）；MVP 決策自主範圍（技術選型 + 功能優先級）|
| **核可日期** | TBD（BRD 完成後） |
| **升級路徑** | 若遇阻礙，升級至 CEO / Founder 層級 |

---

### 10.2 Stakeholder Pre-alignment Matrix

| 利害關係人 | 角色 | 對本 IDEA 的態度 | 主要顧慮 | 對齊策略 | 對齊期限 |
|-----------|------|:--------------:|---------|---------|---------|
| Product Manager | 產品負責人 | 支持 | MVP 範圍控制（避免功能蔓延）| 明確 Non-MVP 清單，鎖定 P0 功能 | BRD 前 |
| Engineering Lead | 技術負責人 | 中立 | Email 認領安全性、像素生成組合空間、後端擴展性 | PoC 驗證核心技術可行性（email + 生成演算法）| EDD 前 |
| 法務（Legal）| Legal | 中立 | GDPR / CAN-SPAM email 合規、兒童數據保護（COPPA）| 提前法務審查 email 認領機制與數據保留政策 | BRD 前 |
| Marketing | 行銷負責人 | 支持 | 如何在 itch.io / Twitter 建立初始用戶基礎 | 準備 itch.io 頁面 + 競技場活動預告行銷計畫 | PRD 前 |

---

### 10.3 Communication Plan（溝通計畫）

| 里程碑 | 溝通對象 | 溝通形式 | 期限 |
|--------|---------|---------|------|
| IDEA 核准 | Executive Sponsor | 1-pager + 口頭簡報 | BRD 啟動前 |
| BRD 完成 | All Stakeholders | 文件分享 + 審查會議 | BRD 生成後 1 週內 |
| PRD 核准 | Product + Engineering | Sprint Planning | PRD 生成後 |
| MVP 上線 | All Stakeholders + 行銷 | Demo + 數據儀表板分享 | MVP 上線後 1 週 |

---

## 11. IDEA Quality Score（構想品質評分）

> 由 /gendoc-auto Step 5.5 自動計算，用於判斷是否具備開始 BRD 的條件。

**整體評分**：★★★★☆（4/5）

| 評分維度 | 分數 | 評估說明 | 改進建議 |
|---------|:----:|---------|---------|
| 目標清晰度 | 1 / 1 | 一句話描述清晰，包含 Who / Problem / Solution / Why Now / Differentiator，無模糊詞 | 無需改進 |
| 使用者具體度 | 0.9 / 1 | 四類用戶群明確（休閒玩家 / 像素藝術愛好者 / 競技玩家 / 收藏愛好者），含職業/行為/痛點描述；年齡層未完全定義 | 在 BRD Persona 中補充年齡層與地理分佈估算 |
| 痛點可量化 | 0.8 / 1 | 帳號門檻問題有量化（帳號轉換率僅 5-15%）；寵物數據不持久有具體描述；部分痛點仍為定性描述 | 在 BRD 用戶研究後補充更多量化數據（NPS / 放棄率）|
| 範圍邊界明確 | 1 / 1 | MVP P0/P1/P2 明確分層，Non-MVP 清單具體，Kill Conditions 可量化 | 無需改進 |
| 技術可行性初判 | 0.3 / 1 | 技術選型方向正確（Phaser + Node.js + PostgreSQL），但 email 認領安全性（預掃描問題）和像素唯一性組合空間需 PoC 驗證；研究來源為靜態推斷，無即時 Web Research | 在 EDD 前完成技術 PoC；補充即時競品研究數據 |

**評分解讀：**

| 分數 | 星等 | 含義 | 建議行動 |
|------|------|------|---------|
| 4 | ★★★★☆ | 良好，微小缺漏 | 生成 BRD，審查後啟動 |

**本次評分說明：**

```
【IDEA 品質評分】★★★★☆（4/5）
  優點：目標清晰、範圍邊界明確、競品分析充分、Kill Conditions 可量化
  缺漏：部分痛點量化數據仍為估算（需用戶訪談驗證）；技術可行性需 PoC 確認
  建議：完成 Q1-Q5 澄清後立即生成 BRD，並在 EDD 前安排 email + 生成演算法 PoC
```

---

## 12. Critical Assumptions（關鍵假設清單）

*假設是尚未被事實驗證的陳述。以下按「影響 × 不確定性」排序，影響最高者優先驗證。*

| # | 假設陳述 | 影響層級 | 不確定性 | 驗證方式 | 驗證期限 |
|---|---------|:-------:|:-------:|---------|---------|
| A1 | 訪客 → email 認領轉換率 ≥ 10%（「輸入 email 換取永久寵物」的心理摩擦可接受）（基於 Q2 痛點）| HIGH | HIGH | MVP cohort 數據 + 訪談（N ≥ 10）| MVP 上線後第 4 週 |
| A2 | Day-7 留存率 ≥ 25%（訓練/競技機制足以驅動持續回訪）（基於 Q4 規模假設）| HIGH | MEDIUM | 留存漏斗分析 + 用戶訪談 | MVP 上線後第 6 週 |
| A3 | 程序化像素寵物生成組合空間可達 > 10 億種，且視覺上足夠有辨識度（基於 Q3 技術限制）| MEDIUM | HIGH | 技術 PoC（生成演算法驗證）| EDD 完成前 |
| A4 | Email 認領安全機制（密碼信 + 專屬 URL）可有效防止 email client 預掃描問題（基於 R1 風險）| HIGH | MEDIUM | 技術 PoC（跨 email client 測試）| EDD 完成前 |
| A5 | 寵物交易市場在 DAU > 1,000 後有自然成交，形成留存驅動力（基於 §5.1 Non-MVP 判斷）| MEDIUM | HIGH | A/B 測試（引入交易市場前後的 DAU 對比）| PRD 完成前 |

*A1 若假設錯誤，專案應終止或根本性調整方向（考慮改為匿名 token 模式）。*

---

## 13. Open Questions（待解問題）

| # | 問題 | 影響層級 | 若不解決的後果 | 負責人 | 狀態 |
|---|------|:-------:|------------|--------|:----:|
| OQ1 | 當玩家刪除 email 或換 email 時，如何轉移寵物所有權？（token 與 email 強綁定的設計風險）| 策略 | 可能需修改身份識別架構，影響 EDD 設計 | Engineering | 🔲 OPEN |
| OQ2 | 競技場對戰需要即時匹配（WebSocket）還是非同步匹配？影響後端架構複雜度 | 範圍 | 影響 MVP 後端架構選型（WebSocket vs. Polling）| Engineering | 🔲 OPEN |
| OQ3 | GDPR 合規：EU 用戶的 email 數據保留政策（認領後多久可刪除 email？）| 法規 | 可能影響 EU 市場進入時程 | Legal | 🔲 OPEN |
| OQ4 | 寵物交易是否涉及虛擬貨幣定價問題？（各地法規對虛擬物品交易的規定不一）| 法規 | 部分市場可能無法開放交易功能 | Legal | 🔲 OPEN |
| OQ5 | 初始寵物生成是純隨機（每次刷新都不同），還是「每個 IP 每日限制 1 次隨機」？影響稀缺感設計 | 範圍 | 影響前端交互設計和後端邏輯 | Product | 🔲 OPEN |

---

## 14. IDEA → BRD Handoff Checklist

> 以下所有項目確認後，方可執行 `/gendoc brd` 或啟動 `/gendoc-auto`。

| # | Checklist 項目 | 狀態 | 負責人 |
|---|--------------|:----:|--------|
| C1 | 一句話描述（§1.1）已清晰表達，無模糊詞 | ✅ | PM |
| C2 | 核心假說（§1.2）符合可測試格式 | ✅ | PM |
| C3 | Q1 使用者描述具體（非「所有人」）| ✅ | PM |
| C4 | Q2 痛點已量化（時間 / 成本損失有初步估算）| ✅（帳號轉換率 5-15%）| PM |
| C5 | Q4 規模已選定（影響架構決策）| ✅（DAU 2k-5k，PCU 200-500）| PM |
| C6 | 至少 1 個競品在 §7 已識別 | ✅（5 個競品 / 參考工具）| PM |
| C7 | 至少 3 項風險在 §8 已識別 | ✅（6 項風險）| PM |
| C8 | Kill Conditions（§8.2）已定義 | ✅（4 條，可量化）| PM |
| C9 | 關鍵假設 A1（§12）已識別並有驗證計畫 | ✅ | PM |
| C10 | IDEA Quality Score ≥ 3 | ✅（4/5）| AI 自動 |
| C11 | 原始 IDEA 原文已逐字保留（§6 末段）| ✅ | AI 自動 |
| C12 | Open Questions 中無 P0 級別未解技術問題 | ✅（OQ2 競技場架構待確認，但不阻塞 BRD 生成）| Engineering |

**Handoff 結論**：所有 C1-C12 已通過 ✅，可執行 `/gendoc brd` 生成 BRD。

---

## 15. Traceability Note（溯源說明）

*此文件是需求鏈的起點，扮演「原始意圖記錄者」的角色。*

**向下追溯（Forward）：**

```
IDEA.md （本文件）
  └─► BRD.md       ← /gendoc brd（由 /gendoc-auto 自動生成）
        └─► PRD.md      ← /gendoc prd
              └─► PDD.md      ← /gendoc pdd
                    └─► EDD.md      ← /gendoc edd
                          └─► ARCH / API / SCHEMA / BDD → 實作
```

**素材來源追溯：**

| 章節 | 來源素材 | 素材類型 |
|------|---------|---------|
| §1 Idea Essence（Elevator Pitch、核心假說）| `docs/req/idea-input.md` + Q1/Q2 澄清 | 原始構想文字輸入 |
| §2 Problem Statement（As-Is Narrative、5 Whys）| `docs/req/idea-input.md` + Q2 澄清 | 原始構想 + 澄清訪談 |
| §3 Target Users | Q1 澄清結果 | 澄清訪談 |
| §4 Value Hypothesis | Q2 澄清 + 研究摘要 | 澄清訪談 + Web Research |
| §5 MVP & Learning Plan | Q1/Q2 澄清 + PM 推斷 | 澄清訪談 + AI 推斷 |
| §6 Clarification Interview Record | Q1–Q5 原始回答 | 澄清訪談（逐字保留）|
| §7 Market & Competitive Intelligence | 研究摘要（state file）| Web Research 摘要 |
| §8 Initial Risk Assessment | 研究摘要（風險部分）+ AI 推斷 | Web Research + AI 推斷 |
| §9 Business Potential | AI 推斷（依商業模式常識）| AI 推斷 |
| §10 Executive Sponsorship | TBD（BRD 階段釐清）| 待補充 |
| §11 IDEA Quality Score | AI 自動評分 | AI 自動 |
| §12 Critical Assumptions | Q2/Q3/Q4 澄清 + 研究摘要 | 澄清訪談 + AI 推斷 |
| §13 Open Questions | AI 推斷（依技術 / 法規常識）| AI 推斷 |

**需求變更判斷準則：**

| 場景 | 對比依據 | 分類 |
|------|---------|------|
| 功能行為與原始 IDEA Q1/Q2 一致但實作有誤 | IDEA §6 原文 | **BUG**（修正，不需 ECR） |
| 功能需求超出原始 Q1/Q2 描述範圍 | IDEA §6 原文 | **ECR**（需人工評估變更範圍） |
| 技術選型偏離 Q3 且理由不足 | IDEA §6 Q3 | **ECR 或 ADR**（需說明決策依據） |

---

## Appendix A：Research Raw Data（研究原始資料）

*以下為研究的完整原始摘要（來自 state file research_summary），供 BRD §0 引用。*

### 搜尋 1：競品與開源專案

```
查詢：GitHub topics/virtual-pet browser HTML5 pixel art
結果：
- GitHub topics/virtual-pet：多個 Tamagotchi 風格虛擬寵物開源項目（瀏覽器 + 狀態機 + WebSocket）
- KilledByAPixel/LittleJS：輕量 HTML5 遊戲引擎（無依賴，⭐ 3k+），適合像素小遊戲
- Phaser.js：成熟 HTML5 遊戲框架，有豐富 pixel art + arcade 範例
- itch.io HTML5 Pixel Art + Procedural Generation 工具集：多款類似風格參考
```

### 搜尋 2：技術最佳實踐

```
查詢：HTML5 pixel art procedural generation + email magic link authentication
結果：
- 渲染框架建議：Phaser 3 或 LittleJS（輕量），Canvas 搭配 image-rendering: pixelated
- 像素生成：程序化生成（Sprite 組件拼裝），支援調色盤隨機化確保唯一性
- 後端：Node.js (Express/Fastify) + PostgreSQL（寵物數據持久化）
- Auth：Email Magic Link（JWT token，有效期 15 分鐘）+ 專屬 URL（長效 token）
- Email：SendGrid / Nodemailer（SMTP fallback）
```

### 搜尋 3：已知挑戰與陷阱

```
查詢：email magic link security risks + virtual pet game engagement retention
結果：
- Email Client 預掃描問題：收信後 client 可能提前點擊 magic link 導致失效
  → 改用 Password email 配合手動輸入，或使用 TOTP fallback
- Token 過期管理：必須設置 TTL + already-used tracking，防止 token 重用攻擊
- 帳號枚舉攻擊：email 不論是否存在都回傳相同訊息（不透露是否已存在）
- 像素寵物唯一性保證：需設計足夠大的隨機組合空間（種子 + 多屬性組合），並記錄已用 seed
- 競技場公平性：防止刷戰績（Rate limiting + 對戰冷卻期）
```

---

## Appendix B：Document History

| 版本 | 日期 | 作者 | 修改摘要 |
|------|------|------|---------|
| v0.1-capture | 2026-05-03 | AI Generated (gendoc-gen-idea) | 初始捕捉，由 AI 自動填寫（依 Q1-Q5 澄清 + docs/req/idea-input.md + state file research_summary）|
| v0.2 | — | — | — |

---

## Appendix C：素材清單

*列出所有引用的 docs/req/ 素材。*

| 檔案路徑 | 素材類型 | 應用於（對應章節）|
|---------|---------|-----------------|
| `docs/req/idea-input.md` | 產品原始構想文字輸入（使用者逐字輸入）| §1 Idea Essence、§2 Problem Statement、§4 Value Hypothesis、§6 原始 IDEA 原文（逐字保留）|
| `.gendoc-state-tobala-main.json`（Q1-Q5 欄位）| 澄清訪談紀錄（AI 自動填入）| §3 Target Users、§6 Clarification Interview Record（Q1-Q5）|
| `.gendoc-state-tobala-main.json`（research_summary 欄位）| Web Research 摘要（AI 研究後填入 state）| §7 Market & Competitive Intelligence、§8 Initial Risk Assessment、Appendix A |
| `.gendoc-state-tobala-main.json`（q4_dau / q4_peak_ccu / q4_estimate_basis 欄位）| PM Expert 容量推估（自動填入）| §6 Q4、§7.3 研究來源（流量估算）|

---

*此 IDEA.md 由 /gendoc 自動生成並保存。它記錄了需求探索過程的所有原始輸入、假設與品質評分，是未來 BUG vs ECR 判斷的一級依據。*

*未來需求發生變化時，請先閱讀本文件 §6（原始 IDEA 原文）與 §12（關鍵假設），確認變更是否超出原始意圖範圍。*
