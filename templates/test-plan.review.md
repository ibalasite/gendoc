---
doc-type: test-plan
target-path: docs/test-plan.md
reviewer-roles:
  primary: "資深 QA Architect（Test Plan 審查者）"
  primary-scope: "測試策略完整性、RTM 覆蓋率、測試環境定義、風險評估、自動化策略"
  secondary: "資深 SRE Expert"
  secondary-scope: "效能測試設計、負載測試策略、SLO 驗收測試"
  tertiary: "資深 DevOps Expert"
  tertiary-scope: "CI/CD 測試整合、測試環境可重現性、測試資料管理"
quality-bar: "任何 QA 工程師拿到 Test Plan，能立即開始撰寫測試案例，所有 PRD P0 功能都有對應測試策略，RTM 可直接追溯。"
upstream-alignment:
  - field: PRD User Story 清單
    source: PRD.md §User Story 清單
    check: RTM 中每個 PRD P0 US 是否有 TC 覆蓋（至少一個 Happy Path TC-FUNC 或 TC-E2E）
  - field: API Endpoints 清單
    source: API.md §2 Endpoints
    check: Integration Test 必須覆蓋所有 P0 API Endpoints
  - field: EDD SLO/SLI
    source: EDD.md §10.5 SLO/SLI
    check: Performance Test 目標數字是否與 EDD §10.5 完全對齊
  - field: SCHEMA 關鍵約束
    source: SCHEMA.md
    check: 是否有對應的資料庫測試策略（FK、NOT NULL、Unique Index 驗證）
---

# test-plan Review Items

本檔案定義 `docs/test-plan.md`（含同目錄 RTM 相關內容）的審查標準。由 `/reviewdoc test-plan` 讀取並遵循。
審查角色：三角聯合審查（資深 QA Architect + 資深 SRE Expert + 資深 DevOps Expert）
審查標準：「假設公司聘請一位 15 年 QA 資深顧問，以最嚴格的業界標準進行 Test Plan + RTM 驗收審查。」

---

## Review Items

### Layer 1: 測試策略完整性（由 QA Architect 主審，共 5 項）

#### [CRITICAL] 1 — Test Plan 18 章節缺失
**Check**: Test Plan 是否涵蓋標準章節（§1 Test Strategy / §2 Test Scope / §3 Test Tools / §4 Test Data / §5 Test Environment / §6 Entry/Exit Criteria / §7 Risk / §8 Schedule / §9 Unit Test Plan / §10 Integration Test Plan / §11 E2E Test Plan / §12 Security Test Plan / §13 Performance Test Plan / §14 Accessibility Test Plan / §15 Regression Test Plan / §16 Smoke Test Plan / §17 CI/CD Integration / §18 Reporting）？逐一列出缺失的章節名稱。
**Risk**: 缺少必要章節，QA 工程師執行時缺乏指導，可能遺漏關鍵測試類型（安全測試、效能測試），導致上線後才發現系統性測試漏洞。
**Fix**: 補充所有缺失章節，每個章節需有具體內容；禁止只有章節標題而無內容的空殼章節。

#### [CRITICAL] 2 — 測試目標缺少 SMART 量化指標
**Check**: §1.1 測試目標是否有具體量化指標（如「Unit Test 覆蓋率 ≥ 80%」「PR merge 前由 CI gate 強制驗收」「P99 延遲 ≤ X ms」）？泛化目標（「確保品質」「充分測試」「符合需求」）均視為 finding；逐一列出缺少量化數字的目標條目。
**Risk**: 目標無量化標準，QA 工程師無法判斷何時可以 sign off，管理層也無法判斷測試是否達標，導致測試目標形同虛設。
**Fix**: 依 PRD SLO 和 EDD §10.5，為每個測試目標補充具體數字（覆蓋率 %、延遲 ms、錯誤率 %、AC 通過率）。

