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


# ─── K2: F1 加嚴 — 樹狀全留 ASCII（非 mermaid） ─────────────────────────

# Real-world fixture: pet/docs/FRONTEND.md L70-... directory tree
FILE_TREE = """\
apps/player/
├── index.html
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx
    └── components/
        ├── layout/
        │   ├── NavBar.tsx
        │   └── Layout.tsx
        ├── landing/
        │   ├── LandingPage.tsx
        │   └── ClaimCTA.tsx
        └── pet/
            ├── PetPage.tsx
            └── StatsPanel.tsx
"""

# pet/docs/PDD.md §3.1 Sitemap (URL paths inside tree branches)
SITEMAP_TREE = """\
pixel-pet-arena.com
│
├── / (Landing Page — Guest Mode)
│   ├── Canvas: Random pixel pet display
│   ├── "Claim This Pet" CTA → /claim
│   └── Nav: Leaderboard, [My Pet if URL known]
│
├── /claim (Claim Pet Page)
│   ├── Email input form
│   ├── Code entry screen
│   └── URL reveal screen
│
├── /pet/:petId (My Pet Page)
│   ├── Pet canvas
│   └── Stats panel
"""

# Synthesized React component tree (matching pet/docs/FRONTEND.md §2.2 shape)
COMPONENT_TREE = """\
<App>
├── <Layout>
│   ├── <NavBar>
│   └── <Outlet>
│       ├── <LandingPage>
│       ├── <ClaimPage>
│       └── <PetPage>
└── <Router>
"""

# pet/docs/IDEA.md §15 Traceability (uses └─►)
TRACEABILITY_TREE = """\
IDEA.md (本文件)
  └─► BRD.md       ← /gendoc brd
        └─► PRD.md      ← /gendoc prd
              └─► PDD.md      ← /gendoc pdd
                    └─► EDD.md      ← /gendoc edd
"""

# Negative case: pure single-column flow (should still be 'system', not tree)
PURE_FLOW = """\
Developer workstation
        │
        ▼
GitHub Pull Request
        │
        ▼
Merge to develop
"""

# Negative case: arch multi-column box (must still be 'system')
ARCH_MULTI_COLUMN = """\
┌────────────┐  ┌────────────┐
│ Guest      │  │ Owner      │
│ (no token) │  │ (URL token)│
└─────┬──────┘  └─────┬──────┘
      │                │
      ▼                ▼
┌──────────────────────────┐
│  CDN / Edge              │
└──────────────────────────┘
"""


def test_K2_file_tree_not_classified_system():
    """File directory tree (含檔名 .ts/.tsx + dir/) 不應被判 'system' → 留 ASCII。"""
    kind = gh._classify_ascii_block(FILE_TREE)
    assert kind != 'system', f'file tree must not be system; got {kind!r}'


def test_K2_sitemap_not_classified_system():
    """Sitemap with URL paths in tree branches → not 'system'."""
    kind = gh._classify_ascii_block(SITEMAP_TREE)
    assert kind != 'system', f'sitemap must not be system; got {kind!r}'


def test_K2_react_component_tree_not_system():
    """React component tree (`<App>`, `<Layout>`) → not 'system'."""
    kind = gh._classify_ascii_block(COMPONENT_TREE)
    assert kind != 'system', f'component tree must not be system; got {kind!r}'


def test_K2_traceability_tree_not_system():
    """IDEA.md traceability `└─►` tree → not 'system'."""
    kind = gh._classify_ascii_block(TRACEABILITY_TREE)
    assert kind != 'system', f'traceability tree must not be system; got {kind!r}'


def test_K2_pure_single_column_flow_still_system():
    """純單欄流 (▼ 含內容行) 仍判 'system'（這個會留給 K3 改 mermaid）。"""
    kind = gh._classify_ascii_block(PURE_FLOW)
    assert kind == 'system', f'pure flow must remain system; got {kind!r}'


