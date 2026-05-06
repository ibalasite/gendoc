---
name: gendoc-guard
description: 監控任意 skill 執行，session 中斷時自動排隊重新喚起，並透過 SECS 白名單攔截未授權工具呼叫。用法：/gendoc-guard <skill-name>
version: 2.0.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Skill
---

# gendoc-guard

```
Input:   /gendoc-guard <target-skill-name>
Output:  執行目標 skill，中斷時自動排隊下次 session 繼續
         + SECS：PreToolUse 攔截白名單外的工具呼叫
         + PostToolUse：記錄每次工具呼叫至 history
Purpose: 不修改任何目標 skill，外掛式監控 + 自動重啟 + 合規執行
```

---

## Step 0：解析目標 Skill

```bash
source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

# 從 args 取得目標 skill 名稱
_TARGET="${ARGS:-}"
if [ -z "$_TARGET" ]; then
  echo "[GUARD] ❌ 用法：/gendoc-guard <skill-name>"
  echo "         例如：/gendoc-guard gendoc-repair"
  exit 1
fi
echo "[GUARD] 目標 skill：/$_TARGET"
echo "[GUARD] 工作目錄：$(pwd)"
```

---

## Step 1：建立監控 Marker（含 SECS 白名單）

> **⚠️ 此步驟在 guard 啟動前執行一次性寫入，禁止拆成兩步。**
> guard 不存在時 blocker exit 0，所以本步驟不受任何 SECS 限制。
> 白名單分析（原 Step 2.5）已合併於此，確保只有一次 guard 檔寫入。

```python
import json, os, re
from datetime import datetime, timezone
from pathlib import Path

_target    = os.environ.get('_TARGET', '')
_guard_file = '.gendoc-guard.json'

# ── 1. 計算重試次數（guard 不存在時為 0）──────────────────────
_existing = {}
if os.path.exists(_guard_file):
    try:
        _existing = json.load(open(_guard_file, encoding='utf-8'))
    except Exception:
        pass
_retry_count = (
    _existing.get('retry_count', 0)
    if _existing.get('target_skill') == _target else 0
)

# ── 2. SECS 白名單靜態分析（純讀取，不寫任何檔案）────────────
def _extract_whitelist(path, depth=0, visited=None):
    if visited is None:
        visited = set()
    key = str(path)
    if key in visited or depth > 3:
        return {}
    visited.add(key)
    try:
        content = open(path, encoding='utf-8').read()
    except Exception:
        return {}
    result = {
        'tool_types': set(), 'skill_calls': set(),
        'known_functions': set(), 'allow_inline_python_write': False,
    }
    fm = re.search(r'^---\n(.+?)\n---', content, re.DOTALL)
    if fm:
        for t in re.findall(r'- (\S+)', fm.group(1)):
            if t not in ('name', 'description', 'version'):
                result['tool_types'].add(t)
    for m in re.finditer(
        r'(?:Skill\s+tool[^`\n]{0,40}`([a-zA-Z0-9_-]+)`'
        r'|呼叫\s+`([a-zA-Z0-9_-]+)`'
        r'|→\s+([a-zA-Z][a-zA-Z0-9_-]+)\s+skill'
        r'|/([a-zA-Z][a-zA-Z0-9_-]+)\s)',
        content
    ):
        name = next((g for g in m.groups() if g), None)
        if name and ('-' in name or name.startswith('gendoc')):
            result['skill_calls'].add(name)
    WRITE_PATS = [
        r"open\s*\([^)]*['\"][wa]", r"json\.dump\s*\(",
        r"\.write\s*\(", r"os\.replace\s*\(", r"os\.rename\s*\(",
    ]
    for block in re.findall(r'```(?:python|bash|sh|py)?\n(.*?)```', content, re.DOTALL):
        for fn in re.findall(r'^\s*def\s+(\w+)\s*\(', block, re.MULTILINE):
            result['known_functions'].add(fn)
        if any(re.search(p, block) for p in WRITE_PATS):
            result['allow_inline_python_write'] = True
    json_refs = set()
    for block in re.findall(r'```[^\n]*\n(.*?)```', content, re.DOTALL):
        for m in re.finditer(r"""['"]([^'"*\s]+\.json)['"]""", block):
            json_refs.add(Path(m.group(1)).name)
        for m in re.finditer(r'\b([a-zA-Z0-9_-]+\.json)\b', block):
            json_refs.add(m.group(1))
    json_refs = {r for r in json_refs if len(r) > 8}
    SKILL_NAME_RE = re.compile(r'\b([a-zA-Z][a-zA-Z0-9]*(?:-[a-zA-Z0-9]+)+)\b')
    def _walk_json(obj):
        if isinstance(obj, str):
            for m in SKILL_NAME_RE.finditer(obj):
                if '-' in m.group(1): result['skill_calls'].add(m.group(1))
        elif isinstance(obj, dict):
            for v in obj.values(): _walk_json(v)
        elif isinstance(obj, list):
            for v in obj: _walk_json(v)
    for ref in json_refs:
        for base in [path.parent.parent / 'templates',
                     Path.home() / '.claude' / 'skills' / 'gendoc' / 'templates']:
            p = base / ref
            if p.exists():
                try: _walk_json(json.loads(p.read_text(encoding='utf-8')))
                except Exception: pass
                break
    parent_dir = path.parent.parent
    for sub in list(result['skill_calls']):
        sub_wl = _extract_whitelist(parent_dir / sub / 'SKILL.md', depth + 1, visited)
        result['skill_calls'].update(sub_wl.get('skill_calls', set()))
        result['known_functions'].update(sub_wl.get('known_functions', set()))
        if sub_wl.get('allow_inline_python_write'): result['allow_inline_python_write'] = True
    return {
        'tool_types': sorted(result['tool_types']),
        'skill_calls': sorted(result['skill_calls']),
        'known_functions': sorted(result['known_functions']),
        'allow_inline_python_write': result['allow_inline_python_write'],
    }

