---
name: gendoc-gen-dryrun
description: DRYRUN Step (Phase A → Phase B gateway) — Read all 8 Phase A files (IDEA~ARCH), extract 20 quantitative metrics, derive 31 step specifications, embed in state file, generate MANIFEST.md
version: 2.0.0
allowed-tools:
  - Read
  - Write
  - Bash
---

# gendoc-gen-dryrun — Phase A→B Gateway & Specification Derivation Engine

## Overview

**Purpose**: Gateway between Phase A completion (IDEA~ARCH) and Phase B execution (API~HTML). Read all completed Phase A documents, extract quantitative baselines, derive specifications for all 31 Phase B steps, embed in state file (no target project pollution), generate MANIFEST.md.

**Input**:
- Current directory's `.gendoc-state-*.json`
- All 8 Phase A files: docs/IDEA.md, docs/BRD.md, docs/PRD.md, docs/CONSTANTS.md, docs/PDD.md, docs/VDD.md, docs/EDD.md, docs/ARCH.md

**Output**:
- Updated `.gendoc-state-*.json` with `step_specifications` field (31 steps × 3 spec types each)
- docs/MANIFEST.md (quantitative baseline summary, human-readable)
- Git commit with state file changes

**Key Design Principles**:
- **No target project pollution**: All specifications embedded in state file, no .gendoc-rules/ directory created
- **20 quantitative metrics**: persona_count, moscow_p0_count, kpi_count, user_story_count, feature_count, use_case_count, total_ac_count, constant_count, screen_count, flow_count, total_component_count, design_token_count, color_count, entity_count, relationship_count, rest_endpoint_count, domain_count, layer_count, service_count, nfr_count
- **31 step specifications**: quantitative_specs + content_mapping + cross_file_validation for each Phase B step
- **Double-layer review enablement**: AI review + shell script quantitative checks (via review.sh) → merged findings → AI fix

---

## Step 0: Environment Initialization & Precondition Checks

**Bash Setup**:

```bash
set -euo pipefail

_CWD="$(pwd)"
_DOCS_DIR="${_CWD}/docs"
_STATE_FILE=$(ls "${_CWD}"/.gendoc-state-*.json 2>/dev/null | head -1 || echo "${_CWD}/.gendoc-state.json")

# Verify state file exists
if [[ ! -f "$_STATE_FILE" ]]; then
  echo "❌ [DRYRUN] State file not found: $_STATE_FILE"
  echo "           Run /gendoc-auto first to initialize"
  exit 1
fi

# Verify Phase A completion (all 8 files required)
_PHASE_A_FILES=("IDEA" "BRD" "PRD" "CONSTANTS" "PDD" "VDD" "EDD" "ARCH")
_MISSING=()
for _FILE in "${_PHASE_A_FILES[@]}"; do
  if [[ ! -f "${_DOCS_DIR}/${_FILE}.md" ]]; then
    _MISSING+=("${_FILE}.md")
  fi
done

if [[ ${#_MISSING[@]} -gt 0 ]]; then
  echo "❌ [DRYRUN] Missing Phase A files: ${_MISSING[*]}"
  echo "           All 8 Phase A documents required before DRYRUN"
  exit 1
fi

echo "✅ [DRYRUN] Phase A complete: 8/8 files found"
echo "[DRYRUN] CWD: $_CWD"
echo "[DRYRUN] State file: $_STATE_FILE"
```

---

## Step 1: Read Phase A Files & Extract 20 Quantitative Metrics

**[AI Instruction]** Use Read tool to load all 8 Phase A files, extract 20 quantitative metrics via grep/count operations.

**Extraction Logic**:

| # | Metric | File | Grep Pattern | Fallback |
|----|--------|------|--------------|----------|
| 1 | persona_count | IDEA.md | grep -c '^## Persona:' | 1 |
| 2 | moscow_p0_count | BRD.md | grep '^## P0' / moscow table rows | 3 |
| 3 | kpi_count | BRD.md | grep -cE '^.+: [0-9]+' (KPI rows) | 1 |
| 4 | user_story_count | PRD.md | grep -c '^\(## \|### \)US-' | 1 |
| 5 | feature_count | PRD.md | grep -c '^## FE-' / features section | 1 |
| 6 | use_case_count | PRD.md | grep -c '^## UC-' / use cases section | 1 |
| 7 | total_ac_count | PRD.md | grep -c '- \[ \] ' (AC checkboxes) | 5 |
| 8 | constant_count | CONSTANTS.md | grep -c '^\| [A-Z_]' (table rows) | 3 |
| 9 | screen_count | PDD.md | grep -c '^### Screen' / screen definitions | 1 |
| 10 | flow_count | PDD.md | grep -c '^### User Flow' / flow diagrams | 1 |
| 11 | total_component_count | PDD.md | grep -c '^\- ' (component list items) | 3 |
| 12 | design_token_count | VDD.md | grep -c '^\- \`' (token definitions) | 5 |
| 13 | color_count | VDD.md | grep -c '^\| #[0-9A-Fa-f]' (color palette rows) | 5 |
| 14 | entity_count | EDD.md | grep -c '^\s*class ' (UML class defs) | 3 |
| 15 | relationship_count | EDD.md | grep -cE '(--|<\|--|\*--|o--)' (association lines) | 3 |
| 16 | rest_endpoint_count | EDD.md | grep -cE '(<<REST>>|<<Interface>>|GET\|POST\|PUT\|DELETE)' | 5 |
| 17 | domain_count | EDD.md | grep -c '^### ' (domain sections) | 2 |
| 18 | layer_count | ARCH.md | grep -c '^\| [A-Za-z0-9_]' (tech stack rows, excluding header) | 4 |
| 19 | service_count | ARCH.md | grep -c '^#### ' (service definitions) | 3 |
| 20 | nfr_count | ARCH.md | grep -c '^## NFR' / grep -c '^\- ' (NFR list items) | 12 |