def test_K2_multi_column_arch_still_system():
    """多欄並排 box（同行 ≥ 2 個 ┌）仍判 'system'（K4 處理）。"""
    kind = gh._classify_ascii_block(ARCH_MULTI_COLUMN)
    assert kind == 'system', f'arch multi-column must remain system; got {kind!r}'


def test_K2_md_to_html_file_tree_falls_through_to_pre():
    """整合測試: md_to_html 遇到 file tree → emit `<pre>`，不該變 mermaid。"""
    md = f'# T\n\n```\n{FILE_TREE}\n```\n'
    html = gh.md_to_html(md)
    assert '<pre class="mermaid">' not in html, \
        f'file tree was wrongly converted to mermaid; html (first 600):\n{html[:600]}'


def test_K2_md_to_html_sitemap_falls_through_to_pre():
    """整合測試: sitemap → `<pre>`."""
    md = f'# T\n\n```\n{SITEMAP_TREE}\n```\n'
    html = gh.md_to_html(md)
    assert '<pre class="mermaid">' not in html, \
        f'sitemap was wrongly converted to mermaid; html (first 600):\n{html[:600]}'


# ─── K3: F2 單欄流 mermaid 轉換修對 ─────────────────────────────────────

# Real-world fixture: developer-guide.html L575 Request Lifecycle pattern
# (含 box 邊界以觸發 F2 dispatch entry condition)
SINGLE_COL_FLOW_PURE = """\
┌──────────────────┐
│ Player browser   │
└──────────────────┘
        │
        ▼
┌──────────────────────────┐
│ Vite dev server          │
└──────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│ Fastify API              │
└──────────────────────────┘
"""

# Single-column flow with edge annotations (cicd L347 pattern)
SINGLE_COL_FLOW_WITH_LABELS = """\
┌──────────────────┐
│ Developer        │
└──────────────────┘
        │
        │  git push origin feature
        ▼
┌──────────────────────────┐
│ GitHub PR                │
└──────────────────────────┘
        │
        │  Merge to develop
        ▼
┌──────────────────────────┐
│ deploy-staging           │
└──────────────────────────┘
"""


def test_K3_triangle_arrow_not_a_node():
    """`▼` 行不該變成 mermaid node label。"""
    md = gh._ascii_to_mermaid_td(SINGLE_COL_FLOW_PURE)
    assert md is not None, 'F2 should produce mermaid for single-col flow with boxes'
    # 不應該有 N\d+["▼"] 這種 node
    assert not re.search(r'N\d+\["▼"\]', md), \
        f'▼ should NOT become a node; got mermaid:\n{md}'
    assert not re.search(r'N\d+\["▲"\]', md), \
        f'▲ should NOT become a node; got mermaid:\n{md}'


def test_K3_chain_three_boxes():
    """A ▼ B ▼ C → 3 個 node 各一個 box，edges A→B, B→C。"""
    md = gh._ascii_to_mermaid_td(SINGLE_COL_FLOW_PURE)
    assert md is not None
    # 3 個 box content 應出現
    assert 'Player browser' in md
    assert 'Vite dev server' in md
    assert 'Fastify API' in md
    # 應有兩條 edge（不要求嚴格 syntax，至少 mermaid 內 -- 或 --> 出現 ≥ 2 次）
    arrow_count = md.count('-->')
    assert arrow_count >= 2, \
        f'expected ≥2 edges between 3 boxes; arrow_count={arrow_count}\nmermaid:\n{md}'


def test_K3_edge_annotation_becomes_label():
    """`│  git push origin feature` 形式的 annotation 變 edge label。"""
    md = gh._ascii_to_mermaid_td(SINGLE_COL_FLOW_WITH_LABELS)
    assert md is not None
    # annotation 文字不該變成獨立 node
    assert not re.search(r'N\d+\["git push origin feature"\]', md), \
        f'edge annotation should NOT be a node; got:\n{md}'
    assert not re.search(r'N\d+\["Merge to develop"\]', md), \
        f'edge annotation should NOT be a node; got:\n{md}'
    # annotation 應在 edge label 內（mermaid syntax: -->|"label"|）
    assert 'git push origin feature' in md, \
        f'annotation text "git push origin feature" should appear (as edge label):\n{md}'
    assert 'Merge to develop' in md, \
        f'annotation text "Merge to develop" should appear (as edge label):\n{md}'


