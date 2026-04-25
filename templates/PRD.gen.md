---
doc-type: PRD
output-path: docs/PRD.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA.md Appendix C 引用）
  - docs/IDEA.md    # 需求鏈 Layer 0（產品概念、目標市場、功能假設）
  - docs/BRD.md     # 需求鏈 Layer 1（業務目標、MoSCoW、成功指標、限制）
quality-bar: "任何工程師或設計師讀完 PRD.md，不需問任何人，能獨立判斷：這個功能要做什麼、做到什麼程度算完成、邊界條件如何處理、資料如何儲存與保護。"
---

# PRD 生成規則

本檔案定義 `docs/PRD.md` 的生成邏輯（需求鏈 Layer 2）。由 `/gendoc gen-prd` 讀取並遵循。
PRD.md 的結構完全由 `templates/PRD.md` 決定，本檔案僅定義內容生成規則。

---

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## Upstream Sources（上游文件對照表）

| 上游文件 | 提供資訊 | 對應 PRD 章節 |
|---------|---------|-------------|
| `docs/IDEA.md §1` | 產品核心概念、Elevator Pitch | §1 Executive Summary |
| `docs/IDEA.md §2` | Target Users | §3 Stakeholders & Users（Persona 基礎）|
| `docs/IDEA.md §4` | Problem Definition | §2 Problem Statement |
| `docs/IDEA.md §5` | Constraints | §8.1 已知限制 |
| `docs/IDEA.md §8` | Initial Feature Hypotheses | §4 Scope（功能範圍初始邊界）|
| `docs/BRD.md §2` | As-Is Narrative / 5 Whys | §2 Problem Statement |
| `docs/BRD.md §3.1` | SMART 目標（含 KPI）| §7 NFR（具體數字）、§9 Success Metrics |
| `docs/BRD.md §3.4` | RTM（業務目標 → 成功指標）| §15 RTM（繼承並擴充）|
| `docs/BRD.md §4.1` | Target Users | §3 Stakeholders & Users（Persona）|
| `docs/BRD.md §4.4` | RACI Matrix | §3 Stakeholder Map |
| `docs/BRD.md §5.3` | MoSCoW 功能清單（P0/P1/P2/Out）| §4 Scope、§5 User Stories |
| `docs/BRD.md §7.1` | North Star 指標 | §9.1 北極星 |
| `docs/BRD.md §7.2` | 業務指標階層 | §9.2 Guardrail Metrics |
| `docs/BRD.md §8.1` | 限制表 | §8.1 Constraints |
| `docs/BRD.md §8.2` | 假設驗證矩陣 | §8.4 Assumptions |
| `docs/BRD.md §9.1` | 法規 / 標準 | §17 Privacy by Design |
| `docs/BRD.md §9.5` | Data Governance（含 PII）| §11.4 PII 欄位清單、§17 |
| `docs/BRD.md §10` | Risk Assessment | §8.1 Constraints（高影響風險轉化）|
| `docs/BRD.md §11` | Business Model | §9 Success Metrics（收入指標）|
| `docs/BRD.md §13` | Dependencies + Vendor Risk | §8.3 外部依賴 |
| `docs/req/*.md/txt` | 原始素材（Appendix C 應用欄標有「PRD §」的部分）| 對應 §5 User Story / §7 NFR / AC |

---

## Key Fields（關鍵欄位提取清單）

**必須從上游文件提取（不得留空或填 TBD）：**

