---
doc-type: RTM
target-path: docs/RTM.md
reviewer-roles:
  primary: "資深 QA Architect（主審，共 10 項）"
  primary-scope: "覆蓋率完整性、追溯完整性、孤立 Test Case 偵測、統計數字一致性"
  secondary: "資深 Backend Engineer"
  secondary-scope: "Unit Test 追溯準確性、API Endpoint 覆蓋、Integration Test 設計合理性"
  tertiary: "資深 Frontend QA Expert"
  tertiary-scope: "E2E 追溯、BDD @tag 對齊、Client 端 User Story 覆蓋"
quality-bar: "100% PRD P0 User Stories 有對應 Test Case；所有 BDD @smoke tag 在 RTM 有條目；無孤立 Test Case；§1 統計數字與正文完全一致。"
upstream-alignment:
  - field: P0 User Story 清單
    source: PRD.md §5 User Stories（MoSCoW P0）
    check: RTM §3～§5 是否每個 PRD P0 US 都有至少一個 Unit Test 或 E2E 追溯條目
  - field: API Endpoint 清單
    source: API.md §3 Endpoints
    check: RTM §4 Integration Test 追溯表是否覆蓋所有 API Endpoints（含 CRUD + error path）
  - field: BDD @tag 清單
    source: features/ BDD Feature Files（@smoke、@p0 等）
    check: RTM §5 E2E 追溯表是否涵蓋所有 @smoke / @p0 標記的 Scenario
  - field: 測試環境與覆蓋率目標
    source: test-plan.md §3 測試策略
    check: RTM §1 Summary Statistics 的覆蓋率數字是否達到 test-plan 設定的目標
---

# RTM Review Items

本檔案定義 `docs/RTM.md` 的審查標準。由 `/reviewdoc RTM` 讀取並遵循。
審查角色：三角聯合審查（資深 QA Architect + 資深 Backend Engineer + 資深 Frontend QA Expert）
審查標準：「假設公司聘請一位 10 年以上資深 QA Architect 顧問，以最嚴格的業界標準進行 RTM 驗收審查。」

---

## Review Items

### Layer 1: PRD 需求覆蓋完整性（由 QA Architect 主審，共 5 項）

#### [CRITICAL] 1 — P0 User Story 未追溯
**Check**: 逐一比對 PRD §5 的 MoSCoW P0 User Stories，RTM §3～§5 是否每個 P0 US 都有至少一個對應的 Test-ID（Unit / Integration / E2E 任一）？列出缺漏的 US-ID。
**Risk**: P0 需求無對應測試 = 核心功能在上線前可能未被驗證。若缺漏在 CI/CD 後才被發現，將需要緊急補測，延誤發佈時程。
**Fix**: 在 RTM §3 或 §5 為每個缺漏的 P0 US 補充至少一筆追溯條目（Unit Test 或 E2E Scenario），並更新 §6 快查索引。

#### [CRITICAL] 2 — 孤立 Test Case（有測試無需求）
**Check**: RTM 中所有 Test-ID 是否都可追溯回 PRD 的至少一個 US-ID 或 BRD 的業務需求？列出無法追溯的孤立 Test-ID。
**Risk**: 孤立 Test Case 顯示測試超出需求範圍或需求文件未更新，造成測試資源浪費，並在審計時無法提供合規證明。
**Fix**: 為孤立 Test-ID 補充對應的 US-ID（若功能有效），或將其標記為 DEPRECATED 並說明原因，更新 §6 快查索引。

#### [HIGH] 3 — RTM §1 統計數字不一致
**Check**: §1 Summary Statistics 的數字（Total US、Covered US、Coverage %、Test Case 總數）是否與 §3、§4、§5 正文的實際條目數完全一致？手動計算後比對。
**Risk**: 統計摘要與正文不一致是文件品質問題，在管理層審查或審計時失去可信度，並可能掩蓋真實的覆蓋缺口。
**Fix**: 重新計算 §3、§4、§5 的實際條目數，更新 §1 所有統計數字（含百分比），確保 Total = Covered + Uncovered。

