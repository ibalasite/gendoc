#!/usr/bin/env python3
"""
Safely add/remove hooks + env from ~/.claude/settings.json.
Cross-platform (macOS, Linux, Windows). Uses atomic write + dedup.

Usage:
  python3 gendoc-settings-hook.py add "<command>"          # SessionStart hook
  python3 gendoc-settings-hook.py remove                   # SessionStart hook
  python3 gendoc-settings-hook.py add-guard <tools_dir>    # 3 guard hooks
  python3 gendoc-settings-hook.py remove-guard             # 3 guard hooks
  python3 gendoc-settings-hook.py add-env                  # UTF-8 env (one-shot)
  python3 gendoc-settings-hook.py remove-env               # UTF-8 env
"""
import json, os, sys, tempfile

# Force UTF-8 stdout/stderr so prints containing CJK chars or emojis don't
# crash on Windows where default encoding is often cp950 / cp936.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SETTINGS     = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
MARKER       = "gendoc-session-update"
GUARD_MARKER = "gendoc-guard"


def load():
    if not os.path.exists(SETTINGS):
        return {}
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save(data):
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(SETTINGS), suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, SETTINGS)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _hook_exists(hook_list, cmd):
    return any(
        h.get("command", "") == cmd
        for entry in hook_list
        for h in entry.get("hooks", [])
    )


def _remove_by_marker(hook_list, marker):
    new_list, removed = [], 0
    for entry in hook_list:
        kept = [h for h in entry.get("hooks", []) if marker not in h.get("command", "")]
        if kept:
            entry["hooks"] = kept
            new_list.append(entry)
        else:
            removed += len(entry.get("hooks", []))
    return new_list, removed


# ── SessionStart hook ─────────────────────────────────────────────────────────

def cmd_add(command):
    data  = load()
    hooks = data.setdefault("hooks", {})
    ss    = hooks.setdefault("SessionStart", [])
    for entry in ss:
        for h in entry.get("hooks", []):
            if MARKER in h.get("command", ""):
                print("[gendoc-hook] 已存在，略過")
                return
    ss.append({"hooks": [{"type": "command", "command": command}]})
    save(data)
    print("[gendoc-hook] SessionStart hook 已加入")


def cmd_remove():
    data      = load()
    ss        = data.get("hooks", {}).get("SessionStart", [])
    new_ss, n = _remove_by_marker(ss, MARKER)
    if "SessionStart" in data.get("hooks", {}):
        data["hooks"]["SessionStart"] = new_ss
        if not new_ss:
            del data["hooks"]["SessionStart"]
        if not data["hooks"]:
            del data["hooks"]
    save(data)
    print(f"[gendoc-hook] 已移除 {n} 個 SessionStart hook entries")


# ── Guard hooks (PreToolUse / PostToolUse / Stop) ─────────────────────────────

