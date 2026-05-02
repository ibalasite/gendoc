---
doc-type: IDEA
output-path: docs/IDEA.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義層，無上游文件）
quality-bar: "任何 PM 或工程師讀完 IDEA.md，5 分鐘內能說出：這個產品是給誰用的、解決什麼問題、為什麼現在要做、最大風險是什麼。"
---

# IDEA 生成規則

本檔案定義 `docs/IDEA.md` 的生成邏輯（需求鏈 Layer 0）。由 `/gendoc gen-idea` 讀取並遵循。
IDEA.md 的結構完全由 `templates/IDEA.md` 決定，本檔案僅定義內容生成規則。

---

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## Upstream Sources（上游文件對照表）

| 上游素材 | 提供資訊 | 對應 IDEA.md 章節 |
|---------|---------|-----------------|
| `docs/req/*.md / *.txt / *.pdf` | 產品原始構想、市場研究、競品資料、技術調研、使用者訪談紀錄 | 全章節（依 Appendix C 標記的應用範圍） |
| Q1 澄清結果（目標使用者） | 使用者族群、規模、核心需求 | §3 Target Users、§2 Problem Statement |
| Q2 澄清結果（痛點） | 痛點陳述、現有替代方案的不足 | §2 Problem Statement |
| Q3 澄清結果（限制條件） | 技術限制、預算、時間、法規 | §6 Clarification Interview Record |
| Q4 容量推估（PM Expert 自動推算） | DAU / 同時在線峰值（PCU）/ 推估依據 — 由 PM Expert 依競品研究自動寫入 state（`q4_dau` / `q4_peak_ccu` / `q4_estimate_basis`），不詢問使用者 | §7 Market Intelligence（§7.3 流量推估欄位）|
| Q5 澄清結果（補充資訊） | 其他關鍵背景資訊 | 各相關章節 |
| Web Research 摘要 | 競品分析、市場動態、技術建議 | §7 Market Intelligence（競品/技術章節）|

---

## Key Fields（關鍵欄位提取清單）

**必須填寫（不得留空或填 TBD）：**

| 欄位 | 資料來源 | 說明 |
|-----|---------|------|
| `DOC-ID` | 自動產生 | 格式：`IDEA-{PROJECT_NAME}-YYYYMMDD` |
| `PROJECT_NAME` | state / 使用者輸入 | 專案可讀名稱 |
| `PROJECT_TYPE` | state / 使用者輸入 | 產品類型（SaaS / App / API / Platform 等）|
| Elevator Pitch（5 句話） | Q1-Q5 + 輸入素材綜合推斷 | 必須包含：Who / Problem / Solution / Why Now / Key Differentiator |
| Target Users | Q1 澄清結果 | 使用者族群、規模估算 |
| Core Pain Points | Q2 澄清結果 | 具體痛點陳述，避免泛泛而談 |
| Constraints | Q3 澄清結果 | 硬性技術/法規/預算限制 |
| `q4_dau` | state（PM Expert 寫入）/ Web Research 推斷 | 日活用戶（DAU）估算，不得詢問使用者，由 PM Expert 依競品研究自動填入 |
| `q4_peak_ccu` | state（PM Expert 寫入）/ Web Research 推斷 | 同時在線峰值（PCU），同上，AI 推算後寫入 state |
| `q4_estimate_basis` | state（PM Expert 寫入）/ Web Research 推斷 | 推估依據說明（競品名稱 + 行業基準），同上 |
| Competitive Landscape | Web Research 摘要 | 至少 2 個競品的差異化描述 |
| Kill Conditions | PM Expert 推斷 | 明確觸發「放棄本專案」的條件（至少 2 條）|
| docs/req/ 素材清單 | docs/req/ 目錄掃描 | Appendix C 必須列出所有引用的素材檔案 |

---

## Section Rules（章節生成規則）

### Document Control
- `DOC-ID` 格式：`IDEA-{PROJECT_NAME大寫}-$(date +%Y%m%d)`
- `狀態` 初始填 `DRAFT`
- `作者` 填 `AI Generated (gendoc-gen-idea)`

### §0 Input Source（輸入素材說明）
- 說明本次 IDEA.md 的輸入類型（text_idea / file_upload / url / voice 等）
- 列出 docs/req/ 中所有被讀取的素材檔案名稱
- 若無任何 docs/req/ 素材，標注「依 Q1-Q5 澄清直接生成」

### §1 Idea Essence（核心概念）
- **必須**包含 Elevator Pitch 5 句話結構：
  1. Who（目標使用者是誰）
  2. Problem（他們面對什麼問題）
  3. Solution（我們如何解決）
  4. Why Now（為什麼現在是時機）
  5. Key Differentiator（與現有方案的核心差異）
- 禁止使用模糊詞語（如「更好的體驗」「創新方案」）—— 必須具體、可驗證
- §1.2 核心假說（Lean Hypothesis）：填寫「我們相信 [目標使用者] 若能 [我們提供的解決方案]，將能 [實現什麼目標]，我們知道成功當 [驗證指標]」
- §1.3 成功願景：3 年後這個產品成功了，世界會有什麼不同？（1-2 段）
- §1.4 Innovation Type：選擇並說明創新類型（Disruptive / Sustaining / Efficiency）