| 欄位 | 上游來源 | 說明 |
|-----|---------|------|
| `DOC-ID` | 自動產生 | 格式：`PRD-{PROJECT_SLUG大寫}-YYYYMMDD`（例：`PRD-MYAPP-20260420`）|
| 上游 BRD 章節引用 | BRD Document Control | 格式：`BRD.md §{{BRD_SECTION}}`（具體章節號）|
| User Stories | BRD §5.3 MoSCoW（P0/P1/P2）| 每個 In Scope 功能都必須有對應 User Story |
| REQ-ID | 自動產生 | 格式：`US-{FEATURE_CODE}-{NNN}`（FEATURE_CODE 為 2-4 個大寫英文）|
| Persona | BRD §4.1 Target Users | 至少 1 個 Persona 卡片 |
| NFR 數字 | BRD §3.1 SMART KPI | 效能 / 可用性 / 安全等具體數字（不允許「系統應該很快」）|
| North Star | BRD §7.1 | 一個最能代表核心價值的指標 |
| PII 欄位清單 | BRD §9.5 Data Governance | 所有涉及個人資料的欄位 |

---

## Section Rules（章節生成規則）

### Document Control
- `DOC-ID` 格式：`PRD-{PROJECT_SLUG大寫}-YYYYMMDD`
- 上游 BRD 章節引用：`BRD.md §{{BRD_SECTION}}`（具體對應章節號）
- `狀態` 初始填 `DRAFT`

### Change Log
- 第一筆記錄：| v0.1 | YYYYMMDD | AI Generated (gendoc-gen-prd) | 初始生成 |

### §1 Executive Summary
- 來自 IDEA.md §1 Elevator Pitch + BRD §1 Executive Summary 精煉
- 一段式說明：Product Vision + 核心問題 + 解決方案 + 目標使用者

### §2 Problem Statement
- 來自 BRD §2 Problem Statement（As-Is Narrative + 5 Whys 精煉）
- 聚焦工程師視角：「我們要解決什麼問題，為什麼這樣解決」
- **§2.4 System Context Diagram**（必要，Mermaid C4Context 格式）：
  ```mermaid
  C4Context
      title <系統名稱> — System Context
      Person(user, "<主要用戶類型>", "<用戶描述>")
      System(system, "<系統名稱>", "<一句話系統描述>")
      System_Ext(extA, "<外部系統 A>", "<用途>")
      System_Ext(extB, "<外部系統 B>", "<用途>")
      Rel(user, system, "Uses", "HTTPS")
      Rel(system, extA, "Calls", "REST API")
      Rel(system, extB, "Reads from", "SQL")
  ```
  - 依 BRD §13 Dependencies 中提及的外部系統，動態生成 `System_Ext` 節點
  - 每個節點有真實的系統名稱與用途描述

### §3 Stakeholders & Users

**Persona 卡片**（至少 1 個，依 BRD §4.1 Target Users 生成）：
```
姓名：[Persona 名稱]
職業/背景：[職業]
年齡：[範圍]
Goals：[主要目標 2-3 條]
Frustrations：[主要痛點 2-3 條]
Scenario：[典型使用場景一段描述]
```

**Stakeholder Map**：來自 BRD §4.3，列出各利害關係人與關注點

### §4 Scope

- **In Scope（P0）**：來自 BRD §5.3 Must Have，MVP 必做
- **In Scope（P1）**：來自 BRD §5.3 Should Have，Phase 2
- **In Scope（P2）**：來自 BRD §5.3 Could Have，未來版本
- **Out of Scope**：來自 BRD §5.3 Won't Have，明確重申排除項目 + 排除原因
- **Future Scope**：未來可能的延伸方向（非承諾）
- **MoSCoW 表**：功能清單與優先度的結構化對照

### §5 User Stories & Acceptance Criteria

**每個功能的必要元素**（每個 BRD In Scope 功能都必須有對應項）：

```markdown
### [功能名稱]（P0 / P1 / P2）

**REQ-ID：** US-<FEATURE_CODE>-<NNN>（對應 BRD §<N>）

**User Story：**
> 作為 [角色]，我希望 [功能]，以便 [目的]。

**驗收標準（AC）：**

| REQ-ID / AC# | 驗收條件 | 測試方法 |
|-------------|---------|---------|
| US-<CODE>-<N> / AC-1 | [具體、可測試、數字化的條件] | 自動化測試/手動測試 |
| US-<CODE>-<N> / AC-2 | [錯誤路徑的預期行為] | 自動化測試/手動測試 |
| US-<CODE>-<N> / AC-3 | [邊界條件的預期行為] | 自動化測試/手動測試 |

**邊界條件：**
- 正常流程：...
- 空值/最大值：...
- 並發操作：...（若適用）
```

