---
doc-type: test-plan
output-path: docs/test-plan.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md
  - docs/EDD.md
  - docs/ARCH.md
  - docs/API.md
  - docs/SCHEMA.md
  - docs/FRONTEND.md  # Layer 6 — 前端元件架構（E2E 測試目標、VRT 覆蓋範圍）
  - docs/AUDIO.md    # 若存在：音效觸發清單、效能預算 → 音訊播放/靜音/格式/FPS 測試案例
  - docs/ANIM.md     # 若存在：動畫規格、效能預算 → 幀率/記憶體/reduced-motion 測試案例
quality-bar: "Test Pyramid 比例已說明（Unit 70%/Integration 20%/E2E 10%）；所有 P0 AC 均有對應 TC-ID；OWASP A01–A10 每項均有覆蓋計畫；4 個效能測試場景（Smoke/Load/Stress/Soak）均已定義且含具體 P50/P95/P99 數字；RTM 涵蓋所有 Must-have AC"
---

# test-plan.gen.md — Test Plan 文件生成規則

從 IDEA/BRD/PRD/PDD/EDD/ARCH/API/SCHEMA 自動生成 docs/test-plan.md（IEEE 829 Test Plan）。
涵蓋 Unit/Integration/E2E/Performance/UAT/Security 六大測試類型，
依 lang_stack 自動選擇測試工具組合，生成 k6/Locust 效能測試腳本骨架。

---

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## 上游文件讀取規則

### 必讀上游鏈（依優先順序）

| 文件 | 必讀章節 | 用途 |
|------|---------|------|
| `IDEA.md`（若存在）| 全文 | 了解產品願景——Test Plan 範疇不得超出 IDEA 定義的功能邊界 |
| `BRD.md` | 業務目標、成功指標、驗收標準 | Test Plan 的 UAT 驗收標準必須對應 BRD 的業務指標 |
| `PRD.md` | 所有功能 AC、非功能需求、§9 Success Metrics、§9.5 DoD | 每個 AC 必須有對應的 Test Case |
| `PDD.md`（若存在）| §4 功能、§8 Accessibility | UI 測試必須涵蓋 PDD 的互動設計和 WCAG 2.1 AA 要求 |
| `EDD.md` | §4 Security、§7 Scale、§10.5 SLO/SLI、§11 Capacity、§12 Chaos | Security 測試和 Performance 測試基準來自 EDD |
| `ARCH.md` | §9 部署拓撲、§10 Scalability、Service Boundaries | Integration 測試的系統邊界和 E2E 測試環境配置來自 ARCH |
| `API.md` | 所有 Endpoint、錯誤碼 | Contract Testing 必須覆蓋所有 API Endpoint |
| `SCHEMA.md` | 資料模型、索引策略 | DB 層 Integration 測試和效能測試的 Query 模式來自 SCHEMA |
| `FRONTEND.md`（若存在）| §4 Screen 清單、§10 E2E 覆蓋範圍、§11 Core Web Vitals 目標 | E2E 測試目標 Screen、VRT 覆蓋策略、Visual Regression 工具選型來自 FRONTEND |
| `docs/diagrams/class-inventory.md`（若存在）| 全文 | 提取所有 class 清單（Class 名稱/stereotype/src 路徑/test 路徑），用於自動填充 §15.2 Unit Test RTM 的 Class 和 Test File 欄位；未在 class-inventory 的 class 視為測試覆蓋漏洞 |

### IDEA.md Appendix C 素材讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與 Test Plan 相關的檔案。
對每個存在的 `docs/req/` 檔案，讀取全文，結合 Appendix C「應用於」欄位標有「Test Plan §」的段落，
作為生成 Test Plan 對應章節（測試範疇、風險矩陣、驗收條件）的補充依據。
優先採用素材原文描述，而非 AI 推斷。若無引用，靜默跳過。

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- PRD 的非功能需求（延遲、並發）vs EDD 的 SLO 定義（數字是否一致）
- PDD 的 Accessibility 需求 vs EDD 的前端技術選型（工具是否支援 WCAG 測試）
- BRD 的業務驗收標準 vs PRD 的 AC（是否有 BRD 要求但 PRD 未定義的驗收場景）

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並說明影響範圍。

---

## 文件結構規則

