#!/usr/bin/env python3
"""W 群 — title block (H1 + H2 subtitle) 後緊接的 `---` 是 cosmetic separator，
strip 掉避免多餘的 hr 線。

設計（user 拍板版本，依 erp/EDD.md 實機問題）：

問題：很多 SDLC 文件用「title + subtitle + separator + content」結構：
```
# Engineering Design Document (EDD)
## ERP API Token Manager

---                           <- cosmetic title-block separator

## Document Control
...
```
S 群已處理「H1 + HTML comment + ---」的 case，但這個結構**沒**有 HTML
comment — S 群 safety test (`hr_preserved_when_no_metadata_comment`)
反而確保 `# H1\\n\\n---\\n\\n## Section` 必須保留 hr（user intent）。
兩者差別：H2 subtitle 是否存在。

解法：
- W 群 strip 條件：source 開頭 `^# H1\\n## H2\\n\\n---\\n` （title + subtitle + sep）
- count=1，只動 document 開頭第一次 — 不影響後面 author 自己放的 inline `---`
- S 群「無 comment + 無 H2-subtitle 的 H1+---」仍保留為 user intent hr
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh_w', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


# ─── 1: title-block (H1 + H2 subtitle) + --- → strip the --- ─────────

def test_W1_title_block_separator_stripped():
    """`# H1\\n## H2-subtitle\\n\\n---\\n\\n## Section` → 第一個 hr 消失."""
    md = (
        '# Engineering Design Document (EDD)\n'
        '## ERP API Token Manager\n\n'
        '---\n\n'
        '## Document Control\n\n'
        'body\n'
    )
    html = gh.md_to_html(md)
    # H2 subtitle present
    assert 'ERP API Token Manager' in html, \
        'H2 subtitle text must survive; html:\n' + html[:400]
    # No hr between subtitle and Document Control
    pre_doc_ctrl = html[:html.find('Document Control')] if 'Document Control' in html else html
    assert '<hr' not in pre_doc_ctrl, (
        f'W-group: title-block separator `---` (after H1+H2) must be stripped; '
        f'pre-section html:\n{pre_doc_ctrl}'
    )


def test_W1_title_block_separator_stripped_realistic_erp_edd():
    """模擬 erp/EDD.md 開頭結構（user 實機驗證 case）。"""
    md = (
        '# Engineering Design Document (EDD)\n'
        '## ERP API Token Manager\n\n'
        '---\n\n'
        '## Document Control\n\n'
        '| 欄位 | 內容 |\n'
        '|------|------|\n'
        '| **DOC-ID** | EDD-X-001 |\n\n'
        '---\n\n'
        '## Change Log\n\n'
        'body\n'
    )
    html = gh.md_to_html(md)
    # Count hr occurrences — should be exactly 1 (between Document Control
    # table and Change Log), not 2.
    hr_count = len(re.findall(r'<hr\b', html))
    assert hr_count == 1, (
        f'W-group: expected 1 hr (between Doc Control + Change Log), '
        f'got {hr_count}; html:\n{html[:800]}'
    )


# ─── 2: safety — S-group cases preserved ──────────────────────────────

def test_W1_safety_h1_only_hr_preserved():
    """S 群 baseline：`# H1\\n\\n---\\n## Section`（沒 H2 subtitle）→ hr 仍保留
    (user intent hr，W 群修法不能誤砍)."""
    md = (
        '# My Document\n\n'
        '---\n\n'
        '## Section\n'
    )
    html = gh.md_to_html(md)
    assert re.search(r'<hr\b', html), (
        f'W-group must not strip H1+--- pattern (no H2 subtitle = S-group safety); '
        f'html:\n{html[:400]}'
    )


def test_W1_safety_mid_body_hr_preserved():
    """body 中段的 `---` (即使 source 開頭有 title block) 必須保留 (author intent)."""
    md = (
        '# Title\n'
        '## Subtitle\n\n'
        '---\n\n'
        '## Section A\n\n'
        'some text\n\n'
        '---\n\n'
        'more text after divider\n'
    )
    html = gh.md_to_html(md)
    # Only the mid-body `---` should remain (1 hr); title-block separator stripped
    hr_count = len(re.findall(r'<hr\b', html))
    assert hr_count == 1, (
        f'expected 1 mid-body hr (title-block stripped, body preserved); '
        f'got {hr_count}; html:\n{html[:800]}'
    )


def test_W1_safety_s_group_metadata_comment_still_stripped():
    """S 群 metadata comment case 不被 W 群破壞 — comment + --- 仍都 strip."""
    md = (
        '# EDD\n\n'
        '<!-- SDLC Layer 4 -->\n\n'
        '---\n\n'
        '## Document Control\n'
    )
    html = gh.md_to_html(md)
    assert '<hr' not in html, (
        f'S-group metadata comment case must still strip hr; html:\n{html[:400]}'
    )
    assert 'SDLC Layer 4' not in html, \
        'S-group: HTML comment text must not leak'


def test_W1_no_h2_subtitle_no_strip():
    """如果 H1 後直接接 H2 *內容區段* (not subtitle，distinguished by
    `---` not being immediately after) — `---` 不能誤砍."""
    md = (
        '# Document Title\n\n'
        'intro paragraph\n\n'
        '## First Section\n\n'
        '---\n\n'
        '## Second Section\n'
    )
    html = gh.md_to_html(md)
    # The `---` is between two H2 sections in the body, not title-block sep
    assert re.search(r'<hr\b', html), (
        f'inline `---` between body sections must NOT be stripped; html:\n{html[:600]}'
    )


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print('W GROUP — title block (H1 + H2 subtitle) + --- separator strip')
    print('=' * 78)
    tests = [
        ('W1_title_block_separator_stripped', test_W1_title_block_separator_stripped),
        ('W1_title_block_separator_stripped_realistic_erp_edd', test_W1_title_block_separator_stripped_realistic_erp_edd),
        ('W1_safety_h1_only_hr_preserved', test_W1_safety_h1_only_hr_preserved),
        ('W1_safety_mid_body_hr_preserved', test_W1_safety_mid_body_hr_preserved),
        ('W1_safety_s_group_metadata_comment_still_stripped', test_W1_safety_s_group_metadata_comment_still_stripped),
        ('W1_no_h2_subtitle_no_strip', test_W1_no_h2_subtitle_no_strip),
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
