---
name: gendoc-flow
description: |
  Template-driven document pipeline orchestrator（BRD 備妥後接手）。
  從 templates/pipeline.json 動態讀取步驟定義，對每份文件執行：
    專家 Gen subagent → (專家 Review subagent → 專家 Fix subagent → summary) loop → 更新 state
  不含硬編碼文件類型；所有文件類型、順序、條件均由 templates/pipeline.json 定義。
  可由 gendoc-auto handoff 觸發，或在 BRD 已備妥時獨立呼叫。
version: 2.0.0
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

# gendoc-flow v2 — Template-Driven Pipeline Orchestrator

```
Entry:   docs/BRD.md（必要）+ docs/IDEA.md（選用）
Source:  templates/pipeline.json（步驟定義）
         templates/{TYPE}.gen.md（生成規則）
         templates/{TYPE}.review.md（審查標準）
Loop:    For each step → Gen subagent → Review subagent → Fix subagent → loop
Main AI: 主 Claude 協調整條流水線，直到 pipeline 走完
```

**架構原則（不可違反）：**
- 文件類型、順序、條件 → 只在 `templates/pipeline.json` 定義
- 生成規則 → 只在 `templates/{TYPE}.gen.md` 定義
- 審查標準 → 只在 `templates/{TYPE}.review.md` 定義
- 本 skill → 只負責流程穩定，不硬編碼任何文件類型或輸出項目
- 新增文件類型：pipeline.json + 三件套（.md/.gen.md/.review.md），不需改 skill

---

## Iron Law

> **鐵律：每份文件生成前，gen subagent 必須讀取所有上游文件（累積鏈）。**
> 上游清單在 TYPE.gen.md frontmatter `upstream-docs` 中定義；若上游不存在則靜默跳過。
> 違反此鐵律的生成結果視為無效，必須重新生成。

---

## Step -1：版本自動更新檢查 + SPAWNED_SESSION 偵測

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

```bash
[ -n "$OPENCLAW_SESSION" ] && _SPAWNED="true" || _SPAWNED="false"
echo "SPAWNED_SESSION: $_SPAWNED"
[[ "$_SPAWNED" == "true" ]] && echo "[SPAWNED] 強制 full-auto，跳過互動提問"
```

---

## Step 0：Session Config（遵循 gendoc-shared §0）

```bash
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

_MAX_ROUNDS=$(python3 -c "
import json
try: print(int(json.load(open('${_STATE_FILE}')).get('max_rounds', 5)))
except: print(5)
" 2>/dev/null || echo "5")

_START_STEP=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('start_step', '0'))
except: print('0')
" 2>/dev/null || echo "0")

_COMPLETED=$(python3 -c "
import json
try: print(','.join(json.load(open('${_STATE_FILE}')).get('completed_steps',[])))
except: print('')
" 2>/dev/null || echo "")

_CLIENT_TYPE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('client_type','none'))
except: print('none')
" 2>/dev/null || echo "none")

echo "[Session] mode=${_EXEC_MODE} | strategy=${_REVIEW_STRATEGY} | max_rounds=${_MAX_ROUNDS}"
echo "[Session] start_step=${_START_STEP} | completed=[${_COMPLETED}] | client_type=${_CLIENT_TYPE}"
```

**已有值**：沿用已設定，直接繼續。
**無值（首次）**：顯示標準選單（execution_mode + review_strategy），寫入 state。

---

## Step 0-D：前置文件確認

```bash
_CWD="$(pwd)"
_TEMPLATE_DIR="${_TEMPLATE_DIR:-$_CWD/templates}"
_PIPELINE_FILE="${_TEMPLATE_DIR}/pipeline.json"
_BRD_OK=false
_IDEA_OK=false
[[ -s "$_CWD/docs/BRD.md"  ]] && _BRD_OK=true
[[ -s "$_CWD/docs/IDEA.md" ]] && _IDEA_OK=true

echo "[Check] BRD：${_BRD_OK} ／ IDEA：${_IDEA_OK}"
echo "[Check] Pipeline manifest：${_PIPELINE_FILE}"

if [[ "$_BRD_OK" == "false" ]]; then
  echo "[錯誤] docs/BRD.md 不存在或為空。"
  echo "       若無 IDEA：手動建立 BRD.md 後呼叫 /gendoc-flow。"
  echo "       若有 IDEA：先執行 /gendoc-auto 生成 IDEA+BRD。"
  exit 1
fi

if [[ ! -f "$_PIPELINE_FILE" ]]; then
  echo "[錯誤] templates/pipeline.json 不存在：$_PIPELINE_FILE"
  echo "       請確認 gendoc 已正確安裝（./setup）。"
  exit 1
fi

echo "✅ 前置確認通過，讀取 pipeline manifest"
python3 -c "
import json
steps = json.load(open('$_PIPELINE_FILE'))['steps']
print(f'Pipeline：{len(steps)} 個步驟')
for s in steps:
    print(f\"  {s['id']} [{s['layer']}] condition={s['condition']}\")
"
```

