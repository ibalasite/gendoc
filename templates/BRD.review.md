---
doc-type: BRD
target-path: docs/BRD.md
reviewer-roles:
  primary: "資深 Business Analyst（BRD 審查者）"
  primary-scope: "文件完整性、AC 可測試性、需求可執行性、範圍邊界清晰度、RACI 正確性、上游 IDEA 一致性"
  secondary: "資深 PM Expert"
  secondary-scope: "商業目標合理性、MoSCoW 優先級依據、ROI 三情境論證、北極星指標可量化度"
  tertiary: "資深 QA Expert"
  tertiary-scope: "驗收標準具體度、SMART 指標完整性、Handoff Checklist 可執行性、Kill Conditions 量化閾值"
quality-bar: "任何下游 PRD 撰寫者拿到此 BRD，無需與 PM 或業務部門對話，即能清楚理解商業目標、利害關係人需求、範圍邊界與成功標準，並直接開始撰寫 PRD。"
pass-conditions:
  - "CRITICAL 數量 = 0"
  - "Self-Check：template 所有 ## 章節（≥22 個）均存在且有實質內容"
  - "非功能性需求（效能/安全/可用性）均已定義具體數值"
upstream-alignment:
  - field: 核心問題陳述
    source: IDEA.md §2 Problem Statement
    check: BRD §2 Problem Statement 是否忠實反映 IDEA §2 描述的問題現象與根本原因，無遺漏或衝突
  - field: 目標使用者定義
    source: IDEA.md §3.1 主要使用者群
    check: BRD §4.2 Target Users 是否覆蓋 IDEA §3.1 定義的所有使用者群，角色描述一致
  - field: 核心痛點（Q2）
    source: IDEA.md §6 Q2 回答
    check: BRD §5.2 Pain Relievers 是否對應 IDEA Q2 所列的核心痛點
  - field: 技術限制（Q3）
    source: IDEA.md §6 Q3 回答
    check: BRD §8.1 技術約束是否納入 IDEA Q3 的所有技術限制，無遺漏
  - field: 商業模式假說
    source: IDEA.md §9.1 商業模式假說
    check: BRD §11 Business Model 的收入來源與定價策略是否與 IDEA §9.1 一致，或有明確說明變更原因
  - field: 核心假設清單
    source: IDEA.md §12 Critical Assumptions
    check: BRD §8.2 關鍵假設是否涵蓋 IDEA §12 中標記為 HIGH 影響的所有假設
  - field: Kill Conditions
    source: IDEA.md §8.2 Kill Conditions
    check: BRD §10.2 Kill Criteria 是否包含或升版 IDEA §8.2 的 Kill Conditions
---

# BRD Review Items

本檔案定義 `docs/BRD.md` 的審查標準。由 `/reviewdoc BRD` 讀取並遵循。
審查角色：三角聯合審查（資深 Business Analyst + 資深 PM Expert + 資深 QA Expert）
審查標準：「假設公司聘請一位資深 Business Analyst，以業界最嚴格的標準進行 BRD 驗收審查。BRD 的上游為 IDEA.md（含 docs/req/ 所有素材）；所有 Finding 必須引用上游原文或 BRD 內部章節作為依據。」

---

## Review Items

### Layer 1: IDEA 上游對齊（由 Business Analyst 主審，共 4 項）

#### [CRITICAL] 1 — §2 Problem Statement 與 IDEA 問題陳述不一致
**Check**: BRD §2.1 現狀描述與 §2.2 五問分析是否與 IDEA §2（Problem Statement）的核心問題一致？若 BRD 描述的問題現象與 IDEA §2.1 顯著不同（例如 IDEA 說「庫存管理混亂」但 BRD 說「銷售轉換率低」），視為 CRITICAL。若 IDEA 不存在，以 BRD 內部章節一致性為查核基準。
**Risk**: 問題陳述發生漂移，後續 PRD 功能設計將基於與最初構想不一致的問題定義，導致交付物無法解決使用者原始痛點。
**Fix**: 以 IDEA §2 為準，修正 BRD §2.1 的問題描述；若業務情境已演進，在 §15 Decision Log 記錄問題陳述的正式更新，並說明更新依據。

