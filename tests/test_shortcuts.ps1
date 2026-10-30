$ErrorActionPreference = "Stop"
$tempDir = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "tb_test_" + [System.Guid]::NewGuid().ToString())
try {
    & "$PSScriptRoot\..\tools\create_shortcuts.ps1" -Desktop -StartMenu -Startup -OutputRoot $tempDir
    $wsh = New-Object -ComObject WScript.Shell
    $desktopLnk = Join-Path $tempDir "Desktop\Typing Buddy.lnk"
    if (-not (Test-Path $desktopLnk)) { throw "Desktop lnk missing" }
    
    $sc = $wsh.CreateShortcut($desktopLnk)
    Write-Host "TargetPath:" $sc.TargetPath
    Write-Host "Arguments:" $sc.Arguments
    Write-Host "WorkingDirectory:" $sc.WorkingDirectory
    Write-Host "IconLocation:" $sc.IconLocation
    Write-Host "WindowStyle:" $sc.WindowStyle

    if ($sc.Arguments -ne "-m typing_buddy") { throw "Wrong arguments" }
    if ($sc.WindowStyle -ne 7) { throw "Wrong windowstyle" }

    # Test space in path
    $tempSpace = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "tb test folder " + [System.Guid]::NewGuid().ToString())
    try {
        & "$PSScriptRoot\..\tools\create_shortcuts.ps1" -Desktop -OutputRoot $tempSpace
        $spaceLnk = Join-Path $tempSpace "Desktop\Typing Buddy.lnk"
        if (-not (Test-Path $spaceLnk)) { throw "Desktop lnk in spaced path missing" }
    } finally {
        Remove-Item -Recurse -Force $tempSpace -ErrorAction SilentlyContinue
    }

    # Test -Remove
    & "$PSScriptRoot\..\tools\create_shortcuts.ps1" -Remove -OutputRoot $tempDir
    if (Test-Path $desktopLnk) { throw "Remove failed" }

    Write-Host "SHORTCUT SCRIPT VERIFIED SUCCESSFULLY!"
} finally {
    Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
}
