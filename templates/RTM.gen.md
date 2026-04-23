---
doc-type: RTM
output-path: docs/RTM.md
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
  - docs/FRONTEND.md  # Layer 6 — 前端元件追溯到 E2E Test Case
  - docs/test-plan.md
  - features/          # BDD-server 輸出（Server BDD Feature Files）
  - features/client/   # BDD-client 輸出（Client E2E Feature Files，若 client_type≠none）
quality-bar: "100% PRD P0 User Stories 有對應 Test Case；所有 BDD @tag 在 RTM 有對應條目；無孤立 Test Case（有測試無需求）；§1 統計數字與正文完全一致。"
---

# RTM.gen.md — Requirements Traceability Matrix 生成規則

依 PRD + EDD + API + test-plan + BDD 產出 RTM.md，建立從業務需求到測試案例的完整追溯矩陣。

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
| `IDEA.md`（若存在） | 全文 | 了解產品性質、核心業務假設 |
| `BRD.md` | Must Have 需求清單 | 建立頂層 Req-ID 清單（RQ-xxx），對應業務需求 |
| `PRD.md` | §3/§4/§5 User Stories 和 AC、P0/P1/P2 分類 | 建立 US-ID 清單，提取所有 AC 作為 Unit/Integration Test 基礎 |
| `EDD.md` | §3 技術選型、§6 Class Diagram | 提取 Class 名稱和 Method 清單，填入 §3 Unit Test RTM |
| `API.md` | 所有 Endpoint（§2）、認證方式 | 建立 API-ID 清單，填入 §4 Integration Test RTM |
| `SCHEMA.md` | 資料表清單、索引定義 | 補充 DB Layer 的 Integration Test 場景（如 unique constraint）|
| `FRONTEND.md`（若存在）| §4 Screen 清單、§10 E2E 覆蓋範圍 | 前端元件追溯到 E2E Test Case；§5 E2E Test RTM 的 Screen Name 欄位和 VRT 覆蓋條目來自 FRONTEND |
| `test-plan.md` | 測試策略、工具組合、覆蓋率目標 | 確認測試工具選型，填入 Tool 欄位；對齊覆蓋率目標 |
| `features/*.feature`（BDD-server）| Server BDD Scenario、@TC-ID tag | 提取 @TC-ID tag，建立 Server BDD → RTM 映射；填入 §5 E2E Test RTM（後端行為）|
| `features/client/*.feature`（BDD-client，若存在）| Client E2E Scenario、@TC-ID tag | 填入 §5 E2E Test RTM（UI / E2E 行為）；Screen Flow 覆蓋率計算 |
| `PDD.md`（若存在） | Screen 清單、SC-ID | 填入 §5 E2E Test RTM 的 SC-ID 和 Screen Name 欄位 |

### IDEA.md Appendix C 素材讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與需求追溯相關的檔案。
對每個存在的 `docs/req/` 檔案，結合 Appendix C「應用於」欄位，提取業務需求場景和驗收條件，
作為補充 Req-ID 清單和 AC 的參考依據。
優先採用素材原文描述，而非 AI 推斷。若無引用，靜默跳過。

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- BRD Must Have 需求 vs PRD US-ID（是否所有 Must Have 都有對應 US）
- PRD P0 AC 總數 vs BDD Scenario @tag 數量（覆蓋率計算）
- BDD @tag vs RTM TC-ID（是否所有 @tag 都能在 RTM 找到對應條目）
- EDD Class/Method vs RTM Unit Test（是否所有核心 Method 都有 TC-ID）

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並在對應章節加注釋說明。

---

## 資料收集規則

### Req-ID 建立規則

- 從 BRD Must Have 需求清單提取，格式：`RQ-001`、`RQ-002`（三位數遞增）
- 每個 Req-ID 對應 BRD 的一條業務需求
- 若 BRD 無明確 Must Have 分類，以 PRD P0 User Story 為 Req-ID 基礎

### US-ID 對應規則

- 從 PRD §3/§4/§5 提取所有 User Story ID（格式：`US-001`）
- 一個 Req-ID 可對應多個 US-ID（一個業務需求可能拆成多個 User Story）
- 一個 US-ID 對應一個 Req-ID（User Story 必須追溯到一個業務需求）

### TC-ID 命名規則

| Test 類型 | ID 前綴 | 範例 |
|----------|--------|------|
| Unit Test | `TC-` | `TC-001`, `TC-002` |
| Integration Test | `IT-` | `IT-001`, `IT-002` |
| E2E Test | `E2E-` | `E2E-001`, `E2E-002` |

TC-ID 全域唯一，跨三個分類不重複。

### Class/Method 提取規則

- 從 EDD §6 Class Diagram 提取所有 Class 名稱和 Public Method
- 若 EDD 無 Class Diagram，從 EDD §3 技術棧推斷核心 Service Class
- Method 格式：`methodName(paramType)` — 簡化參數類型，保留語意

### BDD @tag 對應規則

