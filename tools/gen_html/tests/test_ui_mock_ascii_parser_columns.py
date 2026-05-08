#!/usr/bin/env python3
"""UI Mock ASCII parser — 2-column split + tables. Stage ⑥ of 11.

Stage ⑥ scope:
  - 2-column split via ┬ in divider + aligned │ in body → page with sidebar
  - Top section (above column split) classified as navbar
  - Left column → sidenav
  - Right column → main content area with its own sub-sections
  - Inline ASCII table detection: 2+ rows with consistent `|` separators
    (ASCII pipes inside the box, not the box `│`) → table primitive

Real-world reference: erp/PDD #2 (Token 管理頁面) and #8 (Admin Table).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)

ascii_parse = gh._ui_mock_ascii_parse


def _find_all(node, type_):
    out = []
    if node.get('type') == type_:
        out.append(node)
    for c in node.get('children', []):
        out.extend(_find_all(c, type_))
    return out


def _flatten_text(node) -> str:
    parts = []
    if isinstance(node.get('value'), str):
        parts.append(node['value'])
    elif isinstance(node.get('value'), list):
        parts.append(' '.join(str(x) for x in node['value']))
    if 'attrs' in node:
        for k in ('title', 'subtitle', 'label'):
            if k in node['attrs']:
                parts.append(str(node['attrs'][k]))
    for child in node.get('children', []):
        parts.append(_flatten_text(child))
    return ' '.join(parts)


# ─── 2-column split detection ────────────────────────────────────────────

def test_two_column_yields_page_with_sidenav():
    text = '''┌──────────────────────────────────┐
│ Top Nav                  [Avatar]│
├──────────┬───────────────────────┤
│ Side Nav │ Content here          │
│          │ More content          │
└──────────┴───────────────────────┘'''
    ast = ascii_parse(text)
    assert ast is not None
    body = ast['children'][0]
    assert body['type'] == 'page', f"expected page, got {body['type']}"
    # Should contain a sidenav
    sidenavs = _find_all(body, 'sidenav')
    assert len(sidenavs) >= 1
    # And the sidenav should reference 'Side Nav'
    flat = _flatten_text(sidenavs[0])
    assert 'Side Nav' in flat


def test_two_column_includes_navbar_for_top_section():
    text = '''┌──────────────────────────────────┐
│ Top Nav                  [Avatar]│
├──────────┬───────────────────────┤
│ Side Nav │ Content               │
└──────────┴───────────────────────┘'''
    ast = ascii_parse(text)
    body = ast['children'][0]
    navbars = _find_all(body, 'navbar')
    assert len(navbars) >= 1
    flat = _flatten_text(navbars[0])
    assert 'Top Nav' in flat


def test_two_column_right_content_preserved():
    text = '''┌──────────────────────────────────┐
│ Top Nav                          │
├──────────┬───────────────────────┤
│ Side     │ Main heading          │
│          │ Body line 1           │
│          │ Body line 2           │
└──────────┴───────────────────────┘'''
    ast = ascii_parse(text)
    flat = _flatten_text(ast['children'][0])
    for s in ['Main heading', 'Body line 1', 'Body line 2']:
        assert s in flat, f'missing {s}'


def test_two_column_with_right_subsection():
    """Right column with internal ─── horizontal divider should split into
    sub-sections (or at least preserve all content)."""
    text = '''┌──────────────────────────────────┐
│ Top Nav                          │
├──────────┬───────────────────────┤
│ Side     │ Header line           │
│          ├───────────────────────┤
│          │ Footer line           │
└──────────┴───────────────────────┘'''
    ast = ascii_parse(text)
    flat = _flatten_text(ast['children'][0])
    assert 'Header line' in flat and 'Footer line' in flat


# ─── ASCII table detection ───────────────────────────────────────────────

def test_table_detected_with_pipe_separators():
    """A run of 2+ lines with consistent `|` column separators → table."""
    text = '''┌─────────────────────────────────────────────────┐
│ Title                                           │
├─────────────────────────────────────────────────┤
│ 描述         | 前綴       | 狀態                │
│ N8N 銷售     | tk_a3f9    | Active              │
│ 庫存監控     | tk_b7c2    | Active              │
└─────────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    tables = _find_all(ast, 'table')
    assert len(tables) >= 1, 'expected at least 1 table'
    t = tables[0]
    cols = t.get('attrs', {}).get('columns', [])
    assert '描述' in cols
    assert '狀態' in cols
    # Rows
    rows = [c for c in t.get('children', []) if c.get('type') == 'row']
    assert len(rows) >= 2
    row_vals_flat = ' '.join(' '.join(map(str, r.get('value') or [])) for r in rows)
    assert 'N8N 銷售' in row_vals_flat and 'tk_a3f9' in row_vals_flat


def test_table_does_not_swallow_non_table_lines():
    """Pipe-separated section sandwiched between plain text — only table
    rows go in the table; plain text remains as separate content."""
    text = '''┌─────────────────────────────────────────┐
│ Plain heading                           │
├─────────────────────────────────────────┤
│ 描述     | 狀態                         │
│ N8N      | Active                       │
├─────────────────────────────────────────┤
│ Footer note                             │
└─────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    flat = _flatten_text(ast['children'][0])
    assert 'Footer note' in flat
    assert 'Plain heading' in flat or ast['children'][0].get('attrs', {}).get('title') == 'Plain heading'
    tables = _find_all(ast, 'table')
    assert len(tables) >= 1


def test_single_pipe_line_is_not_a_table():
    """A single line with one pipe is just text, not a table."""
    text = '''┌──────────────────────┐
│ Foo | Bar            │
└──────────────────────┘'''
    ast = ascii_parse(text)
    tables = _find_all(ast, 'table')
    assert len(tables) == 0, 'single pipe line should not become a table'


def test_table_with_three_columns():
    text = '''┌─────────────────────────────────────────────────────┐
│ T                                                   │
├─────────────────────────────────────────────────────┤
│ 時間            | 動作   | 操作人                    │
│ 10:23:01        | 建立   | mike                      │
│ 09:15:44        | 撤銷   | itadmin                   │
└─────────────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    tables = _find_all(ast, 'table')
    assert tables, 'table should be detected'
    t = tables[0]
    assert len(t['attrs']['columns']) == 3
    rows = [c for c in t['children'] if c.get('type') == 'row']
    assert all(len(r.get('value') or []) == 3 for r in rows)


# ─── Real-world equivalence ──────────────────────────────────────────────

def test_real_world_admin_table_yields_table():
    """Equivalent to erp/PDD #8 — admin audit table inside a card."""
    text = '''┌──────────────────────────────────────────────────────────────┐
│ 🛡 Token 審計日誌                              [⬇ 匯出 CSV]  │
├──────────────────────────────────────────────────────────────┤
│ 時間                | 動作   | 操作人          | IP           │
│ 2026-05-08 10:23:01 | 建立   | mike.chen       | 192.168.1.10 │
│ 2026-05-08 09:15:44 | 撤銷   | itadmin         | 192.168.1.5  │
└──────────────────────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    tables = _find_all(ast, 'table')
    assert len(tables) >= 1
    t = tables[0]
    cols = t.get('attrs', {}).get('columns', [])
    assert any('時間' in c for c in cols)
    assert any('動作' in c for c in cols)
    rows = [c for c in t['children'] if c.get('type') == 'row']
    assert len(rows) == 2
    flat = ' '.join(' '.join(map(str, r.get('value') or [])) for r in rows)
    assert 'mike.chen' in flat


# ─── Standalone runner ───────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'UI MOCK ASCII PARSER — columns + table (stage 6)  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('two_col_page_sidenav', test_two_column_yields_page_with_sidenav),
        ('two_col_navbar', test_two_column_includes_navbar_for_top_section),
        ('two_col_right_content', test_two_column_right_content_preserved),
        ('two_col_subsection', test_two_column_with_right_subsection),
        ('table_pipe_separators', test_table_detected_with_pipe_separators),
        ('table_no_swallow', test_table_does_not_swallow_non_table_lines),
        ('single_pipe_not_table', test_single_pipe_line_is_not_a_table),
        ('table_three_cols', test_table_with_three_columns),
        ('real_world_admin_table', test_real_world_admin_table_yields_table),
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f'  ✅ [{name}]')
        except AssertionError as e:
            failed += 1
            print(f'  ❌ [{name}] {e}')
        except Exception as e:
            failed += 1
            print(f'  ❌ [{name}] EXCEPTION {type(e).__name__}: {e}')
    print('\n' + '=' * 78)
    print(f'TOTAL: {passed} PASS / {failed} FAIL  ({len(tests)} cases)')
    print('=' * 78)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
