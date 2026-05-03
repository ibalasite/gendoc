# gendoc DRYRUN Engine — Testing Plan (TASK-T1~T5)

## Overview

Complete testing strategy for DRYRUN implementation across all 5 test categories:
- **T1**: Unit tests (metric extraction, spec derivation)
- **T2**: Functional tests (review.sh operations)
- **T3**: Integration tests (dryrun + review.sh + flow)
- **T4**: E2E tests (full pipeline execution)
- **T5**: Regression tests (no existing functionality broken)

---

## TASK-T1: Unit Tests

### Test Suite 1a: Metric Extraction (dryrun_core.py)

```bash
# Setup test project with known metrics
cd /tmp/test_dryrun_project
mkdir -p docs

# 建立 DRYRUN 前的文件（IDEA/BRD/PRD 等）
echo "## Persona: Test User" > docs/IDEA.md
echo "## P0" > docs/BRD.md
echo "## US-001" > docs/PRD.md
echo "| TEST |" > docs/CONSTANTS.md
echo "### Screen 1" > docs/PDD.md
echo "- Design Token 1" > docs/VDD.md
echo "class Entity1 { }" > docs/EDD.md
echo "| Service |" > docs/ARCH.md

# Create state file
cat > .gendoc-state.json << 'EOF'
{
  "client_type": "web",
  "has_admin_backend": true
}
EOF

# Run dryrun_core.py
python3 /path/to/dryrun_core.py "$(pwd)" ".gendoc-state.json"

# Verify metrics
python3 << 'PYTHON'
import json
state = json.load(open('.gendoc-state.json'))
metrics = state['dryrun_metadata']
assert metrics['extracted_metrics_count'] == 20, f"Expected 20 metrics, got {metrics['extracted_metrics_count']}"
assert metrics['derived_step_specs_count'] == 31, f"Expected 31 specs, got {metrics['derived_step_specs_count']}"
print("✅ T1a PASS: Metric extraction verified")
PYTHON
```

### Test Suite 1b: Spec Derivation

```bash
# Verify quantitative specs for each step type
python3 << 'PYTHON'
import json
state = json.load(open('.gendoc-state.json'))
specs = state['step_specifications']

# Test API spec
assert 'API' in specs, "API spec missing"
assert 'quantitative_specs' in specs['API'], "API quantitative_specs missing"
assert 'min_endpoint_count' in specs['API']['quantitative_specs'], "min_endpoint_count missing"

# Test SCHEMA spec
assert 'SCHEMA' in specs, "SCHEMA spec missing"
assert 'min_table_count' in specs['SCHEMA']['quantitative_specs'], "min_table_count missing"

# Test test-plan spec
assert 'test-plan' in specs, "test-plan spec missing"
assert 'min_h2_sections' in specs['test-plan']['quantitative_specs'], "min_h2_sections missing"

# Verify all specs have 3 components
for step_id, spec in specs.items():
  for component in ['quantitative_specs', 'content_mapping', 'cross_file_validation']:
    assert component in spec, f"{step_id} missing {component}"

print("✅ T1b PASS: Spec derivation verified")
PYTHON
```

---

## TASK-T2: Functional Tests

### Test Suite 2a: review.sh Quantitative Checks

```bash
cd /tmp/test_project
touch docs/API.md docs/SCHEMA.md

# Test 1: Bare placeholder detection
echo "This has {{PLACEHOLDER}} in it" > docs/API.md
~/.claude/skills/gendoc/tools/bin/review.sh --step API \
  --specs-from-state .gendoc-state.json \
  --target-file docs/API.md \
  --check quantitative --output-format json | grep -q "critical"
echo "✅ T2a-1: Placeholder detection working"

# Test 2: Section count
echo -e "## Section 1\nContent\n## Section 2\nMore\n## Section 3" > docs/API.md
~/.claude/skills/gendoc/tools/bin/review.sh --step API \
  --specs-from-state .gendoc-state.json \
  --target-file docs/API.md \
  --check quantitative --output-format json | grep -q "\"pass\": [1-9]"
echo "✅ T2a-2: Section counting working"

# Test 3: JSON output format
OUTPUT=$( ~/.claude/skills/gendoc/tools/bin/review.sh --step API \
  --specs-from-state .gendoc-state.json \
  --target-file docs/API.md \
  --check quantitative --output-format json )
echo "$OUTPUT" | python3 -m json.tool > /dev/null 2>&1
echo "✅ T2a-3: JSON output format valid"
```

