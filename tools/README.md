# `tools/` — gendoc runtime packages

> 所有 gendoc skill 在執行期會呼叫的 Python / Shell 工具都住在這個目錄。
> Source of truth 在 `tools/<package>/`，runtime artifacts 在 `tools/bin/`。

---

## Layout

```
tools/
├── README.md                     ← 你正在看這個
├── dryrun_core/                  ← package: DRYRUN pipeline 推演
│   ├── dryrun_core.py            ← entry source (1 main 入口)
│   ├── tests/                    ← pytest tests
│   ├── fixtures/                 ← 測試固定 input
│   ├── pytest.ini
│   └── Makefile
├── gen_html/                     ← package: docs/ → docs/pages/ HTML 站
│   ├── gen_html.py               ← entry source
│   ├── tests/                    ← pytest tests
│   ├── preview/                  ← 視覺驗證 sandbox（不影響 pet/erp）
│   │   ├── docs/                 ← 範例 source 含 PDD.md UI mock
│   │   ├── sidebar-pet/          ← rsync 自 ~/projects/pet/docs（gitignored）
│   │   ├── sidebar-erp/          ← rsync 自 ~/projects/erp-api-token-manager/docs
│   │   └── screenshots/          ← Playwright 視覺驗證留檔
│   └── pytest.ini
├── guard/                        ← package: PreToolUse / Stop hook 行為測試
│   ├── simulate_skill.py
│   ├── test_blocker_rules.py
│   ├── test_checkpoint.py
│   └── test_stop_dodge.py
└── bin/                          ← runtime artifacts（由 setup 部署，不要手改）
    ├── dryrun_core.py            ← 從 ../dryrun_core/dryrun_core.py 複製
    ├── gen_html.py               ← 從 ../gen_html/gen_html.py 複製
    ├── gendoc-guard-blocker.py   ← guard hook 執行體
    ├── gendoc-guard-history.py
    ├── gendoc-guard-session-start.py
    ├── gendoc-guard-stop.py
    ├── gate-check.sh             ← shell helpers
    ├── get-upstream.sh
    ├── review.sh
    └── review_integration.sh
```

**設計原則**：
- `tools/<package>/` 含 dev source + tests + fixtures（pytest 跑）
- `tools/bin/` 是 runtime 部署目標（單檔 `.py` / `.sh`），skill 直接呼叫
- 修改永遠在 `tools/<package>/`，部署用 `setup` 自動複製

---

## 怎麼用每個 package

### `dryrun_core` — DRYRUN pipeline 推演核心

**入口**：`dryrun_core.py` (`def main()` 或 `if __name__ == '__main__'`)

```bash
# 在目標專案根目錄執行
cd ~/projects/<your-project>
python3 ~/.claude/skills/gendoc/tools/bin/dryrun_core.py [args]
```

由 `gendoc-flow` skill 自動觸發（DRYRUN step）。

### `gen_html` — Markdown → HTML 文件中心

**入口**：`gen_html.py` (`def main()`)

```bash
# 在目標專案根目錄執行
cd ~/projects/<your-project>
python3 ~/.claude/skills/gendoc/tools/bin/gen_html.py
```

讀取 `docs/*.md` + `features/*.feature`，輸出到 `docs/pages/`。
由 `gendoc-gen-html` skill 自動觸發。

### `guard` — Hook 行為測試（無 runtime 入口）

只跑 pytest，沒有 runtime 入口。所有 hook 執行體在 `bin/` 已是現成 `.py`。

---

## 怎麼測試

### 對單一 package

```bash
cd tools/<package>
python3 -m pytest          # 跑該 package tests/ 全部
python3 -m pytest -k name  # 篩名稱
```

### 跑所有 package tests

```bash
cd tools
for d in */; do
  if [[ -d "$d/tests" ]]; then
    echo "=== $d ==="
    (cd "$d" && python3 -m pytest)
  fi
done
```

### gen_html 額外的 standalone test runner

`gen_html/tests/test_*.py` 每個檔內含 `def main():` standalone runner，
可直接執行（不一定需要 pytest）：

```bash
python3 tools/gen_html/tests/test_path_rewriter.py
python3 tools/gen_html/tests/test_b_group_scanner.py
# 等等
```

### gen_html 視覺驗證（Playwright sandbox）

`tools/gen_html/preview/` 是獨立 sandbox：

```bash
# 同步 pet 的 docs/ 到 sandbox
cd tools/gen_html/preview/sidebar-pet
rsync -a --delete ~/projects/pet/docs/ docs/ \
  --exclude=pages/*.html \
  --exclude=blueprint/scaffold \
  --exclude=blueprint/contracts \
  --exclude=blueprint/infra \
  --exclude=blueprint/mock/data

# 重生 HTML
python3 ../../gen_html.py

# 啟 server 視覺驗證
cd docs/pages && python3 -m http.server 8761
# open http://localhost:8761/index.html
```

