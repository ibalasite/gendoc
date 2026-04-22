---
name: gendoc-flow
description: 純文件生成流水線（BRD已備妥後接手）— PRD→PDD→EDD→ARCH→API→SCHEMA→Test Plan→RTM→BDD→一致性審查→HTML Pages→GitHub Pages。每份文件有 Generation Agent + Review Loop。不含程式碼實作、K8s、CI/CD。由 gendoc-auto 或手動呼叫觸發。
version: 1.2.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - Skill
  - AskUserQuestion
  - TaskCreate
  - TaskUpdate
  - TaskGet
  - TaskList
---

# gendoc-flow — 純文件生成流水線（Agent-per-DOC + Review Loop）

```
Input:   docs/IDEA.md + docs/BRD.md + docs/req/*（由 gendoc-auto 或手動備妥）
Output:  docs/PRD.md → PDD → EDD → ARCH → API → SCHEMA
         → test-plan + RTM + BDD → CONSISTENCY-REPORT
         → docs/pages/ HTML → GitHub Pages
Scope:   純文件，不含程式碼實作、K8s、CI/CD、Deploy
```

每個 DOC step 由主 Claude 協調：
- Phase A：spawn Generator Agent → 寫入文件 → git commit
- Phase B：主 Claude 呼叫 `_review_loop()` → 多輪 Reviewer Agent → 修復 → git commit/round

---

## Iron Law

