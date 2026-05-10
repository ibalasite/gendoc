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
| **不影響其他 case** | R3-1 / R3-4 / R3-5 / R3-7 不動；R1（A1 已改）不動 |
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

# ════════════════════════════════════════════════
# G 群（lightbox / PUML 修正 / .md link rewriter）
# ════════════════════════════════════════════════

## 主問題（user 視角）

> **使用者重點**：
> 1. UI 線稿（DSL pyramid 等）lightbox 點下空白 — **最重要**
> 2. PUML 出圖：要兩層防護（gen-diagrams 不生壞 + gen-html 即使壞也修到能出）
> 3. 圖太大溢出可視範圍（後處理）
> 4. `.md` link 沒 rewrite 成 `.html`

## 已 done

| 編號 | 項目 | 修法 | 實機驗證 |
|---|---|---|---|
| **G-Q2** | lightbox cloned diagram 空白 | inline `<style>` 加 lightbox-scoped CSS，cloned `.diagram-container` 顯式 `width: 80vw; max-width: 1400px; min-width: 60vw`；SVG `width: 100%, height: auto` | ✅ erp/frontend 點 pyramid → 1024×472 container, 974×422 SVG, 3 polygons 全顯示 |
| **G-Q1b** | gen-html 自動修壞 PUML | 新增 `_puml_autofix(text)` 套 3 條規則：1) `par/and→else`；2) arrow `\|label\|` 移除；3) `!define NAME #HEX` 展開。`_plantuml_to_svg` 第一次 server 失敗 → autofix 後重試 | ✅ pet/edd.html 修前 2 fail/7 ok → 修後 0 fail/9 ok；4 個 .puml 檔修前 4 fail → 修後 4 ok |
| **G-Q4** | rewriter bare `.md` → `.html` | rewrite_pages_paths 加 fallback 規則：bare `X.md` / `./X.md` 結尾的 target，改 lowercase + `.html`，pages 有對應檔則改寫，否則 strip | ✅ pet 8 + erp 16 個壞 .md href 全部清零 |

**測試**：283 → 298（+15）全綠。

## 全部 done

| 編號 | 項目 | 修法 | Commit |
|---|---|---|---|
| **G-Q2** | UI Mock DSL pyramid lightbox 空白 | inline `<style>` 加 lightbox cloned diagram 顯式寬度 | `bccc935` |
| **G-Q1b** | gen-html 自動修壞 PUML（Layer 2）| `_puml_autofix` 套 3 條 rule + `_plantuml_to_svg` retry | `c5d1ebb` |
| **G-Q4** | rewriter bare `.md` → `.html` | rewrite_pages_paths 加 fallback rule | `c4edb50` |
| **G-Q5** | main.doc-content 被撐爆 | inline `<style>` 加 `min-width:0` + `pre max-width:100%` | `cdd49b7` |
| **G-Q1a** | gendoc-gen-diagrams 預防（Layer 1）| SKILL.md 加 PUML 禁區附錄（3 條 anti-pattern + 正確寫法） | `87ca90c` |

**測試**：283 → 300（+17）全綠。

**實機驗證**（sandbox-pet/erp）：
- pyramid lightbox 顯示 3 polygons（截圖 `gq2_pyramid_lightbox_fixed.png`）
- EDD.html 9 個 PUML 全 render（修前 2 fail）
- 4 個 .puml 檔全 render（修前 4 fail）
- pet 8 + erp 16 個 .md link 全清零
- main.doc-content 從 3228px → 1016px（截圖 `gq5_edd_constrained_layout.png`）

G 群結案。

---

# ════════════════════════════════════════════════
# H 群（額外發現）
# ════════════════════════════════════════════════

## 全部 done

| # | 子題 | 狀態 |
|---|---|---|
| **H1** | pet/pages 有 22 個 stale HTML | ✅ deferred — user 政策「舊的不砍」（B/E 群已確認），自己手動 rm |
| **H2** | erp/pages 也有 stale HTML | ✅ deferred — 同 H1 |
| **H3** | erp sidebar 沒 `diagrams/` 折疊群 | ✅ resolved by B5/B8 — sandbox-erp 重生後 `📁 DIAGRAMS/` 折疊群完整（截圖 `h3_erp_sidebar_diagrams_folding.png`）|

H 群無新 fix 工作。

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

---

# K 群 — workflow / 目錄樹被誤判 + lightbox 失效

> 範圍：`logic/issues.md` K 群 + 拍板後的處理規則。
> 形態 1（多欄並排）+ 形態 3（單欄垂直流）+ UML state → 改 mermaid。
> 形態 2/4/5（檔案樹/元件樹/sitemap/IA/水平分支樹）→ 留 ASCII。
> UI mock case → 改 umock HTML。
> 所有圖類（mermaid / umock / svg / puml）→ 包 `.diagram-container` 能放大。

---

## 拍板後的最終處理對照（pet 36 個 unwrapped block + 11 個既有 umock card）

| 處理 | 數量 | 涵蓋 |
|---|---:|---|
| **改 mermaid** | 14 | 純單欄流 11、cicd L347 多行框 linear、cicd L1348 1-to-2 fork、proto/arena L415 UML state |
| **變 umock UI 線圖** | 2 | proto/arena L403、proto/pet-display L344 |
| **留 ASCII** | 20 | 純樹狀（檔案樹/元件樹/sitemap/IA/水平分支樹） |
| **既有 umock card 包 wrapper** | 11 | 5 個 spec doc 內既有 UI mock，已渲為 `<div class="umock__card">` 但未包 |

---

## 處理順序（依「最快見效 + 依賴關係」）

1. **K1**（emit wrapper）— 一行 code，36 個 block 立即可放大（即使內容仍爛）
2. **K2**（F1 樹狀偵測）— 20 個樹狀回到乾淨 ASCII
3. **K3**（F2 單欄流修對）— 11 個 block 轉出正確 mermaid
4. **K4**（F2 多欄並排 fan-in）— arch L379
5. **K5**（F2 多行框 linear flow + fork）— cicd L347 + L1348
6. **K6**（F2 UML state diagram）— proto/arena L415
7. **K7**（ASCII → umock 轉換）— proto/arena L403 + proto/pet-display L344
8. **K8**（umock card 包 wrapper）— 11 個既有 UI mock 加放大能力

---

## # K1. F2 emit 加 `.diagram-container` wrapper

