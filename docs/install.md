---
layout: default
title: "Installation Guide — Typing Buddy"
description: "Step-by-step instructions and troubleshooting for installing Typing Buddy on Windows."
---

# Installation Guide

Follow these steps to set up Typing Buddy on your Windows PC.

[![Download for Windows](https://img.shields.io/badge/Download-Typing%20Buddy%20for%20Windows-blue?style=for-the-badge&logo=windows)](https://github.com/harshverse-svg/typing-buddy/releases/latest/download/typing-buddy.zip)

Looking for older releases? See the [All versions](#all-versions) table below.

---

## Easy Setup (Recommended)

### Step 0: Install Python (if you don't have it yet)
1. Download Python 3.10 or newer from [python.org/downloads](https://www.python.org/downloads/).
2. Run the installer. On the first screen, tick **Add python.exe to PATH**.
3. Click **Install Now**.
4. Open a **new** Command Prompt or PowerShell window and verify:
   ```cmd
   python --version
   ```

### Step 1: Download Typing Buddy
Download the latest zip package:  
**[Download for Windows](https://github.com/harshverse-svg/typing-buddy/releases/latest/download/typing-buddy.zip)**

### Step 2: Unblock the Zip (if prompted)
1. In File Explorer, go to your Downloads folder.
2. Right-click `typing-buddy.zip` and select **Properties**.
3. If an **Unblock** checkbox appears at the bottom, tick it and click **OK**.

### Step 3: Extract the Folder
1. Right-click `typing-buddy.zip` and choose **Extract All...**.
2. Click **Extract**.
3. Do **not** run `install.bat` from inside the compressed zip file. Always extract it first.

### Step 4: Run the Installer
1. Open the extracted folder.
2. Double-click **`install.bat`**.
3. The installer sets up an isolated environment and asks if you want Desktop, Start Menu, and Startup shortcuts. Answer `Y` or `N` to each prompt.

### Step 5: Launch Typing Buddy
1. Double-click the **Typing Buddy** shortcut on your Desktop, or search for **Typing Buddy** in the Windows Start menu.
2. Typing Buddy starts silently in the background.

### Step 6: Find the Tray Icon
1. Look at the Windows notification area in the bottom-right corner of your screen (near the clock).
2. If the green icon (🟢) is not visible, click the small up-arrow (`^`) to view hidden tray icons.
3. Right-click the icon to adjust word packs, toggle grammar checks, view statistics, or pause.

---

## For Developers

If you have Git and prefer the command line:

1. Make sure Git is installed on your computer ([git-scm.com/downloads](https://git-scm.com/downloads)).
2. Open **Command Prompt** (not PowerShell).
3. Run:

```cmd
git clone https://github.com/harshverse-svg/typing-buddy.git
cd typing-buddy
install.bat
```

> **Silent Installation:**  
> Run `install.bat /silent` to install with default settings non-interactively.

---

## Troubleshooting Installation

### `git is not recognized`
Git is not installed on your system. Either download Git from [git-scm.com/downloads](https://git-scm.com/downloads) or use the easy zip method above.

### `python is not recognized`
Windows cannot find Python on your PATH.
1. Re-run the Python installer from [python.org/downloads](https://www.python.org/downloads/).
2. Select **Modify**, make sure **Add python.exe to PATH** is checked, and complete setup.
3. Close and reopen your terminal window.
4. You can also try running `py --version` instead.

### `install.bat is not recognized` / `cd typing-buddy` fails
The zip file was not extracted, or your terminal is in the wrong folder. Open File Explorer, navigate to the extracted folder, and double-click `install.bat`.

### `Cannot find path ... does not exist` on Get-FileHash
PowerShell likely opened in `C:\Windows\System32` instead of your Downloads folder. Run:
```powershell
cd $HOME\Downloads
Get-FileHash .\typing-buddy.zip -Algorithm SHA256
```

### "Windows protected your PC" (SmartScreen)
SmartScreen displays this message for new open-source software that lacks an expensive code-signing certificate.
1. Click **More info**.
2. Click **Run anyway**.

### "Smart App Control blocked this app"
Smart App Control (SAC) on Windows 11 blocks untrusted or unsigned scripts and executables.
1. Right-click `typing-buddy.zip` $\rightarrow$ **Properties** $\rightarrow$ check **Unblock** $\rightarrow$ click **OK**.
2. Delete the previously extracted folder and extract the zip again.
3. If still blocked: Smart App Control provides no per-app "Run anyway" button. The only workaround is turning SAC off in **Windows Security** $\rightarrow$ **App & browser control** $\rightarrow$ **Smart App Control settings** $\rightarrow$ **Off**.
4. **Warning:** Turning Smart App Control off is **permanent**; Windows does not allow re-enabling it without a fresh reinstall or PC reset. Turning it off also lowers your system protection. Only do this on your personal PC if you understand the risks. The Typing Buddy project is free open source and is not code-signed yet.

### Antivirus warning
Typing Buddy monitors keystrokes locally using the Windows Win32 API (`pynput`) to display real-time completions. Some generic antivirus heuristics flag any low-level keyboard hook as suspicious. Typing Buddy contains zero network code, never saves sentences to disk, and runs 100% offline. You can review our [Privacy Policy](https://github.com/harshverse-svg/typing-buddy/blob/main/PRIVACY.md) and run our offline AST code audit script:
```cmd
python tools/check_no_network.py
```

### No tray icon after install
1. Click the small up-arrow (`^`) in the notification area to check hidden icons.
2. Open Windows Task Manager (Ctrl + Shift + Esc) and check if `pythonw.exe` is running.
3. To view any startup error messages directly, open Command Prompt in the extracted folder and run:
   ```cmd
   .venv\Scripts\python -m typing_buddy
   ```

---

## All Versions

| Version | Date | Download | Notes |
|---|---|---|---|
| **v1.0.2** (Latest) | 2026-10-30 | [typing-buddy.zip](https://github.com/harshverse-svg/typing-buddy/releases/latest/download/typing-buddy.zip) ([versioned](https://github.com/harshverse-svg/typing-buddy/releases/download/v1.0.2/typing-buddy-v1.0.2.zip)) | Permanent direct link, release verification workflow, detailed install guide |
| **v1.0.1** | 2026-10-30 | [typing-buddy-v1.0.1.zip](https://github.com/harshverse-svg/typing-buddy/releases/download/v1.0.1/typing-buddy-v1.0.1.zip) | CLI argument unescape fix, removed root duplicate files |
| **v1.0.0** | 2026-10-30 | [typing-buddy-v1.0.0.zip](https://github.com/harshverse-svg/typing-buddy/releases/download/v1.0.0/typing-buddy-v1.0.0.zip) | Initial public release (known CLI bug in `--version`/`--help`, fixed in v1.0.1) |

> **Note:** Older versions may have known bugs. Use **Latest** unless you need a specific version. Note that v1.0.0 has a known CLI bug fixed in v1.0.1.
