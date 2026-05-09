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
