#!/usr/bin/env python3
"""Lightbox CSS class alignment — inline <style> 規則的 class name 必須跟
canonical `assets/app.js` 創建的 DOM 一致。

歷史：
- bccc935 加 `.lightbox__zoom-content ...` CSS rule（zoom 版）
- 但 docs/pages/assets/app.js 從未同步 → 用 `.lightbox__content`（退化版）
  → CSS rule 永遠不 apply → lightbox 開了 SVG 不放大
- fce73b9 (2026-05-11) 為對齊退化版，把 inline CSS rename 回 `.lightbox__content`
  → 鎖死退化方向
- LB1 群還原（2026-05-11 same day）：canonical app.js + style.css 補回完整
  zoom 版，inline CSS 也跟著回到 `.lightbox__zoom-content`

本 test：anti-regression — 任何把 canonical 退回 `.lightbox__content`
（沒 zoom 能力）的 commit 都會 FAIL。
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


def test_app_js_uses_zoom_content_class_not_legacy():
    """canonical `app.js` lightbox DOM 必須用 `.lightbox__zoom-content`（zoom 版），
    不能退回 legacy `.lightbox__content`（沒 zoom 能力）。"""
    js = _read(APP_JS)
    assert 'lightbox__zoom-content' in js, \
        'canonical app.js must create lightbox with class lightbox__zoom-content (zoom version)'
    legacy = re.findall(r'lightbox__content(?!\w*zoom)', js)
    assert not legacy, \
        f'canonical app.js still has {len(legacy)} legacy `lightbox__content` ' \
        f'references — must use `lightbox__zoom-content` (zoom version)'


def test_inline_css_targets_zoom_content_not_legacy():
    """inline <style> SVG 放大 rule 必須對齊 canonical app.js DOM
    (`.lightbox__zoom-content`)，不能再用 legacy `.lightbox__content`。"""
    text = _read(GEN_HTML)
    legacy_hits = re.findall(r'\.lightbox__content\b', text)
    assert not legacy_hits, \
        f'gen_html.py still has {len(legacy_hits)} legacy `.lightbox__content` ' \
        f'references — must be `.lightbox__zoom-content` to match canonical app.js DOM'
    assert re.search(r'\.lightbox__zoom-content\s+\.diagram-container\s*\{', text), \
        'inline CSS should target `.lightbox__zoom-content .diagram-container` for SVG sizing'


def main():
    print('=' * 72)
    print('LIGHTBOX CLASS ALIGNMENT (anti-regression for LB1 zoom restoration)')
    print('=' * 72)
    tests = [
        ('app_js_uses_zoom_content_class_not_legacy',
         test_app_js_uses_zoom_content_class_not_legacy),
        ('inline_css_targets_zoom_content_not_legacy',
         test_inline_css_targets_zoom_content_not_legacy),
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
