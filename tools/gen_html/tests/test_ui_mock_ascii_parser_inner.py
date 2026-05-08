#!/usr/bin/env python3
"""UI Mock ASCII parser — inner boxes / form-row / hint / info. Stage ⑦ of 11.

Stage ⑦ scope:
- Nested ┌──┐ ... └──┘ inside a segment → input or code-block
- Heuristic: multi-line nested box with `{` braces or json-like content
  → code-block; else single-line text → input (with placeholder text)
- "helper：..." line → hint
- "ⓘ ..." line (info circle) → info  (note: stage ⑤ already created `info`
  for free text; stage ⑦ explicitly tags `ⓘ` as info regardless of content)
- A text line immediately followed by a nested ┌──┐ box becomes a form-row:
  field { label="...", required if line ends with `*` or contains `（必填）`,
          input { placeholder=... } }
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


# ─── Input box detection ─────────────────────────────────────────────────

def test_nested_box_with_text_becomes_input():
    text = '''┌────────────────────────────────────────────┐
│ Title                                  [X] │
├────────────────────────────────────────────┤
│ ┌────────────────────────────────────────┐ │
│ │ N8N 銷售報表工作流                      │ │
│ └────────────────────────────────────────┘ │
└────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    inputs = _find_all(ast, 'input')
    assert len(inputs) == 1
    placeholder = inputs[0]['attrs'].get('placeholder', '')
    assert 'N8N 銷售報表工作流' in placeholder


def test_nested_multiline_box_becomes_code_block():
    """Multi-line nested box with braces → code-block."""
    text = '''┌────────────────────────────────────────────┐
│ JSON Response                              │
├────────────────────────────────────────────┤
│ ┌────────────────────────────────────────┐ │
│ │ {                                      │ │
│ │   "ok": true,                          │ │
│ │   "value": 42                          │ │
│ │ }                                      │ │
│ └────────────────────────────────────────┘ │
└────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    code_blocks = _find_all(ast, 'code-block')
    assert len(code_blocks) == 1
    val = code_blocks[0].get('value', '') or ''
    assert '"ok"' in val or '"value"' in val


def test_two_nested_boxes_yield_two_inputs():
    text = '''┌────────────────────────────┐
│ Form                       │
├────────────────────────────┤
│ ┌────────────────────────┐ │
│ │ Field 1                │ │
│ └────────────────────────┘ │
│ ┌────────────────────────┐ │
│ │ Field 2                │ │
│ └────────────────────────┘ │
└────────────────────────────┘'''
    ast = ascii_parse(text)
    inputs = _find_all(ast, 'input')
    assert len(inputs) == 2


# ─── Form-row composition ────────────────────────────────────────────────

def test_label_followed_by_input_becomes_field():
    """`Label*` line followed by ┌──┐ box → field { label, required, input }."""
    text = '''┌────────────────────────────────────────────┐
│ Title                                  [X] │
├────────────────────────────────────────────┤
│ Token 描述（必填）*                         │
│ ┌────────────────────────────────────────┐ │
│ │ N8N 銷售報表工作流                      │ │
│ └────────────────────────────────────────┘ │
└────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    fields = _find_all(ast, 'field')
    assert len(fields) == 1, f'expected 1 field, got {len(fields)}'
    field = fields[0]
    label = field['attrs'].get('label', '')
    assert 'Token 描述' in label
    assert field['attrs'].get('required') is True
    # Field must contain the input child
    inputs = _find_all(field, 'input')
    assert len(inputs) == 1


def test_label_without_required_marker():
    text = '''┌────────────────────────────────────┐
│ Title                          [X] │
├────────────────────────────────────┤
│ Description                        │
│ ┌────────────────────────────────┐ │
│ │ Optional text                  │ │
│ └────────────────────────────────┘ │
└────────────────────────────────────┘'''
    ast = ascii_parse(text)
    fields = _find_all(ast, 'field')
    assert len(fields) == 1
    field = fields[0]
    assert 'Description' in field['attrs'].get('label', '')
    # required should be falsy
    assert not field['attrs'].get('required')


# ─── Hint detection ──────────────────────────────────────────────────────

def test_helper_prefix_yields_hint():
    text = '''┌────────────────────────────────────┐
│ Title                          [X] │
├────────────────────────────────────┤
│ helper：說明此 Token 的用途          │
└────────────────────────────────────┘'''
    ast = ascii_parse(text)
    hints = _find_all(ast, 'hint')
    assert len(hints) >= 1
    val = hints[0].get('value', '')
    assert '說明此 Token' in val
    # The "helper：" prefix should not be in the value
    assert 'helper' not in val.lower()


# ─── Info detection (ⓘ marker) ───────────────────────────────────────────

def test_info_circle_marker_yields_info():
    text = '''┌────────────────────────────────────┐
│ Title                          [X] │
├────────────────────────────────────┤
│ ⓘ 建議每個工作流獨立 Token          │
└────────────────────────────────────┘'''
    ast = ascii_parse(text)
    infos = _find_all(ast, 'info')
    # At least one info node with the message
    assert any('建議每個工作流' in (i.get('value') or '') for i in infos)


# ─── Pipeline render check ───────────────────────────────────────────────

def test_full_pipeline_form_modal():
    """Real-world ish: erp/PDD #3 modal with form."""
    text = '''┌────────────────────────────────────────────┐
│ ◉ 建立 API Token                       [X] │
├────────────────────────────────────────────┤
│ Token 描述（必填）*                         │
│ ┌────────────────────────────────────────┐ │
│ │ N8N 銷售報表工作流                      │ │
│ └────────────────────────────────────────┘ │
│ helper：說明此 Token 的用途，方便日後識別   │
├────────────────────────────────────────────┤
│ ⓘ 建議每個 N8N 工作流使用獨立 Token        │
├────────────────────────────────────────────┤
│              [取消]   [建立 Token]（主）   │
└────────────────────────────────────────────┘'''
    ast = ascii_parse(text)
    html = gh._ui_mock_render(ast)
    # Title + button labels
    assert '建立 API Token' in html
    assert '取消' in html and '建立 Token' in html
    # Field structure
    assert 'umock__field' in html
    # Input renders
    assert 'umock__input' in html
    # Hint
    assert 'umock__hint' in html
    # Info
    assert 'umock__info' in html
    # No raw box-drawing leakage
    for c in '┌┐└┘├┤':
        assert c not in html


# ─── Standalone runner ───────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'UI MOCK ASCII PARSER — inner boxes (stage 7)  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('nested_box_input', test_nested_box_with_text_becomes_input),
        ('nested_multiline_code_block', test_nested_multiline_box_becomes_code_block),
        ('two_nested_inputs', test_two_nested_boxes_yield_two_inputs),
        ('label_input_field', test_label_followed_by_input_becomes_field),
        ('label_without_required', test_label_without_required_marker),
        ('helper_prefix_hint', test_helper_prefix_yields_hint),
        ('info_circle_marker', test_info_circle_marker_yields_info),
        ('full_pipeline_form_modal', test_full_pipeline_form_modal),
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
