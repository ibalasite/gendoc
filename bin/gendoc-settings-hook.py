#!/usr/bin/env python3
"""
Safely add/remove a SessionStart hook from ~/.claude/settings.json.
Cross-platform (macOS, Linux, Windows). Uses atomic write + dedup.

Usage:
  python3 gendoc-settings-hook.py add "<command>"
  python3 gendoc-settings-hook.py remove
"""
import json, os, sys, tempfile

SETTINGS = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
MARKER   = "gendoc-session-update"

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

def cmd_add(command):
    data = load()
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
    data = load()
    ss = data.get("hooks", {}).get("SessionStart", [])
    new_ss, removed = [], 0
    for entry in ss:
        kept = [h for h in entry.get("hooks", []) if MARKER not in h.get("command", "")]
        if kept:
            entry["hooks"] = kept
            new_ss.append(entry)
        else:
            removed += len(entry.get("hooks", []))
    if "SessionStart" in data.get("hooks", {}):
        data["hooks"]["SessionStart"] = new_ss
        if not new_ss:
            del data["hooks"]["SessionStart"]
        if not data["hooks"]:
            del data["hooks"]
    save(data)
    print(f"[gendoc-hook] 已移除 {removed} 個 hook entries")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "add":
        if len(sys.argv) < 3:
            print("用法：gendoc-settings-hook.py add <command>"); sys.exit(1)
        cmd_add(sys.argv[2])
    elif action == "remove":
        cmd_remove()
    else:
        print("用法：gendoc-settings-hook.py {add <command>|remove}"); sys.exit(1)
