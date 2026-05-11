#!/usr/bin/env python3
"""Q 群 — header 兩層等高 + 白條消除 TDD tests.

設計（user 拍板版本，依 sandbox erp-after.png）：
- Layer 1 深黑 top-nav：含 breadcrumb 路徑（取代原 nav-brand logo）
- Layer 2 深藍 doc-page-banner：只有 H1 title，移除原 banner-breadcrumb
- 兩層等高 56px，無白條 gap
- sidebar 緊貼 banner（修原 sticky top: var(--nav-h) 殘留把 sidebar 下推 56px）
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'


def _read() -> str:
    return GEN_HTML.read_text(encoding='utf-8')


def _html_template(text: str) -> str:
    """Extract HTML_TEMPLATE string content from gen_html.py."""
    m = re.search(r'HTML_TEMPLATE\s*=\s*"""(.*?)"""', text, re.DOTALL)
    return m.group(1) if m else ''


def _inline_style(text: str) -> str:
    """Extract the inline <style>...</style> block from HTML_TEMPLATE."""
    tpl = _html_template(text)
    m = re.search(r'<style>(.*?)</style>', tpl, re.DOTALL)
    return m.group(1) if m else ''


# ─── 1: top-nav 結構 + 高度 ──────────────────────────────────────────

def test_Q1_top_nav_height_56px():
    """inline `<style>` 含 `.top-nav { height: 56px }`。"""
    style = _inline_style(_read())
    assert re.search(r'\.top-nav\s*\{[^}]*height\s*:\s*56px', style), \
        f'.top-nav must have height: 56px in inline <style>'


def test_Q1_top_nav_uses_nav_breadcrumb_not_nav_brand():
    """`<header class="top-nav">` 內用 `<nav class="nav-breadcrumb">`（取代 nav-brand）。"""
    tpl = _html_template(_read())
    # nav-brand should be GONE (replaced)
    assert 'class="nav-brand"' not in tpl, \
        'nav-brand class should be replaced by nav-breadcrumb'
    # nav-breadcrumb should be PRESENT
    assert 'class="nav-breadcrumb"' in tpl, \
        'top-nav must contain a <nav class="nav-breadcrumb"> element'


def test_Q1_nav_breadcrumb_has_separator_and_doc_center_text():
    """`nav-breadcrumb` 含 `›` separator 跟 `文件中心` 文字。"""
    tpl = _html_template(_read())
    m = re.search(r'<nav\s+class="nav-breadcrumb">(.*?)</nav>', tpl, re.DOTALL)
    assert m, 'nav-breadcrumb element not found'
    body = m.group(1)
    assert '›' in body or '&rsaquo;' in body or 'sep' in body, \
        f'nav-breadcrumb should contain separator; body:\n{body}'
    assert '文件中心' in body, \
        f'nav-breadcrumb should contain "文件中心"; body:\n{body}'


def test_Q1_nav_breadcrumb_inline_style_exists():
    """inline `<style>` 含 `.nav-breadcrumb` rule（flex/gap/color）。"""
    style = _inline_style(_read())
    assert re.search(r'\.nav-breadcrumb\s*\{', style), \
        f'.nav-breadcrumb CSS rule missing in inline <style>'


# ─── 2: doc-page-banner 結構 + 高度 ──────────────────────────────────

def test_Q1_banner_no_longer_contains_banner_breadcrumb():
    """`<div class="doc-page-banner">` 移除 `<p class="banner-breadcrumb">`。"""
    tpl = _html_template(_read())
    m = re.search(r'<div class="doc-page-banner">(.*?)</div>', tpl, re.DOTALL)
    assert m, 'doc-page-banner element not found'
    body = m.group(1)
    assert 'banner-breadcrumb' not in body, \
        f'doc-page-banner should NOT contain banner-breadcrumb (moved to top-nav); body:\n{body}'


def test_Q1_banner_keeps_banner_title():
    """`<div class="doc-page-banner">` 仍含 `<h1 class="banner-title">`。"""
    tpl = _html_template(_read())
    m = re.search(r'<div class="doc-page-banner">(.*?)</div>', tpl, re.DOTALL)
    assert m, 'doc-page-banner element not found'
    body = m.group(1)
    assert 'class="banner-title"' in body, \
        f'doc-page-banner must keep <h1 class="banner-title">; body:\n{body}'


def test_Q1_banner_height_56px_match_top_nav():
    """inline `<style>` 含 `.doc-page-banner { height: 56px }`（跟 top-nav 等高）。"""
    style = _inline_style(_read())
    assert re.search(r'\.doc-page-banner\s*\{[^}]*height\s*:\s*56px', style), \
        f'.doc-page-banner must have height: 56px (equal to top-nav)'


def test_Q1_banner_uses_flex_center_layout():
    """`.doc-page-banner { display: flex; align-items: center }`（為了 H1 垂直置中）。"""
    style = _inline_style(_read())
    rule = re.search(r'\.doc-page-banner\s*\{([^}]*)\}', style)
    assert rule, '.doc-page-banner rule not found'
    body = rule.group(1)
    assert 'display' in body and 'flex' in body, \
        f'.doc-page-banner should use display: flex; got:\n{body}'
    assert 'align-items' in body and 'center' in body, \
        f'.doc-page-banner should align-items: center; got:\n{body}'


def test_Q1_banner_title_font_size_compact():
    """`.banner-title` 縮小成 1.25rem（從原 1.75rem，因為 banner 只 56px 高）。"""
    style = _inline_style(_read())
    assert re.search(r'\.banner-title\s*\{[^}]*font-size\s*:\s*1\.25rem', style), \
        f'.banner-title must be font-size: 1.25rem to fit 56px banner height'


# ─── 3: sidebar 白條 root cause 修法 ────────────────────────────────

def test_Q1_inline_sidebar_top_zero_to_kill_whitespace():
    """inline `.sidebar` rule 加 `top: 0` 覆蓋 style.css 的 `top: var(--nav-h)`。

    Root cause（實機驗證）：style.css `.sidebar { position: sticky; top: var(--nav-h) }`
    被 N1 修法改 `position: relative`，但**沒清 `top: 56px`** → sidebar 被
    relative 偏移 56px 下推 → banner 跟 sidebar 之間 56px 白條 gap。
    """
    style = _inline_style(_read())
    rule = re.search(r'\.sidebar\s*\{[^}]*position\s*:\s*relative[^}]*\}', style)
    assert rule, 'N1 inline .sidebar (position: relative) rule not found'
    assert re.search(r'top\s*:\s*0', rule.group(0)), \
        f'N1 inline .sidebar must include `top: 0` to kill 56px whitespace gap'


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print('Q GROUP — header two-row equal-height + whitespace gap removal')
    print('=' * 78)
    tests = [
        ('Q1_top_nav_height_56px', test_Q1_top_nav_height_56px),
        ('Q1_top_nav_uses_nav_breadcrumb_not_nav_brand', test_Q1_top_nav_uses_nav_breadcrumb_not_nav_brand),
        ('Q1_nav_breadcrumb_has_separator_and_doc_center_text', test_Q1_nav_breadcrumb_has_separator_and_doc_center_text),
        ('Q1_nav_breadcrumb_inline_style_exists', test_Q1_nav_breadcrumb_inline_style_exists),
        ('Q1_banner_no_longer_contains_banner_breadcrumb', test_Q1_banner_no_longer_contains_banner_breadcrumb),
        ('Q1_banner_keeps_banner_title', test_Q1_banner_keeps_banner_title),
        ('Q1_banner_height_56px_match_top_nav', test_Q1_banner_height_56px_match_top_nav),
        ('Q1_banner_uses_flex_center_layout', test_Q1_banner_uses_flex_center_layout),
        ('Q1_banner_title_font_size_compact', test_Q1_banner_title_font_size_compact),
        ('Q1_inline_sidebar_top_zero_to_kill_whitespace', test_Q1_inline_sidebar_top_zero_to_kill_whitespace),
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
