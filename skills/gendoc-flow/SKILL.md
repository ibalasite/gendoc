---
name: gendoc-flow
description: |
  Template-driven document pipeline orchestrator（BRD 備妥後接手）。
  從 templates/pipeline.json 動態讀取步驟定義，對每份文件執行：
    專家 Gen subagent → commit(gen) →
    loop: 專家 Review subagent → 專家 Fix subagent → round summary → commit(review-rN) →
    check terminate → step summary → state update →
    total summary（全流水線完成後）
  Commit 時機：每輪 Review-Fix 結束必有一次 commit（含 finding=0 的 PASS 輪）。
  不含硬編碼文件類型；所有文件類型、順序、條件均由 templates/pipeline.json 定義。
  可由 gendoc-auto handoff 觸發，或在 BRD 已備妥時獨立呼叫。
version: 2.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - Skill
  - AskUserQuestion
  - TaskCreate
  - TaskUpdate
  - TaskGet
  - TaskList
---

# gendoc-flow v2 — Template-Driven Pipeline Orchestrator

```
Entry:   docs/BRD.md（必要）+ docs/IDEA.md（選用）
Source:  templates/pipeline.json（步驟定義）
         templates/{TYPE}.gen.md（生成規則）
         templates/{TYPE}.review.md（審查標準）

Per-step execution sequence（每個標準步驟）：
  1. Gen subagent     → 生成初稿    → commit(gen)
  2. Review subagent  → 發現問題
  3. Fix subagent     → 修復問題（finding>0 時執行）
  4. Round summary    → 輸出本輪摘要
  5. commit(review-rN)→ 必定執行（PASS 和 FIX 路徑都 commit）
  6. check terminate  → 若滿足終止條件則 break
  7. Phase D-3        → 步驟完成摘要 + state update
  [repeat 2-6 max_rounds 次]

Pipeline end：
  Total Pipeline Summary（不再額外 commit）

Main AI: 主 Claude 協調整條流水線，直到 pipeline 走完
```

**架構原則（不可違反）：**
- 文件類型、順序、條件 → 只在 `templates/pipeline.json` 定義
- 生成規則 → 只在 `templates/{TYPE}.gen.md` 定義
- 審查標準 → 只在 `templates/{TYPE}.review.md` 定義
- 本 skill → 只負責流程穩定，不硬編碼任何文件類型或輸出項目
- 新增文件類型：pipeline.json + 三件套（.md/.gen.md/.review.md），不需改 skill

---

## Iron Law

> **鐵律：每份文件生成前，gen subagent 必須讀取所有上游文件（累積鏈）。**
> 上游清單在 TYPE.gen.md frontmatter `upstream-docs` 中定義；若上游不存在則靜默跳過。
> 違反此鐵律的生成結果視為無效，必須重新生成。

---

## Step -1：版本自動更新檢查 + SPAWNED_SESSION 偵測

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

```bash
[ -n "$OPENCLAW_SESSION" ] && _SPAWNED="true" || _SPAWNED="false"
echo "SPAWNED_SESSION: $_SPAWNED"
[[ "$_SPAWNED" == "true" ]] && echo "[SPAWNED] 強制 full-auto，跳過互動提問"
```

---

## Step 0：Session Config（遵循 gendoc-shared §0）

```bash
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")

_EXEC_MODE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('execution_mode',''))
except: print('')
" 2>/dev/null || echo "")

_REVIEW_STRATEGY=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('review_strategy','standard'))
except: print('standard')
" 2>/dev/null || echo "standard")

_MAX_ROUNDS=$(python3 -c "
import json
try: print(int(json.load(open('${_STATE_FILE}')).get('max_rounds', 5)))
except: print(5)
" 2>/dev/null || echo "5")

_START_STEP=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('start_step', '0'))
except: print('0')
" 2>/dev/null || echo "0")

_COMPLETED=$(python3 -c "
import json
try: print(','.join(json.load(open('${_STATE_FILE}')).get('completed_steps',[])))
except: print('')
" 2>/dev/null || echo "")

_CLIENT_TYPE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('client_type',''))
except: print('')
" 2>/dev/null || echo "")

_CLIENT_TYPE_SOURCE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('client_type_source','auto'))
except: print('auto')
" 2>/dev/null || echo "auto")

echo "[Session] mode=${_EXEC_MODE} | strategy=${_REVIEW_STRATEGY} | max_rounds=${_MAX_ROUNDS}"
echo "[Session] start_step=${_START_STEP} | completed=[${_COMPLETED}] | client_type=${_CLIENT_TYPE:-（未設定，待推斷）} | ct_source=${_CLIENT_TYPE_SOURCE}"
```

**已有值**：沿用已設定，直接繼續。
**無值（首次）**：顯示標準選單（execution_mode + review_strategy），寫入 state。

---

### Step 0-C：client_type 自動推斷（P-13）

**若 `_CLIENT_TYPE` 為空或仍為舊格式 `none`，且來源非 `confirmed`/`manual`，才從 IDEA/BRD/PRD 掃描關鍵字自動決定。**
**若 `_CLIENT_TYPE_SOURCE` 為 `confirmed` 或 `manual`，直接跳過此步驟（使用者已明確確認，不允許被關鍵字覆寫）。**

> **設計原則**：有 UI 的專案比純後端多；預設應傾向「有 client」而非「無 client」。
> 只有在文件中完全找不到任何 UI 跡象時，才輸出 `api-only`。

