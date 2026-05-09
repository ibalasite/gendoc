# gen-html 問題清單（2026-05-09）

> 檔名：`issues.md`（複數，因為是清單；原寫 `issue.md` 拼字無誤但慣例用複數）
>
> 規則：每項都附「事實」「證據」「根因」。未實查者明標 `[未實查]`。
> 不討論修法，僅列問題與根因。

---

## 🎯 核心目標（北極星 — 所有 fix 必先 follow）

> **UI 線圖能清楚、美觀地表達語義，讀者不會誤會。**

任何 fix 提案都先用四把尺評估，達不到的解法不採用：

| 尺 | 含義 | 反例 |
|---|---|---|
| **1. 清楚** | 元素邊界、層次、語義一目了然 | 邊界淡到看不出區塊、表格擠在一起 |
| **2. 美觀** | 視覺協調、不刺眼、不破版 | sidenav `│` 殘留、撞色 focus ring |
| **3. 表達** | mock 看起來像它要表達的 UI | nested `<a>` 把內容吞掉、按鈕變連結 |
| **4. 不誤會** | 同類元素視覺一致，不同類元素視覺有差 | default 按鈕 focus 時看起來像 primary |

**優先順序**：4 > 3 > 1 > 2（誤會 > 內容遺失 > 看不清 > 不美）。
解法若同時對多把尺都加分 → 優先採用；只「蓋過去」不解根因的 workaround 不採用。

---

## A. HTML 渲染瑕疵

### A1. erp/index.html 出現 nested `<a><a>` 巢狀標籤

- **事實**：UI Prototype + API Explorer 兩列的連結 HTML5 invalid，瀏覽器會吞 content。
- **證據**：`grep <a><a>` 在 erp/index.html 找到 2 處：
  ```html
  <a href="prototype/index.html" target="_blank" rel="noopener">
    <a href="prototype/index.html">docs/pages/prototype/index.html</a>
  </a>
  ```
- **根因**：`gen_html.py` 第 1957 行 `_code_to_link` 的 regex `<code>([^<]+)</code>` 不檢查 `<code>` 是否已在 `<a>` 內。
- **觸發來源**：erp/README.md line 421-422 用 `` [`X`](X) `` 寫法（連結文字為 backtick code）→ 產生 `<code>` → 被 R1 二次包 `<a>`。

### A2. sidenav items 顯示前綴 `│` 殘留

- **事實**：截圖中 erp/PDD 的 sidenav 顯示「| ERP Side」「| Nav」「|」。
- **證據**：3 個檔案受影響：
  - `pet/admin_impl.html`
  - `pet/prototype__admin-moderation-prototype.html`
  - `erp/pdd.html`
- **根因**：`gen_html.py` 第 1200 行 `_um_ascii_strip_pipes`，當 line 中只有單一 `│` 時，`first == last`，函式直接 return line 不剝。

### A3. card / page / modal 邊界線淡

- **事實**：視覺上邊界不明顯。
- **證據**：CSS 設定值 `border: 1px solid #cbd5e1`（淺灰）。
- **根因**：CSS 設計選擇。

### A4. table 看起來小、列分隔線淡

- **事實**：表格內距小、行間分隔線不明顯。
- **證據**：CSS `padding: 0.5rem 0.625rem`、`border-bottom: 1px solid #e2e8f0`（淺灰）。
- **根因**：CSS 設計選擇。

### A5. mock 元件 focus 時讓讀者誤會語義（已實查 + 已拍板採 P4）

- **事實**：截圖中 erp/PDD 的「套用」按鈕有藍框，「重設」沒有。讀者會誤以為「套用」是 primary 按鈕。
- **證據**：Playwright 跑 erp/pdd.html，對「套用」按鈕（class=`umock__btn umock__btn--default`）取 computed style：
  - 未 focus：`outline-style: none`，無藍框
  - focus 時：`outline-color: rgb(0,95,204)`、`outline-width: 1px`、`outline-style: auto` ← 瀏覽器**預設 focus ring**
  - 兩個按鈕（套用/重設）class 完全相同；差別只在「套用」是 actions 容器內第一個 button，使用者截圖時 focus 落在它
- **根因**：瀏覽器預設 `:focus-visible` outline 與 mock 的 default 變體配色撞色。**不是 CSS bug、不是 gen_html 邏輯問題，但是核心目標第 4 把尺（不誤會）的直接違反**。
- **核心目標對齊**：第 4 把尺「不誤會」直接命中 → **必修**。
- **修法決策（已拍板）**：採 **P4 — mock 元件加 `tabindex="-1"`，根本不可 focus**。
  - 為何不採 P1a（自定 outline，窄）：只是「蓋過去」，未解根因（mock 不應該被 Tab 到）。
  - 為何不採 P1b（全頁 focus 設計系統，寬）：過度擴張，跟 UI 線圖「不誤會」目標無直接關係。
  - 為何不採 P2（移除 outline）：破 WCAG 2.1 SC 2.4.7（焦點可見）。
  - 為何不採 P3（不修）：誤會仍在，違反核心目標 4。
  - **P4 為何符合**：mock 是文件展示用、不是真互動；focus ring 永遠不出現 → 0 誤會（根除非覆蓋）；鍵盤使用者本來就點不下去這些按鈕，跳過反而合理；改動最小（3 個 render 函式各加 1 個 HTML attr）。
