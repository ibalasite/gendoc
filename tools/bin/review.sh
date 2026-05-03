#!/bin/bash
#
# review.sh — DRYRUN 審查工具（機械式驗證層）
# 對比 .gendoc-rules/*.json（期望）vs docs/*.md（實際）
# STEP 6: 審查工具實現 (DRYRUN_CORE_IMPLEMENTATION_PLAN.md)
#

set -e

CWD="${1:-.}"
RULES_DIR="$CWD/.gendoc-rules"
DOCS_DIR="$CWD/docs"
REPORT_FILE="$DOCS_DIR/DRYRUN_REVIEW_REPORT.md"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Utility functions
log_pass() { echo -e "${GREEN}✓${NC} $1"; }
log_fail() { echo -e "${RED}✗${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }

# Validate environment
if [[ ! -d "$RULES_DIR" ]]; then
  echo "ERROR: .gendoc-rules not found. Run DRYRUN first."
  exit 1
fi

if [[ ! -d "$DOCS_DIR" ]]; then
  echo "ERROR: docs directory not found at $DOCS_DIR"
  exit 1
fi

echo "======================================================"
echo "DRYRUN Review Tool (Mechanical Validation)"
echo "======================================================"
echo "Rules: $RULES_DIR"
echo "Docs: $DOCS_DIR"
echo ""

# Initialize counters
total_steps=0
passed_steps=0
failed_steps=0
warn_steps=0

# Initialize report
report_lines=()
report_lines+=("# DRYRUN Review Report")
report_lines+=("")
report_lines+=("**Generated**: $(date)")
report_lines+=("**Tool**: review.sh (Mechanical Validation)")
report_lines+=("")
report_lines+=("## Validation Results")
report_lines+=("")
report_lines+=("|Step|Expected|Actual|Status|")
report_lines+=("|----|--------|------|------|")

# Process each rules file
for rules_file in "$RULES_DIR"/*.json; do
    [[ ! -f "$rules_file" ]] && continue

    step_id=$(basename "$rules_file" -rules.json | tr '[:lower:]' '[:upper:]')
    total_steps=$((total_steps + 1))

    # Read expected value (try different keys)
    expected=$(jq -r '.min_h2_sections // .min_endpoint_count // .min_table_count // .min_scenario_count // 0' "$rules_file" 2>/dev/null || echo "0")

    # Find doc file
    doc_file="$DOCS_DIR/${step_id}.md"

    if [[ ! -f "$doc_file" ]]; then
        log_fail "$step_id: Document not found"
        report_lines+=("| $step_id | $expected | ❌ Missing | FAIL |")
        failed_steps=$((failed_steps + 1))
        continue
    fi

    # Count actual occurrences based on expected key
    if jq -e '.min_h2_sections' "$rules_file" &>/dev/null; then
        actual=$(grep -c "^## " "$doc_file" || echo "0")
        metric="H2 sections"
    elif jq -e '.min_endpoint_count' "$rules_file" &>/dev/null; then
        actual=$(grep -oE "(GET|POST|PUT|DELETE|PATCH) /" "$doc_file" 2>/dev/null | sort -u | wc -l || echo "0")
        metric="Endpoints"
    elif jq -e '.min_table_count' "$rules_file" &>/dev/null; then
        actual=$(grep -c "^|" "$doc_file" 2>/dev/null || echo "0")
        metric="Tables"
    elif jq -e '.min_scenario_count' "$rules_file" &>/dev/null; then
        actual=$(grep -c "Scenario:" "$doc_file" 2>/dev/null || echo "0")
        metric="Scenarios"
    else
        log_warn "$step_id: Unknown rule type"
        report_lines+=("| $step_id | ? | ? | WARN |")
        warn_steps=$((warn_steps + 1))
        continue
    fi

    # Compare
    if [[ $actual -ge $expected ]]; then
        log_pass "$step_id ($metric): $actual >= $expected"
        report_lines+=("| $step_id | $expected | $actual | ✅ PASS |")
        passed_steps=$((passed_steps + 1))
    else
        log_fail "$step_id ($metric): $actual < $expected"
        report_lines+=("| $step_id | $expected | $actual | ❌ FAIL |")
        failed_steps=$((failed_steps + 1))
    fi
done

# Write report to file
{
    for line in "${report_lines[@]}"; do
        echo "$line"
    done
    echo ""
    echo "## Summary"
    echo ""
    echo "- **Total steps**: $total_steps"
    echo "- **Passed**: $passed_steps"
    echo "- **Failed**: $failed_steps"
    echo "- **Warnings**: $warn_steps"
    echo ""

    if [[ $failed_steps -eq 0 ]]; then
        echo "✅ **All mechanical validations passed**"
    else
        echo "❌ **$failed_steps step(s) failed validation**"
        echo ""
        echo "### Failed Steps"
        echo ""
        echo "Run corresponding fix or regeneration for each failed step."
    fi
} > "$REPORT_FILE"

echo ""
echo "======================================================"
echo "Summary:"
printf "  Total: %d | Passed: %d | Failed: %d | Warnings: %d\n" \
  "$total_steps" "$passed_steps" "$failed_steps" "$warn_steps"
echo "======================================================"

# Exit code
if [[ $failed_steps -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ All reviews passed!${NC}"
    echo "Report: $REPORT_FILE"
    exit 0
else
    echo ""
    echo -e "${RED}❌ $failed_steps step(s) failed review${NC}"
    echo "Report: $REPORT_FILE"
    exit 1
fi
