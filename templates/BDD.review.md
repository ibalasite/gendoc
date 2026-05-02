---
doc-type: BDD
target-path: docs/BDD.md
reviewer-roles:
  primary: "資深 BDD Expert / QA Architect（主審，共 10 項）"
  primary-scope: "BDD 慣例品質、Given/When/Then 語義正確性、Tag Taxonomy 完整性、Feature File 命名規範、Step 可維護性"
  secondary: "資深 Backend Engineer"
  secondary-scope: "API/Server-side BDD 覆蓋度、契約測試完整性、Step 實作可行性"
  tertiary: "資深 Frontend QA Expert"
  tertiary-scope: "E2E / Client-side BDD 覆蓋度、Visual Regression 策略、測試資料管理"
quality-bar: "任何工程師接手此 BDD 文件後，不需詢問 QA，能立即撰寫符合規範的 Feature File 並通過 CI/CD Gate。"
upstream-alignment:
  - field: P0 User Story 清單
    source: PRD.md §5 User Stories（MoSCoW P0）
    check: BDD §3 Feature File Template 的 @tag 分類是否涵蓋所有 P0 US 對應的 Feature
  - field: API Endpoint 清單
    source: API.md §3 Endpoints
    check: BDD §12.1 BDD ↔ OpenAPI 追溯矩陣是否列出所有主要 API Endpoint 的契約測試對應
  - field: 測試金字塔策略
    source: test-plan.md §3 Test Pyramid
    check: BDD §1 Test Pyramid Placement 的定位是否與 test-plan 設定的 BDD 覆蓋比例一致
---

# BDD Review Items

本檔案定義 `docs/BDD.md` 的審查標準。由 `/reviewdoc BDD` 讀取並遵循。
審查角色：三角聯合審查（資深 BDD Expert/QA Architect + 資深 Backend Engineer + 資深 Frontend QA Expert）
審查標準：「假設公司聘請一位 10 年以上資深 BDD/TDD 顧問，以最嚴格的業界標準進行 BDD 慣例文件驗收審查。」

> 注意：本檔案審查 `docs/BDD.md`（BDD 慣例規範文件）。實際 Feature File 的審查請使用
> `/reviewdoc BDD-server`（`features/*.feature`）和 `/reviewdoc BDD-client`（`features/client/*.feature`）。

---

## Review Items

### Layer 1: Tag Taxonomy 完整性（由 BDD Expert 主審，共 4 項）

#### [CRITICAL] 1 — @tag 分類體系不完整
**Check**: §2.3 Tag Taxonomy 是否至少定義以下必要 tag 類別：優先級（@p0/@p1/@p2）、測試層級（@smoke/@regression/@integration）、功能模組（@auth/@payment 等）、執行排除（@wip/@skip）？列出缺漏的分類。
**Risk**: Tag 分類體系不完整導致 CI/CD 無法精準篩選 Smoke Test，Nightly Build 無法只跑 @regression，Release Gate 無法確認 @p0 全通過。
**Fix**: 在 §2.3 補充缺漏的 tag 類別，每個 tag 說明用途、適用場景、在 CI/CD 哪個階段執行。

#### [CRITICAL] 2 — @smoke 定義模糊或缺失
**Check**: §2.3 中 @smoke tag 是否明確定義：適用範圍（P0 Happy Path only / 所有 P0 Scenario？）、執行時間上限（如 < 5 分鐘）、在哪個 CI Stage 執行（PR Merge / Deploy / 兩者）？
**Risk**: @smoke 定義模糊導致各工程師對「什麼要加 @smoke」判斷不一，PR Gate 效果不穩定，上線品質管控失效。
**Fix**: 在 §2.3 @smoke 說明中加入：定義（必須在 PR Merge 前通過）、執行時間上限、覆蓋範圍（P0 Happy Path + Critical Error Path）、與 @regression 的區別。

