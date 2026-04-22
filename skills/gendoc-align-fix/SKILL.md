---
name: gendoc-align-fix
description: |
  讀取 docs/ALIGN_REPORT.md（或先執行 align-check），依指定 layer 自動修復對齊問題。
  layer 選項：docs / doc-code / code-test / doc-test / all（預設 all）。
  每個 fix 都 verify 確認後才 commit，修復完輸出 Fix Summary。
  呼叫時機：user 說「修復對齊問題」「fix alignment」或 align-check 執行後。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
  - Skill
---

# gendoc-align-fix — 對齊問題自動修復

讀取 align-check 報告，依 layer 修復所有對齊問題，每條 fix 都 verify 後 commit。

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 1：確定修復範圍

```bash
# _LAYER 從 skill 呼叫方式解析：
# /gendoc-align-fix docs → _LAYER=docs
# /gendoc-align-fix code → _LAYER=code
# /gendoc-align-fix all 或無參數 → _LAYER=all
# [AI: 從使用者的呼叫文字解析 _LAYER 值，預設為 "all"]
_LAYER="all"  # 將被 AI 從呼叫參數覆寫

# 確認 ALIGN_REPORT.md 存在
if [[ ! -f "docs/ALIGN_REPORT.md" ]]; then
  echo "❌ docs/ALIGN_REPORT.md 不存在"
  echo "請先執行 /gendoc-align-check 生成報告後再執行此 skill"
  exit 1
fi
```

### 全上游讀取規則

Align Fix 在修復對齊問題前，必須讀取**被修復文件的所有上游文件**：

```bash
_IDEA="${_IDEA:-$_DOCS/IDEA.md}"
_BRD="${_BRD:-$_DOCS/BRD.md}"
_PRD="${_PRD:-$_DOCS/PRD.md}"
_PDD="${_PDD:-$_DOCS/PDD.md}"
_EDD="${_EDD:-$_DOCS/EDD.md}"
_ARCH="${_ARCH:-$_DOCS/ARCH.md}"
_API="${_API:-$_DOCS/API.md}"
_SCHEMA="${_SCHEMA:-$_DOCS/SCHEMA.md}"
```

修復策略：
1. 先確認衝突的上游優先順序（IDEA > BRD > PRD > PDD > EDD > ARCH > API > SCHEMA）
2. 以優先度最高的上游文件為準修復下游
3. 若修復影響多個下游文件，列出所有受影響文件的修復清單
4. 修復後再次執行 align-check 驗證

---

## Step 2：讀取報告，按 layer + severity 排序

解析規則：ALIGN_REPORT.md 中每個 finding 以 `[SEVERITY]` 開頭的行為問題行，格式為 `[SEVERITY] LAYER: 來源 → 目標`；下方縮排行為描述；`受影響範圍：` 開頭的行為範圍說明。

從 `docs/ALIGN_REPORT.md` 提取問題清單，排序規則：
1. 先按 severity（CRITICAL → HIGH → MEDIUM → LOW）
2. 同 severity 按 layer（docs → doc-code → code-test → doc-test）
3. 若 `_LAYER` 非 all，只保留指定 layer 的問題

---

## Step 3：依 Layer 修復

### Layer: docs — 文件上下游對齊修復

spawn Agent，傳入所有 Doc→Doc 的 findings，修復策略：

---
角色：資深技術文件撰寫者

針對每個 Doc→Doc finding，依衝突類型執行對應修復：

---

#### 衝突類型：缺失（upstream 有，downstream 無）

**PRD 缺少功能（BRD→PRD missing）**
- 在 PRD 的對應功能區段補充 User Story + AC
- AC 必須具體可測（含數字、邊界條件）

**PDD 缺少設計規格（PRD→PDD missing，且 client_type 非 none）**
- 讀取 docs/PRD.md 所有涉及 UI/UX 的 User Story 和 AC
- 在 docs/PDD.md 對應章節補充：Component 規格、互動流程、State 設計
- 確認 PRD 的 P0 AC 都有對應的 UX 設計描述

**EDD 缺少設計（PRD→EDD missing）**
- 在 EDD 的對應章節補充技術設計
- 包含：介面定義、資料流、錯誤處理、效能考量

**API 缺少 endpoint（EDD→API missing）**
- 在 API.md 補充對應 endpoint 定義
- 包含：HTTP method、path、request/response schema、error codes