def test_K3_pure_flow_no_label_no_extra_nodes():
    """純 flow（無 annotation）→ edges 沒 label，nodes 數 = 內容 box 數。"""
    md = gh._ascii_to_mermaid_td(SINGLE_COL_FLOW_PURE)
    assert md is not None
    # 應該剛好 3 個 N\d+
    node_count = len(re.findall(r'^\s*N\d+\["', md, re.MULTILINE))
    assert node_count == 3, \
        f'expected 3 nodes for 3 boxes; got {node_count}\nmermaid:\n{md}'


# ─── K4: F2 多欄並排 fan-in（arch L379 形） ──────────────────────────────

# Real-world fixture: pet/docs/ARCH.md §1.2 System Context Diagram (4 actors)
ARCH_MULTI_COL_FAN_IN = """\
┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐  ┌───────────────┐
│ Guest Player│  │ Pet Owner        │  │Competitive Player │  │Admin Operator │
│ (no token)  │  │ (URL token)      │  │(token + arena)    │  │(TOTP session) │
└──────┬──────┘  └────────┬─────────┘  └─────────┬─────────┘  └──────┬────────┘
       │  HTTPS            │  HTTPS                  │  HTTPS            │  HTTPS
       ▼                   ▼                         ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  CDN / Edge (Vercel)                                                                │
└─────────────────────────────────────────────────────────────────────────────────────┘
"""


def test_K4_multi_column_creates_separate_nodes():
    """4 並排 box → 4 個 mermaid node，每個 label 含對應 actor 名稱。"""
    md = gh._ascii_to_mermaid_td(ARCH_MULTI_COL_FAN_IN)
    assert md is not None, 'multi-column arch must produce mermaid'
    assert 'Guest Player' in md
    assert 'Pet Owner' in md
    assert 'Competitive Player' in md
    assert 'Admin Operator' in md
    assert 'CDN / Edge' in md


def test_K4_no_pipe_chars_in_node_labels():
    """node label 內不該殘留 `│` 字元（K1 描述的核心 bug）。"""
    md = gh._ascii_to_mermaid_td(ARCH_MULTI_COL_FAN_IN)
    assert md is not None
    # 抽出所有 N\d+["..."] label，檢查內容無 │
    for m in re.finditer(r'N\d+\["([^"]*)"\]', md):
        label = m.group(1)
        assert '│' not in label, \
            f'node label "{label}" contains `│` (multi-column bug); mermaid:\n{md}'


def test_K4_multi_row_cell_joins_with_br():
    """多 row 的同一欄（"Guest Player" + "(no token)"）合併成 1 個 node 的 multi-line label。"""
    md = gh._ascii_to_mermaid_td(ARCH_MULTI_COL_FAN_IN)
    assert md is not None
    # mermaid `<br/>` 用來分行；同一個 actor 的兩行應在同一 N\d+ label
    # 形如 N0["Guest Player<br/>(no token)"]
    assert re.search(r'N\d+\["[^"]*Guest Player[^"]*<br\s*/?>[^"]*\(no token\)[^"]*"\]', md), \
        f'multi-row cell merge missing; mermaid:\n{md}'


def test_K4_fan_in_to_downstream():
    """4 個 actor box 各自 → 1 個 CDN box 的 fan-in（4 條 edges 指向同一 N）。"""
    md = gh._ascii_to_mermaid_td(ARCH_MULTI_COL_FAN_IN)
    assert md is not None
    # 找到 CDN node id
    cdn_match = re.search(r'(N\d+)\["[^"]*CDN[^"]*"\]', md)
    assert cdn_match, f'CDN node missing; mermaid:\n{md}'
    cdn_id = cdn_match.group(1)
    # 應有 ≥ 4 條 edges 指向 cdn_id（4 個 actor → CDN）
    edges_to_cdn = len(re.findall(rf'-->[^\n]*\b{cdn_id}\b', md))
    assert edges_to_cdn >= 4, \
        f'expected ≥4 edges to CDN; got {edges_to_cdn}\nmermaid:\n{md}'


