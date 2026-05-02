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

# [Fix-D] 版本更新檢查
source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"
if [[ -d "$GENDOC_DIR/.git" ]]; then
  bash "$GENDOC_DIR/setup" upgrade 2>/dev/null && echo "[R-00] ✅ gendoc 已是最新版" || echo "[R-00] ⚠️ upgrade 失敗，繼續執行"
else
  echo "[R-00] ⚠️ 找不到 gendoc runtime，跳過版本更新"
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
has_admin   = bool(state.get("has_admin_backend", False))

all_steps  = []
# 支援 top-level steps（v2.x）和 phases（舊格式）兩種 pipeline 格式
if "steps" in pipe:
    raw_steps = [(s, s.get("layer") or "?") for s in pipe["steps"]]
elif "phases" in pipe:
    raw_steps = []
    for phase in pipe["phases"]:
        pname = phase.get("name") or phase.get("id") or "?"
        for s in (phase.get("steps") or []):
            raw_steps.append((s, pname))
else:
    raw_steps = []

for step, phase_name in raw_steps:
    sid = step.get("id", "")
    if not sid:
        continue
    # 條件過濾（與 gendoc-flow 相同的判斷邏輯）
    cond = step.get("condition", "")
    if cond == "client_type != api-only" and client_type == "api-only":
        continue
    if cond == "client_type == api-only" and client_type != "api-only":
        continue
    if cond == "client_type != none" and client_type in ("none", ""):
        continue
    if cond == "client_type == game" and client_type != "game":
        continue
    if cond == "has_admin_backend" and not has_admin:
        continue
    all_steps.append({
        "id":    sid,
        "phase": phase_name,
        "name":  step.get("name", step.get("type", "")),
        "type":  step.get("type", "standard"),
    })

missing  = [s for s in all_steps if s["id"] not in completed]
present  = [s for s in all_steps if s["id"] in completed]

print(f"\n{'='*70}")
print(f"  Pipeline Diff 報告")
print(f"  pipeline        : {pipeline_file.split('/')[-1]}")
print(f"  client_type     : {client_type}")
print(f"  has_admin_backend: {has_admin}")
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

## Step 1.5：語意輸出驗證（Output Completeness Check）

已標記 completed 但輸出檔案缺失的步驟，會獨立列為「語意不完整」，與「根本未執行」的步驟分開呈現。

