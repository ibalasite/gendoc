---
name: gendoc-config
description: |
  互動式設定專案的審查強度，並選擇從哪個 STEP 重新開始。
  無需手動編輯任何文件，全程對話引導。
  呼叫時機：user 說「重跑」「重設」「換嚴格模式」「我想重新開始」
  「設定 review 強度」「從第幾步重跑」「不滿意想重來」「清除設定」。
allowed-tools:
  - Bash
  - AskUserQuestion
---

# gendoc-config — 互動式專案設定

用對話引導方式重設審查強度、重跑起點、或清除全部設定。全程不需手動改任何文件。

**注意：此 skill 是 gendoc 套件中唯一的互動入口。所有其他 skill（gendoc-auto / gendoc-flow / gen-* / review-*）只讀取 state file 中的變數，不主動詢問使用者。**

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 0：讀取現況

```bash
_CWD="$(pwd)"
_STATE=""

# 找 state file（優先找目前 user+branch 的檔案）
_GIT_USER=$(git config user.name 2>/dev/null | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g' | cut -c1-20)
_GIT_BRANCH=$(git branch --show-current 2>/dev/null | tr '[:upper:]/' '[:lower:]-' | sed 's/[^a-z0-9-]//g' | cut -c1-30)
_NAMED_STATE="$_CWD/.gendoc-state-${_GIT_USER}-${_GIT_BRANCH}.json"

if [[ -f "$_NAMED_STATE" ]]; then
  _STATE="$_NAMED_STATE"
elif [[ -f "$_CWD/.gendoc-state.json" ]]; then
  _STATE="$_CWD/.gendoc-state.json"
fi
```

### 情境 A：找到 state file → 顯示現況

```bash
if [[ -n "$_STATE" ]]; then
  _STEP=$(python3 -c "import json; d=json.load(open('$_STATE')); print(d.get('start_step'))" 2>/dev/null)
  _STRATEGY=$(python3 -c "import json; d=json.load(open('$_STATE')); print(d.get('review_strategy'))" 2>/dev/null)
  _CT=$(python3 -c "import json; d=json.load(open('$_STATE')); print(d.get('client_type'))" 2>/dev/null)
  _CT_SOURCE=$(python3 -c "import json; d=json.load(open('$_STATE')); print(d.get('client_type_source'))" 2>/dev/null)

  echo ""
  echo "╔══════════════════════════════════════════════╗"
  echo "║  目前專案狀態                                  ║"
  echo "╠══════════════════════════════════════════════╣"
  printf "║  %-10s %-32s ║\n" "已完成至" "STEP ${_STEP}"
  printf "║  %-10s %-32s ║\n" "審查強度" "${_STRATEGY}"
  printf "║  %-10s %-32s ║\n" "client_type" "${_CT}（來源：${_CT_SOURCE}）"
  echo "╚══════════════════════════════════════════════╝"
fi
```

### 情境 B：找不到 state file

輸出：`尚未在此目錄執行過 /gendoc-auto，將建立全新設定。`

用 `AskUserQuestion` 詢問（此問題取代 gendoc-auto Step 1.8 的 client_type 偵測，確保首次設定正確）：

```
question: "請先確認專案類型（此為全流水線的關鍵設定，後續可用 /gendoc-config 修改）"
options:
  - "web（建議）— SaaS / 管理後台 / 行動 App（執行 PDD/FRONTEND/BDD-client，跳過 AUDIO/ANIM）"
  - "game — 遊戲專案（執行全部，含 AUDIO/ANIM）"
  - "api-only — 純後端 API 服務（跳過所有 client 側文件）"
```

取得 `_INIT_CLIENT_TYPE`（解析選項為 "web" / "game" / "api-only"）。

繼續進入 Step 1。

---

## Step 1：選擇目標（第一層）

**注意：`gendoc-config` 本質上是互動式工具，固定以互動模式執行，不受 state file 中 `execution_mode` 影響。**

