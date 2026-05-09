# sidebar-pet preview sandbox

獨立於 pet 專案的視覺驗證環境。**不會碰原始 pet 專案任何檔案**。

## 建立 / 同步

```bash
cd tools/gen_html/preview/sidebar-pet
rsync -a --delete \
  ~/projects/pet/docs/ docs/ \
  --exclude pages \
  --exclude blueprint/scaffold \
  --exclude blueprint/contracts \
  --exclude blueprint/infra \
  --exclude blueprint/mock/data
```

## 重生 HTML + sidebar 預覽

```bash
python3 ../../gen_html.py
python3 -m http.server 8761
# open http://localhost:8761/index.html
```

## 用途

驗證 B 群（B1–B7）：
- 子目錄 .md → subdir .html 鏡射
- sidebar 樹狀折疊（含巢狀 blueprint/mock/）
- diagrams 內部 Server/Frontend → Activity/Class/Sequence/State/CI/CD/其他 分區

## 排除規則

非 .md 子目錄（scaffold / contracts schemas / infra / mock data）排除 rsync，
讓 sandbox 輕量；不影響 sidebar 測試（只關注 .md 鏡射）。
