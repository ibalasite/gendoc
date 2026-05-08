// Mermaid parse helper: read mermaid content from stdin, parse via mermaid v11.
// Exit 0 = parse OK, exit 1 = parse error (with error message on stderr).
// Used by test runner to verify _mermaid_fix_block output.
import fs from 'node:fs';
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost/',
});
global.window = dom.window;
global.document = dom.window.document;
Object.defineProperty(global, 'navigator', {
  value: dom.window.navigator,
  writable: true,
});
global.HTMLElement = dom.window.HTMLElement;
global.SVGElement = dom.window.SVGElement;
global.Node = dom.window.Node;

const mermaid = (await import('mermaid')).default;

let content = '';
for await (const chunk of process.stdin) content += chunk;

try {
  await mermaid.parse(content);
  process.exit(0);
} catch (e) {
  const msg = (e.message || e.str || String(e)).split('\n')[0];
  process.stderr.write(msg + '\n');
  process.exit(1);
}