whitelist = {}
if _target:
    home = Path.home()
    candidates = [
        home / '.claude' / 'skills' / 'gendoc' / _target / 'SKILL.md',
        home / '.claude' / 'skills' / _target / 'SKILL.md',
        Path(f'skills/{_target}/SKILL.md'),
    ]
    skill_md = next((p for p in candidates if p.exists()), None)
    if skill_md:
        whitelist = _extract_whitelist(skill_md)
        print(f'[GUARD] SECS 白名單來源：{skill_md}')
        print(f'[GUARD] skill_calls: {whitelist["skill_calls"]}')
        print(f'[GUARD] allow_inline_python_write: {whitelist["allow_inline_python_write"]}')
    else:
        print(f'[GUARD] WARNING: 找不到 /{_target} SKILL.md，SECS 停用')

# ── 3. 一次性寫入完整 guard（guard 尚未啟動，blocker exit 0）──
marker = {
    "target_skill": _target,
    "status": "running",
    "phase": "invoking",
    "cwd": os.getcwd(),
    "started_at": datetime.now(timezone.utc).isoformat(),
    "retry_count": _retry_count,
    "max_retries": 5,
    "secs_whitelist": whitelist,
}
with open(_guard_file, 'w', encoding='utf-8') as f:
    json.dump(marker, f, indent=2, ensure_ascii=False)

if _retry_count > 0:
    print(f"[GUARD] ♻️  Resume 模式（第 {_retry_count} 次重試）")
else:
    print(f"[GUARD] ✅ 監控 marker 建立（含 SECS 白名單）：{_guard_file}")
```

---

## Step 2：呼叫目標 Skill

用 **Skill tool** 呼叫 `_TARGET`，不傳任何 args。

等待 Skill tool 回傳後才繼續 Step 3。

若目標 skill 回傳錯誤或 exception，記錄原因並繼續 Step 3（不中止）。

---

## Step 3：正常完成，刪除所有 guard 檔案

```python
import os

_GUARD_FILES = [
    '.gendoc-guard.json',
    '.gendoc-guard-queue',
    '.gendoc-guard-history.jsonl',
]

