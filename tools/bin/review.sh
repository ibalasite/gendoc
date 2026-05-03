#!/bin/bash
################################################################################
# review.sh — Unified Quantitative & Content Validation Tool
#
# Purpose: Double-layer review for Phase B steps (AI review + quantitative checks)
# Usage:   review.sh --step API --specs-from-state .gendoc-state.json \
#            --target-file docs/API.md [--check MODE] [--output-format FORMAT] [--strict]
#
# Parameters:
#   --step STEP_ID              Step identifier (API, SCHEMA, FRONTEND, etc.)
#   --specs-from-state FILE     Path to .gendoc-state-*.json
#   --target-file FILE          Path to output file to validate
#   --check MODE                Check mode: quantitative|content_mapping|cross_file|all (default: all)
#   --output-format FORMAT      Output format: json|text (default: json)
#   --strict                    Treat warnings as errors
################################################################################

set -euo pipefail

# Color codes for text output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Global state
STEP_ID=""
STATE_FILE=""
TARGET_FILE=""
CHECK_MODE="all"
OUTPUT_FORMAT="json"
STRICT=false

# Findings array (JSON)
declare -a FINDINGS
FINDING_COUNT=0
CRITICAL_COUNT=0
HIGH_COUNT=0
MEDIUM_COUNT=0
LOW_COUNT=0
PASS_COUNT=0

################################################################################
# Utility Functions
################################################################################

log_error() {
  echo "[ERROR] $*" >&2
}

log_info() {
  if [[ "$OUTPUT_FORMAT" == "text" ]]; then
    echo "[INFO] $*"
  fi
}

add_finding() {
  local id=$1
  local type=$2
  local severity=$3
  local message=$4
  local expected=${5:-""}
  local actual=${6:-""}
  local suggested_fix=${7:-""}

  local finding_json=$(cat <<EOF
{
  "id": "$id",
  "type": "$type",
  "source": "quantitative_check",
  "severity": "$severity",
  "message": "$message",
  "expected": "$expected",
  "actual": "$actual",
  "suggested_fix": "$suggested_fix"
}
EOF
)

  FINDINGS+=("$finding_json")
  ((FINDING_COUNT++))

  case "$severity" in
    critical) ((CRITICAL_COUNT++)) ;;
    high) ((HIGH_COUNT++)) ;;
    medium) ((MEDIUM_COUNT++)) ;;
    low) ((LOW_COUNT++)) ;;
  esac
}

add_pass() {
  local id=$1
  local message=$2

  ((PASS_COUNT++))

  if [[ "$OUTPUT_FORMAT" == "text" ]]; then
    echo -e "${GREEN}✅ PASS${NC} $id: $message"
  fi
}

################################################################################
# Parameter Parsing
################################################################################

parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --step)
        STEP_ID="$2"
        shift 2
        ;;
      --specs-from-state)
        STATE_FILE="$2"
        shift 2
        ;;
      --target-file)
        TARGET_FILE="$2"
        shift 2
        ;;
      --check)
        CHECK_MODE="$2"
        shift 2
        ;;
      --output-format)
        OUTPUT_FORMAT="$2"
        shift 2
        ;;
      --strict)
        STRICT=true
        shift
        ;;
      *)
        log_error "Unknown parameter: $1"
        show_usage
        exit 1
        ;;
    esac
  done

  # Validate required parameters
  if [[ -z "$STEP_ID" ]] || [[ -z "$STATE_FILE" ]] || [[ -z "$TARGET_FILE" ]]; then
    log_error "Missing required parameters"
    show_usage
    exit 1
  fi

  # Validate file existence
  if [[ ! -f "$STATE_FILE" ]]; then
    log_error "State file not found: $STATE_FILE"
    exit 1
  fi

  if [[ ! -f "$TARGET_FILE" ]]; then
    log_error "Target file not found: $TARGET_FILE"
    exit 1
  fi
}

show_usage() {
  cat <<EOF
Usage: review.sh --step STEP_ID --specs-from-state STATE_FILE \\
                  --target-file TARGET_FILE [OPTIONS]

Options:
  --check MODE           Check mode: quantitative|content_mapping|cross_file|all
  --output-format FORMAT Output format: json|text
  --strict               Treat warnings as errors

Example:
  review.sh --step API --specs-from-state .gendoc-state.json \\
            --target-file docs/API.md --check all --output-format json
EOF
}

################################################################################
# Spec Extraction from State File
################################################################################

