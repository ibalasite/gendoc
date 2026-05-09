#!/usr/bin/env python3
"""TDD test suite for HTML path rewriter / sidebar prototype scan.

Server root = docs/pages/. All href/src must:
- Be relative paths
- Resolve INSIDE docs/pages/ (any depth)
- Not use '..' to escape pages/

Test cases cover the 6 issues from comprehensive survey:
- R1: <code>path</code> auto-link when target exists in pages/
- R2: Sidebar prototype scan
- R3-1: href="docs/pages/X.html" → "X.html"
- R3-2: href="docs/X.md" → "X.html" (rendered sibling)
- R3-3: href="diagrams/X.md" → "diag-X.html" (gendoc flatten convention)
- R3-4: href="features/X" / src/ etc. → strip <a> (no pages/ counterpart)
- R3-5: href="blueprint/X" → strip <a> (engineering specs not for users)
- R3-6: prototype subdir 跳出 pages/ (../../../X) — handled in gendoc-gen-prototype
       (not in gen_html.py)

Plus LEGIT baseline cases that must remain unchanged after rewrite.

Runnable both as pytest and standalone:
  pytest tools/gen_html/tests/
  python3 tools/gen_html/tests/test_path_rewriter.py
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


# ─── Helpers ───────────────────────────────────────────────────────────

def _make_pages_dir(layout: dict) -> pathlib.Path:
    """Create a temp pages/ dir with given layout (filename → empty content).

    Used to test path rewriter's existence-check logic (auto-link, R3-2).
    """
    tmp = pathlib.Path(tempfile.mkdtemp())
    for rel, content in layout.items():
        target = tmp / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if isinstance(content, str) else '')
    return tmp


# ─── R3-1: docs/pages/X.html prefix strip ─────────────────────────────

def test_R3_1_strip_docs_pages_prefix():
    """href="docs/pages/X.html" → "X.html"。"""
    html = '<a href="docs/pages/api.html">api</a>'
    pages = _make_pages_dir({'api.html': '', 'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="api.html"' in out
    assert 'docs/pages/' not in out


# ─── R3-2: docs/X.md → X.html ─────────────────────────────────────────

def test_R3_2_md_to_html_when_html_exists():
    """href="docs/API.md" → "api.html" (lowercase, .md→.html)。"""
    html = '<a href="docs/API.md">API spec</a>'
    pages = _make_pages_dir({'api.html': '', 'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="api.html"' in out
    assert 'docs/' not in out


def test_R3_2_md_with_anchor():
    """href="docs/ARCH.md#adr" → "arch.html#adr"。"""
    html = '<a href="docs/ARCH.md#adr">ADRs</a>'
    pages = _make_pages_dir({'arch.html': '', 'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="arch.html#adr"' in out


# ─── R3-3: diagrams/X.md → diag-X.html ────────────────────────────────

def test_R3_3_diagrams_md_to_diag_html():
    """href="diagrams/class-application.md" → "diag-class-application.html"。"""
    html = '<a href="diagrams/class-application.md">class</a>'
    pages = _make_pages_dir({
        'diag-class-application.html': '',
        'index.html': '',
    })
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="diag-class-application.html"' in out


def test_R3_3_diagrams_dir_link_strips():
    """href="diagrams/" — 整個目錄無對應 single page → strip。"""
    html = '<a href="diagrams/">all diagrams</a>'
    pages = _make_pages_dir({'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    # 沒有對應 pages/ 內檔 → 應拆 <a>
    assert '<a href' not in out
    assert 'all diagrams' in out


# ─── R3-4: features/ → strip ──────────────────────────────────────────

def test_R3_4_features_strip():
    """href="features/" — pages/ 內無對應 → strip <a>。"""
    html = '<a href="features/">features</a>'
    pages = _make_pages_dir({'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert '<a href' not in out
    assert 'features' in out


# ─── R3-5: blueprint/ → strip ─────────────────────────────────────────

def test_R3_5_blueprint_strip():
    """href="blueprint/contracts/openapi.yaml" — 工程規格不進 pages/ → strip。"""
    html = '<a href="blueprint/contracts/openapi.yaml">openapi</a>'
    pages = _make_pages_dir({'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert '<a href' not in out
    assert 'openapi' in out


# ─── R1: <code>path</code> auto-link ──────────────────────────────────

def test_R1_code_to_link_when_path_exists():
    """<code>prototype/index.html</code> 且 pages/prototype/index.html 存在 → 包 <a>。"""
    html = '<code>prototype/index.html</code>'
    pages = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
    })
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert '<a href="prototype/index.html"' in out
    assert 'prototype/index.html</a>' in out


def test_R1_code_with_docs_pages_prefix_to_link():
    """<code>docs/pages/prototype/api-explorer/index.html</code> → strip prefix + auto-link。"""
    html = '<code>docs/pages/prototype/api-explorer/index.html</code>'
    pages = _make_pages_dir({
        'index.html': '',
        'prototype/api-explorer/index.html': '',
    })
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert '<a href="prototype/api-explorer/index.html"' in out


def test_R1_code_path_not_existing_stays_code():
    """<code>config.json</code> 但 pages/config.json 不存在 → 不該變 link。"""
    html = '<code>config.json</code>'
    pages = _make_pages_dir({'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert '<code>config.json</code>' in out
    assert '<a href' not in out


# ─── A1: Avoid nested <a><a> ──────────────────────────────────────────
# When <code> is already inside an <a>, R1 must NOT wrap it again.

def test_A1_code_inside_a_not_double_wrapped():
    """已被 <a> 包住的 <code> 不該被 R1 二次包成 <a><a>。"""
    html = '<a href="prototype/index.html"><code>prototype/index.html</code></a>'
    pages = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
    })
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    # Output must contain exactly ONE <a> wrap around the code
    assert out.count('<a ') == 1, f'expected exactly 1 <a>, got: {out}'
    assert '<a href="prototype/index.html"><code>prototype/index.html</code></a>' in out


def test_A1_code_outside_a_still_wrapped():
    """裸 <code>（不在 <a> 內）仍應被 R1 正常包連結。"""
    html = 'plain <code>prototype/index.html</code> text'
    pages = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
    })
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert '<a href="prototype/index.html">prototype/index.html</a>' in out


def test_A1_code_inside_a_multiline():
    """<a> 內的 <code> 跨行也不該被二次包。"""
    html = (
        '<a href="prototype/index.html">\n'
        '<code>prototype/index.html</code>\n'
        '</a>'
    )
    pages = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
    })
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert out.count('<a ') == 1
    # The <code> should still be there, untouched
    assert '<code>prototype/index.html</code>' in out


def test_A1_code_inside_a_multiple_codes():
    """<a> 內多個 <code> 都不該被包。"""
    html = (
        '<a href="prototype/index.html">'
        '<code>prototype/index.html</code>'
        '<code>prototype/index.html</code>'
        '</a>'
    )
    pages = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
    })
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    # Still exactly one <a>, both codes untouched
    assert out.count('<a ') == 1
    assert out.count('<code>prototype/index.html</code>') == 2


def test_A1_already_nested_a_not_re_wrapped():
    """source 已是 nested <a><a> (malformed) — R1 至少不該再加層。"""
    html = (
        '<a href="prototype/index.html">'
        '<a href="prototype/index.html">'
        '<code>prototype/index.html</code>'
        '</a></a>'
    )
    pages = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
    })
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    # R1 must not introduce a NEW <a> on top of the existing nest.
    assert out.count('<a ') == html.count('<a '), (
        f'R1 added an extra <a>: input had {html.count("<a ")}, '
        f'output has {out.count("<a ")}'
    )


# ─── LEGIT baseline (must NOT change) ─────────────────────────────────

def test_LEGIT_simple_relative_link_unchanged():
    """已正確的相對連結不該被動。"""
    html = '<a href="api.html">API</a>'
    pages = _make_pages_dir({'api.html': '', 'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="api.html"' in out


def test_LEGIT_external_url_unchanged():
    """http(s):// 完全不該被動。"""
    html = '<a href="https://example.com/foo">external</a>'
    pages = _make_pages_dir({'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="https://example.com/foo"' in out


def test_LEGIT_anchor_link_unchanged():
    """純 #anchor 不該被動。"""
    html = '<a href="#section-1">jump</a>'
    pages = _make_pages_dir({'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="#section-1"' in out


def test_LEGIT_subdir_html_relative_within_unchanged():
    """從 pages/prototype/index.html 的 href="assets/X" 是該檔內合法相對連結。"""
    html = '<link rel="stylesheet" href="assets/prototype.css">'
    pages = _make_pages_dir({
        'prototype/index.html': '',
        'prototype/assets/prototype.css': '',
    })
    out = gh.rewrite_pages_paths(
        html, pages / 'prototype' / 'index.html', pages,
    )
    assert 'href="assets/prototype.css"' in out


def test_LEGIT_already_correct_code_block_unchanged():
    """<code>config.json</code> 不存在不該變 link，保留原 <code>。"""
    html = '<p>set <code>API_KEY</code> in config</p>'
    pages = _make_pages_dir({'index.html': ''})
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert '<code>API_KEY</code>' in out


# ─── R3-6: subdir 跳出 pages/（AI 亂寫 ../../../） ────────────────────

def test_R3_6_subdir_too_many_dots_strip():
    """從 prototype/api-explorer/index.html 寫 ../../../index.html
    解析跳出 pages/ → strip <a>。"""
    html = '<a href="../../../index.html">← 文件站</a>'
    pages = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
        'prototype/api-explorer/index.html': '',
    })
    out = gh.rewrite_pages_paths(
        html, pages / 'prototype' / 'api-explorer' / 'index.html', pages,
    )
    assert '<a href' not in out
    assert '文件站' in out


def test_R3_6_subdir_correct_relative_unchanged():
    """從 prototype/api-explorer/index.html 寫 ../../index.html (docs entry)
    解析在 pages/ 內 → 不動。"""
    html = '<a href="../../index.html">docs entry</a>'
    pages = _make_pages_dir({
        'index.html': '',
        'prototype/api-explorer/index.html': '',
    })
    out = gh.rewrite_pages_paths(
        html, pages / 'prototype' / 'api-explorer' / 'index.html', pages,
    )
    assert 'href="../../index.html"' in out


# ─── R2: Sidebar prototype scan ───────────────────────────────────────

def test_R2_sidebar_scan_prototype_entries():
    """scan_prototype_entries 應回傳 pages/prototype/{,*/}index.html。"""
    pages = _make_pages_dir({
        'prototype/index.html': '',
        'prototype/api-explorer/index.html': '',
        'prototype/admin/index.html': '',
    })
    entries = gh.scan_prototype_entries(pages)
    paths = [e['href'] for e in entries]
    assert 'prototype/index.html' in paths
    assert 'prototype/api-explorer/index.html' in paths
    assert 'prototype/admin/index.html' in paths


def test_R2_sidebar_scan_no_prototype_dir():
    """pages/prototype/ 不存在 → 空 list。"""
    pages = _make_pages_dir({'index.html': ''})
    entries = gh.scan_prototype_entries(pages)
    assert entries == []


def test_R2_sidebar_scan_only_main_prototype():
    """只有 prototype/index.html，沒 api-explorer 等。"""
    pages = _make_pages_dir({'prototype/index.html': ''})
    entries = gh.scan_prototype_entries(pages)
    paths = [e['href'] for e in entries]
    assert paths == ['prototype/index.html']


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print(f'PATH REWRITER TEST  source={GEN_HTML}')
    print('=' * 78)

    tests = [
        # R3-1
        ('R3_1_strip_docs_pages_prefix', test_R3_1_strip_docs_pages_prefix),
        # R3-2
        ('R3_2_md_to_html_when_html_exists', test_R3_2_md_to_html_when_html_exists),
        ('R3_2_md_with_anchor', test_R3_2_md_with_anchor),
        # R3-3
        ('R3_3_diagrams_md_to_diag_html', test_R3_3_diagrams_md_to_diag_html),
        ('R3_3_diagrams_dir_link_strips', test_R3_3_diagrams_dir_link_strips),
        # R3-4
        ('R3_4_features_strip', test_R3_4_features_strip),
        # R3-5
        ('R3_5_blueprint_strip', test_R3_5_blueprint_strip),
        # R3-6
        ('R3_6_subdir_too_many_dots_strip', test_R3_6_subdir_too_many_dots_strip),
        ('R3_6_subdir_correct_relative_unchanged',
         test_R3_6_subdir_correct_relative_unchanged),
        # R1
        ('R1_code_to_link_when_path_exists', test_R1_code_to_link_when_path_exists),
        ('R1_code_with_docs_pages_prefix_to_link', test_R1_code_with_docs_pages_prefix_to_link),
        ('R1_code_path_not_existing_stays_code', test_R1_code_path_not_existing_stays_code),
        # A1
        ('A1_code_inside_a_not_double_wrapped', test_A1_code_inside_a_not_double_wrapped),
        ('A1_code_outside_a_still_wrapped', test_A1_code_outside_a_still_wrapped),
        ('A1_code_inside_a_multiline', test_A1_code_inside_a_multiline),
        ('A1_code_inside_a_multiple_codes', test_A1_code_inside_a_multiple_codes),
        ('A1_already_nested_a_not_re_wrapped', test_A1_already_nested_a_not_re_wrapped),
        # R2
        ('R2_sidebar_scan_prototype_entries', test_R2_sidebar_scan_prototype_entries),
        ('R2_sidebar_scan_no_prototype_dir', test_R2_sidebar_scan_no_prototype_dir),
        ('R2_sidebar_scan_only_main_prototype', test_R2_sidebar_scan_only_main_prototype),
        # LEGIT
        ('LEGIT_simple_relative_link_unchanged', test_LEGIT_simple_relative_link_unchanged),
        ('LEGIT_external_url_unchanged', test_LEGIT_external_url_unchanged),
        ('LEGIT_anchor_link_unchanged', test_LEGIT_anchor_link_unchanged),
        ('LEGIT_subdir_html_relative_within_unchanged',
         test_LEGIT_subdir_html_relative_within_unchanged),
        ('LEGIT_already_correct_code_block_unchanged',
         test_LEGIT_already_correct_code_block_unchanged),
    ]

    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f'  ✅ [{name}]')
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f'  ❌ [{name}] AssertionError: {e}')
        except AttributeError as e:
            failed += 1
            print(f'  ❌ [{name}] missing impl: {e}')
        except Exception as e:
            failed += 1
            print(f'  ❌ [{name}] {type(e).__name__}: {e}')

    print('\n' + '=' * 78)
    print(f'TOTAL: {passed} PASS / {failed} FAIL  ({len(tests)} cases)')
    print('=' * 78)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