> **鐵律（不可違反）：每份文件生成前，必須讀取所有上游文件（累積鏈，非僅直接父文件）。**
> docs/req/* 素材全部關聯讀取。若上游不存在，靜默跳過；不得因此降低覆蓋深度。
> 違反此鐵律的生成結果視為無效，必須重新生成。

---

## Step -1：版本自動更新檢查 + SPAWNED_SESSION 偵測

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

```bash
# SPAWNED_SESSION 偵測（由 gendoc-auto 觸發時通常為 spawned）
[ -n "$OPENCLAW_SESSION" ] && _SPAWNED="true" || _SPAWNED="false"
echo "SPAWNED_SESSION: $_SPAWNED"
# spawned session 強制 full-auto，跳過所有 AskUserQuestion
[[ "$_SPAWNED" == "true" ]] && echo "[SPAWNED] 強制 full-auto，跳過互動提問"
```

---

## §STEP-MAPPING — autodev↔autogen 步驟對照表（A-06）

> 讓 `start_step`（autodev 31 步格式）可跨 autogen 共用。autogen 讀取 state 的 `start_step` 後，透過此表翻譯為 autogen DOC 步驟。

| autodev STEP | 說明 | autogen DOC STEP |
|-------------|------|-----------------|
| STEP-01 | Workspace + State | 無（前置，略過）|
| STEP-02 | PM Expert / Project Init | 無（前置，略過）|
| STEP-03 | BRD | BRD（前置文件，由 gendoc/idea 提供）|
| STEP-04 | PRD | `DOC-03` |
| STEP-05 | PDD | `DOC-04` |
| STEP-06 | EDD | `DOC-05` |
| STEP-07 | SDD/ARCH | `DOC-06` |
| STEP-08 | API Design | `DOC-07` |
| STEP-09 | Schema | `DOC-08` |
| STEP-10 | Test Plan | `DOC-09` |
| STEP-11 | BDD Features | `DOC-10` |
| STEP-12 | RTM | `DOC-09`（RTM 整合在 Test Plan 步驟）|
| STEP-11.5 | Runbook + LOCAL_DEPLOY | `DOC-10-D`（BDD 之後，align-check 之前）|
| STEP-13+ | Code / Deploy / Test | 不在 autogen 範圍 → 使用最後一個 autogen DOC |

**翻譯邏輯**：若 `start_step` ≤ 3（前置步驟），從 DOC-03（PRD）開始。若 `start_step` ≥ 13（Code 以後），從最後一個文件步驟 DOC-12 開始（或直接報告已完成）。

```bash
# start_step → autogen DOC 步驟翻譯
_AUTODEV_STEP=$(python3 -c "
import json
try: s=int(json.load(open('${_STATE_FILE}')).get('start_step',4))
except: s=4
# 對照表：autodev STEP → autogen DOC number (3=PRD=03, 4=PDD=04...)
mapping={3:3,4:3,5:4,6:5,7:6,8:7,9:8,10:9,11:10,12:9}
# STEP-01/02 or <=3 → start from DOC-03; >=13 → start from DOC-12
if s<=3: print(3)
elif s>=13: print(12)
else: print(mapping.get(s,3))
" 2>/dev/null || echo "3")
echo "[STEP-MAPPING] start_step=${_START_STEP} → autogen DOC-0${_AUTODEV_STEP}"
```

---

## Step 0：Session Config（遵循 gendoc-shared §0）

```bash
# 動態偵測 state file
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")

_EXEC_MODE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('execution_mode',''))
except: print('')
" 2>/dev/null || echo "")

_REVIEW_STRATEGY=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('review_strategy','standard'))
except: print('standard')
" 2>/dev/null || echo "standard")

# review_strategy → max_rounds（遵循 gendoc-shared §14）
case "$_REVIEW_STRATEGY" in
  rapid)      _LOOP_COUNT=1 ;;
  standard)   _LOOP_COUNT=2 ;;
  thorough)   _LOOP_COUNT=3 ;;
  exhaustive) _LOOP_COUNT=5 ;;
  *)          _LOOP_COUNT=2 ;;
esac
```

**已有值**：`echo "[Session Config] 沿用已設定 — 模式：${_EXEC_MODE} ／ Review 策略：${_REVIEW_STRATEGY}（${_LOOP_COUNT} 輪）"` → 繼續。

**無值**：顯示 §0 標準選單（execution_mode + review_strategy），寫入 state。

---

## Step 0-B：起始步驟（TF-02 狀態機 + §STEP-MAPPING）

```bash
# 讀取 start_step（由 gendoc-auto/idea 寫入，格式為 autodev 31 步編號）
_START_STEP=$(python3 -c "
import json
try: print(int(json.load(open('${_STATE_FILE}')).get('start_step', 4)))
except: print(4)
" 2>/dev/null || echo "4")

# 讀取已完成步驟（TF-02 斷點續行）
_COMPLETED=$(python3 -c "
import json
try: print(','.join(json.load(open('${_STATE_FILE}')).get('completed_steps',[])))
except: print('')
" 2>/dev/null || echo "")

echo "[Start] start_step=${_START_STEP}，completed_steps=[${_COMPLETED}]"
```

**`_EXEC_MODE=full-auto`**：依 `completed_steps` 自動跳過已完成步驟，從 `start_step` 對應的 DOC 繼續。
**`_EXEC_MODE=interactive`**：先顯示已完成步驟，詢問是否從建議步驟繼續或指定步驟。

---

## Step 0-D：確認前置文件存在 + Handoff State 讀取（D-02）

```bash
# 讀取 Handoff State（D-02）
_HANDOFF_SOURCE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('handoff_source',''))
except: print('')
" 2>/dev/null || echo "")

_BRD_REVIEW_PASSED=$(python3 -c "
import json
try: print(str(json.load(open('${_STATE_FILE}')).get('brd_review_passed',False)).lower())
except: print('false')
" 2>/dev/null || echo "false")

_IDEA_REVIEW_PASSED=$(python3 -c "
import json
try: print(str(json.load(open('${_STATE_FILE}')).get('idea_review_passed',False)).lower())
except: print('false')
" 2>/dev/null || echo "false")

echo "[Handoff] 來源：${_HANDOFF_SOURCE:-手動} ／ BRD 已 Review：${_BRD_REVIEW_PASSED} ／ IDEA 已 Review：${_IDEA_REVIEW_PASSED}"

_BRD_OK=false
_IDEA_OK=false
[[ -s "$(pwd)/docs/BRD.md"  ]] && _BRD_OK=true
[[ -s "$(pwd)/docs/IDEA.md" ]] && _IDEA_OK=true

echo "[Check] BRD：${_BRD_OK} ／ IDEA：${_IDEA_OK}"

if [[ "$_BRD_OK" == "false" ]]; then
  echo "[錯誤] docs/BRD.md 不存在或為空。"
  echo "       請先執行 /gendoc-auto 或手動建立 BRD。"
  exit 1
fi

# brd_review_passed=true → BRD 已通過完整 Review Loop，可信任直接使用
[[ "$_BRD_REVIEW_PASSED" == "true" ]] && echo "[Check] BRD 已通過 Review Loop（${_HANDOFF_SOURCE}），直接使用"
# idea_review_passed=true → IDEA.md 已通過完整 Review Loop
[[ "$_IDEA_REVIEW_PASSED" == "true" ]] && echo "[Check] IDEA.md 已通過 Review Loop（${_HANDOFF_SOURCE}），直接使用"
```

---

## 共用函式：_review_loop()

⚠️ 這是「主 Claude 執行規則」，不是 Bash 函式。
主 Claude 預先建立所有 Round 的 Task，強制執行每一輪，不可跳過。

### 函式簽名

```
_review_loop(
  doc_id        = "03",              # DOC 編號
  document_path = "docs/PRD.md",    # 審查目標文件
  strategy      = _REVIEW_STRATEGY, # rapid/standard/exhaustive/tiered/custom
  reviewer_role = "資深 UX Expert",  # 審查角色
  dimensions    = [...]              # 審查面向清單
)
```

### Phase 1：依策略決定最大輪次，預建所有 Round Task

策略 → 最大輪次：
- rapid: 2 輪
- standard: 3 輪（預設）
- exhaustive: 99 輪（視為無上限）
- tiered: 前 3 輪 strict，第 4 輪起 lenient（合計預建 99）
- custom: 依使用者輸入

```
max_rounds = 依策略決定（_LOOP_COUNT 可覆蓋）
round_task_ids = []

for N in 1..max_rounds:
  tid = TaskCreate({
    subject: "DOC-{doc_id} Review Round {N}/{max_rounds}",
    description: "status=pending",
    metadata: { doc_id: "{doc_id}", round: N, max_rounds: max_rounds, findings_total: -1 }
  })
  round_task_ids.append(tid)

輸出：📋 已建立 {max_rounds} 個 Review Round Task（DOC-{doc_id}）
```

### Phase 2：按順序執行每個 Round Task

```
for (N, tid) in enumerate(round_task_ids, start=1):

  TaskUpdate(tid, status: "in_progress")
  輸出：── DOC-{doc_id} Review Round {N}/{max_rounds} 開始 ──

  # spawn Reviewer Agent
  spawn Agent（角色：{reviewer_role}）：
    讀取 {document_path}，依以下審查面向找出所有問題：
    {dimensions 逐項列出}
    輸出規則（強制）：
    輸出最後一行必須完全匹配以下格式之一：
    有問題：REVIEW_JSON: {"round":N,"doc":"{doc_id}","findings":[{"id":"F1","sev":"CRITICAL|HIGH|MEDIUM|LOW","title":"...","fix":"..."}],"total":N}
    無問題：REVIEW_JSON: {"round":N,"doc":"{doc_id}","findings":[],"total":0}

  # 解析 REVIEW_JSON
  findings_total = JSON.total
  findings_list  = JSON.findings
  TaskUpdate(tid, metadata: { findings_total: findings_total })

  # 判斷終止條件
  若 findings_total == 0：
    TaskUpdate(tid, status: "completed", description: "finding=0，提前結束")
    刪除後續 pending Round Task
    → 進入 Phase 3

  # 有 findings → spawn Fixer Agent
  spawn Agent（角色：修復工程師）：
    接收 finding 清單：{findings_list}
    對每個 finding 逐一處理（無例外）：
      可修復 → 直接修復文件（不留 TODO/FIXME）
      不合理 → 在文件中標記：
        <!-- TODO[REVIEW-DEFERRED]:
          Finding: <原始 finding>
          Severity: <sev>
          Cannot-fix reason: <具體原因>
          Source: DOC-{doc_id} Review Round {N}
        -->
    輸出最後一行：
    FIX_COMPLETE: {"round":N,"doc":"{doc_id}","fixed":M,"todo":K,"remaining":0}

  # git commit（每輪）
  Bash:
    git add {document_path}
    git commit -m "review(devsop)[DOC-{doc_id}]: Round {N} — {findings_total} findings fixed"

  # Per-Round Summary
  ╔══ DOC-{doc_id} Review Round {N}/{max_rounds} ══╗
  ║ Findings：{findings_total} 個
  ║ {逐項列出：[{sev}] {title} → {fix}}
  ║ Fix 結果：fixed={fixed} todo={todo}
  ║ Commit: {git rev-parse --short HEAD}
  ╚══════════════════════════════════════════════════╝

  TaskUpdate(tid, status: "completed", description: "finding={findings_total} fixed={fixed}")
```

### Phase 3：Total Summary

```
收集所有 Round Task metadata.findings_total

╔══ DOC-{doc_id} Review Loop 完成 ══╗
║ 策略：{strategy}  共 {實際輪次} 輪
║ Finding 趨勢：Round 1: N個 / Round 2: M個 / ...
║ 最終狀態：{最後一輪 finding 數} 個問題
║ 總 Commit 數：{實際輪次}
╚══════════════════════════════════╝
```

---

## DOC-03：PRD（產品需求文件）

**Skip 條件**：`_START_STEP > 3` 或（full-auto 且 `docs/PRD.md` 非空）

### DOC-03-A：生成 PRD（D-03）

透過 **Skill tool** 呼叫 `gendoc`，args: `prd`（gen 規則由 templates/PRD.gen.md 定義）。

gen-prd 完成後：

```bash
git add docs/PRD.md
git commit -m "docs(devsop)[DOC-03]: gen — PRD 初稿生成"
```

### DOC-03-B：PRD Review Loop

主 Claude 呼叫 `_review_loop()`：

```
_review_loop(
  doc_id        = "03",
  document_path = "docs/PRD.md",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 UX Expert（PRD 審查者）",
  dimensions    = [
    "BRD 一致性：PRD 目標是否忠實反映 BRD，無遺漏或衝突",
    "Personas 具體度：每個 Persona 有明確痛點與使用情境，非虛構空泛",
    "US 格式正確性：格式為「作為 <角色>，我希望 <功能>，以便 <價值>」",
    "AC 可測試性：每條 AC 可量化驗收，無模糊用語（如「方便」「更好」）",
    "Journey 覆蓋度：Happy Path + Error Path + Boundary 全覆蓋",
    "MoSCoW 合理性：Must Have 是否確實是核心功能，非 Nice to Have 混入",
  ]
)
```

---

## DOC-04：PDD（產品設計文件）

**Skip 條件**：`_START_STEP > 4` 或（full-auto 且 `docs/PDD.md` 非空）

### DOC-04-A：生成 PDD（D-03）

透過 **Skill tool** 呼叫 `gendoc`，args: `pdd`（gen 規則由 templates/PDD.gen.md 定義）。

gen-pdd 完成後：

```bash
git add docs/PDD.md
git commit -m "docs(devsop)[DOC-04]: gen — PDD 初稿生成"
```

### DOC-04-B：PDD Review Loop

```
_review_loop(
  doc_id        = "04",
  document_path = "docs/PDD.md",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 PM Expert（PDD 審查者）",
  dimensions    = [
    "PRD 一致性：每個 PRD Feature 都有對應 IA 節點",
    "IA 完整性：資訊架構圖層次清晰，導覽路徑無孤立節點",
    "Component 定義完整：每個元件有 State/Props/行為說明",
    "Client Class Diagram 正確性：類別關係符合前端架構",
    "WCAG 2.1 AA 合規：Checklist 全部檢視，無跳過項目",
    "Design Token 完整性：Color/Typography/Spacing/Shadow 全覆蓋",
  ]
)
```

---

## DOC-05：EDD（工程設計文件）

**Skip 條件**：`_START_STEP > 5` 或（full-auto 且 `docs/EDD.md` 非空）

### DOC-05-A：生成 EDD（D-03）

透過 **Skill tool** 呼叫 `gendoc`，args: `edd`（gen 規則由 templates/EDD.gen.md 定義）。

gen-edd 完成後：

```bash
_CLASS_COUNT=$(grep -c "^[[:space:]]*class " "$(pwd)/docs/EDD.md" 2>/dev/null || echo 0)
python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['class_count']=${_CLASS_COUNT}; d['uml_diagrams_generated']=9
json.dump(d,open(f,'w'),ensure_ascii=False,indent=2)
"
echo "[DOC-05] class_count=${_CLASS_COUNT}, UML 9大圖已生成"

git add docs/EDD.md docs/diagrams/ 2>/dev/null; true
git add docs/EDD.md 2>/dev/null
git commit -m "docs(devsop)[DOC-05]: gen — EDD 初稿，UML 9大圖，class_count=${_CLASS_COUNT}"
```

### DOC-05-B：EDD Review Loop

```
_review_loop(
  doc_id        = "05",
  document_path = "docs/EDD.md",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 Backend Expert（EDD 審查者）",
  dimensions    = [
    "Clean Architecture 合規：4 層分離（Domain/App/Infra/Interface），無跨層直接依賴",
    "UML 9大圖完整性：9 張圖全部存在，Mermaid 語法正確",
    "Class Diagram 正確性：Design Pattern 標記清楚，關係箭頭正確（繼承/聚合/組合）",
    "Sequence Diagram 覆蓋：至少 3 個主流程，含 Error Path",
    "API 可實作性：每個 API endpoint 在 EDD 中有對應設計",
    "安全設計：OWASP Top 10 已考量，Auth/Authz 設計明確",
    "部署圖合理性：Deployment Diagram 反映實際部署拓撲",
  ]
)
```

---

## DOC-06：ARCH（架構圖說明）

**Skip 條件**：`_START_STEP > 6` 或（full-auto 且 `docs/ARCH.md` 非空）

### DOC-06-A：生成 ARCH（D-03）

透過 **Skill tool** 呼叫 `gendoc`，args: `arch`（gen 規則由 templates/ARCH.gen.md 定義）。

gen-arch 完成後：

```bash
git add docs/ARCH.md docs/diagrams/puml/ 2>/dev/null; true
git add docs/ARCH.md 2>/dev/null
git commit -m "docs(devsop)[DOC-06]: gen — ARCH 初稿，C4 架構圖 + .puml 檔案"
```

### DOC-06-B：ARCH Review Loop

```
_review_loop(
  doc_id        = "06",
  document_path = "docs/ARCH.md",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 Domain Expert（ARCH 審查者）",
  dimensions    = [
    "C4 Level 完整性：Level 1（System Context）+ Level 2（Container）均存在",
    "EDD 一致性：ARCH 中的元件與 EDD Class/Component Diagram 一致",
    "Infrastructure Topology：實際部署元件（DB/Cache/Queue/CDN）全部呈現",
    "Data Flow 正確性：資料流向清晰，無循環依賴",
    "Security Architecture：認證、加密、邊界保護設計完整",
    "PlantUML 檔案：每個 .puml 檔語法正確，與 Mermaid 版本一致",
  ]
)
```

---

## DOC-06.5：Mermaid 圖表統一抽取

**Skip 條件**：full-auto 且 `docs/diagrams/` 已有 ≥ 6 個 .md 檔

透過 **Skill tool** 呼叫 `gendoc-gen-diagrams`（圖表結構由 gen-diagrams 定義，不在此 inline）。

gen-diagrams 完成後：

```bash
_DIAG_COUNT=$(ls "$(pwd)/docs/diagrams/"*.md 2>/dev/null | wc -l | tr -d ' ')
echo "[DOC-06.5] 已生成 ${_DIAG_COUNT} 個圖表到 docs/diagrams/"

git add docs/diagrams/
git commit -m "docs(devsop)[DOC-06.5]: diagrams — 統一抽取 ${_DIAG_COUNT} 個 Mermaid 圖表至 docs/diagrams/"
```

---

## DOC-07：API Design

**Skip 條件**：`_START_STEP > 7` 或（full-auto 且 `docs/API.md` 非空）

### DOC-07-A：生成 API Design（D-03）

透過 **Skill tool** 呼叫 `gendoc`，args: `api`（gen 規則由 templates/API.gen.md 定義）。

gen-api 完成後：

```bash
git add docs/API.md
git commit -m "docs(devsop)[DOC-07]: gen — API Design 初稿生成"
```

### DOC-07-B：API Design Review Loop

```
_review_loop(
  doc_id        = "07",
  document_path = "docs/API.md",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 QA Expert（API 審查者）",
  dimensions    = [
    "EDD 一致性：每個 EDD 中的 API 都有對應 endpoint",
    "Endpoint 可測試性：method/path/request/response 完整，curl 範例可直接執行",
    "Error Codes 完整性：4xx/5xx 錯誤碼有明確說明，不使用通用 500",
    "Schema 清晰度：request/response 欄位有類型/必填/說明",
    "Auth 設計正確：每個 endpoint 的 Auth 需求明確標示",
    "Rate Limiting 合理：限流規則有業務依據",
    "Versioning 策略：API 版本控制方式明確",
  ]
)
```

---

## DOC-08：DB Schema

**Skip 條件**：`_START_STEP > 8` 或（full-auto 且 `docs/SCHEMA.md` 非空）

### DOC-08-A：生成 DB Schema（D-03）

透過 **Skill tool** 呼叫 `gendoc`，args: `schema`（gen 規則由 templates/SCHEMA.gen.md 定義）。

gen-schema 完成後：

```bash
git add docs/SCHEMA.md
git commit -m "docs(devsop)[DOC-08]: gen — DB Schema 初稿生成"
```

### DOC-08-B：DB Schema Review Loop

```
_review_loop(
  doc_id        = "08",
  document_path = "docs/SCHEMA.md",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 System Architect（Schema 審查者）",
  dimensions    = [
    "ERD 完整性：所有 EDD 實體都有對應 Table，FK 關係正確",
    "正規化設計：至少 3NF，重複資料已消除，或有明確非正規化理由",
    "索引策略合理性：查詢頻繁欄位有索引，複合索引設計正確",
    "約束完整性：NOT NULL/UNIQUE/CHECK 約束符合業務規則",
    "Migration Plan 可執行：遷移步驟有序，無不可逆操作",
    "效能考量：大表分區策略、軟刪除設計、審計欄位",
  ]
)
```

---

## DOC-09：Test Plan + RTM

**Skip 條件**：`_START_STEP > 9` 或（full-auto 且 `docs/test-plan.md` 非空）

```bash
_CLASS_COUNT=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('class_count',0))
except: print(0)
" 2>/dev/null || echo 0)

# 取得 lang_stack（若未設定則詢問或從 BRD 推斷）
_LANG_STACK=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('lang_stack',''))
except: print('')
" 2>/dev/null || echo "")

if [[ -z "$_LANG_STACK" ]]; then
  if [[ "$_EXEC_MODE" == "interactive" ]]; then
    # AskUserQuestion: 請選擇技術語言（用於測試工具選型）
    # [1] Python  [2] Node.js  [3] Go  [4] Java  [5] 其他
    echo "[DOC-09] 互動模式：請告知 lang_stack（將透過 AskUserQuestion 詢問）"
  else
    # full-auto：從 BRD/EDD 關鍵字推斷
    _LANG_STACK=$(python3 -c "
import re, os
content = ''
for f in ['docs/BRD.md','docs/EDD.md']:
    try: content += open(f).read()
    except: pass
content = content.lower()
if any(k in content for k in ['python','django','fastapi','flask','pytest']): print('python')
elif any(k in content for k in ['node','express','nestjs','next.js','jest']): print('nodejs')
elif any(k in content for k in [' go ','golang','gin ','echo ','fiber ']): print('go')
elif any(k in content for k in ['java','spring','springboot','maven','gradle']): print('java')
else: print('nodejs')
" 2>/dev/null || echo "nodejs")
    echo "[Full-Auto] lang_stack 推斷：${_LANG_STACK}"
    python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['lang_stack']='${_LANG_STACK}'
json.dump(d,open(f,'w'),ensure_ascii=False,indent=2)
"
  fi
fi

echo "[DOC-09] lang_stack=${_LANG_STACK} | class_count=${_CLASS_COUNT}"
```

### DOC-09-A：生成 Test Plan + RTM（D-03）

透過 **Skill tool** 呼叫 `gendoc`，args: `test-plan`（gen 規則由 templates/test-plan.gen.md 定義）。

gen-test-plan 完成後（同時輸出 test-plan.md、RTM.md、RTM.csv）：

```bash
git add docs/test-plan.md docs/RTM.md docs/RTM.csv 2>/dev/null
git commit -m "docs(devsop)[DOC-09]: gen — Test Plan（18章節）+ RTM 初稿，lang=${_LANG_STACK} class=${_CLASS_COUNT}"
```

### DOC-09-B：Test Plan + RTM Review Loop

```
_review_loop(
  doc_id        = "09",
  document_path = "docs/RTM.md",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 Domain Expert（RTM 審查者）",
  dimensions    = [
    "1:1 覆蓋：每個 EDD Class 是否有對應測試檔案（1 class = 1 test file）",
    "TC-ID 命名規範：格式 TC-{TYPE}-{MODULE}-{SEQ}-{CASE} 嚴格遵守",
    "三類情境覆蓋：Unit 含 Success/Error/Boundary；Integration 含 200/400/401/404",
    "RTM 完整性：PRD 每個 US 有 TC 覆蓋，無遺漏",
    "RTM.csv 格式正確：可匯入工具，8 欄位對齊 RTM.md 內容",
    "Test Plan 18 章節：每章節非空，SLO 數字具體，OWASP A01-A10 全覆蓋",
    "lang_stack 工具選型：§3 工具與 lang_stack 一致，非通用描述",
    "E2E 測試計劃：關鍵用戶旅程有 E2E TC，且與 BDD Scenario 對應",
  ]
)
```

---

## DOC-10：Server BDD Feature Files

**Skip 條件**：`_START_STEP > 10` 或（full-auto 且 `features/*.feature` 已存在）

### DOC-10-A：生成 Server BDD Feature Files（D-03）

透過 **Skill tool** 呼叫 `gendoc`，args: `bdd`（gen 規則由 templates/BDD.gen.md 定義）。

gen-bdd 完成後：

```bash
_BDD_COUNT=$(ls "$(pwd)/features/"*.feature 2>/dev/null | wc -l | tr -d ' ')
echo "[DOC-10] 生成 ${_BDD_COUNT} 個 .feature 檔案"

git add features/
git commit -m "test(devsop)[DOC-10]: bdd-server — 生成 ${_BDD_COUNT} 個 Gherkin Scenario（Server BDD）"
```

### DOC-10-B：Server BDD Review Loop

```
_review_loop(
  doc_id        = "10",
  document_path = "features/",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 QA Expert（Server BDD 審查）",
  dimensions    = [
    "TC-ID tag 完整性：每個 Scenario 必須有 @TC-E2E-{MODULE}-{SEQ}-{CASE} tag，對應 RTM.md",
    "Gherkin 格式正確性：Given/When/Then 語義清晰，非同步操作有對應 step",
    "三類情境覆蓋：每個 Feature 有 Happy/Error/Boundary Scenario",
    "PRD US + RTM 覆蓋：每個 US 至少一個 Scenario，TC-ID 可回溯至 RTM",
    "Scenario Outline 使用：有重複情境的地方使用 Examples 表格",
    "EDD WS 覆蓋：若有 WebSocket 設計，@websocket Scenario 存在",
  ]
)
```

---

## DOC-10-C：Client BDD Feature Files

**Skip 條件**：`_START_STEP > 10`；若 `client_type = none` → 靜默跳過

```bash
_CLIENT_TYPE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('client_type','none'))
except: print('none')
" 2>/dev/null || echo "none")

if [[ "$_CLIENT_TYPE" == "none" ]]; then
  echo "[DOC-10-C] client_type=none，跳過 Client BDD"
else
  echo "[DOC-10-C] 生成 Client BDD，client_type=${_CLIENT_TYPE}"
fi
```

### DOC-10-C-A：生成 Client BDD Feature Files（D-03）

透過 **Skill tool** 呼叫 `gendoc`，args: `client-bdd`（`_CLIENT_TYPE = none` 時跳過，gen 規則由 templates/BDD.gen.md 定義）。

gen-client-bdd 完成後：

```bash
git add features/client/ tests/ 2>/dev/null; true
git commit -m "test(devsop)[DOC-10-C]: client-bdd — Client BDD，client_type=${_CLIENT_TYPE}"
```

### DOC-10-C-B：Client BDD Review Loop

```
_review_loop(
  doc_id        = "10C",
  document_path = "features/client/",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 QA Expert（Client BDD 審查）",
  dimensions    = [
    "PRD AC 完整覆蓋：每個 AC 有正常/錯誤/邊界三種 Scenario",
    "平台特定 tag：@responsive / @a11y / @performance / @mobile 存在且合理",
    "Step Definitions 骨架：web 類型有對應 .steps.ts 骨架存在",
    "與 Server BDD 不重複：Client BDD 只測 UI 行為，非後端邏輯",
    "client_type 一致性：生成格式與 state 中 client_type 一致",
  ]
)
```

---

## DOC-10-D：Runbook + LOCAL_DEPLOY（最後層文件）

**Skip 條件**：full-auto 且 `docs/RUNBOOK.md` 與 `docs/LOCAL_DEPLOY.md` 均非空

> 位置：最後層文件，在 BDD 之後生成（需讀取所有上游文件）。

### DOC-10-D-A：生成 RUNBOOK

透過 **Skill tool** 呼叫 `gendoc`，args: `runbook`（gen 規則由 templates/runbook.gen.md 定義，讀取全鏈上游文件）。

gen-runbook 完成後：

```bash
git add docs/RUNBOOK.md
git commit -m "docs(devsop)[DOC-10-D]: gen — RUNBOOK 初稿生成（全鏈上游對齊）"
```

### DOC-10-D-B：Runbook Review Loop

透過 **Skill tool** 呼叫 `reviewdoc`，args: `runbook`（審查標準由 templates/runbook.review.md 定義）。

reviewdoc 完成後：

```bash
git add docs/RUNBOOK.md
git commit -m "docs(devsop)[DOC-10-D]: review — RUNBOOK 審查通過"
```

### DOC-10-D-C：生成 LOCAL_DEPLOY

透過 **Skill tool** 呼叫 `gendoc`，args: `local-deploy`（gen 規則由 templates/LOCAL_DEPLOY.gen.md 定義，讀取全鏈上游文件）。

gen-local-deploy 完成後：

```bash
git add docs/LOCAL_DEPLOY.md
git commit -m "docs(devsop)[DOC-10-D]: gen — LOCAL_DEPLOY 初稿生成（全鏈上游對齊）"
```

### DOC-10-D-D：LOCAL_DEPLOY Review Loop

透過 **Skill tool** 呼叫 `reviewdoc`，args: `local-deploy`（審查標準由 templates/LOCAL_DEPLOY.review.md 定義）。

reviewdoc 完成後：

```bash
git add docs/LOCAL_DEPLOY.md
git commit -m "docs(devsop)[DOC-10-D]: review — LOCAL_DEPLOY 審查通過"
```

---

## DOC-11：對齊掃描（gendoc-align-check）

**Skip 條件**：`_START_STEP > 11`

### DOC-11-A：呼叫 gendoc-align-check skill

**立即用 Skill 工具呼叫 `/gendoc-align-check`（必須真正觸發 Skill tool，不得只輸出文字）：**

用 Skill 工具，skill name = `gendoc-align-check`，不帶任何 args。

> align-check 將執行：
> - **Dimension 0**（必要文件存在性）：確認 BRD/PRD/EDD/ARCH/API/SCHEMA/RTM 存在且非空
> - **Dimension 1**（Doc→Doc）：BRD→PRD→PDD→EDD→ARCH/API/SCHEMA→BDD 鏈完整性
> - **Dimension 2**（Doc→Code）：autogen 無 src/，此維度自動略過或 0 findings
> - **Dimension 3**（Code→Test）：autogen 無 src/，此維度自動略過或 0 findings
> - **Dimension 4**（Doc→Test）：PRD AC → BDD Scenario → RTM TC-ID 完整鏈
>
> 輸出：`docs/ALIGN_REPORT.md`（問題清單，╔══╗ 格式，含各維度 finding 統計）

```bash
_ALIGN_CRITICAL=$(grep -c "CRITICAL\|HIGH" "$(pwd)/docs/ALIGN_REPORT.md" 2>/dev/null || echo 0)
echo "[DOC-11] align-check 完成，CRITICAL/HIGH 問題：${_ALIGN_CRITICAL} 個"

git add docs/ALIGN_REPORT.md
git commit -m "docs(devsop)[DOC-11]: align-check — Doc/BDD/RTM 對齊掃描，issues=${_ALIGN_CRITICAL}"
```

### DOC-11-B：對齊報告 Review Loop

```
_review_loop(
  doc_id        = "11",
  document_path = "docs/ALIGN_REPORT.md",
  strategy      = _REVIEW_STRATEGY,
  reviewer_role = "資深 Domain Expert（對齊二次審查）",
  dimensions    = [
    "Dimension 0 完整性：所有必要文件已確認存在，無遺漏",
    "Dimension 1 鏈完整：BRD→PRD→EDD→ARCH/API/SCHEMA→BDD 每個節點可回溯",
    "Dimension 4 覆蓋：PRD 每個 AC 可追溯至 BDD @tag 和 RTM TC-ID",
    "問題嚴重度分級正確：CRITICAL/HIGH/MEDIUM/LOW 分類符合實際影響",
    "修復建議可執行：每個 finding 有具體修復步驟",
    "術語一致性：跨文件同一概念使用相同術語",
  ]
)
```

若 `_ALIGN_CRITICAL > 5` 且 `_EXEC_MODE=interactive`：
```
AskUserQuestion: 發現 ${_ALIGN_CRITICAL} 個 CRITICAL/HIGH 問題，是否立即修復？
[1] 是 — AI 自動修復對應文件（執行 /gendoc-align-fix all）
[2] 否 — 記錄後繼續
```

---

## DOC-12：HTML 生成 + GitHub Pages 部署

**Skip 條件**：`_START_STEP > 12`

### Step 12-A：呼叫 gendoc-gen-html

用 **Skill 工具**呼叫 `/gendoc-gen-html`，生成 `docs/pages/` 靜態網站。

> **圖表引用規格（傳給 gen-html 的指引）**：
> - `docs/diagrams/*.md` 中每個 Mermaid 區塊直接嵌入對應 HTML 頁面（含 Lightbox 放大功能）
> - `docs/diagrams/puml/*.puml` 顯示為帶下載連結的圖表卡
> - EDD 頁面必須顯示 UML 9 大圖；ARCH 頁面顯示 C4 + Infrastructure 圖；SCHEMA 頁面顯示 ER 圖
> - Mermaid 渲染設定（每個 HTML 含）：
>   ```html
>   <script type="module">
>     import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
>     mermaid.initialize({ startOnLoad: true, flowchart: { curve: 'basis' }, er: { layoutDirection: 'TD', minEntityWidth: 100 } });
>   </script>
>   ```
> - 必須生成的頁面：index（README）/ brd / prd / pdd / edd（含所有 Mermaid 圖）/ arch / api（含程式碼高亮）/ schema（含 ER 圖 + CREATE TABLE SQL）/ test-plan / rtm / bdd（Scenario 列表）/ align-report
> - sidebar 動態包含所有已生成頁面

### Step 12-B：寫入 GitHub Actions Workflow

```bash
mkdir -p "$(pwd)/.github/workflows"
_APP_NAME=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('project_name','myapp'))
except: print('myapp')
" 2>/dev/null || echo "myapp")
echo "[DOC-12] 寫入 .github/workflows/pages.yml (app=${_APP_NAME})"
```

Read `templates/GITHUB_PAGES.yml`，替換 `__APP_NAME__` 為 `_APP_NAME`，Write 工具寫入 `.github/workflows/pages.yml`。

### Step 12-C：GitHub Repo 建立（若不存在）

```bash
_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
if [[ -z "$_REMOTE" ]]; then
  gh auth status 2>/dev/null || { echo "[錯誤] gh CLI 未登入，請執行 gh auth login"; exit 1; }
  gh repo create "${_APP_NAME}" --public \
    --description "Generated by gendoc-flow — MYDEVSOP" \
    --source=. --remote=origin --push 2>/dev/null \
    || echo "[警告] Repo 建立失敗，請手動建立並設定 remote"
  gh api "repos/$(gh api user --jq .login)/${_APP_NAME}/pages" \
    --method POST -f "source[branch]=gh-pages" -f "source[path]=/" 2>/dev/null \
    || echo "[Info] Pages 可能已啟用，或請至 Repo Settings 手動啟用"
else
  echo "[DOC-12] Remote 已存在：${_REMOTE}"
fi
```

### Step 12-D：Commit + Push

```bash
_INPUT_TYPE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('input_type','unknown'))
except: print('unknown')
" 2>/dev/null || echo "unknown")

git add docs/ features/ .github/ README.md 2>/dev/null
git diff --cached --quiet && echo "[Info] 無新變更" || \
git commit -m "$(cat <<EOF
docs(gendoc-flow): generate complete documentation set

Documents: PRD PDD EDD ARCH API SCHEMA test-plan RTM BDD CONSISTENCY-REPORT
HTML Pages: docs/pages/
GitHub Actions: .github/workflows/pages.yml
Input: ${_INPUT_TYPE} | Loop: ${_LOOP_COUNT} rounds per doc
EOF
)"
git push origin main 2>/dev/null || echo "[警告] Push 失敗，請確認 remote 設定"
```

### Step 12-E：完成報告

```bash
_PROJ=$(python3 -c "import json; print(json.load(open('${_STATE_FILE}')).get('project_name','?'))" 2>/dev/null || echo "?")
_CLASSES=$(python3 -c "import json; print(json.load(open('${_STATE_FILE}')).get('class_count','?'))" 2>/dev/null || echo "?")
_GH_OWNER=$(gh api user --jq .login 2>/dev/null || echo "[owner]")

echo "╔══════════════════════════════════════════════════╗"
echo "║  gendoc-flow — 完成！                         ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  專案：${_PROJ}"
echo "║  Classes：${_CLASSES} | Loop：${_LOOP_COUNT} 輪/doc"
echo "║  輸入：${_INPUT_TYPE}"
echo "╠══════════════════════════════════════════════════╣"
for f in docs/BRD.md docs/PRD.md docs/PDD.md docs/EDD.md docs/ARCH.md \
          docs/API.md docs/SCHEMA.md docs/test-plan.md docs/RTM.md \
          docs/RUNBOOK.md docs/LOCAL_DEPLOY.md \
          docs/CONSISTENCY-REPORT.md; do
  [[ -f "$f" ]] && echo "║  ✓ $f"
done
echo "╠══════════════════════════════════════════════════╣"
echo "║  GitHub Pages（約 1-5 分鐘後生效）："
echo "║  https://${_GH_OWNER}.github.io/${_PROJ}/"
echo "║  Actions: https://github.com/${_GH_OWNER}/${_PROJ}/actions"
echo "╚══════════════════════════════════════════════════╝"
```

---

## 6 Expert 角色定義

| 角色 | 生成職責 | 審查誰 |
|------|----------|--------|
| **PM Expert** | PRD（DOC-03） | PDD（by PM, DOC-04） |
| **UX Expert** | PDD（DOC-04） | PRD（by UX, DOC-03） |
| **System Architect** | EDD（DOC-05）、ARCH（DOC-06） | EDD（by Backend, DOC-05）、ARCH（by Domain, DOC-06）、Schema（by SA, DOC-08） |
| **Backend Expert** | API Design（DOC-07）、DB Schema（DOC-08） | API（by QA, DOC-07） |
| **QA Expert** | Test Plan+RTM（DOC-09）、BDD（DOC-10） | RTM（by Domain, DOC-09）、BDD（self, DOC-10） |
| **Domain Expert** | 一致性報告（DOC-11） | ARCH（DOC-06）、RTM（DOC-09）、CONSISTENCY-REPORT（DOC-11） |

---

## Escalation Budget

每個 DOC 的 Phase A（gen）和 Phase B（review loop）各維護連續失敗計數器。連續失敗 3 次時立即停止，輸出：

```
STATUS: BLOCKED
REASON: [1-2 sentences — 具體說明在哪個 DOC/Phase 卡住]
ATTEMPTED: [嘗試過什麼，最多 3 條]
RECOMMENDATION: [使用者下一步應做什麼]
```

計數器在步驟成功時重置為 0。Review loop 中每「輪」計一次（finding > 0 且修復後下一輪仍 CRITICAL > 0 算失敗）。

---

## Confusion Protocol

以下情境觸發停止並詢問，不得猜測：
- 同一份上游文件（如 EDD）的不同章節說法相互矛盾，且無法判斷以哪版為準
- 兩份相鄰文件的核心數字（SLO / Port / Namespace）衝突
- 生成某文件需要破壞性覆寫（已有完整內容），且使用者未明確授權

觸發時：一句話說明歧義，列出 2-3 個選項與各自取捨，等待確認。
**SPAWNED_SESSION 下**：自動選最保守選項，輸出 `[SPAWNED] 自動選擇最保守選項：<選項說明>`，繼續。
**不適用於**：例行生成、明確已指定 DOC 類型的呼叫。

---

## Completion Status Protocol

本 skill 完成時，以下列格式回報：

- **DONE** — 全部 DOC 步驟完成，所有文件通過 Review，GitHub Pages 已部署
- **DONE_WITH_CONCERNS** — 完成，但有已知問題需使用者留意（逐一列出，例如：某 DOC review 達輪次上限但仍有 MEDIUM finding）
- **BLOCKED** — 無法繼續（見 Escalation Budget 格式）
- **NEEDS_CONTEXT** — 缺少必要資訊（明確說明缺什麼上游文件或資訊）

---

*此技能由 MYDEVSOP 框架維護。版本：1.2.0*
