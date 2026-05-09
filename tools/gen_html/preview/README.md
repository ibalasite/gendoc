# gen_html visual preview sandbox

獨立於 pet/erp 的視覺驗證環境，**不會碰任何下游專案**。

## 用途

驗證 A 群（A1–A5）CSS / 渲染變動的視覺效果。

## 重生

```bash
cd tools/gen_html/preview
python3 ../gen_html.py
```

產出：
- `docs/pages/index.html`
- `docs/pages/pdd.html`（A 群驗證樣本）

## 開啟

```bash
open docs/pages/pdd.html       # macOS
# 或
xdg-open docs/pages/pdd.html   # Linux
```

## 驗證清單

| 樣本 | 對應 A 項 | 看什麼 |
|---|---|---|
| §1 Card | A3 | 邊界深灰 1.5px，title-bar 有明顯分隔線 |
| §2 Modal | A3 | 同上 |
| §3 Table | A4 | cell padding 寬鬆、列分隔可見、thead 突出 2px |
| §4 Page | A2 / A3 / A5 | sidenav 沒 `│` 殘留、外框深、按鈕 Tab 跳過 |
| §5 Buttons | A5 | Tab 鍵不會 focus 任何 mock 按鈕 |

## 為何放這裡

`gen_html` 用 `Path.cwd()/docs/` 當輸入根，所以這目錄自帶 `docs/PDD.md`，
`cd preview` 後跑 gen_html 就能用本地源產出本地頁面，完全不依賴 pet/erp。