```bash
if [[ "$_CLIENT_TYPE_SOURCE" == "confirmed" || "$_CLIENT_TYPE_SOURCE" == "manual" ]]; then
  echo "[P-13] ⏭️  client_type_source=${_CLIENT_TYPE_SOURCE}，跳過自動推斷（使用者已確認：${_CLIENT_TYPE}）"
elif [[ -z "$_CLIENT_TYPE" || "$_CLIENT_TYPE" == "none" ]]; then
  echo "[P-13] client_type 未設定或為舊格式，從 IDEA/BRD/PRD 自動推斷..."
  _CLIENT_TYPE=$(python3 - <<'PYEOF'
import os
texts = []
for f in ['docs/IDEA.md', 'docs/BRD.md', 'docs/PRD.md']:
    try: texts.append(open(f).read().lower())
    except: pass
combined = ' '.join(texts)

# ⚠️ 關鍵字清單統一定義於 gendoc-shared §13-B（R-09），此處使用完整版本
# GAME_KEYWORDS（優先判斷）→ client_type=game，觸發 AUDIO/ANIM 生成
game_keywords = [
    # 引擎/框架
    'game', 'arcade', 'unity', 'cocos', 'phaser', 'pixijs', 'godot', 'unreal',
    'canvas', 'webgl', 'opengl', 'directx', 'vulkan', 'metal',
    # 中文遊戲術語
    '遊戲', '魚機', '博弈', '遊藝', '投幣', '玩家', '角色', '場景',
    '卡牌', '棋牌', '捕魚', '電子遊戲', '老虎機', '水果機',
    '捕魚達人', '麻將', '鬥地主', '百家樂',
    # 遊戲機制
    'sprite', 'tilemap', 'collision', 'physics engine', 'particle system',
    '音效', '動畫', 'fps', 'render loop',
]
# UI_KEYWORDS → client_type=web（SaaS/管理後台/行動 App，不觸發 AUDIO/ANIM）
ui_keywords = [
    # 前端框架/技術
    'ui', 'ux', 'frontend', 'front-end', 'web', 'html', 'css',
    'react', 'vue', 'angular', 'svelte', 'nextjs', 'nuxt',
    # 行動 App
    'app', 'mobile', 'native', 'ios', 'android', 'flutter', 'swift', 'kotlin',
    'react native', 'expo',
    # 介面元件
    'interface', 'screen', 'display', 'dashboard', 'portal', 'panel',
    'page', 'view', 'layout', 'widget', 'button', 'form',
    '介面', '畫面', '螢幕', '顯示', '前端', '操作面板', '儀表板', '視覺',
    '按鈕', '頁面', '視窗', '彈窗', '選單', '使用者介面',
    # 嵌入式顯示
    'lcd', 'oled', 'touchscreen', '觸控', '嵌入式顯示',
    # 客戶端
    'client', '客戶端', '用戶端',
]
if any(kw in combined for kw in game_keywords):
    print('game')
elif any(kw in combined for kw in ui_keywords):
    print('web')
else:
    print('api-only')
PYEOF
  )

  if [[ "$_CLIENT_TYPE" == "game" ]]; then
    echo "[P-13] ✅ 偵測到遊戲關鍵字 → client_type=game（AUDIO/ANIM 將生成，PDD/VDD/FRONTEND/BDD-client 將執行）"
  elif [[ "$_CLIENT_TYPE" == "web" ]]; then
    echo "[P-13] ✅ 偵測到 UI 關鍵字 → client_type=web（PDD/VDD/FRONTEND/BDD-client 將執行，AUDIO/ANIM 跳過）"
  else
    echo "[P-13] ℹ️  未偵測到 UI 關鍵字 → client_type=api-only（PDD/VDD/FRONTEND/BDD-client 跳過）"
    echo "[P-13]    若專案實際有 UI，請執行 /gendoc-config 手動設定 client_type=web 或 client_type=game"
  fi

  # 寫入 state（原子寫入）
  python3 - <<PYEOF2
import json, os
f = '${_STATE_FILE}'
try: d = json.load(open(f))
except: d = {}
d['client_type'] = '${_CLIENT_TYPE}'
d['client_type_source'] = 'auto'   # P-14：標記為自動偵測，允許 D03-PRD 後重新驗證
tmp = f + '.tmp'
with open(tmp, 'w', encoding='utf-8') as fp:
    json.dump(d, fp, indent=2, ensure_ascii=False)
os.replace(tmp, f)
print('[P-13] client_type 已寫入 state：${_CLIENT_TYPE}（source=auto）')
PYEOF2
fi

echo "[Session] client_type 最終值：${_CLIENT_TYPE}"
```

---

### Step 0-E：Pipeline Hash 驗證（P-11）

```bash
_PIPELINE_HASH_CURRENT=$(python3 -c "
import hashlib, json
try:
    content = open('$_PIPELINE_FILE', 'rb').read()
    print(hashlib.sha256(content).hexdigest()[:16])
except:
    print('unknown')
" 2>/dev/null || echo "unknown")

_PIPELINE_HASH_STORED=$(python3 -c "
import json
try: print(json.load(open('$_STATE_FILE')).get('pipeline_hash',''))
except: print('')
" 2>/dev/null || echo "")

if [[ -n "$_PIPELINE_HASH_STORED" && "$_PIPELINE_HASH_STORED" != "$_PIPELINE_HASH_CURRENT" ]]; then
  echo "[P-11] ⚠️  Pipeline 版本已變更（${_PIPELINE_HASH_STORED} → ${_PIPELINE_HASH_CURRENT}）"
  echo "[P-11] 若有升級，已完成步驟的文件可能不符新版標準，建議人工確認 completed_steps。"
fi

# 更新 pipeline_hash
python3 -c "
import json, os
f='$_STATE_FILE'
try: d=json.load(open(f))
except: d={}
d['pipeline_hash'] = '$_PIPELINE_HASH_CURRENT'
tmp=f+'.tmp'
open(tmp,'w').write(json.dumps(d,indent=2,ensure_ascii=False))
os.replace(tmp,f)
" 2>/dev/null || true
echo "[Pipeline] hash：$_PIPELINE_HASH_CURRENT"
```

---

## Step 0-D：前置文件確認

```bash
_CWD="$(pwd)"
_TEMPLATE_DIR="${_TEMPLATE_DIR:-$_CWD/templates}"
_PIPELINE_FILE="${_TEMPLATE_DIR}/pipeline.json"
_BRD_OK=false
_IDEA_OK=false
[[ -s "$_CWD/docs/BRD.md"  ]] && _BRD_OK=true
[[ -s "$_CWD/docs/IDEA.md" ]] && _IDEA_OK=true

# ── 起點文件判斷 ──────────────────────────────────────────────────
# gendoc-flow 支援兩種合法起點：
#   Mode A（有 IDEA）：IDEA.md + BRD.md 俱全（gendoc-auto handoff 或使用者自備）
#   Mode B（BRD only）：只有 BRD.md，使用者已有明確 BRD 直接進流水線
# IDEA.md 不是強制必要文件，缺少時下游 Gen Agent 只讀 BRD.md 作為最高層需求來源。
# 唯一必要文件：BRD.md（沒有 BRD 什麼都做不了）

if [[ "$_IDEA_OK" == "true" && "$_BRD_OK" == "true" ]]; then
  echo "[Check] Mode A — IDEA.md + BRD.md 俱全，完整上游鏈可用"
elif [[ "$_IDEA_OK" == "false" && "$_BRD_OK" == "true" ]]; then
  echo "[Check] Mode B — 僅 BRD.md（無 IDEA.md），以 BRD 作為最高層需求來源繼續"
  echo "        [注意] 下游 Gen Agent 讀取 BRD.md 替代 IDEA.md 作為核心背景，文件品質可能略低"
  echo "        [提示] 若日後補充 IDEA.md，可從 D03-PRD 重跑以充分利用 IDEA 背景"
else
  echo "[錯誤] docs/BRD.md 不存在或為空——這是 gendoc-flow 唯一必要文件。"
  echo "       情境 1：自備 BRD：手動建立 docs/BRD.md 後呼叫 /gendoc-flow"
  echo "       情境 2：從頭開始：先執行 /gendoc-auto，它會自動生成 IDEA.md + BRD.md"
  exit 1
fi

echo "[Check] Pipeline manifest：${_PIPELINE_FILE}"

if [[ ! -f "$_PIPELINE_FILE" ]]; then
  echo "[錯誤] templates/pipeline.json 不存在：$_PIPELINE_FILE"
  echo "       請確認 gendoc 已正確安裝（./setup）。"
  exit 1
fi

# P-08：handoff 來源記錄（僅供日誌，不影響流程）
_HANDOFF=$(python3 -c "
import json
try: print(json.load(open('$_STATE_FILE')).get('handoff', False))
except: print(False)
" 2>/dev/null || echo "False")
if [[ "$_HANDOFF" == "True" ]]; then
  echo "[P-08] gendoc-auto handoff 模式"
else
  echo "[P-08] 獨立呼叫模式（直接以 BRD.md 起點執行）"
fi

echo "✅ 前置確認通過，讀取 pipeline manifest"
python3 -c "
import json
steps = json.load(open('$_PIPELINE_FILE'))['steps']
print(f'Pipeline：{len(steps)} 個步驟')
for s in steps:
    print(f\"  {s['id']} [{s['layer']}] condition={s['condition']}\")
"
```

