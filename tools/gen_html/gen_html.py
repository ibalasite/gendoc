#!/usr/bin/env python3
# tools/gen_html/gen_html.py  (deployed to tools/bin/gen_html.py by setup)
# VERSION: 3.8.0
# Maintained by gendoc — DO NOT EDIT IN TARGET PROJECTS
# Install: ~/.claude/skills/gendoc/setup  →  ~/.claude/skills/gendoc/tools/bin/gen_html.py
# Usage:   python3 ~/.claude/skills/gendoc/tools/bin/gen_html.py   (run from project root)

import os, re, json, html as _html, subprocess, urllib.request, urllib.error, zlib
from pathlib import Path
from typing import Optional

# ─── PlantUML support ────────────────────────────────────────────────────────

PLANTUML_SERVER = 'https://www.plantuml.com/plantuml'
_puml_cache: dict = {}  # puml_text → svg_string (session cache)

def _plantuml_encode(text: str) -> str:
    """Encode PlantUML text for plantuml.com server URL (custom base64 of raw DEFLATE)."""
    raw = zlib.compress(text.encode('utf-8'))[2:-4]  # strip zlib header + Adler32 tail
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    result = []
    for i in range(0, len(raw), 3):
        b = (raw[i:i+3] + b'\x00\x00')[:3]
        result += [chars[b[0] >> 2],
                   chars[((b[0] & 3) << 4) | (b[1] >> 4)],
                   chars[((b[1] & 15) << 2) | (b[2] >> 6)],
                   chars[b[2] & 63]]
    return ''.join(result)

def _puml_autofix(text: str) -> str:
    """G-Q1b — auto-fix common PUML syntax errors that the public plantuml.com
    server rejects (HTTP 400) so the diagram can render even when source has
    issues. Applied as second-attempt repair in _plantuml_to_svg.

    Three rules verified against pet's 6 failing PUML files:
      1. par/and/end → par/else/end (sequence-diagram parallel branch).
         Tracks block nesting so `and` inside nested alt/loop/opt is left alone.
      2. arrow `|label|` token → stripped (use case / dataflow arrow labels
         that the official server doesn't accept). Lossy (label is dropped)
         but the connection itself renders.
      3. !define NAME #HEX macros → expanded inline. Server doesn't apply
         !define to package/component color attributes (#NAME).

    Idempotent: applying twice gives the same result.
    """
    import re as _re
    # Rule 1: par/and → par/else (block-aware)
    out = []
    stack = []
    for line in text.split('\n'):
        s = line.strip()
        if _re.match(r'^par\b', s):
            stack.append('par')
            out.append(line)
            continue
        if _re.match(r'^(alt|opt|loop|group|critical|break)\b', s):
            stack.append('other')
            out.append(line)
            continue
        if _re.match(r'^end\b', s):
            if stack:
                stack.pop()
            out.append(line)
            continue
        if _re.match(r'^and\b', s) and stack and stack[-1] == 'par':
            out.append(_re.sub(r'\band\b', 'else', line, count=1))
            continue
        out.append(line)
    text = '\n'.join(out)
    # Rule 2: strip |label| tokens after arrow heads
    text = _re.sub(r'(\s*-+\.?-?>)\s*\|[^|]+\|\s*', r'\1 ', text)
    text = _re.sub(r'(\s*<-?\.?-+)\s*\|[^|]+\|\s*', r'\1 ', text)
    # Rule 3: expand !define NAME #HEX inline
    macros = {}
    for m in _re.finditer(
        r'^\s*!define\s+(\w+)\s+(#[0-9A-Fa-f]{3,8})\b', text, _re.MULTILINE,
    ):
        macros[m.group(1)] = m.group(2)
    if macros:
        new_lines = []
        for line in text.split('\n'):
            if any(_re.match(rf'^\s*!define\s+{name}\b', line) for name in macros):
                new_lines.append(line)
                continue
            for name, hex_val in macros.items():
                line = _re.sub(rf'#{name}\b', hex_val, line)
            new_lines.append(line)
        text = '\n'.join(new_lines)
    return text


def _plantuml_to_svg(text: str) -> Optional[str]:
    """Convert PlantUML text → inline SVG string. Returns None on failure.
    Priority: 1) local plantuml CLI  2) plantuml.com server (raw + autofix)
              3) None
    G-Q1b: when the first server attempt fails, retry with auto-fixed source
    so common syntax errors don't kill the diagram.
    """
    if text in _puml_cache:
        return _puml_cache[text]

    svg = None

    # 1) Try local plantuml binary (no network, fastest)
    try:
        proc = subprocess.run(
            ['plantuml', '-tsvg', '-pipe', '-charset', 'UTF-8'],
            input=text.encode('utf-8'), capture_output=True, timeout=15
        )
        if proc.returncode == 0 and b'<svg' in proc.stdout:
            svg = proc.stdout.decode('utf-8')
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 2) Fallback: plantuml.com server (raw input)
    if svg is None:
        try:
            url = f'{PLANTUML_SERVER}/svg/{_plantuml_encode(text)}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = r.read().decode('utf-8')
                if '<svg' in data:
                    svg = data
        except Exception:
            pass

    # 2b) G-Q1b: retry server with auto-fixed PUML if first attempt failed.
    if svg is None:
        fixed = _puml_autofix(text)
        if fixed != text:
            try:
                url = f'{PLANTUML_SERVER}/svg/{_plantuml_encode(fixed)}'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=12) as r:
                    data = r.read().decode('utf-8')
                    if '<svg' in data:
                        svg = data
            except Exception:
                pass

    if svg:
        # Strip XML declaration so SVG can be embedded inline
        svg = re.sub(r'<\?xml[^>]+\?>\s*', '', svg).strip()
        # 拿掉 inline 固定 px 寬高，讓 CSS .diagram-container--puml svg 統一控制
        svg = _strip_svg_dimensions(svg)
        _puml_cache[text] = svg
    return svg


def _strip_svg_dimensions(svg: str) -> str:
    """Remove fixed pixel width/height from outer <svg> tag so CSS controls sizing.

    Targets: width="Npx", height="Npx" attributes, plus 'width:Npx;height:Npx' in
    inline style. Other style props (background, etc.) are preserved.
    """
    # Match the first <svg ...> opening tag
    def _clean(match: 're.Match[str]') -> str:
        tag = match.group(0)
        # remove width="Npx" / height="Npx"
        tag = re.sub(r'\s+(?:width|height)="[\d.]+px"', '', tag)
        # remove width:Npx; / height:Npx; from inline style="..."
        def _strip_style(sm):
            style = sm.group(1)
            style = re.sub(r'(?:^|;)\s*(?:width|height)\s*:\s*[\d.]+px\s*(?=;|$)',
                           '', style)
            style = re.sub(r';;+', ';', style).strip(';').strip()
            return f'style="{style}"' if style else ''
        tag = re.sub(r'style="([^"]*)"', _strip_style, tag, count=1)
        # tidy whitespace
        tag = re.sub(r'\s+', ' ', tag).replace(' >', '>')
        return tag
    return re.sub(r'<svg\b[^>]*>', _clean, svg, count=1)

def _puml_block_to_html(raw_lines: list[str]) -> str:
    """Convert a list of plantuml block lines to HTML (inline SVG or code fallback)."""
    puml = '\n'.join(raw_lines).strip()
    if not puml.startswith('@startuml'):
        puml = '@startuml\n' + puml + '\n@enduml'
    svg = _plantuml_to_svg(puml)
    if svg:
        return f'<div class="diagram-container diagram-container--puml">{svg}</div>'
    # Fallback: show raw source with warning
    return (f'<pre><code class="language-plantuml">{esc(puml)}</code></pre>'
            f'<p style="color:var(--text-muted);font-size:0.875rem">⚠️ PlantUML 圖表無法生成'
            f'（請確認本機已安裝 plantuml 或網路可連至 plantuml.com）</p>')

# Always resolve relative to cwd (the target project root), not this script's location
BASE = Path.cwd()
DOCS_DIR = BASE / "docs"
PAGES_DIR = BASE / "docs" / "pages"
FEATURES_DIR = BASE / "features"
REQ_DIR = BASE / "docs" / "req"
DIAGRAMS_DIR = DOCS_DIR / "diagrams"

def read_state():
    try:
        return json.loads((BASE / ".gendoc-state.json").read_text())
    except:
        return {}

