---
name: gendoc-guard
description: 監控任意 skill 執行，session 中斷時自動排隊重新喚起，並透過 SECS 白名單攔截未授權工具呼叫。用法：/gendoc-guard <skill-name>
version: 2.0.0
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
         + SECS：PreToolUse 攔截白名單外的工具呼叫
         + PostToolUse：記錄每次工具呼叫至 history
Purpose: 不修改任何目標 skill，外掛式監控 + 自動重啟 + 合規執行
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

## Step 1：自我安裝（首次執行時安裝四個 hook，之後 idempotent）

安裝以下四個 hook：
- **Stop hook**（已有）：中斷時寫 queue + macOS 通知
- **SessionStart hook**（已有）：讀 queue + inject additionalContext 喚起
- **PreToolUse hook**（新增）：SECS 白名單攔截
- **PostToolUse hook**（新增）：記錄工具呼叫 history

```python
import json, os, stat

HOME = os.path.expanduser('~')
BIN_DIR = os.path.join(HOME, '.claude', 'gendoc-guard', 'bin')
os.makedirs(BIN_DIR, exist_ok=True)

STOP_HOOK_PATH     = os.path.join(BIN_DIR, 'gendoc-guard-stop-hook.sh')
SESSION_HOOK_PATH  = os.path.join(BIN_DIR, 'gendoc-guard-session-start.sh')
BLOCKER_HOOK_PATH  = os.path.join(BIN_DIR, 'gendoc-guard-blocker-hook.sh')
HISTORY_HOOK_PATH  = os.path.join(BIN_DIR, 'gendoc-guard-history-hook.sh')
SETTINGS_PATH      = os.path.join(HOME, '.claude', 'settings.json')

# ── Stop hook ─────────────────────────────────────────────────────────────────
STOP_HOOK_SCRIPT = r'''#!/usr/bin/env bash
# gendoc-guard Stop hook：偵測被中斷的 skill session，寫入 queue 等待下次喚起
set -euo pipefail

GUARD_FILE=".gendoc-guard.json"
QUEUE_FILE=".gendoc-guard-queue"
HISTORY_FILE=".gendoc-guard-history.jsonl"

RAW=$(cat)
printf '%s' "$RAW"

[ -f "$GUARD_FILE" ] || exit 0

STATUS=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('status', ''))
except: print('')
" 2>/dev/null)

[ "$STATUS" = "running" ] || exit 0

TARGET=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('target_skill', ''))
except: print('')
" 2>/dev/null)

RETRY=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('retry_count', 0))
except: print(0)
" 2>/dev/null)

MAX_RETRIES=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('max_retries', 5))
except: print(5)
" 2>/dev/null)

CWD=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('cwd', '.'))
except: print('.')
" 2>/dev/null)

if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
  >&2 echo "[GUARD] ⛔ /$TARGET 已達最大重試次數（$MAX_RETRIES），停止監控"
  osascript -e "display notification \"/$TARGET 達到最大重試 $MAX_RETRIES 次，請手動確認\" with title \"Gendoc Guard: 已停止\" sound name \"Basso\"" 2>/dev/null || true
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

# 更新 marker retry_count → queued
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

# 寫 queue file（含最後 20 筆 history）
python3 - <<PYEOF
import json, os
from datetime import datetime, timezone

queue = {
    "target_skill": "$TARGET",
    "retry_count": $NEXT_RETRY,
    "max_retries": $MAX_RETRIES,
    "cwd": "$CWD",
    "queued_at": datetime.now(timezone.utc).isoformat(),
    "last_history": []
}

history_file = "$HISTORY_FILE"
if os.path.exists(history_file):
    try:
        lines = open(history_file).readlines()
        queue["last_history"] = [
            json.loads(l.strip()) for l in lines[-20:] if l.strip()
        ]
    except Exception:
        pass

with open("$QUEUE_FILE", "w") as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)
PYEOF

>&2 echo ""
>&2 echo "╔══════════════════════════════════════════════════╗"
>&2 echo "║  [GENDOC-GUARD] /$TARGET session 中斷             ║"
>&2 echo "║  已排隊 (重試 $NEXT_RETRY/$MAX_RETRIES)           ║"
>&2 echo "║  下次開啟此目錄的 claude session 將自動繼續       ║"
>&2 echo "╚══════════════════════════════════════════════════╝"

osascript -e "display notification \"/$TARGET 中斷，下次開啟 session 將自動繼續 (重試 $NEXT_RETRY/$MAX_RETRIES)\" with title \"Gendoc Guard\" sound name \"Ping\"" 2>/dev/null || true
'''

# ── SessionStart hook ─────────────────────────────────────────────────────────
SESSION_HOOK_SCRIPT = r'''#!/usr/bin/env bash
# gendoc-guard SessionStart hook：偵測 queue，inject additionalContext 自動喚起
set -euo pipefail

QUEUE_FILE=".gendoc-guard-queue"

RAW=$(cat)
printf '%s' "$RAW"

[ -f "$QUEUE_FILE" ] || exit 0

TARGET=$(python3 -c "
import json
try:
    d = json.load(open('$QUEUE_FILE'))
    print(d.get('target_skill', ''))
except: print('')
" 2>/dev/null)

RETRY=$(python3 -c "
import json
try:
    d = json.load(open('$QUEUE_FILE'))
    print(d.get('retry_count', 1))
except: print(1)
" 2>/dev/null)

MAX_RETRIES=$(python3 -c "
import json
try:
    d = json.load(open('$QUEUE_FILE'))
    print(d.get('max_retries', 5))
except: print(5)
" 2>/dev/null)

[ -n "$TARGET" ] || exit 0

rm -f "$QUEUE_FILE"

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

python3 - "$TARGET" "$RETRY" "$MAX_RETRIES" <<'PYEOF'
import json, sys, os

target, retry, max_retries = sys.argv[1], sys.argv[2], sys.argv[3]

# 讀取 queue 裡的 history（queue 已被 rm，從 .gendoc-guard.json 讀 secs_whitelist 狀態）
history_lines = []
if os.path.exists('.gendoc-guard-history.jsonl'):
    try:
        lines = open('.gendoc-guard-history.jsonl').readlines()
        history_lines = [json.loads(l.strip()) for l in lines[-20:] if l.strip()]
    except Exception:
        pass

history_summary = ''
if history_lines:
    parts = []
    for r in history_lines:
        ts = r.get('ts', '')[:19]
        tool = r.get('tool', '')
        summary = r.get('summary', '')[:80]
        parts.append(f'  {ts} {tool} {summary}')
    history_summary = f'\n最後 {len(history_lines)} 筆工具呼叫記錄：\n' + '\n'.join(parts)

msg = (
    f"[GENDOC-GUARD RESUME] 上一個 session 執行 /{target} 時中斷（重試 {retry}/{max_retries}）。"
    f"請立即執行 /gendoc-guard {target} 繼續未完成的工作。"
    f"不要等待使用者指示，直接呼叫 Skill tool 執行 gendoc-guard，args=\"{target}\"。"
    + history_summary
)
print(json.dumps({"additionalContext": msg}))
PYEOF
'''

# ── PreToolUse SECS 攔截 hook ─────────────────────────────────────────────────
BLOCKER_HOOK_SCRIPT = r'''#!/usr/bin/env bash
# gendoc-guard PreToolUse hook: SECS whitelist enforcement
# exit 2 = block tool call; exit 0 = allow
set -eo pipefail

GUARD_FILE=".gendoc-guard.json"

# Passthrough stdin
RAW=$(cat)
printf '%s' "$RAW"

[ -f "$GUARD_FILE" ] || exit 0

STATUS=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('status', ''))
except: print('')
" 2>/dev/null)

[ "$STATUS" = "running" ] || exit 0

# Write to temp file for safe parsing
TMPFILE=$(mktemp /tmp/gendoc-secs-XXXXXX.json 2>/dev/null || echo "/tmp/gendoc-secs-$$.json")
printf '%s' "$RAW" > "$TMPFILE"
trap 'rm -f "$TMPFILE"' EXIT

python3 - "$TMPFILE" "$GUARD_FILE" <<'SECS_EOF'
import json, sys, re

tmpfile, guard_file = sys.argv[1], sys.argv[2]

try:
    call  = json.loads(open(tmpfile).read())
    guard = json.load(open(guard_file))
except Exception:
    sys.exit(0)

if guard.get('status') != 'running':
    sys.exit(0)

tool = call.get('tool_name', '')
inp  = call.get('tool_input', {})
wl   = guard.get('secs_whitelist', {})

# 若尚未建立白名單（skill SKILL.md 找不到），跳過檢查
if not wl:
    sys.exit(0)

allowed_skills = set(wl.get('skill_calls', []))
known_fns      = set(wl.get('known_functions', []))
allow_ipy_wr   = wl.get('allow_inline_python_write', False)

WRITE_PATS = [
    r"open\s*\([^)]*['\"][wa]['\"]",
    r"json\.dump\s*\(",
    r"\.write\s*\(",
    r"os\.replace\s*\(",
    r"os\.rename\s*\(",
]

def has_write(code):
    return any(re.search(p, code) for p in WRITE_PATS)

def block(reason):
    target = guard.get('target_skill', '?')
    sys.stderr.write(f'\n╔══════════════════════════════════════════════════╗\n')
    sys.stderr.write(f'║  [SECS] BLOCKED: /{target}                        \n')
    sys.stderr.write(f'║  {reason[:80]}\n')
    if allowed_skills:
        sys.stderr.write(f'║  Whitelisted skills: {sorted(allowed_skills)}\n')
    sys.stderr.write(f'╚══════════════════════════════════════════════════╝\n')
    sys.exit(2)

# === Skill tool: 白名單檢查 ===
if tool == 'Skill':
    name = inp.get('skill', '')
    if name and allowed_skills and name not in allowed_skills:
        block(f'Skill "{name}" 不在白名單。允許：{sorted(allowed_skills)}')
    sys.exit(0)

# === Bash tool: inline Python 檢查 ===
if tool == 'Bash':
    cmd = inp.get('command', '')

    # 提取 heredoc 方式的 inline Python
    hdocs = re.findall(
        r'python3?\s+-\s+<<[\'"]?(\w+)[\'"]?\n(.*?)\n\1',
        cmd, re.DOTALL
    )
    codes = [code for _, code in hdocs]

    # 提取 python3 -c '...' 方式
    for m in re.finditer(r"python3?\s+-c\s+['\"]([^'\"]{20,})['\"]", cmd, re.DOTALL):
        codes.append(m.group(1))

    for code in codes:
        n_lines = code.count('\n') + 1

        # 規則 1：行數上限
        if n_lines > 30:
            block(f'Inline Python {n_lines} 行 > 30 行上限 — 應透過 Skill tool 執行')

        # 規則 2：stdout.reconfigure（已知 SSOT 繞過特徵）
        if 'sys.stdout.reconfigure' in code:
            block('sys.stdout.reconfigure 在 inline Python 中 — 已知 SSOT 繞過模式')

        # 規則 3：inline write 但 SKILL.md 無此授權
        if has_write(code) and not allow_ipy_wr:
            block('Inline Python 含寫檔操作，但目標 SKILL.md 不包含 inline write — 繞過嘗試')

        # 規則 4：重新定義 SKILL.md 已知函式
        for fn in known_fns:
            if re.search(rf'\bdef\s+{re.escape(fn)}\b', code):
                block(f'重新定義 SKILL.md 函式 "{fn}" — 應直接呼叫 Skill tool')

sys.exit(0)
SECS_EOF
'''

# ── PostToolUse history 記錄 hook ─────────────────────────────────────────────
HISTORY_HOOK_SCRIPT = r'''#!/usr/bin/env bash
# gendoc-guard PostToolUse hook: 記錄工具呼叫 history
set -eo pipefail

GUARD_FILE=".gendoc-guard.json"
HISTORY_FILE=".gendoc-guard-history.jsonl"

RAW=$(cat)
printf '%s' "$RAW"

[ -f "$GUARD_FILE" ] || exit 0

STATUS=$(python3 -c "
import json
try:
    d = json.load(open('$GUARD_FILE'))
    print(d.get('status', ''))
except: print('')
" 2>/dev/null)

[ "$STATUS" = "running" ] || exit 0

python3 - "$RAW" "$HISTORY_FILE" <<'HIST_EOF'
import json, sys, os
from datetime import datetime, timezone

raw, history_file = sys.argv[1], sys.argv[2]

try:
    call = json.loads(raw)
except Exception:
    sys.exit(0)

tool = call.get('tool_name', '')
inp  = call.get('tool_input', {})
res  = call.get('tool_result', {})

summary = ''
if tool == 'Bash':
    summary = inp.get('command', '')[:120].replace('\n', ' ')
elif tool in ('Write', 'Edit'):
    summary = inp.get('file_path', '')
elif tool == 'Skill':
    summary = f"skill:{inp.get('skill', '')}"
elif tool == 'Read':
    summary = inp.get('file_path', '')
else:
    summary = str(inp)[:80]

record = {
    'ts':      datetime.now(timezone.utc).isoformat(),
    'tool':    tool,
    'result':  res.get('type', '') if isinstance(res, dict) else '',
    'summary': summary,
}

with open(history_file, 'a', encoding='utf-8') as f:
    f.write(json.dumps(record, ensure_ascii=False) + '\n')

# 截斷至最多 500 筆
try:
    lines = open(history_file, encoding='utf-8').readlines()
    if len(lines) > 500:
        with open(history_file, 'w', encoding='utf-8') as f:
            f.writelines(lines[-500:])
except Exception:
    pass
HIST_EOF
'''

# ── 寫入腳本檔案 ───────────────────────────────────────────────────────────────
scripts = [
    (STOP_HOOK_PATH,    STOP_HOOK_SCRIPT),
    (SESSION_HOOK_PATH, SESSION_HOOK_SCRIPT),
    (BLOCKER_HOOK_PATH, BLOCKER_HOOK_SCRIPT),
    (HISTORY_HOOK_PATH, HISTORY_HOOK_SCRIPT),
]
for path, content in scripts:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[GUARD] ✅ 寫入：{path}")

# ── 更新 settings.json：加入四個 hook ─────────────────────────────────────────
try:
    with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {}

STOP_CMD     = f'bash {STOP_HOOK_PATH}'
SESSION_CMD  = f'bash {SESSION_HOOK_PATH}'
BLOCKER_CMD  = f'bash {BLOCKER_HOOK_PATH}'
HISTORY_CMD  = f'bash {HISTORY_HOOK_PATH}'

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

# PreToolUse SECS 攔截 hook
pre_list = hooks.setdefault('PreToolUse', [])
if not _hook_exists(pre_list, BLOCKER_CMD):
    pre_list.append({
        "matcher": "*",
        "hooks": [{"type": "command", "command": BLOCKER_CMD, "timeout": 10, "async": False}]
    })
    print("[GUARD] ✅ PreToolUse SECS hook 已安裝")
else:
    print("[GUARD] PreToolUse SECS hook 已存在，略過")

# PostToolUse history hook
post_list = hooks.setdefault('PostToolUse', [])
if not _hook_exists(post_list, HISTORY_CMD):
    post_list.append({
        "matcher": "*",
        "hooks": [{"type": "command", "command": HISTORY_CMD, "timeout": 5, "async": True}]
    })
    print("[GUARD] ✅ PostToolUse history hook 已安裝")
else:
    print("[GUARD] PostToolUse history hook 已存在，略過")

# 原子寫回 settings.json
tmp = SETTINGS_PATH + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
os.replace(tmp, SETTINGS_PATH)
print(f"[GUARD] ✅ settings.json 更新完成（4 個 hook 已安裝）")
```

