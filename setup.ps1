# gendoc setup.ps1 — Windows native (PowerShell) version
# Usage:
#   .\setup.ps1             # install
#   .\setup.ps1 -Uninstall  # remove hook
#   .\setup.ps1 -Quiet      # silent mode

param(
    [switch]$Uninstall,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SettingsHook = Join-Path $ScriptDir "bin\gendoc-settings-hook.py"
$HookPy       = Join-Path $ScriptDir "bin\gendoc-session-update.py"
$InstallPy    = Join-Path $ScriptDir "install.py"

function Log($msg) { if (-not $Quiet) { Write-Host $msg } }

# Dependency check
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "❌ 需要 git（請安裝 Git for Windows）"; exit 1
}
if (-not (Get-Command python3 -ErrorAction SilentlyContinue) -and
    -not (Get-Command python  -ErrorAction SilentlyContinue)) {
    Write-Error "❌ 需要 Python 3"; exit 1
}
$py = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }

if ($Uninstall) {
    Log "[setup] 解除安裝..."
    & $py $SettingsHook remove
    Log "[setup] hook 已移除。skills 保留，如需清除請手動刪除 $env:USERPROFILE\.claude\skills\gendoc*"
    exit 0
}

Log "[setup] 安裝 gendoc (Windows)..."

# Deploy skills
$quietFlag = if ($Quiet) { "--quiet" } else { "" }
& $py $InstallPy $quietFlag

# Register SessionStart hook (Python version for Windows)
$hookCmd = "$py `"$HookPy`""
& $py $SettingsHook add $hookCmd

Log ""
Log "[setup] 完成！"
Log "  · 下次開啟 Claude Code 時，gendoc 會自動檢查更新（每小時一次）"
Log "  · 手動更新：cd $ScriptDir && git pull && $py install.py"
Log "  · 解除安裝：.\setup.ps1 -Uninstall"
