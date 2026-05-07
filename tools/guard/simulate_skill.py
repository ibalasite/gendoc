#!/usr/bin/env python3
"""Skill-execution simulator: parse <skill>/SKILL.md, extract every ```bash
and ```python block, build the actual Bash tool cmd shape Claude would emit
(bash blocks as-is; python blocks wrapped in heredoc), feed each to
evaluate_bash() in tools/bin/gendoc-guard-blocker.py.

Usage:
    python3 tools/guard/simulate_skill.py <skill_dir>
    python3 tools/guard/simulate_skill.py /Users/tobala/projects/gendoc/skills/gendoc-repair
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BLOCKER = REPO / 'tools' / 'bin' / 'gendoc-guard-blocker.py'

spec = importlib.util.spec_from_file_location('blocker', BLOCKER)
blocker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blocker)
evaluate_bash = blocker.evaluate_bash


def extract_blocks(md_path: pathlib.Path):
    """Yield (kind, line_no, body) for every ```bash and ```python block."""
    text = md_path.read_text(encoding='utf-8')
    pat = re.compile(r'^```(bash|python)\s*\n(.*?)^```\s*$',
                     re.DOTALL | re.MULTILINE)
    for m in pat.finditer(text):
        kind = m.group(1)
        body = m.group(2)
        line_no = text[:m.start()].count('\n') + 1
        yield kind, line_no, body


def to_bash_cmd(kind: str, body: str) -> str:
    """python block → wrapped in heredoc (the shape Claude actually emits)."""
    if kind == 'bash':
        return body
    return f"python3 - <<'EOF'\n{body}EOF\n"


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: simulate_skill.py <skill_dir>')
        return 2
    skill_dir = pathlib.Path(sys.argv[1])
    md = skill_dir / 'SKILL.md'
    if not md.is_file():
        print(f'NOT FOUND: {md}')
        return 2

    print('=' * 78)
    print(f'SKILL execution simulation  {skill_dir.name}')
    print(f'  blocker = {BLOCKER}')
    print('=' * 78)

    pass_n = fail_n = 0
    for kind, line, body in extract_blocks(md):
        cmd = to_bash_cmd(kind, body)
        reason = evaluate_bash(cmd)
        head = body.splitlines()[0] if body.splitlines() else '(empty)'
        head = head[:64] + ('...' if len(head) > 64 else '')
        if reason is None:
            print(f'  ✅ L{line:>4} [{kind}] PASS  {head!r}')
            pass_n += 1
        else:
            print(f'  ❌ L{line:>4} [{kind}] BLOCK  {reason}')
            print(f'        first line: {head!r}')
            fail_n += 1

    print('\n' + '=' * 78)
    print(f'TOTAL: {pass_n} PASS / {fail_n} BLOCK')
    print('=' * 78)
    if fail_n:
        print('\n⚠️  Skill 內有 block 命中規則 — 需要白名單或規則微調')
    else:
        print('\n✅ Skill 全部區塊放行 — hook 不會阻礙正常執行')
    return 0 if fail_n == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