| 欄位 | 內容 |
|---|---|
| **問題** | F2 emit `<pre class="mermaid">` 沒包 wrapper，lightbox click handler `document.querySelectorAll('.diagram-container')` 抓不到，36 個 F2-mermaid block 全部不能放大 |
| **證據** | gen_html.py L2566-2576 直接 emit 裸 `<pre>`；arch.html `<div class="diagram-container">` 數=0、`<pre class="mermaid">` 數=3；對照組 edd.html 27/27 全包 |
| **對齊核心目標** | **1. 清楚**（複雜圖看不清）+ **3. 表達**（內容無法放大檢視） |
| **預期解** | F2 emit 改成 `<div class="diagram-container"><pre class="mermaid">{src}</pre></div>` |
| **Test case** | 1. `test_K1_f2_emit_wraps_in_diagram_container`：F2 轉換的輸出含 `<div class="diagram-container">`<br>2. `test_K1_existing_native_mermaid_unchanged`：原生 mermaid path 仍正確 |
| **不影響其他 case** | 既有 311+ test 全綠；原生 mermaid / PUML 路徑不動 |
| **驗收對應** | pet 重跑 gen-html，36 個 unwrapped → 0；隨機抽 cicd.html L347 點擊能開 lightbox |
| **Status** | **done** ✅（4 test 全綠，315/315 全綠） |

---

## # K2. F1 加嚴 — 樹狀全留 ASCII

| 欄位 | 內容 |
|---|---|
| **問題** | F1 把「任何含 `├──`/`└──` 後接文字」一律判 'system'，檔案樹/元件樹/sitemap/IA 全被誤轉 mermaid |
| **證據** | gen_html.py L1966-1972 in-content tree-branches rule 過寬；20 個樹狀 block 全被誤轉（admin_impl L422 directory、frontend L387 directory、frontend L679 React Component Tree、pdd L484 Sitemap 等） |
| **對齊核心目標** | **3. 表達**（樹狀階層被打平失去語義）+ **4. 不誤會**（讀者預期看到階層樹，看到散點 mermaid） |
| **預期解** | F1 在「tree branches → 'system'」前先檢查是否為樹狀內容：偵測「節點含檔名副檔名 `.ts/.tsx/.yaml/.html/...`」「節點以 `/` 結尾（目錄）」「節點是 `<Component>` JSX」「URL path 起頭如 `/admin/login`」→ 回傳 `'tree'`（新類別，由 dispatcher 直接 emit `<pre>`，不進 F2） |
| **Test case** | 1. `test_K2_file_tree_classified_as_tree`（assets/sprites/ + .png 檔名 → tree）<br>2. `test_K2_react_component_tree_as_tree`（含 `<App>` `<Layout>` → tree）<br>3. `test_K2_sitemap_classified_as_tree`（URL paths `/admin/login` → tree）<br>4. `test_K2_pure_flow_still_system`（單欄 `▼` 流不誤判為 tree）<br>5. `test_K2_multi_column_still_system`（同行 ≥3 個 ┌ 不誤判為 tree） |
| **不影響其他 case** | 11 個純單欄流仍判 'system'；arch L379 多欄並排仍判 'system' |
| **驗收對應** | pet 重跑 gen-html，20 個樹狀 block 渲染成 `<pre>` ASCII（保留原視覺）；admin_impl/anim/audio/cicd k8s/clinet_impl/frontend directory 等檔案樹回到乾淨等寬字體 |
| **Status** | **done** ✅（8 test 全綠，323/323 全綠） |

---

## # K3. F2 單欄流 mermaid 轉換修對

| 欄位 | 內容 |
|---|---|
| **問題** | F2 把 ▼ 當獨立 node、把 ▼ 上下的註解文字當 node、edge label 從未抽取，導致 11 個純單欄流 block 結構錯亂 |
| **證據** | cicd.html L351 `N2["▼"]`；developer_guide.html L575（11 nodes / 3 edges、預期應 11 nodes / 10 edges）；frontend L1363 Pet Claim Flow N0~N18 全變散點+▼ 散落其中 |
| **對齊核心目標** | **3. 表達**（流程方向遺失）+ **1. 清楚**（▼ 變 box 看不出箭頭） |
| **預期解** | F2 對「單欄流」型態：<br>1. ▼ / ↓ 行**不**建 node，只建 edge<br>2. ▼ 上下若有「無框」說明文字（如 `git push origin feature`），抽成 edge label `A -->\|"git push"\| B`<br>3. 每個帶內容的非 ▼/註解行才建 node |
| **Test case** | 1. `test_K3_triangle_arrow_becomes_edge_not_node`（▼ 不出現在 N0~Nn label）<br>2. `test_K3_inline_arrow_text_becomes_edge_label`（`A` `▼` `git push` `▼` `B` → `A -->\|"git push"\| B`）<br>3. `test_K3_pure_flow_no_text`（A `▼` B → 純 edge 無 label）<br>4. `test_K3_chain_three_nodes`（A `▼` B `▼` C → A→B→C） |
| **不影響其他 case** | K2 樹狀繼續走 'tree' path；K1 wrapper 不變；多欄/UML 留待 K4/K6 |
| **驗收對應** | pet 重跑 gen-html，11 個單欄流 block 結構正確、▼ 不再變獨立 node；developer_guide L575/L592 兩個 Request Lifecycle 圖完整 |
| **Status** | **done** ✅（4 test 全綠，327/327 全綠） |

---

## # K4. F2 多欄並排 fan-in（arch L379 形）

| 欄位 | 內容 |
|---|---|
| **問題** | 多欄 ASCII 架構圖（4 個 actor box 並排 → 共同匯流到 CDN/API/DB）F2 把整列當 1 個 node、`│` 留進 label |
| **證據** | arch.html L381 `N1["Guest Player│  │ Pet Owner...│  │Competitive Player...│  │Admin Operator"]`；arch.html 內 206 個殘留 `│` 字元 |
| **對齊核心目標** | **3. 表達**（並排語義消失）+ **4. 不誤會**（讀者預期 4 個 actor，看到 1 個 long-string） |
| **預期解** | F2 偵測「同一行 ≥ 2 個 ┌」→ 多欄解析器：<br>1. 用 `│` 邊界把每一行 split 為「欄位 cells」<br>2. 同一欄跨 row 的 cell（如 "Guest Player" + "(no token)"）合成一個 label（用 `<br/>` 分行）<br>3. 偵測 `▼` 行所在欄 → 從該欄 box 連到下方匯流 box<br>4. 下方單一 box → 單一 node，多上游 → 多條 edge fan-in |
| **Test case** | 1. `test_K4_split_columns_by_pipe_boundary`（`│ A │  │ B │` → 2 nodes A, B）<br>2. `test_K4_merge_multi_row_cell`（`│Guest│\n│(no token)│` → 1 node "Guest<br/>(no token)"）<br>3. `test_K4_fanin_to_downstream`（4 並排 + 4 ▼ + 1 共同下方 box → 4→1 fan-in edges）<br>4. `test_K4_pipe_not_in_node_label`（轉出 mermaid 內 N\d+\["...│..."\] 不應出現） |
| **不影響其他 case** | K2 樹狀 / K3 單欄流不受影響；多欄判定條件嚴：必須同行 ≥ 2 個 ┌ |
| **驗收對應** | pet 重跑 gen-html，arch.html L379 §1.2 System Context 渲染成 4 個 actor → CDN → API → DB 的清楚 fan-in mermaid；殘留 `│` = 0 |
| **Status** | **done** ✅（6 test 全綠，333/333 全綠） |