---

## Step 2：建立監控 Marker

```python
import json, os
from datetime import datetime, timezone

_target = os.environ.get('_TARGET', '')
_guard_file = '.gendoc-guard.json'

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
    "max_retries": 5,
    "secs_whitelist": {}
}

with open(_guard_file, 'w', encoding='utf-8') as f:
    json.dump(marker, f, indent=2, ensure_ascii=False)

if _retry_count > 0:
    print(f"[GUARD] ♻️  Resume 模式（第 {_retry_count} 次重試）：寫入 marker")
else:
    print(f"[GUARD] ✅ 監控 marker 建立：{_guard_file}")
print(f"[GUARD] max_retries = {marker['max_retries']}")
```

## Step 2.5：SECS 白名單靜態分析

分析目標 skill 的 `SKILL.md`，提取允許的工具呼叫清單，寫入 `.gendoc-guard.json`。

```python
import json, os, re
from pathlib import Path

_target = os.environ.get('_TARGET', '')
_guard_file = '.gendoc-guard.json'

def _extract_whitelist(path, depth=0, visited=None):
    """從 SKILL.md 靜態分析提取白名單，遞迴展開 sub-skill。"""
    if visited is None:
        visited = set()
    key = str(path)
    if key in visited or depth > 3:
        return {}
    visited.add(key)

    try:
        content = open(path, encoding='utf-8').read()
    except Exception:
        return {}

    result = {
        'tool_types': set(),
        'skill_calls': set(),
        'known_functions': set(),
        'allow_inline_python_write': False,
    }

    # 從 frontmatter 提取 allowed-tools
    fm = re.search(r'^---\n(.+?)\n---', content, re.DOTALL)
    if fm:
        for t in re.findall(r'- (\S+)', fm.group(1)):
            if t not in ('name', 'description', 'version'):
                result['tool_types'].add(t)

    # Skill 呼叫：中英文自然語言描述
    for m in re.finditer(
        r'(?:Skill\s+tool[^`\n]{0,40}`([a-zA-Z0-9_-]+)`'
        r'|呼叫\s+`([a-zA-Z0-9_-]+)`'
        r'|→\s+([a-zA-Z][a-zA-Z0-9_-]+)\s+skill'
        r'|/([a-zA-Z][a-zA-Z0-9_-]+)\s)',
        content
    ):
        name = next((g for g in m.groups() if g), None)
        if name and ('-' in name or name.startswith('gendoc')):
            result['skill_calls'].add(name)

    # 從所有 code block 分析
    code_blocks = re.findall(r'```(?:python|bash|sh|py)?\n(.*?)```', content, re.DOTALL)
    WRITE_PATS = [
        r"open\s*\([^)]*['\"][wa]",
        r"json\.dump\s*\(",
        r"\.write\s*\(",
        r"os\.replace\s*\(",
        r"os\.rename\s*\(",
    ]
    for block in code_blocks:
        # 已知函式定義
        for fn in re.findall(r'^\s*def\s+(\w+)\s*\(', block, re.MULTILINE):
            result['known_functions'].add(fn)
        # inline write 授權偵測
        if any(re.search(p, block) for p in WRITE_PATS):
            result['allow_inline_python_write'] = True

    # 遞迴展開 sub-skill 白名單
    parent_dir = path.parent.parent
    for sub in list(result['skill_calls']):
        sub_path = parent_dir / sub / 'SKILL.md'
        sub_wl = _extract_whitelist(sub_path, depth + 1, visited)
        result['skill_calls'].update(sub_wl.get('skill_calls', set()))
        result['known_functions'].update(sub_wl.get('known_functions', set()))
        if sub_wl.get('allow_inline_python_write'):
            result['allow_inline_python_write'] = True

    return {
        'tool_types': sorted(result['tool_types']),
        'skill_calls': sorted(result['skill_calls']),
        'known_functions': sorted(result['known_functions']),
        'allow_inline_python_write': result['allow_inline_python_write'],
    }


