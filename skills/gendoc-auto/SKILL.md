---
name: gendoc-auto
description: 任意輸入→IDEA.md+BRD→移交 gendoc-flow — 支援 idea/圖片/文件/URL/codebase/git 輸入，素材保存至 docs/req/（唯讀原則），生成 IDEA.md + BRD，再由 gendoc-flow 接手純文件生成流水線
version: 2.1.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - WebFetch
  - WebSearch
  - Skill
  - Agent
---

# gendoc-auto — 任意輸入 → IDEA.md + BRD.md → 移交 gendoc-flow

```
Input:   IDEA text / Image URL / Document (URL/git/local) / Codebase (git/local)
Output:  docs/IDEA.md + docs/BRD.md → 移交 gendoc-flow
Steps:   PRE-1~PRE-4 → Q → R → IDEA → IDEA-Review → BRD → BRD-Review → Handoff
Experts: PM / UX / System Architect / Backend / QA / Domain
Scope:   僅負責 D01-IDEA + D02-BRD；其餘文件由 gendoc-flow 接手
```

**使用路徑選擇：**

| 情境 | 使用方式 |
|------|---------|
| 從 Idea 出發（無任何文件） | `/gendoc-auto` → 自動 handoff 到 gendoc-flow |
| 已有 BRD.md，直接從 PRD 開始 | 跳過此 skill，直接呼叫 `/gendoc-flow`（確保 docs/BRD.md 存在）|
| 中途斷點續行（某 D-step 開始）| `/gendoc-config` 選擇起始步驟 → `/gendoc-flow` |

---

## Iron Law