生成內容必須遵循 `templates/test-plan.md` 全 **21 節**結構：
§1 Executive Summary、§2 Test Scope、§3 Test Types（Unit/Integration/E2E/Performance/UAT/Security）、
§4 Test Environment、§5 Test Data Management、§6 Entry & Exit Criteria、
§7 Defect Management、§8 Test Schedule、§9 Risk-Based Testing、
§10 Performance Testing Spec、§11 CI/CD Integration、§12 Tooling Matrix、
§13 Reporting & Metrics、§14 RACI Matrix、§15 Requirements Traceability Matrix（RTM）、
§16 Glossary、§17 References、§18 Approval Sign-off、
§19 Mobile Testing Strategy、§20 Accessibility Testing Strategy、§21 Test Debt Management。

---

## Class Inventory 讀取規則

若 `docs/diagrams/class-inventory.md` 存在，必須：
1. 讀取全文，提取所有 class 條目（Class / Stereotype / Layer / src 路徑 / test 路徑）
2. 以 class-inventory 為基礎，在 §15.2 Unit Test RTM 中為每個 class 生成至少 3 個 TC-ID 條目（S=Success / E=Error / B=Boundary）
3. TC-ID 格式：`TC-UNIT-{MODULE}-{SEQ}-{CASE}`（MODULE 從 class 名稱縮寫取 2-5 字母，SEQ 為序號，CASE 為 S/E/B）
4. 若某個 class 只有 private methods（如純 DTO / ValueObject），標注「僅需建構子測試（TC-UNIT-{MODULE}-001-B）」
5. 生成 §15.2 時，Test File 欄位必須從 class-inventory 的「test 路徑」欄位直接複製，不得自行猜測

**若 class-inventory.md 不存在**：從 EDD §4.5.2 的 classDiagram 程式碼塊手動提取 class 名稱，推斷路徑後填入，並在段落開頭標注 `[WARNING] class-inventory.md 未找到，Class 路徑為推斷值，請執行 /gendoc-gen-diagrams 後更新。`

---

## 測試工具組合選擇規則（依 lang_stack）

依技術棧自動選擇測試工具（Unit / Integration / E2E / Performance / SAST）：

| lang_stack | Unit | Integration | E2E | Performance | SAST |
|-----------|------|-------------|-----|-------------|------|
| Python/FastAPI/Django/Flask | pytest + coverage.py | httpx + testcontainers | Playwright | Locust | Bandit + Semgrep |
| Node/Express/NestJS/Next.js | Jest + istanbul | Supertest + testcontainers | Playwright | k6 | ESLint security plugin + Semgrep |
| Go/Gin/Echo/Fiber | go test + go cover | httptest + testcontainers-go | Playwright | k6 | gosec + Semgrep |
| Java/Spring Boot/Quarkus | JUnit 5 + JaCoCo | MockMvc + Testcontainers | Playwright | k6 | SpotBugs + Semgrep |
| Ruby/Rails | RSpec + SimpleCov | RSpec request specs + testcontainers | Playwright | k6 | Brakeman + Semgrep |
| PHP/Laravel/Symfony | PHPUnit + Xdebug | Laravel HTTP Tests + testcontainers | Playwright | k6 | PHPCS Security + Semgrep |
| Rust/Actix/Axum | cargo test + tarpaulin | actix-web test + testcontainers | Playwright | k6 | cargo-audit + Semgrep |
| 預設/TypeScript | Jest + istanbul | Supertest + testcontainers | Playwright | k6 | Semgrep |

---

## §1 Executive Summary 生成規則

**§1.1 Purpose & Scope：**
- 說明本測試計畫目的、適用版本（來自 PRD Document Control）
- 測試對象簡述（產品名稱 + 核心功能數量）

**§1.2 Test Pyramid 比例（固定策略）：**
- Unit Tests：70%（快速回饋，覆蓋所有業務邏輯）
- Integration Tests：20%（API 契約 + 資料庫邊界）
- E2E Tests：10%（Critical User Flows 僅限 Happy Path）

**§1.3 Testing Philosophy：**
- Shift-Left 原則：測試計畫在實作前建立
- Risk-Based：Must-have 功能覆蓋率 ≥ 90%，Should-have ≥ 80%
- 自動化優先：除 UAT 外，所有類型整合 CI/CD

**§1.4 品質目標（量化，來自 PRD §9 Success Metrics）：**

| 指標 | 目標值 | 來源 |
|------|--------|------|
| 單元測試覆蓋率 | ≥ 80% | 業界標準 |
| Defect Escape Rate | < 5% | PRD §9 |
| P99 latency | < 500ms | EDD §10.5 或預設 |
| Critical Flow Pass Rate | 100% | PRD §9.5 DoD |