#### [HIGH] 3 — Feature File 命名規範不夠具體
**Check**: §2.1 Path Pattern 和 §2.2 Naming Examples 是否包含足夠的例子（至少 5 個不同功能的 Feature File 命名示例）？命名規則是否明確區分 Server-side 和 Client-side 路徑？
**Risk**: 命名規範不具體導致不同工程師在 `features/` 目錄下建立不一致的目錄結構，破壞 RTM 追溯和 CI/CD 路徑配置。
**Fix**: 在 §2.1 補充 Server-side (`features/*.feature`) vs Client-side (`features/client/*.feature`) 的路徑規則，在 §2.2 增加至少 5 個涵蓋不同功能模組的命名示例。

#### [MEDIUM] 4 — Background Section 使用條件未說明
**Check**: §7 Background Section Pattern 是否說明何時應使用 Background（超過 3 個 Scenario 共用同一前置條件）vs 何時不應使用（複雜的資料設定應用 Hooks/Fixtures）？
**Risk**: Background 濫用導致 Feature File 可讀性下降，特別是有多個 Scenario 但 Background 只對部分有意義時。
**Fix**: 在 §7 開頭加入「適用條件」段落（使用場景 vs 不適用場景），並說明複雜前置條件應改用 Hooks 的判斷原則。

---

### Layer 2: Given/When/Then 語義品質（由 BDD Expert + Backend Engineer 聯合審查，共 4 項）

#### [CRITICAL] 5 — Forbidden Patterns 未定義或不完整
**Check**: §4.5 禁止模式是否涵蓋以下常見錯誤：技術實作細節洩漏（如「當 API 呼叫 /api/v1/users」）、Given 包含 Action（如「Given 使用者已登入並點擊按鈕」）、Then 包含多個斷言（如「Then 回應碼 200 且 body 包含 name 欄位且 email 格式正確」）？
**Risk**: 缺乏明確的禁止模式導致 Feature File 混入實作細節，BDD 的「活文件」特性喪失，未來重構實作時 Feature File 必須同步修改，維護成本極高。
**Fix**: 在 §4.5 補充完整的禁止模式列表，每個模式提供：❌ 反例（Bad）+ ✅ 正例（Good），說明為何禁止。

#### [HIGH] 6 — Step 原子性原則未明確
**Check**: §4.2 When 章節是否明確說明「每個 When 只能有一個 Action」原則？是否有示例展示如何將複合 Action 拆分？
**Risk**: When 包含多個 Action 導致 Scenario 顆粒度過粗，測試失敗時無法精確定位是哪個 Action 失敗，除錯效率低。
**Fix**: 在 §4.2 加入「複合 Action 拆分指南」，提供 Before/After 示例，說明如何將「使用者填入 Email、密碼並點擊登入」拆分為獨立的 Scenario 或使用 And 正確延伸。

#### [HIGH] 7 — Step 可觀測性（Then 的 Observability）未強調
**Check**: §4.3 Then 章節是否強調 Then 步驟必須描述「可觀測的預期結果」而非內部狀態（如禁用「Then 資料庫中有一筆記錄」，應改為「Then 使用者收到確認 Email」）？
**Risk**: Then 描述內部狀態而非外部行為，違反 BDD 「行為驅動」核心原則，導致非技術 Stakeholder 無法閱讀 Feature File。
**Fix**: 在 §4.3 加入「可觀測性原則」段落：Then 必須描述使用者或系統的可見行為（UI 變化、訊息發送、API 回應）；提供 3 個從「不可觀測內部狀態 → 可觀測行為」的轉換示例。

#### [MEDIUM] 8 — Scenario Outline 適用條件不明確
**Check**: §6 Scenario Outline Pattern 是否說明何時適合使用（同一 Scenario 需要 ≥ 3 組不同輸入值）vs 何時不適合（只有 2 組輸入時用普通 Scenario）？Examples 表格的列數建議是否有說明？
**Risk**: Scenario Outline 濫用（2 組輸入也用）造成可讀性下降；不用 Outline（10 組輸入卻寫 10 個 Scenario）造成代碼冗余。
**Fix**: 在 §6 開頭加入適用條件（≥ 3 組輸入、每組輸入含義相同但數值不同），並說明 Examples 建議不超過 10 行的原則。

---

### Layer 3: 契約測試與 API 對齊（由 Backend Engineer 主審，共 4 項）