extract_spec() {
  local spec_type=$1  # quantitative_specs, content_mapping, or cross_file_validation

  python3 << PYTHON
import json
import sys

try:
  state = json.load(open("$STATE_FILE"))
  specs = state.get("step_specifications", {}).get("$STEP_ID", {})
  spec_value = specs.get("$spec_type", {})
  print(json.dumps(spec_value))
except Exception as e:
  print("{}")
  sys.exit(1)
PYTHON
}

################################################################################
# Quantitative Checks
################################################################################

run_quantitative_checks() {
  log_info "Running quantitative checks for $STEP_ID..."

  local specs_json
  specs_json=$(extract_spec "quantitative_specs")

  # Parse min_endpoint_count
  local min_endpoint_count
  min_endpoint_count=$(echo "$specs_json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('min_endpoint_count', 0))")

  if [[ "$min_endpoint_count" -gt 0 ]]; then
    check_endpoint_count "$min_endpoint_count"
  fi

  # Parse min_table_count
  local min_table_count
  min_table_count=$(echo "$specs_json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('min_table_count', 0))")

  if [[ "$min_table_count" -gt 0 ]]; then
    check_table_count "$min_table_count"
  fi

  # Parse min_component_count
  local min_component_count
  min_component_count=$(echo "$specs_json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('min_component_count', 0))")

  if [[ "$min_component_count" -gt 0 ]]; then
    check_component_count "$min_component_count"
  fi

  # Parse min_h2_sections
  local min_h2_sections
  min_h2_sections=$(echo "$specs_json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('min_h2_sections', 0))")

  if [[ "$min_h2_sections" -gt 0 ]]; then
    check_h2_sections "$min_h2_sections"
  fi

  # Parse min_row_count
  local min_row_count
  min_row_count=$(echo "$specs_json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('min_row_count', 0))")

  if [[ "$min_row_count" -gt 0 ]]; then
    check_row_count "$min_row_count"
  fi
}

check_endpoint_count() {
  local expected=$1
  local actual
  actual=$(grep -cE '^\s*\*\*[A-Z]+\*\*' "$TARGET_FILE" 2>/dev/null || echo "0")

  if [[ $actual -lt $expected ]]; then
    add_finding "QUANT-001" "quantitative" "high" \
      "API endpoint count insufficient" \
      "min: $expected" \
      "actual: $actual" \
      "Add missing endpoints from EDD specification"
  else
    add_pass "QUANT-001" "Endpoint count: $actual >= $expected ✓"
  fi
}

check_table_count() {
  local expected=$1
  local actual
  actual=$(grep -c '^\| [A-Z_]' "$TARGET_FILE" 2>/dev/null || echo "0")

  if [[ $actual -lt $expected ]]; then
    add_finding "QUANT-002" "quantitative" "high" \
      "Table count insufficient in SCHEMA" \
      "min: $expected" \
      "actual: $actual" \
      "Add database table definitions for missing entities"
  else
    add_pass "QUANT-002" "Table count: $actual >= $expected ✓"
  fi
}

check_component_count() {
  local expected=$1
  local actual
  actual=$(grep -c '^### [A-Z]' "$TARGET_FILE" 2>/dev/null || echo "0")

  if [[ $actual -lt $expected ]]; then
    add_finding "QUANT-003" "quantitative" "medium" \
      "Component count insufficient in FRONTEND" \
      "min: $expected" \
      "actual: $actual" \
      "Add missing UI component definitions"
  else
    add_pass "QUANT-003" "Component count: $actual >= $expected ✓"
  fi
}

check_h2_sections() {
  local expected=$1
  local actual
  actual=$(grep -c '^## ' "$TARGET_FILE" 2>/dev/null || echo "0")

  if [[ $actual -lt $expected ]]; then
    add_finding "QUANT-004" "quantitative" "medium" \
      "H2 section count insufficient" \
      "min: $expected" \
      "actual: $actual" \
      "Add missing major sections per test-plan requirements"
  else
    add_pass "QUANT-004" "H2 sections: $actual >= $expected ✓"
  fi
}

check_row_count() {
  local expected=$1
  local actual
  actual=$(grep -c '^\|' "$TARGET_FILE" 2>/dev/null || echo "0")

  if [[ $actual -lt $expected ]]; then
    add_finding "QUANT-005" "quantitative" "high" \
      "Table row count insufficient in RTM" \
      "min: $expected" \
      "actual: $actual" \
      "Add traceability rows for all user stories"
  else
    add_pass "QUANT-005" "Row count: $actual >= $expected ✓"
  fi
}

################################################################################
# Content Mapping Checks
################################################################################

