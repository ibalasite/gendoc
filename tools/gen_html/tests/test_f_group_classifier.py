#!/usr/bin/env python3
"""F 群 — ASCII 區塊分類器 + (F2) ASCII→Mermaid 轉換器 TDD test suite.

Fixtures 來自 pet 實際 .md 內容，覆蓋：
- 系統流程（sequence diagram with → arrows + lifelines）
- 系統架構（parallel boxes）
- 流程樹（in-content ├──, └── branches）
- UI mockup（buttons, inputs, pagination, navbar+sidenav）
- Edge cases（unknown / ambiguous）

F1 (classifier): 每個 fixture 應正確被分類成 'system' | 'ui' | 'unknown'
F2 (mermaid):    'system' fixtures 經 ascii_to_mermaid_td() 後輸出合法 mermaid TD
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


# ─── Fixtures (real pet/erp content) ───────────────────────────────────

# SYSTEM — sequence diagram with horizontal arrows + lifelines (ARCH block 9)
SEQ_LIFELINES = """\
Guest Browser                  Game API (Fastify)          PostgreSQL       Redis         SendGrid
     │                               │                          │               │               │
     │  GET /api/v1/pets/random       │                          │               │               │
     │──────────────────────────────>│                          │               │               │
     │                               │ Generate seed (random)   │               │               │
     │                               │─────────────────────────>│               │               │
     │                               │ INSERT pets(seed, rarity, reserved_until=NOW()+24h)       │
     │                               │<─────────────────────────│               │               │
     │  {petId, seed, rarity, ...}   │                          │               │               │
     │<──────────────────────────────│                          │               │               │
