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
       └── cp tools/<package>/<entry>.py → tools/bin/<entry>.py
5. ~/.claude/skills/gendoc/tools/bin/<entry>.py 變新版
```

對應 `setup` 內部：

```bash
# setup line 118-133 (bash) / setup.ps1 line 51-64 (powershell)
_deploy_tools() {
  log "[deploy] 部署 tools/<package>/ 源碼至 $RUNTIME_DIR/tools/bin/"
  if [[ -f "$RUNTIME_DIR/tools/dryrun_core/dryrun_core.py" ]]; then
    cp "$RUNTIME_DIR/tools/dryrun_core/dryrun_core.py" "$RUNTIME_DIR/tools/bin/dryrun_core.py"
  fi
  if [[ -f "$RUNTIME_DIR/tools/gen_html/gen_html.py" ]]; then
    cp "$RUNTIME_DIR/tools/gen_html/gen_html.py" "$RUNTIME_DIR/tools/bin/gen_html.py"
  fi
}
```

### 加一個新 package（例：`tools/myalign/myalign.py`）

1. 建 `tools/myalign/myalign.py` + `tools/myalign/tests/test_*.py` + `pytest.ini`
2. 改 `setup`（bash + ps1）的 `_deploy_tools()`：

   ```bash
   if [[ -f "$RUNTIME_DIR/tools/myalign/myalign.py" ]]; then
     cp "$RUNTIME_DIR/tools/myalign/myalign.py" "$RUNTIME_DIR/tools/bin/myalign.py"
   fi
   ```

3. 改對應 skill（`skills/gendoc-myalign/SKILL.md`）讓它呼叫 `bin/myalign.py`
4. commit + push
5. user `./setup upgrade`

---

## 重要邊界（絕對不可打破）

1. **不要直接改 `~/.claude/skills/gendoc/`** — PreToolUse hook 會擋
2. **`tools/bin/` 是部署產物** — 只能由 `setup` 寫，git 不必 commit `bin/<entry>.py` 是否最新（remote checkout 後 setup 會覆蓋）
3. **修改流程必須 commit + push 才生效** — SessionStart hook `git pull` 後才會 deploy 最新版
4. **目標專案只呼叫 `~/.claude/skills/gendoc/tools/bin/`** — 不讀 `~/projects/gendoc/tools/<package>/`，目標專案不依賴作者本機

詳見 [CLAUDE.md](../CLAUDE.md) §架構原則。
