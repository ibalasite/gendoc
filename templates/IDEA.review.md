---
doc-type: IDEA
target-path: docs/IDEA.md
reviewer-roles:
  primary: "資深 Business Strategist（IDEA 審查者）"
  primary-scope: "需求清晰度、市場機會驗證、問題陳述品質、願景可行性、使用者定義精確度"
  secondary: "資深 Product Manager Expert"
  secondary-scope: "功能優先級合理性、成功指標可量化度、Next Steps 具體性、Handoff Checklist 完整性"
  tertiary: "資深 Technical Advisor"
  tertiary-scope: "技術約束完整性、可行性評估、假設驗證方式、競品技術生態合理性"
quality-bar: "任何產品開發者拿到此 IDEA.md，無需與發想者對話，即能清楚理解商業問題、目標使用者、核心功能範圍與成功標準，並直接開始撰寫 BRD。"
upstream-alignment:
  - field: IDEA 本身是需求鏈起點，無上游文件
    source: N/A
    check: 確認 IDEA.md 為自洽文件，§1–§15 各章節內部無矛盾
  - field: docs/req/ 素材完整性
    source: IDEA.md Appendix C（若存在）
    check: Appendix C 列出的所有 docs/req/ 檔案是否均實際存在於目錄中
---

# IDEA Review Items

本檔案定義 `docs/IDEA.md` 的審查標準。由 `/reviewdoc IDEA` 讀取並遵循。
審查角色：三角聯合審查（資深 Business Strategist + 資深 PM Expert + 資深 Technical Advisor）
審查標準：「假設公司聘請一位資深 Business Strategist，以最嚴格的業界標準進行 IDEA 驗收審查。IDEA.md 是需求鏈起點，無上游文件；所有 Finding 以 IDEA.md 自身完整性與 templates/IDEA.md 章節結構為依據。」

---

## Review Items

### Layer 1: 需求清晰度與完整性（由 Business Strategist 主審，共 7 項）

#### [CRITICAL] 1 — §1.1 Elevator Pitch 含模糊詞或為空
**Check**: §1.1 Elevator Pitch 是否清楚說明「幫助 [具體使用者] 解決 [具體痛點]，方式是 [差異化做法]」？是否含「讓事情更好」「提升體驗」「更方便」等模糊表達，或整段為 `{{PLACEHOLDER}}`？逐一列出模糊詞彙。
**Risk**: Elevator Pitch 不清晰，BRD 撰寫者無法準確把握產品方向，後續所有下游文件的目標錨定均會偏移。
**Fix**: 按照 What/Who/Why 句型重寫 §1.1，確保「使用者」「痛點」「解法」三要素各自具體可辨，刪除所有模糊詞彙。

#### [CRITICAL] 2 — §2.1 現狀描述缺乏具體場景
**Check**: §2.1 是否描述了目前使用者如何應對問題（含具體 workaround 或替代方案）？若僅有泛化陳述（「現在的解法很麻煩」），未提及具體操作步驟或實際痛苦場景，視為 CRITICAL。
**Risk**: 現狀描述不具體，BRD §2 Problem Statement 將缺乏真實用戶場景支撐，導致解法設計偏離實際需求。
**Fix**: 補充「使用者目前如何處理此問題」的具體流程（含工具、步驟、痛苦點），確保 §2.1 可直接作為 BRD §2.1 的原始輸入。

#### [CRITICAL] 3 — §2.2 五問分析（5 Whys）未達根本原因
**Check**: §2.2 的 5 Whys 鏈是否完整（至少 3 層，且最後一層指向系統性根因而非症狀）？若最末層仍是「流程不好」「工具不夠好」等症狀描述，或整段為 `{{PLACEHOLDER}}`，視為 CRITICAL。
**Risk**: 根因分析停留在症狀層，解法可能只治標不治本，下游 BRD 的 Problem Statement 缺乏深度論證。
**Fix**: 補充每個 Why 層級的具體原因，確保最末層是「系統性根因」而非可進一步追問的症狀；若問題不到 5 層即到達根因，說明原因。

