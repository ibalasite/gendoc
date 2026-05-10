# k-group preview sandbox

K 群驗證環境。**不碰任何真實專案（pet/erp）的檔案**。

包含 K1-K8 全部場景的 fixture，用來：
1. 跑 gen_html 產出 docs/pages/
2. 用 Playwright 開頁、點 lightbox、截圖
3. screenshots/ 存所有驗證截圖

## 重新產出

```bash
cd /Users/tobala/projects/gendoc/tools/gen_html/preview/k-group
python3 ../../gen_html.py
```

## 場景對應

| 檔 | K 群 step | 驗證 |
|---|---|---|
| `docs/K-FIXTURE.md` | K1-K8 | 所有形態混在 1 個 .md，方便集中驗證 |
