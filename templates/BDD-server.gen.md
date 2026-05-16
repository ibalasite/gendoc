---
doc-type: BDD-server
output-path: features/（多個 .feature 檔案）
output-glob: features/*.feature
multi-file: true
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/EDD.md
  - docs/ARCH.md
  - docs/API.md
  - docs/SCHEMA.md
  - docs/test-plan.md
quality-bar: "所有 PRD P0 AC 有對應 Server BDD Scenario（正常路徑 + 錯誤路徑）；所有 API Endpoint 有 @contract Scenario；6 個 HTTP 錯誤碼（401/403/404/409/422/429）有對應 Error Scenario；無 UI 操作或前端細節滲入 Step；無假斷言（Then 必須具體且可測試）"
gen-expert: "資深 Backend QA Architect（10 年以上 BDD + API Contract Testing 經驗）"
---

# BDD-server.gen.md — Server BDD Feature Files 生成規則

依 PRD 每個驗收標準（AC）、API.md 每個 Endpoint，自動生成完整的 Server BDD Feature Files（Gherkin 格式）。
輸出目錄：`features/`（每個 PRD 功能 → 一個 .feature 檔案）。

**職責邊界（與 BDD-client 區分）：**
- Server BDD = API 層行為、業務邏輯、資料持久化、認證授權、Contract Testing
- 禁止包含 UI 操作、畫面跳轉、元件顯示等前端行為（那是 BDD-client 的責任）

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
| `IDEA.md`（若存在）| 全文 | 了解產品願景，BDD 業務語言需反映 IDEA 業務概念 |
| `BRD.md` | 業務目標、驗收標準 | Feature 標題的業務語意來自 BRD |
| `PRD.md` | 所有功能 AC | **主要輸入**：每個 AC → 至少 1 正常路徑 + 1 錯誤路徑 Scenario |
| `EDD.md` | §4 Security、§5 BDD 設計、§3 lang_stack | 確認認證流程（JWT/OAuth）和已規劃的 Scenario 結構 |
| `ARCH.md` | §3 元件架構 | 確認 Contract Testing 的 Provider/Consumer 邊界 |
| `API.md` | 所有 Endpoint、Request/Response | **@contract tag**：每個 API Endpoint 必須有對應 BDD Scenario |
| `SCHEMA.md` | 資料模型 | Background 的資料初始化步驟（Given 的 clean state 設計）|
| `test-plan.md` | §3.3 E2E/BDD、§9 Risk Matrix | Smoke 標記（Risk=High 的功能 Scenario 數量加倍）|

若某文件不存在，靜默跳過，依既有流程繼續。

### test-plan.md 特別讀取規則

若 `docs/test-plan.md` 存在，額外讀取：
- **§3.3 E2E / BDD Tests**：確認 BDD 工具（Cucumber/Behave/Godog 等）、Critical User Flow 清單
  → 清單中標記為 `Smoke: Y` 的 Flow 必須生成 `@smoke` tag Scenario
- **§9 Risk-Based Testing Matrix**：Risk Level = High 的功能，Scenario 數量加倍（至少 2× 正常 + 2× 錯誤 + 1× 邊界）
- **§15 RTM（若存在 TC-ID）**：生成的 Scenario tag 補充對應 TC-ID（格式：`@TC-E2E-{MODULE}-{SEQ}-{CASE}`）

### IDEA.md Appendix C 素材讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與 BDD 相關的檔案。
結合 Appendix C「應用於」欄位標有「BDD §」的段落，作為生成 Scenario 的補充依據。
若無引用，靜默跳過。

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- PRD 的 AC vs API.md 的 Endpoint（是否有 AC 無對應 API）
- EDD §5 的 BDD 設計 vs PRD 的 AC（是否有 Scenario 設計但無對應 AC）

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並說明影響的 Scenario 範圍。

---

## 多檔案生成規則

**一個 PRD 功能 → 一個 .feature 檔案**，輸出到 `features/` 目錄。

命名規則：
```
features/{domain}/{resource}_{action}.feature
```

範例：
| PRD 功能 | Domain | 輸出路徑 |
|---------|--------|---------|
| 使用者登入 | auth | `features/auth/user_login.feature` |
| 使用者註冊 | auth | `features/auth/user_registration.feature` |
| 訂單建立 | orders | `features/orders/order_create.feature` |
| 訂單查詢 | orders | `features/orders/order_list.feature` |
| 商品搜尋 | catalog | `features/catalog/product_search.feature` |

**[AI 指令]** 生成每個 .feature 檔案時，使用 Write 工具逐一寫入，並輸出：
```
GENERATED_FILE: features/{domain}/{name}.feature
```
最後彙總所有生成的檔案清單。

---

## Gherkin 格式規範

### 標準結構

```gherkin
# features/<domain>/<resource>_<action>.feature
# 來源：PRD §<功能名稱>，AC-1～AC-N

Feature: <功能名稱（與 PRD 一致）>
  作為 <角色>
  我希望 <功能>
  以便 <目的>

  Background:
    Given 資料庫已初始化（clean state）
    And <必要的測試資料>

  # ─── 正常路徑 ───────────────────────────────────────────
  @p0 @smoke @contract @TC-{MODULE}-{SEQ}-001
  Scenario: <正常路徑描述（業務語言）>
    Given <系統初始狀態（非操作動詞）>
    When <使用者或系統執行的單一動作>
    Then <可觀測的業務結果（具體、可測試）>
    And <補充斷言>

  # ─── 錯誤路徑 ───────────────────────────────────────────
  @p0 @regression @TC-{MODULE}-{SEQ}-002
  Scenario: <錯誤路徑描述>
    Given <初始狀態>
    When <觸發錯誤的動作>
    Then <預期的錯誤回應（含具體錯誤碼 / 訊息）>

  # ─── 邊界條件 ───────────────────────────────────────────
  @p0 @regression @TC-{MODULE}-{SEQ}-003
  Scenario Outline: <邊界條件描述>
    Given <初始狀態>
    When <使用者輸入 "<input_value>">
    Then <預期結果是 "<expected_result>">

    Examples:
      | input_value | expected_result |
      | ""          | 錯誤：必填欄位  |
      | "invalid"   | 錯誤：格式不合  |
```

### Step 語義規範

| Step | 規範 | 反面範例（禁止）|
|------|------|----------------|
| Given | 描述**狀態**，非操作動詞 | `Given 呼叫了 POST /users` |
| When | 每個 Scenario **只有一個 When** | `When 先呼叫 A，再呼叫 B` |
| Then | **可觀測的業務結果**（具體值）| `Then 程式沒有報錯` |

---

## Scenario 數量規則

**基本規則（每個 AC）：**
- 至少 1 個正常路徑 Scenario
- 至少 1 個錯誤路徑 Scenario
- 有邊界條件時使用 Scenario Outline + Examples Table

**Risk Level = High 的功能（來自 test-plan.md §9）：**
- 至少 2× 正常路徑 Scenario
- 至少 2× 錯誤路徑 Scenario
- 至少 1× 邊界 Scenario Outline

---

## Tag 策略

| Tag | 用途 | 規則 |
|-----|------|------|
| `@p0` | Must-have 功能 Scenario | PRD P0 AC 全部標記 |
| `@p1` | Should-have 功能 Scenario | PRD P1 AC 全部標記 |
| `@smoke` | 核心主要路徑 Scenario | Critical Flow Happy Path |
| `@regression` | 完整回歸測試 Scenario | 所有 Scenario 均標記 |
| `@api` | API 層測試 Scenario | 後端 API Scenario |
| `@contract` | API 契約測試 | 每個 API Endpoint 必須有一個 |
| `@TC-E2E-{MODULE}-{SEQ}-{CASE}` | RTM 追溯 tag | 與 test-plan RTM 完全一致 |

---

## Error Scenario Catalog（必備 6 個 HTTP 錯誤碼）

每個 Feature 必須涵蓋以下 HTTP 錯誤碼的 Scenario：

| HTTP 碼 | 場景 | 必備 Scenario |
|---------|------|--------------|
| 401 | 未認證 | Token 無效或過期時拒絕存取 |
| 403 | 無權限 | 角色不符時拒絕操作 |
| 404 | 資源不存在 | 操作不存在的資源 |
| 409 | 衝突 | 建立重複資源 |
| 422 | 業務規則違反 | 違反業務邏輯（含具體說明）|
| 429 | Rate Limit | 超過速率限制 |

---

## Contract Testing 規則

- API.md 中每個 Endpoint 必須有至少一個 `@contract` tagged Scenario
- `@contract` Scenario 的 Then 步驟必須驗證具體的 HTTP 狀態碼和回應結構
- Contract Testing 追溯矩陣需建立（BDD Scenario → API Endpoint → HTTP Method → 回應碼）

---

## Test Data Management 規則

- 使用 Factory 動態建立 Test Data（禁止 hardcode 真實 PII）
- AfterScenario / Background 清理機制確保 clean state
- 測試帳號使用 `@example.com` 或 `@test.internal` 網域
- 禁止：測試 Scenario 依賴其他 Scenario 的資料殘留
- 禁止：直接使用生產環境帳號

---

## 禁止模式（Anti-patterns）

**技術語言滲入（CRITICAL）：**
- 禁止在 Given/When/Then 出現 SQL 語法、class 名稱
- 除 `@contract` Scenario 外，不暴露 HTTP 狀態碼數字（用業務語言描述）

**假斷言（CRITICAL）：**
- 禁止 Then 步驟為空或僅含 `# TODO`
- 禁止 `Then 程式沒有報錯`（過於模糊）

**前端邏輯滲入（HIGH）：**
- 禁止在 Server BDD 中描述 UI 元素（按鈕、頁面跳轉、視覺狀態）
- 所有 UI 層驗收場景由 BDD-client 負責

**隔離性破壞（HIGH）：**
- 禁止 Scenario 依賴其他 Scenario 的執行順序
- 每個 Scenario 必須能獨立執行

---

## Self-Check Checklist（生成前必查）

- [ ] 每個 PRD P0 功能至少有一個 .feature 檔
- [ ] 每個 PRD AC 至少有一個 Scenario（正常路徑 + 錯誤路徑）
- [ ] 邊界條件使用 Scenario Outline + Examples Table
- [ ] 所有 Then 斷言具體且可測試（無模糊語言）
- [ ] 無 UI 操作或前端細節滲入 Step（頁面跳轉、按鈕點擊等）
- [ ] 所有 API.md Endpoint 有對應的 `@contract` tagged Scenario
- [ ] Contract Testing 追溯矩陣已建立
- [ ] 6 個 HTTP 錯誤碼（401/403/404/409/422/429）均有對應的 Error Scenario
- [ ] `@smoke` 已標記核心 Critical Flow 主要路徑 Scenario
- [ ] Risk Level = High 的功能（test-plan.md §9）Scenario 數量已加倍
- [ ] test-plan.md RTM 的 TC-ID 已補充至對應 Scenario tag（`@TC-E2E-*`）
- [ ] Background 清理機制確保 clean state
- [ ] Test Data 使用 Factory 動態建立，禁止 hardcode 真實 PII
- [ ] 所有 `[UPSTREAM_CONFLICT]` 標記均已處理或說明
- [ ] 每個 .feature 檔案都輸出了 `GENERATED_FILE: features/{path}` 紀錄
- [ ] Step Definitions skeleton 已生成（`features/step_definitions/server_steps.ts` 或對應語言副檔名）

---

## F-03：Step Definitions Skeleton 生成要求

所有 `.feature` 檔案生成完成後，必須額外生成 Step Definitions skeleton：

**輸出路徑**：依 lang_stack 偵測決定副檔名
- TypeScript/JavaScript → `features/step_definitions/server_steps.ts`
- Python → `features/step_definitions/server_steps.py`
- Go → `features/step_definitions/server_steps_test.go`
- Java → `src/test/java/stepdefs/ServerSteps.java`

**Skeleton 格式要求**：
1. 列出所有在 .feature 中出現的 Step Pattern（Given/When/Then）
2. 每個 Step 有空實作（`// TODO: implement`）
3. 包含必要的 import/require（依語言）
4. 不得實作業務邏輯（只提供 skeleton，供開發者填入）
5. 使用 `GENERATED_FILE: features/step_definitions/server_steps.{ext}` 紀錄

**Skeleton 範例（TypeScript/Cucumber）**：
```typescript
import { Given, When, Then } from '@cucumber/cucumber';

// Auto-generated skeleton from BDD-server.gen.md — DO NOT EDIT (structure)
// Fill in implementation for each step

Given('a valid user with credentials {string} and {string}', async (username, password) => {
  // TODO: implement
});

When('I POST to {string} with body {string}', async (endpoint, body) => {
  // TODO: implement
});

Then('I receive HTTP status {int}', async (statusCode) => {
  // TODO: implement
});
```

**支援檔案（必須同步生成）：**

**`features/support/world.ts`（TypeScript 範例）**：
```typescript
import { IWorldOptions, World, setWorldConstructor } from '@cucumber/cucumber';
import axios, { AxiosInstance } from 'axios';

export interface ApiWorld {
  client: AxiosInstance;
  response: { status: number; data: unknown } | null;
  db: { seed: (fixture: string) => Promise<void>; clean: () => Promise<void> };
}

class CustomWorld extends World implements ApiWorld {
  client: AxiosInstance;
  response: { status: number; data: unknown } | null = null;
  db: { seed: (fixture: string) => Promise<void>; clean: () => Promise<void> };

  constructor(options: IWorldOptions) {
    super(options);
    this.client = axios.create({ baseURL: process.env.API_BASE_URL || 'http://localhost:8080' });
    this.db = {
      seed: async (fixture) => { /* TODO: load fixture data */ },
      clean: async () => { /* TODO: truncate test tables */ },
    };
  }
}