#### [HIGH] 3 — lang_stack 測試工具選型不一致
**Check**: §3 Test Tools 中選用的測試框架是否與專案 lang_stack 一致（Python → pytest + coverage.py；Node.js → Jest/Vitest；Go → testing + testify；Java → JUnit + Mockito；PHP → PHPUnit）？逐一列出工具選型與 lang_stack 不一致的項目及正確應選工具。
**Risk**: 工具選型與 lang_stack 不一致，工程師按 Test Plan 安裝錯誤框架，測試無法執行，浪費 Sprint 初期的環境建置時間。
**Fix**: 依 lang_stack 修正 §3 的工具選型，確保每個測試類型（Unit / Integration / E2E / Performance / Security）都有對應工具及版本號。

#### [HIGH] 4 — Test Pyramid 比例與策略未說明
**Check**: §1.3（或相應章節）是否定義了 Test Pyramid 的測試組合比例（Unit ~70% / Integration ~20% / E2E ~10%）及 Automation First 原則（自動化率目標）？若無 Pyramid 說明或比例完全空白，視為 finding。
**Risk**: 無 Pyramid 策略，工程師可能集中在 E2E 測試（執行慢、維護成本高），導致 CI pipeline 過長，Fail-Fast 無法實現。
**Fix**: 補充 Test Pyramid 圖示（Mermaid diagram 或文字說明）及各層比例目標；明確自動化率目標（建議 ≥ 90%）。

#### [HIGH] 5 — §6 Entry/Exit Criteria 缺失或過於泛化
**Check**: §6 是否明確定義 Entry Criteria（進入測試的前提條件，如「Code Review 通過」「Unit Test ≥ 80%」「Staging 環境可用」）和 Exit Criteria（測試完成的驗收條件，如「所有 P0 TC 通過」「無 CRITICAL open defect」「覆蓋率達標」）？泛化描述（「品質達到標準」）視為 finding，逐一列出。
**Risk**: Entry/Exit Criteria 不明確，QA Lead 無法判斷何時可以開始測試或發布，造成發布決策依賴個人判斷而非客觀標準。
**Fix**: 補充具體的 Entry Criteria（至少 3 條量化條件）和 Exit Criteria（至少 4 條含覆蓋率、缺陷清零、Performance Pass 等條件）。

---

### Layer 2: RTM 覆蓋率（由 QA Architect 主審，共 4 項）

#### [CRITICAL] 6 — PRD P0 US 無 TC 覆蓋
**Check**: RTM 中是否每個 PRD P0 User Story 至少有一個 TC（TC-FUNC 或 TC-E2E）？逐一核對 PRD §User Story 清單與 RTM 的 US-ID 欄位，列出無 TC 覆蓋的 US-ID 及 PRD 對應章節。
**Risk**: PRD P0 US 無 TC 覆蓋，核心業務功能未經測試驗證，發布時可能直接在生產環境出現 P0 功能故障。
**Fix**: 為每個無 TC 的 PRD P0 US 補充至少一個 TC（含 Happy Path TC-FUNC 或 TC-E2E），並更新 RTM 所有相關欄位。

#### [CRITICAL] 7 — API Endpoints 無 Integration Test 覆蓋
**Check**: API.md 中所有 P0 API Endpoints 是否在 RTM 的 Integration Test 欄位有對應的 TC-INT 條目？逐一對比 API.md §2 Endpoints 清單與 RTM，列出缺少 TC-INT 的 Endpoint（Method + Path）。
**Risk**: P0 Endpoints 無 Integration Test，API 的回應格式、錯誤碼、Auth 行為未被驗證，前後端整合問題在 E2E 階段才被發現，修復成本高。
**Fix**: 為每個缺少 TC-INT 的 P0 Endpoint 補充 Integration Test 條目，至少涵蓋 200 Happy Path 和 400/401/404 Error Path。

#### [HIGH] 8 — TC-ID 命名規範違規
**Check**: TC-ID 格式是否嚴格遵守 `TC-{TYPE}-{MODULE}-{SEQ}-{CASE}`（如 TC-UNIT-AUTH-001-HappyPath、TC-E2E-ORDER-002-InvalidInput）？逐一掃描 RTM 中所有 TC-ID，列出格式不符的 TC-ID 及其正確格式建議。
**Risk**: TC-ID 命名不規範，BDD @tag 與 RTM 無法對應，CI 報告中的 TC 追溯鏈斷裂，無法自動化驗證覆蓋率。
**Fix**: 依命名規範重新命名所有違規 TC-ID，同步更新 RTM 及對應的 BDD .feature 檔案的 @tag。

