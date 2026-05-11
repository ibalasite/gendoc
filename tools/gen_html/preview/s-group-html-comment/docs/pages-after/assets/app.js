// docs/pages/assets/app.js

// ─── Active Sidebar Link ──────────────────────────
const currentPage = location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.sidebar__link').forEach(link => {
  if (link.getAttribute('href') === currentPage) link.classList.add('active');
});

// ─── Lightbox ─────────────────────────────────────
const lightbox = document.createElement('div');
lightbox.className = 'lightbox';
lightbox.innerHTML = '<span class="lightbox__close">&#x2715;</span><div class="lightbox__content"></div>';
document.body.appendChild(lightbox);

lightbox.querySelector('.lightbox__close').addEventListener('click', () => lightbox.classList.remove('active'));
lightbox.addEventListener('click', e => { if (e.target === lightbox) lightbox.classList.remove('active'); });

document.querySelectorAll('.diagram-container').forEach(el => {
  el.addEventListener('click', () => {
    const clone = el.cloneNode(true);
    lightbox.querySelector('.lightbox__content').innerHTML = '';
    lightbox.querySelector('.lightbox__content').appendChild(clone);
    lightbox.classList.add('active');
    if (window.mermaid) mermaid.run({ nodes: lightbox.querySelectorAll('.mermaid:not([data-processed])') });
  });
});

// ─── Client-side Search ───────────────────────────
let searchData = null;
async function initSearch() {
  try {
    const res = await fetch('search-data.json');
    if (res.ok) searchData = await res.json();
  } catch {}
}

const searchInput = document.querySelector('.search-input');
const searchResultsEl = document.querySelector('.search-results');

searchInput?.addEventListener('input', e => {
  const q = e.target.value.trim().toLowerCase();
  if (!q || !searchData || !searchResultsEl) {
    if (searchResultsEl) searchResultsEl.style.display = 'none';
    return;
  }
  const hits = Object.values(searchData)
    .filter(d => d.title.toLowerCase().includes(q) || d.excerpt.toLowerCase().includes(q))
    .slice(0, 8);
  if (!hits.length) { searchResultsEl.style.display = 'none'; return; }
  searchResultsEl.innerHTML = hits.map(d =>
    `<a class="search-result-item" href="${d.url}">
      <div class="search-result-item__title">${d.title}</div>
      <div class="search-result-item__excerpt">${d.excerpt.slice(0,80)}…</div>
    </a>`).join('');
  searchResultsEl.style.display = 'block';
});

document.addEventListener('click', e => {
  if (!e.target.closest('.search-wrap') && searchResultsEl) {
    searchResultsEl.style.display = 'none';
  }
});

initSearch();

// ─── Sidebar Toggle & Resize ──────────────────
const sidebarToggle = document.getElementById('sidebarToggle');
const pageWrapper   = document.querySelector('.page-wrapper');
const sidebarEl     = document.querySelector('.sidebar');
const resizerEl     = document.getElementById('sidebarResizer');

// N1: namespaced key — single source of truth for sidebar collapse state
// across both the top-nav button (#sidebarToggle) and the in-sidebar
// button (#sidebarCollapseBtn). Falls back to the legacy unprefixed key
// once so users with prior state don't see a regression.
const SIDEBAR_COLLAPSE_KEY = 'gendoc:sidebar-collapsed';
const legacyCollapsed = localStorage.getItem('sidebar-collapsed');
const initialCollapsed = (
  localStorage.getItem(SIDEBAR_COLLAPSE_KEY) ?? legacyCollapsed
) === 'true';
if (initialCollapsed) pageWrapper?.classList.add('sidebar-collapsed');
const savedW = localStorage.getItem('sidebar-width');
if (savedW) document.documentElement.style.setProperty('--sidebar-w', savedW);

function toggleSidebarCollapse() {
  if (!pageWrapper) return;
  const collapsed = pageWrapper.classList.toggle('sidebar-collapsed');
  localStorage.setItem(SIDEBAR_COLLAPSE_KEY, String(collapsed));
}
sidebarToggle?.addEventListener('click', toggleSidebarCollapse);
const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
sidebarCollapseBtn?.addEventListener('click', toggleSidebarCollapse);

// ─── N1: Sidebar tab switcher (📁 文件 / 📑 本頁目錄) ─────────
document.querySelectorAll('.sidebar__tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const target = tab.dataset.tab;
    document.querySelectorAll('.sidebar__tab').forEach(t => {
      const on = t.dataset.tab === target;
      t.classList.toggle('active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    document.querySelectorAll('.sidebar__panel').forEach(p => {
      p.classList.toggle('active', p.dataset.panel === target);
    });
  });
});

// ─── N1: TOC scroll-spy via IntersectionObserver ─────────────
// Highlights the .toc__link whose target heading is currently in view.
// Falls back silently when no headings/links are present.
(function initTocScrollSpy() {
  const tocLinks = Array.from(document.querySelectorAll('.toc__link'));
  if (!tocLinks.length || typeof IntersectionObserver === 'undefined') return;
  const idToLink = new Map();
  tocLinks.forEach(a => {
    const href = a.getAttribute('href') || '';
    if (href.startsWith('#')) idToLink.set(href.slice(1), a);
  });
  const headings = Array.from(idToLink.keys())
    .map(id => document.getElementById(id))
    .filter(Boolean);
  if (!headings.length) return;
  const setActive = (id) => {
    tocLinks.forEach(a => a.classList.remove('active'));
    const link = idToLink.get(id);
    if (link) link.classList.add('active');
  };
  const visible = new Set();
  const observer = new IntersectionObserver(entries => {
    for (const e of entries) {
      if (e.isIntersecting) visible.add(e.target.id);
      else visible.delete(e.target.id);
    }
    // Pick the topmost visible heading (smallest viewport-relative top)
    const inView = headings.filter(h => visible.has(h.id));
    if (!inView.length) return;
    inView.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top);
    setActive(inView[0].id);
  }, { rootMargin: '-72px 0px -60% 0px', threshold: [0, 1] });
  headings.forEach(h => observer.observe(h));
})();

if (resizerEl && pageWrapper && sidebarEl) {
  let startX, startW;
  resizerEl.addEventListener('mousedown', e => {
    startX = e.clientX;
    startW = sidebarEl.offsetWidth;
    resizerEl.classList.add('dragging');
    document.body.style.cssText += 'user-select:none;cursor:col-resize;';
    const move = e => {
      const w = Math.max(140, Math.min(520, startW + e.clientX - startX));
      document.documentElement.style.setProperty('--sidebar-w', w + 'px');
    };
    const up = () => {
      resizerEl.classList.remove('dragging');
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
      const w = getComputedStyle(document.documentElement).getPropertyValue('--sidebar-w').trim();
      localStorage.setItem('sidebar-width', w);
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', up);
    };
    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', up);
  });
}
