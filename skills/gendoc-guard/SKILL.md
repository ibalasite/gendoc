---
name: gendoc-guard
description: 監控任意 skill 執行，session 中斷時自動排隊重新喚起。用法：/gendoc-guard <skill-name>
version: 1.0.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Skill
---

# gendoc-guard

```
Input:   /gendoc-guard <target-skill-name>
Output:  執行目標 skill，中斷時自動排隊下次 session 繼續
Purpose: 不修改任何目標 skill，外掛式監控 + 自動重啟
```

---

## Step 0：解析目標 Skill

```bash
# 從 args 取得目標 skill 名稱
_TARGET="${ARGS:-}"
if [ -z "$_TARGET" ]; then
  echo "[GUARD] ❌ 用法：/gendoc-guard <skill-name>"
  echo "         例如：/gendoc-guard gendoc-repair"
  exit 1
fi
echo "[GUARD] 目標 skill：/$_TARGET"
echo "[GUARD] 工作目錄：$(pwd)"
```

---

## Step 1：自我安裝（首次執行時安裝 Stop + SessionStart hook，之後 idempotent）

```python
import json, os, stat

HOME = os.path.expanduser('~')
BIN_DIR = os.path.join(HOME, '.claude', 'gendoc-guard', 'bin')
os.makedirs(BIN_DIR, exist_ok=True)

STOP_HOOK_PATH    = os.path.join(BIN_DIR, 'gendoc-guard-stop-hook.sh')
SESSION_HOOK_PATH = os.path.join(BIN_DIR, 'gendoc-guard-session-start.sh')
SETTINGS_PATH     = os.path.join(HOME, '.claude', 'settings.json')

# ── 寫 Stop hook script ────────────────────────────────────────────────────
STOP_HOOK_SCRIPT = r'''#!/usr/bin/env bash
# gendoc-guard Stop hook：偵測被中斷的 skill session，寫入 queue 等待下次喚起
set -euo pipefail

GUARD_FILE=".gendoc-guard.json"
QUEUE_FILE=".gendoc-guard-queue"

# 讀取 stdin（Stop hook 規範：必須 passthrough stdout）
RAW=$(cat)
printf '%s' "$RAW"

[ -f "$GUARD_FILE" ] || exit 0

# 解析 marker
STATUS=$(python3 -c "
import json, sys
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('status', ''))
except Exception:
    print('')
" 2>/dev/null)

[ "$STATUS" = "running" ] || exit 0

TARGET=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('target_skill', ''))
except Exception:
    print('')
" 2>/dev/null)

RETRY=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('retry_count', 0))
except Exception:
    print(0)
" 2>/dev/null)

MAX_RETRIES=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('max_retries', 5))
except Exception:
    print(5)
" 2>/dev/null)

CWD=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('cwd', '.'))
except Exception:
    print('.')
" 2>/dev/null)

if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
  >&2 echo "[GUARD] ⛔ /$TARGET 已達最大重試次數（$MAX_RETRIES），停止監控"
  # 通知使用者放棄
  osascript -e "display notification \"/$TARGET 達到最大重試 $MAX_RETRIES 次，請手動確認\" with title \"Gendoc Guard: 已停止\" sound name \"Basso\"" 2>/dev/null || true
  # 清除 marker
  python3 -c "
import json, os
d = json.load(open('$GUARD_FILE'))
d['status'] = 'max_retries_exceeded'
with open('$GUARD_FILE', 'w') as f:
    json.dump(d, f, indent=2)
"
  exit 0
fi

NEXT_RETRY=$((RETRY + 1))

# 更新 marker 的 retry_count（標示已排隊）
python3 - <<PYEOF
import json, os
from datetime import datetime, timezone
d = json.load(open('$GUARD_FILE'))
d['retry_count'] = $NEXT_RETRY
d['status'] = 'queued'
d['queued_at'] = datetime.now(timezone.utc).isoformat()
tmp = '$GUARD_FILE.tmp'
with open(tmp, 'w') as f:
    json.dump(d, f, indent=2)
os.replace(tmp, '$GUARD_FILE')
PYEOF

# 寫入 queue file（讓 SessionStart hook 讀取）
cat > "$QUEUE_FILE" <<QEOF
{
  "target_skill": "$TARGET",
  "retry_count": $NEXT_RETRY,
  "max_retries": $MAX_RETRIES,
  "cwd": "$CWD"
}
QEOF

>&2 echo ""
>&2 echo "╔══════════════════════════════════════════════════╗"
>&2 echo "║  [GENDOC-GUARD] /$TARGET session 中斷             ║"
>&2 echo "║  已排隊 (重試 $NEXT_RETRY/$MAX_RETRIES)           ║"
>&2 echo "║  下次開啟此目錄的 claude session 將自動繼續       ║"
>&2 echo "╚══════════════════════════════════════════════════╝"

# macOS 通知
osascript -e "display notification \"/$TARGET 中斷，下次開啟 session 將自動繼續 (重試 $NEXT_RETRY/$MAX_RETRIES)\" with title \"Gendoc Guard\" sound name \"Ping\"" 2>/dev/null || true
'''

# ── 寫 SessionStart hook script ───────────────────────────────────────────
SESSION_HOOK_SCRIPT = r'''#!/usr/bin/env bash
# gendoc-guard SessionStart hook：偵測 queue，inject additionalContext 自動喚起
set -euo pipefail

QUEUE_FILE=".gendoc-guard-queue"

# 讀取 stdin（SessionStart hook 規範：必須 passthrough）
RAW=$(cat)
printf '%s' "$RAW"

[ -f "$QUEUE_FILE" ] || exit 0

TARGET=$(python3 -c "
import json
try:
    d = json.load(open('$QUEUE_FILE'))
    print(d.get('target_skill', ''))
except Exception:
    print('')
" 2>/dev/null)

RETRY=$(python3 -c "
import json
try:
    d = json.load(open('$QUEUE_FILE'))
    print(d.get('retry_count', 1))
except Exception:
    print(1)
" 2>/dev/null)

MAX_RETRIES=$(python3 -c "
import json
try:
    d = json.load(open('$QUEUE_FILE'))
    print(d.get('max_retries', 5))
except Exception:
    print(5)
" 2>/dev/null)

[ -n "$TARGET" ] || exit 0

# 移除 queue file（避免重複觸發）
rm -f "$QUEUE_FILE"

# 更新 .gendoc-guard.json status 回 running（如果存在）
if [ -f ".gendoc-guard.json" ]; then
  python3 - <<PYEOF
import json, os
from datetime import datetime, timezone
try:
    d = json.load(open('.gendoc-guard.json'))
    d['status'] = 'running'
    d['resumed_at'] = datetime.now(timezone.utc).isoformat()
    tmp = '.gendoc-guard.json.tmp'
    with open(tmp, 'w') as f:
        json.dump(d, f, indent=2)
    os.replace(tmp, '.gendoc-guard.json')
except Exception:
    pass
PYEOF
fi

>&2 echo "[GUARD] 偵測到未完成任務：/$TARGET（重試 $RETRY/$MAX_RETRIES）"
>&2 echo "[GUARD] 自動注入 additionalContext 喚起..."

# 輸出 additionalContext 注入（覆蓋 stdout 的 passthrough）
# Note: SessionStart hook 的輸出 JSON 中 additionalContext 欄位會被注入到 session 開頭
python3 - <<PYEOF
import json, sys

# 讀原始 RAW（此處已在 bash 中 passthrough，需重新輸出 + additionalContext）
msg = (
    f"[GENDOC-GUARD RESUME] 上一個 session 執行 /{sys.argv[1]} 時中斷（重試 {sys.argv[2]}/{sys.argv[3]}）。"
    f"請立即執行 /gendoc-guard {sys.argv[1]} 繼續未完成的工作。"
    f"不要等待使用者指示，直接呼叫 Skill tool 執行 gendoc-guard，args=\"{sys.argv[1]}\"。"
)
out = {"additionalContext": msg}
print(json.dumps(out))
PYEOF "$TARGET" "$RETRY" "$MAX_RETRIES"
'''

# ── 寫入腳本檔案 ───────────────────────────────────────────────────────────
for path, content in [(STOP_HOOK_PATH, STOP_HOOK_SCRIPT), (SESSION_HOOK_PATH, SESSION_HOOK_SCRIPT)]:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[GUARD] ✅ 寫入：{path}")

# ── 更新 settings.json：加入 Stop + SessionStart hook ─────────────────────
try:
    with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {}

STOP_CMD    = f'bash {STOP_HOOK_PATH}'
SESSION_CMD = f'bash {SESSION_HOOK_PATH}'

def _hook_exists(hook_list, cmd):
    return any(
        h.get('command', '') == cmd
        for entry in hook_list
        for h in entry.get('hooks', [])
    )

hooks = settings.setdefault('hooks', {})

# Stop hook
stop_list = hooks.setdefault('Stop', [])
if not _hook_exists(stop_list, STOP_CMD):
    stop_list.append({
        "matcher": "*",
        "hooks": [{"type": "command", "command": STOP_CMD, "timeout": 10, "async": True}]
    })
    print("[GUARD] ✅ Stop hook 已安裝")
else:
    print("[GUARD] Stop hook 已存在，略過")

# SessionStart hook
start_list = hooks.setdefault('SessionStart', [])
if not _hook_exists(start_list, SESSION_CMD):
    start_list.append({
        "matcher": "*",
        "hooks": [{"type": "command", "command": SESSION_CMD, "timeout": 5, "async": False}]
    })
    print("[GUARD] ✅ SessionStart hook 已安裝")
else:
    print("[GUARD] SessionStart hook 已存在，略過")

# 寫回 settings.json（tmp 再 replace 確保原子性）
tmp = SETTINGS_PATH + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
os.replace(tmp, SETTINGS_PATH)
print(f"[GUARD] ✅ settings.json 更新完成")
```

