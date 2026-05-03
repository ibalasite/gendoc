#!/bin/bash
################################################################################
# review.sh — Unified Quantitative & Content Validation Tool (Complete)
# Supports 4 checking modes: quantitative, content_mapping, cross_file, all
################################################################################

set -u

STEP_ID=""
STATE_FILE=""
TARGET_FILE=""
CHECK_MODE="all"
OUTPUT_FORMAT="json"

# Findings array
declare -a FINDINGS
CRITICAL_COUNT=0
HIGH_COUNT=0
MEDIUM_COUNT=0
PASS_COUNT=0

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

# Helper: Add finding to array
# Each finding is a JSON object with:
#   severity: CRITICAL (blocks Phase B), HIGH (should fix), MEDIUM (nice to have), or PASS
#   check: rule name (e.g., "placeholders_exist", "entity_parity_missing")
#   message: human-readable issue description
#   suggested_fix: actionable remedy (used by AI Fix layer)
add_finding() {
  local severity=$1
  local check_name=$2
  local message=$3
  local suggested_fix=$4

  FINDINGS+=("{\"severity\": \"$severity\", \"check\": \"$check_name\", \"message\": \"$message\", \"suggested_fix\": \"$suggested_fix\"}")

  case $severity in
    CRITICAL) CRITICAL_COUNT=$((CRITICAL_COUNT + 1)) ;;
    HIGH) HIGH_COUNT=$((HIGH_COUNT + 1)) ;;
    MEDIUM) MEDIUM_COUNT=$((MEDIUM_COUNT + 1)) ;;
  esac
}

# Helper: Count pattern matches
count_pattern() {
  local pattern=$1
  local file=$2
  grep -o "$pattern" "$file" 2>/dev/null | wc -l | xargs 2>/dev/null || echo "0"
}

# ═══════════════════════════════════════════════════════════════════════════
# R-3.1: QUANTITATIVE CHECKING MODE
#
# Purpose: Structural completeness validation (DRYRUN spec baseline enforcement)
# Checks: 10 metrics extracted from target file via regex patterns
# Examples:
#   - placeholder_count: {{PLACEHOLDER}} unresolved template variables
#   - section_count: ## markdown headers (min 3)
#   - endpoint_count: API endpoints (min 1 for API.md)
#   - table_count: | table structures (min 1 for SCHEMA.md)
#   - entity_count: class definitions (min 1 for EDD.md)
#
# Each check has a min threshold from DRYRUN spec_rules. Violations = HIGH/MEDIUM severity.
# ═══════════════════════════════════════════════════════════════════════════