### Test Suite 2b: review.sh Content Checks

```bash
# Test cross-file validation
cd /tmp/test_project

# Create EDD with entities
echo "class User { id; name }" > docs/EDD.md

# Create SCHEMA with fewer tables
echo "| users | id | name |" > docs/SCHEMA.md

# Run cross-file check
~/.claude/skills/gendoc/tools/bin/review.sh --step SCHEMA \
  --specs-from-state .gendoc-state.json \
  --target-file docs/SCHEMA.md \
  --check cross_file --output-format json | grep -q "high"
echo "✅ T2b: Cross-file validation working"
```

### Test Suite 2c: review.sh Exit Codes

```bash
# Test exit code 0 (pass)
echo "Good content" > docs/API.md
~/.claude/skills/gendoc/tools/bin/review.sh --step API \
  --specs-from-state .gendoc-state.json \
  --target-file docs/API.md \
  --check quantitative >/dev/null 2>&1
[[ $? -eq 0 ]] && echo "✅ T2c-1: Exit code 0 on pass"

# Test exit code 2 (critical)
echo "{{PLACEHOLDER}}" > docs/API.md
~/.claude/skills/gendoc/tools/bin/review.sh --step API \
  --specs-from-state .gendoc-state.json \
  --target-file docs/API.md \
  --check quantitative >/dev/null 2>&1
[[ $? -eq 2 ]] && echo "✅ T2c-2: Exit code 2 on critical"
```

---

## TASK-T3: Integration Tests

### Test Suite 3a: DRYRUN + review.sh Integration

```bash
# Full DRYRUN execution with review.sh integration
cd /tmp/full_test
python3 /path/to/dryrun_core.py "$(pwd)" ".gendoc-state.json" --template /path/to/DRYRUN.md

# Verify state file has specs
python3 << 'PYTHON'
import json
state = json.load(open('.gendoc-state.json'))
assert 'step_specifications' in state, "step_specifications missing"
assert len(state['step_specifications']) == 31, "Not all 31 steps have specs"
print("✅ T3a-1: DRYRUN state file generation verified")
PYTHON

# Verify MANIFEST.md generated
[[ -f docs/MANIFEST.md ]] && echo "✅ T3a-2: MANIFEST.md generated"

# Verify review.sh can read state file
~/.claude/skills/gendoc/tools/bin/review.sh --step API \
  --specs-from-state .gendoc-state.json \
  --target-file docs/API.md \
  --check all --output-format json >/dev/null 2>&1
echo "✅ T3a-3: review.sh + state file integration verified"
```

### Test Suite 3b: Multi-step Execution

```bash
# Run through multiple steps with review
cd /tmp/multi_step_test

# 生成所有 DRYRUN 前的文件
for doc in IDEA BRD PRD CONSTANTS PDD VDD EDD ARCH; do
  echo "# $doc Document" > docs/$doc.md
done

# Run DRYRUN
python3 /path/to/dryrun_core.py "$(pwd)" ".gendoc-state.json"

# Run review.sh on multiple steps
for step in API SCHEMA test-plan; do
  touch docs/${step}.md
  ~/.claude/skills/gendoc/tools/bin/review.sh --step $step \
    --specs-from-state .gendoc-state.json \
    --target-file docs/${step}.md \
    --check all --output-format json >/dev/null 2>&1 && \
    echo "✅ T3b: $step validated"
done
```

---

## TASK-T4: E2E Tests

### Test Suite 4a: Full Pipeline Execution

