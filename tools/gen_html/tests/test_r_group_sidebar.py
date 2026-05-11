#!/usr/bin/env python3
"""R 群 — sidebar 文件 label 移除 + 全展開無 scrollbar + main 留白縮減.

設計（user 拍板版本，依 sandbox r-group-sidebar/after.png）：
1. `make_sidebar()` 內 docs panel 第一個 `<div class="sidebar__label">文件</div>`
   要移除（跟 tab `📁 文件` 重複）
2. inline `<style>` `.sidebar` 改 `height: auto; overflow: visible`
   （取消 style.css 固定 viewport 高 + scrollbar）
3. inline `<style>` `.sidebar__panel` 改 `overflow: visible`
   （取消 N1 原 `overflow-y: auto`）
4. inline `<style>` 新增 `.doc-content { padding-top: 1rem }`
   （main 上方留白從 2.5rem 縮成 1rem）
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh_r', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


def _read() -> str:
    return GEN_HTML.read_text(encoding='utf-8')


def _inline_style(text: str) -> str:
    m = re.search(r'HTML_TEMPLATE\s*=\s*"""(.*?)"""', text, re.DOTALL)
    tpl = m.group(1) if m else ''
    m = re.search(r'<style>(.*?)</style>', tpl, re.DOTALL)
    return m.group(1) if m else ''


# ─── 1: docs panel 內第一個「文件」label 移除 ─────────────────────────

def test_R1_sidebar_docs_panel_no_redundant_label():
    """`make_sidebar()` 產出的 docs panel 不應再含 `<div class="sidebar__label">文件</div>`
    （已由 tab `📁 文件` 表示）."""
    sidebar = gh.make_sidebar(
        doc_pages=[('idea', 'IDEA', '💡'), ('edd', 'EDD', '🏗️')],
        server_diagrams=[], frontend_diagrams=[], sub_docs={},
        current='idea',
    )
    # Extract docs panel (the first sidebar__panel)
    m = re.search(
        r'<div[^>]*data-panel="docs"[^>]*>(.*?)</div>\s*<div[^>]*data-panel="toc"',
        sidebar, re.DOTALL,
    )
    assert m, 'docs panel not found in sidebar HTML'
    docs_panel = m.group(1)
    # The redundant "文件" label should NOT appear inside docs panel.
    assert '<div class="sidebar__label">文件</div>' not in docs_panel, \
        f'docs panel must not have redundant "文件" label; got:\n{docs_panel[:500]}'


def test_R1_sidebar_subdir_labels_still_present():
    """Regression — 其他 sidebar__label（subdir / req / diagrams）仍應保留。"""
    sidebar = gh.make_sidebar(
        doc_pages=[('idea', 'IDEA', '💡')],
        server_diagrams=[('class-a', 'Class A', '📐', None)],
        frontend_diagrams=[], sub_docs={}, current='idea',
    )
    # Server UML label should still be present (subdir grouping)
    assert 'Server UML' in sidebar or 'sidebar__label' in sidebar, \
        f'subdir labels (Server UML / Frontend UML) should still appear'


# ─── 2: sidebar overflow visible / height auto ──────────────────────

def test_R1_sidebar_overflow_visible():
    """inline `<style>` `.sidebar` 改 `overflow: visible`（取消 N1 hidden）。"""
    style = _inline_style(_read())
    rule = re.search(r'\.sidebar\s*\{[^}]*display\s*:\s*flex[^}]*\}', style)
    assert rule, 'N1 inline .sidebar rule not found'
    body = rule.group(0)
    assert 'overflow' in body and 'visible' in body, \
        f'.sidebar must use overflow: visible; body:\n{body}'
    assert 'overflow: hidden' not in body and 'overflow:hidden' not in body, \
        f'.sidebar must NOT use overflow: hidden; body:\n{body}'


def test_R1_sidebar_height_viewport_fit():
    """inline `<style>` `.sidebar` 加 `height: calc(100vh - 56px)`
    — T 群升級後 sidebar sticky 占 viewport 下方剩餘空間（取代 R 群原
    `height: auto` 設計）。R 群「全展開無 scrollbar」spirit 由 T 群
    `scrollbar-width: thin` + 6px webkit scrollbar 接手。"""
    style = _inline_style(_read())
    rule = re.search(r'\.sidebar\s*\{[^}]*display\s*:\s*flex[^}]*\}', style)
    assert rule, 'T-group inline .sidebar rule not found'
    body = rule.group(0)
    assert re.search(r'height\s*:\s*calc\(\s*100vh\s*-\s*56px\s*\)', body), \
        f'.sidebar must use height: calc(100vh - 56px) for T-group sticky fit; body:\n{body}'


# ─── 3: sidebar__panel overflow visible ─────────────────────────────

def test_R1_sidebar_panel_internal_scroll():
    """inline `<style>` `.sidebar__panel` 改 `overflow-y: auto` + scrollbar-width: thin
    — T 群升級後 panel 自己內部捲，scrollbar 細到 6px 幾乎不擾眼（取代 R 群原
    `overflow: visible` 設計）。Tabs 因此能釘 sidebar 頂端不被 panel scroll 帶走。"""
    style = _inline_style(_read())
    rule = re.search(
        r'\.sidebar__panel\s*\{[^}]*flex\s*:\s*1\s+1\s+auto[^}]*\}', style,
    )
    assert rule, 'T-group .sidebar__panel rule (flex: 1 1 auto) not found'
    body = rule.group(0)
    assert 'overflow-y: auto' in body or 'overflow-y:auto' in body, \
        f'.sidebar__panel must use overflow-y: auto (T-group internal scroll); body:\n{body}'
    assert 'scrollbar-width: thin' in body or 'scrollbar-width:thin' in body, \
        f'.sidebar__panel must use scrollbar-width: thin to keep R-group "no visual scrollbar" spirit; body:\n{body}'


# ─── 4: main 上方留白縮減 ────────────────────────────────────────────

def test_R1_doc_content_padding_top_reduced():
    """inline `<style>` 含 `.doc-content { padding-top: 1rem }`（從 2.5rem 縮成 1rem）。"""
    style = _inline_style(_read())
    assert re.search(r'\.doc-content\s*\{[^}]*padding-top\s*:\s*1rem', style), \
        f'.doc-content must have padding-top: 1rem to reduce gap below banner'


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print('R GROUP — sidebar 文件 label 移除 + 全展開無 scrollbar + main 留白縮減')
    print('=' * 78)
    tests = [
        ('R1_sidebar_docs_panel_no_redundant_label', test_R1_sidebar_docs_panel_no_redundant_label),
        ('R1_sidebar_subdir_labels_still_present', test_R1_sidebar_subdir_labels_still_present),
        ('R1_sidebar_overflow_visible', test_R1_sidebar_overflow_visible),
        ('R1_sidebar_height_viewport_fit', test_R1_sidebar_height_viewport_fit),
        ('R1_sidebar_panel_internal_scroll', test_R1_sidebar_panel_internal_scroll),
        ('R1_doc_content_padding_top_reduced', test_R1_doc_content_padding_top_reduced),
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