---

## # K5. F2 多行框 linear flow + 1-to-2 fork（cicd L347 + L1348）

| 欄位 | 內容 |
|---|---|
| **問題** | 「大框 → ▼ → 大框」型 linear flow（cicd L347 Pipeline）跟「上半 linear + 下半 fork」型（cicd L1348 GitOps）F2 把每個 box 內每行當獨立 node，box 結構消失 |
| **證據** | cicd.html L347 28 nodes（原本是 3 個大框）；cicd.html L1348 13 nodes / 0 edges（原本是 GitHub→ArgoCD→2 Application） |
| **對齊核心目標** | **3. 表達**（box 整體語義被拆散）+ **1. 清楚**（28 個小 node 看不出 3 階段流程） |
| **預期解** | F2 偵測「┌─┐...└─┘」block boundary：<br>1. 整個 box 內所有 lines 抽成 1 個 multi-line label，用 `<br/>` 連接<br>2. box 之間的 ▼ 連 edge<br>3. 偵測 box 結尾的 `└─┴─┘` 或縮排型 fork → 連到多個下游 box（fan-out）<br>4. 不在 box 內的單行 text node 仍照 K3 處理 |
| **Test case** | 1. `test_K5_box_content_joined_with_br`（`┌──┐\n│ A │\n│ B │\n│ C │\n└──┘` → 1 node "A<br/>B<br/>C"）<br>2. `test_K5_linear_chain_of_boxes`（box1 ▼ box2 ▼ box3 → 3 nodes linear chain）<br>3. `test_K5_fork_at_end`（box → 2 子 box → 2 條 edges from parent）<br>4. `test_K5_inline_tree_chars_preserved`（box 內 `├── ESLint` 字元保留進 multi-line label） |
| **不影響其他 case** | K2 純檔案樹（無 ┌─┐ 框）不受影響；K3 單欄流（無 ┌─┐ 框）不受影響 |
| **驗收對應** | pet 重跑 gen-html，cicd L347 渲染成 3 大 box linear chain（每 box 含子 list 在 label 內）；cicd L1348 上半 GitHub→ArgoCD linear、下半 ArgoCD→staging+production 1-to-2 fork |
| **Status** | **done** ✅（6 test 全綠，339/339 全綠；下半 fork 留為 single multi-line ArgoCD node，可讀，未做 inner-fork 拆分） |

---

## # K6. F2 UML state diagram 識別（proto/arena L415）

| 欄位 | 內容 |
|---|---|
| **問題** | proto/arena L415 「State Machine」是 UML 狀態機，但 F2 用 graph TD 轉，狀態之間 transition 不像狀態機箭頭 |
| **證據** | proto/arena-battle-prototype.html L415 13 nodes / 1 edge，含 `IDLE  │─────opponent────▶│` 等 ASCII state machine 標準寫法 |
| **對齊核心目標** | **3. 表達**（state machine 用錯 mermaid 形態） |
| **預期解** | F2 加 state machine 偵測：「狀態名（ALL_CAPS / TitleCase）+ `─label─▶` 或 `→ event →`」→ 用 mermaid `stateDiagram-v2` 而非 `graph TD`，每條 transition 寫成 `STATE1 --> STATE2: event` |
| **Test case** | 1. `test_K6_state_machine_uses_stateDiagram_v2`（含 `IDLE → ANIM` → 輸出 `stateDiagram-v2`）<br>2. `test_K6_transition_label_extracted`（`IDLE ─opponent─▶ LIST` → `IDLE --> LIST: opponent`）<br>3. `test_K6_initial_state_arrow`（`──▶ IDLE` → `[*] --> IDLE`） |
| **不影響其他 case** | 非狀態機 ASCII 流不誤判（無 ALL_CAPS state 名 + 無 transition label 不觸發） |
| **驗收對應** | proto/arena L415 渲染成 mermaid stateDiagram，狀態箭頭與標籤正確 |
| **Status** | **done** ✅（4 test 全綠，343/343 全綠；初始 arrow + 所有 state declared + 同行可抽 transition；多行 spanning transitions 為 best-effort，未抽出） |

---

## # K7. ASCII → umock UI 線圖轉換（proto/arena L403、proto/pet-display L344）

| 欄位 | 內容 |
|---|---|
| **問題** | proto/arena L403 「Screen 3 Post-Battle」+ proto/pet-display L344 「Screen Layout」是 UI mock（含 [Button]、🏆、`____` input、Phaser canvas 區域），被 F2 誤抓進 mermaid |
| **證據** | proto/arena-battle-prototype.html L403 7 nodes / 0 edges，labels 含 `🏆 BLAZEKIN WINS!`、`(confetti + sparkles)`、`XP Gained: +120`；pet-display L344 含 `[Play...]`、`Phaser 3 Canvas`、`160 × 160 px` |
| **對齊核心目標** | **3. 表達**（UI mock 該用 umock 渲染，當 mermaid 散點看不出畫面）+ **4. 不誤會**（讀者期待看到 UI 畫面，看到方框雲） |
| **預期解** | F1 加偵測：含「emoji（🏆 ⚡ 等）+ 數值單位（`+120`、`160 × 160 px`）+ 圓括號註解（`(confetti)`）」+ 無框/有 [Button] → 'umock'。dispatcher 對 'umock' kind 走 umock render path（既有 `_um_*` render 函式） |
| **Test case** | 1. `test_K7_ui_mock_with_emoji_classified_umock`（含 🏆、+120 → 'umock'）<br>2. `test_K7_ui_mock_with_canvas_area_classified_umock`（含 `Phaser Canvas` + 像素尺寸 → 'umock'）<br>3. `test_K7_pure_workflow_not_umock`（單欄流 + ▼ 不誤判為 umock）<br>4. `test_K7_emit_umock_html`（轉出 `<pre class="umock">` 而非 `<pre class="mermaid">`） |
| **不影響其他 case** | K3 單欄流（無 emoji 無 [Button]）不誤判；K4 多欄架構（系統元件名 + ▼）不誤判 |
| **驗收對應** | proto/arena L403、proto/pet-display L344 渲染成 umock UI 線圖（與既有 spec doc 內 UI mock 視覺一致） |
| **Status** | **done** ✅（5 test 全綠，348/348 全綠） |

---

## # K8. umock card 包 wrapper（既有 11 個 UI 線圖加放大）