### §2 Problem Statement（問題陳述）
- 來自 Q2 澄清結果
- §2.1 As-Is Narrative：現狀工作流描述（含 workaround 行為、痛點發生頻率）
- §2.2 根本原因分析（5 Whys）：連續追問 5 個「為什麼」找出根本原因
- §2.3 問題規模：頻率 × 影響度 = 優先程度，含量化估算或定性說明
- 禁止泛泛描述——必須引用 Q2 原文或 docs/req/ 素材

### §3 Target Users（目標使用者）
- 來自 Q1 澄清結果
- §3.1 主要使用者群：描述使用者族群的 3-5 個特徵（職業/行為/環境/需求）
- §3.2 Jobs to Be Done：使用者要完成的核心任務（至少 3 個）
- §3.3 非目標使用者：明確排除群體（至少 1 條）+ 排除原因
- 規模估算（定性或定量均可，但需說明依據）

### §4 Value Hypothesis（價值假說）
- §4.1 核心價值主張（Value Proposition Canvas）：填寫「對 [目標使用者]，[產品名] 是一個 [解決方案類型]，能夠 [核心價值]，不像 [替代方案]，我們 [差異化優勢]」
- §4.2 差異化定位：與至少 2 個競品或替代方案的對比（優勢 / 劣勢各列）
- 禁止使用「全方位解決方案」「業界最佳」等模糊聲明

### §5 MVP & Learning Plan（最小可行驗證計畫）
- §5.1 MVP 邊界定義：P0 必做功能（不超過 5 項，每項附假設驗證方式）
  - P1 應該做功能（可延後）
  - P2 未來可考慮功能
- §5.2 Validation Metrics：驗證成功的可量化指標（至少 3 個，含目標數值）
- §5.3 Riskiest Assumption：最高風險假設（Leap of Faith），並說明如何用 MVP 驗證它

### §6 Clarification Interview Record（澄清訪談記錄）
- 原文保存 Q1-Q5 的問題與回答（含技術限制、預算、時間、法規等限制條件）
- 禁止摘要或改寫——保留原始輸入
- 目的：作為後續 BRD/PRD 生成的可追溯原始資料

### §7 Market & Competitive Intelligence（市場與競品情報）
- 來自 Q4 澄清結果 + Web Research 摘要
- §7.1 競品 / 參考資源：至少 2 個競品的優劣勢對比表（功能、定價、市場份額）
- §7.2 技術生態建議：關鍵技術選項或趨勢（依 docs/req/ 素材或 Web Research）
- §7.3 研究來源：列出所有引用的市場資料來源
- TAM/SAM 初步估算（可為定性描述）+ 市場時機說明（趨勢驅動因素）

### §8 Initial Risk Assessment（初始風險評估）
- §8.1 風險矩陣：列出已知風險（可能性 × 影響度），至少 3 條
- §8.2 Kill Conditions：至少 2 條明確的專案終止條件（觸發條件 + 觸發閾值）
  - 例：「若 Pilot 期間 NPS < 20，終止開發」
  - 禁止使用「若無市場需求」等模糊條件
- §8.3 Dependencies & External Risks：外部依賴（第三方 API、法規、合作夥伴）風險
- §8.4 Pre-mortem：若 1 年後此專案失敗，最可能的失敗原因是什麼？（至少 2 條）

### §9 Business Potential（初步商業潛力）
- §9.1 商業模式假說：初步推斷的獲利方式（訂閱 / 廣告 / 交易抽成 / 授權等）
- §9.2 戰略對齊：與公司現有產品線或戰略方向的關聯說明
- 若商業模式尚不明確，標注「商業模式 TBD，由 BRD 定義」並說明暫緩原因

### §10 Executive Sponsorship & Stakeholder Alignment（執行贊助與利害關係人對齊）
- §10.1 執行贊助人：填寫負責人姓名（若未知，填「TBD — 由 BRD 釐清」）
- §10.2 Stakeholder Pre-alignment Matrix：關鍵利害關係人清單（角色 / 訴求 / 對齊狀態）
- §10.3 Communication Plan：如何定期向利害關係人報告進度（頻率 / 格式）

### §11 IDEA Quality Score（品質評分）
- 對照生成結果，自評各維度分數（1-5 分）
- 維度：問題清晰度、使用者明確度、差異化明確度、可行性、市場時機
- 若任一維度 ≤ 2，需在此節說明原因與補救方式

### §12 Critical Assumptions（關鍵假設清單）
- 列出本 IDEA 成立的所有前提假設（至少 3 條）
- 每條附：假設描述 / 驗證方法 / 驗證時間點
- 標注優先驗證順序（最不確定且影響最大的先驗證）

### §13 Open Questions（待解問題）
- 列出尚未解答、需在 BRD 或 PRD 階段釐清的問題
- 格式：問題描述 / 負責人 / 期限

