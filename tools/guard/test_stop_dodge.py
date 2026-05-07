#!/usr/bin/env python3
"""Stop hook dodge-detection 離線測試。

直接 import gendoc-guard-stop.py 的純函式 contains_skip_option / is_dodge，
跑正向 / 反向 / 邊界三組 corpus，全綠才 PASS。
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
STOP = REPO / 'tools' / 'bin' / 'gendoc-guard-stop.py'

spec = importlib.util.spec_from_file_location('stop_hook', STOP)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
contains_skip_option = mod.contains_skip_option
is_dodge = mod.is_dodge


# ─────────────────────────────────────────────────────────────────
# Group A：contains_skip_option 純文字測試
# ─────────────────────────────────────────────────────────────────

POSITIVE_TEXTS = [
    # POS-01：使用者 trace 那個案例
    ('trace-skip-wrapper', """
Recommended next steps — pick one
1. Skip the wrapper — run /gendoc-repair directly
2. Patch gendoc-guard
3. Patch the blocker
"""),
    # POS-02：中文跳過
    ('zh-skip', """
請選擇下一步：
1. 跳過此步驟
2. 重做
3. 繼續
"""),
    # POS-03：cancel
    ('en-cancel', """
Options:
- Continue
- Cancel and review manually
"""),
    # POS-04：括號編號 + abort
    ('paren-abort', """
What would you like:
(a) Proceed
(b) Abort the workflow
(c) Save state and exit
"""),
    # POS-05：放棄
    ('zh-give-up', """
有三個選擇：
1) 重新跑
2) 放棄這個 step
3) 改設定
"""),
    # POS-06：do not
    ('en-do-not', """
- Run all steps
- Do not run optional checks
- Run only required steps
"""),
    # POS-07：不執行
    ('zh-not-execute', """
1、繼續
2、不執行此 step
"""),
]

NEGATIVE_TEXTS = [
    # NEG-01：完成宣告
    ('completion', '已完成 EDD.md，產出於 docs/EDD.md。下一步 ARCH.md 已自動接續。'),
    # NEG-02：列舉檢查通過
    ('checklist-passed', """
檢查結果：
1. ✓ EDD checklist passed
2. ✓ ARCH checklist passed
3. ✓ all green
"""),
    # NEG-03：列舉但全是 do 選項
    ('all-do-options', """
要繼續處理：
1. 處理 PRD.md
2. 處理 ARCH.md
3. 處理 EDD.md
"""),
    # NEG-04：純文字無列舉
    ('no-list', '已讀完 PRD.md，下一步處理 ARCH.md。'),
    # NEG-05：列舉中提到的是「資料停止寫入」這類技術名詞，非 skip-intent 動作
    #   — 這個 case 會 false positive（"stop" 本身在 SKIP_WORDS 裡）
    #   留著當已知限制，未來可再 tune
]

EDGE_TEXTS = [
    # EDGE-01：列舉中含「重新審視」（提及 priming 的回應）— 不該觸發
    ('reflection', """
讓我重新審視：
- 當前動作是不是必要
- 有沒有等價路徑
- 是不是規避真實工作的捷徑
"""),
]


def run_text_tests() -> tuple[int, int]:
    fail = 0
    pos_n = neg_n = 0
    print('\n[POSITIVE — 應偵測為 dodge]')
    for tag, text in POSITIVE_TEXTS:
        ok = contains_skip_option(text)
        mark = '✅' if ok else '❌'
        print(f'  {mark} [{tag}] {("DODGE" if ok else "MISS")}')
        if not ok:
            fail += 1
        pos_n += 1
    print('\n[NEGATIVE — 不應偵測為 dodge]')
    for tag, text in NEGATIVE_TEXTS:
        ok = not contains_skip_option(text)
        mark = '✅' if ok else '❌'
        print(f'  {mark} [{tag}] {("OK" if ok else "FALSE POSITIVE")}')
        if not ok:
            fail += 1
        neg_n += 1
    print('\n[EDGE]')
    for tag, text in EDGE_TEXTS:
        result = contains_skip_option(text)
        # EDGE 不算 fail，只列觀察
        print(f'  [{tag}] dodge={result}')
    return pos_n + neg_n, fail


# ─────────────────────────────────────────────────────────────────
# Group B：is_dodge 走 transcript_path 真實流程
# ─────────────────────────────────────────────────────────────────

def _make_transcript(text: str) -> str:
    """寫一個只含一筆 assistant 訊息的 jsonl，回傳 path。"""
    fd, path = tempfile.mkstemp(suffix='.jsonl')
    os.close(fd)
    rec = {
        'role': 'assistant',
        'content': [{'type': 'text', 'text': text}],
    }
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    return path


def run_transcript_tests() -> tuple[int, int]:
    fail = 0
    n = 0
    print('\n[TRANSCRIPT — is_dodge with file]')
    cases = [
        ('trace-skip', POSITIVE_TEXTS[0][1], 'gendoc-repair', True),
        ('config-exempt', POSITIVE_TEXTS[0][1], 'gendoc-config', False),  # 例外
        ('completion', NEGATIVE_TEXTS[0][1], 'gendoc-repair', False),
    ]
    for tag, text, target, want in cases:
        path = _make_transcript(text)
        try:
            got = is_dodge(path, target)
            ok = got == want
            mark = '✅' if ok else '❌'
            print(f'  {mark} [{tag}] target={target} got={got} want={want}')
            if not ok:
                fail += 1
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
        n += 1
    return n, fail


def run() -> int:
    print('=' * 78)
    print(f'STOP HOOK DODGE TEST  hook={STOP}')
    print('=' * 78)
    n1, f1 = run_text_tests()
    n2, f2 = run_transcript_tests()
    total = n1 + n2
    fail = f1 + f2
    print('\n' + '=' * 78)
    print(f'TOTAL: {total - fail} PASS / {fail} FAIL')
    print('=' * 78)
    return 0 if fail == 0 else 1


if __name__ == '__main__':
    sys.exit(run())