**背景說明**：`AskUserQuestion` 每題最多 4 個選項，原本 6 個選項須拆成兩層。

用 `AskUserQuestion` 詢問：

```
question: "你想做什麼？"
options:
  - "重設流程進度（重新跑全部 / 從某步開始）"
  - "修改審查強度（不重設進度）"
  - "修改專案設定（client_type / Admin 後台）"
  - "清除全部設定（刪除所有 state file）"
```

---

## Step 1b：第二層選單（依第一層觸發）

### 第一層選「重設流程進度」→ 繼續詢問

用 `AskUserQuestion` 詢問：

```
question: "要從哪裡重新開始？"
options:
  - "重新跑全部流程（從頭，保留文件）"
  - "從某個 STEP 重新開始"
```

### 第一層選「修改專案設定」→ 繼續詢問

用 `AskUserQuestion` 詢問：

```
question: "要修改哪個設定？"
options:
  - "client_type（web / game / api-only）"
  - "has_admin_backend（Admin 後台開關）"
```

### 第一層選「修改審查強度」或「清除全部設定」→ 直接進入 Step 2

---

## Step 2：依選擇分流

### 選「重設流程進度」→「重新跑全部流程」

→ 設 `_NEW_STEP = "0"`，繼續 Step 3（審查強度）→ Step 4 寫入

---

### 選「重設流程進度」→「從某個 STEP 重新開始」

**[AI 指令]** 先執行以下 bash + python3 取得動態清單，再呼叫 `AskUserQuestion`：

```bash
# 1. 定位 pipeline.yml（local-first）；fallback 到 pipeline.json
_CWD="$(pwd)"
if [[ -f "$_CWD/templates/pipeline.yml" ]]; then
  _PIPELINE_FILE="$_CWD/templates/pipeline.yml"
elif [[ -f "$_CWD/templates/pipeline.json" ]]; then
  _PIPELINE_FILE="$_CWD/templates/pipeline.json"
elif [[ -f "$HOME/.claude/gendoc/templates/pipeline.yml" ]]; then
  _PIPELINE_FILE="$HOME/.claude/gendoc/templates/pipeline.yml"
elif [[ -f "$HOME/.claude/gendoc/templates/pipeline.json" ]]; then
  _PIPELINE_FILE="$HOME/.claude/gendoc/templates/pipeline.json"
else
  echo "⚠️  找不到 pipeline.yml 或 pipeline.json，無法動態產生 step 清單"; exit 1
fi

# 2. 從 pipeline.yml 生成 step 選項（gen + review-loop 兩行一組）
python3 - "$_PIPELINE_FILE" <<'PY'
import json, sys
try:
    import yaml
    if sys.argv[1].endswith('.yml'):
        pipe = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
    else:
        pipe = json.load(open(sys.argv[1], encoding="utf-8"))
except ImportError:
    pipe = json.load(open(sys.argv[1], encoding="utf-8"))
# 這些 special_skill 步驟沒有獨立的 review loop
SPECIAL = {
    "gendoc-gen-diagrams", "gendoc-align-check", "gendoc-align-fix",
    "gendoc-gen-contracts", "gendoc-gen-mock", "gendoc-gen-prototype", "gendoc-gen-html",
    "gendoc-gen-dryrun"
}
for s in pipe.get("steps", []):
    sid   = s["id"]
    stype = s["type"]
    cond  = s.get("condition", "always")
    note  = s.get("note", "")
    cond_str = f"（{cond}）" if cond != "always" else ""
    print(f"{sid}：{stype} 生成{cond_str}")
    if not s.get("special_skill"):
        print(f"{sid}-R：{stype} Review Loop")
PY
```

**[AI 指令]** 將 python3 每行輸出作為一個 option，呼叫：

```
AskUserQuestion(
  question: "從哪個 STEP 重新開始？",
  options: [<python3 輸出的每一行>]
)
```

