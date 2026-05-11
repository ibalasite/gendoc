#!/usr/bin/env python3
"""Lightbox CSS class alignment — inline <style> 規則的 class name 必須跟
`assets/app.js` 創建的 DOM 一致。

歷史上 commit `bccc935` 在 gen_html.py 加了 `.lightbox__zoom-content ...`
CSS rule，但 `docs/pages/assets/app.js` 從來都用 `.lightbox__content`
（line 12 `<div class="lightbox__content"></div>`）。class name 不對齊
→ CSS rule 永遠不 apply → lightbox 開了 SVG 不放大（顯示原始小尺寸）。

實機驗證（pet/edd.html lightbox click）：SVG 顯示 300×174 而非預期
1100+ × 700+。
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'
APP_JS = REPO / 'docs' / 'pages' / 'assets' / 'app.js'


def _read(p):
    return p.read_text(encoding='utf-8')


def test_app_js_uses_lightbox_content_class():
    """`app.js` lightbox DOM 用 `.lightbox__content` class（baseline / 不動）."""
    js = _read(APP_JS)
    assert '.lightbox__content' in js, \
        'app.js should create lightbox with class lightbox__content'
    assert '.lightbox__zoom-content' not in js, \
        'app.js should NOT use lightbox__zoom-content (mismatched legacy)'


def test_inline_css_targets_lightbox_content_not_zoom_content():
    """inline <style> 的 SVG 放大規則必須對齊 app.js DOM (`.lightbox__content`)。"""
    text = _read(GEN_HTML)
    # No stale zoom-content references should remain.
    zoom_hits = re.findall(r'\.lightbox__zoom-content', text)
    assert not zoom_hits, \
        f'gen_html.py still has {len(zoom_hits)} `.lightbox__zoom-content` ' \
        f'references — must be `.lightbox__content` to match app.js DOM'
    # And lightbox SVG sizing rule must exist for the correct class.
    assert re.search(r'\.lightbox__content\s+\.diagram-container\s*\{', text), \
        'inline CSS should target `.lightbox__content .diagram-container` for SVG sizing'


def main():
    print('=' * 72)
    print('LIGHTBOX CLASS ALIGNMENT')
    print('=' * 72)
    tests = [
        ('app_js_uses_lightbox_content_class', test_app_js_uses_lightbox_content_class),
        ('inline_css_targets_lightbox_content_not_zoom_content', test_inline_css_targets_lightbox_content_not_zoom_content),
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
    print(f'\nTOTAL: {passed} PASS / {failed} FAIL  ({len(tests)} cases)')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
