# IDEA Document Template

<!-- SDLC Requirements Engineering — Layer 0：Idea Capture -->
<!-- 此文件是需求鏈的起點（IDEA → BRD → PRD → PDD → EDD），記錄最原始的構想輸入 -->
<!-- 由 /gendoc-auto 自動填寫；未來需求變更時，此文件作為「原始意圖」比對基準 -->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | IDEA-{{PROJECT_SLUG_UPPER}}-{{YYYYMMDD}} |
| **專案名稱** | {{PROJECT_NAME}} |
| **文件版本** | v0.1-capture |
| **狀態** | DRAFT ／ IN_REVIEW ／ APPROVED ／ SUPERSEDED |
| **作者** | {{AUTHOR}}（由 /gendoc-auto 自動生成） |
| **建立日期** | {{YYYY-MM-DD}} |
| **最後更新** | {{YYYY-MM-DD}} |
| **輸入模式** | {{多輪訪談 \| Quick Start \| AI 自動填入}} |
| **建立方式** | /gendoc-auto 自動捕捉；請執行 /reviewdoc brd 審查後方可升版 |
| **下游文件** | docs/BRD.md（由本文件產生） |
| **client_type** | {{web \| mobile \| both \| game \| api-only}}（由 gendoc-auto Step 1.8 確認填入） |

---

## 1. Idea Essence（核心本質）

### 1.1 一句話描述（Elevator Pitch）

> **{{PROJECT_NAME}} 幫助 {{TARGET_USERS}} 解決 {{CORE_PAINPOINT}}，方式是 {{SOLUTION_APPROACH}}。**

*寫法指引：遵循「幫助 [具體使用者] 達成 [具體目標]，方式是 [差異化做法]」句型。避免「讓事情更好」等模糊表達。*

---

### 1.2 核心假說（Lean Hypothesis）

> **If we build** {{SOLUTION_DESCRIPTION}},  
> **then** {{TARGET_USERS}}  
> **will** {{DESIRED_OUTCOME}},  
> **which will lead to** {{BUSINESS_RESULT}}.

*假說需可測試、可被推翻。若無法在 90 天內驗證，請拆分為更小的假說。*

---

### 1.3 成功願景（Success Vision）

**12 個月後，若本專案成功，以下情境將成真：**

- 用戶維度：{{USER_SUCCESS_SCENARIO}}
- 業務維度：{{BUSINESS_SUCCESS_SCENARIO}}
- 技術維度：{{TECH_SUCCESS_SCENARIO}}

### 1.4 Innovation Type Classification（創新類型分類）

| 類型 | 定義 | 是否適用 |
|------|------|:-------:|
| **Incremental**（漸進式）| 改善既有產品功能或流程效率 | ☐ |
| **Sustaining**（持續性）| 在既有市場中競爭，提供更好的解法 | ☐ |
| **Adjacent**（鄰近式）| 現有能力進入新市場或新用戶群 | ☐ |
| **Disruptive**（顛覆性）| 從低端或全新市場切入，重塑現有市場 | ☐ |
| **Radical / Breakthrough**（突破性）| 基於新技術或商業模式，創造新市場 | ☐ |

**本 IDEA 的分類**：{{INNOVATION_TYPE}}

**分類依據**：{{CLASSIFICATION_RATIONALE}}

*分類影響資源投入策略：Incremental/Sustaining 適合快速 ROI 路徑；Disruptive/Radical 需要更長實驗週期與更高風險容忍。*

---

## 2. Problem Statement（問題陳述）

### 2.1 現狀描述（As-Is Narrative）

{{CURRENT_STATE_DESCRIPTION}}

*說明目前使用者如何應對這個問題，包括現有的替代方案或臨時方法（workaround）。*

---

### 2.2 根本原因分析（5 Whys）

```
問題現象：{{PROBLEM_SYMPTOM}}
  Why 1：{{WHY_1}}
    Why 2：{{WHY_2}}
      Why 3：{{WHY_3}}
        Why 4：{{WHY_4}}
          Why 5（根本原因）：{{ROOT_CAUSE}} ← 我們要解決的是這個
```

*5 Whys 不一定每次都有 5 層，但必須找到系統性根因，而非只解決症狀。*

---

### 2.3 問題規模（量化估算）

