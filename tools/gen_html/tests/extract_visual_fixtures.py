#!/usr/bin/env python3
"""Extract visual-lock fixtures driven by the scan report (not from .md walk).

For each of the 256 scan-pass items, locate the source and build a fixture:
  - source = .md / .puml / README.md   →  mode="replay"
      input = original fenced block (or .puml content)
      expected = the Nth <div class="diagram-container..."> outerHTML produced
                 by gen_html for that source (deterministic, reproducible)
  - source = none (stale flat .html)   →  mode="snapshot"
      expected = the Nth diagram block from the stored .html (today's content)
      no input; test only verifies the .html file still holds this block.

Excludes the 3 真實破圖 listed in BROKEN.

Output:
  fixtures/visual_lock/{pet,erp}/<safe-file>-block<idx>.json
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'
FIX_DIR = REPO / 'tools' / 'gen_html' / 'tests' / 'fixtures' / 'visual_lock'
REPORT = REPO / 'tools' / 'gen_html' / 'tests' / 'visual_report.json'

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)

PROJ_ROOT = {
    'pet': pathlib.Path('/Users/tobala/projects/pet'),
    'erp': pathlib.Path('/Users/tobala/projects/erp-api-token-manager'),
}

# 3 broken (in logic/issues.md P group) — never lock these.
BROKEN = {
    ('pet', 'frontend.html', 2),
    ('pet', 'frontend.html', 5),
    ('erp', 'frontend.html', 1),
}


# ─── helpers ──────────────────────────────────────────────────────────

def find_source(proj: str, html_relpath: str):
    """Return ('md'|'puml'|'readme', path) or None for stale."""
    root = PROJ_ROOT[proj]
    stem = pathlib.Path(html_relpath).stem
    rel_dir = pathlib.Path(html_relpath).parent
    if stem == 'index' and html_relpath == 'index.html':
        r = root / 'README.md'
        if r.is_file(): return ('readme', r)
    if html_relpath.startswith('puml--'):
        for puml in (root / 'docs/diagrams/puml').glob('*.puml'):
            if puml.stem in html_relpath:
                return ('puml', puml)
    if '/' in html_relpath:
        p = root / 'docs' / rel_dir / f'{stem}.md'
        if p.is_file(): return ('md', p)
    for md in (root / 'docs').glob('*.md'):
        if md.stem.lower() == stem.lower():
            return ('md', md)
    for md in (root / 'docs').glob('*.md'):
        if md.stem.lower().replace('-', '_') == stem.lower().replace('-', '_'):
            return ('md', md)
    return None


def extract_all_diagram_blocks(html_text: str) -> list[str]:
    """Return all <div class="diagram-container..."> outerHTML strings
    in document order (flat, including nested — to match scan idx semantics
    using document.querySelectorAll which yields nested elements too)."""
    blocks = []
    # Find all opening tags, walk depth, capture each top-level + nested
    pat = re.compile(r'<div(?:\s+class="diagram-container[^"]*")', re.IGNORECASE)
    # Simpler: use a depth walk per opening
    pos = 0
    div_open_re = re.compile(r'<div\b[^>]*?class="diagram-container[^"]*"[^>]*>', re.IGNORECASE)
    while True:
        m = div_open_re.search(html_text, pos)
        if not m: break
        # find matching </div>
        i = m.end()
        depth = 1
        # advance scanning for nested <div> opens & </div> closes
        scan_re = re.compile(r'</?div\b', re.IGNORECASE)
        while depth > 0:
            sm = scan_re.search(html_text, i)
            if not sm: break
            if sm.group(0).startswith('</'):
                depth -= 1
                i = sm.end() + 1   # past >
            else:
                depth += 1
                i = sm.end()
        # i points just past the closing </div>
        end = html_text.find('</div>', i - 1)
        if end == -1:
            # fallback: best-effort
            blocks.append(html_text[m.start():i].strip())
        else:
            blocks.append(html_text[m.start():end + len('</div>')].strip())
        pos = m.end()
    return blocks


def get_block_at_idx(html_text: str, idx: int) -> str | None:
    blocks = extract_all_diagram_blocks(html_text)
    return blocks[idx] if 0 <= idx < len(blocks) else None


def render_source_to_html(kind: str, src_path: pathlib.Path) -> str:
    """Run gen_html's md_to_html (or equivalent for puml) and return rendered HTML."""
    if kind in ('md', 'readme'):
        text = src_path.read_text(encoding='utf-8')
        return gh.md_to_html(text, src_dir=src_path.parent)
    if kind == 'puml':
        # puml has its own path in gen_html.main(); for fixture purposes,
        # we use the rendered .html file directly (snapshot semantics on puml).
        return ''
    return ''


