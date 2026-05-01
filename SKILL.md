---
name: gendoc
description: |
  Universal document generator. Reads templates/<TYPE>.md (structure) and
  templates/<TYPE>.gen.md (generation rules) to produce docs/<TYPE>.md from
  upstream engineering documents. Type is provided as the first argument.
  Use when asked to "gendoc edd", "gen brd", "生成 PRD", "gendoc local-deploy", etc.
  Proactively invoke when the user specifies a document type to generate. (gendoc)
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
  - Skill
---

# gendoc — 通用文件生成器

依 `templates/<TYPE>.md`（結構）+ `templates/<TYPE>.gen.md`（生成規則）產出 `docs/<TYPE>.md`。
呼叫格式：`/gendoc <type>`，例如 `/gendoc edd`、`/gendoc local-deploy`、`/gendoc runbook`。

---

## Iron Law
**NO GENERATION WITHOUT READING BOTH TYPE.md AND TYPE.gen.md FIRST. Templates are the single source of truth.**

---

## Step -1：初始化守衛

> 版本更新由 SessionStart hook 自動處理（每小時一次）。手動更新：`/gendoc-upgrade`

```bash
_INIT_STATE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo "")
if [[ -z "$_INIT_STATE" ]]; then
  echo "[R-01] 未偵測到 state file"
fi
```

**[R-01 AI 指令]** 若 `_INIT_STATE` 為空，使用 **Skill tool** 呼叫 `/gendoc-config`，完成後重新讀取 state file，再繼續。

---

## Step 0：解析 Type 參數與 Session Config

### 0a. 取得 type 參數

```bash
# 從對話上下文取得 _DOC_TYPE（使用者輸入的 type 名稱，如 edd / brd / local-deploy / runbook）
# 以下為 AI 指令：從最近的使用者訊息中解析第一個非 skill 名稱的 token 作為 _DOC_TYPE

_DOC_TYPE=""   # AI 從 user 訊息解析後填入，e.g., "local-deploy"
```

**若 `_DOC_TYPE` 為空**（使用者沒有給 type）：

- 若 `SPAWNED_SESSION=true`：輸出 `STATUS: BLOCKED — type argument missing`，停止
- 若互動模式：使用 `AskUserQuestion` 詢問：

```
question: "請選擇要生成的文件類型（或直接輸入類型名稱）："
options:
  - "edd — Engineering Design Document"
  - "brd — Business Requirements Document"
  - "prd — Product Requirements Document"
  - "pdd — Product Design Document"
  - "arch — Architecture Document"
  - "api — API Design Document"
  - "schema — Database Schema Document"
  - "bdd — BDD Feature Files"
  - "test-plan — Test Plan + RTM"
  - "runbook — Operations Runbook"
  - "local-deploy — Local K8s Deploy Guide"
  - "frontend — Frontend Design Document"
  - "其他（手動輸入）"
```

### 0b. 解析 type → 檔名對照

```bash
# 對照表（AI 執行時從此表查找）
# type input    → TEMPLATE_BASENAME（不含 .md）
# edd           → EDD
# brd           → BRD
# prd           → PRD
# pdd           → PDD
# arch          → ARCH
# api           → API
# schema        → SCHEMA
# bdd           → BDD
# rtm           → RTM
# test-plan     → test-plan
# runbook       → runbook
# local-deploy  → LOCAL_DEPLOY
# idea          → IDEA
# readme        → README
# uml-class     → UML-CLASS-GUIDE
# frontend      → FRONTEND
# client        → FRONTEND  （向後相容別名）
# client-impl   → CLIENT_IMPL
# client_impl   → CLIENT_IMPL  （底線別名）
# cocos         → CLIENT_IMPL  （遊戲快捷別名）
# unity         → CLIENT_IMPL
# react-impl    → CLIENT_IMPL
# vue-impl      → CLIENT_IMPL
# admin-impl    → ADMIN_IMPL
# admin_impl    → ADMIN_IMPL   （底線別名）
# admin         → ADMIN_IMPL   （快捷別名）

_CWD="$(pwd)"
if [[ -f "$_CWD/templates/pipeline.json" ]]; then
  _TEMPLATE_DIR="${_TEMPLATE_DIR:-$_CWD/templates}"
else
  _TEMPLATE_DIR="${_TEMPLATE_DIR:-$HOME/.claude/gendoc/templates}"
fi
_DOCS_DIR="${_DOCS_DIR:-$_CWD/docs}"

# 查找對應的模板基名（TYPE_BASENAME）
# AI 根據上表查找 _DOC_TYPE → _TYPE_BASENAME
# 若查不到，嘗試：先 tr '[:lower:]-' '[:upper:]_'，再 find 大小寫不分

_TEMPLATE_FILE="${_TEMPLATE_DIR}/${_TYPE_BASENAME}.md"
_GEN_RULES_FILE="${_TEMPLATE_DIR}/${_TYPE_BASENAME}.gen.md"
_OUTPUT_FILE="${_DOCS_DIR}/${_TYPE_BASENAME}.md"

echo "[gendoc] type=${_DOC_TYPE} → template=${_TEMPLATE_FILE}"
echo "[gendoc] gen rules=${_GEN_RULES_FILE}"
echo "[gendoc] output=${_OUTPUT_FILE}"
```