| 指標 | 估算數字 | 資料來源 | 信心水準 |
|------|---------|---------|---------|
| 受影響使用者數（全球） | {{AFFECTED_USERS_GLOBAL}} | {{SOURCE}} | 低/中/高 |
| 受影響使用者數（目標市場） | {{AFFECTED_USERS_TARGET}} | {{SOURCE}} | 低/中/高 |
| 每人每週損失時間 | {{HOURS_LOST_PER_WEEK}} 小時 | 待用戶訪談驗證 | 低 |
| 每人每年成本損失 | {{COST_LOST_PER_YEAR}} | 待驗證 | 低 |
| 可定址市場規模（TAM） | {{TAM}} | {{SOURCE}} | 低 |
| 可服務市場規模（SAM） | {{SAM}} | {{SOURCE}} | 低 |
| 可獲取市場規模（SOM，預估 12 月） | {{SOM}} | AI 推斷 | 低 |

*以上數字為初始估算，需在 PRD 阶段的用戶研究後更新。*

---

## 3. Target Users（目標使用者）

### 3.1 主要使用者群（Q1 澄清結果）

**使用者描述**：{{Q1_USERS}}

| 屬性 | 描述 |
|------|------|
| 職業 / 角色 | {{USER_ROLE}} |
| 行業 / 情境 | {{USER_INDUSTRY_CONTEXT}} |
| 技術成熟度 | 初學 ／ 中階 ／ 進階 |
| 使用頻率 | 每日 ／ 每週 ／ 不定期 |
| 決策角色 | 使用者 ／ 採購者 ／ 推薦者 ／ 決策者 |

---

### 3.2 Jobs to Be Done（用戶核心任務）

| 任務類型 | 用戶任務描述 |
|---------|------------|
| **Functional**（功能性）| 當我 {{CONTEXT}}，我想要 {{ACTION}}，以便 {{OUTCOME}}。 |
| **Emotional**（情感性） | {{EMOTIONAL_JOB}} |
| **Social**（社交性） | {{SOCIAL_JOB}} |

---

### 3.3 非目標使用者（Not Our Users）

| 排除群體 | 排除原因 |
|---------|---------|
| ❌ {{EXCLUDED_GROUP_1}} | {{REASON_1}} |
| ❌ {{EXCLUDED_GROUP_2}} | {{REASON_2}} |

*明確定義「不服務誰」與「服務誰」同等重要，防止範圍無限擴張。*

---

## 4. Value Hypothesis（價值假說）

### 4.1 核心價值主張（Value Proposition Canvas）

**Pain Relievers（痛點緩解）：**

| 使用者痛點 | 我們的緩解方式 |
|-----------|-------------|
| {{PAIN_1}}（Q2：{{Q2_PAINPOINT}}） | {{RELIEF_1}} |
| {{PAIN_2}} | {{RELIEF_2}} |
| {{PAIN_3}} | {{RELIEF_3}} |

**Gain Creators（增益創造）：**

| 使用者期望收益 | 我們如何創造 |
|-------------|------------|
| {{GAIN_1}} | {{CREATOR_1}} |
| {{GAIN_2}} | {{CREATOR_2}} |

---

### 4.2 差異化定位

**相對現有解法（競品 / 替代方案），本產品的獨特差異：**

> {{DIFFERENTIATION_STATEMENT}}

*差異化必須真實存在且可持續，而非臨時性優勢。*

---

## 5. MVP & Learning Plan（最小可行驗證計畫）

### 5.1 MVP 邊界定義

> **MVP 的目的是驗證最關鍵的假設，而非交付完整產品。**

| MVP 功能 | 驗證假設 | 最低可接受標準 |
|---------|---------|--------------|
| {{MVP_FEATURE_1}} | {{ASSUMPTION_VALIDATED}} | {{SUCCESS_THRESHOLD}} |
| {{MVP_FEATURE_2}} | {{ASSUMPTION_VALIDATED}} | {{SUCCESS_THRESHOLD}} |
| {{MVP_FEATURE_3}} | {{ASSUMPTION_VALIDATED}} | {{SUCCESS_THRESHOLD}} |

**明確不在 MVP 範圍（Non-MVP）：**
- ❌ {{NON_MVP_1}}（推遲原因：{{REASON}}）
- ❌ {{NON_MVP_2}}（推遲原因：{{REASON}}）

