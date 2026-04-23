# PRD — Product Requirements Document
<!-- 對應學術標準：IEEE 830 (SRS)，對應業界：Google PRD / Amazon PRFAQ -->
<!-- Version: v1.1 | Status: DRAFT | DOC-ID: PRD-GENDOC-20260422 -->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | PRD-GENDOC-20260422 |
| **產品名稱** | gendoc — AI-Driven Implementation Blueprint Generator |
| **文件版本** | v1.1 |
| **狀態** | DRAFT |
| **作者（PM）** | AI Product Manager Agent |
| **日期** | 2026-04-22 |
| **上游來源** | MYDEVSOP 文件生成流水線（devsop-gendoc / devsop-autogen） |
| **審閱者** | 技術架構師、QA Lead |
| **核准者** | 待定 |

---

## Change Log

| 版本 | 日期 | 作者 | 變更摘要 |
|------|------|------|---------|
| v1.3 | 2026-04-24 | PM Agent | 補入 §5.5 Gen/Review/Fix 三專家模式與 Expert Roles 完整表；修正 §7.5/§8 BDD 模板欄位（BDD.md → BDD-server.md + BDD-client.md）；State file 完整欄位說明 |
| v1.2 | 2026-04-24 | PM Agent | 重建文件流水線：加入 VDD（視覺設計）、FRONTEND 獨立步驟、RTM 移至 BDD 之後；修正累積上游鏈；D01-D17 完整編號 |
| v1.1 | 2026-04-22 | PM Agent | 重新定位核心使命：從文件生成工具 → 可直接實作的開發藍圖生成器；補充藍圖細粒度品質標準 |
| v1.0 | 2026-04-22 | PM Agent | 初版 PRD，從 MYDEVSOP 文件生成子系統萃取，建立獨立 gendoc skill 套件 |

---

## 1. Executive Summary

### 核心使命

**gendoc 的目標是：讓任何人或任何 AI，拿到產出的文件後，不需要問任何問題，就能直接開始實作。**

市面上的文件生成工具產出的是「可閱讀的說明文件」，但 gendoc 產出的是「可實作的開發藍圖」。兩者的差距在於細粒度：

| 普通技術文件 | gendoc 開發藍圖 |
|------------|---------------|
| 描述功能意圖 | 定義到 class、method 簽名、參數型別 |
| 說明 API 端點 | 包含每個欄位的型別、驗證規則、錯誤回應範例 |
| 提及需要測試 | 列出具體測試情境、邊界值、等價類劃分 |
| 描述資料結構 | 給出 Schema DDL、index 策略、constraint 定義 |
| 說明架構組件 | 包含 sequence diagram、component 間呼叫合約 |

### 什麼是「可實作的藍圖」

gendoc 生成的每份文件都必須達到以下標準，才視為合格輸出：

1. **EDD（Engineering Design Doc）**：每個 module 的 class 清單；每個 class 的 method 簽名、參數名稱、型別、回傳值、例外行為；跨 class 的呼叫關係圖
2. **API.md**：每個端點的 URL、HTTP method、request body schema（含欄位、型別、是否必填、驗證規則）、response schema、error code 列舉、Rate Limit
3. **SCHEMA.md**：完整 DDL；每個欄位的型別、nullable、default、constraint；全部 index（含 composite）；外鍵關係；migration 策略
4. **test-plan.md**：每個功能點的正向測試、負向測試、邊界值分析（BVA）；等價類劃分（EP）；具體輸入值與預期輸出值的對照表
5. **BDD.md**：每個 Scenario 的 Given/When/Then 完整定義；edge case Scenario；unhappy path Scenario

### 雙受眾設計

| 受眾 | 如何使用 gendoc 產出 |
|------|--------------------|
| **AI（LLM / Claude Code）** | 直接餵入文件，不需追問，依 EDD 建 class、依 SCHEMA 寫 migration、依 test-plan 寫 test cases |
| **人類開發者** | 開箱即用的任務清單：每個 class 是一張卡片，每個 method 是一個 subtask，每個 test 情境是一個 checklist item |

### 一句話定位

> gendoc 是一套 Claude Code Skill 系統，從任意形式的輸入（文字 / 圖片 / URL / Git repo），在 60 分鐘內生成一份「細到任何人都能直接開始寫程式碼」的完整技術藍圖，包含 IDEA → BRD → PRD → PDD → VDD → EDD → ARCH → API → SCHEMA → FRONTEND → Test Plan → BDD → RTM → Runbook → LOCAL_DEPLOY，以及自動部署的 HTML 文件站。

---

## 2. Problem Statement

### 2.1 現狀痛點

#### 問題一：「可閱讀」≠「可實作」

現有技術文件工具（包括 AI 生成）產出的文件偏向說明性，缺乏足夠細節讓實作者直接動手。常見問題：

- EDD 只說「需要一個 UserService 處理使用者邏輯」，但沒有列出 `UserService` 裡有哪些 method
- API 文件列出端點路徑，但 request 欄位的 validation rule、error code 的 HTTP status mapping 都缺失
- 測試文件只說「測試登入功能」，但沒有給出：密碼長度邊界（7 / 8 / 129 / 130 字元）、特殊字元處理、並發登入、token 過期邊界等具體場景

結果：開發者或 AI 拿到文件後，仍需大量「填空」，等同於沒有藍圖。

#### 問題二：AI 開發者的需求更嚴苛

當「開發者」是 AI（如 Claude Code + MYDEVSOP）時，模糊的文件直接導致錯誤實作：

