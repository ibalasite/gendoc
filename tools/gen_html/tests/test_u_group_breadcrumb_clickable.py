#!/usr/bin/env python3
"""U 群 — top-nav breadcrumb 當前頁名可點，smooth scroll 回頁首.

設計（user 拍板版本，依 sandbox t-group-sidebar-sticky/after-v3-clickable-current.png）：

問題：T 群 sidebar sticky 後，本文卷到下半頁時，top-nav 黑 bar 內的當前頁名
（例如「產品設計文件 (PDD)」）只是純文字，user 想點它就回頁首。但只有左邊
repo 名是 anchor，當前頁名不可點。

解法：
1. `render_page()` 非 index 頁的 breadcrumb：
   `<a href="index.html">{APP_NAME}</a> › <a href="#top"
    class="nav-breadcrumb__current"
    onclick="event.preventDefault(); window.scrollTo({top:0, behavior:'smooth'});">
    {banner}</a>`
2. inline `<style>` 加 `.nav-breadcrumb__current`，cursor pointer + hover 顏色
   跟左邊 repo link 一致（fff → 60a5fa）。
3. Index 頁不需要（is_index=True 本來就是 `文件中心` 不需要點回自己）。
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh_u', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


def _read() -> str:
    return GEN_HTML.read_text(encoding='utf-8')


def _inline_style(text: str) -> str:
    m = re.search(r'HTML_TEMPLATE\s*=\s*"""(.*?)"""', text, re.DOTALL)
    tpl = m.group(1) if m else ''
    m = re.search(r'<style>(.*?)</style>', tpl, re.DOTALL)
    return m.group(1) if m else ''


def _render_non_index(banner='產品設計文件 (PDD)'):
    return gh.render_page(
        content='<p>x</p>', title='Test', banner=banner,
        doc_pages=[('index', '首頁', '🏠'), ('pdd', 'PDD', '📐')],
        server_diagrams=[], frontend_diagrams=[], sub_docs={},
        current='pdd', is_index=False,
    )


def _render_index():
    return gh.render_page(
        content='<p>x</p>', title='Home', banner='文件中心',
        doc_pages=[('index', '首頁', '🏠')],
        server_diagrams=[], frontend_diagrams=[], sub_docs={},
        current='index', is_index=True,
    )


# ─── 1: non-index breadcrumb has clickable current page link ─────────

def test_U1_non_index_current_is_anchor():
    """非 index 頁的 breadcrumb 內，當前頁名（banner 字串）必須包在 `<a>` tag 內，
    不能是純文字。"""
    rendered = _render_non_index(banner='產品設計文件 (PDD)')
    m = re.search(r'<nav\s+class="nav-breadcrumb">(.*?)</nav>', rendered, re.DOTALL)
    assert m, 'nav-breadcrumb element not found in rendered page'
    body = m.group(1)
    # left anchor (repo)
    assert re.search(r'<a\s+href="index\.html"', body), \
        f'left repo anchor missing; body:\n{body}'
    # current page name must appear inside an <a> tag
    assert re.search(
        r'<a[^>]*>[^<]*產品設計文件\s*\(PDD\)[^<]*</a>', body,
    ), f'current page name "產品設計文件 (PDD)" must be wrapped in <a>; body:\n{body}'


def test_U1_non_index_current_has_dedicated_class():
    """current page anchor 帶 `class="nav-breadcrumb__current"` 方便 CSS 區隔."""
    rendered = _render_non_index(banner='產品設計文件 (PDD)')
    m = re.search(r'<nav\s+class="nav-breadcrumb">(.*?)</nav>', rendered, re.DOTALL)
    body = m.group(1)
    assert 'class="nav-breadcrumb__current"' in body, \
        f'current anchor must use class="nav-breadcrumb__current"; body:\n{body}'


def test_U1_non_index_current_smooth_scroll_handler():
    """current anchor 必含 inline `onclick=` 觸發 smooth scroll 到頁首
    （不依賴外部 JS，避免 race condition）。"""
    rendered = _render_non_index()
    m = re.search(r'<nav\s+class="nav-breadcrumb">(.*?)</nav>', rendered, re.DOTALL)
    body = m.group(1)
    assert 'onclick=' in body, f'current anchor missing onclick; body:\n{body}'
    assert 'scrollTo' in body and "behavior:'smooth'" in body.replace('"', "'"), \
        f'onclick must call window.scrollTo with smooth behavior; body:\n{body}'
    # preventDefault to avoid jumping to #top hash
    assert 'preventDefault' in body, \
        f'onclick must preventDefault to avoid #top hash jump; body:\n{body}'


def test_U1_non_index_current_href_top():
    """current anchor `href="#top"` — onclick 失敗時退回 hash 跳轉行為（仍卷頂部）."""
    rendered = _render_non_index()
    m = re.search(r'<nav\s+class="nav-breadcrumb">(.*?)</nav>', rendered, re.DOTALL)
    body = m.group(1)
    assert 'href="#top"' in body or "href='#top'" in body, \
        f'current anchor href must be "#top"; body:\n{body}'


# ─── 2: index page breadcrumb still uses index.html link only ────────

def test_U1_index_breadcrumb_unchanged():
    """index 頁 breadcrumb 結構不動（it already shows `文件中心`，no need to
    link to self）— 確保 U 群修法不會誤砍 index 頁的 GitHub 補充 link。"""
    rendered = _render_index()
    m = re.search(r'<nav\s+class="nav-breadcrumb">(.*?)</nav>', rendered, re.DOTALL)
    body = m.group(1)
    assert '文件中心' in body, \
        f'index breadcrumb must keep "文件中心" label; body:\n{body}'
    # index 頁不應該把「文件中心」包進 nav-breadcrumb__current
    assert 'nav-breadcrumb__current' not in body, \
        f'index page must NOT use nav-breadcrumb__current; body:\n{body}'


# ─── 3: inline <style> has .nav-breadcrumb__current rule ──────────────

def test_U1_inline_style_nav_breadcrumb_current_rule():
    """inline `<style>` 必含 `.nav-breadcrumb__current { ... cursor: pointer ... }`
    讓游標明示可點."""
    style = _inline_style(_read())
    rule = re.search(r'\.nav-breadcrumb__current\s*\{([^}]*)\}', style)
    assert rule, '.nav-breadcrumb__current CSS rule missing in inline <style>'
    body = rule.group(1)
    assert 'cursor' in body and 'pointer' in body, \
        f'.nav-breadcrumb__current must use cursor: pointer; body:\n{body}'
    # color matches the other breadcrumb anchor (#fff)
    assert re.search(r'color\s*:\s*#fff', body), \
        f'.nav-breadcrumb__current color must be #fff (match repo link); body:\n{body}'


def test_U1_inline_style_nav_breadcrumb_current_hover():
    """`.nav-breadcrumb__current:hover` 顏色跟其他 nav-breadcrumb a:hover 一致（#60a5fa）。"""
    style = _inline_style(_read())
    rule = re.search(r'\.nav-breadcrumb__current:hover\s*\{([^}]*)\}', style)
    assert rule, '.nav-breadcrumb__current:hover CSS rule missing'
    body = rule.group(1)
    assert re.search(r'color\s*:\s*#60a5fa', body), \
        f'.nav-breadcrumb__current:hover must use color: #60a5fa; body:\n{body}'


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print('U GROUP — breadcrumb 當前頁名可點 smooth-scroll 回頁首')
    print('=' * 78)
    tests = [
        ('U1_non_index_current_is_anchor', test_U1_non_index_current_is_anchor),
        ('U1_non_index_current_has_dedicated_class', test_U1_non_index_current_has_dedicated_class),
        ('U1_non_index_current_smooth_scroll_handler', test_U1_non_index_current_smooth_scroll_handler),
        ('U1_non_index_current_href_top', test_U1_non_index_current_href_top),
        ('U1_index_breadcrumb_unchanged', test_U1_index_breadcrumb_unchanged),
        ('U1_inline_style_nav_breadcrumb_current_rule', test_U1_inline_style_nav_breadcrumb_current_rule),
        ('U1_inline_style_nav_breadcrumb_current_hover', test_U1_inline_style_nav_breadcrumb_current_hover),
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
