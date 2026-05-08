#!/usr/bin/env python3
"""UI Mock DSL `pyramid` renderer — Stage ④ of 11.

`pyramid` = stacked trapezoid layers (testing pyramid, capability pyramid,
investment pyramid, etc.). Renders as inline SVG embedded in a
`.diagram-container` so existing lightbox can zoom it.

DSL form:
    pyramid {
        layer "E2E Tests"          pct:"5–10%"   detail:"Playwright"
        layer "Integration Tests"  pct:"20–30%"  detail:"xUnit"
        layer "Unit Tests"         pct:"60–70%"  detail:"xUnit + FluentAssertions"
    }
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

parse = gh._ui_mock_dsl_parse
render = gh._ui_mock_render


def render_dsl(text: str) -> str:
    return render(parse(text))


def test_empty_pyramid_renders_svg():
    html = render_dsl('pyramid { }')
    assert '<svg' in html
    assert '</svg>' in html


def test_wrapped_in_diagram_container():
    html = render_dsl('pyramid { layer "L1" }')
    assert 'diagram-container' in html


def test_three_layers_yields_three_polygons():
    text = '''pyramid {
        layer "Top"
        layer "Middle"
        layer "Bottom"
    }'''
    html = render_dsl(text)
    # Each layer is a trapezoid <polygon>
    polygons = re.findall(r'<polygon\b', html)
    assert len(polygons) == 3, f'expected 3 polygons, got {len(polygons)}'
    for label in ['Top', 'Middle', 'Bottom']:
        assert label in html, f'missing {label}'


def test_pct_attr_renders():
    html = render_dsl('pyramid { layer "E2E" pct:"5%" }')
    assert 'E2E' in html
    assert '5%' in html


def test_detail_attr_renders():
    html = render_dsl('pyramid { layer "E2E" detail:"Playwright" }')
    assert 'E2E' in html
    assert 'Playwright' in html


def test_real_world_test_pyramid():
    text = '''pyramid {
        layer "E2E Tests" pct:"5–10%" detail:"Playwright — Critical User Flows"
        layer "Integration Tests" pct:"20–30%" detail:"xUnit + WebApplicationFactory"
        layer "Unit Tests" pct:"60–70%" detail:"xUnit + FluentAssertions"
    }'''
    html = render_dsl(text)
    for s in ['E2E Tests', 'Integration Tests', 'Unit Tests',
              '5–10%', '20–30%', '60–70%',
              'Playwright', 'xUnit', 'FluentAssertions']:
        assert s in html, f'missing {s!r}'
    # Three trapezoids
    assert html.count('<polygon') == 3


def test_top_layer_is_narrower_than_bottom():
    """Verify trapezoid widths increase top → bottom."""
    text = '''pyramid {
        layer "Top"
        layer "Bottom"
    }'''
    html = render_dsl(text)
    # Extract polygon points
    polys = re.findall(r'<polygon[^>]*points="([^"]+)"', html)
    assert len(polys) == 2, f'expected 2 polygons, got {len(polys)}'

    def width_of(points_str):
        # Each polygon has 4 points; we measure max-x minus min-x of the pair
        pairs = [tuple(map(float, p.split(','))) for p in points_str.strip().split(' ') if p]
        xs = [x for x, y in pairs]
        return max(xs) - min(xs)

    w_top = width_of(polys[0])
    w_bot = width_of(polys[1])
    assert w_bot > w_top, f'bottom ({w_bot}) should be wider than top ({w_top})'


def test_html_escape_in_layer_label():
    html = render_dsl('pyramid { layer "<x>" }')
    # Inside SVG <text>, raw < > break parsing — must be escaped
    assert '<x>' not in html
    assert '&lt;x&gt;' in html


def test_single_layer_still_renders():
    html = render_dsl('pyramid { layer "Solo" }')
    assert '<polygon' in html
    assert 'Solo' in html


def main() -> int:
    print('=' * 78)
    print(f'UI MOCK DSL — pyramid (stage 4)  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('empty_pyramid', test_empty_pyramid_renders_svg),
        ('diagram_container', test_wrapped_in_diagram_container),
        ('three_polygons', test_three_layers_yields_three_polygons),
        ('pct_attr', test_pct_attr_renders),
        ('detail_attr', test_detail_attr_renders),
        ('real_world_pyramid', test_real_world_test_pyramid),
        ('width_increases_down', test_top_layer_is_narrower_than_bottom),
        ('html_escape', test_html_escape_in_layer_label),
        ('single_layer', test_single_layer_still_renders),
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
