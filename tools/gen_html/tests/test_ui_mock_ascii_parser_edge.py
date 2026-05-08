#!/usr/bin/env python3
"""UI Mock ASCII parser — layered-arch + pyramid detection. Stage ⑧ of 11.

Stage ⑧ scope:
  - layered-arch: outer frame with >=2 sections AND ↓/↑ flow arrow in body.
    Each section becomes a `layer` node; arrows become `flow-down/flow-up`.
  - pyramid: stacked boxes of progressively increasing width joined by `┴`
    characters. Each box's interior text becomes a `layer` (label + pct +
    detail extracted from the lines).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)

ascii_parse = gh._ui_mock_ascii_parse


def _find_all(node, type_):
    out = []
    if node.get('type') == type_:
        out.append(node)
    for c in node.get('children', []):
        out.extend(_find_all(c, type_))
    return out


# ─── layered-arch detection ──────────────────────────────────────────────

def test_layered_arch_via_down_arrow():
    text = '''┌─────────────────────────────────────────────────────┐
│  Presentation Layer                                 │
│  React components: PetCanvas, ClaimFlow             │
│                      ↓ calls (via props)            │
├─────────────────────────────────────────────────────┤
│  Application Layer                                  │
│  Custom hooks: usePet, useClaim                     │
└─────────────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    assert ast is not None
    # Top-level should contain a layered-arch node
    arches = _find_all(ast, 'layered-arch')
    assert len(arches) == 1
    layers = _find_all(arches[0], 'layer')
    assert len(layers) == 2
    flows = _find_all(arches[0], 'flow-down')
    assert len(flows) == 1
    assert 'calls' in flows[0].get('value', '')


def test_layered_arch_three_layers_with_up_flow():
    text = '''┌─────────────────────────────────────────────────────┐
│  Presentation                                       │
│                      ↓ calls                        │
├─────────────────────────────────────────────────────┤
│  Application                                        │
│                      ↓ uses                         │
├─────────────────────────────────────────────────────┤
│  Domain                                             │
│                      ↑ implemented by               │
├─────────────────────────────────────────────────────┤
│  Infrastructure                                     │
└─────────────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    arches = _find_all(ast, 'layered-arch')
    assert len(arches) == 1
    layers = _find_all(arches[0], 'layer')
    assert len(layers) == 4
    flow_down = _find_all(arches[0], 'flow-down')
    flow_up = _find_all(arches[0], 'flow-up')
    assert len(flow_down) == 2
    assert len(flow_up) == 1
    # Labels
    flow_labels = ([f.get('value', '') for f in flow_down] +
                    [f.get('value', '') for f in flow_up])
    assert any('calls' in l for l in flow_labels)
    assert any('implemented by' in l for l in flow_labels)


def test_layered_arch_layer_labels_extracted():
    text = '''┌─────────────────────────────────────────────────────┐
│  Presentation Layer                                 │
│                      ↓                              │
├─────────────────────────────────────────────────────┤
│  Domain Layer                                       │
└─────────────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    layers = _find_all(ast, 'layer')
    assert len(layers) == 2
    labels = [l.get('value', '') for l in layers]
    assert any('Presentation' in l for l in labels)
    assert any('Domain' in l for l in labels)


def test_layered_arch_full_pipeline_render():
    text = '''┌─────────────────────────────────────────────────────┐
│  Presentation Layer                                 │
│                      ↓ calls                        │
├─────────────────────────────────────────────────────┤
│  Application Layer                                  │
└─────────────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    html = gh._ui_mock_render(ast)
    # mermaid block
    assert 'flowchart TB' in html
    assert 'Presentation Layer' in html
    assert 'Application Layer' in html
    assert 'calls' in html


def test_normal_modal_is_not_layered_arch():
    """A modal with sections but no arrows should NOT be classified as layered-arch."""
    text = '''┌──────────────────────────────┐
│ Title                    [X] │
├──────────────────────────────┤
│ Section A                    │
├──────────────────────────────┤
│ Section B                    │
└──────────────────────────────┘'''
    ast = ascii_parse(text)
    arches = _find_all(ast, 'layered-arch')
    assert len(arches) == 0
    assert ast['children'][0]['type'] == 'modal'


# ─── pyramid detection ───────────────────────────────────────────────────

def test_pyramid_three_layers():
    text = '''              ┌─────────────┐
              │  E2E Tests  │
              │   5–10%     │
         ┌────┴─────────────┴────┐
         │  Integration Tests    │
         │     20–30%            │
    ┌────┴───────────────────────┴────┐
    │  Unit Tests                     │
    │     60–70%                      │
    └─────────────────────────────────┘'''
    ast = ascii_parse(text)
    assert ast is not None
    pyramids = _find_all(ast, 'pyramid')
    assert len(pyramids) == 1, f'expected 1 pyramid, got {len(pyramids)}'
    layers = _find_all(pyramids[0], 'layer')
    assert len(layers) == 3
    labels = [l.get('value', '') for l in layers]
    assert any('E2E' in l for l in labels)
    assert any('Integration' in l for l in labels)
    assert any('Unit' in l for l in labels)


def test_pyramid_pct_extracted():
    """Lines containing `%` → pct attr."""
    text = '''              ┌─────────────┐
              │  E2E        │
              │   5–10%     │
         ┌────┴─────────────┴────┐
         │  Unit                 │
         │     90%               │
         └───────────────────────┘'''
    ast = ascii_parse(text)
    layers = _find_all(ast, 'layer')
    assert len(layers) == 2
    pcts = [l['attrs'].get('pct', '') for l in layers]
    assert any('5–10%' in p or '5-10%' in p for p in pcts)
    assert '90%' in pcts


def test_pyramid_full_pipeline_render():
    text = '''              ┌─────────────┐
              │  E2E Tests  │
         ┌────┴─────────────┴────┐
         │  Unit Tests           │
         └───────────────────────┘'''
    ast = ascii_parse(text)
    html = gh._ui_mock_render(ast)
    assert '<svg' in html
    assert 'E2E Tests' in html
    assert 'Unit Tests' in html
    polys = html.count('<polygon')
    assert polys == 2


def test_normal_card_is_not_pyramid():
    """A single rectangular card should NOT be pyramid."""
    text = '''┌────────────────────┐
│ Just a card        │
└────────────────────┘'''
    ast = ascii_parse(text)
    pyramids = _find_all(ast, 'pyramid')
    assert len(pyramids) == 0


# ─── Standalone runner ───────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'UI MOCK ASCII PARSER — edge cases (stage 8)  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('layered_arch_down_arrow', test_layered_arch_via_down_arrow),
        ('layered_arch_three_layers', test_layered_arch_three_layers_with_up_flow),
        ('layered_arch_labels', test_layered_arch_layer_labels_extracted),
        ('layered_arch_full_render', test_layered_arch_full_pipeline_render),
        ('modal_not_layered_arch', test_normal_modal_is_not_layered_arch),
        ('pyramid_three_layers', test_pyramid_three_layers),
        ('pyramid_pct_extracted', test_pyramid_pct_extracted),
        ('pyramid_full_render', test_pyramid_full_pipeline_render),
        ('card_not_pyramid', test_normal_card_is_not_pyramid),
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
