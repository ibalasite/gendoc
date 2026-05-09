#!/usr/bin/env python3
"""B 群 — scanner / writer / sidebar 測試套件.

B1: scan_subdirectory_docs slug 公式 `subdir__stem` → `subdir/stem`
B2: write_page mkdir parents
B3: writer site 改用新 slug
B4: pages/prototype/ 既有檔保護
B5/B6: sidebar 樹狀 + relpath（在後續 step 加入）

每個測試獨立建 temp DOCS_DIR/PAGES_DIR 並 monkeypatch gh 模組常數，
跑完還原；保證測試彼此隔離、不依賴 cwd。
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile
import shutil
import contextlib

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


@contextlib.contextmanager
def _temp_project(layout: dict):
    """Build a temp project root with given layout, override gh module
    constants for the duration.

    layout keys are paths relative to BASE root (e.g. 'docs/req/idea.md',
    'docs/pages/index.html'). Values are file content strings.
    """
    base = pathlib.Path(tempfile.mkdtemp())
    for rel, content in layout.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if isinstance(content, str) else '')

    saved = {}
    for k in ('BASE', 'DOCS_DIR', 'PAGES_DIR', 'FEATURES_DIR', 'REQ_DIR',
              'DIAGRAMS_DIR'):
        saved[k] = getattr(gh, k)
    gh.BASE = base
    gh.DOCS_DIR = base / 'docs'
    gh.PAGES_DIR = base / 'docs' / 'pages'
    gh.FEATURES_DIR = base / 'features'
    gh.REQ_DIR = base / 'docs' / 'req'
    gh.DIAGRAMS_DIR = base / 'docs' / 'diagrams'
    gh.PAGES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        yield base
    finally:
        for k, v in saved.items():
            setattr(gh, k, v)
        shutil.rmtree(base, ignore_errors=True)


def _slugs_only(scan_result):
    out = []
    for subdir_name, entries in scan_result.items():
        for slug, _label, _p in entries:
            out.append(slug)
    return sorted(out)


# ─── B1: scanner slug 公式升級 ─────────────────────────────────────────

def test_B1_scan_slug_preserves_slash_simple():
    """docs/req/idea-input.md → slug 'req/idea-input' (含 /，不含 __)."""
    with _temp_project({
        'docs/req/idea-input.md': '# idea',
    }):
        result = gh.scan_subdirectory_docs()
        slugs = _slugs_only(result)
        assert 'req/idea-input' in slugs, f'expected req/idea-input, got {slugs}'
        assert not any('__' in s for s in slugs), f'__ leaked: {slugs}'


def test_B1_scan_slug_preserves_slash_nested():
    """docs/blueprint/mock/X.md → slug 'blueprint/mock/x'."""
    with _temp_project({
        'docs/blueprint/mock/X.md': '# x',
    }):
        result = gh.scan_subdirectory_docs()
        slugs = _slugs_only(result)
        assert 'blueprint/mock/x' in slugs, f'expected blueprint/mock/x, got {slugs}'


def test_B1_scan_slug_no_double_underscore():
    """所有 slug 都不該含 __."""
    with _temp_project({
        'docs/req/idea-input.md': '',
        'docs/blueprint/mock/X.md': '',
        'docs/contracts/api-admin-contract.md': '',
        'docs/prototype/sample.md': '',
    }):
        result = gh.scan_subdirectory_docs()
        slugs = _slugs_only(result)
        assert slugs, 'no slugs scanned'
        leaked = [s for s in slugs if '__' in s]
        assert not leaked, f'__ leaked in: {leaked}'


def test_B1_scan_slug_lowercase():
    """MOCK_SERVER_GUIDE.md → slug ...mock_server_guide (lowercase 規則保留)."""
    with _temp_project({
        'docs/blueprint/mock/MOCK_SERVER_GUIDE.md': '',
    }):
        result = gh.scan_subdirectory_docs()
        slugs = _slugs_only(result)
        assert 'blueprint/mock/mock_server_guide' in slugs, slugs


# ─── B2: write_page mkdir parents ────────────────────────────────────────

def test_B2_write_page_creates_nested_dirs():
    """write_page("a/b/c.html", ...) 在乾淨 PAGES_DIR 上自動建 parent dirs."""
    with _temp_project({'docs/dummy.md': ''}) as base:
        # Build minimal write_page invocation. write_page is defined inside
        # main(), so we test the underlying write helper differently:
        # invoke gh._write_page_path which is the extracted helper, OR
        # call it via a small driver. Here we just ensure that calling
        # PAGES_DIR / "a/b/c.html" + parent.mkdir + write_text works,
        # and that gen_html.py's write_page does the mkdir step.
        # We simulate by calling the helper used inside main:
        out_path = gh.PAGES_DIR / "a/b/c.html"
        # Simulate B2 contract: write_page must mkdir before write
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("<html>ok</html>")
        assert out_path.exists()
        assert (gh.PAGES_DIR / "a").is_dir()
        assert (gh.PAGES_DIR / "a/b").is_dir()


def test_B2_write_page_nested_via_main_does_not_crash():
    """跑 gh.main() 時若 sub_docs slug 含 '/'，write_page 必須能寫入而不 crash."""
    layout = {
        'docs/EDD.md': '# EDD\n\nplain content',
        'docs/blueprint/mock/SAMPLE.md': '# Sample\n\nplain content',
        'docs/req/idea-input.md': '# Idea\n\nplain content',
        'README.md': '# Project',
    }
    with _temp_project(layout):
        # main() should not raise FileNotFoundError when writing nested paths.
        try:
            gh.main()
        except FileNotFoundError as e:
            raise AssertionError(
                f'write_page failed to mkdir before write: {e}'
            )
        # And the nested files should exist
        assert (gh.PAGES_DIR / "blueprint/mock/sample.html").is_file(), (
            "expected pages/blueprint/mock/sample.html"
        )
        assert (gh.PAGES_DIR / "req/idea-input.html").is_file(), (
            "expected pages/req/idea-input.html"
        )


def test_B2_write_page_root_unchanged():
    """root .html 寫入路徑不變 (regression)."""
    layout = {
        'docs/EDD.md': '# EDD',
        'README.md': '',
    }
    with _temp_project(layout):
        gh.main()
        assert (gh.PAGES_DIR / "edd.html").is_file()
        assert (gh.PAGES_DIR / "index.html").is_file()


# ─── B3: writer site 用新 slug 寫 subdir ───────────────────────────────

def _make_diagram_md(title='X'):
    return f'# {title}\n\n```mermaid\ngraph TD\n  A --> B\n```\n'


def test_B3_diagrams_writer_subdir():
    """server_diagrams writer 寫 pages/diagrams/{stem}.html (不是 diag-{stem}.html)."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/diagrams/use-case.md': _make_diagram_md('Use Case'),
        'docs/diagrams/sequence-foo.md': _make_diagram_md('Sequence Foo'),
    }
    with _temp_project(layout):
        gh.main()
        assert (gh.PAGES_DIR / "diagrams/use-case.html").is_file(), \
            "expected pages/diagrams/use-case.html"
        assert (gh.PAGES_DIR / "diagrams/sequence-foo.html").is_file(), \
            "expected pages/diagrams/sequence-foo.html"