**[AI Implementation]**:

Create a JSON structure in memory (do NOT write to file):

```json
{
  "extracted_metrics": {
    "persona_count": <value>,
    "moscow_p0_count": <value>,
    "kpi_count": <value>,
    "user_story_count": <value>,
    "feature_count": <value>,
    "use_case_count": <value>,
    "total_ac_count": <value>,
    "constant_count": <value>,
    "screen_count": <value>,
    "flow_count": <value>,
    "total_component_count": <value>,
    "design_token_count": <value>,
    "color_count": <value>,
    "entity_count": <value>,
    "relationship_count": <value>,
    "rest_endpoint_count": <value>,
    "domain_count": <value>,
    "layer_count": <value>,
    "service_count": <value>,
    "nfr_count": <value>
  },
  "extraction_timestamp": "<ISO-8601 now>",
  "phase_a_files_read": 8,
  "ready_for_step_2": true
}
```

Record this in working memory. Proceed to Step 2.

---

## Step 2: Derive Specifications for 31 Phase B Steps

**[AI Instruction]** Based on 20 extracted metrics from Step 1, calculate specification logic for all 31 Phase B steps (API, SCHEMA, FRONTEND, AUDIO, ANIM, CLIENT_IMPL, ADMIN_IMPL, RESOURCE, UML, test-plan, BDD-server, BDD-client, RTM, runbook, LOCAL_DEPLOY, CICD, DEVELOPER_GUIDE, UML-CICD, ALIGN, CONTRACTS, MOCK, PROTOTYPE, HTML, etc.).

Each step gets 3 specification types:

### 2a. Quantitative Specs

Map extracted metrics to concrete min/max thresholds for each step:

| Step | quantitative_specs | Derivation |
|------|-------------------|-----------|
| API | min_endpoint_count | rest_endpoint_count (min 5) |
| SCHEMA | min_table_count | entity_count (min 3) |
| test-plan | min_h2_sections | layer_count + 4 |
| BDD-server | min_scenario_count | ceil(user_story_count × 0.8) |
| BDD-client | min_scenario_count | ceil(user_story_count × 0.6) |
| RTM | min_row_count | user_story_count |
| FRONTEND | min_component_count | total_component_count (min 3) |
| RESOURCE | min_resource_entries | max(constant_count, 5) |
| (other steps) | step-specific rules | (per progress.md TASK-D2) |

### 2b. Content Mapping

Define expected coverage ranges (entity names, user story references, etc.):

```json
"content_mapping": {
  "entity_coverage": {
    "expected_entities": [ list from EDD entity_count ],
    "coverage_requirement": 0.95
  },
  "user_story_traceability": {
    "expected_us_count": user_story_count,
    "coverage_requirement": 1.0
  },
  "constant_usage": {
    "expected_constant_count": constant_count,
    "coverage_requirement": 0.8
  }
}
```

### 2c. Cross-File Validation

Define consistency checks across Phase A → Phase B:

```json
"cross_file_validation": {
  "entity_parity": {
    "source_doc": "EDD.md",
    "source_metric": entity_count,
    "target_metric": "min_table_count",
    "rule": "SCHEMA must reference all EDD entities"
  },
  "endpoint_mapping": {
    "source_doc": "EDD.md",
    "source_metric": rest_endpoint_count,
    "target_metric": "API.md endpoint count",
    "rule": "API must map all EDD REST endpoints"
  }
}
```

Create this structure in memory for all 31 steps. Do NOT write to file yet.

---

## Step 3: Embed Specifications in State File

**[AI Instruction]** Read the current state file, add `step_specifications` field with all 31 step specs from Step 2, write back to same state file using Write tool.

**State File Structure** (preserve all existing fields, add new one):

```json
{
  "...existing_fields...": "...",
  "step_specifications": {
    "API": {
      "quantitative_specs": { "min_endpoint_count": X, ... },
      "content_mapping": { "entity_coverage": {...}, ... },
      "cross_file_validation": { "entity_parity": {...}, ... }
    },
    "SCHEMA": { ... },
    "FRONTEND": { ... },
    ...  (all 31 steps)
  },
  "dryrun_metadata": {
    "extraction_timestamp": "<ISO-8601>",
    "extracted_metrics_count": 20,
    "derived_step_specs_count": 31,
    "phase_a_version": "v2.0.0"
  }
}
```