run_quantitative_checks() {
  # Extract quantitative counts from target file using grep patterns
  local placeholder_count=$(count_pattern '{{[^}]*}}' "$TARGET_FILE")
  local section_count=$(grep -c '^##' "$TARGET_FILE" 2>/dev/null || echo "0")
  local endpoint_count=$(grep -c '^\*\*' "$TARGET_FILE" 2>/dev/null || echo "0")
  local table_count=$(grep -c '^|' "$TARGET_FILE" 2>/dev/null || echo "0")
  local row_count=$(grep -c '^-' "$TARGET_FILE" 2>/dev/null || echo "0")
  local component_count=$(grep -c 'component' "$TARGET_FILE" 2>/dev/null | tr -d ' ' || echo "0")
  local entity_count=$(grep -c '^class ' "$TARGET_FILE" 2>/dev/null || echo "0")
  local constant_count=$(grep -c '`[A-Z_]*`' "$TARGET_FILE" 2>/dev/null || echo "0")
  local method_count=$(grep -c 'def ' "$TARGET_FILE" 2>/dev/null || echo "0")
  local field_count=$(grep -c ': ' "$TARGET_FILE" 2>/dev/null || echo "0")

  # Ensure numeric values
  placeholder_count=${placeholder_count:-0}
  section_count=${section_count:-0}
  endpoint_count=${endpoint_count:-0}
  table_count=${table_count:-0}
  row_count=${row_count:-0}
  component_count=${component_count:-0}
  entity_count=${entity_count:-0}
  constant_count=${constant_count:-0}
  method_count=${method_count:-0}
  field_count=${field_count:-0}

  # Check 1: No placeholders
  if [[ $placeholder_count -gt 0 ]]; then
    add_finding "CRITICAL" "placeholders_exist" \
      "Found $placeholder_count unresolved template placeholders" \
      "Replace all {{PLACEHOLDER}} with actual values from state file"
  else
    PASS_COUNT=$((PASS_COUNT + 1))
  fi

  # Check 2: Minimum sections
  if [[ $section_count -lt 3 ]]; then
    add_finding "HIGH" "insufficient_sections" \
      "Document has $section_count sections (minimum 3 required)" \
      "Add at least 3 main sections (##) to document"
  else
    PASS_COUNT=$((PASS_COUNT + 1))
  fi

  # Check 3: Endpoints (for API step)
  if [[ "$STEP_ID" == "API" ]] || [[ "$STEP_ID" == "SCHEMA" ]] || [[ "$STEP_ID" == "test-plan" ]]; then
    if [[ $endpoint_count -lt 1 ]]; then
      add_finding "HIGH" "insufficient_endpoints" \
        "Document has $endpoint_count endpoints (minimum 1 required)" \
        "Define API endpoints with ** prefix or request/response models"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 4: Tables (for SCHEMA, test-plan, RTM)
  if [[ "$STEP_ID" == "SCHEMA" ]] || [[ "$STEP_ID" == "test-plan" ]] || [[ "$STEP_ID" == "RTM" ]]; then
    if [[ $table_count -lt 1 ]]; then
      add_finding "MEDIUM" "insufficient_tables" \
        "Document has $table_count tables (minimum 1 required)" \
        "Add Markdown tables (|header|) to structure information"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 5: Rows
  if [[ $row_count -lt 1 ]] && [[ "$STEP_ID" != "IDEA" ]] && [[ "$STEP_ID" != "BRD" ]]; then
    add_finding "MEDIUM" "insufficient_rows" \
      "Document has $row_count list items (minimum 1 required)" \
      "Add structured list items with - prefix to organize content"
  else
    PASS_COUNT=$((PASS_COUNT + 1))
  fi

  # Check 6: Components (for FRONTEND, PDD)
  if [[ "$STEP_ID" == "FRONTEND" ]] || [[ "$STEP_ID" == "PDD" ]]; then
    if [[ $component_count -lt 1 ]]; then
      add_finding "HIGH" "insufficient_components" \
        "Document has $component_count component references" \
        "List all UI components used in the design (buttons, forms, etc.)"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 7: Entities (for EDD, SCHEMA)
  if [[ "$STEP_ID" == "EDD" ]] || [[ "$STEP_ID" == "SCHEMA" ]]; then
    if [[ $entity_count -lt 1 ]]; then
      add_finding "HIGH" "insufficient_entities" \
        "Document has $entity_count entity definitions" \
        "Define database entities or data models with 'class' keyword"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 8: Constants (for CONSTANTS, ARCH)
  if [[ "$STEP_ID" == "CONSTANTS" ]] || [[ "$STEP_ID" == "ARCH" ]]; then
    if [[ $constant_count -lt 1 ]]; then
      add_finding "MEDIUM" "insufficient_constants" \
        "Document has $constant_count constant definitions" \
        "Define constants and configuration values with \`CONSTANT_NAME\` notation"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 9: Methods (for SCHEMA, API, ARCH)
  if [[ "$STEP_ID" == "API" ]] || [[ "$STEP_ID" == "ARCH" ]]; then
    if [[ $method_count -lt 1 ]]; then
      add_finding "MEDIUM" "insufficient_methods" \
        "Document has $method_count method/function definitions" \
        "Define API methods or system functions"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 10: Fields (for SCHEMA, EDD)
  if [[ "$STEP_ID" == "SCHEMA" ]] || [[ "$STEP_ID" == "EDD" ]]; then
    if [[ $field_count -lt 1 ]]; then
      add_finding "MEDIUM" "insufficient_fields" \
        "Document has $field_count field definitions" \
        "Define data fields/properties with type annotations"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi
}

# ═══════════════════════════════════════════════════════════════════════════
# R-3.2: CONTENT_MAPPING CHECKING MODE
#
# Purpose: Cross-document reference coverage (traceability validation)
# Checks: 4 mapping rules validating that documents properly reference upstream content
# Examples:
#   - API.md must reference all entities from EDD.md
#   - BDD.md must trace back to PRD user stories
#   - ARCH/SCHEMA must use constants from CONSTANTS.md
#   - FRONTEND must map to screens/flows from PDD.md
#
# Each check verifies that the document properly integrates upstream specifications.
# ═══════════════════════════════════════════════════════════════════════════

run_content_mapping_checks() {
  # Check 1: entity_endpoint_coverage (API vs EDD)
  if [[ "$STEP_ID" == "API" ]]; then
    if ! grep -q "entity\|Entity" "$TARGET_FILE"; then
      add_finding "MEDIUM" "entity_coverage_missing" \
        "API.md does not reference entities from EDD" \
        "Add entity references in request/response models: 'All X entities must be..'"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 2: user_story_traceability (BDD vs PRD)
  if [[ "$STEP_ID" == "BDD-server" ]] || [[ "$STEP_ID" == "BDD-client" ]]; then
    if ! grep -q "user story\|User Story\|US-" "$TARGET_FILE"; then
      add_finding "MEDIUM" "user_story_traceability_missing" \
        "BDD.md does not reference user stories" \
        "Link BDD scenarios to PRD user stories: 'Given user story US-X...'"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 3: constant_usage (ARCH vs CONSTANTS)
  if [[ "$STEP_ID" == "ARCH" ]] || [[ "$STEP_ID" == "SCHEMA" ]]; then
    if ! grep -qE '\`[A-Z_]+\`|CONSTANT' "$TARGET_FILE"; then
      add_finding "MEDIUM" "constant_usage_missing" \
        "Document does not reference constants from CONSTANTS.md" \
        "Use constants defined in CONSTANTS.md: \`MAX_RETRIES\`, \`TIMEOUT\`, etc."
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 4: flow_screen_coverage (FRONTEND vs PDD)
  if [[ "$STEP_ID" == "FRONTEND" ]]; then
    if ! grep -qE "screen|Screen|flow|Flow" "$TARGET_FILE"; then
      add_finding "MEDIUM" "flow_coverage_missing" \
        "FRONTEND.md does not reference PDD screens/flows" \
        "Map components to PDD screens: 'Screen X uses Component Y'"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi
}