#### [CRITICAL] 4 — §3.1 目標使用者定義過於寬泛
**Check**: §3.1 使用者描述是否具體到可以識別具體個人特徵（職業/角色、行業/情境、技術成熟度、使用頻率、決策角色）？若使用「所有人」「任何用戶」「有需求的人」等泛化描述，或 User_Role / User_Industry_Context 欄位為空，視為 CRITICAL。
**Risk**: 使用者定義模糊，PRD Persona 無法精確設計，功能優先序無法基於真實用戶行為做出；BRD §4 Stakeholders 將缺乏具體受眾錨點。
**Fix**: 補充具體的職業/角色描述；若有多個用戶群，分別列出各群的特徵屬性表；明確填寫技術成熟度與決策角色欄位。

#### [HIGH] 5 — §14 IDEA→BRD Handoff Checklist 未填寫或大量 PENDING
**Check**: §14 IDEA→BRD Handoff Checklist（C1–C12）是否已逐項確認？若有超過 3 項為 🔲 PENDING 狀態（且 IDEA Quality Score < 3），視為 HIGH。若 C1（Elevator Pitch 清晰）、C3（Q1 使用者具體）、C4（Q2 痛點已量化）三項中任一仍為 PENDING，升為 CRITICAL。
**Risk**: Checklist 未完成即進入 BRD 生成，會導致 BRD 因缺少輸入而充滿 placeholder，後續審查輪次需要大量額外補充工作。
**Fix**: 逐項確認 C1–C12，填寫具體的完成狀態（✅）；無法確認的項目補充說明原因並標記為 DEFERRED（含期限和負責人）。

#### [HIGH] 6 — §6 澄清訪談記錄（Q1–Q5）與正文章節內容不一致
**Check**: §6 的 Q1–Q5 回答是否與 §3.1（Q1）、§2.1/§4.1（Q2）、§7.2（Q3）、§2.3（Q4）對應章節的內容一致？逐一比對關鍵詞，若有矛盾（例如 Q1 答「企業 IT 管理員」但 §3.1 描述「個人用戶」），視為 HIGH。
**Risk**: Q&A 記錄與文件正文不同步，後續升版時 BRD 生成器會以哪個版本為準存在歧義，導致需求追溯困難。
**Fix**: 以 §6 的 Q&A 記錄為主要依據，逐一更新正文中不一致的章節；或反向確認正文為準後更新 §6 記錄。

#### [MEDIUM] 7 — §11 Quality Score 低於建議門檻或未填寫
**Check**: §11 IDEA Quality Score 是否已填寫且分數 ≥ 3？若分數為 1–2，是否有對應改進計畫說明？若 §11 整段為空或 `{{STAR_RATING}}` 未替換，升為 HIGH。
**Risk**: Quality Score 過低但未記錄改進計畫，意味著 IDEA 帶著大量 AI 推斷進入 BRD 階段，導致 BRD 品質連鎖下降；QA 無法判斷 IDEA 是否具備啟動 BRD 的最低門檻。
**Fix**: 依 §11 各評分維度（目標清晰度/使用者具體度/痛點可量化/範圍邊界/技術可行性）逐項評分，填寫具體分數；若有維度得 0 分，補充改進說明或在 §13 Open Questions 記錄待解事項。

---

### Layer 2: 市場與業務價值（由 Business Strategist 主審，共 5 項）

#### [HIGH] 8 — §7.1 競品分析少於 2 個，或比較維度缺失
**Check**: §7.1 競品分析表是否至少包含 2 個具名競品（非「其他工具」等泛指）？每個競品是否填寫了「核心定位/優勢/劣勢/我們的差異」四個維度？若任何維度保留 `{{PLACEHOLDER}}`，視為 finding。
**Risk**: 競品分析不完整，BRD §6 Market & Competitive Analysis 缺乏數據支撐，差異化定位無法被驗證；Elevator Pitch 的「差異化做法」也無法被質疑或確認。
**Fix**: 補充至少 2 個具名競品，逐一填寫四個比較維度；若市場真的無直接競品，說明替代解法（如「目前用 Excel 處理」）並分析其局限性。