### 0c. 驗證檔案存在

```bash
_TEMPLATE_EXISTS=false
_GEN_RULES_EXISTS=false

if [[ -f "$_TEMPLATE_FILE" ]]; then
  _TEMPLATE_EXISTS=true
  echo "✅ Template 找到：$_TEMPLATE_FILE（$(wc -l < "$_TEMPLATE_FILE") 行）"
else
  echo "❌ Template 不存在：$_TEMPLATE_FILE"
fi

if [[ -f "$_GEN_RULES_FILE" ]]; then
  _GEN_RULES_EXISTS=true
  echo "✅ Gen rules 找到：$_GEN_RULES_FILE（$(wc -l < "$_GEN_RULES_FILE") 行）"
else
  echo "⚠️  Gen rules 不存在：$_GEN_RULES_FILE（將僅依 template 結構生成，不套用推斷規則）"
fi
```

**Confusion Protocol — 找不到 template 時：**

```
STOP. 找不到 template：$_TEMPLATE_FILE
可能原因：
  A) type 名稱拼錯（使用者輸入的是 "${_DOC_TYPE}"）
  B) template 尚未建立
  C) templates 目錄不在預期位置（${_TEMPLATE_DIR}）

請確認後重試，或使用 /gendoc <正確type名稱>。
STATUS: BLOCKED
```

**Escalation Budget**：若連續 3 次找不到 template 或讀取失敗，停止並輸出：

```
STATUS: BLOCKED
REASON: 連續 3 次無法讀取 template 或 gen rules
ATTEMPTED: <嘗試過的路徑列表>
RECOMMENDATION: 確認 templates 目錄位置，或使用 /gendoc-config 初始化設定
```

### 0d. 讀取 Session Config

```bash
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")

_EXEC_MODE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('execution_mode','full-auto'))
except: print('full-auto')
" 2>/dev/null || echo "full-auto")

_REVIEW_STRATEGY=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('review_strategy','standard'))
except: print('standard')
" 2>/dev/null || echo "standard")

echo "[gendoc] mode=${_EXEC_MODE} / review=${_REVIEW_STRATEGY}"
```

---

## Step 1：讀取 Template 與 Gen Rules

**[AI 指令]** 依序使用 `Read` 工具讀取：

1. `$_TEMPLATE_FILE`（文件結構骨架）
2. `$_GEN_RULES_FILE`（若存在：關鍵欄位提取規則、推斷邏輯、Section Rules、Self-Check Checklist）

從 gen rules 的 frontmatter 提取：
- `upstream-docs`：上游文件清單
- `output-path`：輸出路徑（若有，覆蓋 Step 0b 推算的 `_OUTPUT_FILE`）
- `quality-bar`：品質標準（供 Step 3 自我檢核用）

---

## Step 2：讀取上游文件

```bash
# 從 gen rules frontmatter 的 upstream-docs 讀取
# 例：["docs/EDD.md", "docs/BRD.md", "docs/PRD.md"]

for _upstream in "${_UPSTREAM_DOCS[@]}"; do
  if [[ -f "$_upstream" ]]; then
    echo "✅ 讀取上游文件：$_upstream（$(wc -l < "$_upstream") 行）"
  else
    echo "⚠️  上游文件不存在：$_upstream（略過，對應欄位使用格式範例佔位符）"
  fi
done
```