---

## §2 Test Scope 生成規則

**§2.1 In-Scope：**
- 列出所有 Must-have 功能（標記 P0）及 AC 數量
- 列出所有 Should-have 功能（標記 P1）及 AC 數量
- 來源：PRD MoSCoW 分類

**§2.2 Out-of-Scope（來自 PRD Out of Scope）：**
- 第三方服務內部邏輯（僅測試整合點）
- 非目標版本的功能

**§2.3 測試假設：**
- 測試環境可模擬生產環境 80% 以上場景
- 第三方 API 在 Staging 環境有 Sandbox
- 測試資料可按需生成，不依賴生產資料

---

## §3 Test Types 生成規則（最重要章節）

### §3.1 Unit Tests

- **工具**：依 lang_stack 選定
- **覆蓋率目標**：≥ 80%（行覆蓋率）；核心業務邏輯模組 ≥ 90%
- **主要測試模組**（從 PRD AC + ARCH 推斷）：
  - 業務邏輯層（Service / UseCase）
  - 資料轉換層（Serializer / DTO / Mapper）
  - 工具函式（Utility / Helper）
  - 邊界條件驗證（Input Validation）
- **執行策略**：Pre-commit hook + PR CI 強制通過
- **排除項目**：純 I/O 操作、第三方 SDK wrapper（改用 Integration Test 覆蓋）

### §3.2 Integration Tests

- **工具**：依 lang_stack 選定
- **Scope**：ARCH service boundaries（所有模組間 API 呼叫 + DB 操作）
- **API Endpoint 覆蓋**（從 API.md 提取所有 endpoint）：
  - 每個 endpoint 至少覆蓋：200 成功、400 輸入錯誤、401/403 授權錯誤、404 資源不存在、500 內部錯誤
- **資料庫**：使用 testcontainers 啟動真實 DB（非 mock）
- **外部服務**：使用 WireMock / MSW 模擬，不真實呼叫

### §3.3 E2E Tests

- **工具**：Playwright（跨框架統一）
- **Browser Matrix**：Chrome（主要）/ Firefox / Safari（WebKit）
- **Critical User Flows**（從 PRD §6 User Flows Happy Path 提取，每個 Flow 對應一個 spec 檔）：
  - 每個 Must-have 功能的 Happy Path Flow
  - 每個 Flow：步驟描述 + 預期結果 + Selector 策略（優先 data-testid）
- **測試資料策略**：
  - Fixture：靜態測試帳號 + 預設資料集
  - Factory：API 呼叫動態建立測試資料
  - AfterEach：清理測試資料（隔離性保證）
- **不測試範圍**：外部支付 Gateway、Email 寄送（改用 mock）

### §3.4 Performance Tests

- **工具**：依 lang_stack 選定（k6 或 Locust）
- **SLO Targets**（從 EDD §10.5 提取，若無則使用預設值）：

| 指標 | P50 | P95 | P99 | Error Rate |
|------|-----|-----|-----|------------|
| API 回應時間 | < 100ms | < 300ms | < 500ms | < 0.1% |
| 頁面載入時間 | < 1s | < 2s | < 3s | - |
| 資料庫查詢 | < 50ms | < 150ms | < 300ms | - |

**四個測試場景（缺一不可）：**

**Smoke Test（每次部署後執行）：**
- 目的：確認基本功能在生產配置下可運行
- VU：1，Duration：1 分鐘
- Pass Criteria：0 error，所有 SLO P99 達標

**Load Test（PR CI + 每日 Nightly）：**
- 目的：驗證正常工作負載下的效能
- Stages：ramp-up 5min → steady-state 20min → ramp-down 5min
- VU：正常負載值（來自 EDD §7 或估算）
- Pass Criteria：Error Rate < 0.1%，P99 < 500ms

**Stress Test（Release Gate）：**
- 目的：找出系統在超載下的崩潰點
- Stages：逐步增加 VU 至 150% 峰值負載 × 10min
- Pass Criteria：系統在壓力移除後 5min 內恢復正常

**Soak Test（每週一次 + 大版本發布前）：**
- 目的：發現記憶體洩漏、連線池耗盡、資源累積問題
- Duration：2 小時持續正常負載
- 監測指標：Memory heap、DB connection pool、CPU、Error Rate
- Pass Criteria：2h 內 Error Rate 無上升趨勢，Memory 無線性增長