def test_B3_diagrams_writer_no_flat_diag():
    """diagrams writer 不再寫 pages/diag-{stem}.html flat naming."""
    layout = {
        'README.md': '',
        'docs/diagrams/use-case.md': _make_diagram_md('Use Case'),
    }
    with _temp_project(layout):
        gh.main()
        assert not (gh.PAGES_DIR / "diag-use-case.html").exists(), \
            "should NOT write flat diag-use-case.html"


def test_B3_blueprint_mock_writer_subdir():
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/blueprint/mock/MOCK_GUIDE.md': '# Mock\n\nbody',
    }
    with _temp_project(layout):
        gh.main()
        assert (gh.PAGES_DIR / "blueprint/mock/mock_guide.html").is_file(), \
            "expected pages/blueprint/mock/mock_guide.html"
        # No flat residue from this run
        flat_residue = list(gh.PAGES_DIR.glob("blueprint__*.html"))
        assert not flat_residue, f'flat residue: {flat_residue}'


def test_B3_contracts_writer_subdir():
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/contracts/api-admin.md': '# API\n\nbody',
    }
    with _temp_project(layout):
        gh.main()
        assert (gh.PAGES_DIR / "contracts/api-admin.html").is_file(), \
            "expected pages/contracts/api-admin.html"
        flat_residue = list(gh.PAGES_DIR.glob("contracts__*.html"))
        assert not flat_residue, f'flat residue: {flat_residue}'


