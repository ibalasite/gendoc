# gendoc setup.ps1 -- Windows native (PowerShell) version
# Usage:
#   .\setup.ps1             # install (default)
#   .\setup.ps1 install     # same as above
#   .\setup.ps1 uninstall   # remove hook + delete runtime
#   .\setup.ps1 upgrade     # git pull + re-deploy

param(
    [string]$Command = "install"
)

$ErrorActionPreference = "Stop"

# Force UTF-8 across the whole setup pipeline. Without this, Windows Python
# defaults stdout to cp950 (zh-TW) / cp936 (zh-CN), so any print containing
# CJK or emoji (e.g. the hook installer's "✅ ... 已加入") raises
# UnicodeEncodeError and aborts setup. Apply at both env and console layers
# so child Python procs and PowerShell's own buffer both stay UTF-8.
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # Older Windows PowerShell hosts may reject this; ignore — env vars above
    # are sufficient for the Python subprocesses we actually care about.
}
$RepoUrl         = "https://github.com/ibalasite/gendoc.git"
$RuntimeDir      = Join-Path $env:USERPROFILE ".claude\skills\gendoc"
$SkillsSrc       = Join-Path $RuntimeDir "skills"
$ToolsBin        = Join-Path $RuntimeDir "tools\bin"
$ClaudeSkillsDir = Join-Path $env:USERPROFILE ".claude\skills"
$SettingsHook    = Join-Path $RuntimeDir "bin\gendoc-settings-hook.py"
$HookPy          = Join-Path $RuntimeDir "bin\gendoc-session-update.py"

# Test actual execution — Get-Command python3 on Windows may return the
# Microsoft Store stub which opens the Store (exit 49) instead of running Python.
function Find-Python {
    foreach ($candidate in @("python3", "python")) {
        try {
            $out = & $candidate --version 2>&1
            if ($LASTEXITCODE -eq 0 -and "$out" -match "Python 3") { return $candidate }
        } catch {}
    }
    return $null
}

