---
doc-type: PRD
target-path: docs/PRD.md
reviewer-roles:
  primary: "資深 UX Expert（PRD 審查者）"
  primary-scope: "BRD 一致性、Persona 具體度、US 格式完整性、AC 可測試性、Journey 覆蓋、MoSCoW 合理性"
  secondary: "資深 PM Expert"
  secondary-scope: "功能優先級合理性、商業可行性、上游 BRD 對齊、KPI 可量化度"
  tertiary: "資深 QA Expert"
  tertiary-scope: "AC 可測試性、驗收標準具體度、Edge Case 覆蓋"
quality-bar: "任何工程師拿到 PRD 後，不需問任何 PM，就能直接開始 Sprint Planning 並拆出所有 User Story。"
upstream-alignment:
  - field: 業務目標
    source: BRD.md §商業目標
    check: PRD 功能目標是否全部可追溯回 BRD 業務目標，無遺漏或衝突
  - field: 使用者角色
    source: BRD.md §使用者角色
    check: PRD Persona 是否覆蓋 BRD 定義的所有角色，無額外未解釋的新角色
  - field: 核心功能範圍
    source: IDEA.md §核心功能
    check: PRD User Stories 是否完整涵蓋 IDEA 中定義的所有核心功能，無遺漏
---

# PRD Review Items

本檔案定義 `docs/PRD.md` 的審查標準。由 `/reviewdoc PRD` 讀取並遵循。
審查角色：三角聯合審查（資深 UX Expert + 資深 PM Expert + 資深 QA Expert）
審查標準：「假設公司聘請一位 10 年以上資深 UX 顧問，以最嚴格的業界標準進行 PRD 驗收審查。」

---

## Review Items

### Layer 1: BRD 一致性（由 PM Expert 主審，共 5 項）

#### [CRITICAL] 1 — BRD 目標未對齊
**Check**: PRD 列出的功能目標是否全部可追溯回 BRD 業務目標？是否有 PRD 功能找不到對應 BRD 業務目標？逐一列出無法追溯的功能。
**Risk**: 功能目標與業務目標脫鉤，工程師開發的功能無法達成商業價值，浪費資源且上線後無法衡量成效。
**Fix**: 為每個 PRD 功能目標建立 BRD 業務目標追溯表；刪除或重新定義無法追溯的功能。若新增功能有正當業務理由，在 PRD 中明確說明依據。

#### [CRITICAL] 2 — PRD 遺漏 BRD Must-Have 需求
**Check**: BRD 中每個 Must Have 業務需求是否在 PRD 中有對應 User Story？列出所有 BRD Must Have 項目及其在 PRD 中的對應 US-ID；缺少對應的視為 CRITICAL finding。
**Risk**: BRD 核心需求未轉化為 User Story，導致產品交付後無法滿足業務契約或利害關係人期望。
**Fix**: 逐一對應 BRD Must Have 清單，為每個缺漏的業務需求補充對應的 User Story（含 AC 和優先級）。

#### [HIGH] 3 — 使用者角色不一致
**Check**: PRD Persona 是否包含 BRD 定義的所有使用者角色？若 PRD 自行新增角色，是否有 BRD 或業務依據說明？列出 BRD 角色與 PRD Persona 的對照關係，標出缺漏或新增項目。
**Risk**: 角色不一致導致設計和開發針對錯誤的使用者，PDD/EDD 的受眾假設出現分歧，後續測試用例無法覆蓋真實使用者場景。
**Fix**: 補充缺漏的 BRD 角色；若 PRD 新增角色，在 Persona 說明中標注業務依據來源（如用戶訪談、市場分析）。

#### [HIGH] 4 — IDEA 核心功能未涵蓋
**Check**: IDEA.md 中定義的核心功能是否全部在 PRD User Stories 中有對應？列出 IDEA 核心功能與 PRD US 的對應矩陣，標出缺漏。
**Risk**: IDEA 定義的核心功能缺漏，產品交付後不符合最初的設計意圖，需要追加需求。
**Fix**: 為 IDEA 中每個未覆蓋的核心功能補充對應 US；若刻意排除，在 PRD §4.2 Out of Scope 中明確說明原因。

