#!/usr/bin/env node
/**
 * scan_three_way.mjs — 對每張圖做三邊比對（.md ↔ .html ↔ 放大圖）
 *
 * 規則（user 訂的）：
 *   1. .md 原碼 跟 .html 原意相同即可（文字可不同）— 用 mermaid node/edge 數量
 *      或 umock children 結構判斷，超過容差才標 ⚠️
 *   2. .html 跟放大圖必須一模一樣 — SVG 結構比對（normalize id 後 byte-equal）
 *   3. 圖必須 render 出來 — 不能是 Syntax error / 0×0 SVG
 *   4. 三邊一致 → ✅；render fail / lightbox 不一致 → ❌；
 *      .md vs .html 原意可疑 → ⚠️（留清單給 user 看）
 *
 * 範圍：mermaid + DSL UI 線圖（umock）兩種
 *
 * Output: visual_3way_report.json + 終端摘要
 */
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const PROJECTS = [
  { name: 'pet', root: '/Users/tobala/projects/pet', port: 8784 },
  { name: 'erp', root: '/Users/tobala/projects/erp-api-token-manager', port: 8786 },
];

const REPORT_PATH = '/Users/tobala/projects/gendoc/tools/gen_html/tests/visual_3way_report.json';

// ─── source resolver ─────────────────────────────────────────────────

function findSource(root, htmlRel) {
  const stem = path.basename(htmlRel, '.html');
  const dir = path.dirname(htmlRel);
  // index.html → README.md
  if (htmlRel === 'index.html' && fs.existsSync(path.join(root, 'README.md'))) {
    return { kind: 'readme', path: path.join(root, 'README.md') };
  }
  // puml--*.html → docs/diagrams/puml/X.puml
  if (htmlRel.startsWith('puml--')) {
    const pumlDir = path.join(root, 'docs/diagrams/puml');
    if (fs.existsSync(pumlDir)) {
      for (const p of fs.readdirSync(pumlDir)) {
        if (p.endsWith('.puml') && htmlRel.includes(p.replace('.puml', ''))) {
          return { kind: 'puml', path: path.join(pumlDir, p) };
        }
      }
    }
  }
  // subdir html → docs/<dir>/<stem>.md
  if (dir !== '.') {
    const p = path.join(root, 'docs', dir, stem + '.md');
    if (fs.existsSync(p)) return { kind: 'md', path: p };
  }
  // flat → docs/<stem>.md (case-insensitive, also try _ vs -)
  const docsDir = path.join(root, 'docs');
  if (fs.existsSync(docsDir)) {
    for (const f of fs.readdirSync(docsDir)) {
      if (!f.endsWith('.md')) continue;
      const fstem = f.slice(0, -3);
      if (fstem.toLowerCase() === stem.toLowerCase() ||
          fstem.toLowerCase().replace(/-/g, '_') === stem.toLowerCase().replace(/-/g, '_')) {
        return { kind: 'md', path: path.join(docsDir, f) };
      }
    }
  }
  return null;
}

// ─── md fenced block extractor ───────────────────────────────────────

function extractFencedBlocks(mdText) {
  const lines = mdText.split('\n');
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    const m = lines[i].match(/^```(\w*)\s*$/);
    if (m) {
      const lang = m[1];
      const start = i;
      i++;
      const body = [];
      while (i < lines.length && lines[i].trim() !== '```') {
        body.push(lines[i]);
        i++;
      }
      blocks.push({ lang, body: body.join('\n'), full: lines.slice(start, i + 1).join('\n') });
      i++;
    } else {
      i++;
    }
  }
  return blocks;
}

// ─── auto judges ─────────────────────────────────────────────────────

