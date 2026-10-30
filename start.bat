@echo off
setlocal

:: Prefer virtual environment pythonw
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" -m typing_buddy %*
    exit /b 0
)

:: Fallback to system pythonw
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw -m typing_buddy %*
    exit /b 0
)

echo [ERROR] Neither .venv nor system pythonw found.
echo Please run install.bat first to set up Typing Buddy.
pause
exit /b 1