#### [MEDIUM] 5 — 商業指標缺失或不可量化
**Check**: PRD 是否定義了可量化的成功指標（KPI/OKR）？每個 P0 功能是否有對應的 KPI 及 Baseline + 目標值？泛化描述（「提升用戶體驗」「改善效率」）且無數值的視為 finding。
**Risk**: 無量化指標，產品上線後無法判斷是否成功，也無法作為後續迭代的決策依據，A/B Test 無法設計。
**Fix**: 為每個 P0 功能補充具體 KPI（如「30 天留存率提升 15%」「轉換率 > 3%」「P99 延遲 < 1000ms」），並連結至 BRD 商業目標，填入 §9.1 KPI 表格。

---

### Layer 2: User Story 品質（由 UX Expert 主審，共 5 項）

#### [CRITICAL] 6 — US 格式錯誤
**Check**: 每個 User Story 是否嚴格遵守「作為 <角色>，我希望能 <功能>，以便 <業務價值>」三段式格式？列出所有不符格式的 US（缺少角色、缺少業務價值、或僅描述技術實作）。
**Risk**: 格式錯誤的 US 缺少角色或價值維度，工程師無法判斷實作優先級，QA 無法驗收業務價值，Sprint Planning 無法自主決策。
**Fix**: 逐一修正格式不符的 US，確保三段式結構完整（角色 / 功能 / 業務價值），不得省略任何一段；「以便」後面必須是業務成果，不得是技術描述。

#### [CRITICAL] 7 — AC 不可測試
**Check**: 每條 Acceptance Criteria 是否可量化驗收（有具體數值、明確行為或 Given/When/Then 結構），無模糊用語（「方便」「更好」「盡量」「適當」）？逐一列出每條模糊 AC 及其位置。
**Risk**: 模糊 AC 導致 QA 無法自動化測試，開發和 QA 對「完成」定義不一，上線後頻繁爭議和返工。
**Fix**: 將每條模糊 AC 替換為可量化描述（如「回應時間 < 2 秒」「錯誤訊息顯示於輸入框下方 4px 以內」「列表返回後滾動位置保持不變」）；推薦使用 Given/When/Then 格式。

#### [HIGH] 8 — AC 缺少 Error Path 和 Edge Case
**Check**: 每個 P0 User Story 是否有 Happy Path + Error Path + Boundary Case 三種情境的 AC？缺少 Error Path（API 失敗、驗證失敗、逾時）或 Boundary Case（空資料、上限值、並發）任一者視為 HIGH finding。
**Risk**: 只有 Happy Path AC，系統在錯誤情境下的行為未定義，開發各自實作不一致的錯誤處理，用戶在異常情況下體驗不一致甚至看到空白或崩潰。
**Fix**: 為每個 P0 US 補充 Error Path AC（API 失敗回傳 → 顯示 retry 提示、驗證失敗 → Inline 錯誤訊息）和 Boundary Case AC（空列表 → Empty State、輸入超過上限 → 截斷並提示）。

#### [HIGH] 9 — US 無 Priority 標記或分類不合理
**Check**: 每個 US 是否有 MoSCoW 或 P0/P1/P2 優先級標記？P0 中是否有明顯可延後的功能？P2 中是否混入了對 P0 AC 有依賴的核心功能？無標記的 US 及疑問項目均列出。
**Risk**: 未標記優先級的 US 進入 Sprint 後，團隊無法自主判斷取捨；優先級錯誤導致資源分配不當，核心功能被延後或次要功能佔用工程資源。
**Fix**: 為所有 US 加上優先級標記（P0/P1/P2 或 MoSCoW），並在文件頂部說明分類標準；重新評估疑問項目，根據業務影響和技術依賴關係調整分類。

#### [MEDIUM] 10 — Persona 抽象化
**Check**: 每個 Persona 是否有具體的痛點（≥ 2 個）、典型使用情境（≥ 1 個場景）、技術熟悉度（低/中/高）描述？純名稱無內容（「一般用戶」「系統管理員」）視為 finding。
**Risk**: 抽象 Persona 無法指導設計決策，UX 設計師和工程師對目標使用者的假設各異，功能設計分散，PDD 無法依據 Persona 做出有依據的設計取捨。
**Fix**: 為每個 Persona 補充：典型使用情境（1-2 個具體場景）、核心痛點（2-3 個），技術熟悉度（低/中/高），以及「成功時的感受」描述。

---

### Layer 3: Journey 與流程（由 UX Expert 主審，共 4 項）