#### [HIGH] 9 — 三類情境覆蓋不足（Unit / Integration / E2E）
**Check**: 每個 Module/功能點是否有 Unit（含 Success/Error/Boundary）+ Integration（含 200/400/401/404）+ E2E 三類 TC？逐一核對每個 Module，列出缺少任一類別的 Module 及缺少的 TC 類型。
**Risk**: 缺少任一類別的測試，對應層級的問題無法被捕捉：缺 Unit 導致業務邏輯錯誤漏測，缺 Integration 導致 API 行為漏測，缺 E2E 導致用戶流程漏測。
**Fix**: 為每個缺少類別的 Module 補充對應類型的 TC 並更新 RTM；補充原則：每個 Module 至少有 Unit + Integration 兩類，P0 Module 必須有 E2E。

#### [HIGH] 9b — Unit Test 未依 Clean Architecture 層次組織
**Check**: §3.1 Unit Tests 是否明確區分以下三層測試策略？(1) Domain 層（`<<AggregateRoot>>`/`<<Entity>>`/`<<ValueObject>>`）：完全隔離，無任何 DB/HTTP/ORM import；(2) Application 層（`<<UseCase>>`/`<<ApplicationService>>`）：mock Interface，不啟動 DB；(3) Infrastructure 層（`<<RepositoryImpl>>`/`<<Adapter>>`）：列入 Integration Test，使用 Testcontainers。若三層未區分、或 Domain 層測試引用了 DB/ORM 依賴視為 HIGH。
**Risk**: Domain / Application / Infrastructure 測試策略混用，Domain 層測試啟動 DB（慢且脆弱）；Application 層測試未 mock Repository（測試了 Infrastructure 而非業務邏輯）；CI 執行時間增加，且 Infrastructure 問題被錯誤診斷為業務邏輯問題。
**Fix**: 依 EDD §3.1b Dependency Rule 和 `docs/diagrams/class-inventory.md` 的 Stereotype + Layer 欄位重新組織 §3.1；Domain 層測試不得引用任何 ORM / DB / HTTP 依賴；Application 層測試改用 mock Interface 注入；`<<RepositoryImpl>>`/`<<Adapter>>` 測試移至 §3.2 Integration Tests。

---

### Layer 3: 測試環境（由 DevOps Expert + QA Architect 聯合審查，共 4 項）

#### [CRITICAL] 10 — 測試環境規格未定義
**Check**: §5 是否說明各類型測試（Unit / Integration / E2E / Performance）的執行環境（Local / CI / Staging）及環境差異（如 Integration 使用 Test DB、E2E 使用 Staging DB）？是否說明環境建置步驟（`docker-compose up` 或 `make test-env`）？逐一列出缺少環境規格的測試類型。
**Risk**: 測試環境規格不明，工程師不知道在哪個環境執行哪類測試，可能在錯誤環境執行（如在 Production 環境執行 E2E），或環境差異導致「在我機器上可以」問題。
**Fix**: 為每個測試類型補充執行環境說明（環境名稱、DB 設定、External Service Mock 策略、環境重置方式、啟動命令）。

#### [HIGH] 11 — 測試資料策略未定義
**Check**: §4 是否說明測試資料的建立策略（Factory / Fixture / Seed Data）和清除策略（每個 Test Case 後清除 vs. Shared Fixtures）？是否說明隔離機制（Transaction Rollback / 獨立 Schema / TestContainers）？
**Risk**: 測試資料策略不明，工程師使用不一致的資料建立方式，導致測試間相互干擾（Test Pollution），測試結果不穩定，CI 有時通過有時失敗。
**Fix**: 在 §4 補充完整的測試資料策略：（1）建立方式（Factory 函式 / Fixture 檔案 / Seed Script），（2）清除時機（每個 Test Case 後 / 每個 Test Suite 後），（3）隔離機制說明。

