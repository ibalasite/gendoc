# gen-html 修復 TODO — A 群（HTML 渲染瑕疵）

> 範圍：只討論 issues.md 的 **A 群**（A1–A5）。
> B/C/D/E/F/G/H 群的細節保留在 `logic/issues.md`，**A 群結束後**才往下談。

---

## 🎯 核心目標（北極星 — 所有 fix 必先 follow）

> **UI 線圖能清楚、美觀地表達語義，讀者不會誤會。**

任何 fix 提案都必須先用四把尺評估，達不到的解法不採用：

| 尺 | 含義 | 反例 |
|---|---|---|
| **1. 清楚** | 元素邊界、層次、語義一目了然 | 邊界淡到看不出區塊、表格擠在一起 |
| **2. 美觀** | 視覺協調、不刺眼、不破版 | sidenav `│` 殘留、撞色 focus ring |
| **3. 表達** | mock 看起來像它要表達的 UI | nested `<a>` 把內容吞掉、按鈕變連結 |
| **4. 不誤會** | 同類元素視覺一致，不同類元素視覺有差 | default 按鈕 focus 時看起來像 primary |

**優先順序**：4 > 3 > 1 > 2（誤會 > 內容遺失 > 看不清 > 不美）。

---

## 行為承諾

1. 每個 fix 先確認問題理解 → 對齊核心目標 → 寫 test（RED）→ 改 code（GREEN）→ commit（不 push）
2. 一個 fix 完才談下一個
3. Commit 訊息：`fix(gen-html): A<N> ...`

Status: `review` | `todo` | `running` | `done`

---

## 處理順序（依核心目標優先級）

1. **A1**（4. 表達 + 3. 表達：內容遺失，最硬）
2. **A5/P4**（4. 不誤會：語義誤會，必修；改動最小）
3. **A2**（2. 美觀 + 3. 表達：破版）
4. **A3**（1. 清楚：CSS 微調，需 user 看截圖確認）
5. **A4**（1. 清楚：同上）

---

## # A1. erp/index.html nested `<a><a>`

| 欄位 | 內容 |
|---|---|
| **問題** | R1 自動加連結把已在 `<a>` 內的 `<code>` 又包一層，產生 invalid nested `<a><a>`，瀏覽器吞 content |
| **證據** | erp/index.html 2 處；gen_html.py L1957 `_code_to_link` regex `<code>([^<]+)</code>` 不檢查 `<code>` 上下文；觸發來源 erp/README.md L421-422 `` [`X`](X) `` 寫法 |
| **對齊核心目標** | **3. 表達**（內容被瀏覽器吞 → 讀者看不到）+ **4. 不誤會**（讀者預期是連結但連結結構壞掉）|
| **預期解** | `_code_to_link` 改成兩階段：先掃出所有 `<a>...</a>` 區間（**支援跨行**），再對其外的 `<code>` 才包連結 |
| **Test case（含 edge）** | 1. `test_code_inside_a_not_double_wrapped`：`<a href="x"><code>x</code></a>` → 不變<br>2. `test_code_outside_a_wrapped`：裸 `<code>x</code>`（pages/x 存在）→ 包成 `<a>`<br>3. `test_code_inside_a_multiline`（**新增 edge**）：`<a href="x">\n<code>y</code>\n</a>` → 不變<br>4. `test_code_inside_a_multiple_codes`（**新增 edge**）：`<a href="x"><code>y</code><code>z</code></a>` → 兩個都不再被包<br>5. `test_code_inside_already_nested_a`（**新增 edge**）：`<a href="x"><a href="y"><code>z</code></a></a>` → 不再追加包覆 |
| **不影響其他 case** | 既有 18+ path_rewriter test 全綠；R1 對裸 `<code>` 仍正常包；nested 計數歸零 |
| **驗收對應** | D（erp/index.html 沒有 invalid HTML）|
| **Status** | **done** ✅（5 test 全綠，196/196 全綠）|

---

## # A2. sidenav items 顯示前綴 `│` 殘留

| 欄位 | 內容 |
|---|---|
| **問題** | `_um_ascii_strip_pipes` 對單一 `│` case 直接 return 原樣 |
| **證據** | 影響 3 檔（pet/admin_impl, pet/prototype__admin-mod-prototype, erp/pdd）；gen_html.py L1200 `first == last` 條件下直接 return line 不剝 |
| **對齊核心目標** | **2. 美觀**（殘留管道符破版）+ **3. 表達**（讓 mock 不像真 sidenav）|
| **預期解** | `first == last` 時：在頭（first==0 或前面只有空白）→ 剝左；在尾（last==len-1 或後面只有空白）→ 剝右；中間 → 保留（mock 作者刻意當分隔符）<br>**＋ render 層追加：sidenav item trim 後為空字串時不渲染**（避免空 row 破洞）|
| **Test case** | 1. `test_strip_pipes_single_at_start`：`│ Item` → `Item`<br>2. `test_strip_pipes_single_at_end`：`Item │` → `Item`<br>3. `test_strip_pipes_single_in_middle`：`Foo │ Bar` → `Foo │ Bar`（保留）<br>4. `test_strip_pipes_only_pipe`：`│` → ``（空字串）<br>5. `test_strip_pipes_pipe_then_whitespace`：`│   ` → ``（空字串）<br>6. `test_sidenav_filters_empty_item`：sidenav AST 含一個 strip 後為空的 line → render 結果不含空 `<li>` |
| **不影響其他 case** | 既有 14+ ASCII parser test 全綠 |
| **驗收對應** | A（sidenav 不出現 `│` `|` 開頭）|
| **Status** | **done** ✅（8 test 全綠，208/208 全綠）|

---

## # A3. card / page / modal 邊界淡

| 欄位 | 內容 |
|---|---|
| **問題** | `border: 1px solid #cbd5e1` 視覺不明顯；title-bar `border-bottom: 1px solid #e2e8f0` 同樣淡 |
| **證據** | gen_html.py L162-173；scope 確認在 `.umock__page, .umock__modal, .umock__card` 與 `.umock__card-title, .umock__page-title, .umock__modal-titlebar` |
| **對齊核心目標** | **1. 清楚**（邊界看不出來）|
| **預期解** | 統一加深「外框 + title 內分隔線」兩處：<br>- `.umock__page, .umock__modal, .umock__card`：`border: 1.5px solid #94a3b8`<br>- `.umock__card-title, .umock__page-title, .umock__modal-titlebar` 的 `border-bottom`：改 `1.5px solid #94a3b8`（**同步加深，避免只解一半**）<br>- box-shadow：保守不動（避免 card 看起來像 modal，破第 4 把尺）|
| **Test case** | 1. `test_css_card_border_is_strong`：rendered HTML inline style 含 `border: 1.5px solid #94a3b8`<br>2. `test_css_title_bar_border_is_strong`：含 `border-bottom: 1.5px solid #94a3b8`（針對三個 title 選擇器）<br>3. **視覺驗證**：跑 erp/pdd.html 截圖給 user 看 |
| **不影響其他 case** | 不動 lightbox / PUML / mermaid CSS；不動 sidebar、navbar；不動一般 markdown div |
| **驗收對應** | B（card / page / modal 邊界視覺清楚）|
| **Status** | **done** ✅（2 test 全綠，210/210 全綠；視覺驗證待 user 看截圖）|