state = read_state()
APP_NAME = state.get("project_name") or BASE.name
GITHUB_REPO = state.get("github_repo", "")
if not GITHUB_REPO:
    try:
        import subprocess
        _url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            cwd=str(BASE), stderr=subprocess.DEVNULL
        ).decode().strip()
        GITHUB_REPO = _url.removesuffix(".git") if _url.endswith(".git") else _url
    except:
        pass

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TITLE__ — __APP__</title>
  <link rel="stylesheet" href="assets/style.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css">
  <style>
    /* ─── Sidebar collapsible folder groups ─── */
    .sidebar__section details { border: none; }
    .sidebar__section details > summary {
      cursor: pointer; list-style: none; display: flex; align-items: center;
      gap: 0.375rem; padding: 0 1rem; margin-bottom: 0.375rem;
      font-size: 0.6875rem; font-weight: 600; color: var(--text-muted);
      text-transform: uppercase; letter-spacing: 0.08em; user-select: none;
    }
    .sidebar__section details > summary::-webkit-details-marker { display: none; }
    .sidebar__section details > summary::before {
      content: '▶'; font-size: 0.5rem; flex-shrink: 0;
      transition: transform 150ms; color: var(--text-muted);
    }
    .sidebar__section details[open] > summary::before { transform: rotate(90deg); }
    .sidebar__section details .sidebar__link { padding-left: 1.75rem; font-size: 0.8125rem; }
    .sidebar__section details details > summary { padding-left: 1.75rem; }
    .sidebar__section details details .sidebar__link { padding-left: 2.5rem; }
    /* B5/B8: labels inside details are sub-labels — indent past their parent <summary>. */
    .sidebar__section details > .sidebar__label {
      padding-left: 2.25rem;
    }
    .sidebar__section details details > .sidebar__label {
      padding-left: 3rem;
    }
    /* B5: sub-label inside diagrams folding for prefix groups (Activity / Class / ...) */
    .sidebar__label--sub {
      padding: 0.25rem 1rem 0.125rem 3rem;
      font-size: 0.6875rem; font-weight: 600;
      color: var(--text-muted); text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    /* B5: links following a sub-label indent further still */
    .sidebar__section details .sidebar__label--sub ~ .sidebar__link {
      padding-left: 3.5rem;
    }
    /* ─── N1: sidebar tab switcher (📁 文件 / 📑 本頁目錄) ─── */
    /* `padding: 0` overrides style.css `.sidebar { padding: 1.5rem 0 }`.
       Without it, tabs/panels inherit 24px top/bottom space and panel
       flex child can't fully fill height → scrollbar truncated mid-list. */
    .sidebar { position: relative; display: flex; flex-direction: column;
      overflow: hidden; padding: 0; }
    .sidebar__toggle { position: absolute; top: 6px; right: 6px;
      background: #f1f5f9; border: 1px solid #cbd5e1;
      padding: 2px 6px; border-radius: 4px;
      cursor: pointer; font-size: 11px; line-height: 1;
      color: #475569; z-index: 3; }
    .sidebar__toggle:hover { background: #e2e8f0; }
    .sidebar__tabs { display: flex; gap: 2px; padding: 4px 32px 0 4px;
      border-bottom: 1px solid #e2e8f0; background: #f8fafc;
      flex-shrink: 0; }
    .sidebar__tab { flex: 1; padding: 6px 8px; font-size: 12px;
      border: 1px solid transparent; border-bottom: none;
      border-radius: 4px 4px 0 0; cursor: pointer; background: transparent;
      color: #64748b; font-family: inherit; text-align: center;
      transition: background-color 150ms, color 150ms; }
    .sidebar__tab:hover { color: #1e293b; background: #f1f5f9; }
    .sidebar__tab.active { background: #fff; color: #1e3a8a;
      border-color: #e2e8f0; font-weight: 600; margin-bottom: -1px; }
    .sidebar__panel { display: none; flex: 1; overflow-y: auto;
      padding: 0.5rem 0; font-size: 0.875rem; }
    .sidebar__panel.active { display: block; }
    /* TOC list rendering inside the toc panel */
    .sidebar__panel .toc-list { list-style: none; padding: 0; margin: 0; }
    .sidebar__panel .toc-list li { margin: 0; }
    .toc__link { display: block; padding: 0.25rem 0.75rem;
      color: #475569; text-decoration: none; font-size: 0.8125rem;
      border-left: 2px solid transparent; margin: 1px 0;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .toc__link:hover { background: #f1f5f9; color: #1e293b; }
    .toc__link.active { background: #eff6ff; color: #1e3a8a;
      border-left-color: #3b82f6; font-weight: 500; }
    .toc__link--h3 { padding-left: 1.5rem; font-size: 0.78rem; color: #64748b; }
    /* Sidebar collapsed state — keep a 32px rail visible so the toggle
       button stays clickable; hide tabs + panels. Overrides style.css's
       .page-wrapper.sidebar-collapsed { grid-template-columns: 0 4px 1fr; }
       to keep the rail. */
    .page-wrapper.sidebar-collapsed { grid-template-columns: 32px 4px 1fr; }
    .page-wrapper.sidebar-collapsed .sidebar {
      width: 32px; min-width: 32px;
      visibility: visible; padding: 0; overflow: visible;
    }
    .page-wrapper.sidebar-collapsed .sidebar__tabs,
    .page-wrapper.sidebar-collapsed .sidebar__panel { display: none; }
    .page-wrapper.sidebar-collapsed .sidebar__toggle { left: 4px; right: 4px; }
    /* RWD — auto-collapse on phones (<768px). Only kicks in when no
       explicit `.sidebar-expanded` flag is set; tap the toggle to expand. */
    @media (max-width: 768px) {
      .page-wrapper:not(.sidebar-expanded) {
        grid-template-columns: 32px 4px 1fr;
      }
      .page-wrapper:not(.sidebar-expanded) .sidebar {
        width: 32px; min-width: 32px;
      }
      .page-wrapper:not(.sidebar-expanded) .sidebar__tabs,
      .page-wrapper:not(.sidebar-expanded) .sidebar__panel { display: none; }
    }
    /* G-Q2: lightbox cloned-diagram visibility.
       The lightbox sets `.lightbox__zoom-content > * { position:absolute }`
       which collapses the cloned .diagram-container to 0×0; its child SVG
       with `width:100%` then renders empty. Force a sensible explicit
       width so the cloned content is actually visible. */
    .lightbox__zoom-content .diagram-container {
      width: 80vw;
      max-width: 1400px;
      min-width: 60vw;
    }
    .lightbox__zoom-content .diagram-container svg {
      width: 100%;
      height: auto;
      max-height: 80vh;
      display: block;
    }
    .lightbox__zoom-content .diagram-container .mermaid {
      width: 100%;
      max-width: none;
    }
    .lightbox__zoom-content svg {
      height: auto;
    }
    /* G-Q5: prevent flex/grid child main.doc-content from expanding to its
       content's intrinsic size when a PUML SVG / pre.mermaid has wide
       content. Without min-width:0, the flex item's default min-width is
       its min-content (i.e. SVG natural width), which pushes <main> to
       3000px+ on PUML pages and breaks layout.

       Pair with `<pre> { max-width: 100% }` so wide source content scrolls
       inside the <pre> block instead of expanding the page. */
    main.doc-content {
      min-width: 0;
    }
    .doc-content pre {
      max-width: 100%;
    }
    .doc-content .diagram-container {
      max-width: 100%;
      overflow-x: auto;
    }

    /* ─── UI Mock DSL (stage 9) ─── */
    .umock { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; color: #1e293b; }
    .umock__page, .umock__modal, .umock__card {
      border: 1.5px solid #94a3b8; border-radius: 8px; background: #fff;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin: 1rem 0;
      overflow: hidden;
    }
    .umock__card-title { padding: 0.625rem 1rem; font-weight: 600; font-size: 0.95rem;
      background: #f8fafc; border-bottom: 1.5px solid #94a3b8; color: #1e293b; }
    .umock__page-title { padding: 0.75rem 1rem; font-weight: 600; font-size: 1.05rem;
      background: #f8fafc; border-bottom: 1.5px solid #94a3b8; }
    /* `.diagram-container` (assets/style.css) defaults to text-align: center
       which is right for SVG/mermaid but wrong for umock body text. Reset
       to start so individual umock elements decide their own alignment.
       Also constrain width to content so umock card mirrors ASCII source
       proportions (rather than stretching to full doc-content width). */
    .diagram-container--umock {
      text-align: start;
      width: fit-content;
      max-width: 100%;
    }
    .diagram-container--umock .umock__card,
    .diagram-container--umock .umock__page,
    .diagram-container--umock .umock__modal {
      width: fit-content;
      max-width: 100%;
    }
    /* Outer-alignment modifiers — applied via attrs.align detected from
       the source ASCII's leading/trailing whitespace within `│ ... │`. */
    .umock__card-title--center, .umock__page-title--center,
    .umock__text--center, .umock__info--center, .umock__hint--center,
    .umock__actions--center { text-align: center; }
    .umock__card-title--right, .umock__page-title--right,
    .umock__text--right, .umock__info--right, .umock__hint--right,
    .umock__actions--right { text-align: right; }
    .umock__modal { max-width: 540px; }
    .umock__modal-titlebar { display: flex; justify-content: space-between; align-items: center;
      padding: 0.75rem 1rem; background: #f1f5f9; border-bottom: 1.5px solid #94a3b8; }
    .umock__modal-title { font-weight: 600; font-size: 1rem; }
    .umock__modal-close { color: #94a3b8; font-size: 1.1rem; cursor: default; }
    .umock__modal-body, .umock__page > .umock__section,
    .umock__card { padding: 0.75rem 1rem; }
    .umock__navbar { display: flex; gap: 1rem; align-items: center;
      padding: 0.625rem 1rem; background: #1e293b; color: #f1f5f9;
      border-radius: 8px 8px 0 0; }
    .umock__sidenav { float: left; width: 12rem; padding: 0.75rem;
      background: #f8fafc; border-right: 1px solid #e2e8f0; min-height: 200px; }
    .umock__sidenav .umock__item { padding: 0.375rem 0.5rem; border-radius: 4px;
      color: #475569; font-size: 0.875rem; }
    .umock__sidenav .umock__item:hover { background: #e2e8f0; }
    .umock__page > *:not(.umock__navbar):not(.umock__sidenav) { margin-left: 12.5rem;
      padding: 0.75rem 1rem; }
    .umock__page::after { content: ""; display: block; clear: both; }
    .umock__section { padding: 0.75rem 0; }
    .umock__section-title { margin: 0 0 0.5rem 0; font-size: 1rem; font-weight: 600; }
    .umock__section-subtitle { color: #64748b; font-size: 0.875rem; margin-bottom: 0.5rem; }
    .umock__field { margin: 0.5rem 0; }
    .umock__field-label { display: block; font-size: 0.85rem; color: #334155;
      margin-bottom: 0.25rem; font-weight: 500; }
    .umock__field-required { color: #dc2626; margin-left: 0.125rem; }
    .umock__input, .umock__search {
      display: block; width: 100%; padding: 0.5rem 0.625rem; font-size: 0.9rem;
      border: 1px solid #94a3b8; border-radius: 4px; background: #fff;
      color: #475569; box-sizing: border-box;
    }
    .umock__btn { display: inline-block; padding: 0.4rem 0.9rem; margin: 0.125rem;
      font-size: 0.875rem; font-weight: 500; border: 1px solid transparent;
      border-radius: 4px; cursor: default; background: #e2e8f0; color: #334155; }
    .umock__btn--primary { background: #2563eb; color: #fff; }
    .umock__btn--secondary { background: #fff; color: #475569; border-color: #cbd5e1; }
    .umock__btn--danger { background: #dc2626; color: #fff; }
    .umock__actions { padding: 0.5rem 0;
      border-top: 1px solid #f1f5f9; }
    .umock__badge { display: inline-block; padding: 0.125rem 0.5rem;
      border-radius: 999px; font-size: 0.75rem; font-weight: 500;
      background: #e2e8f0; color: #475569; }
    .umock__badge--active { background: #dcfce7; color: #166534; }
    .umock__badge--inactive { background: #fee2e2; color: #991b1b; }
    .umock__badge--warning { background: #fef3c7; color: #92400e; }
    .umock__hint { color: #64748b; font-size: 0.8rem; margin: 0.25rem 0 0.5rem 0; }
    .umock__info { background: #eff6ff; border-left: 3px solid #3b82f6;
      padding: 0.5rem 0.75rem; margin: 0.5rem 0; color: #1e3a8a; font-size: 0.875rem; }
    /* Plain body text row in UI mock: monospace, preserve whitespace,
       left-aligned, no background. Maps to ASCII content rows that aren't
       semantic markers (ⓘ / helper:). */
    .umock__text { padding: 0.125rem 1rem; margin: 0; color: #1e293b;
      font-family: 'Menlo','Consolas','Courier New',monospace;
      font-size: 0.85rem; white-space: pre; }
    /* Higher specificity than `.doc-content pre` (assets/style.css) so the
       umock dark-canvas background isn't overridden by the generic `pre`
       rule when umock is rendered inside `.doc-content`. */
    .doc-content pre.umock__code, pre.umock__code { background: #1e293b; color: #f1f5f9; padding: 0.75rem;
      border-radius: 4px; overflow-x: auto; font-size: 0.8rem;
      font-family: ui-monospace, "SF Mono", Consolas, monospace; }
    .umock__code code { background: none; color: inherit; padding: 0; }
    .umock__table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.9rem; }
    .umock__table th, .umock__table td { padding: 0.75rem 0.875rem; text-align: left;
      border-bottom: 1px solid #cbd5e1; }
    .umock__table th { background: #f8fafc; font-weight: 600; color: #334155;
      border-bottom: 2px solid #94a3b8; }
    .umock__table tbody tr:hover { background: #f8fafc; }
    .umock__pagination { padding: 0.5rem 0; color: #64748b; font-size: 0.8rem; text-align: right; }
    .umock__tabs { display: flex; gap: 0.5rem; padding: 0.25rem 0; border-bottom: 1px solid #e2e8f0; }
    .umock__tab { padding: 0.375rem 0.75rem; color: #475569; font-size: 0.875rem;
      border-bottom: 2px solid transparent; }
    .umock__tab:first-child { border-bottom-color: #2563eb; color: #1e40af; font-weight: 500; }
    .umock__filter-bar { display: flex; gap: 0.5rem; align-items: center;
      padding: 0.5rem 0; }
    .umock__divider { border: 0; border-top: 1px solid #e2e8f0; margin: 0.5rem 0; }
    .umock__meta-line { color: #64748b; font-size: 0.8rem; margin: 0.125rem 0; }
    .umock__row { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
    .umock__row-cell { font-size: 0.875rem; color: #334155; }
    .umock__avatar { width: 1.75rem; height: 1.75rem; border-radius: 50%;
      background: #94a3b8; display: inline-block; }
    .umock__logo { font-weight: 700; letter-spacing: 0.02em; }
    .umock__spacer { flex: 1; }
    .umock__pyramid { display: block; max-width: 100%; height: auto; }
    /* generic fallback for unknown types */
    .umock__x { padding: 0.5rem; border: 1px dashed #cbd5e1; border-radius: 4px;
      color: #64748b; font-size: 0.875rem; margin: 0.25rem 0; }
  </style>
</head>
<body>
  <header class="top-nav">
    <a href="index.html" class="nav-brand">__APP__</a>
    <div class="nav-controls">
      <div class="search-wrap">
        <input class="search-input" type="search" placeholder="搜尋文件...">
        <div class="search-results"></div>
      </div>
      __GH_LINK__
      <button class="sidebar-toggle" id="sidebarToggle" title="收合/展開側欄">☰</button>
    </div>
  </header>
  <div class="doc-page-banner">
    <p class="banner-breadcrumb">__BREADCRUMB__</p>
    <h1 class="banner-title">__BANNER__</h1>
  </div>
  <div class="page-wrapper">
    <aside class="sidebar" aria-label="文件導覽">
      __SIDEBAR__
    </aside>
    <div class="sidebar-resizer" id="sidebarResizer"></div>
    <main class="doc-content">__CONTENT__</main>
  </div>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({startOnLoad:true,theme:'default',
      flowchart:{curve:'basis',nodeSpacing:60,rankSpacing:80},
      er:{layoutDirection:'TD',minEntityWidth:100,fontSize:12},
      sequence:{actorMargin:60,messageMargin:30}});
  </script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-bash.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-yaml.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-sql.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-go.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-typescript.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-json.min.js"></script>
  <script src="assets/app.js"></script>
</body>
</html>"""

def esc(t):
    return _html.escape(str(t))

def _mermaid_fix_block(lines):
    """Fix mermaid v11 breaking patterns in flowchart/graph/sequenceDiagram/
    stateDiagram/classDiagram blocks."""
    if not lines:
        return lines
    first = next((l.strip() for l in lines if l.strip()), '')
    is_flowchart = bool(re.match(r'^(flowchart|graph)\b', first))
    is_sequence  = bool(re.match(r'^sequenceDiagram', first))
    is_state     = bool(re.match(r'^stateDiagram(-v2)?\b', first))
    is_class     = bool(re.match(r'^classDiagram\b', first))
    is_er        = bool(re.match(r'^erDiagram\b', first))
    if not (is_flowchart or is_sequence or is_state or is_class or is_er):
        return lines

    # ── Orientation directive 機械修：讓 wide > tall 圖盡量變 tall ──
    # R-1/R-2: flowchart/graph LR/RL → TD
    # R-3:     classDiagram 無 direction → 加 direction TB
    # R-4:     classDiagram direction LR → 改 TB
    # R-5:     erDiagram 無 direction → 加 direction TB
    if is_flowchart:
        lines = list(lines)
        for i, ln in enumerate(lines):
            m = re.match(r'^(\s*)(flowchart|graph)\s+(LR|RL)\b(.*)$', ln)
            if m:
                lines[i] = f'{m.group(1)}{m.group(2)} TD{m.group(4)}'
                break
    if is_class or is_er:
        lines = list(lines)
        # 找第一行非空、非註解的 first content 行（diagram type 那行之後）
        # 看有沒有 direction directive
        body_start = None
        for i, ln in enumerate(lines):
            if ln.strip() and not ln.lstrip().startswith('%%'):
                body_start = i
                break
        if body_start is not None:
            has_direction = False
            for j in range(body_start + 1, min(len(lines), body_start + 6)):
                m = re.match(r'^(\s*)direction\s+(TB|BT|LR|RL)\b', lines[j])
                if m:
                    has_direction = True
                    if m.group(2) in ('LR', 'RL'):
                        lines[j] = f'{m.group(1)}direction TB'
                    break
            if not has_direction:
                # 在 body_start 之後插入 direction TB
                indent = ''
                # 用 body_start+1 的縮排猜（如果有）
                if body_start + 1 < len(lines):
                    nxt = lines[body_start + 1]
                    indent_m = re.match(r'^(\s*)', nxt)
                    indent = indent_m.group(1) if indent_m else '    '
                lines.insert(body_start + 1, f'{indent}direction TB')

    def fix_flowchart_line(line):
        # Mermaid v11: unquoted [label] nodes cannot contain (, {, or nested [
        # Fix: wrap such labels in double quotes → ["label"]
        # Negative lookbehind (?<!\() avoids matching the inner [...] of ([...]) stadium shapes
        def quote_if_needed(m):
            content = m.group(1)
            # Already quoted — leave alone
            if content.startswith('"') and content.endswith('"'):
                return '[' + content + ']'
            # Cylinder shape [(...)] — valid in Mermaid v11, leave alone
            if content.startswith('(') and content.endswith(')'):
                return '[' + content + ']'
            # De-nest one level of inner brackets, keeping their text content
            clean = re.sub(r'\[([^\[\]]*)\]', lambda nm: nm.group(1), content)
            # If problematic chars exist, wrap entire label in double quotes
            if '(' in clean or '{' in clean or '[' in clean:
                return '["' + clean.replace('"', "'") + '"]'
            return '[' + content + ']'

        # Match [content] with optional one level of nesting; skip ([...]) stadium shapes
        line = re.sub(r'(?<!\()\[([^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*)\]', quote_if_needed, line)

        # Edge label |content| with special chars (parens / slash / semicolon / etc.)
        # → 改成 |"content"|
        def quote_edge_label(m):
            content = m.group(1)
            if content.startswith('"') and content.endswith('"'):
                return '|' + content + '|'
            if any(c in content for c in '()/;{}'):
                return '|"' + content.replace('"', "'") + '"|'
            return '|' + content + '|'
        line = re.sub(r'\|([^|]*)\|', quote_edge_label, line)
        return line

    def fix_sequence_line(line):
        # Mermaid v11: alt/else 分支內若 +/- 不平衡會 inactivate inactive 報錯。
        # 完全剝除 activation tracking：
        # - 箭頭後的 +/- 修飾（->>+X / -->>-X 等）
        # - 獨立 activate/deactivate 行
        # （犧牲 activation bar 視覺，換取整圖能 parse）
        line = re.sub(r'(--?>>?x?)([+-])(\w+)', r'\1\3', line)
        if re.match(r'^\s*(activate|deactivate)\s+\w+\s*$', line):
            return ''
        # Mermaid v11: ; in message text treated as statement separator
        msg = re.match(r'^(\s*\S.*?(?:->>|-->>|->x|-->x|->>|->|-->)\s*\S[^:]*:\s*)(.*)', line, re.DOTALL)
        if msg:
            prefix, message = msg.group(1), msg.group(2)
            message = message.replace(';', ',').replace('\\n', ' ')
            line = prefix + message
        # Note over X,Y: text — also strip ; in label
        note = re.match(r'^(\s*Note\s+(?:over|right of|left of)\s+[^:]+:\s*)(.*)', line)
        if note:
            prefix, message = note.group(1), note.group(2)
            message = message.replace(';', ',')
            line = prefix + message
        return line

    # Mermaid v11 stateDiagram-v2 內當 state 名會撞 grammar 的字（case-sensitive）
    # 只列實證會壞的——不要過度擴張，避免改到合法 keyword 位置
    _STATE_NAME_RESERVED = {'Default', 'default'}

    def fix_state_line(line):
        # Strip `entry:` / `exit:` keywords (UML concept, mermaid v11 不支援)
        if re.match(r'^\s*(entry|exit)\s*:', line):
            return ''
        # Rename 撞 grammar 的 state 名 → 加 _st 後綴
        # 只動 state-name position：state X / X --> / --> X / X :
        for bad in _STATE_NAME_RESERVED:
            esc = re.escape(bad)
            # state X
            line = re.sub(rf'(\bstate\s+){esc}\b', rf'\1{bad}_st', line)
            # X --> 或 --> X（state 轉換）
            line = re.sub(rf'\b{esc}(\s*-->)', rf'{bad}_st\1', line)
            line = re.sub(rf'(-->\s*){esc}\b', rf'\1{bad}_st', line)
            # X : (state description 行首)
            line = re.sub(rf'^(\s*){esc}(\s*:)', rf'\1{bad}_st\2', line)
        # Mermaid v11: ; in transition / state label treated as statement separator
        # — 仍須改成 ,
        # NOTE：早先有 `[...] → (...)` 跟 `{...} → (...)` 改寫，註解寫「mermaid
        # 把 [X] 當 state ref」。對 mermaid v11.14 經實機驗證為錯：
        # browser mermaid.run() 對 transition label 含 `[guard]` 是合法的，
        # 強改成 `(guard)` 反而產生 `event() (guard) /` 連續括號樣式，
        # mermaid v11 parser 渲染失敗（顯示「Syntax error in text」）。
        # → common fix：留 source 原 syntax，只做必要的 ; → , normalize。
        m = re.match(r'^(.*?(?:-->|state\s+\S+).*?:\s*)(.*)$', line)
        if m:
            prefix, label = m.group(1), m.group(2)
            label = label.replace(';', ',')
            line = prefix + label
        return line

    def fix_class_line(line):
        # Skip 開頭聲明、空行、註解
        s = line.strip()
        if not s or s.startswith('%%'):
            return line
        # M03: classDiagram member 內 {} 被當 STRUCT_STOP/OPEN_IN_STRUCT
        # 把不在配對 class { 開頭/結尾 的 { } 換成 ( )
        if not re.match(r'^\s*class\s+\S+\s*\{?\s*$', line) \
           and not re.match(r'^\s*\}\s*$', line):
            line = line.replace('{', '(').replace('}', ')')
        # M09: relationship target 包引號 + 泛型 "X~T~" → 純 X
        # X ..> "Y~T~" : label  →  X ..> Y : label
        line = re.sub(
            r'(\.\.>|-->|--\|>|\.\.\|>|\*--|\.\.|--)\s*"([^"~]+)~[^"]*~"',
            r'\1 \2',
            line,
        )
        return line

    def strip_flowchart_sequence_misuse(lines_in):
        """Stack-based strip of sequence-only blocks 誤用在 flowchart：
        - `par X` / `rect rgba(...)`：opener，整行剝
        - `and X`：sequence par 的分隔，剝
        - `end`：若對應到剝過的 opener 才剝；對應 subgraph 則保留
        """
        out = []
        stack = []   # 每個元素：'subgraph' (保留) 或 'strip' (要連同 end 一起剝)
        for ln in lines_in:
            s = ln.strip()
            if re.match(r'^par\b', s) or re.match(r'^rect\s+rgba\b', s):
                stack.append('strip')
                continue
            if re.match(r'^and\b', s) and stack and stack[-1] == 'strip':
                continue
            if re.match(r'^subgraph\b', s):
                stack.append('subgraph')
                out.append(ln)
                continue
            if s == 'end' or re.match(r'^end\s', s):
                if stack:
                    top = stack.pop()
                    if top == 'strip':
                        continue
                out.append(ln)
                continue
            out.append(ln)
        return out

    if is_flowchart:
        cleaned = strip_flowchart_sequence_misuse(lines)
        return [fix_flowchart_line(l) for l in cleaned]
    if is_sequence:
        return [fix_sequence_line(l) for l in lines]
    if is_state:
        per_line = [fix_state_line(l) for l in lines]
        # Post-pass: remove empty `state X { ... }` blocks. mermaid v11 browser
        # parser fails on empty blocks (only blank/comment lines between { and }).
        # This commonly happens after fix_state_line strips all entry:/exit: lines
        # within a state block. The `state X : description` companion line stays.
        out = []
        i = 0
        n = len(per_line)
        while i < n:
            ln = per_line[i]
            m = re.match(r'^(\s*)state\s+\S+\s*\{\s*$', ln)
            if m:
                # Find matching closing `}` (state blocks don't nest the same way
                # as flowchart subgraphs — just look for the next `}` at any indent).
                j = i + 1
                while j < n and not re.match(r'^\s*\}\s*$', per_line[j]):
                    j += 1
                if j < n:
                    body = per_line[i + 1:j]
                    non_empty = [
                        b for b in body
                        if b.strip() and not b.lstrip().startswith('%%')
                    ]
                    if not non_empty:
                        # Whole block is effectively empty → drop i..j inclusive.
                        i = j + 1
                        continue
            out.append(ln)
            i += 1
        return out
    if is_class:
        return [fix_class_line(l) for l in lines]
    return lines


# ─── UI Mock DSL ────────────────────────────────────────────────────────
# Stage ① of 11 — DSL parser → AST
#
# Grammar (informal):
#   block      = ident value? attrs* body?
#   value      = string | number | list
#   attrs      = ident ":" (string | number | bool | list)
#              | ident                         # bare flag → bool true
#   list       = "[" (item ("," item)*)? "]"
#   item       = string | number
#   body       = "{" block* "}"
#
# AST node:
#   {'type': str, 'attrs': dict, 'value': any|None, 'children': list}
# Top-level wrapped as {'type': 'root', ...}.

_UM_TOK_IDENT = 'ident'
_UM_TOK_STR = 'str'
_UM_TOK_NUM = 'num'
_UM_TOK_BOOL = 'bool'
_UM_TOK_LBRACE = '{'
_UM_TOK_RBRACE = '}'
_UM_TOK_LBRACK = '['
_UM_TOK_RBRACK = ']'
_UM_TOK_COLON = ':'
_UM_TOK_COMMA = ','


def _ui_mock_tokenize(text: str) -> list:
    """Tokenize DSL text. Returns list of (kind, value) tuples."""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        # whitespace
        if c.isspace():
            i += 1
            continue
        # comment to EOL
        if c == '#':
            while i < n and text[i] != '\n':
                i += 1
            continue
        # punctuation
        if c == '{':
            tokens.append((_UM_TOK_LBRACE, c)); i += 1; continue
        if c == '}':
            tokens.append((_UM_TOK_RBRACE, c)); i += 1; continue
        if c == '[':
            tokens.append((_UM_TOK_LBRACK, c)); i += 1; continue
        if c == ']':
            tokens.append((_UM_TOK_RBRACK, c)); i += 1; continue
        if c == ':':
            tokens.append((_UM_TOK_COLON, c)); i += 1; continue
        if c == ',':
            tokens.append((_UM_TOK_COMMA, c)); i += 1; continue
        # string
        if c == '"':
            j = i + 1
            buf = []
            while j < n:
                cj = text[j]
                if cj == '\\' and j + 1 < n:
                    nxt = text[j + 1]
                    if nxt == '"':
                        buf.append('"'); j += 2; continue
                    if nxt == '\\':
                        buf.append('\\'); j += 2; continue
                    if nxt == 'n':
                        buf.append('\n'); j += 2; continue
                    buf.append(nxt); j += 2; continue
                if cj == '"':
                    break
                buf.append(cj)
                j += 1
            if j >= n:
                raise ValueError(f'unterminated string at offset {i}')
            tokens.append((_UM_TOK_STR, ''.join(buf)))
            i = j + 1
            continue
        # number
        if c.isdigit() or (c == '-' and i + 1 < n and text[i + 1].isdigit()):
            j = i + 1
            while j < n and (text[j].isdigit() or text[j] == '.'):
                j += 1
            raw = text[i:j]
            num = float(raw) if '.' in raw else int(raw)
            tokens.append((_UM_TOK_NUM, num))
            i = j
            continue
        # identifier (kebab-case allowed)
        if c.isalpha() or c == '_':
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] in '-_'):
                j += 1
            ident = text[i:j]
            if ident == 'true':
                tokens.append((_UM_TOK_BOOL, True))
            elif ident == 'false':
                tokens.append((_UM_TOK_BOOL, False))
            else:
                tokens.append((_UM_TOK_IDENT, ident))
            i = j
            continue
        raise ValueError(f'unexpected char {c!r} at offset {i}')
    return tokens


def _ui_mock_parse_list(tokens: list, pos: int) -> tuple:
    """Parse [a, b, c] list. Returns (list_value, new_pos). pos points at '['."""
    assert tokens[pos][0] == _UM_TOK_LBRACK
    pos += 1
    items = []
    first = True
    while pos < len(tokens) and tokens[pos][0] != _UM_TOK_RBRACK:
        if not first:
            if tokens[pos][0] != _UM_TOK_COMMA:
                raise ValueError(f'expected "," in list, got {tokens[pos]}')
            pos += 1
        kind, val = tokens[pos]
        if kind not in (_UM_TOK_STR, _UM_TOK_NUM):
            raise ValueError(f'list items must be string or number, got {tokens[pos]}')
        items.append(val)
        pos += 1
        first = False
    if pos >= len(tokens):
        raise ValueError('unterminated list')
    return items, pos + 1  # consume ']'


def _ui_mock_is_flag_at(tokens: list, pos: int) -> bool:
    """An ident at `pos` is a bare flag iff its lookahead chain bottoms out at
    an "anchor" (LBRACE / RBRACE / end / keyed-attr) without hitting a value
    token (str/num/list) that would mean it actually starts a sibling block.
    """
    if pos + 1 >= len(tokens):
        return True
    nk, _ = tokens[pos + 1]
    if nk in (_UM_TOK_LBRACE, _UM_TOK_RBRACE):
        return True
    if nk == _UM_TOK_IDENT:
        # next ident is keyed attr (followed by ':') → current is flag
        if pos + 2 < len(tokens) and tokens[pos + 2][0] == _UM_TOK_COLON:
            return True
        # otherwise: only a flag if the next ident is also a flag (recursive)
        return _ui_mock_is_flag_at(tokens, pos + 1)
    # str / num / lbrack / colon / comma → ident starts new sibling
    return False


def _ui_mock_parse_block(tokens: list, pos: int) -> tuple:
    """Parse one block. Returns (node, new_pos)."""
    if pos >= len(tokens):
        raise ValueError('expected block, got EOF')
    kind, val = tokens[pos]
    if kind != _UM_TOK_IDENT:
        raise ValueError(f'expected identifier, got {tokens[pos]}')
    node = {'type': val, 'attrs': {}, 'value': None, 'children': []}
    pos += 1
    # Optional naked value (string | number | list)
    value_consumed = False
    if pos < len(tokens):
        k, v = tokens[pos]
        if k == _UM_TOK_STR or k == _UM_TOK_NUM:
            node['value'] = v
            pos += 1
            value_consumed = True
        elif k == _UM_TOK_LBRACK:
            lst, pos = _ui_mock_parse_list(tokens, pos)
            node['value'] = lst
            value_consumed = True
    # Attrs (zero or more): ident [':' value] OR bare flag.
    # After a naked value is consumed, only keyed attrs are accepted — a bare
    # ident at this point starts the next sibling block.
    while pos < len(tokens):
        k, v = tokens[pos]
        if k != _UM_TOK_IDENT:
            break
        if pos + 1 < len(tokens) and tokens[pos + 1][0] == _UM_TOK_COLON:
            # ident ':' value
            attr_key = v
            pos += 2  # skip ident, colon
            if pos >= len(tokens):
                raise ValueError(f'expected value for attr {attr_key}')
            vk, vv = tokens[pos]
            if vk in (_UM_TOK_STR, _UM_TOK_NUM, _UM_TOK_BOOL):
                node['attrs'][attr_key] = vv
                pos += 1
            elif vk == _UM_TOK_LBRACK:
                lst, pos = _ui_mock_parse_list(tokens, pos)
                node['attrs'][attr_key] = lst
            elif vk == _UM_TOK_IDENT:
                # bare ident as enum value (variant:primary)
                node['attrs'][attr_key] = vv
                pos += 1
            else:
                raise ValueError(f'unexpected attr value {tokens[pos]}')
            continue
        # Bare flag candidate. Two preconditions:
        #   (1) No naked value has been consumed yet — once a value is set,
        #       any bare ident is the next sibling block.
        #   (2) Disambiguation lookahead must "anchor" at LBRACE/RBRACE/EOF/
        #       keyed-attr, not a str/num/list (which would mean sibling).
        if value_consumed:
            break
        if _ui_mock_is_flag_at(tokens, pos):
            node['attrs'][v] = True
            pos += 1
            continue
        break  # ident starts next sibling block; let outer loop handle it
    # Optional body
    if pos < len(tokens) and tokens[pos][0] == _UM_TOK_LBRACE:
        pos += 1
        while pos < len(tokens) and tokens[pos][0] != _UM_TOK_RBRACE:
            child, pos = _ui_mock_parse_block(tokens, pos)
            node['children'].append(child)
        if pos >= len(tokens):
            raise ValueError('unterminated block (missing "}")')
        pos += 1  # consume '}'
    return node, pos


def _ui_mock_dsl_parse(text: str) -> dict:
    """Parse DSL text into AST root.

    Top-level always wraps multiple blocks under {'type': 'root'}.
    Empty / whitespace / comment-only input → root with no children.
    """
    tokens = _ui_mock_tokenize(text)
    root = {'type': 'root', 'attrs': {}, 'value': None, 'children': []}
    pos = 0
    while pos < len(tokens):
        node, pos = _ui_mock_parse_block(tokens, pos)
        root['children'].append(node)
    return root


# ─── UI Mock DSL renderer ──────────────────────────────────────────────
# Stage ② — AST → HTML for the 12 basic primitives + utilities.
# Layered-arch (→ mermaid) and pyramid (→ SVG) are stages ③–④.

def _um_esc(s) -> str:
    """HTML-escape a value (str/int/float/bool/None → safe string)."""
    if s is None:
        return ''
    if isinstance(s, bool):
        return 'true' if s else 'false'
    return (str(s)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def _um_render_children(node) -> str:
    return ''.join(_ui_mock_render_node(c) for c in node.get('children', []))


def _um_value_text(node) -> str:
    """Get node value as plain text (escaped). Lists joined by space."""
    v = node.get('value')
    if v is None:
        return ''
    if isinstance(v, list):
        return ' '.join(_um_esc(x) for x in v)
    return _um_esc(v)


def _um_attr(node, key, default=''):
    v = node.get('attrs', {}).get(key, default)
    return v


# ─── primitive renderers ─────────────────────────────────────────────────

def _um_r_page(n):
    title = _um_esc(_um_attr(n, 'title'))
    title_html = f'<div class="umock__page-title">{title}</div>' if title else ''
    return f'<div class="umock umock__page">{title_html}{_um_render_children(n)}</div>'


def _um_r_modal(n):
    title = _um_esc(_um_attr(n, 'title'))
    closable = _um_attr(n, 'closable', False)
    close_html = '<span class="umock__modal-close" aria-hidden="true">×</span>' if closable else ''
    return (
        '<div class="umock umock__modal">'
        f'<div class="umock__modal-titlebar"><span class="umock__modal-title">{title}</span>{close_html}</div>'
        f'<div class="umock__modal-body">{_um_render_children(n)}</div>'
        '</div>'
    )


def _um_r_navbar(n):
    return f'<div class="umock__navbar">{_um_render_children(n)}</div>'


def _um_r_sidenav(n):
    return f'<div class="umock__sidenav">{_um_render_children(n)}</div>'


def _um_r_section(n):
    title = _um_esc(_um_attr(n, 'title'))
    sub = _um_esc(_um_attr(n, 'subtitle'))
    title_html = f'<h3 class="umock__section-title">{title}</h3>' if title else ''
    sub_html = f'<div class="umock__section-subtitle">{sub}</div>' if sub else ''
    return (
        '<section class="umock__section">'
        f'{title_html}{sub_html}'
        f'<div class="umock__section-body">{_um_render_children(n)}</div>'
        '</section>'
    )


def _um_r_table(n):
    cols = _um_attr(n, 'columns', []) or []
    head = '<thead><tr>' + ''.join(f'<th>{_um_esc(c)}</th>' for c in cols) + '</tr></thead>'
    body_rows = []
    for child in n.get('children', []):
        if child.get('type') != 'row':
            continue
        cells = child.get('value') or []
        if not isinstance(cells, list):
            cells = [cells]
        body_rows.append('<tr>' + ''.join(f'<td>{_um_esc(c)}</td>' for c in cells) + '</tr>')
    body = '<tbody>' + ''.join(body_rows) + '</tbody>'
    return f'<table class="umock__table">{head}{body}</table>'


def _um_r_field(n):
    label = _um_esc(_um_attr(n, 'label'))
    required = _um_attr(n, 'required', False)
    req_mark = ' <span class="umock__field-required" aria-label="required">*</span>' if required else ''
    label_html = f'<label class="umock__field-label">{label}{req_mark}</label>' if label else ''
    return (
        '<div class="umock__field">'
        f'{label_html}'
        f'<div class="umock__field-body">{_um_render_children(n)}</div>'
        '</div>'
    )


def _um_r_button(n):
    variant = _um_esc(_um_attr(n, 'variant', 'default'))
    label = _um_value_text(n) or 'Button'
    return (
        f'<button type="button" tabindex="-1" '
        f'class="umock__btn umock__btn--{variant}">{label}</button>'
    )


def _um_r_badge(n):
    status = _um_esc(_um_attr(n, 'status', 'default'))
    label = _um_value_text(n)
    return f'<span class="umock__badge umock__badge--{status}">{label}</span>'


def _um_r_input(n):
    typ = _um_esc(_um_attr(n, 'type', 'text'))
    placeholder = _um_esc(_um_attr(n, 'placeholder'))
    maxlen = _um_attr(n, 'maxlength')
    maxlen_attr = f' maxlength="{_um_esc(maxlen)}"' if maxlen != '' and maxlen is not None else ''
    return (
        f'<input class="umock__input" type="{typ}" '
        f'placeholder="{placeholder}"{maxlen_attr} tabindex="-1" readonly>'
    )


def _um_r_code_block(n):
    lang = _um_esc(_um_attr(n, 'language', ''))
    inner = _um_value_text(n) or _um_render_children(n)
    if lang:
        # With language: let Prism syntax-highlight via class="language-X"
        return (
            f'<pre class="umock__code">'
            f'<code class="language-{lang}">{inner}</code>'
            '</pre>'
        )
    # No language: skip <code class=""> wrapper to avoid Prism interference
    # that fades inline rendering (Prism's tomorrow theme + empty class
    # triggers text-shadow + transparent token color on plain text).
    return f'<pre class="umock__code">{inner}</pre>'


def _um_r_hint(n):
    cls = _um_align_class(n, 'umock__hint')
    return f'<div class="{cls}">{_um_value_text(n)}</div>'


# ─── utility/container renderers ─────────────────────────────────────────

def _um_r_actions(n):
    cls = _um_align_class(n, 'umock__actions')
    return f'<div class="{cls}">{_um_render_children(n)}</div>'


def _um_align_class(node, base: str) -> str:
    """Return 'base' or 'base base--center' / 'base base--right' depending
    on node's `align` attr (default 'left' = no modifier)."""
    align = _um_attr(node, 'align', '')
    if align in ('center', 'right'):
        return f'{base} {base}--{align}'
    return base


def _um_r_info(n):
    cls = _um_align_class(n, 'umock__info')
    return f'<div class="{cls}">{_um_value_text(n)}</div>'


def _um_r_text(n):
    """Plain body text row inside a UI mock (no decoration, monospace,
    preserve whitespace). Used for ASCII screen lines that don't carry
    semantic markers like `ⓘ` or `helper:`. Outer alignment via
    `align` attr (default left)."""
    cls = _um_align_class(n, 'umock__text')
    return f'<div class="{cls}">{_um_value_text(n)}</div>'


def _um_r_spacer(n):
    return '<div class="umock__spacer" aria-hidden="true"></div>'


def _um_r_avatar(n):
    return '<div class="umock__avatar" aria-hidden="true"></div>'


def _um_r_tabs(n):
    items = n.get('value') or []
    if not isinstance(items, list):
        items = [items]
    parts = ''.join(f'<span class="umock__tab">{_um_esc(t)}</span>' for t in items)
    return f'<div class="umock__tabs">{parts}</div>'


def _um_r_search(n):
    placeholder = _um_esc(_um_attr(n, 'placeholder'))
    return (
        f'<input class="umock__search" type="search" '
        f'placeholder="{placeholder}" tabindex="-1" readonly>'
    )


def _um_r_card(n):
    title = _um_esc(_um_attr(n, 'title'))
    title_align = _um_attr(n, 'title_align', '')
    title_cls = 'umock__card-title'
    if title_align in ('center', 'right'):
        title_cls = f'umock__card-title umock__card-title--{title_align}'
    title_html = f'<div class="{title_cls}">{title}</div>' if title else ''
    return f'<div class="umock__card">{title_html}{_um_render_children(n)}</div>'


def _um_r_divider(n):
    return '<hr class="umock__divider">'


def _um_r_meta_line(n):
    return f'<div class="umock__meta-line">{_um_value_text(n)}</div>'


def _um_r_row(n):
    # `row` has dual role: inside table = data row (handled in _um_r_table);
    # standalone (inside card etc.) = horizontal flex container.
    val = n.get('value')
    if isinstance(val, list):
        # Treated as data row when not inside a table
        cells = ''.join(f'<span class="umock__row-cell">{_um_esc(c)}</span>' for c in val)
        return f'<div class="umock__row">{cells}</div>'
    return f'<div class="umock__row">{_um_render_children(n)}</div>'


def _um_r_label(n):
    return f'<span class="umock__label">{_um_value_text(n)}</span>'


def _um_r_logo(n):
    return f'<span class="umock__logo">{_um_value_text(n)}</span>'


def _um_r_item(n):
    return f'<div class="umock__item">{_um_value_text(n) or _um_render_children(n)}</div>'


def _um_r_pagination(n):
    total = _um_attr(n, 'total', '')
    page = _um_attr(n, 'page', '')
    of = _um_attr(n, 'of', '')
    summary = []
    if page != '' and of != '':
        summary.append(f'{_um_esc(page)} / {_um_esc(of)}')
    if total != '':
        summary.append(f'total {_um_esc(total)}')
    return f'<div class="umock__pagination">{" · ".join(summary)}</div>'


def _um_r_filter_bar(n):
    return f'<div class="umock__filter-bar">{_um_render_children(n)}</div>'


def _um_mermaid_label(text: str) -> str:
    """Escape a string for use inside mermaid `["..."]` node label.
    Mermaid treats `"` as quote and `<br/>` as line break."""
    if text is None:
        return ''
    # Strip raw quotes; mermaid doesn't have an escape for them inside `[" "]`.
    return (str(text)
            .replace('"', "'")
            .replace('\n', '<br/>'))


def _um_r_layered_arch(n):
    """Render layered-arch as mermaid `flowchart TB` inside diagram-container.

    Children stream: alternating `layer { ... }` and `flow-down "..."` /
    `flow-up "..."`. Adjacent layers without an explicit flow get a default
    plain arrow.
    """
    layers = []      # list of (id, label_text)
    flows = []       # list of (from_idx, to_idx, label, kind) — flow between layers
    pending_flow = None  # tuple (label, kind) waiting to be attached
    for child in n.get('children', []):
        ctype = child.get('type')
        if ctype == 'layer':
            label = child.get('value') or ''
            details = []
            for sub in child.get('children', []):
                if sub.get('type') == 'detail':
                    details.append(str(sub.get('value') or ''))
            full = label
            if details:
                full = label + '<br/>' + '<br/>'.join(details)
            layers.append(('L' + str(len(layers)), full))
            if len(layers) >= 2:
                from_i = len(layers) - 2
                to_i = len(layers) - 1
                if pending_flow is not None:
                    label_, kind_ = pending_flow
                    pending_flow = None
                else:
                    label_, kind_ = '', 'down'
                flows.append((from_i, to_i, label_, kind_))
        elif ctype in ('flow-down', 'flow-up'):
            kind = 'down' if ctype == 'flow-down' else 'up'
            label = str(child.get('value') or '')
            pending_flow = (label, kind)
    # Build mermaid source
    lines = ['flowchart TB']
    for nid, lbl in layers:
        lines.append(f'    {nid}["{_um_mermaid_label(lbl)}"]')
    for from_i, to_i, label, kind in flows:
        a = layers[from_i][0]
        b = layers[to_i][0]
        # flow-down: top → bottom (a → b). flow-up: bottom → top (b → a).
        src, dst = (a, b) if kind == 'down' else (b, a)
        if label:
            lines.append(f'    {src} -->|{_um_mermaid_label(label)}| {dst}')
        else:
            lines.append(f'    {src} --> {dst}')
    # Run through the same v11-fix pipeline as user-authored mermaid blocks
    # (see fix_flowchart_line edge-label quoting at L604-609). Without this,
    # auto-generated edge labels containing `()` / `/` etc. break mermaid v11.
    fixed = _mermaid_fix_block(lines)
    body = '\n'.join(fixed)
    return (
        '<div class="diagram-container">'
        f'<pre class="mermaid">\n{body}\n</pre>'
        '</div>'
    )


def _um_r_pyramid(n):
    """Render pyramid (e.g., testing pyramid) as inline SVG.

    Top layer is narrowest; bottom is widest. Each layer is a trapezoid
    polygon with three lines of text inside (label / pct / detail).
    """
    layers = []
    for child in n.get('children', []):
        if child.get('type') != 'layer':
            continue
        layers.append({
            'label': str(child.get('value') or ''),
            'pct': str(child.get('attrs', {}).get('pct', '') or ''),
            'detail': str(child.get('attrs', {}).get('detail', '') or ''),
        })
    n_layers = len(layers)
    if n_layers == 0:
        return (
            '<div class="diagram-container">'
            '<svg class="umock__pyramid" viewBox="0 0 600 80" '
            'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="empty pyramid">'
            '</svg></div>'
        )
    # Geometry
    svg_w = 600
    layer_h = 80
    svg_h = layer_h * n_layers + 20
    cx = svg_w / 2
    top_w = 220        # top layer base width
    bottom_w = 540     # bottom layer base width
    if n_layers == 1:
        widths = [(top_w + bottom_w) / 2]
    else:
        widths = [
            top_w + (bottom_w - top_w) * (i / (n_layers - 1))
            for i in range(n_layers)
        ]
    # Per-layer fill (light → dark cool palette)
    palette = [
        '#dbeafe', '#bfdbfe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb',
    ]
    elements = []
    for i, layer in enumerate(layers):
        top_y = 10 + i * layer_h
        bot_y = top_y + layer_h - 4
        # The polygon: trapezoid with this layer's width at bottom and the
        # previous layer's width at top — produces continuous pyramid sides.
        if i == 0:
            top_left_x = cx - widths[i] / 2 + 30  # narrow apex top
            top_right_x = cx + widths[i] / 2 - 30
        else:
            top_left_x = cx - widths[i - 1] / 2
            top_right_x = cx + widths[i - 1] / 2
        bot_left_x = cx - widths[i] / 2
        bot_right_x = cx + widths[i] / 2
        pts = (
            f'{top_left_x:.1f},{top_y:.1f} '
            f'{top_right_x:.1f},{top_y:.1f} '
            f'{bot_right_x:.1f},{bot_y:.1f} '
            f'{bot_left_x:.1f},{bot_y:.1f}'
        )
        fill = palette[min(i, len(palette) - 1)]
        elements.append(
            f'<polygon points="{pts}" fill="{fill}" stroke="#1e40af" stroke-width="1.5"/>'
        )
        # Text inside trapezoid
        text_y = (top_y + bot_y) / 2
        label = _um_esc(layer['label'])
        pct = _um_esc(layer['pct'])
        detail = _um_esc(layer['detail'])
        # Label (bold, slightly above center)
        if label:
            elements.append(
                f'<text x="{cx:.1f}" y="{text_y - 14:.1f}" '
                'text-anchor="middle" font-family="system-ui,sans-serif" '
                'font-size="14" font-weight="600" fill="#0f172a">'
                f'{label}</text>'
            )
        # Pct (smaller)
        if pct:
            elements.append(
                f'<text x="{cx:.1f}" y="{text_y + 4:.1f}" '
                'text-anchor="middle" font-family="system-ui,sans-serif" '
                'font-size="12" fill="#1e3a8a">'
                f'{pct}</text>'
            )
        # Detail (bottom line, gray)
        if detail:
            elements.append(
                f'<text x="{cx:.1f}" y="{text_y + 22:.1f}" '
                'text-anchor="middle" font-family="system-ui,sans-serif" '
                'font-size="11" fill="#475569">'
                f'{detail}</text>'
            )
    svg = (
        f'<svg class="umock__pyramid" viewBox="0 0 {svg_w} {svg_h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="pyramid">'
        + ''.join(elements) +
        '</svg>'
    )
    return f'<div class="diagram-container">{svg}</div>'


# ─── unknown / generic ───────────────────────────────────────────────────

def _um_r_generic(n):
    """Silent fallback for unrecognized types (per user spec: no warnings)."""
    typ = _um_esc(n.get('type', 'unknown'))
    val = _um_value_text(n)
    children = _um_render_children(n)
    if val and not children:
        return f'<div class="umock__x" data-type="{typ}">{val}</div>'
    if children and not val:
        return f'<div class="umock__x" data-type="{typ}">{children}</div>'
    return f'<div class="umock__x" data-type="{typ}">{val}{children}</div>'


_UM_DISPATCH = {
    # 12 basic primitives
    'page': _um_r_page,
    'modal': _um_r_modal,
    'navbar': _um_r_navbar,
    'sidenav': _um_r_sidenav,
    'section': _um_r_section,
    'table': _um_r_table,
    'field': _um_r_field,
    'button': _um_r_button,
    'badge': _um_r_badge,
    'input': _um_r_input,
    'code-block': _um_r_code_block,
    'hint': _um_r_hint,
    # utilities
    'actions': _um_r_actions,
    'info': _um_r_info,
    'text': _um_r_text,
    'spacer': _um_r_spacer,
    'avatar': _um_r_avatar,
    'tabs': _um_r_tabs,
    'search': _um_r_search,
    'card': _um_r_card,
    'divider': _um_r_divider,
    'meta-line': _um_r_meta_line,
    'row': _um_r_row,
    'label': _um_r_label,
    'logo': _um_r_logo,
    'item': _um_r_item,
    'pagination': _um_r_pagination,
    'filter-bar': _um_r_filter_bar,
    # edge-case primitives
    'layered-arch': _um_r_layered_arch,
    'pyramid': _um_r_pyramid,
}


def _ui_mock_render_node(node) -> str:
    """Dispatch render for one AST node."""
    typ = node.get('type', '')
    if typ == 'root':
        return _um_render_children(node)
    fn = _UM_DISPATCH.get(typ)
    if fn:
        return fn(node)
    return _um_r_generic(node)


def _ui_mock_render(ast) -> str:
    """Render top-level AST root → HTML string."""
    return _ui_mock_render_node(ast)


# ─── UI Mock ASCII parser (stage ⑤) ─────────────────────────────────────
# Heuristic detection of ASCII box-drawing UI mockups → same AST shape as
# the DSL parser. Failure is silent (returns None); caller is expected to
# fall back to <pre> for unrecognized blocks.
#
# Stage ⑤: outer frame, modal-vs-card classification, title, sections,
#          buttons in action rows, badges (●/○).
# Stages ⑥–⑧ extend with: 2-column split, tables, inner boxes, layered-
# arch and pyramid detection.

_UM_BOX_CHARS = set('┌┐└┘├┤┬┴┼─│┏┓┗┛┃━')


def _um_ascii_outer_align(line: str) -> str:
    """Detect a text line's outer alignment within its `│ ... │` borders.

    Returns 'center' / 'left' / 'right' based on leading vs trailing
    whitespace inside the outer pipe boundary:
      - L (leading spaces) >= 4 AND R (trailing) >= 4 → 'center'
      - L >= 4 AND R == 0 → 'right'
      - else → 'left'

    A line without `│` boundaries is treated as having the whole line as
    its inner content (no surrounding frame).
    """
    first = line.find('│')
    if first == -1:
        first = line.find('┃')
    last = line.rfind('│')
    if last <= first:
        last2 = line.rfind('┃')
        if last2 > first:
            last = last2
    if first == -1 or last <= first:
        inner = line
    else:
        inner = line[first + 1:last]
    stripped = inner.strip()
    if not stripped:
        return 'left'
    leading = len(inner) - len(inner.lstrip(' '))
    trailing = len(inner) - len(inner.rstrip(' '))
    if leading >= 4 and trailing >= 4:
        return 'center'
    if leading >= 4 and trailing == 0:
        return 'right'
    return 'left'


def _um_ascii_strip_pipes(line: str) -> str:
    """Extract content between first and last │ (or ┃) on a line.

    A2 fix — single-pipe handling:
      - pipe at start (only whitespace before) → strip leading pipe
      - pipe at end   (only whitespace after)  → strip trailing pipe
      - pipe in middle (mock author's separator) → keep line unchanged
    """
    first = -1
    last = -1
    for i, c in enumerate(line):
        if c in '│┃':
            if first < 0:
                first = i
            last = i
    if first < 0:
        return line
    if last > first:
        return line[first + 1:last]
    # single pipe — disambiguate by surrounding whitespace
    before = line[:first]
    after = line[first + 1:]
    if before.strip() == '':
        return after
    if after.strip() == '':
        return before
    return line


def _um_ascii_is_divider_line(line: str) -> bool:
    """True iff line is a section divider like ├────...────┤."""
    if '├' not in line or '┤' not in line:
        return False
    # Between ├ and ┤, only ─ ┬ ┴ ┼ are allowed
    a = line.index('├')
    b = line.rindex('┤')
    middle = line[a + 1:b]
    return all(c in '─┬┴┼' for c in middle) and bool(middle)


def _um_ascii_split_segments(interior_lines: list) -> list:
    """Split interior (between top and bottom of frame) by ├──┤ dividers.
    Returns list-of-list-of-content-strings (one list per segment)."""
    segments = []
    cur = []
    for line in interior_lines:
        if _um_ascii_is_divider_line(line):
            segments.append(cur)
            cur = []
            continue
        cur.append(_um_ascii_strip_pipes(line))
    segments.append(cur)
    return segments


_UM_BUTTON_RE = __import__('re').compile(r'\[([^\]\n]+)\]')


def _um_ascii_parse_segment_actions(segment_lines: list):
    """If segment is a single 'actions row' (only [labels] + variant hints),
    return (True, [(label, variant), ...]).  Else (False, [])."""
    import re as _re
    joined = ' '.join(s.strip() for s in segment_lines if s.strip())
    if not joined:
        return False, []
    buttons = _UM_BUTTON_RE.findall(joined)
    if not buttons:
        return False, []
    non_button = _UM_BUTTON_RE.sub('', joined)
    # Strip variant hints in （...） parens
    non_button_clean = _re.sub(r'[（(][^）)]*[）)]', '', non_button).strip()
    if non_button_clean:
        return False, []
    # Parse variants per button
    out = []
    for m in _UM_BUTTON_RE.finditer(joined):
        label = m.group(1).strip()
        after = joined[m.end():]
        vm = _re.match(r'\s*[（(]([^）)]+)[）)]', after)
        variant = 'default'
        if vm:
            hint = vm.group(1).lower()
            if 'primary' in hint or '主' in hint:
                variant = 'primary'
            elif 'danger' in hint or '危險' in hint:
                variant = 'danger'
            elif 'secondary' in hint or '次' in hint:
                variant = 'secondary'
        out.append((label, variant))
    return True, out


def _um_ascii_extract_table(segment_lines: list):
    """Look for a contiguous run of >=2 lines with same number of `|` ASCII
    pipes (not the box `│`). If found, return (table_node, leftover_lines).
    Otherwise (None, segment_lines)."""
    # Find runs
    pipe_counts = []
    for line in segment_lines:
        # Count `|` not inside box drawing chars; but since we already stripped
        # outer `│`, any `|` in this content is an ASCII pipe.
        pipe_counts.append(line.count('|'))
    # Find first run of >=2 consecutive lines with same count >=1
    n = len(segment_lines)
    best_start = -1
    best_end = -1
    best_count = 0
    for i in range(n):
        if pipe_counts[i] < 1:
            continue
        j = i + 1
        while j < n and pipe_counts[j] == pipe_counts[i] and pipe_counts[j] >= 1:
            j += 1
        # require at least 2 lines (1 header + 1 data)
        if j - i >= 2 and (j - i) > (best_end - best_start):
            best_start, best_end, best_count = i, j, pipe_counts[i]
    if best_start < 0:
        return None, segment_lines
    rows_text = segment_lines[best_start:best_end]
    # Header is first row; data are subsequent
    header_cells = [c.strip() for c in rows_text[0].split('|')]
    data_rows = []
    for r in rows_text[1:]:
        data_rows.append([c.strip() for c in r.split('|')])
    table_node = {
        'type': 'table',
        'attrs': {'columns': header_cells},
        'value': None,
        'children': [
            {'type': 'row', 'attrs': {}, 'value': cells, 'children': []}
            for cells in data_rows
        ],
    }
    leftover = segment_lines[:best_start] + segment_lines[best_end:]
    return table_node, leftover


def _um_ascii_extract_inner_boxes(segment_lines: list, taken_title_text: str = ''):
    """Find nested ┌──┐ ... └──┘ boxes inside a segment. For each, build:
      - input or code-block node based on content shape
      - K9-b: if a top-border line has ≥ 2 ┌ chars (parallel boxes side-by-side
        on same row), parse each box independently by column ranges. If each
        contains only short single-line text → emit `actions { button×N }`.
        Else emit N independent boxes.
      - if preceded by a label line (last non-blank line before the box),
        wrap the box in a `field { label, required?, child=box }` node and
        consume the label line too
      - K9-a: skip label lines whose stripped text equals `taken_title_text`
        (already consumed as outer card-title)
    Returns list of (anchor_idx, last_idx, node) tuples sorted by anchor.
    """
    out = []
    n = len(segment_lines)
    consumed = set()
    i = 0
    while i < n:
        line = segment_lines[i]
        # K9-b: parallel-box row detection (≥ 2 ┌ on same line)
        if line.count('┌') >= 2:
            # Find matching bottom row: ≥ 2 └ on a later line
            box_end = -1
            for j in range(i + 1, n):
                if segment_lines[j].count('└') >= 2:
                    box_end = j
                    break
            if box_end < 0:
                i += 1
                continue
            # Walk top border, collect each [start, end] col range (┌ → ┐)
            top = line
            col_ranges = []
            jj = 0
            while jj < len(top):
                if top[jj] == '┌':
                    start = jj
                    kk = jj + 1
                    while kk < len(top) and top[kk] != '┐':
                        kk += 1
                    if kk >= len(top):
                        break
                    col_ranges.append((start, kk))
                    jj = kk + 1
                else:
                    jj += 1
            # Extract per-box content lines using col ranges
            box_contents = [[] for _ in col_ranges]
            for k in range(i + 1, box_end):
                row = segment_lines[k]
                for ci, (s, e) in enumerate(col_ranges):
                    if s + 1 < len(row):
                        cell = row[s + 1:min(e, len(row))].strip().strip('│').strip()
                        if cell:
                            box_contents[ci].append(cell)
            # Heuristic: each box has only ≤ 1 short line (≤ 16 chars,
            # no `=`, not ALL_CAPS const) → buttons; else → independent boxes
            def _looks_like_button(lines):
                if len(lines) != 1:
                    return False
                txt = lines[0]
                if len(txt) > 24:
                    return False
                if '=' in txt:
                    return False
                if re.fullmatch(r'[A-Z][A-Z0-9_]*', txt):
                    return False
                return True

            all_buttons = all(_looks_like_button(bc) for bc in box_contents) and len(box_contents) >= 2
            if all_buttons:
                children = []
                for bc in box_contents:
                    label = bc[0]
                    children.append({
                        'type': 'button', 'attrs': {},
                        'value': label, 'children': [],
                    })
                # K9 align: detect row's outer alignment from the top
                # border line's leading/trailing whitespace
                row_align = _um_ascii_outer_align(line)
                actions_attrs = {}
                if row_align != 'left':
                    actions_attrs['align'] = row_align
                node = {
                    'type': 'actions', 'attrs': actions_attrs, 'value': None,
                    'children': children,
                }
                out.append((i, box_end, node))
                for k in range(i, box_end + 1):
                    consumed.add(k)
                i = box_end + 1
                continue
            # Else: emit N independent boxes (each input/code-block, no label)
            for ci, bc in enumerate(box_contents):
                if not bc:
                    continue
                joined_txt = ' '.join(bc)
                is_code = len(bc) >= 2 or any(c in joined_txt for c in ('{', '}', '"', '[', ']'))
                if is_code:
                    sub = {'type': 'code-block', 'attrs': {},
                           'value': '\n'.join(bc), 'children': []}
                else:
                    sub = {'type': 'input',
                           'attrs': {'placeholder': joined_txt} if joined_txt else {},
                           'value': None, 'children': []}
                out.append((i, box_end, sub))
            for k in range(i, box_end + 1):
                consumed.add(k)
            i = box_end + 1
            continue
        # ── Single-box path (original logic) ─────────────────────────────
        if '┌' in line and '┐' in line and line.index('┌') < line.rindex('┐'):
            # Find matching └──┘ on a later line
            box_end = -1
            for j in range(i + 1, n):
                if '└' in segment_lines[j] and '┘' in segment_lines[j]:
                    box_end = j
                    break
            if box_end < 0:
                i += 1
                continue
            # Content between box top and bottom; strip inner │ pipes
            content_lines = [
                _um_ascii_strip_pipes(segment_lines[k]).rstrip()
                for k in range(i + 1, box_end)
            ]
            non_empty = [l for l in content_lines if l.strip()]
            # Heuristic: code-block iff multi-line OR has braces/quotes
            joined = ' '.join(non_empty)
            is_code = len(non_empty) >= 2 or any(
                c in joined for c in ('{', '}', '"', '[', ']')
            )
            if is_code:
                box_node = {
                    'type': 'code-block', 'attrs': {},
                    'value': '\n'.join(content_lines).strip('\n'),
                    'children': [],
                }
            else:
                placeholder = ' '.join(non_empty).strip()
                attrs = {'placeholder': placeholder} if placeholder else {}
                box_node = {
                    'type': 'input', 'attrs': attrs,
                    'value': None, 'children': [],
                }
            # Look for a label line (immediate previous non-blank, not consumed)
            # K9-a: also skip if the candidate label equals an already-taken
            # outer card-title (avoid duplicate title in field-label)
            label_idx = -1
            for k in range(i - 1, -1, -1):
                if k in consumed:
                    break
                if segment_lines[k].strip():
                    candidate = segment_lines[k].strip()
                    if taken_title_text and candidate == taken_title_text:
                        # Skip this candidate; don't take an earlier one as label
                        # (the box just won't have a field-label wrapper).
                        break
                    label_idx = k
                    break
            anchor = label_idx if label_idx >= 0 else i
            if label_idx >= 0:
                label_text = segment_lines[label_idx].strip()
                required = False
                if label_text.endswith('*'):
                    required = True
                    label_text = label_text.rstrip('*').strip()
                for marker in ('（必填）', '(必填)'):
                    if marker in label_text:
                        required = True
                        label_text = label_text.replace(marker, '').strip()
                attrs = {'label': label_text}
                if required:
                    attrs['required'] = True
                node = {
                    'type': 'field', 'attrs': attrs,
                    'value': None, 'children': [box_node],
                }
            else:
                node = box_node
            out.append((anchor, box_end, node))
            for k in range(min(anchor, i), box_end + 1):
                consumed.add(k)
            i = box_end + 1
            continue
        i += 1
    return out, consumed


def _um_ascii_parse_segment_content(segment_lines: list, taken_title_text: str = ''):
    """Extract table + nested boxes + form rows + hints + badges + text
    + trailing action row from a non-action segment.
    Returns list of AST child nodes.
    K9-a: `taken_title_text` is forwarded to `_um_ascii_extract_inner_boxes`
    so a candidate field-label that equals the outer card-title is skipped.
    """
    import re as _re
    # Detect trailing action row (last non-empty line is all-buttons + hints)
    trailing_actions = None
    for k in range(len(segment_lines) - 1, -1, -1):
        if not segment_lines[k].strip():
            continue
        is_actions, btns = _um_ascii_parse_segment_actions([segment_lines[k]])
        if is_actions:
            trailing_actions = btns
            segment_lines = segment_lines[:k]
        break
    table_node, segment_lines = _um_ascii_extract_table(segment_lines)
    children = []
    if table_node:
        children.append(table_node)
    inner_boxes, consumed = _um_ascii_extract_inner_boxes(segment_lines, taken_title_text)
    inner_boxes.sort(key=lambda t: t[0])
    box_at = {anchor: (last, node) for anchor, last, node in inner_boxes}
    text_parts = []

    def flush_text():
        # Generic rule: each non-blank line in `text_parts` becomes its own
        # node, preserving line structure + outer alignment from source ASCII.
        # text_parts holds (text, align) tuples where `align` is the outer
        # alignment detected from leading/trailing whitespace within `│ ... │`.
        # Plain lines → 'text' node (monospace, no decoration).
        # `helper:` / `ⓘ` markers → 'hint' / 'info' (intentional banners).
        if not text_parts:
            return
        for raw, align in text_parts:
            line = raw.strip()
            if not line:
                continue
            attrs = {'align': align} if align != 'left' else {}
            m = _re.match(r'^\s*helper\s*[：:]\s*(.+)$', line, _re.IGNORECASE)
            if m:
                children.append({'type': 'hint', 'attrs': attrs,
                                 'value': m.group(1).strip(), 'children': []})
                continue
            m = _re.match(r'^\s*ⓘ\s*(.+)$', line)
            if m:
                children.append({'type': 'info', 'attrs': attrs,
                                 'value': m.group(1).strip(), 'children': []})
                continue
            children.append({'type': 'text', 'attrs': attrs,
                             'value': line, 'children': []})
        text_parts.clear()

    i = 0
    n = len(segment_lines)
    while i < n:
        if i in box_at:
            flush_text()
            last, node = box_at[i]
            children.append(node)
            i = last + 1
            continue
        if i in consumed:
            i += 1
            continue
        raw_line = segment_lines[i]
        align = _um_ascii_outer_align(raw_line)
        line = raw_line.strip()
        if not line:
            flush_text()
            i += 1
            continue
        # K9-a: skip lines that exactly match the outer card-title (avoid
        # the title showing up as a duplicate `info` node inside the body).
        if taken_title_text and line == taken_title_text:
            i += 1
            continue
        # Badge inline
        m = _re.search(r'([●○])\s*(\S+)', line)
        if m:
            circle, label = m.group(1), m.group(2)
            label = label.rstrip('，,。.;；:：')
            status = 'active' if circle == '●' else 'inactive'
            children.append({'type': 'badge', 'attrs': {'status': status},
                             'value': label, 'children': []})
            line = (line[:m.start()] + line[m.end():]).strip()
        if line:
            text_parts.append((line, align))
        i += 1
    flush_text()
    if trailing_actions:
        children.append({
            'type': 'actions', 'attrs': {}, 'value': None,
            'children': [
                {'type': 'button',
                 'attrs': ({'variant': v} if v != 'default' else {}),
                 'value': l, 'children': []}
                for l, v in trailing_actions
            ],
        })
    return children


def _um_ascii_find_column_split(interior: list):
    """Find a section-divider line containing ┬ (column split start).
    Verify subsequent body lines have │ at that column position.
    Returns (divider_idx, col_pos) or None.
    """
    for i, line in enumerate(interior):
        if not _um_ascii_is_divider_line(line):
            continue
        if '┬' not in line:
            continue
        pos = line.index('┬')
        # Verify at least one subsequent body line has │ at col `pos`
        for body in interior[i + 1:]:
            if _um_ascii_is_divider_line(body):
                continue
            if pos < len(body) and body[pos] in '│┃':
                return (i, pos)
        # No verification possible — treat as no column split
        return None
    return None


def _um_ascii_extract_two_column(interior: list, divider_idx: int, col_pos: int):
    """Split below-divider lines into (left_lines, right_lines) at col_pos.
    Returns (top_lines_before_divider, left_lines, right_lines).
    """
    top = interior[:divider_idx]
    below = interior[divider_idx + 1:]
    left_lines = []
    right_lines = []
    for line in below:
        right_part = line[col_pos + 1:] if len(line) > col_pos + 1 else ''
        # If the column split position has ├ or ┼ (right column's own inner
        # divider), prepend ├ so splitter recognizes the divider.
        if col_pos < len(line) and line[col_pos] in '├┼':
            right_part = '├' + right_part
        # Body-line right portion ends with the outer-frame │; strip it.
        # Don't strip if this is a divider line (├──┤) — splitter needs it.
        if not _um_ascii_is_divider_line(right_part):
            right_part = right_part.rstrip()
            while right_part.endswith('│') or right_part.endswith('┃'):
                right_part = right_part[:-1].rstrip()
        right_lines.append(right_part)
        left_part = line[:col_pos]
        left_part = _um_ascii_strip_pipes(left_part)
        left_lines.append(left_part)
    return top, left_lines, right_lines


def _um_ascii_build_two_column(interior: list, divider_idx: int, col_pos: int):
    """Build a `page` AST with navbar (top) + sidenav (left) + main body
    sections (right column processed recursively)."""
    top, left_lines, right_lines = _um_ascii_extract_two_column(
        interior, divider_idx, col_pos,
    )
    # Build navbar from top section: aggregate non-empty stripped lines
    navbar_text = ' '.join(
        _um_ascii_strip_pipes(l).strip() for l in top
        if _um_ascii_strip_pipes(l).strip()
    )
    navbar_node = {
        'type': 'navbar', 'attrs': {}, 'value': None,
        'children': [
            {'type': 'logo', 'attrs': {}, 'value': navbar_text, 'children': []}
        ] if navbar_text else [],
    }
    # Build sidenav: each non-empty distinct stripped line becomes an item
    seen = set()
    sidenav_items = []
    for l in left_lines:
        s = l.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        sidenav_items.append({
            'type': 'item', 'attrs': {}, 'value': s, 'children': [],
        })
    sidenav_node = {
        'type': 'sidenav', 'attrs': {}, 'value': None,
        'children': sidenav_items,
    }
    # Right column: split into segments using its own ├──┤ dividers
    right_segments = _um_ascii_split_segments(right_lines)
    main_children = []
    for seg in right_segments:
        if not any(s.strip() for s in seg):
            continue
        is_actions, btns = _um_ascii_parse_segment_actions(seg)
        if is_actions:
            children = []
            for label, variant in btns:
                attrs = {}
                if variant != 'default':
                    attrs['variant'] = variant
                children.append({
                    'type': 'button', 'attrs': attrs,
                    'value': label, 'children': [],
                })
            main_children.append({
                'type': 'actions', 'attrs': {}, 'value': None,
                'children': children,
            })
            continue
        main_children.extend(_um_ascii_parse_segment_content(seg))
    page = {
        'type': 'page',
        'attrs': {},
        'value': None,
        'children': [navbar_node, sidenav_node] + main_children,
    }
    return {'type': 'root', 'attrs': {}, 'value': None, 'children': [page]}


def _um_ascii_detect_pyramid(text: str):
    """Detect stacked-box pyramid pattern (progressively wider boxes joined
    by `┴` characters). Returns AST root or None.
    """
    import re as _re
    lines = text.splitlines()
    # Find header lines: pattern is whitespace + ┌[─┴]+┐ (with optional ┴
    # joiners from a smaller box above) at start of a line.
    headers = []
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        m = _re.match(r'^(\s*)(┌[─┴]+┐)\s*$', stripped)
        if m:
            indent = len(m.group(1))
            box = m.group(2)
            headers.append({'idx': i, 'left': indent, 'right': indent + len(box) - 1})
    # Need >=2 headers, each progressively wider (left earlier, right later)
    if len(headers) < 2:
        return None
    for i in range(1, len(headers)):
        if headers[i]['right'] - headers[i]['left'] <= \
           headers[i - 1]['right'] - headers[i - 1]['left']:
            return None
    # Find footer (the final └─...─┘ line after the last header)
    footer_idx = -1
    for j in range(headers[-1]['idx'] + 1, len(lines)):
        if _re.match(r'^\s*└[─┴]*┘\s*$', lines[j].rstrip()):
            footer_idx = j
            break
    if footer_idx < 0:
        return None
    # Build layers: content between header[i] and either header[i+1] or footer
    layers_ast = []
    for i, h in enumerate(headers):
        next_idx = headers[i + 1]['idx'] if i + 1 < len(headers) else footer_idx
        body_lines = lines[h['idx'] + 1:next_idx]
        # Strip outer │ pipes and use content within [h['left']+1 : h['right']]
        text_lines = []
        for bl in body_lines:
            # Limit to box bounds; characters outside (right of) right edge
            # belong to annotations beside the pyramid
            inside = bl[h['left'] + 1:h['right']] if len(bl) > h['left'] + 1 else ''
            inside = inside.strip().rstrip('│┃').strip()
            if inside:
                text_lines.append(inside)
        # Heuristic: first non-pct line = label; line containing % = pct;
        # lines outside the box (annotations) become detail
        label = ''
        pct = ''
        for tl in text_lines:
            if '%' in tl:
                pct = tl
            elif not label:
                label = tl
        # Detail = annotations to the right of the box on each row
        detail_parts = []
        for bl in body_lines:
            if len(bl) > h['right'] + 1:
                annot = bl[h['right'] + 1:].strip()
                if annot:
                    detail_parts.append(annot)
        layer_attrs = {}
        if pct:
            layer_attrs['pct'] = pct
        if detail_parts:
            layer_attrs['detail'] = ' '.join(detail_parts)
        layers_ast.append({
            'type': 'layer', 'attrs': layer_attrs,
            'value': label, 'children': [],
        })
    pyramid_node = {
        'type': 'pyramid', 'attrs': {}, 'value': None,
        'children': layers_ast,
    }
    return {'type': 'root', 'attrs': {}, 'value': None, 'children': [pyramid_node]}


def _um_ascii_segments_to_layered_arch(segments: list):
    """Convert list-of-segments (each = list of stripped content lines) into
    a `layered-arch` AST: each segment becomes a `layer` node; arrows (↓/↑)
    become `flow-down/flow-up` nodes interleaved between layers.

    Heuristic: first non-blank, non-arrow line of a segment = layer label;
    remaining non-arrow lines = `detail`. Arrow lines containing `↓` or `↑`
    are attached to the segment as flow indicators.
    """
    children = []
    pending_flow = None  # (kind, label)
    for seg_idx, seg in enumerate(segments):
        label = ''
        details = []
        flow_label = ''
        flow_kind = None
        for raw in seg:
            line = raw.strip()
            if not line:
                continue
            if '↓' in line or '↑' in line:
                kind = 'down' if '↓' in line else 'up'
                # Strip the arrow itself
                fl = line.replace('↓', '').replace('↑', '').strip()
                flow_label = fl
                flow_kind = kind
                continue
            if not label:
                label = line
            else:
                details.append(line)
        layer_attrs = {}
        layer_children = []
        if details:
            layer_children.append({
                'type': 'detail', 'attrs': {},
                'value': ' '.join(details), 'children': [],
            })
        # Add pending flow BEFORE this layer (from previous segment)
        if pending_flow is not None:
            kind, txt = pending_flow
            children.append({
                'type': f'flow-{kind}', 'attrs': {},
                'value': txt, 'children': [],
            })
            pending_flow = None
        children.append({
            'type': 'layer', 'attrs': layer_attrs,
            'value': label, 'children': layer_children,
        })
        # If this segment also contained a flow arrow → goes BEFORE next layer
        if flow_kind is not None:
            pending_flow = (flow_kind, flow_label)
    arch = {
        'type': 'layered-arch', 'attrs': {}, 'value': None,
        'children': children,
    }
    return {'type': 'root', 'attrs': {}, 'value': None, 'children': [arch]}


def _looks_like_ui_mock_signal(text: str) -> bool:
    """K7 — detect UI mock screen-layout signals (vs system / state machine).

    Strong signals (any → 'ui'):
      1. Emoji in U+1F000-1FFFF range (🏆 ⚡ 🎮 🔥 💧 🐉 etc.)
      2. Pixel dimensions like `160 × 160 px` or `220x220px`
      3. Canvas / sprite markers: `Phaser ... Canvas`, `(pet sprite)`
      4. UI-specific labels: `Lv\\d+`, `XP Gained`, `Player:`, `Type:`

    These signals are unique to UI mocks and won't appear in system
    architecture or state machine ASCII.
    """
    # Emoji range (covers most pictographs)
    if re.search(r'[\U0001F000-\U0001FAFF\U00002600-\U000027BF]', text):
        return True
    # Pixel dimensions
    if re.search(r'\d+\s*[×x]\s*\d+\s*px', text):
        return True
    # Canvas markers (Phaser / WebGL canvas labels in UI mocks)
    if re.search(r'(?:Phaser|WebGL|HTML5)\s+\d?\s*Canvas', text, re.IGNORECASE):
        return True
    # Game-specific UI labels (Lv, XP, Type, Rank)
    ui_label_count = 0
    for pat in (r'\bLv\s*\d+', r'XP\s+Gained', r'Player:\s', r'Type:\s', r'Rank:'):
        if re.search(pat, text):
            ui_label_count += 1
    if ui_label_count >= 2:
        return True
    return False


def _looks_like_tree(text: str) -> bool:
    """K2 — detect tree-shaped ASCII (file dir / component tree / sitemap / IA tree).

    Such content's semantic intent is "hierarchy", not "flow", and forcing it
    through F2 graph-TD conversion flattens the structure (parents collapse
    to the same level). Better to preserve as `<pre>` ASCII.

    Rules (all required):
      1. Has ≥ 2 lines with ├── / └── / ├─► / └─► tree-branch markers
      2. No box-only corners (┌ ┐ ┘) — those signal box-frame.
         (└ is excluded from the box check because trees use └── as
         "last child" marker; only └ + ─ + ┘ closes a box.)
      3. No standalone vertical-arrow lines (▼ / ▲ alone) — that signals flow

    Free-standing tree shapes (file dir / sitemap / IA / component) all match.
    Box-flow architectures (arch §1.2 multi-column / cicd L347 box-stack)
    fail rule 2. Single-column flows (developer-guide §2.1) fail rule 1
    (not enough tree markers) or rule 3 (standalone ▼).
    """
    lines = [ln for ln in text.split('\n') if ln.strip()]
    if not lines:
        return False
    # Rule 2: any box-only corner (┌/┐/┘) → not a tree.
    # `└` excluded from this check (used in trees: └── last-child marker).
    if any(c in line for line in lines for c in '┌┐┘'):
        return False
    # Rule 3: standalone vertical arrow → not a tree
    if any(line.strip() in ('▼', '▲') for line in lines):
        return False
    # Rule 1: at least 2 tree-branch markers
    branch_re = re.compile(r'(├──|└──|├─►|└─►)')
    branch_count = sum(1 for line in lines if branch_re.search(line))
    return branch_count >= 2


def _classify_ascii_block(text: str) -> str:
    """F1 — classify a fenced ASCII code block as 'system' | 'ui' | 'tree' | 'unknown'.

    K2: 'tree' is returned for hierarchical structures (file/component/sitemap/IA)
        that should be preserved as `<pre>` rather than forced through F2.

    Strategy: tree first; then strong system signals; then UI signals.

    System signals (any → 'system'):
      - Unicode arrows: → ← ↑ ↓ ► ◄
      - Long ASCII arrows: ──...──>  <──...──
      - Text arrows: -->, <--
      - Multiple parallel boxes on the same line: 2+ '┌' or 2+ '┐'
      - Multiple vertical lifelines: 4+ '│' on 3+ lines (sequence diagram)
      - In-content tree branches: '│ ... ├──' / '│ ... └──' inside a frame line

    UI signals (any → 'ui') — only if no system signal:
      - Short button labels: '[Apply]', '[取消]', '[+ 新增]' (1-12 chars,
        not ALL_CAPS_CONSTANT, no '=' sign)
      - Input fields: 6+ underscores in a row
      - Pagination: '[< 1 2 3 ... >]'
      - Page chrome: ☰, ▾ following short text in brackets

    Else → 'unknown' (caller should fall back to <pre>).
    """
    # ── K2: tree-shaped content (file dir / component / sitemap / IA) ──
    # Detected before system signals so that traceability trees (`└─►`)
    # and other hierarchies don't trip the arrow rules below.
    if _looks_like_tree(text):
        return 'tree'

    # ── K7: UI mock signals (emoji / pixel dimensions / canvas markers) ──
    # Detected before system signals so that screen layouts with arrows
    # like `↑ +4` (rank delta) don't get mis-routed to mermaid graph TD.
    if _looks_like_ui_mock_signal(text):
        return 'ui'

    # ── Strong system signals ──────────────────────────────────────
    # Vertical / triangular arrows are unambiguous flow direction markers,
    # but ONLY when they appear OUTSIDE square brackets (inside [label ▼]
    # they are UI dropdown indicators). Horizontal `→ ←` are intentionally
    # excluded — UI documentation uses them inline. Long ASCII arrows
    # `──>` `<──` are caught by the next rule.
    cleaned_for_arrow = re.sub(r'\[[^\]\n]*\]', '', text)
    if re.search(r'[↑↓►◄▲▼◀▶]', cleaned_for_arrow):
        return 'system'
    if re.search(r'──+>|<──+', text):
        return 'system'
    if re.search(r'(?:^|\s)-{2,}>|<-{2,}(?:\s|$)', text):
        return 'system'
    # Parallel boxes on same line (2+ '┌'), but NOT inside a UI table row
    # (UI tables have 2+ ┌ on the same line but always with a leading │ and
    # no arrows — already excluded by the arrow checks above).
    for line in text.split('\n'):
        if line.count('┌') >= 2:
            # If line starts with │ (we're inside a frame) and contains other
            # UI markers (e.g. brackets [Ban]), treat as table row inside UI
            # mock — let UI signals decide. Otherwise it's a parallel-box
            # architecture diagram.
            stripped = line.strip()
            if stripped.startswith('│') and re.search(r'\[\s*[^\]]{1,12}\s*\]', line):
                continue
            return 'system'
    # In-content tree branches: a │…│ line that contains ├── or └── followed
    # by TEXT (a child label). Pure table-border └────┴─── doesn't qualify.
    for line in text.split('\n'):
        m = re.search(
            r'│[^│┤]*?(?:├──|└──)[^│┤A-Za-z一-鿿_]*[A-Za-z一-鿿_]',
            line,
        )
        if m and '┤' not in line[m.end():]:
            return 'system'

    # ── UI signals ────────────────────────────────────────────────
    has_button = False
    for m in re.finditer(r'\[\s*([^\]\[]+?)\s*\]', text):
        label = m.group(1).strip()
        if not (1 <= len(label) <= 12):
            continue
        if '=' in label:
            continue
        # Skip ALL_CAPS_CONSTANTS (likely annotation, not a button)
        if re.fullmatch(r'[A-Z][A-Z0-9_]*', label):
            continue
        has_button = True
        break
    has_input = bool(re.search(r'_{6,}', text))
    has_paginator = bool(re.search(r'\[\s*<.*?\d.*?>\s*\]', text))
    if has_button or has_input or has_paginator:
        return 'ui'

    return 'unknown'


def _try_parse_state_machine(text: str):
    """K6: parse UML state machine ASCII → mermaid stateDiagram-v2.

    Detection: ≥ 3 ALL_CAPS state-like words (3-30 chars) inside `│ STATE │`
    box-bordered cells.

    Best-effort transition extraction: lines containing 2 state names with
    arrow/dash text between them yield `S1 --> S2: label`. Multi-line
    spanning transitions are not extracted (acceptable trade-off; at least
    states render correctly with `[*] --> first_state` initial arrow).

    Returns mermaid src starting with 'stateDiagram-v2' or None.
    """
    state_pattern = re.compile(r'│\s*([A-Z][A-Z_]{2,30})\s*│')
    seen = []
    for match in state_pattern.finditer(text):
        s = match.group(1)
        if s not in seen:
            seen.append(s)
    if len(seen) < 3:
        return None

    md_lines = ['stateDiagram-v2']
    md_lines.append(f'  [*] --> {seen[0]}')
    # Explicitly declare all detected states so even those without in-line
    # transitions still render as boxes.
    for state in seen:
        md_lines.append(f'  {state}')

    # Extract in-line transitions: lines with ≥ 2 state-name occurrences
    seen_pairs = set()
    transitions = []
    for line in text.split('\n'):
        token_matches = list(re.finditer(r'\b([A-Z][A-Z_]{2,30})\b', line))
        if len(token_matches) < 2:
            continue
        for i in range(len(token_matches) - 1):
            s1 = token_matches[i].group(1)
            s2 = token_matches[i + 1].group(1)
            if s1 not in seen or s2 not in seen or s1 == s2:
                continue
            if (s1, s2) in seen_pairs:
                continue
            between = line[token_matches[i].end():token_matches[i + 1].start()]
            # Strip box / arrow / quote chars to get label
            label = re.sub(r'[─▶▼▲►◄│┃└┘┐┌→\"]+', ' ', between)
            label = re.sub(r'\s+', ' ', label).strip()
            transitions.append((s1, s2, label))
            seen_pairs.add((s1, s2))

    for s1, s2, label in transitions:
        if label:
            md_lines.append(f'  {s1} --> {s2}: {label}')
        else:
            md_lines.append(f'  {s1} --> {s2}')

    return '\n'.join(md_lines)


def _try_parse_multi_column(text: str):
    """K4: parse multi-column architecture diagram (parallel boxes + fan-in).

    Detection: a line containing ≥ 2 '┌' chars marks a multi-column top border.
    Algorithm:
      1. Find column [start,end] ranges from the top border by walking '┌'..'┐'.
      2. For each row line until bottom border, slice text per column range.
      3. Concatenate cell text per column with '<br/>' → multi-line node label.
      4. After bottom, look for edge-label row (e.g. "HTTPS") and downstream
         single-column box → fan-in edges from each column → downstream node.

    Returns (nodes, edges) or None if not applicable.
    nodes = [(id, label), ...]
    edges = [(src_id, dst_id, edge_label), ...]
    """
    lines = text.split('\n')

    # Find first line with ≥ 2 '┌' chars
    multi_top_idx = None
    for i, line in enumerate(lines):
        if line.count('┌') >= 2:
            multi_top_idx = i
            break
    if multi_top_idx is None:
        return None

    top = lines[multi_top_idx]
    # Walk top border to extract column [start, end] ranges (┌ → matching ┐)
    col_ranges = []
    j = 0
    while j < len(top):
        if top[j] == '┌':
            start = j
            k = j + 1
            while k < len(top) and top[k] != '┐':
                k += 1
            if k >= len(top):
                break
            col_ranges.append((start, k))
            j = k + 1
        else:
            j += 1
    if len(col_ranges) < 2:
        return None

    # Collect content rows for each column until bottom border
    n_cols = len(col_ranges)
    col_lines = [[] for _ in range(n_cols)]
    bottom_idx = None
    for i in range(multi_top_idx + 1, len(lines)):
        line = lines[i]
        # Bottom signal: ≥ 2 '└' chars on the line
        if line.count('└') >= 2:
            bottom_idx = i
            break
        # Extract cell content per column range
        for ci, (s, e) in enumerate(col_ranges):
            if s + 1 < len(line):
                cell = line[s + 1:min(e, len(line))].strip().strip('│').strip()
                if cell:
                    col_lines[ci].append(cell)

    if bottom_idx is None:
        return None

    # Build column nodes (de-dup by label)
    nodes = []
    seen = {}
    col_node_ids = []
    for ci, ls in enumerate(col_lines):
        label = '<br/>'.join(ls).strip()
        if not label:
            col_node_ids.append(None)
            continue
        if label in seen:
            col_node_ids.append(seen[label])
            continue
        nid = f'N{len(nodes)}'
        nodes.append((nid, label))
        seen[label] = nid
        col_node_ids.append(nid)

    # Walk lines after bottom: collect edge label, then find downstream box
    edge_label = ''
    downstream_id = None
    i = bottom_idx + 1
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        # Arrow row: contains ▼/↓ but no other significant text
        bare = re.sub(r'[▼▲↓↑│┃\s]+', '', line)
        if not bare:
            i += 1
            continue
        # Downstream box top: starts with ┌── (single ┌)
        stripped = line.lstrip()
        if stripped.startswith('┌') and line.count('┌') == 1:
            # Walk content lines until '└'
            content_parts = []
            j = i + 1
            while j < len(lines):
                cont = lines[j]
                if cont.lstrip().startswith('└'):
                    break
                if '│' in cont:
                    cell = cont.strip().strip('│').strip()
                    if cell:
                        content_parts.append(cell)
                j += 1
            if content_parts:
                ds_label = '<br/>'.join(content_parts)
                if ds_label in seen:
                    downstream_id = seen[ds_label]
                else:
                    downstream_id = f'N{len(nodes)}'
                    nodes.append((downstream_id, ds_label))
                    seen[ds_label] = downstream_id
            break
        # Otherwise it's an edge-label row (e.g. "│  HTTPS  │  HTTPS  ...")
        # Extract first non-empty alpha token
        parts = [p.strip() for p in line.split('│')
                 if p.strip()
                 and p.strip() not in ('▼', '↓', '↑', '▲')
                 and not re.fullmatch(r'[─\s]+', p.strip())]
        if parts and not edge_label:
            edge_label = parts[0]
        i += 1

    # Fan-in edges: each column → downstream
    edges = []
    if downstream_id:
        for cid in col_node_ids:
            if cid and cid != downstream_id:
                edges.append((cid, downstream_id, edge_label))

    if not nodes:
        return None
    return nodes, edges


def _ascii_to_mermaid_td(text: str) -> 'str | None':
    """F2 — best-effort ASCII → mermaid graph TD converter.

    Returns mermaid source code (with `graph TD` direction) or None when
    the block isn't system content or can't be converted.

    Strategy:
      1. Refuse if classifier says 'ui'.
      2. Extract all 'box' labels: text inside ┌──┐ / └──┘ frames OR
         non-blank lines (for text-only flows).
      3. Detect connections:
         - Sequential arrows (→ / ──> / ↓) → linear chain
         - Tree branches (├── / └──) → parent-children edges
      4. Emit `graph TD` with quoted labels and edges.

    This is intentionally conservative: when the structure is too complex,
    it still emits at least a usable list of nodes so the reader sees the
    extracted information rather than nothing.
    """
    kind = _classify_ascii_block(text)
    if kind == 'ui':
        return None

    # K6: try state machine first (ALL_CAPS state names in boxes)
    state_machine_md = _try_parse_state_machine(text)
    if state_machine_md is not None:
        return state_machine_md

    # K4: try multi-column architecture (parallel boxes + fan-in to downstream)
    multi_col_result = _try_parse_multi_column(text)
    if multi_col_result is not None:
        nodes, edges = multi_col_result
        if nodes:
            md = ['graph TD']
            for nid, label in nodes:
                safe = label.replace('"', "'")
                md.append(f'  {nid}["{safe}"]')
            for src, dst, edge_label in edges:
                if edge_label:
                    safe_label = edge_label.replace('"', "'")
                    md.append(f'  {src} -->|"{safe_label}"| {dst}')
                else:
                    md.append(f'  {src} --> {dst}')
            return '\n'.join(md)

    lines = text.split('\n')

    nodes = []  # list of (id, label) preserving order
    seen_labels = {}

    def _add_node(label: str) -> str:
        label = label.strip().rstrip('│')
        # Strip leading tree chars
        label = re.sub(r'^[├└─\s]+', '', label).strip()
        # Strip trailing arrows etc.
        label = re.sub(r'[─→↓>▼▲]+$', '', label).strip()
        if not label:
            return ''
        # De-duplicate
        if label in seen_labels:
            return seen_labels[label]
        nid = f'N{len(nodes)}'
        nodes.append((nid, label))
        seen_labels[label] = nid
        return nid

    # K3: edges now carry an optional label — list of (src_id, dst_id, label_or_'')
    edges = []

    # K3+K5: classify each raw line as one of:
    #   ('node', text)       — a content node
    #   ('arrow', None)      — a standalone vertical arrow (▼/▲/↓/↑)
    #   ('annot', text)      — edge annotation: indent + │ + text (arrow-side note)
    # K5: a single-column box (┌──┐ ... └──┘) groups all interior content lines
    #     into ONE 'node' event with multi-line label joined by '<br/>'.
    # Frame-only / blank lines are skipped.
    events = []
    arrow_only_re = re.compile(r'^\s*[▼▲↓↑]+\s*$')
    frame_only_re = re.compile(r'^[─┌┐└┘├┤┬┴┼━│┃▼▲↓↑\s]*$')
    annot_re = re.compile(r'^\s*[│┃]\s+([^│┃]+?)\s*$')
    # K5 box-frame detection: single ┌ on top, single ┘ on bottom (single-col box).
    # Multi-col case is already handled by _try_parse_multi_column above and
    # would have returned earlier — so by here, only single ┌/┘ remain.
    box_top_re = re.compile(r'^\s*┌[─┬]+┐\s*$')
    box_bottom_re = re.compile(r'^\s*└[─┴]+┘\s*$')

    in_box = False
    box_content = []
    for raw in lines:
        # K5: box top → enter box collecting mode
        if box_top_re.match(raw):
            in_box = True
            box_content = []
            continue
        # K5: box bottom → emit accumulated box content as one 'node' event
        if box_bottom_re.match(raw):
            if in_box:
                label = '<br/>'.join(box_content).strip()
                if label:
                    events.append(('node', label))
                box_content = []
            in_box = False
            continue
        if in_box:
            # Inside box: strip outer │ borders, accumulate content (preserve internal
            # decoration like ├── ESLint per user pinning).
            s = re.sub(r'^[\s│┃]+', '', raw)
            s = re.sub(r'[\s│┃]+$', '', s)
            if not s or re.fullmatch(r'[─\s]+', s):
                continue
            box_content.append(s)
            continue
        # ── Outside box: existing K3 line-by-line logic ──
        if not raw.strip():
            continue
        # Standalone arrow line → 'arrow' event (advances flow but doesn't create node)
        if arrow_only_re.match(raw):
            events.append(('arrow', None))
            continue
        # Edge annotation: starts with whitespace + │, then text (no other │/┃ on line)
        m = annot_re.match(raw)
        if m:
            annot_text = m.group(1).strip()
            # Annotation must be substantive text (not empty, not all frame chars)
            if annot_text and not frame_only_re.match(annot_text):
                events.append(('annot', annot_text))
                continue
        # Strip frame chars (│ at edges, top/bottom borders) for cleaning
        s = re.sub(r'^[\s│┃]+', '', raw)
        s = re.sub(r'[\s│┃]+$', '', s)
        if not s:
            continue
        # Pure frame line (top/bottom border like ┌────┐)?
        if re.fullmatch(r'[─┌┐└┘├┤┬┴┼━]+', s):
            continue
        # Strip arrow tokens before deciding if substantive
        text_part = re.sub(r'──+>|<──+|[→←↑↓►◄▼▲◀▶]', '', s).strip()
        if not text_part:
            # Was just arrows / frame chars
            if re.search(r'[▼▲↓↑]', raw):
                events.append(('arrow', None))
            continue
        events.append(('node', text_part))

    # Build nodes + linear-flow edges from event stream
    prev_node_id = None
    pending_label_parts = []
    saw_arrow_since_prev = False

    for typ, val in events:
        if typ == 'arrow':
            saw_arrow_since_prev = True
            continue
        if typ == 'annot':
            pending_label_parts.append(val)
            saw_arrow_since_prev = True  # annotation implies a flow direction
            continue
        # typ == 'node'
        cur_id = _add_node(val)
        if not cur_id:
            continue
        if prev_node_id and saw_arrow_since_prev and prev_node_id != cur_id:
            label = ' '.join(pending_label_parts).strip()
            if (prev_node_id, cur_id, label) not in edges:
                edges.append((prev_node_id, cur_id, label))
        prev_node_id = cur_id
        pending_label_parts = []
        saw_arrow_since_prev = False

    # Pass 3 (legacy): tree-branch connections — kept for non-tree mixed cases
    # (note: K2 'tree' kind already early-exits before reaching F2 for free-standing trees;
    #  this pass remains for in-frame ├── still inside system-classified blocks)
    cleaned = []
    for raw in lines:
        s = re.sub(r'^[\s│┃]+', '', raw)
        s = re.sub(r'[\s│┃]+$', '', s)
        if s and not re.match(r'^[─┌┐└┘├┤┬┴┼━]+$', s):
            cleaned.append(s)
    parent_id = None
    existing_pairs = {(s, d) for s, d, _ in edges}
    for line in cleaned:
        if re.match(r'^[├└]──', line.strip()):
            child_label = re.sub(r'^[├└]──+\s*', '', line.strip())
            child_label = re.sub(r'[─→↓>]+$', '', child_label).strip()
            cid = seen_labels.get(child_label)
            if parent_id and cid and parent_id != cid:
                if (parent_id, cid) not in existing_pairs:
                    edges.append((parent_id, cid, ''))
                    existing_pairs.add((parent_id, cid))
        else:
            text_part = re.sub(r'──+>|<──+|[→←↑↓►◄]', '', line).strip()
            label = text_part
            if label in seen_labels:
                parent_id = seen_labels[label]

    if not nodes:
        return None

    # Emit mermaid
    md = ['graph TD']
    for nid, label in nodes:
        # Sanitise label: escape quotes
        safe = label.replace('"', "'")
        md.append(f'  {nid}["{safe}"]')
    for src, dst, edge_label in edges:
        if edge_label:
            safe_label = edge_label.replace('"', "'")
            md.append(f'  {src} -->|"{safe_label}"| {dst}')
        else:
            md.append(f'  {src} --> {dst}')
    return '\n'.join(md)


def _ui_mock_ascii_parse(text: str):
    """Parse ASCII box-drawing UI mock into AST root, or None if not parseable.

    Stage ⑤ scope — see module-level comment. Stages ⑥–⑧ extend with
    column-split (page+sidenav), tables, inner boxes (input/code/field),
    layered-arch (↓/↑ arrows between sections), and pyramid (stacked
    progressively wider boxes joined by ┴).
    """
    import re as _re
    if not any(any(c in _UM_BOX_CHARS for c in line) for line in text.splitlines()):
        return None
    # Try pyramid first (it has multiple separate boxes, no single outer frame)
    pyr = _um_ascii_detect_pyramid(text)
    if pyr is not None:
        return pyr
    lines = text.splitlines()
    # Locate top-frame (first line containing ┌) and bottom-frame (last line
    # containing └).
    top = -1
    bot = -1
    for i, line in enumerate(lines):
        if '┌' in line and top < 0:
            top = i
        if '└' in line:
            bot = i
    if top < 0 or bot < 0 or top >= bot:
        return None
    frame = lines[top:bot + 1]
    if len(frame) < 2:
        return None
    interior = frame[1:-1]
    # Detect 2-column split (┬ in a divider line, verified by │ alignment)
    col_split = _um_ascii_find_column_split(interior)
    if col_split is not None:
        return _um_ascii_build_two_column(interior, *col_split)
    # Sections split by ├──┤
    segments = _um_ascii_split_segments(interior)
    # If body has flow arrows (↓ ↑) and >=2 segments → layered-arch
    body_text = '\n'.join('\n'.join(_um_ascii_strip_pipes(l) for l in seg)
                          for seg in segments)
    if (len(segments) >= 2 and ('↓' in body_text or '↑' in body_text)):
        # Strip outer │ pipes from each segment line for cleaner content
        clean_segments = [
            [_um_ascii_strip_pipes(l) for l in seg] for seg in segments
        ]
        return _um_ascii_segments_to_layered_arch(clean_segments)
    # Determine outer type: modal if `[X]` or `[x]` anywhere in frame
    raw_text = '\n'.join(frame)
    is_modal = bool(_re.search(r'\[\s*[Xx]\s*\]', raw_text))
    # Title = first non-empty line of first segment; strip [X] markers.
    # Also detect outer align (center/left/right) from leading/trailing
    # whitespace of the title line within `│ ... │` borders.
    title = ''
    title_align = 'left'
    if segments and segments[0]:
        for line in segments[0]:
            s = line.strip()
            if s:
                title = s
                title_align = _um_ascii_outer_align(line)
                break
    title = _re.sub(r'\s*\[\s*[Xx]\s*\]\s*', ' ', title).strip()
    # Body segments
    if is_modal or len(segments) > 1:
        body_segments = segments[1:]
    else:
        body_segments = segments
    body_children = []
    for seg in body_segments:
        if not any(s.strip() for s in seg):
            continue
        is_actions, btns = _um_ascii_parse_segment_actions(seg)
        if is_actions:
            children = []
            for label, variant in btns:
                attrs = {}
                if variant != 'default':
                    attrs['variant'] = variant
                children.append({
                    'type': 'button', 'attrs': attrs,
                    'value': label, 'children': [],
                })
            body_children.append({
                'type': 'actions', 'attrs': {}, 'value': None,
                'children': children,
            })
            continue
        body_children.extend(_um_ascii_parse_segment_content(seg, title))
    outer_type = 'modal' if is_modal else 'card'
    outer_attrs = {}
    if title:
        outer_attrs['title'] = title
        if title_align != 'left':
            outer_attrs['title_align'] = title_align
    if is_modal:
        outer_attrs['closable'] = True
    outer = {
        'type': outer_type,
        'attrs': outer_attrs,
        'value': None,
        'children': body_children,
    }
    return {'type': 'root', 'attrs': {}, 'value': None, 'children': [outer]}


def rewrite_pages_paths(html: str, current_html_path, pages_dir) -> str:
    """Rewrite href/src in rendered HTML to be valid relative paths under
    server root = pages_dir/. 規則：

    R3-1: href="docs/pages/X" → "X"
    R3-2: href="docs/X.md" → "X.html" (when pages_dir/X.html exists)
    R3-3: href="diagrams/X.md" → "diag-X.html" (gendoc flatten convention)
          href="diagrams/" → strip <a>（無單一 page 對應）
    R3-4 / R3-5: href="features/X" / "blueprint/X" / "src/X" 等 root 路徑
                  → 在 pages/ 內無對應檔 → strip <a>，保留 inner text
    R1: <code>X</code> where X is path-like AND pages/X exists → 包 <a>
    LEGIT 不動: http(s)://、#anchor、existing relative paths

    `current_html_path` 是當前 HTML 將寫入的路徑（pathlib.Path）。
    """
    import os as _os
    pages_dir = Path(pages_dir)
    current_html_path = Path(current_html_path)
    rel_dir = current_html_path.parent.relative_to(pages_dir)

    def _resolve(target: str) -> 'pathlib.Path | None':
        """從當前 HTML 看 target 解析後對應的 pages/ 內絕對路徑。"""
        # 砍 #fragment / ?query
        clean = target.split('#', 1)[0].split('?', 1)[0]
        if not clean:
            return None
        candidate = (pages_dir / rel_dir / clean).resolve()
        try:
            candidate.relative_to(pages_dir.resolve())
        except ValueError:
            return None  # 跳出 pages/
        return candidate

    def _href_rewrite(match):
        full_match = match.group(0)
        attr = match.group(1)        # href / src
        target = match.group(2)
        # 完全跳過外部 / anchor
        if target.startswith(('http://', 'https://', '#', 'mailto:',
                              'data:', 'javascript:')):
            return full_match
        # R3-1: docs/pages/ prefix → 直接剝
        if target.startswith('docs/pages/'):
            target = target[len('docs/pages/'):]
        # R3-2: docs/X.md → X.html（若存在）
        if target.startswith('docs/') and ('.md' in target):
            tail = target[len('docs/'):]
            md_part, _, frag = tail.partition('#')
            if md_part.endswith('.md'):
                base = md_part[:-3].lower()
                html_name = base + '.html'
                # docs/diagrams/X.md 走 R3-3 處理
                if base.startswith('diagrams/'):
                    flat = 'diag-' + base[len('diagrams/'):] + '.html'
                    if (pages_dir / flat).is_file():
                        target = flat + (('#' + frag) if frag else '')
                    else:
                        return _strip_anchor(full_match)
                else:
                    if (pages_dir / html_name).is_file():
                        target = html_name + (('#' + frag) if frag else '')
                    else:
                        return _strip_anchor(full_match)
        # R3-3: diagrams/X.md（沒走 docs/ prefix 的版本）
        elif target.startswith('diagrams/'):
            tail = target[len('diagrams/'):]
            md_part, _, frag = tail.partition('#')
            if md_part.endswith('.md'):
                # B3+B7: subdir mirror — diagrams/X.md → diagrams/X.html (subdir)
                target = 'diagrams/' + md_part[:-3] + '.html' + (('#' + frag) if frag else '')
                # Existence check delegated to R3-6 final guard
            elif md_part.endswith('.html'):
                # Already an .html link in diagrams/ subdir — leave alone (sidebar self-links).
                pass
            else:
                # 純 diagrams/ 目錄 link → 無單一 page 對應
                return _strip_anchor(full_match)
        # R3-4 / R3-5: features/、blueprint/、src/ 等 root 路徑
        # B5/B7: subdir-mirrored .md → .html 在 pages/ 內合法（如 blueprint/mock/x.html）
        # 因此只 strip 非 .html 的 target（feature / yaml / py 等原始碼）。
        elif (re.match(r'^(features|blueprint|src|tests|infrastructure|scripts)/', target)
              and not target.split('#', 1)[0].split('?', 1)[0].endswith('.html')):
            return _strip_anchor(full_match)
        # G-Q4: bare X.md / ./X.md / subdir/X.md (no `docs/` prefix)
        # 把 .md 改成 .html (lowercase)，若 pages/ 內有對應檔則保留連結，
        # 否則 strip。anchor (#section) 保留。
        else:
            md_part, _, frag = target.partition('#')
            if md_part.endswith('.md'):
                # Strip leading "./" if present
                clean_md = md_part[2:] if md_part.startswith('./') else md_part
                html_candidate = clean_md[:-3].lower() + '.html'
                if (pages_dir / html_candidate).is_file():
                    target = html_candidate + (('#' + frag) if frag else '')
                else:
                    return _strip_anchor(full_match)
        # R3-7 (L1): generic root-prefix for subdir pages.
        # When current page is in pages/<subdir>/ and target is a root-level
        # path that resolves to an actual file/dir at pages/, prepend
        # `../` × depth so the browser resolves correctly.
        # Examples it fixes:
        #   <head><link href="assets/style.css">  in pages/diagrams/x.html
        #     → href="../assets/style.css"
        #   <a href="index.html" class="nav-brand"> in pages/diagrams/x.html
        #     → href="../index.html"
        # Excludes:
        #   - already-prefixed paths (../X) — sidebar pre-prefixes via make_sidebar
        #   - absolute (/X) and external (http://) — handled earlier
        #   - root-level page (depth=0) — no prefix needed
        depth = len(rel_dir.parts) if rel_dir != Path('.') else 0
        if depth > 0 and not target.startswith(('../', '/')):
            check_path = target.split('#', 1)[0].split('?', 1)[0]
            if check_path and (pages_dir / check_path).exists():
                target = ('../' * depth) + target

        # R3-6 防護：最終 target 解析後必須在 pages/ 內，否則 strip
        # （catch AI 寫 ../../../X 跳出 server root 的情況）
        resolved_check = _resolve(target)
        if resolved_check is None:
            return _strip_anchor(full_match)
        # 已重寫，回傳新 attr
        return f'{attr}="{target}"'

    def _strip_anchor(full_a_match: str) -> str:
        """把整個 <a href="..."> ... </a> 拆成純 inner text。
        full_a_match 是只匹配到 attr 的一段，需要找到包圍的 <a>。
        實作：因 _href_rewrite 只看 attr，這裡先回 sentinel，
        post-process 階段再轉成 strip。"""
        return '__STRIP_A_TAG__' + full_a_match

    # Step 1: 走訪 href / src，找需要改寫 / strip 的
    rewritten = re.sub(r'\b(href|src)="([^"]+)"', _href_rewrite, html)

    # Step 2: 對標記 strip 的 <a>，把整個 <a ...>inner</a> 換成 inner text
    def _strip_a(match):
        return match.group(1)
    rewritten = re.sub(
        r'<a [^>]*__STRIP_A_TAG__[^>]*>([^<]*)</a>',
        _strip_a, rewritten,
    )
    # 殘留的 sentinel 也清掉（防 self-closing 等）
    rewritten = rewritten.replace('__STRIP_A_TAG__', '')

    # Step 2b (M8): 對指向 prototype/ 的 <a> 注入 target="prototype-window"
    # 讓 docs 主 tab 不被取代，多次點 prototype 入口 → 同一個 named tab 切換。
    # 規則：<a href> 含 'prototype/' AND 沒已有 target → 加 target；
    #       <link href>、<script src> 不動。
    def _inject_prototype_target(m):
        full = m.group(0)
        if 'target=' in full:
            return full
        return full[:-1] + ' target="prototype-window">'

    rewritten = re.sub(
        r'<a\s[^>]*href="[^"]*prototype/[^"]*"[^>]*>',
        _inject_prototype_target, rewritten,
    )

    # Step 3: R1 — <code>X</code> auto-link when pages/X exists
    # A1 fix: skip <code> already inside <a>...</a> to avoid invalid nested <a><a>.
    def _find_a_spans(s):
        spans = []
        pos = 0
        while True:
            open_m = re.search(r'<a\b[^>]*>', s[pos:])
            if not open_m:
                break
            open_start = pos + open_m.start()
            close_idx = s.find('</a>', pos + open_m.end())
            if close_idx == -1:
                spans.append((open_start, len(s)))
                break
            end = close_idx + len('</a>')
            spans.append((open_start, end))
            pos = end
        return spans

    a_spans = _find_a_spans(rewritten)

    def _is_inside_a(idx):
        for lo, hi in a_spans:
            if lo <= idx < hi:
                return True
        return False

    def _code_to_link(match):
        if _is_inside_a(match.start()):
            return match.group(0)
        content = match.group(1)
        if not (('/' in content) or content.endswith(
                ('.html', '.md', '.json', '.yaml', '.yml'))):
            return match.group(0)
        try_targets = [content]
        if content.startswith('docs/pages/'):
            try_targets.append(content[len('docs/pages/'):])
        for t in try_targets:
            resolved = _resolve(t)
            if resolved is not None and resolved.is_file():
                return f'<a href="{t}">{content}</a>'
        return match.group(0)
    rewritten = re.sub(r'<code>([^<]+)</code>', _code_to_link, rewritten)

    return rewritten


def scan_prototype_entries(pages_dir):
    """掃 pages_dir/prototype/{,*/}index.html，回傳 list of {label, href}。

    用於 sidebar 自動生成 Interactive Prototypes 區塊。
    """
    pages_dir = Path(pages_dir)
    proto_dir = pages_dir / 'prototype'
    if not proto_dir.is_dir():
        return []
    entries = []
    # 主 prototype/index.html
    if (proto_dir / 'index.html').is_file():
        entries.append({'label': 'UI Prototype',
                        'href': 'prototype/index.html'})
    # 每個子目錄 prototype/<sub>/index.html
    for sub in sorted(proto_dir.iterdir()):
        if not sub.is_dir():
            continue
        if (sub / 'index.html').is_file():
            label_map = {
                'api-explorer': 'API Explorer',
                'admin': 'Admin Prototype',
            }
            label = label_map.get(sub.name, sub.name.replace('-', ' ').title())
            entries.append({'label': label,
                            'href': f'prototype/{sub.name}/index.html'})
    return entries


def strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter (--- ... ---) from the top of a markdown file."""
    if not (text.startswith('---\n') or text.startswith('---\r\n')):
        return text
    end = text.find('\n---', 4)
    if end < 0:
        return text
    # Skip past the closing --- and any trailing newline
    after = end + 4
    if after < len(text) and text[after] in ('\n', '\r'):
        after += 1
    return text[after:]

def _heading_slug(text: str) -> str:
    """J2: derive HTML id from heading text (GitHub-style slug).

    Order matters — same as GitHub / commonmark slug:
      1. Strip [label](url) wrappers → keep label only
      2. Lowercase
      3. EACH whitespace char → '-' (no collapse)
      4. Drop everything that isn't alphanumeric / CJK / '-' / '_'
      5. Trim leading/trailing '-'

    Producing e.g. `§9 — Data Access Layer` → `9--data-access-layer`
    (matches existing TOC anchors): `§` and `—` both removed in step 4
    AFTER spaces became '-', so the dashes from spaces stay.
    """
    s = text or ''
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
    s = s.lower()
    # Each whitespace → '-' (preserves consecutive separators as multi-'-')
    s = re.sub(r'\s', '-', s)
    # Drop non-allowed chars (keeps a-z, 0-9, _, -, CJK)
    s = re.sub(r'[^\w\-一-鿿]', '', s, flags=re.UNICODE)
    s = s.strip('-')
    return s


def inline_md(text, src_dir=None):
    """Process inline markdown. src_dir: Path of source .md file's directory for img path fixing."""
    codes = {}
    def save(m):
        k = f"\x00C{len(codes)}\x00"
        codes[k] = f"<code>{esc(m.group(1))}</code>"
        return k
    text = re.sub(r'`([^`]+)`', save, text)
    text = esc(text)
    for k, v in codes.items():
        text = text.replace(esc(k), v)

    def fix_img(m):
        alt, src = m.group(1), m.group(2)
        if src_dir and not src.startswith(('http', 'data:', '//', '#')):
            cand = (src_dir / src).resolve()
            if cand.exists():
                try:
                    src = os.path.relpath(cand, PAGES_DIR).replace('\\', '/')
                except ValueError:
                    pass
        return (f'<img src="{src}" alt="{esc(alt)}" loading="lazy" '
                f'onerror="this.replaceWith(Object.assign(document.createElement(\'span\'),'
                f'{{className:\'badge-fallback\',textContent:this.alt}}))">')

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_img, text)
    # J1: in-page anchor [X](#section) must not get target="_blank" (otherwise
    # it opens a new tab and never scrolls to the anchor).
    def _link(m):
        label, href = m.group(1), m.group(2)
        if href.startswith('#'):
            return f'<a href="{href}">{label}</a>'
        return f'<a href="{href}" target="_blank" rel="noopener">{label}</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', _link, text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\w)__(.+?)__(?!\w)', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', text)
    return text

def build_table(table_lines, src_dir=None):
    rows = []
    for line in table_lines:
        if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)
    if not rows:
        return ''
    out = ['<table>']
    out.append('<tr>' + ''.join(f'<th>{inline_md(c, src_dir)}</th>' for c in rows[0]) + '</tr>')
    for row in rows[1:]:
        out.append('<tr>' + ''.join(f'<td>{inline_md(c, src_dir)}</td>' for c in row) + '</tr>')
    out.append('</table>')
    return '\n'.join(out)

def md_to_html(text, src_dir=None):
    """Convert markdown to HTML.
    src_dir: Path directory of the source .md file — used to resolve relative img paths."""
    text = strip_frontmatter(text)
    lines = text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith('```mermaid'):
            block = []
            i += 1
            while i < len(lines) and lines[i].strip() != '```':
                block.append(lines[i])
                i += 1
            fixed = _mermaid_fix_block(block)
            out.append('<div class="diagram-container"><pre class="mermaid">' + '\n'.join(esc(l) for l in fixed) + '</pre></div>')
        elif re.match(r'^```\s*(plantuml|puml)\b', s):
            block = []
            i += 1
            while i < len(lines) and lines[i].strip() != '```':
                block.append(lines[i])
                i += 1
            out.append(_puml_block_to_html(block))
        elif re.match(r'^```\s*ui-mock\b', s):
            # Stage 9: UI Mock DSL fenced block → parse + render. Per user
            # spec: silent fallback to <pre> on parse error (no warning).
            block = []
            i += 1
            while i < len(lines) and lines[i].strip() != '```':
                block.append(lines[i])
                i += 1
            try:
                ast = _ui_mock_dsl_parse('\n'.join(block))
                # K8: wrap umock in .diagram-container so lightbox can bind.
                out.append(
                    '<div class="diagram-container diagram-container--umock">'
                    + _ui_mock_render(ast)
                    + '</div>'
                )
            except Exception:
                escaped = '\n'.join(esc(l) for l in block)
                out.append(f'<pre><code>{escaped}</code></pre>')
        elif s.startswith('```'):
            lang = s[3:].strip()
            raw_block = []
            i += 1
            while i < len(lines) and lines[i].strip() != '```':
                raw_block.append(lines[i])
                i += 1
            # F1+F2 + Stage 9: classify ASCII blocks before deciding renderer.
            #   - special shapes (pyramid / layered-arch) → existing UI Mock
            #     parser handles them (it already emits mermaid TB / SVG).
            #   - 'ui'     → UI Mock parser
            #   - 'system' → ASCII → mermaid TD (F2)
            #   - 'unknown' → <pre> (safe default)
            block_text = '\n'.join(raw_block)
            if not lang and any(any(c in line for c in '┌┐└┘├┤')
                                for line in raw_block):
                # Try special-shape detection first (pyramid / layered-arch).
                special_ast = _ui_mock_ascii_parse(block_text)
                if special_ast and special_ast.get('children'):
                    first_type = special_ast['children'][0].get('type')
                    if first_type in ('pyramid', 'layered-arch'):
                        # K8: wrap umock in .diagram-container so lightbox binds.
                        out.append(
                            '<div class="diagram-container diagram-container--umock">'
                            + _ui_mock_render(special_ast)
                            + '</div>'
                        )
                        i += 1
                        continue

                kind = _classify_ascii_block(block_text)
                if kind == 'ui':
                    ast = special_ast or _ui_mock_ascii_parse(block_text)
                    if ast is not None:
                        # K8: wrap umock in .diagram-container so lightbox binds.
                        out.append(
                            '<div class="diagram-container diagram-container--umock">'
                            + _ui_mock_render(ast)
                            + '</div>'
                        )
                        i += 1
                        continue
                elif kind == 'system':
                    mermaid_src = _ascii_to_mermaid_td(block_text)
                    if mermaid_src:
                        # Run through v11-fix pipeline (edge-label quoting,
                        # node-label paren handling, etc.) so auto-generated
                        # mermaid follows the same rules as authored mermaid.
                        fixed_src = '\n'.join(
                            _mermaid_fix_block(mermaid_src.split('\n'))
                        )
                        out.append(
                            '<div class="diagram-container">'
                            f'<pre class="mermaid">{esc(fixed_src)}</pre>'
                            '</div>'
                        )
                        i += 1
                        continue
                # 'unknown' or conversion failed → fall through to <pre>
            cls = f'language-{lang}' if lang else ''
            escaped = '\n'.join(esc(l) for l in raw_block)
            out.append(f'<pre><code class="{cls}">' + escaped + '</code></pre>')
        elif s.startswith('#### '):
            txt = s[5:]
            out.append(f'<h4 id="{_heading_slug(txt)}">{inline_md(txt, src_dir)}</h4>')
        elif s.startswith('### '):
            txt = s[4:]
            out.append(f'<h3 id="{_heading_slug(txt)}">{inline_md(txt, src_dir)}</h3>')
        elif s.startswith('## '):
            txt = s[3:]
            out.append(f'<h2 id="{_heading_slug(txt)}">{inline_md(txt, src_dir)}</h2>')
        elif s.startswith('# '):
            txt = s[2:]
            out.append(f'<h1 id="{_heading_slug(txt)}">{inline_md(txt, src_dir)}</h1>')
        elif re.match(r'^[-*_]{3,}$', s):
            out.append('<hr>')
        elif s.startswith('> '):
            out.append(f'<blockquote><p>{inline_md(s[2:], src_dir)}</p></blockquote>')
        elif s.startswith('|') and '|' in s[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            out.append(build_table(table_lines, src_dir))
            continue
        elif re.match(r'^[-*+] ', s):
            items = []
            while i < len(lines):
                raw = lines[i]
                stripped = raw.strip()
                indent = len(raw) - len(raw.lstrip())
                if re.match(r'^[-*+] ', stripped):
                    text = stripped[2:]
                    if text.startswith('[ ] '):
                        li = f'<li style="list-style:none"><input type="checkbox" disabled> {inline_md(text[4:], src_dir)}</li>'
                    elif text.startswith('[x] ') or text.startswith('[X] '):
                        li = f'<li style="list-style:none"><input type="checkbox" checked disabled> {inline_md(text[4:], src_dir)}</li>'
                    elif indent >= 2:
                        li = f'<li style="margin-left:{indent * 0.5}rem">{inline_md(text, src_dir)}</li>'
                    else:
                        li = f'<li>{inline_md(text, src_dir)}</li>'
                    items.append(li)
                    i += 1
                else:
                    break
            out.append('<ul>' + ''.join(items) + '</ul>')
            continue
        elif re.match(r'^\d+\. ', s):
            items = []
            while i < len(lines) and re.match(r'^\d+\. ', lines[i].strip()):
                t = re.sub(r'^\d+\. ', '', lines[i].strip())
                items.append(f'<li>{inline_md(t, src_dir)}</li>')
                i += 1
            out.append('<ol>' + ''.join(items) + '</ol>')
            continue
        elif s:
            out.append(f'<p>{inline_md(s)}</p>')
        i += 1
    return '\n'.join(out)

PAGE_META = {
    'index':        ('首頁',                    '🏠'),
    'idea':         ('構想文件 (IDEA)',          '💡'),
    'brd':          ('商業需求文件 (BRD)',        '📋'),
    'prd':          ('產品需求文件 (PRD)',        '📝'),
    'pdd':          ('產品設計文件 (PDD)',        '🎨'),
    'vdd':          ('視覺設計文件 (VDD)',        '🖼️'),
    'edd':          ('工程設計文件 (EDD)',        '🏗️'),
    'arch':         ('架構設計',                 '🧩'),
    'api':          ('API 文件',                 '🔌'),
    'schema':       ('Schema 文件',              '🗄️'),
    'frontend':     ('前端設計文件',              '🖥️'),
    'audio':        ('音效設計文件',              '🔊'),
    'anim':         ('動畫特效文件',              '🎬'),
    'client_impl':  ('客戶端實作規格',            '🖥'),
    'constants':    ('業務常數文件',              '🔢'),
    'contracts':    ('機器可讀合約',              '📦'),
    'test-plan':    ('測試計畫 (Test Plan)',      '✅'),
    'bdd':          ('BDD Scenarios',            '🧪'),
    'rtm':          ('需求追蹤矩陣 (RTM)',        '🗂️'),
    'runbook':      ('Runbook',                  '📖'),
    'local_deploy': ('本地部署指南',              '🚀'),
    'align_report': ('對齊報告',                 '🔍'),
}

DIAGRAM_META = {
    'use-case':          ('用例圖 (Use Case)',          '👤', 'server'),
    'class-domain':      ('類別圖：領域模型',            '🗂️', 'server'),
    'class-service':     ('類別圖：服務層',              '⚙️', 'server'),
    'class-data':        ('類別圖：資料層',              '🗄️', 'server'),
    'object-snapshot':   ('物件圖：快照',               '📸', 'server'),
    'sequence-flow':     ('循序圖：主流程',              '🔄', 'server'),
    'sequence-ws':       ('循序圖：WebSocket',          '🔌', 'server'),
    'sequence-auth':     ('循序圖：認證',               '🔐', 'server'),
    'communication':     ('協作圖',                    '🤝', 'server'),
    'state-machine-fish':('狀態機圖：魚群生命週期',      '🐟', 'server'),
    'state-machine':     ('狀態機圖',                   '🔀', 'server'),
    'activity-flow':     ('活動圖',                    '📊', 'server'),
    'component':         ('元件圖',                    '🧩', 'server'),
    'deployment':        ('部署圖',                    '☁️', 'server'),
    'er-diagram':        ('ER 關聯圖',                  '🗃️', 'server'),
    'class-inventory':   ('類別清單',                   '📋', 'server'),
    'frontend-use-case':          ('前端用例圖',                 '👤', 'frontend'),
    'frontend-class-component':   ('前端類別圖：元件',           '🗂️', 'frontend'),
    'frontend-class-scene':       ('前端類別圖：場景控制器',      '🎬', 'frontend'),
    'frontend-class-services':    ('前端類別圖：Client 服務',    '⚙️', 'frontend'),
    'frontend-object-snapshot':   ('前端物件圖：UI 快照',        '📸', 'frontend'),
    'frontend-sequence-ws':       ('前端循序圖：WS 協議',        '🔌', 'frontend'),
    'frontend-sequence-scene':    ('前端循序圖：場景切換',        '🔄', 'frontend'),
    'frontend-sequence-shoot':    ('前端循序圖：射擊流程',        '🎯', 'frontend'),
    'frontend-state-scene':       ('前端狀態機：場景',           '🔀', 'frontend'),
    'frontend-state-ui':          ('前端狀態機：UI',             '🖥️', 'frontend'),
    'frontend-activity-gameplay': ('前端活動圖：遊戲主流程',      '📊', 'frontend'),
    'frontend-activity-ui':       ('前端活動圖：UI 互動',        '🖱️', 'frontend'),
    'frontend-activity-init':     ('前端活動圖：初始化',         '🚀', 'frontend'),
    'frontend-component':         ('前端元件圖：Cocos 節點樹',   '🧩', 'frontend'),
    'frontend-deployment':        ('前端部署圖：建構管線',        '☁️', 'frontend'),
    'frontend-communication':     ('前端協作圖：WS 協議',        '🤝', 'frontend'),
}

def scan_diagram_pages():
    if not DIAGRAMS_DIR.exists():
        return [], []
    server, frontend = [], []
    for p in sorted(DIAGRAMS_DIR.glob("*.md")):
        stem = p.stem
        if stem in ('class-inventory',):
            continue
        meta = DIAGRAM_META.get(stem)
        if meta:
            label, icon, side = meta
        else:
            label = stem.replace('-', ' ').title()
            icon = '📐'
            side = 'frontend' if stem.startswith('frontend-') else 'server'
        entry = (stem, label, icon, p)
        if side == 'frontend':
            frontend.append(entry)
        else:
            server.append(entry)
    return server, frontend

def scan_subdirectory_docs():
    """Scan docs/ subdirectories recursively for .md files.
    Excludes: docs/pages/ (output), docs/diagrams/ (handled by scan_diagram_pages).
    Returns: dict { subdir_name: [(slug, label, path), ...] } ordered by dirname.
    Slug format: '{subdir}/{relative_stem}' (lowercase, preserves '/').
    """
    excluded = {PAGES_DIR.resolve(), DIAGRAMS_DIR.resolve()}
    result = {}
    if not DOCS_DIR.exists():
        return result
    for subdir in sorted(DOCS_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        if subdir.resolve() in excluded or subdir.name.startswith('.'):
            continue
        md_files = sorted(subdir.rglob("*.md"))
        if not md_files:
            continue
        entries = []
        for p in md_files:
            rel = p.relative_to(subdir).with_suffix('')
            slug = subdir.name.lower() + '/' + str(rel).replace('\\', '/').lower()
            label = p.stem.replace('_', ' ').replace('-', ' ').title()
            entries.append((slug, label, p))
        result[subdir.name] = entries
    return result


def scan_puml_files():
    """Scan docs/ recursively for standalone .puml files (excluding pages/).
    Returns list of (slug, label, path) sorted by path."""
    if not DOCS_DIR.exists():
        return []
    results = []
    for p in sorted(DOCS_DIR.rglob('*.puml')):
        if PAGES_DIR.resolve() in p.resolve().parents:
            continue
        rel = p.relative_to(DOCS_DIR).with_suffix('')
        slug = 'puml--' + str(rel).replace('/', '-').replace('\\', '-').lower()
        label = p.stem.replace('_', ' ').replace('-', ' ').title()
        results.append((slug, label, p))
    return results


_DIR_ICONS = {
    'req': '📎', 'logic': '📐', 'diagrams': '🖼️', 'features': '🧪',
    'notes': '📓', 'adr': '📋', 'runbooks': '📖', 'specs': '📄',
}

def _build_subdir_tree(sub_docs):
    """Build recursive tree from sub_docs entries.

    sub_docs shape: {top_subdir_name: [(slug, label, path), ...]}
    where slug is like 'blueprint/mock/x' (from B1 — preserves '/').

    Returns tree shape:
      {'leaves': [(slug, label), ...], 'dirs': {dir_name: subtree}}
    """
    tree = {'leaves': [], 'dirs': {}}
    for _subdir_name, entries in sub_docs.items():
        for slug, label, _path in entries:
            parts = slug.split('/')
            node = tree
            for part in parts[:-1]:
                node = node['dirs'].setdefault(part, {'leaves': [], 'dirs': {}})
            node['leaves'].append((slug, label))
    return tree


def _tree_contains_active(tree, current):
    if any(slug == current for slug, _ in tree['leaves']):
        return True
    return any(_tree_contains_active(sub, current) for sub in tree['dirs'].values())


def _diag_prefix_of(stem, is_frontend):
    """Return the prefix label group for a diagram filename stem."""
    s = stem
    if is_frontend and s.startswith('frontend-'):
        s = s[len('frontend-'):]
    if s.startswith('activity-'):
        return 'Activity'
    if s.startswith('class-'):
        return 'Class'
    if s.startswith('sequence-'):
        return 'Sequence'
    if s.startswith('state-'):
        return 'State'
    if s.startswith('cicd-'):
        return 'CI/CD'
    if s in ('infra-local-topology', 'developer-workflow-activity'):
        return 'CI/CD'
    return '其他'


_DIAG_PREFIX_ORDER = ['Activity', 'Class', 'Sequence', 'State', 'CI/CD', '其他']


_TOC_HEADING_RE = re.compile(
    r'<h([23])\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h\1>',
    re.DOTALL | re.IGNORECASE,
)
_TOC_TAG_STRIP_RE = re.compile(r'<[^>]+>')


def _build_toc(html):
    """Extract H2/H3 with id attributes from rendered HTML and produce a
    `<ul class="toc-list">` for the sidebar TOC panel.

    H4+ excluded. Returns empty list HTML when no H2/H3 found (still a `<ul>`
    so the panel structure stays consistent).

    N1 (TOC tab): used by render_page to fill `<div data-panel="toc">`.
    """
    if not isinstance(html, str):
        return '<ul class="toc-list"></ul>'
    items = []
    for m in _TOC_HEADING_RE.finditer(html):
        level, hid, inner = m.group(1), m.group(2), m.group(3)
        text = _TOC_TAG_STRIP_RE.sub('', inner).strip()
        if not text:
            continue
        cls = 'toc__link' + (' toc__link--h3' if level == '3' else '')
        items.append(
            f'<li><a class="{cls}" href="#{_html.escape(hid)}">'
            f'{_html.escape(text)}</a></li>'
        )
    return '<ul class="toc-list">' + ''.join(items) + '</ul>'


def make_sidebar(doc_pages, server_diagrams, frontend_diagrams, sub_docs, current, has_req=False, puml_files=None, toc_html=''):
    # B6: compute href relative to current page's location.
    # current is a slug like 'index', 'edd', 'blueprint/mock/x', or 'diagrams/foo'.
    # Pages are at pages/{current}.html. For a target slug, href must be the
    # relative path from current's parent dir to the target file.
    current_parts = current.split('/') if current else ['']
    current_depth = len(current_parts) - 1  # 'blueprint/mock/x' → depth 2

    def link(slug, label, icon=''):
        cls = ' active' if slug == current else ''
        prefix = f'{icon} ' if icon else ''
        if current_depth == 0:
            href = f'{slug}.html'
        else:
            href = ('../' * current_depth) + f'{slug}.html'
        return f'<a class="sidebar__link{cls}" href="{href}">{prefix}{label}</a>'

    def render_subdir_tree(name, tree):
        """Recursive <details> render for a subdir tree node."""
        is_active = _tree_contains_active(tree, current)
        open_attr = ' open' if is_active else ''
        icon = _DIR_ICONS.get(name.lower(), '📁')
        out = [f'<details{open_attr}>',
               f'<summary>{icon} {name}/</summary>']
        for slug, label in tree['leaves']:
            out.append(link(slug, label))
        for sub_name in sorted(tree['dirs'].keys()):
            out.append(render_subdir_tree(sub_name, tree['dirs'][sub_name]))
        out.append('</details>')
        return '\n'.join(out)

    def render_diagram_prefix_groups(diagrams, is_frontend):
        groups = {}
        for slug, label, icon, _ in diagrams:
            pfx = _diag_prefix_of(slug, is_frontend)
            groups.setdefault(pfx, []).append((slug, label, icon))
        out = []
        for pfx in _DIAG_PREFIX_ORDER:
            if pfx not in groups:
                continue
            out.append(f'<div class="sidebar__label sidebar__label--sub">{pfx}</div>')
            for slug, label, icon in groups[pfx]:
                out.append(link(f'diagrams/{slug}', label, icon))
        return out

    sections = []

    # B8: pre-fetch interactive prototype entries to inject into 📁 prototype/
    proto_entries = scan_prototype_entries(PAGES_DIR)
    depth_prefix = ('../' * current_depth) if current_depth else ''

    def render_interactive_block():
        """Render Interactive Prototypes label + 🎮 entries (used inside prototype/ folder).

        M8: 所有 prototype 連結加 `target="prototype-window"` named tab，
        讓 docs 主 tab 不被取代；多次點 prototype 入口 → 同一個 tab 切換。
        """
        out = ['<div class="sidebar__label sidebar__label--sub">Interactive Prototypes</div>']
        for entry in proto_entries:
            href = depth_prefix + entry['href']
            out.append(
                f'<a class="sidebar__link" href="{href}" '
                f'target="prototype-window">'
                f'🎮 {entry["label"]}</a>'
            )
        return out

    def render_prototype_subdir(name, tree):
        """Specialised render for prototype/ folder: include Interactive entries inside."""
        is_active = _tree_contains_active(tree, current) or bool(proto_entries)
        # Force open if interactive entries exist (they are user's likely landing path)
        open_attr = ' open' if is_active else ''
        icon = _DIR_ICONS.get(name.lower(), '📁')
        out = [f'<details{open_attr}>',
               f'<summary>{icon} {name}/</summary>']
        if proto_entries:
            out.extend(render_interactive_block())
        # B9: distinguish .md spec docs from interactive entries with a label
        # (only when both interactive and .md leaves exist; pure-md case shows
        # leaves directly under the folder summary without a redundant label).
        leaves = tree['leaves']
        if leaves and proto_entries:
            out.append('<div class="sidebar__label sidebar__label--sub">規格文件</div>')
        for slug, label in leaves:
            out.append(link(slug, label))
        for sub_name in sorted(tree['dirs'].keys()):
            out.append(render_subdir_tree(sub_name, tree['dirs'][sub_name]))
        out.append('</details>')
        return '\n'.join(out)

    # ── Main docs ──────────────────────────────────────────
    sections.append('<div class="sidebar__section">')
    sections.append('<div class="sidebar__label">文件</div>')
    for slug, label, icon in doc_pages:
        sections.append(link(slug, label, icon))
    sections.append('</div>')

    # ── Subdirectory tree (recursive collapsible) ─────────
    subdir_tree = _build_subdir_tree(sub_docs)
    rendered_top_names = set()
    for top_name in sorted(subdir_tree['dirs'].keys()):
        sections.append('<div class="sidebar__section">')
        if top_name.lower() == 'prototype':
            sections.append(render_prototype_subdir(top_name, subdir_tree['dirs'][top_name]))
        else:
            sections.append(render_subdir_tree(top_name, subdir_tree['dirs'][top_name]))
        rendered_top_names.add(top_name.lower())
        sections.append('</div>')

    # B8: synthesize 📁 prototype/ folder if interactive entries exist but no
    # docs/prototype/*.md was scanned (so subdir_tree has no 'prototype' node).
    if proto_entries and 'prototype' not in rendered_top_names:
        sections.append('<div class="sidebar__section">')
        sections.append('<details open>')
        sections.append('<summary>📁 prototype/</summary>')
        sections.extend(render_interactive_block())
        sections.append('</details>')
        sections.append('</div>')

    # ── req download page (only if req/ not already a subdir tree node) ──
    if has_req and 'req' not in subdir_tree['dirs']:
        sections.append('<div class="sidebar__section">')
        sections.append('<div class="sidebar__label">原始素材</div>')
        sections.append(link('req', 'req/ 素材清單', '📎'))
        sections.append('</div>')

    # ── UML diagrams (📁 diagrams/ collapsible) ──
    # B8: PlantUML files render inside this same details (since .puml lives in
    # docs/diagrams/puml/), not as a sibling section.
    if server_diagrams or frontend_diagrams or puml_files:
        is_active = (
            any(f'diagrams/{slug}' == current for slug, *_ in server_diagrams)
            or any(f'diagrams/{slug}' == current for slug, *_ in frontend_diagrams)
            or (puml_files and any(slug == current for slug, _, _ in puml_files))
        )
        open_attr = ' open' if is_active else ''
        sections.append('<div class="sidebar__section">')
        sections.append(f'<details{open_attr}>')
        sections.append('<summary>📁 diagrams/</summary>')
        if server_diagrams:
            sections.append('<div class="sidebar__label">Server UML</div>')
            sections.extend(render_diagram_prefix_groups(server_diagrams, is_frontend=False))
        if frontend_diagrams:
            sections.append('<div class="sidebar__label">Frontend UML</div>')
            sections.extend(render_diagram_prefix_groups(frontend_diagrams, is_frontend=True))
        if puml_files:
            sections.append('<div class="sidebar__label">PlantUML</div>')
            for slug, label, _ in puml_files:
                sections.append(link(slug, label))
        sections.append('</details>')
        sections.append('</div>')

    # ── N1: wrap docs sections in tab/panel structure with TOC ──
    docs_panel_html = '\n'.join(sections)
    toc_panel_html = toc_html if toc_html else '<ul class="toc-list"></ul>'
    return (
        '<button class="sidebar__toggle" id="sidebarCollapseBtn" '
        'type="button" aria-label="收合 / 展開側欄" title="收合 / 展開">⇤</button>'
        '<div class="sidebar__tabs" role="tablist">'
        '<button class="sidebar__tab active" data-tab="docs" '
        'type="button" role="tab" aria-selected="true">📁 文件</button>'
        '<button class="sidebar__tab" data-tab="toc" '
        'type="button" role="tab" aria-selected="false">📑 本頁目錄</button>'
        '</div>'
        '<div class="sidebar__panel active" data-panel="docs" role="tabpanel">'
        f'{docs_panel_html}'
        '</div>'
        '<div class="sidebar__panel" data-panel="toc" role="tabpanel">'
        f'{toc_panel_html}'
        '</div>'
    )

def render_page(content, title, banner, doc_pages, server_diagrams, frontend_diagrams, sub_docs, current, is_index=False, has_req=False, puml_files=None):
    gh = (f'<a class="nav-gh-link" href="{GITHUB_REPO}" target="_blank" rel="noopener">⌥ GitHub</a>'
          if GITHUB_REPO else '')
    if is_index:
        bc = f'<a href="index.html">{APP_NAME}</a> › 文件中心'
        if GITHUB_REPO:
            bc += (f' <span style="margin-left:1rem">'
                   f'<a href="{GITHUB_REPO}" target="_blank" rel="noopener" style="color:var(--banner-link)">⌥ GitHub ↗</a>'
                   f'</span>')
    else:
        bc = f'<a href="index.html">{APP_NAME}</a> › {banner}'
    toc_html = _build_toc(content)
    sidebar_html = make_sidebar(doc_pages, server_diagrams, frontend_diagrams, sub_docs, current, has_req=has_req, puml_files=puml_files, toc_html=toc_html)
    return (HTML_TEMPLATE
            .replace('__TITLE__', title)
            .replace('__APP__', APP_NAME)
            .replace('__GH_LINK__', gh)
            .replace('__BREADCRUMB__', bc)
            .replace('__BANNER__', banner)
            .replace('__SIDEBAR__', sidebar_html)
            .replace('__CONTENT__', content))

def health_section():
    try:
        step = json.loads((BASE / ".gendoc-state.json").read_text()).get("current_step", "0")
    except:
        step = "0"
    return (
        '<section style="margin-top:3rem;padding:1.5rem;background:#fff;'
        'border:1px solid var(--border);border-radius:8px;">'
        '<h2 style="margin-top:0">📊 專案健康狀態</h2>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:1rem;margin-top:1rem">'
        '<div style="text-align:center;padding:1rem;background:var(--page-bg);border-radius:6px">'
        '<div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.25rem">已完成 STEP</div>'
        f'<div style="font-size:1.5rem;font-weight:700;color:var(--accent)">{step}/20</div>'
        '</div></div></section>'
    )

def prototype_cards_section():
    """D2: dedicated 'Prototype' section at top of index.html body.

    Renders an independent <section> with its own h2 header and an index-grid
    containing one card per scan_prototype_entries() result. Returns '' when
    no entries.
    """
    entries = scan_prototype_entries(PAGES_DIR)
    if not entries:
        return ''
    cards = []
    for entry in entries:
        cards.append(
            f'<a class="index-card" href="{entry["href"]}" '
            f'target="prototype-window">'
            f'<span class="index-card__icon">🎮</span>'
            f'<span class="index-card__title">{esc(entry["label"])}</span>'
            f'</a>'
        )
    return (
        '<section style="margin-top:2.5rem">'
        '<h2 style="font-size:1rem;font-weight:600;color:var(--text-muted);'
        'text-transform:uppercase;letter-spacing:.08em;margin-bottom:.75rem">'
        '🎮 互動 Prototype</h2>'
        '<div class="index-grid">' + ''.join(cards) + '</div>'
        '</section>'
    )


def doc_cards_section(doc_pages, server_diagrams, frontend_diagrams):
    cards = []
    for slug, label, icon in doc_pages:
        if slug == 'index':
            continue
        cards.append(
            f'<a class="index-card" href="{slug}.html">'
            f'<span class="index-card__icon">{icon}</span>'
            f'<span class="index-card__title">{esc(label)}</span>'
            f'</a>'
        )
    diag_total = len(server_diagrams) + len(frontend_diagrams)
    if diag_total:
        cards.append(
            f'<a class="index-card" href="diagrams/{server_diagrams[0][0] if server_diagrams else frontend_diagrams[0][0]}.html">'
            f'<span class="index-card__icon">📐</span>'
            f'<span class="index-card__title">UML 圖表 ({diag_total} 張)</span>'
            f'<span class="index-card__desc">Server {len(server_diagrams)} / Frontend {len(frontend_diagrams)}</span>'
            f'</a>'
        )
    if not cards:
        return ''
    return (
        '<section style="margin-top:2.5rem">'
        '<h2 style="font-size:1rem;font-weight:600;color:var(--text-muted);'
        'text-transform:uppercase;letter-spacing:.08em;margin-bottom:.75rem">文件導覽</h2>'
        '<div class="index-grid">' + ''.join(cards) + '</div>'
        '</section>'
    )

def req_section():
    if not REQ_DIR.exists():
        return ''
    files = sorted(f for f in REQ_DIR.iterdir() if f.is_file() and not f.name.startswith('.'))
    if not files:
        return ''
    EXT_ICON = {
        '.pdf': '📄', '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️',
        '.gif': '🖼️', '.svg': '🖼️', '.webp': '🖼️',
        '.xlsx': '📊', '.xls': '📊', '.csv': '📊',
        '.docx': '📝', '.doc': '📝', '.pptx': '📊', '.ppt': '📊',
        '.zip': '📦', '.tar': '📦', '.gz': '📦',
        '.mp4': '🎬', '.mov': '🎬', '.mp3': '🎵',
    }
    items = []
    for f in files:
        size = f.stat().st_size
        size_str = f"{size // 1024} KB" if size >= 1024 else f"{size} B"
        icon = EXT_ICON.get(f.suffix.lower(), '📎')
        rel = f"../../docs/req/{f.name}"
        items.append(
            f'<li style="padding:0.5rem 0;border-bottom:1px solid var(--border)">'
            f'{icon} <a href="{rel}" download="{f.name}" target="_blank"'
            f' style="color:var(--accent)">{esc(f.name)}</a>'
            f' <span style="color:var(--text-muted);font-size:0.8125rem">({size_str})</span>'
            f'</li>'
        )
    return (
        '<section style="margin-top:2rem;padding:1.5rem;background:#fff;'
        'border:1px solid var(--border);border-radius:8px;">'
        '<h2 style="margin-top:0">📎 附件與素材 (req/)</h2>'
        f'<p style="color:var(--text-muted);font-size:0.875rem;margin-bottom:0.75rem">'
        f'共 {len(files)} 個附件，點擊下載</p>'
        '<ul style="list-style:none;padding:0;margin:0">'
        + ''.join(items) +
        '</ul></section>'
    )

def _deploy_canonical_assets(pages_dir):
    """Sync `pages/assets/{app.js,style.css}` from gendoc canonical source.

    Source resolution: `<gendoc>/docs/pages/assets/`, located two directory
    levels up from this script (works for both dev path
    `~/projects/gendoc/tools/gen_html/gen_html.py` and runtime path
    `~/.claude/skills/gendoc/tools/bin/gen_html.py`).

    Always overwrites — target dirs may have stale copies from prior runs
    that pre-date current sidebar/tab handlers (실機 erp/pet 上的 N1 sidebar
    壞掉 root cause).
    """
    src_dir = Path(__file__).resolve().parent.parent.parent / 'docs' / 'pages' / 'assets'
    if not src_dir.is_dir():
        return  # silent — running outside the gendoc tree (rare)
    target_dir = pages_dir / 'assets'
    target_dir.mkdir(exist_ok=True)
    for name in ('app.js', 'style.css'):
        src = src_dir / name
        if src.is_file():
            (target_dir / name).write_bytes(src.read_bytes())


def main():
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    _deploy_canonical_assets(PAGES_DIR)

    doc_pages = [('index', '首頁', '🏠')]
    known_order = ['IDEA', 'BRD', 'PRD', 'PDD', 'VDD', 'EDD', 'ARCH', 'API', 'SCHEMA',
                   'FRONTEND', 'AUDIO', 'ANIM', 'CLIENT_IMPL', 'CONSTANTS',
                   'test-plan', 'runbook', 'LOCAL_DEPLOY', 'RTM', 'ALIGN_REPORT']
    known_doc_entries = []
    for name in known_order:
        p = DOCS_DIR / f"{name}.md"
        if p.exists():
            s = name.lower()
            label, icon = PAGE_META.get(s, (name, '📄'))
            doc_pages.append((s, label, icon))
            known_doc_entries.append((s, label, p))

    extra_doc_entries = []
    known_slugs = {'readme'} | {s for s, _, _ in doc_pages}
    for p in sorted(DOCS_DIR.glob("*.md")):
        s = p.stem.lower()
        if s in known_slugs:
            continue
        label_str, icon_str = PAGE_META.get(s, (p.stem.replace('_', ' ').title(), '📄'))
        doc_pages.append((s, label_str, icon_str))
        extra_doc_entries.append((s, label_str, p))

    client_bdd_dir = FEATURES_DIR / "client"
    server_bdd_features = (sorted(FEATURES_DIR.glob("*.feature"))
                           if FEATURES_DIR.exists() else [])
    client_bdd_features = (sorted(client_bdd_dir.rglob("*.feature"))
                           if client_bdd_dir.exists() else [])
    has_server_bdd = bool(server_bdd_features)
    has_client_bdd = bool(client_bdd_features)
    if has_server_bdd:
        doc_pages.append(('bdd-server', 'Server BDD', '🧪'))
    if has_client_bdd:
        doc_pages.append(('bdd-client', 'Client BDD', '🧪'))

    has_req = (REQ_DIR.exists() and
               any(f for f in REQ_DIR.iterdir() if f.is_file() and not f.name.startswith('.')))

    server_diagrams, frontend_diagrams = scan_diagram_pages()
    sub_docs = scan_subdirectory_docs()
    puml_files = scan_puml_files()

    search_data = {}

    def write_page(filename, content, title, banner, current, is_index=False):
        out_path = PAGES_DIR / filename
        # B4: protect existing files under pages/prototype/ — gendoc-gen-prototype
        # writes interactive HTML there; gen_html mirroring docs/prototype/*.md
        # must not overwrite gen-prototype's output.
        if out_path.exists():
            try:
                rel_parts = out_path.relative_to(PAGES_DIR).parts
            except ValueError:
                rel_parts = ()
            if 'prototype' in rel_parts:
                print(f"↪ skip {filename} (prototype/ preserved)")
                return
        html = render_page(content, title, banner,
                           doc_pages, server_diagrams, frontend_diagrams,
                           sub_docs, current, is_index, has_req=has_req, puml_files=puml_files)
        # Rewrite paths to be valid under server root = PAGES_DIR
        html = rewrite_pages_paths(html, out_path, PAGES_DIR)
        # B2: ensure parent dir exists for nested filenames (e.g. "req/x.html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html)
        exc = re.sub(r'<[^>]+>', '', content)[:150]
        search_data[filename] = {"url": filename, "title": title, "excerpt": exc}
        print(f"✓ {filename}")

    # index.html
    readme = BASE / "README.md"
    proto_section_html = prototype_cards_section()
    cards = doc_cards_section(doc_pages, server_diagrams, frontend_diagrams)
    if readme.exists():
        body = (md_to_html(readme.read_text(), src_dir=BASE)
                + proto_section_html + cards + health_section())
    else:
        body = (f'<h1>{APP_NAME} 文件中心</h1>'
                '<p>請從左側導覽列選擇文件。</p>'
                + proto_section_html + cards + health_section())
    write_page("index.html", body, f'{APP_NAME} 文件中心', f'{APP_NAME} 文件中心', 'index', True)

    for s, label, p in known_doc_entries:
        c = md_to_html(p.read_text(), src_dir=p.parent)
        if s == 'idea':
            c += req_section()
        write_page(f"{s}.html", c, label, label, s)

    for s, label, p in extra_doc_entries:
        c = md_to_html(p.read_text(), src_dir=p.parent)
        write_page(f"{s}.html", c, label, label, s)

    if has_server_bdd:
        parts = [f"## {f.name}\n\n```gherkin\n{f.read_text()}\n```"
                 for f in server_bdd_features]
        c = md_to_html('\n\n'.join(parts), src_dir=FEATURES_DIR)
        write_page("bdd-server.html", c, "Server BDD", "Server BDD Scenarios", 'bdd-server')

    if has_client_bdd:
        parts = [f"## {f.relative_to(client_bdd_dir)}\n\n```gherkin\n{f.read_text()}\n```"
                 for f in client_bdd_features]
        c = md_to_html('\n\n'.join(parts), src_dir=client_bdd_dir)
        write_page("bdd-client.html", c, "Client BDD", "Client BDD Scenarios", 'bdd-client')

    if has_req:
        req_body = (f'<h1>📎 原始素材 (req/)</h1>'
                    f'<p style="color:var(--text-muted)">專案原始素材與需求附件，點擊下載。</p>'
                    + req_section())
        write_page("req.html", req_body, "原始素材 (req/)", "原始素材 (req/)", 'req')

    for stem, label, icon, p in server_diagrams:
        c = md_to_html(p.read_text(), src_dir=p.parent)
        write_page(f"diagrams/{stem}.html", c, label, label, f'diagrams/{stem}')

    for stem, label, icon, p in frontend_diagrams:
        c = md_to_html(p.read_text(), src_dir=p.parent)
        write_page(f"diagrams/{stem}.html", c, label, label, f'diagrams/{stem}')

    # Subdirectory docs (recursive scan)
    sub_page_count = 0
    for subdir_name, entries in sub_docs.items():
        for slug, label, p in entries:
            c = md_to_html(p.read_text(), src_dir=p.parent)
            write_page(f"{slug}.html", c, label, f'{subdir_name}/ › {label}', slug)
            sub_page_count += 1

    # Standalone .puml files → rendered SVG pages
    for slug, label, p in puml_files:
        puml_text = p.read_text(encoding='utf-8')
        if not puml_text.strip().startswith('@startuml'):
            puml_text = '@startuml\n' + puml_text + '\n@enduml'
        svg = _plantuml_to_svg(puml_text)
        if svg:
            c = (f'<h1>{esc(label)}</h1>'
                 f'<div class="diagram-container diagram-container--puml">{svg}</div>')
        else:
            c = (f'<h1>{esc(label)}</h1>'
                 f'<pre><code class="language-plantuml">{esc(puml_text)}</code></pre>'
                 f'<p style="color:var(--text-muted)">⚠️ PlantUML 圖表無法生成'
                 f'（請確認本機已安裝 plantuml 或網路可連至 plantuml.com）</p>')
        write_page(f'{slug}.html', c, label, f'PlantUML › {label}', slug)

    (PAGES_DIR / "search-data.json").write_text(
        json.dumps(search_data, ensure_ascii=False, indent=2))
    print("✓ search-data.json")

    # ── Post-process：對 pages/ 內所有子目錄 HTML 也跑 path rewriter ──
    # gen_html 主流程只寫 pages/ root 的 .html；prototype/ 子目錄 HTML 由
    # gendoc-gen-prototype skill 直接寫，可能有 AI 寫錯的相對路徑（譬如
    # ../../../X 跳出 pages/ root）。在這層補做一次 rewrite。
    fixed_count = 0
    for sub_html in PAGES_DIR.rglob('*.html'):
        if sub_html.parent == PAGES_DIR:
            continue  # root 已在 write_page() 處理過
        try:
            text = sub_html.read_text(encoding='utf-8')
            new_text = rewrite_pages_paths(text, sub_html, PAGES_DIR)
            if new_text != text:
                sub_html.write_text(new_text, encoding='utf-8')
                fixed_count += 1
        except Exception:
            pass
    if fixed_count:
        print(f"✓ subdir path rewrite：{fixed_count} 個 HTML 修正")
    total_diag = len(server_diagrams) + len(frontend_diagrams)
    bdd_count = int(has_server_bdd) + int(has_client_bdd)
    req_count = int(has_req)
    sub_dirs_count = len(sub_docs)
    print(f"\n✅ 完成：{len(search_data)} 頁"
          f"（文件 + BDD×{bdd_count} + {total_diag} UML + {sub_page_count} 子目錄×{sub_dirs_count}dirs"
          f" + puml×{len(puml_files)} + req×{req_count}）"
          f"→ {PAGES_DIR}")

if __name__ == "__main__":
    main()