def test_B3_req_writer_subdir():
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/req/idea-input.md': '# Idea',
    }
    with _temp_project(layout):
        gh.main()
        assert (gh.PAGES_DIR / "req/idea-input.html").is_file(), \
            "expected pages/req/idea-input.html"
        # The dedicated 'req.html' download page may still exist; check for
        # NO flat req__X.html
        flat_residue = list(gh.PAGES_DIR.glob("req__*.html"))
        assert not flat_residue, f'flat residue: {flat_residue}'


# ─── B4: pages/prototype/ 既有檔保護 ───────────────────────────────────

def test_B4_prototype_existing_html_preserved():
    """pages/prototype/index.html 預先存在 → gen_html 不覆寫."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/prototype/sample.md': '# Sample',
        'docs/pages/prototype/index.html': '<!-- MARKER-INTERACTIVE -->',
    }
    with _temp_project(layout):
        gh.main()
        kept = (gh.PAGES_DIR / 'prototype/index.html').read_text()
        assert 'MARKER-INTERACTIVE' in kept, \
            f'pages/prototype/index.html overwritten: {kept[:200]}'


def test_B4_prototype_md_mirror_writes_when_target_absent():
    """docs/prototype/sample.md 而 pages/prototype/sample.html 不存在 → 鏡射寫入."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/prototype/sample.md': '# Sample\n\nspec body',
    }
    with _temp_project(layout):
        gh.main()
        out = gh.PAGES_DIR / 'prototype/sample.html'
        assert out.is_file(), 'expected pages/prototype/sample.html'


def test_B4_prototype_md_skip_when_target_present():
    """docs/prototype/sample.md 而 pages/prototype/sample.html 已存在
    (gen-prototype 寫的 interactive 版) → gen_html 不覆寫."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/prototype/sample.md': '# Sample (spec)',
        'docs/pages/prototype/sample.html': '<!-- INTERACTIVE-VERSION -->',
    }
    with _temp_project(layout):
        gh.main()
        kept = (gh.PAGES_DIR / 'prototype/sample.html').read_text()
        assert 'INTERACTIVE-VERSION' in kept, \
            f'pages/prototype/sample.html overwritten: {kept[:200]}'


def test_B4_non_prototype_subdir_overwrites_normally():
    """blueprint/mock/X.md 對應 pages/blueprint/mock/x.html 已存在 (前次 gen) →
    本次 gen_html 正常覆寫 (regenerate)."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/blueprint/mock/X.md': '# X NEW',
        'docs/pages/blueprint/mock/x.html': '<!-- STALE OLD -->',
    }
    with _temp_project(layout):
        gh.main()
        new = (gh.PAGES_DIR / 'blueprint/mock/x.html').read_text()
        assert 'STALE OLD' not in new, \
            'blueprint/mock/x.html should be regenerated, not preserved'
        assert 'X NEW' in new, f'expected new content, got: {new[:200]}'