run_content_mapping_checks() {
  log_info "Running content mapping checks for $STEP_ID..."

  local specs_json
  specs_json=$(extract_spec "content_mapping")

  # Check for bare placeholders (anti-fake rule)
  check_no_bare_placeholders

  # Check for minimum section words
  check_min_section_words

  # Check for duplicate paragraphs
  check_duplicate_paragraphs
}

check_no_bare_placeholders() {
  local count
  count=$(grep -o '{{[A-Z_]*}}' "$TARGET_FILE" 2>/dev/null | wc -l)

  if [[ $count -gt 0 ]]; then
    add_finding "CONTENT-001" "content_mapping" "critical" \
      "Bare placeholder strings found" \
      "0" \
      "$count" \
      "Replace all {{PLACEHOLDER}} with actual values from upstream documents"
  else
    add_pass "CONTENT-001" "No bare placeholders ✓"
  fi
}

check_min_section_words() {
  local section_count
  section_count=$(grep -c '^## \|^### ' "$TARGET_FILE" 2>/dev/null || echo "0")

  if [[ $section_count -eq 0 ]]; then
    add_finding "CONTENT-002" "content_mapping" "high" \
      "No sections found in document" \
      ">= 1" \
      "0" \
      "Add proper section headers (## or ###)"
  else
    add_pass "CONTENT-002" "Document has sections: $section_count ✓"
  fi
}

check_duplicate_paragraphs() {
  # Simple check: look for repeated lines (>= 150 chars)
  local dup_count
  dup_count=$(python3 << 'PYTHON'
import re

try:
  with open("$TARGET_FILE") as f:
    content = f.read()

  # Find paragraphs >= 150 chars
  paragraphs = re.split(r'\n\n+', content)
  long_paras = [p for p in paragraphs if len(p) >= 150]

  # Check for duplicates
  seen = set()
  dups = 0
  for p in long_paras:
    if p in seen:
      dups += 1
    else:
      seen.add(p)

  print(dups)
except:
  print(0)
PYTHON
)

  if [[ $dup_count -gt 0 ]]; then
    add_finding "CONTENT-003" "content_mapping" "high" \
      "Duplicate paragraphs detected" \
      "0" \
      "$dup_count" \
      "Remove duplicate content and replace with unique, meaningful text"
  else
    add_pass "CONTENT-003" "No duplicate paragraphs ✓"
  fi
}

################################################################################
# Cross-File Validation Checks
################################################################################

run_cross_file_checks() {
  log_info "Running cross-file validation checks for $STEP_ID..."

  # Entity parity check (if SCHEMA)
  if [[ "$STEP_ID" == "SCHEMA" ]]; then
    check_entity_parity
  fi

  # Endpoint mapping check (if API)
  if [[ "$STEP_ID" == "API" ]]; then
    check_endpoint_mapping
  fi

  # Story coverage check (if RTM or BDD)
  if [[ "$STEP_ID" == "RTM" ]] || [[ "$STEP_ID" == "BDD-server" ]]; then
    check_story_coverage
  fi
}

check_entity_parity() {
  # Verify SCHEMA references entities from EDD
  if [[ -f "docs/EDD.md" ]]; then
    local edd_entities
    edd_entities=$(grep -c '^\s*class ' "docs/EDD.md" 2>/dev/null || echo "0")

    local schema_tables
    schema_tables=$(grep -c '^\| [A-Z_]' "$TARGET_FILE" 2>/dev/null || echo "0")

    if [[ $schema_tables -lt $edd_entities ]]; then
      add_finding "CROSS-001" "cross_file" "high" \
        "SCHEMA table count does not match EDD entity count" \
        "edd_entities: $edd_entities" \
        "schema_tables: $schema_tables" \
        "Add schema definitions for all EDD entities"
    else
      add_pass "CROSS-001" "Entity parity: schema >= edd ✓"
    fi
  fi
}

check_endpoint_mapping() {
  # Verify API references endpoints from EDD
  if [[ -f "docs/EDD.md" ]]; then
    local edd_endpoints
    edd_endpoints=$(grep -cE '(<<REST>>|GET|POST|PUT|DELETE)' "docs/EDD.md" 2>/dev/null || echo "0")

    local api_endpoints
    api_endpoints=$(grep -c '^\*\*' "$TARGET_FILE" 2>/dev/null || echo "0")

    if [[ $api_endpoints -lt $edd_endpoints ]]; then
      add_finding "CROSS-002" "cross_file" "high" \
        "API endpoint count does not match EDD specification" \
        "edd_endpoints: $edd_endpoints" \
        "api_endpoints: $api_endpoints" \
        "Add all EDD REST endpoints to API documentation"
    else
      add_pass "CROSS-002" "Endpoint mapping: api >= edd ✓"
    fi
  fi
}

