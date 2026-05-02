---
name: gendoc-repair
description: Phase-aware backfill — 把不完整的目標專案補到與 gendoc-auto + gendoc-flow 從頭執行完全一致的狀態。分三區 diff（Phase A / DRYRUN Gate / Phase B）、DRYRUN 三態偵測、rules.json 品質驗證、兩階段補跑模式。
version: 2.0.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Skill
  - Agent
  - AskUserQuestion
---

# gendoc-repair — Phase-Aware Backfill

```
Input:   當前目錄的 .gendoc-state-*.json（或 .gendoc-state.json）
Output:  三區 diff 報告 + DRYRUN 狀態 + 品質驗證 + 可選的補跑
Purpose: 把任何不完整的目標專案補到與 gendoc-auto + gendoc-flow 從頭執行完全一致的狀態
```

Pipeline 相位邊界：
```
Phase A（內容層）                 Gate           Phase B（技術文件層）
IDEA BRD PRD CONSTANTS ... ARCH → DRYRUN → API SCHEMA ... HTML
                                      ↑
                         讀 EDD/PRD/ARCH → .gendoc-rules/*.json
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

## Step 1：Pipeline Diff 分析（Phase-Aware）

**[AI 指令]** 用 Python 計算差異，分三區輸出：Phase A（pre-DRYRUN）、DRYRUN Gate、Phase B（post-DRYRUN）：

```bash
python3 - "$_PIPELINE" "$_STATE_FILE" <<'PY'
import json, sys

pipeline_file = sys.argv[1]
state_file    = sys.argv[2]

pipe  = json.load(open(pipeline_file, encoding="utf-8"))
state = json.load(open(state_file, encoding="utf-8"))

completed   = set(state.get("completed_steps", []))
client_type = state.get("client_type", "unknown")
has_admin   = bool(state.get("has_admin_backend", False))

all_steps = []
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
        "layer": phase_name,
        "name":  step.get("name", step.get("type", "")),
        "type":  step.get("type", "standard"),
    })

# ── Phase boundary: split on DRYRUN ──
dryrun_idx   = next((i for i, s in enumerate(all_steps) if s["id"] == "DRYRUN"), None)
if dryrun_idx is not None:
    phase_a_all = all_steps[:dryrun_idx]
    phase_b_all = all_steps[dryrun_idx + 1:]
    dryrun_done = "DRYRUN" in completed
else:
    phase_a_all = all_steps
    phase_b_all = []
    dryrun_done = False

phase_a_missing = [s for s in phase_a_all if s["id"] not in completed]
phase_b_missing = [s for s in phase_b_all if s["id"] not in completed]
all_missing     = [s for s in all_steps   if s["id"] not in completed]
all_present     = [s for s in all_steps   if s["id"] in completed]

# ── Header ──
print(f"\n{'='*70}")
print(f"  Pipeline Diff 報告（Phase-Aware）")
print(f"  pipeline         : {pipeline_file.split('/')[-1]}")
print(f"  client_type      : {client_type}")
print(f"  has_admin_backend: {has_admin}")
print(f"  total steps      : {len(all_steps)}")
print(f"  completed        : {len(all_present)}")
print(f"  missing          : {len(all_missing)}")
print(f"{'='*70}\n")

# ── Phase A ──
a_sym = "✅ 完整" if not phase_a_missing else f"⚠️  缺 {len(phase_a_missing)} 個"
print(f"Phase A（內容層 — pre-DRYRUN）：{a_sym}")
if phase_a_missing:
    print(f"  {'ID':<26} {'Layer':<22} {'Name'}")
    print(f"  {'-'*26} {'-'*22} {'-'*28}")
    for s in phase_a_missing:
        print(f"  {s['id']:<26} {s['layer']:<22} {s['name']}")

# ── DRYRUN Gate ──
if dryrun_idx is not None:
    gate_sym = "✅ 已完成" if dryrun_done else "❌ 未執行"
    print(f"\nDRYRUN Gate（量化基線校準）：{gate_sym}")

