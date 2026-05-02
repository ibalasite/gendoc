#!/usr/bin/env bash
# tools/bin/gate-check.sh
# Usage: bash tools/bin/gate-check.sh <step-id> [project-dir]
# Reads .gendoc-rules/<step-id>-rules.json and performs mechanical verification
# Outputs JSON array of findings (empty [] if no issues or no rules file)
# Exit 0 always (findings are communicated via JSON stdout, not exit code)

set -euo pipefail

STEP_ID="${1:-}"
PROJECT_DIR="${2:-$(pwd)}"
RULES_FILE="${PROJECT_DIR}/.gendoc-rules/${STEP_ID}-rules.json"

if [[ -z "$STEP_ID" ]]; then
  echo "Usage: gate-check.sh <step-id> [project-dir]" >&2
  echo "[]"
  exit 0
fi

if [[ ! -f "$RULES_FILE" ]]; then
  echo "[]"
  exit 0
fi

# Use Python for robust JSON processing and multi-line checks
python3 - "$RULES_FILE" "$PROJECT_DIR" "$STEP_ID" <<'PYEOF'
import json, sys, re, os
from pathlib import Path

rules_file = sys.argv[1]
project_dir = Path(sys.argv[2])
step_id = sys.argv[3]

try:
    rules = json.loads(Path(rules_file).read_text(encoding="utf-8"))
except Exception as e:
    print(f"[]", file=sys.stdout)
    sys.exit(0)

findings = []
finding_idx = [0]

def add_finding(rule_id, check, file_path, detail, fix_hint, severity="MECHANICAL"):
    finding_idx[0] += 1
    findings.append({
        "severity": severity,
        "rule_id": f"MG-{finding_idx[0]:02d}",
        "check": check,
        "file": str(file_path),
        "detail": detail,
        "fix_hint": fix_hint,
    })