---

### 5.2 Validation Metrics（驗證指標，Pre-BRD 階段）

*以下指標在 IDEA 驗證期間每週追蹤，達到閾值後方可升級為 BRD。*

| 指標 | 測量方式 | 通過閾值（Go）| 失敗閾值（Pivot/Kill）| 追蹤週期 |
|------|---------|:-----------:|:------------------:|---------|
| 問題確認率 | 用戶訪談：「您認為這是高優先問題嗎？」 | ≥ 70% 答「是」 | < 40% | 週 1–2 |
| 緊迫程度分數 | 1–5 量表問卷，N ≥ 10 | 平均 ≥ 3.5 | 平均 < 2.5 | 週 1–2 |
| 付費意願 | 願意付費的受訪者比例 | ≥ 40% | < 20% | 週 2–3 |
| 訪談完成數 | 完成深度訪談人數 | ≥ 10 人 | < 5 人 | 週 1–3 |
| 競品替代接受度 | 受訪者「願意從競品切換」比例 | ≥ 30% | < 15% | 週 2–3 |

**驗證計畫時程：**

```
Week 1：用戶招募（目標 N ≥ 15 人），完成問卷調查
Week 2：深度訪談（N ≥ 10），蒐集質化資料
Week 3：數據分析，決策：Go（生成 BRD）/ Pivot（修改 IDEA）/ Kill（停止）
```

---

### 5.3 Riskiest Assumption（最高風險假設，Leap of Faith）

> **以下假設一旦被推翻，整個 IDEA 必須根本性調整或放棄。**

**核心 Leap of Faith：**

> 我們假設 **{{LEAP_OF_FAITH_STATEMENT}}**。
> 若此假設為假，則 **{{CONSEQUENCE_IF_FALSE}}**，專案應 **{{PIVOT_OR_KILL}}**。
> 我們將透過 **{{VALIDATION_METHOD}}** 在 **{{VALIDATION_DEADLINE}}** 前驗證此假設。

| 假設 | 驗證方法 | 驗證期限 | 若錯誤的後果 |
|------|---------|---------|------------|
| {{LEAP_OF_FAITH_1}}（最高風險） | 訪談 / A/B / PoC / 市場測試 | {{DATE}} | 根本性 Pivot |
| {{LEAP_OF_FAITH_2}} | {{METHOD}} | {{DATE}} | 調整定位 |

*Leap of Faith ≠ 普通風險。它是整個商業邏輯成立的前提條件。*

---

## 6. Clarification Interview Record（澄清訪談記錄）

> 本節記錄 /gendoc-auto Step 2 互動提問的完整結果，是 BRD 各章節的原始輸入來源。

### Q1 — 主要使用者

| 欄位 | 內容 |
|------|------|
| **回答** | {{Q1_USERS}} |
| **選擇方式** | AI 推薦預設 ／ 使用者自行輸入 ／ Quick Start 自動推斷 |
| **影響範疇** | BRD §4 Stakeholders、PDD Persona、RTM 使用者欄位 |

---

### Q2 — 核心痛點

| 欄位 | 內容 |
|------|------|
| **回答** | {{Q2_PAINPOINT}} |
| **選擇方式** | AI 推薦預設 ／ 使用者自行輸入 ／ Quick Start 自動推斷 |
| **影響範疇** | BRD §2 Problem Statement、§5 Proposed Solution、§7 Success Metrics |

---

### Q3 — 技術限制或偏好

| 欄位 | 內容 |
|------|------|
| **回答** | {{Q3_TECH}} |
| **選擇方式** | 無特殊限制（AI 推薦）／ 指定技術 ／ 整合限制 ／ 自行輸入 |
| **影響範疇** | BRD §8 Constraints、EDD 技術選型、ARCH 架構設計 |

---

### Q4 — 預期使用規模

| 欄位 | 內容 |
|------|------|
| **回答** | {{Q4_SCALE}} |
| **選項** | 小規模（1–100 人）／ 中規模（100–10,000 人）／ 大規模（10,000 人以上）|
| **影響範疇** | ARCH 可擴展性設計、SCHEMA 分表策略、EDD 容量規劃 |

---

### Q5 — 其他補充說明（動態追問）