**腳本骨架生成規則：**
- 若選 k6：生成 JavaScript 腳本骨架（含 stages + thresholds + scenarios）
- 若選 Locust：生成 Python 腳本骨架（含 User class + task set + wait time）

### §3.5 UAT

- **工具**：手動 + 測試管理工具（TestRail / Zephyr）
- **驗收標準**：直接來自 PRD §9.5 Definition of Done，逐項列出（不得泛泛描述）
- **參與者**：Product Owner + QA Lead + 代表性終端用戶（1-3 人）
- **通過條件**：P0 功能 100% 通過，P1 功能 ≥ 95% 通過，無 Critical/High 嚴重度未解決缺陷

### §3.6 Security Tests

- **工具**：依 lang_stack SAST 工具 + OWASP ZAP（DAST）
- **OWASP Top 10 評估矩陣**（A01-A10 每項均必須有覆蓋計畫）：

| OWASP ID | 名稱 | 適用性 | 測試方法 | 負責人 |
|---------|------|--------|----------|--------|
| A01 | Broken Access Control | 高 | API 授權測試 + DAST | QA Lead |
| A02 | Cryptographic Failures | 中 | 設定審查 + SAST | Security |
| A03 | Injection | 高 | SAST + Fuzz Testing | QA Lead |
| A04 | Insecure Design | 中 | Threat Modeling Review | Architect |
| A05 | Security Misconfiguration | 高 | CI config scan | DevOps |
| A06 | Vulnerable Components | 高 | Dependency audit | DevOps |
| A07 | Auth & Session Failures | 高 | Auth flow 測試 + 滲透測試 | Security |
| A08 | Software Integrity Failures | 低 | SBOM 審查 | DevOps |
| A09 | Logging Failures | 中 | Log review + SIEM check | DevOps |
| A10 | SSRF | 中 | DAST URL 注入測試 | QA Lead |

- **執行策略**：SAST 整合 PR CI；DAST 在 Staging 環境每週執行；Dependency audit 每日 Nightly

---

## §4 Test Environment 生成規則

至少定義三個環境：

| 環境 | 用途 | 資料策略 | 存取控制 |
|------|------|----------|----------|
| Local Dev | 開發者本機單元測試 + 快速整合測試 | 輕量 mock / testcontainers | 開發者本人 |
| Staging | E2E / Performance / Security / UAT | 匿名化生產資料 replica | QA + Dev + PM |
| Prod-like（Pre-Prod）| 最終 Release Gate / Soak Test | 完整生產資料副本 | QA Lead + DevOps |

---

## §5 Test Data Management 生成規則

策略選擇（四種，說明各自適用場景）：
- Factory（動態生成）：Unit + Integration，資料隔離性最佳
- Fixture（靜態預設）：E2E 固定角色帳號
- Seed（DB 初始化）：Staging 環境基礎資料
- Mock（虛擬回應）：外部 API 依賴

**PII 處理原則：**
- 測試環境禁止使用真實 PII
- 生產資料副本必須先匿名化（masking / tokenization）
- 測試帳號使用 @example.com 或 @test.internal 網域

---

## §6 Entry & Exit Criteria 生成規則

**整體 Test Entry Criteria：**
- 功能開發完成，PR 已合併到 main
- 所有 Unit Test 通過（CI 通過）
- Build 成功，Docker image 已推送至 Registry
- Staging 環境部署成功
- 測試資料已準備就緒

**各測試階段 Exit Criteria（含 Blocking Defect 定義）：**

| 測試階段 | 通過條件 | Blocking Defect 定義 |
|---------|---------|---------------------|
| Unit Test | 覆蓋率 ≥ 80%，0 failure | 任何 failure 均 Block |
| Integration Test | 所有 API endpoint 測試通過 | P0 功能 failure Block |
| E2E Test | Critical flows 100% pass | Happy Path failure Block |
| Performance Test | SLO P99 達標，Error Rate < 0.1% | SLO 超標 50% Block |
| Security Test | OWASP High 全數修復 | Critical / High 未修復 Block |
| UAT | P0 功能 100%，P1 ≥ 95% | Any Critical defect Block |

**Release Exit Criteria（上線決策閘門）：**
- 所有測試階段 Exit Criteria 均達標
- 所有 P0 / P1 缺陷已修復並驗證
- QA Lead + Product Owner 書面核准
- Soak Test 結果無記憶體洩漏跡象

---

## §7 Defect Management 生成規則