#### [CRITICAL] 2 — §4.2 Target Users 遺漏 IDEA 定義的使用者角色
**Check**: BRD §4.2 Target Users 表格是否涵蓋 IDEA §3.1 定義的所有使用者群（主要、次要）？若 IDEA 定義了「企業 IT 管理員」和「一般員工」兩個角色，但 BRD §4.2 只列一個，視為 CRITICAL。若 BRD 自行新增角色，是否有說明新增依據？
**Risk**: 遺漏使用者角色，PRD Persona 設計和功能優先排序將基於不完整的受眾定義，導致部分使用者群的核心需求在 Sprint 中被系統性忽略。
**Fix**: 補充缺漏的使用者角色行；若 BRD 新增了 IDEA 未定義的角色，在 §14 Open Questions 記錄此角色的業務依據來源（訪談/數據）。

#### [HIGH] 3 — §8.1 技術約束遺漏 IDEA Q3 指定的限制
**Check**: 若 IDEA §6 Q3 回答明確了技術限制（如「必須整合既有 SAP 系統」「只能使用 AWS 服務」「不支援原生行動 App」），這些限制是否全部出現在 BRD §8.1 技術限制表格中？逐一比對 IDEA Q3 的每個限制，列出缺漏的項目。
**Risk**: 技術約束未轉移到 BRD，EDD 撰寫者在技術選型時將缺乏關鍵邊界條件，可能選用與既有系統不相容的架構，導致後期高成本整合工作。
**Fix**: 逐一將 IDEA Q3 的技術限制填入 BRD §8.1，標注類型（硬性/軟性）並說明對實作策略的影響。

#### [HIGH] 4 — §8.2 關鍵假設未涵蓋 IDEA HIGH 影響假設
**Check**: 對照 IDEA §12 Critical Assumptions 中標記為「影響層級=HIGH」的假設（A1/A2 等），BRD §8.2 是否均有對應的假設條目？若 IDEA A1（最高風險假設）未出現在 BRD §8.2，視為 HIGH。
**Risk**: IDEA 識別的高影響假設未被 BRD 繼承，PRD 和 EDD 將在未驗證的假設上建立設計，一旦假設被推翻將引發大規模返工。
**Fix**: 將 IDEA §12 的 HIGH 影響假設逐一加入 BRD §8.2，補充 BRD 階段的驗證方式和時間點；若假設已被驗證，記錄驗證結果。

---

### Layer 2: 商業目標品質（由 PM Expert 主審，共 5 項）

#### [CRITICAL] 5 — §3.1 商業目標缺乏 SMART 量化指標
**Check**: §3.1 的每個商業目標（O1/O2/O3）是否同時滿足 SMART 五要素：**S**pecific（具體指標名稱）、**M**easurable（有具體數字）、**A**chievable（合理可達）、**R**elevant（與業務目標相關）、**T**ime-bound（有時間框架）？「提升使用者體驗」「增加效率」「改善用戶滿意度」等無量化數字的目標視為 CRITICAL。逐一列出不符合 SMART 的目標。
**Risk**: 不可量化的目標使得 PRD 成功指標無從定義，工程師無法判斷功能是否達標，最終上線後無法回答「這個 BRD 目標達成了嗎」的問題。
**Fix**: 為每個目標補充量化指標（KPI 名稱 + 具體目標值 + 時間框架），例如「3 個月內 DAU 達到 10,000」；「提升」類描述必須改寫為「提升 X% 至 Y 值，在 Z 日前達成」。