setWorldConstructor(CustomWorld);
```

**`features/support/hooks.ts`**：
```typescript
import { BeforeAll, AfterAll, Before, After, setDefaultTimeout } from '@cucumber/cucumber';
import { ApiWorld } from './world';

setDefaultTimeout(30_000);

BeforeAll(async () => {
  // TODO: start test database, run migrations
});

AfterAll(async () => {
  // TODO: close database connections
});

Before(async function (this: ApiWorld) {
  await this.db.clean();
});

After(async function (this: ApiWorld) {
  this.response = null;
});
```

使用 `GENERATED_FILE: features/support/world.ts` 和 `GENERATED_FILE: features/support/hooks.ts` 紀錄。

---

## §A World Fixture Factory（AI Gencode 強制）

> **目的**：讓 AI codegen 能生成可執行的 Given step，直接 seed DB 前置資料，不依賴人工推斷。

### §A.1 World 介面（具體版，非 TODO）

以下為 world.ts 的**完整實作介面**，替換上方 TODO 骨架中的 `db` 定義。

`db` 的完整介面：

```typescript
// FixtureMap key = SCHEMA.md §BC ownership 的 BC 名稱（不寫死）
interface FixtureMap {
  [bcName: string]: Record<string, unknown>[];
}

interface DbHelper {
  // 依 SCHEMA.md FK 順序 INSERT 測試資料
  seed(map: FixtureMap): Promise<void>;
  // TRUNCATE 所有 business tables（排除 audit/log tables）
  clean(): Promise<void>;
  // 供 Then step 直接查 DB 驗證狀態
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[] }>;
}
```

`redis` 的介面（**SCHEMA.md 含 Redis key pattern 時才生成**）：

```typescript
interface RedisHelper {
  set(key: string, value: string, ttl?: number): Promise<void>;
  get(key: string): Promise<string | null>;
  del(key: string): Promise<void>;
}
```

Auth helper 介面（**強制**）：

```typescript
interface AuthHelper {
  // role 名稱從 SCHEMA.md role table 讀取（不寫死 'admin'/'player'）
  loginAs(role: string, overrides?: Record<string, unknown>): Promise<string>; // 回傳 JWT
  // has_admin_backend=true 時生成
  loginAsAdmin(email: string, password: string, otpCode?: string): Promise<string>;
}
```

World 必備屬性（**依 SCHEMA.md 主鍵欄位動態生成**）：

```typescript
// 通用屬性
lastResponse: { status: number; body: unknown };
authToken: string | null;
// 每個 BC 的主鍵屬性，依 SCHEMA.md 生成
// 例：petId, userId, listingId — 名稱從 SCHEMA.md 各 BC 主表讀取
db: DbHelper;
redis?: RedisHelper;  // SCHEMA.md 含 Redis 時生成
auth: AuthHelper;
```

### §A.2 Fixture 資料規則（通用鐵律）

| 規則 | 說明 |
|------|------|
| UUID 格式 | `'{domain_prefix}-{sequence:03}'`，如 `'user-001'`，確保跨 scenario 不衝突 |
| 時間欄位 | `new Date().toISOString()`，禁止硬碼字串 |
| ENUM 值 | 必須使用 SCHEMA.md 中已定義的合法 enum 值 |
| 禁止 PII | 使用 `test@example.com`、`test-user-001` 等明顯測試資料 |
| FK 順序 | seed() 依 SCHEMA.md FK 依賴順序執行（parent BC 先插） |
| 禁止共享狀態 | 每個 scenario 必須獨立 seed，Before hook 呼叫 clean() |

### §A.3 Before Hook（具體版）

```typescript
// hooks.ts — 具體版
BeforeAll(async () => {
  // 1. 建立 DB 連線 pool（連線字串從 ENV 讀取）
  // 2. 執行 migration（若 test DB 未 up）
  // 3. SCHEMA.md 含 Redis 時：await redis.flushDb()（測試用 DB，非生產 DB）
});