嚴重度定義與 SLA（必須量化，不得使用「視情況」）：

| Priority | 定義 | 修復 SLA | 驗證 SLA |
|---------|------|----------|----------|
| P0 Critical | 系統崩潰 / 資料遺失 / 安全漏洞 | 4 小時 | 2 小時 |
| P1 High | 核心功能無法使用（無 workaround）| 24 小時 | 4 小時 |
| P2 Medium | 功能受損但有 workaround | 3 個工作天 | 1 個工作天 |
| P3 Low | UI 問題 / 次要功能異常 | Next Sprint | Next Sprint |

---

## §8 Test Automation & CI/CD Integration 生成規則

CI Pipeline 測試閘門（必須定義每個觸發條件）：

```
PR Created → Unit Test → Integration Test → SAST Scan → Build
PR Merged  → E2E Test (Staging) → Smoke Test (Staging)
Nightly    → Load Test + Security DAST
Weekly     → Soak Test + Stress Test + Full Security Scan
Release    → Soak Test + Stress Test + UAT Gate
```

測試執行時間目標（PR CI 必須在 10 分鐘內完成）：
- Unit Test：< 2 分鐘
- Integration Test：< 5 分鐘
- SAST：< 3 分鐘

並行執行策略：Unit + SAST 並行；Integration 在 Unit 通過後觸發。

工具矩陣（完整版，含版本目標和設定檔位置）：

| 類型 | 工具 | 版本目標 | 設定檔位置 |
|------|------|---------|-----------|
| Unit | （依 lang_stack）| latest stable | 對應設定檔 |
| Integration | （依 lang_stack）| latest stable | 對應設定檔 |
| E2E | Playwright | latest stable | `playwright.config.ts` |
| Performance | （k6 或 Locust）| latest stable | `tests/performance/` |
| SAST | （依 lang_stack）| latest stable | CI 設定 |
| DAST | OWASP ZAP | latest | `zap/` |

---

## §9 Risk-Based Testing 生成規則

風險優先級對應矩陣（依 BRD MoSCoW 推斷）：

| 功能 | 業務優先級 | 風險等級 | 測試深度 | 覆蓋率目標 |
|------|----------|---------|---------|-----------|
| Must-have 功能 | P0 | High | 全面（Unit+Integration+E2E）| ≥ 90% |
| Should-have 功能 | P1 | Medium | 標準（Unit+Integration）| ≥ 80% |
| Could-have 功能 | P2 | Low | 基本（Unit）| ≥ 70% |

高風險功能詳細清單（從 BRD Must-have 或 PRD P0 AC 提取，逐一列出功能名稱 + 對應 AC）。

---

## §10 Performance Testing Spec 生成規則

Load Targets 表格（從 EDD §7 提取，若無則依產品規模估算）：

| 場景 | 並發用戶數 | 持續時間 | 目標 RPS |
|------|----------|---------|---------|
| Smoke | 1 | 1 min | 1 |
| Normal Load | 從 EDD §7 提取或估算 | 30 min | N |
| Peak Load | Normal × 3 | 10 min | N×3 |
| Soak | Normal | 2 hours | N |

SLO / SLI 矩陣（P50/P95/P99 均必須有具體數字）：

| Endpoint 類型 | P50 | P95 | P99 | Max Error Rate |
|-------------|-----|-----|-----|----------------|
| 讀取 API（GET）| < 100ms | < 300ms | < 500ms | < 0.1% |
| 寫入 API（POST/PUT）| < 200ms | < 500ms | < 1000ms | < 0.1% |
| 批次操作 | < 500ms | < 2000ms | < 5000ms | < 0.5% |
| 報表 / 匯出 | < 2s | < 5s | < 10s | < 1% |

---

## §11 Security Testing Scope 生成規則

依 EDD §4（Security）和 OWASP 標準定義安全測試範圍：

**SAST（Static Application Security Testing）：**
- 工具：依 lang_stack（SonarQube / Bandit / Semgrep / CodeQL）
- 觸發：PR 提交時自動執行
- 必須掃描：注入漏洞、驗證繞過、敏感資料洩漏

**DAST（Dynamic Application Security Testing）：**
- 工具：OWASP ZAP
- 觸發：Nightly 和 Release 前
- 掃描目標：所有 API Endpoint（來自 API.md §3）

**必測的 OWASP Top 10 項目**（每項標注測試方法和工具）：

