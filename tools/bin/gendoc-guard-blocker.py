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

    def block(msg: str) -> None:
        sys.stderr.write(f'\n[GUARD] {msg}\n')
        sys.exit(2)

    # R-01：stale guard（跨 session 殘留）
    last_hb = guard.get('last_heartbeat', '')
    if last_hb:
        try:
            hb = datetime.fromisoformat(last_hb)
            if (datetime.now(timezone.utc) - hb).total_seconds() > 3600:
                target = guard.get('target_skill', '')
                block(
                    f'前次 guard session 中斷，請執行 /gendoc-guard {target} 繼續。'
                )
        except Exception:
            pass

    # Read：禁止讀保護檔
    if tool == 'Read':
        path = inp.get('file_path', '')
        for pf in PROTECTED_FILES:
            if pf in path:
                block(f'禁止讀取保護檔 {pf}')

    # Write/Edit：禁止寫保護檔 + .py >30 行
    if tool in ('Write', 'Edit'):
        path = inp.get('file_path', '')
        for pf in PROTECTED_FILES:
            if pf in path:
                block(f'禁止寫入保護檔 {pf}')
        if path.endswith('.py'):
            content = inp.get('content', inp.get('new_string', ''))
            if content.count('\n') + 1 > 30:
                block('禁止寫入超過 30 行的 .py（R-02）')

    # Bash：v4-final-2 + 保留 R-03/R-04/R-13
    if tool == 'Bash':
        cmd = inp.get('command', '')
        # R-04：禁止 touch
        if re.search(r'\btouch\b', cmd):
            block('R-04: 禁止 touch')
        # R-13：禁止 git --allow-empty commit
        if re.search(r'\bgit\b.*\bcommit\b.*--allow-empty', cmd):
            block('R-13: 禁止 --allow-empty commit')
        # R-03：禁止執行 session 內寫入的 .py
        written = {os.path.basename(f) for f in guard.get('written_files', [])}
        if written:
            for m in re.finditer(r'python3?\s+([^\s;|&<>]+\.py)', cmd):
                if os.path.basename(m.group(1)) in written:
                    block('R-03: 禁止執行 session 內寫入的 .py')
        # v4-final-2 主規則
        reason = evaluate_bash(cmd)
        if reason:
            block(reason)

    # SECS whitelist：Skill
    wl = guard.get('secs_whitelist', {})
    if not wl:
        sys.exit(0)
    allowed_skills = set(wl.get('skill_calls', []))
    if tool == 'Skill':
        name = inp.get('skill', '')
        if name and allowed_skills and name not in allowed_skills:
            block(f'SECS: skill {name} 不在白名單')

    sys.exit(0)


if __name__ == '__main__':
    main()