→ 設 `_NEW_STEP = <使用者選擇文字中 `:` 前的 ID 部分>`，繼續 Step 3 → Step 4

---

### 選「修改審查強度」

→ 設 `_NEW_STEP = $_STEP`（維持現有進度），繼續 Step 3（審查強度）→ Step 4 寫入

---

### 選「修改專案設定」→「client_type」

用 `AskUserQuestion` 詢問：

```
question: "請選擇 client_type（影響 AUDIO / ANIM / FRONTEND / PDD / BDD-client 是否執行）"
options:
  - "web   — 一般 SaaS / 管理後台 / 行動 App（執行 PDD/FRONTEND/BDD-client，跳過 AUDIO/ANIM）"
  - "game  — 遊戲專案（執行全部，含 AUDIO/ANIM）"
  - "api-only — 純後端 API 服務（跳過所有 client 側文件）"
```

取得 `_NEW_CLIENT_TYPE`。

→ 維持 `_NEW_STEP = $_STEP`（不重設進度）
→ 直接跳到 Step 4 寫入（跳過 Step 3 審查強度）

---

### 選「修改專案設定」→「has_admin_backend」

用 `AskUserQuestion` 詢問：

```
question: "請設定 has_admin_backend（影響 ADMIN_IMPL 是否生成）"
options:
  - "true  — 需要 Admin 後台（生成 ADMIN_IMPL.md，預設 Vue3+ElementPlus+Vite）"
  - "false — 無需 Admin 後台（跳過 ADMIN_IMPL）"
```

取得 `_NEW_ADMIN_BACKEND`（`true` 或 `false`）。

→ 維持 `_NEW_STEP = $_STEP`（不重設進度）
→ 直接跳到 Step 4 寫入（跳過 Step 3 審查強度）

---

### 選「清除全部設定（刪除所有 state file）」

```bash
_COUNT=0
for f in "$_CWD"/.gendoc-state*.json; do
  [[ -f "$f" ]] && rm -f "$f" && _COUNT=$((_COUNT+1))
done
[[ -L "$_CWD/.gendoc-state.json" ]] && rm -f "$_CWD/.gendoc-state.json"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  設定已清除（Reset to Defaults）               ║"
echo "╠══════════════════════════════════════════════╣"
printf "║  %-44s ║\n" "已刪除 ${_COUNT} 個 state file，所有進度歸零。"
echo "╚══════════════════════════════════════════════╝"
```

→ 完成後直接結束，不進入 Step 3 / Step 4。

---

## Step 3：審查強度

用 `AskUserQuestion` 詢問：

```
question: "🔄 請選擇 Review 策略（影響每份文件的審查輪次）"
options:
  - "standard   — 最多 5 輪，任一輪 finding=0 提前結束（← 預設，建議新專案使用）"
  - "rapid      — 最多 3 輪，finding=0 提前結束（快速驗收，適合小型文件）"
  - "exhaustive — 無上限，持續至 finding=0（最嚴格，適合關鍵系統文件）"
  - "tiered     — 前 5 輪 finding=0；第 6 輪起 CRITICAL+HIGH+MEDIUM=0 即停（平衡嚴謹度）"
  - "custom     — 自訂終止條件"
```

若選 **custom**：再用 `AskUserQuestion`（無 options）詢問自訂條件，取得 `_NEW_STRATEGY_CUSTOM`。

取得 `_NEW_STRATEGY`。