#### [HIGH] 11 — User Journey 缺少 Error Path
**Check**: PRD §6 User Flows 是否包含錯誤路徑（網路失敗、API 錯誤、驗證失敗、逾時、無權限）？只有 Happy Path 且無任何錯誤分支的 Flow 圖視為 HIGH finding。
**Risk**: 錯誤路徑未定義，開發各自處理異常行為，用戶在錯誤情境下體驗不一致，甚至出現空白畫面或無回應狀態。
**Fix**: 在每個 User Flow 圖中為關鍵步驟補充錯誤分支，至少覆蓋：網路失敗（Retry 提示）、伺服器錯誤（Error State + Feedback）、使用者輸入錯誤（Inline 驗證提示）三類。

#### [HIGH] 12 — 邊界條件 AC 缺漏
**Check**: 數值型 AC 是否說明上下界（如「最多上傳 10MB」「最少輸入 8 字元」）？並發行為是否有 AC 定義（如「多用戶同時編輯同一筆資料時的衝突處理」）？
**Risk**: 邊界值未定義，工程師各自實作不同上下限，QA 無邊界測試依據，上線後出現意外截斷、超限或數據競爭的錯誤。
**Fix**: 為所有數值型 AC 補充明確邊界條件（最小值、最大值、特殊值如 0 或空字串的處理方式）；為關鍵並發場景補充樂觀鎖或衝突解決策略的 AC。

#### [MEDIUM] 13 — 狀態機缺失
**Check**: 若 PRD 涉及有明確生命週期的業務實體（訂單、審批流程、任務狀態等），§6.3 State Machine 圖是否存在且完整？各狀態的轉換條件和觸發方是否都有說明？
**Risk**: 業務實體的狀態流不清晰，後端開發各自實作不同的狀態轉換邏輯，QA 無法設計狀態機測試，上線後出現非法狀態轉換。
**Fix**: 為每個有生命週期的業務實體補充 stateDiagram-v2 狀態機圖，標注每個轉換的觸發條件（操作者、事件名稱）和守衛條件（前提）。

#### [LOW] 14 — Epic 未分組
**Check**: US 數量超過 10 個時，是否按 Epic 或功能模組分組？無分組的大量 US 平鋪展示視為 LOW finding。
**Risk**: 大量 US 平鋪展示，Sprint Planning 時難以快速定位相關功能群組，影響估算效率和範圍管理。
**Fix**: 將 US 依業務功能分組為 Epic（建議每個 Epic 5-10 個 US），在文件結構中以 Epic 為章節組織；每個 Epic 說明其業務目標和與 BRD 目標的對應關係。

---

### Layer 4: 非功能性需求（由 PM Expert + QA Expert 聯合審查，共 4 項）

#### [HIGH] 15 — 效能 NFR 無具體數值
**Check**: §7.1 效能需求是否有具體數值目標（API P50/P99 延遲 ms、頁面 LCP 秒、批次吞吐量 records/sec）？泛化描述（「系統應快速回應」「不應有明顯延遲」）視為 HIGH finding。
**Risk**: 模糊效能 NFR 導致工程師無優化目標，QA 無效能驗收標準，SRE 無 SLO 設定依據，上線後效能問題無基準可判斷。
**Fix**: 填入具體 NFR 數值（API P99 < 1000ms、LCP < 2.5s 等）；若有 EDD，確保 NFR 數字與 EDD §SLO 一致；在 §9.2 護欄指標中加入效能 Guardrail。

#### [HIGH] 16 — 安全性與合規要求缺失
**Check**: §7.4 安全性需求是否明確定義：認證方式（JWT/OAuth2/Session）、授權模型（RBAC/ABAC）、PII 欄位清單（§11.5）、合規要求（GDPR/HIPAA/PDPA）？若有用戶個人資料處理但 PII 欄位缺失，視為 HIGH finding。
**Risk**: 安全需求不明確，工程師各自實作不同的安全策略；PII 遺漏導致合規風險，可能違反法律法規面臨罰款。
**Fix**: 補充 §7.4 安全認證方式和授權模型；填寫 §11.5 PII 欄位清單，為每個 PII 欄位指定處理方式和法規依據；§17 Privacy by Design 合規清單需逐項填寫。

