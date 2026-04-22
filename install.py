#!/usr/bin/env python3
"""
install.py — cross-platform version of install.sh (Windows native support).
Syncs gendoc skills from repo to ~/.claude/skills/
Usage: python3 install.py [--quiet]
"""
import os, sys, shutil

GENDOC_DIR  = os.path.dirname(os.path.abspath(__file__))
SKILLS_SRC  = os.path.join(GENDOC_DIR, "skills")
SKILLS_DST  = os.path.join(os.path.expanduser("~"), ".claude", "skills")
QUIET       = "--quiet" in sys.argv

def log(msg):
    if not QUIET:
        print(msg)

if not os.path.isdir(SKILLS_SRC):
    print(f"❌ skills/ 目錄不存在：{SKILLS_SRC}")
    sys.exit(1)

log(f"[install] 同步 gendoc skills → {SKILLS_DST}")

for skill_name in os.listdir(SKILLS_SRC):
    src = os.path.join(SKILLS_SRC, skill_name, "SKILL.md")
    if not os.path.isfile(src):
        continue
    dst_dir = os.path.join(SKILLS_DST, skill_name)
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, "SKILL.md"))
    log(f"  ✓ {skill_name}")

stamp = os.path.join(GENDOC_DIR, ".last-update-check")
try:
    os.remove(stamp)
except OSError:
    pass

log("[install] 完成")