# ── Phase B ──
b_sym = "✅ 完整" if not phase_b_missing else f"⚠️  缺 {len(phase_b_missing)} 個"
print(f"\nPhase B（技術文件層 — post-DRYRUN）：{b_sym}")
if phase_b_missing:
    print(f"  {'ID':<26} {'Layer':<22} {'Name'}")
    print(f"  {'-'*26} {'-'*22} {'-'*28}")
    for s in phase_b_missing:
        print(f"  {s['id']:<26} {s['layer']:<22} {s['name']}")

# ── Machine-readable markers ──
first_missing = all_missing[0]["id"]      if all_missing      else ""
first_phase_a = phase_a_missing[0]["id"]  if phase_a_missing  else ""
first_phase_b = phase_b_missing[0]["id"]  if phase_b_missing  else ""

print(f"\nMISSING_COUNT:{len(all_missing)}")
print(f"FIRST_MISSING:{first_missing}")
print(f"PHASE_A_MISSING_COUNT:{len(phase_a_missing)}")
print(f"PHASE_B_MISSING_COUNT:{len(phase_b_missing)}")
print(f"DRYRUN_GATE_DONE:{'true' if dryrun_done else 'false'}")
if first_phase_a:
    print(f"FIRST_PHASE_A:{first_phase_a}")
if first_phase_b:
    print(f"FIRST_PHASE_B:{first_phase_b}")
if not all_missing:
    print("✅ 所有 pipeline 步驟已完成，無需補跑。")
PY
```

**[AI 指令]** 從輸出中擷取：
- `_MISSING_COUNT`：`MISSING_COUNT:N` 行的 N
- `_FIRST_MISSING`：`FIRST_MISSING:xxx` 行的 xxx
- `_PHASE_A_MISSING_COUNT`：`PHASE_A_MISSING_COUNT:N` 行的 N
- `_PHASE_B_MISSING_COUNT`：`PHASE_B_MISSING_COUNT:N` 行的 N
- `_DRYRUN_GATE_DONE`：`DRYRUN_GATE_DONE:true|false` 行的值
- `_FIRST_PHASE_A`：`FIRST_PHASE_A:xxx` 行的 xxx（可能不存在）
- `_FIRST_PHASE_B`：`FIRST_PHASE_B:xxx` 行的 xxx（可能不存在）

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

## Step 1.5b：品質門檻驗證（rules.json）

若 `.gendoc-rules/` 存在，對已完成步驟驗 rules.json 品質門檻。若 DRYRUN 未跑（無 `.gendoc-rules/`），靜默跳過此區塊。

```bash
python3 - "$_PIPELINE" "$_STATE_FILE" "$_CWD" <<'PY'
import json, re, sys
from pathlib import Path

pipeline_file = sys.argv[1]
state_file    = sys.argv[2]
cwd           = Path(sys.argv[3])
rules_dir     = cwd / ".gendoc-rules"

if not rules_dir.exists():
    print("\n[Step 1.5b] .gendoc-rules/ 不存在，跳過品質門檻驗證（DRYRUN 未執行）")
    print("QUALITY_FAIL_COUNT:0")
    sys.exit(0)

state     = json.load(open(state_file, encoding="utf-8"))
completed = set(state.get("completed_steps", []))

quality_fails = []

PLACEHOLDER_RE = re.compile(r'\{\{[A-Z_]+\}\}')