#### [HIGH] 9 — §4.2 差異化定位陳述空洞或無法持續
**Check**: §4.2 差異化定位陳述（`DIFFERENTIATION_STATEMENT`）是否說明了「為什麼是我們而不是競品」？若差異化僅依賴「更便宜」「更快」「更好用」等一時性優勢，或整段為 `{{PLACEHOLDER}}`，視為 HIGH。
**Risk**: 差異化不可持續，競品可快速複製；BRD 的競爭壁壘論述將缺乏依據，投資決策難以成立。
**Fix**: 重新定義差異化，確保至少引用一個結構性壁壘（技術護城河/數據優勢/網路效應/切換成本）；若目前無護城河，在 §8 風險中明確記錄並提出應對策略。

#### [HIGH] 10 — §2.3 問題規模完全缺失量化數據
**Check**: §2.3 的 TAM/SAM/SOM 三個指標是否至少有初始估算值（可為 AI 推斷，但需標注信心水準）？若三個指標均為 `{{PLACEHOLDER}}` 或留空，視為 HIGH；若僅有定性描述（「市場很大」），亦視為 finding。
**Risk**: 缺少市場規模估算，BRD §2.3 和 §3.3 ROI 分析將缺乏輸入數據，投資決策無法量化論證。
**Fix**: 補充 TAM/SAM/SOM 估算，即使是低信心水準的 AI 推斷也需填入具體數字範圍；標注數據來源和信心水準。若某指標真的無法估算，說明原因。

#### [MEDIUM] 11 — §9.1 商業模式假說為空或過於籠統
**Check**: §9.1 商業模式假說的收入來源和定價策略是否填寫了具體假設（例如「SaaS 訂閱 $29/月」而非「訂閱制」）？若整欄為 `{{PLACEHOLDER}}` 或僅有一個詞（「SaaS」），視為 MEDIUM。
**Risk**: 商業模式不明確，BRD §11 Business Model 的撰寫缺乏基礎假設，ROI 三情境估算也無法合理設定驅動假設。
**Fix**: 補充初始定價假設（含方案類型和具體金額區間）；若為內部工具，填寫「成本節省量化方式」；商業模式假說不需精確，但需具體到可被討論和挑戰。

#### [MEDIUM] 12 — §9.2 戰略對齊表與公司策略目標脫節
**Check**: §9.2 中列出的公司策略目標是否真實反映公司的實際 OKR 或策略方向？若使用 `{{COMPANY_STRATEGY_1}}` 等通用佔位符，或所有對齊強度均標為「強」，視為 MEDIUM。
**Risk**: 戰略對齊表流於形式，Executive Sponsor 在 BRD 審查時無法確認此 IDEA 與公司方向的實際連結，影響優先級決策。
**Fix**: 填寫具體的公司策略目標（可參考公司 OKR 或年度策略文件），並誠實評估對齊強度；若對齊強度為「弱」，說明其他正當化理由。

---

### Layer 3: 功能範圍定義（由 PM Expert 主審，共 4 項）

#### [HIGH] 13 — §5.1 MVP 範圍與驗證假設未明確連結
**Check**: §5.1 MVP 功能表格的每一行是否都填寫了「驗證假設」和「最低可接受標準」？若有功能行的這兩欄為空或 `{{PLACEHOLDER}}`，視為 HIGH。若 MVP 功能超過 5 項且全部標記為「Must」，視為 finding（MVP 範圍過大）。
**Risk**: MVP 功能無明確驗證假設，開發完成後無法評估是否達到 Go/Pivot/Kill 決策點；MVP 範圍過大則失去「最小可行」的本意。
**Fix**: 為每個 MVP 功能填寫具體的「驗證假設」（對應 §12 某條假設）和「最低可接受標準」（可量化閾值）；若 MVP 超過 5 項，重新評估哪些功能是核心驗證必需，其餘移至 Non-MVP 清單。

#### [HIGH] 14 — §3.3 非目標使用者（Not Our Users）缺失或不具體
**Check**: §3.3 是否至少列出 2 個具體排除群體，並說明排除原因？若整節為空、僅有 `{{EXCLUDED_GROUP_1}}`，或排除原因過於籠統（「不是我們的用戶」），視為 HIGH。
**Risk**: 未明確「不服務誰」，範圍蔓延風險高；PRD 功能定義缺乏邊界約束，容易被利害關係人無限追加需求。
**Fix**: 列出至少 2 個具體的排除群體（含職業/規模/行為特徵），並說明排除的業務原因（如「小於 10 人的團隊 ROI 不足以支撐我們的銷售成本」）。

