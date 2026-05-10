#!/usr/bin/env python3
"""A 群視覺強化 — issues.md A3 / A4。

A3：card / page / modal 邊界從 1px #cbd5e1 → 1.5px #94a3b8（深一階 + 加粗），
header / body 分隔線同步換成 #94a3b8，input 邊框跟著改 #94a3b8。

A4：table 行 padding 0.5/0.625rem → 0.75/0.875rem（行間距 +50%），
行分隔線從 #e2e8f0 → #cbd5e1（深一階），新增 tbody tr:hover 行高亮。

對應 issues.md 核心目標尺 1（清楚）/ 2（美觀）/ 3（表達）。
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'


def _read() -> str:
    return GEN_HTML.read_text(encoding='utf-8')


def _find_rule(css: str, selector: str) -> str | None:
    """Return the body of a single CSS rule matching `selector` exactly,
    or None. Selector may include `:hover` / multi-selector lists. We match
    the rule whose head (text before `{`) contains `selector` as a token."""
    # Normalize whitespace inside selector for matching
    pat = re.compile(
        r'([^{}]*)\{([^{}]*)\}',
        re.DOTALL,
    )
    sel_tokens = [s.strip() for s in selector.split(',')]
    for m in pat.finditer(css):
        head = m.group(1).strip()
        head_tokens = [s.strip() for s in head.split(',')]
        # Match if every requested token appears in this rule's selector list
        if all(any(req == h or req in h for h in head_tokens) for req in sel_tokens):
            return m.group(2)
    return None


# ─── A3: card / page / modal 邊界 ────────────────────────────────────

def test_A3_card_border_uses_94a3b8_and_1_5px():
    """`.umock__card` 邊框 1.5px solid #94a3b8。"""
    css = _read()
    body = _find_rule(css, '.umock__card')
    assert body is not None, '.umock__card rule not found'
    assert '1.5px' in body, f'.umock__card should use 1.5px border; body:\n{body}'
    assert '#94a3b8' in body, f'.umock__card should use #94a3b8; body:\n{body}'


def test_A3_page_border_uses_94a3b8_and_1_5px():
    """`.umock__page` 邊框 1.5px solid #94a3b8。"""
    css = _read()
    body = _find_rule(css, '.umock__page')
    assert body is not None, '.umock__page rule not found'
    assert '1.5px' in body, f'.umock__page should use 1.5px border; body:\n{body}'
    assert '#94a3b8' in body, f'.umock__page should use #94a3b8; body:\n{body}'


def test_A3_modal_border_uses_94a3b8_and_1_5px():
    """`.umock__modal` 邊框 1.5px solid #94a3b8。"""
    css = _read()
    body = _find_rule(css, '.umock__modal')
    assert body is not None, '.umock__modal rule not found'
    assert '1.5px' in body, f'.umock__modal should use 1.5px border; body:\n{body}'
    assert '#94a3b8' in body, f'.umock__modal should use #94a3b8; body:\n{body}'


def test_A3_card_title_border_bottom_94a3b8():
    """`.umock__card-title` 底線改 1.5px solid #94a3b8（跟外框同調）。"""
    css = _read()
    body = _find_rule(css, '.umock__card-title')
    assert body is not None, '.umock__card-title rule not found'
    assert '#94a3b8' in body, \
        f'.umock__card-title should use #94a3b8 border; body:\n{body}'


def test_A3_page_title_border_bottom_94a3b8():
    """`.umock__page-title` 底線改 1.5px solid #94a3b8。"""
    css = _read()
    body = _find_rule(css, '.umock__page-title')
    assert body is not None, '.umock__page-title rule not found'
    assert '#94a3b8' in body, \
        f'.umock__page-title should use #94a3b8 border; body:\n{body}'


def test_A3_modal_titlebar_border_bottom_94a3b8():
    """`.umock__modal-titlebar` 底線 1.5px solid #94a3b8。"""
    css = _read()
    body = _find_rule(css, '.umock__modal-titlebar')
    assert body is not None, '.umock__modal-titlebar rule not found'
    assert '#94a3b8' in body, \
        f'.umock__modal-titlebar should use #94a3b8 border; body:\n{body}'