if not _target:
    print('[GUARD] WARNING: _TARGET 未設定，跳過 SECS 白名單分析')
else:
    # 搜尋目標 skill 的 SKILL.md
    home = Path.home()
    candidates = [
        home / '.claude' / 'skills' / 'gendoc' / _target / 'SKILL.md',
        home / '.claude' / 'skills' / _target / 'SKILL.md',
        Path(f'skills/{_target}/SKILL.md'),
    ]
    skill_md = next((p for p in candidates if p.exists()), None)

    if skill_md:
        whitelist = _extract_whitelist(skill_md)
        print(f'[GUARD] SECS 白名單來源：{skill_md}')
        print(f'[GUARD] tool_types             : {whitelist["tool_types"]}')
        print(f'[GUARD] skill_calls             : {whitelist["skill_calls"]}')
        print(f'[GUARD] known_functions         : {whitelist["known_functions"]}')
        print(f'[GUARD] allow_inline_python_write: {whitelist["allow_inline_python_write"]}')

        # 寫入 .gendoc-guard.json
        d = json.load(open(_guard_file, encoding='utf-8'))
        d['secs_whitelist'] = whitelist
        tmp = _guard_file + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        os.replace(tmp, _guard_file)
        print('[GUARD] ✅ SECS 白名單已寫入 marker')
    else:
        print(f'[GUARD] WARNING: 找不到 /{_target} 的 SKILL.md，SECS 停用（所有工具呼叫放行）')
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
| `secs_whitelist` | SECS 白名單（Step 2.5 寫入） |
| `secs_whitelist.tool_types` | 目標 skill 允許使用的工具列表 |
| `secs_whitelist.skill_calls` | 允許呼叫的 skill 名稱（遞迴展開） |
| `secs_whitelist.known_functions` | SKILL.md 中定義的已知函式 |
| `secs_whitelist.allow_inline_python_write` | 目標 skill 是否含 inline Python 寫檔 |