- **影響範圍**：`_um_r_btn`、`_um_r_input`、`_um_r_search` 三個 render 函式。不動外殼（sidebar-toggle / search-input / 一般連結）。

---

## B. 目錄結構違反 source 1:1 mirror

### B1. `docs/diagrams/X.md` 應產出 `pages/diagrams/X.html`

- **事實**：來源 47 個 `.md`，輸出 49 個 flat `pages/diag-*.html`（含 9 個 stale）。
- **證據**：`pages/diagrams/` 子目錄不存在；`pages/diag-*.html` 49 個。
- **根因**：`gen_html.py` 多處寫死 `diag-{stem}` flat naming：
  - L1902: `flat = 'diag-' + base[len('diagrams/'):] + '.html'`
  - L1917: `flat = 'diag-' + md_part[:-3] + '.html'`
  - L2596 / L2600: `write_page(f"diag-{stem}.html", ...)`

### B2. `docs/req/X.md` 應產出 `pages/req/X.html`

- **事實**：pet 來源 1 個（idea-input.md），輸出 flat `pages/req__idea-input.html`。
- **證據**：`pages/req/` 子目錄不存在；`pages/req__idea-input.html` 存在。
- **根因**：`scan_subdirectory_docs` 用 `{subdir}__{stem}` flat slug 規則。

### B3. `pages/diagrams/` 子目錄不存在

- **事實**：`os.path.exists() = False`。
- **根因**：同 B1。

### B4. `pages/req/` 子目錄不存在

- **事實**：`os.path.exists() = False`。
- **根因**：同 B2。

---

## C. 「實作用」檔案誤生成到 pages/  ✅ **全部 RESOLVED BY B 群（方向反轉）**

> **2026-05-09 user 釐清**：原 C 群 4 子題都是「EXCLUDE 方向」，user 反轉
> 為「.md 都要鏡射，但要進正確 subdir」。B 群實作後 4 子題全部達成。

### ~~C1.~~ `docs/blueprint/mock/MOCK_SERVER_GUIDE.md`  ✅ resolved by B1+B3

- **原**：blueprint 不該出現在 pages
- **現**：`pages/blueprint/mock/mock_server_guide.html` 存在於正確 subdir（B1 slug + B3 writer）

### ~~C2.~~ `docs/contracts/*.md`  ✅ resolved by B1+B3

- **原**：contracts 不該在 pages
- **現**：`pages/contracts/{api-admin,api-player,event-schema}-contract.html` 全部進 subdir

### ~~C3.~~ sidebar 出現 📁 blueprint/、📁 contracts/、📁 bdd/  ✅ resolved by B5

- **原**：sidebar 不該顯示這些折疊群
- **現**：sidebar **正確顯示**這些折疊群（user 新意願：sidebar 樹狀 = pages/ 目錄結構）

### ~~C4.~~ `docs/CONTRACTS.md`（root）vs `docs/contracts/`（subdir）命名衝突  ✅ resolved by B1+B2

- **原**：root contracts.html 與 flat contracts__*.html 共用 contracts 前綴混淆
- **現**：`pages/contracts.html`（檔，root CONTRACTS.md）與 `pages/contracts/`（目錄，含 3 個 sub-md html）filesystem 共存無衝突

---

## D. Prototype 曝光降級

### D1. 12 天前 erp/index.html body 有 prominent index-cards

- **事實**：commit `8517c6b`（12 天前）erp/index.html body 含：
  ```html
  <div class="index-grid">
    <a class="index-card" href="prototype/index.html">🖥️ UI Prototype...</a>
    <a class="index-card" href="prototype/api-explorer/index.html">🔌 API Explorer...</a>
  </div>
  ```
- **證據**：`git show 8517c6b:docs/pages/index.html | grep -A3 index-card`。

### D2. 10 小時前（548bc9c）cards 消失

- **事實**：跑過一次 gen-html 後，cards 變成 README markdown 表格列。
- **證據**：commit `548bc9c` 內容 `<tr><td>UI Prototype</td><td><code>docs/pages/prototype/index.html</code></td>...`。

### D3. 現在（1dacc22）= D2 + A1 nested `<a>` bug

- **事實**：表格列因 R1 bug 變成 invalid HTML。
- **證據**：A1 證據。

### D4. pet/index.html body 從未有 prominent cards

- **事實**：grep 6 個 commit 都沒找到 `index-card.*prototype` 在 pet 的 body。
- **根因**：`gendoc-gen-prototype` 沒對 pet 跑過 Step 4-B（推測）。

### D5. 根因：架構衝突