---

## Step 1：Pipeline 主循環

**主 Claude 讀取 pipeline.json 取得 steps 清單，按序執行。**

```python
# 主 Claude 依序執行以下邏輯（pseudo-code，AI 理解並執行）
pipeline = load_json("templates/pipeline.json")["steps"]
start_num = extract_step_num(_START_STEP)  # "D06-EDD" → 6, "0" → 0
completed = _COMPLETED.split(",")

for step in pipeline:
    step_num = extract_step_num(step["id"])  # "D06-EDD" → 6
    
    # ── Skip ──────────────────────────────────────────────
    if step_num < start_num:
        print(f"[Skip] {step['id']} — 早於 start_step，略過")
        continue
    
    if step["id"] in completed:
        print(f"[Skip] {step['id']} — 已在 completed_steps，略過")
        continue
    
    if step.get("handled_by") == "gendoc-auto":
        # P-03：前置驗證 — 輸出文件必須真的存在
        expected_output = step["output"][0]
        if not file_exists_and_nonempty(expected_output):
            print(f"[ABORT P-03] {step['id']} 標示為 gendoc-auto 負責，但 {expected_output} 不存在。")
            print(f"             請先執行 /gendoc-auto 完成 IDEA/BRD 生成，再執行 /gendoc-flow。")
            exit(1)
        if step["id"] not in completed:
            print(f"[P-03] {step['id']} 補寫至 completed_steps（檔案存在但 state 未記錄）")
            update_state_completed(step["id"])
        print(f"[Skip] {step['id']} — 由 gendoc-auto 處理，{expected_output} 已確認存在，略過")
        continue
    
    # ── Condition ─────────────────────────────────────────
    # P-10/P-13：client_type 條件步驟跳過
    # 接受 'api-only'（新格式）和 'none'（舊格式 backward compat）
    _is_no_client = _CLIENT_TYPE in ("api-only", "none")
    _is_game = _CLIENT_TYPE == "game"

    def _archive_and_skip(step, reason_msg):
        for out_path in step.get("output", []):
            if file_exists_and_nonempty(out_path):
                import os, datetime
                ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                basename = os.path.basename(out_path.rstrip("/"))
                archive = f"docs/req/old-{basename}-{ts}"
                os.rename(out_path, archive)
                git_add_and_commit(archive, msg=f"chore(gendoc)[{step['id']}]: 歸檔殘檔（client_type={_CLIENT_TYPE}）")
                print(f"[P-10] client_type={_CLIENT_TYPE}，{out_path} 已歸檔至 {archive}")
        print(f"[Skip] {step['id']} — {reason_msg}，跳過")
        update_state_completed(step["id"])

    if step["condition"] == "client_type != none" and _is_no_client:
        _archive_and_skip(step, f"client_type={_CLIENT_TYPE}（no UI project）")
        continue

    # AUDIO/ANIM：僅遊戲專案生成（client_type=game）；web/api-only 跳過
    if step["condition"] == "client_type == game" and not _is_game:
        _archive_and_skip(step, f"client_type={_CLIENT_TYPE}（非遊戲專案，AUDIO/ANIM 不適用）")
        continue
    
    # ── P-02/P-04/P-05 Skip 5 重寫：review_progress 優先 ─────
    if _EXEC_MODE == "full-auto":
        _skip5_done = False
        _skip_gen_only = False
        _resume_from_round = 1
        
        _rev_prog = state.get('review_progress', {}).get(step["id"])
        
        if step.get("multi_file"):
            # P-04：multi-file 步驟（BDD）—— 檢查 review_progress
            if _rev_prog and _rev_prog.get('terminated'):
                print(f"[Skip P-04] {step['id']} — review 已完成（{_rev_prog['terminate_reason']}），略過")
                update_state_completed(step["id"])
                _skip5_done = True
            elif _rev_prog and not _rev_prog.get('terminated'):
                # 中斷在 review loop 中 → 跳 Gen，從未完成的下一輪繼續
                _resume_from_round = _rev_prog['rounds_done'] + 1
                print(f"[Resume P-04] {step['id']} — 從 Review Round {_resume_from_round} 繼續")
                _skip_gen_only = True
            # 若無 review_progress：Gen subagent 收到指令「只生成 output_glob 中不存在的檔」（增量模式）
        else:
            # P-02/P-05：single-file 步驟
            primary_output = step["output"][0]
            if file_exists_and_nonempty(primary_output):
                if _rev_prog and _rev_prog.get('terminated'):
                    # Review 確實跑完了 → 正常 skip
                    print(f"[Skip P-02] {step['id']} — {primary_output} 存在且 review 完成，略過")
                    update_state_completed(step["id"])
                    _skip5_done = True
                elif _rev_prog and not _rev_prog.get('terminated'):
                    # P-02：檔案在，review 跑到一半 → 跳 Gen，從下一輪繼續
                    _resume_from_round = _rev_prog['rounds_done'] + 1
                    print(f"[Resume P-02] {step['id']} — {primary_output} 存在，Review 從 Round {_resume_from_round} 繼續")
                    _skip_gen_only = True
                else:
                    # P-05：檔案在但從未 review（Gen commit 後中斷）→ 跳 Gen，從 Round 1 開始 review
                    print(f"[Resume P-05] {step['id']} — {primary_output} 存在但無 review 記錄，直接進 Review Round 1")
                    _skip_gen_only = True
                    _resume_from_round = 1
        
        if _skip5_done:
            continue
    
    # ── 執行步驟 ──────────────────────────────────────────
    # _skip_gen_only=True：略過 Gen，直接從 _resume_from_round 開始 Review
    execute_step(step, skip_gen=_skip_gen_only, resume_from_round=_resume_from_round)
    update_state_completed(step["id"])

    # ── P-14：D03-PRD 完成後重新驗證 client_type ──────────
    # 理由：Step 0-C 執行時 PRD 尚未生成（由 gendoc-flow 負責），
    #       若關鍵遊戲/UI 關鍵字僅出現在 PRD，初次偵測可能錯判。
    #       PRD 生成並審查完成後立即重新偵測，確保後續步驟條件正確。
    if step["id"] == "D03-PRD":
        _client_type_source = state.get("client_type_source", "auto")
        if _client_type_source not in ("manual", "confirmed"):  # P-13/P-14 不覆寫已確認值
            _CLIENT_TYPE_NEW = python3_detect_client_type()  # 重跑 P-13 偵測腳本
            if _CLIENT_TYPE_NEW != _CLIENT_TYPE:
                print(f"[P-14] ⚠️  client_type 重新偵測結果不同：{_CLIENT_TYPE} → {_CLIENT_TYPE_NEW}")
                print(f"[P-14]     PRD 內容提供了更明確的專案類型線索，已更新。")
                _CLIENT_TYPE = _CLIENT_TYPE_NEW
                # 原子寫入更新後的 client_type
                update_state_client_type(_CLIENT_TYPE)
            else:
                print(f"[P-14] ✅ client_type 確認一致（PRD 驗證後）：{_CLIENT_TYPE}")
```