---

## Step 1：Pipeline 主循環

**主 Claude 讀取 pipeline.json 取得 steps 清單，按序執行。**

```python
# 主 Claude 依序執行以下邏輯（pseudo-code，AI 理解並執行）
pipeline = load_json("templates/pipeline.json")["steps"]
start_num = extract_step_num(_START_STEP)  # "D06-EDD" → 6, "0" → 0
completed = _COMPLETED.split(",")

for step in pipeline:
    step_num = extract_step_num(step["id"])  # "D06-EDD" → 6
    
    # ── Skip ──────────────────────────────────────────────
    if step_num < start_num:
        print(f"[Skip] {step['id']} — 早於 start_step，略過")
        continue
    
    if step["id"] in completed:
        print(f"[Skip] {step['id']} — 已在 completed_steps，略過")
        continue
    
    if step.get("handled_by") == "gendoc-auto":
        print(f"[Skip] {step['id']} — 由 gendoc-auto 處理，略過")
        continue
    
    # ── Condition ─────────────────────────────────────────
    if step["condition"] == "client_type != none" and _CLIENT_TYPE == "none":
        print(f"[Skip] {step['id']} — client_type=none，跳過")
        update_state_completed(step["id"])
        continue
    
    # ── 輸出文件已存在（full-auto 斷點續行）─────────────────
    if _EXEC_MODE == "full-auto" and not step.get("multi_file"):
        primary_output = step["output"][0]
        if file_exists_and_nonempty(primary_output):
            print(f"[Skip] {step['id']} — {primary_output} 已存在（full-auto），略過")
            update_state_completed(step["id"])
            continue
    
    # ── 執行步驟 ──────────────────────────────────────────
    execute_step(step)
    update_state_completed(step["id"])
```

---

## Step 1-C：特殊步驟（special_skill）

若 `step["special_skill"]` 存在（如 `gendoc-align-check`、`gendoc-gen-html`）：

```
用 Skill 工具呼叫 step["special_skill"]，不帶額外 args。
等待完成後：
  git add {step.output}
  git commit -m "{step.commit_prefix}: {special_skill} 完成"
update_state_completed(step["id"])
繼續下一步，不進入 gen→review loop。
```

---

## Step 1-D：標準步驟執行（gen → review loop → fix）

**以下是每個標準步驟（無 special_skill）的完整執行邏輯。**

### Phase D-1：Gen Subagent

**主 Claude 使用 Agent tool** 派送生成專家（依 TYPE 選角色），prompt 如下：

```
你是 [{TYPE}] 文件生成專家（角色依 templates/{TYPE}.gen.md 的 reviewer-roles 定義）。

你的任務：依照 templates/{TYPE}.gen.md 的規範，生成以下文件：
  {step.output}（多文件模式：{step.multi_file}）

執行步驟（不得跳過）：
1. 讀取 templates/{TYPE}.gen.md — 獲取生成規範、upstream-docs 清單、Self-Check Checklist
2. 讀取 templates/{TYPE}.md — 獲取文件結構模板
3. 讀取 upstream-docs 中所有上游文件（若不存在則靜默跳過）
4. 若 docs/IDEA.md 存在，讀取其 Appendix C 所列 docs/req/* 所有檔案（Iron Rule）
5. 依生成規範逐章節生成輸出文件

多文件模式（multi_file=true）：
- 依 {TYPE}.gen.md 規範生成多個檔案（e.g., features/*.feature）
- 每生成一個文件輸出：GENERATED_FILE: {path}
- 所有文件遵循統一的命名規範（見 gen.md §2 命名規範）

品質要求：
- 所有章節必須有實質內容，禁止留 {{placeholder}} 或「待補」
- 數字必須具體（SLO 數字、test coverage 目標等）
- 上游文件的關鍵欄位必須提取並引用，不得遺漏
- 通過 gen.md Self-Check Checklist 所有項目

完成後必須輸出（格式嚴格）：
GEN_RESULT:
  step_id: {step.id}
  type: {TYPE}
  files_generated:
    - {path1}
    - {path2}
  sections_completed: N
  self_check_passed: true|false
  notes: "任何特殊情況或推斷說明（可選）"
```

Gen subagent 完成後，主 Claude：
```bash
# 依 step.output 和 step.output_glob（多文件）git add
_OUTPUT_GLOB="${step.output_glob:-${step.output[0]}}"
git add $_OUTPUT_GLOB 2>/dev/null || git add ${step.output} 2>/dev/null
git commit -m "${step.commit_prefix}: gen — {TYPE} 初稿生成"
```

