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

MD → HTML 一對一映射，呼叫 `~/.claude/gendoc/bin/gen_html.py`（由 install.sh 安裝維護）。

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

## Step 4：確認 central script 存在

> **⚠️ 絕對路徑原則**：永遠使用 `$HOME/.claude/gendoc/bin/gen_html.py`。
> 目標專案目錄（含 `docs/pages/`）內若存在任何 `gen_html.py`，**完全忽略**，不得執行、不得參考、不得修改。
> 那是使用者自己的工具，與 gendoc 無關。

```bash
_CENTRAL="$HOME/.claude/gendoc/bin/gen_html.py"
if [[ ! -f "$_CENTRAL" ]]; then
  echo "❌ 找不到 $_CENTRAL"
  echo "   請執行 /gendoc-update 安裝最新版本"
  exit 1
fi
_VERSION=$(head -3 "$_CENTRAL" | grep "# VERSION:" | awk '{print $NF}' || echo "?")
echo "[gen_html] central script：$_CENTRAL（VERSION: $_VERSION）"
```

---

## Step 5：執行生成腳本

```bash
python3 "$HOME/.claude/gendoc/bin/gen_html.py"
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

若任何必要頁面缺失 → 重新執行 `python3 "$HOME/.claude/gendoc/bin/gen_html.py"`

---

## Step 6.1：圖表品質 Fix Loop（最多 3 輪）

**目的**：確保所有 UML 圖表頁面不含 frontmatter 殘留、本地圖片路徑正確、mermaid block 非空。

```bash
_MAX_FIX_ROUNDS=3
_FIX_ROUND=0
_ISSUE_COUNT=999  # enter loop

while [[ $_FIX_ROUND -lt $_MAX_FIX_ROUNDS && $_ISSUE_COUNT -gt 0 ]]; do
  _FIX_ROUND=$((_FIX_ROUND + 1))
  echo "[html-verify] Round $_FIX_ROUND/$_MAX_FIX_ROUNDS"

  _REPORT=$(python3 - <<'PY'
import re, sys
from pathlib import Path

pages = Path.cwd() / "docs/pages"
issues = []

for html_file in sorted(pages.glob("*.html")):
    content = html_file.read_text()
    m = re.search(r'<main class="doc-content">(.*?)</main>', content, re.DOTALL)
    body = m.group(1) if m else ""

    # 1. Frontmatter leak — generated YAML fields appearing as <p> tags
    for field in ("diagram:", "uml-type:", "generated:", "source:", "note:"):
        if f"<p>{field}" in body:
            issues.append(f"FRONTMATTER|{html_file.name}|{field}")
            break

    # 2. Broken local img src
    for im in re.finditer(r'<img[^>]+src="([^"]+)"', content):
        src = im.group(1)
        if src.startswith(("http", "data:", "#", "//")):
            continue
        if not (pages / src).resolve().exists():
            issues.append(f"BROKEN_IMG|{html_file.name}|{src}")

    # 3. Empty mermaid blocks in diagram pages
    if html_file.name.startswith("diag-"):
        for blk in re.findall(r'<pre class="mermaid">(.*?)</pre>', content, re.DOTALL):
            if not blk.strip():
                issues.append(f"EMPTY_MERMAID|{html_file.name}")

    # 4. Mermaid v11 syntax: par without and (causes "Syntax error in text")
    if html_file.name.startswith("diag-"):
        for blk in re.findall(r'<pre class="mermaid">(.*?)</pre>', content, re.DOTALL):
            blk_s = blk.strip()
            if not blk_s or 'sequenceDiagram' not in blk_s:
                continue
            lines_b = blk_s.split('\n')
            in_par = False; has_and = False
            for line in lines_b:
                s = line.strip()
                if re.match(r'^par\b', s):
                    in_par = True; has_and = False
                elif re.match(r'^and\b', s) and in_par:
                    has_and = True
                elif s == 'end' and in_par:
                    if not has_and:
                        issues.append(f"MERMAID_SYNTAX|{html_file.name}|par_without_and")
                    in_par = False

print(f"ISSUE_COUNT:{len(issues)}")
for iss in issues:
    print(f"ISSUE:{iss}")
PY
  )

  _ISSUE_COUNT=$(echo "$_REPORT" | grep "^ISSUE_COUNT:" | cut -d: -f2)
  echo "[html-verify] 發現問題：$_ISSUE_COUNT"

  if [[ "$_ISSUE_COUNT" -gt 0 ]]; then
    echo "$_REPORT" | grep "^ISSUE:" | head -20

    # 修復 MERMAID_SYNTAX：在源 .md 中移除缺少 and 的 par/end 包裹
    if echo "$_REPORT" | grep -q "^ISSUE:MERMAID_SYNTAX|"; then
      echo "[html-verify] 修復 MERMAID_SYNTAX（在 docs/diagrams/ 中移除無效 par/end）..."
      python3 - <<'FIXPY'
import re, sys
from pathlib import Path

