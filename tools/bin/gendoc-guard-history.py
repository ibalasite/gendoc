#!/usr/bin/env python3
"""gendoc-guard PostToolUse hook: 記錄每次工具呼叫至 history.jsonl"""
import json, os, sys
from datetime import datetime, timezone

GUARD_FILE   = '.gendoc-guard.json'
HISTORY_FILE = '.gendoc-guard-history.jsonl'

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
except Exception:
    pass
