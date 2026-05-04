#!/bin/bash
#
# review.sh — DRYRUN 機械式驗證工具
# 讀取 .gendoc-rules/*.json（期望）→ 測量 docs/*.md（實際）→ 機械比對所有量化指標
#
# 支援的指標類型：
#   min_*  → 實際值必須 >= 期望值（總量指標 + 深度指標）
#   max_*  → 實際值必須 <= 期望值（placeholder anti-fake）
#
# 用法：review.sh [project_dir]
#   project_dir 預設為當前目錄

set -euo pipefail

CWD="${1:-.}"
RULES_DIR="$CWD/.gendoc-rules"
DOCS_DIR="$CWD/docs"
REPORT_FILE="$DOCS_DIR/DRYRUN_REVIEW_REPORT.md"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log_pass() { echo -e "${GREEN}✓${NC} $1"; }
log_fail() { echo -e "${RED}✗${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }

# ─── 環境驗證 ────────────────────────────────────────────────────────────────

[[ -d "$RULES_DIR" ]] || { echo "ERROR: .gendoc-rules not found. Run DRYRUN first."; exit 1; }
[[ -d "$DOCS_DIR"  ]] || { echo "ERROR: docs/ directory not found at $DOCS_DIR"; exit 1; }

echo "======================================================"
echo "DRYRUN Review Tool — Mechanical Validation"
echo "======================================================"
echo "Rules : $RULES_DIR"
echo "Docs  : $DOCS_DIR"
echo ""

# ─── 簡單計量函式（grep 可完成）────────────────────────────────────────────────

measure_min_h2_sections()      { grep -c "^## " "$1" 2>/dev/null || true; }
measure_min_endpoint_count()   { grep -cE "^#### (GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) /" "$1" 2>/dev/null || true; }
measure_min_scenario_count()   { grep -c "^Scenario:" "$1" 2>/dev/null || true; }
measure_min_component_count()  { grep -c "^### " "$1" 2>/dev/null || true; }
measure_min_animation_defs()   { grep -c "^### " "$1" 2>/dev/null || true; }
measure_min_resource_entries() { grep -c "^### " "$1" 2>/dev/null || true; }
measure_max_placeholder_count(){ grep -c "{{" "$1" 2>/dev/null || true; }
measure_min_bgm_entries()      { grep -cEi "bgm|background.?music" "$1" 2>/dev/null || true; }
measure_min_sfx_entries()      { grep -cEi "sfx|sound.?effect" "$1" 2>/dev/null || true; }

measure_min_rbac_roles() {
  grep -cEi "^###.*[Rr]ole|^-\s.*[Rr]ole" "$1" 2>/dev/null || true
}

measure_min_table_count() {
  grep -cE "^\|[-| :]+\|" "$1" 2>/dev/null || true
}

measure_min_diagram_count() {
  python3 - "$1" <<'PYEOF'
import re, sys
content = open(sys.argv[1]).read()
mermaid = content.count('```mermaid')
images  = len(re.findall(r'!\[.*?\]\(', content))
print(mermaid + images)
PYEOF
}

measure_min_class_count() {
  grep -cE "^class [A-Z]|^\s+class [A-Z]" "$1" 2>/dev/null || true
}

measure_min_row_count() {
  python3 - "$1" <<'PYEOF'
import re, sys
lines = open(sys.argv[1]).read().splitlines()
data_rows = 0
prev_is_sep = False
for line in lines:
    if re.match(r'^\|[-| :]+\|', line):
        prev_is_sep = True
        continue
    if line.startswith('|'):
        if not prev_is_sep:
            data_rows += 1
    else:
        prev_is_sep = False
print(data_rows)
PYEOF
}

measure_min_rules_json_count() {
  find "$RULES_DIR" -maxdepth 1 -name "*.json" 2>/dev/null | wc -l | tr -d ' '
}

# ─── 深度計量函式（anti-fake：每個單元必須達到最低深度）───────────────────────

measure_min_fields_per_endpoint() {
  # 每個 endpoint block (#### METHOD /path) 中的 field 定義行數最小值
  python3 - "$1" <<'PYEOF'
import re, sys
content = open(sys.argv[1]).read()
blocks = re.split(r'^####\s+(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+/', content, flags=re.MULTILINE)
if len(blocks) <= 1:
    print(0); sys.exit()
counts = []
for block in blocks[1:]:
    body = block.split('\n####')[0]
    fields = re.findall(r'^[\-\*]\s+\w+|^\|\s*\w+|^\*\*\w+|\|\s*`\w+`', body, re.MULTILINE)
    counts.append(len(fields))
print(min(counts) if counts else 0)
PYEOF
}

measure_min_columns_per_table() {
  # 每個 table 的最少欄位數（anti-fake：不能只有 id 一欄）
  python3 - "$1" <<'PYEOF'
import re, sys
lines = open(sys.argv[1]).read().splitlines()
col_counts = []
for i, line in enumerate(lines):
    if re.match(r'^\|[-| :]+\|', line) and i > 0:
        header = lines[i - 1]
        cols = len([c for c in header.split('|') if c.strip()])
        if cols > 0:
            col_counts.append(cols)
print(min(col_counts) if col_counts else 0)
PYEOF
}

measure_min_steps_per_scenario() {
  # 每個 Scenario: block 中的 Given/When/Then/And/But 步驟最小數
  python3 - "$1" <<'PYEOF'
import re, sys
content = open(sys.argv[1]).read()
blocks = re.split(r'^Scenario:', content, flags=re.MULTILINE)
if len(blocks) <= 1:
    print(0); sys.exit()
counts = []
for block in blocks[1:]:
    steps = re.findall(r'^\s*(Given|When|Then|And|But)\s', block, re.MULTILINE)
    counts.append(len(steps))
print(min(counts) if counts else 0)
PYEOF
}

measure_min_lines_per_section() {
  # 每個 ## section 的非空內容行最小數（anti-fake：section 不能只有標題）
  python3 - "$1" <<'PYEOF'
import re, sys
content = open(sys.argv[1]).read()
blocks = re.split(r'^## .+', content, flags=re.MULTILINE)
if len(blocks) <= 1:
    print(0); sys.exit()
counts = []
for block in blocks[1:]:
    lines = [l for l in block.splitlines() if l.strip() and not l.startswith('#')]
    counts.append(len(lines))
print(min(counts) if counts else 0)
PYEOF
}

measure_min_columns_per_row() {
  # RTM 每個資料列的欄位數最小值
  python3 - "$1" <<'PYEOF'
import re, sys
lines = open(sys.argv[1]).read().splitlines()
col_counts = []
for line in lines:
    if line.startswith('|') and not re.match(r'^\|[-| :]+\|', line):
        cols = len([c for c in line.split('|') if c.strip()])
        if cols > 0:
            col_counts.append(cols)
print(min(col_counts) if col_counts else 0)
PYEOF
}

# ─── 分派函式 ─────────────────────────────────────────────────────────────────

IS_MAX_CONSTRAINT=0

dispatch_metric() {
  local key="$1" doc="$2"
  IS_MAX_CONSTRAINT=0
  case "$key" in
    min_h2_sections)           measure_min_h2_sections "$doc" ;;
    min_endpoint_count)        measure_min_endpoint_count "$doc" ;;
    min_table_count)           measure_min_table_count "$doc" ;;
    min_scenario_count)        measure_min_scenario_count "$doc" ;;
    min_component_count)       measure_min_component_count "$doc" ;;
    min_animation_defs)        measure_min_animation_defs "$doc" ;;
    min_rbac_roles)            measure_min_rbac_roles "$doc" ;;
    min_resource_entries)      measure_min_resource_entries "$doc" ;;
    min_row_count)             measure_min_row_count "$doc" ;;
    min_diagram_count)         measure_min_diagram_count "$doc" ;;
    min_class_count)           measure_min_class_count "$doc" ;;
    min_bgm_entries)           measure_min_bgm_entries "$doc" ;;
    min_sfx_entries)           measure_min_sfx_entries "$doc" ;;
    min_rules_json_count)      measure_min_rules_json_count ;;
    min_fields_per_endpoint)   measure_min_fields_per_endpoint "$doc" ;;
    min_columns_per_table)     measure_min_columns_per_table "$doc" ;;
    min_steps_per_scenario)    measure_min_steps_per_scenario "$doc" ;;
    min_lines_per_section)     measure_min_lines_per_section "$doc" ;;
    min_columns_per_row)       measure_min_columns_per_row "$doc" ;;
    max_placeholder_count)     IS_MAX_CONSTRAINT=1; measure_max_placeholder_count "$doc" ;;
    source|timestamp|step_id)  echo -2 ;;  # metadata fields, skip
    *)                         echo -1 ;;  # unknown metric
  esac
}

