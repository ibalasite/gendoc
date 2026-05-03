# gendoc-flow + review.sh Integration Guide

## TASK-F1~F4 Implementation Summary

### Overview
This guide describes how to integrate the new `review.sh` quantitative validation tool into `gendoc-flow`'s review loop, enabling double-layer validation (AI review + shell script quantitative checks).

### Architecture

```
Phase D-2: Review Loop (per step)
    ↓
Step A-0: Gate Check (Run review.sh)
    ├─ Shell findings (quantitative checks)
    └─ Output: mechanical_findings JSON
    ↓
Step A: AI Review
    ├─ Read template/{TYPE}.review.md
    ├─ Run review checks
    ├─ Output: AI findings
    └─ Merge with mechanical_findings
    ↓
Step B: Merge Findings
    ├─ Input: AI findings + mechanical findings
    ├─ Deduplicate by ID
    ├─ Sort by severity (critical → low)
    └─ Output: combined_findings
    ↓
Step C: Fix Subagent
    ├─ Input: combined_findings
    ├─ Fix all CRITICAL + HIGH
    ├─ Attempt MEDIUM + LOW
    └─ Output: modified files
    ↓
Step D: Round Summary + Commit
```

### Integration Points

#### TASK-F1: Gate Check Integration

**Location:** gendoc-flow SKILL.md, Phase D-2, Step A-0

**Before (old):**
```bash
_GATE_OUT=$(bash tools/bin/gate-check.sh {step.id} {_PROJECT_DIR})
```

**After (new):**
```bash
_SHELL_FINDINGS=$(bash skills/gendoc-flow/review_integration.sh \
  "{step.id}" \
  "{_PRIMARY_OUTPUT}" \
  "{_STATE_FILE}" \
  "json")
```

**Scripts involved:**
- `review_integration.sh` — Wrapper that calls review.sh and converts output
- `review.sh` (in ~/.claude/skills/gendoc/tools/bin/) — Core validation tool

#### TASK-F2: Finding Merge Logic

**Location:** gendoc-flow SKILL.md, Phase D-2, Step B

**Implementation:**
```python
# Merge AI findings + shell findings
def merge_findings(ai_findings, shell_findings):
    seen = {}
    for f in ai_findings + shell_findings:
        fid = f["id"]
        if fid not in seen:
            seen[fid] = f
        else:
            # Keep higher severity
            if severity_rank(f["severity"]) > severity_rank(seen[fid]["severity"]):
                seen[fid] = f

    # Sort by severity
    return sorted(seen.values(), key=lambda x: severity_rank(x["severity"]), reverse=True)
```

#### TASK-F3: Fix Subagent Receives Merged Findings

**Location:** gendoc-flow SKILL.md, Phase D-2, Step C

**Change:**
- Pass `combined_findings` (merged result) to Fix subagent
- Include both sources in finding message: "AI + quantitative check found..."
- Fix subagent handles all sources uniformly

#### TASK-F4: Gate-Check Logic Update

**Location:** gendoc-flow SKILL.md, Phase D-2, Step A-0

**Changes:**
1. Replace `.gendoc-rules/{step.id}-rules.json` lookup with state file lookup
2. Call `review_integration.sh` instead of `gate-check.sh`
3. Mechanical findings always treated as CRITICAL
4. Merge happens before Step A Review, so AI review sees both

### Step-by-Step Integration

1. **Copy review_integration.sh** to `/Users/tobala/projects/gendoc/skills/gendoc-flow/`

2. **Update gendoc-flow SKILL.md**:
   - Step A-0: Replace gate-check.sh call with review_integration.sh
   - Step B: Add finding merge logic (Python)
   - Step C: Update Fix subagent prompt to handle merged findings
   - Step D: Update summary to show both AI + mechanical counts

3. **Testing sequence**:
   - Run `/gendoc edd` on test project
   - Verify review.sh is called in Round 1
   - Verify mechanical findings appear in summary
   - Verify fix subagent acts on merged findings

### Key Files

| File | Role | Status |
|------|------|--------|
| `tools/bin/review.sh` | Core validation tool | ✅ Complete |
| `skills/gendoc-flow/review_integration.sh` | Wrapper for gendoc-flow | ✅ Complete |
| `skills/gendoc-flow/SKILL.md` | Integration points | ⏳ Manual edit needed |
| `skills/gendoc-gen-dryrun/dryrun_core.py` | Spec generation | ✅ Complete |

### Manual Updates Required

The following sections of `gendoc-flow/SKILL.md` need manual editing:

1. **Line ~871 (Step A-0 Gate Check)**
   - Replace gate-check.sh call
   - Add review_integration.sh call signature

2. **Line ~883 (Step A Review)**
   - Add merge logic before Step A review findings output

3. **Line ~895 (Step C Fix)**
   - Update to use combined_findings instead of just AI findings

4. **Line ~901 (Step D Summary)**
   - Add mechanical findings count to summary output

### Verification

After integration, verify:
- ✅ review.sh callable from ~/.claude/skills/gendoc/tools/bin/
- ✅ review_integration.sh present in gendoc-flow skills
- ✅ gendoc-flow SKILL.md updated at integration points
- ✅ Test run on sample project produces dual-layer findings
- ✅ Fix subagent receives and acts on all findings
- ✅ Round summary shows both AI + mechanical counts
- ✅ All findings merged by ID, no duplicates

### Rollback

If issues arise:
1. Restore gendoc-flow SKILL.md from git: `git checkout skills/gendoc-flow/SKILL.md`
2. review.sh remains unaffected (in ~/.claude/skills/gendoc/tools/bin/)
3. Previous gate-check.sh logic can be reinstated temporarily

---

## TASK-T1~T5 Testing

See `TESTING.md` for comprehensive test plans.
