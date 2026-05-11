#!/usr/bin/env python3
"""V 群 — TOC / sidebar anchor jump 必須避開 sticky top-nav.

設計（user 拍板版本，依 sandbox after-v5-anchor-jump-fixed.png）：

問題：T 群 top-nav 設成 sticky 56px 後，任何 anchor jump（TOC 點 `#section`、
sidebar 點 `#heading`、URL hash）瀏覽器都會把 target 卷到 viewport top=0 —
但 viewport top 0-56px 被 sticky top-nav 蓋住 → 點到的 heading 永遠看不見。

User 實機驗證：點「2.0 User Personas」TOC link，畫面直接停在「Persona A」
（2.0 標題藏在 nav 底下）。

解法：
1. inline `<style>` 加 `.doc-content [id] { scroll-margin-top: 64px }`
   — 任何被當 anchor target 的 element（heading / table / div / span）
   都自動避開 nav 高度 + 8px 視覺呼吸 = 64px
2. 只挑 `.doc-content` 內的 element 避免影響 sidebar / nav 內部結構
3. `scroll-padding-top` 跟 `scroll-margin-top` 二擇一（會疊加），這裡只用後者
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


# ─── 1: doc-content [id] scroll-margin-top 64px ──────────────────────

def test_V1_doc_content_id_scroll_margin_top():
    """inline `<style>` 含 `.doc-content [id] { scroll-margin-top: 64px }`
    — 任何 anchor target element 避開 sticky top-nav."""
    style = _inline_style(_read())
    pattern = (
        r'\.doc-content\s+\[id\]\s*\{'
        r'[^}]*scroll-margin-top\s*:\s*64px[^}]*\}'
    )
    assert re.search(pattern, style), (
        '.doc-content [id] { scroll-margin-top: 64px } missing in inline <style>'
    )


def test_V1_no_double_scroll_padding_on_html():
    """不應該同時設 `html { scroll-padding-top }` — 跟 `[id] scroll-margin-top`
    會疊加成 128px 偏移（sandbox 實測 gap 71.625 → 修法是只留一條）."""
    style = _inline_style(_read())
    # 不該有 html { ... scroll-padding-top ... }
    html_rule = re.search(r'(?:^|\W)html\s*\{[^}]*\}', style)
    if html_rule:
        body = html_rule.group(0)
        assert 'scroll-padding-top' not in body, (
            f'html rule must NOT set scroll-padding-top '
            f'(conflicts with [id] scroll-margin-top); body:\n{body}'
        )


# ─── 2: scope restricted to .doc-content（不誤砍 sidebar/nav） ────────

def test_V1_scroll_margin_scoped_to_doc_content():
    """`scroll-margin-top` 規則必須限定 `.doc-content` 下層，避免影響
    sidebar 內部 anchor 結構（例如 sidebar__tab data-tab 切換）."""
    style = _inline_style(_read())
    # 任何 `[id]` 規則前面必須有 `.doc-content` 或其他明確 scope；不能是
    # `^[id]` 或 `\n[id]`（這代表 unscoped global rule）。
    for m in re.finditer(r'\[id\]\s*\{[^}]*scroll-margin-top', style):
        # Walk backwards to find what precedes `[id]`
        start = m.start()
        # Look for the last 30 chars before [id]
        prefix = style[max(0, start - 30):start]
        assert '.doc-content' in prefix or '.content' in prefix, (
            f'scroll-margin-top rule must be scoped under .doc-content; '
            f'unscoped [id] found, prefix:\n{prefix!r}'
        )


# ─── 3: nav 高度跟 sidebar top 對齊（變更要同步 V 群 padding） ─────────

def test_V1_scroll_margin_value_matches_sticky_nav():
    """`scroll-margin-top: 64px` = top-nav 高 56px + 8px 視覺呼吸。
    確保跟 T 群 `.sidebar { top: 56px }` 一致 — nav 高度若改，這條也要改."""
    style = _inline_style(_read())
    # T 群 sidebar top 必須是 56px（前置條件）
    sidebar_rule = re.search(
        r'\.sidebar\s*\{[^}]*display\s*:\s*flex[^}]*\}', style,
    )
    assert sidebar_rule, '.sidebar T-group rule missing (V depends on T)'
    assert 'top: 56px' in sidebar_rule.group(0), \
        '.sidebar top must be 56px to match V-group scroll-margin-top: 64px'
    # V 群 scroll-margin-top 應該是 nav 高度 + 8 buffer
    v_rule = re.search(
        r'\.doc-content\s+\[id\]\s*\{[^}]*?scroll-margin-top\s*:\s*(\d+)px',
        style,
    )
    assert v_rule, 'V-group scroll-margin-top rule missing'
    px = int(v_rule.group(1))
    assert px >= 56, (
        f'scroll-margin-top must be >= nav height 56px (got {px}px) to avoid '
        f'heading hidden under sticky nav'
    )
    assert px <= 80, (
        f'scroll-margin-top should not exceed 80px (got {px}px) — too much '
        f'whitespace above heading wastes viewport'
    )


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print('V GROUP — anchor jump 避開 sticky top-nav，heading 永遠看得到')
    print('=' * 78)
    tests = [
        ('V1_doc_content_id_scroll_margin_top', test_V1_doc_content_id_scroll_margin_top),
        ('V1_no_double_scroll_padding_on_html', test_V1_no_double_scroll_padding_on_html),
        ('V1_scroll_margin_scoped_to_doc_content', test_V1_scroll_margin_scoped_to_doc_content),
        ('V1_scroll_margin_value_matches_sticky_nav', test_V1_scroll_margin_value_matches_sticky_nav),
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
