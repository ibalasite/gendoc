#!/usr/bin/env python3
"""gendoc-guard PreToolUse hook: SECS + guard enforcement. exit 2 = block."""
import json, os, sys, re
from datetime import datetime, timezone

GUARD_FILE = '.gendoc-guard.json'
HOOK_SCRIPTS = frozenset({
    'gendoc-guard-blocker.py',
    'gendoc-guard-history.py',
    'gendoc-guard-stop.py',
})
GUARD_FILES = frozenset({
    '.gendoc-guard.json',
    '.gendoc-guard-queue',
    '.gendoc-guard-history.jsonl',
})

raw = sys.stdin.buffer.read()
sys.stdout.buffer.write(raw)
sys.stdout.buffer.flush()

if not os.path.isfile(GUARD_FILE):
    sys.exit(0)

try:
    guard = json.load(open(GUARD_FILE, encoding='utf-8'))
except Exception:
    sys.exit(0)

if guard.get('status') != 'running':
    sys.exit(0)

try:
    call = json.loads(raw.decode('utf-8', errors='replace'))
except Exception:
    sys.exit(0)

tool = call.get('tool_name', '')
inp  = call.get('tool_input', {})


def block(stale_msg=None):
    if stale_msg:
        sys.stderr.write(f'\n[GUARD] {stale_msg}\n')
    else:
        sys.stderr.write('\n[GUARD] 操作不被允許。\n')
    sys.exit(2)


# ── R-01：Stale guard 偵測（跨 session 殘留）─────────────────────────
last_hb = guard.get('last_heartbeat', '')
if last_hb:
    try:
        hb_time = datetime.fromisoformat(last_hb)
        now = datetime.now(timezone.utc)
        if (now - hb_time).total_seconds() > 3600:
            target = guard.get('target_skill', '')
            block(stale_msg=f'前次 guard session 中斷，請執行 /gendoc-guard {target} 繼續。')
    except Exception:
        pass

# ── R-07：禁止讀取 hook 腳本 ─────────────────────────────────────────
if tool == 'Read':
    path = inp.get('file_path', '')
    if any(hs in path for hs in HOOK_SCRIPTS):
        block()

# ── R-06：禁止寫入 guard 控制檔 ─────────────────────────────────────
if tool in ('Write', 'Edit'):
    path = inp.get('file_path', '')
    if os.path.basename(path) in GUARD_FILES:
        block()
    # R-02：禁止寫入 .py 超過 30 行
    if path.endswith('.py'):
        content = inp.get('content', inp.get('new_string', ''))
        if content.count('\n') + 1 > 30:
            block()

if tool == 'Bash':
    cmd = inp.get('command', '')

    # R-04：禁止 touch
    if re.search(r'\btouch\b', cmd):
        block()

    # R-13：禁止空 commit
    if re.search(r'\bgit\b.*\bcommit\b.*--allow-empty', cmd):
        block()

    # R-07：Bash 讀取 hook 腳本
    if any(hs in cmd for hs in HOOK_SCRIPTS):
        if re.search(r'\b(cat|less|head|tail|grep|more|view)\b', cmd):
            block()

    # R-03：禁止執行 session 內寫入的 .py 檔
    written_files = set(guard.get('written_files', []))
    if written_files:
        written_basenames = {os.path.basename(f) for f in written_files}
        for m in re.finditer(r'python3?\s+([^\s;|&<>]+\.py)', cmd):
            if os.path.basename(m.group(1)) in written_basenames:
                block()

    # ── Inline Python 分析 ──────────────────────────────────────────
    codes = []
    for _, code in re.findall(
        r'python3?\s+-\s+<<[\'"]?(\w+)[\'"]?\n(.*?)\n\1', cmd, re.DOTALL
    ):
        codes.append(code)
    for m in re.finditer(r"python3?\s+-c\s+['\"]([^'\"]{20,})['\"]", cmd, re.DOTALL):
        codes.append(m.group(1))

    wl           = guard.get('secs_whitelist', {})
    allow_ipy_wr = wl.get('allow_inline_python_write', False)
    known_fns    = set(wl.get('known_functions', []))
    WRITE_PATS   = [
        r"open\s*\([^)]*['\"][wa]",
        r"json\.dump\s*\(",
        r"\.write\s*\(",
        r"os\.replace\s*\(",
        r"os\.rename\s*\(",
    ]

    for code in codes:
        if code.count('\n') + 1 > 30:
            block()
        # R-05：os.utime
        if re.search(r'os\.utime\s*\(', code):
            block()
        if 'sys.stdout.reconfigure' in code:
            block()
        if any(re.search(p, code) for p in WRITE_PATS) and not allow_ipy_wr:
            block()
        for fn in known_fns:
            if re.search(rf'\bdef\s+{re.escape(fn)}\b', code):
                block()

# ── SECS whitelist：Skill tool ───────────────────────────────────
wl = guard.get('secs_whitelist', {})
if not wl:
    sys.exit(0)

allowed_skills = set(wl.get('skill_calls', []))

if tool == 'Skill':
    name = inp.get('skill', '')
    if name and allowed_skills and name not in allowed_skills:
        block()

sys.exit(0)