#### [HIGH] 12 — Mock/Stub 策略缺失
**Check**: §10 Integration Test 是否說明 External Dependencies 的 Mock 策略（DB Mock vs. Real Test DB、External API Mock vs. Sandbox、Message Queue Mock vs. Real Queue）？逐一列出缺少 Mock 策略說明的 External Dependency。
**Risk**: Mock 策略不明，不同工程師對同一 External Dependency 使用不同 Mock 方式，導致 Integration Test 行為不一致，難以 Debug Mock 相關問題。
**Fix**: 為每個 External Dependency 補充 Mock 策略說明（使用哪個工具、Mock 層級、何時用 Real vs. Mock）。

#### [MEDIUM] 13 — SCHEMA 資料庫測試策略缺失
**Check**: §10 Integration Test 或相應章節是否包含針對 SCHEMA.md 定義的資料庫約束的測試策略（FK Constraint 測試、NOT NULL 邊界測試、Unique Index 衝突測試、SCHEMA 遷移回滾測試）？若 SCHEMA.md 存在但無對應 DB 測試策略，視為 finding。
**Risk**: 資料庫約束無測試覆蓋，FK 違反、NULL 值插入等 DB 層面問題在整合測試中無法發現，直到生產資料出現異常才暴露。
**Fix**: 補充資料庫測試策略章節，至少涵蓋 FK Constraint 測試、Unique Index 測試、Migration 回滾測試三類。

---

### Layer 4: 自動化策略（由 DevOps Expert 主審，共 3 項）

#### [CRITICAL] 14 — CI/CD 觸發條件未定義
**Check**: §17 是否說明各類型測試的 CI 觸發條件（Unit: 每次 PR / Integration: Merge to main / E2E: Release Branch / Performance: 週期性排程）？是否說明 CI 失敗時的處理方式（Block merge vs. Warning only）？逐一列出未定義觸發條件的測試類型。
**Risk**: CI/CD 觸發條件不明，可能導致 Integration Test 未在 PR 時執行，Bug 在 Merge 後才被發現，修復成本翻倍；或 E2E 從未自動觸發，成為純粹的手動測試負擔。
**Fix**: 為每個測試類型補充 CI 觸發條件（觸發事件、Pipeline Stage、執行時間預算、失敗是否 Block merge）。

#### [HIGH] 15 — 自動化率目標缺失
**Check**: §17 或 §1.2 是否明確定義自動化率目標（整體 ≥ 90%、E2E Smoke 100%、Regression 80% 等）？是否說明哪些測試不適合自動化（UAT、探索性測試）及原因？若完全無自動化率相關說明，視為 finding。
**Risk**: 無自動化率目標，測試工作可能大量依賴手動測試，CI pipeline 無法提供可靠的質量門控，導致 QA 瓶頸。
**Fix**: 補充自動化率目標（按測試類型分別說明），並列出手動測試的範圍和理由。

#### [MEDIUM] 16 — §16 Smoke Test 範圍未定義
**Check**: §16 是否明確定義 Smoke Test 的範圍（覆蓋哪些 P0 功能）、觸發時機（每次部署後）、執行時間上限（通常 ≤ 5 分鐘）？若 Smoke Test 章節只有標題或泛化描述，視為 finding。
**Risk**: Smoke Test 範圍不明，部署後無法快速驗證系統基本可用性，意外在 Staging 或 Production 環境靜默失敗。
**Fix**: 補充 Smoke Test 清單（按 P0 功能列出至少 5 個核心測試項）、觸發腳本路徑、執行時間目標和失敗處理流程。

---

### Layer 5: 效能與負載測試（由 SRE Expert 主審，共 4 項）