diagrams = Path.cwd() / "docs" / "diagrams"
pages    = Path.cwd() / "docs" / "pages"

def fix_par_without_and(block_lines):
    result = []
    i = 0
    while i < len(block_lines):
        line = block_lines[i]
        s = line.strip()
        if re.match(r'^par\b', s):
            j = i + 1; depth = 1; found_and = False
            while j < len(block_lines):
                s2 = block_lines[j].strip()
                if re.match(r'^(par|loop|alt|opt|critical|break)\b', s2): depth += 1
                elif s2 == 'end':
                    depth -= 1
                    if depth == 0: break
                elif re.match(r'^and\b', s2) and depth == 1: found_and = True
                j += 1
            if not found_and:
                i += 1; depth = 1
                while i < len(block_lines):
                    s2 = block_lines[i].strip()
                    if s2 == 'end' and depth == 1: i += 1; break
                    if re.match(r'^(par|loop|alt|opt|critical|break)\b', s2):
                        depth += 1; result.append(block_lines[i])
                    elif s2 == 'end':
                        depth -= 1; result.append(block_lines[i])
                    elif re.match(r'^and\b', s2) and depth == 1:
                        pass  # skip stray 'and' in invalid par block
                    else:
                        result.append(block_lines[i])
                    i += 1
                continue
        result.append(line); i += 1
    return result

for html_file in sorted(pages.glob("diag-*.html")):
    content = html_file.read_text()
    has_issue = False
    for blk in re.findall(r'<pre class="mermaid">(.*?)</pre>', content, re.DOTALL):
        blk_s = blk.strip()
        if 'sequenceDiagram' not in blk_s: continue
        lines_b = blk_s.split('\n'); in_par = False; has_and = False
        for line in lines_b:
            s = line.strip()
            if re.match(r'^par\b', s): in_par = True; has_and = False
            elif re.match(r'^and\b', s) and in_par: has_and = True
            elif s == 'end' and in_par:
                if not has_and: has_issue = True
                in_par = False
    if not has_issue: continue
    # Map diag-{name}.html -> docs/diagrams/{name}.md
    md_name = html_file.stem[5:] + ".md"
    md_file = diagrams / md_name
    if not md_file.exists(): print(f"  WARN: source not found: {md_name}"); continue
    lines = md_file.read_text().split('\n')
    result = []; in_mermaid = False; mermaid_buf = []; changed = False
    for line in lines:
        if line.strip() == '```mermaid': in_mermaid = True; mermaid_buf = []
        elif in_mermaid and line.strip() == '```':
            in_mermaid = False
            if any('sequenceDiagram' in l for l in mermaid_buf):
                fixed = fix_par_without_and(mermaid_buf)
                if fixed != mermaid_buf: changed = True
                result.append('```mermaid'); result.extend(fixed); result.append('```')
            else:
                result.append('```mermaid'); result.extend(mermaid_buf); result.append('```')
        elif in_mermaid: mermaid_buf.append(line)
        else: result.append(line)
    if changed:
        md_file.write_text('\n'.join(result))
        print(f"  FIXED: {md_name}")
    else:
        print(f"  UNCHANGED: {md_name} (source may already be correct)")
FIXPY
    fi

    echo "[html-verify] 重新執行 gen_html.py 修復..."
    python3 "$HOME/.claude/gendoc/bin/gen_html.py"
  fi
done

if [[ "$_ISSUE_COUNT" -gt 0 ]]; then
  echo "⚠️  [html-verify] 仍有 $_ISSUE_COUNT 個問題未修復，列出詳情："
  echo "$_REPORT" | grep "^ISSUE:"
  echo ""
  echo "常見原因："
  echo "  FRONTMATTER    → gen_html.py 版本過舊（需 ≥ 3.2.0），執行 /gendoc-update 更新"
  echo "  BROKEN_IMG     → docs/*.md 中有不存在的圖片路徑，需修正來源 .md 或補充圖片檔"
  echo "  EMPTY_MERMAID  → docs/diagrams/*.md 中某個 mermaid block 為空"
  echo "  MERMAID_SYNTAX → sequenceDiagram 中 par 缺少 and 分隔子句（mermaid v11 語法錯誤）"
  echo "                   建議：重新執行 /gendoc-gen-diagrams 以正確語法重生成圖表"
else
  echo "✅ [html-verify] 所有圖表頁面驗證通過（frontmatter 已清除、圖片路徑正確、mermaid 非空、語法合規）"
fi
```

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
  - gen_html.py：~/.claude/gendoc/bin/gen_html.py（central，install.sh 維護）
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
| 路徑錯誤 | BASE 路徑計算錯誤 | gen_html.py 使用 Path.cwd()，確認從專案根目錄執行 |
| central script 不存在 | install.sh 未執行 | 執行 bash ~/projects/gendoc/install.sh |
| README 未生成 | Mode full 但未呼叫 gendoc readme | 確認 Step 1-A 執行了 Skill("gendoc", args="readme") |
