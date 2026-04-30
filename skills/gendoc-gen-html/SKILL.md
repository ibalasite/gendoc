---
name: gendoc-gen-html
description: |
  將 docs/*.md 和 features/*.feature 動態掃描並一對一轉換為專業 HTML 文件網站（docs/pages/）。
  Mermaid 圖表直接渲染，深色頂導覽列 + 淺色內容區 + 中文字型，Prism.js 語法高亮，RWD。
  Mode 1（預設）：全產生 — README.md + HTML；Mode 2：僅 HTML。
  可獨立呼叫或由 gendoc-auto 自動呼叫。
allowed-tools:
  - Read
  - Write
  - Bash
  - Skill
  - AskUserQuestion
---

# gendoc-gen-html — 生成 HTML 文件網站

MD → HTML 一對一映射，Write 工具直接寫入，不依賴外部腳本。

**模式說明（由 `_EXEC_MODE` 直接決定，不存中間變數）：**
- `full-auto` 或 interactive 選 full（預設）：先呼叫 `/gendoc readme`，再轉換所有頁面為 HTML
- interactive 選 html-only：跳過 README，直接轉換 md 檔為 HTML

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 0：Session Config 讀取 + 模式選擇（遵循 gendoc-shared §0）

### Step 0-A：讀取 `_EXEC_MODE`

```bash
# 從 .gendoc-state.json 讀取執行模式
_EXEC_MODE=$(python3 -c "
import json
try:
    d = json.load(open('.gendoc-state.json'))
    print(d.get('execution_mode', ''))
except:
    print('')
" 2>/dev/null || echo "")

echo "EXEC_MODE：${_EXEC_MODE:-（未設定）}"
```

**若 `_EXEC_MODE` 為空**（無 state file 或首次執行）→ 顯示 Session Config 選單：

```
╔══════════════════════════════════════════════════════╗
║       gendoc — 請選擇執行模式                        ║
╠══════════════════════════════════════════════════════╣
║  [1] Interactive — 互動引導模式（關鍵點等待確認）      ║
║  [2] Full-Auto   — 全自動模式（AI 自動選預設值）       ║
╚══════════════════════════════════════════════════════╝
```

用 `AskUserQuestion` 詢問，取得選擇後：
- 選 [1] → **立即將 `_EXEC_MODE` 設為 `"interactive"`**，並寫入 `.gendoc-state.json`
- 選 [2] → **立即將 `_EXEC_MODE` 設為 `"full-auto"`**，並寫入 `.gendoc-state.json`

⚠️ 重要：選完後 `_EXEC_MODE` 變數必須在當次執行中更新，Step 0-B 才能正確路由。

**若 `_EXEC_MODE` 已有值**（由 gendoc-config 設定）→ 直接沿用，不再詢問：
```
[Session Config] 沿用已設定 — 模式：<_EXEC_MODE>
```

### Step 0-B：路由

**預設永遠是 full（README + HTML）。`_EXEC_MODE` 只控制要不要暫停詢問。**

**`_EXEC_MODE=full-auto`（或任何非 interactive 值）**：
```
[Full-Auto] gendoc-gen-html：full 模式 → 直接執行 Step 1-A
```

**`_EXEC_MODE=interactive`**：用 `AskUserQuestion` 詢問（只給切換機會，預設仍是 full）：

```
gendoc-gen-html 預設執行 full 模式（README + HTML）。
需要改為 html-only 嗎？

[1] 繼續 full（預設）
[2] 改為 html-only — 跳過 README，只重新產生 HTML 頁面
```

- 回答 1 或 Enter → 執行 Step 1-A（full）
- 回答 2 → 跳到 Step 1-B（html-only）

---

## Step 1-A：Mode full — 呼叫 gendoc readme 生成 README.md

**`_EXEC_MODE=full-auto` 或 interactive 選 full 時執行。**

用 Skill 工具呼叫 `/gendoc`，args=`"readme"`：
- 該 skill 會自動收集 BRD/PRD/PDD/EDD 資料並寫入 README.md
- 完成後繼續 Step 1-B

---

## Step 1-B：初始化環境

```bash
_CWD="$(pwd)"
_DOCS_DIR="${_CWD}/docs"
_PAGES_DIR="${_CWD}/docs/pages"
_ASSETS_DIR="${_PAGES_DIR}/assets"

mkdir -p "$_PAGES_DIR"
mkdir -p "$_ASSETS_DIR"

_APP_NAME=$(basename "$_CWD")
echo "專案：$_APP_NAME"
echo "=== 掃描 docs/*.md ==="
ls "${_DOCS_DIR}"/*.md 2>/dev/null || echo "(無 .md 檔案)"
ls "$(pwd)/features"/*.feature 2>/dev/null && echo "BDD：有 .feature 檔案" || echo "BDD：無 .feature 檔案"
```

---

## Step 2：寫入 docs/pages/assets/style.css

使用 **Write 工具**寫入以下完整 CSS（不得省略任何內容）：

**目標路徑：`docs/pages/assets/style.css`**

```css
/* docs/pages/assets/style.css — stock_monitor 風格 */
/* 深色頂導覽列 + 深色 Banner + 淺色內容區 + 中文優先字型 */