**SCHEMA 缺少資料表（EDD→SCHEMA missing）**
- 在 SCHEMA.md 補充 ER 圖更新、表說明、CREATE TABLE SQL

**BDD 缺少 Scenario（PRD→BDD missing）**
- 在對應的 features/*.feature 補充 Gherkin Scenario
- 每個 AC 至少：正常路徑 + 錯誤路徑各一個 Scenario

---

#### 衝突類型：B1-下游合理（下游實作比上游定義更合理）

> 下游（EDD/API/src/）對某行為的設計比上游（BRD/PRD）的描述更合理，
> 上游文件需要「補簽名」授權下游的設計決策。

**修復原則：更新上游文件，授權下游設計**

- 找到上游文件（BRD/PRD）中描述該行為的對應段落
- 將段落更新為下游實際設計的描述（保留上游意圖，修正執行方式描述）
- 在更新段落末尾加上標記：
  `> 設計決策（align-fix 授權）：原描述為「X」，基於「Y 理由」更新為「Z」，與 EDD/src/ 實作對齊。`
- **不修改下游**（下游設計本身是對的）
- 若改動了 BRD，同步確認 PRD/PDD/EDD/API 的相關描述也一致

範例：
- BRD §6.2 說「Server 自動切換到揭示階段」
- EDD/程式碼實作「Host 主動觸發揭示」
- B1 修復：更新 BRD §6.2 為「Host 主動觸發揭示，Server 執行原子狀態轉換」，附上決策標記

---

#### 衝突類型：B2-下游偏離（下游偏離上游授權範圍）

> 下游（EDD/API/src/）引入了上游沒有授權、且無明顯好處的設計改動。

**修復原則：修正下游對齊上游**

- 找到下游文件/程式碼中偏離的部分
- 將下游修正為符合上游定義的行為
- commit 說明為何這是偏離而非改進

---

#### 衝突類型：B-待確認（兩種設計各有嚴重取捨）

> 極少數情況：AI 無法判斷哪個方向正確，兩種設計對產品策略有根本影響。

- 在 `docs/ALIGN_REPORT.md` 對應 finding 加入詳細比較說明：
  ```
  [MANUAL: B-待確認]
  方案 A（上游設計）：<具體描述> 優點：<> 缺點：<>
  方案 B（下游設計）：<具體描述> 優點：<> 缺點：<>
  建議：<AI 傾向哪個，及理由>
  ```
- 不修改任何文件或程式碼，等待人工確認

---

每個修復後：
- verify subagent 重新審查該 finding 是否已解決
- 確認解決後 commit：`docs(gendoc)[align-fix]: docs — <描述>`
---

---

### Layer: doc-code — 文件↔程式碼對齊修復

spawn Agent，傳入所有 Doc→Code 的 findings：

---
角色：資深工程師（實作補充者）

針對每個 Doc→Code finding：

**API endpoint 未實作（API→src missing）**
- 在 src/ 對應位置新增 route + handler skeleton
- handler 實作必須符合 API.md 的 request/response schema
- 不能是 mock（return hard-coded data）
- 加上基本的 input validation

**ORM model 缺少（SCHEMA→src missing）**
- 在 src/models/ 新增對應的 model 定義
- 欄位型別、nullable、default 與 SCHEMA.md 一致
- 若用 migration 框架（alembic/flyway），同時生成 migration 檔

**src/ 有但 API.md 未記錄的 endpoint（gold-plating）**

Gold-plating 是唯一允許標 MANUAL 的情況，但必須先評估：

步驟 1：評估合理性
- 讀取該 endpoint/module 的實作邏輯，判斷是否為「合理且有意為之」的功能
- 合理性判斷標準：有正確的 input validation、error handling、業務邏輯（非空骨架、非 dead code）

步驟 2a：若合理（看起來是刻意實作的功能）
- **不刪除程式碼**
- 在 API.md 對應位置補充 endpoint 文件（確保文件化）
- 同時在 `docs/ALIGN_REPORT.md` 對應 finding 行加入：
  `[MANUAL: gold-plating — 合理實作，已補文件，請使用者完成流程後評估是否納入正式需求]`
- 若 API.md 補充後，下游 BDD/tests 也缺，依上下游原則一路補齊

步驟 2b：若不合理（空骨架、dead code、測試痕跡、無業務意義）
- **不自動刪除**
- 標記：`[MANUAL: gold-plating — 疑似 dead code，建議刪除，請人工確認]`
- 在程式碼中加上 `# TODO(align-fix): gold-plating — 疑似 dead code，人工確認後可刪除` 注釋

**目錄結構不符 EDD 分層**
- 若 src/ 缺少某個 layer 的目錄，建立並補充 __init__.py / index.ts 等入口

每個修復後：verify → commit：`feat(gendoc)[align-fix]: doc-code — <描述>`
---

---

### Layer: code-test — 程式碼↔測試對齊修復

spawn Agent，傳入所有 Code→Test 的 findings：

---
角色：QA 工程師（測試補充者）

針對每個 Code→Test finding：

**缺少 unit test**
- 在 tests/unit/ 對應位置新增 test file
- 每個 public function 至少：
  - 正常輸入的成功路徑測試
  - 邊界條件測試（空值、最大值、null）
  - 錯誤路徑測試（期待的 exception）
- 遵守 Anti-Fake 原則：斷言必須因錯誤實作而 FAIL

**缺少 integration test**
- 在 tests/integration/ 新增對應的 integration test
- 使用 testcontainers 或真實依賴，不能 mock 外部 I/O

**測試存在但 src/ 無對應實作（TDD RED 狀態）**
- **補 src/ 實作**，使測試通過（TDD GREEN phase）
- 遵守 EDD 架構分層，不可把邏輯塞進 test file
- 禁止刪測試——測試是上游文件

**孤兒測試（src/ 整個 module 已被刪除，測試所指向的功能已廢棄）**
- 確認 src/ 對應 module 確實不存在且非 TDD 預寫測試
- 才可刪除對應的 orphan test file，commit 說明原因

每個修復後：verify（執行測試確認 PASS）→ commit：`test(gendoc)[align-fix]: code-test — <描述>`
---

---

### Layer: doc-test — 文件↔測試對齊修復

spawn Agent，傳入所有 Doc→Test 的 findings：

---
角色：BA + QA（需求測試橋接修復者）

針對每個 Doc→Test finding：

**PRD AC 無 BDD Scenario**
- 在 features/ 補充 Gherkin Scenario（正常 + 錯誤 + 邊界）

**BDD Scenario 無 step definition**
- 在對應的 step definition 檔補充實作
- step definition 呼叫實際業務邏輯，不能直接 return True

**BDD Scenario 無 test 或 test 未通過**
- 補充 test case 或修復失敗的 test
- 若 BDD Scenario 本身有邏輯錯誤，修正 Scenario

每個修復後：執行相關測試確認 PASS → commit：`test(gendoc)[align-fix]: doc-test — <描述>`
---

---

## Step 3b：更新 ALIGN_REPORT.md 修復狀態

在所有 finding 修復確認後，在 `docs/ALIGN_REPORT.md` 對應 finding 行的末尾加入修復狀態標記：
- 已修復：`[FIXED: <commit_hash>]`
- STUBBORN（5 輪未解）：`[STUBBORN: 5 rounds]`
- 需人工確認：`[MANUAL: <原因>]`

這樣 `/gendoc-align-check` 在讀取 ALIGN_REPORT.md 時能取得最新修復狀態，並在 HTML 儀表板中顯示正確的修復進度。

---

## Step 4：Fix Summary 輸出

```
╔══════════════════════════════════════════════════════════════╗
║           gendoc — 對齊修復摘要                               ║
╠══════════════════════════════════════════════════════════════╣
║  修復 Layer：<_LAYER>                                        ║
║  修復前問題總數：21（CRITICAL:3 HIGH:10 MEDIUM:6 LOW:2）      ║
║  已修復：18                                                   ║
║  STUBBORN（5 輪未解）：2                                      ║
║  跳過（需人工決定）：1                                        ║
╠══════════════════════════════════════════════════════════════╣
║  修復明細：                                                   ║
║    ✅ [CRITICAL] API→src: GET /api/v1/reports/export 已補實作 ║
║    ✅ [HIGH] PRD→EDD: AC-07 匯出功能 EDD 設計已補充          ║
║    🔁 [STUBBORN] Code→Test: ReportService.stream() 測試複雜  ║
║    ⚠️  [人工] src 有 /internal/debug endpoint，請確認是否保留 ║
╠══════════════════════════════════════════════════════════════╣
║  Commits（時序）：                                            ║
║    abc1234  docs(gendoc)[align-fix]: docs — PRD AC-07 補充   ║
║    def5678  feat(gendoc)[align-fix]: doc-code — export 實作  ║
║    ...                                                        ║
╠══════════════════════════════════════════════════════════════╣
║  建議後續：/gendoc-align-check  驗證剩餘問題                 ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 修復原則

### 上下游強制對齊原則（最高優先，所有 Layer 適用，不可繞過）

整個 gendoc pipeline 有嚴格的上下游依賴鏈：

```
BRD（最上游）
 └─► PRD（User Story + AC）
      └─► EDD（技術設計）
           ├─► ARCH（架構設計）
           ├─► API.md（接口定義）
           └─► SCHEMA.md（資料設計）
                └─► BDD features/（驗收場景）
                     └─► step definitions（場景實作）
                          └─► src/ 實作程式碼
                               └─► tests/unit/ + tests/integration/（測試）
```

**上游存在 = 下游必須覆蓋**。任何層的 upstream→downstream 缺失，**必須自動補齊**，無例外。

唯一合法跳過條件：該功能明確出現在 **BRD `## Out of Scope`** 章節。

#### 所有層的強制修復範例

| 發現問題 | 正確動作 | 禁止動作 |
|---------|---------|---------|
| BRD 有功能，PRD 沒寫 | 在 PRD 補 User Story + AC | ❌ 標 MANUAL「產品決策」|
| PRD 有 AC，EDD 無技術設計 | 在 EDD 補對應章節 | ❌ 標 MANUAL「需確認」|
| EDD 有介面，API.md 無 endpoint | 在 API.md 補 endpoint | ❌ 標 MANUAL「架構爭議」|
| EDD 有資料實體，SCHEMA.md 缺表 | 在 SCHEMA.md 補 CREATE TABLE | ❌ 標 MANUAL |
| PRD AC 無 BDD Scenario | 在 features/ 補 Gherkin Scenario | ❌ 標 MANUAL |
| BDD Scenario 無 step definition | 補 step definition（呼叫真實業務邏輯） | ❌ 標 MANUAL |
| BDD/test plan 存在，src/ 無實作 | 補 src/ 實作（TDD GREEN phase） | ❌ 刪測試（測試是上游！）|
| src/ public function 無 unit test | 在 tests/unit/ 補 test case | ❌ 標 MANUAL |

| BRD 說 X，EDD 實作 Y（B1：Y 更合理）| 更新 BRD 授權 Y（上游補簽名）| ❌ 標 MANUAL「產品決策」|
| BRD 說 X，EDD 實作 Y（B2：Y 無根據）| 修 EDD 對齊 BRD | ❌ 標 MANUAL「架構爭議」|

**禁止以下理由跳過任何 upstream↔downstream 問題：**
- ❌「這是產品決策」
- ❌「需要人工確認」
- ❌「不確定要不要實作」
- ❌「架構爭議」
- ❌「上下游說法不一致，留給使用者決定」

> B1/B2 的判斷是 AI 的責任，不得推給使用者。只有兩種設計對商業策略有根本分歧、AI 完全無法判斷時，才可標 `B-待確認` 並附詳細比較。
>
> **特別注意**：`test 存在但 src/ 無實作` = TDD RED 狀態，測試是上游文件，**補實作而非刪測試**。

---

### 唯一允許標 MANUAL 的情況

僅 **gold-plating**（src/ 有程式碼，但 API.md / doc 完全沒有對應定義）才標 MANUAL。
處理流程：

1. **先評估合理性**（讀程式碼邏輯，非讀文件）
2. **合理實作** → 補 API.md 文件 + 標 `[MANUAL: gold-plating — 合理實作，已補文件，請評估是否納入正式需求]`
   - 下游若有缺（BDD/tests），依上下游原則一路補齊
3. **疑似 dead code** → 加 TODO 注釋 + 標 `[MANUAL: gold-plating — 疑似 dead code，建議刪除，請人工確認]`
   - 絕不自動刪除程式碼

---

### 其他修復原則

- 補充程式碼時遵守現有 lang_stack 和 EDD 架構規範
- 補充測試時遵守 Anti-Fake 原則（斷言必須因錯誤實作而 FAIL）
- 每個 fix 都先 verify 確認問題消除，再 commit
- STUBBORN 定義：同一個 finding 5 輪修復嘗試後仍未解決
