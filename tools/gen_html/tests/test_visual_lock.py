#!/usr/bin/env python3
"""Visual-lock unit tests — one test per fixture.

256 fixtures (extracted from scan_visual.mjs pass set). Two modes:
  - mode="replay"   : run `gh.md_to_html(input_md)`, extract Nth
                      <div class="diagram-container">, compare to expected_html.
  - mode="snapshot" : read the stored .html file directly, extract Nth
                      diagram block, compare to expected_html (snapshot used
                      for stale flat .html / puml that gen_html no longer
                      regenerates from a normal md_to_html path).

The 3 真實破圖 (P1/P2/P3 in logic/issues.md) are NOT here — they're tracked
in issues.md and locked once fixed.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'
FIX_DIR = pathlib.Path(__file__).resolve().parent / 'fixtures' / 'visual_lock'

PROJ_ROOT = {
    'pet': pathlib.Path('/Users/tobala/projects/pet'),
    'erp': pathlib.Path('/Users/tobala/projects/erp-api-token-manager'),
}

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


def _normalize(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def _extract_all_diagram_blocks(html: str) -> list[str]:
    """Same algorithm as extractor: all <div class="diagram-container...">
    outerHTML in document order, including nested."""
    blocks = []
    div_open_re = re.compile(
        r'<div\b[^>]*?class="diagram-container[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    scan_re = re.compile(r'</?div\b', re.IGNORECASE)
    pos = 0
    while True:
        m = div_open_re.search(html, pos)
        if not m:
            break
        i = m.end()
        depth = 1
        while depth > 0:
            sm = scan_re.search(html, i)
            if not sm:
                break
            if sm.group(0).startswith('</'):
                depth -= 1
                i = sm.end() + 1
            else:
                depth += 1
                i = sm.end()
        end = html.find('</div>', i - 1)
        if end == -1:
            blocks.append(html[m.start():i].strip())
        else:
            blocks.append(html[m.start():end + len('</div>')].strip())
        pos = m.end()
    return blocks


def _make_test(fix_path: pathlib.Path):
    def run():
        f = json.loads(fix_path.read_text(encoding='utf-8'))
        mode = f.get('mode', 'replay')
        idx = f['block_idx']
        expected = f['expected_html']

        if mode == 'replay':
            input_md = f['input_md']
            src_kind = f.get('source_kind', 'md')
            # src_dir: locate the source file dir for relative refs
            src_rel = f.get('source_file', '')
            proj = f['project']
            src_dir = PROJ_ROOT[proj] / pathlib.Path(src_rel).parent if src_rel else None
            actual_html = gh.md_to_html(input_md, src_dir=src_dir)
            actual_blocks = _extract_all_diagram_blocks(actual_html)
            if idx >= len(actual_blocks):
                raise AssertionError(
                    f'{f["id"]}: md_to_html only produced {len(actual_blocks)} blocks, '
                    f'idx={idx} out of range'
                )
            actual = actual_blocks[idx]
        else:
            # snapshot mode: read the stored .html and pull block[idx]
            proj = f['project']
            html_path = PROJ_ROOT[proj] / 'docs/pages' / f['html_file']
            stored = html_path.read_text(encoding='utf-8')
            stored_blocks = _extract_all_diagram_blocks(stored)
            if idx >= len(stored_blocks):
                raise AssertionError(
                    f'{f["id"]}: stored .html only has {len(stored_blocks)} blocks, '
                    f'idx={idx} out of range'
                )
            actual = stored_blocks[idx]

        if _normalize(actual) != _normalize(expected):
            raise AssertionError(
                f'{f["id"]} [{mode}] — output drift\n'
                f'--- actual ---\n{actual[:400]}\n'
                f'--- expected ---\n{expected[:400]}'
            )

    run.__name__ = f'test_{fix_path.stem.replace("-", "_")}'
    return run


# ─── Auto-register all fixtures ──────────────────────────────────────
_TESTS = []
for proj_dir in sorted(FIX_DIR.iterdir()):
    if not proj_dir.is_dir():
        continue
    for fix in sorted(proj_dir.glob('*.json')):
        name = f'test_{proj_dir.name}_{fix.stem.replace("-", "_")}'
        fn = _make_test(fix)
        fn.__name__ = name
        globals()[name] = fn
        _TESTS.append((name, fn, fix))


def main():
    print('=' * 78)
    print(f'VISUAL LOCK — {len(_TESTS)} fixtures')
    print('=' * 78)
    passed = failed = 0
    failures = []
    by_mode = {'replay': 0, 'snapshot': 0}
    for name, fn, fix in _TESTS:
        d = json.loads(fix.read_text(encoding='utf-8'))
        by_mode[d.get('mode', 'replay')] = by_mode.get(d.get('mode', 'replay'), 0) + 1
        try:
            fn()
            passed += 1
        except AssertionError as e:
            failed += 1
            failures.append((name, str(e)))
        except Exception as e:
            failed += 1
            failures.append((name, f'{type(e).__name__}: {e}'))
    print(f'modes: replay={by_mode["replay"]}, snapshot={by_mode["snapshot"]}')
    if failures:
        print(f'\n{len(failures)} failures (first 5):')
        for name, msg in failures[:5]:
            print(f'\n❌ {name}\n   {msg[:600]}')
    print('\n' + '=' * 78)
    print(f'TOTAL: {passed} PASS / {failed} FAIL  ({len(_TESTS)} cases)')
    print('=' * 78)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