### §14 IDEA → BRD Handoff Checklist（移交清單）
- 確認以下事項已完成後，才可進行 BRD 生成：
  - [ ] Q1-Q5 澄清結果均已記錄（§6）
  - [ ] 競品分析已完成（≥ 2 個競品，§7）
  - [ ] Kill Conditions 已定義（≥ 2 條，§8.2）
  - [ ] docs/req/ 素材均已關聯至對應章節
  - [ ] IDEA Quality Score ≥ 3（所有維度，§11）
  - [ ] Critical Assumptions 已列出（≥ 3 條，§12）

### §15 Traceability Note（溯源說明）
- 說明本 IDEA.md 與原始輸入素材（docs/req/）的對應關係
- 列出哪些章節來自哪個素材檔案（格式：§章節 ← docs/req/檔案名）
- 目的：確保 BRD/PRD 生成時可追溯回最原始的使用者輸入

### Appendix C（素材清單）
- 列出所有引用的 docs/req/ 素材
- 格式：表格，欄位包含：檔案路徑 / 素材類型 / 應用於（對應章節）
- 若無 docs/req/ 素材，標注「無外部素材，依 Q1-Q5 直接生成」

---

## Inference Rules（推斷規則）

1. **Q1-Q5 缺失時**：依 docs/req/ 素材內容推斷，並在對應章節標注「推斷自素材：{檔案名}」
2. **Web Research 缺失時**：依輸入素材中提及的競品名稱進行靜態分析，並標注「無即時 Web Research，以下為靜態推斷」
3. **docs/req/ 素材缺失時**：完全依賴 Q1-Q5 澄清結果生成，不可因缺少素材而降低任何章節的覆蓋深度
4. **PROJECT_NAME 缺失時**：依 Elevator Pitch 的產品名稱或輸入素材的標題推斷
5. **Q4 容量推估（強制 PM Expert 推算，禁止詢問使用者）**：
   - `q4_dau`、`q4_peak_ccu`、`q4_estimate_basis` 三個欄位**必須由 PM Expert 從 Web Research 結果和競品數據推算**，寫入 state 後直接顯示在 §7.3，不得詢問使用者選擇「小/中/大規模」
   - 若 state 中已有這三個欄位，直接引用；若無，PM Expert 依競品研究推算後填入
   - 推算方式：找 1-2 個同類競品的公開 MAU/DAU 數據，估算本專案在 1 年內可能達到的 DAU 比例（例如：「參考 Notion（1000 萬 DAU），保守估算本專案初期達到 1% ≈ 10 萬 DAU」）
   - 這些數值僅供 EDD 容量規劃使用，**不影響架構選型**（架構統一採 HA 設計，≥ 2 replica）

---

## Self-Check Checklist（生成後自我審查）

生成完成後，逐項確認，有遺漏則自行補齊後再寫入檔案：

- [ ] 所有 templates/IDEA.md 中定義的章節均已生成
- [ ] DOC-ID 格式正確（IDEA-XXX-YYYYMMDD）
- [ ] §0 Input Source：輸入類型和素材清單已填寫
- [ ] §1 Idea Essence：Elevator Pitch 5 句已填寫（Who / Problem / Solution / Why Now / Differentiator）
- [ ] §2 Problem Statement：As-Is Narrative 已填寫（非泛泛描述）
- [ ] §3 Target Users：明確的使用者描述 + 「不是我們的使用者」
- [ ] §4 Value Hypothesis：差異化定位（對比 ≥ 2 個競品）
- [ ] §5 MVP & Learning Plan：P0 功能 ≤ 5 項，每項有假設驗證方式
- [ ] §6 Clarification Interview Record：Q1-Q5 原始澄清結果已完整保存
- [ ] §7 Market Intelligence：競品分析表 ≥ 2 個競品
- [ ] §8 Initial Risk Assessment：Kill Conditions ≥ 2 條且具體可測
- [ ] §11 IDEA Quality Score：每個維度有分數（非空白）
- [ ] §12 Critical Assumptions：關鍵假設 ≥ 3 條
- [ ] §14 Handoff Checklist：已填寫完畢
- [ ] Appendix C：docs/req/ 素材清單已列出所有引用檔案
- [ ] 全文無 "TBD"、"待補"、"N/A（無資料）" 等空白佔位
- [ ] client_type 已填入（非 TBD）
- [ ] §7.2 服務角色表至少 2 項

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| 所有 §章節齊全 | 對照 IDEA.md 章節清單，無缺失章節 | 補寫缺失章節 |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 目標用戶具體 | 目標用戶描述非「所有人」「一般使用者」，至少含職業/行為/痛點三個維度 | 從輸入素材提取並具體化 |
| 數值非 TBD/N/A | 市場規模、競品數量、目標用戶數有實際估算數字 | 從 web research 結果或輸入資料推算 |
| 痛點明確 | 至少 3 個具體的使用者痛點（非泛泛的「效率低」「不方便」） | 從輸入素材提取或從競品分析推斷 |
| 差異化優勢 | 至少 2 個與現有競品的明確差異點 | 從 web research 的競品分析結果提取 |
| 服務角色表非空 | §7.2 服務角色識別表至少 2 個具名服務（非裸 placeholder） | 補全服務角色名、用途、建議技術 |
