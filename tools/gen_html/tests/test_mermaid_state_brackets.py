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
