#!/usr/bin/env python3
"""
SessionStart hook: auto-update gendoc (cross-platform, Windows native support)
Design: non-blocking background process, 1h throttle, atomic lockfile, always exit 0
"""
import os, sys, subprocess, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GENDOC_DIR = os.path.dirname(SCRIPT_DIR)
STAMP_FILE = os.path.join(GENDOC_DIR, ".last-update-check")
LOCK_DIR   = os.path.join(GENDOC_DIR, ".update-lock")
THROTTLE   = 3600

# Guard: must be a git repo
if not os.path.isdir(os.path.join(GENDOC_DIR, ".git")):
    sys.exit(0)

# Throttle
if os.path.exists(STAMP_FILE):
    if time.time() - os.path.getmtime(STAMP_FILE) < THROTTLE:
        sys.exit(0)

# Lock (atomic mkdir)
try:
    os.mkdir(LOCK_DIR)
except OSError:
    sys.exit(0)

# Spawn background worker and return immediately
worker = os.path.join(SCRIPT_DIR, "_gendoc-update-worker.py")
try:
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    subprocess.Popen([sys.executable, worker, GENDOC_DIR, STAMP_FILE, LOCK_DIR], **kwargs)
except Exception:
    try:
        os.rmdir(LOCK_DIR)
    except OSError:
        pass

sys.exit(0)