for _f in _GUARD_FILES:
    try:
        os.remove(_f)
    except FileNotFoundError:
        pass

print(f"\n[GUARD] ✅ /{os.environ.get('_TARGET','')} 正常完成，監控結束")
print(f"[GUARD] guard 檔案已清除，Stop hook 不再觸發")
```

---

## 附錄：Marker 格式

`.gendoc-guard.json` 存在於目標專案根目錄，不加入 git（應在 `.gitignore` 中排除）。

| 欄位 | 說明 |
|------|------|
| `target_skill` | 被監控的 skill 名稱 |
| `status` | `running` / `queued` / `complete` / `max_retries_exceeded` |
| `phase` | 當前執行階段（由目標 skill 自選更新，可選） |
| `cwd` | 目標專案目錄（Stop hook 使用） |
| `retry_count` | 已重啟次數 |
| `max_retries` | 最大重啟次數（預設 5） |
| `secs_whitelist` | SECS 白名單（Step 1 寫入） |
| `secs_whitelist.tool_types` | 目標 skill 允許使用的工具列表 |
| `secs_whitelist.skill_calls` | 允許呼叫的 skill 名稱（遞迴展開） |
| `secs_whitelist.known_functions` | SKILL.md 中定義的已知函式 |
| `secs_whitelist.allow_inline_python_write` | 目標 skill 是否含 inline Python 寫檔 |

`.gendoc-guard-history.jsonl`：每行一筆 PostToolUse 記錄，最多保留 500 筆。

| 欄位 | 說明 |
|------|------|
| `ts` | ISO 8601 時間戳 |
| `tool` | 工具名稱（Bash/Write/Skill/Read 等） |
| `result` | 工具回傳類型 |
| `summary` | 呼叫摘要（最多 120 字元） |

## 附錄：流程圖

```
/gendoc-guard gendoc-repair
      │
      ▼
Step 1：自安裝 4 個 hook（idempotent）
  ├── Stop hook          → 中斷時寫 queue + history snapshot
  ├── SessionStart hook  → 讀 queue + inject context + history 摘要
  ├── PreToolUse hook    → SECS 白名單攔截（exit 2 = block）
  └── PostToolUse hook   → 記錄每次工具呼叫至 history.jsonl
      │
      ▼
Step 1：SECS 白名單靜態分析 + 寫入完整 .gendoc-guard.json
  ├── 讀 ~/.claude/skills/gendoc/{target}/SKILL.md（純讀取）
  ├── 提取：allowed-tools / skill_calls / known_functions / allow_inline_python_write
  ├── 遞迴展開 sub-skill（最多 3 層）
  └── 一次性寫入 guard（guard 尚未啟動，blocker exit 0）
      │
      ▼
Step 2：Skill tool → gendoc-repair（PreToolUse hook 全程監控）
      │
      ├── 正常完成 ──→ Step 3：刪除所有 guard 檔案 → 結束
      │
      └── session 中斷（context limit / crash / 手動結束）
                │
                ▼
           Stop hook 觸發
                ├── 附加最後 20 筆 history 至 queue
                ├── retry >= max → 通知停止
                └── retry < max → 寫 .gendoc-guard-queue，macOS 通知
                                        │
                                        ▼
                                  下次 claude session 開啟
                                        │
                                        ▼
                                  SessionStart hook
                                  讀 queue + history 摘要
                                  inject additionalContext
                                        │
                                        ▼
                                  Claude 自動執行
                                  /gendoc-guard gendoc-repair
                                  （retry_count + 1）

SECS 三層攔截規則（PreToolUse hook）：
  Layer 1 - 純讀放行：
    Bash inline Python 無寫檔 pattern → 直接 exit 0

  Layer 2 - 白名單執行：
    Skill tool → 只允許 secs_whitelist.skill_calls 內的 skill

  Layer 3 - 通用異常偵測（無需白名單）：
    × Inline Python > 30 行
    × sys.stdout.reconfigure 在 inline Python 中
    × Inline Python 含寫檔且 allow_inline_python_write=False
    × 重新定義 known_functions 中的函式
```