for sid in sorted(completed):
    rules_file = rules_dir / f"{sid}-rules.json"
    if not rules_file.exists():
        continue
    try:
        rules = json.load(open(rules_file, encoding="utf-8"))
    except Exception:
        continue

    for spec in rules.get("output_files", []):
        path_str = spec.get("path", "")
        if not path_str:
            continue
        doc_path = cwd / path_str
        if not doc_path.exists():
            continue  # 檔案不存在由 Step 1.5 處理，這裡只驗品質

        try:
            content = doc_path.read_text(encoding="utf-8")
        except Exception:
            continue

        # 驗 min_h2_sections
        min_h2 = spec.get("min_h2_sections", 0)
        if min_h2:
            actual_h2 = len(re.findall(r'^## ', content, re.MULTILINE))
            if actual_h2 < min_h2:
                quality_fails.append({
                    "id": sid,
                    "check": "min_h2_sections",
                    "detail": f"有 {actual_h2} 個 ## 標題，需 ≥ {min_h2}",
                    "severity": "QUALITY_FAIL",
                })
                continue  # 一個 step 只報一次

        # 驗 required_sections
        for section in spec.get("required_sections", []):
            if section.lower() not in content.lower():
                quality_fails.append({
                    "id": sid,
                    "check": "required_sections",
                    "detail": f"缺少必要章節：{section}",
                    "severity": "QUALITY_FAIL",
                })
                break

        # 驗 no_placeholder_strings
        for rule in rules.get("anti_fake_rules", []):
            if rule.get("type") == "no_placeholder_strings":
                pattern = rule.get("pattern", r'\{\{[A-Z_]+\}\}')
                if re.search(pattern, content):
                    quality_fails.append({
                        "id": sid,
                        "check": "no_placeholder_strings",
                        "detail": f"文件含未填充的 placeholder（pattern: {pattern}）",
                        "severity": "QUALITY_FAIL",
                    })
                    break

print(f"\n{'='*70}")
print(f"  品質門檻驗證（rules.json Gate Check）")
print(f"  rules_dir  : {rules_dir}")
print(f"  QUALITY_FAIL 步驟數：{len(quality_fails)}")
print(f"{'='*70}\n")

print(f"QUALITY_FAIL_COUNT:{len(quality_fails)}")

if quality_fails:
    print(f"{'ID':<28} {'Check':<25} {'Detail'}")
    print(f"{'-'*28} {'-'*25} {'-'*35}")
    for item in quality_fails:
        print(f"{item['id']:<28} {item['check']:<25} {item['detail']}")
    print()
    for item in quality_fails:
        print(f"QUALITY_FAIL:{item['id']}")
else:
    print("✅ 所有已完成步驟通過 rules.json 品質門檻驗證")