def cmd_add_guard(tools_dir):
    # Build paths at RUNTIME inside the one-liner using os.path.expanduser so that
    # Git Bash's /c/Users/... style never gets baked into settings.json — Claude Code
    # runs hooks with the native Python/OS, which needs the correct path separator.
    _bin = "os.path.join(os.path.expanduser('~'),'.claude','skills','gendoc','tools','bin')"

    # PreToolUse blocker: resilient wrapper — pass stdin through and exit 0 if the
    # script doesn't exist yet, preventing accidental blocking during fresh install.
    blocker_cmd = (
        "python3 -c \""
        "import sys,os,subprocess; "
        f"p=os.path.join({_bin},'gendoc-guard-blocker.py'); "
        "b=sys.stdin.buffer.read(); "
        "sys.exit(subprocess.run([sys.executable,p],input=b,stdout=sys.stdout.buffer).returncode) "
        "if os.path.exists(p) "
        "else (sys.stdout.buffer.write(b),sys.exit(0))\""
    )

    history_cmd = (
        "python3 -c \""
        "import sys,os,subprocess; "
        f"p=os.path.join({_bin},'gendoc-guard-history.py'); "
        "b=sys.stdin.buffer.read(); "
        "os.path.exists(p) and sys.exit(subprocess.run([sys.executable,p],input=b).returncode)\""
    )

    stop_cmd = (
        "python3 -c \""
        "import sys,os,subprocess; "
        f"p=os.path.join({_bin},'gendoc-guard-stop.py'); "
        "os.path.exists(p) and sys.exit(subprocess.run([sys.executable,p]).returncode)\""
    )

    data  = load()
    hooks = data.setdefault("hooks", {})

    # Remove old / stale guard hooks first so format upgrades apply cleanly
    for event in ("PreToolUse", "PostToolUse", "Stop"):
        hooks.setdefault(event, [])
        new_list, _ = _remove_by_marker(hooks[event], GUARD_MARKER)
        hooks[event] = new_list

    pre_list  = hooks["PreToolUse"]
    post_list = hooks["PostToolUse"]
    stop_list = hooks["Stop"]

    added = 0

    if not _hook_exists(pre_list, blocker_cmd):
        pre_list.append({
            "matcher": "*",
            "hooks": [{"type": "command", "command": blocker_cmd, "timeout": 10}]
        })
        added += 1
        print("[gendoc-hook] ✅ PreToolUse (blocker) hook 已加入")
    else:
        print("[gendoc-hook] PreToolUse (blocker) hook 已存在，略過")

    if not _hook_exists(post_list, history_cmd):
        post_list.append({
            "matcher": "*",
            "hooks": [{"type": "command", "command": history_cmd, "timeout": 10}]
        })
        added += 1
        print("[gendoc-hook] ✅ PostToolUse (history) hook 已加入")
    else:
        print("[gendoc-hook] PostToolUse (history) hook 已存在，略過")

    if not _hook_exists(stop_list, stop_cmd):
        stop_list.append({
            "hooks": [{"type": "command", "command": stop_cmd, "timeout": 10}]
        })
        added += 1
        print("[gendoc-hook] ✅ Stop hook 已加入")
    else:
        print("[gendoc-hook] Stop hook 已存在，略過")

    save(data)
    print(f"[gendoc-hook] guard hooks 安裝完成（新增 {added} 個）")


def cmd_remove_guard():
    data    = load()
    h       = data.get("hooks", {})
    removed = 0

    for event in ("PreToolUse", "PostToolUse", "Stop"):
        if event not in h:
            continue
        new_list, n = _remove_by_marker(h[event], GUARD_MARKER)
        removed += n
        h[event] = new_list
        if not new_list:
            del h[event]

    if not h:
        data.pop("hooks", None)

    save(data)
    print(f"[gendoc-hook] 已移除 {removed} 個 guard hook entries")


# ── UTF-8 env (single source for all Python subprocesses Claude Code spawns) ──
#
# Claude Code injects ~/.claude/settings.json `env` into every spawned
# subprocess (Bash tool, hook scripts, inline python3). Setting
# PYTHONIOENCODING=utf-8 + PYTHONUTF8=1 here once removes the need for any
# individual script to call sys.stdout.reconfigure(encoding="utf-8") — new
# Python scripts added later "just work" on Windows cp950 / cp936 terminals.
#
# Merge-style: respects pre-existing `env` keys the user set themselves,
# only writes our two keys if absent (or with our exact value).

ENV_KEYS = {
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
}


def cmd_add_env():
    data = load()
    env = data.setdefault("env", {})
    added, kept = [], []
    for k, v in ENV_KEYS.items():
        if env.get(k) == v:
            kept.append(k)
        else:
            env[k] = v
            added.append(k)
    save(data)
    if added:
        print(f"[gendoc-hook] env 已寫入：{', '.join(added)}")
    if kept:
        print(f"[gendoc-hook] env 已存在略過：{', '.join(kept)}")


def cmd_remove_env():
    data = load()
    env = data.get("env", {})
    removed = []
    for k, v in ENV_KEYS.items():
        if env.get(k) == v:
            del env[k]
            removed.append(k)
    if "env" in data and not data["env"]:
        del data["env"]
    save(data)
    print(f"[gendoc-hook] env 已移除：{', '.join(removed) if removed else '無'}")


# ── dispatch ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "add":
        if len(sys.argv) < 3:
            print("用法：gendoc-settings-hook.py add <command>"); sys.exit(1)
        cmd_add(sys.argv[2])
    elif action == "remove":
        cmd_remove()
    elif action == "add-guard":
        if len(sys.argv) < 3:
            print("用法：gendoc-settings-hook.py add-guard <tools_dir>"); sys.exit(1)
        cmd_add_guard(sys.argv[2])
    elif action == "remove-guard":
        cmd_remove_guard()
    elif action == "add-env":
        cmd_add_env()
    elif action == "remove-env":
        cmd_remove_env()
    else:
        print("用法：gendoc-settings-hook.py {add <command>|remove|add-guard <tools_dir>|remove-guard|add-env|remove-env}")
        sys.exit(1)
