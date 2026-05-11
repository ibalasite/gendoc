#!/usr/bin/env python3
"""T 群 — sidebar sticky 跟著 viewport 卷，tabs 釘 sidebar 頂端不卷.

設計（user 拍板版本，依 sandbox t-group-sidebar-sticky/after-v2-scrolled.png）：

問題：N1+R 把 `.sidebar` 設成 `position: relative; height: auto; overflow: visible`
— sidebar 跟著整頁卷下去就看不見。User 要求黑色 top-nav 跟 sidebar 都能黏住
viewport，本文可獨立卷動。

解法：
1. `.sidebar { position: sticky; top: 56px }` — top-nav 下方黏住
2. `.sidebar { height: calc(100vh - 56px) }` — 占滿 viewport 下方剩餘空間
3. `.sidebar { align-self: start }` — grid item 不被 row 拉長
4. `.sidebar { display: flex; flex-direction: column; overflow: visible }` —
   wrapper 自己不卷（避免 tabs 被 panel scroll 帶走）
5. `.sidebar__tabs { flex: 0 0 auto }` — tabs row 固定在頂端不被擠壓
6. `.sidebar__panel { flex: 1 1 auto; overflow-y: auto }` — panel 自己捲，
   scrollbar 細到 hover 才看得到
7. R 群「全展開無 scrollbar」spirit 改成「scrollbar thin / auto-hide」，
   `.sidebar__panel::-webkit-scrollbar { width: 6px }` 視覺上幾乎不擾眼
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'


def _read() -> str:
    return GEN_HTML.read_text(encoding='utf-8')


def _inline_style(text: str) -> str:
    m = re.search(r'HTML_TEMPLATE\s*=\s*"""(.*?)"""', text, re.DOTALL)
    tpl = m.group(1) if m else ''
    m = re.search(r'<style>(.*?)</style>', tpl, re.DOTALL)
    return m.group(1) if m else ''


def _sidebar_rule(style: str) -> str:
    """The N1/Q1/R1 inline `.sidebar { ... }` rule body (without selector)."""
    m = re.search(
        r'\.sidebar\s*\{([^}]*?display\s*:\s*flex[^}]*?)\}', style,
    )
    return m.group(1) if m else ''


def _sidebar_tabs_rule(style: str) -> str:
    m = re.search(
        r'\.sidebar__tabs\s*\{([^}]*?display\s*:\s*flex[^}]*?)\}', style,
    )
    return m.group(1) if m else ''


def _sidebar_panel_rule(style: str) -> str:
    """The base `.sidebar__panel { display: none; flex: ... }` rule body."""
    m = re.search(
        r'\.sidebar__panel\s*\{([^}]*?display\s*:\s*none[^}]*?)\}', style,
    )
    return m.group(1) if m else ''


# ─── 1: .sidebar position sticky + viewport-fit ───────────────────────

def test_T1_sidebar_position_sticky():
    """`.sidebar { position: sticky }` — 取代 N1 的 `position: relative`."""
    style = _inline_style(_read())
    body = _sidebar_rule(style)
    assert body, '.sidebar rule not found in inline <style>'
    assert re.search(r'position\s*:\s*sticky', body), \
        f'.sidebar must use position: sticky (T-group); body:\n{body}'
    assert 'position: relative' not in body and 'position:relative' not in body, \
        f'.sidebar must NOT use position: relative (replaced by sticky); body:\n{body}'


def test_T1_sidebar_top_below_top_nav():
    """`.sidebar { top: 56px }` — sticky 啟動位置在 top-nav 下方."""
    style = _inline_style(_read())
    body = _sidebar_rule(style)
    assert re.search(r'top\s*:\s*56px', body), \
        f'.sidebar must have top: 56px to sit below sticky top-nav; body:\n{body}'


def test_T1_sidebar_height_viewport_fit():
    """`.sidebar { height: calc(100vh - 56px) }` — 占滿 viewport 下方剩餘高度."""
    style = _inline_style(_read())
    body = _sidebar_rule(style)
    assert re.search(r'height\s*:\s*calc\(\s*100vh\s*-\s*56px\s*\)', body), \
        f'.sidebar must have height: calc(100vh - 56px) for sticky fit; body:\n{body}'


def test_T1_sidebar_align_self_start():
    """`.sidebar { align-self: start }` — grid item 不被 row 拉長到 row 高."""
    style = _inline_style(_read())
    body = _sidebar_rule(style)
    assert re.search(r'align-self\s*:\s*start', body), \
        f'.sidebar must have align-self: start (grid context); body:\n{body}'


def test_T1_sidebar_wrapper_no_scroll():
    """`.sidebar` 自己 `overflow: visible`，scroll 由 `.sidebar__panel` 處理."""
    style = _inline_style(_read())
    body = _sidebar_rule(style)
    assert 'overflow: visible' in body or 'overflow:visible' in body, \
        f'.sidebar wrapper must use overflow: visible (panel scrolls, not wrapper); body:\n{body}'


# ─── 2: .sidebar__tabs flex 0 0 auto (anchored at top) ────────────────

def test_T1_sidebar_tabs_flex_fixed():
    """`.sidebar__tabs { flex: 0 0 auto }` — tabs 永遠在 sidebar 頂端不卷."""
    style = _inline_style(_read())
    body = _sidebar_tabs_rule(style)
    assert body, '.sidebar__tabs rule not found in inline <style>'
    assert re.search(r'flex\s*:\s*0\s+0\s+auto', body), \
        f'.sidebar__tabs must have flex: 0 0 auto (anchored top); body:\n{body}'


# ─── 3: .sidebar__panel scrollable interior ───────────────────────────

def test_T1_sidebar_panel_flex_grow():
    """`.sidebar__panel { flex: 1 1 auto }` — 占滿 sidebar 剩餘空間."""
    style = _inline_style(_read())
    body = _sidebar_panel_rule(style)
    assert body, '.sidebar__panel base rule not found in inline <style>'
    assert re.search(r'flex\s*:\s*1\s+1\s+auto', body), \
        f'.sidebar__panel must use flex: 1 1 auto to fill sidebar; body:\n{body}'


def test_T1_sidebar_panel_overflow_y_auto():
    """`.sidebar__panel { overflow-y: auto }` — panel 內部捲，tabs 不卷."""
    style = _inline_style(_read())
    body = _sidebar_panel_rule(style)
    assert ('overflow-y: auto' in body or 'overflow-y:auto' in body), \
        f'.sidebar__panel must use overflow-y: auto (internal scroll); body:\n{body}'


def test_T1_sidebar_panel_scrollbar_thin():
    """`.sidebar__panel { scrollbar-width: thin }` — 內部 scrollbar 細到幾乎不擾眼."""
    style = _inline_style(_read())
    body = _sidebar_panel_rule(style)
    assert 'scrollbar-width: thin' in body or 'scrollbar-width:thin' in body, \
        f'.sidebar__panel must use scrollbar-width: thin; body:\n{body}'


def test_T1_sidebar_panel_webkit_scrollbar_narrow():
    """`.sidebar__panel::-webkit-scrollbar { width: 6px }` —
    Chromium 系列瀏覽器顯示細 scrollbar."""
    style = _inline_style(_read())
    assert re.search(
        r'\.sidebar__panel::-webkit-scrollbar\s*\{[^}]*width\s*:\s*6px', style,
    ), f'.sidebar__panel::-webkit-scrollbar must be 6px wide'


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print('T GROUP — sidebar sticky + tabs anchored + panel internal scroll')
    print('=' * 78)
    tests = [
        ('T1_sidebar_position_sticky', test_T1_sidebar_position_sticky),
        ('T1_sidebar_top_below_top_nav', test_T1_sidebar_top_below_top_nav),
        ('T1_sidebar_height_viewport_fit', test_T1_sidebar_height_viewport_fit),
        ('T1_sidebar_align_self_start', test_T1_sidebar_align_self_start),
        ('T1_sidebar_wrapper_no_scroll', test_T1_sidebar_wrapper_no_scroll),
        ('T1_sidebar_tabs_flex_fixed', test_T1_sidebar_tabs_flex_fixed),
        ('T1_sidebar_panel_flex_grow', test_T1_sidebar_panel_flex_grow),
        ('T1_sidebar_panel_overflow_y_auto', test_T1_sidebar_panel_overflow_y_auto),
        ('T1_sidebar_panel_scrollbar_thin', test_T1_sidebar_panel_scrollbar_thin),
        ('T1_sidebar_panel_webkit_scrollbar_narrow', test_T1_sidebar_panel_webkit_scrollbar_narrow),
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