- class 邊界不清 → AI 可能把不同職責混在同一 class
- method 簽名未定義 → AI 可能自創不相容的介面
- 測試情境未列 → AI 生成的 test 只覆蓋 happy path，缺少 edge case
- 邊界值未定義 → AI 無從判斷 `0 ≤ quantity ≤ 999` 還是 `1 ≤ quantity ≤ 9999`

**gendoc 的核心假設**：如果文件細到 AI 能直接實作，人類一定也能。但反過來不成立。

#### 問題三：技術文件生成需要完整 SDLC 工具

MYDEVSOP 是一套完整的 31-STEP SDLC 自動化工具。許多場景只需文件生成能力，安裝整套是過度設計。

#### 問題四：模板系統缺乏細粒度品質標準

現有模板描述「這份文件應包含哪些章節」，但沒有定義每個章節的「細粒度完成標準」。

### 2.2 根本原因分析

- **根本原因一**：文件生成的品質目標設定錯了——目標應是「可實作」，而非「可閱讀」
- **根本原因二**：現有 AI 生成文件缺乏細粒度驗證機制，無從判斷文件是否達到「可直接實作」的標準
- **根本原因三**：MYDEVSOP 文件生成子系統與 SDLC 完整工具緊耦合，無法單獨萃取

### 2.3 機會假設

| ID | 假設 | 驗證指標 |
|----|------|---------|
| H-1 | 若 EDD 細到 class + method 層級，AI 實作時的重構次數可降低 60% 以上 | 對比有/無細粒度 EDD 的 AI 實作輪次 |
| H-2 | 若 test-plan 包含具體 BVA + EP 情境，測試覆蓋率首次執行即可達 85% 以上 | 首次 AI 生成 test 的覆蓋率 |
| H-3 | 若 gendoc 可獨立安裝，安裝成本降低 80%，使用者從安裝到產出第一份文件 ≤ 5 分鐘 | 安裝到完成 IDEA.md 的時間 |
| H-4 | Full-Auto 模式下 60 分鐘內完成 9 份完整文件集 | 端對端生成時間 |

### 2.4 System Context Diagram

```mermaid
C4Context
    title gendoc — System Context Diagram

    Person(dev, "開發者 / PM", "執行 /gendoc-auto 指令")
    Person(ai_dev, "AI 開發者（Claude Code）", "讀取 gendoc 輸出，直接實作程式碼")
    Person(stakeholder, "技術主管 / 客戶", "閱讀 HTML 文件站，確認規格")

    System(gendoc, "gendoc Skill Suite", "22 個 Claude Code skills\n任意輸入 → 可直接實作的完整技術藍圖")

    System_Ext(claude_api, "Claude API (Anthropic)", "AI 推理能力，執行每個文件生成 Agent")
    System_Ext(github, "GitHub", "存放輸出文件，建立 commit")
    System_Ext(github_pages, "GitHub Pages", "托管自動生成的 HTML 文件網站")
    System_Ext(web_sources, "外部來源", "URL / GitHub Repo / 圖片 / 本地文件")

    Rel(dev, gendoc, "執行 /gendoc-auto", "Claude Code CLI")
    Rel(ai_dev, gendoc, "讀取 docs/ 直接實作", "File System / Claude Context")
    Rel(stakeholder, gendoc, "閱讀 HTML 文件站", "Browser")
    Rel(gendoc, claude_api, "spawn subagent，執行文件生成", "Claude Agent SDK")
    Rel(gendoc, github, "git push + 建立文件 commit", "git / gh CLI")
    Rel(gendoc, github_pages, "部署 docs/pages/*.html", "GitHub Actions")
    Rel(gendoc, web_sources, "WebFetch 讀取輸入素材", "HTTP")
```

---

## 3. Stakeholders & Users

### 3.1 Stakeholder Map

| 角色 | 關係 | 主要關切 |
|------|------|---------|
| 獨立開發者 | 主要使用者 | 快速從構想生成完整可實作藍圖 |
| AI 開發工具（Claude Code / Cursor） | 主要消費者 | 文件細粒度夠高，可直接依文件建 class / 寫 test |
| 技術主管 | 次要使用者 | 文件品質、結構一致性、規格完整性 |
| 開源專案維護者 | 次要使用者 | 從現有 codebase 生成規格文件 |

### 3.2 User Personas

#### Persona A：獨立開發者 / 技術文件需求者

| 欄位 | 內容 |
|------|------|
| **背景** | 全端工程師，需要為新專案快速生成完整技術文件集，再交給 AI（或團隊）實作 |
| **核心需求** | 文件細到不需要再補充說明，AI 拿去就能生成第一版可運行程式碼 |
| **痛點** | 手工撰寫文件耗時 2-4 週；AI 生成文件太模糊，實作時仍需大量追問 |
| **成功標準** | 60 分鐘內完成 9 份文件；Claude Code 讀取文件後首次生成程式碼通過 CI |

#### Persona B：開源專案維護者

| 欄位 | 內容 |
|------|------|
| **背景** | 有現有 Git repo，想為其生成正式規格文件，供 contributor 或 AI 參考實作 |
| **核心需求** | 從 codebase 逆向生成包含 class 設計、API spec、test 情境的完整文件集 |
| **痛點** | 逆向工程文件品質低落，缺少測試情境、邊界值定義 |
| **使用場景** | `/gendoc-auto https://github.com/user/repo`，輸入類型自動偵測為 `codebase_git` |

#### Persona C：AI 開發工具（Claude Code）

| 欄位 | 內容 |
|------|------|
| **背景** | 作為後續程式碼生成工具，讀取 gendoc 產出的 docs/ 目錄，依文件實作系統 |
| **核心需求** | EDD 中每個 class 的 method 列表；SCHEMA 的完整 DDL；test-plan 的具體輸入/輸出對照 |
| **失敗條件** | 文件中有「TBD」、「待定」、「視情況而定」等未決定項目 → 視為文件不合格 |