Before(async function (this: AppWorld) {
  await this.db.clean();  // TRUNCATE 所有 business tables
  // SCHEMA.md 含 Redis：可選擇 flushDb 或逐 key 清理
});

AfterAll(async () => {
  // 關閉 DB pool + Redis client
});
```

---

## §B.0 Given Step 唯一合法模式（所有專案強制鐵律）

Given step 建立前置狀態的**唯一合法模式**是直接 DB seed（引用 §A World fixture 介面）：

```typescript
// ✅ 唯一合法模式
Given('{string} exists', async function(this: AppWorld) {
  await this.db.seed({
    '{bc_name_from_schema}': [{ id: 'entity-001', status: 'active', ... }]
    //  ↑ key = SCHEMA.md BC 名稱  ↑ id 固定格式字串（非 uuid()）
  });
});
```

### 禁止的 Anti-patterns（明確列舉，AI 不得生成以下任何模式）

**❌ Anti-pattern 1：在 Given step 呼叫 API endpoint 建立資料**

```typescript
// ❌ 禁止
Given('{string} exists', async function(this: AppWorld) {
  this.lastResponse = await this.client.post('/api/entity', { ... }); // API 呼叫
});
```

原因：Given 依賴 API 實作；API 改動會讓 Given 失敗，導致測試 cascade 崩潰。

---

**❌ Anti-pattern 2：Factory helper 帶隨機資料**

```typescript
// ❌ 禁止
Given('{string} exists', async function(this: AppWorld) {
  const entity = EntityFactory.create();  // 隨機資料，不可重現
});
```

原因：隨機值導致 test vector 不可重現；ENUM 值可能隨機到無效值。

---

**❌ Anti-pattern 3：跨 scenario 共享狀態（缺少 Before clean）**

```typescript
// ❌ 禁止（第一個 scenario 的 seed 污染第二個 scenario）
// Before hook 必須每次 clean，見 §A.3
```

原因：未 clean 的前一 scenario seed 資料會使下一個 scenario 狀態不確定。

---

**❌ Anti-pattern 4：直接寫 SQL 字串而非 seed() 介面**

```typescript
// ❌ 禁止
await this.db.query("INSERT INTO entities VALUES (...)", [...]);
```

原因：`seed()` 封裝了 FK 依賴排序，繞過它會導致 FK violation。

---

### 唯一合法模式（完整規則）

```typescript
// ✅ 永遠用 this.db.seed({ '{bc_name_from_schema}': [{ ...fixed_values }] })
// ✅ id 欄位用固定格式字串（'entity-001'），不用 uuid()
// ✅ ENUM 欄位用 SCHEMA.md 定義的合法值（引用 type alias，不寫字串 literal）
// ✅ 時間欄位用 new Date().toISOString()（不寫死日期字串）
// ✅ FK 欄位用與父表 seed 一致的固定 id（'parent-001' 等）
```

**Quality Gate**：

| 檢查項 | 合格標準 |
|--------|---------|
| AI Gencode — Given 唯一模式 | 所有 Given step 使用 `this.db.seed()`；無 API 呼叫、factory、隨機資料、裸 SQL |

---

## §B Step Definition 實作配方（AI Gencode 強制）

> **目的**：提供 Given/When/Then 三種 step 的具體程式碼骨架，AI codegen 可直接套用。

### §B.1 Given — 建立前置狀態（fixture seeding）

```typescript
// 模式：seed DB → 儲存 ID 到 world 供後續 step 使用
Given('{string} user exists with {string}', async function(this: AppWorld, role, email) {
  await this.db.seed({
    // key = SCHEMA.md BC 名稱；欄位名從 SCHEMA.md 對應表讀取
    identity: [{ id: 'user-001', email, status: 'active', created_at: new Date().toISOString() }],
  });
  this.authToken = await this.auth.loginAs(role);
});
```

### §B.2 When — 呼叫 API（必須捕獲完整 response）

```typescript
// 模式：呼叫 API → 捕獲 response（含 4xx/5xx，不 throw）→ 儲存到 world
When('the client calls {string} {string}', async function(this: AppWorld, method, path) {
  this.lastResponse = await this.client.request({
    method: method.toLowerCase() as 'get' | 'post' | 'put' | 'delete' | 'patch',
    url: path,   // path 從 API.md 讀取（不硬碼）
    headers: this.authToken ? { Authorization: `Bearer ${this.authToken}` } : {},
  }).then(r => ({ status: r.status, body: r.data }))
    .catch(e => ({ status: e.response?.status ?? 0, body: e.response?.data ?? null }));
});
```

### §B.3 Then — 斷言 HTTP 狀態 + DB 狀態

```typescript
// HTTP 狀態斷言
Then('the response status is {int}', function(this: AppWorld, expectedStatus) {
  assert.strictEqual(this.lastResponse.status, expectedStatus,
    `Expected ${expectedStatus}, got ${this.lastResponse.status}: ${JSON.stringify(this.lastResponse.body)}`);
});