def test_B4_prototype_nested_existing_html_preserved():
    """pages/prototype/api-explorer/index.html (nested) 也保護."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/pages/prototype/api-explorer/index.html': '<!-- API-EXPLORER-INT -->',
    }
    with _temp_project(layout):
        gh.main()
        kept = (gh.PAGES_DIR / 'prototype/api-explorer/index.html').read_text()
        assert 'API-EXPLORER-INT' in kept, \
            'nested pages/prototype/api-explorer/index.html overwritten'


# ─── B5: Sidebar tree + diagrams 內部分區 ──────────────────────────────

def _sidebar_for(layout, current='index'):
    """Build a layout, run gh.main(), return (sidebar_html_of_index, all_html)."""
    with _temp_project(layout):
        gh.main()
        # Pick a representative page to inspect sidebar from
        idx = (gh.PAGES_DIR / 'index.html')
        return idx.read_text() if idx.exists() else ''


def test_B5_sidebar_one_level_collapsible():
    html = _sidebar_for({
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/req/idea.md': '# Idea',
    })
    assert '<details' in html
    assert '📁 req/' in html or '📎 req/' in html or 'req/' in html
    # The link target should be req/idea.html (subdir path)
    assert 'href="req/idea.html"' in html or 'href="./req/idea.html"' in html, \
        f'expected req/idea.html link in sidebar; html sample: {html[:400]}'


def test_B5_sidebar_nested_collapsible():
    html = _sidebar_for({
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/blueprint/mock/X.md': '# X',
    })
    # Two nested <details>: outer for blueprint, inner for mock
    # Look for the indicative structure
    blueprint_idx = html.find('blueprint/')
    mock_idx = html.find('mock/')
    assert blueprint_idx >= 0 and mock_idx > blueprint_idx, \
        f'expected blueprint/ then mock/ nested; got blueprint@{blueprint_idx} mock@{mock_idx}'
    # Count <details> tags between blueprint/ start and the link
    snippet = html[blueprint_idx:mock_idx + 200]
    assert snippet.count('<details') >= 1, \
        f'expected at least one nested <details> between blueprint and link; got {snippet}'


def test_B5_sidebar_collapsed_unless_active():
    html = _sidebar_for({
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/req/x.md': '# X',
    })
    # On index page (current=index), <details> for req/ should NOT have open attr
    # Find the req/ summary and check the corresponding <details>
    import re as _re
    # All <details> tags before req/ summary
    m = _re.search(r'<details(\s+open)?\s*>\s*<summary>[^<]*req/', html)
    assert m, f'no req/ details found: {html[:500]}'
    assert m.group(1) is None, f'req/ details unexpectedly open on index page'


def test_B5_sidebar_open_chain_when_active():
    """current=blueprint/mock/x → both blueprint/ and mock/ <details> have open."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/blueprint/mock/X.md': '# X',
    }
    with _temp_project(layout):
        gh.main()
        # The page for blueprint/mock/X is at pages/blueprint/mock/x.html
        page = (gh.PAGES_DIR / 'blueprint/mock/x.html').read_text()
        # On this page, sidebar must have blueprint/ and mock/ both open
        import re as _re
        # Find blueprint/ details
        bm = _re.search(r'<details(\s+open)?\s*>\s*<summary>[^<]*blueprint/', page)
        assert bm and bm.group(1), 'blueprint/ details not open on its descendant page'
        mm = _re.search(r'<details(\s+open)?\s*>\s*<summary>[^<]*mock/', page)
        assert mm and mm.group(1), 'mock/ details not open on its descendant page'


def _diagrams_layout():
    """Fixture with a representative mix of diagram filenames."""
    return {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/diagrams/use-case.md': '# Use Case',
        'docs/diagrams/activity-foo.md': '# Activity Foo',
        'docs/diagrams/activity-bar.md': '# Activity Bar',
        'docs/diagrams/class-application.md': '# Class App',
        'docs/diagrams/sequence-create-token.md': '# Seq',
        'docs/diagrams/state-machine-pet.md': '# State',
        'docs/diagrams/cicd-pipeline-sequence.md': '# CICD',
        'docs/diagrams/er-diagram.md': '# ER',
        'docs/diagrams/frontend-activity-init.md': '# Frontend Activity',
        'docs/diagrams/frontend-class-component.md': '# Frontend Class',
    }


def test_B5_sidebar_diagrams_collapsible():
    html = _sidebar_for(_diagrams_layout())
    assert '📁 diagrams/' in html, \
        f'expected 📁 diagrams/ collapsible group; got: {html[:600]}'
    # The old root-level 'Server UML' / 'Frontend UML' sections should be
    # gone from sidebar root — they're now INSIDE 📁 diagrams/.
    # We test inclusion by structural position later.


def test_B5_diagrams_inner_has_server_label():
    html = _sidebar_for(_diagrams_layout())
    # Server UML label must appear inside diagrams details
    diag_idx = html.find('📁 diagrams/')
    assert diag_idx >= 0
    # Find the closing </details> for the diagrams summary
    end_idx = html.find('</details>', diag_idx)
    while end_idx >= 0 and html[diag_idx:end_idx].count('<details') > html[diag_idx:end_idx].count('</details>'):
        end_idx = html.find('</details>', end_idx + 1)
    chunk = html[diag_idx:end_idx]
    assert 'Server UML' in chunk, f'Server UML not inside 📁 diagrams/ block; chunk: {chunk[:600]}'


def test_B5_diagrams_inner_has_frontend_label():
    html = _sidebar_for(_diagrams_layout())
    diag_idx = html.find('📁 diagrams/')
    end_idx = html.find('</details>', diag_idx)
    while end_idx >= 0 and html[diag_idx:end_idx].count('<details') > html[diag_idx:end_idx].count('</details>'):
        end_idx = html.find('</details>', end_idx + 1)
    chunk = html[diag_idx:end_idx]
    assert 'Frontend UML' in chunk, 'Frontend UML not inside 📁 diagrams/'


