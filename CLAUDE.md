# gendoc 專案 — Claude Code 必讀原則

## Session 開始時必須執行

每次進入此專案的 session，**必須立即執行**：

將以下原則寫入 memory（`~/.claude/projects/-Users-tobala-projects-gendoc/memory/project_gendoc_architecture_principles.md`）：
- Remote-first 分發原則
- Runtime 完全獨立原則
- 目標專案邊界原則
- 修改流程（edit → commit → push 才能生效）
- 禁止直接修改 runtime
- 任何動作前必須先告知使用者

---

## 架構原則

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
- **不得讀取**本地 `~/projects/gendoc/` 的任何內容來安裝
- 本地 gendoc 專案目錄不能是任何人 runtime 的依賴

### 3. Runtime 完全獨立
`~/.claude/` 安裝完後自給自足：
- `~/.claude/skills/` — skill 指令
- `~/.claude/gendoc/bin/` — 執行腳本
- `~/.claude/gendoc/templates/` — 模板

Runtime 不依賴、不引用 `~/projects/gendoc/` 的任何路徑。

### 4. 目標專案邊界
任何目標專案執行 skill 時：
- 只呼叫 `~/.claude/gendoc/bin/gen_html.py`
- **不讀** `~/projects/gendoc/` 的任何內容
- **不讀**目標專案自己目錄下的任何同名腳本

### 5. 修改流程（必須依序）
```
1. 修改 ~/projects/gendoc/skills/ 或 bin/
2. commit
3. push 到 remote        ← 不做這步，修改永遠不會生效
4. 告知使用者 run update  ← 不要自己跑
```
禁止跳過 push 直接 install，否則 SessionStart hook git pull 後會覆蓋回舊版。

### 6. 禁止直接修改 Runtime
永遠不得直接 Edit/Write `~/.claude/skills/` 或 `~/.claude/gendoc/`。
PreToolUse hook 已封鎖此行為。

### 7. 任何動作前必須問
改完告訴使用者，讓使用者決定下一步。不得自行 push、install、upgrade。

---

## 這個工具是給所有人用的

gendoc 的目標是讓任何人 clone + setup 後就能用，不依賴作者本機的任何狀態。
任何只在作者本機生效的修改都是錯的。