:root {
  /* 導覽列（永遠深色） */
  --nav-bg: #111827;
  --nav-text: #f9fafb;
  --nav-accent: #2d9ef5;

  /* 頁面 Banner（深色漸層） */
  --banner-from: #1e3a5f;
  --banner-to: #111827;
  --banner-text: #fff;
  --banner-link: #93c5fd;

  /* 主體（淺色） */
  --page-bg: #f6f8fa;
  --sidebar-bg: #fff;
  --content-bg: #fff;
  --border: #e1e4e8;
  --text: #24292e;
  --text-muted: #586069;
  --accent: #2d9ef5;
  --accent-hover: #1a8ae0;
  --code-bg: #f6f8fa;
  --table-stripe: #fafbfc;
  --active-bg: #eff8ff;

  /* 字型 */
  --font: system-ui, "Segoe UI", "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", sans-serif;
  --font-mono: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;

  /* 尺寸：sidebar 固定，content 填滿剩餘空間，無最大寬度上限（4K 友好） */
  --nav-h: 56px;
  --sidebar-w: 260px;
  --content-pad-h: 3rem;  /* 內容左右 padding */
}

@media (min-width: 1440px) {
  :root { --sidebar-w: 280px; }
}
@media (min-width: 1920px) {
  :root { --sidebar-w: 300px; --content-pad-h: 4rem; }
}
@media (min-width: 2560px) {
  :root { --sidebar-w: 320px; --content-pad-h: 5rem; }
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }

body {
  font-family: var(--font);
  font-size: 15px;
  line-height: 1.7;
  color: var(--text);
  background: var(--page-bg);
  min-height: 100vh;
}

/* ─── Top Navigation（永遠深色） ─────────────────── */

.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--nav-h);
  background: var(--nav-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.4);
}

.nav-brand {
  font-size: 1rem;
  font-weight: 700;
  color: var(--nav-text);
  text-decoration: none;
  letter-spacing: -0.01em;
  transition: color 120ms;
}
.nav-brand:hover { color: var(--nav-accent); }

.nav-controls { display: flex; align-items: center; gap: 0.75rem; }

/* GitHub link in nav */
.nav-gh-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: #d1d5db;
  text-decoration: none;
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid #374151;
  border-radius: 6px;
  transition: all 120ms;
  white-space: nowrap;
}
.nav-gh-link:hover {
  background: #1f2937;
  color: var(--nav-accent);
  border-color: var(--nav-accent);
}

/* ─── Search ─────────────────────────────────────── */

.search-wrap { position: relative; }