#### [CRITICAL] 17 — SLO 效能目標缺少具體數字
**Check**: §13 效能測試是否有具體量化目標（P95/P99 延遲 ms、Throughput QPS、Error Rate %、Concurrent Users 數量）？泛化目標（「系統應快速回應」「效能應符合預期」）均視為 finding；逐一列出缺少具體數字的效能目標，並與 EDD §10.5 SLO 比對。
**Risk**: 效能測試目標無具體數字，無法判斷效能測試是否通過，Pass/Fail 標準模糊導致效能問題被忽略，直到上線後才發現 SLO 違反。
**Fix**: 以 EDD §10.5 SLO/SLI 為依據，為每個效能目標補充具體數字（P95 ≤ X ms、Throughput ≥ Y QPS、Error Rate ≤ Z%）。

#### [HIGH] 18 — 負載測試場景未定義
**Check**: §13 是否定義具體的負載測試場景（Normal Load、Peak Load、Stress Test、Soak Test 四種）？每個場景是否有測試工具（k6 / Locust / JMeter）、RPS 或 Concurrent Users 設定、測試時長？若完全無場景說明，視為 finding。
**Risk**: 負載測試場景不明確，無法模擬真實流量模式，效能測試結果無法反映生產環境下的行為，SLO 無法被有效驗證。
**Fix**: 補充至少 2 個負載測試場景（Normal Load + Peak Load），每個場景含：工具、RPS/Users、持續時間、Pass/Fail 標準。

#### [HIGH] 19 — OWASP A01-A10 安全測試覆蓋
**Check**: §12 安全測試章節是否逐項說明 OWASP A01-A10 的測試方式（A01: Broken Access Control、A02: Cryptographic Failures、A03: Injection、A04: Insecure Design、A05: Security Misconfiguration、A06: Vulnerable Components、A07: Authentication Failures、A08: Software Integrity Failures、A09: Logging Failures、A10: SSRF）？只列名稱不說明測試方式視為 finding；逐一列出缺少測試方式說明的項目。
**Risk**: OWASP 安全測試說明不具體，QA 工程師無法執行安全測試，關鍵安全漏洞（SQL Injection、認證繞過）未被測試覆蓋，造成安全合規風險。
**Fix**: 為每個 OWASP A01-A10 項目補充具體測試方式（工具名稱、測試案例描述、驗收標準）。

#### [MEDIUM] 20 — 效能測試環境與工具缺失
**Check**: §13 是否說明效能測試所需的專用環境規格（與 Integration Test 環境隔離、資料量要求）、使用工具版本和執行命令？若效能測試只有目標數字但無環境和工具說明，視為 finding。
**Risk**: 效能測試環境規格不明，在不一致的環境下執行效能測試，結果不可重現，無法作為 SLO 驗收依據。
**Fix**: 補充效能測試環境規格（硬體/雲端規格、資料量要求）、工具版本及執行命令（如 `k6 run --vus 100 --duration 5m scripts/load-test.js`）。

---

### Layer 6: 上游對齊（由 QA Architect 通盤審查，共 3 項）

#### [HIGH] 21 — Boundary Value Analysis（BVA）缺失
**Check**: 數值型輸入的 TC 是否包含邊界值（最小值、最大值、最小值-1、最大值+1）？逐一審查含數值輸入的 TC，識別只有正常值而缺少邊界值測試的情況，列出缺漏的邊界值 TC 及對應的 PRD/SCHEMA 規格來源。
**Risk**: 缺少邊界值測試，邊界條件的 Bug（如 `<` 應為 `<=`、整數溢位）在測試階段無法發現，直到生產環境邊界情境觸發才暴露。
**Fix**: 為每個數值型輸入補充邊界值 TC（min、max、min-1、max+1），並更新 RTM。

#### [MEDIUM] 22 — Integration TC 缺少 401/403 情境
**Check**: 每個需要 Auth 的 API Integration TC 是否包含 401（Token 無效/過期）和 403（Token 有效但權限不足）兩種錯誤情境？逐一核對需要 Auth 的 API TC，列出缺少 401 或 403 情境的 TC 及對應 Endpoint。
**Risk**: 缺少 401/403 測試，認證授權邏輯的缺陷（未驗證 Token、權限邊界錯誤）無法被測試覆蓋，影響系統安全性。
**Fix**: 為每個需要 Auth 的 API 補充 401 TC（Token 無效）和 403 TC（Token 有效但權限不足），並更新 RTM。

