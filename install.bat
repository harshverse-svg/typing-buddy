@echo off
setlocal enabledelayedexpansion

:: Check command-line switches
set SILENT_MODE=0
set NO_SHORTCUTS=0

for %%A in (%*) do (
    if /i "%%A"=="/silent" set SILENT_MODE=1
    if /i "%%A"=="-silent" set SILENT_MODE=1
    if /i "%%A"=="--silent" set SILENT_MODE=1
    if /i "%%A"=="/noshortcuts" set NO_SHORTCUTS=1
    if /i "%%A"=="-noshortcuts" set NO_SHORTCUTS=1
    if /i "%%A"=="--noshortcuts" set NO_SHORTCUTS=1
)

echo =======================================================
echo          Typing Buddy - Windows Setup Script
echo =======================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10 or newer from https://www.python.org/
    echo Make sure to check the box "Add Python to PATH" during installation.
    echo.
    if !SILENT_MODE! equ 0 pause
    exit /b 1
)

:: Check Python version (>= 3.10)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10 or newer is required.
    echo Found version:
    python --version
    echo Please upgrade Python from https://www.python.org/
    echo.
    if !SILENT_MODE! equ 0 pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

:: 2. Create virtual environment
if not exist ".venv" (
    echo [*] Creating virtual environment in .venv ...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        if !SILENT_MODE! equ 0 pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment .venv already exists.
)

:: 3. Offline Grammar support choice
set PKG_SPEC=.[grammar]
if !SILENT_MODE! equ 0 (
    echo.
    echo Would you like to enable offline grammar suggestions?
    echo [Powered by Harper, ~50MB download, runs 100%% offline in RAM]
    set /p INSTALL_GRAMMAR="Install offline grammar support? [Y/n]: "
    if /i "!INSTALL_GRAMMAR!"=="N" (
        set PKG_SPEC=.
        echo [*] Installing basic typing suggestions without grammar...
    ) else (
        echo [*] Installing typing suggestions with offline grammar support...
    )
) else (
    echo [*] Silent mode: installing with offline grammar support...
)

echo.
echo [*] Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet

echo [*] Installing Typing Buddy dependencies...
.venv\Scripts\python.exe -m pip install -e "%PKG_SPEC%"
if %errorlevel% neq 0 (
    echo [ERROR] Installation failed. Please check the error messages above.
    if !SILENT_MODE! equ 0 pause
    exit /b 1
)

:: 4. Shortcuts creation
if !NO_SHORTCUTS! equ 0 (
    set CREATE_DESKTOP=Y
    set CREATE_STARTMENU=Y
    set CREATE_STARTUP=N

    if !SILENT_MODE! equ 0 (
        echo.
        echo -------------------------------------------------------
        echo Shortcuts and Auto-Start Configuration:
        echo -------------------------------------------------------
        set /p ASK_DESKTOP="Create a desktop icon? [Y/n]: "
        if /i "!ASK_DESKTOP!"=="N" set CREATE_DESKTOP=N

        set /p ASK_START="Add Typing Buddy to the Start menu so you can search for it? [Y/n]: "
        if /i "!ASK_START!"=="N" set CREATE_STARTMENU=N

        set /p ASK_STARTUP="Start Typing Buddy automatically when Windows starts? [y/N]: "
        if /i "!ASK_STARTUP!"=="Y" set CREATE_STARTUP=Y
    )

    set PS_FLAGS=
    if /i "!CREATE_DESKTOP!"=="Y" set PS_FLAGS=!PS_FLAGS! -Desktop
    if /i "!CREATE_STARTMENU!"=="Y" set PS_FLAGS=!PS_FLAGS! -StartMenu
    if /i "!CREATE_STARTUP!"=="Y" set PS_FLAGS=!PS_FLAGS! -Startup

    if defined PS_FLAGS (
        echo.
        echo [*] Creating requested shortcuts...
        powershell -ExecutionPolicy Bypass -File tools\create_shortcuts.ps1 !PS_FLAGS!
    )
)

echo.
echo =======================================================
echo [SUCCESS] Typing Buddy has been installed!
echo =======================================================
echo.
echo Where to find Typing Buddy:
echo   - Desktop: Double-click the "Typing Buddy" desktop icon
echo   - Start Menu: Press Windows Key and search "Typing Buddy"
echo   - System Tray: Look for the blue and green icon in the system tray
echo                  (click the up arrow if you do not see it).
echo.
echo Your user settings and word packs are stored at:
echo   %%APPDATA%%\typing-buddy\settings.json
echo.

if !SILENT_MODE! equ 0 (
    set /p LAUNCH_NOW="Launch Typing Buddy right now? [Y/n]: "
    if /i not "!LAUNCH_NOW!"=="N" (
        start "" ".venv\Scripts\pythonw.exe" -m typing_buddy
        echo [*] Typing Buddy launched in background!
    )
    pause
)
