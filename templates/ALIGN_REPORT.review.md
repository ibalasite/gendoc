---
doc-type: ALIGN_REPORT
target-path: docs/ALIGN_REPORT.md
reviewer-roles:
  primary: "資深 Software Architect（Alignment Expert）"
  primary-scope: "跨文件一致性、上下游數字對齊、術語統一性、功能覆蓋完整性"
  secondary: "資深 QA Expert"
  secondary-scope: "RTM 追溯完整性、測試覆蓋對齊、BDD Scenario 與 AC 一致性"
  tertiary: "資深 Tech Writer"
  tertiary-scope: "術語一致性、文件引用正確性、Finding 描述具體性"
quality-bar: "所有下游文件與上游需求完全一致，無數字矛盾、術語衝突、功能遺漏。任何工程師拿到 ALIGN_REPORT.md 後，能直接按 finding 清單修復對應文件，不需理解完整的文件鏈結構。"
upstream-alignment:
  - field: BRD→PRD→EDD 鏈完整
    source: docs/BRD.md → docs/PRD.md → docs/EDD.md
    check: 文件鏈中每個節點是否存在且包含上游必要欄位
  - field: RTM TC-ID → BDD @tag 全覆蓋
    source: docs/RTM.md TC-ID → features/*.feature @tag
    check: RTM 所有 TC-ID 是否在 features/ 中有對應 @tag
  - field: SLO 數字一致性
    source: docs/EDD.md §10.5 → docs/RUNBOOK.md §3
    check: EDD 定義的 SLO 數字是否在所有下游文件中完全一致
  - field: API Base URL
    source: docs/API.md → docs/FRONTEND.md → docs/LOCAL_DEPLOY.md
    check: API Base URL 是否在所有使用端文件中一致
---

# ALIGN_REPORT Review Items

本檔案定義 `docs/ALIGN_REPORT.md` 的審查標準。由 `/reviewdoc align-report` 讀取並遵循。
審查角色：三角聯合審查（資深 Software Architect + 資深 QA Expert + 資深 Tech Writer）
審查標準：「假設公司聘請一位 15 年系統分析資深顧問，以最嚴格的業界標準進行文件對齊報告的二次驗收審查。」

---

## Review Items

### Layer 1: 業務目標追溯鏈（由 Software Architect 主審，共 5 項）

#### [CRITICAL] 1 — Dimension 0（必要文件存在性）缺失
**Check**: ALIGN_REPORT 是否列出所有必要文件（IDEA/BRD/PRD/PDD/EDD/ARCH/API/SCHEMA/test-plan/RTM）的存在狀態？每個必要文件是否有明確的 PASS/FAIL/SKIP 狀態標記？逐一核對必要文件清單，列出 ALIGN_REPORT 未涵蓋或未標記的文件。
**Risk**: 必要文件缺失但 ALIGN_REPORT 未標記，工程師啟動開發時缺乏關鍵文件依據（如無 SCHEMA 無法建立資料庫），導致開發受阻或依賴錯誤假設。
**Fix**: 補充 Dimension 0 清單，涵蓋所有必要文件的存在性檢查；將 FAIL 狀態的文件標記為 CRITICAL Finding，並說明缺失文件的業務影響。

#### [CRITICAL] 2 — BRD 業務目標在下游文件中的追溯鏈斷裂
**Check**: ALIGN_REPORT 是否驗證每個 BRD Must Have 需求（業務目標）在 PRD → EDD → ARCH → API 的完整下游追溯鏈？每個節點是否能找到明確的對應關係？逐一核對 BRD 業務目標清單，列出追溯鏈中斷的節點。
**Risk**: 業務目標的追溯鏈斷裂，表示某個業務承諾無法被任何實作或測試覆蓋，產品上線後可能不符合業務方的預期，造成重工。
**Fix**: 補充每個 BRD 業務目標的完整下游追溯，從 BRD → PRD US-ID → EDD 功能區塊 → API Endpoint → Test Case，並標記未對應的節點為 CRITICAL Finding。

#### [CRITICAL] 3 — Dimension 1（Doc→Doc 文件鏈）覆蓋不完整
**Check**: ALIGN_REPORT 是否驗證完整的文件鏈（BRD→PRD→PDD→EDD→ARCH/API/SCHEMA→BDD→RTM）？鏈中每個節點間的追溯關係是否有具體的驗證結果（列出通過的對應關係和缺漏的對應關係）？逐一核對文件鏈的每個節點間驗證，列出未驗證的鏈節點。
**Risk**: 文件鏈中任一節點未驗證，表示有一段上下游關係可能存在斷鏈（如 EDD 新增實體但 SCHEMA 未更新），且無法在 ALIGN_REPORT 中發現。
**Fix**: 補充缺少的文件鏈節點驗證，逐一說明每個節點間的對應關係結果（對應數量、缺漏清單）。

#### [HIGH] 4 — PRD P0 功能在 EDD/API/SCHEMA 的覆蓋完整性
**Check**: ALIGN_REPORT 是否驗證每個 PRD P0 User Story 在 EDD（對應功能區塊或 Class）、API（對應 Endpoint）、SCHEMA（對應 Table 或 Column）中均有覆蓋？是否列出各層的覆蓋率數字（如「PRD P0 US 共 X 條，EDD 覆蓋 Y 條」）？
**Risk**: P0 功能在設計文件中覆蓋不完整，可能導致工程師在開發時才發現遺漏，臨時補充設計，增加架構風險。
**Fix**: 補充 P0 功能的三層覆蓋驗證（EDD/API/SCHEMA），列出覆蓋數量和缺漏清單；未覆蓋的 P0 US 標記為 CRITICAL Finding。

#### [MEDIUM] 5 — Dimension 2/3 跳過說明缺失
**Check**: 若系統無程式碼（autogen 模式或純文件交付），Dimension 2（Doc→Code 對應）和 Dimension 3（Code→Test 對應）可略過，但 ALIGN_REPORT 是否明確說明略過原因（如「本次交付為 autogen 文件模式，尚無程式碼實作，Dimension 2/3 待 Sprint 1 開發完成後補充」）？
**Risk**: Dimension 2/3 無說明直接跳過，審查者無法區分「刻意略過（有理由）」與「遺漏（疏失）」，導致審查結論不明確。
**Fix**: 在 ALIGN_REPORT 的 Dimension 2/3 章節補充明確的略過說明，包含略過原因和預計補充時間。

---

### Layer 2: 術語一致性（由 Tech Writer 主審，共 5 項）

#### [HIGH] 6 — 核心業務術語跨文件不一致
**Check**: 跨文件使用不同術語表達同一業務概念（如「使用者」vs「用戶」vs「User」、「訂單」vs「Order」vs「purchase」）是否在 ALIGN_REPORT 中標記為 Finding？逐一比對 BRD/PRD/EDD/API/SCHEMA 中的核心業務術語，識別術語不一致的情況。
**Risk**: 術語不一致導致工程師看不同文件時產生混淆（「使用者」和「用戶」是同一個概念還是不同角色？），增加溝通成本，也可能導致 ORM Entity 命名與 DB Table 命名不一致。
**Fix**: 列出跨文件術語不一致的清單，建議統一術語（選定一個標準術語並在所有文件中一致使用）。

#### [HIGH] 7 — API 術語與 SCHEMA 命名不一致
**Check**: API.md 中的 Request/Response 欄位名稱（camelCase）是否與 SCHEMA.md 的資料庫欄位名稱（snake_case 或其他命名慣例）存在語意不一致？逐一核對 API Payload 與 DB Column 的命名對應關係，識別語意衝突。
**Risk**: API 欄位名稱與 DB Column 語意不一致（如 API 用 `isActive` 但 DB 用 `status`），工程師在 ORM Mapping 時可能混淆，導致 Data Mapping Bug。
**Fix**: 補充 API → SCHEMA 欄位映射說明，或在 ALIGN_REPORT 中標記語意衝突的欄位對。

#### [MEDIUM] 8 — Persona / 角色定義跨文件衝突
**Check**: BRD 定義的使用者角色（如 Admin / Member / Guest）是否與 PRD User Stories 的角色、EDD 的認證授權設計完全一致？是否有角色在某些文件中存在但在其他文件中缺失？
**Risk**: 角色定義不一致，工程師在實作 RBAC 時對「哪些角色有哪些權限」產生困惑，可能實作出錯誤的權限邊界。
**Fix**: 列出各文件中的角色定義，識別衝突或遺漏；建議以 EDD 認證設計為 Source of Truth，其他文件對齊。

#### [MEDIUM] 9 — 狀態機術語跨文件不一致
**Check**: 業務對象的狀態描述（如訂單的「待付款」vs「PENDING」vs「unpaid」）是否在所有文件中使用一致的術語？逐一核對 PRD 業務流程描述與 SCHEMA 的狀態欄位定義和 API Response 的狀態值。
**Risk**: 狀態術語不一致，前後端對「哪個值代表哪個業務狀態」理解不同，導致前端顯示錯誤的狀態或觸發錯誤的業務邏輯。
**Fix**: 建立統一的狀態術語對照表（業務描述 ↔ API 值 ↔ DB 值），在 ALIGN_REPORT 中標記衝突項目。

#### [LOW] 10 — 縮寫與專有名詞未統一定義
**Check**: 文件中使用的縮寫（SLA、SLO、MFA、RBAC 等）和技術專有名詞是否在第一次出現時有完整定義？跨文件使用相同縮寫但含意不同的情況是否被標記？
**Risk**: 縮寫定義不統一，新加入的工程師或 PM 閱讀文件時產生混淆，需要反覆確認含意。
**Fix**: 建議在 ALIGN_REPORT 附錄中維護一份專案術語表（Glossary），確保跨文件縮寫含意一致。

---

### Layer 3: 數字對齊（由 Software Architect + QA Expert 聯合審查，共 5 項）

#### [CRITICAL] 11 — SLO 數字跨文件不一致
**Check**: EDD §10.5 定義的 SLO 數字（Availability %、P99 延遲 ms、Error Rate %）是否在所有引用它的文件（RUNBOOK、test-plan、ARCH）中完全一致？列出所有使用 SLO 數字的文件和它們的實際值。
**Risk**: SLO 數字跨文件不一致（如 EDD 定義 99.9% 但 RUNBOOK 寫 99.5%），導致 Alert 閾值設定錯誤、Error Budget 計算錯誤、SRE 使用錯誤的值設定監控告警。
**Fix**: 以 EDD §10.5 為 Source of Truth，逐一修正其他文件中不一致的 SLO 數字，並在 ALIGN_REPORT 中標記已修正的文件。

#### [CRITICAL] 12 — Port 號碼跨文件不一致
**Check**: API Port、DB Port、Redis Port 等關鍵服務 Port 號碼是否在 EDD、ARCH、LOCAL_DEPLOY、RUNBOOK 中完全一致？列出每個 Port 在各文件的實際值。
**Risk**: Port 號碼不一致（如 EDD 定義 API Port 8080 但 LOCAL_DEPLOY 用 8000），工程師依不同文件設定環境時互相衝突，本地環境無法正常啟動。
**Fix**: 以 EDD §3.5 服務 Port 對照表為 Source of Truth，修正其他文件中不一致的 Port 號碼。

#### [HIGH] 13 — 效能目標數字跨文件不一致
**Check**: API Response Time 目標（P95/P99）、資料庫查詢超時設定、Cache TTL 等效能數字是否在 EDD、ARCH、test-plan 中完全一致？識別所有設定了效能目標但數字互相矛盾的文件。
**Risk**: 效能目標不一致（如 EDD 定義 P95 < 200ms 但 test-plan 的 Load Test 目標設 500ms），QA 可能在效能達標時判斷為不達標，造成不必要的工程投入。
**Fix**: 以 EDD SLO 章節為 Source of Truth，統一所有文件中的效能目標數字。

#### [HIGH] 14 — 資源配額數字跨文件不一致
**Check**: K8s 資源限制（CPU limit、Memory limit）、Auto-scaling 設定（min replicas、max replicas、HPA threshold）是否在 EDD 和 ARCH 中完全一致？識別不一致的資源配額數字。
**Risk**: 資源配額不一致，SRE 依不同文件設定 K8s 資源時可能使用錯誤的值，導致 OOM Kill 或資源浪費。
**Fix**: 以 EDD §7 K8s 資源規格為 Source of Truth，修正 ARCH 中不一致的資源配額。

#### [MEDIUM] 15 — API Version 跨文件不一致
**Check**: API Version（v1、v2 等）是否在 API.md Endpoint 定義、EDD 技術選型、FRONTEND.md 的 API 呼叫路徑中完全一致？識別使用不同 API Version 的文件。
**Risk**: API Version 不一致，前端工程師依不同文件設定 Base URL 時可能呼叫到錯誤的 API 版本，導致功能異常。
**Fix**: 統一所有文件使用相同的 API Version，並在 ALIGN_REPORT 中標記修正的文件。

---

### Layer 4: 功能覆蓋完整性（由 QA Expert 主審，共 5 項）

#### [CRITICAL] 16 — PRD AC → BDD Scenario 追溯斷鏈
**Check**: ALIGN_REPORT 是否驗證每個 PRD AC（Acceptance Criteria）在 BDD .feature 中有 Scenario 覆蓋（含 @TC-ID tag）？是否列出 PRD P0 AC 總數和 BDD 覆蓋數量及覆蓋率？逐一核對 PRD AC 清單與 BDD features/ 的 Scenario @tag。
**Risk**: PRD AC→BDD 追溯斷鏈，Product Owner 定義的驗收標準無法自動化驗證，發布時無法確認 AC 是否達成，需依賴手動驗收，增加 QA 負擔。
**Fix**: 補充 PRD AC→BDD 追溯驗證，列出每個 PRD AC 對應的 BDD Scenario @tag；若有 PRD AC 無對應 BDD Scenario，標記為 CRITICAL Finding。

#### [CRITICAL] 17 — BDD @tag → RTM TC-ID 斷鏈
**Check**: ALIGN_REPORT 是否驗證 features/*.feature 中所有 @TC-ID tag 都在 RTM.md 中存在對應條目？是否識別孤立 @tag（features/ 中有但 RTM 不存在的 TC-ID）？逐一核對 features/ 中的所有 @tag 與 RTM TC-ID 清單。
**Risk**: 孤立 @tag 表示 BDD 測試案例未在 RTM 中登記，測試管理工具無法追蹤這些 TC 的執行狀態，覆蓋率統計不完整。
**Fix**: 補充 BDD @tag→RTM TC-ID 一致性驗證，列出所有孤立 @tag；為每個孤立 @tag 在 RTM 中補充對應條目，或移除無效的 @tag。

#### [HIGH] 18 — BRD → PRD 未驗證
**Check**: ALIGN_REPORT 是否驗證每個 BRD Must Have 需求在 PRD 中有對應的 US（US-ID 明確引用 BRD 需求 ID）？是否列出 BRD Must Have 需求總數和 PRD 覆蓋數量？逐一核對 BRD Must Have 清單與 PRD US 清單的對應關係。
**Risk**: BRD→PRD 追溯未驗證，可能有 BRD 的核心業務需求（Must Have）在 PRD 中被遺漏，導致開發出的系統不符合業務方最初的需求定義。
**Fix**: 補充 BRD→PRD 追溯驗證，列出每個 BRD Must Have 需求對應的 PRD US-ID；若有 BRD 需求無對應 PRD US，標記為 CRITICAL Finding。

#### [HIGH] 19 — Dimension 4（Doc→Test）覆蓋不完整
**Check**: ALIGN_REPORT 是否驗證 PRD AC → BDD Scenario @tag → RTM TC-ID 的完整追溯鏈（三層均需驗證）？是否列出每層的覆蓋率數字（如「PRD P0 AC 共 X 條，BDD 覆蓋 Y 條，覆蓋率 Z%」）？
**Risk**: Dimension 4 缺失，無法確認測試覆蓋是否充分，發布前無法量化 P0 功能的驗收覆蓋率，管理層看不到有意義的品質指標。
**Fix**: 補充 Dimension 4 三層追溯驗證（PRD AC → BDD @tag 覆蓋率、BDD @tag → RTM TC-ID 一致性、RTM TC-ID 完整性），並列出每層的覆蓋率數字。

#### [MEDIUM] 20 — 非功能需求覆蓋驗證缺失
**Check**: ALIGN_REPORT 是否驗證 BRD/PRD 中的非功能需求（效能、安全性、可用性）是否在 EDD 中有對應的設計描述，並在 test-plan 中有對應的測試案例？識別未被設計或測試覆蓋的非功能需求。
**Risk**: 非功能需求（如「P95 < 200ms」「99.9% 可用性」）若只在 BRD/PRD 中提及但未在 EDD 中設計、在 test-plan 中驗證，則上線後可能無法達成這些承諾。
**Fix**: 補充非功能需求追溯表（BRD/PRD NFR → EDD 設計章節 → test-plan 測試類型），標記無對應設計或測試的 NFR。

---

### Layer 5: 文件引用正確性（由 Tech Writer 主審，共 5 項）

#### [HIGH] 21 — Finding 描述含模糊用語
**Check**: Finding 描述是否具體到「哪個文件的哪個章節的哪個欄位」？逐一審查所有 Finding 描述，列出使用模糊用語（「EDD 和 PRD 不一致」「文件需要補充」「覆蓋率不足」）的 Finding。
**Risk**: 模糊描述讓工程師無法直接行動，需要自行調查「哪裡不一致」、「補充什麼」，增加修復成本並可能修錯位置。
**Fix**: 將模糊 Finding 描述改寫為具體格式（「EDD §3.2 的 UserRole enum 包含 'super_admin'，但 PRD §5.1 的 AC-003 未提及此角色，兩者不一致」）。

#### [HIGH] 22 — CRITICAL Finding 缺少修復步驟
**Check**: 每個 CRITICAL Finding 是否有具體的修復步驟（指出要修改哪個文件的哪個章節的哪個具體欄位或項目）？逐一審查所有 CRITICAL Finding，列出只說「需修復」或「請補充」而無具體修復步驟的 Finding。
**Risk**: 修復步驟不具體，工程師看到 CRITICAL Finding 後不知道從哪裡開始修復，需要花時間理解上下文才能行動，延遲問題解決。
**Fix**: 為每個 CRITICAL Finding 補充具體修復步驟（格式：「修改 {文件名} §{章節} 的 {欄位/項目}，將 {現況} 改為 {目標狀態}」）。

#### [HIGH] 23 — 嚴重度分級不正確
**Check**: Finding 嚴重度是否與實際業務影響一致？追溯鏈斷裂（如 PRD US 無 BDD Scenario）應為 CRITICAL，術語不一致應為 MEDIUM，文件缺少章節應為 HIGH。逐一審查每個 Finding 的嚴重度，識別分級明顯過低或過高的 Finding。
**Risk**: 嚴重度分級錯誤，工程師按優先順序修復時，輕重緩急判斷錯誤（如把 CRITICAL 追溯斷鏈分級為 LOW 導致被延後修復），影響發布品質。
**Fix**: 依業務影響重新評估每個 Finding 的嚴重度，使用統一標準（CRITICAL=追溯斷鏈或必要文件缺失、HIGH=覆蓋不完整或數字不一致、MEDIUM=術語/格式問題、LOW=排版/佔位符問題）。

#### [MEDIUM] 24 — Finding 無優先修復排序
**Check**: ALIGN_REPORT 是否建議修復順序（先修 CRITICAL → 再修 HIGH → 最後處理 MEDIUM/LOW）？是否說明哪些 Finding 存在依賴關係（如必須先修復 D0 文件缺失才能進行 D1 追溯驗證）？
**Risk**: 無修復排序，工程師從 Finding 清單的任意位置開始修復，可能先修 LOW Finding 而遺漏 CRITICAL 問題，或修復順序不當導致重工（如先修 D1 追溯但上游 D0 文件尚未補充）。
**Fix**: 在 ALIGN_REPORT 末尾補充「建議修復優先順序」章節，按 CRITICAL→HIGH→MEDIUM→LOW 排序，並說明有依賴關係的 Finding 組。

#### [LOW] 25 — Finding 統計數字不正確或裸 Placeholder
**Check**: ALIGN_REPORT 報告末尾的 Finding 統計（CRITICAL/HIGH/MEDIUM/LOW 各 N 個、總計 M 個）是否與正文列出的 Finding 完全一致？是否有 `{{PLACEHOLDER}}` 格式未替換（Finding 描述中的文件路徑、章節引用、數字佔位符等）？
**Risk**: Finding 統計數字不正確，管理層基於錯誤的統計評估風險等級，可能做出錯誤的發布決策。裸 placeholder 讓工程師無法理解 Finding 的具體內容。
**Fix**: 重新計算正文中各嚴重度的 Finding 數量，修正統計表格；替換所有裸 placeholder 為真實的文件路徑、章節引用或具體數字。