換算 `max_rounds` 和 `stop_condition`：
```bash
case "$_NEW_STRATEGY" in
  rapid)      _NEW_MAX_ROUNDS=3  ; _NEW_STOP_CONDITION="任一輪 finding=0 或第 3 輪 fix 完" ;;
  standard)   _NEW_MAX_ROUNDS=5  ; _NEW_STOP_CONDITION="任一輪 finding=0 或第 5 輪 fix 完" ;;
  exhaustive) _NEW_MAX_ROUNDS=99 ; _NEW_STOP_CONDITION="finding=0（無上限）" ;;
  tiered)     _NEW_MAX_ROUNDS=99 ; _NEW_STOP_CONDITION="前 5 輪 finding=0；第 6 輪起 CRITICAL+HIGH+MEDIUM=0" ;;
  custom)     _NEW_MAX_ROUNDS=99 ; _NEW_STOP_CONDITION="$_NEW_STRATEGY_CUSTOM" ;;
  *)          _NEW_MAX_ROUNDS=5  ; _NEW_STOP_CONDITION="任一輪 finding=0 或第 5 輪 fix 完" ;;
esac
```

---

## Step 4：寫入 state file

```bash
# 若 state file 不存在，先建立最小初始 JSON
if [[ -z "$_STATE" ]]; then
  _STATE="$_CWD/.gendoc-state-${_GIT_USER}-${_GIT_BRANCH}.json"
  _NOW=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
  python3 -c "
import json
d = {
  'version': '1.0',
  'project_dir': '$_CWD',
  'start_step': '0',
  'execution_mode': 'full-auto',
  'max_rounds': 5,
  'client_type': '${_INIT_CLIENT_TYPE}',
  'client_type_source': 'confirmed',
  'last_updated': '$_NOW'
}
with open('$_STATE', 'w') as f: json.dump(d, f, indent=2)
"
  ln -sf "$_STATE" "$_CWD/.gendoc-state.json" 2>/dev/null || true
fi

# 原子寫入更新
_NOW=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
_TMP="${_STATE}.tmp.$$"
python3 - <<PYEOF
import json, os
with open('$_STATE') as f:
    d = json.load(f)
d['start_step']             = '${_NEW_STEP}'
d['execution_mode']         = 'full-auto'
d['review_strategy']        = '${_NEW_STRATEGY}'
d['review_strategy_custom'] = '${_NEW_STRATEGY_CUSTOM:-}'
d['max_rounds']             = ${_NEW_MAX_ROUNDS}
d['stop_condition']         = '${_NEW_STOP_CONDITION}'
d['last_updated']           = '$_NOW'
# 若使用者在 Step 2 手動設定了 client_type，覆寫自動偵測值
if '${_NEW_CLIENT_TYPE:-}':
    d['client_type'] = '${_NEW_CLIENT_TYPE}'
    d['client_type_source'] = 'confirmed'  # P-13/P-14 不再覆寫此值
# 若使用者手動設定了 has_admin_backend
if '${_NEW_ADMIN_BACKEND:-}' in ('true', 'false'):
    d['has_admin_backend'] = '${_NEW_ADMIN_BACKEND}' == 'true'
# 若是情境 B 首次建立（_INIT_CLIENT_TYPE 已寫入初始 JSON，此處不再重複寫入）
with open('$_TMP', 'w') as f:
    json.dump(d, f, indent=2)
os.replace('$_TMP', '$_STATE')
print("✅ 設定已儲存")
PYEOF
```

---

## Step 5：輸出摘要與下一步

```
╔══════════════════════════════════════════════════════╗
║  /gendoc-config 設定完成                              ║
╠══════════════════════════════════════════════════════╣
║  執行模式：full-auto                                  ║
║  審查強度：<_NEW_STRATEGY>（最多 <_NEW_MAX_ROUNDS> 輪）║
║  從 STEP：<_NEW_STEP> 開始                            ║
║  client_type：<_NEW_CLIENT_TYPE 若有設定，否則顯示「沿用自動偵測」> ║
║  has_admin_backend：<_NEW_ADMIN_BACKEND 若有設定，否則顯示「沿用現有值」> ║
╚══════════════════════════════════════════════════════╝
```

[白話說明] 設定已儲存完成。執行 `/gendoc-auto` 或 `/gendoc-flow`，它會自動從 STEP {N} 以所設定的審查強度繼續。