**REQ-ID 編號規則**：
- `FEATURE_CODE`：功能縮寫（2-4 個英文大寫字母，如 `AUTH`、`PAY`、`NOTIF`）
- `NNN`：同功能下的流水號（001, 002, …）
- 每個 User Story 至少 2 個 AC（正常路徑 + 錯誤路徑）

### User Story Activity Diagram 連結規則

每個 P0/P1 User Story 在生成時，必須在其描述中加入對應的 Activity Diagram 連結欄位：
- 連結格式：`[activity-{flow-name}.md](../docs/diagrams/activity-{flow-name}.md)`
- `{flow-name}` 從 User Story 的動詞+名詞推斷（kebab-case，如 `user-login`、`create-order`、`process-payment`）
- 若 `docs/diagrams/` 目錄下還未有對應 Activity Diagram，標注「[待生成：/gendoc-gen-diagrams]」
- 每個 P0 User Story 必須有活動圖連結；P1 建議有；P2 可選

### §6 User Flows

**必須包含三種 Mermaid 圖**：

1. **Happy Path**（使用者成功完成核心任務的流程）
2. **Error Flow**（關鍵錯誤場景的處理流程）
3. **State Machine**（系統關鍵狀態與轉換條件）

每種圖各以 Mermaid flowchart 或 stateDiagram-v2 格式呈現。若使用 `stateDiagram-v2`，**禁止** 在 transition label 使用 `<br/>`（Safari/Firefox 破圖）；換行說明移到 `note right of STATE` 區塊。

### §7 Non-Functional Requirements（NFR）

**所有 NFR 必須有具體數字，禁止模糊描述。**

**§7.1 性能**：
- API 回應時間：`P99 < Xms @ Y RPS`（數字來自 BRD §3.1 KPI）
- 頁面載入時間：`FCP < Xs, LCP < Xs`

**§7.2 安全**：
- 認證 / 授權要求（具體機制）
- 資料加密要求（傳輸 + 靜態）
- 來自 BRD §9 Regulatory 的安全要求

**§7.3 可用性**：
- `SLA N%`（數字來自 BRD §3.1）
- 維護視窗定義

**§7.4 擴展性**：
- `支援 N 倍流量增長，無需重構`（基準流量 + 擴展倍數）

**§7.5 維護性**：
- 程式碼覆蓋率要求、部署頻率目標

**§7.6 國際化**：
- 支援語系清單、時區處理、日期格式

**§7.7 Observability（可觀測性）**：

Logging 規格：
- 格式：結構化 JSON，含 `timestamp`, `level`, `service`, `trace_id`, `user_id`（遮罩）
- 必記錄：所有 API 請求/回應、業務關鍵事件、認證事件
- 日誌等級：生產環境 INFO，異常時升 WARN/ERROR

Metrics 必須項目：

| 指標 | 類型 | 量測方式 | 告警閾值 |
|------|------|---------|---------|
| API 回應時間 P99 | Histogram | APM | > 1s |
| 錯誤率 | Counter | APM | > 1% |
| 可用性 | Gauge | Health Check | < 99.9% |
| 業務 KPI 達成率 | Gauge | 業務事件計算 | < 目標 80% |

（業務 KPI 達成率一欄依 BRD 北極星指標具體化為業務指標名稱）

Tracing 需求：
- 所有跨服務呼叫帶 `trace_id`（W3C TraceContext）
- Sampling Rate：生產環境 10%，異常時升至 100%

Dashboard 要求：
- 即時運營 Dashboard（P99 延遲、錯誤率、活躍用戶）
- 業務 KPI Dashboard（北極星指標、轉換漏斗）

**§7.8 Analytics Event Instrumentation Map**：

