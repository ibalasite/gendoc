---
name: gendoc-repair
description: Pipeline diff + backfill — 比對專案 completed_steps 與 pipeline.json 的差異，列出缺漏步驟，並選擇性地從第一個缺漏步驟啟動 gendoc-flow 補跑
version: 1.0.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Skill
  - Agent
  - AskUserQuestion
---

# gendoc-repair — Pipeline Diff & Backfill

```
Input:   當前目錄的 .gendoc-state-*.json（或 .gendoc-state.json）
Output:  缺漏步驟表格 + 可選的 gendoc-flow 補跑
Purpose: 讓老專案在 pipeline.json 新增步驟後能夠補跑，不需手動查詢
```

---

## Step -1：版本自動更新檢查 + SPAWNED_SESSION 偵測

```bash
# SPAWNED_SESSION 偵測
[ -n "$OPENCLAW_SESSION" ] && _SPAWNED="true" || _SPAWNED="false"
echo "SPAWNED_SESSION: $_SPAWNED"

# [Fix-D] 主動版本比對 — 若 repo 有新版則自動 upgrade，再繼續
_GENDOC_REPO="$HOME/projects/gendoc"
_VERSION_FILE="$HOME/.claude/gendoc/.installed-version"
_REPO_HEAD=$(git -C "$_GENDOC_REPO" rev-parse --short HEAD 2>/dev/null || echo "")
_INSTALLED=$(cat "$_VERSION_FILE" 2>/dev/null | tr -d '[:space:]' || echo "")
if [[ -n "$_REPO_HEAD" && "$_REPO_HEAD" != "$_INSTALLED" ]]; then
  echo "[R-00] 偵測到新版 gendoc（${_INSTALLED:-未知} → ${_REPO_HEAD}），執行 upgrade..."
  bash "$_GENDOC_REPO/bin/gendoc-upgrade"
  echo "[R-00] ✅ upgrade 完成，繼續執行"
else
  echo "[R-00] gendoc 版本已是最新（${_REPO_HEAD:-未知}），繼續"
fi
```

---

## Step 0：讀取 State File + Pipeline

```bash
_CWD="$(pwd)"

# 尋找 state file（優先 named，其次 generic）
_STATE_FILE=$(ls "$_CWD"/.gendoc-state-*.json 2>/dev/null | head -1 || echo "")
[[ -z "$_STATE_FILE" && -f "$_CWD/.gendoc-state.json" ]] && _STATE_FILE="$_CWD/.gendoc-state.json"

if [[ -z "$_STATE_FILE" ]]; then
  echo "❌ 在 $_CWD 找不到 .gendoc-state-*.json 或 .gendoc-state.json"
  echo "   請先執行 /gendoc-auto 或 /gendoc-flow 初始化此專案"
  exit 1
fi

echo "[repair] state file：$_STATE_FILE"

# 讀取 completed_steps
_COMPLETED=$(python3 -c "
import json, sys
try:
  d = json.load(open('$_STATE_FILE'))
  steps = d.get('completed_steps', [])
  print('\n'.join(steps))
except Exception as e:
  print(f'ERROR: {e}', file=sys.stderr)
  sys.exit(1)
" 2>/dev/null || echo "")

echo "[repair] 已完成步驟數：$(echo "$_COMPLETED" | grep -c . 2>/dev/null || echo 0)"

# 尋找 pipeline.json（local-first）
_PIPELINE_LOCAL="$_CWD/templates/pipeline.json"
_PIPELINE_GLOBAL="$HOME/.claude/gendoc/templates/pipeline.json"
if [[ -f "$_PIPELINE_LOCAL" ]]; then
  _PIPELINE="$_PIPELINE_LOCAL"
  echo "[repair] pipeline：local ($  _PIPELINE_LOCAL)"
elif [[ -f "$_PIPELINE_GLOBAL" ]]; then
  _PIPELINE="$_PIPELINE_GLOBAL"
  echo "[repair] pipeline：global ($_PIPELINE_GLOBAL)"
else
  echo "❌ 找不到 pipeline.json（local 或 global）"
  exit 1
fi
```

---

## Step 1：Pipeline Diff 分析

**[AI 指令]** 用 Python 計算差異，產出 diff 表格：