---

## 4. 藍圖品質標準（Blueprint Depth Standard）

這是 gendoc 的核心品質定義。每份文件生成後，Review Loop 必須驗證這些標準。

### 4.1 EDD（Engineering Design Document）細粒度標準

每份 EDD 必須包含：

**Class-Level 設計**
```
ClassName
├── 職責說明（≤ 2 句話，若超過 2 句表示職責過重）
├── 依賴注入清單（constructor 接受的參數型別）
└── Method 清單：
    ├── methodName(param1: Type, param2: Type): ReturnType
    │   ├── 前置條件（Pre-condition）
    │   ├── 後置條件（Post-condition）
    ├── 例外行為（throws XxxException when ...）
    └── 邊界行為（param1 為 null 時、param1 超出範圍時）
```

**範例（合格 EDD 片段）**
```
class UserAuthService
  職責：驗證使用者身份，簽發 JWT token
  依賴：UserRepository, PasswordHasher, TokenSigner

  Method: authenticate(email: string, password: string): AuthResult
    Pre-condition: email 符合 RFC 5321；password 長度 8-128 字元
    Post-condition: 成功時 AuthResult.token 為有效 JWT，exp = now + 24h
    throws: InvalidCredentialsException（email 不存在 or 密碼錯誤，統一訊息不區分）
    throws: AccountLockedException（連續失敗 ≥ 5 次且距上次失敗 < 30 分鐘）
    邊界：password 為空字串 → throws ValidationException（不進行 DB 查詢）
    邊界：email 大小寫不敏感（db 查詢前 toLower）

  Method: logout(userId: UUID, tokenJti: string): void
    Post-condition: tokenJti 加入 blacklist，TTL = 原 token 剩餘時間
    邊界：tokenJti 已在 blacklist → 靜默成功（冪等）
    邊界：userId 不存在 → 靜默成功（不拋例外）
```

### 4.2 API.md 細粒度標準

每個端點必須包含：

```
POST /api/v1/auth/login
  Summary: 使用者登入，取得 access token 與 refresh token
  Request Body (application/json):
    email        string  required  RFC 5321 格式；大小寫不敏感
    password     string  required  長度 8-128；至少 1 大寫、1 數字
    remember_me  boolean optional  default: false；true 時 refresh_token TTL = 30d

  Response 200 OK:
    access_token   string  JWT；exp = now + 15m
    refresh_token  string  Opaque token；exp = now + 7d（or 30d）
    token_type     string  "Bearer"（固定值）

  Error Responses:
    400 Bad Request      欄位格式錯誤；body: { code: "VALIDATION_ERROR", fields: [...] }
    401 Unauthorized     email 不存在 or 密碼錯誤；body: { code: "INVALID_CREDENTIALS" }
    423 Locked           帳號鎖定；body: { code: "ACCOUNT_LOCKED", unlock_at: ISO8601 }
    429 Too Many Req.    IP 限速（> 10 次/分鐘）；header: Retry-After: 60

  Rate Limit: 10 req/min per IP（未登入）；不限（已登入）
  Auth Required: No
  Idempotent: No
```

### 4.3 SCHEMA.md 細粒度標準

每個 Table 必須包含完整 DDL：

```sql
-- users 表
CREATE TABLE users (
  id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  email       VARCHAR(254) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,                  -- bcrypt $2b$, cost factor 12
  is_verified BOOLEAN      NOT NULL DEFAULT FALSE,
  is_locked   BOOLEAN      NOT NULL DEFAULT FALSE,
  lock_until  TIMESTAMPTZ  NULL,                        -- NULL = 未鎖定
  failed_attempts SMALLINT NOT NULL DEFAULT 0,          -- 範圍 0-127
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Index 策略（必須列出理由）
CREATE UNIQUE INDEX idx_users_email ON users (LOWER(email));  -- 大小寫不敏感唯一索引
CREATE INDEX idx_users_is_locked ON users (is_locked) WHERE is_locked = TRUE;  -- Partial index，只索引鎖定帳號

-- Constraint
ALTER TABLE users ADD CONSTRAINT chk_failed_attempts CHECK (failed_attempts >= 0);
ALTER TABLE users ADD CONSTRAINT chk_email_format CHECK (email ~* '^[^@]+@[^@]+\.[^@]+$');

-- Migration 策略
-- 新增 failed_attempts 欄位（已存在的 row 預設值為 0，無 downtime）
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts SMALLINT NOT NULL DEFAULT 0;
```

### 4.4 test-plan.md 細粒度標準

每個功能必須包含以下測試類型，並給出**具體輸入值與預期輸出**：

**等價類劃分（Equivalence Partitioning, EP）**

| 測試類別 | 輸入 | 預期輸出 |
|---------|------|---------|
| 正向：合法登入 | email=`user@example.com`, password=`Passw0rd!` | 200 + tokens |
| 負向：email 不存在 | email=`noone@example.com`, password=`Passw0rd!` | 401 INVALID_CREDENTIALS |
| 負向：密碼錯誤 | email=`user@example.com`, password=`WrongPass1!` | 401 INVALID_CREDENTIALS |
| 負向：格式錯誤 email | email=`notanemail`, password=`Passw0rd!` | 400 VALIDATION_ERROR |
| 負向：帳號鎖定 | 連續失敗 5 次後再試 | 423 ACCOUNT_LOCKED |

**邊界值分析（Boundary Value Analysis, BVA）**

