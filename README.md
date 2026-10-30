<p align="center">
  <img src="assets/banner.png" alt="Typing Buddy Banner" width="100%">
</p>

# <img src="assets/logo.svg" width="36" height="36" align="center" alt="Typing Buddy Icon" /> Typing Buddy

> **The offline, privacy-first typing assistant and autocomplete for Windows.**

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D6.svg?logo=windows&logoColor=white" alt="Windows 10 | 11">
  <img src="https://img.shields.io/badge/network-100%25%20Offline-success.svg" alt="100% Offline">
  <a href="https://github.com/harshverse-svg/typing-buddy/actions/workflows/ci.yml"><img src="https://github.com/harshverse-svg/typing-buddy/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="https://github.com/harshverse-svg/typing-buddy/releases/latest"><img src="https://img.shields.io/github/v/release/harshverse-svg/typing-buddy?color=blue" alt="Latest Release"></a>
</p>

---

## What is Typing Buddy?

**Typing Buddy** is a lightweight, open source **offline typing assistant** for **Windows** built with **Python**. It provides instant **word suggestions**, intelligent **autocomplete**, fuzzy **typo correction**, and real-time **grammar checker** suggestions as you type in any application. Engineered with a **privacy-first** architecture, Typing Buddy requires **no cloud** connection and contains **no telemetry**. It includes native **Hinglish support** for multilingual dialogue, runs with near-zero idle CPU, and operates strictly in local memory.

---

## How It Looks

<!-- Real recording placeholder: capture with ScreenToGif and save to assets/demo.gif (see assets/RECORDING_GUIDE.md) -->
<p align="center">
  <img src="assets/how-it-works.svg" alt="Typing Buddy Architecture Diagram" width="850">
</p>

```
  she go|
  +------------------------------------------------------------------+
  | [1] ✎ goes               [2] going            [3] good           |
  |     Subject-verb agreement                                       |
  +------------------------------------------------------------------+
```

As you type in Notepad, Word, Slack, or your browser, a clean floating pill appears right next to your text cursor. Press `F2`, `F3`, `F4` (or `Tab`) to accept suggestions instantly without moving your hands away from the keyboard.

---

## Why Typing Buddy?

- 🔒 **100% Offline with Zero Network Code:** Contains no HTTP client, no analytics, and no sockets. Verified by automated AST code analysis.
- ⚡ **RAM-Only Volatile Tracking:** Sentence tracking stays in RAM (max 300 characters) and is wiped on mouse clicks, arrow navigation, or focus switch. Never logged or saved to disk.
- 🛡️ **Password Safety:** Automatically pauses whenever your cursor enters a password field or sensitive window.
- 💬 **Hinglish Word Pack:** Romanized Hindi expressions (`kya`, `theek`, `accha`, `yaar`) are recognized without false typo or grammar flags.
- 🪶 **Ultra Lightweight:** Idle CPU is 0.00%. Suggestions compute in 0.03 ms.

---

## Features

| Feature | Description |
|---|---|
| **Intelligent Word Completions** | Trie-indexed dictionary ranking powered by unigram and bigram frequency. |
| **Fuzzy Typo Correction** | Damerau-Levenshtein distance with QWERTY keyboard adjacency weighting. |
| **Offline Grammar Linter** | Powered by Harper; catches subject-verb agreement and word choice errors. |
| **Text Shortcuts / Snippets** | Instant abbreviation expansion with dynamic dates, time, and clipboard text. |
| **Desktop & Start Integration** | Desktop shortcut, Windows Start search, and single-instance launch guard. |
| **Auto-Pause & Blocklist** | Automatically detects password elements; user-customizable blocked apps. |

---

## Installation

Choose either method below:

### Method 1: Easy Installer (Recommended)
1. Download the latest **`typing-buddy-v1.0.0.zip`** from [Releases](https://github.com/harshverse-svg/typing-buddy/releases/latest).
2. Extract the ZIP folder to your preferred location.
3. Double-click **`install.bat`**.
   - Verifies Python $\ge$ 3.10 (download from [python.org](https://www.python.org/) with "Add Python to PATH" checked).
   - Sets up an isolated `.venv` environment and installs dependencies.
   - Prompts whether to create Desktop/Start menu icons and enable auto-start.
4. Launch Typing Buddy anytime from your Desktop icon or Start menu!

### Method 2: From Source (Developers)
```cmd
git clone https://github.com/harshverse-svg/typing-buddy.git
cd typing-buddy

:: Run installer
install.bat
```

> **Silent Installation (for CI / scripting):**  
> Run `install.bat /silent` to install with default settings non-interactively.

---

## Open It Like a Normal App

After running `install.bat`, you never need to touch the project folder again:

1. **Desktop Icon:** Double-click the **Typing Buddy** shortcut on your Desktop.
2. **Start Menu Search:** Press the `Windows Key`, type `Typing Buddy`, and press Enter.
3. **Pin to Taskbar:** Right-click the Typing Buddy icon in your Start menu and select **Pin to taskbar** (Windows requires users to pin items manually).
4. **System Tray:** Look for the Typing Buddy icon (🟢) in your notification area (bottom-right next to the clock). If hidden, click the small up-arrow (`^`) to see it.
5. **How to Quit:** Right-click the tray icon and select **Quit**.

---

## Quick Start: 5 Things to Try

Open **Notepad** and test these 5 features:

1. **Word Completion:** Type `diff` $\rightarrow$ Suggestion pill displays `different`, `difficult`. Press `F2` to pick.
2. **Tab Acceptance:** Type `exam` $\rightarrow$ Press `Tab` $\rightarrow$ Inserts `example `.
3. **Fuzzy Typo Fix:** Type `recie ` (with space) $\rightarrow$ Suggestion pill offers `receive`. Press `Tab` to fix.
4. **Grammar Correction:** Type `she go` $\rightarrow$ Suggestion pill displays `✎ goes` with `Subject-verb agreement`.
5. **Pause Hotkey:** Press the `Pause/Break` key $\rightarrow$ Tray icon turns grey (🔘) and suggestions pause. Press again to resume.

---

## Tray States & Menu

<p align="center">
  <img src="assets/tray-states.png" alt="Typing Buddy Tray States" width="700">
</p>

Right-click the Typing Buddy icon in your notification area to quickly toggle word packs, enable or disable grammar suggestions, open your settings, or pause the assistant:

<p align="center">
  <img src="assets/screenshot-tray.png" alt="Typing Buddy System Tray Menu on Windows 11" width="480">
</p>

- 🟢 **Active:** Ready and suggesting words.
- 🟠 **Auto-Paused:** Focus is inside a password field or blocked application.
- 🔘 **Paused:** Manually paused via Pause hotkey or tray menu.

---

## Word Packs

Switch word packs on the fly from the System Tray menu or `%APPDATA%\typing-buddy\settings.json`:

| Pack | Words | RAM Footprint | Notes |
|---|---|---|---|
| **`en-basic`** | 5,000 | ~120 MB | Enabled by default; covers 95% of daily English typing. |
| **`en-large`** | 150,000 | ~330 MB | Optional; full dictionary for academic & technical writing. |
| **`hinglish`** | 320+ | < 1 MB | Common Roman-script Hindi dialogue (`kya`, `haan`, `theek`, `accha`). |

To list packs from terminal:
```cmd
python -m typing_buddy packs list
```

---

## Configuration (`settings.json`)

Your settings reside safely in `%APPDATA%\typing-buddy\settings.json`:

| Option | Type | Default | Description |
|---|---|---|---|
| `pick_keys` | `list[str]` | `["f2", "f3", "f4"]` | Keys to select suggestions (supports `"1"`, `"2"`, `"3"`). |
| `enable_tab_pick` | `bool` | `true` | Allows pressing `Tab` to accept first suggestion. |
| `pause_key` | `str` | `"pause"` | Global hotkey to toggle pause (`"pause"`, `"f12"`). |
| `word_packs` | `list[str]` | `["en-basic"]` | Enabled word pack IDs. |
| `grammar_enabled` | `bool` | `true` | Enables offline grammar feedback. |
| `grammar_show_reason` | `bool` | `true` | Shows grammatical explanation subtitle under pills. |
| `blocked_apps` | `list[str]` | `["keepass.exe", ...]` | Apps where Typing Buddy automatically sleeps. |

---

## Privacy & Security

Typing Buddy is built on a **zero-trust local privacy architecture**:

- **No Network Imports:** You can verify with our automated Abstract Syntax Tree scanner:
  ```cmd
  python tools/check_no_network.py
  ```
- **Volatile Text Buffer:** Sentence context is tracked in RAM only (`TextTracker`, 300 char cap). It is wiped on clicks, cursor navigation, window changes, and pauses.
- **Is this a Keylogger?**  
  Keyloggers secretly record and save your sentences to disk or transmit them to cloud servers. Typing Buddy does neither: it runs 100% offline, stores zero sentence logs, only counts individual word frequencies for ranking, and is fully open source. Read [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).

---

## Troubleshooting

- **No tray icon visible?**  
  Click the small up-arrow (`^`) in the Windows taskbar overflow area.
- **Icon looks blank or cached?**  
  Windows occasionally caches shortcut icons. Restart Windows Explorer in Task Manager, or run:
  ```cmd
  ie4uinit.exe -show
  ```
- **Suggestions not appearing in an app?**  
  If the application is running with elevated Administrator privileges, Typing Buddy must also be run as Administrator due to Windows security isolation (UIPI).
- **Antivirus false positive?**  
  Because Typing Buddy monitors keystrokes via low-level Windows hooks (`pynput`), generic heuristic scanners may flag it. Running from source in Python `.venv` avoids binary false positives.
- **View diagnostic logs:**  
  Open `%APPDATA%\typing-buddy\predictor.log` in Notepad.

---

## Frequently Asked Questions (FAQ)

**Q: Does Typing Buddy send my typing anywhere?**  
A: No. Typing Buddy contains zero network code. It never connects to the internet or sends telemetry.

**Q: Does it work completely offline?**  
A: Yes. All dictionaries, fuzzy matching, and grammar rules run locally on your CPU.

**Q: Does Typing Buddy work on macOS or Linux?**  
A: No. Typing Buddy is specifically designed for the Windows Win32 / UIA desktop subsystem.

**Q: How do I turn off Start with Windows?**  
A: Right-click the tray icon and uncheck "Start with Windows", or run `uninstall.bat`.

**Q: How do I uninstall?**  
A: Run `uninstall.bat`. It removes all shortcuts and registry entries, and asks if you want to delete the user data directory.

---

## Contributing & License

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md).

Typing Buddy is licensed under the [MIT License](LICENSE).  
Third-party component notices and licenses are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