#### [CRITICAL] 6 — §7.1 北極星指標（North Star Metric）缺失或無法量化
**Check**: §7.1 是否定義了一個具體可量化的北極星指標，且「定義/測量方式」已填寫？若 North Star 欄位為 `{{NORTH_STAR_METRIC}}` 或留空，視為 CRITICAL；若定義方式泛化（「用戶滿意度」而無測量方法），視為 HIGH。
**Risk**: 沒有北極星指標，整個產品開發缺乏聚焦點；團隊在 Sprint 間無共同的「好壞」判斷標準，導致功能優先序爭議不斷。
**Fix**: 定義一個核心北極星指標（建議選用能反映使用者核心價值創造的 Output Metric），填寫具體的計算公式或數據來源；同時確認 §7.2 的 Outcome/Output/Input 三層指標鏈邏輯自洽。

#### [HIGH] 7 — §3.3 ROI 三情境分析缺失或僅有單一情境
**Check**: §3.3 是否完整填寫了悲觀/基準/樂觀三個情境，每個情境是否有獨立的「驅動假設」（而非對基準情境的比例縮放）？若三個情境共用相同假設，或「驅動假設」欄為 `{{ASSUMPTION_X}}`，視為 HIGH；若整個 §3.3 缺失，視為 CRITICAL。
**Risk**: 單一情境 ROI 分析無法反映不確定性，Executive Sponsor 基於過度樂觀的單一估算做出投資決策，一旦市場反應低於預期無備案計畫。
**Fix**: 確保三個情境各有獨立的驅動假設（悲觀：市場滲透低 + 競爭加劇；基準：依計畫執行；樂觀：快速採納 + 競爭優勢顯現）；填入每個情境的具體成本、收益、Payback Period 和 3 年 NPV 估算。

#### [HIGH] 8 — §5.3 範圍邊界（In/Out Scope）Out of Scope 缺乏理由
**Check**: §5.3 Out of Scope 清單中每個排除項目是否都有「排除原因」說明？若有功能僅列「❌ 功能 X」而無括號內的理由，視為 HIGH；若 Out of Scope 整節為空，視為 CRITICAL。
**Risk**: 缺少排除理由，利害關係人在 PRD 審查時可以輕易主張「把 Out of Scope 功能加回來」，導致範圍蔓延；工程師也無法從文件中理解排除的商業邏輯。
**Fix**: 為每個 Out of Scope 功能補充排除原因（如「資源限制：MVP 預算不足」「時機問題：依賴外部 API 尚未就緒」「戰略選擇：此功能屬競品護城河，自建 ROI 不足」）。

#### [MEDIUM] 9 — §5.4 MoSCoW 優先度缺乏與商業目標的對應
**Check**: §5.4 MoSCoW 表格的「對應 BRD 目標」欄是否已填寫具體的 O1/O2/O3 目標編號？Must Have 功能加總是否超過估算開發容量的 60%？若「對應 BRD 目標」欄有任何空白或 `{{N}}`，視為 MEDIUM。
**Risk**: 功能優先排序與業務目標脫鉤，Sprint Planning 時無法用業務價值論據支撐優先級決策；Must Have 超過 60% 導致 MVP 開發風險過高。
**Fix**: 為每個功能填寫對應的 BRD 目標編號；重新評估 Must Have 功能比例，確保不超過開發容量的 60%；若超過，將部分 Must Have 降為 Should Have 並說明理由。

---

### Layer 3: 利害關係人與 RACI（由 Business Analyst 主審，共 3 項）

#### [HIGH] 10 — §4.4 RACI Matrix 每列活動有多個「A」或缺少「A」
**Check**: §4.4 RACI Matrix 的每個活動列是否有且只有一個「A」（Accountable，最終負責人）？逐一掃描每列，列出有多個 A 或缺少 A 的活動行。
**Risk**: RACI 中多個 A 或缺少 A 會導致決策責任模糊，在需要快速決策時出現「推諉」或「多頭馬車」情況，影響上線決策（Go/No-Go）的執行效率。
**Fix**: 為每個活動確認唯一的 A 角色；若組織內某活動確實有共同負責需求，改為一位 A + 其他人標記 R，並在備注說明協作方式。

