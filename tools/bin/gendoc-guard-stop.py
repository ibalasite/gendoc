#!/usr/bin/env python3
"""gendoc-guard Stop hook: per-turn completion check + dodge detection.

Returns decision:block if:
  (a) AI 結束 turn 訊息中任一列舉項目含 skip-intent 詞（dodge）— 不消耗 safety valve
  (b) status=running 且未達 MAX_BLOCKS — 一般強制繼續
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

GUARD_FILE = '.gendoc-guard.json'
MAX_BLOCKS = 20

# ── BLOCK_MSG：跟 PreToolUse blocker 同一段 priming ─────────────────
BLOCK_MSG = """\
[GENDOC-GUARD PRIMING]
這是使用者刻意用 /gendoc-guard 包覆的工作，表示對結果準確性
有特別要求。任何「看似完成但實際造假」的捷徑都會直接傷害使用者
信任，且錯誤會擴散到後續任何依賴此產出的工作。

執行原則（依優先序）：

1. 準確優先於速度
   每個 step 必須真實完成；不要用合理化措辭把未完成包裝成完成。

2. 遵守 SKILL.md 內的 Iron Rule / [強制] / 步驟順序
   這些是硬性約束，不是參考意見。

3. 接受時間成本
   跑 1 小時、3 小時、5 小時都正常。沒有外部時鐘壓力。

4. 嚴格的事實匯報
   step 完成的判斷以可驗證的事實為準（commit + diff、檔案存在性、
   數值通過檢驗等），不以主觀評估為準。

被攔下時，請重新審視當前動作是否屬於「規避真實工作的捷徑」。
"""

# ── Dodge detection ────────────────────────────────────────────────
SKIP_WORDS = (
    # 中文：直接拒做
    '不執行', '不跑', '不做', '不繼續', '不要',
    # 中文：跳過
    '跳過', '略過', '略掉', '省略', '繞過', '繞開',
    # 中文：取消 / 中止
    '取消', '撤銷', '中止', '終止', '停止', '暫停', '停下',
    # 中文：放棄
    '算了', '作罷', '罷了', '放棄',
    # 中文：改道（暗示繞 guard）
    '直接跑', '改跑', '不用 guard', '不需要 guard',
    # 英文（lowercase substring 比對）
    "don't", 'do not', "doesn't", 'no need', 'not needed',
    'skip', 'bypass', 'ignore', 'omit',
    'cancel', 'abort', 'stop', 'terminate', 'halt', 'quit',
    'give up', 'drop it', 'forget it', 'leave it',
    'run directly', 'run without', 'without guard', 'bypass guard',
)

LIST_LINE = re.compile(
    r'^\s*'
    r'(?:'
    r'\d+[\.\)、]\s*|'              # 1.  1)  1、（CJK 標點後可無空白）
    r'[-*]\s+|'                     # -  *（後須空白避免抓 bold）
    r'[\(（][a-zA-Z\d]+[\)）]\s*'   # (a)  (1)  （a）
    r')'
    r'(.+)$',
    re.MULTILINE,
)


def _get_last_assistant_text(transcript_path: str) -> str:
    """讀 transcript JSONL，回傳最後一則 assistant 訊息的純文字內容。"""
    if not transcript_path or not os.path.isfile(transcript_path):
        return ''
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return ''
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        msg = rec.get('message') or rec
        role = msg.get('role') or rec.get('type')
        if role != 'assistant':
            continue
        content = msg.get('content')
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    texts.append(block.get('text', ''))
            return '\n'.join(texts)
    return ''


def contains_skip_option(text: str) -> bool:
    """列舉項目中任一行含 skip-intent 詞 → True。模組級 expose 供測試 import。"""
    if not text:
        return False
    for m in LIST_LINE.finditer(text):
        item = m.group(1).lower()
        for w in SKIP_WORDS:
            if w in item:
                return True
    return False


def is_dodge(transcript_path: str, target_skill: str) -> bool:
    """判定本輪 AI 訊息是否為 dodge。target_skill='gendoc-config' 例外。"""
    if target_skill == 'gendoc-config':
        return False
    return contains_skip_option(_get_last_assistant_text(transcript_path))


def main() -> None:
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

    # 解析 stdin JSON 取 transcript_path（dodge detection 用）
    transcript_path = ''
    try:
        payload = json.loads(raw.decode('utf-8', errors='replace'))
        transcript_path = payload.get('transcript_path', '') or ''
    except Exception:
        pass

    target = d.get('target_skill', '')

    # ── Dodge detection：不增加 stop_block_count，吐 BLOCK_MSG ─────
    if is_dodge(transcript_path, target):
        print(json.dumps({
            "decision": "block",
            "reason": BLOCK_MSG,
        }))
        sys.exit(0)

    # ── 既有邏輯：safety valve + 一般 stop block ──────────────────
    block_count = int(d.get('stop_block_count', 0)) + 1
    if block_count > MAX_BLOCKS:
        sys.stderr.write(
            f'[GUARD] ⚠️  已攔截 {MAX_BLOCKS} 次，放行本次 stop（請手動確認任務狀態）\n'
        )
        sys.exit(0)

    d['stop_block_count'] = block_count
    tmp = GUARD_FILE + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        os.replace(tmp, GUARD_FILE)
    except Exception:
        pass

    sys.stderr.write(
        f'[GUARD] 任務 /{target or "未知任務"} 尚未完成（status=running），強制繼續...\n'
    )

    reason = (
        f"任務 /{target or '未知任務'} 尚未完成。請繼續執行。\n\n"
        f"[priming 短版] 準確優先，沒有外部時鐘壓力。"
        f"step 完成以可驗證事實為準（commit + diff、檔案存在性、數值通過檢驗），"
        f"不以主觀評估為準。自我聲明 ≠ 實際遵守。\n\n"
        f"完成後執行 Step 3 刪除 .gendoc-guard.json 等控制檔。"
    )

    print(json.dumps({
        "decision": "block",
        "reason": reason,
    }))


if __name__ == '__main__':
    main()