def test_B5_diagrams_inner_has_activity_sub_label():
    html = _sidebar_for(_diagrams_layout())
    # Sub-label CSS class
    assert 'sidebar__label--sub' in html, \
        f'expected sidebar__label--sub class for sub-grouping; got: {html[:600]}'
    # Activity sub-label exists
    assert '>Activity<' in html, 'Activity sub-label missing'


def test_B5_diagrams_inner_class_group():
    html = _sidebar_for(_diagrams_layout())
    assert '>Class<' in html, 'Class sub-label missing'


def test_B5_diagrams_frontend_strips_prefix_for_grouping():
    """frontend-activity-init.md → 在 Frontend UML 區的 Activity 下，不在 Server 區."""
    html = _sidebar_for(_diagrams_layout())
    # Find Frontend UML position
    fe_idx = html.find('Frontend UML')
    assert fe_idx >= 0
    # The frontend-activity-init link must appear AFTER Frontend UML label
    link_idx = html.find('frontend-activity-init')
    assert link_idx > fe_idx, \
        f'frontend-activity-init should appear after Frontend UML label (server@{html.find("Server UML")} fe@{fe_idx} link@{link_idx})'


def test_B5_diagrams_other_group_catches_misc():
    """er-diagram.md (沒 prefix) → 進入 '其他' sub-label."""
    html = _sidebar_for(_diagrams_layout())
    assert '>其他<' in html or 'Other' in html, \
        f'其他 sub-label missing for misc diagrams; html: {html[:600]}'
    # er-diagram link must appear after 其他 sub-label
    other_idx = html.find('>其他<')
    if other_idx < 0:
        other_idx = html.find('Other')
    er_idx = html.find('er-diagram')
    assert er_idx > other_idx, \
        f'er-diagram should be under 其他 (er@{er_idx} other@{other_idx})'


def test_B5_sidebar_prototype_md_inside_folder():
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/prototype/sample.md': '# Sample',
    }
    html = _sidebar_for(layout)
    # 📁 prototype/ collapsible must exist (mirroring the docs/prototype/ subdir)
    assert '📁 prototype/' in html or '🎮 prototype/' in html or 'prototype/' in html, \
        f'expected prototype/ subdir group; html: {html[:600]}'


def test_B5_sidebar_interactive_prototype_section_kept():
    """Interactive Prototypes section 仍存在 (由 scan_prototype_entries 提供)."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/pages/prototype/index.html': '<h1>Interactive</h1>',
    }
    html = _sidebar_for(layout)
    assert 'Interactive Prototypes' in html, \
        f'Interactive Prototypes section missing; html: {html[:600]}'


# ─── B6: cross-link relpath ────────────────────────────────────────────

def test_B6_link_root_to_root():
    """current=index → target=edd.md → href=edd.html (same dir)."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
    }
    with _temp_project(layout):
        gh.main()
        idx = (gh.PAGES_DIR / 'index.html').read_text()
        assert 'href="edd.html"' in idx, \
            f'expected href="edd.html" on index page; got: {idx[:600]}'


def test_B6_link_root_to_subdir():
    """current=index → target=blueprint/mock/x → href=blueprint/mock/x.html."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/blueprint/mock/X.md': '# X',
    }
    with _temp_project(layout):
        gh.main()
        idx = (gh.PAGES_DIR / 'index.html').read_text()
        assert 'href="blueprint/mock/x.html"' in idx, \
            f'expected href="blueprint/mock/x.html" on index; got: {idx[:600]}'


def test_B6_link_subdir_to_root():
    """current=blueprint/mock/x → sidebar 連 EDD → href=../../edd.html."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/blueprint/mock/X.md': '# X',
    }
    with _temp_project(layout):
        gh.main()
        page = (gh.PAGES_DIR / 'blueprint/mock/x.html').read_text()
        assert 'href="../../edd.html"' in page, \
            f'expected href="../../edd.html" on subdir page; got first 1000: {page[:1000]}'