- 從 `features/*.feature`（BDD-server）掃描所有 `@TC-E2E-*` 格式的 @tag → 對應 §5 E2E Test RTM（後端）
- 從 `features/client/*.feature`（BDD-client，若存在）掃描所有 `@TC-E2E-*` 格式的 @tag → 對應 §5 E2E Test RTM（UI / E2E）
- 每個 BDD Scenario 的 @tag 對應一個 RTM TC-ID 或 E2E-ID
- 若 BDD Scenario 無 @tag，標記為 `[MISSING_TAG]` 並在 §5 中記錄

---

## §0 Document Control 生成規則

- `DOC-ID`：`RTM-<PROJECT_SLUG 大寫>-<YYYYMMDD>`
- `Status`：`DRAFT`
- `Upstream PRD`：`docs/PRD.md`（真實連結）
- `Upstream EDD`：`docs/EDD.md`（真實連結）
- `Upstream API`：`docs/API.md`（真實連結）
- `Upstream Test Plan`：`docs/test-plan.md`（真實連結）
- `Upstream BDD-server`：`features/`（若目錄存在，填入路徑；否則標注「N/A — BDD-server 尚未生成」）
- `Upstream BDD-client`：`features/client/`（若目錄存在且 client_type≠none，填入路徑；否則標注「N/A」）
- 審閱者：從 EDD Document Control 或 ARCH 提取 QA Lead、Engineering Lead、Product Manager 角色

---

## §1 Summary Statistics 生成規則

### 必填數字

所有統計數字必須從實際上游文件計算，不得保留 `{{...}}` 佔位符：

| 指標 | 計算方式 |
|------|---------|
| `TOTAL_REQUIREMENTS` | BRD Must Have 需求總數（若無 BRD，用 PRD P0 US 數量）|
| `TOTAL_USER_STORIES` | PRD 中所有 US-ID 的數量（P0+P1+P2 總計）|
| `TOTAL_CLASSES` | EDD Class Diagram 中列出的 Class 數量（若無 EDD，填 TBD）|
| `TOTAL_METHODS` | RTM §3.2 表格中不重複的 Method 數量 |
| `TOTAL_TEST_CASES` | `TOTAL_UNIT_TESTS + TOTAL_INTEGRATION_TESTS + TOTAL_E2E_TESTS` |
| `TOTAL_UNIT_TESTS` | RTM §3.2 的資料行數 |
| `TOTAL_INTEGRATION_TESTS` | RTM §4.2 的資料行數 |
| `TOTAL_E2E_TESTS` | RTM §5.2 的資料行數 |
| `REQ_COVERAGE` | `有至少一個 Test Case 的 Req-ID 數 ÷ TOTAL_REQUIREMENTS × 100` |
| `METHOD_COVERAGE` | `有至少一個 TC-ID 的 Method 數 ÷ TOTAL_METHODS × 100` |
| `PASS_RATE` | `狀態為 PASS 的 TC 數 ÷ TOTAL_TEST_CASES × 100` |
| `FAIL_COUNT` | 狀態為 FAIL 的 TC 總數 |
| `TODO_COUNT` | 狀態為 TODO 的 TC 總數（初次生成時應等於 TOTAL_TEST_CASES）|

### §1.1 Mermaid 圖

Pie Chart 使用計算後的真實數字，不保留 `{{...}}` 佔位符。
初次生成時 PASS_COUNT=0、FAIL_COUNT=0、IN_PROGRESS_COUNT=0，所有 TC 狀態為 TODO。

---

## §3 Unit Test RTM 生成規則

### §3.2 Unit Test 追溯表填入規則

**每個 Method 至少生成 3 條 TC：**
1. **Success Path**：正常輸入下的預期成功行為
2. **Error Path**：非法輸入或業務規則違反的錯誤行為（對應 PRD AC 的否定場景）
3. **Boundary**：邊界值測試（空值、最大值、極端格式等）

**Method 選取優先順序：**
1. 首先覆蓋 PRD P0 AC 直接對應的 Service Method
2. 其次覆蓋 Authentication/Authorization 相關 Method
3. 再次覆蓋 SCHEMA Unique Constraint 相關的 Validation Method

**狀態填入規則：**
- 初次生成時所有 Status 填 `TODO`（測試尚未撰寫）
- 若 EDD 已有測試描述，可填 `IN_PROGRESS`
- 不得假設任何 Test 為 `PASS` 狀態（必須等實際執行後更新）

**Class/Method 佔位符處理：**
- 若 EDD 無 Class Diagram，Class 欄填 `{{ClassName}}（待 EDD §6 補充）`，標記 `[UPSTREAM_CONFLICT]`
- 若 PRD 有 AC 但 EDD 無對應 Method，填入推斷的 Method 名稱並加 `（推斷）` 說明

---

## §4 Integration Test RTM 生成規則

### §4.2 Integration Test 追溯表填入規則

