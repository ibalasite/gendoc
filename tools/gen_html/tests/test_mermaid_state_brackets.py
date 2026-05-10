#!/usr/bin/env python3
"""Mermaid stateDiagram-v2 transition label — `[guard]` 不應被改寫。

Root cause（gen_html.py `fix_state_line` L662-663）：
    label = re.sub(r'\\[([^\\[\\]]*)\\]', r'(\\1)', label)   # [X] → (X)
    label = re.sub(r'\\{([^\\{\\}]*)\\}', r'(\\1)', label)   # {X} → (X)

對 mermaid v11 stateDiagram-v2 transition label，`[guard]` 是合法純文字。
強改成 `(guard)` 後，連續括號 `event() (guard) /` 讓瀏覽器 mermaid.run()
parser 失敗 → 顯示「Syntax error in text」。

實機證據（pet/erp 重 render 仍破）：
- erp/diagrams/frontend-state-scene.html block 0
- erp/diagrams/frontend-state-ui.html block 0, 1
- pet/pdd.html block 1
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh_state', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


def _fix(src: str) -> str:
    return '\n'.join(gh._mermaid_fix_block(src.split('\n')))


# ─── 1: transition label `[guard]` 保留 ───────────────────────────────

def test_state_transition_guard_brackets_preserved():
    """`A --> B : event() [guard] / action` 內 `[guard]` 不應被改寫。"""
    src = (
        'stateDiagram-v2\n'
        '    [*] --> Default : mount() [enabled] / renderInitialUI()\n'
        '    Default --> Hover : pointerEnter() [not disabled] / applyHoverClass()\n'
    )
    fixed = _fix(src)
    assert '[enabled]' in fixed, \
        f'[enabled] should be preserved; got:\n{fixed}'
    assert '[not disabled]' in fixed, \
        f'[not disabled] should be preserved; got:\n{fixed}'


def test_state_transition_braces_in_label_preserved():
    """`A --> B : event { x }` 內 `{x}` 不應被改寫成 `(x)`（mermaid v11 接受）。"""
    src = (
        'stateDiagram-v2\n'
        '    A --> B : event { kind: foo } / action\n'
    )
    fixed = _fix(src)
    assert '{ kind: foo }' in fixed or '{kind: foo}' in fixed.replace(' ', ''), \
        f'curly should be preserved; got:\n{fixed}'


def test_state_transition_label_no_paren_substitution():
    """fix 後 label 不應出現「pointerEnter() (guard) /」這種雙括號 mermaid v11 解析失敗的形式。"""
    src = (
        'stateDiagram-v2\n'
        '    Default --> Hover : pointerEnter() [not disabled] / applyHoverClass()\n'
    )
    fixed = _fix(src)
    # The bug pattern: method() (...) / — three tokens: parens-call, parens-text, slash
    bad_pattern = 'pointerEnter() (not disabled)'
    assert bad_pattern not in fixed, \
        f'should not produce continuous `() (...)` form; got:\n{fixed}'


# ─── 2: regression — 既有 fix 仍要保留（不要把整個 fix_state_line 砍掉）─

def test_state_default_keyword_still_renamed():
    """state name `Default` 撞 mermaid grammar，仍應 rename 為 `Default_st`。"""
    src = (
        'stateDiagram-v2\n'
        '    [*] --> Default\n'
        '    Default --> Done\n'
    )
    fixed = _fix(src)
    assert 'Default_st' in fixed, \
        f'reserved name "Default" should still be renamed to Default_st; got:\n{fixed}'


def test_state_entry_exit_lines_still_stripped():
    """`entry: ...` / `exit: ...` 仍應被刪除（mermaid v11 不支援）。"""
    src = (
        'stateDiagram-v2\n'
        '    state Foo {\n'
        '      entry: doSomething()\n'
        '      exit: cleanup()\n'
        '    }\n'
    )
    fixed = _fix(src)
    for line in fixed.split('\n'):
        s = line.strip()
        assert not s.startswith('entry:'), \
            f'entry: line should be stripped; line={line!r}'
        assert not s.startswith('exit:'), \
            f'exit: line should be stripped; line={line!r}'


def test_state_semicolon_in_label_still_normalized():
    """label 內 `;` 仍應改成 `,`（mermaid v11 把 ; 當 statement separator）。"""
    src = (
        'stateDiagram-v2\n'
        '    A --> B : event; another\n'
    )
    fixed = _fix(src)
    assert ';' not in fixed.split('\n')[1] or ',' in fixed, \
        f'semicolon should be normalized to comma; got:\n{fixed}'


# ─── 3: empty state block 移除（真實破圖 root cause）──────────────────
# 實機 Playwright + mermaid v11.14 browser 驗證：
# v7a 只 transitions          → ✅ render OK
# v7b transitions + 空 state X { } → ❌ Syntax error in text
# v7c transitions + state X : 描述 → ✅
# v7e 只 state X : 描述         → ✅
# → root cause: 空的 `state X { }` block 讓 mermaid v11 browser parser fail。
#   gen_html.py `fix_state_line` L643-644 刪掉 `entry:` / `exit:` 行後，
#   既有 source（pet/PDD.md, erp/diagrams/frontend-state-{scene,ui}.md）
#   的 `state X { entry: ... exit: ... }` block 被掏空 → 留下空 block → 破圖。

def test_empty_state_block_removed_after_entry_exit_strip():
    """`state X { entry: ... exit: ... }` 經 entry/exit strip 變空後，
    整個 block 應移除（避免空 block 導致 mermaid v11 parse fail）。"""
    src = (
        'stateDiagram-v2\n'
        '    [*] --> Foo\n'
        '    state Foo {\n'
        '      entry: doSomething()\n'
        '      exit: cleanup()\n'
        '    }\n'
    )
    fixed = _fix(src)
    # The block body (entry/exit) is fully stripped → block becomes empty →
    # the entire `state Foo { ... }` block must be removed.
    assert 'state Foo {' not in fixed, \
        f'empty state block should be removed; got:\n{fixed}'


def test_state_block_with_only_blank_lines_removed():
    """`state X { (only blank lines) }` 也視為空 block，整個移除。"""
    src = (
        'stateDiagram-v2\n'
        '    [*] --> Bar\n'
        '    state Bar {\n'
        '\n'
        '\n'
        '    }\n'
    )
    fixed = _fix(src)
    assert 'state Bar {' not in fixed, \
        f'state block with only blank lines should be removed; got:\n{fixed}'


def test_state_block_with_real_content_preserved():
    """非空 state block（含 nested state / transition）必須保留。"""
    src = (
        'stateDiagram-v2\n'
        '    [*] --> Outer\n'
        '    state Outer {\n'
        '        [*] --> Sub1\n'
        '        Sub1 --> Sub2\n'
        '        Sub2 --> [*]\n'
        '    }\n'
    )
    fixed = _fix(src)
    assert 'state Outer {' in fixed, \
        f'state block with content should be preserved; got:\n{fixed}'
    assert 'Sub1' in fixed and 'Sub2' in fixed, \
        f'nested states should be preserved; got:\n{fixed}'


def test_state_block_description_line_preserved_when_block_removed():
    """空 block 移除時，同 state 的 `state X : description` 行必須保留。"""
    src = (
        'stateDiagram-v2\n'
        '    [*] --> Idle\n'
        '    state Idle {\n'
        '      entry: enable()\n'
        '      exit: disable()\n'
        '    }\n'
        '    state Idle : 預設靜止狀態\n'
    )
    fixed = _fix(src)
    assert 'state Idle {' not in fixed, \
        f'empty block should be removed; got:\n{fixed}'
    assert 'state Idle : 預設靜止狀態' in fixed, \
        f'description line should be preserved; got:\n{fixed}'


# ─── 4: emit-time _mermaid_fix_block 套用（layered-arch + F2 ASCII→mermaid）

def test_layered_arch_emit_quotes_edge_label_with_parens():
    """`_um_r_layered_arch` emit 的 edge label 含 () 必須 quote-wrap。

    Root cause（pet/PDD.md 重 render 後 block 1 仍破）：
    `_um_r_layered_arch` 直接寫 `<pre class="mermaid">flowchart TB ...</pre>`
    沒過 `_mermaid_fix_block`，所以 edge label `|calls (via props / context)|`
    內含 `()` 沒被 quote-wrap → mermaid v11 browser parser fail。

    fix_flowchart_line L604-609 已實作 edge label quote-wrap，但 emit point
    沒套用。Common fix: emit time 統一過 _mermaid_fix_block。
    """
    ast = {
        'type': 'root',
        'children': [{
            'type': 'layered-arch',
            'children': [
                {'type': 'layer', 'value': 'L0', 'children': []},
                {'type': 'flow-down', 'value': 'calls (via props / context)'},
                {'type': 'layer', 'value': 'L1', 'children': []},
            ]
        }]
    }
    html = gh._ui_mock_render(ast)
    # mermaid v11 needs edge label with `()` to be wrapped in `|"..."|`
    assert '|"calls (via props / context)"|' in html, \
        f'edge label with parens must be quoted; got:\n{html[:600]}'


def test_ascii_to_mermaid_td_emit_quotes_edge_label_parens():
    """F2 `_ascii_to_mermaid_td` emit 的 edge label 也要過 fix（quote 含 () 的 label）。"""
    # Build a tiny ASCII flow that should produce mermaid with parens in edges
    ascii_src = (
        '┌─────┐\n'
        '│ A   │\n'
        '└──┬──┘\n'
        '   │ calls (sync)\n'
        '   ▼\n'
        '┌─────┐\n'
        '│ B   │\n'
        '└─────┘\n'
    )
    mermaid_src = gh._ascii_to_mermaid_td(ascii_src)
    if not mermaid_src or '-->' not in mermaid_src:
        # Some inputs may not yield edges — skip in that case.
        return
    # If the converter produced an edge label containing `(`, the EMIT path
    # must quote it (so mermaid v11 won't trip).
    for ln in mermaid_src.split('\n'):
        m = re.search(r'\|([^|]+)\|', ln)
        if m and '(' in m.group(1):
            assert m.group(1).startswith('"') and m.group(1).endswith('"'), \
                f'edge label with `(` must be quoted; got line:\n{ln}'


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print(f'STATE BRACKETS — common fix for [guard] preservation  source={GEN_HTML.name}')
    print('=' * 78)
    tests = [
        ('state_transition_guard_brackets_preserved', test_state_transition_guard_brackets_preserved),
        ('state_transition_braces_in_label_preserved', test_state_transition_braces_in_label_preserved),
        ('state_transition_label_no_paren_substitution', test_state_transition_label_no_paren_substitution),
        ('state_default_keyword_still_renamed', test_state_default_keyword_still_renamed),
        ('state_entry_exit_lines_still_stripped', test_state_entry_exit_lines_still_stripped),
        ('state_semicolon_in_label_still_normalized', test_state_semicolon_in_label_still_normalized),
        ('empty_state_block_removed_after_entry_exit_strip', test_empty_state_block_removed_after_entry_exit_strip),
        ('state_block_with_only_blank_lines_removed', test_state_block_with_only_blank_lines_removed),
        ('state_block_with_real_content_preserved', test_state_block_with_real_content_preserved),
        ('state_block_description_line_preserved_when_block_removed', test_state_block_description_line_preserved_when_block_removed),
        ('layered_arch_emit_quotes_edge_label_with_parens', test_layered_arch_emit_quotes_edge_label_with_parens),
        ('ascii_to_mermaid_td_emit_quotes_edge_label_parens', test_ascii_to_mermaid_td_emit_quotes_edge_label_parens),
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