| OWASP 項目 | 測試類型 | 工具 | 觸發條件 |
|-----------|---------|------|---------|
| A01 Broken Access Control | 整合測試 + DAST | ZAP | Nightly |
| A02 Cryptographic Failures | SAST + 程式碼審查 | SonarQube | PR |
| A03 Injection（SQL/NoSQL/Command）| SAST + DAST | SonarQube + ZAP | PR + Nightly |
| A05 Security Misconfiguration | DAST + Config Scan | ZAP + Trivy | Weekly |
| A07 Identification/Authentication | 整合測試 | 自撰測試 | PR |

**滲透測試計畫**（Release 前）：若有 P0 認證 / 金融相關功能，必須列出 Pen Test 委外計畫。

---

## §12 UAT Plan 生成規則

依 PRD P0 User Story 和業務利害關係人需求，定義用戶驗收測試計畫：

**UAT 範圍和參與者**：
- 列出哪些 PRD P0 功能需要 UAT（通常為所有使用者直接操作的 P0 功能）
- 定義 UAT 參與者（Product Owner / 業務代表 / 測試用戶）

**UAT 測試案例格式**（每個 P0 功能至少 1 個 UAT 場景）：

| UAT-ID | 功能 | 前置條件 | 測試步驟 | 預期結果 | 驗收標準 |
|--------|------|---------|---------|---------|---------|
| UAT-001 | （來自 PRD P0 功能）| （環境狀態）| 1. 操作步驟 | 系統回應 | AC 達成標準 |

**UAT 環境和資料**：
- 環境：Staging（與 Production 配置一致）
- 測試資料：指定測試帳號和預載資料
- 時間：Release Candidate 確認後，3-5 個工作天

**UAT 通過條件**：所有 P0 UAT 案例通過 + 無 CRITICAL 缺陷 → 核准上線。

---

## §13 Test Schedule & Milestones 生成規則

依 PRD 里程碑和 Sprint 計畫，定義測試時程：

| 測試階段 | 開始條件 | 預計週期 | 執行方式 | 里程碑 |
|---------|---------|---------|---------|-------|
| Unit Test | 每次 commit | 持續 | CI 自動化 | 每個 PR |
| Integration Test | PR created | 持續 | CI 自動化 | 每個 PR |
| E2E Test | PR merged to main | Daily + Nightly | CI 自動化 | Sprint Review |
| Performance Test | Staging deploy | Weekly + Release | 排程 CI | Release Candidate |
| Security Test | Weekly | Weekly | 排程 CI | Release Candidate |
| UAT | Release Candidate 確認 | 3-5 個工作天 | 手動 | Sign-off 前 |
| Smoke Test（Production）| 每次部署後 | < 15 分鐘 | CI 自動化 | 每次 Release |

**測試階段關鍵 Go/No-Go 條件**：列出各里程碑的通過標準（如「Sprint Review 通過：所有 Unit Test 通過，覆蓋率 ≥ 80%」）。

**CI 報告（自動化）：**
- 每次 CI run 產出 Coverage Report（HTML + JSON badge）
- E2E 失敗自動截圖 + trace 存入 CI artifact（保留 30 天）
- Performance 測試產出 HTML report（含 P50/P95/P99 圖表）
- 品質指標告警：覆蓋率下降 > 5% 觸發 Slack 通知

---

## §14 RACI Matrix 生成規則

| 活動 | QA Lead | Dev | DevOps | PM | Product Owner |
|------|---------|-----|--------|----|---------------|
| Unit Test 撰寫 | Consulted | Responsible | - | - | - |
| Integration Test 撰寫 | Responsible | Consulted | - | - | - |
| E2E Test 撰寫 | Responsible | Consulted | - | - | - |
| Performance Test 設計 | Responsible | Consulted | Consulted | - | - |
| CI Pipeline 設定 | Consulted | Consulted | Responsible | - | - |
| Security Test 執行 | Responsible | Informed | Consulted | - | - |
| UAT 協調 | Responsible | Informed | - | Consulted | Accountable |
| 缺陷 Triage | Responsible | Consulted | - | Informed | Accountable |
| Release 核准 | Consulted | - | - | Responsible | Accountable |

---

## §15 Requirements Traceability Matrix（RTM）生成規則

從 PRD 全部 AC 清單生成完整 RTM，至少涵蓋所有 Must-have AC：

| TC-ID | PRD REQ-ID | AC 描述 | BDD Scenario | 測試類型 | 狀態 |
|-------|-----------|---------|--------------|---------|------|
| TC-001 | REQ-001 | （來自 PRD AC-1）| （來自 features/）| Unit + E2E | 待執行 |