#### [HIGH] 4 — §1.1 覆蓋率視覺化與統計不一致
**Check**: §1.1 的 ASCII 進度條（`■` 填充比例）是否對應 §1 的覆蓋率百分比？若有分層覆蓋率（Unit/Integration/E2E），各層是否分別標注？
**Risk**: 視覺化不準確會誤導讀者判斷測試健康度，特別是在管理層快速瀏覽時。
**Fix**: 依 §1 數字重新計算並更新 §1.1 進度條，Unit/Integration/E2E 分別計算並標注。

#### [MEDIUM] 5 — Status 狀態碼未統一使用
**Check**: §3、§4、§5 追溯表中所有 Status 欄位是否只使用 §2 定義的狀態碼（PASS / FAIL / WIP / SKIP / PLANNED）？有無非標準狀態碼（如 "OK"、"Done"、"-"）？
**Risk**: 非標準狀態碼使自動化解析失敗（§8 CSV export 依賴標準碼），並造成 §1 統計計算錯誤。
**Fix**: 將所有非標準狀態碼替換為 §2 定義的標準碼，並確認 §8 CSV 同步更新。

---

### Layer 2: API Endpoint 追溯（由 Backend Engineer 主審，共 4 項）

#### [CRITICAL] 6 — API Endpoint 未追溯
**Check**: 比對 API.md §3 列出的所有 Endpoints，RTM §4 Integration Test 追溯表是否涵蓋每個 Endpoint 的至少一個 Happy Path 測試？列出缺漏的 Endpoints。
**Risk**: 未測試的 API Endpoint 在上線後可能暴露未知缺陷，API 層是前後端整合失敗的最常見點。
**Fix**: 為每個缺漏的 Endpoint 在 §4 補充追溯條目，標注 INT-ID、Endpoint URL、Method、Test Case、Status。

#### [HIGH] 7 — Error Path 測試缺失
**Check**: §4 Integration Test 追溯表中，是否有至少 30% 的 Test Case 對應 Error Path（4xx/5xx 回應）？特別確認 401/403、400 Validation Error、500 的覆蓋。
**Risk**: 僅測試 Happy Path 無法驗證系統在錯誤狀態下的行為，Auth 問題和 Validation 缺陷是生產環境最常見的回歸問題。
**Fix**: 在 §4 補充 Error Path Test Case，為每個主要 Endpoint 加入至少一筆 4xx 追溯條目，並更新 §1 統計。

#### [HIGH] 8 — §4.2 欄位格式不符合 §4.1 說明
**Check**: §4.2 追溯表的所有欄位是否與 §4.1 欄位說明完全對應（INT-ID、US-ID、HTTP Method、Endpoint URL、Scenario、Tool、Status、Notes）？有無遺漏欄或多餘欄？
**Risk**: 欄位不一致使 §8.2 CSV Export 無法正確解析，並影響後續自動化工具讀取 RTM 資料。
**Fix**: 對照 §4.1，補充或移除 §4.2 中不一致的欄位，確保每行條目與欄位說明完全對應。

#### [MEDIUM] 9 — Integration Test Tool 未標注
**Check**: §4.2 中每個 Test Case 的「Tool」欄位是否填入具體工具名稱（如 pytest、Postman、RestAssured、k6），而非空白或泛稱「API Test」？
**Risk**: Tool 欄空白導致無法判斷測試的可重現性和自動化程度，在 CI/CD 整合分析時缺少關鍵資訊。
**Fix**: 為每個 Integration Test 條目填入具體工具名稱，若使用多個工具，以逗號分隔標注。

---

### Layer 3: E2E 與 BDD 追溯（由 Frontend QA Expert 主審，共 4 項）