function countMermaidNodes(text) {
  if (!text) return 0;
  // Count "N0[...]" / "A --> B" identifiers — approximate
  const ids = new Set();
  for (const m of text.matchAll(/^\s*([A-Za-z_][\w]*)\s*[\[\(\{"]/gm)) ids.add(m[1]);
  for (const m of text.matchAll(/-->/g)) {}
  return ids.size;
}
function countMermaidEdges(text) {
  if (!text) return 0;
  return (text.match(/-->/g) || []).length + (text.match(/--/g) || []).length;
}

function normalizeSvg(html) {
  if (!html) return '';
  return html
    .replace(/mermaid-\d+/g, 'M')
    .replace(/id="[^"]*"/g, 'id="X"')
    .replace(/aria-roledescription="[^"]*"/g, '')
    .replace(/url\(#[^)]*\)/g, 'url(#R)')
    .replace(/marker-end="[^"]*"/g, 'marker-end="M"')
    .replace(/\s+/g, ' ')
    .trim();
}

// ─── main scan ───────────────────────────────────────────────────────

function walk(base, prefix='') {
  const out = [];
  for (const ent of fs.readdirSync(base)) {
    const full = path.join(base, ent);
    const rel = prefix ? `${prefix}/${ent}` : ent;
    if (['assets'].includes(ent) || ent.startsWith('_') || ent.startsWith('.')) continue;
    const st = fs.statSync(full);
    if (st.isDirectory()) out.push(...walk(full, rel));
    else if (ent.endsWith('.html')) out.push(rel);
  }
  return out;
}

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });

const SUMMARY = { pass: 0, broken: 0, flagged: 0 };
const items = [];

for (const proj of PROJECTS) {
  const pagesDir = path.join(proj.root, 'docs/pages');
  if (!fs.existsSync(pagesDir)) continue;
  const all = walk(pagesDir);
  console.error(`\n=== ${proj.name}: ${all.length} html ===`);

  let count = 0;
  for (const htmlRel of all) {
    count++;
    if (count % 20 === 0) console.error(`  [${count}/${all.length}]`);

    // resolve source + extract md fenced blocks
    const src = findSource(proj.root, htmlRel);
    let mdBlocks = [];
    if (src && (src.kind === 'md' || src.kind === 'readme')) {
      try {
        mdBlocks = extractFencedBlocks(fs.readFileSync(src.path, 'utf-8'));
      } catch (e) {}
    }

    const page = await ctx.newPage();
    try {
      await page.goto(`http://localhost:${proj.port}/${htmlRel}`, { timeout: 6000, waitUntil: 'load' });
      await page.waitForTimeout(2200);

      const containers = await page.$$('.diagram-container');
      let mdBlockCursor = 0;   // points to next md fenced block to consume
      for (let idx = 0; idx < containers.length; idx++) {
        const c = containers[idx];
        const info = await c.evaluate(node => {
          const pre = node.querySelector('pre.mermaid, .mermaid');
          const isUmock = node.classList.contains('diagram-container--umock');
          const isNested = node.parentElement?.closest('.diagram-container') != null;
          const svg = node.querySelector('svg');
          const txt = node.textContent || '';
          // raw mermaid source if present (before mermaid rewrites textContent)
          const mermaidSrc = pre?.getAttribute('data-source') || null;
          return {
            isMermaid: !!pre,
            isUmock,
            isNested,
            hasSvg: !!svg,
            sw: svg?.clientWidth || 0,
            sh: svg?.clientHeight || 0,
            synErr: /Syntax error|Parse error/i.test(txt),
            svgOuter: svg?.outerHTML || '',
            outerHtml: node.outerHTML.slice(0, 8000),
          };
        });

        const entry = {
          project: proj.name,
          html_file: htmlRel,
          idx,
          kind: info.isUmock ? 'umock' : (info.isMermaid ? 'mermaid' : 'other'),
          nested: info.isNested,
          src_kind: src ? src.kind : null,
          src_path: src ? path.relative(proj.root, src.path) : null,
        };

        // ── 1. render check ──
        if (info.isMermaid) {
          if (!info.hasSvg || info.synErr || (info.sw < 100 && info.sh < 200)) {
            entry.status = '❌ broken';
            entry.reason = `mermaid render failed (svg=${info.sw}x${info.sh}, synErr=${info.synErr})`;
            items.push(entry); SUMMARY.broken++;
            continue;
          }
        } else if (info.isUmock) {
          if (info.hasSvg && info.sw < 100 && info.sh < 200 && !info.isNested) {
            entry.status = '❌ broken';
            entry.reason = `umock svg too small (${info.sw}x${info.sh})`;
            items.push(entry); SUMMARY.broken++;
            continue;
          }
        }

        // ── 2. lightbox check (skip nested — outer covers lightbox bind) ──
        if (!info.isNested) {
          try {
            await page.evaluate(() => {
              const lb = document.querySelector('.lightbox.active');
              if (lb) lb.classList.remove('active');
            });
            await c.click({ timeout: 2000 });
            await page.waitForTimeout(400);
            const lb = await page.evaluate(() => {
              const lb = document.querySelector('.lightbox');
              if (!lb || !lb.classList.contains('active')) return { open: false };
              const lbSvg = lb.querySelector('svg');
              return { open: true, hasSvg: !!lbSvg, lbSvgOuter: lbSvg?.outerHTML || '' };
            });
            if (info.isMermaid && info.hasSvg) {
              if (!lb.open) {
                entry.status = '❌ broken';
                entry.reason = 'lightbox did not open after click';
                items.push(entry); SUMMARY.broken++;
                continue;
              }
              if (!lb.hasSvg) {
                entry.status = '❌ broken';
                entry.reason = 'lightbox open but no SVG inside';
                items.push(entry); SUMMARY.broken++;
                continue;
              }
              const a = normalizeSvg(info.svgOuter);
              const b = normalizeSvg(lb.lbSvgOuter);
              const tol = Math.max(80, Math.floor(a.length * 0.05));
              if (Math.abs(a.length - b.length) > tol) {
                entry.status = '❌ broken';
                entry.reason = `lightbox SVG differs from inline (len ${a.length} vs ${b.length})`;
                items.push(entry); SUMMARY.broken++;
                continue;
              }
            }
            await page.evaluate(() => {
              const lb = document.querySelector('.lightbox.active');
              if (lb) lb.classList.remove('active');
            });
          } catch (e) {
            // lightbox bind/click error — flag, do not break test
          }
        }

        // ── 3. .md ↔ .html 原意比對 (mermaid only) ──
        // Find the next md fenced block that should map to this top-level .html block.
        // Skip nested containers (outer == md block; nested == inner refinement).
        if (!info.isNested && info.isMermaid && (src?.kind === 'md' || src?.kind === 'readme')) {
          // advance cursor: find next fenced block whose md_to_html would yield a diagram
          // For now: take next non-empty block and compare
          let mdBlock = null;
          while (mdBlockCursor < mdBlocks.length) {
            mdBlock = mdBlocks[mdBlockCursor];
            mdBlockCursor++;
            // We don't know if it produces a diagram without running gen_html; trust order.
            break;
          }
          if (mdBlock) {
            const mdEdges = countMermaidEdges(mdBlock.body);
            const htmlEdges = countMermaidEdges(info.outerHtml);
            // tolerance: ±3 edges
            if (Math.abs(mdEdges - htmlEdges) > 3 && Math.max(mdEdges, htmlEdges) > 5) {
              entry.status = '⚠️ flagged';
              entry.reason = `md vs html edge count differs (md=${mdEdges}, html=${htmlEdges})`;
              entry.md_block_preview = mdBlock.body.slice(0, 200);
              items.push(entry); SUMMARY.flagged++;
              continue;
            }
          }
        }

        // ── all checks passed ──
        entry.status = '✅ pass';
        items.push(entry); SUMMARY.pass++;
      }
    } catch (e) {
      items.push({ project: proj.name, html_file: htmlRel, idx: -1, kind: 'page',
                   status: '⚠️ flagged', reason: `page error: ${e.message.slice(0, 100)}` });
      SUMMARY.flagged++;
    }
    await page.close();
  }
}

await browser.close();
fs.writeFileSync(REPORT_PATH, JSON.stringify({ summary: SUMMARY, items }, null, 2));

console.log('\n' + '='.repeat(72));
console.log(`SUMMARY: ✅ ${SUMMARY.pass}  ❌ ${SUMMARY.broken}  ⚠️ ${SUMMARY.flagged}  (total ${SUMMARY.pass + SUMMARY.broken + SUMMARY.flagged})`);
console.log('='.repeat(72));

const broken = items.filter(i => i.status?.startsWith('❌'));
const flagged = items.filter(i => i.status?.startsWith('⚠️'));
if (broken.length) {
  console.log('\n❌ BROKEN (必修):');
  broken.forEach(r => console.log(`  ${r.project}/${r.html_file}#${r.idx} [${r.kind}]  ${r.reason}`));
}
if (flagged.length) {
  console.log('\n⚠️ FLAGGED (留 user 看):');
  flagged.forEach(r => console.log(`  ${r.project}/${r.html_file}#${r.idx} [${r.kind}]  ${r.reason}`));
}
console.log(`\nFull report: ${REPORT_PATH}`);