| 欄位 | 內容 |
|---|---|
| **問題** | 5 個 spec doc 內既有 11 個 `<div class="umock__card">` 沒包 `.diagram-container`，無法 lightbox 放大 |
| **證據** | prototype/admin-moderation-prototype.html 0/2、prototype/arena-battle-prototype.html 0/2、pet-display 0/1、prototype__admin-moderation 0/2、prototype__arena 0/4 |
| **對齊核心目標** | **1. 清楚**（複雜 UI mock 看不清細節） |
| **預期解** | umock render 函式（`_um_*`）emit 時，最外層 wrap `<div class="diagram-container diagram-container--umock">`；K7 新增的 ASCII→umock 路徑也共用此 wrapper |
| **Test case** | 1. `test_K8_umock_card_wrapped`（umock render 輸出含 `diagram-container`）<br>2. `test_K8_lightbox_selector_matches_umock`（CSS selector `.diagram-container--umock` 不破現有 lightbox） |
| **不影響其他 case** | mermaid / PUML wrapper 仍走原 path；既有 umock render 函式內部 markup 不變 |
| **驗收對應** | pet 重跑 gen-html，5 個 spec doc 內 11 個 umock card 全部能 lightbox 放大；K7 新轉出的 2 個 umock 也能放大 |
| **Status** | **done** ✅（4 test 全綠，352/352 全綠） |

---

## # K9. `_ui_mock_ascii_parse` 渲染品質：title 重複 / 並排 box 變 input / `│` 殘留 / 無置中

| 欄位 | 內容 |
|---|---|
| **問題** | K7 把 ASCII screen mock 正確路由到 umock path、K8 包好 wrapper，但底層 `_ui_mock_ascii_parse` 把 UI mock parse 成不合理結構，內容不可讀；CSS 層也沒置中標題與按鈕 |
| **實機證據（k-group sandbox §9 K7+K8 Post-Battle 螢幕）** | source ASCII：title 置中 + Phaser anim 子框 + 統計列 + **並排兩個 button** (`Fight Again` / `Back to Pet View`)<br>渲染後 HTML 結果：`<div class="umock__card"><div class="umock__card-title">🏆 BLAZEKIN WINS!</div><div class="umock__field"><label>🏆 BLAZEKIN WINS!</label>` ← **title 重複**<br>`<input placeholder="Fight Again   │    │   Back to Pet View" readonly>` ← **2 button 變成 1 個 input field 帶 placeholder**，**`│` 殘留**<br>標題 + 按鈕渲染都 left-aligned，原 ASCII 是視覺置中 → **CSS 沒對齊原意**<br>截圖：`tools/gen_html/preview/k-group/screenshots/05-K7-ui-mock-screen-lightbox.png` |
| **對齊核心目標** | **3. 表達**（兩個按鈕被吃掉變 input、title 重複出現）+ **4. 不誤會**（讀者預期 victory screen 含 2 個置中按鈕，看到 left-aligned input field）+ **2. 美觀**（CSS 對齊不符 mock screen 慣例） |
| **5 個獨立 bug + 原始碼定位** | **K9-a 重複 title**：gen_html.py L2540-2546 把首段第一行 `🏆 BLAZEKIN WINS!` 抓為 outer card title；接著 L1488 `_um_ascii_extract_inner_boxes` 處理 Phaser anim 子框時，L1538-1543 用「上一行 non-blank」當 label，又抓到 `🏆 BLAZEKIN WINS!`，包成 `field { label="🏆 BLAZEKIN WINS!", child=box }`，導致 title 出現兩次<br><br>**K9-b 並排 box 誤合併為單 box**：L1502 偵測 inner box 用 `'┌' in line and '┐' in line and line.index('┌') < line.rindex('┐')`，這對「同一行多個並排 ┌──┐」永遠 True（因為 `index('┌')` 是第一個、`rindex('┐')` 是最後一個），把整個橫跨多 box 的範圍當一個大 box<br><br>**K9-c 兩 button 變 input**：L1517-1535 heuristic 判 box 是 input 還 code-block：multi-line 或含 `{}"[]` → code-block；否則 → input with placeholder。並排 button 是單行（合併後）、無特殊符號 → input。但**正解是 actions group with 2 buttons**<br><br>**K9-d `│` 殘留**：L1513 `_um_ascii_strip_pipes(segment_lines[k])` 只剝外側 `│`，並排 box 中間的 `│    │` 是「box A 右邊界 + box B 左邊界」，留在 line 中央未被剝；joined 後進 placeholder<br><br>**K9-e CSS 不置中**：L308 `.umock__card-title` 預設 left-aligned；L310 `.umock__page-title` 同；L348 `.umock__actions { text-align: right }` ← actions 是右對齊，**不是置中**。Mock screen 慣例上 title + actions 都應置中 |
| **預期解** | **5 個獨立 fix（按行號順序）**：<br><br>**Fix K9-b（最關鍵，先做）**：`_um_ascii_extract_inner_boxes` L1500-1568 加「同行多 ┌」偵測：<br>- 若 line.count('┌') ≥ 2 → 不視為單一 box，**而是「並排 box 行」**<br>- 對並排 box 行，用 `┌` 位置 split 出每個 box 的 [start,end] col range<br>- 對應 last bottom line 也應有同數量 `└`<br>- 中間 row 用 col range 切出每 box 的 cell 內容<br>- 若每 box 內只 1 行短文字（≤ 16 chars，無 `=`，非 ALL_CAPS）→ 視為 button list → 產出 `actions { button×N }` AST 而非 input<br>- 否則 → 多個獨立 box（原邏輯，每個各自 input/code-block）<br><br>**Fix K9-d（K9-b 副作用消除）**：因 K9-b 改後並排 box 各自獨立 parse，`│` 不再進 placeholder（自動修復）<br><br>**Fix K9-c**：K9-b actions 路徑直接產 button AST，不走 input heuristic（無需獨立 fix）<br><br>**Fix K9-a 重複 title**：`_um_ascii_extract_inner_boxes` L1538-1543 找 label line 前，加「跳過已被當 outer card-title 的行」邏輯：<br>- 從 caller 帶入 `taken_title_text` 參數<br>- 找 label 時若 `segment_lines[k].strip() == taken_title_text` 則跳過該行<br>- caller (`_ui_mock_ascii_parse` L2548) 傳入 outer title<br><br>**Fix K9-e CSS 置中**：gen_html.py 內聯 `<style>` 改 3 條 rule：<br>- L308 `.umock__card-title` 加 `text-align: center;`<br>- L310 `.umock__page-title` 加 `text-align: center;`<br>- L348 `.umock__actions { text-align: right }` 改為 `text-align: center;`（並排 button 在 mock screen 上慣例置中；form footer actions 仍可由具名 modifier 如 `umock__actions--right` 後續細分，但本 K9 不動）<br>不動：`.umock__modal-titlebar`（已 flex justify-between）、`.umock__table`（資料表用左對齊正確） |
| **Test case（含 edge）** | 1. `test_K9_parallel_buttons_become_actions_not_input`<br>   輸入：兩並排 box 含短文字 → AST 含 `{type:'actions', children:[button×2]}`，無 `input` node<br>2. `test_K9_no_pipe_in_input_placeholder`<br>   輸入：上述並排 button → 整個 segment 內無 placeholder 含 `│`<br>3. `test_K9_title_not_duplicated_in_field_label`<br>   輸入：含 title + 子框，子框前一行 = title 文字 → AST 中 title 只出現 1 次（card-title），不出現在 field label<br>4. `test_K9_md_to_html_post_battle_screen`<br>   整合：fixture 同 k-group §9 → 輸出 HTML 含 `umock__actions` + 2 個 `umock__btn`，**不含** `umock__input`，**不含** `placeholder.*│`<br>5. `test_K9_single_inner_box_unchanged`（regression）<br>   輸入：單一個內框（K7 一般 case）→ 仍正確 parse 為 input/code-block + field label<br>6. `test_K9e_card_title_centered_in_css`<br>   輸出 HTML `<style>` 包含 `.umock__card-title { ... text-align: center ... }`<br>7. `test_K9e_page_title_centered_in_css`<br>   `.umock__page-title` 含 `text-align: center`<br>8. `test_K9e_actions_centered_in_css`<br>   `.umock__actions` 含 `text-align: center`（不再是 `right`） |
| **不影響其他 case** | 既有 9 個 ui_mock_* test 檔（pyramid / layered-arch / columns / inner / dsl_parser / dsl_render / 等共 ~150 test）全綠（已實查：無 test assert text-align 屬性，CSS 改動安全） |
| **驗收對應** | k-group sandbox 重跑：<br>- §9 K7+K8 lightbox 內顯示 2 個**置中**並排 button（不是 input field）<br>- title 不重複（card-title 只出現 1 次）+ **置中**顯示<br>- 整個 umock HTML 內無 `│` 字元殘留<br>- §10 DSL fence Login Page title 也置中<br>- 3 張截圖一致對比：`K9-1-md-source.png`（原 ASCII）/ `K9-2-html-inline.png`（HTML inline）/ `K9-3-lightbox.png`（lightbox），結構元素一致：title→Phaser anim 框→stats→2 並排按鈕 |
| **Status** | **done** ✅（9 test 全綠 + 3 驗證截圖；361/361 整體全綠） |