.search-input {
  padding: 0.375rem 0.75rem;
  border: 1px solid #374151;
  border-radius: 6px;
  background: #1f2937;
  color: var(--nav-text);
  font-family: var(--font);
  font-size: 0.875rem;
  width: 200px;
  transition: border-color 120ms;
}
.search-input::placeholder { color: #9ca3af; }
.search-input:focus { outline: none; border-color: var(--nav-accent); }

.search-results {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: var(--content-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  width: 320px;
  max-height: 400px;
  overflow-y: auto;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  z-index: 200;
  display: none;
}
.search-result-item {
  padding: 0.625rem 1rem;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  text-decoration: none;
  display: block;
  color: var(--text);
}
.search-result-item:hover { background: var(--page-bg); }
.search-result-item__title { font-weight: 600; font-size: 0.875rem; }
.search-result-item__excerpt { color: var(--text-muted); font-size: 0.8125rem; margin-top: 2px; }

/* ─── Page Banner（深色漸層） ────────────────────── */

.doc-page-banner {
  background: linear-gradient(135deg, var(--banner-from) 0%, var(--banner-to) 100%);
  color: var(--banner-text);
  padding: 2.5rem 2rem 2rem;
  border-bottom: 1px solid #0d1117;
}

.banner-breadcrumb {
  font-size: 0.8125rem;
  color: var(--banner-link);
  margin-bottom: 0.5rem;
}
.banner-breadcrumb a {
  color: var(--banner-link);
  text-decoration: none;
}
.banner-breadcrumb a:hover { text-decoration: underline; }

.banner-title {
  font-size: clamp(1.5rem, 3vw, 2.25rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0;
}

.banner-desc {
  font-size: 0.9375rem;
  color: #d1d5db;
  margin-top: 0.5rem;
}

/* ─── Page Wrapper ───────────────────────────────── */

.page-wrapper {
  display: grid;
  grid-template-columns: var(--sidebar-w) 4px 1fr;
  width: 100%;
  min-height: calc(100vh - var(--nav-h) - 7rem);
  align-items: start;
  transition: grid-template-columns 200ms ease;
}

/* ─── Sidebar ────────────────────────────────────── */

.sidebar {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  padding: 1.5rem 0;
  position: sticky;
  top: var(--nav-h);
  height: calc(100vh - var(--nav-h));
  overflow-y: auto;
}

.sidebar__section { margin-bottom: 1.5rem; }

.sidebar__label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 0 1rem;
  margin-bottom: 0.375rem;
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4375rem 1rem;
  color: var(--text);
  text-decoration: none;
  font-size: 0.875rem;
  border-left: 2px solid transparent;
  transition: all 120ms;
}
.sidebar__link:hover {
  background: var(--page-bg);
  color: var(--accent);
}
.sidebar__link.active {
  border-left-color: var(--accent);
  color: var(--accent);
  background: var(--active-bg);
  font-weight: 500;
}

/* ─── Doc Content ────────────────────────────────── */

.doc-content {
  padding: 2.5rem var(--content-pad-h);
  width: 100%;          /* 填滿 1fr，隨螢幕自動擴展，不設 max-width */
  background: transparent;
}

.doc-content h1 {
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 1.25rem;
  color: var(--text);
  border-bottom: 2px solid var(--border);
  padding-bottom: 0.625rem;
}
.doc-content h2 {
  font-size: clamp(1.125rem, 2vw, 1.5rem);
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 2.5rem 0 0.75rem;
  color: var(--text);
  padding-bottom: 0.375rem;
  border-bottom: 1px solid var(--border);
}
.doc-content h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 1.75rem 0 0.5rem;
}
.doc-content h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 1.25rem 0 0.375rem;
}
.doc-content p { margin-bottom: 1rem; }
.doc-content ul, .doc-content ol { margin: 0.5rem 0 1rem 1.5rem; }
.doc-content li { margin-bottom: 0.25rem; }

.doc-content a { color: var(--accent); text-decoration: none; }
.doc-content a:hover { text-decoration: underline; }

.doc-content blockquote {
  border-left: 3px solid var(--accent);
  padding: 0.625rem 1rem;
  margin: 1rem 0;
  background: #f0f7ff;
  border-radius: 0 6px 6px 0;
  color: var(--text-muted);
}
.doc-content hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 2rem 0;
}

/* Table */
.doc-content table {
  display: block;
  overflow-x: auto;
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
  font-size: 0.875rem;
}
.doc-content th {
  background: var(--page-bg);
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-weight: 600;
  border: 1px solid var(--border);
}
.doc-content td {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  vertical-align: top;
}
.doc-content tr:nth-child(even) td { background: var(--table-stripe); }

/* Code */
.doc-content pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem 1.25rem;
  overflow-x: auto;
  margin: 1rem 0;
  font-family: var(--font-mono);
  font-size: 0.875rem;
  line-height: 1.6;
}
.doc-content code {
  font-family: var(--font-mono);
  font-size: 0.875em;
  background: var(--code-bg);
  padding: 1px 5px;
  border-radius: 4px;
  border: 1px solid var(--border);
}
.doc-content pre code {
  background: none;
  padding: 0;
  border: none;
  font-size: 1em;
}

/* Mermaid diagrams */
.diagram-container {
  background: var(--content-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  margin: 1.5rem 0;
  text-align: center;
  cursor: pointer;
  overflow-x: auto;
  transition: border-color 200ms, box-shadow 200ms;
}
.diagram-container:hover {
  border-color: var(--accent);
  box-shadow: 0 2px 8px rgba(45,158,245,0.15);
}

/* Lightbox */
.lightbox {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  z-index: 1000;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}
.lightbox.active { display: flex; }
.lightbox__content {
  background: var(--content-bg);
  border-radius: 8px;
  padding: 2rem;
  max-width: 95vw;
  max-height: 90vh;
  overflow: auto;
}
.lightbox__close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  font-size: 2rem;
  color: white;
  cursor: pointer;
  line-height: 1;
}

