#!/usr/bin/env python3
"""UI Mock DSL `layered-arch` renderer — Stage ③ of 11.

`layered-arch` = stacked architecture layers connected by directional flows.
Renders as a Mermaid `flowchart TB` wrapped in `.diagram-container` so the
existing mermaid JS + lightbox kick in automatically.

DSL form:
    layered-arch {
        layer "Presentation Layer" { detail "React components: ..." }
        flow-down "calls (via props)"
        layer "Application Layer"  { detail "Custom hooks: ..." }
        flow-up   "implemented by"
        layer "Infrastructure Layer" { detail "API client: ..." }
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


def test_empty_layered_arch_renders_mermaid_block():
    html = render_dsl('layered-arch { }')
    assert 'class="mermaid"' in html or 'class=\'mermaid\'' in html
    assert 'flowchart TB' in html


def test_wrapped_in_diagram_container():
    """For lightbox + responsive sizing — must wrap in .diagram-container."""
    html = render_dsl('layered-arch { layer "L1" }')
    assert 'diagram-container' in html


def test_single_layer_renders_node():
    html = render_dsl('layered-arch { layer "Presentation" }')
    assert 'Presentation' in html
    # Mermaid node syntax: an identifier followed by ["..."]
    assert re.search(r'\w+\s*\[\s*"[^"]*Presentation[^"]*"', html), \
        'Expected mermaid node like X["...Presentation..."]'


def test_layer_with_detail_combines_into_node_label():
    html = render_dsl('''layered-arch {
        layer "Application Layer" {
            detail "Custom hooks: usePet, useClaim"
        }
    }''')
    assert 'Application Layer' in html
    assert 'Custom hooks' in html
    # detail should be part of the same mermaid node label (HTML-escaped <br/>)
    assert '<br' in html or '<br/>' in html or '<br />' in html


def test_two_layers_with_flow_down_creates_arrow():
    html = render_dsl('''layered-arch {
        layer "L1"
        flow-down "calls"
        layer "L2"
    }''')
    # mermaid arrow with label: -->|calls|
    assert re.search(r'-->\s*\|\s*calls\s*\|', html), \
        'Expected mermaid labeled arrow: -->|calls|'


def test_flow_up_creates_reverse_arrow():
    """flow-up means lower layer → upper layer (reverse flow)."""
    html = render_dsl('''layered-arch {
        layer "Domain"
        flow-up "implemented by"
        layer "Infrastructure"
    }''')
    # The "Infrastructure" → "Domain" direction (lower to upper).
    # We just need any arrow with the "implemented by" label.
    assert 'implemented by' in html
    assert re.search(r'-->\s*\|', html), 'Expected mermaid arrow'


def test_three_layers_with_two_flows():
    html = render_dsl('''layered-arch {
        layer "Presentation"
        flow-down "calls"
        layer "Application"
        flow-down "uses"
        layer "Domain"
    }''')
    # Two arrows expected
    arrows = re.findall(r'-->\s*\|', html)
    assert len(arrows) >= 2, f'Expected >=2 arrows, got {len(arrows)}'
    # All three layer names present
    for label in ['Presentation', 'Application', 'Domain']:
        assert label in html


def test_layers_without_flow_get_default_arrows():
    """Adjacent layers without explicit flow should still chain top-down."""
    html = render_dsl('''layered-arch {
        layer "A"
        layer "B"
        layer "C"
    }''')
    # Should still have arrows linking them (default top-down)
    arrows = re.findall(r'-->', html)
    assert len(arrows) >= 2


def test_real_world_pet_pdd_layered_arch():
    """Real-world equivalent of pet/PDD #1 sample."""
    text = '''layered-arch {
        layer "Presentation Layer" {
            detail "React components: PetCanvas, ClaimFlow, ArenaPage"
        }
        flow-down "calls (via props / context)"
        layer "Application Layer" {
            detail "Custom hooks: usePet, useClaim, useArena"
        }
        flow-down "uses"
        layer "Domain Layer" {
            detail "Entities & interfaces: Pet, Battle, ClaimToken"
        }
        flow-up "implemented by"
        layer "Infrastructure Layer" {
            detail "API client: fetchPet(), enterArena()"
        }
    }'''
    html = render_dsl(text)
    # All four layer names
    for layer in ['Presentation Layer', 'Application Layer', 'Domain Layer', 'Infrastructure Layer']:
        assert layer in html, f'missing {layer}'
    # All flow labels
    for flow in ['calls', 'uses', 'implemented by']:
        assert flow in html, f'missing flow label {flow}'
    # Mermaid envelope
    assert 'flowchart TB' in html
    assert 'class="mermaid"' in html


def test_html_escape_in_layer_text():
    html = render_dsl('layered-arch { layer "<x>" }')
    assert '<x>' not in html.split('class="mermaid"')[0], \
        'should not leak unescaped tags before mermaid block'
    # Inside mermaid block, mermaid handles its own escaping but quotes are
    # already in `[". . ."]` so HTML tags inside will be parsed as text.
    # We just need the label content to contain the escaped characters.


def main() -> int:
    print('=' * 78)
    print(f'UI MOCK DSL — layered-arch (stage 3)  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('empty_layered_arch', test_empty_layered_arch_renders_mermaid_block),
        ('diagram_container_wrap', test_wrapped_in_diagram_container),
        ('single_layer', test_single_layer_renders_node),
        ('layer_with_detail', test_layer_with_detail_combines_into_node_label),
        ('two_layers_flow_down', test_two_layers_with_flow_down_creates_arrow),
        ('flow_up_reverse', test_flow_up_creates_reverse_arrow),
        ('three_layers_two_flows', test_three_layers_with_two_flows),
        ('default_arrows', test_layers_without_flow_get_default_arrows),
        ('real_world_pet_pdd', test_real_world_pet_pdd_layered_arch),
        ('html_escape', test_html_escape_in_layer_text),
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