# ─── main ─────────────────────────────────────────────────────────────

def main():
    # Clear old fixtures
    if FIX_DIR.exists():
        for f in FIX_DIR.rglob('*.json'):
            f.unlink()
    FIX_DIR.mkdir(parents=True, exist_ok=True)

    report = json.loads(REPORT.read_text(encoding='utf-8'))
    pass_items = [r for r in report['items'] if r['status'].startswith('✅')]

    counts = {'replay_md': 0, 'replay_readme': 0, 'replay_puml': 0,
              'snapshot_stale': 0, 'skipped_broken': 0, 'skipped_no_source': 0}

    for r in pass_items:
        proj, html_rel, idx = r['project'], r['file'], r['idx']
        if (proj, html_rel, idx) in BROKEN:
            counts['skipped_broken'] += 1
            continue

        # Resolve the stored html file for snapshot data
        html_path = PROJ_ROOT[proj] / 'docs/pages' / html_rel
        if not html_path.is_file():
            counts['skipped_no_source'] += 1
            continue
        stored_html = html_path.read_text(encoding='utf-8')
        stored_block = get_block_at_idx(stored_html, idx)
        if stored_block is None:
            counts['skipped_no_source'] += 1
            continue

        src = find_source(proj, html_rel)
        proj_dir = FIX_DIR / proj
        proj_dir.mkdir(exist_ok=True)
        safe = html_rel.replace('/', '__').replace('.html', '')
        fid = f'{safe}-block{idx}'

        if src is None:
            # stale flat → snapshot mode
            fixture = {
                'id': fid,
                'project': proj,
                'html_file': html_rel,
                'block_idx': idx,
                'mode': 'snapshot',
                'reason': 'stale flat .html — no source markdown; locked as static snapshot (user policy "舊的不砍")',
                'expected_html': stored_block,
            }
            counts['snapshot_stale'] += 1
        elif src[0] == 'puml':
            # puml is generated by a different gen_html path; lock as snapshot too
            fixture = {
                'id': fid,
                'project': proj,
                'html_file': html_rel,
                'block_idx': idx,
                'mode': 'snapshot',
                'source_file': str(src[1].relative_to(PROJ_ROOT[proj])),
                'reason': 'puml rendered via separate path; locked as snapshot of current output',
                'expected_html': stored_block,
            }
            counts['replay_puml'] += 1
        else:
            # md / readme → replay mode
            kind, src_path = src
            rendered = render_source_to_html(kind, src_path)
            rendered_blocks = extract_all_diagram_blocks(rendered)
            if idx >= len(rendered_blocks):
                # md_to_html produced fewer blocks than stored .html → fallback to snapshot
                fixture = {
                    'id': fid, 'project': proj, 'html_file': html_rel,
                    'block_idx': idx, 'mode': 'snapshot',
                    'source_file': str(src_path.relative_to(PROJ_ROOT[proj])),
                    'reason': f'md_to_html produced only {len(rendered_blocks)} blocks but stored idx={idx}; snapshot fallback',
                    'expected_html': stored_block,
                }
                counts['snapshot_stale'] += 1
            else:
                fixture = {
                    'id': fid,
                    'project': proj,
                    'html_file': html_rel,
                    'block_idx': idx,
                    'mode': 'replay',
                    'source_kind': kind,
                    'source_file': str(src_path.relative_to(PROJ_ROOT[proj])),
                    'input_md': src_path.read_text(encoding='utf-8'),
                    'expected_html': rendered_blocks[idx],
                }
                if kind == 'readme':
                    counts['replay_readme'] += 1
                else:
                    counts['replay_md'] += 1

        out_path = proj_dir / f'{fid}.json'
        out_path.write_text(json.dumps(fixture, indent=2, ensure_ascii=False), encoding='utf-8')

    print('=' * 72)
    print(f'EXTRACTED — by mode:')
    for k, v in counts.items(): print(f'  {k}: {v}')
    total = sum(v for k, v in counts.items() if not k.startswith('skipped'))
    print(f'  TOTAL fixtures: {total}')
    print('=' * 72)


if __name__ == '__main__':
    main()
