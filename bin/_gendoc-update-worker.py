#!/usr/bin/env python3
"""Background worker for gendoc-session-update.py — runs detached."""
import os, sys, subprocess

def main():
    if len(sys.argv) < 4:
        return
    runtime_dir, stamp_file, lock_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        open(stamp_file, "w").close()
        if sys.platform == "win32":
            setup_ps1 = os.path.join(runtime_dir, "setup.ps1")
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", setup_ps1, "upgrade"],
                capture_output=True,
            )
        else:
            setup = os.path.join(runtime_dir, "setup")
            subprocess.run(["bash", setup, "upgrade", "--quiet"], capture_output=True)
    finally:
        try:
            os.rmdir(lock_dir)
        except OSError:
            pass

main()