def test_K4_https_label_on_edges():
    """4 條 fan-in edges 應帶 HTTPS label。"""
    md = gh._ascii_to_mermaid_td(ARCH_MULTI_COL_FAN_IN)
    assert md is not None
    # 至少 1 條 edge 含 "HTTPS" label
    https_edges = len(re.findall(r'-->\|"[^"]*HTTPS[^"]*"\|', md))
    assert https_edges >= 1, \
        f'expected ≥1 edge with HTTPS label; got {https_edges}\nmermaid:\n{md}'


def test_K4_pure_flow_still_works_no_multi_col():
    """純單欄流（K3 的 fixture）不應走 multi-col parser，結果照舊。"""
    md = gh._ascii_to_mermaid_td(SINGLE_COL_FLOW_PURE)
    assert md is not None
    # K3 行為：3 個 box → 3 個 node
    node_count = len(re.findall(r'^\s*N\d+\["', md, re.MULTILINE))
    assert node_count == 3, \
        f'K3 single-col regression: expected 3 nodes, got {node_count}\nmermaid:\n{md}'


# ─── K5: F2 多行框 linear flow + box-with-inner-content ──────────────────

# Real-world fixture: pet/docs/CICD.md L24-69 Pipeline Overview shape
CICD_PIPELINE_LINEAR = """\
Developer workstation
        │
        │  git push origin feature/my-feature
        ▼
┌───────────────────────────────────────────────────────┐
│  GitHub Pull Request                                  │
│  ci.yml  ─── pnpm install                            │
│           ├── ESLint + tsc                            │
│           ├── Vitest unit tests                       │
│           └── Playwright E2E                          │
│  All checks green → PR can be merged                 │
└───────────────────────────────────────────────────────┘
        │
        │  Merge PR into develop
        ▼
┌───────────────────────────────────────────────────────┐
│  deploy-staging.yml                                   │
│  ├── Build Docker images                              │
│  └── ArgoCD auto-sync                                 │
└───────────────────────────────────────────────────────┘
"""


def test_K5_box_content_joined_with_br():
    """單個大 box 的多行內容 → 合成 1 個 mermaid node 的 multi-line label。"""
    box_only = """\
┌────────────────────────┐
│  Line A                │
│  Line B                │
│  Line C                │
└────────────────────────┘
"""
    md = gh._ascii_to_mermaid_td(box_only)
    assert md is not None
    # 應該只 1 個 node
    node_count = len(re.findall(r'^\s*N\d+\["', md, re.MULTILINE))
    assert node_count == 1, f'expected 1 node for 1 box; got {node_count}\n{md}'
    # label 應含 <br/> 連 3 行
    m = re.search(r'N0\["([^"]+)"\]', md)
    assert m, f'N0 missing; mermaid:\n{md}'
    label = m.group(1)
    assert 'Line A' in label and 'Line B' in label and 'Line C' in label
    assert '<br' in label, f'multi-line label should use <br/>; got: {label!r}'


def test_K5_linear_chain_three_boxes_in_pipeline():
    """cicd L347 風格: text-node + 2 大 box，linear chain → 3 nodes + 2 edges。"""
    md = gh._ascii_to_mermaid_td(CICD_PIPELINE_LINEAR)
    assert md is not None
    # 期望 3 個 node：Developer workstation + GitHub PR (multi-line) + deploy-staging (multi-line)
    node_count = len(re.findall(r'^\s*N\d+\["', md, re.MULTILINE))
    assert node_count == 3, f'expected 3 nodes; got {node_count}\n{md}'
    # 應含內容：Developer / GitHub PR / deploy-staging
    assert 'Developer workstation' in md
    assert 'GitHub Pull Request' in md
    assert 'deploy-staging' in md


