#!/usr/bin/env python3
"""UI Mock — real PET/ERP fixture validation. Stage ⑩ of 11.

Loads the 10 actual UI-mockup ASCII blocks extracted from pet/erp PDD/
FRONTEND/VDD into `fixtures/ui_mock_real/M01..M10.txt` and asserts each
one converts (via gen_html.md_to_html with the box-content wrapped in a
fenced block) into expected primitives:

  M01 pet/PDD       layered architecture        → layered-arch (mermaid)
  M02 erp/PDD       page + sidebar + table      → page + sidenav + table
  M03 erp/PDD       create-token modal          → modal + field + actions
  M04 erp/PDD       success modal               → modal + actions
  M05 erp/PDD       confirm-delete modal        → modal + actions
  M06 erp/PDD       quick-start guide           → card with sections
  M07 erp/PDD       API test console            → card + form + code-block
  M08 erp/PDD       audit-log table             → card with table
  M09 erp/FRONTEND  test pyramid                → pyramid (svg)
  M10 erp/VDD       descriptor card             → card

The assertion bar is "no raw box-drawing chars in HTML and at least one
expected umock_/svg/mermaid class is present" — full-fidelity element
parity is best-effort and not enforced (heuristic ASCII parsing has a
known accuracy ceiling).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'
FIXTURES = pathlib.Path(__file__).resolve().parent / 'fixtures' / 'ui_mock_real'

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


def render_fixture(name: str) -> str:
    """Wrap fixture content in a fenced block and run through md_to_html."""
    raw = (FIXTURES / name).read_text()
    md = '```\n' + raw.rstrip() + '\n```'
    return gh.md_to_html(md)


# Per-fixture expectations: (name, [must_contain_substrings])
CASES = [
    ('M01_pet_PDD.txt',     ['flowchart TB', 'Presentation Layer', 'Application Layer']),
    ('M02_erp_PDD.txt',     ['umock__page', 'umock__sidenav', 'umock__table', 'API Token']),
    ('M03_erp_PDD.txt',     ['umock__modal', 'umock__field', 'umock__btn', '建立 API Token']),
    ('M04_erp_PDD.txt',     ['umock__modal', 'umock__btn', 'Token']),
    ('M05_erp_PDD.txt',     ['umock__modal', 'umock__btn', 'umock__btn--danger', '撤銷']),
    ('M06_erp_PDD.txt',     ['Quick Start', 'umock__']),  # quick-start guide
    ('M07_erp_PDD.txt',     ['POC API Test', 'umock__']),
    ('M08_erp_PDD.txt',     ['umock__table', '審計日誌']),
    ('M09_erp_FRONTEND.txt',['<svg', '<polygon', 'E2E Tests', 'Unit Tests']),
    ('M10_erp_VDD.txt',     ['umock__', 'N8N 銷售報表']),
]


def test_no_raw_box_chars_in_any_fixture_output():
    """Across ALL 10 fixtures, no raw ┌┐└┘├┤ should leak into rendered HTML."""
    leaks = []
    for name, _ in CASES:
        html = render_fixture(name)
        for c in '┌┐└┘├┤':
            if c in html:
                leaks.append((name, c))
    assert not leaks, f'box-drawing leakage: {leaks}'


def test_each_fixture_produces_expected_substrings():
    failures = []
    for name, expected in CASES:
        html = render_fixture(name)
        for s in expected:
            if s not in html:
                failures.append(f'{name}: missing {s!r}')
    assert not failures, '\n'.join(failures)


def test_summary_report():
    """Print summary of what each fixture produced — for debugging only."""
    print()
    for name, _ in CASES:
        html = render_fixture(name)
        n_modals = html.count('umock__modal')
        n_cards = html.count('umock__card')
        n_pages = html.count('umock__page')
        n_tables = html.count('umock__table')
        n_buttons = html.count('umock__btn')
        n_polygons = html.count('<polygon')
        n_mermaid = html.count('flowchart TB')
        print(f'  {name}: '
              f'modal={n_modals} card={n_cards} page={n_pages} '
              f'table={n_tables} btn={n_buttons} '
              f'svg-poly={n_polygons} mermaid={n_mermaid}')


def main() -> int:
    print('=' * 78)
    print(f'UI MOCK REAL FIXTURES (stage 10)  source={GEN_HTML}')
    print(f'  fixtures: {FIXTURES}')
    print('=' * 78)
    tests = [
        ('no_raw_box_chars', test_no_raw_box_chars_in_any_fixture_output),
        ('expected_substrings', test_each_fixture_produces_expected_substrings),
        ('summary', test_summary_report),
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f'  ✅ [{name}]')
        except AssertionError as e:
            failed += 1
            print(f'  ❌ [{name}]\n{e}')
        except Exception as e:
            failed += 1
            print(f'  ❌ [{name}] EXCEPTION {type(e).__name__}: {e}')
    print('\n' + '=' * 78)
    print(f'TOTAL: {passed} PASS / {failed} FAIL  ({len(tests)} cases)')
    print('=' * 78)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