---

## # A4. table 小、分隔線淡

| 欄位 | 內容 |
|---|---|
| **問題** | cell padding 0.5rem 偏小、border `#e2e8f0` 偏淡 |
| **證據** | gen_html.py L222-225；scope 確認在 `.umock__table`（**不影響一般 markdown table**）|
| **對齊核心目標** | **1. 清楚**（行擠在一起、分隔線看不到）|
| **預期解** | - `.umock__table th, td`：padding `0.75rem 0.875rem`、border-bottom `1px solid #cbd5e1`、font-size `0.9rem`<br>- `.umock__table th`：border-bottom `2px solid #94a3b8`（thead 強化）<br>- **拿掉 `border-radius`**（collapsed table 上 border-radius 不生效，寫了也白寫）<br>- 不加外殼 div（避免改動 render 邏輯影響既有 191 測試）|
| **Test case** | 1. `test_css_table_padding_increased`：含 `padding: 0.75rem 0.875rem`<br>2. `test_css_table_row_border_strong`：td border 改 `#cbd5e1`<br>3. `test_css_table_thead_emphasized`：th border-bottom `2px solid #94a3b8`<br>4. `test_css_table_no_invalid_border_radius`：`.umock__table` rule 不含 `border-radius`<br>5. **視覺驗證 + 寬度檢查**：跑 erp/pdd.html，確認 table 不溢出 sidebar 區（用 Playwright bbox） |
| **不影響其他 case** | 不動 markdown 一般 table；不動 .umock__pagination |
| **驗收對應** | C（table cell padding 足夠、列分隔明顯、thead 突出）|
| **Status** | **done** ✅（4 test 全綠，214/214 全綠；視覺驗證待 user 看截圖）|

---

## # A5. mock 元件不可 focus（採 P4）

| 欄位 | 內容 |
|---|---|
| **問題** | 瀏覽器預設 `:focus-visible` outline（`rgb(0,95,204)` 1px auto）讓 default 變體按鈕 focus 時看起來像 primary |
| **證據** | Playwright 實查 erp/pdd.html「套用」按鈕；gen_html.py L201-206 4 種 button 變體均無 `:focus` 規則 |
| **對齊核心目標** | **4. 不誤會**（default 看起來像 primary = 語義誤會）|
| **預期解** | mock 是文件展示用，加 `tabindex="-1"` 讓 Tab 鍵跳過 → focus ring 永遠不出現（根除非覆蓋）<br>影響 3 個 render 函式：<br>- `_um_r_btn` (gen_html.py L839)<br>- `_um_r_input` (L848)<br>- `_um_r_search` (L893) |
| **Test case** | 1. `test_mock_button_renders_tabindex_minus_one`：`_um_r_btn(...)` 輸出含 `tabindex="-1"`<br>2. `test_mock_input_renders_tabindex_minus_one`：同上<br>3. `test_mock_search_renders_tabindex_minus_one`：同上<br>4. `test_outer_chrome_button_unaffected`：`.sidebar-toggle` 等外殼按鈕的 HTML 不含 `tabindex="-1"`（不能誤波及）|
| **不影響其他 case** | 不動外殼（sidebar-toggle、search-input、頁面連結）；既有 191 個 UI Mock test 不檢查 tabindex |
| **驗收對應** | E（截圖中不存在 default 看起來像 primary 的視覺誤會）|
| **Status** | **done** ✅（4 test 全綠，200/200 全綠）|

---

## A 群決策點（彙總）

| 編號 | 決策 | 狀態 |
|---|---|---|
| A3 | 邊界 CSS 加深的色值 / 寬度（`#94a3b8` / 1.5px）→ 開做後 user 看截圖再 tune | 已寫 spec |
| A4 | table padding / border 的具體值（0.75rem / `#cbd5e1`）→ 同上 | 已寫 spec |
| A5 | P1/P2/P3 → ~~已拍板採 P4~~ | ✅ done |

---

## 行為承諾

- A 群 5 項全部 `done` 之前，**不討論 B/C/D/E/F/G/H**
- 順序：A1 → A5 → A2 → A3 → A4
- 每項：寫 test（RED）→ 改 code（GREEN）→ run all tests → commit（不 push）
- 每項 commit 後 user 確認 → 才進下一項

---

# ════════════════════════════════════════════════
# B 群（docs/**/*.md → pages/**/*.html 全面 1:1 鏡射）
# ════════════════════════════════════════════════

## 統一原則（user 在 2026-05-09 釐清）

