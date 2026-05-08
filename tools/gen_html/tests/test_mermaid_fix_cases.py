#!/usr/bin/env python3
"""Mermaid `_mermaid_fix_block` TDD test suite.

Covers 17 fixture cases:
- 12 BROKEN — real-world AI-generated diagrams that fail mermaid v11 parse.
  After `_mermaid_fix_block`, each must parse OK.
- 5 LEGIT — known-working diagrams. After `_mermaid_fix_block`, must
  still parse OK（regression baseline — proves we don't break good ones）.

Each case is run by:
  1. Read fixture .mmd content
  2. Pass through gen_html._mermaid_fix_block(lines)
  3. Subprocess to Node + mermaid.parse to verify

Test runner is BOTH pytest- and standalone-runnable:
  pytest tools/gen_html/tests/
  python3 tools/gen_html/tests/test_mermaid_fix_cases.py
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'
FIXTURES = pathlib.Path(__file__).resolve().parent / 'fixtures' / 'mermaid'
PARSER = pathlib.Path(__file__).resolve().parent / '_parser_helper.mjs'

# Persistent node_modules workdir (so we don't re-install mermaid every run)
NODE_WORK = pathlib.Path('/tmp/mermaid-scan')

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


def _ensure_node_workdir():
    """Set up persistent node_modules dir with mermaid + jsdom installed."""
    if (NODE_WORK / 'node_modules' / 'mermaid').is_dir() and \
       (NODE_WORK / 'node_modules' / 'jsdom').is_dir():
        return
    NODE_WORK.mkdir(parents=True, exist_ok=True)
    subprocess.run(['npm', 'init', '-y'], cwd=NODE_WORK,
                   capture_output=True, check=False)
    subprocess.run(['npm', 'install', 'mermaid@11', 'jsdom'],
                   cwd=NODE_WORK, capture_output=True, check=False)


def mermaid_parse(content: str) -> tuple[bool, str]:
    """Run content through mermaid.parse via Node helper.
    Returns (ok, stderr_msg)."""
    _ensure_node_workdir()
    # Copy parser helper to NODE_WORK if needed (must resolve mermaid imports
    # from NODE_WORK's node_modules)
    target = NODE_WORK / '_parser_helper.mjs'
    if not target.exists() or target.read_bytes() != PARSER.read_bytes():
        target.write_bytes(PARSER.read_bytes())
    p = subprocess.run(
        ['node', str(target)],
        input=content, capture_output=True, text=True, timeout=30,
    )
    return p.returncode == 0, p.stderr.strip()


def fix_block(content: str) -> str:
    """Apply gen_html._mermaid_fix_block to mermaid content (handle full block)."""
    lines = content.split('\n')
    fixed = gh._mermaid_fix_block(lines)
    return '\n'.join(fixed)


# ─── Case definitions ────────────────────────────────────────────────────

BROKEN_CASES = [
    # name → (description for error reporting)
    ('M01_flowchart_par_and_end',          'flowchart 誤用 sequence par/and/end'),
    ('M02_flowchart_par_and_end_v2',       '同上（不同內容）'),
    ('M03_classDiagram_regex_member',      'classDiagram member 含 regex 特殊字'),
    ('M04_flowchart_edge_label_slash',     'flowchart edge label |...| 內 /'),
    ('M05_flowchart_rect_rgba',            'flowchart 誤用 sequence rect rgba(...)'),
    ('M06_classDiagram_object_curly',      'classDiagram object 屬性引號內 {}'),
    ('M07_stateDiagram_semicolon',         'stateDiagram label 含 ;（statement separator）'),
    ('M08_sequenceDiagram_note_semicolon', 'sequenceDiagram Note label 含 ;'),
    ('M09_classDiagram_quoted_generic',    'classDiagram relationship target "X~T~"'),
    ('M10_stateDiagram_entry_exit_guard',  'stateDiagram entry:/exit:/[guard]'),
    ('M11_sequenceDiagram_unbalanced_alt', 'sequenceDiagram alt 內 +/- 不平衡'),
    ('M12_flowchart_edge_label_parens',    'flowchart edge label |...| 內 (...)'),
]

LEGIT_CASES = [
    ('L01_simple_flowchart',     '單純 flowchart（regression baseline）'),
    ('L02_simple_stateDiagram',  '單純 stateDiagram（regression baseline）'),
    ('L03_simple_sequenceDiagram', '單純 sequenceDiagram（regression baseline）'),
    ('L04_simple_classDiagram',  '單純 classDiagram（regression baseline）'),
    ('L05_simple_graph',         '單純 graph（regression baseline）'),
]


# ─── Orientation directive cases ─────────────────────────────────────
# 直接驗 substring（不需 mermaid parser）

ORIENTATION_BROKEN = [
    # name → (substring expected to be GONE, substring expected to be PRESENT)
    ('O01_flowchart_lr', 'flowchart LR', 'flowchart TD'),
    ('O02_graph_lr',     'graph LR',     'graph TD'),
    ('O03_classDiagram_no_direction', None,
     'direction TB'),  # 加 direction TB
    ('O04_classDiagram_lr_direction', 'direction LR', 'direction TB'),
    ('O05_erDiagram_no_direction', None, 'direction TB'),
]

ORIENTATION_LEGIT = [
    # name → (subscript that should remain unchanged)
    ('OL01_flowchart_td', 'flowchart TD'),
    ('OL02_classDiagram_tb', 'direction TB'),
    ('OL03_sequence_no_direction', 'sequenceDiagram'),
]


def fix_orientation_check(name, expect_gone, expect_present):
    raw = (FIXTURES / f'{name}.mmd').read_text(encoding='utf-8')
    fixed = fix_block(raw)
    if expect_gone is not None and expect_gone in fixed:
        return False, f'expected "{expect_gone}" gone, but still present'
    if expect_present not in fixed:
        return False, f'expected "{expect_present}" present, but missing'
    return True, ''


def legit_orientation_check(name, must_keep):
    raw = (FIXTURES / f'{name}.mmd').read_text(encoding='utf-8')
    fixed = fix_block(raw)
    if must_keep not in fixed:
        return False, f'LEGIT regression: "{must_keep}" disappeared'
    # Also: shouldn't introduce TB directive into a diagram that didn't have it
    # for sequenceDiagram (no concept of direction)
    if name == 'OL03_sequence_no_direction':
        if 'direction' in fixed:
            return False, 'should not add direction to sequenceDiagram'
    return True, ''


def _make_test_orient_broken(name, expect_gone, expect_present):
    def f():
        ok, msg = fix_orientation_check(name, expect_gone, expect_present)
        assert ok, f'[{name}] {msg}'
    f.__name__ = f'test_orient_broken_{name}'
    return f


def _make_test_orient_legit(name, must_keep):
    def f():
        ok, msg = legit_orientation_check(name, must_keep)
        assert ok, f'[{name}] {msg}'
    f.__name__ = f'test_orient_legit_{name}'
    return f


for _name, _gone, _pres in ORIENTATION_BROKEN:
    globals()[f'test_orient_broken_{_name}'] = \
        _make_test_orient_broken(_name, _gone, _pres)

for _name, _keep in ORIENTATION_LEGIT:
    globals()[f'test_orient_legit_{_name}'] = _make_test_orient_legit(_name, _keep)


def _run_case(name: str, expect_pass_after_fix: bool) -> tuple[bool, str]:
    """Returns (test_passed, message)."""
    fixture = FIXTURES / f'{name}.mmd'
    if not fixture.is_file():
        return False, f'fixture missing: {fixture}'
    raw = fixture.read_text(encoding='utf-8')
    fixed = fix_block(raw)
    ok, err = mermaid_parse(fixed)
    if ok == expect_pass_after_fix:
        return True, ''
    if expect_pass_after_fix:
        return False, f'expected PASS but parse failed: {err}'
    return False, 'expected FAIL but parse OK'


# ─── pytest-compatible test functions ────────────────────────────────────

def _make_test_broken(name, desc):
    def f():
        ok, msg = _run_case(name, expect_pass_after_fix=True)
        assert ok, f'[{name}] {desc} — {msg}'
    f.__name__ = f'test_broken_{name}'
    f.__doc__ = f'BROKEN case {name}: {desc} — must parse OK after fix.'
    return f


def _make_test_legit(name, desc):
    def f():
        ok, msg = _run_case(name, expect_pass_after_fix=True)
        assert ok, f'[{name}] {desc} — regression: {msg}'
    f.__name__ = f'test_legit_{name}'
    f.__doc__ = f'LEGIT case {name}: {desc} — must still parse OK after fix.'
    return f


# Generate test functions at module load (so pytest discovers them)
for _name, _desc in BROKEN_CASES:
    globals()[f'test_broken_{_name}'] = _make_test_broken(_name, _desc)

for _name, _desc in LEGIT_CASES:
    globals()[f'test_legit_{_name}'] = _make_test_legit(_name, _desc)


# ─── Standalone runner ────────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'MERMAID FIX TEST SUITE  source={GEN_HTML}')
    print(f'  fixtures: {FIXTURES}')
    print(f'  node workdir: {NODE_WORK}')
    print('=' * 78)
    print('\nEnsuring node_modules ...', flush=True)
    _ensure_node_workdir()

    total = passed = failed = 0
    print('\n[BROKEN — must parse OK after fix]')
    for name, desc in BROKEN_CASES:
        ok, msg = _run_case(name, expect_pass_after_fix=True)
        total += 1
        mark = '✅' if ok else '❌'
        if ok:
            passed += 1
        else:
            failed += 1
        line = f'  {mark} [{name}] {desc}'
        if msg and not ok:
            line += f' → {msg[:140]}'
        print(line)

    print('\n[LEGIT — must still parse OK after fix]')
    for name, desc in LEGIT_CASES:
        ok, msg = _run_case(name, expect_pass_after_fix=True)
        total += 1
        mark = '✅' if ok else '❌'
        if ok:
            passed += 1
        else:
            failed += 1
        line = f'  {mark} [{name}] {desc}'
        if msg and not ok:
            line += f' → {msg[:140]}'
        print(line)

    print('\n[ORIENTATION BROKEN — directive 機械修]')
    for name, gone, pres in ORIENTATION_BROKEN:
        ok, msg = fix_orientation_check(name, gone, pres)
        total += 1
        mark = '✅' if ok else '❌'
        if ok:
            passed += 1
        else:
            failed += 1
        line = f'  {mark} [{name}]'
        if msg and not ok:
            line += f' → {msg}'
        print(line)

    print('\n[ORIENTATION LEGIT — 不能改]')
    for name, keep in ORIENTATION_LEGIT:
        ok, msg = legit_orientation_check(name, keep)
        total += 1
        mark = '✅' if ok else '❌'
        if ok:
            passed += 1
        else:
            failed += 1
        line = f'  {mark} [{name}]'
        if msg and not ok:
            line += f' → {msg}'
        print(line)

    print('\n' + '=' * 78)
    print(f'TOTAL: {passed} PASS / {failed} FAIL  ({total} cases)')
    print('=' * 78)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
