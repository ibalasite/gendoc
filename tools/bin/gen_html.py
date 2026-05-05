#!/usr/bin/env python3
# tools/bin/gen_html.py
# VERSION: 3.7.0
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

def _plantuml_to_svg(text: str) -> Optional[str]:
    """Convert PlantUML text → inline SVG string. Returns None on failure.
    Priority: 1) local plantuml CLI  2) plantuml.com server  3) None"""
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

    # 2) Fallback: plantuml.com server
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

    if svg:
        # Strip XML declaration so SVG can be embedded inline
        svg = re.sub(r'<\?xml[^>]+\?>\s*', '', svg).strip()
        _puml_cache[text] = svg
    return svg

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
    """Fix mermaid v11 breaking patterns in flowchart/graph/sequenceDiagram blocks."""
    if not lines:
        return lines
    first = next((l.strip() for l in lines if l.strip()), '')
    is_flowchart = bool(re.match(r'^(flowchart|graph)\b', first))
    is_sequence  = bool(re.match(r'^sequenceDiagram', first))
    if not is_flowchart and not is_sequence:
        return lines

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
        return line

    def fix_sequence_line(line):
        # Mermaid v11: semicolons in message text are treated as statement separators
        msg = re.match(r'^(\s*\S.*?(?:->>|-->>|->x|-->x|->>|->|-->)\s*\S[^:]*:\s*)(.*)', line, re.DOTALL)
        if msg:
            prefix, message = msg.group(1), msg.group(2)
            message = message.replace(';', ',').replace('\\n', ' ')
            line = prefix + message
        return line

    if is_flowchart:
        return [fix_flowchart_line(l) for l in lines]
    else:
        return [fix_sequence_line(l) for l in lines]

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
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
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
        elif s.startswith('```'):
            lang = s[3:].strip()
            block = []
            i += 1
            while i < len(lines) and lines[i].strip() != '```':
                block.append(esc(lines[i]))
                i += 1
            cls = f'language-{lang}' if lang else ''
            out.append(f'<pre><code class="{cls}">' + '\n'.join(block) + '</code></pre>')
        elif s.startswith('#### '):
            out.append(f'<h4>{inline_md(s[5:], src_dir)}</h4>')
        elif s.startswith('### '):
            out.append(f'<h3>{inline_md(s[4:], src_dir)}</h3>')
        elif s.startswith('## '):
            out.append(f'<h2>{inline_md(s[3:], src_dir)}</h2>')
        elif s.startswith('# '):
            out.append(f'<h1>{inline_md(s[2:], src_dir)}</h1>')
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
    Slug format: '{subdir}__{relative_stem}' (lowercase, / → -)
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
            slug = subdir.name.lower() + '__' + str(rel).replace('/', '-').replace('\\', '-').lower()
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

def make_sidebar(doc_pages, server_diagrams, frontend_diagrams, sub_docs, current, has_req=False, puml_files=None):
    def link(slug, label, icon=''):
        cls = ' active' if slug == current else ''
        prefix = f'{icon} ' if icon else ''
        return f'<a class="sidebar__link{cls}" href="{slug}.html">{prefix}{label}</a>'

    sections = []

    # ── Main docs ──────────────────────────────────────────
    sections.append('<div class="sidebar__section">')
    sections.append('<div class="sidebar__label">文件</div>')
    for slug, label, icon in doc_pages:
        sections.append(link(slug, label, icon))
    sections.append('</div>')

    # ── Subdirectory groups (collapsible) ──────────────────
    for subdir_name, entries in sub_docs.items():
        is_active = any(slug == current for slug, _, _ in entries)
        open_attr = ' open' if is_active else ''
        icon = _DIR_ICONS.get(subdir_name.lower(), '📁')
        sections.append('<div class="sidebar__section">')
        sections.append(f'<details{open_attr}>')
        sections.append(f'<summary>{icon} {subdir_name}/</summary>')
        for slug, label, _ in entries:
            sections.append(link(slug, label))
        # If req/ subdir: also link to download page
        if subdir_name.lower() == 'req' and has_req:
            sections.append(link('req', '📥 附件下載清單'))
        sections.append('</details>')
        sections.append('</div>')

    # ── req download page (only if req/ not in sub_docs) ──
    if has_req and 'req' not in sub_docs:
        sections.append('<div class="sidebar__section">')
        sections.append('<div class="sidebar__label">原始素材</div>')
        sections.append(link('req', 'req/ 素材清單', '📎'))
        sections.append('</div>')

    # ── PlantUML standalone files ──────────────────────────
    if puml_files:
        is_active_puml = any(slug == current for slug, _, _ in puml_files)
        open_attr = ' open' if is_active_puml else ''
        sections.append('<div class="sidebar__section">')
        sections.append(f'<details{open_attr}>')
        sections.append('<summary>📐 PlantUML</summary>')
        for slug, label, _ in puml_files:
            sections.append(link(slug, label))
        sections.append('</details>')
        sections.append('</div>')

    # ── UML diagrams ───────────────────────────────────────
    if server_diagrams:
        sections.append('<div class="sidebar__section">')
        sections.append('<div class="sidebar__label">Server UML</div>')
        for slug, label, icon, _ in server_diagrams:
            sections.append(link(f'diag-{slug}', label, icon))
        sections.append('</div>')

    if frontend_diagrams:
        sections.append('<div class="sidebar__section">')
        sections.append('<div class="sidebar__label">Frontend UML</div>')
        for slug, label, icon, _ in frontend_diagrams:
            sections.append(link(f'diag-{slug}', label, icon))
        sections.append('</div>')

    return '\n'.join(sections)

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
    sidebar_html = make_sidebar(doc_pages, server_diagrams, frontend_diagrams, sub_docs, current, has_req=has_req, puml_files=puml_files)
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
            f'<a class="index-card" href="diag-{server_diagrams[0][0] if server_diagrams else frontend_diagrams[0][0]}.html">'
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

def main():
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    (PAGES_DIR / "assets").mkdir(exist_ok=True)

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
        html = render_page(content, title, banner,
                           doc_pages, server_diagrams, frontend_diagrams,
                           sub_docs, current, is_index, has_req=has_req, puml_files=puml_files)
        (PAGES_DIR / filename).write_text(html)
        exc = re.sub(r'<[^>]+>', '', content)[:150]
        search_data[filename] = {"url": filename, "title": title, "excerpt": exc}
        print(f"✓ {filename}")

    # index.html
    readme = BASE / "README.md"
    cards = doc_cards_section(doc_pages, server_diagrams, frontend_diagrams)
    if readme.exists():
        body = md_to_html(readme.read_text(), src_dir=BASE) + cards + health_section()
    else:
        body = (f'<h1>{APP_NAME} 文件中心</h1>'
                '<p>請從左側導覽列選擇文件。</p>' + cards + health_section())
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
        write_page(f"diag-{stem}.html", c, label, label, f'diag-{stem}')

    for stem, label, icon, p in frontend_diagrams:
        c = md_to_html(p.read_text(), src_dir=p.parent)
        write_page(f"diag-{stem}.html", c, label, label, f'diag-{stem}')

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
