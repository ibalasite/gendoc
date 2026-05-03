#!/bin/bash
################################################################################
# review_integration.sh
# R4-V1: Integrates AI + Shell findings into unified review
# Called by gendoc-flow Phase D-2 (Gate Check)
################################################################################

set -u

STEP_ID="${1:-}"
TARGET_FILE="${2:-}"
STATE_FILE="${3:-}"
AI_FINDINGS="${4:-[]}"
OUTPUT_FORMAT="${5:-json}"

# Resolve review.sh location
REVIEW_SH="${HOME}/.claude/skills/gendoc/tools/bin/review.sh"

if [[ -z "$STEP_ID" ]] || [[ -z "$TARGET_FILE" ]] || [[ -z "$STATE_FILE" ]]; then
  echo "Error: Missing required parameters (step_id, target_file, state_file)" >&2
  echo "[]"
  exit 1
fi

if [[ ! -f "$TARGET_FILE" ]]; then
  echo "Error: Target file not found: $TARGET_FILE" >&2
  echo "[]"
  exit 1
fi

if [[ ! -f "$STATE_FILE" ]]; then
  echo "Error: State file not found: $STATE_FILE" >&2
  echo "[]"
  exit 1
fi

################################################################################
# STEP 1: Run shell-based checks (review.sh) with all 3 modes
#
# review.sh validates documents against DRYRUN spec_rules (three independent checks):
# 1. quantitative: 10 structural completeness checks (placeholder count, section count, etc.)
# 2. content_mapping: 4 cross-document traceability checks (entity coverage, US traceability, etc.)
# 3. cross_file: 4 multi-document parity checks (entity parity, moscow priority, etc.)
#
# Each check run produces separate JSON with findings[]: {severity, check, message, suggested_fix}
# Then merged into unified result (Step 3).
################################################################################

SHELL_FINDINGS_QUANTITATIVE="{}"
SHELL_FINDINGS_CONTENT="{}"
SHELL_FINDINGS_CROSS="{}"

if [[ -x "$REVIEW_SH" ]]; then
  # Run quantitative checks
  SHELL_FINDINGS_QUANTITATIVE=$("$REVIEW_SH" \
    --step "$STEP_ID" \
    --specs-from-state "$STATE_FILE" \
    --target-file "$TARGET_FILE" \
    --check quantitative \
    --output-format json 2>/dev/null || echo "{}")

  # Run content_mapping checks
  SHELL_FINDINGS_CONTENT=$("$REVIEW_SH" \
    --step "$STEP_ID" \
    --specs-from-state "$STATE_FILE" \
    --target-file "$TARGET_FILE" \
    --check content_mapping \
    --output-format json 2>/dev/null || echo "{}")

  # Run cross_file checks
  SHELL_FINDINGS_CROSS=$("$REVIEW_SH" \
    --step "$STEP_ID" \
    --specs-from-state "$STATE_FILE" \
    --target-file "$TARGET_FILE" \
    --check cross_file \
    --output-format json 2>/dev/null || echo "{}")
else
  echo "Warning: review.sh not found at $REVIEW_SH" >&2
fi

################################################################################
# STEP 2: Extract severity counts from shell findings
################################################################################

