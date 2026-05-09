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