#### [MEDIUM] 15 — §13 Open Questions 未記錄 BRD 階段待解問題
**Check**: §13 Open Questions 是否至少包含 1 個「影響層級=策略或範圍」的待解問題？若整節為空，或所有 OQ 均為 LOW 影響級別，或問題描述過於技術細節（屬 EDD 層次），視為 MEDIUM。
**Risk**: 未記錄 BRD 階段待解問題，導致 BRD 撰寫者在沒有明確問題指引的情況下需要自行推斷，產生的 BRD 可能遺漏關鍵商業決策點。
**Fix**: 補充至少 1 個策略層級的待解問題（例如「是否進入企業市場還是 SMB 市場」「定價模型是否支援年繳折扣」）；確保每個 OQ 有負責人和狀態。

#### [LOW] 16 — §5.3 Riskiest Assumption（核心 Leap of Faith）未明確標記驗證期限
**Check**: §5.3 的 Leap of Faith 陳述是否包含「若此假設為假的後果」和「驗證截止日期」？若兩者均缺失，視為 LOW（若缺少後果描述，升為 MEDIUM）。
**Risk**: Leap of Faith 沒有截止日，驗證工作容易被無限推遲；沒有「若假設為假的後果」描述，團隊無法提前準備 Pivot 方案。
**Fix**: 補充驗證截止日期（建議在 Discovery 週 3 前）和「若假設為假則應採取的行動」（Pivot 或 Kill 選項），確保 §5.3 的核心假說格式完整。

---

### Layer 4: docs/req/ 素材管理（由 Business Strategist 主審，共 2 項）

#### [HIGH] 17 — docs/req/ 素材未在 IDEA.md 中完整引用
**Check**: 若 docs/req/ 目錄存在，IDEA.md 的 Appendix C（或等效章節）是否列出了所有 docs/req/ 下的檔案？逐一比對 Appendix C 清單與實際目錄內容。若有 docs/req/ 檔案未被引用，視為 HIGH；若 Appendix C 整節缺失但 docs/req/ 目錄非空，視為 HIGH。
**Risk**: 輸入素材未在 IDEA.md 中記錄，後續 BRD 生成和審查時可能遺漏重要的原始資料（用戶訪談、競品截圖、原始需求文件），導致下游文件與原始輸入脫鉤。
**Fix**: 在 IDEA.md 添加或更新 Appendix C，逐一列出 docs/req/ 下所有檔案的檔名、類型（圖片/文件/URL）和簡短描述；確保與實際目錄完全對應。

#### [MEDIUM] 18 — §6 原始 IDEA 原文（逐字保留）為空或已被修改
**Check**: §6「原始 IDEA（使用者輸入原文，逐字保留）」code block 是否包含原始輸入的完整原文？若此區塊為空、僅有 `{{ORIGINAL_IDEA_VERBATIM}}`，或內容看起來已被潤飾改寫（而非逐字保留），視為 MEDIUM。
**Risk**: 原始輸入原文缺失，未來 ECR（Engineering Change Request）審查時無法確認需求變更是 BUG 修正還是範圍擴充，ECR 判斷失去依據。
**Fix**: 將使用者最原始的輸入（無論是文字描述、口語記錄、還是摘要）完整填入此 code block，標注輸入時間戳；若輸入為圖片或 URL，記錄「原始輸入已保存至 docs/req/XXX」。

---

### Layer 5: 技術約束與可行性（由 Technical Advisor 主審，共 4 項）

#### [HIGH] 19 — §7.2 技術生態建議與 Q3 技術約束矛盾
**Check**: §7.2 建議的程式語言/框架/資料庫是否與 §6 Q3（技術限制或偏好）的回答一致？若 Q3 指定「必須使用 Python」但 §7.2 建議 Node.js，或 Q3 說「整合限制：現有系統為 .NET」但 §7.2 沒有提及此限制，視為 HIGH。
**Risk**: 技術建議與已知約束矛盾，EDD 撰寫者和開發團隊將收到相互衝突的指引，導致技術選型爭議或返工。
**Fix**: 以 Q3 約束為優先，修正 §7.2 使其與已知技術限制保持一致；若 AI 建議與約束不符，在 §7.2 明確說明「受 Q3 約束，建議改用 XXX」。