/* Index grid */
.index-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}
.index-card {
  background: var(--content-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  text-decoration: none;
  color: var(--text);
  transition: all 120ms;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.index-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(45,158,245,0.15);
}
.index-card__icon { font-size: 1.75rem; }
.index-card__title { font-weight: 600; font-size: 1rem; }
.index-card__desc { color: var(--text-muted); font-size: 0.875rem; }

/* Responsive */
@media (max-width: 768px) {
  .page-wrapper { grid-template-columns: 1fr; max-width: 100%; }
  .sidebar { display: none; }
  .doc-content { padding: 1.5rem 1rem; }
  .search-input { width: 140px; }
  .doc-page-banner { padding: 1.5rem 1rem 1rem; }
  .nav-gh-link { display: none; }  /* 小螢幕隱藏，省空間 */
}

/* ─── Badge Fallback ─────────────────────────── */
.badge-fallback {
  display: inline-block;
  padding: 2px 8px;
  font-size: 0.75rem;
  font-family: var(--font-mono);
  background: #e1e4e8;
  border-radius: 4px;
  color: var(--text-muted);
  vertical-align: middle;
}

/* ─── Sidebar Toggle Button ──────────────────── */
.sidebar-toggle {
  background: transparent;
  border: 1px solid #374151;
  color: #d1d5db;
  padding: 0.375rem 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  transition: all 120ms;
  flex-shrink: 0;
}
.sidebar-toggle:hover { background: #1f2937; color: var(--nav-accent); }

/* ─── Sidebar Resizer ────────────────────────── */
.sidebar-resizer {
  width: 4px;
  background: var(--border);
  cursor: col-resize;
  transition: background 120ms;
  z-index: 5;
  user-select: none;
  flex-shrink: 0;
}
.sidebar-resizer:hover,
.sidebar-resizer.dragging { background: var(--accent); }

/* ─── Sidebar Collapsed State ────────────────── */
.page-wrapper.sidebar-collapsed {
  grid-template-columns: 0 4px 1fr;
}
.page-wrapper.sidebar-collapsed .sidebar {
  overflow: hidden;
  min-width: 0;
  width: 0;
  padding: 0;
  border: none;
  visibility: hidden;
}
```

---

## Step 3：寫入 docs/pages/assets/app.js

使用 **Write 工具**寫入以下 JS：

**目標路徑：`docs/pages/assets/app.js`**

```javascript
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

if (localStorage.getItem('sidebar-collapsed') === 'true') {
  pageWrapper?.classList.add('sidebar-collapsed');
}
const savedW = localStorage.getItem('sidebar-width');
if (savedW) document.documentElement.style.setProperty('--sidebar-w', savedW);

sidebarToggle?.addEventListener('click', () => {
  const collapsed = pageWrapper.classList.toggle('sidebar-collapsed');
  localStorage.setItem('sidebar-collapsed', collapsed);
});

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
```

---

## Step 4：檢查 / 寫入 docs/pages/gen_html.py

```bash
_SCRIPT_VERSION="3.0.0"
_SCRIPT="$(pwd)/docs/pages/gen_html.py"

# 讀取現有腳本版本
_CURRENT=$(head -3 "$_SCRIPT" 2>/dev/null | grep "# VERSION:" | awk '{print $NF}' || echo "")

echo "gen_html.py 版本：${_CURRENT:-（不存在）} → 期望：$_SCRIPT_VERSION"
```

若 `_CURRENT == _SCRIPT_VERSION`：
```
echo "[Skip] gen_html.py 已是最新，略過重寫"
```

若 `_CURRENT != _SCRIPT_VERSION` 或檔案不存在：
```
echo "[寫入] gen_html.py..."
```
用 **Write 工具**寫入以下完整 Python 腳本到 `docs/pages/gen_html.py`：

```python
#!/usr/bin/env python3
# docs/pages/gen_html.py
# VERSION: 3.0.0
# Auto-generated by gendoc-gen-html — DO NOT EDIT MANUALLY

import os, re, json, html as _html
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
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

def inline_md(text):
    codes = {}
    def save(m):
        k = f"\x00C{len(codes)}\x00"
        codes[k] = f"<code>{esc(m.group(1))}</code>"
        return k
    text = re.sub(r'`([^`]+)`', save, text)
    text = esc(text)
    for k, v in codes.items():
        text = text.replace(esc(k), v)
    # 先處理 image/link，避免 URL 裡的底線被 italic regex 誤解析
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement(\'span\'),{className:\'badge-fallback\',textContent:this.alt}))">', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    # bold/italic — 底線版加 word boundary 防止 URL 誤觸發
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\w)__(.+?)__(?!\w)', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', text)
    return text

def build_table(table_lines):
    rows = []
    for line in table_lines:
        if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)
    if not rows:
        return ''
    out = ['<table>']
    out.append('<tr>' + ''.join(f'<th>{inline_md(c)}</th>' for c in rows[0]) + '</tr>')
    for row in rows[1:]:
        out.append('<tr>' + ''.join(f'<td>{inline_md(c)}</td>' for c in row) + '</tr>')
    out.append('</table>')
    return '\n'.join(out)