**Important**: Write using Write tool, overwriting the original state file. This is safe because Step 3 is non-destructive (only adds a new field).

---

## Step 4: Validate Completeness & Generate MANIFEST.md

**[AI Instruction]**:

1. **Verify completeness** (sanity check):
   - [ ] State file contains `step_specifications` field
   - [ ] All 31 steps present in step_specifications
   - [ ] Each step has quantitative_specs, content_mapping, cross_file_validation
   - [ ] All 20 metrics extracted and stored in dryrun_metadata

2. **Generate MANIFEST.md** from template `templates/DRYRUN.md`:
   - Load DRYRUN.md template
   - Replace all `{{PLACEHOLDER}}` values with actual extracted metrics and counts
   - Placeholder mapping:
     - `{{GENERATED_DATE}}` → today's ISO 8601 date
     - `{{ENTITY_COUNT}}` → entity_count from Step 1
     - `{{REST_ENDPOINT_COUNT}}` → rest_endpoint_count from Step 1
     - `{{USER_STORY_COUNT}}` → user_story_count from Step 1
     - `{{ARCH_LAYER_COUNT}}` → layer_count from Step 1
     - (complete list per PRD §7.7)
   - Section §2.1 System Parameters: fill with all 20 extracted metrics
   - Section §3 Mandatory Steps Checklist: fill active steps count
   - Section §4 Per-Step Completeness Standards: fill quantitative thresholds from state file

3. **Write MANIFEST.md** to docs/ using Write tool

---

## Step 5: Commit & Output Completion Signal

**[AI Instruction]**:

```bash
# Commit state file with embedded specifications
cd "$_CWD"
git add .gendoc-state-*.json
git commit -m "docs(gendoc)[DRYRUN]: Phase A→B specification derivation complete

Extracted Metrics:
  - persona_count: <value>
  - moscow_p0_count: <value>
  - user_story_count: <value>
  - entity_count: <value>
  - rest_endpoint_count: <value>
  - layer_count: <value>
  (all 20 metrics)

Specifications Derived: 31 steps
State File Field: step_specifications
MANIFEST.md: Generated

Next: Run Phase B steps (API → HTML) with double-layer review:
  - Layer 1: AI review (gendoc-flow)
  - Layer 2: Quantitative checks (review.sh --specs-from-state)
  - Merge findings → AI fix"

# Output completion summary
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  DRYRUN Complete: Phase A→B Specification Derivation         ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Metrics Extracted        : 20                               ║"
echo "║  Step Specifications      : 31                               ║"
echo "║  State File Updated       : $(basename $_STATE_FILE)        ║"
echo "║  MANIFEST.md Generated    : docs/MANIFEST.md                 ║"
echo "║  Git Commit               : OK                               ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Ready for Phase B: execute /gendoc API                      ║"
echo "║  Phase B review uses dual-layer validation                   ║"
echo "║  (AI + quantitative specs from state file)                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"

echo "DRYRUN_COMPLETE: step_specifications embedded in state file"
```

If git commit fails (no git repo), skip commit step but continue to output summary.

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Missing Phase A file(s) | STOP in Step 0 (precondition check). Output required files. |
| Grep extraction returns 0 | Use fallback value (shown in extraction table, typically 1-5) |
| State file read fails | STOP. Output error and ask user to verify state file exists. |
| State file write fails | STOP. Output error and ask user to check write permissions. |
| Template DRYRUN.md not found | STOP. Output message asking to verify template location. |
| All 20 metrics = 0 (unlikely) | Use conservative defaults for all metrics to enable Phase B execution |

---

## Design Rationale

1. **No .gendoc-rules/ directory** in target project → Specifications live in state file (single source of truth)
2. **All 8 Phase A files required** → Rich baseline for more accurate Phase B specs
3. **20 metrics** → Covers business (personas, KPIs), product (user stories, features), design (screens, tokens), technical (entities, endpoints, layers)
4. **31 step specs** → Every Phase B step has quantitative + content + cross-file expectations
5. **State file as distribution mechanism** → Phase B steps read specs from state file, review.sh tool also reads from state file (no copy/pollution)
6. **MANIFEST.md for human reference** → Transparent summary of quantitative baselines and specification logic

---

## Next Steps (TASK-D2 ~ D5, TASK-R1 ~ R6)

- **TASK-D2**: Implement specification derivation logic (progresses.md §TASK-D2)
- **TASK-D3**: Embed in state file with proper JSON structure (progresses.md §TASK-D3)
- **TASK-D4**: Completeness validation (progresses.md §TASK-D4)
- **TASK-D5**: MANIFEST.md generation + git commit (progresses.md §TASK-D5)
- **TASK-R1 ~ R6**: Implement review.sh tool (parameterized bash, ~400 lines)
- **TASK-F1 ~ F4**: Integrate with gendoc-flow (call review.sh, merge findings, AI fix)

See `progress.md` for full implementation task breakdown.