**P-14 偵測腳本（與 Step 0-C 完全相同的 python3 block）：**

```python
# update_state_client_type 輔助函式（原子寫入）
def update_state_client_type(ct):
    import json, os
    f = _STATE_FILE
    try: d = json.load(open(f))
    except: d = {}
    d['client_type'] = ct
    d['client_type_source'] = 'auto'
    tmp = f + '.tmp'
    open(tmp,'w').write(json.dumps(d, indent=2, ensure_ascii=False))
    os.replace(tmp, f)
    print(f"[P-14] client_type 已更新至 state：{ct}")

# update_state_lang_stack 輔助函式（原子寫入，鎖定技術棧）
def update_state_lang_stack(lang_stack):
    import json, os, re
    f = _STATE_FILE
    try: d = json.load(open(f))
    except: d = {}
    d['lang_stack']        = lang_stack
    d['lang_stack_locked'] = True   # 鎖定後 P-15 不再覆寫
    tmp = f + '.tmp'
    open(tmp,'w').write(json.dumps(d, indent=2, ensure_ascii=False))
    os.replace(tmp, f)
    print(f"[P-15] lang_stack 已寫入 state 並鎖定：{lang_stack}")

# python3_extract_lang_stack 輔助函式（從 EDD.md 提取技術棧）
def python3_extract_lang_stack():
    import re
    try:
        content = open('docs/EDD.md', encoding='utf-8').read()
        # 優先：找「語言/框架（lang_stack）：<值>」這行
        m = re.search(r'(?:語言/框架|lang_stack)[（(]?[^）)]*[）)]?\s*[：:]\s*(.+)', content)
        if m:
            return m.group(1).strip().split('\n')[0].strip()
        # 次選：找「主要語言：<值>」
        m2 = re.search(r'主要語言\s*[：:]\s*(.+)', content)
        if m2:
            return m2.group(1).strip().split('\n')[0].strip()
        # 再次：找「Backend：<值>」或「技術棧」
        m3 = re.search(r'(?:Backend|技術棧|Tech Stack)\s*[：:]\s*(.+)', content)
        if m3:
            return m3.group(1).strip().split('\n')[0].strip()
        return ""
    except:
        return ""
```

**P-14 注意事項：**
- 若使用者透過 `/gendoc-config` 手動設定或確認 `client_type`，則 `client_type_source = "confirmed"`（或 `"manual"`），P-14 不覆寫
- 若 D03-PRD 是被 skip（P-02/P-05 resume），P-14 仍執行（PRD 已存在，可讀取）
- 若重新偵測結果改變，條件步驟（D04/D05/D10/D12b/D10b/D10c）的 skip/execute 判斷會以新值為準

    # ── P-15：D06-EDD 完成後提取並鎖定 lang_stack ──────────
    # 理由：EDD §語言/框架 決定的技術棧必須寫入 state 並鎖定，
    #       確保後續 test-plan、BDD、runbook、LOCAL_DEPLOY 使用相同技術棧，
    #       不因不同 AI 自行推斷而產生不同結果。
    if step["id"] == "D06-EDD":
        _lang_stack_current = state.get("lang_stack", "")
        _lang_stack_locked  = state.get("lang_stack_locked", False)
        if not _lang_stack_locked:
            # 從 EDD.md 提取技術棧（讀取 §語言/框架 或 lang_stack 行）
            _lang_stack_new = python3_extract_lang_stack()
            if _lang_stack_new and _lang_stack_new != "unknown":
                update_state_lang_stack(_lang_stack_new)
                print(f"[P-15] ✅ lang_stack 已從 EDD.md 提取並鎖定：{_lang_stack_new}")
            else:
                # N-06 Fallback：正規表達式失敗時，指示 Gen Agent 手動讀取
                print(f"[P-15] ⚠️  正規表達式均未能自動提取 lang_stack（現有值：{_lang_stack_current or '(空)'}）")
                print(f"[P-15] [FALLBACK — 必須執行] 請直接讀取 docs/EDD.md 的 §語言/框架 章節，")
                print(f"[P-15]   找出技術棧選型（例如 'Python/FastAPI + React/TypeScript'），")
                print(f"[P-15]   然後呼叫 update_state_lang_stack('<語言棧>') 寫入 state 並鎖定。")
                print(f"[P-15]   若 EDD.md 中也無明確聲明，以 EDD Gen Agent 在 §語言/框架 所選定的值填入，不得留空。")
        else:
            print(f"[P-15] ⏭️  lang_stack 已鎖定（{_lang_stack_current}），跳過提取")

---

## Step 1-C：特殊步驟（special_skill）

若 `step["special_skill"]` 存在（如 `gendoc-align-check`、`gendoc-gen-html`）：

```python
# P-09：special_skill 步驟 skip 判斷（使用 special_completed，比 file-exists 更可靠）
if step.get("special_skill"):
    _spec_done = state.get('special_completed', {}).get(step["id"], False)
    if _spec_done:
        print(f"[Skip P-09] {step['id']} — special_completed=true，略過")
        update_state_completed(step["id"])
        continue  # 繼續到下一步
    
    # P-09：執行前清除可能的半生成檔
    for out_path in step.get("output", []):
        if file_exists_and_nonempty(out_path):
            content = open(out_path).read()
            is_complete = False
            if step["id"] == "D17-HTML":
                is_complete = "</html>" in content and len(content) > 5000
            elif step["id"] == "D16-ALIGN":
                is_complete = ("## Summary" in content or "## 摘要" in content) and ("## Findings" in content or "## 發現" in content)
            else:
                is_complete = len(content) > 500  # 一般 fallback
            
            if is_complete:
                print(f"[P-09] {out_path} 結構完整（pre-check），若 special_completed 未設定可能是上次未寫入，繼續執行 special_skill 重新確認")
            else:
                print(f"[P-09] {out_path} 結構不完整（可能為半生成），清除後重新執行")
                os.remove(out_path)
```

```
用 Skill 工具呼叫 step["special_skill"]，不帶額外 args。
等待完成後：
  git add {step.output}
  # §8-B Pre-Commit Scan
  _BARE=$(python3 -c "import re,sys; from pathlib import Path; p=re.compile(r'(?<!\w)\{\{([A-Z][A-Z0-9_]*)\}\}(?!\s*[：:\-—])'); a=re.compile(r'\{\{.+?\}\}.*[：:\-—]'); total=sum(1 for f in Path('docs').glob('*.md') for l in f.read_text('utf-8').splitlines() if p.search(l) and not a.search(l)); print(total)" 2>/dev/null || echo "0")
  [[ "$_BARE" -gt "0" ]] && echo "[PRE-COMMIT BLOCKED] ${_BARE} 個裸 placeholder — 修復後重試" && exit 1
  git commit -m "{step.commit_prefix}: {special_skill} 完成"
```

