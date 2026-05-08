#!/usr/bin/env python3
"""PUML SVG dimension stripping + diagram-container CSS rule tests.

Verifies:
1. _strip_svg_dimensions() removes inline width/height attributes and
   pixel rules from style attribute on the outer <svg> tag.
2. _puml_block_to_html() wraps SVG in `.diagram-container--puml`.
3. CSS in skills/gendoc-gen-html/SKILL.md contains the new
   `.diagram-container--puml svg` rule that lets container control width.

Runnable both as pytest and standalone:
    pytest tools/gen_html/tests/
    python3 tools/gen_html/tests/test_puml_styling.py
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'
SKILL_MD = REPO / 'skills' / 'gendoc-gen-html' / 'SKILL.md'

spec = importlib.util.spec_from_file_location('gen_html', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


# ─── Sample PUML SVG output from PlantUML CLI (real-world shape) ───────────
SAMPLE_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" \
xmlns:xlink="http://www.w3.org/1999/xlink" contentStyleType="text/css" \
data-diagram-type="CLASS" height="707px" preserveAspectRatio="none" \
style="width:671px;height:707px;background:#FFFFFF;" version="1.1" \
viewBox="0 0 671 707" width="671px" zoomAndPan="magnify">
  <rect x="0" y="0" width="100" height="50"/>
</svg>'''


# ──────────────────────────────────────────────────────────────────────────
# 1. _strip_svg_dimensions
# ──────────────────────────────────────────────────────────────────────────

def test_strip_removes_width_attr():
    out = gh._strip_svg_dimensions(SAMPLE_SVG)
    assert 'width="671px"' not in out
    assert 'width="' not in out.split('>', 1)[0]   # no width on outer svg


def test_strip_removes_height_attr():
    out = gh._strip_svg_dimensions(SAMPLE_SVG)
    assert 'height="707px"' not in out
    assert 'height="' not in out.split('>', 1)[0]


def test_strip_removes_inline_style_width_height():
    out = gh._strip_svg_dimensions(SAMPLE_SVG)
    head = out.split('>', 1)[0]
    assert 'width:671px' not in head
    assert 'height:707px' not in head
    assert 'width:' not in head
    assert 'height:' not in head


def test_strip_keeps_other_style_props():
    """background should remain in style attribute."""
    out = gh._strip_svg_dimensions(SAMPLE_SVG)
    assert 'background:#FFFFFF' in out


def test_strip_keeps_viewBox():
    """viewBox is essential for proper SVG scaling — must NOT be stripped."""
    out = gh._strip_svg_dimensions(SAMPLE_SVG)
    assert 'viewBox="0 0 671 707"' in out


def test_strip_keeps_inner_rect():
    """Only outer <svg> tag should be touched. Inner content untouched."""
    out = gh._strip_svg_dimensions(SAMPLE_SVG)
    assert '<rect x="0" y="0" width="100" height="50"/>' in out


def test_strip_keeps_data_diagram_type():
    out = gh._strip_svg_dimensions(SAMPLE_SVG)
    assert 'data-diagram-type="CLASS"' in out


def test_strip_idempotent():
    """Running strip twice should be no-op the second time."""
    once = gh._strip_svg_dimensions(SAMPLE_SVG)
    twice = gh._strip_svg_dimensions(once)
    assert once == twice


# ──────────────────────────────────────────────────────────────────────────
# 2. _puml_block_to_html wraps with diagram-container--puml
# ──────────────────────────────────────────────────────────────────────────

def test_puml_block_html_uses_diagram_container_class():
    """If SVG conversion succeeded, output must wrap with both diagram-container
    and diagram-container--puml classes."""
    # Stub _plantuml_to_svg so test doesn't need plantuml CLI / network
    original = gh._plantuml_to_svg
    gh._plantuml_to_svg = lambda t: SAMPLE_SVG
    try:
        html = gh._puml_block_to_html(['class A {}'])
        assert 'class="diagram-container diagram-container--puml"' in html
        assert '<svg' in html
    finally:
        gh._plantuml_to_svg = original


# ──────────────────────────────────────────────────────────────────────────
# 3. SKILL.md CSS contains the new puml svg rule
# ──────────────────────────────────────────────────────────────────────────

def test_skill_md_has_puml_svg_css_rule():
    text = SKILL_MD.read_text(encoding='utf-8')
    # Expect the new selector and the key responsive props
    assert '.diagram-container--puml svg' in text, \
        'Missing .diagram-container--puml svg CSS selector in SKILL.md'
    # At minimum these properties must be set
    block_match = re.search(
        r'\.diagram-container--puml svg\s*\{([^}]+)\}', text, re.DOTALL,
    )
    assert block_match, 'CSS block for .diagram-container--puml svg not found'
    block = block_match.group(1)
    for prop in ('width:', '100%', 'height:', 'auto'):
        assert prop in block, \
            f'Required CSS property "{prop}" missing in puml svg rule'


# ──────────────────────────────────────────────────────────────────────────
# 4. End-to-end: real plantuml flow if CLI available, else skip
# ──────────────────────────────────────────────────────────────────────────

def test_e2e_strip_via_real_pipeline():
    """Run _strip_svg_dimensions on the sample, then verify final SVG is
    embeddable in HTML without fixed dimensions."""
    cleaned = gh._strip_svg_dimensions(SAMPLE_SVG)
    # The cleaned outer tag must NOT contain width/height attrs or inline px
    head = cleaned.split('>', 1)[0]
    assert not re.search(r'\s(?:width|height)="[\d.]+px"', head), \
        f'outer svg still has fixed px dimension: {head}'
    assert not re.search(r'(?:width|height)\s*:\s*[\d.]+px', head), \
        f'outer svg style still has fixed px dimension: {head}'


# ──────────────────────────────────────────────────────────────────────────
# Standalone runner
# ──────────────────────────────────────────────────────────────────────────

def main():
    print('=' * 78)
    print(f'PUML STYLING TEST  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('strip_removes_width_attr', test_strip_removes_width_attr),
        ('strip_removes_height_attr', test_strip_removes_height_attr),
        ('strip_removes_inline_style_width_height',
         test_strip_removes_inline_style_width_height),
        ('strip_keeps_other_style_props', test_strip_keeps_other_style_props),
        ('strip_keeps_viewBox', test_strip_keeps_viewBox),
        ('strip_keeps_inner_rect', test_strip_keeps_inner_rect),
        ('strip_keeps_data_diagram_type', test_strip_keeps_data_diagram_type),
        ('strip_idempotent', test_strip_idempotent),
        ('puml_block_html_uses_diagram_container_class',
         test_puml_block_html_uses_diagram_container_class),
        ('skill_md_has_puml_svg_css_rule', test_skill_md_has_puml_svg_css_rule),
        ('e2e_strip_via_real_pipeline', test_e2e_strip_via_real_pipeline),
    ]
    fail = 0
    for name, fn in tests:
        try:
            fn()
            print(f'  ✅ [{name}] PASS')
        except AssertionError as e:
            fail += 1
            print(f'  ❌ [{name}] FAIL — {e}')
        except Exception as e:
            fail += 1
            print(f'  ❌ [{name}] ERROR — {type(e).__name__}: {e}')
    print('\n' + '=' * 78)
    print(f'TOTAL: {len(tests) - fail} PASS / {fail} FAIL')
    print('=' * 78)
    return 0 if fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
