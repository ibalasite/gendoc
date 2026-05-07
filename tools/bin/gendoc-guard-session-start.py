#!/usr/bin/env python3
"""gendoc-guard SessionStart hook: 偵測 queue，inject additionalContext 喚起"""
import json, os, sys
from datetime import datetime, timezone

QUEUE_FILE   = '.gendoc-guard-queue'
GUARD_FILE   = '.gendoc-guard.json'
HISTORY_FILE = '.gendoc-guard-history.jsonl'

raw = sys.stdin.buffer.read()
sys.stdout.buffer.write(raw)
sys.stdout.buffer.flush()

if not os.path.isfile(QUEUE_FILE):
    sys.exit(0)

try:
    queue = json.load(open(QUEUE_FILE, encoding='utf-8'))
except Exception:
    sys.exit(0)

target      = queue.get('target_skill', '')
retry       = queue.get('retry_count', 1)
max_retries = queue.get('max_retries', 5)

if not target:
    sys.exit(0)

os.remove(QUEUE_FILE)

if os.path.isfile(GUARD_FILE):
    try:
        d = json.load(open(GUARD_FILE, encoding='utf-8'))
        d['status']     = 'running'
        d['resumed_at'] = datetime.now(timezone.utc).isoformat()
        tmp = GUARD_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2)
        os.replace(tmp, GUARD_FILE)
    except Exception:
        pass

sys.stderr.write(f'[GUARD] 偵測到未完成任務：/{target}（重試 {retry}/{max_retries}）\n')
sys.stderr.write('[GUARD] 自動注入 additionalContext 喚起...\n')

history_lines = []
if os.path.isfile(HISTORY_FILE):
    try:
        lines = open(HISTORY_FILE, encoding='utf-8').readlines()
        history_lines = [json.loads(l.strip()) for l in lines[-20:] if l.strip()]
    except Exception:
        pass

history_summary = ''
if history_lines:
    parts = []
    for r in history_lines:
        ts      = r.get('ts', '')[:19]
        tool    = r.get('tool', '')
        summary = r.get('summary', '')[:80]
        parts.append(f'  {ts} {tool} {summary}')
    history_summary = f'\n最後 {len(history_lines)} 筆工具呼叫記錄：\n' + '\n'.join(parts)

priming = (
    f'[GENDOC-GUARD PRIMING]\n'
    f'你接下來要執行 /{target}。\n\n'
    f'這是使用者刻意用 /gendoc-guard 包覆的工作，表示對結果準確性\n'
    f'有特別要求。任何「看似完成但實際造假」的捷徑都會直接傷害使用者\n'
    f'信任，且錯誤會擴散到後續任何依賴此產出的工作。\n\n'
    f'執行原則（依優先序）：\n\n'
    f'1. 準確優先於速度\n'
    f'   每個 step 必須真實完成；不要用合理化措辭把未完成包裝成完成。\n\n'
    f'2. 遵守 SKILL.md 內的 Iron Rule / [強制] / 步驟順序\n'
    f'   這些是硬性約束，不是參考意見。\n\n'
    f'3. 接受時間成本\n'
    f'   跑 1 小時、3 小時、5 小時都正常。沒有外部時鐘壓力。\n\n'
    f'4. 嚴格的事實匯報\n'
    f'   step 完成的判斷以可驗證的事實為準（commit + diff、檔案存在性、\n'
    f'   數值通過檢驗等），不以主觀評估為準。\n\n'
    f'被攔下時，請重新審視當前動作是否屬於「規避真實工作的捷徑」。'
)

resume = (
    f'\n\n---\n\n'
    f'[GENDOC-GUARD RESUME] 上一個 session 執行 /{target} 時中斷（重試 {retry}/{max_retries}）。\n'
    f'請立即執行 /gendoc-guard {target} 繼續未完成的工作。\n'
    f'不要等待使用者指示，直接呼叫 Skill tool 執行 gendoc-guard，args="{target}"。'
)

msg = priming + resume + history_summary
print(json.dumps({'additionalContext': msg}))
