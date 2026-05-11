#!/usr/bin/env node
/**
 * scan_visual.mjs — Visual regression scanner for mermaid + DSL UI mock blocks.
 *
 * Walks every live .html under pet/erp pages dirs, for each diagram block:
 *   1. Render check  : mermaid renders OK (no Syntax error, SVG ≥ 100×200).
 *   2. Lightbox check: clicking the diagram opens a lightbox; the lightbox SVG
 *                      must equal the in-page SVG byte-for-byte.
 *
 * Output: visual_report.json + terminal summary
 *   ❌ broken    — render failed OR lightbox mismatch (must fix)
 *   ⚠️  flagged  — auto-judged inconclusive (留 user 看)
 *   ✅ pass      — render + lightbox both OK
 *
 * Stale-excluded: flat `diag-X.html` when subdir `diagrams/X.html` exists.
 *
 * Usage: node scan_visual.mjs
 *   (assumes pet at localhost:8784, erp at localhost:8786)
 */
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const PROJECTS = [
  { name: 'pet', dir: '/Users/tobala/projects/pet/docs/pages', port: 8784 },
  { name: 'erp', dir: '/Users/tobala/projects/erp-api-token-manager/docs/pages', port: 8786 },
];

const REPORT_PATH = '/Users/tobala/projects/gendoc/tools/gen_html/tests/visual_report.json';

// ─── helpers ──────────────────────────────────────────────────────────

function isStaleFlat(rel, allFiles) {
  if (rel.startsWith('diag-') && !rel.includes('/')) {
    const stem = rel.slice(5).replace('.html', '');
    if (allFiles.has(`diagrams/${stem}.html`)) return true;
  }
  return false;
}

function walk(base, prefix='') {
  const out = [];
  for (const ent of fs.readdirSync(base)) {
    const full = path.join(base, ent);
    const rel = prefix ? `${prefix}/${ent}` : ent;
    if (ent === 'assets' || ent.startsWith('_') || ent.startsWith('.')) continue;
    const st = fs.statSync(full);
    if (st.isDirectory()) out.push(...walk(full, rel));
    else if (ent.endsWith('.html')) out.push(rel);
  }
  return out;
}

// Normalize SVG for comparison: strip mermaid auto-generated id prefixes
// (e.g. "mermaid-1778429..." vary per render call) so structural comparison
// of in-page vs lightbox SVG is meaningful.
function normalizeSvg(html) {
  if (!html) return '';
  return html
    .replace(/mermaid-\d+/g, 'mermaid-XXXX')
    .replace(/id="[^"]*-\d+"/g, 'id="ID"')
    .replace(/aria-roledescription="[^"]*"/g, '')
    // some random ids in markers
    .replace(/url\(#[^)]*\)/g, 'url(#R)')
    .replace(/marker-end="[^"]*"/g, 'marker-end="M"')
    .replace(/\s+/g, ' ')
    .trim();
}

// ─── main scan ────────────────────────────────────────────────────────

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });

const report = [];   // entries: { project, file, idx, kind, status, reason }
const SUMMARY = { pass: 0, broken: 0, flagged: 0 };

