# gendoc 架構違規清查報告

> 審查日期：2026-05-01  
> 原則來源：CLAUDE.md  
> 狀態：待 owner 決策，所有修改暫緩

---

## Principle 2 違規：install 讀取本地，而非只從 remote 拉

> 原則：install / setup / update 只從 remote (GitHub) 拉，不讀本地 `~/projects/gendoc/`

| # | 檔案 | 位置 | 違規內容 | 建議的改法 | 決策 |
|---|------|------|---------|-----------|------|
| P2-1 | `install.sh` | L6–38 | `GENDOC_DIR="$(dirname "$0")"` 後 `cp -r "$SKILLS_SRC/"` → `~/.claude/`，直接讀本地 working tree | 改為從 remote 下載 tarball（`gh release download` 或 `curl` GitHub raw），不依賴本地目錄 | |
| P2-2 | `install.py` | L9–31 | `GENDOC_DIR = os.path.dirname(__file__)` 後複製本地 skills/ templates/ bin/，Windows 版同上 | 同 P2-1，改為從 remote 抓 tarball，或由 install.sh 呼叫後廢棄此檔 | |
| P2-3 | `bin/gendoc-upgrade` | L8–9 | `git pull` 後立即 `bash "$GENDOC_DIR/install.sh"`；即使已 pull，install 步驟仍讀本地 | git pull 後直接以 rsync/cp 從已更新的本地 working tree 安裝，或改為在 pull 後只呼叫已安裝至 ~/.claude/gendoc/bin/ 的腳本本身 | |
| P2-4 | `bin/gendoc-session-update` | L30–31 | 同 P2-3，git pull 後 `bash "$GENDOC_DIR/install.sh"` | 同 P2-3 | |
| P2-5 | `bin/_gendoc-update-worker.py` | L13–18 | git pull 後呼叫本地 `install.py` 或 `install.sh` | 同 P2-3 | |
| P2-6 | `skills/gendoc-rebuild-templates/SKILL.md` | Step 6, L343–347 | 步驟明確寫 `./install.sh`，假設 CWD 是 gendoc dev 目錄 | Step 6 改為呼叫 `/gendoc-update` skill，不直接執行 install.sh | |
| P2-7 | `skills/reviewtemplate/SKILL.md` | L373 | 建議 `執行 ./install.sh 同步到 ~/.claude/skills/` | 同 P2-6，改為告知執行 `/gendoc-update` | |

---

## Principle 3 違規：Runtime 引用 `~/projects/gendoc/` 路徑

> 原則：`~/.claude/` 安裝後自給自足，runtime 不引用 `~/projects/gendoc/` 任何路徑