---

## K 群決策點（彙總，等 user 拍板）

| # | 議題 | 我的建議 |
|---|---|---|
| 1 | **K1 wrapper 加上後 36 個 block 雖能放大但內容仍爛** — 是否同意先合 K1 commit、後續 K2~K8 漸進改善？ | ✅（K1 是最安全、最快見效，不依賴其他 step） |
| 2 | **K2 新增 'tree' kind 還是直接 'unknown'？** | 用 'tree' 明確（dispatcher 顯式判斷，未來想加 tree-specific 渲染（如行號）有 hook） |
| 3 | **K5 多行框 box 內 `├──` 視覺裝飾** 保留進 mermaid label 還是清乾淨？ | 保留（讀者已習慣這個視覺，user 也說「裡面有文字」可保留樹狀字元） |
| 4 | **K7 umock 偵測** 邊界（emoji + 像素尺寸 vs 純流程）— 邊界判錯會把 system 圖誤分為 UI | 偵測門檻設高（至少 2 個 UI 訊號才觸發；單一訊號不夠） |
| 5 | **K6 stateDiagram 觸發條件** | 嚴格只在偵測到「ALL_CAPS 狀態名 + transition arrow + label」三條件齊備才觸發 |

---

## K 群實作順序與依賴

```
K1 (wrapper) ─────────────┐
                          │
K2 (F1 樹狀偵測) ─┐       │
                  ↓       ↓
K3 (F2 單欄流) ─→ 進 K4   │
                  │       │
K4 (F2 多欄) ──── ┤       │  最後驗收：
                  │       │  pet 重跑 gen-html，
K5 (F2 多行框) ── ┤       ├→ 36 個 block 全部能放大
                  │       │  + 內容對 14 個 mermaid
K6 (F2 UML state) ┤       │  + 留 ASCII 20 個
                  │       │  + 變 umock 2 個
K7 (ASCII→umock) ─┘       │  + 11 個既有 umock card 能放大
                          │
K8 (umock wrapper) ───────┘
```

依賴：
- K1 獨立、優先做（最安全、最快見效）
- K2 獨立（不影響 K3+ 純流的判斷）
- K3, K4, K5, K6, K7 五個解析器互不依賴，可平行討論但循序 commit
- K8 獨立（純 wrapper 補加，跟 K1 同性質但對 umock）

---

## K 群與 A/B 群一致的行為承諾

- 一個 step commit 完才談下一個
- RED → GREEN → run all tests → commit（不 push）
- 每項 commit 後 user 確認 → 才進下一項
- 每個 step 的 commit 訊息：`fix(gen-html): K<N> ...`

---

# L 群 — subdir HTML 的 `<head>` CSS / nav-brand / breadcrumb 路徑全壞

> 範圍：`logic/issues.md` L 群。50 個位於 subdir 的 HTML（`pages/diagrams/*.html` `pages/contracts/*.html` `pages/blueprint/mock/*.html` `pages/req/*.html` `pages/prototype/*.html`）的 `<head>` 引用 CSS 路徑相對於 pages/ 根，但檔案在 subdir 內，瀏覽器找不到 → **打開沒任何 style**。

---

## 問題範圍實機統計（pet/docs/pages，read-only inspection）

| 路徑類型 | broken / total subdir HTMLs |
|---|---|
| `<link rel="stylesheet" href="assets/style.css">` | 50 / 57 |
| `<a href="index.html" class="nav-brand">pet</a>` | 50 / 57 |
| `<p class="banner-breadcrumb"><a href="index.html">pet</a> ...` | 50 / 57 |

對照：sidebar `<a class="sidebar__link" href="../idea.html">` ✅ 全部正確帶 `../` prefix（B6 `make_sidebar` 已做 depth-aware 處理）。

---

## L 群處理順序（整併為 1 個 step）

依拍板的 3 個決策：
- ✅ K-group sandbox 加 subdir 案例驗證
- ✅ R3-7 檢查目標檔存在才 prepend `../`
- ✅ root pages/ 不處理（depth=0），只 subdir 加 prefix

整併為 1 個 step：**L1 = R3-7 通用規則 + sandbox subdir 案例 + 3 視角驗證**。

---

## # L1. R3-7 通用規則：root-level 路徑在 subdir 中 prepend `../`