#### [CRITICAL] 10 — BDD @smoke Scenario 未追溯
**Check**: 從 `features/` 目錄讀取所有標記 `@smoke` 或 `@p0` 的 BDD Scenario，確認每個 Scenario 都在 RTM §5 E2E 追溯表中有對應條目（E2E-ID → Feature File → Scenario Title）？
**Risk**: @smoke Scenario 是 Release Gate 的最後防線；若 RTM 未追溯，CI/CD 管道無法確認哪些場景被覆蓋，也無法在 Sprint Review 向 Stakeholder 展示驗收狀態。
**Fix**: 在 §5 為所有缺漏的 @smoke / @p0 Scenario 補充追溯條目，更新 §6 快查索引並更新 §1 E2E 覆蓋率統計。

#### [HIGH] 11 — E2E Test 缺乏 Client 端分層
**Check**: §5 E2E 追溯表是否區分 Web Client、Mobile、或其他 Client 類型（若 PRD 定義多個 Client）？是否有對應 `features/client/` 的追溯條目？
**Risk**: 單一 E2E 層無法分辨不同 Client 的測試覆蓋狀況，Web 通過的功能未必在 Mobile 上也通過。
**Fix**: 在 §5 追溯表加入 Client-Type 欄位，或以子表格分層標注 Server-side E2E vs Client-side E2E。

#### [MEDIUM] 12 — §5 E2E 缺少 Page/Feature File 位置
**Check**: §5.2 追溯表中每個 E2E 條目是否標注 Feature File 路徑（如 `features/auth/login.feature`）和 Scenario 標題？
**Risk**: 缺少 Feature File 位置使開發人員無法直接定位 E2E 腳本，增加除錯成本。
**Fix**: 在 §5.2 每個條目的 Notes 欄補充 Feature File 路徑和 Scenario 全名。

#### [LOW] 13 — §6 快查索引與正文不同步
**Check**: §6 Req-ID ↔ Test-ID 快查索引是否涵蓋所有 §3、§4、§5 出現的 US-ID 和 Test-ID？若有條目在正文中新增但未更新索引，逐一列出。
**Risk**: 快查索引失效使 RTM 喪失快速定位能力，在 Sprint Review 或緊急除錯時需逐行翻閱正文。
**Fix**: 重新掃描 §3～§5 所有 US-ID 和 Test-ID，更新 §6 確保完整覆蓋，建議以字母/數字排序。

---

### Layer 4: 缺陷追蹤與 CSV Export 品質（由 QA Architect 主審，共 4 項）

#### [HIGH] 14 — §7 FAIL 缺陷追蹤缺漏
**Check**: §3～§5 中所有 Status = FAIL 的條目，是否都在 §7 FAIL 缺陷追蹤快查中有對應記錄（含 Defect-ID、失敗原因、優先級、負責人）？列出未記錄的 FAIL Test-ID。
**Risk**: FAIL 條目未追蹤缺陷代表已知問題沒有責任人和修復計畫，可能在下次 Release 時再次出現。
**Fix**: 為每個 FAIL Test-ID 在 §7 建立對應記錄，填入 Defect-ID（Jira/Linear ticket）、失敗原因、P0/P1/P2 優先級、負責人和預計修復日期。

#### [HIGH] 15 — §8 CSV Export 格式破損
**Check**: §8.1～§8.4 的 CSV 區塊是否使用正確分隔符（逗號）、每行欄位數一致、無換行符嵌入欄位、Header 行正確？用逗號計數驗證每行欄位數是否與 Header 一致。
**Risk**: 格式破損的 CSV 無法被 CI/CD 自動化工具或報表系統解析，RTM 的機器可讀功能完全失效。
**Fix**: 修正格式破損的 CSV 行，含有逗號的欄位值用雙引號包覆，確保所有行的欄位數與 Header 一致。

#### [MEDIUM] 16 — §8.4 Summary CSV 計算錯誤
**Check**: §8.4 Summary Statistics CSV 中的各項覆蓋率數字是否與 §1 的數字完全一致？Total、Covered、Coverage% 是否正確計算？
**Risk**: Summary CSV 的計算錯誤會傳播到依賴此 CSV 的 Dashboard（如 HTML report 的覆蓋率圖表），造成管理層決策依據失真。
**Fix**: 重新計算 Coverage% = Covered / Total，更新 §8.4 所有數字，確保與 §1 完全一致。

