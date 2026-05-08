#!/usr/bin/env python3
"""UI Mock DSL parser TDD test suite — Stage ① of 11.

Validates `_ui_mock_dsl_parse(text) -> AST` from gen_html.py.

AST node schema:
    {
        'type': str,           # primitive name (modal, button, ...)
        'attrs': dict,         # key:value modifiers + bare flags (bool true)
        'value': str|None,     # naked string after keyword, or None
        'children': list,      # nested AST nodes
    }

Top-level is always wrapped as `{'type': 'root', ...}`.

14 primitives:
  page modal navbar sidenav section table
  field button badge input code-block hint
  layers pyramid

Container/utility keywords:
  actions, info, spacer, avatar, tabs, search, card, divider,
  meta-line, row, label, flow-down, layer, logo, item, columns,
  pagination
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

parse = gh._ui_mock_dsl_parse


# ─── Lexer-level tests (via parse output) ────────────────────────────────

def test_empty_input_yields_empty_root():
    ast = parse('')
    assert ast == {'type': 'root', 'attrs': {}, 'value': None, 'children': []}


def test_whitespace_only_yields_empty_root():
    ast = parse('   \n\t  \n')
    assert ast['type'] == 'root'
    assert ast['children'] == []


def test_comment_only_yields_empty_root():
    ast = parse('# just a comment\n# another\n')
    assert ast['children'] == []


# ─── Single primitive (no children) ──────────────────────────────────────

def test_bare_keyword():
    ast = parse('spacer')
    assert len(ast['children']) == 1
    assert ast['children'][0] == {
        'type': 'spacer', 'attrs': {}, 'value': None, 'children': [],
    }


def test_keyword_with_naked_string():
    ast = parse('button "Cancel"')
    node = ast['children'][0]
    assert node['type'] == 'button'
    assert node['value'] == 'Cancel'
    assert node['attrs'] == {}
    assert node['children'] == []


def test_keyword_with_attrs():
    ast = parse('input placeholder:"Search..." maxlength:100')
    node = ast['children'][0]
    assert node['type'] == 'input'
    assert node['attrs'] == {'placeholder': 'Search...', 'maxlength': 100}
    assert node['value'] is None


def test_keyword_with_bare_flag():
    """Bare identifier as attr → bool true."""
    ast = parse('field required')
    node = ast['children'][0]
    assert node['attrs'] == {'required': True}


def test_keyword_with_value_and_attrs():
    ast = parse('button "Submit" variant:primary')
    node = ast['children'][0]
    assert node['type'] == 'button'
    assert node['value'] == 'Submit'
    assert node['attrs'] == {'variant': 'primary'}


# ─── Block (children) ────────────────────────────────────────────────────

def test_empty_block():
    ast = parse('actions { }')
    node = ast['children'][0]
    assert node['type'] == 'actions'
    assert node['children'] == []


def test_block_with_one_child():
    ast = parse('actions { button "OK" }')
    actions = ast['children'][0]
    assert actions['type'] == 'actions'
    assert len(actions['children']) == 1
    btn = actions['children'][0]
    assert btn['type'] == 'button'
    assert btn['value'] == 'OK'


def test_block_with_multiple_children():
    text = '''actions {
        button "Cancel" variant:secondary
        button "Submit" variant:primary
    }'''
    actions = parse(text)['children'][0]
    assert len(actions['children']) == 2
    assert actions['children'][0]['attrs']['variant'] == 'secondary'
    assert actions['children'][1]['attrs']['variant'] == 'primary'


def test_nested_block():
    text = '''modal title:"X" closable {
        field label:"Name" required {
            input placeholder:"..."
            hint "Enter your name"
        }
    }'''
    modal = parse(text)['children'][0]
    assert modal['type'] == 'modal'
    assert modal['attrs'] == {'title': 'X', 'closable': True}
    field = modal['children'][0]
    assert field['type'] == 'field'
    assert field['attrs'] == {'label': 'Name', 'required': True}
    assert len(field['children']) == 2
    assert field['children'][0]['type'] == 'input'
    assert field['children'][1]['type'] == 'hint'
    assert field['children'][1]['value'] == 'Enter your name'


# ─── List values ─────────────────────────────────────────────────────────

def test_list_attr_value():
    ast = parse('tabs ["全部", "僅有效"]')
    node = ast['children'][0]
    # `tabs` takes a naked list as its value (no key:)
    # We model this as: keyword + list → value=list
    assert node['value'] == ['全部', '僅有效']


def test_keyed_list_attr():
    ast = parse('table columns:["A","B","C"]')
    node = ast['children'][0]
    assert node['attrs']['columns'] == ['A', 'B', 'C']


def test_row_with_list():
    ast = parse('row ["x", "y", "z"]')
    node = ast['children'][0]
    assert node['type'] == 'row'
    assert node['value'] == ['x', 'y', 'z']


# ─── Real-world fragment ─────────────────────────────────────────────────

def test_modal_real_world():
    text = '''modal title:"建立 API Token" closable {
        field label:"Token 描述" required {
            input placeholder:"N8N 銷售報表工作流" maxlength:100
            hint "說明此 Token 的用途，方便日後識別"
        }
        info "建議每個 N8N 工作流使用獨立 Token"
        actions {
            button "取消" variant:secondary
            button "建立 Token" variant:primary
        }
    }'''
    modal = parse(text)['children'][0]
    assert modal['type'] == 'modal'
    assert modal['attrs']['title'] == '建立 API Token'
    assert modal['attrs']['closable'] is True
    assert len(modal['children']) == 3
    types = [c['type'] for c in modal['children']]
    assert types == ['field', 'info', 'actions']


def test_table_real_world():
    text = '''table columns:["描述","前綴","狀態"] {
        row ["N8N 銷售", "tk_a3f9...", "Active"]
        row ["庫存監控", "tk_b7c2...", "Active"]
    }'''
    table = parse(text)['children'][0]
    assert table['type'] == 'table'
    assert table['attrs']['columns'] == ['描述', '前綴', '狀態']
    assert len(table['children']) == 2
    assert table['children'][0]['value'] == ['N8N 銷售', 'tk_a3f9...', 'Active']


# ─── Edge cases ──────────────────────────────────────────────────────────

def test_multiple_top_level_blocks():
    text = '''button "A"
    button "B"
    button "C"'''
    children = parse(text)['children']
    assert len(children) == 3
    assert [c['value'] for c in children] == ['A', 'B', 'C']


def test_string_with_escaped_quote():
    ast = parse(r'hint "He said \"hello\""')
    assert ast['children'][0]['value'] == 'He said "hello"'


def test_string_with_colon_inside():
    ast = parse('hint "前綴：tk_a1b2c3d4"')
    assert ast['children'][0]['value'] == '前綴：tk_a1b2c3d4'


def test_kebab_case_keyword():
    ast = parse('code-block language:json { }')
    node = ast['children'][0]
    assert node['type'] == 'code-block'
    assert node['attrs']['language'] == 'json'


def test_meta_line_keyword():
    ast = parse('meta-line "前綴：tk_a1b2"')
    assert ast['children'][0]['type'] == 'meta-line'


def test_flow_down_keyword():
    ast = parse('flow-down "calls (via props)"')
    node = ast['children'][0]
    assert node['type'] == 'flow-down'
    assert node['value'] == 'calls (via props)'


def test_number_attribute():
    ast = parse('pagination total:1243 page:1 of:13')
    node = ast['children'][0]
    assert node['attrs'] == {'total': 1243, 'page': 1, 'of': 13}


def test_comment_in_middle():
    text = '''actions {
        # this is a comment
        button "OK"
        # trailing comment
    }'''
    actions = parse(text)['children'][0]
    assert len(actions['children']) == 1
    assert actions['children'][0]['value'] == 'OK'


# ─── Standalone runner ───────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'UI MOCK DSL PARSER  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('empty', test_empty_input_yields_empty_root),
        ('whitespace_only', test_whitespace_only_yields_empty_root),
        ('comment_only', test_comment_only_yields_empty_root),
        ('bare_keyword', test_bare_keyword),
        ('keyword_with_naked_string', test_keyword_with_naked_string),
        ('keyword_with_attrs', test_keyword_with_attrs),
        ('keyword_with_bare_flag', test_keyword_with_bare_flag),
        ('keyword_with_value_and_attrs', test_keyword_with_value_and_attrs),
        ('empty_block', test_empty_block),
        ('block_with_one_child', test_block_with_one_child),
        ('block_with_multiple_children', test_block_with_multiple_children),
        ('nested_block', test_nested_block),
        ('list_attr_value', test_list_attr_value),
        ('keyed_list_attr', test_keyed_list_attr),
        ('row_with_list', test_row_with_list),
        ('modal_real_world', test_modal_real_world),
        ('table_real_world', test_table_real_world),
        ('multiple_top_level_blocks', test_multiple_top_level_blocks),
        ('string_with_escaped_quote', test_string_with_escaped_quote),
        ('string_with_colon_inside', test_string_with_colon_inside),
        ('kebab_case_keyword', test_kebab_case_keyword),
        ('meta_line_keyword', test_meta_line_keyword),
        ('flow_down_keyword', test_flow_down_keyword),
        ('number_attribute', test_number_attribute),
        ('comment_in_middle', test_comment_in_middle),
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
