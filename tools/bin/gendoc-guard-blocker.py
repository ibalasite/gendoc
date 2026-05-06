#!/usr/bin/env python3
"""gendoc-guard PreToolUse hook: SECS whitelist enforcement. exit 2 = block."""
import json, os, sys, re

GUARD_FILE = '.gendoc-guard.json'

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
wl   = guard.get('secs_whitelist', {})

if not wl:
    sys.exit(0)

allowed_skills = set(wl.get('skill_calls', []))
known_fns      = set(wl.get('known_functions', []))
allow_ipy_wr   = wl.get('allow_inline_python_write', False)

WRITE_PATS = [
    r"open\s*\([^)]*['\"][wa]['\"]",
    r"json\.dump\s*\(",
    r"\.write\s*\(",
    r"os\.replace\s*\(",
    r"os\.rename\s*\(",
]

def has_write(code):
    return any(re.search(p, code) for p in WRITE_PATS)

def block(reason):
    target = guard.get('target_skill', '?')
    sys.stderr.write('\n╔══════════════════════════════════════════════════╗\n')
    sys.stderr.write(f'║  [SECS] BLOCKED: /{target}\n')
    sys.stderr.write(f'║  {reason[:80]}\n')
    if allowed_skills:
        sys.stderr.write(f'║  Whitelisted skills: {sorted(allowed_skills)}\n')
    sys.stderr.write('╚══════════════════════════════════════════════════╝\n')
    sys.exit(2)

if tool == 'Skill':
    name = inp.get('skill', '')
    if name and allowed_skills and name not in allowed_skills:
        block(f'Skill "{name}" 不在白名單。允許：{sorted(allowed_skills)}')
    sys.exit(0)

if tool == 'Bash':
    cmd = inp.get('command', '')
    hdocs = re.findall(
        r'python3?\s+-\s+<<[\'"]?(\w+)[\'"]?\n(.*?)\n\1',
        cmd, re.DOTALL
    )
    codes = [code for _, code in hdocs]
    for m in re.finditer(r"python3?\s+-c\s+['\"]([^'\"]{20,})['\"]", cmd, re.DOTALL):
        codes.append(m.group(1))
    for code in codes:
        n_lines = code.count('\n') + 1
        if n_lines > 30:
            block(f'Inline Python {n_lines} 行 > 30 行上限 — 應透過 Skill tool 執行')
        if 'sys.stdout.reconfigure' in code:
            block('sys.stdout.reconfigure 在 inline Python 中 — 已知 SSOT 繞過模式')
        if has_write(code) and not allow_ipy_wr:
            block('Inline Python 含寫檔操作，但目標 SKILL.md 不包含 inline write — 繞過嘗試')
        for fn in known_fns:
            if re.search(rf'\bdef\s+{re.escape(fn)}\b', code):
                block(f'重新定義 SKILL.md 函式 "{fn}" — 應直接呼叫 Skill tool')

sys.exit(0)