"""

# SYSTEM — architecture with parallel boxes side by side (EDD block 1)
ARCH_PARALLEL = """\
┌─────────────────────────────────────────────────────────────────────┐
│  Client Layer (Browser)                                             │
│                                                                     │
│  ┌──────────────────────────────────┐   ┌─────────────────────────┐ │
│  │  Player App (React + Phaser.js)  │   │  Admin Portal (Vue 3)   │ │
│  │  Vite build / CDN (Vercel)       │   │  Vite build / CDN       │ │
│  └─────────────┬────────────────────┘   └──────────────┬──────────┘ │
└────────────────┼──────────────────────────────────────┼─────────────┘
"""

# SYSTEM — CI/CD flow with inline branches (CICD block 0)
CICD_INLINE_TREE = """\
┌─────────────────────────────────────────────────────────┐
│  GitHub Pull Request (feature/* → develop or main)      │
│                                                         │
│  ci.yml  ─── pnpm install                               │
│           ├── ESLint + tsc (all packages)               │
│           ├── Vitest unit tests (≥80% coverage)         │
│           ├── Supabase local stack (integration tests)  │
│           └── upload coverage to Codecov                │
└─────────────────────────────────────────────────────────┘
"""

# SYSTEM — text-only flow with ASCII arrows (no boxes)
TEXT_FLOW = """\
User Action (click pet, complete training, win arena battle)
     │
     ↓
React event handler
     │
     ↓
Phaser game loop tick
"""

# UI — admin moderation prototype (page + sidenav + table + buttons)
UI_ADMIN_TABLE = """\
┌────────────────────────────────────────────────────────────────────┐
│  pixel-pet-arena Admin                          [admin@arena ▾]    │
├──────────────┬─────────────────────────────────────────────────────┤
│  Pets        │  Pet Management                                      │
│  Battles     │                                                      │
│  GDPR        │  Search: [________________]  Type: [All ▾]  [Filter]│
│              │  ┌──────┬──────────┬──────┬───────┬────────────────┐│
│              │  │ ID   │ Name     │ Lvl  │ Owner │ Status  Action ││
│              │  ├──────┼──────────┼──────┼───────┼────────────────┤│
│              │  │abc12 │ Blazekin │  12  │ user1 │ Active  [Ban]  ││
│              │  │volt4 │ Voltclaw │  11  │ user2 │ Active  [Ban]  ││
│              │  └──────┴──────────┴──────┴───────┴────────────────┘│
│              │  Showing 3 of 1,204 pets  [< 1  2  3 ... 101 >]     │
└──────────────┴─────────────────────────────────────────────────────┘
"""

# UI — simple modal with form fields and action buttons
UI_MODAL_FORM = """\
┌─[X]─ 編輯 Token ───────────────────────────────┐
│ 描述：[N8N 銷售報表________________]            │
│ 過期：[2026-12-31_______________]              │
│                                                 │
│                        [取消]  [儲存]           │
└─────────────────────────────────────────────────┘
"""

# UNKNOWN — directory tree (text only, no arrows, no boxes, no UI)
DIRECTORY_TREE = """\
apps/player/
├── src/
│   ├── App.tsx
│   ├── PetPage.tsx
│   └── components/
└── package.json
"""

# UNKNOWN — single small box with plain text
SIMPLE_BOX_TEXT = """\
┌──────────────────────────┐
│ Pure text inside a box   │
│ no arrows, no buttons    │
└──────────────────────────┘
"""


# ─── F1: classifier tests ───────────────────────────────────────────────

def test_F1_classify_seq_lifelines_as_system():
    assert gh._classify_ascii_block(SEQ_LIFELINES) == 'system'


def test_F1_classify_arch_parallel_as_system():
    assert gh._classify_ascii_block(ARCH_PARALLEL) == 'system'


def test_F1_classify_cicd_inline_tree_as_system():
    assert gh._classify_ascii_block(CICD_INLINE_TREE) == 'system'


def test_F1_classify_text_flow_as_system():
    assert gh._classify_ascii_block(TEXT_FLOW) == 'system'


def test_F1_classify_ui_admin_table_as_ui():
    assert gh._classify_ascii_block(UI_ADMIN_TABLE) == 'ui'


def test_F1_classify_ui_modal_form_as_ui():
    assert gh._classify_ascii_block(UI_MODAL_FORM) == 'ui'


def test_F1_classify_directory_tree_unknown_or_system():
    """Directory tree has └── ├── characters — classify as 'tree' (K2 added),
    'system' (legacy), or 'unknown'. Must NOT be 'ui' (no buttons / inputs)."""
    result = gh._classify_ascii_block(DIRECTORY_TREE)
    assert result in ('tree', 'system', 'unknown'), f'unexpected: {result}'


def test_F1_classify_simple_box_text_unknown():
    """Plain text in a single box — no signals → unknown."""
    assert gh._classify_ascii_block(SIMPLE_BOX_TEXT) == 'unknown'


# ─── F1 integration: gen_html does NOT UI-mock-render system ASCII ────

def test_F1_integration_arch_block_not_rendered_as_umock():
    """ARCH md with parallel-box system block → output HTML does NOT contain
    umock__page or umock__card classes for that block."""
    import tempfile, shutil
    base = pathlib.Path(tempfile.mkdtemp())
    try:
        (base / 'README.md').write_text('# r')
        (base / 'docs').mkdir()
        (base / 'docs' / 'ARCH.md').write_text(
            f'# Arch\n\n```\n{ARCH_PARALLEL}\n```\n'
        )
        # Patch gh constants
        saved = {k: getattr(gh, k) for k in ('BASE','DOCS_DIR','PAGES_DIR','FEATURES_DIR','REQ_DIR','DIAGRAMS_DIR')}
        gh.BASE = base; gh.DOCS_DIR = base/'docs'; gh.PAGES_DIR = base/'docs/pages'
        gh.FEATURES_DIR = base/'features'; gh.REQ_DIR = base/'docs/req'
        gh.DIAGRAMS_DIR = base/'docs/diagrams'
        gh.PAGES_DIR.mkdir(parents=True, exist_ok=True)
        try:
            gh.main()
            arch_html = (gh.PAGES_DIR / 'arch.html').read_text()
            # The CSS block always contains umock__ rules — that's fine.
            # We check there's no <div class="umock__page|card|modal"> in body.
            import re as _re
            mocks = _re.findall(r'<div class="umock__(?:page|card|modal)\b', arch_html)
            assert len(mocks) == 0, \
                f'ARCH block was incorrectly rendered as UI mock ({len(mocks)} blocks)'
        finally:
            for k, v in saved.items(): setattr(gh, k, v)
    finally:
        shutil.rmtree(base, ignore_errors=True)


# ─── F2: ASCII → mermaid TD conversion ─────────────────────────────────

def test_F2_arch_parallel_to_mermaid_td():
    """ARCH parallel-boxes → mermaid graph TD with at least the box labels as nodes."""
    md = gh._ascii_to_mermaid_td(ARCH_PARALLEL)
    assert md is not None
    # Must declare top-down direction
    assert 'graph TD' in md or 'flowchart TD' in md, f'expected TD direction: {md[:200]}'
    # Must mention the labels (Player App / Admin Portal etc.)
    assert 'Player App' in md, 'Player App box missing in mermaid output'
    assert 'Admin Portal' in md, 'Admin Portal box missing in mermaid output'


def test_F2_cicd_inline_tree_to_mermaid_td():
    """CICD with ├── ESLint, ├── Vitest etc. → mermaid TD with ESLint, Vitest as nodes."""
    md = gh._ascii_to_mermaid_td(CICD_INLINE_TREE)
    assert md is not None
    assert 'graph TD' in md or 'flowchart TD' in md
    # ESLint, Vitest mentioned
    assert 'ESLint' in md
    assert 'Vitest' in md or 'unit tests' in md


def test_F2_text_flow_to_mermaid_td():
    """Pure text-arrow flow → mermaid TD chain."""
    md = gh._ascii_to_mermaid_td(TEXT_FLOW)
    assert md is not None
    assert 'graph TD' in md or 'flowchart TD' in md
    assert 'React event handler' in md
    assert 'Phaser' in md


def test_F2_ui_block_returns_none():
    """UI block should not be sent to mermaid converter (caller's responsibility),
    but if called, the converter should at least not crash and return None or
    a non-mermaid string."""
    md = gh._ascii_to_mermaid_td(UI_ADMIN_TABLE)
    # We accept None (refuse to convert) or string starting with non-mermaid marker
    assert md is None or 'graph TD' not in (md or ''), \
        'UI block should not produce mermaid TD'


# ─── Standalone runner ───────────────────────────────────────────────────

def main() -> int:
    print('=' * 78)
    print(f'F GROUP CLASSIFIER + MERMAID CONVERTER  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('F1_classify_seq_lifelines_as_system', test_F1_classify_seq_lifelines_as_system),
        ('F1_classify_arch_parallel_as_system', test_F1_classify_arch_parallel_as_system),
        ('F1_classify_cicd_inline_tree_as_system', test_F1_classify_cicd_inline_tree_as_system),
        ('F1_classify_text_flow_as_system', test_F1_classify_text_flow_as_system),
        ('F1_classify_ui_admin_table_as_ui', test_F1_classify_ui_admin_table_as_ui),
        ('F1_classify_ui_modal_form_as_ui', test_F1_classify_ui_modal_form_as_ui),
        ('F1_classify_directory_tree_unknown_or_system', test_F1_classify_directory_tree_unknown_or_system),
        ('F1_classify_simple_box_text_unknown', test_F1_classify_simple_box_text_unknown),
        ('F1_integration_arch_block_not_rendered_as_umock', test_F1_integration_arch_block_not_rendered_as_umock),
        ('F2_arch_parallel_to_mermaid_td', test_F2_arch_parallel_to_mermaid_td),
        ('F2_cicd_inline_tree_to_mermaid_td', test_F2_cicd_inline_tree_to_mermaid_td),
        ('F2_text_flow_to_mermaid_td', test_F2_text_flow_to_mermaid_td),
        ('F2_ui_block_returns_none', test_F2_ui_block_returns_none),
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