# ─── 主迴圈 ───────────────────────────────────────────────────────────────────

total_steps=0; passed_steps=0; failed_steps=0; skipped_steps=0
report_lines=()
report_lines+=("# DRYRUN Review Report")
report_lines+=("")
report_lines+=("**Generated**: $(date)")
report_lines+=("**Tool**: review.sh — Mechanical Validation")
report_lines+=("")
report_lines+=("## Results by Step")
report_lines+=("")

for rules_file in "$RULES_DIR"/*.json; do
  [[ -f "$rules_file" ]] || continue

  step_id=$(basename "$rules_file" -rules.json | tr '[:lower:]' '[:upper:]')

  # 找文件檔案（大寫或小寫均可）
  doc_file=""
  for candidate in \
    "$DOCS_DIR/${step_id}.md" \
    "$DOCS_DIR/$(echo "$step_id" | tr '[:upper:]' '[:lower:]').md"; do
    [[ -f "$candidate" ]] && { doc_file="$candidate"; break; }
  done

  # DRYRUN step：驗 .gendoc-rules/ 本身（min_rules_json_count）
  [[ "$step_id" == "DRYRUN" ]] && doc_file="$RULES_DIR/placeholder"

  if [[ -z "$doc_file" ]]; then
    log_warn "$step_id: 文件不存在 — 跳過"
    skipped_steps=$((skipped_steps + 1))
    report_lines+=("### $step_id — ⏭ SKIPPED (document not found)")
    report_lines+=("")
    continue
  fi

  total_steps=$((total_steps + 1))
  step_pass=1
  step_failures=()
  step_details=()

  # 逐一比對 rules JSON 中的每個指標
  while IFS='=' read -r key expected; do
    [[ -z "$key" || -z "$expected" ]] && continue

    actual=$(dispatch_metric "$key" "$doc_file" 2>/dev/null || echo -1)

    case "$actual" in
      -2) continue ;;  # metadata field, skip
      -1) step_details+=("  ⚠ $key: 未知指標，跳過"); continue ;;
    esac

    if [[ $IS_MAX_CONSTRAINT -eq 1 ]]; then
      if [[ $actual -le $expected ]]; then
        step_details+=("  ✓ ${key}: ${actual} ≤ ${expected}")
      else
        step_details+=("  ✗ ${key}: ${actual} > ${expected}  ← FAIL (${actual} placeholder(s) found)")
        step_failures+=("${key}:${actual}>${expected}")
        step_pass=0
      fi
    else
      if [[ $actual -ge $expected ]]; then
        step_details+=("  ✓ ${key}: ${actual} ≥ ${expected}")
      else
        step_details+=("  ✗ ${key}: ${actual} < ${expected}  ← FAIL")
        step_failures+=("${key}:${actual}<${expected}")
        step_pass=0
      fi
    fi
  done < <(jq -r 'to_entries[] | "\(.key)=\(.value)"' "$rules_file" 2>/dev/null)

  if [[ $step_pass -eq 1 ]]; then
    log_pass "$step_id: all metrics passed"
    passed_steps=$((passed_steps + 1))
    report_lines+=("### $step_id — ✅ PASS")
  else
    log_fail "$step_id: FAIL — ${step_failures[*]}"
    failed_steps=$((failed_steps + 1))
    report_lines+=("### $step_id — ❌ FAIL")
  fi

  report_lines+=("")
  for detail in "${step_details[@]}"; do
    report_lines+=("$detail")
  done
  report_lines+=("")
done

# ─── 報告輸出 ─────────────────────────────────────────────────────────────────

{
  for line in "${report_lines[@]}"; do echo "$line"; done
  echo "---"
  echo ""
  echo "## Summary"
  echo ""
  echo "- **Steps checked**: $total_steps"
  echo "- **Passed**: $passed_steps"
  echo "- **Failed**: $failed_steps"
  echo "- **Skipped** (doc missing): $skipped_steps"
  echo ""
  if [[ $failed_steps -eq 0 ]]; then
    echo "✅ **All mechanical validations passed**"
  else
    echo "❌ **${failed_steps} step(s) failed** — regenerate or fix the flagged documents"
  fi
} > "$REPORT_FILE"

echo ""
echo "======================================================"
printf "Checked: %d | Passed: %d | Failed: %d | Skipped: %d\n" \
  "$total_steps" "$passed_steps" "$failed_steps" "$skipped_steps"
echo "======================================================"
echo "Report: $REPORT_FILE"
echo ""

[[ $failed_steps -eq 0 ]] && exit 0 || exit 1