#### [HIGH] 20 — §8.1 風險矩陣少於 3 項，或缺乏法規風險
**Check**: §8.1 是否至少識別了 3 個不同類型的風險（市場/執行/技術/法規）？是否有至少 1 項法規或合規風險？若整個風險矩陣均為 `{{RISK_N}}` placeholder，或所有風險類型相同，視為 HIGH。
**Risk**: 風險識別不足，BRD §10 Risk Assessment 缺乏原始輸入；若法規風險未在 IDEA 階段識別，可能在 BRD 或 EDD 階段才被發現，導致計畫返工。
**Fix**: 補充至少 3 個不同類型的具體風險；確保至少 1 項為法規/合規風險（如隱私法、行業監管）；為每個風險填寫初步緩解策略。

#### [MEDIUM] 21 — §8.2 Kill Conditions 觸發閾值不可量化
**Check**: §8.2 的 Kill Conditions 每個條目是否有具體的量化觸發閾值（如「用戶訪談中 > 70% 不願付費」）？若觸發閾值為「不符合預期」「效果不好」等定性描述，視為 MEDIUM。
**Risk**: Kill Conditions 無量化閾值，在實際業務壓力下容易被理性化忽視（「還沒到 Kill 的地步」），無法做出及時的 Pivot 或 Kill 決策。
**Fix**: 為每個 Kill Condition 補充量化觸發閾值和具體的檢查時機（如「Discovery 完成後/Alpha 第 4 週」），確保閾值可被客觀衡量。

#### [LOW] 22 — §8.4 Pre-mortem 失敗情境缺少自定義場景（F6）
**Check**: §8.4 Pre-mortem 表格的最後一行（F6 或其他自定義場景）是否已填寫具體的失敗情境和預防措施？若 F6 行整行為 `{{CUSTOM_FAILURE_SCENARIO}}` 等 placeholder，視為 LOW。
**Risk**: Pre-mortem 未加入產品特定的失敗風險，依賴通用失敗模板，可能遺漏本產品最獨特的風險點。
**Fix**: 根據 §8.1 風險矩陣中評級最高的風險，補充一個產品特定的自定義失敗情境，包含根本原因、預防措施和早期預警訊號。

---

### Layer 6: 文件結構完整性（由 Technical Advisor 通盤掃描，共 2 項）

#### [HIGH] 23 — 裸 Placeholder 掃描（核心章節）
**Check**: 掃描以下核心欄位是否存在未替換的 `{{PLACEHOLDER}}` 格式字串：§1.1（Elevator Pitch）、§2.2（5 Whys 每一層）、§3.1（User_Role/User_Industry_Context）、§7.1（競品表至少一行）、§8.1（風險矩陣至少一行）、§14（Handoff Checklist C1/C3/C4）。逐一列出發現的裸 placeholder 及其位置。
**Risk**: 核心章節含裸 placeholder，BRD 生成器以 IDEA 作為輸入時將繼承這些 placeholder，導致 BRD 大量空白欄位，需要多輪額外補充。
**Fix**: 對每個裸 placeholder，依上下文推斷並填入具體值；若確實無法確定，以「（待定：[說明]）」替代 placeholder，而非保留雙大括號格式。

---

### Layer 7: 技術種子完整性（由 Technical Advisor 主審，共 2 項）

#### [HIGH] 25 — client_type 欄位缺失或為 TBD
**Check**: Document Control 的 `client_type` 欄位是否已由 gendoc-auto Step 1.8 填入具體值（非空白、非 TBD、非 placeholder）？
**Risk**: client_type 未確認，下游 PDD/EDD 無法判斷是否需要 client 端技術選型（web/mobile/game/api-only），導致架構設計遺漏或多做無用功。
**Fix**: 執行 gendoc-auto Step 1.8 確認 client_type 並填入；若為 api-only 需在 §7.2 說明無 client 端。

#### [HIGH] 26 — §7.2 服務角色識別表少於 2 個具名服務
**Check**: §7.2「服務角色識別」小表是否至少有 2 行具名服務（角色名非 `{{SERVICE_ROLE_N}}`，用途與建議技術均已填寫）？若整表為 placeholder 或缺少此子表，視為 HIGH。
**Risk**: 服務角色不明確，EDD 撰寫者無法從 IDEA.md 推導服務邊界，導致 EDD §3 服務架構設計從零推斷，增加遺漏風險。
**Fix**: 依 §1 Elevator Pitch 和 §7.1 競品分析，識別至少 2 個核心服務角色（如 API Gateway、Auth Service、Worker），填入角色名、用途、建議技術。