每個測試用例必須對應 PRD REQ-ID，確保測試覆蓋所有業務需求。

---

## §16 Test Summary Report Template 生成規則

生成一個可在測試周期結束時填寫的 Test Summary Report 模板：

**測試總結報告結構**：

```markdown
# Test Summary Report — {{PROJECT_NAME}} v{{VERSION}}

**測試期間**：{{START_DATE}} – {{END_DATE}}
**測試環境**：Staging（版本 {{STAGING_VERSION}}）
**測試負責人**：{{QA_LEAD}}

## 執行摘要
| 測試類型 | 計劃數 | 執行數 | 通過 | 失敗 | 跳過 | 通過率 |
|---------|-------|-------|------|------|------|-------|
| Unit Test | N | N | N | N | N | N% |
| Integration Test | N | N | N | N | N | N% |
| E2E Test | N | N | N | N | N | N% |

## 覆蓋率
- 程式碼覆蓋率：N%（目標：80%+）
- PRD P0 AC 覆蓋率：N%（目標：100%）

## 缺陷摘要
| 嚴重度 | 發現 | 已修復 | 殘留 |
|-------|------|-------|------|
| CRITICAL | N | N | N |
| HIGH | N | N | N |

## Go / No-Go 建議
[ ] GO — 所有通過條件達成，建議上線
[ ] NO-GO — 原因：{{REASON}}
```

**術語表（同時放入此節尾部）**：SLO / SLI / P99 / MTTR / TC-ID 的標準定義。
| Soak Test | 長時間低負載測試，用於發現記憶體洩漏 |
| SAST | Static Application Security Testing |
| DAST | Dynamic Application Security Testing |
| RTM | Requirements Traceability Matrix |
| VU | Virtual User（虛擬用戶，效能測試並發單位）|
| DoD | Definition of Done：功能完成的驗收標準 |

---

## §17 Open Questions 生成規則

列出測試規劃過程中尚未解答的問題，需在 Sprint Planning 前釐清：

| # | 問題 | 影響範圍 | 負責人 | 目標釐清時間 |
|---|------|---------|-------|-----------|
| 1 | （例：外部支付 API 的 Sandbox 環境是否支援 Webhook 測試？）| E2E 測試 | Dev Lead | Sprint N 開始前 |

若所有問題均已在文件生成時確認，填入「無待解問題」。

---

## §18 Approval Sign-off 生成規則

填寫核准欄位（姓名 + 日期欄位留空，供實際簽核時填入）：

| 角色 | 姓名 | 簽核日期 | 備注 |
|------|------|---------|------|
| QA Lead | {{QA_LEAD}} | ________ | |
| Dev Lead | {{DEV_LEAD}} | ________ | |
| Product Owner | {{PO}} | ________ | 最終 Release 核准人 |

---

## §19 Mobile Testing Strategy 生成規則

若產品有 Mobile App 或 Mobile Web，必須定義：

**裝置矩陣（iOS + Android 各三級）：**
- P0（主要裝置）：最新款旗艦
- P1（次要裝置）：市占前三款
- P2（相容裝置）：二代前的舊款

**弱網環境測試：**
- 使用 Playwright CDP 網路節流
- 測試情境：3G（150ms 延遲 + 10 秒加載超時）

**App 效能預算：**
- 冷啟動：≤ 2s
- 熱啟動：≤ 0.5s
- 包體積：iOS ≤ 50MB / Android ≤ 30MB

---

## §20 Accessibility Testing Strategy 生成規則

**自動化掃描（axe-core + Playwright）：**
- WCAG 2.1 AA tags：`wcag2a/wcag2aa/wcag21aa`
- CI Gate：critical/serious violations 零容忍

**AT 手動測試矩陣（三組合）：**
- NVDA + Chrome
- VoiceOver macOS + Safari
- TalkBack + Chrome

**A11y CI Gate 配置：**
提供 GitHub Actions workflow YAML 範例（失敗時阻斷 PR 合併）。

---

## §21 Test Debt Management 生成規則

**Flaky Test 管理流程：**
- `@flaky` 標記 + 隔離清單
- 1 週修復 SLA
- 超時自動刪除 + 通知

**測試健康儀表板（6 項週度指標）：**
1. 測試覆蓋率（行 / 分支）
2. Mutation Score（≥ 70%）
3. Flaky Test 數量
4. CI 平均執行時間
5. 測試失敗率
6. Accessibility 違規數