| Event 名稱 | 觸發時機 | 對應功能 | 關鍵屬性 | 分析用途 |
|-----------|---------|---------|---------|---------|
| | | | | |

- 每個功能（§5 User Stories）至少 1 個 Analytics Event
- Event 名稱採 `snake_case`

### §8 Constraints & Dependencies

**§8.1 Constraints**：來自 IDEA.md §5 + BRD §8.1，區分硬性 / 軟性

**§8.2 技術依賴**：列出主要技術棧依賴與版本要求

**§8.3 外部依賴**：來自 BRD §13 Dependencies，列出第三方服務與 SLA 要求

**§8.4 關鍵假設（Assumptions）**：

> 假設是「我們相信為真但尚未驗證的事項」；Constraints 是「已知的硬性限制」。兩者必須嚴格區分。

| # | 假設 | 若假設錯誤的風險 | 驗證方式 | 驗證截止日 | 負責人 |
|---|------|----------------|---------|-----------|--------|
| A1 | [來自 BRD §8.2 業務假設] | HIGH/MEDIUM/LOW | | | PM |
| A2 | [技術假設，如第三方 API SLA] | HIGH | SLA 合約確認 | 開發前 | Engineering |
| A3 | [用戶行為假設] | MEDIUM | A/B Test | Beta 期間 | PM |

生成規則：
- 至少 3 條假設（依 BRD §8.2 假設驗證矩陣擴充）
- 技術假設（外部依賴 SLA）至少 1 條
- 業務假設（用戶行為、市場前提）至少 1 條
- 若假設錯誤風險為 HIGH，驗證截止日必須排在開發啟動前

**§8.5 向後相容性宣告**：

| 欄位 | 內容 |
|------|------|
| **Breaking Change** | 是 / 否 |
| **受影響 API 版本** | [版本號 或 N/A] |
| **Deprecation Timeline** | [舊版本停止支援日期 或 N/A] |
| **Migration Guide 責任** | [負責方 + 完成時間 或 N/A] |
| **向下相容保障期** | [N 個月 或 N/A（全新產品）] |

若 BRD 為全新產品（無既有版本），`Breaking Change` 填「否」，其餘填「N/A」。

### §9 Success Metrics & Launch Criteria

**§9.1 北極星指標**：來自 BRD §7.1，一個最能代表核心價值的指標

**§9.2 Guardrail Metrics**：
- 不得惡化的指標（負向護欄）
- 每個 Guardrail 有具體閾值

**§9.3 Go-No-Go Launch Criteria**：
- 明確列出上線決策標準（達到什麼條件才能 GA）
- 每條標準有可量化的數字門檻

**§9.4 A/B Test Plan**（若適用）：

| 實驗名稱 | 假說 | 對照組 | 實驗組 | 主要指標 | Guardrail Metrics | 最小樣本量 | 持續時間 |
|---------|------|-------|-------|---------|-----------------|-----------|---------|

**§9.5 Definition of Done（DoD）**：

Product DoD：

| # | 條件 | 負責方 |
|---|------|--------|
| | | PM |

Engineering DoD：

| # | 條件 | 負責方 |
|---|------|--------|
| | 單元測試覆蓋率 ≥ 80% | Engineering |
| | 所有 P0 AC 自動化測試通過 | QA |
| | 無 P0 Bug | QA |
| | Security Review 通過 | Security |
| | Performance Benchmark 達標 | Engineering |

### §10 Rollout Plan

分階段上線計畫：

| 階段 | 名稱 | 目標用戶 | 持續時間 | 成功指標 | 退出條件 |
|------|------|---------|---------|---------|---------|
| Alpha | 內測 | 內部員工 | X 週 | | |
| Beta | 封閉測試 | X% 真實用戶 | X 週 | | |
| GA | 全面上線 | 所有用戶 | — | | |

**§10.2 Feature Flag 規格**：

