#!/usr/bin/env python3
"""UI Mock DSL renderer TDD test suite — Stage ② of 11.

Validates `_ui_mock_render(ast) -> str` from gen_html.py.

Test strategy:
- DSL → parse → AST → render → HTML.
- Assert required substrings/classes in output (not exact HTML — tolerant
  to whitespace and attribute order).
- Cover 12 basic primitives + container/utility keywords.

Edge cases (layered-arch / test-pyramid) covered separately in stages 3 & 4.
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


# ─── 12 basic primitives ─────────────────────────────────────────────────

def test_page_renders_outer_div():
    html = render_dsl('page { }')
    assert 'umock__page' in html


def test_page_with_title():
    html = render_dsl('page title:"Dashboard" { }')
    assert 'Dashboard' in html
    assert 'umock__page' in html


def test_modal_renders_titlebar():
    html = render_dsl('modal title:"Edit Token" { }')
    assert 'umock__modal' in html
    assert 'Edit Token' in html


def test_modal_closable_renders_close_button():
    html = render_dsl('modal title:"X" closable { }')
    assert 'umock__modal-close' in html or 'modal__close' in html


def test_navbar_renders():
    html = render_dsl('navbar { logo "ACME" }')
    assert 'umock__navbar' in html
    assert 'ACME' in html


def test_sidenav_renders():
    html = render_dsl('sidenav { item "Home" item "Settings" }')
    assert 'umock__sidenav' in html
    assert 'Home' in html
    assert 'Settings' in html


def test_section_renders_with_title():
    html = render_dsl('section title:"Users" { }')
    assert 'umock__section' in html
    assert 'Users' in html


def test_table_renders_thead_tbody():
    text = '''table columns:["Name", "Email"] {
        row ["Alice", "a@b.com"]
        row ["Bob", "b@c.com"]
    }'''
    html = render_dsl(text)
    assert '<table' in html
    assert '<thead' in html
    assert '<tbody' in html
    assert 'Name' in html and 'Email' in html
    assert 'Alice' in html and 'a@b.com' in html
    assert 'Bob' in html and 'b@c.com' in html


def test_field_renders_label_required():
    html = render_dsl('field label:"Name" required { input placeholder:"..." }')
    assert 'umock__field' in html
    assert 'Name' in html
    # required marker
    assert '*' in html or 'required' in html.lower()


def test_button_primary():
    html = render_dsl('button "Submit" variant:primary')
    assert 'umock__btn' in html
    assert 'primary' in html
    assert 'Submit' in html


def test_button_secondary_default():
    html = render_dsl('button "Cancel"')
    assert 'umock__btn' in html
    assert 'Cancel' in html


def test_button_danger():
    html = render_dsl('button "Delete" variant:danger')
    assert 'danger' in html


def test_badge_with_status():
    html = render_dsl('badge "Active" status:active')
    assert 'umock__badge' in html
    assert 'Active' in html
    assert 'active' in html


def test_input_with_placeholder():
    html = render_dsl('input placeholder:"Search..." maxlength:50')
    assert '<input' in html
    assert 'Search...' in html
    assert '50' in html


def test_code_block_renders_pre():
    html = render_dsl('code-block language:json { }')
    assert '<pre' in html
    assert '<code' in html


def test_hint_renders():
    html = render_dsl('hint "Helpful tip"')
    assert 'umock__hint' in html
    assert 'Helpful tip' in html


# ─── Container/utility primitives ────────────────────────────────────────

def test_actions_container():
    html = render_dsl('actions { button "OK" button "Cancel" }')
    assert 'umock__actions' in html
    assert 'OK' in html and 'Cancel' in html


def test_info_renders():
    html = render_dsl('info "Important note"')
    assert 'umock__info' in html
    assert 'Important note' in html


def test_card_renders():
    html = render_dsl('card { row { label "Header" } }')
    assert 'umock__card' in html
    assert 'Header' in html


def test_divider_renders():
    html = render_dsl('divider')
    # divider is typically <hr> or <div class="...divider">
    assert 'divider' in html.lower()


def test_meta_line_renders():
    html = render_dsl('meta-line "Created: 2026-04-01"')
    assert 'Created: 2026-04-01' in html


def test_pagination_renders():
    html = render_dsl('pagination total:1243 page:1 of:13')
    assert '1243' in html or '1,243' in html
    assert '13' in html


def test_tabs_renders():
    html = render_dsl('tabs ["All", "Active", "Revoked"]')
    assert 'All' in html and 'Active' in html and 'Revoked' in html


# ─── Composition (real-world fragments) ──────────────────────────────────

def test_modal_full_composition():
    text = '''modal title:"建立 Token" closable {
        field label:"描述" required {
            input placeholder:"N8N 工作流" maxlength:100
            hint "說明此 Token 的用途"
        }
        info "建議每個工作流獨立 Token"
        actions {
            button "取消" variant:secondary
            button "建立" variant:primary
        }
    }'''
    html = render_dsl(text)
    # All key text present
    for s in ['建立 Token', '描述', 'N8N 工作流', '說明此 Token', '建議每個', '取消', '建立']:
        assert s in html, f'missing {s!r}'
    # Structural classes
    for cls in ['umock__modal', 'umock__field', 'umock__info', 'umock__actions', 'umock__btn']:
        assert cls in html, f'missing class {cls}'
    # No raw DSL leakage
    assert 'closable' not in html or 'umock__modal-close' in html
    assert '{' not in html.split('<style')[0] if '<style' in html else True


def test_page_with_navbar_and_table():
    text = '''page {
        navbar { logo "ERP" }
        section title:"Tokens" {
            table columns:["Description", "Status"] {
                row ["N8N Sales", "Active"]
                row ["Inventory", "Revoked"]
            }
        }
    }'''
    html = render_dsl(text)
    for s in ['ERP', 'Tokens', 'Description', 'Status', 'N8N Sales', 'Active', 'Inventory', 'Revoked']:
        assert s in html, f'missing {s!r}'


# ─── HTML escaping (security) ────────────────────────────────────────────

def test_value_html_is_escaped():
    html = render_dsl('hint "<script>alert(1)</script>"')
    assert '<script>' not in html
    assert '&lt;script&gt;' in html


def test_attr_html_is_escaped():
    html = render_dsl('button "OK" variant:"<bad>"')
    # variant value should not produce raw <bad> tag
    assert '<bad>' not in html


def test_table_cells_escaped():
    html = render_dsl('table columns:["X"] { row ["<b>raw</b>"] }')
    assert '<b>raw</b>' not in html
    assert '&lt;b&gt;' in html


# ─── Unknown type fallback ───────────────────────────────────────────────

def test_unknown_type_renders_silently():
    """Unknown primitive should render something (not crash) without warning text."""
    html = render_dsl('foo-bar "value"')
    # Per user spec: silent fallback, no warning text in HTML
    assert 'value' in html
    # Should not contain alarming words like "ERROR", "UNKNOWN", "WARNING"
    for word in ['ERROR', 'UNKNOWN', 'WARNING', 'unsupported']:
        assert word not in html


# ─── Standalone runner ───────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'UI MOCK DSL RENDERER  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('page_renders_outer_div', test_page_renders_outer_div),
        ('page_with_title', test_page_with_title),
        ('modal_renders_titlebar', test_modal_renders_titlebar),
        ('modal_closable', test_modal_closable_renders_close_button),
        ('navbar_renders', test_navbar_renders),
        ('sidenav_renders', test_sidenav_renders),
        ('section_with_title', test_section_renders_with_title),
        ('table_thead_tbody', test_table_renders_thead_tbody),
        ('field_label_required', test_field_renders_label_required),
        ('button_primary', test_button_primary),
        ('button_secondary_default', test_button_secondary_default),
        ('button_danger', test_button_danger),
        ('badge_with_status', test_badge_with_status),
        ('input_with_placeholder', test_input_with_placeholder),
        ('code_block_pre', test_code_block_renders_pre),
        ('hint_renders', test_hint_renders),
        ('actions_container', test_actions_container),
        ('info_renders', test_info_renders),
        ('card_renders', test_card_renders),
        ('divider_renders', test_divider_renders),
        ('meta_line_renders', test_meta_line_renders),
        ('pagination_renders', test_pagination_renders),
        ('tabs_renders', test_tabs_renders),
        ('modal_full_composition', test_modal_full_composition),
        ('page_with_navbar_and_table', test_page_with_navbar_and_table),
        ('value_html_escaped', test_value_html_is_escaped),
        ('attr_html_escaped', test_attr_html_is_escaped),
        ('table_cells_escaped', test_table_cells_escaped),
        ('unknown_type_silent', test_unknown_type_renders_silently),
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
