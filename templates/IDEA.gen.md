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
| Q1 澄清結果（目標使用者） | 使用者族群、規模、核心需求 | §2 Target Users、§4 Problem Definition |
| Q2 澄清結果（痛點） | 痛點陳述、現有替代方案的不足 | §4 Problem Definition |
| Q3 澄清結果（限制條件） | 技術限制、預算、時間、法規 | §5 Constraints |
| Q4 澄清結果（規模） | 使用量、市場規模估算 | §3 Market Opportunity |
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
| Market Scale | Q4 澄清結果 | TAM/SAM 初步估算或定性描述 |
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

### §2 Target Users（目標使用者）
- 來自 Q1 澄清結果
- 描述使用者族群的 3-5 個特徵（職業/行為/環境/需求）
- 包含「不是我們的使用者」（明確排除群體，至少 1 條）
- 規模估算（定性或定量均可，但需說明依據）

### §3 Market Opportunity（市場機會）
- 來自 Q4 澄清結果 + Web Research
- TAM/SAM 初步估算（可為定性描述）
- 市場時機說明（趨勢驅動因素）

### §4 Problem Definition（問題定義）
- 來自 Q2 澄清結果
- As-Is Narrative（現狀工作流描述，含 workaround 行為）
- 問題的嚴重性評估（頻率 × 影響度）
- 與市場已有解法的不足說明

### §5 Constraints（已知限制）
- 來自 Q3 澄清結果
- 分類列出：技術限制、預算限制、時間限制、法規/合規限制
- 硬性限制（不可協商）vs. 軟性限制（可討論）需區分標注

### §6 Q1–Q5 澄清訪談記錄（完整保存）
- 原文保存 Q1-Q5 的問題與回答
- 禁止摘要或改寫——保留原始輸入
- 目的：作為後續 BRD/PRD 生成的可追溯原始資料

### §7 Market Intelligence（市場研究）
- 來自 Web Research 摘要
- **競品分析**：至少 2 個競品的優劣勢對比表
- **技術調研**：關鍵技術選項或趨勢
- **風險評估**：市場或技術層面已知風險

### §8 Initial Feature Hypotheses（初始功能假設）
- P0 必做功能（MVP 核心，不超過 5 項）
- P1 應該做功能
- P2 未來可考慮功能
- 每項功能附一句「假設驗證方式」

### §9 IDEA Quality Score（品質評分）
- 對照生成結果，自評各維度分數（1-5 分）
- 維度：問題清晰度、使用者明確度、差異化明確度、可行性、市場時機
- 若任一維度 ≤ 2，需在此節說明原因與補救方式

### §10 Risk & Kill Conditions（風險與終止條件）
- 至少 2 條明確的 Kill Conditions（觸發條件 + 觸發閾值）
- 例：「若 Pilot 期間 NPS < 20，終止開發」
- 禁止使用「若無市場需求」等模糊條件

### Handoff Checklist（移交清單）
- 確認以下事項已完成後，才可進行 BRD 生成：
  - [ ] Q1-Q5 澄清結果均已記錄
  - [ ] 競品分析已完成（≥ 2 個競品）
  - [ ] Kill Conditions 已定義（≥ 2 條）
  - [ ] docs/req/ 素材均已關聯至對應章節
  - [ ] IDEA Quality Score ≥ 3（所有維度）

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

---

## Self-Check Checklist（生成後自我審查）

生成完成後，逐項確認，有遺漏則自行補齊後再寫入檔案：

- [ ] 所有 templates/IDEA.md 中定義的章節均已生成
- [ ] DOC-ID 格式正確（IDEA-XXX-YYYYMMDD）
- [ ] §0 Input Source：輸入類型和素材清單已填寫
- [ ] §1 Idea Essence：Elevator Pitch 5 句已填寫（Who / Problem / Solution / Why Now / Differentiator）
- [ ] §2 Target Users：明確的使用者描述 + 「不是我們的使用者」
- [ ] §4 Problem Definition：As-Is Narrative 已填寫（非泛泛描述）
- [ ] §5 Constraints：硬性 / 軟性限制已區分
- [ ] §6 Q1-Q5：原始澄清結果已完整保存
- [ ] §7 Market Intelligence：競品分析表 ≥ 2 個競品
- [ ] §9 IDEA Quality Score：每個維度有分數（非空白）
- [ ] §10 Risk & Kill Conditions：Kill Conditions ≥ 2 條且具體可測
- [ ] Handoff Checklist：已填寫完畢
- [ ] Appendix C：docs/req/ 素材清單已列出所有引用檔案
- [ ] 全文無 "TBD"、"待補"、"N/A（無資料）" 等空白佔位