---

### Phase D-2：Review → Fix Loop

**主 Claude 執行以下 loop（max_rounds 次）：**

```python
for round in range(1, max_rounds + 1):
    
    # ── Review Subagent ──────────────────────────────
    review_result = spawn_review_agent(step, round)
    
    finding_total = review_result["finding_total"]
    critical = review_result["critical"]
    high = review_result["high"]
    medium = review_result["medium"]
    
    # ── 終止條件判斷 ─────────────────────────────────
    terminate = False
    terminate_reason = ""
    
    if finding_total == 0:
        terminate = True
        terminate_reason = "finding=0 (PASSED)"
    elif round == max_rounds:
        terminate = True
        terminate_reason = f"max_rounds={max_rounds} 已達"
    elif review_strategy == "tiered" and round >= 6 and (critical + high + medium) == 0:
        terminate = True
        terminate_reason = "tiered: CRITICAL+HIGH+MEDIUM=0 (PASSED)"
    elif review_strategy == "rapid" and round >= 3:
        terminate = True
        terminate_reason = "rapid: max_rounds=3 已達"
    
    if terminate:
        print(f"[{step.id}] Round {round} → 終止：{terminate_reason}")
        break
    
    # ── Fix Subagent ─────────────────────────────────
    spawn_fix_agent(step, round, review_result["findings"])
    
    git commit -m "{step.commit_prefix}: review-r{round} — Fix {finding_total} findings"
```

**Review Subagent prompt（主 Claude 派送）：**

```
你是 [{TYPE}] 文件審查專家（依 templates/{TYPE}.review.md 定義的 reviewer-roles）。

任務：依照 templates/{TYPE}.review.md 的審查標準，審查以下文件：
  {step.output}（多文件：{step.output_glob}）

執行步驟：
1. 讀取 templates/{TYPE}.review.md — 獲取所有 review items
2. 讀取被審查的文件（所有輸出文件）
3. 逐項執行每個 review item 的 Check：
   - 引用文件中的具體§章節
   - 說明通過或未通過的具體理由
4. 套用 Escalation Protocol（CRITICAL 未通過 → 停止後續低優先級審查）

完成後必須輸出（格式嚴格，主 Claude 將解析此區塊）：
REVIEW_RESULT:
  step_id: {step.id}
  type: {TYPE}
  round: {round}
  finding_total: N
  critical: N
  high: N
  medium: N
  low: N
  passed: true|false
  findings:
    - id: F-{N:02d}
      severity: CRITICAL|HIGH|MEDIUM|LOW
      item_ref: "[CRITICAL] 1 — 問題標題"
      section: "§X.Y"
      issue: "具體問題描述（引用文件內容）"
      fix_guide: "Fix 指引（來自 review.md 對應 item 的 Fix 段落）"
```

**Fix Subagent prompt（主 Claude 派送，findings_text 由主 Claude 從 REVIEW_RESULT 提取）：**

```
你是 [{TYPE}] 文件修復專家。

任務：依照以下 findings，精準修復文件中的具體問題。

本輪 Findings（Round {round}，共 {finding_total} 個）：
{findings_text}

被修復的文件：{step.output}（多文件：{step.output_glob}）

執行步驟（不得跳過）：
1. 讀取被修復的文件
2. 讀取 templates/{TYPE}.review.md 中對應 item 的 Fix 指引
3. 對每個 finding，執行精準修復：
   - 只修改 finding 指出的具體問題及其章節
   - 不修改 finding 未提及的部分（最小修改原則）
   - 保持文件整體結構、命名、格式不變
   - CRITICAL → 必須修復；HIGH → 必須修復；MEDIUM/LOW → 盡力修復
4. 修復後驗證：重讀修復段落，確認問題已解決
5. 多文件模式：同樣對所有相關 .feature 檔案執行修復

完成後必須輸出：
FIX_RESULT:
  step_id: {step.id}
  type: {TYPE}
  round: {round}
  fixed:
    - id: F-{N:02d}
      action: "具體修復說明（修改了哪個章節、加了什麼內容）"
  unfixed:
    - id: F-{N:02d}
      reason: "無法修復的原因（若有）"
  summary: "一句話：本輪共修復 N 個 findings，主要修復了 ..."
```

---

### Phase D-3：步驟完成 Summary

每個步驟完成後，主 Claude 輸出：

```
╔══════════════════════════════════════════════════════════╗
║  {step.id} — {step.type} 完成                            ║
╠══════════════════════════════════════════════════════════╣
║  審查輪次：{rounds_completed} 輪                         ║
║  最終 findings：CRITICAL={c} HIGH={h} MEDIUM={m} LOW={l} ║
║  狀態：PASSED / MAX_ROUNDS / CRITICAL_REMAINING          ║
╚══════════════════════════════════════════════════════════╝
```