| Flag 名稱 | 預設值 | 目標群組 | 啟用條件 | Kill Switch | 管理工具 | 預計移除日 |
|-----------|--------|---------|---------|------------|---------|-----------|
| `<feature_flag_name>` | OFF | [用戶群] | [啟用條件] | 是（立即關閉）| [LaunchDarkly / GrowthBook / 待確認] | GA + 2 週 |

Flag 管理原則：
- 所有 P0 功能必須有 Kill Switch Feature Flag（Flag 名稱採 `snake_case`）
- P1 功能若有風險（影響核心流程），亦建議加 Flag
- Flag 在功能穩定 GA 後 2 週內移除（避免 Flag debt）
- Flag 狀態變更需記錄在 Decision Log
- 若 BRD 未提及具體技術棧，管理工具預設填「待 Engineering 確認」

### §11 Data Requirements

**§11.1 新增資料需求**：

| 資料表/欄位 | 操作 | 理由 | 關聯 PRD 功能 |
|-----------|------|------|--------------|
| [table_name] | 新增 | [業務理由] | §5.[N] |

生成規則：依 BRD 業務流程推斷所需資料表與欄位（至少列出核心實體）

**§11.2 Data Dictionary**：

| 欄位名稱 | 型別 | 長度/精度 | 必填 | 說明 | 範例值 | PII |
|---------|------|---------|------|------|--------|-----|

**§11.3 資料品質要求**：
- 完整性：[必填欄位完整率，如 ≥ 99.5%]
- 準確性：[資料準確率要求]
- 時效性：[資料更新頻率]
- 唯一性：[唯一鍵約束說明]

**§11.4 PII 欄位清單**：

| 欄位 | PII 類型 | 處理方式 | 保留期限 |
|------|---------|---------|---------|
| [欄位名] | [姓名/Email/電話等] | 加密儲存 + Log 遮罩 | [N 年後刪除] |

- 凡涉及用戶個資（姓名、Email、電話、地址、IP 等）必須標記 PII 並填入此表
- PII 保留期限依所在地區個資法規（預設：臺灣個資法 → 依業務需求最短保留）

### §12 Open Questions

至少 2 項影響策略方向的未解問題：

| # | 問題 | 影響範圍 | 影響層級（高/中/低）| 負責人 | 解決截止日 |
|---|------|---------|-----------------|--------|-----------|

### §13 Glossary

列出文件中所有領域術語與縮寫定義

### §14 References

- 上游 BRD：`docs/BRD.md`（DOC-ID：BRD-XXX-YYYYMMDD）
- 上游 IDEA：`docs/IDEA.md`
- docs/req/ 素材：所有被引用的素材檔案路徑
- 外部標準 / 法規連結

### §15 Requirements Traceability Matrix（RTM）

> RTM 確保每一個業務需求都能追溯到設計決策、技術實現和測試案例，形成完整的需求追蹤鏈。

| REQ-ID | BRD 目標 | User Story 章節 | AC# | PDD 設計章節 | EDD 技術方案章節 | 測試案例 ID | 狀態 |
|--------|---------|---------------|-----|------------|---------------|-----------|------|
| US-<CODE>-001 | BRD O1 | §5.1 | AC-1, AC-2 | 待 PDD 生成後補填 | 待 EDD 生成後補填 | TC-001 | DRAFT |

狀態說明：
- `DRAFT`：需求已識別，尚未設計
- `IN_REVIEW`：正在設計/審查
- `APPROVED`：已核准，可以開發
- `VERIFIED`：開發完成，測試通過

生成規則：
- RTM 每一行對應一個 REQ-ID（User Story）
- PRD 生成階段，PDD/EDD 章節欄填「待 PDD/EDD 生成後補填」
- 狀態預設為 `DRAFT`

### §16 Approval Sign-off

| 角色 | 姓名 | 簽核狀態 | 日期 | 備注 |
|------|------|---------|------|------|
| PM | | 🔲 待簽核 | | |
| Engineering Lead | | 🔲 待簽核 | | |
| Design Lead | | 🔲 待簽核 | | |

