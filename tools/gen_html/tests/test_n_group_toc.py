#!/usr/bin/env python3
"""N 群 — 每頁 TOC（Table of Contents）標配 TDD tests.

設計（user 拍板版本）：
- 左 sidebar 兩 tab：「📁 文件」（預設 active）+「📑 本頁目錄」
- TOC 深度：H2 + H3
- Scroll-spy 高亮
- 收合按鈕（localStorage 記憶）
- 手機 RWD 自動收合
- source manual TOC 不破壞、sidebar TOC tab 永遠存在
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh_n', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


# ─── Helpers ───────────────────────────────────────────────────────────

SAMPLE_MD = '''# Sample

## §1. Overview

Intro.

## §2. Architecture

Stuff.

### §2.1 Components

Detail.

#### §2.1.1 Detail H4

H4 should NOT appear in TOC.

## §3. API

API content.

### §3.1 Endpoints

Endpoint content.
'''

SHORT_MD = '''# Short

Just one paragraph, no H2 sections.
'''

MD_WITH_MANUAL_TOC = '''# Doc with Manual TOC

## Table of Contents

- [Overview](#overview)
- [Detail](#detail)

## Overview

Intro.

## Detail

Detail content.
'''


def _read_app_js() -> str:
    """Canonical source of assets/app.js lives in the gendoc repo at
    `docs/pages/assets/app.js`; setup copies it into every target's
    pages/assets/ dir. We test the source-of-truth, not a downstream copy."""
    app_js = REPO / 'docs' / 'pages' / 'assets' / 'app.js'
    return app_js.read_text(encoding='utf-8') if app_js.is_file() else ''


def _read_gen_html_text() -> str:
    return GEN_HTML.read_text(encoding='utf-8')


# ─── 1: sidebar has two tabs ───────────────────────────────────────────

def test_N1_sidebar_has_two_tabs():
    """sidebar 含 [data-tab="docs"] 跟 [data-tab="toc"] 兩個 tab button。"""
    sidebar = gh.make_sidebar(
        doc_pages=[('idea', 'IDEA', '💡'), ('edd', 'EDD', '🏗️')],
        server_diagrams=[], frontend_diagrams=[], sub_docs={},
        current='edd',
    )
    assert re.search(r'<button[^>]*data-tab="docs"', sidebar), \
        f'docs tab missing; sidebar:\n{sidebar[:600]}'
    assert re.search(r'<button[^>]*data-tab="toc"', sidebar), \
        f'toc tab missing; sidebar:\n{sidebar[:600]}'


def test_N1_doc_list_in_docs_panel():
    """原本 sidebar 文件 link 進 `<div data-panel="docs">`。"""
    sidebar = gh.make_sidebar(
        doc_pages=[('idea', 'IDEA', '💡'), ('edd', 'EDD', '🏗️')],
        server_diagrams=[], frontend_diagrams=[], sub_docs={},
        current='edd',
    )
    docs_panel = re.search(
        r'<div[^>]*data-panel="docs"[^>]*>(.+?)</div>(?:\s*<div|\s*</aside)',
        sidebar, re.DOTALL,
    )
    assert docs_panel, f'docs panel missing; sidebar:\n{sidebar[:800]}'
    panel_html = docs_panel.group(1)
    assert 'idea.html' in panel_html or 'IDEA' in panel_html, \
        f'doc links missing in docs panel; got:\n{panel_html[:400]}'


def test_N1_toc_panel_exists():
    """sidebar 含 `<div data-panel="toc">` (永遠存在，即便該頁無 H2)。"""
    sidebar = gh.make_sidebar(
        doc_pages=[('idea', 'IDEA', '💡')],
        server_diagrams=[], frontend_diagrams=[], sub_docs={},
        current='idea',
    )
    assert re.search(r'<div[^>]*data-panel="toc"', sidebar), \
        f'toc panel missing; sidebar:\n{sidebar[:600]}'


def test_N1_active_tab_default_docs():
    """docs tab 預設帶 active class。"""
    sidebar = gh.make_sidebar(
        doc_pages=[('idea', 'IDEA', '💡')], server_diagrams=[],
        frontend_diagrams=[], sub_docs={}, current='idea',
    )
    # docs tab 必含 active；toc tab 不含
    docs_tab = re.search(r'<button[^>]*data-tab="docs"[^>]*>', sidebar)
    toc_tab = re.search(r'<button[^>]*data-tab="toc"[^>]*>', sidebar)
    assert docs_tab and 'active' in docs_tab.group(0), \
        f'docs tab not default-active: {docs_tab.group(0) if docs_tab else None}'
    assert toc_tab and 'active' not in toc_tab.group(0), \
        f'toc tab should not be active by default: {toc_tab.group(0) if toc_tab else None}'


def test_N1_collapse_toggle_button_exists():
    """sidebar 含收合 toggle button。"""
    sidebar = gh.make_sidebar(
        doc_pages=[('idea', 'IDEA', '💡')], server_diagrams=[],
        frontend_diagrams=[], sub_docs={}, current='idea',
    )
    assert re.search(r'<button[^>]*class="[^"]*sidebar__toggle', sidebar), \
        f'sidebar__toggle button missing; sidebar:\n{sidebar[:600]}'


# ─── 2: TOC builder ───────────────────────────────────────────────────

def test_N1_toc_builder_extracts_h2_h3():
    """`_build_toc(html)` 抽 `<h2 id="..">` `<h3 id="..">`，產 list HTML。"""
    html = '''<h1 id="title">Title</h1>
<h2 id="overview">Overview</h2>
<p>p1</p>
<h2 id="arch">Architecture</h2>
<h3 id="ctx">Context</h3>
<h4 id="detail">Detail</h4>
'''
    toc = gh._build_toc(html)
    assert 'href="#overview"' in toc
    assert 'href="#arch"' in toc
    assert 'href="#ctx"' in toc


def test_N1_h4_not_in_toc():
    """H4 anchor 不出現在 TOC。"""
    html = '<h2 id="a">A</h2><h3 id="b">B</h3><h4 id="c">C</h4>'
    toc = gh._build_toc(html)
    assert 'href="#c"' not in toc, f'H4 should not appear in TOC; got:\n{toc}'


def test_N1_toc_builder_handles_no_headings():
    """無 H2 時也產出（可空 list 或提示，但不爆錯）。"""
    html = '<p>just text, no headings</p>'
    toc = gh._build_toc(html)
    # Either empty result or minimal non-throwing output — both acceptable
    assert isinstance(toc, str), f'_build_toc should return str; got {type(toc)}'


# ─── 3: integration via md_to_html / page rendering ────────────────────

def test_N1_manual_toc_in_main_preserved():
    """source markdown 含 `## Table of Contents` → main 內仍渲染 manual TOC。"""
    html = gh.md_to_html(MD_WITH_MANUAL_TOC)
    # manual TOC heading 應出現
    assert re.search(r'<h2[^>]*>\s*Table of Contents\s*</h2>', html), \
        f'manual TOC heading should be preserved in main; html:\n{html[:600]}'


# ─── 4: app.js localStorage + IntersectionObserver ─────────────────────

def test_N1_localstorage_key_in_js():
    """app.js 有 localStorage 邏輯處理 sidebar collapse 狀態。"""
    js = _read_app_js()
    if not js:
        assert False, 'gendoc canonical app.js not readable at docs/pages/assets/app.js'
    assert 'gendoc:sidebar-collapsed' in js, \
        f'app.js should contain localStorage key gendoc:sidebar-collapsed'


def test_N1_scrollspy_intersection_observer_in_js():
    """app.js 含 IntersectionObserver + scroll-spy active class 切換邏輯。"""
    js = _read_app_js()
    if not js:
        assert False, 'gendoc canonical app.js not readable at docs/pages/assets/app.js'
    assert 'IntersectionObserver' in js, \
        f'app.js should use IntersectionObserver for scroll-spy'
    # toc__link active toggling
    assert 'toc__link' in js, \
        f'app.js should reference .toc__link for scroll-spy'


# ─── 5: CSS — RWD mobile auto-collapse ─────────────────────────────────

def test_N1_rwd_mobile_collapse_css():
    """gen_html.py 內聯 `<style>` 含 `@media (max-width: 768px)` 對
    sidebar 的 default-collapse rule。"""
    text = _read_gen_html_text()
    # Look for media query for mobile that targets sidebar
    mobile_rules = re.findall(
        r'@media[^{]*max-width:\s*768px[^{]*\{[^}]*\}',
        text, re.DOTALL,
    )
    assert any('sidebar' in r.lower() for r in mobile_rules), \
        f'no @media (max-width: 768px) rule targeting sidebar; mobile_rules:\n{mobile_rules}'


def test_N1_tab_panel_css_exists():
    """`.sidebar__tab` `.sidebar__panel` `.sidebar-collapsed` CSS rules 存在。"""
    text = _read_gen_html_text()
    assert re.search(r'\.sidebar__tab\b', text), '.sidebar__tab CSS missing'
    assert re.search(r'\.sidebar__panel\b', text), '.sidebar__panel CSS missing'
    assert re.search(r'\.sidebar-collapsed\b', text), '.sidebar-collapsed CSS missing'


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print(f'N GROUP — TOC + sidebar tabs  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('N1_sidebar_has_two_tabs', test_N1_sidebar_has_two_tabs),
        ('N1_doc_list_in_docs_panel', test_N1_doc_list_in_docs_panel),
        ('N1_toc_panel_exists', test_N1_toc_panel_exists),
        ('N1_active_tab_default_docs', test_N1_active_tab_default_docs),
        ('N1_collapse_toggle_button_exists', test_N1_collapse_toggle_button_exists),
        ('N1_toc_builder_extracts_h2_h3', test_N1_toc_builder_extracts_h2_h3),
        ('N1_h4_not_in_toc', test_N1_h4_not_in_toc),
        ('N1_toc_builder_handles_no_headings', test_N1_toc_builder_handles_no_headings),
        ('N1_manual_toc_in_main_preserved', test_N1_manual_toc_in_main_preserved),
        ('N1_localstorage_key_in_js', test_N1_localstorage_key_in_js),
        ('N1_scrollspy_intersection_observer_in_js', test_N1_scrollspy_intersection_observer_in_js),
        ('N1_rwd_mobile_collapse_css', test_N1_rwd_mobile_collapse_css),
        ('N1_tab_panel_css_exists', test_N1_tab_panel_css_exists),
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