#### [HIGH] 9 — §12.1 BDD ↔ OpenAPI 追溯矩陣缺失關鍵 Endpoint
**Check**: §12.1 追溯矩陣是否涵蓋 API.md 中所有 P0 Endpoints（含 CRUD 和 Auth）？對每個 Endpoint 是否有對應的 Feature File + Scenario 路徑標注？
**Risk**: 關鍵 API Endpoint 沒有對應的 BDD Scenario，API 契約測試覆蓋不完整，API 重構時缺乏行為驗收保護。
**Fix**: 更新 §12.1，逐一比對 API.md Endpoint 清單，為每個缺漏的 Endpoint 新增追溯矩陣條目（Endpoint URL + Method → Feature File → Scenario）。

#### [HIGH] 10 — Provider-Driven Contract Test 規範不具體
**Check**: §12.2 Provider-Driven Contract Test 是否說明：使用哪個工具（Pact / Spring Cloud Contract / Dredd）、如何在 CI/CD 中執行、如何處理 Provider 驗證失敗？
**Risk**: 契約測試工具未定義導致各團隊使用不同工具，Consumer/Provider 契約無法自動驗證，微服務整合測試依賴手動介接。
**Fix**: 在 §12.2 補充工具選型說明、CI/CD 執行階段（建議 Merge 前）、Provider 驗證失敗處理流程（Block / Notify）。

#### [MEDIUM] 11 — 測試資料策略與清理原則不完整
**Check**: §13.1 測試資料策略是否涵蓋：資料隔離（每個 Scenario 獨立資料 or 共享 Fixture）、跨環境資料策略（dev/staging/prod 隔離方式）？§13.2 資料清理是否說明在 Scenario 級別 vs Suite 級別清理的選擇？
**Risk**: 測試資料策略不清晰導致 Scenario 間相互污染，在 CI 並行執行時出現不穩定（Flaky）的測試結果，嚴重降低測試可信度。
**Fix**: 在 §13.1 加入資料隔離策略決策樹（獨立資料 vs 共享 Fixture 的選擇原則），在 §13.2 說明清理時機選擇。

#### [LOW] 12 — Mutation Testing 覆蓋目標未設定
**Check**: §15 Mutation Testing Strategy 是否設定具體的 Mutation Score 目標（如 ≥ 70%）和達成期限（如 Sprint N）？是否說明哪些模組優先進行 Mutation Testing？
**Risk**: 缺少 Mutation Score 目標使 Mutation Testing 成為可選項，在 Sprint 壓力下容易被跳過，無法量化測試品質的實際保護能力。
**Fix**: 在 §15.1 加入 Mutation Score 目標（建議 ≥ 70% 作為基線），設定優先模組（Core Business Logic 優先），並在 §15.4 CI/CD 整合中標注觸發時機。

---

### Layer 4: Visual Regression 與文件完整性（由 Frontend QA Expert + BDD Expert 聯合審查，共 4 項）

#### [HIGH] 13 — VRT 基準快照策略未定義
**Check**: §14.3 Playwright VRT 標準模式是否說明：基準快照（Baseline）如何建立和更新（PR 流程）？快照儲存位置（Git LFS / CI Artifact）？快照更新審批流程？
**Risk**: 基準快照管理不清晰導致 VRT 成為「橡皮圖章」——不一致時工程師直接 update snapshot 而不調查原因，VRT 保護效果完全喪失。
**Fix**: 在 §14.3 加入「Baseline 管理規範」：如何建立初始快照、PR 中 VRT 失敗的處理流程（必須截圖審查 + PR Comment 確認）、快照更新的 git commit 規範。

#### [HIGH] 14 — VRT 覆蓋範圍與 Breakpoint 未說明
**Check**: §14 是否說明 VRT 應覆蓋哪些頁面/元件（P0 頁面 + 關鍵 Component）？是否指定必測的 Viewport（mobile 375px / tablet 768px / desktop 1440px）？是否說明 Dark Mode VRT 的覆蓋要求？
**Risk**: VRT 覆蓋範圍不明確導致工程師任意選擇快照對象，關鍵頁面的視覺回歸可能未被捕獲。
**Fix**: 在 §14.1 加入「VRT 覆蓋優先級」清單（P0 頁面必測 / 關鍵 Component 建議測），在 §14.3 標注必測的 3 個 Viewport，並說明 Dark Mode 快照要求。