| 欄位 | 邊界值 | 預期行為 |
|------|-------|---------|
| password 長度 | 7 字元 | 400（低於最小值） |
| password 長度 | 8 字元 | 正常處理（最小合法值） |
| password 長度 | 128 字元 | 正常處理（最大合法值） |
| password 長度 | 129 字元 | 400（超過最大值） |
| password 長度 | 0（空字串） | 400（不觸發 DB 查詢） |
| failed_attempts | 4 次錯誤後 | 401（不鎖定） |
| failed_attempts | 第 5 次錯誤 | 423（鎖定，lock_until = now + 30m） |
| failed_attempts | 第 5 次錯誤後 30 分 1 秒 | 401（自動解鎖，重置計數） |

**並發與冪等性測試**

| 情境 | 測試方法 | 預期行為 |
|------|---------|---------|
| 同一帳號同時登入（10 並發） | 同時送出 10 個合法登入請求 | 全部返回 200，token 各自獨立 |
| 重複登出同一 token | 兩次 POST /logout 同一 jti | 兩次都返回 200（冪等） |
| 登入時 DB unavailable | Mock DB 拋出 connection timeout | 503 SERVICE_UNAVAILABLE（不返回 500） |

### 4.5 BDD.md 細粒度標準

每個 Feature 必須涵蓋 happy path、unhappy path、edge case：

```gherkin
Feature: 使用者登入
  Background:
    Given 存在帳號 "user@example.com" 密碼 "Passw0rd!"
    And 該帳號未被鎖定

  Scenario: 正常登入取得 token
    When 我以 "user@example.com" / "Passw0rd!" 發送登入請求
    Then 回應狀態碼為 200
    And 回應包含 access_token（JWT 格式）
    And 回應包含 refresh_token
    And access_token 的 exp 距現在 15 分鐘以內

  Scenario: 密碼錯誤登入
    When 我以 "user@example.com" / "WrongPass" 發送登入請求
    Then 回應狀態碼為 401
    And 回應 body 的 code 為 "INVALID_CREDENTIALS"
    And 回應不揭示是 email 不存在還是密碼錯誤

  Scenario Outline: 連續失敗 N 次後的行為
    When 我連續失敗登入 <次數> 次
    Then 帳號狀態為 <狀態>
    And 回應狀態碼為 <HTTP狀態碼>

    Examples:
      | 次數 | 狀態   | HTTP狀態碼 |
      | 4    | 正常   | 401       |
      | 5    | 鎖定   | 423       |
      | 6    | 鎖定   | 423       |

  Scenario: 密碼邊界值（7 字元，低於最小）
    When 我以 "user@example.com" / "Pass0r!" 發送登入請求（7字元密碼）
    Then 回應狀態碼為 400
    And 回應 body 的 code 為 "VALIDATION_ERROR"
    And 回應不查詢資料庫

  Scenario: 鎖定後 30 分鐘自動解鎖
    Given 帳號已被鎖定（lock_until = 30 分鐘前）
    When 我以正確密碼發送登入請求
    Then 回應狀態碼為 200
    And 帳號的 failed_attempts 重置為 0
```

---

## 5. Skill 架構與流程

### 5.1 Skill 清單（22 個）

| 分層 | Skill 名稱 | 功能 |
|------|-----------|------|
| **入口層** | `gendoc-auto` | 任意輸入→IDEA+BRD→移交 gendoc-flow |
| **流水線層** | `gendoc-flow` | 純文件生成流水線（PRD→BDD→HTML） |
| **共用層** | `gendoc-shared` | 共用邏輯參考（狀態管理、Review 策略） |
| **更新層** | `gendoc-update` | 版本自動更新 |
| **生成層** | `gendoc-gen-idea` | 生成 IDEA.md |
| | `gendoc-gen-brd` | 生成 BRD.md |
| | `gendoc-gen-prd` | 生成 PRD.md |
| | `gendoc-gen-pdd` | 生成 PDD.md |
| | `gendoc-gen-edd` | 生成 EDD.md（含 class + method 細節） |
| | `gendoc-gen-arch` | 生成 ARCH.md（含 sequence diagram） |
| | `gendoc-gen-api` | 生成 API.md（含完整 request/response schema） |
| | `gendoc-gen-schema` | 生成 SCHEMA.md（含完整 DDL + index 策略） |
| | `gendoc-gen-test-plan` | 生成 test-plan.md（含 BVA + EP 具體值）+ RTM.md |
| | `gendoc-gen-bdd` | 生成 BDD.md（含 edge case Scenario） |
| | `gendoc-gen-diagrams` | 生成 UML / Mermaid 圖表 |
| | `gendoc-gen-readme` | 生成 README.md |
| | `gendoc-gen-html` | 生成靜態 HTML 文件網站 |
| | `gendoc-gen-client-bdd` | 生成客戶端 BDD（可選） |
| **Review 層** | `gendoc-idea-review` | IDEA.md Review Loop |
| | `gendoc-brd-review` | BRD.md Review Loop |
| | `gendoc-align-check` | 跨文件對齊審查 |
| | `gendoc-align-fix` | 自動修復對齊問題 |

### 5.2 完整流程圖

