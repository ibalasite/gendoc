# gendoc Agent Guidelines

## Session 開始時的必要動作

每次進入 gendoc 專案的 session，**必須立即執行**：

1. 讀取本檔案（`AGENTS.md`）
2. 將以下原則寫入 memory（路徑：`~/.claude/projects/-Users-tobala-projects-gendoc/memory/project_gendoc_architecture_principles.md`），確保下次 session 也能載入：
   - Remote-first 分發原則
   - Runtime 完全獨立原則
   - 目標專案邊界原則
   - 修改流程（edit → commit → push，才能生效）
   - 禁止直接修改 runtime

這個動作確保原則在任何 session、任何 agent 下都不會被遺忘。

---

## 架構原則（任何 AI agent 必須遵守）

### 1. Single Source of Truth
`~/projects/gendoc/`（git repo）是唯一真相來源。所有修改只在這裡發生，commit 後 push 到 remote。

### 2. 分發路徑：只從 remote，不讀本地
```
~/projects/gendoc/ → push → remote (GitHub)
                                ↓
                         install / setup / update
                                ↓
                          ~/.claude/（runtime）
```
- install、setup、update **只從 remote 拉**
- **不得讀取** 本地 `~/projects/gendoc/` 的任何內容來安裝
- 本地 gendoc 專案目錄不能是任何人 runtime 的依賴

### 3. Runtime 完全獨立
安裝完成後，`~/.claude/` 自給自足：
- `~/.claude/skills/` — skill 指令
- `~/.claude/gendoc/bin/` — 執行腳本（如 gen_html.py）
- `~/.claude/gendoc/templates/` — 模板

Runtime 不依賴、不引用 `~/projects/gendoc/` 的任何路徑。

### 4. 目標專案邊界
任何目標專案（keyvault、stock_monitor 等）執行 skill 時：
- 只呼叫 `~/.claude/gendoc/bin/gen_html.py`
- **不讀** `~/projects/gendoc/` 的任何內容
- **不讀** 目標專案自己目錄下的任何同名腳本（如 `docs/pages/gen_html.py`）

### 5. 修改流程
```
1. 修改 ~/projects/gendoc/skills/ 或 bin/
2. commit
3. push 到 remote
4. 使用者 run install/setup/update → 從 remote 取得
```
**禁止跳過 push 直接 install**，否則只有本機暫時生效，SessionStart hook git pull 後會被覆蓋回舊版。

### 6. 禁止直接修改 Runtime
永遠不得直接 Edit/Write `~/.claude/skills/` 或 `~/.claude/gendoc/`。
PreToolUse hook 已封鎖此行為。

---

## 這個工具是給所有人用的

gendoc 的目標是讓任何人 clone + setup 後就能用，不依賴作者本機的任何狀態。
任何修改如果只在作者本機生效，就是錯的。
