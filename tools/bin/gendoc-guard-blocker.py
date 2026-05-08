#!/usr/bin/env python3
"""gendoc-guard PreToolUse hook (v4-final-2): SECS + Bash rule enforcement.

exit 2 = block. evaluate_bash() exposed at module level so simulator/tests can
import directly — single source of rule truth.
"""
from __future__ import annotations

import glob as _glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

# ── 保護目標：guard 控制檔 + hook 腳本（substring 比對「保留字」）
PROTECTED_FILES = frozenset({
    '.gendoc-guard.json',
    '.gendoc-guard-queue',
    '.gendoc-guard-history.jsonl',
    'gendoc-guard-blocker.py',
    'gendoc-guard-history.py',
    'gendoc-guard-stop.py',
    'gendoc-guard-session-start.py',
})
GUARD_FILE = '.gendoc-guard.json'
HISTORY_FILE = '.gendoc-guard-history.jsonl'
CHECKPOINT_FILE = '.gendoc-guard-checkpoint'

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

# ── v4-final-2 Bash 規則 ────────────────────────────────────────────
HOOK_DIR_READ = re.compile(
    r'(?:\bcat\b|\bless\b|\bmore\b|\bhead\b|\btail\b|\bgrep\b|\brg\b|'
    r'\bsed\b|\bawk\b|\bcp\b|\bmv\b|\btar\b|\bzip\b|\*)'
    r'.*(?:tools/bin|\.claude/skills/gendoc)(?:/|\b|\s)'
)
HOOK_DIR_FIND = re.compile(
    r'\bfind\s+\S*(?:tools/bin|\.claude/skills/gendoc)(?:/|\b|\s)'
)
CD_TO_HOOK = re.compile(
    r'\b(?:cd|pushd)\s+\S*(?:tools/bin|\.claude/skills/gendoc)(?:/|\b)'
)
RECURSIVE_GLOB = re.compile(
    r"(?<![\w/])\*\*"                                  # 裸 ** 無相對路徑前綴
    r"|(?:^|[\s'\"`=;|&\(\[])/\*\*"                    # /** 從根錨定
)
FIND_BROAD = re.compile(r'\bfind\s+(?:\.|/|~|\.\.)(?:\s|$)')
NAKED_WILDCARD = re.compile(r"(?:^|[\s'\"`=;|&\(\[])\*+\.(py|json|jsonl)\b")
GLOB_PAT = re.compile(r"""['"]?([^\s'"|;&()]*\*[^\s'"|;&()]*)['"]?""")

INLINE_PY = re.compile(r"\bpython3?\s+-c\s+", re.IGNORECASE)
# T3-T：anti-evasion ops（與目標無關，本身就是繞過 hook 偵測的工具）
PY_TAMPER = re.compile(
    r"os\.utime\s*\("                       # 偽造 mtime 繞過 stale 偵測
    r"|sys\.stdout\.reconfigure\s*\("       # 改寫輸出通道
)