| 欄位 | 內容 |
|------|------|
| **回答** | {{Q5_EXTRA}}（若未追問填「無」） |
| **追問觸發原因** | {{FOLLOWUP_REASON}}（如：Q2 答案過於模糊） |
| **影響範疇** | {{AFFECTED_SECTIONS}} |

---

### 原始 IDEA（使用者輸入原文，逐字保留）

```
{{ORIGINAL_IDEA_VERBATIM}}
```

*保留原文供未來 ECR（Engineering Change Request）審查時比對，確認需求變更屬 BUG 修正還是範圍擴充。*

---

## 7. Market & Competitive Intelligence（市場與競品情報）

> 本節由 /gendoc-auto Step 3 WebSearch 自動蒐集，作為 BRD §6 的原始資料來源。

### 7.1 競品 / 參考資源

| 競品 / 工具 | 核心定位 | 優勢 | 劣勢 | 我們的差異 |
|-----------|---------|------|------|-----------|
| {{COMPETITOR_1}} | {{POSITIONING_1}} | {{STRENGTH_1}} | {{WEAKNESS_1}} | {{DIFF_1}} |
| {{COMPETITOR_2}} | {{POSITIONING_2}} | {{STRENGTH_2}} | {{WEAKNESS_2}} | {{DIFF_2}} |
| {{REFERENCE_3}} | {{POSITIONING_3}} | {{STRENGTH_3}} | — | 參考借鑒 |

---

### 7.2 技術生態建議

| 層次 | 建議方案 | 選擇理由 |
|------|---------|---------|
| 程式語言 / 框架 | {{TECH_LANG_FRAMEWORK}} | {{REASON}} |
| 資料庫 | {{TECH_DATABASE}} | {{REASON}} |
| 核心套件 / 服務 | {{TECH_PACKAGES}} | {{REASON}} |
| 基礎設施 | {{TECH_INFRA}} | {{REASON}} |

*技術建議基於 Q3（{{Q3_TECH}}）與 Q4（{{Q4_SCALE}}）。*

#### 服務角色識別

| 角色名 | 用途 | 建議技術 |
|--------|------|---------|
| {{SERVICE_ROLE_1}} | {{SERVICE_ROLE_1_PURPOSE}} | {{SERVICE_ROLE_1_TECH}} |
| {{SERVICE_ROLE_2}} | {{SERVICE_ROLE_2_PURPOSE}} | {{SERVICE_ROLE_2_TECH}} |

---

### 7.3 研究來源

| 搜尋關鍵字 | 主要發現 | 可信度 |
|-----------|---------|--------|
| {{SEARCH_QUERY_1}} | {{FINDING_1}} | 低/中/高 |
| {{SEARCH_QUERY_2}} | {{FINDING_2}} | 低/中/高 |
| {{SEARCH_QUERY_3}} | {{FINDING_3}} | 低/中/高 |

---

## 8. Initial Risk Assessment（初始風險評估）

### 8.1 風險矩陣

| # | 風險描述 | 類型 | 可能性 | 影響 | 風險等級 | 初步緩解策略 |
|---|---------|------|:------:|:----:|:------:|------------|
| R1 | {{RISK_1}}（來自研究） | 市場 | MEDIUM | HIGH | 🔴 HIGH | {{MITIGATION_1}} |
| R2 | {{RISK_2}} | 執行 | HIGH | MEDIUM | 🟡 MEDIUM | {{MITIGATION_2}} |
| R3 | {{RISK_3}} | 技術 | LOW | HIGH | 🟡 MEDIUM | {{MITIGATION_3}} |
| R4 | {{RISK_4}} | 法規 | MEDIUM | HIGH | 🔴 HIGH | {{MITIGATION_4}} |
| R5 | {{RISK_5}} | 競爭 | HIGH | MEDIUM | 🟡 MEDIUM | {{MITIGATION_5}} |

風險等級 = 可能性 × 影響：HIGH/HIGH = 🔴，其他組合 = 🟡 或 🟢。

---

### 8.2 Kill Conditions（專案終止條件）

*以下任一情況發生，應暫停或終止專案，避免繼續投入：*

