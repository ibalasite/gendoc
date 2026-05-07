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

function Register-Hooks {
    Log "[deploy] register SessionStart hook..."
    & $py $SettingsHook add $HookCmd

    Log "[deploy] register guard hooks (PreToolUse / PostToolUse / Stop)..."
    & $py $SettingsHook add-guard $ToolsBin
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
    Register-Hooks

    Log ""
    Log "[install] done. Restart Claude Code to activate skills."
}

function Do-Uninstall {
    Log "[uninstall] remove hooks..."
    if (Test-Path $SettingsHook) {
        & $py $SettingsHook remove
        & $py $SettingsHook remove-guard
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