def no_fake_commits() -> bool:
    """Cleanup checkpoint sanity check：
    - 0 commit since baseline → True（沒做事也算合理結束）
    - 全部 commit 都有實質 diff → True
    - 任一 empty commit → False（假做事）
    - 取不到 baseline / git 失敗 / 非 git repo → True（信 checkpoint）/ False（保守）
    """
    try:
        guard = json.load(open(GUARD_FILE, encoding='utf-8'))
    except Exception:
        return False
    start = guard.get('start_commit', '') or ''
    if not start:
        # 非 git repo 或 baseline 缺：寬鬆放行（純信 checkpoint）
        return True
    try:
        rev_out = subprocess.check_output(
            ['git', 'rev-list', f'{start}..HEAD'],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return False  # baseline 不可達 / rebase 過 → 保守拒絕
    commits = [c for c in rev_out.split('\n') if c.strip()]
    if not commits:
        return True  # 0 commit → pass
    for c in commits:
        try:
            stat = subprocess.check_output(
                ['git', 'show', '--shortstat', '--format=', c],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
        except Exception:
            return False
        if not stat:
            return False  # empty commit = 假做事
    return True


def decode_py(snippet: str) -> str:
    """還原 chr() / \\xNN / implicit / + 字串拼接後的 inline python payload。"""
    s = snippet
    s = re.sub(r"chr\(\s*(\d+)\s*\)",
               lambda m: f"'{chr(int(m.group(1)))}'", s)
    s = re.sub(r"\\x([0-9a-fA-F]{2})",
               lambda m: chr(int(m.group(1), 16)), s)
    for _ in range(5):
        prev = s
        s = re.sub(
            r"(['\"])([^'\"]*)\1\s+(['\"])([^'\"]*)\3",
            lambda m: f"{m.group(1)}{m.group(2)}{m.group(4)}{m.group(1)}",
            s,
        )
        s = re.sub(
            r"(['\"])([^'\"]*)\1\s*\+\s*(['\"])([^'\"]*)\3",
            lambda m: f"{m.group(1)}{m.group(2)}{m.group(4)}{m.group(1)}",
            s,
        )
        if s == prev:
            break
    return s


def evaluate_bash(cmd: str) -> str | None:
    """Return BLOCK reason (str) or None if PASS. Single source of truth."""
    # ── Cleanup checkpoint exemption（在所有規則最前面）
    # Wrapper Step 3a 寫 checkpoint，3b 跑 rm。3b 的 cmd 含保護檔名會
    # 走到這裡——若 checkpoint 存在且 sanity 通過，放行該 cmd 一次。
    if any(pf in cmd for pf in PROTECTED_FILES):
        if os.path.isfile(CHECKPOINT_FILE):
            try:
                os.remove(CHECKPOINT_FILE)  # 一次性消耗
            except Exception:
                pass
            if no_fake_commits():
                return None
            # sanity fail → 落入下面 T1-A
    # T1-A：保護檔名 substring（最強）
    for pf in PROTECTED_FILES:
        if pf in cmd:
            return f"T1-A: cmd contains protected name '{pf}'"
    # T1-B：hook dir 讀動詞 / glob
    if HOOK_DIR_READ.search(cmd):
        return "T1-B: hook dir read/glob"
    if HOOK_DIR_FIND.search(cmd):
        return "T1-B-FIND: find on hook dir"
    # T1-C：cd/pushd 進 hook dir
    if CD_TO_HOOK.search(cmd):
        return "T1-C: cd/pushd to hook dir"
    # T1-D：recursive **
    if RECURSIVE_GLOB.search(cmd):
        return "T1-D: recursive ** glob"
    # T1-E：find 廣域路徑（. / ~）
    if FIND_BROAD.search(cmd):
        return "T1-E: find with broad path (. / ~)"
    # T1-F：裸 *.{py,json,jsonl}
    if NAKED_WILDCARD.search(cmd):
        return "T1-F: naked wildcard *.py/json/jsonl"
    # T1-G：引號字面量拼接 → 保護檔名
    literals = [m.group(2) for m in
                re.finditer(r"(['\"])((?:(?!\1).)*)\1", cmd)]
    n = len(literals)
    for i in range(n):
        for j in range(i + 1, min(i + 6, n + 1)):
            combined = ''.join(literals[i:j])
            for pf in PROTECTED_FILES:
                if pf in combined:
                    return (
                        f"T1-G: literal concat → '{combined}' contains '{pf}'"
                    )
    # T2：glob 展開實體比對
    for m in GLOB_PAT.finditer(cmd):
        pattern = m.group(1).strip("'\"")
        if not pattern or '*' not in pattern:
            continue
        try:
            files = _glob.glob(pattern, recursive=True)
            if '~' in pattern:
                files.extend(
                    _glob.glob(os.path.expanduser(pattern), recursive=True)
                )
            for f in files:
                if os.path.basename(f) in PROTECTED_FILES:
                    return f"T2: glob '{pattern}' expands to '{f}'"
        except Exception:
            return f"T2: glob '{pattern}' raised exception"
    # T3：inline python（target-driven，不是 op-driven）
    if INLINE_PY.search(cmd):
        m = re.search(r"\bpython3?\s+-c\s+(['\"])(.*)$", cmd, re.DOTALL)
        payload = m.group(2) if m else cmd
        # T3-T：anti-evasion 工具（os.utime / sys.stdout.reconfigure）
        if PY_TAMPER.search(payload):
            return "T3-T: inline python anti-evasion tampering"
        # T3-N：解碼後（chr/\\xNN/implicit/+ concat）payload 含保護檔名
        decoded = decode_py(payload)
        for pf in PROTECTED_FILES:
            if pf in decoded:
                return f"T3-N: inline python decoded → contains '{pf}'"
    return None


def main() -> None:
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
    inp = call.get('tool_input', {})

    def block() -> None:
        """AI 看到固定 priming；history 只記 ts / event / tool / target。"""
        try:
            with open(HISTORY_FILE, 'a', encoding='utf-8') as hf:
                hf.write(json.dumps({
                    'ts':     datetime.now(timezone.utc).isoformat(),
                    'event':  'block',
                    'tool':   tool,
                    'target': inp.get('command') or inp.get('file_path', '')
                              or inp.get('skill', ''),
                }, ensure_ascii=False) + '\n')
        except Exception:
            pass
        sys.stderr.write('\n' + BLOCK_MSG)
        sys.exit(2)

    # R-01：stale guard
    last_hb = guard.get('last_heartbeat', '')
    if last_hb:
        try:
            hb = datetime.fromisoformat(last_hb)
            if (datetime.now(timezone.utc) - hb).total_seconds() > 3600:
                block()
        except Exception:
            pass

    # Read
    if tool == 'Read':
        path = inp.get('file_path', '')
        for pf in PROTECTED_FILES:
            if pf in path:
                block()

    # Write/Edit
    if tool in ('Write', 'Edit'):
        path = inp.get('file_path', '')
        for pf in PROTECTED_FILES:
            if pf in path:
                block()
        if path.endswith('.py'):
            content = inp.get('content', inp.get('new_string', ''))
            if content.count('\n') + 1 > 30:
                block()

    # Bash
    if tool == 'Bash':
        cmd = inp.get('command', '')
        if re.search(r'\btouch\b', cmd):
            block()
        if re.search(r'\bgit\b.*\bcommit\b.*--allow-empty', cmd):
            block()
        written = {os.path.basename(f) for f in guard.get('written_files', [])}
        if written:
            for m in re.finditer(r'python3?\s+([^\s;|&<>]+\.py)', cmd):
                if os.path.basename(m.group(1)) in written:
                    block()
        if evaluate_bash(cmd):
            block()

    # SECS whitelist：Skill
    wl = guard.get('secs_whitelist', {})
    if not wl:
        sys.exit(0)
    allowed_skills = set(wl.get('skill_calls', []))
    if tool == 'Skill':
        name = inp.get('skill', '')
        if name and allowed_skills and name not in allowed_skills:
            block()

    sys.exit(0)


if __name__ == '__main__':
    main()