| 欄位 | 內容 |
|---|---|
| **問題** | `rewrite_pages_paths` 只處理 5 種特定 transform（R3-1~R3-5），**沒有 generic「subdir 內 root-level 路徑要 prepend `../`」規則**。導致 50/57 個 subdir HTMLs 的 3 類路徑全壞：<br>(a) `<head><link href="assets/style.css">` → subdir 找不到 CSS → 整頁無樣式<br>(b) `<a class="nav-brand" href="index.html">pet</a>` → 點下去 404 / 落到子目錄 index<br>(c) `<a href="index.html">pet</a>` (breadcrumb) → 同 (b) |
| **實機證據（pet 50/57）** | `<link href="assets/style.css">`：50/57<br>`nav-brand href="index.html"`：50/57<br>`breadcrumb href="index.html">pet</a>`：50/57<br>檔案：`pages/diagrams/*.html` (42)、`pages/contracts/*.html` (3)、`pages/blueprint/mock/*.html` (1)、`pages/req/*.html` (1)、`pages/prototype/*spec.html` (3)<br>對照組（已對的）：sidebar `<a class="sidebar__link" href="../idea.html">` 50/50 全對（`make_sidebar` L3460-3464 depth-aware 處理） |
| **gen_html.py 行號** | head template L221（寫死）<br>header template L424（寫死）<br>banner-breadcrumb 生成處（用 `__APP__` 嵌 `<a href="index.html">`）<br>L2817 `rewrite_pages_paths` regex L2929 涵蓋所有 href/src 但 callback L2867-2920 只 5 種規則<br>L3460-3464 `make_sidebar.link()` 已用 `'../' * current_depth` 做 depth-aware，可參考 |
| **對齊核心目標** | **3. 表達**（整頁無 CSS 無法讀）+ **4. 不誤會**（nav-brand 點下去 404 / 落到錯地方）|
| **預期解** | `_href_rewrite` 加 R3-7 通用規則：<br>1. 計算 `depth = len(rel_dir.parts)`（current page 距 pages/ 根的深度，root = 0）<br>2. 若 `depth == 0` → 不處理（root page 路徑本來就對）<br>3. target 是外部 URL / anchor / mailto / data: / javascript: / 已 `../` 前綴 / `/` 絕對路徑 → 跳過<br>4. R3-1~R3-5 已 cover 的 case → 走原邏輯，最後再 wrap `'../' * depth +` 結果<br>5. 通用 fallback：若 `(pages_dir / target).exists()`（target 對應 pages/ 根級檔／資料夾），且 depth > 0 → return `'../' * depth + target`<br>6. 否則 → 不處理（保守）|
| **Test case（含 edge）** | 1. `test_L1_subdir_head_css_gets_dotdot_prefix`<br>   `<link href="assets/style.css">` 在 `pages/diagrams/X.html` 中 → 變成 `href="../assets/style.css"`<br>2. `test_L1_subdir_navbrand_index_gets_prefix`<br>   `<a href="index.html" class="nav-brand">` 在 `pages/diagrams/X.html` → `href="../index.html"`<br>3. `test_L1_subdir_breadcrumb_gets_prefix`<br>   `<a href="index.html">pet</a>` 在 banner-breadcrumb 內 → `href="../index.html"`<br>4. `test_L1_two_level_deep_gets_double_dotdot`<br>   `pages/blueprint/mock/X.html` （depth=2）→ `href="../../assets/style.css"`<br>5. `test_L1_root_page_unchanged`<br>   `pages/index.html` (depth=0) → `href="assets/style.css"`（不動）<br>6. `test_L1_already_prefixed_unchanged`<br>   `<a href="../assets/style.css">` 已對 → 不重複加 prefix<br>7. `test_L1_external_url_unchanged`<br>   `<a href="https://example.com">`、`<a href="#section">`、`<a href="mailto:x@y">` → 不動<br>8. `test_L1_target_not_in_pages_unchanged`<br>   `<a href="nonexistent.html">` （pages/ 根級沒這檔）→ 不動（保守）<br>9. `test_L1_existing_R3_rules_still_work`（regression）<br>   R3-1~R3-5 既有 transform 不受影響 |
| **不影響其他 case** | 27 個既有 path_rewriter test 全綠；sidebar `__link` 已 pre-prefixed，rewriter 看到 `../` 開頭會跳過（rule 3）|
| **驗收對應（3 視角 + screenshot）** | 1. sandbox 案例：`tools/gen_html/preview/k-group/docs/diagrams/sample-diag.md` (depth=1)<br>2. inspect HTML: `<head><link href="../assets/style.css">`、nav-brand `href="../index.html"`、breadcrumb `href="../index.html">k-group</a>`、sidebar `__link href="../X">` 全帶 `../`<br>3. **screenshot L1-1**: 樣式正常顯示（top nav / banner / sidebar / 內容全部 styled）<br>4. **screenshot L1-2**: 點 nav-brand 跳到 root index.html（k-group 文件中心首頁）<br>5. evaluate 驗證 `nav-brand.href == http://.../index.html`、`breadcrumb a.href == http://.../index.html`（root） |
| **Status** | **done** ✅（9 test 全綠，370/370 全綠，subdir 樣式驗收通過） |

---

# M 群 — prototype 回 docs link 失效

> 範圍：`logic/issues.md` M 群。prototype 目錄下的 HTML 沒有正確回 docs 首頁的 link，使用者一旦進去就「迷路」。

---

## 雙層保護模型（user 拍板）

| 層 | 角色 | 內容 |
|---|---|---|
| **docs 端**（gen-html） | 入口 | 所有 docs → prototype 連結用 `target="prototype-window"` named tab；docs 主 tab 永遠保留 |
| **prototype 端**（gen-prototype） | 出口 | 每個 prototype HTML 模板自身要有「← 文件站」link 回 docs 首頁；review subagent 必驗 |

兩層獨立、不重複、不互相依賴。

---

## 子題狀態表

