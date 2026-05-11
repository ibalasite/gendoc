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

## A. HTML 渲染瑕疵  ✅ DONE

### ~~A1.~~ erp/index.html 出現 nested `<a><a>` 巢狀標籤  ✅ DONE

- **原**：`gen_html.py` `_code_to_link` 不檢查 `<code>` 是否已在 `<a>` 內 → 產生 invalid `<a><a>`。
- **修法**：`_code_to_link` 加守衛跳過 `<code>` 已在 `<a>` 內的 case（gen_html.py L3034 + L3060）。
- **驗收**：pet/index.html 0 處 nested、erp/index.html 0 處 nested。

### ~~A2.~~ sidenav items 顯示前綴 `│` 殘留  ✅ DONE

- **原**：`_um_ascii_strip_pipes` 對單一 `│` line（first == last）直接 return 不剝。
- **修法**：UI Mock parser stage 5-8 重構期間順帶修對。
- **驗收**：pet 9 個 sidenav / 0 殘留；erp 65 個 .html sidenav / 0 殘留。

### ~~A3.~~ card / page / modal 邊界線淡  ✅ DONE

- **原**：CSS `border: 1px solid #cbd5e1`（淺灰）+ header / body 分隔線同色，整個區塊邊界跟內部分隔糊在一起。
- **修法**：
  - card / page / modal 外框 → `1.5px solid #94a3b8`（K9 期間順帶改）
  - card-title / page-title / modal-titlebar 底線 → `1.5px solid #94a3b8`（K9 期間順帶改）
  - **input / search border → `1px solid #94a3b8`**（commit `b1dbde5`）
- **驗收**：8/8 test PASS（`test_a_group_visuals.py` A3 區段）。
- **demo**：`tools/gen_html/preview/a-group-demo/A3-card-borders.png`。

### ~~A4.~~ table 看起來小、列分隔線淡  ✅ DONE

- **原**：CSS `padding 0.5rem 0.625rem`（緊）+ `border-bottom 1px solid #e2e8f0`（極淡）→ 列擠在一起。
- **修法**：
  - cell padding → `0.75rem 0.875rem`（行間距 +50%；K9 期間順帶改）
  - 行分隔線 → `1px solid #cbd5e1`（深一階；K9 期間順帶改）
  - **新增 `tbody tr:hover { background: #f8fafc }` 行高亮**（commit `6cae549`）
- **驗收**：4/4 test PASS（`test_a_group_visuals.py` A4 區段）。
- **demo**：`tools/gen_html/preview/a-group-demo/A4-tables.png`。

### ~~A5.~~ mock 元件 focus 時讓讀者誤會語義（P4 拍板）  ✅ DONE

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

## B. 目錄結構違反 source 1:1 mirror  ✅ DONE

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

## D. Prototype 曝光降級  ✅ DONE BY M 群

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

## G. doc_cards_section（首頁卡片格）  ✅ DONE（G2 用 prototype_cards_section 另起 section）

### ~~G1~~

- **撤回**（誤判）。CICD/Developer Guide/Implementation Readiness/Manifest/Resource/background-jobs 都是合法 root `.md` 文件。

### G2. doc_cards_section 不含 prototype 卡片

- **事實**：函式內無 `prototype`、無 `scan_prototype` 引用。
- **證據**：grep 結果 `'prototype' in body.lower() = False`。

---

## H. 額外發現  ✅ **全部 RESOLVED 或 DEFERRED**

### ~~H1.~~ pet/pages 有 22 個 stale HTML 檔  ✅ deferred (user 政策「舊的不砍」)