| 終止條件 | 觸發閾值 | 檢查時機 |
|---------|---------|---------|
| 用戶驗證失敗 | 用戶訪談中 > 70% 目標用戶表示「不會付費或使用」 | Discovery 完成後 |
| 技術不可行 | 核心功能無法在可接受成本內實作 | PoC 完成後 |
| 競品搶先 | 直接競品以相同定位已獲得大量用戶 | BRD 審查後 |
| 法規阻礙 | 法務評估後無法在目標市場合法運營 | BRD 審查後 |

---

### 8.3 Dependencies & External Risks（依賴與外部風險）

| 依賴項 | 類型 | 關鍵性 | 若失效的影響 | 備援方案 |
|--------|------|:-----:|------------|---------|
| {{DEPENDENCY_1}} | 技術 / 市場 / 人員 | 高 / 中 / 低 | {{IMPACT_1}} | {{FALLBACK_1}} |
| {{DEPENDENCY_2}} | 技術 / 市場 / 人員 | 高 / 中 / 低 | {{IMPACT_2}} | {{FALLBACK_2}} |

*此處記錄影響 IDEA 成立的關鍵外部依賴（如核心 API 服務、關鍵合作夥伴、技術可行性驗證）。不同於 §8.1 的內部風險，本節聚焦於「我們無法完全控制」的外部因素。*

---

### 8.4 Pre-mortem Exercise（失敗前情境模擬）

> **想象 12 個月後，這個專案已徹底失敗。請列出最可能的失敗原因：**

| # | 失敗情境 | 根本原因 | 預防措施 | 早期預警訊號 |
|---|---------|---------|---------|-----------|
| F1 | 用戶雖有此問題，但緊迫度不足以促成付費 | 痛點評估過於樂觀 | Week 2 訪談驗證付費意願 | 訪談付費意願 < 30% |
| F2 | 競品快速跟進並以更低價格複製核心功能 | 差異化不夠深（技術/數據/網路效應） | 定義護城河（Moat）| 競品功能更新頻率加快 |
| F3 | 開發速度遠低於預期，市場時機窗口關閉 | 技術複雜度低估（{{Q3_TECH}}） | PoC 在 BRD 確認前完成 | PoC 超出 2 週仍未完成 |
| F4 | 用戶習慣改變困難，採用率低 | 替代成本（Switching Cost）過高 | 設計無縫遷移路徑 | 60 日留存率 < 40% |
| F5 | 法規變化使核心功能不合規 | 法規掃描不完整 | 法務提前介入（BRD 前） | 法規諮詢警告信號 |
| F6 | {{CUSTOM_FAILURE_SCENARIO}} | {{ROOT_CAUSE}} | {{PREVENTION}} | {{EARLY_WARNING}} |

**Pre-mortem 結論：** 最可能的失敗路徑是 **{{MOST_LIKELY_FAILURE}}**，需在 BRD 階段優先設計預防機制。

---

## 9. Business Potential（初步商業潛力）

### 9.1 商業模式假說

| 項目 | 初步假設 |
|------|---------|
| 收入來源 | {{REVENUE_MODEL}}（如 SaaS 訂閱 / 一次性授權 / 使用量計費 / 廣告） |
| 主要定價策略 | {{PRICING_STRATEGY}} |
| 主要成本驅動因子 | {{COST_DRIVERS}} |
| 核心資源 | {{KEY_RESOURCES}} |
| 獲客管道 | {{ACQUISITION_CHANNELS}} |

*以上為概念階段假設，需在 BRD §11 Business Model 中深化，PRD 中以用戶研究驗證。*

---

### 9.2 戰略對齊

| 公司策略目標 | 本 IDEA 的貢獻方式 | 對齊強度 |
|-----------|-----------------|---------|
| {{COMPANY_STRATEGY_1}} | {{CONTRIBUTION_1}} | 強 / 中 / 弱 |
| {{COMPANY_STRATEGY_2}} | {{CONTRIBUTION_2}} | 強 / 中 / 弱 |

---

## 10. Executive Sponsorship & Stakeholder Alignment（執行贊助與關鍵利害關係人對齊）

### 10.1 Executive Sponsor

| 欄位 | 內容 |
|------|------|
| **贊助人** | {{EXECUTIVE_SPONSOR_NAME}}（{{TITLE}}） |
| **贊助原因** | {{WHY_THIS_SPONSOR}}（與其策略目標的對應關係） |
| **授權範圍** | 預算上限 {{BUDGET_CEILING}}、決策自主範圍 {{DECISION_SCOPE}} |
| **核可日期** | {{SPONSOR_APPROVAL_DATE}} |
| **升級路徑** | 若遇阻礙，升級至 {{ESCALATION_CONTACT}} |