```
使用者輸入（文字/圖片/URL/Git/本地）
    ↓
/gendoc-auto
    ├── 輸入類型偵測（text/image_url/doc_url/doc_git/codebase_local/codebase_git）
    ├── 素材保存至 docs/req/（唯讀原則）
    ├── PM Expert 分析（產品/技術雙視角）
    ├── 網路背景研究（WebSearch × 3）
    ├── gendoc-gen-idea → docs/IDEA.md
    ├── gendoc-idea-review（Review Loop）
    ├── gendoc-gen-brd  → docs/BRD.md
    ├── gendoc-brd-review（Review Loop）
    └── 移交 /gendoc-flow
         ↓
/gendoc-flow（D01-D17）
    ├── D01: IDEA.md    ← [需求層] 概念入口（可選）
    ├── D02: BRD.md     ← 商業需求、範疇、成功指標
    ├── D03: PRD.md     ← User Stories + Acceptance Criteria
    ├── D04: PDD.md*    ← UX/互動設計（client_type≠none）
    ├── D05: VDD.md*    ← 視覺設計、Design Token、Art Direction（client_type≠none）
    ├── D06: EDD.md     ← [設計層] class + method 細節（讀取 VDD Token 規格）
    ├── D07: ARCH.md    ← 元件圖、Mermaid C4、sequence diagram
    ├── D08: API.md     ← 完整 request/response/error schema
    ├── D09: SCHEMA.md  ← DDL + index + constraint
    ├── D10: FRONTEND.md* ← 前端技術設計（實作 VDD Design Token）（client_type≠none）
    ├── D11: test-plan.md ← [品質層] EP + BVA + 並發測試策略
    ├── D12: BDD.md（server）← Gherkin Scenario
    ├── D12b: BDD.md（client）*← Client E2E Scenario（client_type≠none）
    ├── D13: RTM.md     ← 需求追溯矩陣（PRD US → TC → BDD Scenario）
    ├── D14: RUNBOOK.md ← [運維層] 凌晨 3 點可直接執行
    ├── D15: LOCAL_DEPLOY.md ← 5 分鐘本地環境啟動
    ├── D16: ALIGN_REPORT.md ← [稽核層] 跨文件對齊掃描
    └── D17: docs/pages/ + GitHub Pages ← HTML 文件站（含 README）

    * = client_type ≠ none 時執行（有 UI 的產品）
```

### 5.3 文件流水線依賴鏈（Pipeline Dependency Chain）

每份文件生成時**必須讀取所有上游文件**（累積鏈，非僅直接父文件）。以下為各文件類型的權威累積上游依賴，來源為各 `templates/*.gen.md` 的 `upstream-docs` 欄位。

#### 層次樹（Hierarchical Tree）

```
docs/req/（原始輸入層，所有文件的最終上游）
│
└─► IDEA.md（Layer 0：概念入口，可選）
     └─► BRD.md（Layer 1：商業需求）
          └─► PRD.md（Layer 2：產品需求）
               ├─► PDD.md（Layer 3a：UX 互動設計，可選）
               │    └─► VDD.md（Layer 3.5：視覺設計、Design Token，可選）
               │         └─► EDD.md（Layer 4：工程技術設計）
               │              ├─► ARCH.md（Layer 5a：架構設計）
               │              │    ├─► API.md（Layer 5b：API 定義）
               │              │    │    └─► SCHEMA.md（Layer 5c：資料模型）
               │              │    │         └─► FRONTEND.md（Layer 6：前端技術設計，可選）
               │              │    │              └─► test-plan.md（Layer 7：測試策略）
               │              │    │                   ├─► BDD features/（Layer 8a：Server BDD）
               │              │    │                   │    └─► RTM.md（Layer 9：需求追溯矩陣）
               │              │    │                   └─► BDD client/（Layer 8b：Client BDD，可選）
               │              │    │
               │              │    └─► RUNBOOK.md（Layer 9：運維文件）
               │              │         └─► LOCAL_DEPLOY.md（Layer 9：本地部署）
               │              │
               │              └─[稽核層] ALIGN_REPORT.md + README.md → docs/pages/
```

#### 累積上游依賴表（Cumulative Upstream Table）