- **原**：來源 `.md` 已不存在，但 HTML 仍留存（22 個）
- **user 政策**（B/E 群已確認）：「gen_html 不用管 docs/*.md 是真的還是假的，他就是照轉，這樣才能通用，若是有問題我自己會去 rm error .md」
- 結論：**無 fix 工作**；user 自行手動 rm 即可

### ~~H2.~~ erp/pages 也有 stale HTML  ✅ deferred (同 H1)

- **原**：erp 71 個 HTML，部分為歷史殘留
- 同 H1 政策

### ~~H3.~~ erp sidebar 沒 `diagrams/` 折疊群  ✅ resolved by B5/B8

- **原**：flat 命名導致 sidebar 無法分群
- **現**：sandbox-erp 重生後 `📁 DIAGRAMS/` 折疊群完整，內含 Server UML / Frontend UML + Activity/Class/Sequence/State/CI/CD/其他 6 個 prefix sub-groups
- 證據：`h3_erp_sidebar_diagrams_folding.png`

---

## I. SCHEMA / EDD 資料表呈現格式不一致（PostgreSQL vs Redis 寫法不對齊）  ✅ DONE

### I1. PostgreSQL 資料表只給 SQL，沒有欄位說明表

**現況**：`SCHEMA.md` §3 「資料表定義」每張 PostgreSQL 表的格式是
**先 `CREATE TABLE` SQL，後（甚至沒有）欄位說明**。

例（pet/SCHEMA.md L137-186）：
````
### 3.1 `claim_codes`

```sql
CREATE TABLE claim_codes (
    id          UUID NOT NULL DEFAULT gen_random_uuid(),
    pet_id      UUID NOT NULL REFERENCES pets(id),
    code_hash   TEXT NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    ...
)
```
（沒有對應的欄位說明 markdown table）
````

**問題**：HTML 渲染後 user 看到的只是 SQL 程式碼，要逐欄位讀 SQL 才知道
意義。SQL 是「實作面」，不是「閱讀面」。

### I2. Redis Key 只給表格，沒給命令語法

**現況**：`SCHEMA.md` §4 「Redis Key Schema」每個 key 的格式是
**只有 markdown table（Key Pattern / TTL / Value / Notes），沒給 Redis CLI 命令範例**。

例（pet/SCHEMA.md L731-737）：
```
| Key Pattern | TTL | Value | Notes |
|-------------|-----|-------|-------|
| `rl:claim:{email_hash}` | 3600 s | Integer attempt count | ... |
```
（沒有對應 `SET / EXPIRE / ZADD` 等 command 範例）

**問題**：實作端只有 table 看不到 command 語法，要自行翻譯成 Redis 操作。

### I3. 期望（user 拍板）：兩者都要「**欄位說明 → 然後 syntax**」

對 PostgreSQL 表 與 Redis key，兩者**都採同一順序**：

```
1. 欄位/Key 說明 markdown table（必填欄：欄位名 / 型別 / Nullable /
   預設值 / 說明）
2. 該 table/key 對應的語法區塊（CREATE TABLE / SET / ZADD ...）
```

理由：
- HTML 渲染後 user **同時看得到表格（閱讀）跟語法（實作）**，不用
  在語法跟說明間切換
- PostgreSQL 跟 Redis 兩種儲存層的呈現方式一致，避免認知切換成本

### I4. 同樣規則套用到 EDD 內任何 schema-like 區塊

EDD 文件中若引用 schema-style 內容（如 §3.4 BC Schema Ownership table、
§4.x 模組內列出 entity/table、§6.3 資料生命週期含 storage 結構等），
**任何時候列出資料表/Redis key 都遵守「說明表 → 然後語法」順序**，
不要只給 SQL 或只給 table。

### I5. 修法切片

| 檔案 | 改什麼 |
|---|---|
| `templates/SCHEMA.gen.md` Part 2 + Part 3 | 改成「欄位說明 → 然後 SQL」明確順序；新增 Part 對 Redis key 加「key 說明 → 然後 command 範例」|
| `templates/SCHEMA.review.md` | 新增 finding：**`[HIGH] PostgreSQL 表沒欄位說明表`** + **`[HIGH] Redis key 沒 command 範例`** |
| `templates/SCHEMA.md` | §3.1 / §3.2 範例改成新順序；§4.x（如有）加範例 |
| `templates/EDD.gen.md` | 在「§3.4 / §4.x / §6.3 schema 引用區塊」說明：列 table/key 一律 dual format |
| `templates/EDD.review.md` | 加對應 finding（同 SCHEMA review）|

預期執行 `gendoc-flow EDD` / `gendoc-flow SCHEMA` 時，review subagent
會列出缺漏並 fix subagent 補上 missing 欄位說明 / 缺的語法區塊。

---

## J. TOC / heading anchor 失效（所有 HTML 通病）  ✅ DONE

### J1. in-page anchor 連結被加 `target="_blank"` 開新分頁

**現況**：所有 `[X](#section)` markdown link 都被 inline_md L2447 加上
`target="_blank"`，導致點 TOC 連結時瀏覽器**開新分頁**而非定位滾動。

實查影響：pet 8 頁 + erp 5 頁含 `href="#X" target="_blank"`。

### J2. heading（h1~h4）沒 id 屬性

**現況**：`<h2>§9 — Data Access Layer</h2>` 沒 `id` 屬性，TOC 用
`<a href="#9--data-access-layer">` 找不到目標。

### J3. 修法（已 done）

- `_link()` callback 偵測 `#` 開頭 → 不加 `target="_blank"`
- 新增 `_heading_slug(text)` GitHub-style 算 slug，h1~h4 都帶 `id`
- slug 規則：lowercase → 每 `\s` 變 `-`（不 collapse） → drop 非
  alphanumeric/CJK/- → 修剪首尾 `-`
- 範例：`§9 — Data Access Layer` → `9--data-access-layer`

實機驗證（sandbox-erp/edd.html）：
- `href="#X" target=_blank` 數：1 → 0 ✅
- heading 全部帶 id ✅
- Playwright 點 §9 TOC → 同分頁 + URL hash 正確 + 滾到 §9.1（截圖 `j_toc_anchor_works.png`）

11 個 J group test 全綠（311/311 全綠）。

---

## K. workflow / 目錄樹被誤判為「系統圖」+ F2 mermaid 缺 lightbox  ✅ DONE

> **2026-05-10 user 在 pet 真實專案發現**：跑完 gen-html 後，arch.html / frontend.html / admin-impl.html / client-impl.html 多處原本可讀的 ASCII workflow、容器拓撲、目錄樹，全部被 F2 ascii→mermaid 轉成無 edge 或 label 含 `│` 的破壞版，且不能點開放大。

### K1. 多欄並排 ASCII 架構圖被擠成「整列 1 個 node、內部 `│` 留在 label」

- **事實**：`docs/ARCH.md` §1.2 System Context Diagram、§1.3 Container Diagram、§2.x Component Hierarchy 等 4 欄並排（Guest Player / Pet Owner / Competitive Player / Admin Operator）的 ASCII 系統圖被 F2 轉成 mermaid graph TD，每行（含原本的欄位分隔 `│`）變成**一個** node label。
- **證據**（`pet/docs/pages/arch.html` 渲染後）：
  ```
  L381: N1["Guest Player│  │ Pet Owner        │  │Competitive Player │  │Admin Operator"]
  L382: N2["(no token)  │  │ (URL token)      │  │(token + arena)    │  │(TOTP session)"]
  L383: N3["HTTPS            │  HTTPS                  │  HTTPS            │  HTTPS"]
  L386: N6["Player App                   │    │  Admin Portal"]
  L389: N9["HTTPS                                       │ HTTPS"]
  ```
  pipe 字元在 pet/arch.html 共 **206 個**，全部來自 F2 轉換（其他正常 mermaid 區塊不含 `│`）。
- **根因**（gen_html.py L2024-2025 of `_ascii_to_mermaid_td`）：
  ```python
  s = re.sub(r'^[\s│┃]+', '', s)   # 只剝行首
  s = re.sub(r'[\s│┃]+$', '', s)   # 只剝行尾
  ```
  **內部欄位分隔的 `│` 完全沒處理**。pass 1 把整行（含內部 pipes）整段塞給 `_add_node`，`_add_node` 內 `label.strip().rstrip('│')` 也只處理尾端，所以 4 欄並排的 actor box 就變 1 個塞滿 pipe 的長字串 node。
- **影響檔**（pipe 字元數排序）：`arch.html` 206、`client-impl.html` 154、`admin-impl.html` 91、`frontend.html` 54、`admin_impl.html` 12、`developer-guide.html` 9、`brd.html` 8、`prototype__pet-display-prototype.html` 6、`prototype__arena-battle-prototype.html` 6、`audio.html` 6、`prototype__admin-moderation-prototype.html` 2。

### K2. 檔案目錄樹被當成「系統元件樹」並平鋪成 mermaid 散點

- **事實**：`docs/FRONTEND.md` §2.1 Directory Structure、`docs/CLIENT_IMPL.md` §2.1 Directory Structure 等**檔案系統階層樹**（語意：內容階層）被 F1 分類成 'system'、F2 轉成 mermaid graph TD。
- **證據**（`pet/docs/pages/frontend.html` L387-419）：
  ```
  graph TD
    N0["apps/player/"]
    N1["index.html"]
    N2["vite.config.ts"]
    N4["src/"]
    N5["main.tsx                    # Entry point; React root"]
    N17["ClaimPage.tsx"]
    ...（共 382 nodes，11 個 mermaid block 跨整個 frontend.html）
  ```
  原本 markdown 是 `<pre>` 內的：
  ```
  apps/player/
  ├── index.html
  ├── vite.config.ts
  └── src/
      ├── main.tsx
  ```
- **根因**（gen_html.py `_classify_ascii_block` L1966-1972）：
  ```python
  for line in text.split('\n'):
      m = re.search(
          r'│[^│┤]*?(?:├──|└──)[^│┤A-Za-z一-鿿_]*[A-Za-z一-鿿_]',
          line,
      )
      if m and '┤' not in line[m.end():]:
          return 'system'
  ```
  這條「In-content tree branches」rule 對任何含 `├──` / `└──` 的行都判 'system'。**檔案目錄樹的視覺符號跟系統元件樹一樣**，分類器無法區分「檔案階層」vs「架構元件流向」，全部走 F2 路徑。
- **副作用**：F2 對純樹狀結構雖然會生 edges（從第一個非 `├──` 行當 parent），但 frontend.html 的 directory tree 結構深、嵌套多層，pass 3 只能配對「直接子節點」，巢狀層被打平。結果：382 nodes / 509 edges 但語意完全錯位。

### K3. F2 產生的 mermaid 沒包 `.diagram-container` → lightbox 完全失效

- **事實**：`assets/app.js` L146 把 lightbox click handler 綁在 `.diagram-container` class 上：
  ```js
  document.querySelectorAll('.diagram-container').forEach(el => { ... });
  ```
  edd.html / 其他原生 mermaid 區塊都包在 `<div class="diagram-container"><pre class="mermaid">...</pre></div>`，所以 lightbox bind 成功；F2 emit 的 mermaid 是裸 `<pre class="mermaid">...</pre>`，**沒包 wrapper**。
- **證據**：
  | 檔 | `.diagram-container` 數 | `<pre class="mermaid">` 數 | 比例 |
  |---|---|---|---|
  | `edd.html` (原生 mermaid 路徑) | 27 | 27 | 1:1（每個 mermaid 都有 wrapper）|
  | `arch.html` (F2 路徑) | 0 (5 是 CSS selector，不是真 element) | 3 | 0:3（**全部 F2 mermaid 無 wrapper**）|
- **根因**：F2 在 `gen_html.py` L2566-2576 的 dispatch 直接把 mermaid src 包成 `<pre class="mermaid">{src}</pre>` 寫出，沒套用原生 mermaid 路徑的 `<div class="diagram-container">` wrapper。**兩條 mermaid 輸出 path 沒共用同一個 emit 函式**。
- **使用者觀察對應**：「延伸他沒法點成大圖，所以當是橫向 workflow 根本看不清」— 雙重打擊：先被 K1/K2 破壞 label，又因 K3 不能放大檢視。

### K4. F1 + F2 沒分辨「應留 `<pre>` 不轉」的 case

- **事實**：「Request Lifecycle」這類**單欄垂直流**（player browser → Vite dev server → Fastify API），在 `developer-guide.html` 留為 `<pre class="doc-code"><code class="lang-text">`，**沒被轉換**。
- **證據**（`pet/docs/pages/developer-guide.html` L410-423）：
  ```html
  <pre class="doc-code"><code class="lang-text">Player browser
    │  HTTPS
    ▼
  Vite dev server (localhost:5173)  ← HMR websocket for .tsx/.ts/.css changes
    │  fetch() to localhost:3000
    ▼
  Fastify API (localhost:3000)
  ...
  </code></pre>
  ```
  這個正確（單欄垂直流，內容已可讀）。
- **對比**：同樣是「資訊流」結構，arch.html §1.2（多欄）被 F2 破壞，developer-guide.html §2.1（單欄）保留。**分類器邊界不明，user 看不出何時會被轉、何時不會**。
- **根因**：分類器與轉換器之間缺一個「品質閘」— F1 給出 'system' 後，F2 沒驗證「轉出的 mermaid 是否優於原 `<pre>`」就直接 emit。對多欄表格 + 純檔案樹，轉出的 mermaid 比原 `<pre>` 還差。

---

## L. subdir HTML 的 CSS / nav-brand / breadcrumb 路徑全壞 → style 盡失  ✅ DONE

> **2026-05-10 user 在 pet 真實專案發現**：所有 subdir 下的 `.html`（diagrams/、contracts/、prototype/、blueprint/mock/、req/）打開**完全沒有 CSS 樣式**，看起來像純文字頁。

### L1. `<head><link rel="stylesheet" href="assets/style.css">` 沒 depth-aware

- **事實**：subdir 下每個 `.html` 的 `<head>` 仍寫死 `href="assets/style.css"`（相對於 pages/ 根的路徑），但檔案實際在 `pages/<subdir>/`，瀏覽器解析後找的是 `pages/<subdir>/assets/style.css` ← **不存在**。
- **證據**：
  ```
  pages/diagrams/class-domain.html        L7: <link rel="stylesheet" href="assets/style.css">
  pages/contracts/api-admin-contract.html L7: <link rel="stylesheet" href="assets/style.css">
  pages/blueprint/mock/mock_server_guide.html L7: <link rel="stylesheet" href="assets/style.css">
  pages/req/idea-input.html               L7: <link rel="stylesheet" href="assets/style.css">
  pages/prototype/admin-moderation-prototype.html L7: <link rel="stylesheet" href="assets/style.css">
  ```
  正確路徑：1 層深要 `../assets/style.css`，2 層深（`blueprint/mock/`）要 `../../assets/style.css`。
- **損壞範圍實測**：

  | Subdir | 壞檔 / 該層 .html 總數 |
  |---|---|
  | `diagrams/` | 42 / 42 |
  | `contracts/` | 3 / 3 |
  | `prototype/`（spec docs，gen-html 渲的） | 3 / 4（gen-prototype 自產的 index.html 用 `assets/prototype.css` 自家 CSS，不破）|
  | `blueprint/mock/` | 1 / 1 |
  | `req/` | 1 / 1 |
  | **合計** | **50 / 51** |

### L2. nav-brand 連結 `<a href="index.html">` 同樣沒 prefix

- **事實**：subdir 下每個 .html 的 header `<a class="nav-brand">pet</a>` 寫死 `href="index.html"`，點下去解析為 `pages/<subdir>/index.html`，不是 `pages/index.html`。
- **證據**：
  ```
  pages/diagrams/class-domain.html         L177: <a href="index.html" class="nav-brand">pet</a>
  pages/contracts/api-admin-contract.html  L177: <a href="index.html" class="nav-brand">pet</a>
  ```
- **後果**：在 `diagrams/` 與 `contracts/` 點 nav-brand → 404（兩 subdir 內無 index.html）；在 `prototype/` 點 → 落到 prototype shell（誤導）。

### L3. banner-breadcrumb 連結 `<a href="index.html">pet</a>` 同樣沒 prefix

- **事實**：subdir 下每個 .html 的 banner `<p class="banner-breadcrumb"><a href="index.html">pet</a> › ...</p>` 寫死 `href="index.html"`，行為同 L2。
- **證據**：
  ```
  pages/diagrams/class-domain.html         L188: <a href="index.html">pet</a> › 類別圖：領域模型
  pages/contracts/api-admin-contract.html  L188: <a href="index.html">pet</a> › contracts/ › Api Admin Contract
  pages/prototype/arena-battle-prototype.html L188: <a href="index.html">pet</a> › prototype/ › Arena Battle Prototype
  ```

### L4. sidebar `__link href` 反而**正確**帶 `../` 前綴（單一被處理的部分）

- **事實**：sidebar 內的 `<a class="sidebar__link" href="../idea.html">` 全部正確帶 `../`（1 層）或 `../../`（2 層）prefix。
- **證據**（`pages/diagrams/class-domain.html`）：
  ```
  L195: sidebar__link" href="../index.html
  L196: sidebar__link" href="../idea.html
  ```
  （`pages/blueprint/mock/mock_server_guide.html`）：
  ```
  sidebar__link" href="../../index.html
  ```
- **意涵**：path rewriter（`rewrite_pages_paths`，B7 R3-2/R3-3）**只處理 sidebar 區塊內的 `__link`**，沒擴及到 `<head><link>`、`nav-brand`、`banner-breadcrumb` 三類連結。
- **根因**：B7 path rewriter 設計時把「跨層 path 修正」聚焦在 sidebar list（因為當時主訴是「subdir 頁的 sidebar 連回主文件失效」），但 head/nav-brand/breadcrumb 的 path **是同樣跨層問題的不同位置**，沒一起納入 rewrite scope。

### L5. 為何 prototype 內的 spec docs 也壞但 prototype shell index 不壞

- **事實**：
  - `prototype/index.html`（gen-prototype 自產）：`<link rel="stylesheet" href="assets/prototype.css">` ← **檔案實際存在 `pages/prototype/assets/prototype.css`** → 不破
  - `prototype/admin-moderation-prototype.html`（gen-html 從 `docs/prototype/admin-moderation-prototype.md` 渲染）：`<link rel="stylesheet" href="assets/style.css">` → 找 `pages/prototype/assets/style.css` ← 不存在 → 破
- **意涵**：兩個 skill 的 asset 部署假設不同，gen-html 沒對 subdir 做 depth-aware，gen-prototype 自帶 assets 子樹所以剛好沒事。

---

## M. prototype 回 docs 的 link 全部失效  ✅ DONE

> **2026-05-10 user 反映**：prototype 目錄底下的 HTML 已有，但「原本可以回文件的 link 都失效了」。需 gen-prototype 寫對、gen-html 驗錯修正。

### M1. spec docs（admin-moderation / arena-battle / pet-display-prototype.html）的 breadcrumb 落到錯地方

- **事實**：`pages/prototype/<spec>.html` 的 banner breadcrumb `<a href="index.html">pet</a>`，相對於 `pages/prototype/`，解析為 `pages/prototype/index.html`（**prototype shell**），**不是 `pages/index.html`（docs hub）**。
- **證據**（`pages/prototype/admin-moderation-prototype.html` L188）：
  ```html
  <p class="banner-breadcrumb"><a href="index.html">pet</a> › prototype/ › Admin Moderation Prototype</p>
  ```
- **後果**：使用者預期 "pet" → 回文件中心，實際被導到 prototype shell。
- **根因**：同 L3（path rewriter 沒處理 banner）。

### M2. prototype shell（gen-prototype 自產的 `prototype/index.html`）完全沒回 docs 連結

- **事實**：grep `pages/prototype/index.html` 對 keyword `docs / 文件 / 首頁 / home / 主頁 / DOCS / RETURN / BACK_TO_DOCS` → **0 命中**。
- **證據**：整檔內所有 anchor：
  ```
  L144: <button id="btn-back" onclick="protoBack()">← BACK</button>   ← JS history.back，外部直開時不能用
  L146: <a href="api-explorer/index.html" target="_blank">API EXPLORER ↗</a>
  L147: <a href="admin/index.html" target="_blank">ADMIN ↗</a>
  L249: {name:'Dashboard', href:'admin/index.html', ...}
  ```
  全部是 prototype 內部，**沒有任何 anchor 指向 `../index.html` 或同等的 docs hub**。
- **根因**：`skills/gendoc-gen-prototype/SKILL.md` 的 shell 模板沒寫 docs back-link。

### M3. admin prototype（`prototype/admin/*.html`）整層 nav 沒出口

- **事實**：`pages/prototype/admin/index.html` nav 列：
  ```
  L21: <a href="index.html"       class="nav-link active">▦ Dashboard</a>
  L22: <a href="pets.html"        class="nav-link">🐾 Pets</a>
  L23: <a href="leaderboard.html" class="nav-link">🏆 Leaderboard</a>
  L25: <a href="config.html"      class="nav-link">⚙ Config</a>
  L26: <a href="analytics.html"   class="nav-link">📊 Analytics</a>
  ```
  + 多個內部跳轉 `pets.html?status=flagged`、`config.html`、`analytics.html`。
- **證據**：grep `href="\.\.|HOME|BACK|DOCS|prototype/index|首頁` → **0 命中**。**整個 admin 子樹沒有任何路徑回 prototype shell 或 docs**。
- **根因**：gen-prototype 把 admin 子模組視為獨立 SPA，未加全域 back-link。

### M4. api-explorer（`prototype/api-explorer/index.html`）只回到 prototype shell，不回 docs

- **事實**：`pages/prototype/api-explorer/index.html` L540：
  ```html
  <a href="../index.html" class="nav-link">← Prototype</a>
  ```
- **意涵**：唯一一處有「回上層」link 的是 api-explorer，但只回 prototype shell，**不直連 docs hub**。
- **根因**：同 M2，模板層沒留 docs 出口。

### M5. gen-html 對 prototype/ 的處理是 byte-copy，無法修正 M1/M2/M3/M4

- **事實**：`gen_html.py` `write_page` 對 `pages/prototype/` 已有保護邏輯（B4）— 不覆寫 gen-prototype 寫進去的檔。但這個保護**也阻止了 gen-html 修正壞掉的 link**。
- **證據**：B4 保護實作（gen_html.py 對應段落）跳過 prototype/ 下 user 既有檔，不做任何 path-rewrite。
- **意涵**：M1（spec docs，這些是 gen-html 自己渲染，**不在保護內**）→ gen-html 應該能處理但因為 path-rewriter scope 太窄而沒處理；M2/M3/M4（gen-prototype 自產的檔，**在保護內**）→ gen-html 完全不碰，只能由 gen-prototype 修。

### M6. user 新需求：gen-prototype 與 gen-html 雙重保險

- **user 原話**：「有必要 gen-prototype 也要寫對，gen-html 要去檢查，若錯要修正」
- **拆解**：
  - gen-prototype 端：shell 模板必須含 `<a href="../index.html">回文件</a>`（或同等 anchor）；admin 子樹也須有路徑回 prototype shell + docs
  - gen-html 端：對 prototype/ 內所有 .html（不論是自己渲的 spec docs 或 gen-prototype 寫的 shell）做 link 完整性掃描；發現指向不存在或路徑錯誤的 docs/shell 連結 → 修正

---

## N. TOC（Table of Contents）— 新需求：每個 HTML 都要標配  ✅ DONE

> **2026-05-10 user 新增需求**：「不是每一個 HTML，有 table of contents，對於這個我想 gen-html 要把每一個 html 都有這個標配」。

### N1. 現況：絕大多數 HTML 沒 TOC

- **事實**：pet/docs/pages 110 個 top-level `.html` 中，**只 7 個** body 內含字串 "Table of Contents"：
  ```
  api.html
  cicd.html
  developer-guide.html
  developer_guide.html
  index.html
  runbook.html
  test-plan.html
  ```
- **這 7 個的來源**：source markdown 自己手寫了 `## Table of Contents` + 一串 `[X](#anchor)` list；gen_html 只是被動 render 出來，沒主動產生。

### N2. 主要文件全部沒 TOC

- **事實**：grep `Table of Contents|class="toc"|nav.*toc` 對以下檔 → 全部 0 命中：
  ```
  edd.html       (107940 bytes，21 個 H2)
  schema.html    (129810 bytes，18 個 H2)
  arch.html      (101685 bytes，多個 H2)
  prd.html       (111781 bytes)
  brd.html       (61586 bytes)
  pdd.html       (141259 bytes)
  vdd.html       (105188 bytes)
  ```
- **意涵**：最大、最常被讀的核心文件**都沒目錄**，使用者無法快速跳轉到指定 section。

### N3. gen_html 沒任何 TOC 自動生成邏輯

- **事實**：grep `gen_html.py` 對 `toc / table.of.contents / TOC / build_toc / make_toc` → **0 個函式**做這件事。
- **證據**：`gen_html.py` 沒有「掃描所有 H1~H4 → 生成 anchor list → 注入到頁首」這條 pipeline。
- **根因**：gen_html 一直定位為 "passive renderer"（被動把 markdown 轉 HTML），沒主動加值。

### N4. TOC 標配化的技術前提：哪些有、哪些沒

- **✅ 有**：J 群已加 `_heading_slug(text)`，h1~h4 都帶 `id="..."`（驗證：edd.html 154/155 個 heading 帶 id），所以 anchor 跳得到目標。
- **✅ 有**：J 群已修 `inline_md`，in-page `#anchor` 不再被加 `target="_blank"`，跳轉行為正確（同分頁滾動）。
- **❌ 沒**：build-time TOC 抽取邏輯（掃 H2/H3 list）
- **❌ 沒**：TOC 渲染版位設計（main 頂部 sticky? sidebar 浮動? floating right rail?）
- **❌ 沒**：「TOC 展開深度」規格（只展 H2? 還是 H2+H3? 還是全展?）
- **❌ 沒**：「短文件不需 TOC」門檻（如 < 3 個 H2 不顯示）
- **❌ 沒**：CSS（高亮 current section、scroll-spy 行為）

### N5. 含 TOC 的 7 個檔的 TOC 形式（觀察）

- **事實**：抽 `index.html` 的 TOC（L363）：
  ```html
  <ul>
    <li><a href="#overview">Overview</a></li>
    <li><a href="#core-features">Core Features</a></li>
    <li><a href="#system-architecture">System Architecture</a></li>
    ...（共 17 條）
  </ul>
  ```
  純 markdown list（每行一個 H2/H3），無 sticky、無 scroll-spy、無 indent 區分階層。
- **意涵**：這個 baseline 就算 gen-html 自動生成、其他文件也只能達到這個樣子。**user 的標配要求暗示需要更好的 UX**（至少 sticky / 高亮 current）— 還未跟 user 對齊。

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
## P. 真實破圖（visual-lock 找到、scan_visual 確認）

> **2026-05-11 03:0X** scan_visual.mjs 對 pet+erp 全 260 個 mermaid+umock block 跑 Playwright + browser render 後找到。3 個必修（孤兒 stale 不算）。
> **每個項目附 .md 原 fenced block + .html 內 render 後 mermaid/umock 文字**，方便回頭驗修法。

> **規則**：修法時以 `tools/gen_html/tests/test_visual_lock.py` 245 個 fixture 全綠當 baseline，動到任何一個都會被擋下。

---

### P1. pet/frontend.html block #2

- **狀態**：OPEN
- **Source markdown**: `pet/docs/FRONTEND.md` — 第 3 個 diagram fenced block
- **Root cause**：F2 ASCII → mermaid，edge label 含字面 `|`（`RUN | STRENGTH | STAMINA`）。commit `84326e2` 把 `_mermaid_fix_block` 套到 F2 emit point，`fix_flowchart_line.quote_edge_label` (gen_html.py:604-611) 的 regex `\|([^|]*)\|` 沿字面 `|` 切成 N 段，每段獨立判斷 → segment 含 `(`/`{`/`/` 觸發 quote-wrap → 引號炸碎。

**輸入 .md fenced block（節錄前 30 行）**：

```text
```
PetPage (owner authenticated via Bearer token)
  ↓ clicks TrainingEntry
TrainingPage /pet/:petId/train
  │
  ├─ TrainingActions shows 3 action cards (RUN / STRENGTH / STAMINA)
  │    Each card shows current stat value and trains-remaining count
  │    training_actions_per_day = 3 actions per UTC day
  │
  ├─ User clicks "Train" on a card
  │    → POST /api/v1/pets/:petId/train  { trainingType: 'RUN' | 'STRENGTH' | 'STAMINA' }
  │    ← { updatedStats, statDelta, actionsRemainingToday }
  │
  ├─ On success:
  │    StatChangeIndicator appears: "+X Speed" floats up, visible for
  │    training_stat_display_duration_seconds = 2 seconds
  │    Stat bars animate to new values
  │    usePet cache is invalidated → PetPage re-fetches
  │
  ├─ Error states:
  │    HTTP 400 VALIDATION_ERROR → toast: "Invalid training type. Please try again."
  │    HTTP 400 TRAINING_LIMIT_REACHED → all action cards disabled; DailyResetTimer shown
  │    HTTP 400 STAT_AT_MAXIMUM → toast: "Stat is already at maximum (pet_stat_max = 100)"; card remains
  │                                enabled for other stats not yet at max
  │    HTTP 401 → handled globally: clearPetToken() + redirect to /
  │    HTTP 403 NOT_OWNER → toast: "You do not own this pet." (should not occur in normal flow)
  │    HTTP 404 PET_NOT_FOUND → toast: "Pet not found. Please reload and try again." (should not occur in normal flow)
  │
  └─ Exhausted (actionsRemainingToday = 0):
       DailyResetTimer shows countdown to UTC 00:00 reset
... (省略)
```

**輸出 .html（render 後 mermaid/umock 文字，節錄）**：

```html
<div class="diagram-container"><pre class="mermaid">graph TD
  N0[&quot;PetPage (owner authenticated via Bearer token)&quot;]
  N1[&quot;clicks TrainingEntry&quot;]
  N2[&quot;TrainingPage /pet/:petId/train&quot;]
  N3[&quot;TrainingActions shows 3 action cards (RUN / STRENGTH / STAMINA)&quot;]
  N4[&quot;User clicks &#x27;Train&#x27; on a card&quot;]
  N5[&quot;On success:&quot;]
  N6[&quot;Error states:&quot;]
  N7[&quot;Exhausted (actionsRemainingToday = 0):&quot;]
  N8[&quot;DailyResetTimer shows countdown to UTC 00:00 reset&quot;]
  N9[&quot;All action cards disabled&quot;]
  N10[&quot;Neglect check: if last_trained_at &gt; training_neglect_threshold_days = 3 days ago&quot;]
  N11[&quot;NeglectedState overlay renders on PetCanvas&quot;]
  N3 --&gt;|&quot;Each card shows current stat value and trains-remaining count training_actions_per_day = 3 actions per UTC day&quot;| N4
  N4 --&gt;|&quot;&#x27;→ POST /api/v1/pets/:petId/train  { trainingType: &#x27;RUN&#x27; &quot;| &#x27;STRENGTH&#x27; |&quot; &#x27;STAMINA&#x27; } ← { updatedStats, statDelta, actionsRemainingToday }&#x27;&quot;| N5
  N5 --&gt;|&quot;StatChangeIndicator appears: &#x27;+X Speed&#x27; floats up, visible for training_stat_display_duration_seconds = 2 seconds Stat bars animate to new values usePet cache is invalidated → PetPage re-fetches&quot;| N6
  N6 --&gt;|&quot;HTTP 400 VALIDATION_ERROR → toast: &#x27;Invalid training type. Please try again.&#x27; HTTP 400 TRAINING_LIMIT_REACHED → all action cards d...
```

---

### P2. pet/frontend.html block #5

- **狀態**：OPEN
- **Source markdown**: `pet/docs/FRONTEND.md` — 第 6 個 diagram fenced block
- **Root cause**：同 P1 機制：edge label 含字面 `|`（GDPR types `erasure | data_access | ...`）。

**輸入 .md fenced block（節錄前 30 行）**：

```text
```
PetPage (owner authenticated via Bearer token)
  ↓ clicks "Data Rights" / GDPR link
GdprPage /gdpr
  │
  ├─ GdprRequestForm
  │    Type selector (radio / dropdown):
  │      erasure | data_access | restrict_processing | object_leaderboard | rectification
  │    → POST /api/v1/gdpr/request  { type: "erasure" | ... }   (auth: Bearer token)
  │    ← { jobId, message }  HTTP 202 Accepted
  │    jobId stored in component state; GdprStatusBanner activates
  │
  ├─ GdprStatusBanner (after submission)
  │    Polls GET /api/v1/gdpr/request/status?jobId=<jobId>  (auth: Bearer token)
  │    Displays current status: pending | processing | completed | failed
  │    SLA copy displayed per request type:
  │      erasure → "Processed within 7 days (gdpr_email_deletion_window_days = 7)"
  │      data_access / portability → "Processed within 30 days (gdpr_data_access_response_days = 30; gdpr_data_portability_response_days = 30)"
  │      restrict_processing → "Processed within 24 hours (gdpr_restrict_processing_response_hours = 24)"
  │      object_leaderboard → "Processed within 5 business days (gdpr_object_leaderboard_response_business_days = 5)"
  │      rectification → "Processed within 24 hours (gdpr_email_rectification_response_hours = 24)"
  │
  └─ Error states:
       HTTP 400 VALIDATION_ERROR → inline form error: "Please select a valid request type."
       HTTP 401 → redirect to / (token cleared)
       HTTP 403 FORBIDDEN → "Your account is not authorized to view this request."
       HTTP 404 NOT_FOUND → "Request not found."
```
```

**輸出 .html（render 後 mermaid/umock 文字，節錄）**：

```html
<div class="diagram-container"><pre class="mermaid">graph TD
  N0[&quot;PetPage (owner authenticated via Bearer token)&quot;]
  N1[&quot;clicks &#x27;Data Rights&#x27; / GDPR link&quot;]
  N2[&quot;GdprPage /gdpr&quot;]
  N3[&quot;GdprRequestForm&quot;]
  N4[&quot;GdprStatusBanner (after submission)&quot;]
  N5[&quot;Error states:&quot;]
  N6[&quot;HTTP 400 VALIDATION_ERROR  inline form error: &#x27;Please select a valid request type.&#x27;&quot;]
  N7[&quot;HTTP 401  redirect to / (token cleared)&quot;]
  N8[&quot;HTTP 403 FORBIDDEN  &#x27;Your account is not authorized to view this request.&#x27;&quot;]
  N9[&quot;HTTP 404 NOT_FOUND  &#x27;Request not found.&#x27;&quot;]
  N3 --&gt;|&quot;&#x27;Type selector (radio / dropdown): erasure &quot;| data_access | restrict_processing | object_leaderboard |&quot; rectification → POST /api/v1/gdpr/request  { type: &#x27;erasure&#x27; &quot;| ... }   (auth: Bearer token) ← { jobId, message }  HTTP 202 Accepted jobId stored in component state; GdprStatusBanner activates&quot;| N4
  N4 --&gt;|&quot;&#x27;Polls GET /api/v1/gdpr/request/status?jobId=&lt;jobId&gt;  (auth: Bearer token) Displays current status: pending &quot;| processing | completed | failed SLA copy displayed per request type: erasure → &#x27;Processed within 7 days (gdpr_email_deletion_window_days = 7)&#x27; data_access / portability → &#x27;Processed within 30 days (gdpr_data_access_response_days = 30; gdpr_data_portability_response_days = 30)&#x27; restrict_processing ...
```

---

### P3. erp/frontend.html block #1 (umock)

- **狀態**：OPEN
- **Source markdown**: `erp-api-token-manager/docs/FRONTEND.md` — 第 2 個 diagram fenced block
- **Root cause**：ASCII testing-pyramid 偵測為 umock pyramid SVG，`_um_r_pyramid` emit `<svg viewBox="0 0 600 260">` **沒設 width/height attr**；CSS `.umock__pyramid { display:block; max-width:100%; height:auto }` 但外層 `.diagram-container--umock { width: fit-content }` 對純 SVG 撐不開 → SVG `clientWidth/clientHeight` 都 0px 看不到。

**輸入 .md fenced block（節錄前 30 行）**：

```text
```
              ┌─────────────┐
              │  E2E Tests  │   Playwright .NET 1.44
              │   5–10%     │   Critical User Flows（建立 / 撤銷 / 審計）
         ┌────┴─────────────┴────┐
         │  Integration Tests    │   xUnit + WebApplicationFactory
         │     20–30%            │   PageModel ↔ Use Case ↔ DB（Testcontainers PostgreSQL）
    ┌────┴───────────────────────┴────┐
    │  Unit Tests                     │   xUnit + FluentAssertions
    │     60–70%                      │   PageModel 單元 / Domain Service / Validator
    └─────────────────────────────────┘
```
```

**輸出 .html（render 後 mermaid/umock 文字，節錄）**：

```html
<div class="diagram-container diagram-container--umock"><div class="diagram-container"><svg class="umock__pyramid" viewBox="0 0 600 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="pyramid"><polygon points="220.0,10.0 380.0,10.0 410.0,86.0 190.0,86.0" fill="#dbeafe" stroke="#1e40af" stroke-width="1.5"/><text x="300.0" y="34.0" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" font-weight="600" fill="#0f172a">E2E Tests</text><text x="300.0" y="52.0" text-anchor="middle" font-family="system-ui,sans-serif" font-size="12" fill="#1e3a8a">5–10%</text><text x="300.0" y="70.0" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" fill="#475569">Playwright .NET 1.44 Critical User Flows（建立 / 撤銷 / 審計）</text><polygon points="190.0,90.0 410.0,90.0 490.0,166.0 110.0,166.0" fill="#bfdbfe" stroke="#1e40af" stroke-width="1.5"/><text x="300.0" y="114.0" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" font-weight="600" fill="#0f172a">Integration Tests</text><text x="300.0" y="132.0" text-anchor="middle" font-family="system-ui,sans-serif" font-size="12" fill="#1e3a8a">20–30%</text><text x="300.0" y="150.0" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" fill="#475569">xUnit + WebApplicationFactory PageModel ↔ Use Case ↔ DB（Testcontainers PostgreSQL）</text><polygon points="110.0,170.0 490.0,170.0 570.0,246.0 30.0,246.0" fill="#93c5fd" stroke="#1e40af" stroke-width="1.5"/><text x="300.0" y="194.0" tex...
```

---

### Status Tracker

| ID | Status | Fix Commit |
|---|---|---|
| P1 | OPEN | — |
| P2 | OPEN | — |
| P3 | OPEN | — |