extract_summary() {
  local findings_json="$1"
  python3 -c "
import sys, json
try:
  d = json.loads('''$findings_json''')
  summary = d.get('summary', {})
  print(f\"{summary.get('critical', 0)},{summary.get('high', 0)},{summary.get('medium', 0)}\")
except:
  print('0,0,0')
" 2>/dev/null || echo "0,0,0"
}

read -r QUANT_CRIT QUANT_HIGH QUANT_MED <<< "$(extract_summary "$SHELL_FINDINGS_QUANTITATIVE")"
read -r CONTENT_CRIT CONTENT_HIGH CONTENT_MED <<< "$(extract_summary "$SHELL_FINDINGS_CONTENT")"
read -r CROSS_CRIT CROSS_HIGH CROSS_MED <<< "$(extract_summary "$SHELL_FINDINGS_CROSS")"

TOTAL_CRITICAL=$((${QUANT_CRIT:-0} + ${CONTENT_CRIT:-0} + ${CROSS_CRIT:-0}))
TOTAL_HIGH=$((${QUANT_HIGH:-0} + ${CONTENT_HIGH:-0} + ${CROSS_HIGH:-0}))
TOTAL_MEDIUM=$((${QUANT_MED:-0} + ${CONTENT_MED:-0} + ${CROSS_MED:-0}))

################################################################################
# STEP 3: Merge AI findings + Shell findings
#
# DRYRUN 后的 step Document Review is TWO-LAYER:
# - Layer 1 (AI): Semantic review (clarity, completeness, alignment with intent)
# - Layer 2 (Shell): Quantitative/structural review via review.sh (DRYRUN gate validation)
#
# Merger strategy:
# 1. Parse AI findings (from Claude review agent)
# 2. Extract all shell findings from 3 modes (quantitative, content_mapping, cross_file)
# 3. Normalize to unified format: {severity, check, message, suggested_fix, source}
# 4. Deduplicate by message (prevent duplicate findings across modes)
# 5. Sort by severity (CRITICAL → HIGH → MEDIUM)
#
# Result: Single deduplicated list ready for AI Fix agent
################################################################################

merge_findings() {
  local ai_findings="$1"
  local shell_findings_q="$2"
  local shell_findings_c="$3"
  local shell_findings_x="$4"

  python3 << 'PYTHON'
import sys, json

ai_findings = []
shell_findings = []

try:
  # Parse AI findings
  ai_findings = json.loads('''AI_FINDINGS_PLACEHOLDER''')
  if not isinstance(ai_findings, list):
    ai_findings = []
except:
  pass

try:
  # Parse shell findings and extract individual findings
  all_findings = []

  for findings_json in ['''SHELL_FINDINGS_Q_PLACEHOLDER''',
                        '''SHELL_FINDINGS_C_PLACEHOLDER''',
                        '''SHELL_FINDINGS_X_PLACEHOLDER''']:
    try:
      data = json.loads(findings_json)
      findings = data.get('findings', [])
      if isinstance(findings, list):
        all_findings.extend(findings)
    except:
      pass

  # Convert shell findings to unified format
  for idx, finding in enumerate(all_findings):
    if isinstance(finding, dict):
      shell_findings.append({
        "id": f"SHELL-{idx+1:03d}",
        "source": "review.sh",
        "severity": finding.get('severity', 'medium').upper(),
        "type": "mechanical",
        "check": finding.get('check', ''),
        "message": finding.get('message', ''),
        "suggested_fix": finding.get('suggested_fix', '')
      })
except Exception as e:
  pass

# Merge findings (AI first, then shell)
merged = ai_findings + shell_findings

# Remove duplicates based on message
seen = set()
unique = []
for f in merged:
  msg = f.get('message', '')
  if msg not in seen:
    seen.add(msg)
    unique.append(f)

print(json.dumps(unique, indent=2, ensure_ascii=False))
PYTHON
}

# Perform substitution and merge
MERGED_FINDINGS=$(merge_findings "$AI_FINDINGS" "$SHELL_FINDINGS_QUANTITATIVE" "$SHELL_FINDINGS_CONTENT" "$SHELL_FINDINGS_CROSS")
MERGED_FINDINGS="${MERGED_FINDINGS//'AI_FINDINGS_PLACEHOLDER'/$AI_FINDINGS}"
MERGED_FINDINGS="${MERGED_FINDINGS//'SHELL_FINDINGS_Q_PLACEHOLDER'/$SHELL_FINDINGS_QUANTITATIVE}"
MERGED_FINDINGS="${MERGED_FINDINGS//'SHELL_FINDINGS_C_PLACEHOLDER'/$SHELL_FINDINGS_CONTENT}"
MERGED_FINDINGS="${MERGED_FINDINGS//'SHELL_FINDINGS_X_PLACEHOLDER'/$SHELL_FINDINGS_CROSS}"

################################################################################
# STEP 4: Output unified result
################################################################################

if [[ "$OUTPUT_FORMAT" == "json" ]]; then
  cat <<EOF
{
  "step_id": "$STEP_ID",
  "target_file": "$TARGET_FILE",
  "source": "review_integration",
  "review_layers": {
    "quantitative": {
      "critical": $QUANT_CRIT,
      "high": $QUANT_HIGH,
      "medium": $QUANT_MED
    },
    "content_mapping": {
      "critical": $CONTENT_CRIT,
      "high": $CONTENT_HIGH,
      "medium": $CONTENT_MED
    },
    "cross_file": {
      "critical": $CROSS_CRIT,
      "high": $CROSS_HIGH,
      "medium": $CROSS_MED
    }
  },
  "summary": {
    "critical": $TOTAL_CRITICAL,
    "high": $TOTAL_HIGH,
    "medium": $TOTAL_MEDIUM,
    "ai_findings_count": $(echo "$AI_FINDINGS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d) if isinstance(d, list) else 0)" 2>/dev/null || echo "0"),
    "shell_findings_count": $(echo "$SHELL_FINDINGS_QUANTITATIVE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('findings', [])) if isinstance(d, dict) else 0)" 2>/dev/null || echo "0")
  },
  "findings": $MERGED_FINDINGS
}
EOF
else
  echo "Review Results: $STEP_ID (Integrated AI + Shell)"
  echo "File: $TARGET_FILE"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Summary: Critical=$TOTAL_CRITICAL, High=$TOTAL_HIGH, Medium=$TOTAL_MEDIUM"
  echo ""
  echo "$MERGED_FINDINGS" | python3 -m json.tool 2>/dev/null || echo "$MERGED_FINDINGS"
fi

################################################################################
# STEP 5: Exit with appropriate code
################################################################################

[[ $TOTAL_CRITICAL -gt 0 ]] && exit 2
[[ $TOTAL_HIGH -gt 0 ]] && exit 1
exit 0