**每個 API Endpoint 至少生成 3 條 IT：**
1. **Success Path（200/201/204）**：合法 Request + 正確 Response
2. **Error Path（401/403/404）**：認證失敗、授權失敗、資源不存在
3. **Boundary（400/422）**：Request Body 驗證失敗（缺少必填欄位、格式錯誤）

**額外必須涵蓋的場景：**
- 若 Endpoint 有 `unique constraint`（如 email 唯一），加一條 409 Conflict 測試
- 若 SCHEMA 有 `content-type` 要求，加一條 415 Unsupported Media Type 測試
- 若 API 有 Pagination，加一條超出範圍頁碼的測試（404 or 空結果）

**API-ID 格式**：`API-001` — 三位數遞增，對應 API.md 的 Endpoint 序號。

---

## §5 E2E Test RTM 生成規則

### §5.2 E2E Test 追溯表填入規則

**每個 P0 Screen Flow 至少生成 3 條 E2E：**
1. **Happy Path**：完整成功流程（主要使用者旅程）
2. **Error Path**：輸入錯誤或操作失敗的流程
3. **Edge Case**：Auth Guard、直接訪問受保護路由、並發操作等邊界場景

**SC-ID 來源：**
- 若 PDD.md 存在且定義了 Screen 清單，使用 PDD 的 SC-ID（格式：`SC-001`）
- 若無 PDD，從 PRD P0 US 推斷畫面並自行編號

**Tool 欄位：**
- 從 test-plan.md 中提取 E2E 工具選型（預設 Playwright）
- 若 test-plan 無 E2E 工具說明，填 `Playwright`（業界預設）

---

## §6 Req-ID ↔ Test-ID 快查索引生成規則

- 遍歷 §3.2、§4.2、§5.2 的所有資料行，按 Req-ID 分組統計
- 每個 Req-ID 的「對應所有 TC/IT/E2E」欄填入完整 ID 列表（逗號分隔）
- 統計欄（總測試數/PASS/FAIL/TODO）從正文計算，不得人工輸入
- 確認 Req-ID 清單與 §0 Document Control 和 §1 Summary 中的數字一致

---

## §7 FAIL 缺陷追蹤快查生成規則

- 初次生成時此表通常為空（所有 TC 狀態為 TODO）
- 若後續更新有 FAIL 項目，從 §3/§4/§5 的 FAIL TC-ID 自動填入此表
- Bug Ticket 欄預設填 `{{TICKET_TRACKER}}/{{TICKET_NUM}}`（格式範例佔位符，允許保留）
- 負責人欄填 `{{ASSIGNED_DEV}}`（格式範例佔位符）

---

## §8 CSV Export 生成規則

- §8.1/§8.2/§8.3 的 CSV 內容必須與 §3.2/§4.2/§5.2 的表格資料完全一致
- CSV 欄位中的中文描述要去除逗號（避免 CSV 格式錯誤），改用空格
- `rtm-{{PROJECT_CODE}}-{{YYYYMMDD}}.csv` 中的 PROJECT_CODE 使用真實 PROJECT_SLUG
- §8.4 Summary Statistics CSV 的數字與 §1 完全一致

---

## 生成前自我檢核清單

- [ ] 所有 PRD P0 User Stories（US-ID）在 §3 Unit Test RTM 中至少有一條 TC
- [ ] 所有 PRD P0 AC 在 §3 或 §4 中至少有一條對應的 Success + Error Test
- [ ] 所有 API.md P0 Endpoint（API-ID）在 §4 Integration Test RTM 中至少有 3 條 IT
- [ ] §5 E2E Test RTM 覆蓋所有 PRD P0 Screen Flow（含 Happy Path + Error Path）
- [ ] §1 統計數字已計算（無裸 `{{...}}` 佔位符）
- [ ] §1 統計數字與正文資料行數完全一致（人工核對）
- [ ] §1 Mermaid Pie Chart 使用真實數字（非佔位符）
- [ ] §3.2 所有 TC-ID 格式正確（`TC-` 前綴 + 三位數字）
- [ ] §4.2 所有 IT-ID 格式正確（`IT-` 前綴 + 三位數字）
- [ ] §5.2 所有 E2E-ID 格式正確（`E2E-` 前綴 + 三位數字）
- [ ] §6 快查索引所有 Req-ID 與 §1 總需求數一致
- [ ] §8 CSV 與 §3/§4/§5 表格資料完全一致
- [ ] 若 `features/` 存在：所有 BDD-server @TC-E2E-* tag 在 §5 E2E RTM 中有對應條目
- [ ] 若 `features/client/` 存在：所有 BDD-client @TC-E2E-* tag 在 §5 E2E RTM 中有對應條目
- [ ] 若 PDD.md 存在：§5 SC-ID 欄位來自 PDD Screen 清單（非自行編號）
- [ ] 無裸 `{{PROJECT_NAME}}`、`{{PROJECT_CODE}}`、`{{DATE}}` placeholder（應已替換）
- [ ] 初次生成：所有 TC 狀態為 `TODO`（無預設 PASS 狀態）
- [ ] 初次生成：§7 FAIL 缺陷表為空或僅含格式範例行