| # | 子題 | 修法位置 | Status |
|---|---|---|---|
| M1 spec docs breadcrumb | gen-html R3-7 | ✅ done by L1 |
| **M2** prototype shell 加 `← 文件站` | SKILL.md Step G-7 模板 (L572-576 nav 區) | review |
| **M3** admin/*.html 加 `← 文件站` | SKILL.md Step A-4 模板 (L987 起每頁 nav) | review |
| **M4** api-explorer 修 label/href + 加 `← 文件站` | SKILL.md Step G-2 模板 (L694) | review |
| M5 B4 保護 | （不動）| ✅ done by design |
| ~~M6~~ gen-html fallback floating button | **撤銷**（M2/M3/M4 修對就不缺）| 取消 |
| **M7** gen-prototype review subagent 驗 | SKILL.md review 階段加 checklist | review |
| **M8** docs 端 prototype link 加 named target | gen_html.py 3 處（make_sidebar / doc_cards_section / rewrite_pages_paths） | review |

---

## 修法分 2 commits

### Commit 1：M2/M3/M4/M7 — gen-prototype side

**修 `skills/gendoc-gen-prototype/SKILL.md`**：
1. **M2** Step G-7 prototype shell 模板 (L572-576 nav 區) — 加 `<a href="../index.html" class="proto-back-docs">← 文件站</a>`
2. **M3** Step A-4 admin 5 頁模板 (L987+) — top nav 加 `<a href="../../index.html">← 文件站</a>`（depth=2）
3. **M4** Step G-2 api-explorer 模板 (L694) — 修 label/href 不對應，改成 `<a href="../../index.html">← 文件站</a>`（label 跟 href 都對）
4. **M7** review/fix loop 階段加 checklist：「每個 prototype HTML 必須含可解析到 docs index 的 back link」

**Python tests**（grep SKILL.md 驗模板字串）：
- `test_M2_prototype_shell_template_has_docs_link`
- `test_M3_admin_template_has_docs_link`
- `test_M4_api_explorer_template_has_docs_link`
- `test_M7_review_subagent_checks_docs_link`

### Commit 2：M8 — gen-html side

**修 `tools/gen_html/gen_html.py`**：
1. `make_sidebar` 內 prototype 3 個 entry（UI Prototype / Admin / API Explorer）加 `target="prototype-window"`
2. `doc_cards_section`（pages/index.html）內 prototype 卡片加 target
3. `rewrite_pages_paths` 對 `<a href="prototype/...">` 自動補 target

**Python tests**：
- `test_M8_sidebar_prototype_link_has_target`
- `test_M8_cards_prototype_link_has_target`
- `test_M8_rewriter_adds_target_for_prototype_link`
- `test_M8_non_prototype_link_no_target`（regression）

**Sandbox 驗收**（k-group sandbox）：
- 加 mock prototype shell HTML（佯造，含 `← 文件站` 假 link）
- 加 docs page 含 link 指向 prototype
- Playwright：點 docs sidebar prototype entry → 開新 tab；點別的 prototype entry → 同 tab 切換；切回 docs tab → docs 還原位
- 截圖 M8-1 / M8-2

---

---

## L 群驗收（3 視角對照同 K 群慣例）

需建 sandbox case：
- 一個 markdown 在 subdir 例：`docs/diagrams/sample.md` 或 `docs/contracts/sample.md`
- 跑 gen_html 後驗證：
  1. **inspect HTML**: `<head><link href>`、nav-brand、breadcrumb 都帶 `../`
  2. **screenshot subdir page (HTML inline)**: 樣式正常顯示
  3. **screenshot 從 subdir 點 nav-brand**: 跳到 `pages/index.html`（首頁）
  4. **screenshot 從 subdir 點 breadcrumb pet**: 同上跳到首頁

---

## L 群決策點（等 user 拍板）

| # | 議題 | 我的建議 |
|---|---|---|
| 1 | **L 群 fix 後 K group sandbox 內無 subdir 案例可驗證** — 是否要新增 sandbox 加一個 subdir HTML？ | ✅ 加（K group sandbox 已存在 fixtures，新增 1-2 個 subdir docs 即可） |
| 2 | **R3-7 是否該檢查 `(pages_dir / target)` 真實存在** 才 prepend `../`？ | ✅（避免誤判：例如 `bare-string` 不是檔案路徑卻被誤加 `../`）|
| 3 | **`href="index.html"` 在 root pages/ 不需處理（self-reference）；只在 subdir 才需 `../`** | ✅（rewrite 用 `current_html_path` 計算 depth，root 時 depth=0 → 不加） |

---

# N 群 — 每頁 TOC（Table of Contents）標配

> **新需求**（user 加）：「不是每一個 HTML 有 table of contents，對於這個我想 gen-html 要把每一個 html 都有這個標配」。

---

## 實機現況（2026-05-10 read-only inspection）

| 指標 | 數值 |
|---|---|
| pet/docs/pages 中 top-level HTML 總數 | 110 |
| 含 "Table of Contents" 字串的 HTML | **7** |
| 主要文件 edd/schema/arch/prd/brd/pdd/vdd 含 TOC | **0** ❌ |
| edd.html (2354 行) heading 結構 | H2=24, H3=76, H4=53 |
| schema.html (2281 行) heading 結構 | H2=22, H3=73, H4=2 |
| arch.html (1428 行) heading 結構 | H2=22, H3=49, H4=0 |
| `gen_html.py` 中 TOC 生成邏輯 | **0 個函式** |
| heading id 屬性（J 群已加，anchor 跳轉前提） | edd.html 154 個 heading 全帶 id ✓ |

**意涵**：使用者打開 edd / schema / arch 等 1500-2400 行的大文件，沒有導覽，只能全頁滑。

---

## 7 個既有含 TOC 的檔案分析

來源都是 source markdown 手寫的：
```
api.html, cicd.html, developer-guide.html, developer_guide.html,
index.html, runbook.html, test-plan.html
```

`cicd.html` L342-343 範例（manual TOC pattern）：
```html
<h2 id="table-of-contents">Table of Contents</h2>
<ol>
  <li><a href="#pipeline-overview">Pipeline Overview</a></li>
  <li><a href="#github-actions-workflows">GitHub Actions Workflows</a></li>
  ...
</ol>
```

純 markdown list，無 sticky、無 scroll-spy、無 indent 階層。

---

## 設計目標（提案 + 待 user 拍板）

要 gen-html 自動生成 TOC，需決定 5 件事：

### 1. TOC 渲染位置（4 選項）

| 選項 | 說明 | 視覺 | RWD |
|---|---|---|---|
| **A. main 頂部 inline** | TOC 寫在 main 開頭（替代 source 寫的 `## Table of Contents`） | 跟 cicd.html 既有 7 個一致 | 簡單，窄屏不受影響 |
| **B. 右側 sticky** | 三欄 layout：左 sidebar + 中 main + 右 sticky TOC | 跟 Stripe / Material UI / Tailwind docs 一致 | 需 RWD（窄屏改回頂部）|
| **C. left sidebar 內折疊** | 在 docs sidebar 底部折疊 `<details><summary>本頁目錄</summary>` | 跟 sidebar 整合，無新欄 | 簡單 |
| **D. floating drawer** | 右下浮動按鈕 → 點開 drawer 顯示 TOC | 不佔版面 | RWD 容易 |

**我的推薦：B（右側 sticky）**。理由：
- 現代 docs site 標準做法（user 期待）
- 大文件（edd 2354 行）需要常態可見 TOC 隨捲動定位
- scroll-spy 可高亮當前 section，user 知道讀到哪
- 窄屏（< 1024px）回退到 A（main 頂部 inline）

### 2. TOC 展開深度（3 選項）

| 選項 | 說明 | edd 例 |
|---|---|---|
| 只 H2 | 22 條 link | 短而簡 |
| H2+H3 | 22+76=98 條 link | 中等 |
| H2+H3+H4 | 22+76+53=151 條 link | 詳細，可能擠 |

**我的推薦：H2+H3**（98 條對 sticky panel 高度合理；H4 太細放折疊）。

### 3. Scroll-spy（隨頁面捲動高亮當前 section）

**我的推薦：✅ 加**。輕量 JS（IntersectionObserver），無需 framework。

### 4. 短文件不顯示（避免 1-2 個 H2 也擺 TOC）

**我的推薦**：H2 數 ≥ 3 才渲染。

### 5. 既有 source 寫的 TOC 怎麼辦

7 個檔內 markdown 已寫 `## Table of Contents` + manual list。auto-TOC 跟 manual TOC 共存會重複。

**我的推薦**：自動偵測 source 含 manual TOC（H2 = "Table of Contents"）→ **跳過 auto-TOC**（尊重作者）。

---

## 修法切片

**單一 commit**（根目標：每頁 TOC 標配）：

| 變更 | 位置 | 動作 |
|---|---|---|
| 加 TOC 生成器 | `gen_html.py` 加 `_build_toc(html)` 函式 — 掃 H2/H3 帶 `id` 的 heading，產出 `<nav class="page-toc">` HTML |
| 加 layout 三欄 | head template L443 `<main class="doc-content">` 改成 `<main class="doc-content"> + <aside class="page-toc-aside" />` |
| 加 CSS | inline `<style>` 內加 `.page-toc-aside`（sticky right）+ `.page-toc__link.active`（scroll-spy 高亮）+ RWD 媒體查詢 |
| 加 scroll-spy JS | `assets/app.js` 加 IntersectionObserver bind H2/H3 → 切 active class |
| 偵測 manual TOC | `_build_toc` 看到 source 已有 H2 "Table of Contents" → return 空（不重複生成） |
| 短文件 skip | H2 數 < 3 → return 空 |

---

## Test case（含 edge）

1. `test_N1_long_doc_gets_auto_toc`<br>
   含 ≥ 3 個 H2 的 markdown → 渲染後含 `<nav class="page-toc">`
2. `test_N1_short_doc_no_toc`<br>
   只 1-2 個 H2 → 不含 page-toc
3. `test_N1_h2_h3_in_toc_h4_skipped`<br>
   含 H2/H3/H4 → page-toc 含 H2 + H3 anchor，無 H4
4. `test_N1_manual_toc_skipped`<br>
   source markdown 已寫 `## Table of Contents` → auto-TOC return 空（regression for cicd / developer-guide / api 等 7 檔）
5. `test_N1_toc_anchors_match_heading_ids`<br>
   page-toc 內 `<a href="#X">` 必須對應到 main 內某個 `<h2 id="X">` 或 `<h3 id="X">`
6. `test_N1_subdir_page_toc_works`<br>
   subdir HTML（如 pages/diagrams/X.html）也有 page-toc（不被 L1 R3-7 路徑誤動）
7. `test_N1_scroll_spy_css_active_class_exists`<br>
   `<style>` 含 `.page-toc__link.active` rule
8. `test_N1_rwd_narrow_screen_falls_back`<br>
   `<style>` 含 `@media (max-width: ...)` 對 .page-toc-aside 的處理（如改 inline）

---

## 驗收（3 視角 + screenshot）

加 sandbox 案例（K-group sandbox 已有 K-FIXTURE 含多 H2/H3，可重用）：
1. **inspect HTML**: K-FIXTURE.html 含 `<nav class="page-toc">` 含 ≥ 11 個 H2 anchor
2. **screenshot N1-1**: docs page 預設視窗（≥ 1024px）顯示左 sidebar + 中 main + 右 sticky TOC 三欄
3. **screenshot N1-2**: 點 TOC 任一條 link → main 滾到對應 section（用 J 群 anchor 跳轉）
4. **screenshot N1-3**: scroll page 後 TOC 高亮當前 section（scroll-spy）
5. **screenshot N1-4**: 窄視窗（< 1024px）TOC 改顯示在 main 頂部 inline

---

## 7 個決策點（user 已拍板）

| # | 議題 | 拍板 |
|---|---|---|
| 1 | 預設 tab active | **文件 tab** |
| 2 | 預設 sidebar 展開狀態 | **展開** |
| 3 | 收合狀態跨頁記憶 | **localStorage 記憶**（key: `gendoc:sidebar-collapsed`）|
| 4 | TOC 展開深度 | **H2 + H3**（H4 不放）|
| 5 | Scroll-spy 高亮 | **加**（IntersectionObserver）|
| 6 | 短文件 + RWD | **永遠渲染** TOC + 手機 RWD 自動收合 |
| 7 | source manual TOC 共存 | **不破壞**（main 內 manual TOC 保留）+ **sidebar TOC tab 永遠存在**（位置不衝突，不重複）|

---

## 設計（採 demo-v4：左 sidebar 兩 tab + 收合）

```
預設展開 (1440 viewport)：
┌──────────┬─────────────────────────┐
│ ⇤ tab    │                         │
│ [📁 文件] │                         │
│ [📑 目錄] │     MAIN (1100px)       │
│ panel    │                         │
│ (240px)  │                         │
└──────────┴─────────────────────────┘

收合後：
┌──┬─────────────────────────────────┐
│⇥ │     MAIN (1340px) — 拉到最大     │
└──┴─────────────────────────────────┘

手機 (375)：
sidebar default collapsed (32px)，user 點 ⇥ 展開（覆蓋 main）
```

---

## 修法切片（單一 commit）

| 變更 | 位置 |
|---|---|
| 加 `_build_toc(html)` 函式 | `gen_html.py` — 掃 `<h2 id>` `<h3 id>` 產出 anchor list |
| 改 sidebar layout | `make_sidebar` 包進 tabs + panels + toggle button |
| 加 CSS | inline `<style>` 加 tab bar / panel / collapsed / scroll-spy / RWD 媒體查詢 |
| 加 JS | `assets/app.js` 加 tab toggle + sidebar collapse + localStorage + IntersectionObserver scroll-spy |

---

## Test case (11 個)

1. `test_N1_sidebar_has_two_tabs` — `<button data-tab="docs">` + `<button data-tab="toc">`
2. `test_N1_doc_list_in_docs_panel` — 原 sidebar 連結進 `<div data-panel="docs">`
3. `test_N1_toc_panel_has_h2_h3_anchors` — toc panel 含對應 anchor links
4. `test_N1_h4_not_in_toc` — H4 不出現
5. `test_N1_toc_panel_always_rendered` — 即使 0 H2 也有 panel（顯示空 list 或提示）
6. `test_N1_manual_toc_in_main_preserved` — source 內 manual TOC 保留
7. `test_N1_active_tab_default_docs` — docs tab 帶 active
8. `test_N1_collapse_toggle_button_exists` — sidebar 含 `<button class="sidebar__toggle">`
9. `test_N1_localstorage_key_in_js` — `app.js` 含 `gendoc:sidebar-collapsed`
10. `test_N1_scrollspy_intersection_observer_in_js` — `app.js` 含 `IntersectionObserver` + active 切換
11. `test_N1_rwd_mobile_collapse_css` — `<style>` 含 `@media (max-width: 768px)` 對 sidebar 的 default-collapse rule

---

## 驗收（4 張截圖）

跑 k-group sandbox `K-FIXTURE.md`（含 11 H2）：
- **N1-final-1-docs-tab.png** (1440)：預設展開 + 文件 tab active
- **N1-final-2-toc-tab.png** (1440)：點 toc tab → 11 H2 + 子 H3 anchor 列出
- **N1-final-3-collapsed.png** (1440)：點 ⇤ → sidebar 32px，main 1340px
- **N1-final-4-mobile-rwd.png** (375 viewport)：手機 sidebar 預設收合