#### [MEDIUM] 11 — §4.3 Not Our Users 為空或過於籠統
**Check**: §4.3 是否至少列出 1 個具體的排除群體（含排除原因）？若整節為空或僅有 `{{EXCLUDED_USER_GROUP}}`，視為 MEDIUM；若排除原因為「不是目標用戶」等循環定義，視為 finding。
**Risk**: 未明確排除群體，功能需求評審時容易被拉入「我們也應該服務 X 群體」的討論，導致 PRD Scope 蔓延；QA 也無法確定哪些用戶行為場景不需要覆蓋。
**Fix**: 填寫至少 1 個具體的排除群體（含職業/規模/行為特徵），說明排除的業務原因（成本/戰略/技術可行性）。

#### [LOW] 12 — §4.1 Stakeholder Map Mermaid 圖含裸 Placeholder
**Check**: §4.1 Stakeholder Map 的 Mermaid 圖中，NAME 欄位（Executive Sponsor/PM/Engineering Lead/Design Lead）是否至少有 1 個已填寫真實名稱（或角色標識）？若所有 `{{NAME}}` 均未替換，視為 LOW。
**Risk**: Stakeholder Map 全是 placeholder，無法作為溝通工具；在 BRD Kick-off 會議中分發此文件，與會者無法識別責任人。
**Fix**: 替換至少核心角色（Executive Sponsor、PM）的 `{{NAME}}` 為真實姓名或職稱；若人員尚未確定，填寫「TBD（職稱）」並在 §14 Open Questions 記錄何時確定。

---

### Layer 4: 成功指標可量化度（由 QA Expert 主審，共 4 項）

#### [CRITICAL] 13 — §7.2 業務指標階層缺少 Outcome 層指標
**Check**: §7.2 的 Outcome/Output/Input 三層指標鏈是否完整？Outcome 層是否有最終業務成果指標（如「營收增長 X%」「成本節省 $Y」）？若 Outcome 欄位為 `{{OUTCOME_METRIC}}` 或缺失，視為 CRITICAL。
**Risk**: 缺少 Outcome 指標，無法從最終業務成果倒推 Output 和 Input 的合理目標；Executive Sponsor 無法用財務語言評估投資回報，BRD 審查將陷入「功能討論」而非「價值討論」。
**Fix**: 定義至少 1 個 Outcome 指標（業務成果，通常為財務或市場份額指標）；確保 Outcome → Output → Input 三層之間有邏輯因果關係（可在圖下加一句說明）。

#### [HIGH] 14 — §3.5 Benefits Realization Plan 基準值（Baseline）缺失
**Check**: §3.5 的每個效益條目是否填寫了「基準值（Pre-launch）」？若基準值為 `{{BASELINE}}` 或「N/A」但無說明（某些新指標確實無歷史基準需說明），視為 HIGH。
**Risk**: 沒有基準值，Launch + 3M/6M/12M 的效益評審無法計算相對改善幅度，Executive Sponsor 無法客觀判斷效益是否兌現，所有效益聲稱均無法驗證。
**Fix**: 為每個效益條目填寫基準值（使用現有數據或「0（新指標，無歷史基準）」說明）；若基準值需要額外調研，在 §14 Open Questions 記錄調研計畫和截止日期。

#### [HIGH] 15 — §7.3 投資門檻條件不可量化
**Check**: §7.3 的每個投資門檻條件（Alpha/Beta 結束後）是否有具體的量化目標值（如「DAU ≥ 5,000 持續 2 週」）？若條件描述為「符合預期」「達到初步驗證」等定性判斷，視為 HIGH。
**Risk**: 投資門檻無量化標準，在實際業務壓力下（如已投入大量資源）容易發生「理性化通過」，無法在正確時機做出 Stop/Pivot/Continue 決策。
**Fix**: 為每個投資門檻條件補充量化閾值（數字 + 持續時間 + 評估時間點）；確保閾值基於 §5.2 Lean Hypothesis 的驗證指標，使兩者相互呼應。