def md_to_html(text):
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
            out.append('<div class="diagram-container"><pre class="mermaid">' + '\n'.join(block) + '</pre></div>')
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
            out.append(f'<h4>{inline_md(s[5:])}</h4>')
        elif s.startswith('### '):
            out.append(f'<h3>{inline_md(s[4:])}</h3>')
        elif s.startswith('## '):
            out.append(f'<h2>{inline_md(s[3:])}</h2>')
        elif s.startswith('# '):
            out.append(f'<h1>{inline_md(s[2:])}</h1>')
        elif re.match(r'^[-*_]{3,}$', s):
            out.append('<hr>')
        elif s.startswith('> '):
            out.append(f'<blockquote><p>{inline_md(s[2:])}</p></blockquote>')
        elif s.startswith('|') and '|' in s[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            out.append(build_table(table_lines))
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
                        li = f'<li style="list-style:none"><input type="checkbox" disabled> {inline_md(text[4:])}</li>'
                    elif text.startswith('[x] ') or text.startswith('[X] '):
                        li = f'<li style="list-style:none"><input type="checkbox" checked disabled> {inline_md(text[4:])}</li>'
                    elif indent >= 2:
                        li = f'<li style="margin-left:{indent * 0.5}rem">{inline_md(text)}</li>'
                    else:
                        li = f'<li>{inline_md(text)}</li>'
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
                items.append(f'<li>{inline_md(t)}</li>')
                i += 1
            out.append('<ol>' + ''.join(items) + '</ol>')
            continue
        elif s:
            out.append(f'<p>{inline_md(s)}</p>')
        i += 1
    return '\n'.join(out)

PAGE_META = {
    'index':     ('首頁',              '🏠'),
    'idea':      ('構想文件 (IDEA)',   '💡'),
    'brd':       ('商業需求文件 (BRD)', '📋'),
    'prd':       ('產品需求文件 (PRD)', '📝'),
    'pdd':       ('產品設計文件 (PDD)', '🎨'),
    'vdd':       ('視覺設計文件 (VDD)', '🖼️'),
    'edd':       ('工程設計文件 (EDD)', '🏗️'),
    'arch':      ('架構設計',           '🧩'),
    'api':       ('API 文件',           '🔌'),
    'schema':    ('Schema 文件',        '🗄️'),
    'frontend':  ('前端設計文件',        '🖥️'),
    'audio':     ('音效設計文件',        '🔊'),
    'anim':      ('動畫特效文件',        '🎬'),
    'test-plan': ('測試計畫 (Test Plan)', '✅'),
    'bdd':       ('BDD Scenarios',     '🧪'),
    'rtm':       ('需求追蹤矩陣 (RTM)', '🗂️'),
    'runbook':   ('Runbook',           '📖'),
    'local_deploy': ('本地部署指南',   '🚀'),
    'align_report': ('對齊報告',       '🔍'),
}

# UML diagram metadata — used to categorise diagrams in the sidebar
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
    # frontend diagrams
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
    """Return (server_diagrams, frontend_diagrams) — list of (slug, label, icon, path)."""
    if not DIAGRAMS_DIR.exists():
        return [], []
    server, frontend = [], []
    for p in sorted(DIAGRAMS_DIR.glob("*.md")):
        stem = p.stem
        if stem in ('class-inventory',):
            continue  # skip inventory — it's a reference doc not a rendered diagram page
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

def make_sidebar(doc_pages, server_diagrams, frontend_diagrams, current, has_req=False):
    def link(slug, label, icon):
        cls = ' active' if slug == current else ''
        return f'<a class="sidebar__link{cls}" href="{slug}.html">{icon} {label}</a>'

    sections = []

    # 文件區
    sections.append('<div class="sidebar__section">')
    sections.append('<div class="sidebar__label">文件</div>')
    for slug, label, icon in doc_pages:
        sections.append(link(slug, label, icon))
    sections.append('</div>')

    # Server UML 區
    if server_diagrams:
        sections.append('<div class="sidebar__section">')
        sections.append('<div class="sidebar__label">Server UML</div>')
        for slug, label, icon, _ in server_diagrams:
            sections.append(link(f'diag-{slug}', label, icon))
        sections.append('</div>')

    # Frontend UML 區
    if frontend_diagrams:
        sections.append('<div class="sidebar__section">')
        sections.append('<div class="sidebar__label">Frontend UML</div>')
        for slug, label, icon, _ in frontend_diagrams:
            sections.append(link(f'diag-{slug}', label, icon))
        sections.append('</div>')

    # 原始素材 (req/) 區
    if has_req:
        sections.append('<div class="sidebar__section">')
        sections.append('<div class="sidebar__label">原始素材</div>')
        sections.append(link('req', 'req/ 素材清單', '📎'))
        sections.append('</div>')

    return '\n'.join(sections)

def render_page(content, title, banner, doc_pages, server_diagrams, frontend_diagrams, current, is_index=False, has_req=False):
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
    sidebar_html = make_sidebar(doc_pages, server_diagrams, frontend_diagrams, current, has_req=has_req)
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

    # Discover doc pages (sidebar section 1)
    doc_pages = [('index', '首頁', '🏠')]
    known_order = ['IDEA', 'BRD', 'PRD', 'PDD', 'VDD', 'EDD', 'ARCH', 'API', 'SCHEMA',
                   'FRONTEND', 'AUDIO', 'ANIM', 'test-plan', 'runbook', 'LOCAL_DEPLOY',
                   'RTM', 'ALIGN_REPORT']
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

    # B-04: Split BDD into server (features/*.feature) and client (features/client/**/*.feature)
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

    # B-03: Detect req/ files for sidebar section
    has_req = (REQ_DIR.exists() and
               any(f for f in REQ_DIR.iterdir() if f.is_file() and not f.name.startswith('.')))

    # Discover diagram pages (sidebar sections 2 + 3)
    server_diagrams, frontend_diagrams = scan_diagram_pages()

    search_data = {}

    def write_page(filename, content, title, banner, current, is_index=False):
        html = render_page(content, title, banner,
                           doc_pages, server_diagrams, frontend_diagrams,
                           current, is_index, has_req=has_req)
        (PAGES_DIR / filename).write_text(html)
        exc = re.sub(r'<[^>]+>', '', content)[:150]
        search_data[filename] = {"url": filename, "title": title, "excerpt": exc}
        print(f"✓ {filename}")

    # index.html
    readme = BASE / "README.md"
    if readme.exists():
        body = md_to_html(readme.read_text()) + health_section()
    else:
        body = (f'<h1>{APP_NAME} 文件中心</h1>'
                '<p>請從左側導覽列選擇文件。</p>' + health_section())
    write_page("index.html", body, f'{APP_NAME} 文件中心', f'{APP_NAME} 文件中心', 'index', True)

    # Known doc pages
    for s, label, p in known_doc_entries:
        c = md_to_html(p.read_text())
        if s == 'idea':
            c += req_section()
        write_page(f"{s}.html", c, label, label, s)

    # Extra doc pages
    for s, label, p in extra_doc_entries:
        c = md_to_html(p.read_text())
        write_page(f"{s}.html", c, label, label, s)

    # B-04: Server BDD page (features/*.feature — root level only)
    if has_server_bdd:
        parts = [f"## {f.name}\n\n```gherkin\n{f.read_text()}\n```"
                 for f in server_bdd_features]
        c = md_to_html('\n\n'.join(parts))
        write_page("bdd-server.html", c, "Server BDD", "Server BDD Scenarios", 'bdd-server')

    # B-04: Client BDD page (features/client/**/*.feature)
    if has_client_bdd:
        parts = [f"## {f.relative_to(client_bdd_dir)}\n\n```gherkin\n{f.read_text()}\n```"
                 for f in client_bdd_features]
        c = md_to_html('\n\n'.join(parts))
        write_page("bdd-client.html", c, "Client BDD", "Client BDD Scenarios", 'bdd-client')

    # B-03: req/ materials page
    if has_req:
        req_body = (f'<h1>📎 原始素材 (req/)</h1>'
                    f'<p style="color:var(--text-muted)">專案原始素材與需求附件，點擊下載。</p>'
                    + req_section())
        write_page("req.html", req_body, "原始素材 (req/)", "原始素材 (req/)", 'req')

    # Server UML diagram pages
    for stem, label, icon, p in server_diagrams:
        c = md_to_html(p.read_text())
        write_page(f"diag-{stem}.html", c, label, label, f'diag-{stem}')

    # Frontend UML diagram pages
    for stem, label, icon, p in frontend_diagrams:
        c = md_to_html(p.read_text())
        write_page(f"diag-{stem}.html", c, label, label, f'diag-{stem}')

    # search-data.json
    (PAGES_DIR / "search-data.json").write_text(
        json.dumps(search_data, ensure_ascii=False, indent=2))
    print("✓ search-data.json")
    total_diag = len(server_diagrams) + len(frontend_diagrams)
    bdd_count = int(has_server_bdd) + int(has_client_bdd)
    req_count = int(has_req)
    print(f"\n✅ 完成：{len(search_data)} 頁（文件 + BDD×{bdd_count} + {total_diag} UML 圖表 + req×{req_count}）→ {PAGES_DIR}")

if __name__ == "__main__":
    main()
```

---

## Step 5：執行生成腳本

```bash
python3 docs/pages/gen_html.py
```

Python 腳本會：
- 掃描 `docs/*.md`、`docs/diagrams/*.md`、`features/*.feature`
- 批次轉換所有 Markdown → HTML，包含 Server UML 和 Frontend UML 圖表頁面
- 側欄自動分三區：文件 / Server UML / Frontend UML
- 寫入 `docs/pages/*.html`（包含 index）
- 寫入 `docs/pages/search-data.json`
- 讀取 `.gendoc-state.json` 取得 APP_NAME、GITHUB_REPO

---

## Step 6：驗證 gate（必須執行）

```bash
# 必要頁面驗證
for _PAGE in index; do
  if [[ ! -f "$(pwd)/docs/pages/${_PAGE}.html" ]]; then
    echo "STEP_FAILED: ${_PAGE}.html 未產出"
  else
    echo "OK: ${_PAGE}.html"
  fi
done

# 條件性頁面驗證（有 .md 才需要有 .html）
for _DOC in idea brd prd pdd edd arch api schema; do
  _MD="$(pwd)/docs/${_DOC^^}.md"
  [[ "$_DOC" == "idea" ]] && _MD="$(pwd)/docs/IDEA.md"
  if [[ -f "$_MD" ]] && [[ ! -f "$(pwd)/docs/pages/${_DOC}.html" ]]; then
    echo "STEP_FAILED: ${_DOC}.html 未產出（但 ${_DOC^^}.md 存在）"
  elif [[ -f "$(pwd)/docs/pages/${_DOC}.html" ]]; then
    echo "OK: ${_DOC}.html"
  fi
done

# test-plan.md 特殊路徑（lowercase 檔名）
if [[ -f "$(pwd)/docs/test-plan.md" ]] && [[ ! -f "$(pwd)/docs/pages/test-plan.html" ]]; then
  echo "STEP_FAILED: test-plan.html 未產出（但 test-plan.md 存在）"
elif [[ -f "$(pwd)/docs/pages/test-plan.html" ]]; then
  echo "OK: test-plan.html"
fi

ls -la $(pwd)/docs/pages/*.html
```

若任何必要頁面缺失 → 重新執行 `python3 docs/pages/gen_html.py`

---

## Step 6.1：Mermaid 語法修復 Loop（v11.14.0 相容性）

**目的**：掃描 `docs/*.md` 原始文件中的已知破圖語法，自動修復後重新生成 HTML。最多 3 輪，finding=0 時提前結束。

**[AI 指令]** 執行以下 Python 掃描腳本（用 Bash 工具）：

```python
import re, pathlib, sys

docs_dir = pathlib.Path("docs")
issues = []

for md_file in sorted(docs_dir.glob("*.md")):
    content = md_file.read_text(encoding="utf-8")
    # 掃描每個 mermaid 區塊
    for blk in re.findall(r'```mermaid\n(.*?)```', content, re.DOTALL):
        lines = blk.split('\n')
        dtype = lines[0].strip() if lines else ''

        # sequenceDiagram: par without and
        if 'sequenceDiagram' in dtype:
            in_par = False
            for line in lines[1:]:
                stripped = line.strip()
                if stripped.lower().startswith('par '):
                    in_par = True
                elif in_par and stripped.lower().startswith('and '):
                    in_par = False
                elif in_par and stripped.lower() == 'end':
                    issues.append(f"PAR_WITHOUT_AND|{md_file.name}")
                    break

        # flowchart: 4 patterns causing "Syntax error in text" in mermaid v11.14.0
        if re.match(r'^(flowchart|graph)\b', dtype):
            for line in lines[1:]:
                if re.search(r'\(\[[^\]]+\]\)', line):
                    issues.append(f"STADIUM_SHAPE|{md_file.name}"); break
            for line in lines[1:]:
                if re.search(r'\{[^}]*<(?![-=&])[^}]*\}', line):
                    issues.append(f"BARE_LT_IN_LABEL|{md_file.name}"); break
            for line in lines[1:]:
                if re.search(r'\[[^\]"]*\\n\[', line):
                    issues.append(f"NESTED_BRACKET|{md_file.name}"); break
            for line in lines[1:]:
                if re.search(r'\[[^\]"]*\{[^}]*\}[^\]"]*\]', line):
                    issues.append(f"BRACE_IN_BRACKET|{md_file.name}"); break

for i in issues:
    print(i)
print(f"TOTAL:{len(issues)}")
```

**若 `TOTAL:0`** → 直接進入 Step 6.5。

**若 `TOTAL:N（N>0）`** → 執行修復腳本（FIXPY）：

```python
import re, pathlib

docs_dir = pathlib.Path("docs")

def fix_stadium(line):
    return re.sub(r'\(\[([^\]]+)\]\)', r'((\1))', line)

def fix_bare_lt(line):
    return re.sub(r'(\{[^}]+\})', lambda m: m.group(0).replace('<', '&lt;'), line)

def fix_nested_bracket(line):
    return re.sub(
        r'\[([^\]"]*?)\\n\[([^\]]*)\]([^\]"]*?)\]',
        lambda m: '[' + m.group(1) + '\\n(' + m.group(2) + ')' + m.group(3) + ']',
        line)

def fix_brace_in_bracket(line):
    return re.sub(
        r'\[([^\]"]*\{[^\]"]*\}[^\]"]*)\]',
        lambda m: '[' + m.group(1).replace('{', '(').replace('}', ')') + ']',
        line)

def fix_flowchart_line(line):
    line = fix_stadium(line)
    line = fix_bare_lt(line)
    line = fix_nested_bracket(line)
    line = fix_brace_in_bracket(line)
    return line

for md_file in sorted(docs_dir.glob("*.md")):
    content = md_file.read_text(encoding="utf-8")
    changed = False

    def replace_block(m):
        nonlocal changed
        inner = m.group(1)
        lines = inner.split('\n')
        dtype = lines[0].strip() if lines else ''
        if not re.match(r'^(flowchart|graph)\b', dtype):
            return m.group(0)
        fixed_lines = [lines[0]] + [fix_flowchart_line(l) for l in lines[1:]]
        fixed = '\n'.join(fixed_lines)
        if fixed != inner:
            changed = True
        return '```mermaid\n' + fixed + '```'

    new_content = re.sub(r'```mermaid\n(.*?)```', replace_block, content, flags=re.DOTALL)
    if changed:
        md_file.write_text(new_content, encoding="utf-8")
        print(f"FIXED: {md_file.name}")
```

修復完後重新執行 `python3 docs/pages/gen_html.py`，再次掃描。最多 3 輪。

| 問題 ID | 觸發條件 | 修復方式 |
|--------|---------|---------|
| STADIUM_SHAPE | `([text])` 在 flowchart 中 | `([text])` → `((text))` |
| BARE_LT_IN_LABEL | `<` 在 `{...}` 菱形 label 內 | `<` → `&lt;` |
| NESTED_BRACKET | `\n[` 在 `[...]` 節點 label 內 | `\n[inner]` → `\n(inner)` |
| BRACE_IN_BRACKET | `{key}` 在 `[...]` 節點 label 內 | `{` / `}` → `(` / `)` |
| PAR_WITHOUT_AND | sequenceDiagram `par` 缺 `and` | 需手動補 `and` 段落 |

---

## Step 6.5：Prototype 生成（條件性）

```bash
# 偵測是否有 Frontend / Client 需求文件，或 API 文件
_HAS_FRONTEND=0
_HAS_API=0
[[ -f "$(pwd)/docs/FRONTEND.md" ]] && _HAS_FRONTEND=1
[[ -f "$(pwd)/docs/PDD.md"      ]] && _HAS_FRONTEND=1
[[ -f "$(pwd)/docs/API.md"      ]] && _HAS_API=1

echo "_HAS_FRONTEND=${_HAS_FRONTEND}  _HAS_API=${_HAS_API}"
```

**若 `_HAS_FRONTEND=1` 或 `_HAS_API=1`**：用 Skill 工具呼叫 `/gendoc-gen-prototype`：
- UI prototype：讀取 PRD/PDD/VDD/FRONTEND/AUDIO/ANIM/SCHEMA，生成可點擊畫面
- API Explorer：讀取 API.md/SCHEMA.md，生成可試打的 mock API 介面
- 輸出至 `docs/pages/prototype/`
- 自動更新 README.md 和 `docs/pages/index.html` 中的 prototype 連結

**若 `_HAS_FRONTEND=0` 且 `_HAS_API=0`**：
```
[Skip] 無 FRONTEND.md / PDD.md / API.md — 跳過 prototype 生成
```

---

## Step 7：git commit

```bash
git add docs/pages/ README.md 2>/dev/null
git commit -m "docs(devsop)[STEP-30]: html — 生成 HTML 文件網站（深色頂導 + 淺色內容 + 中文字型）"
```

---

## Step 8：輸出摘要

```
STEP 30 完成：HTML 文件網站生成
Commit：<git hash>
重點：
  - 模式：<full=含 README | html-only=僅 HTML>
  - gen_html.py 版本：2.8.0（<新寫入 | 已沿用>）
  - 生成 N 個 HTML 頁面到 docs/pages/
  - 風格：深色頂導（#111827）+ 深色 Banner + 淺色內容（#f6f8fa）
  - 功能：Sidebar 導覽、Prism.js 語法高亮、Mermaid 圖表、Client-side 搜尋

STEP_COMPLETE: 19
```

---

## 常見問題與修復

| 問題 | 原因 | 修復 |
|------|------|------|
| HTML 未產出 | Python 腳本執行失敗 | 看 python3 的錯誤訊息，修復後重跑 |
| Mermaid 不渲染 | mermaid 語法被 HTML 轉義 | gen_html.py 的 md_to_html() 不轉義 mermaid 區塊 |
| Mermaid "Syntax error in text" | flowchart 中使用 `([...])` / 裸 `<` in `{...}` / 巢狀 `]` / `{key}` in `[...]` | 執行 Step 6.1 掃描修復 Loop |
| 路徑錯誤 | BASE 路徑計算錯誤 | 確認 gen_html.py 在 docs/pages/ 目錄下 |
| README 未生成 | Mode full 但未呼叫 gendoc readme | 確認 Step 1-A 執行了 Skill("gendoc", args="readme") |