```bash
python3 - "$_PIPELINE" "$_STATE_FILE" <<'PY'
import json, sys

pipeline_file = sys.argv[1]
state_file    = sys.argv[2]

pipe  = json.load(open(pipeline_file, encoding="utf-8"))
state = json.load(open(state_file, encoding="utf-8"))

completed = set(state.get("completed_steps", []))
client_type = state.get("client_type", "unknown")

all_steps  = []
for phase in pipe.get("phases", []):
    phase_name = phase.get("name") or phase.get("id") or "?"
    for step in (phase.get("steps") or []):
        sid = step.get("id", "")
        if not sid:
            continue
        # 條件過濾（與 gendoc-flow 相同的判斷邏輯）
        cond = step.get("condition", "")
        if cond == "client_type != api-only" and client_type == "api-only":
            continue
        if cond == "client_type == api-only" and client_type != "api-only":
            continue
        all_steps.append({
            "id":    sid,
            "phase": phase_name,
            "name":  step.get("name", ""),
            "type":  step.get("type", "standard"),
        })

missing  = [s for s in all_steps if s["id"] not in completed]
present  = [s for s in all_steps if s["id"] in completed]

print(f"\n{'='*70}")
print(f"  Pipeline Diff 報告")
print(f"  pipeline   : {pipeline_file.split('/')[-1]}")
print(f"  client_type: {client_type}")
print(f"  total steps: {len(all_steps)}")
print(f"  completed  : {len(present)}")
print(f"  missing    : {len(missing)}")
print(f"{'='*70}\n")

if missing:
    print(f"{'ID':<28} {'Phase':<20} {'Name':<30}")
    print(f"{'-'*28} {'-'*20} {'-'*30}")
    for s in missing:
        print(f"{s['id']:<28} {s['phase']:<20} {s['name']:<30}")
    print(f"\n第一個缺漏步驟：{missing[0]['id']}")
    print(f"MISSING_COUNT:{len(missing)}")
    print(f"FIRST_MISSING:{missing[0]['id']}")
else:
    print("✅ 所有 pipeline 步驟已完成，無需補跑。")
    print("MISSING_COUNT:0")
PY
```

**[AI 指令]** 從輸出中擷取：
- `_MISSING_COUNT`：`MISSING_COUNT:N` 行的 N
- `_FIRST_MISSING`：`FIRST_MISSING:xxx` 行的 xxx

---

## Step 2：若無缺漏 → 結束

若 `_MISSING_COUNT == 0`：

```
╔══════════════════════════════════════════════════════╗
║  /gendoc-repair 完成                                  ║
╠══════════════════════════════════════════════════════╣
║  ✅ 所有步驟已完成，pipeline 完整無缺                  ║
╚══════════════════════════════════════════════════════╝
```

輸出 `DONE`，結束。

---

## Step 3：若有缺漏 → 詢問是否補跑

`_SPAWNED == "true"` 時自動選 [1]（補跑），跳過提問。

否則用 `AskUserQuestion` 詢問：

```
發現 {_MISSING_COUNT} 個缺漏步驟（從 {_FIRST_MISSING} 開始）。

要從第一個缺漏步驟補跑 gendoc-flow 嗎？

[1] 是，從 {_FIRST_MISSING} 補跑（設定 start_step 並呼叫 gendoc-flow）
[2] 否，只看報告，不補跑
```

---

## Step 4：若選擇補跑 → 更新 start_step + 呼叫 gendoc-flow

```bash
# 更新 state file 的 start_step
_NOW=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
_TMP="${_STATE_FILE}.repair.tmp"
python3 - <<PYEOF
import json, os
d = json.load(open("$_STATE_FILE", encoding="utf-8"))
d["start_step"]   = "$_FIRST_MISSING"
d["last_updated"] = "$_NOW"
with open("$_TMP", "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
os.replace("$_TMP", "$_STATE_FILE")
print(f"[repair] start_step → $_FIRST_MISSING")
PYEOF
```

然後用 **Skill tool** 呼叫 `gendoc-flow`（無額外 args）。

---

## Step 5：若選擇不補跑 → 輸出建議

```
╔══════════════════════════════════════════════════════════════════╗
║  /gendoc-repair — 缺漏步驟報告（不補跑）                          ║
╠══════════════════════════════════════════════════════════════════╣
║  缺漏：{_MISSING_COUNT} 個步驟（首個：{_FIRST_MISSING}）           ║
║                                                                  ║
║  手動補跑方法：                                                    ║
║    /gendoc-config  → 選「從某個 STEP 重新開始」→ 選 {_FIRST_MISSING}  ║
║    /gendoc-flow    → 從 {_FIRST_MISSING} 繼續                    ║
╚══════════════════════════════════════════════════════════════════╝
```

輸出 `DONE`，結束。
