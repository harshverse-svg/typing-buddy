@echo off
setlocal

echo =======================================================
echo          Typing Buddy - Uninstall Script
echo =======================================================
echo.

:: 1. Remove Desktop, Start Menu, and Startup shortcuts
echo [*] Removing shortcuts (Desktop, Start Menu, Startup)...
if exist "tools\create_shortcuts.ps1" (
    powershell -ExecutionPolicy Bypass -File tools\create_shortcuts.ps1 -Remove
)

:: 2. Remove any old or new Windows startup registry entries
echo [*] Cleaning Windows startup registry entries...
for %%K in ("Typing Buddy" "Typing Suggest" "TypingSuggest" "WindowsTypingPredictor") do (
    reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v %%K >nul 2>nul
    if %errorlevel% equ 0 (
        reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v %%K /f >nul 2>nul
        echo [OK] Removed registry entry: %%K
    )
)

:: 3. Optional deletion of user data directory
set DATA_DIR=%APPDATA%\typing-buddy
set OLD_DATA_DIR=%APPDATA%\typing-suggest

if exist "%DATA_DIR%" (
    echo.
    echo Your user data, custom settings, snippets, and learned words are saved at:
    echo     %DATA_DIR%
    echo.
    set /p DEL_DATA="Do you want to permanently delete this user data folder? [y/N]: "
    if /i "!DEL_DATA!"=="Y" (
        rmdir /s /q "%DATA_DIR%"
        echo [OK] Deleted %DATA_DIR%
    ) else (
        echo [INFO] Kept user data in %DATA_DIR%
    )
)

if exist "%OLD_DATA_DIR%" (
    echo.
    echo A legacy data folder was also found at:
    echo     %OLD_DATA_DIR%
    set /p DEL_OLD="Do you want to delete the legacy data folder? [y/N]: "
    if /i "!DEL_OLD!"=="Y" (
        rmdir /s /q "%OLD_DATA_DIR%"
        echo [OK] Deleted %OLD_DATA_DIR%
    )
)

echo.
echo =======================================================
echo [SUCCESS] Uninstall complete.
echo You may now safely delete this project directory.
echo =======================================================
echo.
pause