```bash
# P-09：special_completed 標記（執行成功後才寫）
python3 -c "
import json, os
f='${_STATE_FILE}'
try: d=json.load(open(f))
except: d={}
d.setdefault('special_completed', {})['${step.id}'] = True
tmp=f+'.tmp'
open(tmp,'w').write(json.dumps(d,indent=2,ensure_ascii=False))
os.replace(tmp,f)
print('[P-09] special_completed[${step.id}] = True')
" 2>/dev/null || true
```

```python
update_state_completed(step["id"])
# 繼續下一步，不進入 gen→review loop。
```

---

## Step 1-D：標準步驟執行（gen → review loop → fix）

**以下是每個標準步驟（無 special_skill）的完整執行邏輯。**

### Phase D-1：Gen Subagent

**execute_step 參數說明（P-02/P-04/P-05 斷點續行）：**
- `skip_gen=False`（預設）：正常執行 Gen subagent → commit → Review loop
- `skip_gen=True`：略過 Phase D-1（Gen 不執行），直接從 Phase D-2 開始
- `resume_from_round=1`（預設）：Review loop 從 Round 1 開始
- `resume_from_round=N`：Review loop 從 Round N 開始（N-1 輪已完成）

主 Claude 在 `execute_step` 開頭應先讀取這兩個參數：

```python
if skip_gen:
    print(f"[Resume] {step.id} — skip_gen=True，直接進入 Phase D-2 Review Round {resume_from_round}")
    # 不執行 Phase D-1
else:
    # 正常執行 Phase D-1
    spawn_gen_agent(step)
    git_commit_gen(step)

# Phase D-2 從 resume_from_round 開始
for round in range(resume_from_round, max_rounds + 1):
    ...
```

**主 Claude 使用 Agent tool** 派送生成專家（依 TYPE 選角色），prompt 如下：

```
你是 [{TYPE}] 文件生成專家（角色依 templates/{TYPE}.gen.md 的 reviewer-roles 定義）。

你的任務：依照 templates/{TYPE}.gen.md 的規範，生成以下文件：
  {step.output}（多文件模式：{step.multi_file}）

執行步驟（不得跳過）：
1. 讀取 templates/{TYPE}.gen.md — 獲取生成規範、upstream-docs 清單、Self-Check Checklist
2. 讀取 templates/{TYPE}.md — 獲取文件結構模板
3. 讀取上游文件（Iron Law — 以下優先序）：
   a. 若 docs/IDEA.md 存在 → 讀取 IDEA.md，並讀取其 Appendix C 所列 docs/req/* 所有檔案
   b. 若 docs/IDEA.md **不存在** → 以 docs/BRD.md 作為最高層需求來源（BRD-only Mode），
      在生成文件的 §背景 / §目標 等章節中以 BRD 資訊填充
   c. upstream-docs 中其他上游文件照常讀取（不存在則靜默跳過）
4. 依生成規範逐章節生成輸出文件

多文件模式（multi_file=true）：
- 依 {TYPE}.gen.md 規範生成多個檔案（e.g., features/*.feature）
- 每生成一個文件輸出：GENERATED_FILE: {path}
- 所有文件遵循統一的命名規範（見 gen.md §2 命名規範）

多文件增量模式（P-04）：
- 若 state 中有 `multifile_plan[{step.id}]` 列表且部分檔案已存在：
  → 只生成**不存在**的檔案（skip 已存在且 non-empty 的）
  → 每生成一個檔案立即輸出：GENERATED_FILE: {path}
- 若 state 中無 multifile_plan 或列表為空：
  → 正常生成所有檔案，同時將計劃寫入 state['multifile_plan'][step_id]
- 生成每個文件後立即寫入 state['multifile_progress'][step_id][file_key] = 'generated'

品質要求：
- 所有章節必須有實質內容，禁止留 {{placeholder}} 或「待補」
- 數字必須具體（SLO 數字、test coverage 目標等）
- 上游文件的關鍵欄位必須提取並引用，不得遺漏
- 通過 gen.md Self-Check Checklist 所有項目

完成後必須輸出（格式嚴格）：
GEN_RESULT:
  step_id: {step.id}
  type: {TYPE}
  files_generated:
    - {path1}
    - {path2}
  sections_completed: N
  self_check_passed: true|false
  notes: "任何特殊情況或推斷說明（可選）"
```

Gen subagent 完成後，主 Claude：
```bash
# 依 step.output 和 step.output_glob（多文件）git add
_OUTPUT_GLOB="${step.output_glob:-${step.output[0]}}"
git add $_OUTPUT_GLOB 2>/dev/null || git add ${step.output} 2>/dev/null
# §8-B Pre-Commit Scan：掃描裸 placeholder，有則阻止 commit
_BARE=$(python3 -c "
import re,sys
from pathlib import Path
p=re.compile(r'(?<!\w)\{\{([A-Z][A-Z0-9_]*)\}\}(?!\s*[：:\-—])')
a=re.compile(r'\{\{.+?\}\}.*[：:\-—]')
total=0
for f in Path('docs').glob('*.md'):
    for l in f.read_text('utf-8').splitlines():
        if p.search(l) and not a.search(l):
            total+=1
            print(f'  [{f.name}] {l.strip()[:80]}',file=sys.stderr)
print(total)
" 2>/dev/null || echo "0")
[[ "$_BARE" -gt "0" ]] && echo "[PRE-COMMIT BLOCKED] ${_BARE} 個裸 placeholder — Gen Agent 先修復再 commit" && exit 1
git commit -m "${step.commit_prefix}: gen — {TYPE} 初稿生成"
```

---

### Phase D-2：Review → Fix → Round Summary → Commit Loop

**正確執行序：review → fix（若有 findings）→ round summary → commit → 判斷終止**

> 鐵律：每輪結束必有一次 commit（無論 PASS 或 FIX），round summary 在 commit 之前輸出。
> Fix 不因是最後一輪而跳過——只要有 findings，就先修，再 commit，再終止。

**主 Claude 執行以下 loop（max_rounds 次）：**