更新 state file：
```bash
python3 - <<PYEOF
import json, os
f = '${_STATE_FILE}'
try: d = json.load(open(f))
except: d = {}
completed = d.get('completed_steps', [])
if '${step.id}' not in completed:
    completed.append('${step.id}')
d['completed_steps'] = completed
d['last_completed'] = '${step.id}'
tmp = f + '.tmp'
with open(tmp, 'w') as fp: json.dump(d, fp, ensure_ascii=False, indent=2)
os.replace(tmp, f)
print("✅ state 已更新")
PYEOF
```

---

## Step 2：Total Pipeline Summary

所有步驟完成後，主 Claude 輸出最終摘要：

```
╔══════════════════════════════════════════════════════════════════╗
║  /gendoc-flow 完成                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  步驟                  ║ 狀態     ║ 輪次 ║ 最終 Findings         ║
╠══════════════════════════════════════════════════════════════════╣
║  D03-PRD               ║ PASSED   ║ 2    ║ C=0 H=0 M=0 L=1      ║
║  D04-PDD  (skipped*)   ║ SKIPPED  ║ —    ║ —                    ║
║  ...                   ║ ...      ║ ...  ║ ...                   ║
╚══════════════════════════════════════════════════════════════════╝
* client_type=none 跳過

已生成文件：{list of all generated files}
HTML 網站：docs/pages/index.html
GitHub Pages：{url if configured}

建議下一步：
  - 若有 CRITICAL_REMAINING → 執行 /gendoc-config 選「從 D{N} 重新開始」
  - 若全部 PASSED → 可進入程式碼實作階段
```

---

## 專家角色對照表

主 Claude 在派送 Gen/Review/Fix subagent 時，依以下對照選擇合適的角色 persona：

| TYPE | Gen 專家 | Review 主審 |
|------|---------|------------|
| PRD | 資深 PM + UX Researcher | 資深 PM / BA |
| PDD | 資深 UX Designer | UX Architect |
| VDD | 資深 Visual Designer / Art Director | Art Director + Brand Strategist |
| EDD | 資深 Backend Architect | Backend Architect + Security Engineer |
| ARCH | 資深 System Architect | System Architect + SRE |
| API | 資深 API Designer | API Designer + Backend Engineer |
| SCHEMA | 資深 DBA | DBA + Backend Architect |
| FRONTEND | 資深 Frontend Architect | Frontend Architect + UX Engineer |
| test-plan | 資深 QA Architect | QA Architect + SRE |
| BDD-server | 資深 BDD Expert | BDD Expert + Backend Engineer |
| BDD-client | 資深 Frontend QA Expert | Frontend QA + BDD Expert |
| RTM | 資深 QA Architect | QA Architect + PM |
| runbook | 資深 SRE | SRE + DevOps Engineer |
| LOCAL_DEPLOY | 資深 DevOps Engineer | DevOps + Backend Engineer |

> 若 TYPE 不在此表，從 `templates/{TYPE}.review.md` frontmatter `reviewer-roles` 讀取角色。

---

## 附錄：多文件步驟處理（BDD）

BDD-server 和 BDD-client 是 multi_file=true 的步驟。處理差異：

**Gen 階段：**
- gen subagent 讀取 BDD-server.gen.md（或 BDD-client.gen.md）
- 依 gen.md 規範生成多個 .feature 檔案
- 每個 Feature File 對應一個功能模組（命名規範見 gen.md §2）
- 生成後輸出 GEN_RESULT.files_generated 清單

**Review 階段：**
- review subagent 讀取 BDD-server.review.md
- 審查所有 `features/*.feature` 或 `features/client/*.feature`
- REVIEW_RESULT.findings 中標注具體的 .feature 檔案路徑

**Fix 階段：**
- fix subagent 針對 findings 修改具體的 .feature 檔案
- 可能新增/刪除 Scenario，但不得刪除整個 .feature 檔案

**git commit：**
```bash
# BDD-server
_BDD_COUNT=$(ls features/*.feature 2>/dev/null | wc -l | tr -d ' ')
git add features/
git commit -m "test(gendoc)[D12-BDD-server]: gen — 生成 ${_BDD_COUNT} 個 .feature 檔案"

# BDD-client
_BDD_C_COUNT=$(ls features/client/*.feature 2>/dev/null | wc -l | tr -d ' ')
git add features/client/
git commit -m "test(gendoc)[D12b-BDD-client]: gen — 生成 ${_BDD_C_COUNT} 個 client .feature 檔案"
```