驗證截圖留在 `tools/gen_html/preview/screenshots/`。

---

## 怎麼變 `tools/bin/` 的程式

`tools/bin/` 是部署目標，**禁止手改**（PreToolUse hook 已封鎖
`~/.claude/skills/gendoc/`）。流程：

```
1. 修改 tools/<package>/<entry>.py          ← source of truth
2. cd ~/projects/gendoc
3. git commit + push                         ← 必須先 push 到 remote
4. user runs ./setup upgrade (或 SessionStart hook 自動觸發)
   └── bash setup → _deploy_tools()
       └── 依 package 內檔自動選兩種模式之一（見下）
5. ~/.claude/skills/gendoc/tools/bin/<entry>.py 變新版
```

### 兩種部署模式（per-package 自動選）

`_deploy_tools()` 對 `tools/<package>/` 每個目錄做：

| 條件 | 行為 |
|---|---|
| **`build.sh`（or `build.ps1` on Windows）存在** | 執行該 script，由 script 自行決定產物。適合需要 compile / minify / bundle / 多檔合併 的 package。|
| **否則** | 套 convention：`cp tools/<package>/<package>.py → tools/bin/<package>.py`。適合單檔 Python script。|

### 寫 `build.sh` 的契約

build.sh 拿到的環境變數：

| 變數 | 內容 |
|---|---|
| `PACKAGE_DIR` | 自己 package 的絕對路徑（如 `/Users/.../gendoc/tools/myalign/`）|
| `BIN_DIR` | 部署目標的絕對路徑（如 `/Users/.../gendoc/tools/bin`）|

範例（壓縮 + 加 build header）：

```bash
#!/usr/bin/env bash
# tools/myalign/build.sh
set -e
echo "  [myalign] building..."
{
  echo "# Auto-built $(date -u +%Y-%m-%dT%H:%M:%SZ) — do not edit"
  python3 -c "
import re, sys
src = open('$PACKAGE_DIR/myalign.py').read()
# 範例：剝掉 inline test 區塊
src = re.sub(r'^# === inline tests ===.*\$', '', src, flags=re.S | re.M)
sys.stdout.write(src)
"
} > "$BIN_DIR/myalign.py"
chmod +x "$BIN_DIR/myalign.py"
echo "  [myalign] wrote $BIN_DIR/myalign.py"
```

需求：build.sh 自己**負責把 artifact 寫進 `$BIN_DIR/`**；setup 不會幫你 cp。
exit code 非 0 視為失敗，整個 setup 中止。

### Windows: `build.ps1`

如有（優先用 `build.ps1`），同 contract（環境變數一樣）。
若只有 `build.sh` 而 user 機器有 `bash`（Git Bash / WSL），setup.ps1
會用 bash 執行 `build.sh`。

### 加一個新 package（不需 build）

例：`tools/myalign/myalign.py`，單檔 Python script

1. 建 `tools/myalign/myalign.py` + `tools/myalign/tests/test_*.py` + `pytest.ini`
2. **不用** 改 `setup` — 自動掃 `tools/*/` 並按 convention 套 cp
3. 改對應 skill（`skills/gendoc-myalign/SKILL.md`）讓它呼叫 `bin/myalign.py`
4. commit + push
5. user `./setup upgrade`

### 加一個新 package（需 build）

例：`tools/mybundler/` 多檔合成單一 bundled output

1. 建 `tools/mybundler/` 目錄，含若干 `.py` 模組 + tests
2. 寫 `tools/mybundler/build.sh`（或 `build.ps1`），把所需檔合成
   `$BIN_DIR/mybundler.py`（或任意名稱）
3. **不用** 改 `setup` — 自動偵測 `build.sh` 並執行
4. 改對應 skill 呼叫 `bin/mybundler.py`
5. commit + push
6. user `./setup upgrade`

---

## 重要邊界（絕對不可打破）

1. **不要直接改 `~/.claude/skills/gendoc/`** — PreToolUse hook 會擋
2. **`tools/bin/` 是部署產物** — 只能由 `setup` 寫，git 不必 commit `bin/<entry>.py` 是否最新（remote checkout 後 setup 會覆蓋）
3. **修改流程必須 commit + push 才生效** — SessionStart hook `git pull` 後才會 deploy 最新版
4. **目標專案只呼叫 `~/.claude/skills/gendoc/tools/bin/`** — 不讀 `~/projects/gendoc/tools/<package>/`，目標專案不依賴作者本機

詳見 [CLAUDE.md](../CLAUDE.md) §架構原則。

