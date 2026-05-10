#!/usr/bin/env python3
"""gen_html.py 跑完後，pages/assets/{app.js,style.css} 必須與 gendoc canonical
版本（`<gendoc>/docs/pages/assets/`）byte-equal。

Root cause（實機 erp/index.html N1 sidebar 全壞）：
gen_html.py 以前只 `(PAGES_DIR / "assets").mkdir(exist_ok=True)`，從不 deploy
assets。結果 HTML 用最新 N1 結構（含 `<button class="sidebar__tab">`）但 JS / CSS
是舊版（無 N1 tab handler / collapse / scroll-spy） → tab 點不動、收合不
運作、scrollbar 全展不開、tab 上方留白。

Common fix: gen_html.py 自動從 `<gendoc>/docs/pages/assets/` copy
（dev 路徑跟 runtime 路徑都是相對 `gen_html.py` 兩層上的 `docs/pages/assets/`）。
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'
CANONICAL_ASSETS = REPO / 'docs' / 'pages' / 'assets'


def _run_gen_html_in_sandbox(extra_md: dict[str, str] | None = None) -> pathlib.Path:
    """Spin up a tmp project dir, drop minimal docs/, run gen_html.py.
    Returns path to the produced pages/ dir."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='gendoc_assets_'))
    docs = tmp / 'docs'
    docs.mkdir(parents=True)
    (docs / 'IDEA.md').write_text('# Idea\nminimal.\n', encoding='utf-8')
    if extra_md:
        for name, body in extra_md.items():
            (docs / name).write_text(body, encoding='utf-8')
    proc = subprocess.run(
        [sys.executable, str(GEN_HTML)],
        cwd=str(tmp),
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, \
        f'gen_html exited {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}'
    return tmp / 'docs' / 'pages'


# ─── Test cases ──────────────────────────────────────────────────────

def test_pages_assets_dir_exists():
    """pages/assets/ 目錄存在。"""
    pages = _run_gen_html_in_sandbox()
    try:
        assert (pages / 'assets').is_dir(), \
            f'pages/assets/ should exist after gen_html; got pages/:\n{list(pages.iterdir())}'
    finally:
        shutil.rmtree(pages.parent.parent, ignore_errors=True)


def test_pages_assets_app_js_byte_equal_canonical():
    """pages/assets/app.js 必須跟 gendoc canonical 一字不差（含 N1 邏輯）。"""
    pages = _run_gen_html_in_sandbox()
    try:
        target = pages / 'assets' / 'app.js'
        canonical = CANONICAL_ASSETS / 'app.js'
        assert target.is_file(), f'pages/assets/app.js missing: {target}'
        assert canonical.is_file(), f'canonical missing: {canonical}'
        assert target.read_bytes() == canonical.read_bytes(), \
            f'pages/assets/app.js != canonical\n' \
            f'  target size:    {target.stat().st_size}\n' \
            f'  canonical size: {canonical.stat().st_size}'
    finally:
        shutil.rmtree(pages.parent.parent, ignore_errors=True)


def test_pages_assets_style_css_byte_equal_canonical():
    """pages/assets/style.css 必須跟 gendoc canonical 一字不差。"""
    pages = _run_gen_html_in_sandbox()
    try:
        target = pages / 'assets' / 'style.css'
        canonical = CANONICAL_ASSETS / 'style.css'
        assert target.is_file(), f'pages/assets/style.css missing: {target}'
        assert canonical.is_file(), f'canonical missing: {canonical}'
        assert target.read_bytes() == canonical.read_bytes(), \
            f'pages/assets/style.css != canonical\n' \
            f'  target size:    {target.stat().st_size}\n' \
            f'  canonical size: {canonical.stat().st_size}'
    finally:
        shutil.rmtree(pages.parent.parent, ignore_errors=True)


def test_app_js_contains_n1_handlers():
    """確認 deployed app.js 含 N1 handler（tab toggle + collapse + scroll-spy）。"""
    pages = _run_gen_html_in_sandbox()
    try:
        js = (pages / 'assets' / 'app.js').read_text(encoding='utf-8')
        assert 'gendoc:sidebar-collapsed' in js, \
            'collapse localStorage key missing — app.js outdated'
        assert 'sidebar__tab' in js, 'tab handler missing'
        assert 'IntersectionObserver' in js, 'scroll-spy missing'
    finally:
        shutil.rmtree(pages.parent.parent, ignore_errors=True)


def test_existing_user_assets_overwritten_with_canonical():
    """N1 regression: 即便目標 dir 已有 stale app.js / style.css，
    gen_html 必須覆蓋成 canonical 版（這正是 erp/pet 上 stuck 的原因）。"""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='gendoc_assets_overwrite_'))
    try:
        docs = tmp / 'docs'
        pages_assets = docs / 'pages' / 'assets'
        pages_assets.mkdir(parents=True)
        # Pre-seed with stale content
        (pages_assets / 'app.js').write_text('// stale\n', encoding='utf-8')
        (pages_assets / 'style.css').write_text('/* stale */\n', encoding='utf-8')
        (docs / 'IDEA.md').write_text('# Idea\n', encoding='utf-8')
        proc = subprocess.run(
            [sys.executable, str(GEN_HTML)],
            cwd=str(tmp),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0, f'gen_html failed: {proc.stderr}'
        target_js = (pages_assets / 'app.js').read_text(encoding='utf-8')
        canonical_js = (CANONICAL_ASSETS / 'app.js').read_text(encoding='utf-8')
        assert target_js == canonical_js, \
            f'stale app.js must be overwritten with canonical; got first 100:\n{target_js[:100]}'
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ─── Standalone runner ────────────────────────────────────────────────

def main():
    print('=' * 78)
    print(f'ASSETS DEPLOY — gen_html.py auto-syncs pages/assets/ from canonical')
    print('=' * 78)
    tests = [
        ('pages_assets_dir_exists', test_pages_assets_dir_exists),
        ('pages_assets_app_js_byte_equal_canonical', test_pages_assets_app_js_byte_equal_canonical),
        ('pages_assets_style_css_byte_equal_canonical', test_pages_assets_style_css_byte_equal_canonical),
        ('app_js_contains_n1_handlers', test_app_js_contains_n1_handlers),
        ('existing_user_assets_overwritten_with_canonical', test_existing_user_assets_overwritten_with_canonical),
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