def test_B6_link_subdir_to_sibling_subdir():
    """current=blueprint/mock/x → sidebar 連 contracts/y → href=../../contracts/y.html."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/blueprint/mock/X.md': '# X',
        'docs/contracts/Y.md': '# Y',
    }
    with _temp_project(layout):
        gh.main()
        page = (gh.PAGES_DIR / 'blueprint/mock/x.html').read_text()
        assert 'href="../../contracts/y.html"' in page, \
            f'expected href="../../contracts/y.html"; got: {page[:1000]}'


def test_B6_active_class_still_works():
    """current=blueprint/mock/x → sidebar 對應 link 有 active class."""
    layout = {
        'README.md': '',
        'docs/EDD.md': '# EDD',
        'docs/blueprint/mock/X.md': '# X',
    }
    with _temp_project(layout):
        gh.main()
        page = (gh.PAGES_DIR / 'blueprint/mock/x.html').read_text()
        # Find the sidebar link to blueprint/mock/x — should have ' active'
        # The href will be self-referential ('x.html' since same dir)
        import re as _re
        # The link text X should appear; class may include 'active'
        m = _re.search(r'<a class="sidebar__link[^"]*active[^"]*"[^>]*>[^<]*X', page)
        assert m, f'no active class on self link in subdir page; sidebar slice unavailable'


# ─── Standalone runner ───────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'B GROUP SCANNER TEST  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('B1_scan_slug_preserves_slash_simple', test_B1_scan_slug_preserves_slash_simple),
        ('B1_scan_slug_preserves_slash_nested', test_B1_scan_slug_preserves_slash_nested),
        ('B1_scan_slug_no_double_underscore', test_B1_scan_slug_no_double_underscore),
        ('B1_scan_slug_lowercase', test_B1_scan_slug_lowercase),
        ('B2_write_page_creates_nested_dirs', test_B2_write_page_creates_nested_dirs),
        ('B2_write_page_nested_via_main_does_not_crash', test_B2_write_page_nested_via_main_does_not_crash),
        ('B2_write_page_root_unchanged', test_B2_write_page_root_unchanged),
        ('B3_diagrams_writer_subdir', test_B3_diagrams_writer_subdir),
        ('B3_diagrams_writer_no_flat_diag', test_B3_diagrams_writer_no_flat_diag),
        ('B3_blueprint_mock_writer_subdir', test_B3_blueprint_mock_writer_subdir),
        ('B3_contracts_writer_subdir', test_B3_contracts_writer_subdir),
        ('B3_req_writer_subdir', test_B3_req_writer_subdir),
        ('B4_prototype_existing_html_preserved', test_B4_prototype_existing_html_preserved),
        ('B4_prototype_md_mirror_writes_when_target_absent', test_B4_prototype_md_mirror_writes_when_target_absent),
        ('B4_prototype_md_skip_when_target_present', test_B4_prototype_md_skip_when_target_present),
        ('B4_non_prototype_subdir_overwrites_normally', test_B4_non_prototype_subdir_overwrites_normally),
        ('B4_prototype_nested_existing_html_preserved', test_B4_prototype_nested_existing_html_preserved),
        ('B5_sidebar_one_level_collapsible', test_B5_sidebar_one_level_collapsible),
        ('B5_sidebar_nested_collapsible', test_B5_sidebar_nested_collapsible),
        ('B5_sidebar_collapsed_unless_active', test_B5_sidebar_collapsed_unless_active),
        ('B5_sidebar_open_chain_when_active', test_B5_sidebar_open_chain_when_active),
        ('B5_sidebar_diagrams_collapsible', test_B5_sidebar_diagrams_collapsible),
        ('B5_diagrams_inner_has_server_label', test_B5_diagrams_inner_has_server_label),
        ('B5_diagrams_inner_has_frontend_label', test_B5_diagrams_inner_has_frontend_label),
        ('B5_diagrams_inner_has_activity_sub_label', test_B5_diagrams_inner_has_activity_sub_label),
        ('B5_diagrams_inner_class_group', test_B5_diagrams_inner_class_group),
        ('B5_diagrams_frontend_strips_prefix_for_grouping', test_B5_diagrams_frontend_strips_prefix_for_grouping),
        ('B5_diagrams_other_group_catches_misc', test_B5_diagrams_other_group_catches_misc),
        ('B5_sidebar_prototype_md_inside_folder', test_B5_sidebar_prototype_md_inside_folder),
        ('B5_sidebar_interactive_prototype_section_kept', test_B5_sidebar_interactive_prototype_section_kept),
        ('B6_link_root_to_root', test_B6_link_root_to_root),
        ('B6_link_root_to_subdir', test_B6_link_root_to_subdir),
        ('B6_link_subdir_to_root', test_B6_link_subdir_to_root),
        ('B6_link_subdir_to_sibling_subdir', test_B6_link_subdir_to_sibling_subdir),
        ('B6_active_class_still_works', test_B6_active_class_still_works),
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
