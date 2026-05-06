---
name: gendoc-refresh-docs
description: |
  讀取近期 git log，將最新專案狀態更新至 README.md，
  若 docs/PRD.md 存在則自動遞增版本並補寫 changelog 條目，
  最後重建 docs/pages/index.html + prd.html（呼叫 gen_html.py）。
  專為 gendoc 本身的文件維護設計；不依賴 .gendoc-state.json。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Skill
---

# gendoc-refresh-docs — 更新專案文件現況

讀取 git 近期變更 → 更新 README.md → 更新 docs/PRD.md（選用）→ 重建 HTML。

> 此 skill 只維護 **gendoc 專案本身**的說明文件，不操作目標應用專案。  
> 不依賴 `.gendoc-state.json`；無需 gendoc-config 前置。

---

## Step 0：環境初始化

```bash
source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

_CWD="$(pwd)"
echo "CWD：$_CWD"
echo "GENDOC_TOOLS：$GENDOC_TOOLS"

# 偵測 docs/PRD.md
_HAS_PRD=0
[[ -f "${_CWD}/docs/PRD.md" ]] && _HAS_PRD=1
echo "docs/PRD.md：$( [[ $_HAS_PRD == 1 ]] && echo '存在，納入更新範圍' || echo '不存在，略過')"

# 確認 gen_html.py 可用
if [[ ! -f "$GENDOC_TOOLS/gen_html.py" ]]; then
  echo "❌ 找不到 $GENDOC_TOOLS/gen_html.py"
  echo "   請執行 /gendoc-upgrade 安裝最新版本"
  exit 1
fi
```

---

## Step 1：收集近期變更摘要

```bash
# 取上次 README 或 PRD 有 commit 以來的 git log；若找不到則取最近 20 筆
_LAST_DOC_HASH=$(git log --oneline --follow -- README.md docs/PRD.md 2>/dev/null | head -1 | awk '{print $1}')
if [[ -n "$_LAST_DOC_HASH" ]]; then
  echo "=== git log since last doc commit（${_LAST_DOC_HASH}） ==="
  git log --oneline "${_LAST_DOC_HASH}..HEAD" 2>/dev/null
else
  echo "=== git log（最近 20 筆） ==="
  git log --oneline -20
fi

echo ""
echo "=== 已修改的檔案（近期） ==="
git diff --name-only "${_LAST_DOC_HASH:-HEAD~10}..HEAD" 2>/dev/null | sort | uniq
```

**[AI 指令]** 閱讀上方 git log 與修改清單，在記憶體中整理本次需要寫進文件的重點變更。後續 Step 2 / Step 3 均以此為依據，不再重複執行 git 指令。

---

## Step 2：更新 README.md

**[AI 指令]**

1. 用 Read 工具讀取 `README.md`（全文）
2. 根據 Step 1 收集的變更，**外科手術式修改**受影響的段落：
   - 若新增 skill → 在 Skills 表格新增一列
   - 若修改 `tools/bin/` 工具 → 更新 Repository Structure 對應行
   - 若修改設計原則 → 更新 Design Principles 對應段落
   - 若版本號/功能描述過時 → 就地修正
   - **其他段落不動**，保持現有內容
3. 用 Edit 工具逐段修改（不整體 Write 覆蓋，避免意外遺失內容）
4. 完成後輸出修改摘要（改了哪幾行/哪幾個段落）

---

## Step 3：更新 docs/PRD.md（條件：`_HAS_PRD=1`）

若 `_HAS_PRD=0` → 跳過本 Step，輸出 `[Skip] docs/PRD.md 不存在`。

### Step 3-A：讀取目前版本號

```bash
python3 - << 'PYEOF'
import re, pathlib

prd = pathlib.Path("docs/PRD.md").read_text(encoding="utf-8")

# 從 frontmatter 或 Document Control 表格讀取版本
m = re.search(r'Version:\s*(v[\d.]+)', prd)
if not m:
    m = re.search(r'\*\*文件版本\*\*\s*\|\s*(v[\d.]+)', prd)
if not m:
    m = re.search(r'<!--\s*Version:\s*(v[\d.]+)', prd)

if m:
    ver = m.group(1)          # e.g. "v4.0"
    parts = ver.lstrip('v').split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    next_ver = 'v' + '.'.join(parts)
    print(f"CURRENT_VERSION={ver}")
    print(f"NEXT_VERSION={next_ver}")
else:
    print("CURRENT_VERSION=unknown")
    print("NEXT_VERSION=unknown")
PYEOF
```

### Step 3-B：讀取目前文件

**[AI 指令]** 用 Read 工具讀取 `docs/PRD.md`（全文）。

### Step 3-C：寫入新 changelog 條目

**[AI 指令]**

1. 以 Step 3-A 的 `NEXT_VERSION` 為新版本號（若為 `unknown`，在 Change Log 表格最上方補一列並標注 `vX.Y`）
2. 在 Change Log 表格**最上方**插入新行：

   ```
   | <NEXT_VERSION> | 2026-MM-DD | PM Agent | <根據 Step 1 變更摘要，用繁體中文撰寫> |
   ```

3. 同步更新 frontmatter `<!-- Version: <NEXT_VERSION> ... -->` 和 Document Control 表格中的版本號與日期
4. 用 Edit 工具執行修改（精確替換，不整體覆蓋）

---

## Step 4：重建 HTML（選擇性）

```bash
source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"
python3 "$GENDOC_TOOLS/gen_html.py" 2>&1

# 驗證關鍵頁面
_FAIL=0
for _F in docs/pages/index.html docs/pages/prd.html; do
  if [[ -f "$_F" ]]; then
    echo "[OK] $_F（$(stat -f%z "$_F" 2>/dev/null || stat -c%s "$_F") bytes）"
  else
    echo "[SKIP] $_F 不存在（無對應 .md 來源）"
  fi
done
```

---

## Step 5：git commit

```bash
source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

# Stage 只加本 skill 範圍的檔案
git add README.md docs/PRD.md docs/pages/index.html docs/pages/prd.html docs/pages/search-data.json 2>/dev/null

_STAGED=$(git diff --cached --name-only | tr '\n' ' ')
if [[ -z "$_STAGED" ]]; then
  echo "[Skip] 無檔案異動，不建立 commit"
  exit 0
fi

echo "Staged：$_STAGED"
```

**[AI 指令]** 根據本次實際修改內容，用以下格式建立 commit（透過 Bash 工具執行 git commit）：

```
docs(readme, prd): <一行摘要>

- README: <改了什麼>
- PRD: <新增版本號> — <變更摘要>
- HTML: 重建 index.html + prd.html
```

---

## Step 6：輸出摘要

```
╔══════════════════════════════════════════════════════════╗
║  gendoc-refresh-docs 完成                                ║
╠══════════════════════════════════════════════════════════╣
║  README.md    ：已更新（<N> 個段落修改）                  ║
║  docs/PRD.md  ：<已更新至 vX.Y | 略過（不存在）>          ║
║  HTML 重建    ：index.html + prd.html                     ║
║  Commit       ：<hash>                                    ║
╚══════════════════════════════════════════════════════════╝

下一步（選擇性）：
  git push origin main   ← 推送到 remote
  gh workflow run deploy ← 若有 CI/CD 流程
```
