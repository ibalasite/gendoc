#!/usr/bin/env python3
"""M 群 — prototype HTML 必含回 docs 首頁 link

Commit 1 (M2/M3/M4/M7): grep `skills/gendoc-gen-prototype/SKILL.md`
驗證 4 個位置的模板修對：
- M2: Step G-7 prototype shell 模板 含 `<a href="../index.html" ...>← 文件站</a>`
- M3: Step A-4 admin 5 頁模板 含 `<a href="../../index.html" ...>← 文件站</a>`
- M4: Step G-2 api-explorer 模板 修對 label/href + 含 `<a href="../../index.html" ...>← 文件站</a>`
- M7: review subagent checklist 含 docs link 檢查項

Commit 2 (M8): 在 test_path_rewriter / test_lightbox 加 docs sidebar
prototype link 帶 named target test。
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
SKILL_MD = REPO / 'skills' / 'gendoc-gen-prototype' / 'SKILL.md'


def _read_skill_md() -> str:
    assert SKILL_MD.is_file(), f'SKILL.md not found: {SKILL_MD}'
    return SKILL_MD.read_text(encoding='utf-8')


# ─── M8 helpers — load gen_html.py ─────────────────────────────────────

import importlib.util
import tempfile

GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'
_spec = importlib.util.spec_from_file_location('gh_m8', GEN_HTML)
gh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gh)


def _make_pages_dir(layout):
    tmp = pathlib.Path(tempfile.mkdtemp())
    for rel, content in layout.items():
        target = tmp / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if isinstance(content, str) else '')
    return tmp


# ─── M2: prototype shell template (Step G-7) has docs link ─────────────

def _section_between(text: str, start_marker: str, end_marker_re: str) -> str:
    """Extract text between a start marker (literal, found via str.find) and
    next pattern matching `end_marker_re` (regex, multiline). If end not found
    return till end of text."""
    start = text.find(start_marker)
    assert start >= 0, f'start marker not found: {start_marker!r}'
    rest = text[start:]
    em = re.search(end_marker_re, rest[len(start_marker):], re.MULTILINE)
    if em:
        return rest[:len(start_marker) + em.start()]
    return rest


def test_M2_prototype_shell_template_has_docs_link():
    """SKILL.md Step G-7 模板區（UI prototype shell `prototype/index.html`）含
    `<a href="../index.html" ... >← 文件站</a>`。"""
    text = _read_skill_md()
    # Step G-7 (UI prototype shell) → 邊界到下一個 `## Step` 為止
    g7 = _section_between(text, '**Step G-7:', r'^## Step ')
    pattern = r'<a[^>]*href="\.\./index\.html"[^>]*>[^<]*文件[^<]*</a>'
    assert re.search(pattern, g7), \
        f'Step G-7 模板沒含 ← 文件站 link (../index.html)\n區段前 800 chars:\n{g7[:800]}'


# ─── M3: admin template (Step A-4) has docs link ──────────────────────

def test_M3_admin_template_has_docs_link():
    """SKILL.md Step A-4 模板區（admin 5 頁，深度 2）含
    `<a href="../../index.html" ...>← 文件站</a>`。"""
    text = _read_skill_md()
    # Step A-4 邊界 → 下一個 `## Step` 或 EOF
    a4 = _section_between(text, 'Step A-4', r'^## Step ')
    pattern = r'<a[^>]*href="\.\./\.\./index\.html"[^>]*>[^<]*文件[^<]*</a>'
    assert re.search(pattern, a4), \
        f'Step A-4 模板沒含 ← 文件站 link (../../index.html)\n區段前 800 chars:\n{a4[:800]}'


# ─── M4: api-explorer template (Step 2-B Step G-2) has docs link ───────

def test_M4_api_explorer_template_has_docs_link():
    """SKILL.md `## Step 2-B` API Explorer 區（api-explorer/index.html，深度 2）
    含 `<a href="../../index.html" ...>← 文件站</a>`，label 跟 href 一致。"""
    text = _read_skill_md()
    # `## Step 2-B：API Explorer 生成` 區段 → 邊界到下一個 `## Step` (2-C)
    sec = _section_between(text, '## Step 2-B', r'^## Step ')
    pattern = r'<a[^>]*href="\.\./\.\./index\.html"[^>]*>[^<]*文件[^<]*</a>'
    assert re.search(pattern, sec), \
        f'Step 2-B 模板沒含 ← 文件站 link (../../index.html)\n區段前 800 chars:\n{sec[:800]}'


def test_M4_api_explorer_old_broken_link_removed():
    """SKILL.md `## Step 2-B` 不該再有 `<a href="../index.html">← 文件站</a>` 這種
    label 跟 href 不對應的舊模板（label 寫文件站但 href 只到 prototype shell）。"""
    text = _read_skill_md()
    sec = _section_between(text, '## Step 2-B', r'^## Step ')
    bad_pattern = r'<a[^>]*href="\.\./index\.html"[^>]*>[^<]*文件站[^<]*</a>'
    assert not re.search(bad_pattern, sec), \
        f'Step 2-B 仍含 broken label/href ../index.html → 文件站; should be ../../index.html'


# ─── M7: review subagent checklist verifies docs link ─────────────────

def test_M7_review_subagent_checks_docs_link():
    """SKILL.md review 階段含「每個 prototype HTML 必含回 docs index 的 back link」
    檢查項。"""
    text = _read_skill_md()
    # Look for review/quality checklist mentioning docs link verification
    # Either: a checklist item about back-to-docs link
    # Or: explicit text "回 docs" / "回 文件站" / "back to docs" near review section
    has_review_item = bool(re.search(
        r'(回\s*docs|回\s*文件|back\s*to\s*docs|文件站\s*back-link).*\n.*?(prototype|HTML)',
        text, re.IGNORECASE,
    ))
    has_checklist_item = bool(re.search(
        r'-\s*\[\s*\].*(?:文件站|docs.*link|back.*文件)',
        text, re.IGNORECASE,
    ))
    assert has_review_item or has_checklist_item, \
        'review/quality checklist 沒明確驗證 prototype HTML 含 docs back-link'


# ─── M8: docs side — prototype links use named target ─────────────────
# 所有 docs HTML 中指向 `prototype/...` 的 anchor 加 `target="prototype-window"`
# 行為：第一次點開新 tab；後續點任何 prototype link → 同 tab 切換；
# docs 主 tab 不被取代。

def test_M8_sidebar_prototype_link_has_target():
    """make_sidebar 內 prototype 3 個 entry 渲染為 sidebar link 時帶
    target="prototype-window"。"""
    # Setup minimal pages dir with prototype entries
    tmp = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
        'prototype/admin/index.html': '',
        'prototype/api-explorer/index.html': '',
    })
    # Patch PAGES_DIR for scan
    saved = gh.PAGES_DIR
    gh.PAGES_DIR = tmp
    try:
        sidebar = gh.make_sidebar(
            doc_pages=[], server_diagrams=[], frontend_diagrams=[],
            sub_docs={}, current='index',
        )
    finally:
        gh.PAGES_DIR = saved
    # 必含 prototype link 帶 target
    pattern = r'<a[^>]*href="[^"]*prototype/[^"]+"[^>]*target="prototype-window"'
    matches = re.findall(pattern, sidebar)
    assert len(matches) >= 3, \
        f'sidebar prototype links missing target="prototype-window"; matches={len(matches)}\n' \
        f'sidebar (first 1500 chars):\n{sidebar[:1500]}'


def test_M8_cards_prototype_link_has_target():
    """index.html 內 prototype 卡片帶 target="prototype-window"."""
    tmp = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
        'prototype/admin/index.html': '',
        'prototype/api-explorer/index.html': '',
    })
    saved = gh.PAGES_DIR
    gh.PAGES_DIR = tmp
    try:
        section = gh.prototype_cards_section()
    finally:
        gh.PAGES_DIR = saved
    pattern = r'<a[^>]*class="index-card"[^>]*target="prototype-window"'
    matches = re.findall(pattern, section)
    assert len(matches) >= 3, \
        f'prototype cards missing target="prototype-window"; matches={len(matches)}\n' \
        f'section:\n{section[:1500]}'


def test_M8_rewriter_adds_target_for_prototype_link():
    """rewrite_pages_paths 對 markdown 寫的 `<a href="prototype/...">` 自動補
    target="prototype-window"。"""
    tmp = _make_pages_dir({
        'index.html': '',
        'prototype/index.html': '',
    })
    html = '<a href="prototype/index.html">UI Prototype</a>'
    out = gh.rewrite_pages_paths(html, tmp / 'index.html', tmp)
    assert 'target="prototype-window"' in out, \
        f'rewriter should add target for prototype link; got: {out}'


def test_M8_non_prototype_link_no_target():
    """非 prototype/ 的 link 不該被加 target（regression）。"""
    tmp = _make_pages_dir({
        'index.html': '',
        'edd.html': '',
    })
    html = '<a href="edd.html">EDD</a>'
    out = gh.rewrite_pages_paths(html, tmp / 'index.html', tmp)
    assert 'target="prototype-window"' not in out, \
        f'non-prototype link should not get target; got: {out}'


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print(f'M GROUP — prototype docs back-link  source={SKILL_MD}')
    print('=' * 78)
    tests = [
        ('M2_prototype_shell_template_has_docs_link',
         test_M2_prototype_shell_template_has_docs_link),
        ('M3_admin_template_has_docs_link',
         test_M3_admin_template_has_docs_link),
        ('M4_api_explorer_template_has_docs_link',
         test_M4_api_explorer_template_has_docs_link),
        ('M4_api_explorer_old_broken_link_removed',
         test_M4_api_explorer_old_broken_link_removed),
        ('M7_review_subagent_checks_docs_link',
         test_M7_review_subagent_checks_docs_link),
        ('M8_sidebar_prototype_link_has_target',
         test_M8_sidebar_prototype_link_has_target),
        ('M8_cards_prototype_link_has_target',
         test_M8_cards_prototype_link_has_target),
        ('M8_rewriter_adds_target_for_prototype_link',
         test_M8_rewriter_adds_target_for_prototype_link),
        ('M8_non_prototype_link_no_target',
         test_M8_non_prototype_link_no_target),
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