- **事實**：`skills/gendoc-gen-prototype/SKILL.md` Step 4-B 把 inline-cards 注入 `pages/index.html`，但每次 `gen_html` 重生 `index.html` 都會洗掉。
- **證據**：
  - SKILL.md 內容含 `class="index-card" ... prototype/index.html` HTML 範本
  - `gen_html.py` 的 `main()` 寫 `index.html` 時不知道 gen-prototype 的 cards 存在
- **判定**：架構級衝突，gen-html 規生時不知道下游 skill 注入的內容會被洗。

---

## E. 重複命名（8 對 stale 殘留）  ✅ **實查澄清：無 gen_html bug**

> **2026-05-09 sandbox-pet 重生實機驗證**：current gen_html 對每個 source `.md`
> **只產出一個** `.html`。「同一份 source 產出兩個 HTML」的描述不正確。

| # | 雙版檔 | 真實 source 狀況 | 結論 |
|---|---|---|---|
| ~~E1~~ | `align_report.html` ↔ `align-report.html` | **兩份 source 真的存在** (`ALIGN_REPORT.md` + `ALIGN-REPORT.md`) | ✅ 不是 bug — pet 真的有兩份不同文件 |
| ~~E2~~ | `align_fix_summary.html` ↔ `align-fix-summary.html` | 1 個 source（`ALIGN_FIX_SUMMARY.md`），dash 版 stale | ✅ stale，「舊的不砍」rule |
| ~~E3~~ | `align_fix_complete.html` ↔ `align-fix-complete.html` | 1 個 source，dash stale | ✅ 同上 |
| ~~E4~~ | `admin_impl.html` ↔ `admin-impl.html` | 1 個（`ADMIN_IMPL.md`），dash stale | ✅ 同上 |
| ~~E5~~ | `client_impl.html` ↔ `client-impl.html` | 1 個，dash stale | ✅ 同上 |
| ~~E6~~ | `local_deploy.html` ↔ `local-deploy.html` | 1 個，dash stale | ✅ 同上 |
| ~~E7~~ | `implementation_readiness.html` ↔ `implementation-readiness.html` | 1 個，dash stale | ✅ 同上 |
| ~~E8~~ | `developer_guide.html` ↔ `developer-guide.html` | 1 個，dash stale | ✅ 同上 |

**E 群結論**：
- **E1**：pet 內容問題（兩份真實 source），不是 gen_html bug；若要清需 pet 端決定刪哪份
- **E2–E8**：dash 版是過去 slug 規則殘留；current gen_html 不再產，**符合「舊的不砍」rule**，屬 H1 cleanup 範疇

---

## F. ASCII UI Mock（澄清，非真 bug）

### ~~F1~~

- **撤回**。`pet/admin-impl.html` 是 stale（屬 E4/H1 類）；`pet/admin_impl.html`（現行版）有 80 個 umock_，沒有 mock 偵測 bug。

### F2. 5 處橫向多框架構圖仍 `<pre>`

- **事實**：pet/arch.html、edd.html 中有架構橫向多框（多個並排的 ┌──┐）。
- **判定**：使用者之前說過超出 UI Mock DSL 範圍，留 `<pre>` 是符合規範的。**不是 bug**。

---

## G. doc_cards_section（首頁卡片格）

### ~~G1~~

- **撤回**（誤判）。CICD/Developer Guide/Implementation Readiness/Manifest/Resource/background-jobs 都是合法 root `.md` 文件。

### G2. doc_cards_section 不含 prototype 卡片

- **事實**：函式內無 `prototype`、無 `scan_prototype` 引用。
- **證據**：grep 結果 `'prototype' in body.lower() = False`。

---

## H. 額外發現（清查中）

### H1. pet/pages 有 22 個 stale HTML 檔

- **事實**：來源 `.md` 已不存在，但 HTML 仍留存。
- **證據**：腳本檢查共 22 個（含 `admin-dashboard.html`、`player-arena.html`、9 個 cicd 舊圖、5 個 puml 舊圖等）。
- **根因**：gen_html 不會清舊 HTML，重生時 .md 已刪但 HTML 仍在。

### H2. erp/pages 也有 stale HTML（待清點）`[未實查]`

- **事實**：erp 也有歷史殘留，但未細數。
- **驗證需要**：跑與 pet 相同的腳本。

### H3. erp sidebar 沒 `diagrams/` 折疊群

- **事實**：因為 `diag-*.html` flat 在 root，不會被 subdir scan 收進折疊群。
- **根因**：同 B1，flat 命名導致 sidebar 無法分群。

---

# 待補實查（未列入主清單的不確定項）

| 項 | 待查內容 |
|---|---|
| ~~A5~~ | 已實查 + 已拍板採 P4（`tabindex="-1"`，已更新主清單）|
| E1–E8 | gen_html.py 的 slugify 規則 commit history，確認哪個是現行版 |
| H2 | erp/pages stale HTML 數量 |

---

# 行為承諾（這次討論流程）

1. 不再提任何修法
2. 不再排優先順序
3. 不再問做不做
4. 一個一個問題討論：先確認問題理解，再討論修法，再 fix
5. fix 完一個才談下一個
