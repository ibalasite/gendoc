#!/usr/bin/env python3
"""S 群 — HTML comment strip + metadata separator strip + 空白 collapse.

設計（user 拍板版本，依 sandbox s-group-html-comment/edd-after.png）：
1. HTML comment (`<!-- ... -->`) 不該渲染成文字（markdown parser 預設會把每行
   包 <p>）— 直接 strip，瀏覽器看不到內容
2. SDLC convention：source 含 metadata comment block + H1 + `---` 是
   metadata header pattern。註解 strip 後 `---` 失去意義也跟著 strip
3. 連續空白行 collapse（避免 comment strip 後留大量空白）
4. Safety：source 沒 comment 但有純 `---` 的 → 保留（user intent 的 hr 不誤砍）
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh_s', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


# ─── 1: HTML comment strip ────────────────────────────────────────────

def test_S1_single_line_comment_stripped():
    """`<!-- single-line -->` 應從 markdown 中 strip 掉，不渲染成文字。"""
    md = '# Title\n\n<!-- metadata: foo -->\n\nbody text\n'
    html = gh.md_to_html(md)
    assert '&lt;!--' not in html, \
        f'single-line comment should be stripped; html:\n{html[:300]}'
    assert 'metadata: foo' not in html, \
        f'comment content should not leak as text; html:\n{html[:300]}'


def test_S1_multi_line_comment_stripped():
    """跨行 `<!--\\n  line1\\n  line2\\n-->` 應整段 strip。"""
    md = (
        '# Title\n\n'
        '<!--\n'
        '  DOC-ID: README-X\n'
        '  Version: v1.0\n'
        '  Status: DRAFT\n'
        '-->\n\n'
        'body content\n'
    )
    html = gh.md_to_html(md)
    assert 'DOC-ID' not in html or 'comment' not in html.lower(), \
        f'multi-line comment fields (DOC-ID/Version) should be stripped; html:\n{html[:400]}'
    assert '&lt;!--' not in html, \
        f'no escaped comment markers should remain; html:\n{html[:400]}'


def test_S1_comment_anywhere_in_body_stripped():
    """body 中段的 comment 也要 strip（不只 source 開頭）。"""
    md = (
        '# Title\n\n'
        'first paragraph\n\n'
        '<!-- inline body comment -->\n\n'
        '## Section\n\n'
        'second paragraph\n'
    )
    html = gh.md_to_html(md)
    assert 'inline body comment' not in html, \
        f'mid-body comment should also be stripped; html:\n{html[:400]}'


# ─── 2: metadata `---` separator strip (only when comment exists) ────

def test_S1_metadata_separator_stripped_when_comment_exists():
    """SDLC pattern：`# H1\\n\\n<!-- meta -->\\n\\n---\\n\\n## Section`
    — `---` 跟著被 strip 的 metadata comment 一起 strip。"""
    md = (
        '# EDD — Engineering Design Document\n\n'
        '<!-- SDLC Layer 4 -->\n'
        '<!-- Upstream: PRD -->\n\n'
        '---\n\n'
        '## Document Control\n\n'
        'body\n'
    )
    html = gh.md_to_html(md)
    assert '<hr>' not in html and '<hr/>' not in html, \
        f'metadata separator `---` (after H1) should be stripped along with metadata; html:\n{html[:400]}'


def test_S1_hr_preserved_when_no_metadata_comment():
    """Safety: source 沒 comment 但有真正 `---` 的（user intent hr）不該 strip。"""
    md = (
        '# My Document\n\n'
        '---\n\n'
        '## Section\n'
    )
    html = gh.md_to_html(md)
    assert '<hr>' in html or '<hr/>' in html, \
        f'user-intended `---` (no metadata comment) must be preserved; html:\n{html[:300]}'


def test_S1_hr_in_body_preserved_when_metadata_exists():
    """Safety: 即便有 metadata comment，body 中段（非 H1 緊接）的 `---` 仍要保留。"""
    md = (
        '# Title\n\n'
        '<!-- meta -->\n\n'
        '## Section A\n\n'
        'some text\n\n'
        '---\n\n'
        'more text\n'
    )
    html = gh.md_to_html(md)
    assert '<hr>' in html or '<hr/>' in html, \
        f'body-level `---` (not after H1) must be preserved; html:\n{html[:400]}'


# ─── 3: whitespace collapse ──────────────────────────────────────────

def test_S1_consecutive_blank_lines_collapsed():
    """連續 3+ 空白行 collapse 成 1 個（避免 comment strip 後大空白）。"""
    md = (
        '# Title\n'
        '\n\n\n\n\n'
        'body\n'
    )
    html = gh.md_to_html(md)
    # Count empty paragraph occurrences
    empty_p = len(re.findall(r'<p>\s*</p>', html))
    assert empty_p == 0, \
        f'should not produce empty <p></p> from collapsed whitespace; got {empty_p}'


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print('S GROUP — HTML comment strip + metadata --- strip + whitespace collapse')
    print('=' * 78)
    tests = [
        ('S1_single_line_comment_stripped', test_S1_single_line_comment_stripped),
        ('S1_multi_line_comment_stripped', test_S1_multi_line_comment_stripped),
        ('S1_comment_anywhere_in_body_stripped', test_S1_comment_anywhere_in_body_stripped),
        ('S1_metadata_separator_stripped_when_comment_exists', test_S1_metadata_separator_stripped_when_comment_exists),
        ('S1_hr_preserved_when_no_metadata_comment', test_S1_hr_preserved_when_no_metadata_comment),
        ('S1_hr_in_body_preserved_when_metadata_exists', test_S1_hr_in_body_preserved_when_metadata_exists),
        ('S1_consecutive_blank_lines_collapsed', test_S1_consecutive_blank_lines_collapsed),
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
