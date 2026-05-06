---
name: gendoc-refresh-docs
description: |
  掃描目前目錄實況 + 讀取 Claude memory（project/reference 類型）+ git log，
  與現有 README.md / docs/PRD.md 比對，找出過時或遺漏的內容並修正，
  再將使用者 args（若有）優化後整合進去，最後選擇性重建 HTML。
  適用任意目錄；不假設固定結構；根據 README/PRD 是否存在自動路由。
  支援 args：/gendoc-refresh-docs <文字> 提供本次想補記的內容。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Skill
---

# gendoc-refresh-docs — 更新專案文件現況

掃描實況 → 讀 memory → 比對文件 → 修正差異 → 整合 args → 重建 HTML（選擇性）。

> 不依賴固定目錄結構。空目錄、只有 PRD、只有 README 均可正常執行。

---

## 使用方式

```
# 無 args：自動分析現況，AI 推導需要更新的內容
/gendoc-refresh-docs

# 有 args：使用者直接提供本次想補的內容（優先整合，不覆蓋 AI 發現的差異）
/gendoc-refresh-docs 新增 gendoc-refresh-docs skill，支援任意目錄、memory 整合
/gendoc-refresh-docs 修復 Windows hook 路徑問題，gendoc-guard 改用靜態 .py 腳本
```

args 可以是粗糙關鍵字或完整描述；AI 會根據現況補全細節後整合進文件。

---

## Step 0：環境偵測 + Args 讀取

### Step 0-A：基本環境

```bash
source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh" 2>/dev/null || true

_CWD="$(pwd)"
echo "CWD：$_CWD"

# README / PRD 存在性
_HAS_README=0; _HAS_PRD=0
[[ -f "README.md"      ]] && _HAS_README=1
[[ -f "docs/PRD.md"    ]] && _HAS_PRD=1
echo "README.md    ：$( [[ $_HAS_README == 1 ]] && echo '存在' || echo '不存在')"
echo "docs/PRD.md  ：$( [[ $_HAS_PRD    == 1 ]] && echo '存在，納入更新範圍' || echo '不存在，略過')"

# Git repo 偵測
_IS_GIT=0
git rev-parse --git-dir &>/dev/null && _IS_GIT=1
echo "Git repo     ：$( [[ $_IS_GIT == 1 ]] && echo '是' || echo '否')"

# HTML 重建可用性
_CAN_HTML=0
[[ -d "docs/pages" && -f "$GENDOC_TOOLS/gen_html.py" ]] && _CAN_HTML=1
echo "HTML 重建    ：$( [[ $_CAN_HTML == 1 ]] && echo '可用（docs/pages/ + gen_html.py）' || echo '略過（條件不符）')"
```

### Step 0-B：路由模式

依 `_HAS_README` / `_HAS_PRD` 決定後續執行路徑：

| README | PRD | 模式 |
|--------|-----|------|
| ✓ | ✓ | **A** — 更新 README + 更新 PRD changelog |
| ✓ | ✗ | **B** — 只更新 README |
| ✗ | ✓ | **C** — 從 PRD 建立 README + 更新 PRD |
| ✗ | ✗ | **D** — 從 memory / git / args 建立 README |

輸出：`[模式] <A|B|C|D> — <說明>`

### Step 0-C：讀取 Args（`_USER_CONTEXT`）

**[AI 指令]** 檢查 Skill tool 傳入的 `args` 值：
- **有 args** → `_USER_CONTEXT = args`，輸出 `[Args] 「<內容>」`
- **無 args** → `_USER_CONTEXT = ""`，輸出 `[Args] 無輸入`

`_USER_CONTEXT` 在整個 skill 執行期間保持不變。

---

## Step 1：目錄掃描（地面實況）

```bash
echo "=== 頂層檔案 ==="
ls -la | grep -v "^total"

echo ""
echo "=== Markdown 檔案（排除 node_modules / .git） ==="
find . -name "*.md" \
  ! -path "./node_modules/*" \
  ! -path "./.git/*" \
  ! -path "./docs/pages/*" \
  | sort

echo ""
echo "=== docs/ 結構（若存在） ==="
find docs -maxdepth 2 ! -path "*/pages/*" 2>/dev/null | sort || echo "（docs/ 不存在）"
```

**[AI 指令]** 閱讀掃描結果，在記憶體中建立「實際存在的檔案清單」。這是後續比對的基準，所有文件描述都要與此對照。

---

## Step 2：讀取現有文件

**[AI 指令]** 依模式讀取：

- **模式 A / B**：用 Read 工具讀取 `README.md`（全文）
- **模式 A / C**：用 Read 工具讀取 `docs/PRD.md`（全文）
- **模式 D**：兩者都不存在，跳過