```python
for round in range(1, max_rounds + 1):
    
    # ── Step A: Review Subagent ───────────────────────
    review_result = spawn_review_agent(step, round)
    
    finding_total = review_result["finding_total"]
    critical      = review_result["critical"]
    high          = review_result["high"]
    medium        = review_result["medium"]
    low           = review_result["low"]
    findings      = review_result["findings"]
    
    # ── Step B: 判斷是否終止（先判斷，不跳過 Fix） ────────
    terminate = False
    terminate_reason = ""
    
    if finding_total == 0:
        terminate = True
        terminate_reason = "PASSED — finding=0"
    elif review_strategy == "tiered" and round >= 6 and (critical + high + medium) == 0:
        terminate = True
        terminate_reason = "PASSED — tiered: CRITICAL+HIGH+MEDIUM=0"
    elif round >= max_rounds:
        terminate = True
        terminate_reason = f"MAX_ROUNDS={max_rounds} 已達"
    elif review_strategy == "rapid" and round >= 3:
        terminate = True
        terminate_reason = "MAX_ROUNDS — rapid=3 已達"
    
    # ── Step C: Fix Subagent（finding>0 時必須執行，不跳過）──
    fix_result = None
    if finding_total > 0:
        fix_result = spawn_fix_agent(step, round, findings)
        # Fix 後更新 finding 計數（fix_result.unfixed 即殘留）
        unfixed_count = len(fix_result.get("unfixed", []))
        fixed_count   = len(fix_result.get("fixed", []))
    else:
        unfixed_count = 0
        fixed_count   = 0
    
    # ── Step D: Round Summary（commit 之前輸出）────────────
    # 每輪必須輸出，讓使用者和 log 都看到本輪結果
    status_icon = "✅ PASS" if finding_total == 0 else (
                  "⚠️  MAX" if terminate else "🔄 CONT")
    print(f"""
┌─── {step.id} Review Round {round}/{max_rounds} ─────────────────────────────┐
│  Review：CRITICAL={critical} HIGH={high} MEDIUM={medium} LOW={low}  Total={finding_total}
│  Fix：   修復 {fixed_count} 個 / 殘留 {unfixed_count} 個（本輪未解）
│  本輪狀態：{status_icon}  {terminate_reason if terminate else '繼續下一輪'}
│  Fix summary：{fix_result['summary'] if fix_result else 'N/A（finding=0，無需修復）'}
└─────────────────────────────────────────────────────────────────────┘""")
    
    # ── Step E: Commit（每輪必執行）+ P-02 review_progress 寫入 ──
    _OUTPUT_GLOB = step.get("output_glob") or step["output"][0]
    git add _OUTPUT_GLOB
    
    # P-06/P-12：依終止原因決定品質狀態
    quality_status = (
        "passed"   if finding_total == 0
        else "degraded" if (critical == 0 and high == 0)
        else "failed"
    )
    terminate_reason_code = (
        "zero_finding"  if finding_total == 0
        else "tiered_clean" if (review_strategy == "tiered" and round >= 6 and critical+high+medium == 0)
        else "max_rounds"   if (round >= max_rounds)
        else "rapid_cap"    if (review_strategy == "rapid" and round >= 3)
        else "in_progress"
    )
    
    # P-12：commit message trailer
    if finding_total == 0:
        commit_msg = f"{step.commit_prefix}: review-r{round} — PASS (0 findings)\n\nFinding-Total: 0\nTerminate-Reason: zero_finding\nQuality-Status: passed"
    else:
        commit_msg = f"{step.commit_prefix}: review-r{round} — fix {fixed_count}/{finding_total} findings\n\nFinding-Total: {finding_total}\nFinding-CHM: {critical}/{high}/{medium}\nTerminate-Reason: {terminate_reason_code}\nQuality-Status: {quality_status}"
    
    # §8-B Pre-Commit Scan（只掃 Fix 輪，PASS 輪也掃確保 review 未引入新 placeholder）
    _BARE=$(python3 -c "
import re,sys
from pathlib import Path
p=re.compile(r'(?<!\w)\{\{([A-Z][A-Z0-9_]*)\}\}(?!\s*[：:\-—])')
a=re.compile(r'\{\{.+?\}\}.*[：:\-—]')
total=0
for f in Path('docs').glob('*.md'):
    for l in f.read_text('utf-8').splitlines():
        if p.search(l) and not a.search(l):
            total+=1
            print(f'  [{f.name}] {l.strip()[:80]}',file=sys.stderr)
print(total)
" 2>/dev/null || echo "0")
    [[ "$_BARE" -gt "0" ]] && echo "[PRE-COMMIT BLOCKED] ${_BARE} 個裸 placeholder — Fix Agent 先修復再 commit" && exit 1
    git commit -m "{commit_msg}"
    
    # P-02/P-07：每輪 commit 後立即寫入 review_progress（原子寫入）
    python3 <<PYEOF
import json, os
f = '${_STATE_FILE}'
try:
    d = json.load(open(f))
except:
    d = {}
prog = d.setdefault('review_progress', {})
prog['${step.id}'] = {
    'rounds_done':        ${round},
    'max_rounds':         ${max_rounds},
    'strategy':           '${review_strategy}',
    'last_finding_total': ${finding_total},
    'last_CHM':           [${critical}, ${high}, ${medium}],
    'terminated':         ${terminate},
    'terminate_reason':   '${terminate_reason_code}',
    'quality_status':     '${quality_status}',
}
tmp = f + '.tmp'
with open(tmp, 'w', encoding='utf-8') as fp:
    json.dump(d, fp, indent=2, ensure_ascii=False)
os.replace(tmp, f)
print(f"[P-02] review_progress 已更新：round=${round}, terminated=${terminate}, quality=${quality_status}")
PYEOF
    
    # ── Step F: 終止判斷（commit 之後才 break）──────────────
    if terminate:
        break
    # 否則進入下一輪 Review
```

**Review Subagent prompt（主 Claude 派送）：**

```
你是 [{TYPE}] 文件審查專家（依 templates/{TYPE}.review.md 定義的 reviewer-roles）。

任務：依照 templates/{TYPE}.review.md 的審查標準，審查以下文件：
  {step.output}（多文件：{step.output_glob}）

執行步驟：
1. 讀取 templates/{TYPE}.review.md — 獲取所有 review items
2. 讀取被審查的文件（所有輸出文件）
3. 逐項執行每個 review item 的 Check：
   - 引用文件中的具體§章節
   - 說明通過或未通過的具體理由
4. 套用 Escalation Protocol（CRITICAL 未通過 → 停止後續低優先級審查）

完成後必須輸出（格式嚴格，主 Claude 將解析此區塊）：
REVIEW_RESULT:
  step_id: {step.id}
  type: {TYPE}
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
      item_ref: "[CRITICAL] 1 — 問題標題"
      section: "§X.Y"
      issue: "具體問題描述（引用文件內容）"
      fix_guide: "Fix 指引（來自 review.md 對應 item 的 Fix 段落）"
```

**Fix Subagent prompt（主 Claude 派送，findings_text 由主 Claude 從 REVIEW_RESULT 提取）：**

```
你是 [{TYPE}] 文件修復專家。

任務：依照以下 findings，精準修復文件中的具體問題。

本輪 Findings（Round {round}，共 {finding_total} 個）：
{findings_text}

被修復的文件：{step.output}（多文件：{step.output_glob}）

執行步驟（不得跳過）：
1. 讀取被修復的文件
2. 讀取 templates/{TYPE}.review.md 中對應 item 的 Fix 指引
3. 對每個 finding，執行精準修復：
   - 只修改 finding 指出的具體問題及其章節
   - 不修改 finding 未提及的部分（最小修改原則）
   - 保持文件整體結構、命名、格式不變
   - CRITICAL → 必須修復；HIGH → 必須修復；MEDIUM/LOW → 盡力修復
4. 修復後驗證：重讀修復段落，確認問題已解決
5. 多文件模式：同樣對所有相關 .feature 檔案執行修復

完成後必須輸出：
FIX_RESULT:
  step_id: {step.id}
  type: {TYPE}
  round: {round}
  fixed:
    - id: F-{N:02d}
      action: "具體修復說明（修改了哪個章節、加了什麼內容）"
  unfixed:
    - id: F-{N:02d}
      reason: "無法修復的原因（若有）"
  summary: "一句話：本輪共修復 N 個 findings，主要修復了 ..."
```