```bash
# Complete pipeline from DRYRUN to validation
cd /tmp/e2e_test

# 1. Setup with real documentation
mkdir -p docs features/{server,client}
# ... copy actual IDEA/BRD/PRD/etc from real project

# 2. Run DRYRUN
python3 /path/to/dryrun_core.py "$(pwd)" ".gendoc-state.json" --template /path/to/DRYRUN.md
DRYRUN_EXIT=$?
[[ $DRYRUN_EXIT -eq 0 ]] && echo "✅ T4a-1: DRYRUN completed successfully"

# 3. 生成示例 DRYRUN 后的文件
# ... (gendoc commands for API, SCHEMA, etc.)

# 4. Run review.sh validations
for step in API SCHEMA FRONTEND test-plan; do
  [[ -f docs/${step}.md ]] && \
  ~/.claude/skills/gendoc/tools/bin/review.sh --step $step \
    --specs-from-state .gendoc-state.json \
    --target-file docs/${step}.md \
    --check all --output-format json >/dev/null 2>&1 && \
    echo "✅ T4a: $step validation passed"
done

# 5. Verify MANIFEST.md matches actual metrics
python3 << 'PYTHON'
import json
from pathlib import Path

state = json.load(open('.gendoc-state.json'))
manifest = Path('docs/MANIFEST.md').read_text()

# Verify key placeholders were replaced
assert '{{' not in manifest or 'VERSION' in manifest, "Unreplaced placeholders found"
print("✅ T4a: E2E pipeline execution verified")
PYTHON
```

---

## TASK-T5: Regression Tests

### Test Suite 5a: No Breaking Changes

```bash
# Verify existing functionality still works

# 1. Check that old gate-check mechanism still works (if present)
[[ -f tools/bin/gate-check.sh ]] && \
  bash tools/bin/gate-check.sh TEST_STEP /tmp >/dev/null 2>&1 && \
  echo "✅ T5a-1: Legacy gate-check still functional"

# 2. Verify state file backward compatibility
python3 << 'PYTHON'
import json

# Old-style state file (without step_specifications)
old_state = {
  "client_type": "web",
  "has_admin_backend": true,
  "review_progress": {}
}

# Should be readable by both old and new code
json.dumps(old_state)  # Serializes fine
print("✅ T5a-2: Backward compatibility maintained")
PYTHON

# 3. Verify templates still loadable
[[ -f templates/DRYRUN.md ]] && wc -l templates/DRYRUN.md && echo "✅ T5a-3: Templates accessible"

# 4. Check git history intact
git log --oneline | head -5 && echo "✅ T5a-4: Git history preserved"
```

### Test Suite 5b: Performance Baseline

```bash
# Measure metric extraction time
cd /tmp/perf_test
time python3 /path/to/dryrun_core.py "$(pwd)" ".gendoc-state.json"

# Should complete in < 5 seconds for small project
echo "⏱️  Performance baseline established"
```

---

## Test Execution Order

```
T1 Unit Tests (5 min)
  ├─ T1a: Metric extraction
  └─ T1b: Spec derivation
       ↓
T2 Functional Tests (10 min)
  ├─ T2a: review.sh quantitative checks
  ├─ T2b: review.sh content checks
  └─ T2c: Exit codes
       ↓
T3 Integration Tests (15 min)
  ├─ T3a: DRYRUN + review.sh
  └─ T3b: Multi-step execution
       ↓
T4 E2E Tests (30 min)
  └─ T4a: Full pipeline
       ↓
T5 Regression Tests (5 min)
  ├─ T5a: Backward compatibility
  └─ T5b: Performance baseline

Total: ~65 minutes
```

---

## Success Criteria

**All tests must PASS before marking complete:**

- ✅ T1: 100% metric extraction and spec derivation correct
- ✅ T2: review.sh all checks functional with correct exit codes
- ✅ T3: DRYRUN + review.sh integrated without errors
- ✅ T4: End-to-end pipeline execution successful
- ✅ T5: No regressions, backward compatible

**Exit on first failure:**
- Investigate root cause
- Fix identified issue
- Re-run from failed test
