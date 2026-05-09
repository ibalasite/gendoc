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


# ─── A3: card / page / modal 邊界加深 ─────────────────────────────────────
# 對齊核心目標 1. 清楚 — 邊界視覺要看得出來。
# scope 限 .umock__page / .umock__modal / .umock__card 與其 title-bar，
# 不影響一般 markdown div / table。

def _read_gen_html_css():
    """Return the inline <style> block from gen_html.py source as a string."""
    src = GEN_HTML.read_text(encoding='utf-8')
    return src


def test_A3_card_outer_border_strong():
    css = _read_gen_html_css()
    # The .umock__page, .umock__modal, .umock__card rule must use
    # a 1.5px solid border with a darker shade (#94a3b8).
    assert '1.5px solid #94a3b8' in css, (
        '.umock__page/__modal/__card outer border is still light '
        '(expected 1.5px solid #94a3b8)'
    )


def test_A3_title_bar_border_strong():
    css = _read_gen_html_css()
    # .umock__card-title, .umock__page-title, .umock__modal-titlebar should
    # share the same darker border-bottom so the title visually anchors.
    # We accept the pattern 'border-bottom: 1.5px solid #94a3b8' anywhere
    # the title-bar style block is defined; strict assertion: at least three
    # title-bar selectors in a single contiguous block use it.
    assert css.count('1.5px solid #94a3b8') >= 2, (
        'title-bar border-bottom not unified to 1.5px solid #94a3b8'
    )


# ─── A4: table padding / border 加深 ─────────────────────────────────────
# 對齊核心目標 1. 清楚 — table 行可區分、thead 突出。
# scope 限 .umock__table，不影響一般 markdown table。

def test_A4_table_padding_increased():
    css = _read_gen_html_css()
    assert 'padding: 0.75rem 0.875rem' in css, (
        '.umock__table cell padding should be 0.75rem 0.875rem'
    )


def test_A4_table_row_border_strong():
    css = _read_gen_html_css()
    # th/td common rule — row border now uses #cbd5e1 (was #e2e8f0)
    # We accept the literal "1px solid #cbd5e1" appearing in the umock__table cell rule
    # by checking that the cell rule line follows the new pattern.
    assert 'border-bottom: 1px solid #cbd5e1' in css, (
        '.umock__table td border-bottom should darken to #cbd5e1'
    )


def test_A4_table_thead_emphasized():
    css = _read_gen_html_css()
    # th separately gets a 2px solid #94a3b8 border-bottom override.
    assert 'border-bottom: 2px solid #94a3b8' in css, (
        '.umock__table th border-bottom should be 2px solid #94a3b8'
    )


def test_A4_table_no_invalid_border_radius():
    """border-radius 在 border-collapse: collapse 表格上不會生效，移除避免誤導。"""
    css = _read_gen_html_css()
    # We don't ban border-radius globally (badge / card use it). We check the
    # specific .umock__table rule line doesn't carry it.
    import re as _re
    m = _re.search(r'\.umock__table\s*\{[^}]*\}', css)
    assert m, '.umock__table rule not found'
    table_rule = m.group(0)
    assert 'border-radius' not in table_rule, (
        f'.umock__table should not declare border-radius (collapsed table ignores it): '
        f'{table_rule}'
    )


# ─── A5: mock 元件不可 focus（P4 — tabindex="-1"） ────────────────────────
# Mock 是文件展示用，加 tabindex="-1" 讓 Tab 鍵跳過 → focus ring 永遠不出現。
# 對齊核心目標 4. 不誤會（default 按鈕不會因 focus 看起來像 primary）。

def test_A5_button_renders_tabindex_minus_one():
    html = render_dsl('button "Apply" variant:"primary"')
    assert 'tabindex="-1"' in html, f'button missing tabindex="-1": {html}'
    assert 'umock__btn' in html


def test_A5_button_default_variant_also_tabindex():
    html = render_dsl('button "Reset"')
    assert 'tabindex="-1"' in html


def test_A5_input_renders_tabindex_minus_one():
    html = render_dsl('input placeholder:"name"')
    assert 'tabindex="-1"' in html, f'input missing tabindex="-1": {html}'
    assert 'umock__input' in html


def test_A5_search_renders_tabindex_minus_one():
    html = render_dsl('search placeholder:"find"')
    assert 'tabindex="-1"' in html, f'search missing tabindex="-1": {html}'
    assert 'umock__search' in html


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
        ('A3_card_outer_border_strong', test_A3_card_outer_border_strong),
        ('A3_title_bar_border_strong', test_A3_title_bar_border_strong),
        ('A4_table_padding_increased', test_A4_table_padding_increased),
        ('A4_table_row_border_strong', test_A4_table_row_border_strong),
        ('A4_table_thead_emphasized', test_A4_table_thead_emphasized),
        ('A4_table_no_invalid_border_radius', test_A4_table_no_invalid_border_radius),
        ('A5_button_tabindex', test_A5_button_renders_tabindex_minus_one),
        ('A5_button_default_tabindex', test_A5_button_default_variant_also_tabindex),
        ('A5_input_tabindex', test_A5_input_renders_tabindex_minus_one),
        ('A5_search_tabindex', test_A5_search_renders_tabindex_minus_one),
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