> **使用者原話**：
> - 「docs/ 有子目錄，有些有 md 的文件，像 `blueprint/mock/xxx.md` 也是要依目錄，相對放在 `pages/xxxxxx/xxx/xxx.html`」
> - 「.md 都是轉換目標，但其他檔不動」
> - 「用途可以使用者閱讀，不用去翻 .md，適合多人 review 用」
> - 「舊的不砍」
> - 「sidebar 視覺結構，有目錄的要能折疊」
> - 「原來不在根目錄，就不要在根目錄放」
> - 「要跟 pages/ 下的目錄結構相同，這樣才知道對比那一份 .md」
> - 「docs/prototype 應該是有問題的，是舊版，但剛好可以測，在 pages/ 有了 prototype，docs/prototype 能不能不破壞 pages/prototype/ 也長出三份新的 html，但原本在 pages/prototype/*.html 不破壞」

**唯一規則（一句話）**：
> **所有 `docs/**/*.md` → `pages/**/*.html`，保留相對路徑；非 `.md` 不動；sidebar 樹狀結構 = `pages/` 目錄結構（含折疊）；既有 `pages/prototype/*.html` 絕不覆寫/刪除。**

**對齊核心目標**：
- **3. 表達**：pages/ 目錄結構就是文件分類；URL `pages/blueprint/mock/X.html` 一看就知道源頭是 `docs/blueprint/mock/X.md`
- **4. 不誤會**：URL ↔ source path 完全對得上，不會誤判分類

---

## B 群驗收標準

- **A**. `find pages -name '*.html'` 與 `find docs -name '*.md'` 路徑一一對應（除 prototype/ 互動 HTML 例外）
- **B**. 不再產生任何 flat slug（`diag-X.html`、`req__X.html`、`blueprint__mock-X.html`、`contracts__X.html`、`prototype__X.html`）
- **C**. **舊的 flat HTML 不砍**（user 明確指示）；user 視覺上會看到舊 + 新雙版
- **D**. **`pages/prototype/` 既有 HTML 絕不覆寫/刪除**
- **E**. 跨層連結正確：
  - 從 `pages/diagrams/X.html` 連 `pages/EDD.html` 自動寫 `../EDD.html`
  - 從 `pages/blueprint/mock/X.html` 連 `pages/EDD.html` 自動寫 `../../EDD.html`
- **F**. Sidebar 樹狀結構：
  - 根目錄 .md → flat list（既有）
  - 每個有 .md 的子目錄 → `<details>` 折疊群
  - 巢狀子目錄 → 巢狀折疊（`📁 blueprint/` 內含 `📁 mock/`）
  - 折疊群連結指向新 subdir 路徑
- **G**. 既有 214 test 全綠（含 R3 系列 expected 值升級）

---

## # B1. 統一 scanner — slug 公式 `subdir__stem` → `subdir/stem`

| 欄位 | 內容 |
|---|---|
| **問題** | `scan_subdirectory_docs` 用 `{subdir}__{stem}` flat slug，造成 `docs/blueprint/mock/X.md` → `pages/blueprint__mock-x.html` 全部擠在 root |
| **證據** | gen_html.py L2334：`slug = subdir.name.lower() + '__' + str(rel).replace('/', '-').replace('\\', '-').lower()`；scan 是 rglob 已遞迴，但 slug 把路徑壓平 |
| **對齊核心目標** | 3. 表達 + 4. 不誤會（URL ↔ source path 對應）|
| **預期解** | slug 公式改成 `{subdir}/{rel-with-slashes-lowercase}`，保留 `/` 分隔。例：<br>- `docs/req/idea-input.md` → slug `req/idea-input`<br>- `docs/blueprint/mock/X.md` → slug `blueprint/mock/x` |
| **Test case** | 1. `test_B1_scan_slug_preserves_slash_simple`：`docs/req/idea-input.md` → slug `req/idea-input`<br>2. `test_B1_scan_slug_preserves_slash_nested`：`docs/blueprint/mock/X.md` → slug `blueprint/mock/x`<br>3. `test_B1_scan_slug_no_double_underscore`：scan 結果中沒有任何 slug 含 `__`<br>4. `test_B1_scan_slug_lowercase`：`MOCK_SERVER_GUIDE.md` → slug 結尾為 `mock_server_guide`（lowercase 規則保留） |
| **不影響其他 case** | `scan_prototype_entries`（互動 HTML 入口）獨立邏輯，不波及 |
| **驗收對應** | A、B |
| **Status** | **done** ✅（4 test 全綠，218/218 全綠）|

---

## # B2. `write_page` 支援巢狀子目錄（mkdir parents）

| 欄位 | 內容 |
|---|---|
| **問題** | `write_page(filename, ...)` 直接 `out_path.write_text()`，若 filename 含 `/`（如 `blueprint/mock/x.html`）且父目錄不存在 → FileNotFoundError |
| **證據** | gen_html.py L2599-2601：`out_path = PAGES_DIR / filename` 後直接 `write_text`，無 mkdir |
| **對齊核心目標** | （技術前置）支撐 B1 slug 改 `/` 後仍能寫出檔案 |
| **預期解** | `out_path.parent.mkdir(parents=True, exist_ok=True)` 加在 `write_text` 之前 |
| **Test case** | 1. `test_B2_write_page_creates_nested_dirs`：呼叫 `write_page("a/b/c.html", ...)` 在乾淨 PAGES_DIR 上 → `pages/a/b/c.html` 寫入成功，路徑上 `a/`、`a/b/` 都被建立<br>2. `test_B2_write_page_root_unchanged`：`write_page("foo.html", ...)` 仍在 `pages/foo.html`（regression） |
| **不影響其他 case** | root .html 寫入路徑不變 |
| **驗收對應** | A |
| **Status** | **done** ✅（3 test 全綠，221/221 全綠）|

---

## # B3. 既有 writer site 全部改用統一 slug

| 欄位 | 內容 |
|---|---|
| **問題** | 4 處 writer 寫死 flat naming，需全部改用 B1 的新 slug 公式 |
| **證據** | gen_html.py：<br>- L2646 `write_page(f"diag-{stem}.html", ...)` (server_diagrams)<br>- L2650 `write_page(f"diag-{stem}.html", ...)` (frontend_diagrams)<br>- L2657 `write_page(f"{slug}.html", ...)` (subdir_docs，slug 仍是 flat) |
| **對齊核心目標** | 3. 表達 + 4. 不誤會 |
| **預期解** | <br>1. `server_diagrams` / `frontend_diagrams` writer：`f"diagrams/{stem}.html"`<br>2. `subdir_docs` writer：`f"{slug}.html"`（slug 已含 `/` 來自 B1）|
| **Test case** | 1. `test_B3_diagrams_writer_subdir`：跑後 `pages/diagrams/{stem}.html` 存在<br>2. `test_B3_diagrams_writer_no_flat_diag`：跑後**沒有**新寫 `pages/diag-{stem}.html`<br>3. `test_B3_blueprint_mock_writer_subdir`：fixture `docs/blueprint/mock/X.md` → `pages/blueprint/mock/x.html` 存在<br>4. `test_B3_contracts_writer_subdir`：fixture `docs/contracts/Y.md` → `pages/contracts/y.html` 存在<br>5. `test_B3_req_writer_subdir`：fixture `docs/req/Z.md` → `pages/req/z.html` 存在；**沒有** `pages/req__z.html` |
| **不影響其他 case** | 根目錄 .md writer (line 2620, 2624) 不動 |
| **驗收對應** | A、B |
| **Status** | **done** ✅（5 test 全綠，226/226 全綠）|

---

## # B4. `pages/prototype/` 既有檔保護

| 欄位 | 內容 |
|---|---|
| **問題** | `gendoc-gen-prototype` 寫互動 HTML 到 `pages/prototype/index.html`、`pages/prototype/api-explorer/index.html` 等。若 gen_html 鏡射 `docs/prototype/*.md` 不小心覆寫了 `index.html`，互動入口會被破壞 |
| **證據** | user 原話：「pages/prototype/*.html 不破壞」；現況 `scan_subdirectory_docs` 會掃 `docs/prototype/*.md`，若新寫的 .html 與 gen-prototype 既有 .html 同名會覆寫 |
| **對齊核心目標** | （行為承諾）不破壞下游 skill 寫的內容；間接保 4. 不誤會（互動入口若消失 user 會誤以為功能沒了）|
| **預期解** | `write_page` 對 prototype/ 子目錄啟用「**目標檔已存在 → skip 並印 `↪ skip (preserved)`**」；其他子目錄正常覆寫。實作：<br>```python<br>if out_path.exists() and 'prototype' in out_path.relative_to(PAGES_DIR).parts:<br>    print(f"↪ skip {filename} (preserved)")<br>    return<br>``` |
| **Test case** | 1. `test_B4_prototype_existing_html_preserved`：fixture 預存 `pages/prototype/index.html` 內容 = `MARKER-INTERACTIVE`，跑 gen_html 後內容**不變**<br>2. `test_B4_prototype_md_mirror_writes_when_target_absent`：fixture `docs/prototype/sample.md`，預先**沒有** `pages/prototype/sample.html` → 跑後**寫入**<br>3. `test_B4_prototype_md_skip_when_target_present`：fixture `docs/prototype/sample.md`，預存 `pages/prototype/sample.html` = `INTERACTIVE-VERSION` → 跑後內容**不變**<br>4. `test_B4_non_prototype_subdir_overwrites_normally`：fixture `docs/blueprint/mock/X.md` 已有 `pages/blueprint/mock/x.html`（前次 gen_html 寫的）→ 跑後**覆寫**（非 prototype，正常 regenerate） |
| **不影響其他 case** | 非 prototype/ 子目錄 writer 行為不變（每次 gen_html 重生覆寫）|
| **驗收對應** | D |
| **Status** | **done** ✅（5 test 全綠，231/231 全綠）|

---

## # B5. Sidebar 樹狀折疊 + diagrams 內部分區（non-clickable label）

| 欄位 | 內容 |
|---|---|
| **問題** | <br>1. 現有 `make_sidebar` 對所有 subdir 平層處理（`<details>` 只一層），無法表達 `blueprint/mock/` 這種巢狀<br>2. `📁 diagrams/` 內動輒 30~50 個 .md，平層列表太長，user「查找有困擾」 |
| **證據** | gen_html.py L2378-2391（subdir 只一層 details）；pet/erp diagrams/ 共 ~50 檔 |
| **對齊核心目標** | 3. 表達（sidebar 結構 = pages/ 目錄結構）+ 1. 清楚（不是平 50 行讓 user 找） |
| **預期解** | <br>**(a) 樹狀折疊**：`sub_docs` 從 `dict[subdir, flat-entries]` 升級為「目錄樹」；`make_sidebar` 遞迴 render：每層 subdir 一個 `<details><summary>📁 {name}/</summary>...</details>`<br>**(b) `📁 diagrams/` 內部結構（user 拍板版）**：兩層 non-clickable label，**先依 server/frontend 分大區，再依檔名 prefix 分小區**。視覺樹：<br>```<br>📁 diagrams/  ← <details><summary><br>├─ Server UML       ← label（大區，non-clickable）<br>│  ├─ Activity      ← sub-label（小區，non-clickable）<br>│  │   📐 Activity Arena Battle<br>│  │   📐 Activity Claim And Train<br>│  │   ...<br>│  ├─ Class<br>│  │   📐 Class Application<br>│  │   ...<br>│  ├─ Sequence<br>│  ├─ State<br>│  ├─ CI/CD<br>│  └─ 其他<br>│      📐 Use Case<br>│      📐 Communication<br>│      📐 Component / Deployment / ER / Object<br>├─ Frontend UML    ← label（大區）<br>│  ├─ Activity     ← sub-label（同上規則但檔名前綴是 frontend-，分群時剝掉）<br>│  ├─ Class<br>│  ├─ Sequence<br>│  ├─ State<br>│  └─ 其他<br>├─ 📁 admin/        ← 巢狀子目錄用 nested <details><br>├─ 📁 modulith/<br>└─ 📁 puml/<br>```<br>**(c) 分群規則**：<br>- Server 區：依檔名 prefix（`activity-` / `class-` / `sequence-` / `state-`(含 `state-machine-`) / `cicd-`（加 `infra-local-topology`、`developer-workflow-activity` 一起進 CI/CD）/ 其他<br>- Frontend 區：先剝 `frontend-` 再用同上規則<br>**(d) active 規則**：current slug 在子樹任一位置 → 該層及所有上層 `<details>` 加 `open`<br>**(e) sub-label CSS**：用 `<div class="sidebar__label sidebar__label--sub">` 縮排 / 字小一階；現有 `<div class="sidebar__label">` 樣式不動 |
| **Test case** | <br>1. `test_B5_sidebar_one_level_collapsible`：fixture `docs/req/x.md` → sidebar 含 `<details>...📁 req/...<a href=".../req/x.html">`<br>2. `test_B5_sidebar_nested_collapsible`：fixture `docs/blueprint/mock/x.md` → sidebar 含 `<details>...📁 blueprint/...<details>...📁 mock/...`<br>3. `test_B5_sidebar_collapsed_unless_active`：current = `index` 時，所有 `<details>` 沒 `open`<br>4. `test_B5_sidebar_open_chain_when_active`：current = `blueprint/mock/x` 時，`📁 blueprint/` 與 `📁 mock/` 兩層都 `open`<br>5. `test_B5_sidebar_diagrams_collapsible`：fixture 含若干 `docs/diagrams/*.md` → sidebar 有 `📁 diagrams/` 折疊群（取消現有 root-level `Server UML / Frontend UML` 兩個獨立 section，把它們塞進 `📁 diagrams/` 內當 sub-label）<br>6. `test_B5_diagrams_inner_has_server_label`：`📁 diagrams/` 內含 `<div class="sidebar__label">Server UML</div>`（**non-clickable**，只當分區）<br>7. `test_B5_diagrams_inner_has_frontend_label`：同上對 Frontend UML<br>8. `test_B5_diagrams_inner_has_activity_sub_label`：fixture 含 `activity-arena-battle.md` → `📁 diagrams/` Server UML 區內有 `<div class="sidebar__label sidebar__label--sub">Activity</div>` 後接 `<a>` 連結<br>9. `test_B5_diagrams_inner_class_group`：fixture 含 `class-domain.md` → 出現 Class sub-label group<br>10. `test_B5_diagrams_frontend_strips_prefix_for_grouping`：fixture 含 `frontend-activity-init.md` → 出現在 Frontend UML 區的 Activity sub-label 下（不是 Server 區）<br>11. `test_B5_diagrams_other_group_catches_misc`：fixture 含 `er-diagram.md` → 進入 Server UML 的「其他」sub-label<br>12. `test_B5_diagrams_nested_subdir_uses_details`：fixture 含 `docs/diagrams/admin/admin-c4-container.md` → `📁 diagrams/` 內含 `<details>📁 admin/...`<br>13. `test_B5_sidebar_prototype_md_inside_folder`：fixture `docs/prototype/sample.md` → sidebar `📁 prototype/` 折疊群內含對應連結<br>14. `test_B5_sidebar_interactive_prototype_section_kept`：sidebar 仍有「Interactive Prototypes」section（與 `📁 prototype/` 並存） |
| **不影響其他 case** | `scan_prototype_entries` 邏輯不動；根目錄 .md flat list 不動；CSS 只加 `--sub` modifier，不動其他樣式 |
| **驗收對應** | F |
| **Status** | **done** ✅（13 test 全綠 + R3_3 既有 test 升級至 subdir 預期，244/244 全綠）|

---

## # B6. 跨層連結（`os.path.relpath`）

| 欄位 | 內容 |
|---|---|
| **問題** | 現有 `link()` 寫死 `<a href="{slug}.html">`，不考慮當前頁所在子目錄。當 page 在 `pages/blueprint/mock/x.html`，連 `EDD.html` 應該寫 `../../EDD.html`，現況寫 `EDD.html` 會找不到 |
| **證據** | gen_html.py L2363-2366：`link(slug, label, icon)` 直接 `href="{slug}.html"`，不接受 current page 路徑 |
| **對齊核心目標** | （技術前置）讓 sidebar 在所有頁面都能正確連結；不解 = 子目錄頁 sidebar 全部 broken |
| **預期解** | <br>1. `link()` 加參數 `current_slug`（或 `current_html_path`）<br>2. 用 `os.path.relpath(target_path, current_dir)` 算 href<br>3. `make_sidebar` 把 current 傳進去<br>4. `index-card` 的 href 同樣處理 |
| **Test case** | 1. `test_B6_link_root_to_root`：current=`index`，target=`edd` → href=`edd.html`<br>2. `test_B6_link_root_to_subdir`：current=`index`，target=`blueprint/mock/x` → href=`blueprint/mock/x.html`<br>3. `test_B6_link_subdir_to_root`：current=`blueprint/mock/x`，target=`edd` → href=`../../edd.html`<br>4. `test_B6_link_subdir_to_sibling_subdir`：current=`blueprint/mock/x`，target=`diagrams/y` → href=`../../diagrams/y.html`<br>5. `test_B6_active_class_still_works`：current=`blueprint/mock/x`，link 對應 slug 也是 `blueprint/mock/x` → 含 `class="...active"` |
| **不影響其他 case** | 既有 root page 的 sidebar href 結果不變（relpath 在同層就是檔名）|
| **驗收對應** | E |
| **Status** | **done** ✅（5 test 全綠，249/249 全綠）|

---

## # B7. Path rewriter R3-2 / R3-3 升級

| 欄位 | 內容 |
|---|---|
| **問題** | <br>1. **R3-3** `<a href="diagrams/X.md">` 目前 rewrite 成 `diag-X.html`（flat），應改成 `diagrams/X.html`<br>2. **R3-2** `<a href="docs/X.md">` 目前只支援 root `.md`；若 X 含 `/`（如 `docs/blueprint/mock/Y.md`），需要 rewrite 成 `blueprint/mock/y.html` |
| **證據** | gen_html.py：<br>- L1927 R3-3 docs 變體：`flat = 'diag-' + base[len('diagrams/'):] + '.html'`<br>- L1942 R3-3 直接變體：`flat = 'diag-' + md_part[:-3] + '.html'`<br>- L1933 R3-2：`html_name = base + '.html'`（base 含 `/` 時 fallback 行為要驗證） |
| **對齊核心目標** | 3. 表達（連結也對應 subdir 結構）|
| **預期解** | <br>1. R3-3 兩處：`flat = 'diag-' + ...` → `target = 'diagrams/' + ...`<br>2. R3-2：base 含 `/` 時也 try `pages_dir / (base + '.html')`，若存在則 rewrite |
| **Test case** | 1. **升級** `test_R3_3_diagrams_md_to_diag_html`（既有）：expected 從 `diag-X.html` 改 `diagrams/X.html`<br>2. **新增** `test_B7_R3_2_subdir_md_to_subdir_html`：input `<a href="docs/blueprint/mock/y.md">` 且 `pages/blueprint/mock/y.html` 存在 → href=`blueprint/mock/y.html`<br>3. **新增** `test_B7_R3_2_subdir_md_target_absent_strips`：target 不存在 → strip `<a>` 留 inner text<br>4. **新增** `test_B7_R3_3_diagrams_md_target_must_exist`：rewrite 用 `is_file()` 確認，不存在則 strip |
| **不影響其他 case** | R3-1 / R3-4 / R3-5 / R3-6 不動；R1（A1 已改）不動 |
| **驗收對應** | E |
| **Status** | **done** ✅（2 新 test 全綠；R3-3 已在 B5 順帶解；R3-2 既有 docs/X/Y/Z.md 邏輯已支援巢狀 subdir，無需改 code，251/251 全綠）|

---

## # B8. Sidebar 結構修正（B5 視覺檢視後 user 找到 3 個問題）

| 欄位 | 內容 |
|---|---|
| **問題** | 1. `SERVER UML / FRONTEND UML` label 縮排與 `📁 DIAGRAMS/` 同一層，看起來像獨立區段而非「DIAGRAMS 內的子分區」<br>2. `📐 PLANTUML` 獨立一塊，但 `.puml` 檔本來就在 `docs/diagrams/puml/`，應該在 `📁 DIAGRAMS/` 內<br>3. `INTERACTIVE PROTOTYPES` 獨立一塊，但語意上是 `📁 PROTOTYPE/` 內容的入口，應放進該折疊群 |
| **證據** | pet sidebar 截圖（`b_pet_sidebar_mid.png`）顯示三個結構問題 |
| **對齊核心目標** | 3. 表達（sidebar 結構應對應 pages/ 目錄真實階層，避免讓 user 誤判「PLANTUML 跟 DIAGRAMS 是平級」「INTERACTIVE PROTOTYPES 跟 PROTOTYPE 是兩件事」）|
| **預期解** | <br>1. **CSS**：`.sidebar__section details > .sidebar__label` padding-left 加深一階；`.sidebar__section details details .sidebar__link` 也再加深，反映實際層級<br>2. **PLANTUML 整併進 DIAGRAMS**：`make_sidebar` 中把 puml_files 的 render 從獨立 `<div class="sidebar__section">` 移進 `📁 DIAGRAMS/` `<details>` 內（在 Frontend UML 之後）。`puml_files` 為空時不顯示<br>3. **INTERACTIVE 整併進 PROTOTYPE**：`make_sidebar` 把 `scan_prototype_entries` 的 render 從獨立 section 移進 `📁 PROTOTYPE/` 折疊群內。當 `prototype` 不在 sub_docs 但有 interactive entries 時，仍要建一個 `📁 PROTOTYPE/` 折疊群把 interactive 包進來 |
| **Test case** | 1. `test_B8_server_uml_indented_under_diagrams`：SERVER UML label 在 sidebar 出現位置位於 `📁 DIAGRAMS/` 的 `<details>` 內（DOM 嵌套，既有 test 已驗）；視覺上靠 CSS `.sidebar__section details .sidebar__label` 加 padding-left → 在 HTML 中該 label 是否有對應 selector 命中（grep CSS）<br>2. `test_B8_plantuml_inside_diagrams`：fixture 含 `docs/foo.puml` → sidebar 中 `📐 PLANTUML` 出現在 `📁 DIAGRAMS/` `<details>` 內，**不在** root sidebar level<br>3. `test_B8_no_standalone_plantuml_section`：sidebar 不含 root-level `📐 PLANTUML` `<details>` section<br>4. `test_B8_interactive_inside_prototype_folder`：fixture 含 `docs/pages/prototype/index.html` → sidebar 中 `Interactive Prototypes` label + 🎮 連結出現在 `📁 PROTOTYPE/` `<details>` 內<br>5. `test_B8_no_standalone_interactive_section`：sidebar 不含 root-level `Interactive Prototypes` 區塊（必在 prototype/ 折疊群內）<br>6. `test_B8_interactive_alone_creates_prototype_folder`：fixture 只有 `pages/prototype/index.html`（**沒有** `docs/prototype/*.md`）→ sidebar 仍要建 `📁 PROTOTYPE/` 折疊群，內含 interactive 連結 |
| **不影響其他 case** | 既有 B5 子目錄 tree、B6 relpath、prototype 不覆寫邏輯（B4）不動；非 prototype/ 子目錄不受影響 |
| **驗收對應** | F（sidebar 樹狀真實層級）|
| **Status** | **done** ✅（6 test 全綠，257/257 全綠；視覺實機驗證 pet 三個問題全部解掉）|

---

## # B9. PROTOTYPE/ 內 Interactive 與 .md 鏡射要視覺區隔

| 欄位 | 內容 |
|---|---|
| **問題** | B8 把 Interactive Prototypes 移進 `📁 PROTOTYPE/` 之後，三份 .md 鏡射（Admin Moderation Prototype / Arena Battle Prototype / Pet Display Prototype）緊接在 🎮 連結後面沒有 label 分隔，視覺上像是同一組（user 反映「區別」）|
| **證據** | `b8_pet_prototype_section.png` 截圖：`INTERACTIVE PROTOTYPES` label 後直接 🎮 三筆，再直接 .md 鏡射三筆，沒有 label 隔開 |
| **對齊核心目標** | 4. 不誤會（Interactive 是「可操作的互動 prototype」， .md 鏡射是「設計規格文件」，兩者語意不同，不該看起來是同一群）|
| **預期解** | `render_prototype_subdir` 在 `📁 PROTOTYPE/` 內，先放 `INTERACTIVE PROTOTYPES` label + 🎮 連結，再放第二個 sub-label `規格文件` + .md 鏡射連結。沒有 .md 時不放 label；沒有 interactive 時不放 INTERACTIVE label。|
| **Test case** | 1. `test_B9_prototype_md_under_specs_label`：fixture 含 `pages/prototype/index.html` + `docs/prototype/sample.md` → sidebar 中 sample 連結出現在「規格文件」label 之後（不在 Interactive 之後）<br>2. `test_B9_prototype_only_interactive_no_specs_label`：只有 interactive entries 沒 .md → 不顯示「規格文件」label<br>3. `test_B9_prototype_only_md_no_interactive_label`：只有 .md 沒 interactive → 不顯示「INTERACTIVE PROTOTYPES」label，可選地顯示「規格文件」label 或不顯示（視 spec 而定）|
| **不影響其他 case** | 不動 B8 已對的 PLANTUML 整併、SERVER UML 縮排；不影響其他子目錄 |
| **驗收對應** | F |
| **Status** | **done** ✅（3 test 全綠，260/260 全綠；視覺實機驗證 prototype/ 內 Interactive 與規格文件已視覺區隔）|

---

# ════════════════════════════════════════════════
# C 群（被 B 群吸收，不需新工作）
# ════════════════════════════════════════════════

> **背景**：原 C 群 4 子題都是「EXCLUDE blueprint/contracts/bdd」方向。
> User 在 B 群會議反轉了方向 — `.md` 都要鏡射，只是不能在 root flat。
> B 群實作後，C 群 4 子題全部達成（用相反的方式：透過 subdir 鏡射）。

## 實機驗證（pet sandbox）

| C 子題 | 原描述 | 現況驗證 | Status |
|---|---|---|---|
| **C1** | blueprint/mock/X.md 不該入 pages | `pages/blueprint/mock/mock_server_guide.html` 存在於正確 subdir | **✅ done by B1+B3** |
| **C2** | contracts/*.md 不該入 pages | `pages/contracts/{api-admin,api-player,event-schema}-contract.html` 全部進 subdir | **✅ done by B1+B3** |
| **C3** | sidebar 不該顯示 blueprint/contracts/bdd 折疊群 | sidebar 顯示 `📁 BLUEPRINT/、📁 CONTRACTS/、📁 BDD/` 折疊群（user 新意願）| **✅ done by B5** |
| **C4** | CONTRACTS.md vs contracts/ 命名衝突 | `pages/contracts.html`（檔，來自 root CONTRACTS.md）與 `pages/contracts/`（目錄，含 3 個 .md html）共存無衝突 | **✅ done by B1+B2** |

## 結論

**C 群全部 done。沒有新 fix 要做。**

只需要在 issues.md 加註「resolved by B group」標記讓清單一致。

---

# ════════════════════════════════════════════════
# D 群（Prototype 曝光）
# ════════════════════════════════════════════════

## 主問題（user 視角）

> **使用者原話**：
> - 「prototype 之前提的需求，是在 pages/index.html 原來有地方露出，我請你加 link, 你現在直接整個不見了」
> - 「現在沒有 UI prototype, API explorer 的內容」

**主問題**：`pages/index.html` body 應該在明顯位置有 prototype 連結卡片（UI Prototype / Admin Prototype / API Explorer），讓 user 一眼看到並點得進去；且**重跑 gen_html 不會消失**。

**對齊核心目標**：
- **3. 表達**：index 頁是「文件中心」，prototype 是核心交付物之一，body 不應該完全沒露出
- **4. 不誤會**：sidebar 有 `📁 prototype/`，但 body 沒對應 card → user 可能誤以為「沒有互動 prototype」直到看到 sidebar

**驗收標準**：
- A. 跑 gen_html 後 `pages/index.html` body 含 `<a class="index-card" href="prototype/...">` 形式的卡片
- B. 每個 `scan_prototype_entries` 回傳的 entry 都有對應 card（UI Prototype / Admin Prototype / API Explorer）
- C. 連結點得進去（實際 HTML 存在）
- D. **重跑 gen_html N 次** card 仍存在（gen_html 本身產生它，不依賴 gen-prototype 後續注入）
- E. `pages/prototype/` 不存在時，**不**產生 prototype card（不要寫死 card；要根據 scan 結果動態產生）

---

## # D. doc_cards_section 加 prototype 卡片（採 D5-P1）

| 欄位 | 內容 |
|---|---|
| **問題** | gen_html 寫 index.html 時 body 只列文件 + UML 卡片，**不知道下游 gendoc-gen-prototype 寫過 pages/prototype/**。重跑 gen_html 會洗掉先前手動或 gen-prototype 注入的 prototype cards。|
| **證據** | gen_html.py L2620-2649 `doc_cards_section`：cards 只含 doc_pages（root .md）+ UML 一張，**無 prototype 卡片邏輯**。歷史 commit `8517c6b` 有 prototype index-cards，`548bc9c` 跑過一次 gen_html 後消失。|
| **對齊核心目標** | 3. 表達 + 4. 不誤會 |
| **預期解（D5-P1，user 已先選）** | `doc_cards_section` 主動呼叫 `scan_prototype_entries(PAGES_DIR)`，對每個 entry 輸出 index-card（icon=🎮，title=label，href=entry.href）。<br>實作位置：在現有 doc_pages 卡片與 UML 卡片之間插入。沒掃到 entry 時不出 card（不要硬寫死）。|
| **Test case** | 1. `test_D_index_has_prototype_cards_when_pages_prototype_exists`：fixture 含 `pages/prototype/index.html` → index.html 含 `<a class="index-card" href="prototype/index.html">...UI Prototype...</a>`<br>2. `test_D_no_proto_card_when_no_prototype_dir`：`pages/prototype/` 不存在 → index.html 不含任何 `prototype/*/index.html` 連結卡片<br>3. `test_D_multiple_prototype_entries_each_get_card`：fixture 含 `pages/prototype/index.html` + `pages/prototype/api-explorer/index.html` + `pages/prototype/admin/index.html` → index.html 有 3 張 prototype card<br>4. `test_D_proto_cards_survive_regen`：跑 gen_html 兩次 → 第二次 index.html 仍有 prototype cards（不消失）<br>5. `test_D_proto_cards_no_nested_a`：產出的 prototype card 不含 nested `<a><a>`（A1 regression guard）|
| **不影響其他 case** | doc_pages / UML cards 不變；index.html 其他 sections 不動 |
| **驗收對應** | A、B、C |
| **Status** | **partial** ⚠️（5 test 鎖了「卡片有出現」但**位置不對**：摻在 doc_pages 結尾不夠「明顯位置」。D2 補強位置）|

---

## # D2. Prototype cards 放成獨立 section 在 index 最前面

| 欄位 | 內容 |
|---|---|
| **問題** | D 把 prototype cards 摻進 doc_cards_section 結尾（在文件卡片之間），不符合 user 原話「**明顯位置**有 UI Prototype / API Explorer 可點擊曝光」（M1 驗收 A、B）。歷史 commit `8517c6b` 是獨立 `<div class="index-grid">` 純放 prototype 卡片|
| **證據** | `d_pet_prototype_cards.png` 截圖：3 張 prototype card 在 doc cards 第二列尾，需要 user 滾動才看到，而非「明顯位置」|
| **對齊核心目標** | 3. 表達（prototype 是核心交付物，應獨立顯眼）+ 4. 不誤會（混在文件卡片中讓 user 以為它跟 .md 文件同類）|
| **預期解** | <br>1. 抽 `prototype_cards_section()` 函式，輸出獨立 `<section>` 含 h2 標題（如「🎮 互動 Prototype」）+ 自己的 `index-grid` 含 prototype cards<br>2. `doc_cards_section` 拿掉 prototype cards 邏輯（D 階段加的那段）<br>3. `main()` 寫 index.html 時順序：README → **prototype_cards_section** → doc_cards_section → health<br>4. 沒掃到 entry 時 `prototype_cards_section()` 回 ''（空字串）不渲染 h2 |
| **Test case** | 1. `test_D2_proto_section_has_h2_header`：fixture 含 prototype → index.html 含 `<section>...<h2>...互動 Prototype...</h2>`<br>2. `test_D2_proto_cards_in_dedicated_section`：prototype cards 在獨立 section 內，而非 doc_cards_section 的「文件導覽」section<br>3. `test_D2_proto_section_before_doc_section`：prototype section 在 index.html 中**位置早於**「文件導覽」section（DOM 順序）<br>4. `test_D2_no_proto_section_when_no_prototype`：`pages/prototype/` 不存在 → index.html 不含「互動 Prototype」h2<br>5. `test_D2_doc_cards_no_longer_contain_proto`：fixture 含 prototype → 「文件導覽」section 內**沒有** `href="prototype/...`（已抽出去）|
| **不影響其他 case** | health section 不變；diagram cards 仍在 doc_cards_section |
| **驗收對應** | A、D、E（補 D 沒解的「位置」軸）|
| **Status** | **done** ✅（5 test 全綠，270/270 全綠；視覺驗證 pet body 順序：README → 🎮 互動 PROTOTYPE 獨立 section 含 3 card → 文件導覽 → 健康狀態）|