---

### Phase D-3：步驟完成 Summary + State 更新

所有輪次結束後（loop break 後），主 Claude 輸出步驟級摘要：

```
╔══════════════════════════════════════════════════════════════════╗
║  {step.id} — {step.type} ✅ 完成                                 ║
╠══════════════════════════════════════════════════════════════════╣
║  生成文件：{step.output} （多文件：{N} 個）                      ║
║  審查輪次：{rounds_completed} 輪（最大 {max_rounds}）             ║
║  終止原因：{terminate_reason}                                    ║
║  最終 Findings：CRITICAL={c} HIGH={h} MEDIUM={m} LOW={l}         ║
║  Git commits：{commit_count} 個（1 gen + {rounds_completed} review）║
╠══════════════════════════════════════════════════════════════════╣
║  各輪 Findings 趨勢：                                            ║
║    Gen → R1:{r1_total} → R2:{r2_total} → ... → Rn:{rn_total}    ║
╚══════════════════════════════════════════════════════════════════╝
```

```python
# P-06：若 quality_status == failed，顯示告警橫幅
if _q_status == 'failed':
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  ⚠️  {step.id} — 品質告警（MAX_ROUNDS + CRITICAL/HIGH 殘留）     ║
╠══════════════════════════════════════════════════════════════════╣
║  此文件仍有 CRITICAL/HIGH 未修復 findings，未標記為完成。        ║
║  建議：/gendoc-config → 從 {step.id} 重跑 → 選 exhaustive 策略  ║
╚══════════════════════════════════════════════════════════════════╝""")
```

**狀態說明：**
- `PASSED`：某輪 finding=0 → 品質達標
- `MAX_ROUNDS`：達最大輪次，仍有殘留 finding（CRITICAL/HIGH 需注意）
- `TIERED_PASS`：tiered 策略第 6 輪起 CRITICAL+HIGH+MEDIUM=0

**State file 原子更新（完成步驟記錄）：**

```bash
_NOW=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
python3 - <<PYEOF
import json, os, sys
f = '${_STATE_FILE}'
try:
    d = json.load(open(f))
except Exception:
    d = {}
# P-06：依 quality_status 決定是否加入 completed_steps
completed = d.get('completed_steps', [])
failed_steps = d.get('failed_steps', [])
step_id = '${step.id}'

prog = d.get('review_progress', {}).get(step_id, {})
_q_status = prog.get('quality_status', 'passed')

if _q_status == 'failed':
    # CRITICAL/HIGH 殘留 → 不標記完成，加入 failed_steps
    if step_id not in failed_steps:
        failed_steps.append(step_id)
    d['failed_steps'] = failed_steps
    print(f"[P-06] ⚠️  {step_id} review 達上限但仍有 CRITICAL/HIGH finding，標記為 failed（不加入 completed_steps）")
    print(f"[P-06] 建議：執行 /gendoc-config 選「從 {step_id} 重新開始」並改用 exhaustive 策略")
    # 繼續執行下一步（不 exit），但在 Total Summary 中會顯示告警
else:
    # passed 或 degraded（只剩 MEDIUM/LOW）→ 標記完成
    if step_id not in completed:
        completed.append(step_id)
    d['completed_steps'] = completed
    _status_label = 'PASSED' if _q_status == 'passed' else 'DEGRADED（殘留 MEDIUM/LOW）'
    print(f"[P-06] {step_id} → {_status_label}")

d['last_completed'] = step_id
d['last_updated'] = '${_NOW}'
# 原子寫入（防止部分寫入損毀）
tmp = f + '.tmp.$$'
try:
    with open(tmp, 'w', encoding='utf-8') as fp:
        json.dump(d, fp, ensure_ascii=False, indent=2)
    os.replace(tmp, f)
    print(f"✅ state 已更新：completed_steps=[{', '.join(completed)}]")
except Exception as e:
    print(f"❌ state 寫入失敗：{e}", file=sys.stderr)
    if os.path.exists(tmp):
        os.remove(tmp)
    sys.exit(1)
PYEOF
```

> **State 更新時機**：在步驟的所有 commits 完成之後才更新 state，確保 Git log 與 state 一致。
> 若 git commit 失敗，不更新 state（下次執行會自動重試該步驟）。

---

## Step 1-E：Pipeline 完整性驗證（P-15）

**在 Total Summary 之前執行，確保所有預期步驟都有記錄。**

```python
# P-15：Pipeline 完整性掃描
import json

with open(_STATE_FILE) as f:
    state = json.load(f)

completed_now = state.get("completed_steps", [])
failed_now = state.get("failed_steps", [])
processed = set(completed_now + failed_now)

# 根據 client_type 決定哪些步驟應該執行
expected_ids = []
for s in pipeline_steps:
    cond = s.get("condition", "always")
    if cond == "always":
        expected_ids.append(s["id"])
    elif cond == "client_type != none":
        if _CLIENT_TYPE not in ("api-only", "none"):
            expected_ids.append(s["id"])
    elif cond == "client_type == game":
        if _CLIENT_TYPE == "game":
            expected_ids.append(s["id"])

# 找出未處理的步驟（未在 completed 也未在 failed）
missing = [sid for sid in expected_ids if sid not in processed]

if missing:
    print(f"\n[P-15] ⚠️  發現以下步驟未見執行記錄（請確認是否真的完成）：")
    for sid in missing:
        print(f"  ✗ {sid}")
    print(f"  → 若確實遺漏，請執行 /gendoc-config 從該步驟重新開始")
    print(f"  → 若已執行但 state 未更新，可能是中斷時未寫入，重跑會自動 skip 已完成文件")
else:
    print(f"\n[P-15] ✅ Pipeline 完整性驗證通過：所有 {len(expected_ids)} 個預期步驟均有記錄")
```

---

## Step 2：Total Pipeline Summary

所有步驟完成後，主 Claude 輸出最終摘要（每個步驟的資料來自 Phase D-3 記錄）：

