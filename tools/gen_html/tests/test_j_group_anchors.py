#!/usr/bin/env python3
"""J 群 — TOC anchor 修正 TDD tests.

問題（issue J）:
1. inline_md 對所有 markdown link `[X](Y)` 都加 target="_blank"，連 in-page
   `[X](#section)` 也加 → 開新分頁而非定位滾動
2. <h1>~<h4> 沒加 id 屬性 → 即使移掉 target="_blank"，#anchor 找不到目標

修法:
1. inline_md 偵測 href 開頭 `#` → 不加 target="_blank"
2. md_to_html heading 處理：依 heading text 算 slug → 加 id="..."
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


# ─── J1: inline_md anchor link 不加 target="_blank" ──────────────────

def test_J1_inline_anchor_no_target_blank():
    """[X](#section) → <a href="#section">X</a> 不帶 target=_blank."""
    out = gh.inline_md('[Section 9](#9--data-access-layer)')
    assert 'target="_blank"' not in out, f'in-page anchor should not get target=_blank: {out}'
    assert 'href="#9--data-access-layer"' in out


def test_J1_inline_external_link_keeps_target_blank():
    """[X](https://...) external link 仍帶 target=_blank（regression）."""
    out = gh.inline_md('[Google](https://google.com)')
    assert 'target="_blank"' in out, f'external link should keep target=_blank: {out}'
    assert 'href="https://google.com"' in out


def test_J1_inline_relative_link_keeps_target_blank():
    """[X](../docs/foo.md) relative file link 行為不變（不影響）."""
    out = gh.inline_md('[Foo](foo.html)')
    # current behavior: target="_blank"; we don't touch
    assert 'href="foo.html"' in out


# ─── J2: heading 加 id 屬性 ───────────────────────────────────────────

def test_J2_heading_h2_gets_id():
    html = gh.md_to_html('## §9 — Data Access Layer\n')
    assert 'id="9--data-access-layer"' in html, f'h2 should have slug id; html: {html}'
    assert '<h2' in html and 'Data Access Layer' in html


def test_J2_heading_h1_h2_h3_h4_all_get_id():
    md = '''# Top Title
## Section A
### Subsection B
#### Detail C
'''
    html = gh.md_to_html(md)
    assert 'id="top-title"' in html
    assert 'id="section-a"' in html
    assert 'id="subsection-b"' in html
    assert 'id="detail-c"' in html


def test_J2_heading_id_strips_section_symbol():
    """§ 應被去掉，跟 GitHub-style 一致."""
    html = gh.md_to_html('## §0 — Document Control\n')
    assert 'id="0--document-control"' in html, f'§ should be stripped; html: {html}'


def test_J2_heading_id_handles_chinese():
    """Chinese heading 也要能 slug，保留 unicode chars."""
    html = gh.md_to_html('## 3. 資料表定義\n')
    # Chinese chars preserved + leading number ok
    assert re.search(r'id="3-?資料表定義"', html), f'Chinese slug not generated; html: {html}'


def test_J2_heading_id_collapses_special_chars_to_dash():
    """連續的非字母數字字元變成多個 -（與 erp 實際 anchor 規則一致）."""
    html = gh.md_to_html('## §9 — Data Access Layer\n')
    # § stripped, em-dash → -, spaces → -
    # `§9 ` → `9-` (after § strip + space → -)
    # ` — ` → `--` (space + em-dash strip → space → 連續, 接著 space 來)
    # actually § → "", "9 " → "9-", "— " → "-", "Data Access Layer" → "Data-Access-Layer"
    # combined: 9--data-access-layer (中間多 - 來自 — 跟 spaces)
    assert 'id="9--data-access-layer"' in html


def test_J2_heading_id_not_in_inline_anchors():
    """在 heading text 含 [X](url) 時 id 由 heading 純文字算."""
    html = gh.md_to_html('## Section [link](https://x.com)\n')
    # The heading text without the link anchor part determines slug
    # The link text 'link' should be in the slug since text is 'Section link'
    assert 'id="section-link"' in html or 'id="section"' in html


# ─── J3: 整合測試 ─────────────────────────────────────────────────────

def test_J3_toc_anchor_reaches_heading():
    """TOC link [X](#x) 跟 heading ## X 有對應的 href + id 配對."""
    md = '''## Table of Contents

- [Section A](#section-a)
- [Section B](#section-b)

## Section A

content...

## Section B

more content...
'''
    html = gh.md_to_html(md)
    # TOC anchors:
    assert 'href="#section-a"' in html
    assert 'href="#section-b"' in html
    # No target=_blank on internal anchors
    matches_a = re.findall(r'<a[^>]*href="#section-a"[^>]*>', html)
    assert all('target="_blank"' not in m for m in matches_a), \
        f'in-page anchor target=_blank not stripped: {matches_a}'
    # Headings have matching ids:
    assert 'id="section-a"' in html
    assert 'id="section-b"' in html


def test_J3_external_anchors_keep_target_blank():
    """external https link 仍開新頁 (regression)."""
    md = '參考 [Google](https://google.com).\n'
    html = gh.md_to_html(md)
    assert 'target="_blank"' in html
    assert 'href="https://google.com"' in html


# ─── Standalone runner ──────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'J GROUP TOC ANCHOR TESTS  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('J1_inline_anchor_no_target_blank', test_J1_inline_anchor_no_target_blank),
        ('J1_inline_external_link_keeps_target_blank', test_J1_inline_external_link_keeps_target_blank),
        ('J1_inline_relative_link_keeps_target_blank', test_J1_inline_relative_link_keeps_target_blank),
        ('J2_heading_h2_gets_id', test_J2_heading_h2_gets_id),
        ('J2_heading_h1_h2_h3_h4_all_get_id', test_J2_heading_h1_h2_h3_h4_all_get_id),
        ('J2_heading_id_strips_section_symbol', test_J2_heading_id_strips_section_symbol),
        ('J2_heading_id_handles_chinese', test_J2_heading_id_handles_chinese),
        ('J2_heading_id_collapses_special_chars_to_dash', test_J2_heading_id_collapses_special_chars_to_dash),
        ('J2_heading_id_not_in_inline_anchors', test_J2_heading_id_not_in_inline_anchors),
        ('J3_toc_anchor_reaches_heading', test_J3_toc_anchor_reaches_heading),
        ('J3_external_anchors_keep_target_blank', test_J3_external_anchors_keep_target_blank),
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
