#!/usr/bin/env python3
"""Lightbox zoom canonical assets — `docs/pages/assets/{app.js,style.css}`
必須含完整 zoom/pan/hint/controls 實作.

歷史脈絡：
- 71f7e56 (2026-05-09) 加 lightbox zoom GREEN，但只更新 SKILL.md，沒同步
  到 canonical `docs/pages/assets/app.js` 跟 `style.css`
- _deploy_canonical_assets() 把 canonical 複製到目標專案 → 線上版本永遠
  沒 zoom（只有最簡 click-to-clone）
- fce73b9 (2026-05-11) 因為 inline CSS 跟退化版 app.js 不對齊，把 inline
  CSS 從 `.lightbox__zoom-content` rename 回 `.lightbox__content` 對齊
  退化版 → 鎖死退化方向

本 test 確保 canonical assets 永遠帶完整 zoom 實作。

涵蓋（SKILL.md `Line 703-849` 的 spec）：
- CSS：.lightbox__zoom-content / .lightbox__hint / .lightbox__controls
- JS：wheel zoom + drag pan + keyboard +/-/0/Esc + touch pinch + +/-/reset buttons
- 限定 .diagram-container（mermaid + puml SVG），不抓 <img> / <a href>
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
APP_JS = REPO / 'docs' / 'pages' / 'assets' / 'app.js'
STYLE_CSS = REPO / 'docs' / 'pages' / 'assets' / 'style.css'
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'


def _read(p):
    return p.read_text(encoding='utf-8')


# ─── 1: canonical app.js uses zoom-content DOM ───────────────────────

def test_LB1_app_js_uses_zoom_content_class():
    """canonical app.js 必須建立 `.lightbox__zoom-content` 容器（zoom 版本），
    不能退回 legacy `.lightbox__content`."""
    js = _read(APP_JS)
    assert '.lightbox__zoom-content' in js or 'lightbox__zoom-content' in js, \
        'canonical app.js must use lightbox__zoom-content (zoom version)'


def test_LB1_app_js_does_not_use_legacy_content_class():
    """canonical app.js 不能再用 legacy `.lightbox__content`（沒 zoom 能力的版本）."""
    js = _read(APP_JS)
    # Search for class="lightbox__content" or 'lightbox__content' followed by
    # a non-zoom char — i.e. it's the legacy class, not the zoom-content one.
    legacy_matches = re.findall(r'lightbox__content(?!\w*zoom)', js)
    # Filter out lightbox__content as substring of lightbox__content-* legitimate
    legacy_count = sum(1 for m in legacy_matches)
    assert legacy_count == 0, \
        f'canonical app.js still has {legacy_count} legacy `lightbox__content` references'


def test_LB1_app_js_has_hint_element():
    """canonical app.js 必須建立 `.lightbox__hint` 元素（操作提示文字）."""
    js = _read(APP_JS)
    assert 'lightbox__hint' in js, \
        'canonical app.js must create .lightbox__hint element (operation hint)'


def test_LB1_app_js_has_controls_element():
    """canonical app.js 必須建立 `.lightbox__controls` 元素（[+] [-] [⤺] buttons）."""
    js = _read(APP_JS)
    assert 'lightbox__controls' in js, \
        'canonical app.js must create .lightbox__controls element ([+] [-] [reset])'


# ─── 2: canonical app.js zoom/pan/keyboard/touch event handlers ──────

def test_LB1_app_js_has_wheel_zoom():
    """canonical app.js 必須含 `addEventListener('wheel'` — 滾輪縮放."""
    js = _read(APP_JS)
    assert ("addEventListener('wheel'" in js
            or 'addEventListener("wheel"' in js), \
        'canonical app.js must have wheel event listener for zoom'


def test_LB1_app_js_has_drag_pan():
    """canonical app.js 必須含 `addEventListener('mousedown'` — 拖曳平移."""
    js = _read(APP_JS)
    assert ("addEventListener('mousedown'" in js
            or 'addEventListener("mousedown"' in js), \
        'canonical app.js must have mousedown event listener for drag pan'


def test_LB1_app_js_has_keyboard_shortcuts():
    """canonical app.js 必須含 `addEventListener('keydown'` — +/-/0/Esc."""
    js = _read(APP_JS)
    assert ("addEventListener('keydown'" in js
            or 'addEventListener("keydown"' in js), \
        'canonical app.js must have keydown event listener for keyboard shortcuts'


def test_LB1_app_js_has_touch():
    """canonical app.js 必須含 `addEventListener('touchstart'` — 觸控 pinch zoom."""
    js = _read(APP_JS)
    assert ("addEventListener('touchstart'" in js
            or 'addEventListener("touchstart"' in js), \
        'canonical app.js must have touchstart event listener for pinch zoom'


def test_LB1_app_js_zoom_function_exists():
    """canonical app.js 必須有 cursor-centered zoom 函式（lbZoomAt / lbApply）."""
    js = _read(APP_JS)
    assert 'lbZoomAt' in js or 'zoomAt' in js, \
        'canonical app.js must have a zoom helper function (lbZoomAt or similar)'
    assert 'lbApply' in js or re.search(r'function\s+\w*[Aa]pply\b', js), \
        'canonical app.js must have a transform-apply function'


# ─── 3: canonical app.js targets only .diagram-container (not img/a) ─

def test_LB1_app_js_targets_diagram_container():
    """canonical app.js click handler 必須限定 `.diagram-container` — 涵蓋
    mermaid + puml SVG，不誤抓 <img> / <a href>。"""
    js = _read(APP_JS)
    assert "querySelectorAll('.diagram-container')" in js \
        or 'querySelectorAll(".diagram-container")' in js, \
        'canonical app.js must select .diagram-container for click-to-open'


# ─── 4: canonical style.css has zoom/hint/controls rules ─────────────

def test_LB1_style_css_has_zoom_content_rule():
    """canonical style.css 必須含 `.lightbox__zoom-content` rule（容器尺寸 + cursor）."""
    css = _read(STYLE_CSS)
    assert re.search(r'\.lightbox__zoom-content\s*\{', css), \
        'canonical style.css must define .lightbox__zoom-content'


def test_LB1_style_css_has_zoom_content_child_absolute():
    """`.lightbox__zoom-content > *` 必須 `position: absolute` +
    `transform-origin: 0 0` — zoom 數學前提."""
    css = _read(STYLE_CSS)
    pattern = (
        r'\.lightbox__zoom-content\s*>\s*\*\s*\{'
        r'[^}]*position\s*:\s*absolute[^}]*'
        r'transform-origin\s*:\s*0\s+0'
    )
    assert re.search(pattern, css, re.DOTALL), \
        '.lightbox__zoom-content > * must have position: absolute + transform-origin: 0 0'


def test_LB1_style_css_has_hint_rule():
    """canonical style.css 必須含 `.lightbox__hint` rule."""
    css = _read(STYLE_CSS)
    assert re.search(r'\.lightbox__hint\s*\{', css), \
        'canonical style.css must define .lightbox__hint'


def test_LB1_style_css_has_controls_rule():
    """canonical style.css 必須含 `.lightbox__controls` rule."""
    css = _read(STYLE_CSS)
    assert re.search(r'\.lightbox__controls\s*\{', css), \
        'canonical style.css must define .lightbox__controls'


def test_LB1_style_css_dragging_cursor():
    """`.lightbox__zoom-content.dragging` 必須 `cursor: grabbing`."""
    css = _read(STYLE_CSS)
    pattern = r'\.lightbox__zoom-content\.dragging\s*\{[^}]*cursor\s*:\s*grabbing'
    assert re.search(pattern, css), \
        '.lightbox__zoom-content.dragging must use cursor: grabbing'


# ─── 5: gen_html.py inline <style> 不再 override legacy class ─────────

def test_LB1_inline_no_stale_legacy_class_override():
    """gen_html.py inline `<style>` 不應再有 `.lightbox__content` overrides —
    canonical style.css 用 `.lightbox__zoom-content`，inline 殘留會死碼。"""
    text = _read(GEN_HTML)
    m = re.search(r'HTML_TEMPLATE\s*=\s*"""(.*?)"""', text, re.DOTALL)
    tpl = m.group(1) if m else ''
    m = re.search(r'<style>(.*?)</style>', tpl, re.DOTALL)
    inline = m.group(1) if m else ''
    legacy_hits = re.findall(r'\.lightbox__content\b', inline)
    assert not legacy_hits, (
        f'inline <style> still has {len(legacy_hits)} `.lightbox__content` '
        f'references — legacy class, canonical now uses .lightbox__zoom-content'
    )


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print('LIGHTBOX ZOOM canonical assets — SKILL.md spec sync to docs/pages/assets/')
    print('=' * 78)
    tests = [
        ('LB1_app_js_uses_zoom_content_class', test_LB1_app_js_uses_zoom_content_class),
        ('LB1_app_js_does_not_use_legacy_content_class', test_LB1_app_js_does_not_use_legacy_content_class),
        ('LB1_app_js_has_hint_element', test_LB1_app_js_has_hint_element),
        ('LB1_app_js_has_controls_element', test_LB1_app_js_has_controls_element),
        ('LB1_app_js_has_wheel_zoom', test_LB1_app_js_has_wheel_zoom),
        ('LB1_app_js_has_drag_pan', test_LB1_app_js_has_drag_pan),
        ('LB1_app_js_has_keyboard_shortcuts', test_LB1_app_js_has_keyboard_shortcuts),
        ('LB1_app_js_has_touch', test_LB1_app_js_has_touch),
        ('LB1_app_js_zoom_function_exists', test_LB1_app_js_zoom_function_exists),
        ('LB1_app_js_targets_diagram_container', test_LB1_app_js_targets_diagram_container),
        ('LB1_style_css_has_zoom_content_rule', test_LB1_style_css_has_zoom_content_rule),
        ('LB1_style_css_has_zoom_content_child_absolute', test_LB1_style_css_has_zoom_content_child_absolute),
        ('LB1_style_css_has_hint_rule', test_LB1_style_css_has_hint_rule),
        ('LB1_style_css_has_controls_rule', test_LB1_style_css_has_controls_rule),
        ('LB1_style_css_dragging_cursor', test_LB1_style_css_dragging_cursor),
        ('LB1_inline_no_stale_legacy_class_override', test_LB1_inline_no_stale_legacy_class_override),
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