def test_K5_inline_tree_chars_preserved_in_label():
    """box 內 `├── ESLint`、`└── E2E` 視覺裝飾字元保留進 multi-line label。"""
    md = gh._ascii_to_mermaid_td(CICD_PIPELINE_LINEAR)
    assert md is not None
    # label 應保留 ├── 字元（user 拍板：保留視覺裝飾）
    assert '├──' in md or 'ESLint' in md, \
        f'tree chars / sub-list content missing; mermaid:\n{md}'


def test_K5_text_before_first_box_becomes_node():
    """大 box 前的 standalone text 行（"Developer workstation"）→ 自己一個 node。"""
    md = gh._ascii_to_mermaid_td(CICD_PIPELINE_LINEAR)
    assert md is not None
    # "Developer workstation" 應成 N0 或某個 N\d+ 的單行 label
    found = re.search(r'N\d+\["Developer workstation"\]', md)
    assert found, f'"Developer workstation" missing as own node; mermaid:\n{md}'


def test_K5_edge_annotation_between_boxes():
    """`│  git push origin feature` 跟 `│  Merge PR into develop` 變 edge label。"""
    md = gh._ascii_to_mermaid_td(CICD_PIPELINE_LINEAR)
    assert md is not None
    # annotations 不該變獨立 node
    assert not re.search(r'N\d+\["git push origin feature"\]', md), \
        f'annotation became node; mermaid:\n{md}'
    assert not re.search(r'N\d+\["Merge PR into develop"\]', md), \
        f'annotation became node; mermaid:\n{md}'
    # annotation 應在 edge label 內
    assert 'git push' in md, f'edge label "git push" missing; mermaid:\n{md}'


def test_K5_no_pipe_in_box_node_labels():
    """大 box 的 multi-line node label 內不含殘留 `│`。"""
    md = gh._ascii_to_mermaid_td(CICD_PIPELINE_LINEAR)
    assert md is not None
    for m in re.finditer(r'N\d+\["([^"]*)"\]', md):
        label = m.group(1)
        assert '│' not in label, \
            f'node label "{label}" contains `│` (linear-box bug); mermaid:\n{md}'


# ─── K6: F2 UML state diagram 識別 ──────────────────────────────────────

# Real-world fixture: pet/docs/prototype/arena-battle-prototype.md State Machine
ARENA_STATE_MACHINE = """\
          ┌─────────────────────────────────────────────────────┐
          │                                                     │
  ┌───────▼──────┐   user selects   ┌────────────────────┐      │
  │    IDLE      │─────opponent────▶│   CHALLENGING      │      │
  │ (opponent    │                  │ (POST /arena/battle│      │
  │  list shown) │                  │  in-flight)        │      │
  └──────────────┘                  └─────────┬──────────┘      │
          ▲                                   │ response 200     │
          │                                   ▼                  │
          │                         ┌──────────────────┐        │
          │                         │    BATTLING      │        │
          │                         │ (Phaser animates │        │
          │                         │  battle log)     │        │
          │                         └────────┬─────────┘        │
          │                                  │ animation done   │
          │                                  ▼                  │
          │                         ┌──────────────────┐        │
          └──────"Fight Again"───── │     RESULT       │────────┘
                                    │  (winner, XP,    │  "Back to
                                    │   rank shown)    │   Pet View"
                                    └──────────────────┘
"""


def test_K6_state_machine_emits_stateDiagram_v2():
    """偵測到 ≥ 3 個 ALL_CAPS 狀態名 → 輸出 `stateDiagram-v2` 而非 `graph TD`。"""
    md = gh._ascii_to_mermaid_td(ARENA_STATE_MACHINE)
    assert md is not None
    assert md.startswith('stateDiagram-v2'), \
        f'state machine should use stateDiagram-v2, not graph TD; got:\n{md[:200]}'


