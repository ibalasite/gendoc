# sidebar-erp preview sandbox

獨立於 erp 專案的視覺驗證環境。**不會碰原始 erp 專案任何檔案**。

## 建立 / 同步

```bash
cd tools/gen_html/preview/sidebar-erp
rsync -a --delete \
  ~/projects/erp-api-token-manager/docs/ docs/ \
  --exclude pages \
  --exclude blueprint/scaffold \
  --exclude blueprint/contracts \
  --exclude blueprint/infra \
  --exclude blueprint/mock/data
```

## 重生 HTML + sidebar 預覽

```bash
python3 ../../gen_html.py
python3 -m http.server 8762
# open http://localhost:8762/index.html
```

## 用途

同 sidebar-pet/，驗證 erp 結構下的 B 群結果（含 bdd/client、bdd/server）。
