$ErrorActionPreference = "Stop"
$tempRepo = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "tb_install_test_" + [System.Guid]::NewGuid().ToString())
try {
    Write-Host "Staging temporary repo copy at: $tempRepo"
    New-Item -ItemType Directory -Path $tempRepo | Out-Null
    Copy-Item -Recurse -Path "$PSScriptRoot\..\typing_buddy" -Destination "$tempRepo\typing_buddy"
    Copy-Item -Recurse -Path "$PSScriptRoot\..\tools" -Destination "$tempRepo\tools"
    Copy-Item -Recurse -Path "$PSScriptRoot\..\assets" -Destination "$tempRepo\assets"
    Copy-Item -Recurse -Path "$PSScriptRoot\..\wordpacks" -Destination "$tempRepo\wordpacks"
    Copy-Item -Path "$PSScriptRoot\..\install.bat", "$PSScriptRoot\..\pyproject.toml", "$PSScriptRoot\..\README.md", "$PSScriptRoot\..\settings.example.json", "$PSScriptRoot\..\snippets.example.json", "$PSScriptRoot\..\personal_words.example.txt" -Destination $tempRepo
    
    Write-Host "Running install.bat /silent in temp copy..."
    $proc = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "install.bat", "/silent", "/noshortcuts") -WorkingDirectory $tempRepo -Wait -PassThru -NoNewWindow
    Write-Host "Install.bat exit code: $($proc.ExitCode)"
    if ($proc.ExitCode -ne 0) { throw "install.bat failed with code $($proc.ExitCode)" }
    Write-Host "INSTALL.BAT /SILENT TEST PASSED WITHOUT HANGING!"
} finally {
    Remove-Item -Recurse -Force $tempRepo -ErrorAction SilentlyContinue
}