// DB 狀態斷言（直接查 DB 驗證業務結果）
Then('the {string} record has {string} equal to {string}', async function(
  this: AppWorld, table, column, expectedValue
) {
  // table / column 從 SCHEMA.md 讀取（Cucumber expression 動態傳入）
  const result = await this.db.query(
    `SELECT ${column} FROM ${table} WHERE id = $1`,
    [this.lastEntityId]   // lastEntityId 由 Given step 寫入 world
  );
  assert.ok(result.rows.length > 0, `No row found in ${table}`);
  assert.strictEqual(String(result.rows[0][column]), expectedValue);
});
```

### §B.4 Rate Limit Fixture 模式（SCHEMA.md 含 Redis key 時）

```typescript
// 預填 rate limit 計數器到閾值前一步，讓 When step 直接觸發 429
Given('{int} requests already made this window', async function(this: AppWorld, count) {
  // key pattern 從 SCHEMA.md Redis Key Patterns 欄讀取（不硬碼 prefix）
  const key = `{rate_limit_key_pattern}`.replace('{entityId}', this.lastEntityId);
  const ttl = Number(process.env['RATE_LIMIT_WINDOW_SECONDS'] ?? 3600);  // 從 CONSTANTS.md 讀取
  await this.redis!.set(key, String(count), ttl);
});
```

### §B.5 Multi-step Response ID 串接模式

```typescript
// When step 建立資源後，儲存回傳 ID 供後續 step 使用
When('the client creates a {string}', async function(this: AppWorld, resourceType) {
  this.lastResponse = await this.client.post(
    `{endpoint_from_api_md}`,   // endpoint 從 API.md 讀取
    { /* request body from API.md DTO */ },
    { headers: { Authorization: `Bearer ${this.authToken}` } }
  ).then(r => ({ status: r.status, body: r.data }))
   .catch(e => ({ status: e.response?.status ?? 0, body: e.response?.data ?? null }));

  // 儲存 ID 供後續步驟使用（欄位名從 API.md response schema 讀取）
  if (this.lastResponse.status === 201) {
    this.lastEntityId = (this.lastResponse.body as Record<string, string>)['id'];
  }
});
```

---

## §C Redis Fixture（SCHEMA.md 含 Redis 時強制）

> **觸發條件**：SCHEMA.md 存在 `Redis Key Patterns` 或等效 section（描述 Redis key 命名規則）。

### §C.1 Redis Helper 實作骨架

```typescript
// world.ts — redis 屬性實作骨架
import { createClient, RedisClientType } from 'redis';