---

### 10.2 Stakeholder Pre-alignment Matrix

| 利害關係人 | 角色 | 對本 IDEA 的態度 | 主要顧慮 | 對齊策略 | 對齊期限 |
|-----------|------|:--------------:|---------|---------|---------|
| {{STAKEHOLDER_1}} | {{ROLE}} | 支持 / 中立 / 反對 | {{CONCERN}} | {{STRATEGY}} | {{DATE}} |
| {{STAKEHOLDER_2}} | {{ROLE}} | 支持 / 中立 / 反對 | {{CONCERN}} | {{STRATEGY}} | {{DATE}} |
| {{STAKEHOLDER_3}}（法務）| Legal | 中立 | 法規風險 | 提早法務審查 | BRD 前 |

---

### 10.3 Communication Plan（溝通計畫）

| 里程碑 | 溝通對象 | 溝通形式 | 期限 |
|--------|---------|---------|------|
| IDEA 核准 | Executive Sponsor | 1-pager + 口頭簡報 | {{DATE}} |
| BRD 完成 | All Stakeholders | 文件分享 + 審查會議 | {{DATE}} |
| PRD 核准 | Product + Engineering | Sprint Planning | {{DATE}} |

---

## 11. IDEA Quality Score（構想品質評分）

> 由 /gendoc-auto Step 5.5 自動計算，用於判斷是否具備開始 BRD 的條件。

**整體評分**：{{STAR_RATING}}（{{IDEA_SCORE}}/5）

| 評分維度 | 分數 | 評估說明 | 改進建議 |
|---------|:----:|---------|---------|
| 目標清晰度 | {{D1_SCORE}} / 1 | {{D1_COMMENT}} | {{D1_SUGGESTION}} |
| 使用者具體度 | {{D2_SCORE}} / 1 | {{D2_COMMENT}} | {{D2_SUGGESTION}} |
| 痛點可量化 | {{D3_SCORE}} / 1 | {{D3_COMMENT}} | {{D3_SUGGESTION}} |
| 範圍邊界明確 | {{D4_SCORE}} / 1 | {{D4_COMMENT}} | {{D4_SUGGESTION}} |
| 技術可行性初判 | {{D5_SCORE}} / 1 | {{D5_COMMENT}} | {{D5_SUGGESTION}} |

**評分解讀：**

| 分數 | 星等 | 含義 | 建議行動 |
|------|------|------|---------|
| 5 | ★★★★★ | 優質 IDEA，要素完整 | 直接生成 BRD，啟動 autodev |
| 4 | ★★★★☆ | 良好，微小缺漏 | 生成 BRD，審查後啟動 |
| 3 | ★★★☆☆ | 可行，需補充細節 | 補充 Q2/Q4 後生成 BRD |
| 2 | ★★☆☆☆ | 缺漏較多 | 建議深度用戶訪談後再生成 |
| 1 | ★☆☆☆☆ | 概念模糊，AI 大量推斷 | 需重新訪談，或分解 IDEA |

**本次評分說明：**

```
【IDEA 品質評分】{{STAR_RATING}}（{{IDEA_SCORE}}/5）
  {{DIMENSION_SUMMARY_LINE_1}}
  {{DIMENSION_SUMMARY_LINE_2}}
  {{DIMENSION_SUMMARY_LINE_3}}
```

---

## 12. Critical Assumptions（關鍵假設清單）

*假設是尚未被事實驗證的陳述。以下按「影響 × 不確定性」排序，影響最高者優先驗證。*

| # | 假設陳述 | 影響層級 | 不確定性 | 驗證方式 | 驗證期限 |
|---|---------|:-------:|:-------:|---------|---------|
| A1 | {{ASSUMPTION_1}}（基於 Q2 痛點） | HIGH | HIGH | 用戶訪談（N ≥ 10） | Discovery 週 2 |
| A2 | {{ASSUMPTION_2}}（基於 Q4 規模） | HIGH | MEDIUM | 數據分析 / 市場研究 | BRD 審查前 |
| A3 | {{ASSUMPTION_3}}（基於 Q3 技術） | MEDIUM | HIGH | PoC / 技術驗證 | EDD 完成前 |
| A4 | {{ASSUMPTION_4}} | MEDIUM | MEDIUM | A/B 測試 / 競品分析 | PRD 完成前 |

