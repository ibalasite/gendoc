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
  _STEP=$(python3 -c "import json; d=json.load(open('$_STATE')); print(d.get('start_step','0'))" 2>/dev/null || echo "0")
  _STRATEGY=$(python3 -c "import json; d=json.load(open('$_STATE')); print(d.get('review_strategy','standard'))" 2>/dev/null || echo "standard")

  echo ""
  echo "╔══════════════════════════════════════════════╗"
  echo "║  目前專案狀態                                  ║"
  echo "╠══════════════════════════════════════════════╣"
  printf "║  %-10s %-32s ║\n" "已完成至" "STEP ${_STEP}"
  printf "║  %-10s %-32s ║\n" "審查強度" "${_STRATEGY}"
  echo "╚══════════════════════════════════════════════╝"
fi
```

### 情境 B：找不到 state file

輸出：`尚未在此目錄執行過 /gendoc-auto，將建立全新設定。`，繼續進入 Step 1。

---

## Step 1：選擇目標

**注意：`gendoc-config` 本質上是互動式工具，固定以互動模式執行，不受 state file 中 `execution_mode` 影響。**

用 `AskUserQuestion` 詢問：

```
question: "你想做什麼？"
options:
  - "重新跑全部流程（從頭開始，保留文件）"
  - "從某個 STEP 重新開始"
  - "只更換審查強度（不重設進度）"
  - "手動設定 client_type（web / game / api-only）"
  - "清除全部設定（刪除所有 state file）"
```

---

## Step 2：依選擇分流

### 選「重新跑全部流程」

→ 設 `_NEW_STEP = "0"`，繼續 Step 3（審查強度）→ Step 4 寫入

---

### 選「從某個 STEP 重新開始」

用 `AskUserQuestion` 詢問：

```
question: "從哪個 STEP 重新開始？"
options:
  - "D01-IDEA：IDEA.md 生成"
  - "D01-IDEA-R：IDEA Review Loop"
  - "D02-BRD：BRD.md 生成"
  - "D02-BRD-R：BRD Review Loop"
  - "D03-PRD：PRD 生成"
  - "D03-PRD-R：PRD Review Loop"
  - "D04-PDD：PDD 生成（client_type≠none）"
  - "D04-PDD-R：PDD Review Loop"
  - "D05-VDD：VDD 視覺設計文件生成（client_type≠none）"
  - "D05-VDD-R：VDD Review Loop"
  - "D06-EDD：EDD 生成"
  - "D06-EDD-R：EDD Review Loop"
  - "D07-ARCH：ARCH 架構文件生成"
  - "D07-ARCH-R：ARCH Review Loop"
  - "D08-API：API 設計文件生成"
  - "D08-API-R：API Review Loop"
  - "D09-SCHEMA：Schema 設計文件生成"
  - "D09-SCHEMA-R：Schema Review Loop"
  - "D10-FRONTEND：FRONTEND 前端技術設計生成（client_type≠none）"
  - "D10-FRONTEND-R：FRONTEND Review Loop"
  - "D10b-AUDIO：AUDIO 音效設計文件生成（client_type=game）"
  - "D10b-AUDIO-R：AUDIO Review Loop"
  - "D10c-ANIM：ANIM 動畫特效設計文件生成（client_type=game）"
  - "D10c-ANIM-R：ANIM Review Loop"
  - "D11-test-plan：Test Plan 生成"
  - "D11-test-plan-R：Test Plan Review Loop"
  - "D12-BDD-server：Server BDD Feature Files 生成"
  - "D12-BDD-server-R：Server BDD Review Loop"
  - "D12b-BDD-client：Client BDD Feature Files 生成（client_type≠none）"
  - "D12b-BDD-client-R：Client BDD Review Loop"
  - "D13-RTM：RTM 需求追溯矩陣生成"
  - "D13-RTM-R：RTM Review Loop"
  - "D14-runbook：Runbook 生成"
  - "D14-runbook-R：Runbook Review Loop"
  - "D15-LOCAL_DEPLOY：LOCAL_DEPLOY 生成"
  - "D15-LOCAL_DEPLOY-R：LOCAL_DEPLOY Review Loop"
  - "D16-ALIGN：跨文件對齊掃描（align-check）"
  - "D16-ALIGN-F：對齊問題自動修復（align-fix）"
  - "D17-HTML：HTML 文件網站生成"
  - "D17-HTML-P：GitHub Pages 部署驗證"
```

→ 設 `_NEW_STEP = <使用者選擇的 STEP ID>`，繼續 Step 3 → Step 4

---

### 選「只更換審查強度」

→ 設 `_NEW_STEP = $_STEP`（維持現有進度），繼續 Step 3（審查強度）→ Step 4 寫入

---

### 選「手動設定 client_type」

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
  - "standard   — 最多 5 輪，任一輪 finding=0 提前結束（預設）"
  - "rapid      — 最多 3 輪，finding=0 提前結束"
  - "exhaustive — 無上限，持續至 finding=0"
  - "tiered     — 前 5 輪 finding=0；第 6 輪起 CRITICAL+HIGH+MEDIUM=0 即停"
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
  'review_strategy': 'standard',
  'max_rounds': 5,
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
# 若使用者手動設定了 client_type，覆寫自動偵測值
if '${_NEW_CLIENT_TYPE:-}':
    d['client_type'] = '${_NEW_CLIENT_TYPE}'
    d['client_type_source'] = 'manual'  # P-14：標記為手動設定，防止 D03-PRD 後被自動偵測覆寫
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
╚══════════════════════════════════════════════════════╝
```

[白話說明] 設定已儲存完成。執行 `/gendoc-auto` 或 `/gendoc-flow`，它會自動從 STEP {N} 以所設定的審查強度繼續。
