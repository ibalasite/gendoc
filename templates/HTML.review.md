---
doc-type: HTML
target-path: docs/pages/
special-skill: gendoc-gen-html
reviewer-roles:
  primary: "Frontend Engineer（HTML 產出審查者）"
  primary-scope: "HTML 完整性、導覽結構、內容正確性"
quality-bar: "每份 docs/*.md 文件均有對應的可瀏覽 HTML 頁面，index.html 存在且導覽連結正確。"
---

# HTML Review Items

本檔案定義 `docs/pages/` 目錄的審查標準。由 gendoc-flow Review subagent 讀取並遵循。
HTML 為 special_skill step（gendoc-gen-html），由該 skill 內部 review loop 主導；此檔案補充外部驗證視角。

---

## §A — HTML 完整性

**[CRITICAL] HC-01 — HTML 頁面數量符合預期**

**Check**: `docs/pages/` 下的 `.html` 檔案數（排除 `index.html`）是否等於 `docs/*.md` 的文件數（排除 README.md）？

**Risk**: HTML 頁面缺失導致文件無法瀏覽，使用者無法訪問對應的文件內容。

**Fix**: 對每個缺少對應 HTML 的 `.md` 文件，觸發 gendoc-gen-html 補跑對應頁面。

---

**[HIGH] HC-02 — index.html 存在且導覽連結完整**

**Check**: `docs/pages/index.html` 是否存在？是否包含所有子頁面的導覽連結？所有連結是否正確指向對應的 HTML 檔案？

**Risk**: 缺少 index.html 或連結錯誤，使用者無法導覽文件。

**Fix**: 補充或修正 index.html 的導覽連結清單。

---

**[MEDIUM] HC-03 — 頁面結構一致性**

**Check**: 所有生成的 HTML 頁面是否使用一致的樣式（統一的 CSS 連結、頁首、頁尾結構）？

**Risk**: 不一致的樣式讓文件看起來零散，降低專業性。

**Fix**: 確認所有 HTML 頁面引用同一個 CSS 檔案，頁首/頁尾結構一致。

---

## Self-Check：輸出完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> HTML 為目錄型輸出（special_skill），Self-Check 驗證文件數量而非 H2 章節。

**指令：**
1. 計算 `docs/*.md` 的文件數（排除 README.md、ALIGN_REPORT.md 等非正式文件）→ `expected_count`
2. 計算 `docs/pages/*.html` 的文件數（排除 `index.html`）→ `actual_count`
3. 若 `actual_count < expected_count` → CRITICAL finding（列出缺少 HTML 的 MD 文件名稱）
4. 確認 `docs/pages/index.html` 存在；若不存在 → CRITICAL finding

**通過條件：**
- `actual_count >= expected_count`
- `docs/pages/index.html` 存在且非空