```
╔══════════════════════════════════════════════════════════════════════════╗
║  /gendoc-flow 完成 — {project_name}                                      ║
╠══════════════════════════════════════════════════════════════════════════╣
║  步驟               ║ 狀態             ║ 輪次 ║ 最終 Findings           ║
╠══════════════════════════════════════════════════════════════════════════╣
║  D03-PRD            ║ ✅ PASSED         ║  2   ║ C=0 H=0 M=0 L=1        ║
║  D04-PDD            ║ ⏩ SKIPPED*       ║  —   ║ —                      ║
║  D05-VDD            ║ ⏩ SKIPPED*       ║  —   ║ —                      ║
║  D06-EDD            ║ ✅ PASSED         ║  3   ║ C=0 H=0 M=0 L=0        ║
║  D07-ARCH           ║ ⚠️  MAX_ROUNDS    ║  5   ║ C=0 H=1 M=2 L=0        ║
║  ...                ║ ...              ║  ...  ║ ...                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Total commits：{N} 個（gen×{steps} + review×{total_rounds}）            ║
║  Total findings 修復：{total_fixed} 個                                   ║
║  殘留 findings（未修復）：{total_unfixed} 個                              ║
╚══════════════════════════════════════════════════════════════════════════╝
* client_type={_CLIENT_TYPE}（api-only）→ 跳過 PDD / VDD / FRONTEND / Client BDD / AUDIO / ANIM
  若專案有 UI，執行 /gendoc-config 手動設定 client_type=web（SaaS/App）或 client_type=game（遊戲）後重跑
* client_type={_CLIENT_TYPE}（web）→ 跳過 AUDIO / ANIM（SaaS/管理後台/行動 App 不需音效與動畫設計文件）
  若專案為遊戲，執行 /gendoc-config 手動設定 client_type=game 後重跑

已生成文件（依層次）：
  需求層：docs/BRD.md（已有）{若存在 → docs/IDEA.md（已有）}docs/PRD.md
  設計層：docs/EDD.md docs/ARCH.md diagrams/（UML×9+class-inventory）docs/API.md docs/SCHEMA.md [docs/FRONTEND.md] [docs/AUDIO.md] [docs/ANIM.md]
  品質層：docs/test-plan.md features/（BDD-server）docs/RTM.md
  運維層：docs/runbook.md docs/LOCAL_DEPLOY.md
  稽核層：docs/ALIGN_REPORT.md
  展示層：docs/pages/index.html（HTML 文件站）

建議下一步：
  ┌ 若有 MAX_ROUNDS 步驟且 CRITICAL/HIGH 殘留：
  │  → /gendoc-config 選「從 D{N} 重新開始」（用 exhaustive 策略）
  ├ 若全部 PASSED：
  │  → 執行 /gendoc-align-check 做最終跨文件對齊掃描
  │  → 或直接進入程式碼實作階段
  └ 若需要 HTML 文件網站：
     → /gendoc-gen-html 已由 D17 自動完成，瀏覽 docs/pages/index.html
```

```python
# P-06：列出品質不足的步驟
_failed = state.get('failed_steps', [])
if _failed:
    print(f"\n⚠️  以下步驟品質未達標（CRITICAL/HIGH finding 殘留）：")
    for fs in _failed:
        prog = state.get('review_progress', {}).get(fs, {})
        print(f"  {fs}：CHM={prog.get('last_CHM',[0,0,0])}，建議重跑（exhaustive 策略）")
    print(f"  → 執行 /gendoc-config 選「從 {_failed[0]} 重新開始」並選 exhaustive")
```

**Total Summary 之後不再有額外 commit**（每步驟的 commit 已在各自 Phase D-2 Step E 完成）。

---

## 專家角色對照表

主 Claude 在派送 Gen/Review/Fix subagent 時，依以下對照選擇合適的角色 persona：

| TYPE | Gen 專家 | Review 主審 |
|------|---------|------------|
| PRD | 資深 PM + UX Researcher | 資深 PM / BA |
| PDD | 資深 UX Designer | UX Architect |
| VDD | 資深 Visual Designer / Art Director | Art Director + Brand Strategist |
| EDD | 資深 Backend Architect | Backend Architect + Security Engineer |
| ARCH | 資深 System Architect | System Architect + SRE |
| API | 資深 API Designer | API Designer + Backend Engineer |
| SCHEMA | 資深 DBA | DBA + Backend Architect |
| FRONTEND | 資深 Frontend Architect | Frontend Architect + UX Engineer |
| AUDIO | 資深音效設計師（Senior Audio Designer） | 音效設計師 + 技術音效工程師 + QA 音效測試員 |
| ANIM | 資深技術動畫師（Senior Technical Animator） | 技術動畫師 + VFX 技術工程師 + 效能工程師 |
| test-plan | 資深 QA Architect | QA Architect + SRE |
| BDD-server | 資深 BDD Expert | BDD Expert + Backend Engineer |
| BDD-client | 資深 Frontend QA Expert | Frontend QA + BDD Expert |
| RTM | 資深 QA Architect | QA Architect + PM |
| runbook | 資深 SRE | SRE + DevOps Engineer |
| LOCAL_DEPLOY | 資深 DevOps Engineer | DevOps + Backend Engineer |

> 若 TYPE 不在此表，從 `templates/{TYPE}.review.md` frontmatter `reviewer-roles` 讀取角色。

---

## 附錄：多文件步驟處理（BDD）

BDD-server 和 BDD-client 是 multi_file=true 的步驟。處理差異：

**Gen 階段：**
- gen subagent 讀取 BDD-server.gen.md（或 BDD-client.gen.md）
- 依 gen.md 規範生成多個 .feature 檔案
- 每個 Feature File 對應一個功能模組（命名規範見 gen.md §2）
- 生成後輸出 GEN_RESULT.files_generated 清單

**Review 階段：**
- review subagent 讀取 BDD-server.review.md
- 審查所有 `features/*.feature` 或 `features/client/*.feature`
- REVIEW_RESULT.findings 中標注具體的 .feature 檔案路徑

**Fix 階段：**
- fix subagent 針對 findings 修改具體的 .feature 檔案
- 可能新增/刪除 Scenario，但不得刪除整個 .feature 檔案

**git commit：**
```bash
# §8-B Pre-Commit Scan — BDD
_BARE=$(python3 -c "
import re,sys
from pathlib import Path
p=re.compile(r'(?<!\w)\{\{([A-Z][A-Z0-9_]*)\}\}(?!\s*[：:\-—])')
a=re.compile(r'\{\{.+?\}\}.*[：:\-—]')
total=0
for f in list(Path('features').glob('*.feature'))+list(Path('features/client').glob('*.feature') if Path('features/client').exists() else []):
    for l in f.read_text('utf-8').splitlines():
        if p.search(l) and not a.search(l):
            total+=1
            print(f'  [{f.name}] {l.strip()[:80]}',file=sys.stderr)
print(total)
" 2>/dev/null || echo "0")
[[ "$_BARE" -gt "0" ]] && echo "[PRE-COMMIT BLOCKED] ${_BARE} 個裸 placeholder — Gen Agent 先修復再 commit" && exit 1

# BDD-server
_BDD_COUNT=$(ls features/*.feature 2>/dev/null | wc -l | tr -d ' ')
git add features/
git commit -m "test(gendoc)[D12-BDD-server]: gen — 生成 ${_BDD_COUNT} 個 .feature 檔案"

# BDD-client
_BDD_C_COUNT=$(ls features/client/*.feature 2>/dev/null | wc -l | tr -d ' ')
git add features/client/
git commit -m "test(gendoc)[D12b-BDD-client]: gen — 生成 ${_BDD_C_COUNT} 個 client .feature 檔案"
```