```bash
python3 - "$_PIPELINE" "$_STATE_FILE" <<'PY'
import json, sys, glob as _glob
from pathlib import Path

pipeline_file = sys.argv[1]
state_file    = sys.argv[2]
cwd           = Path.cwd()

pipe  = json.load(open(pipeline_file, encoding="utf-8"))
state = json.load(open(state_file, encoding="utf-8"))

completed = set(state.get("completed_steps", []))

# Build step lookup（支援 top-level steps 和 phases 兩種格式）
step_map = {}
if "steps" in pipe:
    for step in pipe["steps"]:
        sid = step.get("id", "")
        if sid:
            step_map[sid] = step
elif "phases" in pipe:
    for phase in pipe["phases"]:
        for step in (phase.get("steps") or []):
            sid = step.get("id", "")
            if sid:
                step_map[sid] = step

incomplete = []

for sid in sorted(completed):
    step = step_map.get(sid)
    if not step:
        continue  # review-loop 或非標準步驟，跳過

    multi   = step.get("multi_file", False)
    outputs = step.get("output", [])
    og      = step.get("output_glob", "")

    if not multi:
        for out_path in outputs:
            p = cwd / out_path
            if not p.exists():
                incomplete.append({
                    "id":       sid,
                    "expected": out_path,
                    "reason":   "檔案不存在",
                    "severity": "HIGH",
                })
                break
    else:
        if og:
            matches = _glob.glob(str(cwd / og))
            if not matches:
                incomplete.append({
                    "id":       sid,
                    "expected": og,
                    "reason":   "無匹配檔案（期望 ≥ 1）",
                    "severity": "HIGH",
                })
        else:
            for out_path in outputs:
                d = cwd / out_path.rstrip("/")
                if not d.exists() or (d.is_dir() and not any(d.iterdir())):
                    incomplete.append({
                        "id":       sid,
                        "expected": out_path,
                        "reason":   "目錄不存在或為空",
                        "severity": "HIGH",
                    })
                    break

# Special: HTML — index.html 必存在 + ≥ 3 個 .html
if "HTML" in completed:
    pages_dir  = cwd / "docs/pages"
    html_count = len(list(pages_dir.glob("*.html"))) if pages_dir.exists() else 0
    index_ok   = (pages_dir / "index.html").exists()
    if not index_ok or html_count < 3:
        if not any(x["id"] == "HTML" for x in incomplete):
            incomplete.append({
                "id":       "HTML",
                "expected": "docs/pages/index.html + ≥3 .html",
                "reason":   f"HTML 頁面不足（共 {html_count} 個）",
                "severity": "MEDIUM",
            })

print(f"\n{'='*70}")
print(f"  語意輸出驗證（Output Completeness Check）")
print(f"  語意不完整步驟數：{len(incomplete)}")
print(f"{'='*70}\n")

print(f"SEMANTIC_INCOMPLETE_COUNT:{len(incomplete)}")

if incomplete:
    print(f"{'ID':<28} {'Sev':<8} {'期望輸出':<35} {'問題'}")
    print(f"{'-'*28} {'-'*8} {'-'*35} {'-'*25}")
    for item in incomplete:
        print(f"{item['id']:<28} {item['severity']:<8} {item['expected']:<35} {item['reason']}")
    print()
    for item in incomplete:
        print(f"SEMANTIC_INCOMPLETE:{item['id']}")
else:
    print("✅ 所有已完成步驟的輸出均驗證通過")
PY
```

**[AI 指令]** 從輸出中擷取：
- `_SEMANTIC_COUNT`：`SEMANTIC_INCOMPLETE_COUNT:N` 行的 N
- `_SEMANTIC_IDS`：所有 `SEMANTIC_INCOMPLETE:xxx` 行的 xxx，以逗號串接

---

## Step 2：若無缺漏且語意完整 → 結束

若 `_MISSING_COUNT == 0` 且 `_SEMANTIC_COUNT == 0`：

```
╔══════════════════════════════════════════════════════╗
║  /gendoc-repair 完成                                  ║
╠══════════════════════════════════════════════════════╣
║  ✅ 所有步驟已完成，輸出驗證通過，pipeline 完整無缺     ║
╚══════════════════════════════════════════════════════╝
```

輸出 `DONE`，結束。

若 `_MISSING_COUNT == 0` 但 `_SEMANTIC_COUNT > 0`（有步驟已記錄完成但輸出缺失）：
→ 設定 `_FIRST_MISSING` 為 `_SEMANTIC_IDS` 中的第一個 ID，繼續 Step 3。

---

## Step 3：若有缺漏或語意不完整 → 詢問是否補跑

`_SPAWNED == "true"` 時自動選 [1]（補跑），跳過提問。

否則用 `AskUserQuestion` 詢問（依狀況組合說明文字）：

```
[缺漏] 發現 {_MISSING_COUNT} 個未執行步驟，從 {_FIRST_MISSING} 開始。
[語意] 發現 {_SEMANTIC_COUNT} 個步驟已標記完成但輸出缺失：{_SEMANTIC_IDS}

（以上為實際有問題的行，若某項為 0 則省略該行）

要從 {_FIRST_MISSING} 補跑 gendoc-flow 嗎？

[1] 是，從 {_FIRST_MISSING} 補跑（設定 start_step 並呼叫 gendoc-flow）
[2] 否，只看報告，不補跑
```

補充：若 `_MISSING_COUNT == 0` 但 `_SEMANTIC_COUNT > 0`，說明文字改為：
```
發現 {_SEMANTIC_COUNT} 個步驟輸出缺失（{_SEMANTIC_IDS}）。
這些步驟在 state 中標記為已完成，但輸出檔案不存在或不完整。
建議從 {_FIRST_MISSING} 重新執行。
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
