#!/usr/bin/env python3
"""gendoc-guard Stop hook: session 中斷時寫 queue + macOS 通知"""
import json, os, sys, subprocess
from datetime import datetime, timezone

GUARD_FILE   = '.gendoc-guard.json'
QUEUE_FILE   = '.gendoc-guard-queue'
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

target      = d.get('target_skill', '')
retry       = int(d.get('retry_count', 0))
max_retries = int(d.get('max_retries', 5))
cwd         = d.get('cwd', '.')

if retry >= max_retries:
    sys.stderr.write(f'[GUARD] ⛔ /{target} 已達最大重試次數（{max_retries}），停止監控\n')
    subprocess.run(
        ['osascript', '-e',
         f'display notification "/{target} 達到最大重試 {max_retries} 次，請手動確認"'
         f' with title "Gendoc Guard: 已停止" sound name "Basso"'],
        capture_output=True
    )
    d['status'] = 'max_retries_exceeded'
    tmp = GUARD_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2)
    os.replace(tmp, GUARD_FILE)
    sys.exit(0)

next_retry = retry + 1

d['retry_count'] = next_retry
d['status']      = 'queued'
d['queued_at']   = datetime.now(timezone.utc).isoformat()
tmp = GUARD_FILE + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2)
os.replace(tmp, GUARD_FILE)

last_history = []
if os.path.isfile(HISTORY_FILE):
    try:
        lines = open(HISTORY_FILE, encoding='utf-8').readlines()
        last_history = [json.loads(l.strip()) for l in lines[-20:] if l.strip()]
    except Exception:
        pass

queue = {
    'target_skill': target,
    'retry_count':  next_retry,
    'max_retries':  max_retries,
    'cwd':          cwd,
    'queued_at':    datetime.now(timezone.utc).isoformat(),
    'last_history': last_history,
}
with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)

sys.stderr.write('\n')
sys.stderr.write('╔══════════════════════════════════════════════════╗\n')
sys.stderr.write(f'║  [GENDOC-GUARD] /{target} session 中斷\n')
sys.stderr.write(f'║  已排隊 (重試 {next_retry}/{max_retries})\n')
sys.stderr.write('║  下次開啟此目錄的 claude session 將自動繼續\n')
sys.stderr.write('╚══════════════════════════════════════════════════╝\n')

subprocess.run(
    ['osascript', '-e',
     f'display notification "/{target} 中斷，下次開啟 session 將自動繼續 (重試 {next_retry}/{max_retries})"'
     f' with title "Gendoc Guard" sound name "Ping"'],
    capture_output=True
)