---

## Step 2：建立監控 Marker

```python
import json, os
from datetime import datetime, timezone

_target = os.environ.get('_TARGET', '')
_guard_file = '.gendoc-guard.json'

# 讀取既有 marker（resume 模式）
_existing = {}
if os.path.exists(_guard_file):
    try:
        _existing = json.load(open(_guard_file, encoding='utf-8'))
    except Exception:
        _existing = {}

_retry_count = _existing.get('retry_count', 0) if _existing.get('target_skill') == _target else 0

marker = {
    "target_skill": _target,
    "status": "running",
    "phase": "invoking",
    "cwd": os.getcwd(),
    "started_at": datetime.now(timezone.utc).isoformat(),
    "retry_count": _retry_count,
    "max_retries": 5
}

with open(_guard_file, 'w', encoding='utf-8') as f:
    json.dump(marker, f, indent=2, ensure_ascii=False)

if _retry_count > 0:
    print(f"[GUARD] ♻️  Resume 模式（第 {_retry_count} 次重試）：寫入 marker")
else:
    print(f"[GUARD] ✅ 監控 marker 建立：{_guard_file}")
print(f"[GUARD] max_retries = {marker['max_retries']}")
```

---

## Step 3：呼叫目標 Skill

用 **Skill tool** 呼叫 `_TARGET`，不傳任何 args。