#### [MEDIUM] 16 — §3.4 RTM 需求追溯矩陣功能需求欄（REQ-ID）未填寫
**Check**: §3.4 RTM 表格的「功能需求（PRD REQ-ID）」欄是否至少有佔位說明（如「待 PRD 確定後填入」）？若整欄為 `REQ-001, REQ-002` 等明顯複製自範本的 placeholder，且 BRD 狀態已為 IN_REVIEW 或 APPROVED，視為 MEDIUM。
**Risk**: RTM 僅有業務目標欄完整，功能需求欄空白，無法確認業務目標已被所有 PRD 需求覆蓋；BRD → PRD Handoff 後 PM 容易遺忘補全 RTM，導致追溯鏈斷裂。
**Fix**: 若 PRD 尚未完成，將 RTM 的 REQ-ID 欄標記「待 PRD 完成後由 PM 填入（預計日期：{{DATE}}）」；若 PRD 已存在，立即從 PRD 中引用對應的 REQ-ID。

---

### Layer 5: 合規與風險（由 Business Analyst + QA Expert 聯合審查，共 4 項）

#### [CRITICAL] 17 — §9.1 適用法規清單完全缺失或為「N/A」但無說明
**Check**: §9.1 是否已識別所有適用法規？若產品涉及用戶個人資料（PII）但 GDPR/CCPA/個資法均未出現在清單，視為 CRITICAL；若填寫「N/A」但無法律依據說明（`LEGAL_BASIS` 欄空白），視為 HIGH。若整個 §9 缺失，視為 CRITICAL。
**Risk**: 法規未識別，合規成本無法納入 BRD ROI 估算（可能導致上線後被迫追加高成本合規工作）；嚴重情況下可能因法規阻礙無法上市，已投入資源全部損失。
**Fix**: 依產品的目標市場、數據類型、行業領域逐一掃描適用法規（GDPR/CCPA/台灣個資法/HIPAA/PCI-DSS/App Store 政策等）；「N/A」必須填寫明確的法律依據（如「本產品不收集 PII，僅記錄匿名使用統計數據」）。

#### [HIGH] 18 — §10.1 業務風險缺乏技術可行性風險或競爭風險
**Check**: §10.1 的風險清單是否至少包含 3 個不同類型的風險（市場/執行/技術/競爭）？是否有至少 1 個「技術可行性」相關風險？若整個風險清單類型單一（例如全部為「市場風險」），視為 HIGH。
**Risk**: 風險識別不全面，特定類型的風險在 BRD 審查時未受到關注，在 EDD 或實作階段才被發現，導致計畫滯後和成本超支。
**Fix**: 補充缺漏的風險類型；技術可行性風險至少包含一項（特別是對 IDEA Q3 中識別的技術限制）；每個風險填寫緩解策略和負責人。

#### [HIGH] 19 — §10.2 Kill Criteria 觸發閾值不可客觀量化
**Check**: §10.2 的每個 Kill Criterion 是否有可被客觀量化的觸發閾值？「效果不好」「市場反應不如預期」「技術複雜度過高」等定性判斷視為 HIGH；`{{KILL_CONDITION_1}}` 等未替換的 placeholder 視為 CRITICAL。
**Risk**: Kill Criteria 無量化閾值，業務壓力下容易被合理化跳過（「雖然 DAU 沒到目標但有增長趨勢」），導致「殭屍專案」繼續消耗資源而無法及時叫停。
**Fix**: 為每個 Kill Criterion 補充量化觸發條件（指標名稱 + 數字閾值 + 持續時間）；確保閾值可被數據直接驗證，不依賴主觀判斷；至少包含 1 個財務觸發條件和 1 個用戶行為觸發條件。

#### [MEDIUM] 20 — §13.1 Vendor Dependency Risk 缺少 Tier 1 退出計畫
**Check**: §13.1 Vendor & Third-Party Dependency Risk 表格中，Tier 1（核心依賴，無法替代）的供應商是否填寫了退出計畫（Exit Plan）？若 Tier 1 供應商的 Exit Plan 欄為空或 `{{EXIT_PLAN}}`，視為 MEDIUM。若 §13.1 整節缺失且文件有第三方依賴，視為 HIGH。
**Risk**: Tier 1 供應商無退出計畫，當核心依賴服務中斷、漲價或終止時，產品將陷入無備案的危機，緊急遷移成本極高且影響業務連續性。
**Fix**: 為每個 Tier 1 供應商填寫具體退出計畫（遷移時間估算、替代方案、資料遷移策略）；若真的無替代方案，在備注說明「無可替代，建議與供應商簽署長期 SLA 合約」。

