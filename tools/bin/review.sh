#!/bin/bash
################################################################################
# review.sh — Unified Quantitative & Content Validation Tool (Simplified)
################################################################################

set -u

STEP_ID=""
STATE_FILE=""
TARGET_FILE=""
CHECK_MODE="all"
OUTPUT_FORMAT="json"

# Findings counter
FINDINGS_JSON="[]"

while [[ $# -gt 0 ]]; do
  case $1 in
    --step) STEP_ID="$2"; shift 2 ;;
    --specs-from-state) STATE_FILE="$2"; shift 2 ;;
    --target-file) TARGET_FILE="$2"; shift 2 ;;
    --check) CHECK_MODE="$2"; shift 2 ;;
    --output-format) OUTPUT_FORMAT="$2"; shift 2 ;;
    --strict) shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$STEP_ID" ]] || [[ -z "$STATE_FILE" ]] || [[ -z "$TARGET_FILE" ]]; then
  echo "Error: Missing required parameters" >&2
  exit 1
fi

[[ ! -f "$STATE_FILE" ]] && echo "Error: State file not found" >&2 && exit 1
[[ ! -f "$TARGET_FILE" ]] && echo "Error: Target file not found" >&2 && exit 1

# Extract quantitative thresholds from state file
ENDPOINT_COUNT=$(grep -c '^\*\*' "$TARGET_FILE" 2>/dev/null || echo "0")
TABLE_COUNT=$(grep -c '^|' "$TARGET_FILE" 2>/dev/null || echo "0")
SECTION_COUNT=$(grep -c '^##' "$TARGET_FILE" 2>/dev/null || echo "0")

# Build findings JSON
CRITICAL=0
HIGH=0
PASS=0

# Check for placeholders
PLACEHOLDER_COUNT=$(grep -o '{{[^}]*}}' "$TARGET_FILE" 2>/dev/null | wc -l)
if [[ $PLACEHOLDER_COUNT -gt 0 ]]; then
  CRITICAL=$((CRITICAL + 1))
fi

# Check section count
if [[ $SECTION_COUNT -lt 3 ]]; then
  HIGH=$((HIGH + 1))
else
  PASS=$((PASS + 1))
fi

# Check endpoint count (for API)
if [[ "$STEP_ID" == "API" ]] && [[ $ENDPOINT_COUNT -lt 3 ]]; then
  HIGH=$((HIGH + 1))
else
  [[ "$STEP_ID" == "API" ]] && PASS=$((PASS + 1))
fi

# Output
if [[ "$OUTPUT_FORMAT" == "json" ]]; then
  cat <<EOF
{
  "step_id": "$STEP_ID",
  "target_file": "$TARGET_FILE",
  "summary": {
    "critical": $CRITICAL,
    "high": $HIGH,
    "pass": $PASS
  },
  "checks": {
    "placeholders": $PLACEHOLDER_COUNT,
    "sections": $SECTION_COUNT,
    "endpoints": $ENDPOINT_COUNT
  }
}
EOF
else
  echo "Review Results: $STEP_ID"
  echo "File: $TARGET_FILE"
  echo "Critical: $CRITICAL, High: $HIGH, Pass: $PASS"
fi

[[ $CRITICAL -gt 0 ]] && exit 2
[[ $HIGH -gt 0 ]] && exit 1
exit 0