PY
```

**[AI 指令]** 從輸出中擷取：
- `_QUALITY_FAIL_COUNT`：`QUALITY_FAIL_COUNT:N` 行的 N
- `_QUALITY_FAIL_IDS`：所有 `QUALITY_FAIL:xxx` 行的 xxx，以逗號串接

---

## Step 1.6：DRYRUN 三態偵測 + 上游就緒度 + 基線過時檢查

**[AI 指令]** 執行以下 bash，偵測 DRYRUN 狀態並擷取三個變數：`_DRYRUN_STATUS`、`_UPSTREAM_READY`、`_DRYRUN_STALE`。

```bash
# ── DRYRUN 三態偵測 ──
_DRYRUN_IN_COMPLETED=$(python3 -c "
import json
d = json.load(open('$_STATE_FILE', encoding='utf-8'))
print('true' if 'DRYRUN' in d.get('completed_steps', []) else 'false')
" 2>/dev/null || echo "false")

_RULES_COUNT=$(ls "$_CWD/.gendoc-rules/"*.json 2>/dev/null | wc -l | tr -d ' ')

# 偵測 DRYRUN 是否使用了預設值（MANIFEST.md 含 ⚠️ 預設值 或 used_defaults=true）
_DRYRUN_USED_DEFAULTS="false"
if [[ -f "$_CWD/docs/MANIFEST.md" ]]; then
  grep -qE '預設值|used_defaults.*true' "$_CWD/docs/MANIFEST.md" 2>/dev/null \
    && _DRYRUN_USED_DEFAULTS="true"
fi

if [[ "$_DRYRUN_IN_COMPLETED" == "false" ]]; then
  _DRYRUN_STATUS="NONE"
elif [[ "$_DRYRUN_USED_DEFAULTS" == "true" ]]; then
  _DRYRUN_STATUS="DEFAULTS"
else
  _DRYRUN_STATUS="OK"
fi

echo "[repair] DRYRUN_STATUS: $_DRYRUN_STATUS  rules_files: $_RULES_COUNT  used_defaults: $_DRYRUN_USED_DEFAULTS"
echo "DRYRUN_STATUS:$_DRYRUN_STATUS"
echo "DRYRUN_RULES_COUNT:$_RULES_COUNT"

# ── DRYRUN 上游就緒度預檢 ──
_ENTITY_COUNT=$(grep -c '^\s*class ' "$_CWD/docs/EDD.md" 2>/dev/null || echo "0")
_US_COUNT=$(grep -cE '^(## |### )US-' "$_CWD/docs/PRD.md" 2>/dev/null || echo "0")
_ARCH_LAYER_COUNT=$(grep -c '^| [A-Za-z]' "$_CWD/docs/ARCH.md" 2>/dev/null || echo "0")

_UPSTREAM_READY="true"
[[ "$_ENTITY_COUNT" -lt 3 ]] && _UPSTREAM_READY="false"
[[ "$_US_COUNT"     -lt 3 ]] && _UPSTREAM_READY="false"
[[ "$_ARCH_LAYER_COUNT" -lt 4 ]] && _UPSTREAM_READY="false"

echo "UPSTREAM_READY:$_UPSTREAM_READY"

if [[ "$_UPSTREAM_READY" == "false" ]]; then
  echo ""
  echo "⚠️  DRYRUN 上游文件就緒度不足（執行後品質基線可能偏鬆）："
  [[ "$_ENTITY_COUNT"    -lt 3 ]] && echo "    EDD：entity 定義 ${_ENTITY_COUNT} 個（建議 ≥ 3）"
  [[ "$_US_COUNT"        -lt 3 ]] && echo "    PRD：US-* 標題 ${_US_COUNT} 個（建議 ≥ 3）"
  [[ "$_ARCH_LAYER_COUNT" -lt 4 ]] && echo "    ARCH：Tech Stack 行 ${_ARCH_LAYER_COUNT} 個（建議 ≥ 4）"
fi

# ── DRYRUN 基線過時偵測（git 時間戳比對）──
_DRYRUN_STALE="false"
if [[ "$_DRYRUN_STATUS" != "NONE" ]] && [[ -d "$_CWD/.gendoc-rules" ]] && git -C "$_CWD" rev-parse --git-dir &>/dev/null; then
  _UPSTREAM_TS=$(git -C "$_CWD" log -1 --format="%at" -- \
    docs/EDD.md docs/PRD.md docs/ARCH.md 2>/dev/null || echo "0")
  _RULES_TS=$(git -C "$_CWD" log -1 --format="%at" -- \
    .gendoc-rules/ 2>/dev/null || echo "0")
  if [[ "$_UPSTREAM_TS" != "0" ]] && [[ "$_RULES_TS" != "0" ]] \
     && [[ "$_UPSTREAM_TS" -gt "$_RULES_TS" ]]; then
    _DRYRUN_STALE="true"
    _UPSTREAM_DATE=$(git -C "$_CWD" log -1 --format="%ai" -- \
      docs/EDD.md docs/PRD.md docs/ARCH.md 2>/dev/null || echo "?")
    _RULES_DATE=$(git -C "$_CWD" log -1 --format="%ai" -- \
      .gendoc-rules/ 2>/dev/null || echo "?")
    echo ""
    echo "⚠️  DRYRUN 基線可能過時："
    echo "    上游文件（EDD/PRD/ARCH）最新修改：$_UPSTREAM_DATE"
    echo "    .gendoc-rules/ 最後更新        ：$_RULES_DATE"
    echo "    建議重新執行 /gendoc-gen-dryrun 更新品質基線"
  fi
fi

echo "DRYRUN_STALE:$_DRYRUN_STALE"
```

**[AI 指令]** 從輸出中擷取：
- `_DRYRUN_STATUS`：`DRYRUN_STATUS:xxx` 行的 xxx（`NONE` / `DEFAULTS` / `OK`）
- `_DRYRUN_RULES_COUNT`：`DRYRUN_RULES_COUNT:N` 行的 N
- `_UPSTREAM_READY`：`UPSTREAM_READY:true|false` 行的值
- `_DRYRUN_STALE`：`DRYRUN_STALE:true|false` 行的值

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