#### [LOW] 23 — 裸 Placeholder
**Check**: 是否有 `{{PLACEHOLDER}}` 格式未替換（Module 名稱、TC-ID 格式範例、工具版本號、環境 URL、RPS 數字等）？逐一掃描全文，列出所有裸 placeholder 及其位置（章節）。
**Risk**: 裸 placeholder 讓 QA 工程師看到不完整的資訊，需自行猜測正確值，增加出錯機會；含 placeholder 的工具版本號也會導致環境建置失敗。
**Fix**: 替換所有裸 placeholder 為真實的 Module 名稱、TC-ID 範例或具體版本號；若暫時無法確定，加上 `（待確認：說明）` 取代空白 placeholder。

---

### Layer 5: HA / Failover / Chaos 測試覆蓋（由 SRE / QA Lead 主審，共 4 項）

#### [CRITICAL] 24 — HA Failover 測試缺失（放在 Future Scope）
**Check**: §2.3 Future Scope 是否包含「HA Failover」或「高可用性驗證」？若有，視為 CRITICAL（HA 是架構前提，不是 Future Scope）。  
同時確認 §3.6 是否存在 HA/Failover/Chaos 測試策略（包含 Integration Test + E2E Chaos Scenario + 本地驗證）。
**Risk**: 將 HA 測試列為 Future Scope，等同宣告「MVP 上線時可接受單點故障」——與 EDD §3.6 HA 架構設計矛盾，且發生故障時無測試保護。
**Fix**: 從 §2.3 移除 HA Failover；在 §3.6 新增 HA/Failover/Chaos 測試策略（Integration Test + E2E Chaos Scenario + 本地驗證），每個有 Replica 的元件至少一個強制終止場景。

#### [CRITICAL] 25 — HA 測試場景無具體通過條件
**Check**: §3.6 HA 測試場景的「通過條件」是否含有具體數字（如「≤ 5s 內新 pod ready」「Failover ≤ 30s」）？若只寫「服務恢復正常」或「不報錯」等模糊條件，視為 CRITICAL。
**Risk**: 通過條件模糊，測試結果無法客觀判定（5 分鐘恢復是通過嗎？），SLO（≥ 99.9% 可用性）無法被測試保護。
**Fix**: 對每個 HA 場景補充量化通過條件：Pod 重啟 → ≤ 5s 新 pod ready；DB Failover → ≤ 30s 完成切換；期間 5XX 錯誤率 ≤ 0.1%。所有數字從 EDD §3.6 SLO 推算。

#### [HIGH] 26 — 缺少 Graceful Shutdown E2E 場景
**Check**: §3.6 是否包含 Graceful Shutdown 場景（SIGTERM → 停止接受新請求 → in-flight 請求在 30s 內完成 → 退出）？若無此場景，視為 HIGH。
**Risk**: 無 Graceful Shutdown 測試，每次 Deploy 都可能造成 in-flight 請求 502/503；canary/rolling update 期間用戶看到間歇性錯誤。
**Fix**: 在 §3.6.2 E2E Chaos Scenarios 補充 `@ha @graceful-shutdown` Gherkin 場景，通過條件：Pod 收到 SIGTERM 後，現有 5 秒請求正常完成，新請求轉至其他 Pod。

#### [HIGH] 27 — 本地 HA 驗證腳本缺失
**Check**: §3.6 是否包含可直接執行的本地 HA 驗證腳本（kubectl 指令）？是否確認 Local Dev 環境有 ≥ 2 API replicas（遵循 EDD §3.7 圖 B）？
**Risk**: 無本地驗證腳本，開發者無法在 PR 合併前驗證 HA 相關程式碼（shared state、distributed lock、pub/sub）是否正確，HA Bug 留到 Staging 才發現，修改成本高。
**Fix**: 在 §3.6.3 補充本地 HA 驗證腳本：確認 ≥ 2 API replicas 的 kubectl 指令、強制終止一個 Pod 並驗證服務不中斷的完整流程。