---

## 推斷規則

### Test Case 推斷
- PRD 每個 AC → 至少 1 個 Test Case（TC-ID 對應 REQ-ID）
- BRD Must-have → Risk Level High → 測試深度加強（Unit+Integration+E2E）
- EDD SLO → Performance SLO 具體數字（不得使用 TBD）

### 工具推斷
- 若 lang_stack 未在對應表中，使用預設（Jest + Supertest + Playwright + k6）
- E2E 工具統一使用 Playwright（跨語言通用）

### 覆蓋率推斷
- 核心業務邏輯模組（Service / UseCase）：≥ 90%
- 其他模組：≥ 80%

---

## 生成前自我檢核清單

- [ ] §1 Executive Summary：Test Pyramid 比例已說明（Unit 70% / Integration 20% / E2E 10%）
- [ ] §1.4 品質目標：覆蓋率目標、Defect Escape Rate、P99 latency 已量化（非「視情況」）
- [ ] §2 Test Scope：In-Scope 已對應 PRD Must/Should 功能，每個功能有 AC 數量
- [ ] §3.1 Unit Tests：測試工具已依 lang_stack 選定，覆蓋率目標 ≥ 80%，模組清單已列出
- [ ] §3.2 Integration Tests：scope 已覆蓋所有 API endpoint（來自 API.md 或 ARCH）
- [ ] §3.3 E2E：Critical User Flow 清單已從 PRD §6 提取（非泛泛描述）
- [ ] §3.4 Performance：4 個測試場景（Smoke / Load / Stress / Soak）均已定義，含 stages 設定
- [ ] §3.4 Performance：SLO Targets 表格有具體 P50/P95/P99 數字
- [ ] §3.5 UAT：驗收標準來自 PRD §9.5 DoD，逐項列出（非泛泛描述）
- [ ] §3.6 Security：OWASP Top 10 A01-A10 每項均有覆蓋計畫（測試方法已填寫）
- [ ] §4 Test Environment：至少定義 Dev / Staging / Prod-like 三個環境
- [ ] §6 Entry/Exit Criteria：每個測試階段均有明確的 Blocking Defect 條件
- [ ] §7 Defect Management：P0-P3 SLA 已量化（P0=4h, P1=24h, P2=3d, P3=next sprint）
- [ ] §9 Risk-Based Testing：高風險功能已對應 BRD Must-have（或 PRD P0 AC）
- [ ] §10 Performance SLO：P50/P95/P99 均有具體數字，覆蓋主要 endpoint 類型
- [ ] §14 RACI Matrix：QA Lead / Dev / DevOps / PM / Product Owner 五個角色已填寫
- [ ] §15 RTM：至少涵蓋所有 Must-have AC（TC-ID / PRD REQ-ID / BDD Scenario 對應）
- [ ] §18 Approval Sign-off：QA Lead + Engineering Lead + PM + Product Owner 四個角色均已列出
- [ ] §19 Mobile Testing：若有 Mobile App/Web，裝置矩陣（iOS P0/P1/P2 + Android P0/P1/P2）是否已定義？
- [ ] §19 弱網環境：Playwright CDP 網路節流測試是否有示例（3G 150ms 延遲 + 10 秒加載超時）？
- [ ] §19 App 效能預算：冷啟動 ≤2s / 熱啟動 ≤0.5s / 包體積 iOS ≤50MB / Android ≤30MB 是否已設定？
- [ ] §20 Accessibility：axe-core Playwright 掃描是否配置 WCAG 2.1 AA tags（wcag2a/wcag2aa/wcag21aa）？
- [ ] §20 AT 手動測試矩陣：NVDA + Chrome / VoiceOver macOS + Safari / TalkBack + Chrome 三組合是否已規劃？
- [ ] §20 A11y CI Gate：critical/serious violations 零容忍的 CI YAML 是否已提供？
- [ ] §21 Flaky Test 管理：@flaky 標記 + 隔離清單 + 1 週修復 SLA 流程是否已說明？
- [ ] §21 測試健康儀表板：6 項週度指標（覆蓋率/Mutation Score/Flaky 數/CI 時間/失敗率/A11y 違規）是否已定義？
- [ ] 所有 `[UPSTREAM_CONFLICT]` 標記均已處理或說明
- [ ] 無 TBD、「待確認」、「N/A」等未填寫欄位