| # | 檔案 | 位置 | 違規內容 | 建議的改法 | 決策 |
|---|------|------|---------|-----------|------|
| P3-1 | `setup` | L12–46 | `HOOK_BASH="$SCRIPT_DIR/bin/gendoc-session-update"` 寫入 `~/.claude/settings.json`，runtime 永久鎖定本地路徑 | SessionStart hook 應指向 `~/.claude/gendoc/bin/gendoc-session-update`（runtime 路徑），setup 在安裝後寫入 runtime 路徑，而非 dev 路徑 | |
| P3-2 | `setup.ps1` | L15–44 | 同上 Windows 版，`$HookPy = "$ScriptDir\bin\gendoc-session-update.py"` 寫入 settings.json | 同 P3-1 | |
| P3-3 | `skills/gendoc-auto/SKILL.md` | Step -1, L53–63 | `_GENDOC_REPO="$HOME/projects/gendoc"`，呼叫 `bash "$_GENDOC_REPO/bin/gendoc-upgrade"` | 改為 `~/.claude/gendoc/bin/gendoc-upgrade`（runtime 路徑），或改為呼叫 `/gendoc-update` skill | |
| P3-4 | `skills/gendoc-flow/SKILL.md` | Step -1, L80–90 | 同 P3-3，完全相同的 Fix-D 模式 | 同 P3-3 | |
| P3-5 | `skills/gendoc-repair/SKILL.md` | Step -1, L33–43 | 同 P3-3，完全相同的 Fix-D 模式 | 同 P3-3 | |
| P3-6 | `skills/gendoc-update/SKILL.md` | L20–35 | `for _c in "$HOME/projects/gendoc"` 搜尋本地 repo，再 `bash "$_REPO/bin/gendoc-upgrade"` | 此 skill 本身就是「更新工具」，應直接呼叫 `~/.claude/gendoc/bin/gendoc-upgrade`，不需要先找 dev repo | |
| P3-7 | `skills/reviewdoc/SKILL.md` | L35 | `for _c in "$HOME/projects/gendoc"` — runtime skill 直接掃本地 gendoc 路徑 | 同 P3-6，改為直接呼叫 runtime 路徑的 gendoc-upgrade | |
| P3-8 | `skills/gendoc-shared/SKILL.md` | L21–22 | 說明文字寫 `cd ~/projects/gendoc && ./bin/gendoc-upgrade` 和 `cd ~/projects/gendoc && ./setup` | 將說明文字改為指向 `~/.claude/gendoc/bin/gendoc-upgrade`；setup 說明移至 README.md 中的「開發者安裝」章節 | |

---

## Principle 4 違規：目標專案邊界被穿越

> 原則：目標專案執行 skill 時，只呼叫 `~/.claude/gendoc/bin/`，不讀 `~/projects/gendoc/`

| # | 檔案 | 位置 | 違規內容 | 建議的改法 | 決策 |
|---|------|------|---------|-----------|------|
| P4-1 | `skills/gendoc-auto/SKILL.md` | Step -1 | 從 keyvault 等目標專案執行時，呼叫 `$HOME/projects/gendoc/bin/gendoc-upgrade`，穿越至 dev 目錄 | 與 P3-3 同步修正；upgrade 邏輯移至 `~/.claude/gendoc/bin/gendoc-upgrade` | |
| P4-2 | `skills/gendoc-flow/SKILL.md` | Step -1 | 同 P4-1 | 同 P3-4 | |
| P4-3 | `skills/gendoc-repair/SKILL.md` | Step -1 | 同 P4-1 | 同 P3-5 | |

---

## 設計問題（非嚴格違規，但需注意）

| # | 檔案 | 位置 | 說明 | 建議的改法 | 決策 |
|---|------|------|------|-----------|------|
| D1 | `skills/gendoc/SKILL.md` | L108–111 | local-first 路徑：先找 `$_CWD/templates/pipeline.json`，再找 `~/.claude/gendoc/templates/`。從 gendoc dev 目錄執行時讀本地，可能與 runtime 版本不同步 | 移除 local-first fallback；永遠讀 `~/.claude/gendoc/templates/pipeline.json`。開發者若要測試新 template，走 install 流程 | |
| D2 | `docs/pages/gen_html.py` | — | VERSION 3.0.0 舊版 gen_html.py 留在 gendoc 自己的 docs/pages/ 下；上個 session 的 bug 根源（目標專案誤用此版本） | 刪除此檔；gendoc 專案的 HTML 文件應由 runtime `~/.claude/gendoc/bin/gen_html.py` 生成，不應在 repo 內留存舊版 | |

---

## 統計摘要

| 類別 | 數量 |
|------|------|
| Principle 2 違規 | 7 |
| Principle 3 違規 | 8 |
| Principle 4 違規 | 3（與 P3 部分重疊） |
| 設計問題 | 2 |
| **合計** | **20** |

---

## 決策說明（供填寫）

請在「決策」欄填入：
- `accept` — 接受建議的改法
- `reject` — 不修改，保留現狀（請說明原因）
- `modify: <說明>` — 採用不同的改法
- `defer` — 暫緩，列入 backlog
