<#
.SYNOPSIS
    Create or remove Windows shell shortcuts for Typing Buddy.
.DESCRIPTION
    Creates shortcuts pointing directly to .venv\Scripts\pythonw.exe with arguments -m typing_buddy,
    with custom icon, description, and working directory set to project root.
.PARAMETER Desktop
    Create shortcut on the Desktop.
.PARAMETER StartMenu
    Create shortcut in Start Menu Programs.
.PARAMETER Startup
    Create shortcut in Windows Startup folder (auto-start).
.PARAMETER Remove
    Remove existing Typing Buddy shortcuts (and legacy Typing Suggest shortcuts).
.PARAMETER OutputRoot
    Custom root folder for testing/redirection instead of real shell folders.
#>
[CmdletBinding()]
param(
    [switch]$Desktop,
    [switch]$StartMenu,
    [switch]$Startup,
    [switch]$Remove,
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"

# Resolve project root and assets
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"

if (-not (Test-Path $VenvPythonw)) {
    $sysPythonw = Get-Command "pythonw.exe" -ErrorAction SilentlyContinue
    if ($sysPythonw) {
        $PythonwPath = $sysPythonw.Source
    } else {
        $PythonwPath = "pythonw.exe"
    }
} else {
    $PythonwPath = $VenvPythonw
}

$IconPath = Join-Path $ProjectRoot "assets\typing-buddy.ico"
$Arguments = "-m typing_buddy"
$Description = "Typing Buddy - offline typing assistant"

# Determine target directories
if ($OutputRoot -ne "") {
    $DesktopDir = Join-Path $OutputRoot "Desktop"
    $ProgramsDir = Join-Path $OutputRoot "Programs"
    $StartupDir = Join-Path $OutputRoot "Startup"
    New-Item -ItemType Directory -Force -Path $DesktopDir, $ProgramsDir, $StartupDir | Out-Null
} else {
    $DesktopDir = [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)
    $ProgramsDir = [Environment]::GetFolderPath([Environment+SpecialFolder]::Programs)
    $StartupDir = [Environment]::GetFolderPath([Environment+SpecialFolder]::Startup)
}

$wsh = New-Object -ComObject WScript.Shell

function Remove-ShortcutIfExists([string]$folder, [string]$name) {
    if ([string]::IsNullOrWhiteSpace($folder)) { return }
    $lnk = Join-Path $folder "$name.lnk"
    if (Test-Path $lnk) {
        Remove-Item -Path $lnk -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Removed: $lnk"
    }
}

if ($Remove) {
    Write-Host "[*] Removing shortcuts..."
    foreach ($dir in @($DesktopDir, $ProgramsDir, $StartupDir)) {
        Remove-ShortcutIfExists $dir "Typing Buddy"
        Remove-ShortcutIfExists $dir "Typing Suggest"
        Remove-ShortcutIfExists $dir "Windows Typing Predictor"
    }
    Write-Host "[OK] Shortcut removal completed."
    exit 0
}

function Create-Lnk([string]$targetDir, [string]$shortcutName) {
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
    }
    $lnkPath = Join-Path $targetDir "$shortcutName.lnk"
    $shortcut = $wsh.CreateShortcut($lnkPath)
    $shortcut.TargetPath = $PythonwPath
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = $ProjectRoot
    $shortcut.Description = $Description
    $shortcut.WindowStyle = 7  # Minimized (avoids flash)
    if (Test-Path $IconPath) {
        $shortcut.IconLocation = "$IconPath,0"
    }
    $shortcut.Save()
    Write-Host "[OK] Created shortcut: $lnkPath"
}

if ($Desktop) {
    Create-Lnk $DesktopDir "Typing Buddy"
}

if ($StartMenu) {
    Create-Lnk $ProgramsDir "Typing Buddy"
}

if ($Startup) {
    Create-Lnk $StartupDir "Typing Buddy"
}
