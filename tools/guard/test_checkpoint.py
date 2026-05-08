#!/usr/bin/env python3
"""Checkpoint exemption 測試：

驗證 blocker 對 cleanup checkpoint 的判斷：
- 沒 checkpoint → BLOCK（既有 T1-A）
- 有 checkpoint + 0 commit → PASS
- 有 checkpoint + 全實質 commit → PASS
- 有 checkpoint + 任一 empty commit → BLOCK
- 有 checkpoint + 非 git repo → PASS
- Checkpoint 一次性消耗（用過再 rm 應 BLOCK）
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
BLOCKER = REPO / 'tools' / 'bin' / 'gendoc-guard-blocker.py'

spec = importlib.util.spec_from_file_location('b', BLOCKER)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def _setup_git_repo():
    """建立空 git repo + 初始 commit，回傳 (tmp_dir, init_commit_sha)。"""
    tmp = tempfile.mkdtemp()
    os.chdir(tmp)
    subprocess.run(['git', 'init', '-q'], check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test'], check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test'], check=True)
    pathlib.Path('README.md').write_text('init\n')
    subprocess.run(['git', 'add', 'README.md'], check=True)
    subprocess.run(['git', 'commit', '-q', '-m', 'init'], check=True)
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    return tmp, sha


def _write_guard(start_commit: str = ''):
    pathlib.Path('.gendoc-guard.json').write_text(json.dumps({
        'target_skill': 'test',
        'status': 'running',
        'start_commit': start_commit,
    }))


def _write_checkpoint():
    pathlib.Path('.gendoc-guard-checkpoint').write_text('done')


CLEANUP_CMD = (
    'rm -f .gendoc-guard.json .gendoc-guard-queue '
    '.gendoc-guard-history.jsonl .gendoc-guard-checkpoint'
)


def case(name, want_pass, setup_fn):
    """跑單一 case：setup → evaluate → 比對結果。"""
    cwd0 = os.getcwd()
    tmp = tempfile.mkdtemp()
    os.chdir(tmp)
    try:
        setup_fn()
        result = b.evaluate_bash(CLEANUP_CMD)
        actual_pass = result is None
        ok = actual_pass == want_pass
        mark = '✅' if ok else '❌'
        verdict = 'PASS' if actual_pass else f'BLOCK ({result})'
        want_str = 'PASS' if want_pass else 'BLOCK'
        print(f'  {mark} [{name}] got={verdict} want={want_str}')
        return ok
    finally:
        os.chdir(cwd0)
        shutil.rmtree(tmp, ignore_errors=True)


def case_with_repo(name, want_pass, setup_in_repo):
    """跑 case 但需要 git repo。"""
    cwd0 = os.getcwd()
    tmp, init_sha = _setup_git_repo()
    try:
        setup_in_repo(init_sha)
        result = b.evaluate_bash(CLEANUP_CMD)
        actual_pass = result is None
        ok = actual_pass == want_pass
        mark = '✅' if ok else '❌'
        verdict = 'PASS' if actual_pass else f'BLOCK ({result})'
        want_str = 'PASS' if want_pass else 'BLOCK'
        print(f'  {mark} [{name}] got={verdict} want={want_str}')
        return ok
    finally:
        os.chdir(cwd0)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print('=' * 78)
    print(f'CHECKPOINT EXEMPTION TEST  blocker={BLOCKER}')
    print('=' * 78)

    fails = 0

    # 1. 沒 checkpoint 直接 rm → BLOCK
    def setup_no_ckpt():
        _write_guard()  # no start_commit
    if not case('no-checkpoint', False, setup_no_ckpt):
        fails += 1

    # 2. 有 checkpoint + 非 git repo（start_commit 空）→ PASS（寬鬆）
    def setup_no_git():
        _write_guard(start_commit='')
        _write_checkpoint()
    if not case('checkpoint+no-git', True, setup_no_git):
        fails += 1

    # 3. 有 checkpoint + 0 commit since baseline → PASS
    def setup_zero_commits(init_sha):
        _write_guard(start_commit=init_sha)
        _write_checkpoint()
    if not case_with_repo('checkpoint+zero-commits', True, setup_zero_commits):
        fails += 1

    # 4. 有 checkpoint + 1 個有實質內容的 commit → PASS
    def setup_real_commit(init_sha):
        _write_guard(start_commit=init_sha)
        pathlib.Path('feature.py').write_text(
            'def hello():\n    return "world"\n' * 5
        )
        subprocess.run(['git', 'add', 'feature.py'], check=True)
        subprocess.run(['git', 'commit', '-q', '-m', 'real work'], check=True)
        _write_checkpoint()
    if not case_with_repo('checkpoint+real-commit', True, setup_real_commit):
        fails += 1

    # 5. 有 checkpoint + 1 個 empty commit → BLOCK
    def setup_empty_commit(init_sha):
        _write_guard(start_commit=init_sha)
        subprocess.run(
            ['git', 'commit', '-q', '--allow-empty', '-m', 'fake'],
            check=True,
        )
        _write_checkpoint()
    if not case_with_repo('checkpoint+empty-commit', False, setup_empty_commit):
        fails += 1

    # 6. 有 checkpoint + 多 commit 中混入 empty → BLOCK
    def setup_mixed(init_sha):
        _write_guard(start_commit=init_sha)
        pathlib.Path('a.py').write_text('print(1)\n')
        subprocess.run(['git', 'add', 'a.py'], check=True)
        subprocess.run(['git', 'commit', '-q', '-m', 'real 1'], check=True)
        subprocess.run(
            ['git', 'commit', '-q', '--allow-empty', '-m', 'fake'],
            check=True,
        )
        pathlib.Path('b.py').write_text('print(2)\n')
        subprocess.run(['git', 'add', 'b.py'], check=True)
        subprocess.run(['git', 'commit', '-q', '-m', 'real 2'], check=True)
        _write_checkpoint()
    if not case_with_repo('checkpoint+mixed-with-empty', False, setup_mixed):
        fails += 1

    # 7. 有 checkpoint + start_commit 不可達（亂值）→ BLOCK（保守）
    def setup_bad_baseline(init_sha):
        _write_guard(start_commit='deadbeef' * 5)
        _write_checkpoint()
    if not case_with_repo('checkpoint+invalid-baseline', False, setup_bad_baseline):
        fails += 1

    # 8. Checkpoint 一次性消耗：第一次 PASS，第二次 BLOCK
    print('\n[一次性消耗驗證]')
    cwd0 = os.getcwd()
    tmp, init_sha = _setup_git_repo()
    try:
        _write_guard(start_commit=init_sha)
        _write_checkpoint()
        r1 = b.evaluate_bash(CLEANUP_CMD)
        r2 = b.evaluate_bash(CLEANUP_CMD)
        ok = (r1 is None) and (r2 is not None)
        mark = '✅' if ok else '❌'
        print(f'  {mark} [single-use] 1st={r1}  2nd={r2}')
        if not ok:
            fails += 1
    finally:
        os.chdir(cwd0)
        shutil.rmtree(tmp, ignore_errors=True)

    print('\n' + '=' * 78)
    print(f'TOTAL: {8 - fails} PASS / {fails} FAIL')
    print('=' * 78)
    return 0 if fails == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