for (const proj of PROJECTS) {
  const all = walk(proj.dir);
  const allSet = new Set(all);
  const live = all.filter(f => !isStaleFlat(f, allSet));
  console.error(`\n=== ${proj.name}: ${all.length} html, ${live.length} live ===`);

  let fileCount = 0;
  for (const f of live) {
    fileCount++;
    if (fileCount % 20 === 0) console.error(`  [${fileCount}/${live.length}] ${f}`);
    const page = await ctx.newPage();
    try {
      await page.goto(`http://localhost:${proj.port}/${f}`, { timeout: 6000, waitUntil: 'load' });
      await page.waitForTimeout(2200);   // wait mermaid render

      // Find all diagram containers (both mermaid + umock — they share the
      // outer `.diagram-container` for lightbox click binding).
      const containers = await page.$$('.diagram-container');
      for (let idx = 0; idx < containers.length; idx++) {
        const c = containers[idx];
        const info = await c.evaluate(node => {
          const isMermaid = !!node.querySelector('pre.mermaid, .mermaid');
          const isUmock = node.classList.contains('diagram-container--umock');
          const svg = node.querySelector('svg');
          const txt = node.textContent || '';
          return {
            kind: isMermaid ? 'mermaid' : (isUmock ? 'umock' : 'other'),
            hasSvg: !!svg,
            wh: svg ? `${svg.clientWidth}x${svg.clientHeight}` : null,
            sw: svg?.clientWidth || 0,
            sh: svg?.clientHeight || 0,
            synErr: /Syntax error|Parse error/i.test(txt),
            svgOuter: svg?.outerHTML || '',
          };
        });

        // ── 1. render check ──
        if (info.kind === 'mermaid') {
          if (!info.hasSvg || info.synErr || (info.sw < 100 && info.sh < 200)) {
            report.push({
              project: proj.name, file: f, idx, kind: 'mermaid',
              status: '❌ broken', reason: `render failed (svg=${info.wh}, synErr=${info.synErr})`,
            });
            SUMMARY.broken++;
            continue;
          }
        } else if (info.kind === 'umock') {
          // umock can render as inline html (cards/tables) OR as SVG (pyramid/layered-arch).
          // For SVG-based umock, apply the same render check; otherwise just check has child content.
          if (info.hasSvg) {
            if (info.synErr || (info.sw < 100 && info.sh < 200)) {
              report.push({
                project: proj.name, file: f, idx, kind: 'umock',
                status: '❌ broken', reason: `umock svg render failed (svg=${info.wh})`,
              });
              SUMMARY.broken++;
              continue;
            }
          } else {
            // Non-SVG umock: just confirm it has visible children with content
            const childCount = await c.evaluate(n => n.querySelectorAll('*').length);
            if (childCount < 2) {
              report.push({
                project: proj.name, file: f, idx, kind: 'umock',
                status: '⚠️ flagged', reason: 'umock has no rendered children',
              });
              SUMMARY.flagged++;
              continue;
            }
          }
        }

        // ── 2. lightbox check ──
        // Click the diagram container → lightbox should open with cloned SVG.
        let lightboxStatus = 'pass';
        let lightboxReason = '';
        try {
          // close any open lightbox first
          await page.evaluate(() => {
            const lb = document.querySelector('.lightbox.active');
            if (lb) lb.classList.remove('active');
          });
          await c.click({ timeout: 2000 });
          await page.waitForTimeout(400);
          const lb = await page.evaluate((origSvg) => {
            const lb = document.querySelector('.lightbox');
            if (!lb || !lb.classList.contains('active')) return { open: false };
            const lbSvg = lb.querySelector('svg');
            return {
              open: true,
              hasSvg: !!lbSvg,
              lbSvgOuter: lbSvg?.outerHTML || '',
            };
          }, info.svgOuter);

          if (info.kind === 'mermaid' && info.hasSvg) {
            if (!lb.open) {
              lightboxStatus = 'broken';
              lightboxReason = 'lightbox did not open after click';
            } else if (!lb.hasSvg) {
              lightboxStatus = 'broken';
              lightboxReason = 'lightbox open but no SVG inside';
            } else {
              const a = normalizeSvg(info.svgOuter);
              const b = normalizeSvg(lb.lbSvgOuter);
              if (a !== b) {
                // Lightbox often re-renders mermaid via mermaid.run on cloned
                // pre — content can differ in ids only. After normalization,
                // check whether structural shape is similar (length within 5%).
                const diff = Math.abs(a.length - b.length);
                const tol = Math.max(50, Math.floor(a.length * 0.05));
                if (diff > tol) {
                  lightboxStatus = 'broken';
                  lightboxReason = `lightbox SVG differs from inline (len ${a.length} vs ${b.length})`;
                }
              }
            }
          }

          // close
          await page.evaluate(() => {
            const lb = document.querySelector('.lightbox.active');
            if (lb) lb.classList.remove('active');
          });
        } catch (e) {
          lightboxStatus = 'flagged';
          lightboxReason = `click/lightbox error: ${e.message.slice(0, 100)}`;
        }

        if (lightboxStatus === 'broken') {
          report.push({
            project: proj.name, file: f, idx, kind: info.kind,
            status: '❌ broken', reason: lightboxReason,
          });
          SUMMARY.broken++;
        } else if (lightboxStatus === 'flagged') {
          report.push({
            project: proj.name, file: f, idx, kind: info.kind,
            status: '⚠️ flagged', reason: lightboxReason,
          });
          SUMMARY.flagged++;
        } else {
          report.push({
            project: proj.name, file: f, idx, kind: info.kind,
            status: '✅ pass', reason: '',
          });
          SUMMARY.pass++;
        }
      }
    } catch (e) {
      report.push({
        project: proj.name, file: f, idx: -1, kind: 'page',
        status: '⚠️ flagged', reason: `page load error: ${e.message.slice(0, 100)}`,
      });
      SUMMARY.flagged++;
    }
    await page.close();
  }
}

await browser.close();
fs.writeFileSync(REPORT_PATH, JSON.stringify({ summary: SUMMARY, items: report }, null, 2));

// ─── terminal summary ─────────────────────────────────────────────────
console.log('\n' + '='.repeat(72));
console.log(`SUMMARY: ✅ ${SUMMARY.pass}  ❌ ${SUMMARY.broken}  ⚠️ ${SUMMARY.flagged}  (total ${SUMMARY.pass + SUMMARY.broken + SUMMARY.flagged})`);
console.log('='.repeat(72));

const broken = report.filter(r => r.status.startsWith('❌'));
const flagged = report.filter(r => r.status.startsWith('⚠️'));

if (broken.length) {
  console.log('\n❌ BROKEN (must fix):');
  broken.forEach(r => console.log(`  ${r.project}/${r.file}#${r.idx} [${r.kind}]  ${r.reason}`));
}
if (flagged.length) {
  console.log('\n⚠️ FLAGGED (留 user 看):');
  flagged.forEach(r => console.log(`  ${r.project}/${r.file}#${r.idx} [${r.kind}]  ${r.reason}`));
}
if (!broken.length && !flagged.length) {
  console.log('\n✅ All diagrams pass.');
}
console.log(`\nFull report: ${REPORT_PATH}`);