---

### Layer 6: Handoff 完整性（由 QA Expert 主審，共 4 項）

#### [HIGH] 21 — §18.1 Handoff Checklist 有未完成的 H1/H2/H5 項目
**Check**: §18.1 Handoff Checklist 的 H1（所有利害關係人核准）、H2（北極星指標已量化）、H5（成功指標含基準值和目標值）是否均已完成（✅ 狀態）？若三項中任一仍為 ☐ PENDING 且 BRD 狀態為 IN_REVIEW 或 APPROVED，視為 HIGH。
**Risk**: 核心 Handoff 條件未滿足即進入 PRD，PRD 撰寫者將在缺乏利害關係人共識或量化目標的情況下工作，後期反工風險極高。
**Fix**: 逐項確認 H1–H8 的完成狀態；對仍為 PENDING 的項目補充預計完成日期和負責人；若確實無法在 BRD 審查前完成，在 §14 Open Questions 記錄為阻斷項。

#### [HIGH] 22 — §18.2 Handoff 移交文件存放位置全為空連結
**Check**: §18.2 的所有文件條目（用戶研究摘要/技術可行性評估/市場競品分析/財務模型）的「存放位置」是否至少有一個有效連結（或填寫「尚未完成，預計 {{DATE}}」）？若所有 `{{LINK}}` 均未替換，視為 HIGH。
**Risk**: 移交文件位置不明，PRD Owner 接手後需額外花時間尋找支撐資料；若某份關鍵文件（如用戶研究報告）實際上尚未完成，在 Handoff 時才被發現，將延誤 PRD 啟動。
**Fix**: 逐一填寫每份文件的存放連結或狀態（「已完成，存放於 [連結]」或「未完成，預計完成日 {{DATE}}，負責人 {{NAME}}」）；若文件確實不需要，填寫「N/A — 依據：[說明]」。

#### [MEDIUM] 23 — §15 Decision Log 無任何決策記錄
**Check**: §15 Decision Log 是否至少有 1 條真實的決策記錄（非複製自範本的 `{{ISSUE_1}}` 等 placeholder）？若整個 Decision Log 僅有範本 placeholder 行，或文件狀態為 APPROVED 但 Decision Log 為空，視為 MEDIUM。
**Risk**: 決策過程未記錄，BRD 審查者無法了解為何某些範圍或優先級被這樣決定；未來若需要更改決策，缺乏原始依據導致「為什麼當時這樣決定」的問題無法回答。
**Fix**: 補充至少 1 條真實的決策記錄（從 BRD 撰寫過程中最重要的一個選擇出發，例如「是否支援行動端」「定價模型的選擇」「MVP 範圍裁剪決定」），填寫決策依據和決策者。

#### [LOW] 24 — §20 Approval Sign-off 核准者欄位全為空
**Check**: §20 Approval Sign-off 表格的姓名欄是否至少有 Executive Sponsor 和 PM 的姓名已填寫（不需要簽核日期，但姓名應已確認）？若所有 `{{NAME}}` 均未替換，視為 LOW；若文件狀態為 APPROVED 但 Sign-off 均為空，視為 HIGH。
**Risk**: 核准者名單空白，BRD 下游文件的 PRD 撰寫者無法確認應向誰確認業務疑問；也無法追溯誰對此 BRD 的商業承諾負責。
**Fix**: 填寫至少 Executive Sponsor 和 PM 的真實姓名；若某角色組織中不存在（如 Finance），在備注中說明「此組織不設此角色，由 {{替代角色}} 負責」。

---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/BRD.md`，提取所有 `^## ` heading（含條件章節），共約 22 個
2. 讀取 `docs/BRD.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