### §17 Privacy by Design & Data Protection

**七大 Privacy by Design 原則逐條確認**：

| 原則 | 說明 | 本產品實作方式 | 狀態 |
|------|------|-------------|------|
| Proactive, not reactive | 預防而非補救 | | 🔲 待確認 |
| Privacy as the default | 預設隱私保護 | | 🔲 待確認 |
| Privacy embedded into design | 嵌入設計中 | | 🔲 待確認 |
| Full functionality | 無需取捨隱私 | | 🔲 待確認 |
| End-to-end security | 端到端保護 | | 🔲 待確認 |
| Visibility and transparency | 可見與透明 | | 🔲 待確認 |
| Respect for user privacy | 以用戶為中心 | | 🔲 待確認 |

**PII Inventory**：來自 §11.4，所有個人資料欄位、法律依據（GDPR Art. 6 等）標注

**GDPR Rights 實作矩陣**（若適用 GDPR）：

| 使用者權利 | 說明 | 對應 API Endpoint | 實作狀態 |
|----------|------|-----------------|---------|
| 存取權（Art. 15）| 查看個人資料 | | 🔲 待規劃 |
| 更正權（Art. 16）| 修正個人資料 | | 🔲 待規劃 |
| 刪除權（Art. 17）| 要求刪除 | | 🔲 待規劃 |
| 限制處理權（Art. 18）| 暫停處理 | | 🔲 待規劃 |
| 資料可攜權（Art. 20）| 匯出資料 | | 🔲 待規劃 |
| 反對權（Art. 21）| 反對特定處理 | | 🔲 待規劃 |
| 撤回同意權（Art. 7(3)）| 撤回同意 | | 🔲 待規劃 |

**同意管理（Consent Management）**：
- 同意記錄 Schema（`user_consents` table）設計
- 欄位：user_id / consent_type / granted_at / revoked_at / version / ip_address

### §18 Accessibility Requirements（無障礙需求）

**WCAG 2.1 目標里程碑**：
- Level A（MVP 上線前）
- Level AA（上線後 3 個月）
- Level AAA（上線後 12 個月，視情況）

**A11y 需求清單**（A11y-01 到 A11y-10）：

| 編號 | 需求 | WCAG 準則 | 優先度 |
|------|------|----------|-------|
| A11y-01 | 所有圖片有 alt text | 1.1.1 | P0 |
| A11y-02 | 文字對比度 ≥ 4.5:1（一般）/ 3:1（大文字）| 1.4.3 | P0 |
| A11y-03 | 鍵盤可操作所有功能 | 2.1.1 | P0 |
| A11y-04 | 焦點可見（Focus visible）| 2.4.7 | P0 |
| A11y-05 | 表單欄位有 Label | 1.3.1 | P0 |
| A11y-06 | 錯誤訊息有文字描述（非僅顏色）| 1.4.1 | P0 |
| A11y-07 | 頁面有語意化標題結構（H1-H6）| 1.3.1 | P0 |
| A11y-08 | 影片有字幕 | 1.2.2 | P1 |
| A11y-09 | 動畫可暫停 / 停止（支援 prefers-reduced-motion）| 2.3.3 | P1 |
| A11y-10 | 螢幕閱讀器測試通過（NVDA / VoiceOver）| | P1 |

---

## Inference Rules（推斷規則）

1. **BRD 不存在時**：依 IDEA.md + docs/req/ 素材直接生成，在 Document Control 標注「無 BRD，依 IDEA.md 生成」，並在每個 User Story 標注「需 PM 審核確認優先度」
2. **NFR 無具體數字時**：依產品類型（SaaS / 消費者 App / 內部工具）給出合理的業界標準數字，並標注「參考值，需 Engineering 確認」
3. **PII 不確定時**：依用戶資料欄位保守推斷（若可能是 PII，就標記為 PII），並標注「需 Legal 確認」
4. **Feature Flag 工具未指定時**：填「待 Engineering 確認」
5. **GDPR 適用性不確定時**：若目標市場含歐盟用戶，預設適用 GDPR，標注「需 Legal 確認」
6. **docs/req/ 素材存在時**：對 Appendix C「應用於」欄標有「PRD §」的素材，優先採用素材原文描述生成對應 User Story 與 AC

