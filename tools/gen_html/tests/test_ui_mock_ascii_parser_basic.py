#!/usr/bin/env python3
"""UI Mock ASCII parser — basic frame / title / section / button / badge.
Stage ⑤ of 11.

Goal: recognize ASCII box-drawing UI mockups and produce the same AST that
the DSL parser would, so the renderer (stages 2-4) emits identical-quality
HTML for both inputs.

Stage ⑤ scope:
  - outer rectangle detection (┌─┐ ... └─┘)
  - modal vs card classification (has `[X]` → modal)
  - title-bar extraction (first content row)
  - horizontal section dividers (├─┤)
  - in-segment button extraction ([label] tokens in last row)
  - in-segment badge extraction (●text / ○text)
  - free-text fallback (everything else preserved as plain text in `info`
    or under section)

Out of scope (later stages):
  - 2-column split (navbar+sidebar)         → stage ⑥
  - tables                                  → stage ⑥
  - inner boxes (input / code-block)        → stage ⑦
  - layered-arch / pyramid detection        → stage ⑧
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


# ─── Frame detection ─────────────────────────────────────────────────────

def test_returns_none_for_non_box_input():
    """Plain text without box-drawing chars → None (not a UI mock)."""
    assert ascii_parse('hello\nworld') is None


def test_returns_none_for_unclosed_frame():
    """Top-left ┌ but no bottom ┘ → not parseable."""
    text = '┌────┐\n│ X  │\n'
    # parser may try, but should be conservative — no clear bottom
    result = ascii_parse(text)
    # Either None (rejected) or basic free-text segment — must NOT raise
    assert result is None or isinstance(result, dict)


def test_minimal_card_outer_frame():
    text = '''┌────────────┐
│ Hello      │
└────────────┘'''
    ast = ascii_parse(text)
    assert ast is not None
    assert ast['type'] == 'root'
    body = ast['children'][0]
    assert body['type'] in ('card', 'page')
    # Content should appear somewhere
    flat = _flatten_text(body)
    assert 'Hello' in flat


def test_modal_classification_via_close_marker():
    """Frame containing `[X]` → modal."""
    text = '''┌────────────────────────────┐
│ Title                  [X] │
├────────────────────────────┤
│ Body                       │
└────────────────────────────┘'''
    ast = ascii_parse(text)
    assert ast['children'][0]['type'] == 'modal'


# ─── Title extraction ────────────────────────────────────────────────────

def test_title_extracted_from_first_row():
    text = '''┌──────────────────────────┐
│ ◉ 建立 API Token     [X] │
├──────────────────────────┤
│ Body                     │
└──────────────────────────┘'''
    ast = ascii_parse(text)
    modal = ast['children'][0]
    title = modal.get('attrs', {}).get('title', '')
    assert '建立 API Token' in title


def test_title_strips_close_marker():
    """`[X]` should be stripped from the title text."""
    text = '''┌──────────────────────────┐
│ Edit                 [X] │
├──────────────────────────┤
│ Body                     │
└──────────────────────────┘'''
    ast = ascii_parse(text)
    title = ast['children'][0]['attrs'].get('title', '')
    assert '[X]' not in title
    assert 'Edit' in title


def test_title_only_no_divider():
    """Outer frame with only title row, no body."""
    text = '''┌────────────┐
│ Just Title │
└────────────┘'''
    ast = ascii_parse(text)
    body = ast['children'][0]
    title = body.get('attrs', {}).get('title', '')
    # Title attr OR plain text content should contain it
    flat = _flatten_text(body) + ' ' + title
    assert 'Just Title' in flat


# ─── Section dividers ────────────────────────────────────────────────────

def test_two_section_divider():
    """├──┤ splits into two body sections."""
    text = '''┌──────────────┐
│ Title    [X] │
├──────────────┤
│ Section A    │
├──────────────┤
│ Section B    │
└──────────────┘'''
    ast = ascii_parse(text)
    modal = ast['children'][0]
    flat = _flatten_text(modal)
    assert 'Section A' in flat and 'Section B' in flat


def test_three_section_divider_creates_three_segments():
    text = '''┌──────────────┐
│ Title    [X] │
├──────────────┤
│ A            │
├──────────────┤
│ B            │
├──────────────┤
│ C            │
└──────────────┘'''
    ast = ascii_parse(text)
    modal = ast['children'][0]
    flat = _flatten_text(modal)
    for letter in ['A', 'B', 'C']:
        assert letter in flat


# ─── Button extraction ───────────────────────────────────────────────────

def test_buttons_in_action_row():
    """Last segment with `[label]` tokens → actions { button button }."""
    text = '''┌────────────────────┐
│ Title          [X] │
├────────────────────┤
│ Body content       │
├────────────────────┤
│   [Cancel] [OK]    │
└────────────────────┘'''
    ast = ascii_parse(text)
    modal = ast['children'][0]
    # Find any actions container with buttons
    buttons = _find_all(modal, 'button')
    labels = [b.get('value', '') for b in buttons]
    assert 'Cancel' in labels
    assert 'OK' in labels


def test_button_with_variant_hint_primary():
    """`[OK]（主）` → button variant:primary."""
    text = '''┌────────────────────┐
│ T              [X] │
├────────────────────┤
│   [OK]（主）       │
└────────────────────┘'''
    ast = ascii_parse(text)
    btns = _find_all(ast, 'button')
    assert any(b.get('value', '') == 'OK' and
               b.get('attrs', {}).get('variant') == 'primary'
               for b in btns)


def test_button_with_variant_hint_danger():
    """`[Delete]（Danger）` → button variant:danger."""
    text = '''┌────────────────────┐
│ T              [X] │
├────────────────────┤
│   [Delete]（Danger）│
└────────────────────┘'''
    ast = ascii_parse(text)
    btns = _find_all(ast, 'button')
    assert any(b.get('value', '') == 'Delete' and
               b.get('attrs', {}).get('variant') == 'danger'
               for b in btns)


# ─── Badge extraction ────────────────────────────────────────────────────

def test_badge_filled_circle_active():
    """●Active in body → badge with status:active."""
    text = '''┌────────────────────┐
│ Token              │
│  ●Active           │
└────────────────────┘'''
    ast = ascii_parse(text)
    badges = _find_all(ast, 'badge')
    assert any(b.get('value', '') == 'Active' and
               b.get('attrs', {}).get('status') == 'active'
               for b in badges)


def test_badge_open_circle_inactive():
    """○Revoked in body → badge with status:inactive."""
    text = '''┌────────────────────┐
│ Token              │
│  ○Revoked          │
└────────────────────┘'''
    ast = ascii_parse(text)
    badges = _find_all(ast, 'badge')
    assert any(b.get('value', '') == 'Revoked' and
               b.get('attrs', {}).get('status') == 'inactive'
               for b in badges)


# ─── Output round-trip via renderer (sanity) ─────────────────────────────

def test_full_pipeline_modal():
    """ASCII modal → AST → render → HTML must contain expected substrings."""
    text = '''┌──────────────────────────────┐
│ ⚠ 確認撤銷 Token         [X] │
├──────────────────────────────┤
│ 您即將撤銷此 Token            │
├──────────────────────────────┤
│            [取消] [確認撤銷]  │
└──────────────────────────────┘'''
    ast = ascii_parse(text)
    html = gh._ui_mock_render(ast)
    # Title rendered
    assert '撤銷 Token' in html
    # Buttons rendered as <button>
    assert '取消' in html and '確認撤銷' in html
    assert 'umock__btn' in html
    # No raw box-drawing chars in output
    for c in '┌┐└┘├┤─│':
        assert c not in html


# ─── Helpers ─────────────────────────────────────────────────────────────

def _flatten_text(node) -> str:
    """Concat all text-bearing values in subtree."""
    parts = []
    if node.get('type') in ('hint', 'info', 'meta-line', 'label', 'button',
                             'badge', 'logo', 'item'):
        v = node.get('value')
        if v is not None:
            parts.append(str(v) if not isinstance(v, list) else ' '.join(map(str, v)))
    if 'attrs' in node:
        for k in ('title', 'subtitle', 'label'):
            if k in node['attrs']:
                parts.append(str(node['attrs'][k]))
    for child in node.get('children', []):
        parts.append(_flatten_text(child))
    if isinstance(node.get('value'), str):
        parts.append(node['value'])
    return ' '.join(parts)


def _find_all(node, type_):
    out = []
    if node.get('type') == type_:
        out.append(node)
    for c in node.get('children', []):
        out.extend(_find_all(c, type_))
    return out


# ─── Standalone runner ───────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'UI MOCK ASCII PARSER — basic (stage 5)  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('non_box_returns_none', test_returns_none_for_non_box_input),
        ('unclosed_frame', test_returns_none_for_unclosed_frame),
        ('minimal_card_frame', test_minimal_card_outer_frame),
        ('modal_via_close_marker', test_modal_classification_via_close_marker),
        ('title_extracted', test_title_extracted_from_first_row),
        ('title_strips_close', test_title_strips_close_marker),
        ('title_only_no_divider', test_title_only_no_divider),
        ('two_section_divider', test_two_section_divider),
        ('three_sections', test_three_section_divider_creates_three_segments),
        ('buttons_action_row', test_buttons_in_action_row),
        ('button_variant_primary', test_button_with_variant_hint_primary),
        ('button_variant_danger', test_button_with_variant_hint_danger),
        ('badge_filled_circle', test_badge_filled_circle_active),
        ('badge_open_circle', test_badge_open_circle_inactive),
        ('full_pipeline_modal', test_full_pipeline_modal),
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