#### [MEDIUM] 17 — Analytics Event 覆蓋不足
**Check**: §7.8 Analytics Event Instrumentation Map 是否為每個 P0 功能定義了對應的事件？事件命名是否遵循 `{object}_{action}_{result}` 規範？是否有 P0 功能無任何 Analytics 事件？
**Risk**: Analytics 事件缺漏，P0 功能上線後無法量化效果，KPI 追蹤斷層，A/B Test 無法依據數據決策。
**Fix**: 為每個 P0 功能補充至少 1 個核心 Analytics Event，填入 §7.8 表格；確保事件命名遵循規範，並標注關聯 KPI。

#### [MEDIUM] 18 — 無障礙需求缺失或過於泛化
**Check**: §7.5 / §18 是否明確指定 WCAG 合規目標等級（Level A/AA/AAA）？§18 A11y 需求清單是否至少包含對比度、鍵盤操作、螢幕閱讀器三類基本要求？「符合 WCAG 標準」的空泛聲明視為 finding。
**Risk**: 無障礙需求不具體，PDD 和工程師各自解讀，上線後發現 WCAG 不合規，返工成本高；部分地區（歐盟 EAA）有法律合規要求。
**Fix**: 在 §7.5 指定 WCAG 2.1 Level AA 目標；補充 §18 A11y 需求清單，至少包含 A11y-01（alt text）、A11y-02（色彩對比 4.5:1）、A11y-03（鍵盤操作）三項基本要求。

---

### Layer 5: 文件完整性（由技術文件角度通盤審查，共 4 項）

#### [HIGH] 19 — 術語不一致
**Check**: PRD 中同一概念是否使用一致術語（如「用戶」vs「使用者」，「登入」vs「登錄」，「功能」vs「Feature」）？跨章節術語不一致視為 finding；尤其注意 US、AC、KPI 章節之間的術語一致性。
**Risk**: 術語不一致造成下游文件（PDD/EDD/API）各自採用不同稱呼，需要反覆確認概念對應關係，影響開發效率。
**Fix**: 建立 §13 Glossary 術語表，統一全文術語並替換所有不一致的用法；術語表供後續 PDD/EDD/API 文件引用。

#### [HIGH] 20 — RTM 缺失或不完整
**Check**: §15 Requirement Traceability Matrix 是否存在？是否覆蓋所有 P0 US？每行是否包含 BRD 目標、AC#、PDD 章節、EDD 章節、測試案例 ID 欄位？空白的 RTM 表格視為 finding。
**Risk**: 無 RTM 則需求追蹤斷鏈；工程師無法確認某功能的完整實作範圍；QA 無法確認所有需求都有對應測試案例。
**Fix**: 補充 §15 RTM，為所有 P0 US 填入 BRD 目標對應；P1/P2 US 至少填入 BRD 目標和 AC#；各欄位可先填入「待 PDD/EDD 完成後補充」。

#### [MEDIUM] 21 — 裸 Placeholder
**Check**: 是否有 `{{PLACEHOLDER}}` 格式未替換的空白佔位符？重點掃描 §1 Executive Summary、§Document Control（DOC-ID / 作者 / 日期）、§9.1 KPI Baseline 和目標值、§8.5 Backward Compatibility 宣告。
**Risk**: 裸 placeholder 留存表示文件未完成，工程師閱讀時無法確認文件有效性，影響對文件的信任度；DOC-ID 空白也無法進行版本管理。
**Fix**: 替換所有裸 placeholder 為真實值；若確實無法確定，改為 `（待確認：描述說明）` 格式；DOC-ID 和日期必須在文件發布前填入。

#### [LOW] 22 — US 無估算參考
**Check**: US 是否附有 Story Point 估算或 T-Shirt Size（S/M/L/XL）？US 是否符合 INVEST 原則（Independent / Negotiable / Valuable / Estimable / Small / Testable）？無估算不阻塞，但視為 LOW finding。
**Risk**: 無估算參考，Sprint Planning 需要從零開始估算所有 US，延長 Planning 會議時間；過大的 US（XL 或更大）在 Sprint 中無法完成，影響交付節奏。
**Fix**: 為每個 US 補充初步 T-Shirt Size（S/M/L/XL）作為 Planning 參考起點，標注估算假設前提；XL 的 US 建議拆分為更小的 Story。

---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/PRD.md`，提取所有 `^## ` heading（含條件章節），共約 23 個
2. 讀取 `docs/PRD.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