> **鐵律（不可違反）：每份文件生成前，必須讀取所有上游文件（累積鏈，非僅直接父文件）。**
> docs/req/* 素材全部關聯讀取。若上游不存在，靜默跳過；不得因此降低覆蓋深度。
> 違反此鐵律的生成結果視為無效，必須重新生成。

---

## Step -1：版本自動更新檢查 + SPAWNED_SESSION 偵測

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

```bash
# SPAWNED_SESSION 偵測
[ -n "$OPENCLAW_SESSION" ] && _SPAWNED="true" || _SPAWNED="false"
echo "SPAWNED_SESSION: $_SPAWNED"
# 若為 spawned session，全程跳過 AskUserQuestion，強制 full-auto
[[ "$_SPAWNED" == "true" ]] && echo "[SPAWNED] 跳過互動提問，強制 full-auto 模式"
```

**立即用 Skill tool 呼叫 `gendoc-shared`。等 Skill tool 回傳後才繼續 Step 0，在此之前不得執行任何後續步驟。**

---

## Step 0（§PRE-1）：輸入來源偵測（C-01/C-06）

### Step 0-A：偵測輸入類型

依以下優先順序判斷 `_INPUT_TYPE`：

| 條件 | `_INPUT_TYPE` | 後續處理 |
|------|--------------|---------|
| 無 URL / 無路徑，純文字描述 | `text_idea` | 直接擷取為 `_IDEA` |
| `http(s)://` + 圖片副檔名（jpg/png/gif/webp/svg） | `image_url` | WebFetch + Vision 分析→提取需求摘要 |
| `github.com` / `gitlab.com` URL | `doc_git` | WebFetch 讀取 README/docs→提取需求摘要 |
| `http(s)://` + `.pdf/.md/.docx/.txt` | `doc_url` | WebFetch 下載→提取文字→摘要 |
| `http(s)://` 其他網頁 | `doc_url` | WebFetch 讀取頁面→提取需求摘要 |
| 本地目錄路徑（含 `/` 且為目錄） | `codebase_local` | 記錄路徑，Step 1.6 處理 |
| 本地檔案路徑（含 `/` 且為檔案） | `doc_local` | 記錄路徑，Step 1.6 處理 |
| `git@` / `.git` URL | `codebase_git` | 記錄 URL，Step 1.6 處理 |

```bash
_INPUT_TYPE="text_idea"   # 預設
_INPUT_SOURCE=""          # URL 或路徑（若有）
_INPUT_SUMMARY=""         # 分析摘要（供後續步驟使用）
```

### Step 0-B：依輸入類型取得需求摘要

**`text_idea`**（純文字）：

```bash
_IDEA="<從使用者訊息提取的概念描述>"
_INPUT_SUMMARY="$_IDEA"
echo "[Step 0] 輸入類型：text_idea"
```

---

**`image_url`**（圖片）：

使用 WebFetch + Vision 分析圖片，提取：
- 畫面功能描述
- UI 元件清單
- 推斷的使用者需求

```bash
_INPUT_SOURCE="<圖片 URL>"
# WebFetch 取回圖片，以 Vision 分析
_IDEA="<從圖片分析提取的系統/功能描述>"
_INPUT_SUMMARY="[圖片分析] $_IDEA"
echo "[Step 0] 輸入類型：image_url，來源：$_INPUT_SOURCE"
```

---

**`doc_url`**（文件/網頁 URL）：

```bash
_INPUT_SOURCE="<URL>"
# WebFetch 取回文件內容，提取核心需求
_IDEA="<從文件內容提取的產品/系統需求摘要>"
_INPUT_SUMMARY="[文件摘要] $_IDEA"
echo "[Step 0] 輸入類型：doc_url，來源：$_INPUT_SOURCE"
```

---

**`doc_git`**（GitHub/GitLab）：

```bash
_INPUT_SOURCE="<GitHub URL>"
# WebFetch 讀取 README 和 docs/
_IDEA="<從 repo 文件提取的專案目標與功能摘要>"
_INPUT_SUMMARY="[Git Repo 摘要] $_IDEA"
echo "[Step 0] 輸入類型：doc_git，來源：$_INPUT_SOURCE"
```

---

**`doc_local` / `codebase_local` / `codebase_git`**（本地或 git 來源）：

```bash
_INPUT_SOURCE="<使用者提供的本地路徑或 git URL>"
# 無法在 Step 0 讀取（專案目錄尚未建立）
# 標記待 Step 1.6 處理
_IDEA="<從使用者描述或路徑名稱推斷的需求描述（佔位）>"
_INPUT_SUMMARY="[待 Step 1.6 分析] 來源：$_INPUT_SOURCE"
echo "[Step 0] 輸入類型：$_INPUT_TYPE，來源：$_INPUT_SOURCE（Step 1.6 處理）"
```

---

```bash
_PROJECT_SLUG=$(echo "$_IDEA" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | cut -c1-30 | sed 's/-$//')
echo "IDEA: $_IDEA"
echo "INPUT_TYPE: $_INPUT_TYPE"
echo "PROJECT_SLUG: $_PROJECT_SLUG"
```

---

## Step 1（§PRE-2）：偵測專案目錄（C-01）

**預設行為**：在**當前目錄（`$(pwd)`）**直接建置，不建子目錄。可透過引數指定其他目錄。

```bash
# 偵測是否有引數傳入目標目錄（如 /gendoc-auto /path/to/dir <idea>）
_ARG_DIR=""   # 由 skill 引數解析取得（若使用者在 args 中提供路徑）

_CWD="$(pwd)"
_DEFAULT_DIR="$_CWD"   # 預設：當前目錄
echo "CWD: $_CWD"
echo "DEFAULT_DIR: $_DEFAULT_DIR"
```

```bash
# 使用當前目錄（或引數指定目錄）
if [[ -n "$_ARG_DIR" ]]; then
  _PROJECT_DIR="$_ARG_DIR"
  echo "[gendoc-auto] 專案目錄（引數指定）：$_PROJECT_DIR"
else
  _PROJECT_DIR="$(pwd)"
  echo "[gendoc-auto] 專案目錄（當前目錄）：$_PROJECT_DIR"
fi
```

```bash
# Local-first template lookup（同 gendoc/gendoc-flow/reviewdoc 的原則）
if [[ -f "$_PROJECT_DIR/templates/pipeline.json" ]]; then
  _TEMPLATE_DIR="$_PROJECT_DIR/templates"
else
  _TEMPLATE_DIR="$HOME/.claude/gendoc/templates"
fi
echo "[Template] 使用 templates：$_TEMPLATE_DIR"
```

---

## Step 1.5（§PRE-3/§PRE-4）：TF-02 守衛 + 建立工作空間 + Session Config（C-01/C-04/C-05/C-06）

### TF-02 守衛（§PRE-4）

```bash
# 斷點續行路徑：State file 存在
_EXISTING_STATE=$(ls "$_PROJECT_DIR"/.gendoc-state-*.json 2>/dev/null | head -1 || echo "")
if [[ -n "$_EXISTING_STATE" ]]; then
  _SKILL_SOURCE=$(python3 -c "import json; d=json.load(open('$_EXISTING_STATE')); print(d.get('skill_source',''))" 2>/dev/null || echo "")
  if [[ "$_SKILL_SOURCE" != "gendoc-auto" && -n "$_SKILL_SOURCE" ]]; then
    echo "[ABORT] State file 屬於 ${_SKILL_SOURCE}，非 gendoc-auto，無法繼續"
    exit 1
  fi
  echo "[Resume] 偵測到既有 state（skill_source=${_SKILL_SOURCE}），將從上次中斷點繼續"

  # P-08：若 handoff 已完成，導流至 gendoc-flow
  _HANDOFF_DONE=$(python3 -c "
import json
try:
    d = json.load(open('$_EXISTING_STATE'))
    print(str(d.get('handoff', False)))
except:
    print('False')
" 2>/dev/null || echo "False")

  if [[ "$_HANDOFF_DONE" == "True" ]]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  [P-08] Handoff 已完成                               ║"
    echo "╠══════════════════════════════════════════════════════╣"
    echo "║  IDEA.md + BRD.md 已生成並通過 Review。              ║"
    echo "║  請執行 /gendoc-flow 繼續後續文件生成流水線。         ║"
    echo "╚══════════════════════════════════════════════════════╝"
    exit 0
  fi
fi
```

### 建立工作空間

```bash
mkdir -p "$_PROJECT_DIR/docs"
cd "$_PROJECT_DIR"
# 若目錄已是 git repo 則跳過 init
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || git init

# Git 使用者設定（含 fallback）
_GIT_USER=$(git config user.name 2>/dev/null | tr '[:upper:] ' '[:lower:]-' | sed 's/[^a-z0-9-]//g' | cut -c1-20 || whoami 2>/dev/null | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g' | cut -c1-20 || echo "user")
_GIT_BRANCH=$(git branch --show-current 2>/dev/null | tr '/: ' '---' | sed 's/[^a-z0-9-]//g' | cut -c1-30 || echo "main")
_STATE_FILE=".gendoc-state-${_GIT_USER}-${_GIT_BRANCH}.json"
echo "[Workspace] 工作空間：$(pwd)"
echo "[Workspace] git user：${_GIT_USER}，branch：${_GIT_BRANCH}，state file：$_STATE_FILE"

# 寫入 skill_source（state file 由 gendoc-config 建立，此處僅 patch）
python3 -c "
import json, os; f='${_STATE_FILE}'
d=json.load(open(f))
d['skill_source'] = 'gendoc-auto'
tmp=f+'.tmp'
open(tmp,'w').write(json.dumps(d, indent=2, ensure_ascii=False))
os.replace(tmp, f)
"

# 寫入 spawned_session 旗標（供 gendoc-flow 跨 skill 讀取，避免再次詢問使用者）
python3 -c "
import json
try: d=json.load(open('${_STATE_FILE}'))
except: d={}
d['spawned_session'] = ('${_SPAWNED}' == 'true')
import os; tmp='${_STATE_FILE}.tmp'
open(tmp,'w').write(json.dumps(d, indent=2, ensure_ascii=False))
os.replace(tmp, '${_STATE_FILE}')
" 2>/dev/null || true

git add docs/.gitkeep docs/req/.gitkeep CLAUDE.md .gitignore 2>/dev/null || true
git add $(git ls-files --others --exclude-standard docs/ 2>/dev/null | head -20) 2>/dev/null || true
git commit -m "chore(gendoc-auto): init workspace" 2>/dev/null || true
```

**Session Config（以 state file 為主，僅 key 不存在時才寫入預設值）**：

```bash
python3 -c "
import json, datetime
f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d.setdefault('execution_mode',  'full-auto')
d.setdefault('review_strategy', 'standard')
d.setdefault('max_rounds', 5)
d.setdefault('stop_condition', '任一輪 finding=0 或第 5 輪 fix 完')
d['last_updated'] = datetime.datetime.utcnow().isoformat() + 'Z'
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
print('[Session Config] mode=' + d['execution_mode'] + ' / review_strategy=' + d['review_strategy'] + ' / max_rounds=' + str(d['max_rounds']))
"

_EXEC_MODE=$(python3 -c "import json; print(json.load(open('${_STATE_FILE}')).get('execution_mode','full-auto'))" 2>/dev/null || echo "full-auto")
_REVIEW_STRATEGY=$(python3 -c "import json; print(json.load(open('${_STATE_FILE}')).get('review_strategy','standard'))" 2>/dev/null || echo "standard")
_MAX_ROUNDS=$(python3 -c "import json; print(json.load(open('${_STATE_FILE}')).get('max_rounds',5))" 2>/dev/null || echo "5")
_STOP_CONDITION=$(python3 -c "import json; print(json.load(open('${_STATE_FILE}')).get('stop_condition','任一輪 finding=0 或第 5 輪 fix 完'))" 2>/dev/null || echo "任一輪 finding=0 或第 5 輪 fix 完")
```

---

## Step 1.6：多元素材保存至 docs/req/（C-05/C-13）

> **[READ-ONLY 原則]** — 本地路徑（`codebase_local` / `doc_local`）和 git clone 暫存目錄
> 是**唯讀來源**，嚴禁在其中執行任何寫入、刪除、修改或 `mkdir` 操作。
> 所有輸出一律寫入 `$_PROJECT_DIR/docs/req/`（當前專案目錄），不得寫回原始來源。

```bash
mkdir -p "$_PROJECT_DIR/docs/req"
echo "[req/] docs/req/ 已建立，準備保存輸入素材"
```

依 `_INPUT_TYPE` 執行以下對應操作：

---

**`text_idea`**：

```bash
cat > "$_PROJECT_DIR/docs/req/idea-input.md" << 'IDEA_EOF'
# 原始需求輸入

$_IDEA
IDEA_EOF
echo "[req/] text_idea 已保存至 docs/req/idea-input.md"
```

---

**`image_url`**：

Step 0-B 已用 WebFetch + Vision 分析，將摘要 Write → `docs/req/image-analysis.md`：

```markdown
# 圖片分析結果

**來源**：$_INPUT_SOURCE

## 分析摘要

$_INPUT_SUMMARY

## 原始圖片 URL

$_INPUT_SOURCE
```

---

**`doc_url`**：

Step 0-B 已用 WebFetch 取回內容，Write → `$_PROJECT_DIR/docs/req/source-url.md`：

```markdown
# 文件來源

**URL**：$_INPUT_SOURCE

## 內容摘要

$_INPUT_SUMMARY
```

---

**`doc_git`**：

Step 0-B 已用 WebFetch 讀取 README/docs，Write → `$_PROJECT_DIR/docs/req/source-git.md`：

```markdown
# Git Repo 來源

**URL**：$_INPUT_SOURCE

## 內容摘要

$_INPUT_SUMMARY
```

---

**`doc_local`**（本地單一檔案）：

```bash
_SOURCE_PATH="$_INPUT_SOURCE"
_DEST="$_PROJECT_DIR/docs/req/$(basename "$_SOURCE_PATH")"

cp "$_SOURCE_PATH" "$_DEST"
echo "[req/] 已複製：$_SOURCE_PATH → $_DEST（原始檔案未變動）"

_IDEA=$(head -100 "$_DEST" 2>/dev/null | strings | head -30)
_INPUT_SUMMARY="[本地文件] $(basename "$_SOURCE_PATH") — ${_IDEA:0:200}"
```

---

**`codebase_local`**（本地目錄 / codebase）：

```bash
_SOURCE_DIR="$_INPUT_SOURCE"
_REQ_DIR="$_PROJECT_DIR/docs/req"

# 1. 目錄結構摘要（讀取，輸出至 docs/req/）
tree "$_SOURCE_DIR" -L 3 --noreport 2>/dev/null \
  || find "$_SOURCE_DIR" -maxdepth 3 -not -path '*/.git/*' \
  | head -100 > "$_REQ_DIR/codebase-tree.txt"

# 2. 複製關鍵文件（只 cp，不修改原始）
for _FILE in README.md README.rst README.txt CONTRIBUTING.md \
             package.json pyproject.toml go.mod Cargo.toml pom.xml build.gradle; do
  if [[ -f "$_SOURCE_DIR/$_FILE" ]]; then
    cp "$_SOURCE_DIR/$_FILE" "$_REQ_DIR/$_FILE"
    echo "[req/] 已複製：$_FILE"
  fi
done

# 3. 複製 docs/ 子目錄（若存在，只 cp 不寫回）
if [[ -d "$_SOURCE_DIR/docs" ]]; then
  cp -r "$_SOURCE_DIR/docs/." "$_REQ_DIR/source-docs/"
  echo "[req/] 已複製：docs/ → docs/req/source-docs/"
fi

echo "[req/] codebase_local 掃描完成，原始目錄 $_SOURCE_DIR 未變動"

if [[ -f "$_REQ_DIR/README.md" ]]; then
  _IDEA=$(head -30 "$_REQ_DIR/README.md" | strings)
  _INPUT_SUMMARY="[Codebase] $(basename "$_SOURCE_DIR") — ${_IDEA:0:200}"
fi
```

---

**`codebase_git`**（遠端 git repo）：

```bash
_TMP_CLONE=$(mktemp -d)
git clone --depth 1 "$_INPUT_SOURCE" "$_TMP_CLONE" 2>/dev/null

# 從暫存目錄 cp 關鍵文件（C-13：補充 pom.xml / build.gradle / CONTRIBUTING.md）
for _FILE in README.md README.rst README.txt CONTRIBUTING.md \
             package.json pyproject.toml go.mod Cargo.toml \
             pom.xml build.gradle; do
  [[ -f "$_TMP_CLONE/$_FILE" ]] && cp "$_TMP_CLONE/$_FILE" "$_PROJECT_DIR/docs/req/$_FILE"
done

tree "$_TMP_CLONE" -L 3 --noreport 2>/dev/null \
  > "$_PROJECT_DIR/docs/req/codebase-tree.txt"

rm -rf "$_TMP_CLONE"
echo "[req/] codebase_git clone 完成，暫存目錄已清除"

if [[ -f "$_PROJECT_DIR/docs/req/README.md" ]]; then
  _IDEA=$(head -30 "$_PROJECT_DIR/docs/req/README.md" | strings)
  _INPUT_SUMMARY="[Git Codebase] $_INPUT_SOURCE — ${_IDEA:0:200}"
fi
```

---

```bash
# 若 docs/req/ 完全空白，建立 .gitkeep
_REQ_COUNT=$(ls "$_PROJECT_DIR/docs/req/" 2>/dev/null | grep -v '.gitkeep' | wc -l | tr -d ' ')
[[ "$_REQ_COUNT" -eq 0 ]] && touch "$_PROJECT_DIR/docs/req/.gitkeep"

# 儲存 input 資訊至 state
python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['input_type']    = '$_INPUT_TYPE'
d['input_source']  = '$_INPUT_SOURCE'
d['input_summary'] = '$_INPUT_SUMMARY'
d['req_dir']       = 'docs/req'
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
print('[req/] state 已寫入 input_type / input_source / input_summary')
"

echo "📎 素材保存完成：type=${_INPUT_TYPE}，docs/req/ 含 ${_REQ_COUNT} 個素材"
ls -la "$_PROJECT_DIR/docs/req/"
```

---

## Step 1.7：PM Expert Agent

```bash
python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['input_type']    = '${_INPUT_TYPE}'
d['input_source']  = '${_INPUT_SOURCE}'
d['input_summary'] = '${_INPUT_SUMMARY}'
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
"
```

以 Agent 工具（PM Expert 角色）分析 `_INPUT_SUMMARY` + `docs/req/` 下所有素材，提取並寫入 state：

```bash
python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['project_name']     = '${_PROJECT_NAME}'    # 英文小寫連字號，最多 30 字元
d['project_type']     = '${_PROJECT_TYPE}'    # web-app / mobile-app / cli-tool / api-service / data-platform / other
d['key_features']     = '${_KEY_FEATURES}'   # 3-5 核心功能描述
d['target_users']     = '${_TARGET_USERS}'   # 主要使用者描述
d['tech_stack_hints'] = '${_TECH_HINTS}'    # 技術棧提示（若有）
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
print('[PM Expert] project_name={}, project_type={}'.format(d['project_name'], d['project_type']))
"
```

# PM Expert 輸出驗證（只警告，不中止流水線）
_PM_VALID=$(python3 -c "
import json, re
try:
    d = json.load(open('${_STATE_FILE}'))
    warns = []
    pn = d.get('project_name','')
    if not pn:
        warns.append('project_name 為空，將使用目錄名稱作為備援')
        d['project_name'] = '$(basename $(pwd))'
    elif not re.match(r'^[a-z0-9][a-z0-9-]{0,29}$', pn):
        warns.append(f'project_name \"{pn}\" 含非法字元或過長，已截斷並替換特殊字元')
        d['project_name'] = re.sub(r'[^a-z0-9-]','-', pn.lower())[:30].strip('-')
    pt = d.get('project_type','')
    valid_types = ['web-app','mobile-app','cli-tool','api-service','data-platform','game','other']
    if pt not in valid_types:
        warns.append(f'project_type \"{pt}\" 不在已知清單，已設為 other')
        d['project_type'] = 'other'
    if warns:
        import os; tmp='${_STATE_FILE}.tmp'
        open(tmp,'w').write(json.dumps(d, indent=2, ensure_ascii=False))
        os.replace(tmp, '${_STATE_FILE}')
    for w in warns:
        print(f'[PM-WARN] {w}')
    print(f'[PM-OK] 驗證完成（{\"通過\" if not warns else str(len(warns))+\" 個警告，已自動修正\"}）')
except Exception as e:
    print(f'[PM-WARN] 驗證例外：{e}（流水線繼續，使用現有值）')
" 2>/dev/null || echo "[PM-WARN] 驗證腳本執行失敗（流水線繼續）")
echo "$_PM_VALID"
# 注意：驗證失敗只輸出警告，不 exit 1——流水線自動化不能因驗證警告而中止

**專案名稱衝突檢查**（寫入 state 後立即執行）：

```bash
_PROJECT_NAME=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('project_name',''))
except: print('')
" 2>/dev/null || echo "")

_PARENT_DIR=$(dirname "$(pwd)")
_CONFLICT_DIR=false
if [[ -d "$_PARENT_DIR/$_PROJECT_NAME" ]]; then
  _CONFLICT_DIR=true
  echo "[DOC-01] ⚠️  衝突：$_PARENT_DIR/$_PROJECT_NAME 已存在"
fi

_CONFLICT_REPO=false
if command -v gh &>/dev/null; then
  _GH_OWNER=$(gh api user --jq .login 2>/dev/null || echo "")
  if [[ -n "$_GH_OWNER" ]]; then
    gh api "repos/${_GH_OWNER}/${_PROJECT_NAME}" &>/dev/null && _CONFLICT_REPO=true
    [[ "$_CONFLICT_REPO" == "true" ]] && echo "[DOC-01] ⚠️  衝突：GitHub repo ${_GH_OWNER}/${_PROJECT_NAME} 已存在"
  fi
fi
```

**衝突處理**（`_CONFLICT_DIR=true` 或 `_CONFLICT_REPO=true`）：自動忽略衝突，直接在現有目錄繼續。

---

## Step 1.8：client_type 確認 + 規模確認（全流水線唯一互動點）

> **此步驟是整條流水線中唯一與使用者互動的決策點。**
> 確認後，從 IDEA → BRD → PRD → … → HTML 全程自動執行，不再詢問任何問題。
> **SPAWNED 模式**或 **`client_type_source = "confirmed"`** 時：自動採建議值，跳過互動。

```bash
_CT_EXISTING=$(python3 -c "import json; d=json.load(open('${_STATE_FILE}')); print(d.get('client_type',''))" 2>/dev/null || echo "")
_CT_SOURCE=$(python3 -c "import json; d=json.load(open('${_STATE_FILE}')); print(d.get('client_type_source',''))" 2>/dev/null || echo "")
```

### 跳過條件判斷

```bash
_SKIP_1_8=false
if [[ "$_SPAWNED" == "true" ]]; then
  echo "[Step 1.8] SPAWNED 模式，跳過互動，採自動推斷值"
  _SKIP_1_8=true
fi
if [[ "$_CT_SOURCE" == "confirmed" ]] && [[ -n "$_CT_EXISTING" ]]; then
  echo "[Step 1.8] client_type 已由使用者確認（source=confirmed：${_CT_EXISTING}），跳過"
  _SKIP_1_8=true
fi
```

### 推斷建議值（SPAWNED 和互動模式共用）

```bash
_SUGGEST_CT=$(python3 - <<'PYEOF'
import json
try: d=json.load(open('${_STATE_FILE}'))
except: d={}
text=' '.join([d.get('key_features',''),d.get('target_users',''),
               d.get('project_type',''),d.get('input_summary','')]).lower()
game_kw=['game','arcade','unity','cocos','phaser','pixijs','godot','unreal',
         'canvas','webgl','opengl','directx','vulkan','metal',
         '遊戲','魚機','博弈','遊藝','投幣','玩家','角色','場景',
         '卡牌','棋牌','捕魚','電子遊戲','老虎機','水果機',
         '捕魚達人','麻將','鬥地主','百家樂',
         'sprite','tilemap','collision','physics engine','particle system',
         '音效','fps','render loop']
ui_kw  =['ui','ux','frontend','front-end','web','html','css',
         'react','vue','angular','svelte','nextjs','nuxt',
         'app','mobile','native','ios','android','flutter','swift','kotlin',
         'react native','expo',
         'interface','screen','display','dashboard','portal','panel',
         'page','view','layout','widget','button','form',
         '介面','畫面','螢幕','顯示','前端','操作面板','儀表板','視覺',
         '按鈕','頁面','視窗','彈窗','選單','使用者介面',
         'client','客戶端','用戶端']
if any(k in text for k in game_kw): print('game')
elif any(k in text for k in ui_kw): print('web')
else: print('api-only')
PYEOF
)

_SUGGEST_SCALE=$(python3 - <<'PYEOF'
import json,re
try: d=json.load(open('${_STATE_FILE}'))
except: d={}
text=' '.join([d.get('target_users',''),d.get('key_features',''),d.get('input_summary','')]).lower()
nums=re.findall(r'[\d,]+',text)
max_n=max((int(n.replace(',','')) for n in nums if n.replace(',','').isdigit()),default=0)
if max_n>=10000000 or any(k in text for k in ['million','百萬','千萬','億']):
    print('大規模（百萬用戶級，需分散式架構）')
elif max_n>=100000 or any(k in text for k in ['十萬','enterprise','global','企業級']):
    print('中規模（萬~十萬用戶，微服務為主）')
elif any(k in text for k in ['pilot','poc','mvp','prototype','試行','原型','概念驗證']):
    print('MVP/Pilot（快速驗證，可接受技術債）')
else:
    print('小規模（千級用戶，優先交付速度）')
PYEOF
)

echo "[Step 1.8] 建議 client_type：${_SUGGEST_CT} / 建議規模：${_SUGGEST_SCALE}"
```

### SPAWNED / 已確認：直接採用建議值

```bash
if [[ "$_SKIP_1_8" == "true" ]]; then
  # 若 state 中 client_type 已確認，不覆寫；否則寫入建議值
  python3 - <<PYEOF
import json,os
f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
if not d.get('client_type') or d.get('client_type_source','') not in ('confirmed',):
    d['client_type']='${_SUGGEST_CT}'
    d['client_type_source']='auto-confirmed'
if not d.get('q4_scale'):
    d['q4_scale']='${_SUGGEST_SCALE}'
tmp=f+'.tmp'; open(tmp,'w').write(json.dumps(d,indent=2,ensure_ascii=False)); os.replace(tmp,f)
print('[Step 1.8] auto: client_type='+d['client_type']+' / scale='+d['q4_scale'])
PYEOF
fi
```

### 互動模式：顯示建議並詢問確認（2 問）

**若 `_SKIP_1_8=false`**，用 `AskUserQuestion` 執行以下 2 個問題：

**問題 1 — client_type 確認**：

```
question: |
  📋 請確認專案類型（確認後整條流水線全自動執行，不再詢問）

  gendoc 分析您的需求，建議：client_type = {_SUGGEST_CT}

  各選項說明：
  • web     — SaaS / App / 管理後台（含 PDD / FRONTEND / BDD-client，無 AUDIO/ANIM）
  • game    — 遊戲專案（含 AUDIO / ANIM / PDD / FRONTEND / BDD-client）
  • api-only — 純後端 API 服務（跳過所有 client 側文件）

options:
  - "✅ 採用建議：{_SUGGEST_CT}（推薦）"
  - "web     — SaaS / App / 管理後台"
  - "game    — 遊戲專案（含 AUDIO/ANIM）"
  - "api-only — 純後端 API 服務"
```

取得 `_CONFIRMED_CT`：
- 選項 1 → `_CONFIRMED_CT="$_SUGGEST_CT"`
- 選項 2 → `_CONFIRMED_CT="web"`
- 選項 3 → `_CONFIRMED_CT="game"`
- 選項 4 → `_CONFIRMED_CT="api-only"`

**問題 2 — 規模確認**：

```
question: |
  📐 請確認系統規模預期（影響 EDD 效能設計、k8s 資源規格、容量規劃）

  建議：{_SUGGEST_SCALE}

options:
  - "✅ 採用建議：{_SUGGEST_SCALE}（推薦）"
  - "MVP/Pilot — 快速驗證，可接受技術債"
  - "小規模 — 千級用戶，優先交付速度"
  - "中規模 — 萬~十萬用戶，微服務為主"
  - "大規模 — 百萬用戶級，需分散式架構"
```

取得 `_CONFIRMED_SCALE`（選項 1 → `$_SUGGEST_SCALE`；其他 → 對應文字）。

**確認並寫入 state**：

```bash
python3 - <<PYEOF
import json,os
f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['client_type']        = '${_CONFIRMED_CT}'
d['client_type_source'] = 'confirmed'   # P-13/P-14 不再覆寫
d['q4_scale']           = '${_CONFIRMED_SCALE}'
tmp=f+'.tmp'; open(tmp,'w').write(json.dumps(d,indent=2,ensure_ascii=False)); os.replace(tmp,f)
print('[Step 1.8] ✅ client_type='+d['client_type']+' / scale='+d['q4_scale']+' 已確認並鎖定')
PYEOF

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ 設定已確認 — 接下來全程自動執行，無需再次確認         ║"
echo "╠══════════════════════════════════════════════════════════╣"
printf "║  client_type : %-42s ║\n" "${_CONFIRMED_CT}"
printf "║  系統規模    : %-42s ║\n" "${_CONFIRMED_SCALE}"
echo "║                                                          ║"
echo "║  請放心等待，所有文件將依序自動生成完成。               ║"
echo "╚══════════════════════════════════════════════════════════╝"
```

---

## Step 2：AI 自動推斷需求欄位（C-07）

```bash
# 根據 _IDEA 直接推斷所有欄位，不詢問使用者
echo "[gendoc-auto] AI 自動推斷需求欄位（Q1-Q5 由 PM Expert 從輸入素材分析）"
```

PM Expert Agent（Step 1.7）已分析輸入並寫入 state，此處直接讀取：

```bash
_Q1_USERS=$(python3 -c "import json; d=json.load(open('${_STATE_FILE}')); print(d.get('target_users','一般開發者'))" 2>/dev/null || echo "一般開發者")
_Q2_PAINPOINT=$(python3 -c "import json; d=json.load(open('${_STATE_FILE}')); print(d.get('key_features',''))" 2>/dev/null || echo "")
_Q3_TECH=$(python3 -c "import json; d=json.load(open('${_STATE_FILE}')); print(d.get('tech_stack_hints','無特殊限制'))" 2>/dev/null || echo "無特殊限制")
_Q4_SCALE=$(python3 -c "import json; d=json.load(open('${_STATE_FILE}')); print(d.get('q4_scale','小規模（千級用戶，優先交付速度）'))" 2>/dev/null || echo "小規模（千級用戶，優先交付速度）")
_Q5_EXTRA=""
echo "[Step 2] users=${_Q1_USERS} / tech=${_Q3_TECH}"
```

---

## Step 3：網路背景研究（C-08）

使用 `WebSearch` tool 執行 3 次搜尋：

```
搜尋 1："{_PROJECT_SLUG} {_Q2_PAINPOINT} open source github"
搜尋 2："{核心技術關鍵字} best practices 2025"
搜尋 3："{_PROJECT_SLUG} pitfalls challenges"
```

整理研究結果：

```
_RESEARCH_SUMMARY = """
## 競品/參考資源
- [競品名 1]：<簡述>（GitHub: ⭐ N.Nk）
- [競品名 2]：<簡述>
- [參考資源 3]：<簡述>

## 技術建議
- 語言/框架：<建議 + 理由>
- 資料庫：<建議 + 理由>
- 核心套件：<建議>

## 已知風險
- <風險 1>：<說明>
- <風險 2>：<說明>
"""
_RESEARCH_COUNT = <找到的參考資源數>
```

---

## Step 5：生成 IDEA.md（C-09/C-16）

### Skip Guard（P-01：避免已完成步驟重跑）

```bash
# ── P-01 Skip Guard：避免已完成步驟重跑 ─────────────────────────
_COMPLETED_NOW=$(python3 -c "
import json
try:
    d = json.load(open('${_STATE_FILE}'))
    print(','.join(d.get('completed_steps', [])))
except:
    print('')
" 2>/dev/null || echo "")

_IDEA_REVIEWED=$(python3 -c "
import json
try:
    d = json.load(open('${_STATE_FILE}'))
    print(str(d.get('idea_review_passed', False)))
except:
    print('False')
" 2>/dev/null || echo "False")

_SKIP_IDEA_GEN=""
_RESUME_IDEA_REVIEW=""

if [[ ",${_COMPLETED_NOW}," == *",D01-IDEA,"* ]]; then
  if [[ "$_IDEA_REVIEWED" == "True" ]]; then
    echo "[Skip P-01] D01-IDEA 已完成且 review 通過，跳過 IDEA 生成與 review"
    _SKIP_IDEA_GEN="true"
  else
    echo "[Resume P-01] D01-IDEA 已生成但 review 未通過，跳過生成，直接進入 review"
    _SKIP_IDEA_GEN="true"
    _RESUME_IDEA_REVIEW="true"
  fi
fi
```

### 舊版文件歸檔（C-16）

```bash
if [[ -z "$_SKIP_IDEA_GEN" ]]; then
  if [[ -f "docs/IDEA.md" ]]; then
    _TS=$(date +%Y%m%d-%H%M%S)
    mv "docs/IDEA.md" "docs/req/old-IDEA-${_TS}.md"
    echo "[Archive] 舊 docs/IDEA.md → docs/req/old-IDEA-${_TS}.md"
  fi
fi
```

### 寫入 Q1-Q5 + 研究摘要到 state（供 gen-idea 使用）

```bash
if [[ -z "$_SKIP_IDEA_GEN" ]]; then
  python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['q1_users']         = '${_Q1_USERS}'
d['q2_painpoint']     = '${_Q2_PAINPOINT}'
d['q3_constraints']   = '${_Q3_TECH}'
d['q4_scale']         = '${_Q4_SCALE}'
d['q5_additional']    = '${_Q5_EXTRA}'
d['research_summary'] = '''${_RESEARCH_SUMMARY}'''
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
print('[state] Q1-Q5 + research_summary 已寫入')
"
fi
```

### 呼叫 gendoc idea（C-09）

透過 **Skill tool** 呼叫 `gendoc`，args: `idea`（不得 inline 生成，生成規則由 `{_TEMPLATE_DIR}/IDEA.gen.md` 定義）。

```bash
if [[ -z "$_SKIP_IDEA_GEN" ]]; then
```

**以 Agent tool 建立 subagent**，prompt 填入以下內容（替換 `$_PROJECT_DIR` 和 `$_STATE_FILE` 為實際路徑）：

> gendoc 子任務：生成 IDEA.md  
> 專案目錄：`$_PROJECT_DIR`  
> State file：`$_PROJECT_DIR/$_STATE_FILE`  
>  
> 執行：1) cd 到專案目錄 2) 讀取 state file 確認 Q1-Q5/research_summary 存在 3) 用 Skill tool 執行 /gendoc，args: idea 4) 確認 docs/IDEA.md 已寫入 5) 回報成功/失敗及行數

等 Agent 回傳後，繼續執行下方 bash。

gen-idea 完成後：

```bash
  python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['idea_generated'] = True
d['idea_path'] = 'docs/IDEA.md'
if 'D01-IDEA' not in d.get('completed_steps',[]):
    d.setdefault('completed_steps',[]).append('D01-IDEA')
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
"
  git add docs/IDEA.md && git commit -m "docs(gendoc-auto): init IDEA" 2>/dev/null || true
fi
```

---

## Step 5.5：IDEA.md Review Loop（C-10）

```bash
# 僅在 IDEA 未曾 review 通過、或需要重跑 review 時執行
if [[ -z "$_SKIP_IDEA_GEN" ]] || [[ -n "$_RESUME_IDEA_REVIEW" ]]; then
```

主 Claude 直接驅動 Review → Fix → Round Summary → Commit loop（同 gendoc-flow Phase D-2）。

```bash
_MAX_ROUNDS=$(python3 -c "
import json
try: d=json.load(open('${_STATE_FILE}')); print(d.get('max_rounds',5))
except: print(5)
" 2>/dev/null || echo "5")
_REVIEW_STRATEGY=$(python3 -c "
import json
try: d=json.load(open('${_STATE_FILE}')); print(d.get('review_strategy','standard'))
except: print('standard')
" 2>/dev/null || echo "standard")
echo "[IDEA Review] 策略：${_REVIEW_STRATEGY}，最多 ${_MAX_ROUNDS} 輪"
```

**Review → Fix → Round Summary → Commit loop（max_rounds 次）：**

```python
for round in range(1, max_rounds + 1):

    # ── Review Subagent ───────────────────────────────────
    review_result = spawn_review_agent("IDEA", round)
    finding_total = review_result["finding_total"]
    critical      = review_result["critical"]
    high          = review_result["high"]
    medium        = review_result["medium"]
    low           = review_result["low"]
    findings      = review_result["findings"]

    # ── 判斷終止 ──────────────────────────────────────────
    terminate = False
    terminate_reason = ""
    if finding_total == 0:
        terminate = True; terminate_reason = "PASSED — finding=0"
    elif review_strategy == "rapid" and round >= 3:
        terminate = True; terminate_reason = "MAX_ROUNDS — rapid=3 已達"
    elif review_strategy == "tiered" and round >= 6 and (critical + high + medium) == 0:
        terminate = True; terminate_reason = "PASSED — tiered: CRITICAL+HIGH+MEDIUM=0"
    elif round >= max_rounds:
        terminate = True; terminate_reason = f"MAX_ROUNDS={max_rounds} 已達"

    # ── Fix Subagent（finding>0 時必執行）────────────────
    fix_result = None
    if finding_total > 0:
        fix_result = spawn_fix_agent("IDEA", round, findings)
        unfixed_count = len(fix_result.get("unfixed", []))
        fixed_count   = len(fix_result.get("fixed", []))
    else:
        unfixed_count = 0; fixed_count = 0

    # ── Round Summary（commit 之前輸出）──────────────────
    status_icon = "✅ PASS" if finding_total == 0 else ("⚠️  MAX" if terminate else "🔄 CONT")
    print(f"""
┌─── D01-IDEA Review Round {round}/{max_rounds} ──────────────────────────┐
│  Review：CRITICAL={critical} HIGH={high} MEDIUM={medium} LOW={low}  Total={finding_total}
│  Fix：   修復 {fixed_count} 個 / 殘留 {unfixed_count} 個（本輪未解）
│  本輪狀態：{status_icon}  {terminate_reason if terminate else '繼續下一輪'}
│  Fix summary：{fix_result['summary'] if fix_result else 'N/A（finding=0，無需修復）'}
└──────────────────────────────────────────────────────────────────────┘""")

    # ── Commit ───────────────────────────────────────────
    git add docs/IDEA.md
    if finding_total == 0:
        git commit -m f"docs(gendoc-auto)[D01-IDEA]: review-r{round} — PASS (0 findings)"
    else:
        git commit -m f"docs(gendoc-auto)[D01-IDEA]: review-r{round} — fix {fixed_count}/{finding_total} findings"

    if terminate:
        break
```

更新 state：
```bash
python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['idea_review_passed'] = True
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
print('[state] idea_review_passed = True')
"
```

**Review Subagent prompt（主 Claude 用 Agent tool 派送）：**

```
你是 IDEA 文件審查專家。
任務：依照 {_TEMPLATE_DIR}/IDEA.review.md 的審查標準，審查 docs/IDEA.md。

執行步驟：
1. 讀取 {_TEMPLATE_DIR}/IDEA.review.md — 獲取所有 review items
2. 讀取 docs/IDEA.md
3. 逐項執行每個 review item 的 Check，引用文件中的具體§章節

完成後必須輸出（格式嚴格，主 Claude 解析此區塊）：
REVIEW_RESULT:
  step_id: D01-IDEA
  type: IDEA
  round: {round}
  finding_total: N
  critical: N
  high: N
  medium: N
  low: N
  passed: true|false
  findings:
    - id: F-{N:02d}
      severity: CRITICAL|HIGH|MEDIUM|LOW
      section: "§X.Y"
      issue: "具體問題描述（引用文件內容）"
      fix_guide: "修復指引（來自 review.md 對應 item 的 Fix 段落）"
```

**Fix Subagent prompt（主 Claude 從 REVIEW_RESULT 提取 findings_text 後派送）：**

```
你是 IDEA 文件修復專家。
任務：依照以下 findings，精準修復 docs/IDEA.md。

本輪 Findings（Round {round}，共 {finding_total} 個）：
{findings_text}

執行步驟：
1. 讀取 docs/IDEA.md
2. 讀取 {_TEMPLATE_DIR}/IDEA.review.md 中對應 item 的 Fix 指引
3. 精準修復每個 finding（只修改 finding 指出的具體位置，不動其他部分）
4. 修復後驗證

完成後必須輸出：
FIX_RESULT:
  step_id: D01-IDEA
  type: IDEA
  round: {round}
  fixed:
    - id: F-{N:02d}
      action: "具體修復說明"
  unfixed:
    - id: F-{N:02d}
      reason: "無法修復的原因（若有）"
  summary: "一句話：本輪共修復 N 個 findings，主要修復了 ..."
```

```bash
fi  # 結束 Step 5.5 skip guard
```

---

## Step 5.6：生成 BRD.md（C-11/C-16）

### Skip Guard（P-01：避免已完成步驟重跑）

```bash
# ── P-01 Skip Guard：BRD ─────────────────────────────────────
_BRD_REVIEWED=$(python3 -c "
import json
try:
    d = json.load(open('${_STATE_FILE}'))
    print(str(d.get('brd_review_passed', False)))
except:
    print('False')
" 2>/dev/null || echo "False")

_SKIP_BRD_GEN=""
_RESUME_BRD_REVIEW=""

if [[ ",${_COMPLETED_NOW}," == *",D02-BRD,"* ]]; then
  if [[ "$_BRD_REVIEWED" == "True" ]]; then
    echo "[Skip P-01] D02-BRD 已完成且 review 通過，跳過 BRD 生成與 review"
    _SKIP_BRD_GEN="true"
  else
    echo "[Resume P-01] D02-BRD 已生成但 review 未通過，跳過生成，直接進入 review"
    _SKIP_BRD_GEN="true"
    _RESUME_BRD_REVIEW="true"
  fi
fi
```

### 舊版文件歸檔（C-16）

```bash
if [[ -z "$_SKIP_BRD_GEN" ]]; then
  if [[ -f "docs/BRD.md" ]]; then
    _TS=$(date +%Y%m%d-%H%M%S)
    mv "docs/BRD.md" "docs/req/old-BRD-${_TS}.md"
    echo "[Archive] 舊 docs/BRD.md → docs/req/old-BRD-${_TS}.md"
  fi
fi
```

### 呼叫 gendoc brd（C-11）

透過 **Skill tool** 呼叫 `gendoc`，args: `brd`（不得 inline 生成，生成規則由 `{_TEMPLATE_DIR}/BRD.gen.md` 定義）。

```bash
if [[ -z "$_SKIP_BRD_GEN" ]]; then
```

**以 Agent tool 建立 subagent**，prompt 填入以下內容：

> gendoc 子任務：生成 BRD.md  
> 專案目錄：`$_PROJECT_DIR`  
> State file：`$_PROJECT_DIR/$_STATE_FILE`  
>  
> 執行：1) cd 到專案目錄 2) 讀取 state file 確認 idea_review_passed: true 3) 用 Skill tool 執行 /gendoc，args: brd 4) 確認 docs/BRD.md 已寫入 5) 回報成功/失敗及行數

等 Agent 回傳後，繼續執行下方 bash。

gen-brd 完成後：

```bash
  python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['brd_generated'] = True
d['brd_path'] = 'docs/BRD.md'
if 'D02-BRD' not in d.get('completed_steps',[]):
    d.setdefault('completed_steps',[]).append('D02-BRD')
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
"
  git add docs/BRD.md && git commit -m "docs(gendoc-auto): init BRD" 2>/dev/null || true
fi
```

---

## Step 5.7：BRD Review Loop（C-12）

```bash
# 僅在 BRD 未曾 review 通過、或需要重跑 review 時執行
if [[ -z "$_SKIP_BRD_GEN" ]] || [[ -n "$_RESUME_BRD_REVIEW" ]]; then
```

主 Claude 直接驅動 Review → Fix → Round Summary → Commit loop（同 gendoc-flow Phase D-2）。

```bash
_MAX_ROUNDS=$(python3 -c "
import json
try: d=json.load(open('${_STATE_FILE}')); print(d.get('max_rounds',5))
except: print(5)
" 2>/dev/null || echo "5")
_REVIEW_STRATEGY=$(python3 -c "
import json
try: d=json.load(open('${_STATE_FILE}')); print(d.get('review_strategy','standard'))
except: print('standard')
" 2>/dev/null || echo "standard")
echo "[BRD Review] 策略：${_REVIEW_STRATEGY}，最多 ${_MAX_ROUNDS} 輪"
```

**Review → Fix → Round Summary → Commit loop（max_rounds 次）：**

```python
for round in range(1, max_rounds + 1):

    # ── Review Subagent ───────────────────────────────────
    review_result = spawn_review_agent("BRD", round)
    finding_total = review_result["finding_total"]
    critical      = review_result["critical"]
    high          = review_result["high"]
    medium        = review_result["medium"]
    low           = review_result["low"]
    findings      = review_result["findings"]

    # ── 判斷終止 ──────────────────────────────────────────
    terminate = False
    terminate_reason = ""
    if finding_total == 0:
        terminate = True; terminate_reason = "PASSED — finding=0"
    elif review_strategy == "rapid" and round >= 3:
        terminate = True; terminate_reason = "MAX_ROUNDS — rapid=3 已達"
    elif review_strategy == "tiered" and round >= 6 and (critical + high + medium) == 0:
        terminate = True; terminate_reason = "PASSED — tiered: CRITICAL+HIGH+MEDIUM=0"
    elif round >= max_rounds:
        terminate = True; terminate_reason = f"MAX_ROUNDS={max_rounds} 已達"

    # ── Fix Subagent（finding>0 時必執行）────────────────
    fix_result = None
    if finding_total > 0:
        fix_result = spawn_fix_agent("BRD", round, findings)
        unfixed_count = len(fix_result.get("unfixed", []))
        fixed_count   = len(fix_result.get("fixed", []))
    else:
        unfixed_count = 0; fixed_count = 0

    # ── Round Summary（commit 之前輸出）──────────────────
    status_icon = "✅ PASS" if finding_total == 0 else ("⚠️  MAX" if terminate else "🔄 CONT")
    print(f"""
┌─── D02-BRD Review Round {round}/{max_rounds} ───────────────────────────┐
│  Review：CRITICAL={critical} HIGH={high} MEDIUM={medium} LOW={low}  Total={finding_total}
│  Fix：   修復 {fixed_count} 個 / 殘留 {unfixed_count} 個（本輪未解）
│  本輪狀態：{status_icon}  {terminate_reason if terminate else '繼續下一輪'}
│  Fix summary：{fix_result['summary'] if fix_result else 'N/A（finding=0，無需修復）'}
└──────────────────────────────────────────────────────────────────────┘""")

    # ── Commit ───────────────────────────────────────────
    git add docs/BRD.md
    if finding_total == 0:
        git commit -m f"docs(gendoc-auto)[D02-BRD]: review-r{round} — PASS (0 findings)"
    else:
        git commit -m f"docs(gendoc-auto)[D02-BRD]: review-r{round} — fix {fixed_count}/{finding_total} findings"

    if terminate:
        break
```

更新 state：
```bash
python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['brd_review_passed'] = True
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
print('[state] brd_review_passed = True')
"
```

**Review Subagent prompt（主 Claude 用 Agent tool 派送）：**

```
你是 BRD 文件審查專家。
任務：依照 {_TEMPLATE_DIR}/BRD.review.md 的審查標準，審查 docs/BRD.md。

執行步驟：
1. 讀取 {_TEMPLATE_DIR}/BRD.review.md — 獲取所有 review items
2. 讀取 docs/IDEA.md（上游文件）
3. 讀取 docs/BRD.md
4. 逐項執行每個 review item 的 Check，引用文件中的具體§章節

完成後必須輸出（格式嚴格，主 Claude 解析此區塊）：
REVIEW_RESULT:
  step_id: D02-BRD
  type: BRD
  round: {round}
  finding_total: N
  critical: N
  high: N
  medium: N
  low: N
  passed: true|false
  findings:
    - id: F-{N:02d}
      severity: CRITICAL|HIGH|MEDIUM|LOW
      section: "§X.Y"
      issue: "具體問題描述（引用文件內容）"
      fix_guide: "修復指引（來自 review.md 對應 item 的 Fix 段落）"
```

**Fix Subagent prompt（主 Claude 從 REVIEW_RESULT 提取 findings_text 後派送）：**

```
你是 BRD 文件修復專家。
任務：依照以下 findings，精準修復 docs/BRD.md。

本輪 Findings（Round {round}，共 {finding_total} 個）：
{findings_text}

執行步驟：
1. 讀取 docs/BRD.md
2. 讀取 {_TEMPLATE_DIR}/BRD.review.md 中對應 item 的 Fix 指引
3. 精準修復每個 finding（只修改 finding 指出的具體位置，不動其他部分）
4. 修復後驗證

完成後必須輸出：
FIX_RESULT:
  step_id: D02-BRD
  type: BRD
  round: {round}
  fixed:
    - id: F-{N:02d}
      action: "具體修復說明"
  unfixed:
    - id: F-{N:02d}
      reason: "無法修復的原因（若有）"
  summary: "一句話：本輪共修復 N 個 findings，主要修復了 ..."
```

```bash
fi  # 結束 Step 5.7 skip guard
```

---

## Step 6：Handoff Banner + Handoff State（C-14/C-17）

### 寫入 Handoff State（C-17）

```bash
python3 -c "
import json; f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d['handoff']        = True
d['brd_path']       = 'docs/BRD.md'
d['idea_path']      = 'docs/IDEA.md'
d['req_dir']        = 'docs/req'
d['handoff_source'] = 'gendoc-auto'
# 標記 D01-IDEA + D02-BRD 已完成，讓 gendoc-flow 從 D03-PRD 開始
completed = d.get('completed_steps', [])
for step_id in ['D01-IDEA', 'D02-BRD', 'handoff']:
    if step_id not in completed:
        completed.append(step_id)
d['completed_steps'] = completed
json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)
print('[state] handoff state 已寫入（D01+D02 標記完成）')
"
```

### 展示 Handoff Banner（遵循 gendoc-shared §15，C-14）

```bash
_PROJECT_NAME=$(python3 -c "import json; d=json.load(open('${_STATE_FILE}')); print(d.get('project_name',''))" 2>/dev/null || echo "")
_INPUT_TYPE=$(python3 -c "import json; d=json.load(open('${_STATE_FILE}')); print(d.get('input_type',''))" 2>/dev/null || echo "")
_IDEA_LINES=$(wc -l < "docs/IDEA.md" 2>/dev/null || echo "0")
_BRD_LINES=$(wc -l < "docs/BRD.md" 2>/dev/null || echo "0")
```

展示 Banner（格式見 gendoc-shared §15）+ 從 BRD.md 提取摘要（Elevator Pitch、核心功能、成功指標）。

---

## Step 8：銜接 gendoc-flow（C-17）

```bash
echo "🚀 文件已準備就緒！"
echo "   docs/IDEA.md：已通過 Review"
echo "   docs/BRD.md：已通過 Review"
echo "   專案目錄：$(pwd)"
echo ""
echo "正在啟動 /gendoc-flow ..."
```

**立即用 Skill 工具呼叫 `gendoc-flow`**（不得輸出成文字，必須真正觸發工具）。

**若 Skill 工具未能自動觸發**：

立即輸出以下醒目提示（不可只在 prose 中提及）：

```bash
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  [P-08] gendoc-flow 需手動啟動                           ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  IDEA.md + BRD.md 已就緒，請在本 session 執行：          ║"
echo "║                                                          ║"
echo "║     /gendoc-flow                                         ║"
echo "║                                                          ║"
echo "║  若想從特定 step 開始，先執行 /gendoc-config 設定。      ║"
echo "╚══════════════════════════════════════════════════════════╝"
```

---

## Escalation Budget

每個子步驟（gen / review）維護連續失敗計數器。連續失敗 3 次時，立即停止並輸出：

```
STATUS: BLOCKED
REASON: [1-2 sentences — 具體說明卡在哪裡]
ATTEMPTED: [嘗試過什麼，最多 3 條]
RECOMMENDATION: [使用者下一步應做什麼]
```

計數器在子步驟成功時重置為 0。不計入因上游不存在（靜默跳過）而跳過的步驟。

---

## Confusion Protocol

以下情境觸發停止並詢問，不得猜測：
- 輸入來源衝突（多份 docs/req/* 說法矛盾，且無法判斷以哪份為準）
- 指令描述的功能範圍，可能對應兩種截然不同的架構方向
- 有破壞性操作（覆寫已有大量內容的文件）且範圍不明確

觸發時：在一句話內說明歧義，列出 2-3 個選項與各自取捨，等待使用者確認。
**不適用於**：routine 生成、小幅調整、明確指定了文件類型的呼叫。

**SPAWNED_SESSION 下的 Confusion Protocol**：若 `_SPAWNED` 為 `true`，不詢問使用者，改為選最保守選項並在輸出中說明「[SPAWNED] 自動選擇最保守選項：<選項說明>」。

---

## Completion Status Protocol

本 skill 完成時，以下列格式回報：

- **DONE** — 所有步驟完成，docs/IDEA.md + docs/BRD.md 通過 Review，gendoc-flow 已觸發
- **DONE_WITH_CONCERNS** — 完成，但有已知問題需使用者留意（逐一列出）
- **BLOCKED** — 無法繼續（見 Escalation Budget 格式）
- **NEEDS_CONTEXT** — 缺少必要資訊（明確說明缺什麼）

---

## 設計原則

1. **Iron Law** — 每份文件生成前讀取全部上游文件（累積鏈）；違反視為無效
2. **Template-driven** — IDEA.md 與 BRD.md 結構完全由 templates/*.md 決定；gendoc skill 只做流程編排
3. **Skill 委派** — 文件生成和 Review 各有專責 gen-*/review-* skill，gendoc 不做 inline 生成
4. **正確文件階層** — IDEA.md → IDEA Review → BRD.md → BRD Review → gendoc-flow（N-9）
5. **TF-02 斷點續行** — `completed_steps` 記錄已完成 STEP，重新執行時自動跳過
6. **全自動無問答** — 所有決策由 AI 自動推斷（SPAWNED 下強制），不詢問使用者
7. **附件完整保存** — 使用者提供的任何素材均存入 `docs/req/`，IDEA.md Appendix 記錄
8. **Never git add -A** — 只 stage 已知異動的特定檔案，不使用 `-A` 或 `.`

*此技能由 gendoc 維護。版本：2.1.0*