$py = Find-Python
if (-not $py) { Write-Error "Python 3 not found (tried python3 and python)"; exit 1 }
$HookCmd = "$py `"$HookPy`""

function Log($msg) { Write-Host $msg }

function Deploy-Skills {
    Log "[deploy] copy skills -> ~/.claude/skills/"
    New-Item -ItemType Directory -Force -Path $ClaudeSkillsDir | Out-Null
    Get-ChildItem -Path $SkillsSrc -Directory | ForEach-Object {
        $dest = Join-Path $ClaudeSkillsDir $_.Name
        if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
        Copy-Item -Recurse $_.FullName $dest
        Log "  - $($_.Name)"
    }
}

function Deploy-Tools {
    # Source-of-truth packages live in tools/<package>/, runtime executables in tools/bin/.
    # Two deploy modes (auto-selected per package):
    #   1. build.ps1 / build.sh present -> run it; package owns its build
    #      (gets env: BIN_DIR, PACKAGE_DIR)
    #   2. otherwise -> cp tools/<package>/<package>.py -> bin/<package>.py
    Log "[deploy] deploy tools/<package>/ source to $ToolsBin/"
    if (-not (Test-Path $ToolsBin)) {
        New-Item -ItemType Directory -Force -Path $ToolsBin | Out-Null
    }
    $toolsRoot = Join-Path $RuntimeDir "tools"
    Get-ChildItem -Path $toolsRoot -Directory | ForEach-Object {
        $pkgDir = $_.FullName
        $pkgName = $_.Name
        if ($pkgName -eq 'bin') { return }

        $buildPs = Join-Path $pkgDir "build.ps1"
        $buildSh = Join-Path $pkgDir "build.sh"
        $entry   = Join-Path $pkgDir "$pkgName.py"

        if (Test-Path $buildPs) {
            Log "  - build $pkgName (build.ps1)"
            $env:BIN_DIR = $ToolsBin
            $env:PACKAGE_DIR = $pkgDir
            try {
                & powershell -NoProfile -ExecutionPolicy Bypass -File $buildPs
                if ($LASTEXITCODE -ne 0) { throw "build.ps1 exit $LASTEXITCODE" }
            } catch {
                Log "  x build.ps1 failed for $pkgName : $_"
                throw
            } finally {
                Remove-Item Env:BIN_DIR, Env:PACKAGE_DIR -ErrorAction SilentlyContinue
            }
        }
        elseif ((Test-Path $buildSh) -and (Get-Command bash -ErrorAction SilentlyContinue)) {
            Log "  - build $pkgName (build.sh via bash)"
            $env:BIN_DIR = $ToolsBin
            $env:PACKAGE_DIR = $pkgDir
            try {
                bash $buildSh
                if ($LASTEXITCODE -ne 0) { throw "build.sh exit $LASTEXITCODE" }
            } catch {
                Log "  x build.sh failed for $pkgName : $_"
                throw
            } finally {
                Remove-Item Env:BIN_DIR, Env:PACKAGE_DIR -ErrorAction SilentlyContinue
            }
        }
        elseif (Test-Path $entry) {
            $dst = Join-Path $ToolsBin "$pkgName.py"
            Copy-Item -Force $entry $dst
            Log "  - $pkgName/$pkgName.py -> bin/$pkgName.py"
        }
    }
}

function Register-Hooks {
    Log "[deploy] register SessionStart hook..."
    & $py $SettingsHook add $HookCmd

    Log "[deploy] register guard hooks (PreToolUse / PostToolUse / Stop)..."
    & $py $SettingsHook add-guard $ToolsBin

    Log "[deploy] register UTF-8 env (single source for all Python subprocs)..."
    & $py $SettingsHook add-env
}

function Do-Install {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Error "git required"; exit 1 }
    if (-not (Get-Command $py -ErrorAction SilentlyContinue)) { Write-Error "Python 3 required"; exit 1 }

    if (Test-Path (Join-Path $RuntimeDir ".git")) {
        Log "[install] $RuntimeDir already exists, running upgrade..."
        Do-Upgrade; return
    }

    Log "[install] clone gendoc -> $RuntimeDir"
    git clone $RepoUrl $RuntimeDir

    Deploy-Skills
    Deploy-Tools
    Register-Hooks

    Log ""
    Log "[install] done. Restart Claude Code to activate skills."
}

function Do-Uninstall {
    Log "[uninstall] remove hooks..."
    if (Test-Path $SettingsHook) {
        & $py $SettingsHook remove
        & $py $SettingsHook remove-guard
        & $py $SettingsHook remove-env
    }

    Log "[uninstall] remove copied skills..."
    if (Test-Path $SkillsSrc) {
        Get-ChildItem -Path $SkillsSrc -Directory | ForEach-Object {
            $dest = Join-Path $ClaudeSkillsDir $_.Name
            if (Test-Path $dest) { Remove-Item -Recurse -Force $dest; Log "  - removed $($_.Name)" }
        }
    }

    Log "[uninstall] delete $RuntimeDir..."
    if (Test-Path $RuntimeDir) { Remove-Item -Recurse -Force $RuntimeDir }
    Log "[uninstall] done."
}

function Do-Upgrade {
    if (-not (Test-Path (Join-Path $RuntimeDir ".git"))) {
        Write-Error "[upgrade] $RuntimeDir not found. Run install first."; exit 1
    }
    Log "[upgrade] git pull..."
    git -C $RuntimeDir pull --ff-only
    Deploy-Skills
    Deploy-Tools
    Register-Hooks
    Log "[upgrade] done."
}

switch ($Command.ToLower()) {
    "install"   { Do-Install }
    "uninstall" { Do-Uninstall }
    "upgrade"   { Do-Upgrade }
    default {
        Write-Host "Usage: .\setup.ps1 [install|uninstall|upgrade]"
        exit 1
    }
}