`.gendoc-guard-history.jsonl`：每行一筆 PostToolUse 記錄，最多保留 500 筆。

| 欄位 | 說明 |
|------|------|
| `ts` | ISO 8601 時間戳 |
| `tool` | 工具名稱（Bash/Write/Skill/Read 等） |
| `result` | 工具回傳類型 |
| `summary` | 呼叫摘要（最多 120 字元） |

## 附錄：流程圖

```
/gendoc-guard gendoc-repair
      │
      ▼
Step 1：自安裝 4 個 hook（idempotent）
  ├── Stop hook          → 中斷時寫 queue + history snapshot
  ├── SessionStart hook  → 讀 queue + inject context + history 摘要
  ├── PreToolUse hook    → SECS 白名單攔截（exit 2 = block）
  └── PostToolUse hook   → 記錄每次工具呼叫至 history.jsonl
      │
      ▼
Step 2：寫 .gendoc-guard.json {status: running}
      │
      ▼
Step 2.5：SECS 白名單靜態分析
  ├── 讀 ~/.claude/skills/gendoc/{target}/SKILL.md
  ├── 提取：allowed-tools / skill_calls / known_functions / allow_inline_python_write
  ├── 遞迴展開 sub-skill（最多 3 層）
  └── 寫入 .gendoc-guard.json secs_whitelist
      │
      ▼
Step 3：Skill tool → gendoc-repair（PreToolUse hook 全程監控）
      │
      ├── 正常完成 ──→ Step 4：marker {status: complete} → 結束
      │
      └── session 中斷（context limit / crash / 手動結束）
                │
                ▼
           Stop hook 觸發
                ├── 附加最後 20 筆 history 至 queue
                ├── retry >= max → 通知停止
                └── retry < max → 寫 .gendoc-guard-queue，macOS 通知
                                        │
                                        ▼
                                  下次 claude session 開啟
                                        │
                                        ▼
                                  SessionStart hook
                                  讀 queue + history 摘要
                                  inject additionalContext
                                        │
                                        ▼
                                  Claude 自動執行
                                  /gendoc-guard gendoc-repair
                                  （retry_count + 1）

SECS 三層攔截規則（PreToolUse hook）：
  Layer 1 - 純讀放行：
    Bash inline Python 無寫檔 pattern → 直接 exit 0

  Layer 2 - 白名單執行：
    Skill tool → 只允許 secs_whitelist.skill_calls 內的 skill

  Layer 3 - 通用異常偵測（無需白名單）：
    × Inline Python > 30 行
    × sys.stdout.reconfigure 在 inline Python 中
    × Inline Python 含寫檔且 allow_inline_python_write=False
    × 重新定義 known_functions 中的函式
```