---

# ════════════════════════════════════════════════
# E 群（重複命名 / 雙版 slug）
# ════════════════════════════════════════════════

## 實查結論：E 群實際上沒有 gen_html bug

> **2026-05-09 sandbox-pet 重生後實機驗證**：current gen_html 對每個 source `.md` **只產出一個** `.html`，沒有「同一份 source 產出兩個 HTML」的 bug。

| E# | 表面現象 | 真實 source 數 | 是否 gen_html bug |
|---|---|---|---|
| **E1** | `align_report.html` ↔ `align-report.html` | **2 個**：`ALIGN_REPORT.md` + `ALIGN-REPORT.md` 兩份不同文件 | ❌ 不是 bug — pet docs 真的有兩份 source |
| **E2** | `align_fix_summary.html` ↔ `align-fix-summary.html` | 1 個 | dash 版是舊 slug 規則 stale 殘留 |
| **E3** | `align_fix_complete.html` ↔ `align-fix-complete.html` | 1 個 | 同上 |
| **E4** | `admin_impl.html` ↔ `admin-impl.html` | 1 個（`ADMIN_IMPL.md`） | 同上 |
| **E5** | `client_impl.html` ↔ `client-impl.html` | 1 個 | 同上 |
| **E6** | `local_deploy.html` ↔ `local-deploy.html` | 1 個 | 同上 |
| **E7** | `implementation_readiness.html` ↔ `implementation-readiness.html` | 1 個 | 同上 |
| **E8** | `developer_guide.html` ↔ `developer-guide.html` | 1 個 | 同上 |