**[AI 指令]** 使用 `Read` 工具讀取每份存在的上游文件。若 gen rules 未指定 upstream-docs，根據 type 常識判斷（EDD 幾乎總是存在的上游）。

讀取完所有上游文件後，按照 gen rules 的「Key Fields」表格提取欄位，記錄到工作記憶，供 Step 3 填入。

---

## Step 3：生成文件

以 `$_TEMPLATE_FILE` 為結構基礎，套用 gen rules 中的所有規則生成完整文件。

**執行優先順序（gen rules 存在時）：**

1. **Section Rules**：逐章節套用規則（禁止跳過任何章節）
2. **Key Fields 填入**：所有 Gen Rules「Key Fields」表格中標記「不得留裸 `{{...}}`」的欄位，必須填入從上游文件提取的真實值
3. **Inference Rules**：依 gen rules 推斷邏輯填入衍生欄位（MIGRATE_CMD、WEB_DEV_CMD 等）
4. **格式範例佔位符**：允許保留的欄位（在 gen rules 明確標記）加上說明，不視為缺失

**gen rules 不存在時：**
- 依 template 結構和章節標題自行推斷填入邏輯
- 所有欄位使用有意義的格式範例佔位符（非裸空白）

**品質標準**：`$quality-bar`（來自 gen rules frontmatter）

---

## Step 4：自我檢核

**[AI 指令]** 依 gen rules 的「Self-Check Checklist」逐項勾選（不可跳過）。

若 gen rules 不存在，使用通用檢核：

- [ ] 文件無裸 `{{PLACEHOLDER}}` 空白（無說明、無推斷依據的佔位符）
- [ ] Document Control 有填入日期與 DOC-ID
- [ ] 所有章節標題與 template 一致（無遺漏章節）
- [ ] 引用的上游文件數字（Port、namespace、SLO）與實際讀取一致

若有任何項目未通過，立即修正後繼續。

---

## Step 5：寫入並輸出摘要

```bash
mkdir -p "$_DOCS_DIR"
```

使用 `Write` 工具將內容寫入 `$_OUTPUT_FILE`。

寫入後執行 git commit（若在 git repo 中）：

```bash
git add "$_OUTPUT_FILE"
git commit -m "docs(gendoc): gen-${_DOC_TYPE} — initial draft"
```

若 git commit 失敗（無 git repo 或 hooks 阻擋），記錄 `_COMMIT_HASH="N/A"`，繼續輸出摘要，不中斷。

**[AI 輸出摘要]**：

```
╔══════════════════════════════════════════════════════╗
║  /gendoc ${_DOC_TYPE} 完成                            ║
╠══════════════════════════════════════════════════════╣
║  Template：${_TEMPLATE_FILE}                          ║
║  Gen Rules：${_GEN_RULES_FILE}（存在/不存在）          ║
║  輸出：${_OUTPUT_FILE}（<行數> 行）                   ║
║  Commit：<hash 或 N/A>                                ║
╚══════════════════════════════════════════════════════╝
```

[白話說明] 生成完成。執行 `/reviewdoc ${_DOC_TYPE}` 進行品質審查。

**Completion Status**：`DONE`（若 checklist 全通過）/ `DONE_WITH_CONCERNS`（若有格式範例佔位符殘留）/ `BLOCKED`（若連續 3 次自我檢核失敗）

---

## 異常處理

| 狀況 | 處理方式 |
|------|----------|
| Type 不在對照表 | Confusion Protocol（見 Step 0b）|
| Template 不存在 | BLOCKED（見 Step 0c）|
| Gen rules 不存在 | 僅依 template 結構生成，跳過推斷規則；摘要標注 DONE_WITH_CONCERNS |
| 上游文件全部不存在 | 所有欄位使用格式範例佔位符，在文件開頭加 `<!-- WARNING: 無上游文件，所有欄位需手動填入 -->`；繼續生成 |
| 連續 3 次 checklist 失敗 | 寫入 TODO 注釋並繼續；最終摘要標注 DONE_WITH_CONCERNS |
| git commit 失敗 | 不中斷，提示手動 commit |
| SPAWNED_SESSION=true | 全自動，不彈 AskUserQuestion，自動選推薦選項 |