---

#### [LOW] 24 — §1.4 Innovation Type 未分類
**Check**: §1.4 Innovation Type Classification 表格是否已勾選恰好一個類型（Incremental / Sustaining / Adjacent / Disruptive / Radical），且「分類依據」欄位已填寫實質理由？若所有類型均未勾選，或分類依據為 `{{CLASSIFICATION_RATIONALE}}`，視為 LOW。
**Risk**: 未分類創新類型，資源投入策略（快速 ROI vs 長期實驗）無法在 BRD 階段獲得正確的期望校準，stakeholder 對投資時間表可能存在誤解。
**Fix**: 依照 IDEA 的實際定位勾選最匹配的創新類型，並在「分類依據」欄位說明關鍵理由（1–2 句話）。

---

### Layer 8: Q4 容量推估完整性（由 Technical Advisor 主審，共 3 項）

> **背景**：Q4 容量推估欄位（`q4_dau` / `q4_peak_ccu` / `q4_estimate_basis`）必須由 PM Expert 自動推算並寫入 state，**禁止以「小/中/大規模」選單詢問使用者**，因為架構設計統一採 HA（≥ 2 replica），不依賴規模選項。

#### [CRITICAL] 27 — §7.3 Q4 容量推估仍使用規模選項（小/中/大）
**Check**: §7.3 流量推估是否仍呈現「小規模（1–100 人）/ 中規模（100–10,000 人）/ 大規模（10,000 人以上）」這類規模分類選項？若有此類選項出現（無論是 placeholder 還是實際值），視為 CRITICAL（違反 HA-First 原則中「架構只有一種」的要求）。
**Risk**: 以規模選項決定架構，違反架構設計原則（架構從 Day 1 起統一 HA，規模只影響 HPA 閾值和 DB 連線池大小，不影響 replica 數）；下游 EDD/ARCH 生成器會錯誤地基於規模選擇輸出單副本方案。
**Fix**: 將 §7.3 改為 PM Expert 推算的 DAU / PCU / 推估依據三欄，並補充「以上數值僅供容量規劃，不影響架構選型（均採 HA 設計，≥ 2 replica）」說明。

#### [HIGH] 28 — §7.3 q4_dau / q4_peak_ccu / q4_estimate_basis 任一為空或 TBD
**Check**: §7.3 是否已填入具體的 `q4_dau`（日活用戶估算數字）、`q4_peak_ccu`（同時在線峰值數字）、`q4_estimate_basis`（推估依據說明）？若任一欄位為空、TBD、或仍為 `{{PLACEHOLDER}}`，視為 HIGH。
**Risk**: 容量推估欄位缺失，EDD 生成器無法進行 §10 效能規格的容量計算（HPA 閾值、DB 連線池大小、快取命中率目標），導致 EDD 中的容量規劃數字為空或不合理。
**Fix**: PM Expert 依 Web Research 競品數據推算並填入；即使是保守估算（如「參考同類競品 1% 市場份額」）也需填入具體數字，並在 `q4_estimate_basis` 欄位說明推算依據。

#### [MEDIUM] 29 — §7.3 q4_estimate_basis 推估依據僅有結論無來源
**Check**: `q4_estimate_basis` 是否說明了推算依據（引用具體競品名稱 + 公開數據 + 估算比例）？若僅有「根據市場研究」「AI 推算」等無可追溯的說明，視為 MEDIUM。
**Risk**: 推估依據不可追溯，EDD 審查者無法判斷 DAU/PCU 估算的合理性，無法質疑或調整容量規劃假設。
**Fix**: 補充具體推算過程（例如：「參考 Trello（MAU 5000 萬），目標市場 1% ≈ 50 萬 MAU，DAU 率 20% ≈ 10 萬 DAU；PCU 取 DAU 的 10% ≈ 1 萬」），確保可被 EDD 審查者理解和質疑。

---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/IDEA.md`，提取所有 `^## ` heading（含條件章節），共約 9 個
2. 讀取 `docs/IDEA.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