| 文件 | 層級 | 必須讀取的累積上游 | 可選條件 |
|------|------|------|------|
| **IDEA.md** | Layer 0 | `docs/req/` 所有素材 | 可選 |
| **BRD.md** | Layer 1 | `docs/req/` + IDEA | — |
| **PRD.md** | Layer 2 | `docs/req/` + IDEA + BRD | — |
| **PDD.md** | Layer 3a | `docs/req/` + IDEA + BRD + PRD | client_type ≠ none |
| **VDD.md** | Layer 3.5 | `docs/req/` + IDEA + BRD + PRD + PDD | client_type ≠ none |
| **EDD.md** | Layer 4 | `docs/req/` + IDEA + BRD + PRD + PDD + VDD | — |
| **ARCH.md** | Layer 5a | `docs/req/` + IDEA + BRD + PRD + PDD + VDD + EDD | — |
| **API.md** | Layer 5b | `docs/req/` + IDEA + BRD + PRD + PDD + EDD + ARCH | — |
| **SCHEMA.md** | Layer 5c | `docs/req/` + IDEA + BRD + PRD + PDD + EDD + ARCH + API | — |
| **FRONTEND.md** | Layer 6 | `docs/req/` + IDEA + BRD + PRD + PDD + **VDD** + EDD + ARCH + API | client_type ≠ none |
| **test-plan.md** | Layer 7 | `docs/req/` + IDEA ~ SCHEMA + **FRONTEND** | — |
| **BDD features/** | Layer 8a | `docs/req/` + IDEA ~ SCHEMA + FRONTEND + test-plan | — |
| **BDD client/** | Layer 8b | 同 Layer 8a | client_type ≠ none |
| **RTM.md** | Layer 9 | `docs/req/` + IDEA ~ SCHEMA + FRONTEND + test-plan + BDD | — |
| **RUNBOOK.md** | Layer 9 | `docs/req/` + IDEA ~ SCHEMA + **FRONTEND** + test-plan + BDD | — |
| **LOCAL_DEPLOY.md** | Layer 9 | `docs/req/` + IDEA ~ SCHEMA + **FRONTEND** + test-plan + BDD | — |
| **README.md** | Layer 10 | 全部文件（含 RUNBOOK + LOCAL_DEPLOY） | — |
| **ALIGN_REPORT.md** | 稽核層 | 全部已生成文件（由 align-check 掃描） | — |

> **IDEA Appendix C 特殊處理**：讀取 IDEA.md 時，同步讀取其 Appendix C 列出的所有 `docs/req/` 素材。若上游文件不存在，靜默跳過，不降低覆蓋深度。

#### 設計決策說明

| 決策 | 說明 |
|------|------|
| VDD 在 EDD 之前 | VDD 定義 Design Token 命名空間和資產格式規格，EDD 的 CDN/Build Pipeline 技術選型依賴此資訊 |
| FRONTEND 在 SCHEMA 之後 | FRONTEND 依賴 API + ARCH（工程契約），但不依賴 SCHEMA（純後端資料層） |
| FRONTEND 在 test-plan 之前 | E2E 測試範圍和 VRT 覆蓋清單必須以 FRONTEND 的 Screen 清單為基準 |
| RTM 在 BDD 之後 | RTM 建立 US↔TC↔BDD Scenario 三向追溯，BDD 必須先完成 |
| RUNBOOK/LOCAL_DEPLOY 讀 FRONTEND | 有 UI 的產品必須包含前端部署和本地啟動設定 |

#### 合法跳過條件

| 文件 | 跳過條件 |
|------|------|
| PDD、VDD、FRONTEND、Client BDD | `client_type = none`（純 API / CLI 服務，無 UI） |
| 任何文件的特定章節 | 功能明確列在 BRD `## Out of Scope` 章節 |
| 上游文件不存在 | 靜默跳過，不降低生成覆蓋深度 |

### 5.4 State File 管理

```
.gendoc-state-{git_user}-{git_branch}.json
```

State file 記錄：
- `execution_mode`：`full-auto` / `interactive`
- `review_strategy`：`rapid` / `standard` / `exhaustive` / `tiered`
- `completed_steps`：已完成步驟清單（支援斷點續行）
- `skill_source`：`gendoc-auto`（防止跨套件誤用）
- `handoff`：true（gendoc-auto → gendoc-flow 移交標記）
- `start_step`：斷點續行起始步驟 ID（與 pipeline.json step.id 完全一致）
- `client_type`：`none` / `web-saas` / `unity` / `cocos` / `html5-game`（控制條件步驟跳過）
- `lang_stack`：技術棧標籤（`node/typescript`、`python/fastapi` 等）
- `github_repo`：GitHub 倉庫 URL（用於 README badge 生成）
- `max_rounds`：Review Loop 最大輪次
- `stop_condition`：Review Loop 停止條件描述
- `last_completed`：最後一個完成的 step ID
- `last_updated`：ISO 8601 時間戳

---

### 5.5 Gen / Review / Fix 三專家模式（Standard Step Pattern）

每個標準流水線步驟（非 `special_skill` 步驟）都遵循以下三階段子代理模式：

#### 三專家角色

```
┌─────────────────────────────────────────────────────────────┐
│  Step Execution Pattern（每個 D0X 步驟的標準執行流程）        │
│                                                             │
│  主 Claude（協調者）                                         │
│       │                                                     │
│       ├─► [Gen Subagent] ─── 讀 TYPE.gen.md + 所有上游文件   │
│       │         │              生成初稿 → 寫入 output 文件    │
│       │         ▼                                           │
│       ├─► [Review Subagent] ─ 讀 TYPE.review.md + 初稿       │
│       │         │              輸出 REVIEW_JSON findings     │
│       │         ▼                                           │
│       └─► [Fix Subagent] ─── 讀 findings + 當前文件          │
│                 │              修復每個 finding，輸出 diff     │
│                 ▼                                           │
│       主 Claude 判斷：finding=0 或達 max_rounds → 結束        │
│       否則 → 下一輪 Review Subagent                          │
└─────────────────────────────────────────────────────────────┘
```

#### 各文件類型的專家角色

| 文件類型 | Gen Subagent 角色 | Review Subagent 角色 |
|---------|------------------|---------------------|
| **IDEA** | 資深 PM + 產品策略師 | PM + 商業分析師 |
| **BRD** | 資深商業分析師 + PM | 業務架構師 + PM |
| **PRD** | 資深 PM | PM + QA Lead |
| **PDD** | UX Designer + Interaction Designer | UX Architect + Frontend Lead |
| **VDD** | 資深 Visual Designer / Art Director | Art Director + Brand Strategist |
| **EDD** | 資深系統架構師 + Software Engineer | Software Architect + Senior Engineer |
| **ARCH** | 資深 Solution Architect | Cloud Architect + DevOps Lead |
| **API** | 資深 API Architect + Backend Engineer | API Architect + Security Engineer |
| **SCHEMA** | 資深 DBA + Backend Engineer | DBA + Backend Architect |
| **FRONTEND** | 資深 Frontend Architect | Frontend Architect + UX Engineer |
| **test-plan** | 資深 QA Architect + Test Lead | QA Architect + PM |
| **BDD-server** | 資深 BDD Expert + Backend QA Architect | BDD Expert + Backend Engineer |
| **BDD-client** | 資深 Frontend QA Expert + E2E Specialist | Frontend QA + BDD Expert |
| **RTM** | 資深 QA Architect | QA Architect + PM |
| **runbook** | 資深 SRE | SRE + DevOps Engineer |
| **LOCAL_DEPLOY** | 資深 DevOps Engineer | DevOps + Backend Engineer |

#### 模板讀取時序（每步驟的 Gen Subagent 讀取順序）

```
Gen Subagent 被呼叫時：

1. 讀 templates/{TYPE}.gen.md          ← 生成規則（Iron Rule 累積上游）
2. 讀 templates/{TYPE}.md              ← 文件結構模板
3. 依 gen.md 的 upstream-docs 欄位，
   讀取所有上游文件（累積鏈）          ← PRD 說「讀 BRD + IDEA」時，
                                         gen.md 明確列出哪些章節必讀
4. 寫入 output 文件                    ← step.output[0]（或多檔案 output_glob）
```

#### 特殊步驟（special_skill）

以下步驟不走 Gen/Review/Fix 三階段，而是直接呼叫 Skill tool：

| Step ID | special_skill | 行為 |
|---------|--------------|------|
| D16-ALIGN | `gendoc-align-check` | 四維度跨文件對齊掃描，輸出 ALIGN_REPORT.md |
| D17-HTML | `gendoc-gen-html` | MD→HTML 轉換，先呼叫 gendoc-gen-readme，再生成 docs/pages/ |

#### 多文件步驟（multi_file=true）

BDD-server（D12）和 BDD-client（D12b）生成多個 `.feature` 檔案而非單一 md：

```
BDD-server：
  Gen 讀 BDD-server.gen.md → 生成 features/*.feature（多個）
  Review 讀 BDD-server.review.md → 掃描 features/ 下所有 .feature
  commit：test(gendoc)[D12-BDD-server]: gen — 生成 N 個 .feature 檔案

BDD-client：
  Gen 讀 BDD-client.gen.md → 生成 features/client/*.feature（多個）
  Review 讀 BDD-client.review.md → 掃描 features/client/ 下所有 .feature
  commit：test(gendoc)[D12b-BDD-client]: gen — 生成 N 個 client .feature 檔案
```

---

## 6. 功能需求

### 6.1 多元輸入支援（F-01）

| 輸入類型 | 觸發條件 | 處理方式 |
|---------|---------|---------|
| `text_idea` | 純文字描述 | 直接作為 IDEA 來源 |
| `image_url` | http(s):// + 圖片副檔名 | WebFetch + Vision 分析 |
| `doc_git` | github.com / gitlab.com URL | WebFetch 讀取 README/docs |
| `doc_url` | http(s):// + .pdf/.md/.docx | WebFetch 下載 + 文字提取 |
| `doc_local` | 本地檔案路徑 | Read 工具讀取 |
| `codebase_local` | 本地目錄路徑 | tree + 關鍵文件 cp |
| `codebase_git` | git@/. git URL | git clone --depth 1 + 掃描 |

### 6.2 執行模式（F-02）

- **Full-Auto**：全自動，AI 自動選所有預設值，無需人工介入，透過 `/gendoc-config` 設定
- **Interactive**：互動引導，關鍵決策點等待使用者輸入，帶 AI 推薦預設選項

### 6.3 Review 策略（F-03）

| 策略 | 最大輪次 | 停止條件 |
|------|---------|---------|
| `rapid` | 3 輪 | 任一輪 finding=0 |
| `standard` | 5 輪 | 任一輪 finding=0（預設）|
| `exhaustive` | 無上限 | finding=0 |
| `tiered` | 無上限 | 前 5 輪 finding=0；第 6 輪起 CRITICAL+HIGH+MEDIUM=0 |

Review finding 的嚴重等級涵蓋：
- **CRITICAL**：缺少 class 邊界定義、API 缺少 error code、test 缺少 BVA
- **HIGH**：method 缺少例外行為、Schema 缺少 index 策略
- **MEDIUM**：Scenario 缺少 edge case、文件間術語不一致
- **LOW**：格式問題、遣詞建議

### 6.4 素材管理（F-04）

- 所有輸入素材保存至 `docs/req/`（**唯讀原則**：不修改原始來源）
- 舊版文件歸檔至 `docs/req/old-{DOC}-{timestamp}.md`
- `completed_steps` 追蹤已完成步驟，支援斷點續行

### 6.5 模板驅動生成（F-05）

- 所有文件結構由 `templates/*.md` 決定
- gen-* skill 只做流程編排，不 inline 定義文件結構
- 模板位於 `~/projects/gendoc/templates/`（14 份文件模板）

### 6.6 HTML 文件網站（F-06）

- `gendoc-gen-html` 將所有 docs/*.md 轉換為靜態 HTML
- 自動生成導覽、TOC、文件版本資訊
- 支援部署至 GitHub Pages

---

## 7. 非功能需求

### 7.1 效能

- Full-Auto 模式下，完整 9 份文件生成時間目標：≤ 60 分鐘
- 每份文件 Review Loop 時間目標：≤ 10 分鐘（standard 策略）

### 7.2 可靠性

- TF-02 斷點續行：任何步驟中斷後重啟，自動從上次完成點繼續
- State file 原子寫入，防止部分寫入導致的損毀

### 7.3 安全性

- 唯讀原則：本地路徑來源嚴禁寫入、刪除、修改原始目錄
- State file 的 `skill_source` 欄位防止跨套件誤用（`gendoc-auto` 鎖定）

### 7.4 可維護性

- 每個 gen-* skill 獨立，可單獨更新或替換
- 模板與 skill 邏輯分離，更新模板不需修改 skill

### 7.5 文件品質保證（Blueprint Quality Gate）

每份文件必須通過的最低標準（由 Review Loop 執行驗證）：

| 文件 | 必過項目 |
|------|---------|
| EDD | 每個 class 有 method 列表；每個 method 有型別簽名；有 pre/post-condition；有例外行為 |
| API.md | 每個端點有完整 request schema；有全部 error code；有 Rate Limit 定義 |
| SCHEMA.md | 完整 DDL；有 index 策略（含理由）；有 constraint；有 migration 說明 |
| test-plan.md | 每個功能有 EP 測試表；有 BVA 邊界值對照表；有並發/冪等性情境 |
| BDD-server（features/） | 每個 PRD P0 AC 有 Server Gherkin Scenario；6 種 HTTP 錯誤碼（401/403/404/409/422/429）全部覆蓋；無任何 UI 步驟 |
| BDD-client（features/client/） | 每個 P0 Screen 有 E2E Scenario；含 happy path、error flow、auth guard；無後端邏輯驗證 |

---

## 8. 模板清單

| 文件 | 模板 | 對應 gen.md | 層級 | 細粒度要求 |
|------|------|------------|------|-----------|
| `docs/IDEA.md` | `IDEA.md` | `IDEA.gen.md` | Layer 0 | 問題定義、使用者、解法假設、Appendix C 素材索引 |
| `docs/BRD.md` | `BRD.md` | `BRD.gen.md` | Layer 1 | 業務需求、MoSCoW、成功指標、範疇 |
| `docs/PRD.md` | `PRD.md` | `PRD.gen.md` | Layer 2 | User Stories + Acceptance Criteria、功能/非功能需求 |
| `docs/PDD.md` | `PDD.md` | `PDD.gen.md` | Layer 3a | UX Flow、Wireframe 描述、Persona、Journey Map（client_type≠none） |
| `docs/VDD.md` | `VDD.md` | `VDD.gen.md` | Layer 3.5 | Art Direction、Brand Identity、**Design Token 三層架構**、資產管線規格（client_type≠none） |
| `docs/EDD.md` | `EDD.md` | `EDD.gen.md` | Layer 4 | **class + method 簽名 + 型別 + 例外**、UML 9 大圖 |
| `docs/ARCH.md` | `ARCH.md` | `ARCH.gen.md` | Layer 5a | C4 Model、元件圖、sequence diagram、ADR |
| `docs/API.md` | `API.md` | `API.gen.md` | Layer 5b | **完整 request/response/error schema**、Rate Limit |
| `docs/SCHEMA.md` | `SCHEMA.md` | `SCHEMA.gen.md` | Layer 5c | **DDL + index + constraint**、ER 圖、Migration 策略 |
| `docs/FRONTEND.md` | `FRONTEND.md` | `FRONTEND.gen.md` | Layer 6 | 元件架構、State Management、**實作 VDD Design Token**（client_type≠none） |
| `docs/test-plan.md` | `test-plan.md` | `test-plan.gen.md` | Layer 7 | **EP + BVA + 並發**、測試金字塔 |
| `features/*.feature` | `BDD-server.md` | `BDD-server.gen.md` | Layer 8a | **Gherkin Scenario + edge case + unhappy path**（Server API BDD） |
| `features/client/*.feature` | `BDD-client.md` | `BDD-client.gen.md` | Layer 8b | Client E2E Scenario（client_type≠none） |
| `docs/RTM.md` | `RTM.md` | `RTM.gen.md` | Layer 9 | US↔TC↔BDD Scenario 三向追溯矩陣 |
| `docs/RUNBOOK.md` | `runbook.md` | `runbook.gen.md` | Layer 9 | 凌晨 3 點可直接執行，零前情提要 |
| `docs/LOCAL_DEPLOY.md` | `LOCAL_DEPLOY.md` | `LOCAL_DEPLOY.gen.md` | Layer 9 | 新進工程師 5 分鐘內完成本地環境 |
| `docs/README.md` | `README.md` | `README.gen.md` | Layer 10 | 安裝、快速開始、API 概覽 |
| `docs/ALIGN_REPORT.md` | — | align-check skill | 稽核層 | 跨文件不一致清單 |
| — | `UML-CLASS-GUIDE.md` | 靜態參考 | — | Class Diagram 規範（不生成） |

---

## 9. 安裝與使用

### 9.1 安裝

```bash
# Skills 安裝（22 個 skill 位於 ~/.claude/skills/gendoc-*/）
# Templates 安裝（14 份模板位於 ~/projects/gendoc/templates/）
# 無其他依賴，開箱即用
```

### 9.2 基本使用

```bash
# 純文字輸入
/gendoc-auto 我想做一個 AI 驅動的客服機器人

