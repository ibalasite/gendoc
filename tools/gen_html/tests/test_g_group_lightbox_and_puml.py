#!/usr/bin/env python3
"""G 群 — lightbox + PUML auto-fix + .md link rewrite TDD tests.

G-Q2: lightbox shows empty when clicking diagram-container (UI Mock DSL pyramid,
      mermaid, PUML SVG all affected). Root cause: cloned diagram-container
      becomes position:absolute with width 0; SVG width:100% renders 0×0.

G-Q1b: gen-html auto-fix common PUML syntax errors so figure renders even when
       source .md/.puml has issues.

G-Q4: rewrite_pages_paths handle bare X.md / ./X.md hrefs.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
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
    base = pathlib.Path(tempfile.mkdtemp())
    for rel, content in layout.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if isinstance(content, str) else '')
    saved = {k: getattr(gh, k) for k in
             ('BASE','DOCS_DIR','PAGES_DIR','FEATURES_DIR','REQ_DIR','DIAGRAMS_DIR')}
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


# ─── G-Q2: lightbox cloned-diagram visible width ────────────────────────

def test_GQ2_inline_style_has_lightbox_zoom_content_diagram_rule():
    """gen_html inline <style> must contain a CSS rule that gives cloned
    .diagram-container inside .lightbox__zoom-content an explicit, non-zero
    width so the SVG inside renders."""
    src = GEN_HTML.read_text(encoding='utf-8')
    # Find inline <style>...</style> block(s)
    styles = re.findall(r'<style>(.*?)</style>', src, re.DOTALL)
    inline = '\n'.join(styles)
    # Must mention .lightbox__zoom-content with .diagram-container or svg
    has_rule = (
        re.search(r'\.lightbox__zoom-content\s+\.diagram-container', inline) is not None
        or re.search(r'\.lightbox__zoom-content\s+svg', inline) is not None
    )
    assert has_rule, (
        'inline <style> missing G-Q2 fix: rule for .lightbox__zoom-content + '
        '.diagram-container / svg with explicit width'
    )


def test_GQ2_lightbox_diagram_explicit_width():
    """The fix must give cloned diagram-container an explicit width (vw / px /
    fixed value) — otherwise it collapses to 0 because of position:absolute
    in the parent .lightbox__zoom-content > * rule."""
    src = GEN_HTML.read_text(encoding='utf-8')
    styles = '\n'.join(re.findall(r'<style>(.*?)</style>', src, re.DOTALL))
    # Find the lightbox-zoom-content scoped block(s)
    block_match = re.search(
        r'\.lightbox__zoom-content[^{]*\{[^}]*?(?:width|min-width)\s*:\s*[0-9]+\s*(?:vw|px|%)',
        styles, re.DOTALL,
    )
    assert block_match is not None, (
        '.lightbox__zoom-content scoped rule with explicit width:'
        f'{styles[:200]}'
    )


def test_GQ2_lightbox_svg_has_height_auto():
    """SVG inside lightbox should keep aspect ratio (height:auto)."""
    src = GEN_HTML.read_text(encoding='utf-8')
    styles = '\n'.join(re.findall(r'<style>(.*?)</style>', src, re.DOTALL))
    # The fix block should include svg height:auto for aspect-ratio preservation
    has_height_auto = re.search(
        r'\.lightbox__zoom-content[^}]*?svg[^}]*?height\s*:\s*auto',
        styles, re.DOTALL,
    ) is not None or re.search(
        r'\.lightbox__zoom-content\s+svg\s*\{[^}]*?height\s*:\s*auto',
        styles, re.DOTALL,
    ) is not None
    assert has_height_auto, 'svg inside lightbox should set height:auto'


def test_GQ2_pyramid_html_structure_unchanged():
    """Regression: pyramid render still emits <div class="diagram-container">
    with <svg class="umock__pyramid"> inside (existing UI Mock parser output)."""
    md = '''# Test
```
              ┌─────────────┐
              │  E2E Tests  │
              │   5–10%     │
         ┌────┴─────────────┴────┐
         │  Integration Tests    │
         │     20–30%            │
    ┌────┴───────────────────────┴────┐
    │  Unit Tests                     │
    │     60–70%                      │
    └─────────────────────────────────┘
```
'''
    html = gh.md_to_html(md)
    assert '<div class="diagram-container">' in html
    assert '<svg class="umock__pyramid"' in html
    assert '<polygon' in html
    assert 'E2E Tests' in html


# ─── G-Q1b: PUML auto-fix (gen-html 自動修壞 PUML 讓圖能出來) ────────────

# Real fixtures from pet failing PUMLs

# par/and (sequence diagram parallel branch — official PUML uses else, not and)
PUML_PAR_AND = '''@startuml
participant "Player" as p
participant "Server" as s
par Branch A
  p -> s: hi
and
  s -> p: ack
end
@enduml'''

# arrow with |label| (use case / dataflow style — not accepted by official server)
PUML_ARROW_LABEL = '''@startuml
[Player] -->|email + OTP| (Claim Flow)
[Sendgrid] -.->|fallback| [Backup]
@enduml'''

# !define color macro referenced in package color
PUML_DEFINE_COLOR = '''@startuml
!define FRONTEND #E8F4F8
package "Client Layer" #FRONTEND {
  component [Player App] as p
}
@enduml'''


def test_GQ1b_autofix_par_and_to_else():
    fixed = gh._puml_autofix(PUML_PAR_AND)
    # `and` between par and end becomes `else`
    assert re.search(r'\belse\b', fixed), f'par/and not converted to else: {fixed}'
    assert not re.search(r'^\s*and\b', fixed, re.MULTILINE), f'`and` still present: {fixed}'


def test_GQ1b_autofix_arrow_label_stripped():
    fixed = gh._puml_autofix(PUML_ARROW_LABEL)
    # |label| pattern between arrow head and target is removed
    assert '|email + OTP|' not in fixed
    assert '|fallback|' not in fixed
    # The arrow itself (and target) remains
    assert '(Claim Flow)' in fixed
    assert '[Backup]' in fixed


def test_GQ1b_autofix_define_color_expanded():
    fixed = gh._puml_autofix(PUML_DEFINE_COLOR)
    # #FRONTEND inline reference replaced with actual hex
    assert '#FRONTEND' not in fixed.replace('!define FRONTEND', '')
    assert '#E8F4F8' in fixed


def test_GQ1b_autofix_idempotent():
    """Applying autofix twice should give the same result."""
    once = gh._puml_autofix(PUML_PAR_AND)
    twice = gh._puml_autofix(once)
    assert once == twice


def test_GQ1b_autofix_does_not_break_clean_puml():
    """Clean PUML without any of the bad patterns should pass through unchanged."""
    clean = '''@startuml
participant A
participant B
A -> B: hi
B -> A: ok
@enduml'''
    assert gh._puml_autofix(clean) == clean


def test_GQ1b_plantuml_to_svg_retries_with_autofix():
    """When the original PUML fails (HTTP 400), _plantuml_to_svg should
    auto-fix common errors and retry. We verify the offline fix path by
    ensuring _puml_autofix is called (we can't easily mock the network
    here, so this is a structural test)."""
    # Ensure the bridge function exists in the module
    assert hasattr(gh, '_puml_autofix'), '_puml_autofix function must exist'
    # And that _plantuml_to_svg references it (best-effort: source grep)
    src = GEN_HTML.read_text(encoding='utf-8')
    plantuml_fn = re.search(r'def _plantuml_to_svg.*?(?=\ndef |\Z)', src, re.DOTALL)
    assert plantuml_fn is not None
    assert '_puml_autofix' in plantuml_fn.group(0), \
        '_plantuml_to_svg must call _puml_autofix on failure'


# ─── G-Q4: rewrite_pages_paths bare .md → .html ─────────────────────────

def _make_pages_dir_with(layout):
    tmp = pathlib.Path(tempfile.mkdtemp())
    for rel in layout:
        target = tmp / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('')
    return tmp


def test_GQ4_bare_md_rewrites_to_html():
    """<a href="PRD.md"> → <a href="prd.html"> when pages/prd.html exists."""
    html = '<a href="PRD.md">PRD</a>'
    pages = _make_pages_dir_with(['prd.html', 'index.html'])
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="prd.html"' in out, f'expected prd.html href; got: {out}'


def test_GQ4_dot_slash_md_rewrites():
    """<a href="./PRD.md"> → <a href="prd.html">."""
    html = '<a href="./PRD.md">PRD</a>'
    pages = _make_pages_dir_with(['prd.html', 'index.html'])
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="prd.html"' in out, f'expected prd.html href; got: {out}'


def test_GQ4_md_target_missing_strips_anchor():
    """<a href="MISSING.md"> 且 missing.html 不存在 → strip <a> 留 text."""
    html = '<a href="MISSING.md">MISSING</a>'
    pages = _make_pages_dir_with(['index.html'])
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert '<a href' not in out, f'expected stripped anchor; got: {out}'
    assert 'MISSING' in out


def test_GQ4_subdir_relative_md_rewrites():
    """<a href="diagrams/X.md"> bare（無 docs/ prefix）已被 R3-3 處理(B 群)，不重複 case."""
    # Just regression check that it still works
    html = '<a href="diagrams/foo.md">x</a>'
    pages = _make_pages_dir_with(['diagrams/foo.html', 'index.html'])
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="diagrams/foo.html"' in out


def test_GQ4_anchor_after_md_preserved():
    """<a href="PRD.md#section"> → <a href="prd.html#section">."""
    html = '<a href="PRD.md#features">PRD</a>'
    pages = _make_pages_dir_with(['prd.html', 'index.html'])
    out = gh.rewrite_pages_paths(html, pages / 'index.html', pages)
    assert 'href="prd.html#features"' in out, f'anchor not preserved; got: {out}'


# ─── Standalone runner ─────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'G GROUP TESTS  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('GQ2_inline_style_has_lightbox_zoom_content_diagram_rule',
         test_GQ2_inline_style_has_lightbox_zoom_content_diagram_rule),
        ('GQ2_lightbox_diagram_explicit_width',
         test_GQ2_lightbox_diagram_explicit_width),
        ('GQ2_lightbox_svg_has_height_auto',
         test_GQ2_lightbox_svg_has_height_auto),
        ('GQ2_pyramid_html_structure_unchanged',
         test_GQ2_pyramid_html_structure_unchanged),
        ('GQ1b_autofix_par_and_to_else', test_GQ1b_autofix_par_and_to_else),
        ('GQ1b_autofix_arrow_label_stripped', test_GQ1b_autofix_arrow_label_stripped),
        ('GQ1b_autofix_define_color_expanded', test_GQ1b_autofix_define_color_expanded),
        ('GQ1b_autofix_idempotent', test_GQ1b_autofix_idempotent),
        ('GQ1b_autofix_does_not_break_clean_puml', test_GQ1b_autofix_does_not_break_clean_puml),
        ('GQ1b_plantuml_to_svg_retries_with_autofix', test_GQ1b_plantuml_to_svg_retries_with_autofix),
        ('GQ4_bare_md_rewrites_to_html', test_GQ4_bare_md_rewrites_to_html),
        ('GQ4_dot_slash_md_rewrites', test_GQ4_dot_slash_md_rewrites),
        ('GQ4_md_target_missing_strips_anchor', test_GQ4_md_target_missing_strips_anchor),
        ('GQ4_subdir_relative_md_rewrites', test_GQ4_subdir_relative_md_rewrites),
        ('GQ4_anchor_after_md_preserved', test_GQ4_anchor_after_md_preserved),
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
