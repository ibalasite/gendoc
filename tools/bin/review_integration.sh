#!/bin/bash
#
# review_integration.sh — Per-step mechanical gate check for gendoc-flow Phase D-2
#
# 讀取 .gendoc-rules/{STEP_ID}-rules.json → 量測 TARGET_FILE → 回傳 JSON findings array
#
# 使用方式（由 gendoc-flow Gate Check 呼叫）：
#   review_integration.sh STEP_ID TARGET_FILE [STATE_FILE] [AI_FINDINGS] [OUTPUT_FORMAT]
#
# 注意：STATE_FILE / AI_FINDINGS 參數保留簽名相容性，但已不使用。
#   STATE_FILE 已由 .gendoc-rules/*.json 取代（DRYRUN 寫出）
#   AI_FINDINGS 由 gendoc-flow 自行合併，不在此處理
#
# 回傳：JSON array of failing metric findings（CRITICAL 嚴重度）
#       若無違規或無 rules 檔 → 回傳 []

set -u

STEP_ID="${1:-}"
TARGET_FILE="${2:-}"
# STATE_FILE="${3:-}"   # 已廢棄，specs 來自 .gendoc-rules/
# AI_FINDINGS="${4:-}"  # 不處理，由 gendoc-flow 合併
# OUTPUT_FORMAT="${5:-json}"  # 保留簽名相容性

if [[ -z "$STEP_ID" ]] || [[ -z "$TARGET_FILE" ]]; then
  echo "[]"; exit 0
fi

if [[ ! -f "$TARGET_FILE" ]]; then
  echo "[]"; exit 0
fi

# 從 TARGET_FILE 推導 project_dir（TARGET_FILE 在 docs/ 下）
TARGET_DIR=$(dirname "$TARGET_FILE")
PROJECT_DIR=$(dirname "$TARGET_DIR")
RULES_DIR="$PROJECT_DIR/.gendoc-rules"

# 找 rules 檔（大小寫均可）
RULES_FILE=""
for candidate in \
  "$RULES_DIR/$(echo "$STEP_ID" | tr '[:upper:]' '[:lower:]')-rules.json" \
  "$RULES_DIR/$(echo "$STEP_ID" | tr '[:lower:]' '[:upper:]')-rules.json"; do
  [[ -f "$candidate" ]] && { RULES_FILE="$candidate"; break; }
done

if [[ -z "$RULES_FILE" ]]; then
  # DRYRUN 尚未執行，無 rules 檔 → gate 跳過
  echo "[]"; exit 0
fi

# 量測所有指標，回傳 JSON findings array
python3 - "$STEP_ID" "$TARGET_FILE" "$RULES_FILE" <<'PYEOF'
import sys, json, re

step_id  = sys.argv[1]
doc_file = sys.argv[2]
rules_file = sys.argv[3]

try:
    rules = json.load(open(rules_file))
except Exception:
    print("[]"); sys.exit(0)

try:
    content = open(doc_file).read()
    lines   = content.splitlines()
except Exception:
    print("[]"); sys.exit(0)

SKIP_KEYS = {'source', 'timestamp', 'step_id'}

def measure(key: str, content: str, lines: list) -> int:
    if key == 'min_h2_sections':
        return sum(1 for l in lines if l.startswith('## '))
    if key == 'min_endpoint_count':
        return sum(1 for l in lines if re.match(r'^#### (GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) /', l))
    if key == 'min_scenario_count':
        return sum(1 for l in lines if l.startswith('Scenario:'))
    if key in ('min_component_count', 'min_animation_defs', 'min_resource_entries'):
        return sum(1 for l in lines if l.startswith('### '))
    if key == 'max_placeholder_count':
        return content.count('{{')
    if key == 'min_bgm_entries':
        return len(re.findall(r'(?i)bgm|background.?music', content))
    if key == 'min_sfx_entries':
        return len(re.findall(r'(?i)sfx|sound.?effect', content))
    if key == 'min_rbac_roles':
        return sum(1 for l in lines if re.match(r'(?i)^###.*[Rr]ole|^-\s.*[Rr]ole', l))
    if key == 'min_table_count':
        return sum(1 for l in lines if re.match(r'^\|[-| :]+\|', l))
    if key == 'min_diagram_count':
        return content.count('```mermaid') + len(re.findall(r'!\[.*?\]\(', content))
    if key == 'min_class_count':
        return sum(1 for l in lines if re.match(r'^class [A-Z]|^\s+class [A-Z]', l))
    if key == 'min_row_count':
        count, prev_sep = 0, False
        for l in lines:
            if re.match(r'^\|[-| :]+\|', l): prev_sep = True; continue
            if l.startswith('|') and not prev_sep: count += 1
            else: prev_sep = False
        return count
    if key == 'min_fields_per_endpoint':
        blocks = re.split(r'^####\s+(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+/', content, flags=re.MULTILINE)
        if len(blocks) <= 1: return 0
        counts = []
        for block in blocks[1:]:
            body = block.split('\n####')[0]
            counts.append(len(re.findall(r'^[\-\*]\s+\w+|^\|\s*\w+|^\*\*\w+|\|\s*`\w+`', body, re.MULTILINE)))
        return min(counts) if counts else 0
    if key == 'min_columns_per_table':
        col_counts = []
        for i, l in enumerate(lines):
            if re.match(r'^\|[-| :]+\|', l) and i > 0:
                cols = len([c for c in lines[i-1].split('|') if c.strip()])
                if cols > 0: col_counts.append(cols)
        return min(col_counts) if col_counts else 0
    if key == 'min_steps_per_scenario':
        blocks = re.split(r'^Scenario:', content, flags=re.MULTILINE)
        if len(blocks) <= 1: return 0
        counts = [len(re.findall(r'^\s*(Given|When|Then|And|But)\s', b, re.MULTILINE)) for b in blocks[1:]]
        return min(counts) if counts else 0
    if key == 'min_lines_per_section':
        blocks = re.split(r'^## .+', content, flags=re.MULTILINE)
        if len(blocks) <= 1: return 0
        counts = [len([l for l in b.splitlines() if l.strip() and not l.startswith('#')]) for b in blocks[1:]]
        return min(counts) if counts else 0
    if key == 'min_columns_per_row':
        col_counts = []
        for l in lines:
            if l.startswith('|') and not re.match(r'^\|[-| :]+\|', l):
                cols = len([c for c in l.split('|') if c.strip()])
                if cols > 0: col_counts.append(cols)
        return min(col_counts) if col_counts else 0
    return -1  # 未知指標

findings = []
idx = 0

for key, expected in rules.items():
    if key in SKIP_KEYS:
        continue
    if not isinstance(expected, (int, float)):
        continue
    expected = int(expected)

    actual = measure(key, content, lines)
    if actual == -1:
        continue  # 未知指標，跳過

    is_max = key.startswith('max_')
    passed = (actual <= expected) if is_max else (actual >= expected)

    if not passed:
        idx += 1
        op = f"{actual} > {expected}" if is_max else f"{actual} < {expected}"
        findings.append({
            "id": f"MECH-{idx:03d}",
            "severity": "CRITICAL",
            "source": "review.sh",
            "type": "mechanical",
            "check": key,
            "message": f"[{step_id}] {key}: {op}",
            "suggested_fix": f"{'Reduce' if is_max else 'Increase'} {key} (currently {actual}, threshold {expected})"
        })

print(json.dumps(findings, ensure_ascii=False, indent=2))
PYEOF