---

## Self-Check Checklist（生成後自我審查）

生成完成後，逐項確認，有遺漏則自行補齊後再寫入檔案：

- [ ] 每個 BRD §In Scope 功能都有對應的 User Story（不可遺漏）
- [ ] 每個 User Story 至少 2 個 AC（正常路徑 + 錯誤路徑）
- [ ] 所有 User Story 有 REQ-ID 標記（格式：US-CODE-NNN）
- [ ] NFR 有具體數字（禁止「系統應該很快」等模糊描述）
- [ ] P0 功能完整涵蓋 BRD §成功指標
- [ ] Out of Scope 章節明確重申 BRD 排除項目
- [ ] DOC-ID 已填寫（格式：PRD-XXX-YYYYMMDD）
- [ ] §2.4 System Context Diagram 已生成（含外部系統節點，每個節點有真實名稱）
- [ ] §3 Persona 卡片：至少 1 個（含 Goals / Frustrations / Scenario）
- [ ] §3 Stakeholder Map：已生成
- [ ] §6 User Flows：Happy Path + Error Flow + State Machine 三種 Mermaid 圖已生成
- [ ] §7.7 Observability NFR 已填寫（含 Metrics 表格與告警閾值）
- [ ] §7.8 Analytics Event Map 已填寫（每個功能至少 1 個 Event）
- [ ] §8.4 Assumptions 已填寫（≥ 3 條，與 Constraints 嚴格區分）
- [ ] §8.5 Backward Compatibility 已宣告（全新產品填「否/N/A」）
- [ ] §9.4 A/B Test Plan 已填寫（有實驗假說 + Guardrail Metrics）
- [ ] §9.5 DoD 已分拆為 Product DoD + Engineering DoD 兩表
- [ ] §10.2 Feature Flag 規格：每個 P0 功能必須有 Kill Switch Flag
- [ ] §11 Data Requirements 已填寫（含 Data Dictionary + PII 清單）
- [ ] §12 Open Questions：至少 2 項影響策略的未解問題
- [ ] §13 Glossary：領域術語已定義
- [ ] §15 RTM 已建立（每個 User Story 都有追蹤行）
- [ ] §16 Approval Sign-off：PM / Engineering Lead / Design Lead 簽核表已建立
- [ ] §17 Privacy by Design：七大原則逐條確認是否完成
- [ ] §17 PII Inventory：所有個人資料欄位（email/phone/IP 等）已建立清單，法律依據已標注
- [ ] §17 GDPR Rights Matrix：7 項使用者隱私權均有對應 API endpoint 規劃
- [ ] §17 Consent Management：同意記錄 Schema（user_consents table）已設計
- [ ] §18 WCAG 2.1 AA 目標：Level A（MVP）/ Level AA（3 個月）里程碑已設定
- [ ] §18 A11y 需求清單：A11y-01 到 A11y-10 十項已列入
- [ ] 全文無 "TBD"、"待補"、"[待填]" 等空白佔位

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| 所有 §章節齊全 | 對照 PRD.md 章節清單，無缺失章節 | 補寫缺失章節 |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | 技術約束、平台要求與 BRD §8.3 一致 | 以 BRD 技術約束為準修正 |
| 數值非 TBD/N/A | 所有 Success Metrics 填有可量測的具體數字（如：< 2s 回應時間、99.9% uptime） | 從 BRD §Business Objectives 推算填入 |
| AC 完整性 | 每個 User Story 至少有 3 條驗收標準（AC），且 AC 具體可驗證 | 為每個 Story 補充缺失 AC |
| RTM 種子 | 每個 User Story 有對應的 RTM 編號（US-XXX-NNN 格式） | 按序補充 RTM 編號 |