# URL 輸入
/gendoc-auto https://github.com/some/repo

# 本地目錄輸入
/gendoc-auto ~/projects/my-existing-app

# 已有 BRD 直接進入流水線
/gendoc-flow

# 設定執行模式與 Review 策略
/gendoc-config
```

### 9.3 設定模式

- **gendoc-auto**：直接執行，Full-Auto 模式，無任何問答
- **gendoc-config**：互動設定執行模式、Review 策略、從哪個 STEP 重跑

---

## 10. 未來規劃（Out of Scope v1.0）

- 與 MYDEVSOP 完整 SDLC 流水線的雙向同步（已有 BRD 直接接 devsop-autodev）
- 多語言文件輸出（目前以中文為主，英文模板為輔）
- 文件版本差異比較（diff-based document review）
- CI/CD 觸發自動文件更新（code change → doc refresh）
- 程式碼品質反推文件更新（如 test coverage < 80% → 自動更新 test-plan 缺口）

---

## 11. 成功指標

| 指標 | 目標 |
|------|------|
| 完整文件集生成成功率（Full-Auto） | ≥ 90% |
| 平均生成時間（9 份文件） | ≤ 60 分鐘 |
| EDD class + method 完整率 | 100%（每個 class 有 method 列表） |
| test-plan BVA 覆蓋率 | 每個功能至少有邊界值對照表 |
| 跨文件一致性（align-check finding=0 比例） | ≥ 80% |
| AI 讀取文件後首次生成程式碼通過 CI 率 | ≥ 70% |
| 斷點續行成功率 | 100% |
| 安裝步驟數 | ≤ 3 步 |