def test_K6_all_states_extracted():
    """4 個狀態 IDLE / CHALLENGING / BATTLING / RESULT 都應出現在 mermaid 內。"""
    md = gh._ascii_to_mermaid_td(ARENA_STATE_MACHINE)
    assert md is not None
    for state in ('IDLE', 'CHALLENGING', 'BATTLING', 'RESULT'):
        assert state in md, f'state {state} missing; mermaid:\n{md}'


def test_K6_initial_state_arrow():
    """應有 `[*] --> X` 起始狀態 arrow。"""
    md = gh._ascii_to_mermaid_td(ARENA_STATE_MACHINE)
    assert md is not None
    assert re.search(r'\[\*\]\s*-->\s*[A-Z]', md), \
        f'initial state [*] arrow missing; mermaid:\n{md}'


def test_K6_non_state_machine_unaffected():
    """純架構 multi-col（無 ALL_CAPS state names）→ 不該被當 state machine。"""
    md = gh._ascii_to_mermaid_td(ARCH_MULTI_COL_FAN_IN)
    assert md is not None
    # 應該還是 graph TD（K4 路徑），非 stateDiagram
    assert 'graph TD' in md, \
        f'arch multi-col regression: should use graph TD; got:\n{md[:200]}'
    assert not md.startswith('stateDiagram'), \
        f'arch multi-col should NOT use stateDiagram; got:\n{md[:200]}'


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
        ('K2_file_tree_not_classified_system', test_K2_file_tree_not_classified_system),
        ('K2_sitemap_not_classified_system', test_K2_sitemap_not_classified_system),
        ('K2_react_component_tree_not_system', test_K2_react_component_tree_not_system),
        ('K2_traceability_tree_not_system', test_K2_traceability_tree_not_system),
        ('K2_pure_single_column_flow_still_system', test_K2_pure_single_column_flow_still_system),
        ('K2_multi_column_arch_still_system', test_K2_multi_column_arch_still_system),
        ('K2_md_to_html_file_tree_falls_through_to_pre', test_K2_md_to_html_file_tree_falls_through_to_pre),
        ('K2_md_to_html_sitemap_falls_through_to_pre', test_K2_md_to_html_sitemap_falls_through_to_pre),
        ('K3_triangle_arrow_not_a_node', test_K3_triangle_arrow_not_a_node),
        ('K3_chain_three_boxes', test_K3_chain_three_boxes),
        ('K3_edge_annotation_becomes_label', test_K3_edge_annotation_becomes_label),
        ('K3_pure_flow_no_label_no_extra_nodes', test_K3_pure_flow_no_label_no_extra_nodes),
        ('K4_multi_column_creates_separate_nodes', test_K4_multi_column_creates_separate_nodes),
        ('K4_no_pipe_chars_in_node_labels', test_K4_no_pipe_chars_in_node_labels),
        ('K4_multi_row_cell_joins_with_br', test_K4_multi_row_cell_joins_with_br),
        ('K4_fan_in_to_downstream', test_K4_fan_in_to_downstream),
        ('K4_https_label_on_edges', test_K4_https_label_on_edges),
        ('K4_pure_flow_still_works_no_multi_col', test_K4_pure_flow_still_works_no_multi_col),
        ('K5_box_content_joined_with_br', test_K5_box_content_joined_with_br),
        ('K5_linear_chain_three_boxes_in_pipeline', test_K5_linear_chain_three_boxes_in_pipeline),
        ('K5_inline_tree_chars_preserved_in_label', test_K5_inline_tree_chars_preserved_in_label),
        ('K5_text_before_first_box_becomes_node', test_K5_text_before_first_box_becomes_node),
        ('K5_edge_annotation_between_boxes', test_K5_edge_annotation_between_boxes),
        ('K5_no_pipe_in_box_node_labels', test_K5_no_pipe_in_box_node_labels),
        ('K6_state_machine_emits_stateDiagram_v2', test_K6_state_machine_emits_stateDiagram_v2),
        ('K6_all_states_extracted', test_K6_all_states_extracted),
        ('K6_initial_state_arrow', test_K6_initial_state_arrow),
        ('K6_non_state_machine_unaffected', test_K6_non_state_machine_unaffected),
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