## 結論

| 子題 | 對 gen_html 動作 |
|---|---|
| **E1** | 兩份 source 各自合法存在 → gen_html 各產一個 .html，**正確行為**，無 fix |
| **E2–E8** | dash 版是 stale，符合「舊的不砍」(user 在 B 群已明確) → **無 fix**，屬 H1 cleanup 範疇 |

**E 群無新 fix 要做**。如同 C 群被 B 群吸收，E 群被「實查」澄清。

只需要在 issues.md 加註標記讓清單一致。

---

## E 群拍板（2026-05-09）

> **使用者原話**：「gen_html 不用管 docs/*.md 是真的還是假的，他就是照轉，這樣才能通用，若是有問題我自己會去 rm error .md，所以可以不用改」

**Status: done** ✅
- gen_html 是通用工具，不該揣測 source 真假
- 有問題 user 自己 `rm error.md`
- E 群無 code change，純實查紀錄

---

# ════════════════════════════════════════════════
# F 群（ASCII 區塊分類器 + ASCII→Mermaid 轉換）
# ════════════════════════════════════════════════

## 主問題（user 視角）

> **使用者原話**：
> - 「pet 原是 ascii 但被強迫變 DSL，應該用 mermaid 才對」
> - 「不是 UI 的也被換了，而系統，flow, UML 的，原本 .md 是 ascii html 也要幫他變成 mermaid 才對」
> - 「top-down 方向」
> - 「白名單，不就很容易漏嗎？」（→ 改用「強系統訊號」黑名單方式）

**主問題**：UI Mock ASCII parser 太激進，把系統架構 / 流程圖 / UML 等非 UI 內容也渲染成 umock card，造成 EDD/ARCH/CICD 全被誤判。

**對齊核心目標**：
- 4. 不誤會（系統圖不該顯示成 UI 元件）
- 3. 表達（ASCII 系統圖應該以 mermaid 視覺化呈現，不是死板 `<pre>`）

---

## # F1. ASCII 分類器（系統 vs UI vs unknown）

| 欄位 | 內容 |
|---|---|
| **問題** | UI Mock parser 對任何含 `┌┐└┘├┤` 的 fence block 都無條件嘗試解析，無分類機制 |
| **預期解** | `_classify_ascii_block(text) → 'system' | 'ui' | 'unknown'`：先強系統訊號 → 系統；否則檢 UI 訊號 → UI；皆無 → unknown<br>**強系統訊號**：`↑↓►◄▲▼◀▶`（不在 `[...]` 內）/ `──>` `<──` 長 ASCII 箭頭 / 並排多框（line 含 2+ `┌`）/ in-content 樹分支（`├──`/`└──` 後接文字）<br>**強 UI 訊號**：短按鈕 `[Apply]`（1-12 chars，非 ALL_CAPS_CONST）/ 6+ 底線 `[___]` / pagination `[< 1 / N >]` |
| **Test case** | 8 個 fixture（pet 真實內容）：seq lifelines / arch parallel / cicd inline tree / text-flow / ui admin table / ui modal form / directory tree / simple box. 每個分類正確 |
| **Status** | **done** ✅ |

## # F2. ASCII → Mermaid TD 轉換器

| 欄位 | 內容 |
|---|---|
| **問題** | 系統 ASCII 之前只能 `<pre>` 顯示，難讀；user 要求自動轉 mermaid TD |
| **預期解** | `_ascii_to_mermaid_td(text) → str | None`：對 'system' kind 提取 box labels（每個 `┌─label─┐` 一個 node）+ 連線（箭頭 / 樹分支）→ 輸出 `graph TD` |
| **Test case** | arch parallel → mermaid 含 Player App / Admin Portal nodes；cicd inline → 含 ESLint / Vitest；text-flow → chain；UI fixture → return None（拒絕轉換）|
| **Status** | **done** ✅ |

## # F3. Renderer 整合 — gate UI Mock parser by classifier

| 欄位 | 內容 |
|---|---|
| **改動點** | `md_to_html` 處理 fenced code block 時：<br>1. 先試 `_ui_mock_ascii_parse` → 若 AST 第一個 child 是 'pyramid' / 'layered-arch'（特殊形狀），用既有 UI Mock parser（保留 mermaid TB / SVG 行為）<br>2. 否則跑 `_classify_ascii_block`：<br>　 - 'ui' → UI Mock parser（既有行為）<br>　 - 'system' → `_ascii_to_mermaid_td` → `<pre class="mermaid">...</pre>`<br>　 - 'unknown' → `<pre>` |
| **Test case** | `test_F1_integration_arch_block_not_rendered_as_umock`：fixture 含 ARCH parallel-box block → 跑 gen_html → arch.html 不含 `<div class="umock__page|card|modal">`<br>所有現有 ui_mock_real fixtures（M01-M10）仍正確渲染（pyramid SVG / layered-arch mermaid TB / 真 UI 變 umock）|
| **Status** | **done** ✅ |

---

## F 群實機驗證（pet sandbox）

跑 sandbox-pet 重生：

| 檔案 | 修改前 umock body 元素 | 修改後 umock body 元素 |
|---|---|---|
| arch.html | 4（誤判）| 0 ✅（變 3 張 mermaid TD）|
| edd.html | 2（誤判）| 0 ✅（變 2 張 mermaid TD）|
| cicd.html | 4（誤判）| 0 ✅（變 3 張 mermaid TD）|
| admin_impl.html | 1（誤判）| 0 ✅（變 1 張 mermaid TD）|
| frontend.html | 0 | 0（11 張 mermaid TD）|
| prototype/*.html | 8/5/2（正確 UI mock）| 8/5/2 ✅ 保留 |

10 個既有 ui_mock_real fixtures（M01-M10）全部維持原行為：M01 layered-arch 仍出 mermaid TB，M09 pyramid 仍出 SVG polygons，M02-M08/M10 真 UI 仍渲染 umock 元件。

**測試**：270 → 283（+13）全綠。

---

## F 群改動摘要

- 新增 `_classify_ascii_block(text)`：黑名單式分類，先強系統訊號（`▼` 在 `[]` 外、長箭頭、並排多框、in-content 樹分支），再 UI 訊號
- 新增 `_ascii_to_mermaid_td(text)`：best-effort 轉換（提取 box labels，輸出 `graph TD`）
- `md_to_html` 加 gate：特殊形狀（pyramid / layered-arch）走既有 parser；其他依 classifier 路由
- pet sandbox：EDD/ARCH/CICD/ADMIN_IMPL 全部脫離 umock 誤判，正確顯示為 mermaid TD

---

## B 群決策點（彙總，等 user 拍板）

| # | 議題 | 我的建議 |
|---|---|---|
| 1 | **跨層連結機制**：`os.path.relpath` vs `'../' * depth` | ✅ relpath（穩、不需手算） |
| 2 | **prototype/ 既有檔保護範圍**：只保護 `pages/prototype/`，其他 subdir 正常覆寫 | ✅（user 已明確） |
| 3 | ~~B5 diagrams 平層 vs 子分類~~ | ✅ user 已拍板：用 non-clickable label 分區（Server UML / Frontend UML 為主分區，內部再依檔名 prefix 分 Activity / Class / Sequence / State / CI/CD / 其他） |
| 4 | **Stale 不砍** | ✅（user 已明確） |

---

## B 群實作順序

依依賴關係：
1. **B1**（slug 公式）→ 是其他所有的前置
2. **B2**（mkdir parents）→ 讓 B1 的新 slug 能寫得進去
3. **B3**（writer site 改用新 slug）→ 主功能
4. **B4**（prototype/ 保護）→ 確保 B3 不破壞 gen-prototype 寫的檔
5. **B5**（sidebar 樹狀）→ user 視覺核心需求
6. **B6**（cross-link relpath）→ 讓子目錄頁 sidebar 連得回去
7. **B7**（path rewriter 升級）→ 讓文件內 `<a href="docs/X.md">` 也對

---

## 與 A 群一致的行為承諾

- 一個 fix 完才談下一個
- RED → GREEN → run all tests → commit（不 push）
- 每項 commit 後 user 確認 → 才進下一項

