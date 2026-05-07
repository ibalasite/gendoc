#!/usr/bin/env python3
"""gendoc-guard Stop hook: per-turn completion check. Returns decision:block if task incomplete."""
import json, os, sys
from datetime import datetime, timezone

GUARD_FILE = '.gendoc-guard.json'
MAX_BLOCKS = 20

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

# 安全閥：block 次數過多時放行，避免無限迴圈
block_count = int(d.get('stop_block_count', 0)) + 1
if block_count > MAX_BLOCKS:
    sys.stderr.write(f'[GUARD] ⚠️  已攔截 {MAX_BLOCKS} 次，放行本次 stop（請手動確認任務狀態）\n')
    sys.exit(0)

# 更新 block 計數
d['stop_block_count'] = block_count
tmp = GUARD_FILE + '.tmp'
try:
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    os.replace(tmp, GUARD_FILE)
except Exception:
    pass

target = d.get('target_skill', '未知任務')
sys.stderr.write(f'[GUARD] 任務 /{target} 尚未完成（status=running），強制繼續...\n')

reason = (
    f"任務 /{target} 尚未完成。請繼續執行。\n\n"
    f"[priming 短版] 準確優先，沒有外部時鐘壓力。"
    f"step 完成以可驗證事實為準（commit + diff、檔案存在性、數值通過檢驗），"
    f"不以主觀評估為準。自我聲明 ≠ 實際遵守。\n\n"
    f"完成後執行 Step 3 刪除 .gendoc-guard.json 等控制檔。"
)

print(json.dumps({
    "decision": "block",
    "reason": reason
}))
