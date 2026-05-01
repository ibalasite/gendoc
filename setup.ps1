# gendoc setup.ps1 — Windows native (PowerShell) version
# Usage:
#   .\setup.ps1             # install (default)
#   .\setup.ps1 install     # same as above
#   .\setup.ps1 uninstall   # remove hook + delete runtime
#   .\setup.ps1 upgrade     # git pull + re-deploy

param(
    [string]$Command = "install"
)

$ErrorActionPreference = "Stop"
$RepoUrl     = "https://github.com/ibalasite/gendoc.git"
$RuntimeDir  = Join-Path $env:USERPROFILE ".claude\skills\gendoc"
$SkillsSrc   = Join-Path $RuntimeDir "skills"
$ClaudeSkillsDir = Join-Path $env:USERPROFILE ".claude\skills"
$SettingsHook = Join-Path $RuntimeDir "bin\gendoc-settings-hook.py"
$HookPy      = Join-Path $RuntimeDir "bin\gendoc-session-update.py"

$py = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }
$HookCmd = "$py `"$HookPy`""

function Log($msg) { Write-Host $msg }

function Deploy-Skills {
    Log "[deploy] 複製 skills → ~/.claude/skills/"
    New-Item -ItemType Directory -Force -Path $ClaudeSkillsDir | Out-Null
    Get-ChildItem -Path $SkillsSrc -Directory | ForEach-Object {
        $dest = Join-Path $ClaudeSkillsDir $_.Name
        if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
        Copy-Item -Recurse $_.FullName $dest
        Log "  · $($_.Name)"
    }
}

function Do-Install {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Error "❌ 需要 git"; exit 1 }
    if (-not (Get-Command $py -ErrorAction SilentlyContinue)) { Write-Error "❌ 需要 Python 3"; exit 1 }

    if (Test-Path (Join-Path $RuntimeDir ".git")) {
        Log "[install] $RuntimeDir 已存在，執行 upgrade..."
        Do-Upgrade; return
    }

    Log "[install] clone gendoc → $RuntimeDir"
    git clone $RepoUrl $RuntimeDir

    Deploy-Skills

    Log "[deploy] 註冊 SessionStart hook..."
    & $py $SettingsHook add $HookCmd

    Log ""
    Log "[install] 完成！重啟 Claude Code 讓技能生效。"
}

function Do-Uninstall {
    Log "[uninstall] 移除 hook..."
    if (Test-Path $SettingsHook) { & $py $SettingsHook remove }

    Log "[uninstall] 移除 copied skills..."
    if (Test-Path $SkillsSrc) {
        Get-ChildItem -Path $SkillsSrc -Directory | ForEach-Object {
            $dest = Join-Path $ClaudeSkillsDir $_.Name
            if (Test-Path $dest) { Remove-Item -Recurse -Force $dest; Log "  · 刪除 $($_.Name)" }
        }
    }

    Log "[uninstall] 刪除 $RuntimeDir..."
    if (Test-Path $RuntimeDir) { Remove-Item -Recurse -Force $RuntimeDir }
    Log "[uninstall] 完成。"
}

function Do-Upgrade {
    if (-not (Test-Path (Join-Path $RuntimeDir ".git"))) {
        Write-Error "[upgrade] 找不到 $RuntimeDir，請先執行 install。"; exit 1
    }
    Log "[upgrade] git pull..."
    git -C $RuntimeDir pull --ff-only
    Deploy-Skills
    Log "[upgrade] 完成。"
}

switch ($Command.ToLower()) {
    "install"   { Do-Install }
    "uninstall" { Do-Uninstall }
    "upgrade"   { Do-Upgrade }
    default {
        Write-Host "用法：.\setup.ps1 [install|uninstall|upgrade]"
        exit 1
    }
}