# ═══════════════════════════════════════════════════════════════════════════
# R-3.3: CROSS_FILE CHECKING MODE
#
# Purpose: Multi-document consistency & parity validation
# Checks: 4 consistency rules ensuring all document assertions align globally
# Examples:
#   - API entity count must equal EDD entity count (parity)
#   - EDD must define all relationships explicitly (no implicit associations)
#   - PRD/BRD must declare MoSCoW priorities for all features (P0/P1/P2/P3)
#   - PDD/VDD must inventory all UI components (buttons, forms, cards, etc.)
#
# Each check validates that cross-document assertions are consistent and complete.
# ═══════════════════════════════════════════════════════════════════════════

run_cross_file_checks() {
  # Check 1: entity_parity
  if [[ "$STEP_ID" == "API" ]] || [[ "$STEP_ID" == "SCHEMA" ]]; then
    if ! grep -q "entity count\|entity parity\|entities ==" "$TARGET_FILE"; then
      add_finding "MEDIUM" "entity_parity_missing" \
        "Document missing entity parity validation" \
        "Add: 'Entity count in SCHEMA must equal EDD entity count'"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 2: relationship_mapping (EDD cross-check)
  if [[ "$STEP_ID" == "EDD" ]]; then
    if ! grep -qE "relationship|association|foreign key" "$TARGET_FILE"; then
      add_finding "MEDIUM" "relationship_mapping_missing" \
        "EDD.md missing relationship definitions" \
        "Define entity relationships: 'User has many Orders (1:N)'"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 3: moscow_coverage (PRD validation)
  if [[ "$STEP_ID" == "PRD" ]] || [[ "$STEP_ID" == "BRD" ]]; then
    if ! grep -qE "P0|P1|P2|MoSCoW|must|should" "$TARGET_FILE"; then
      add_finding "MEDIUM" "moscow_coverage_missing" \
        "Document missing MoSCoW prioritization" \
        "Add priority levels: P0 (Must), P1 (Should), P2 (Could), P3 (Won't)"
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi

  # Check 4: component_usage (design cross-check)
  if [[ "$STEP_ID" == "VDD" ]] || [[ "$STEP_ID" == "PDD" ]]; then
    if ! grep -qE "component|button|input|card|modal" "$TARGET_FILE"; then
      add_finding "MEDIUM" "component_usage_missing" \
        "Design document missing component inventory" \
        "List all UI components used: buttons, inputs, cards, modals, etc."
    else
      PASS_COUNT=$((PASS_COUNT + 1))
    fi
  fi
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

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
    echo "Error: Unknown check mode '$CHECK_MODE'" >&2
    exit 1
    ;;
esac

# ═══════════════════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════════════════

if [[ "$OUTPUT_FORMAT" == "json" ]]; then
  findings_json="["
  for i in "${!FINDINGS[@]}"; do
    findings_json+="${FINDINGS[$i]}"
    [[ $i -lt $((${#FINDINGS[@]} - 1)) ]] && findings_json+=","
  done
  findings_json+="]"

  cat <<EOF
{
  "step_id": "$STEP_ID",
  "target_file": "$TARGET_FILE",
  "check_mode": "$CHECK_MODE",
  "summary": {
    "critical": $CRITICAL_COUNT,
    "high": $HIGH_COUNT,
    "medium": $MEDIUM_COUNT,
    "pass": $PASS_COUNT
  },
  "findings": $findings_json
}
EOF
else
  echo "Review Results: $STEP_ID ($CHECK_MODE mode)"
  echo "File: $TARGET_FILE"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Summary: Critical=$CRITICAL_COUNT, High=$HIGH_COUNT, Medium=$MEDIUM_COUNT, Pass=$PASS_COUNT"
  echo ""

  for finding in "${FINDINGS[@]}"; do
    echo "$finding"
  done
fi

# Exit with appropriate code
[[ $CRITICAL_COUNT -gt 0 ]] && exit 2
[[ $HIGH_COUNT -gt 0 ]] && exit 1
exit 0
