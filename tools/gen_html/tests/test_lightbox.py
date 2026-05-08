#!/usr/bin/env python3
"""Lint test：skills/gendoc-gen-html/SKILL.md 內 lightbox + zoom 規格完備。

Phase 2：擴 lightbox 加 zoom/pan + UI hint。涵蓋對象嚴格限定：
- .diagram-container（mermaid）
- .diagram-container--puml（puml SVG）
排除：<img>、<a href> （依使用者指示）。

CSS 必含：
- .lightbox（既有）
- .lightbox__zoom-content（zoom 容器）
- .lightbox__hint（操作 hint UI）
- .lightbox__controls（zoom +/-/reset 按鈕）

JS 必含：
- 點擊 .diagram-container → lightbox.classList.add('active')
- wheel event listener（zoom）
- mousedown / mousemove / mouseup（drag pan）
- keydown（+/-/0/Escape）
- touchstart / touchmove（pinch zoom + drag pan）

JS 必**不**含：
- querySelectorAll('img')
- querySelectorAll('a[href')
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
SKILL_MD = REPO / 'skills' / 'gendoc-gen-html' / 'SKILL.md'


def _read_skill():
    return SKILL_MD.read_text(encoding='utf-8')


def test_skill_md_has_lightbox_zoom_content_css():
    """CSS 段落應含 .lightbox__zoom-content（zoom 容器）。"""
    text = _read_skill()
    assert '.lightbox__zoom-content' in text, \
        'Missing .lightbox__zoom-content CSS class'


def test_skill_md_has_lightbox_hint_css():
    """CSS 應含 .lightbox__hint（UI 操作提示）。"""
    text = _read_skill()
    assert '.lightbox__hint' in text, \
        'Missing .lightbox__hint CSS class'


def test_skill_md_has_lightbox_controls_css():
    """CSS 應含 .lightbox__controls（zoom +/-/reset buttons 容器）。"""
    text = _read_skill()
    assert '.lightbox__controls' in text, \
        'Missing .lightbox__controls CSS class'


def test_skill_md_js_has_wheel_zoom():
    """JS 應有 wheel event listener。"""
    text = _read_skill()
    assert "addEventListener('wheel'" in text or \
        'addEventListener("wheel"' in text, \
        'Missing wheel event listener for zoom'


def test_skill_md_js_has_drag_pan():
    """JS 應有 mousedown/mousemove 處理 drag pan。"""
    text = _read_skill()
    assert "addEventListener('mousedown'" in text or \
        'addEventListener("mousedown"' in text, \
        'Missing mousedown event listener for drag pan'


def test_skill_md_js_has_keyboard_shortcuts():
    """JS 應有 keydown 處理 +/-/0/Escape。"""
    text = _read_skill()
    assert "addEventListener('keydown'" in text or \
        'addEventListener("keydown"' in text, \
        'Missing keydown event listener for keyboard shortcuts'


def test_skill_md_js_has_touch():
    """JS 應有 touchstart/touchmove 處理 pinch zoom + drag。"""
    text = _read_skill()
    has_touch = ("addEventListener('touchstart'" in text or
                 'addEventListener("touchstart"' in text)
    assert has_touch, 'Missing touchstart event listener for touch zoom/pan'


def test_skill_md_js_targets_diagram_container():
    """JS 必須繼續 target .diagram-container（涵蓋 mermaid + puml）。"""
    text = _read_skill()
    assert "querySelectorAll('.diagram-container')" in text or \
        'querySelectorAll(".diagram-container")' in text, \
        'Missing .diagram-container selector in lightbox JS'


def test_skill_md_js_does_not_target_img():
    """JS 必**不**能 target <img>（依使用者指示，<img> 不涵蓋）。"""
    text = _read_skill()
    # 在 lightbox 區塊找
    lightbox_section_match = re.search(
        r'(// ─── Lightbox.*?(?=// ─── |$))', text, re.DOTALL,
    )
    if not lightbox_section_match:
        return  # 沒找到 lightbox section，pass
    section = lightbox_section_match.group(1)
    assert "querySelectorAll('img')" not in section, \
        'Lightbox should NOT target <img> (per user spec)'
    assert 'querySelectorAll("img")' not in section, \
        'Lightbox should NOT target <img> (per user spec)'


def test_skill_md_js_does_not_target_anchor():
    """JS 必**不**能 target <a href>（依使用者指示）。"""
    text = _read_skill()
    lightbox_section_match = re.search(
        r'(// ─── Lightbox.*?(?=// ─── |$))', text, re.DOTALL,
    )
    if not lightbox_section_match:
        return
    section = lightbox_section_match.group(1)
    assert "querySelectorAll('a[" not in section, \
        'Lightbox should NOT target <a href> (per user spec)'


def main():
    print('=' * 78)
    print(f'LIGHTBOX LINT TEST  source={SKILL_MD}')
    print('=' * 78)
    tests = [
        ('css_has_zoom_content', test_skill_md_has_lightbox_zoom_content_css),
        ('css_has_hint', test_skill_md_has_lightbox_hint_css),
        ('css_has_controls', test_skill_md_has_lightbox_controls_css),
        ('js_has_wheel_zoom', test_skill_md_js_has_wheel_zoom),
        ('js_has_drag_pan', test_skill_md_js_has_drag_pan),
        ('js_has_keyboard', test_skill_md_js_has_keyboard_shortcuts),
        ('js_has_touch', test_skill_md_js_has_touch),
        ('js_targets_diagram_container', test_skill_md_js_targets_diagram_container),
        ('js_does_not_target_img', test_skill_md_js_does_not_target_img),
        ('js_does_not_target_anchor', test_skill_md_js_does_not_target_anchor),
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
    print('\n' + '=' * 78)
    print(f'TOTAL: {passed} PASS / {failed} FAIL  ({len(tests)} cases)')
    print('=' * 78)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