等待 Skill tool 回傳後才繼續 Step 4。

若目標 skill 回傳錯誤或 exception，記錄原因並繼續 Step 4（不中止）。

---

## Step 4：正常完成，清除 Marker

```python
import json, os
from datetime import datetime, timezone

_guard_file = '.gendoc-guard.json'

if os.path.exists(_guard_file):
    try:
        d = json.load(open(_guard_file, encoding='utf-8'))
        d['status'] = 'complete'
        d['completed_at'] = datetime.now(timezone.utc).isoformat()
        with open(_guard_file, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

print(f"\n[GUARD] ✅ /{os.environ.get('_TARGET','')} 正常完成，監控結束")
print(f"[GUARD] marker 狀態已更新為 complete")
print(f"[GUARD] Stop hook 不會觸發重啟（status=complete）")
```

---

## 附錄：Marker 格式

`.gendoc-guard.json` 存在於目標專案根目錄，不加入 git（應在 `.gitignore` 中排除）。

| 欄位 | 說明 |
|------|------|
| `target_skill` | 被監控的 skill 名稱 |
| `status` | `running` / `queued` / `complete` / `max_retries_exceeded` |
| `phase` | 當前執行階段（由目標 skill 自選更新，可選） |
| `cwd` | 目標專案目錄（Stop hook 使用） |
| `retry_count` | 已重啟次數 |
| `max_retries` | 最大重啟次數（預設 5） |

## 附錄：流程圖

```
/gendoc-guard gendoc-repair
      │
      ▼
Step 1：自安裝 Stop + SessionStart hook（idempotent）
      │
      ▼
Step 2：寫 .gendoc-guard.json {status: running}
      │
      ▼
Step 3：Skill tool → gendoc-repair
      │
      ├── 正常完成 ──→ Step 4：marker {status: complete} → 結束
      │
      └── session 中斷（context limit / crash / 手動結束）
                │
                ▼
           Stop hook 觸發
                │
                ├── retry >= max → 通知停止
                │
                └── retry < max → 寫 .gendoc-guard-queue，macOS 通知
                                        │
                                        ▼
                                  下次 claude session 開啟
                                        │
                                        ▼
                                  SessionStart hook
                                  讀 .gendoc-guard-queue
                                  inject additionalContext
                                        │
                                        ▼
                                  Claude 自動執行
                                  /gendoc-guard gendoc-repair
                                  （retry_count + 1）
```