讀完後記住：README 目前寫了什麼、PRD 的版本號和最後 changelog 條目是什麼。

---

## Step 3：讀取 Claude Memory（project + reference 類型）

```bash
# 推導 memory 目錄路徑
python3 - << 'PYEOF'
import os, pathlib, sys

cwd = os.getcwd()
encoded = cwd.replace('/', '-')        # /foo/bar → -foo-bar
mem_dir = pathlib.Path.home() / '.claude' / 'projects' / encoded / 'memory'
mem_idx  = mem_dir / 'MEMORY.md'

if not mem_dir.exists():
    print(f"MEMORY_DIR_EXISTS=0")
    print(f"MEMORY_DIR={mem_dir}")
    sys.exit(0)

print(f"MEMORY_DIR_EXISTS=1")
print(f"MEMORY_DIR={mem_dir}")

if not mem_idx.exists():
    print("MEMORY_INDEX=none")
    sys.exit(0)

# 列出 index 中的連結
import re
links = re.findall(r'\[.*?\]\((.+?\.md)\)', mem_idx.read_text(encoding='utf-8'))
print(f"MEMORY_FILES={' '.join(links)}")
PYEOF
```

**[AI 指令]**

若 `MEMORY_DIR_EXISTS=0` → 輸出 `[Memory] 無 memory 目錄，略過`，直接進 Step 4。

若 `MEMORY_DIR_EXISTS=1`：
1. 用 Read 工具讀取 `MEMORY_DIR/MEMORY.md`（index）
2. 對 index 中列出的每個 `.md` 連結，用 Read 工具讀取該檔案的**前 10 行**（取 frontmatter 的 `type:` 欄位）
3. **只讀 `type: project` 和 `type: reference` 的檔案全文**
4. **跳過 `type: feedback` 和 `type: user` 的檔案**（這些是操作規範，不寫進文件）
5. 在記憶體中整理出 memory 提供的專案背景知識

輸出：`[Memory] 已讀取 N 個 project/reference 條目，略過 M 個 feedback/user 條目`

---

## Step 4：讀取 Git Log（若 `_IS_GIT=1`）

```bash
if [[ "$_IS_GIT" == "1" ]]; then
  # 取上次 README 或 PRD commit 以來的 log；若無則取最近 15 筆
  _LAST_DOC_HASH=$(git log --oneline -- README.md docs/PRD.md 2>/dev/null | head -1 | awk '{print $1}')
  if [[ -n "$_LAST_DOC_HASH" ]]; then
    echo "=== git log since last doc commit（$_LAST_DOC_HASH） ==="
    git log --oneline "${_LAST_DOC_HASH}..HEAD" 2>/dev/null
  else
    echo "=== git log（最近 15 筆） ==="
    git log --oneline -15
  fi
else
  echo "[Git] 非 git repo，略過 git log"
fi
```

---

## Step 5：差異分析（AI 核心任務）

**[AI 指令]** 綜合 Steps 1–4 的所有資訊，產出三份清單（輸出至終端，不寫入任何檔案）：

**差異清單 A — 「文件描述了但實際不存在」（過時）**
> 例：README 說有 `/gendoc-X` 但 skills/ 目錄沒有；PRD changelog 提到某功能但 git log 找不到對應 commit

**差異清單 B — 「實際存在但文件未提及」（遺漏）**
> 例：tools/bin/ 有新腳本但 README 未列；memory 記錄了某決策但 PRD 未反映；git log 有重要 commit 但文件隻字未提

**差異清單 C — 「使用者 args 要補記的內容」（`_USER_CONTEXT` 非空時）**
> 將 `_USER_CONTEXT` 拆解成具體要更新的點

若所有清單均為空 → 輸出 `[分析] 文件與現況一致，無需更新` 並詢問使用者是否仍要繼續。

---

## Step 6：確認後執行更新

**[AI 指令]** 輸出差異摘要（一行一條），然後在 `_EXEC_MODE` 為 `interactive` 時詢問確認；`full-auto` 或未設定時直接執行。

```
[待更新]
  過時：<N 條>
  遺漏：<M 條>
  Args：<K 條>
→ 繼續更新？[Y/n]（full-auto 自動 Y）
```

確認後依模式執行：

### 模式 A / B — 更新 README.md

**[AI 指令]** 用 Read 工具確認 README.md 最新內容，再用 Edit 工具逐段修改：
- 修正差異清單 A 的過時描述（刪除或更正）
- 補入差異清單 B 的遺漏內容（插入適當段落）
- 若有 `_USER_CONTEXT`，優化後整合進對應段落
- 其他段落不動