#### [MEDIUM] 17 — 裸佔位符殘留
**Check**: 掃描全文，是否有未填入真實值的裸佔位符（`{{...}}`、`<placeholder>`、`[TBD]`）？列出所有殘留位置。
**Risk**: 裸佔位符殘留代表 RTM 尚未完成，若在 Sprint Review 或審計中呈現，失去文件可信度。
**Fix**: 逐一填入實際值，若資訊真的未知，標注「PLANNED - Sprint {{N}}」並說明原因，而非留裸佔位符。

---

### Layer 5: 上游對齊與文件完整性（由 QA Architect + Backend Engineer 聯合審查，共 3 項）

#### [HIGH] 18 — test-plan 覆蓋率目標未達到
**Check**: test-plan.md §3 設定的覆蓋率目標（如「Unit Test ≥ 80%」、「E2E P0 ≥ 95%」）與 RTM §1 的實際覆蓋率比較，是否達標？列出未達標的測試層級。
**Risk**: 覆蓋率不達標代表 Release 風險過高，若在 Release Gate 才發現，將無法在 Sprint 內補救。
**Fix**: 比對差距，在 RTM §7 缺陷追蹤或補充說明中標注哪些 US 需要補充測試，提供修復優先順序建議。

#### [HIGH] 19 — Document Control 資訊未填入
**Check**: Document Control 表格中 DOC-ID、Project Name、Version、Status、Author、Date 是否全部填入真實值？Change Log 是否有至少一筆初始版本記錄？
**Risk**: Document Control 空白的 RTM 無法通過合規審查，也無法追蹤文件版本歷史。
**Fix**: 填入所有 Document Control 欄位，Change Log 加入初始版本記錄（v1.0、日期、作者、建立說明）。

#### [LOW] 20 — §0 說明區塊缺失
**Check**: RTM §0「什麼是 RTM？」的說明是否存在且對非技術讀者（PM、Stakeholder）清楚解釋 RTM 的用途和如何閱讀追溯表？
**Risk**: 缺少說明導致非技術讀者誤解 RTM 的用途，或在 Sprint Review 中需要口頭額外解釋，降低文件自説明性。
**Fix**: 確認 §0 存在且包含：RTM 定義、如何閱讀（US-ID → Test-ID 方向）、各層測試的涵義、Status 說明的指引。

---

## Escalation Protocol

- **CRITICAL**：任一 CRITICAL 項目未通過 → 停止審查，立即修正後重審
- **HIGH**：≥ 3 項 HIGH 未通過 → 視為高風險，回頭修正後繼續
- **MEDIUM/LOW**：累計記錄，不阻擋流程

---

## Completion Criteria

- 所有 CRITICAL 項目通過（P0 覆蓋 100%、無孤立 Test Case、BDD @smoke 全追溯）✅
- HIGH 未通過項目 < 3 ✅
- §1 統計數字與正文一致 ✅
- §8 CSV 格式可被機器解析 ✅
- 上游對齊欄位全部確認（PRD P0、API Endpoints、BDD @smoke、test-plan 目標）✅

> 由 `/reviewdoc RTM` 自動執行本 checklist。


---

## Self-Check：欄位完整性驗證

> RTM 為表格結構，此節驗證欄位完整性而非 H2 章節數。

**指令：**
1. 讀取 `docs/RTM.md`，確認主表格含以下欄位：需求 ID、功能描述、API Endpoint、BDD Scenario、Test Case
2. 逐行確認：無空欄（`—` 或 `N/A` 須有明確理由）
3. 與上游對齊：所有 PRD P0 需求有對應行，所有 API Endpoint 有對應行
4. 任何欄位缺失或上游引用不存在 → CRITICAL finding

**通過條件：**
- 所有 PRD P0 需求有對應 RTM 行
- 所有 API Endpoint 有對應 RTM 行
- 所有 RTM 行有對應的 BDD Scenario 或 Test Case ID