*A1 若假設錯誤，專案應終止或根本性調整方向。*

---

## 13. Open Questions（待解問題）

| # | 問題 | 影響層級 | 若不解決的後果 | 負責人 | 狀態 |
|---|------|:-------:|------------|--------|:----:|
| OQ1 | {{OPEN_QUESTION_1}} | 策略 | 可能需修改整體方向 | PM | 🔲 OPEN |
| OQ2 | {{OPEN_QUESTION_2}} | 範圍 | 影響 MVP 功能邊界 | Engineering | 🔲 OPEN |
| OQ3 | {{OPEN_QUESTION_3}} | 法規 | 可能影響上市時程 | Legal | 🔲 OPEN |

---

## 14. IDEA → BRD Handoff Checklist

> 以下所有項目確認後，方可執行 `/gendoc brd` 或啟動 `/gendoc-auto`。

| # | Checklist 項目 | 狀態 | 負責人 |
|---|--------------|:----:|--------|
| C1 | 一句話描述（§1.1）已清晰表達，無模糊詞 | 🔲 | PM |
| C2 | 核心假說（§1.2）符合可測試格式 | 🔲 | PM |
| C3 | Q1 使用者描述具體（非「所有人」） | 🔲 | PM |
| C4 | Q2 痛點已量化（時間 / 成本損失有初步估算） | 🔲 | PM |
| C5 | Q4 規模已選定（影響架構決策） | 🔲 | PM |
| C6 | 至少 1 個競品在 §7 已識別 | 🔲 | PM |
| C7 | 至少 3 項風險在 §8 已識別 | 🔲 | PM |
| C8 | Kill Conditions（§8.2）已定義 | 🔲 | PM |
| C9 | 關鍵假設 A1（§12）已識別並有驗證計畫 | 🔲 | PM |
| C10 | IDEA Quality Score ≥ 3 | 🔲 | AI 自動 |
| C11 | 原始 IDEA 原文已逐字保留（§6 末段） | 🔲 | AI 自動 |
| C12 | Open Questions 中無 P0 級別未解技術問題 | 🔲 | Engineering |

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

**需求變更判斷準則：**

| 場景 | 對比依據 | 分類 |
|------|---------|------|
| 功能行為與原始 IDEA Q1/Q2 一致但實作有誤 | IDEA §6 原文 | **BUG**（修正，不需 ECR） |
| 功能需求超出原始 Q1/Q2 描述範圍 | IDEA §6 原文 | **ECR**（需人工評估變更範圍） |
| 技術選型偏離 Q3 且理由不足 | IDEA §6 Q3 | **ECR 或 ADR**（需說明決策依據） |

---

## Appendix A：Research Raw Data（研究原始資料）

*以下為 /gendoc-auto Step 3 WebSearch 搜尋的完整原始摘要，供 BRD §0 引用。*

### 搜尋 1：競品與開源專案

```
查詢：{{SEARCH_1_QUERY}}
結果：
{{SEARCH_1_RESULTS}}
```

### 搜尋 2：技術最佳實踐

```
查詢：{{SEARCH_2_QUERY}}
結果：
{{SEARCH_2_RESULTS}}
```

### 搜尋 3：已知挑戰與陷阱

```
查詢：{{SEARCH_3_QUERY}}
結果：
{{SEARCH_3_RESULTS}}
```

---

## Appendix B：Document History

| 版本 | 日期 | 作者 | 修改摘要 |
|------|------|------|---------|
| v0.1-capture | {{DATE}} | /gendoc-auto | 初始捕捉，由 AI 自動填寫 |
| v0.2 | — | — | — |

---

*此 IDEA.md 由 /gendoc-auto 自動生成並保存。它記錄了需求探索過程的所有原始輸入、假設與品質評分，是未來 BUG vs ECR 判斷的一級依據。*

*未來需求發生變化時，請先閱讀本文件 §5（原始 IDEA 原文）與 §10（關鍵假設），確認變更是否超出原始意圖範圍。*
