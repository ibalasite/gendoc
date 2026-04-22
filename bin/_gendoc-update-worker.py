#!/usr/bin/env python3
"""Background worker for gendoc-session-update.py — runs detached."""
import os, sys, subprocess

def main():
    if len(sys.argv) < 4:
        return
    gendoc_dir, stamp_file, lock_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        open(stamp_file, "w").close()
        subprocess.run(
            ["git", "-C", gendoc_dir, "pull", "--ff-only", "--quiet"],
            capture_output=True
        )
        install_py = os.path.join(gendoc_dir, "install.py")
        install_sh = os.path.join(gendoc_dir, "install.sh")
        if os.path.exists(install_py):
            subprocess.run([sys.executable, install_py, "--quiet"], capture_output=True)
        elif os.path.exists(install_sh):
            subprocess.run(["bash", install_sh, "--quiet"], capture_output=True)
    finally:
        try:
            os.rmdir(lock_dir)
        except OSError:
            pass

main()
