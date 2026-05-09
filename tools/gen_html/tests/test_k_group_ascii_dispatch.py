#!/usr/bin/env python3
"""K 群 — workflow / 目錄樹 ASCII dispatch + lightbox wrapper TDD tests.

問題：
  K1: F2 emit `<pre class="mermaid">` 沒包 `.diagram-container`，lightbox 不 fire
  K2~K8: 後續 step

K1: F2 emit 加 wrapper
  - 預期：F2 轉換的 mermaid 一律包 `<div class="diagram-container">`
  - 不影響：原生 mermaid path（已有 wrapper）保持不變
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


# ─── K1: F2 emit 包 .diagram-container wrapper ────────────────────────

# 會被 F1 判為 'system' 的 ASCII：含 ▼ 觸發系統訊號 + 有 ┌─┐ 觸發 dispatch 入口
# (gen_html.py L2555-2556 要求 raw_block 至少有一個 box-drawing char 才進 F1+F2)
SYSTEM_FLOW_WITH_BOX = """\
Developer workstation
        │
        ▼
┌──────────────────┐
│ GitHub PR        │
│ ci.yml ─ install │
└──────────────────┘
        │
        ▼
Merge to develop
"""


def test_K1_f2_emit_wraps_in_diagram_container():
    """F2 (ASCII→mermaid) 的 dispatch 輸出必須包 `<div class="diagram-container">`。

    Setup: 餵一段會被 F1 判為 'system' 的 ASCII，跑 md_to_html。
    Assert: 輸出含 `<div class="diagram-container"><pre class="mermaid">...`
    """
    md = f'# T\n\n```\n{SYSTEM_FLOW_WITH_BOX}\n```\n'
    html = gh.md_to_html(md)
    # 先確認真的觸發 F2（否則無法測 wrapper）
    assert '<pre class="mermaid">' in html, \
        f'F2 should fire on system ASCII; html (first 600 chars):\n{html[:600]}'
    # 核心 assert：mermaid pre 必須被 diagram-container 包住
    pattern = r'<div class="diagram-container">\s*<pre class="mermaid">'
    assert re.search(pattern, html), \
        f'F2 emit must wrap `<pre class="mermaid">` in `<div class="diagram-container">`; html (first 600):\n{html[:600]}'


def test_K1_f2_emit_closes_wrapper_after_pre():
    """`<div class="diagram-container">` 必須在 `</pre>` 後關閉 `</div>`。"""
    md = f'# T\n\n```\n{SYSTEM_FLOW_WITH_BOX}\n```\n'
    html = gh.md_to_html(md)
    # 抽取 wrapper 區段並驗證有對應的 </div>
    match = re.search(
        r'<div class="diagram-container">\s*<pre class="mermaid">.*?</pre>\s*</div>',
        html,
        re.DOTALL,
    )
    assert match, \
        f'wrapper close </div> missing after </pre>; html:\n{html[:800]}'


def test_K1_native_mermaid_path_unchanged():
    """原生 ` ```mermaid ` fenced block 的 wrapper 路徑保持不變（regression）。

    既有 native mermaid path 已包 wrapper（gen_html.py L2519）；K1 改動
    F2 path 不應動到此 path。
    """
    native_md = '# T\n\n```mermaid\ngraph TD\n  A --> B\n```\n'
    html = gh.md_to_html(native_md)
    # native path 也應該包 wrapper
    pattern = r'<div class="diagram-container">\s*<pre class="mermaid">'
    assert re.search(pattern, html), \
        f'native mermaid path must also wrap; html:\n{html[:600]}'
    # 確認只有一個 wrapper（沒重複包）
    wrapper_count = len(re.findall(r'<div class="diagram-container">', html))
    pre_count = len(re.findall(r'<pre class="mermaid">', html))
    assert wrapper_count == pre_count, \
        f'wrapper count {wrapper_count} ≠ pre count {pre_count} (over-wrap?); html:\n{html[:800]}'


def test_K1_no_wrapper_for_failed_f2_or_unknown():
    """F1='unknown' (沒被判 system 也沒 ui) → fall through 到普通 <pre><code>，不該有 wrapper。"""
    plain_md = '# T\n\n```\nplain text no signals\nno arrows or boxes\n```\n'
    html = gh.md_to_html(plain_md)
    # 'unknown' 走 fall-through emit `<pre><code>`，沒 mermaid class
    assert '<pre class="mermaid">' not in html, \
        f'unknown ASCII should NOT become mermaid; html:\n{html[:600]}'


# ─── Standalone runner ──────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'K GROUP TESTS  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('K1_f2_emit_wraps_in_diagram_container', test_K1_f2_emit_wraps_in_diagram_container),
        ('K1_f2_emit_closes_wrapper_after_pre', test_K1_f2_emit_closes_wrapper_after_pre),
        ('K1_native_mermaid_path_unchanged', test_K1_native_mermaid_path_unchanged),
        ('K1_no_wrapper_for_failed_f2_or_unknown', test_K1_no_wrapper_for_failed_f2_or_unknown),
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