#### [MEDIUM] 15 — Document Control 資訊未填入
**Check**: Document Control 表格中 DOC-ID、Version、Status、Author、Date 是否全部填入真實值？Change Log 是否有至少一筆初始版本記錄？
**Risk**: Document Control 空白代表 BDD 規範文件沒有版本管理，無法追蹤規範演進歷史，新加入的工程師無法判斷文件是否最新。
**Fix**: 填入所有 Document Control 欄位，Change Log 加入初始版本記錄（v1.0、日期、作者、建立說明）。

#### [LOW] 16 — §15 Mutation Testing 工具配置未對齊專案語言
**Check**: §15.3 Stryker 配置是否對應專案的實際語言（TypeScript/JavaScript）？若專案使用其他語言（Java/Python），是否有對應的 Mutation Testing 工具說明（PIT / mutmut）？
**Risk**: 工具配置範例語言與實際專案不符，工程師需要自行轉換配置，增加採用阻力。
**Fix**: 確認 §15.3 工具配置示例與實際專案語言一致，若為多語言專案，提供對應各語言的工具選型說明。

---

### Layer 5: Spring Modulith 微服務可拆解性 BDD（由 Backend Architect 主審，共 4 項）

| ID | Severity | Check | Risk | Fix |
|----|----------|-------|------|-----|
| BDD-SM-01 | CRITICAL | `@modulith @p0` Scenario 是否存在（≥ 4 個，覆蓋 HC-1/HC-2/HC-3/HC-5）？ | 缺少架構 BDD 驗證，HC 約束無法在 CI 自動偵測 | 依 §18 補充 `features/architecture/` 目錄下的 4 類 Scenario |
| BDD-SM-02 | HIGH | `@event-contract` Scenario 是否覆蓋 EDD §4.6 所有 Domain Events 的跨 BC consumer？ | Event schema 升版或 topic 改名時 consumer 端無自動偵測 | 依 §18.3 為每個跨 BC event pair 補充 Pact consumer 驗證 Scenario |
| BDD-SM-03 | HIGH | `@module-isolation` Scenario 是否為每個 BC 提供冷啟動驗證場景？ | BC 間存在隱性依賴時無法被提前偵測 | 依 §18.1 / §18.2 為所有 BC 補充 WireMock stub 冷啟動場景 |
| BDD-SM-04 | MEDIUM | §10.1 Tag Taxonomy 是否包含 `@modulith` / `@cross-module` / `@event-contract` / `@module-isolation`？ | 缺乏標籤分類，架構回歸 CI job 無法精準篩選 | 在 §10.1 補充 4 個 Spring Modulith 專用 tag |

---

## Escalation Protocol

- **CRITICAL**：任一 CRITICAL 項目未通過 → 停止審查，立即修正後重審
- **HIGH**：≥ 3 項 HIGH 未通過 → 視為高風險，回頭修正後繼續
- **MEDIUM/LOW**：累計記錄，不阻擋流程

---

## Completion Criteria

- §2.3 Tag Taxonomy 完整（@p0/@smoke/@regression/@wip 全定義）✅
- §4.5 Forbidden Patterns 涵蓋主要錯誤模式 ✅
- §12.1 API ↔ BDD 追溯矩陣覆蓋所有 P0 Endpoints ✅
- §14 VRT 基準快照管理規範清晰 ✅
- §18 Spring Modulith @modulith @p0 Scenario ≥ 4 個 ✅
- §10.1 Tag Taxonomy 包含 4 個 Spring Modulith 專用 tag ✅
- Document Control 完整填入 ✅

> 由 `/reviewdoc BDD` 自動執行本 checklist。
> Feature File 實際內容審查：`/reviewdoc BDD-server`（features/*.feature）和 `/reviewdoc BDD-client`（features/client/*.feature）
