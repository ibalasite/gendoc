#!/usr/bin/env python3
"""gendoc-guard PostToolUse hook: history logging, heartbeat, queue update, written_files tracking."""
import json, os, sys
from datetime import datetime, timezone

GUARD_FILE   = '.gendoc-guard.json'
HISTORY_FILE = '.gendoc-guard-history.jsonl'
QUEUE_FILE   = '.gendoc-guard-queue'

raw = sys.stdin.buffer.read()
sys.stdout.buffer.write(raw)
sys.stdout.buffer.flush()

if not os.path.isfile(GUARD_FILE):
    sys.exit(0)

try:
    d = json.load(open(GUARD_FILE, encoding='utf-8'))
except Exception:
    sys.exit(0)

if d.get('status') != 'running':
    sys.exit(0)

try:
    call = json.loads(raw.decode('utf-8', errors='replace'))
except Exception:
    sys.exit(0)

tool = call.get('tool_name', '')
inp  = call.get('tool_input', {})
res  = call.get('tool_result', {})

# ── History logging ──────────────────────────────────────────────
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

with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
    f.write(json.dumps(record, ensure_ascii=False) + '\n')

try:
    lines = open(HISTORY_FILE, encoding='utf-8').readlines()
    if len(lines) > 500:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines[-500:])
    last_history = [json.loads(l.strip()) for l in lines[-20:] if l.strip()]
except Exception:
    last_history = []

# ── R-11：追蹤 session 內寫入的 .py 檔 ──────────────────────────
if tool in ('Write', 'Edit'):
    path = inp.get('file_path', '')
    if path.endswith('.py'):
        written = d.setdefault('written_files', [])
        abs_path = os.path.abspath(path)
        if abs_path not in written:
            written.append(abs_path)

# ── R-09：更新 last_heartbeat ────────────────────────────────────
d['last_heartbeat'] = datetime.now(timezone.utc).isoformat()

# 原子寫回 guard file
tmp = GUARD_FILE + '.tmp'
try:
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    os.replace(tmp, GUARD_FILE)
except Exception:
    pass

# ── R-10：更新 queue（proactive，session 中斷時已是最新狀態）────
queue = {
    'target_skill': d.get('target_skill', ''),
    'retry_count':  d.get('retry_count', 0),
    'max_retries':  d.get('max_retries', 5),
    'cwd':          d.get('cwd', os.getcwd()),
    'queued_at':    datetime.now(timezone.utc).isoformat(),
    'last_history': last_history,
}
tmp_q = QUEUE_FILE + '.tmp'
try:
    with open(tmp_q, 'w', encoding='utf-8') as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    os.replace(tmp_q, QUEUE_FILE)
except Exception:
    pass