每個 Edit 後立即 `grep` 確認關鍵字存在，失敗時明確輸出警告（不靜默跳過）。

### 模式 A / C — 更新 docs/PRD.md changelog

```bash
# 讀取並遞增版本號
python3 - << 'PYEOF'
import re, pathlib

prd = pathlib.Path("docs/PRD.md").read_text(encoding="utf-8")
for pat in [r'<!--\s*Version:\s*(v[\d.]+)', r'\*\*文件版本\*\*\s*\|\s*(v[\d.]+)']:
    m = re.search(pat, prd)
    if m:
        ver = m.group(1)
        parts = ver.lstrip('v').split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        print(f"CURRENT={ver}")
        print(f"NEXT=v{'.'.join(parts)}")
        break
else:
    print("CURRENT=unknown")
    print("NEXT=unknown")
PYEOF
```

**[AI 指令]** 在 PRD Change Log 表格**最上方**插入新行，內容以差異清單 B + `_USER_CONTEXT` 為主；更新 frontmatter 版本號與日期；用 Edit 工具精確替換（不整體覆蓋）。

### 模式 C / D — 建立 README.md

**[AI 指令]** 若 README.md 不存在，依 PRD 內容（模式 C）或 memory / git / args（模式 D）用 Write 工具建立標準 README.md，包含：專案簡介、功能列表、安裝方式、使用方式（有資料就寫，無資料的段落標 `TBD`）。

---

## Step 7：Gate Check

```bash
# README gate：必須非空且 > 500 bytes
if [[ -f "README.md" ]]; then
  _SZ=$(stat -f%z "README.md" 2>/dev/null || stat -c%s "README.md")
  [[ "$_SZ" -gt 500 ]] && echo "[OK] README.md（$_SZ bytes）" \
                        || echo "[WARN] README.md 過小（$_SZ bytes），請確認內容"
fi

# PRD gate（若有更新）
if [[ "$_HAS_PRD" == "1" ]]; then
  _SZ=$(stat -f%z "docs/PRD.md" 2>/dev/null || stat -c%s "docs/PRD.md")
  [[ "$_SZ" -gt 1000 ]] && echo "[OK] docs/PRD.md（$_SZ bytes）" \
                          || echo "[WARN] docs/PRD.md 過小（$_SZ bytes），請確認內容"
fi
```

---

## Step 8：HTML 重建（條件：`_CAN_HTML=1`）

```bash
if [[ "$_CAN_HTML" == "1" ]]; then
  source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"
  python3 "$GENDOC_TOOLS/gen_html.py" 2>&1

  # 驗證關鍵頁面 > 5KB
  for _F in docs/pages/index.html docs/pages/prd.html; do
    [[ ! -f "$_F" ]] && continue
    _SZ=$(stat -f%z "$_F" 2>/dev/null || stat -c%s "$_F")
    [[ "$_SZ" -gt 5120 ]] && echo "[OK] $_F（$_SZ bytes）" \
                           || echo "[WARN] $_F 過小（$_SZ bytes），可能為空頁面"
  done
else
  echo "[Skip] HTML 重建條件不符（docs/pages/ 不存在或 gen_html.py 不可用）"
fi
```

---

## Step 9：Git Commit（條件：`_IS_GIT=1`）

```bash
if [[ "$_IS_GIT" == "1" ]]; then
  git add README.md docs/PRD.md \
    docs/pages/index.html docs/pages/prd.html \
    docs/pages/search-data.json 2>/dev/null

  _STAGED=$(git diff --cached --name-only | tr '\n' ' ')
  if [[ -z "$_STAGED" ]]; then
    echo "[Skip] 無檔案異動，不建立 commit"
  else
    echo "Staged：$_STAGED"
  fi
fi
```

**[AI 指令]** 若有 staged 檔案，建立 commit（格式如下）；若非 git repo 則略過：

```
docs(readme[, prd]): <一行摘要>

- README: <修正了什麼 / 補了什麼>
- PRD: <新版本號> — <changelog 摘要>（若有更新）
- HTML: 重建 index.html + prd.html（若有執行）
```

---

## Step 10：輸出摘要

```
╔═══════════════════════════════════════════════════╗
║  gendoc-refresh-docs 完成                         ║
╠═══════════════════════════════════════════════════╣
║  模式      ：<A|B|C|D>                            ║
║  README    ：<已更新 N 處 | 已建立 | 未變動>       ║
║  PRD       ：<已更新至 vX.Y | 略過>               ║
║  Memory    ：已整合 N 個 project/reference 條目   ║
║  HTML      ：<已重建 | 略過>                      ║
║  Commit    ：<hash | 略過（非 git repo）>          ║
╚═══════════════════════════════════════════════════╝
```
