#!/bin/bash
################################################################################
# review_integration.sh
# TASK-F1: Integrates review.sh into gendoc-flow review loop
# Called by gendoc-flow Phase D-2 Step A-0 (Gate Check)
################################################################################

STEP_ID="$1"
TARGET_FILE="$2"
STATE_FILE="$3"
OUTPUT_FORMAT="${4:-json}"

# Resolve review.sh location
REVIEW_SH="${HOME}/.claude/skills/gendoc/tools/bin/review.sh"

if [[ ! -x "$REVIEW_SH" ]]; then
  echo "Error: review.sh not found at $REVIEW_SH" >&2
  echo "[]"
  exit 1
fi

# Run review.sh to get shell findings
SHELL_FINDINGS=$("$REVIEW_SH" \
  --step "$STEP_ID" \
  --specs-from-state "$STATE_FILE" \
  --target-file "$TARGET_FILE" \
  --check all \
  --output-format json 2>/dev/null || echo "{}")

# Extract summary from shell findings
CRITICAL=$(echo "$SHELL_FINDINGS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('summary', {}).get('critical', 0))" 2>/dev/null || echo "0")
HIGH=$(echo "$SHELL_FINDINGS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('summary', {}).get('high', 0))" 2>/dev/null || echo "0")

# Convert shell findings to AI findings format
MECHANICAL_FINDINGS=$(echo "$SHELL_FINDINGS" | python3 << 'PYTHON'
import sys, json

try:
  shell_result = json.load(sys.stdin)
  findings = []

  # Convert shell findings to findings list
  checks = shell_result.get('checks', {})
  if checks.get('placeholders', 0) > 0:
    findings.append({
      "id": "MECH-001",
      "source": "review.sh",
      "severity": "critical",
      "type": "mechanical",
      "message": f"Found {checks['placeholders']} bare placeholders",
      "suggested_fix": "Replace all {{PLACEHOLDER}} with actual values"
    })

  if checks.get('sections', 0) < 3:
    findings.append({
      "id": "MECH-002",
      "source": "review.sh",
      "severity": "high",
      "type": "mechanical",
      "message": f"Only {checks['sections']} sections (min 3 required)",
      "suggested_fix": "Add missing major sections"
    })

  print(json.dumps(findings))
except Exception as e:
  print(json.dumps([]))
PYTHON
)

# Output mechanical findings
echo "$MECHANICAL_FINDINGS"

# Return status based on criticality
if [[ $CRITICAL -gt 0 ]]; then
  exit 2
elif [[ $HIGH -gt 0 ]]; then
  exit 1
fi
exit 0