check_story_coverage() {
  # Verify RTM/BDD covers user stories from PRD
  if [[ -f "docs/PRD.md" ]]; then
    local prd_stories
    prd_stories=$(grep -c '^## US-\|^### US-' "docs/PRD.md" 2>/dev/null || echo "0")

    local doc_coverage
    doc_coverage=$(grep -c 'US-' "$TARGET_FILE" 2>/dev/null || echo "0")

    if [[ $doc_coverage -lt $prd_stories ]]; then
      add_finding "CROSS-003" "cross_file" "high" \
        "Story coverage incomplete" \
        "prd_stories: $prd_stories" \
        "coverage: $doc_coverage" \
        "Add traceability/scenarios for all user stories"
    else
      add_pass "CROSS-003" "Story coverage complete ✓"
    fi
  fi
}

################################################################################
# Output Formatting
################################################################################

output_findings_json() {
  local summary_json=$(cat <<EOF
{
  "step_id": "$STEP_ID",
  "target_file": "$TARGET_FILE",
  "check_mode": "$CHECK_MODE",
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "summary": {
    "total": $FINDING_COUNT,
    "critical": $CRITICAL_COUNT,
    "high": $HIGH_COUNT,
    "medium": $MEDIUM_COUNT,
    "low": $LOW_COUNT,
    "pass": $PASS_COUNT
  },
  "findings": [
EOF
)

  # Add individual findings
  for i in "${!FINDINGS[@]}"; do
    summary_json="${summary_json}${FINDINGS[$i]}"
    if [[ $i -lt ${#FINDINGS[@]}-1 ]]; then
      summary_json="${summary_json},"
    fi
    summary_json="${summary_json}"$'\n'
  done

  summary_json="${summary_json}]}"

  echo "$summary_json"
}

output_findings_text() {
  echo ""
  echo "================================"
  echo "Review Results: $STEP_ID"
  echo "================================"
  echo "File: $TARGET_FILE"
  echo "Check Mode: $CHECK_MODE"
  echo ""
  echo "Summary:"
  echo "  Total Findings: $FINDING_COUNT"
  echo "  CRITICAL: $CRITICAL_COUNT"
  echo "  HIGH: $HIGH_COUNT"
  echo "  MEDIUM: $MEDIUM_COUNT"
  echo "  LOW: $LOW_COUNT"
  echo "  PASS: $PASS_COUNT"
  echo ""

  if [[ $FINDING_COUNT -gt 0 ]]; then
    echo "Findings:"
    for finding_json in "${FINDINGS[@]}"; do
      local severity
      severity=$(echo "$finding_json" | python3 -c "import sys, json; print(json.load(sys.stdin)['severity'])")

      case "$severity" in
        critical) echo -e "${RED}❌ CRITICAL${NC}" ;;
        high) echo -e "${RED}⚠️  HIGH${NC}" ;;
        medium) echo -e "${YELLOW}⚠️  MEDIUM${NC}" ;;
        low) echo -e "${BLUE}ℹ️  LOW${NC}" ;;
      esac

      echo "$finding_json" | python3 -c "import sys, json; f=json.load(sys.stdin); print(f'  {f[\"id\"]}: {f[\"message\"]}')"
    done
  fi
  echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
  parse_args "$@"

  # Run checks based on mode
  case "$CHECK_MODE" in
    quantitative)
      run_quantitative_checks
      ;;
    content_mapping)
      run_content_mapping_checks
      ;;
    cross_file)
      run_cross_file_checks
      ;;
    all)
      run_quantitative_checks
      run_content_mapping_checks
      run_cross_file_checks
      ;;
    *)
      log_error "Unknown check mode: $CHECK_MODE"
      exit 1
      ;;
  esac

  # Output results
  if [[ "$OUTPUT_FORMAT" == "json" ]]; then
    output_findings_json
  else
    output_findings_text
  fi

  # Determine exit code
  if [[ $CRITICAL_COUNT -gt 0 ]]; then
    exit 2
  elif [[ $HIGH_COUNT -gt 0 ]] && [[ "$STRICT" == "true" ]]; then
    exit 1
  elif [[ $HIGH_COUNT -gt 0 ]]; then
    exit 0  # High findings don't block by default
  fi

  exit 0
}

main "$@"