// 在 World constructor 中初始化（BeforeAll 後）
const redisClient: RedisClientType = createClient({
  url: process.env['REDIS_TEST_URL'] ?? 'redis://localhost:6379/15',  // DB 15 = 測試專用
});

this.redis = {
  set: (key, value, ttl) => ttl
    ? redisClient.setEx(key, ttl, value).then(() => undefined)
    : redisClient.set(key, value).then(() => undefined),
  get: (key) => redisClient.get(key),
  del: (key) => redisClient.del(key).then(() => undefined),
};
```

### §C.2 Key 命名規則

- **嚴格引用** SCHEMA.md 的 Redis key pattern（禁止自行推斷 key 格式）
- BeforeAll：`await redisClient.flushDb()` — 清空測試用 Redis DB
- 測試用 DB index 必須與生產 DB index 不同（通常使用 DB 14 / DB 15）

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| API 覆蓋率 | API.md 每個 endpoint 至少有一個對應 Scenario | 補充缺失 Scenario |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | HTTP 方法、路徑、Content-Type 與 API.md 定義一致 | 以 API.md 為準修正 |
| 數值非 TBD/N/A | 回應碼、Payload 欄位填有實際值 | 從 API.md 對應定義填入 |
| 測試資料真實 | 請求體範例非 "string" / 1 / true，使用符合業務語義的真實格式 | 替換為業務語義資料 |
| 錯誤路徑覆蓋 | 每個 endpoint 至少有 1 個錯誤 Scenario（4XX/5XX） | 補充錯誤 Scenario |
| Modulith 架構 BDD | `features/architecture/` 目錄存在，@modulith @p0 Scenario **≥ 5 個**（HC-1 Schema 隔離 / HC-2 Public Interface / HC-3 Event Contract / HC-4 Redis Namespace / HC-5 DAG verify 各至少 1 個）| 依 BDD.md §18 生成缺失 Modulith Feature；5 個 HC 每個至少對應 1 個 Scenario |
| Event Contract 覆蓋 | @event-contract Scenario 覆蓋所有跨 BC Domain Event consumer pair（來自 EDD §4.6.1，Consumer BC(s) 非空的每個 pair 各對應 ≥1 個 Scenario）| 依 BDD.md §18.3 補充 Pact consumer 驗證 Scenario；若 EDD §4.6.1 缺失先標注 BLOCKED |
| AI Gencode — Step Definition Stubs | `features/step_definitions/` 目錄存在對應語言的 stub 檔；每個 `.feature` 中的 Given/When/Then 均有對應 stub（`return 'pending'` 或語言等效）；無 step 文字找不到 definition 的錯誤 | 依 §Step Definitions 生成規則補全缺失 stub；`world.{ext}` 和 `hooks.{ext}` 同步生成 |
| AI Gencode — Step stub 品質 | 每個 stub 含 inline 註解指向對應的 API endpoint（例如 `// POST /api/v1/claim — 見 API.md §5.1.2`）；stub 不含任何業務邏輯實作（只有 pending/TODO） | 為每個 stub 補充 API endpoint 引用注釋 |
| AI Gencode — World fixture interface | world.ts 含完整 `db.seed / db.clean / db.query` 介面定義（非 TODO 占位）；Before hook 呼叫 `db.clean()` | 依 §A.1 World 介面補寫；Before hook 補 clean() 呼叫 |
| AI Gencode — Step 實作配方 | BDD-server.md 含 §B Given/When/Then 三種具體程式碼骨架（非 TODO）；When step 以 `.catch` 捕獲 4xx/5xx | 依 §B Step Implementation Pattern 補寫 |
| AI Gencode — Redis fixture（有 Redis 時） | SCHEMA.md 含 Redis key pattern 的專案：world.ts 含 `redis.set/get/del` 介面；BeforeAll 有 flushDb | 依 §C Redis Fixture 補寫 |