def test_A3_input_border_94a3b8():
    """`.umock__input, .umock__search` 邊框換 #94a3b8（中灰）。"""
    css = _read()
    body = _find_rule(css, '.umock__input, .umock__search')
    assert body is not None, '.umock__input, .umock__search rule not found'
    assert '#94a3b8' in body, \
        f'.umock__input border should use #94a3b8; body:\n{body}'


def test_A3_no_residual_cbd5e1_on_card_or_modal_or_page():
    """A3 改完，card/page/modal 三條 rule body 內不應再含 #cbd5e1。"""
    css = _read()
    for sel in ('.umock__page', '.umock__modal', '.umock__card'):
        body = _find_rule(css, sel)
        assert body is not None, f'{sel} rule not found'
        assert '#cbd5e1' not in body, \
            f'{sel} should not retain old #cbd5e1; body:\n{body}'


# ─── A4: table 行間距 / 分隔線 / hover ──────────────────────────────

def test_A4_table_cell_padding_relaxed():
    """`.umock__table th, .umock__table td` padding 0.75rem 0.875rem。"""
    css = _read()
    body = _find_rule(css, '.umock__table th, .umock__table td')
    assert body is not None, '.umock__table th, td rule not found'
    assert '0.75rem 0.875rem' in body, \
        f'cell padding should be 0.75rem 0.875rem; body:\n{body}'


def test_A4_table_row_separator_uses_cbd5e1():
    """`.umock__table th, .umock__table td` border-bottom 1px solid #cbd5e1。"""
    css = _read()
    body = _find_rule(css, '.umock__table th, .umock__table td')
    assert body is not None, '.umock__table th, td rule not found'
    assert '#cbd5e1' in body, \
        f'row separator should use #cbd5e1; body:\n{body}'


def test_A4_table_no_residual_e2e8f0_in_cell_rule():
    """A4 改完，table 行 rule body 不殘留 #e2e8f0（避免回退到太淡）。"""
    css = _read()
    body = _find_rule(css, '.umock__table th, .umock__table td')
    assert body is not None, '.umock__table th, td rule not found'
    assert '#e2e8f0' not in body, \
        f'cell rule should not retain old #e2e8f0; body:\n{body}'


def test_A4_table_hover_row_highlight_present():
    """`.umock__table tbody tr:hover` 行高亮存在。"""
    css = _read()
    # Match the hover rule head loosely (may be on one or two lines)
    pat = re.compile(
        r'\.umock__table\s+tbody\s+tr:hover\s*\{([^{}]*)\}',
        re.DOTALL,
    )
    m = pat.search(css)
    assert m is not None, '.umock__table tbody tr:hover rule missing'
    body = m.group(1)
    assert 'background' in body, \
        f'hover rule should set background color; body:\n{body}'


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print(f'A GROUP — visuals (A3 + A4)  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('A3_card_border_uses_94a3b8_and_1_5px', test_A3_card_border_uses_94a3b8_and_1_5px),
        ('A3_page_border_uses_94a3b8_and_1_5px', test_A3_page_border_uses_94a3b8_and_1_5px),
        ('A3_modal_border_uses_94a3b8_and_1_5px', test_A3_modal_border_uses_94a3b8_and_1_5px),
        ('A3_card_title_border_bottom_94a3b8', test_A3_card_title_border_bottom_94a3b8),
        ('A3_page_title_border_bottom_94a3b8', test_A3_page_title_border_bottom_94a3b8),
        ('A3_modal_titlebar_border_bottom_94a3b8', test_A3_modal_titlebar_border_bottom_94a3b8),
        ('A3_input_border_94a3b8', test_A3_input_border_94a3b8),
        ('A3_no_residual_cbd5e1_on_card_or_modal_or_page', test_A3_no_residual_cbd5e1_on_card_or_modal_or_page),
        ('A4_table_cell_padding_relaxed', test_A4_table_cell_padding_relaxed),
        ('A4_table_row_separator_uses_cbd5e1', test_A4_table_row_separator_uses_cbd5e1),
        ('A4_table_no_residual_e2e8f0_in_cell_rule', test_A4_table_no_residual_e2e8f0_in_cell_rule),
        ('A4_table_hover_row_highlight_present', test_A4_table_hover_row_highlight_present),
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