for output_file_spec in rules.get("output_files", []):
    rel_path = output_file_spec.get("path", "")
    abs_path = project_dir / rel_path

    # ── Check 1: File existence ───────────────────────────────────────────
    if output_file_spec.get("must_exist", True):
        if not abs_path.exists():
            add_finding(
                rule_id="exist",
                check="file_existence",
                file_path=rel_path,
                detail=f"檔案不存在：{rel_path}",
                fix_hint=f"重新執行 {step_id} gen 步驟以生成 {rel_path}",
            )
            continue  # Can't check further if file doesn't exist

    if not abs_path.exists():
        continue

    content = abs_path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    # ── Check 2: Non-empty ───────────────────────────────────────────────
    if output_file_spec.get("must_not_be_empty", True):
        if len(content.strip()) < 100:
            add_finding(
                rule_id="nonempty",
                check="file_not_empty",
                file_path=rel_path,
                detail=f"檔案內容過少（{len(content.strip())} chars < 100）",
                fix_hint=f"重新生成 {rel_path}，確保有實質內容",
            )

    # ── Check 3: Bare placeholders ───────────────────────────────────────
    if output_file_spec.get("no_bare_placeholders", True):
        PLACEHOLDER_RE = re.compile(r'(?<!\w)\{\{([A-Z][A-Z0-9_]*)\}\}(?!\s*[：:\-—])')
        VALID_TEMPLATE_RE = re.compile(r'\{\{.+?\}\}.*[：:\-—]')
        bare_count = 0
        bare_examples = []
        for i, line in enumerate(lines, 1):
            if PLACEHOLDER_RE.search(line) and not VALID_TEMPLATE_RE.search(line):
                bare_count += 1
                if len(bare_examples) < 3:
                    bare_examples.append(f"L{i}: {line.strip()[:60]}")
        if bare_count > 0:
            add_finding(
                rule_id="no_placeholder",
                check="no_bare_placeholders",
                file_path=rel_path,
                detail=f"發現 {bare_count} 個未替換的 {{{{PLACEHOLDER}}}}：{'; '.join(bare_examples)}",
                fix_hint="替換所有 {{}} placeholder 為實際專案內容",
            )

    # ── Check 4: Minimum H2 sections ────────────────────────────────────
    min_h2 = output_file_spec.get("min_h2_sections", 0)
    if min_h2 > 0:
        h2_count = sum(1 for l in lines if re.match(r'^## ', l))
        if h2_count < min_h2:
            add_finding(
                rule_id="min_h2",
                check="min_h2_sections",
                file_path=rel_path,
                detail=f"§章節數不足：{h2_count} < {min_h2}（需要 ≥ {min_h2} 個 ## 章節）",
                fix_hint=f"補全 {rel_path} 的缺少章節，至少達到 {min_h2} 個 ## 章節",
            )

    # ── Check 5: Minimum endpoint count (API.md) ─────────────────────────
    min_ep = output_file_spec.get("min_endpoint_count", 0)
    if min_ep > 0:
        ep_count = len(re.findall(r'^\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|', content, re.MULTILINE))
        # Also count "#### GET /xxx" style
        ep_count += len(re.findall(r'^#{3,5}\s+(GET|POST|PUT|DELETE|PATCH)\s+/', content, re.MULTILINE))
        if ep_count < min_ep:
            add_finding(
                rule_id="min_endpoint",
                check="min_endpoint_count",
                file_path=rel_path,
                detail=f"API endpoint 數不足：{ep_count} < {min_ep}（需要 ≥ {min_ep} 個 endpoint）",
                fix_hint=f"在 {rel_path} §Endpoints 補全所有 API endpoint（目標 EDD 設計的 {min_ep} 個）",
            )

    # ── Check 6: Minimum table count (SCHEMA.md) ─────────────────────────
    min_table = output_file_spec.get("min_table_count", 0)
    if min_table > 0:
        # Count H3 headings (### TableName) in §Tables section as proxy for table count
        table_count = len(re.findall(r'^#{2,4}\s+\w', content, re.MULTILINE))
        # Fallback: count | PRIMARY KEY | or | id | as DB table indicators
        pk_count = len(re.findall(r'PRIMARY\s+KEY|AUTO_INCREMENT|BIGSERIAL|SERIAL', content, re.IGNORECASE))
        actual = max(table_count // 3, pk_count)  # Heuristic
        if actual < min_table:
            add_finding(
                rule_id="min_table",
                check="min_table_count",
                file_path=rel_path,
                detail=f"DB table 定義不足（估計 {actual} < {min_table}）",
                fix_hint=f"在 {rel_path} §Tables 補全所有 DB table 定義（目標 {min_table} 個）",
            )

    # ── Check 7: Minimum RTM row count ───────────────────────────────────
    min_rtm = output_file_spec.get("min_row_count", 0)
    if min_rtm > 0:
        # Count table data rows (| US- or | TC- patterns)
        rtm_count = len(re.findall(r'^\|\s*(US|TC|REQ)-\d+', content, re.MULTILINE))
        if rtm_count < min_rtm:
            add_finding(
                rule_id="min_rtm_rows",
                check="min_row_count",
                file_path=rel_path,
                detail=f"RTM rows 不足：{rtm_count} < {min_rtm}（需覆蓋所有 User Stories）",
                fix_hint=f"在 {rel_path} 補全 RTM 映射，確保每個 US 都有對應 TC",
            )

    # ── Check 8: Required sections ───────────────────────────────────────
    required_sections = output_file_spec.get("required_sections", [])
    for section in required_sections:
        pattern = re.compile(re.escape(section), re.IGNORECASE)
        if not pattern.search(content):
            add_finding(
                rule_id="req_section",
                check="required_section",
                file_path=rel_path,
                detail=f"缺少必要章節：\"{section}\"",
                fix_hint=f"在 {rel_path} 新增 \"{section}\" 章節並填入內容",
            )

    # ── Check 9: Min words per section ───────────────────────────────────
    min_words = output_file_spec.get("min_words_per_section", 0)
    if min_words > 0:
        sections = re.split(r'^#{2,4}\s+', content, flags=re.MULTILINE)
        short_sections = []
        heading_re = re.compile(r'^#{2,4}\s+(.+)$', re.MULTILINE)
        headings = heading_re.findall(content)
        for i, (heading, body) in enumerate(zip(headings, sections[1:])):
            word_count = len(body.split())
            if word_count < min_words:
                short_sections.append(f"「{heading[:30]}」({word_count} words)")
        if short_sections and len(short_sections) > len(headings) * 0.4:
            # Only flag if more than 40% of sections are thin
            add_finding(
                rule_id="min_words",
                check="min_section_words",
                file_path=rel_path,
                detail=f"{len(short_sections)} 個章節內容過少（< {min_words} words）：{'; '.join(short_sections[:3])}",
                fix_hint=f"補全各章節實質內容，每個章節至少 {min_words} words",
            )

# ── Anti-fake rules ──────────────────────────────────────────────────────────
for rule in rules.get("anti_fake_rules", []):
    rule_type = rule.get("type", "")

    if rule_type == "no_duplicate_paragraphs":
        min_len = rule.get("min_char_length", 150)
        # Check across all output files combined
        for output_file_spec in rules.get("output_files", []):
            abs_path = project_dir / output_file_spec.get("path", "")
            if not abs_path.exists():
                continue
            content = abs_path.read_text(encoding="utf-8", errors="replace")
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) >= min_len]
            seen = {}
            for para in paragraphs:
                key = para[:100]  # Use first 100 chars as dedup key
                seen[key] = seen.get(key, 0) + 1
            dupes = [(k, v) for k, v in seen.items() if v > 1]
            if dupes:
                add_finding(
                    rule_id="no_dupe_para",
                    check="no_duplicate_paragraphs",
                    file_path=output_file_spec.get("path", ""),
                    detail=f"發現 {len(dupes)} 個重複段落（≥{min_len} chars）",
                    fix_hint="移除重複段落，每個章節提供獨特內容",
                )

    elif rule_type == "no_trivial_entity_names":
        for output_file_spec in rules.get("output_files", []):
            abs_path = project_dir / output_file_spec.get("path", "")
            if not abs_path.exists():
                continue
            content = abs_path.read_text(encoding="utf-8", errors="replace")
            trivial_re = re.compile(r'\b(Foo|Bar|Baz|Sample|Test|Demo|Example|Dummy|Mock)[A-Z][a-z]', re.IGNORECASE)
            matches = trivial_re.findall(content)
            if len(matches) >= 3:
                add_finding(
                    rule_id="no_trivial_names",
                    check="no_trivial_entity_names",
                    file_path=output_file_spec.get("path", ""),
                    detail=f"發現 {len(matches)} 個無意義 entity 名稱（Foo/Bar/Baz/Sample/Demo 等）",
                    fix_hint="使用真實業務語義的命名（如 Member, Wallet, Transaction 等），不得使用佔位名稱",
                )

print(json.dumps(findings, ensure_ascii=False, indent=2))
PYEOF
