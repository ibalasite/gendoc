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
| **Status** | **todo** |

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
| **Status** | **todo** |

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
| **Status** | **todo** |

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
