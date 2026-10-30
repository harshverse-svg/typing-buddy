# Typing Buddy v1.0.0 — Initial Public Release

> **Notice:** Superseded by v1.0.1 - please download the [latest release](https://github.com/harshverse-svg/typing-buddy/releases/latest).

**Typing Buddy** is a fast, offline, privacy-first typing assistant, autocomplete, and grammar checker for Windows.

---

### Key Features

- **System-Wide Word Autocomplete:** Instant completions as you type in Notepad, browsers, Word, Slack, and code editors powered by trie indexing and unigram/bigram frequency ranking.
- **Fuzzy Typo Corrections:** Intelligent Damerau-Levenshtein distance matching with QWERTY keyboard layout adjacency weighting.
- **Offline Grammar Checker:** Integrated sentence-level grammar linting powered by the offline Harper engine (`harper-py`).
- **Hinglish Language Pack:** Bundled vocabulary pack for colloquial Romanized Hindi communication (`kya`, `haan`, `theek`, `accha`, `yaar`).
- **Desktop & Start Integration:** Dedicated desktop shortcut, Windows Start menu search (`Typing Buddy.lnk`), system tray menu with active/paused status colors, and single-instance launch guard.
- **Password Safety:** Automatically pauses when the text cursor enters a Windows UI Automation (UIA) password field or blocked application.

---

### Installation in 3 Steps

1. Download and extract **`typing-buddy-v1.0.0.zip`** from this release.
2. Double-click **`install.bat`** (requires Python 3.10+ on PATH; download from [python.org](https://www.python.org/downloads/)).
3. Launch Typing Buddy from your Desktop icon or Start menu!

---

### Privacy & Security Guarantee

- **100% Offline:** Contains zero network imports, zero sockets, and zero telemetry (verified via automated AST code inspection).
- **RAM-Only Transient Buffer:** Sentence context is tracked in volatile memory (capped at 300 characters) and wiped immediately upon mouse clicks, arrow key navigation, or window switching.
- **No Keystroke Logging:** Nothing you type is ever written to disk or sent over any network.

---

### Known Limitations

- **Windows Only:** Built for Microsoft Windows 10 and 11 (64-bit).
- **Requires Python:** Requires Python 3.10 or newer with "Add Python to PATH" enabled.
- **Administrator Privileges:** Due to Windows UIPI security boundaries, applications running as Administrator require Typing Buddy to also be run as Administrator.
- **Specialized Applications:** Fullscreen DirectX games, remote desktop sessions, and custom input fields without standard caret reporting may not display floating pills.

---

### Verification

To verify the integrity and authenticity of your download, compute its SHA-256 checksum in PowerShell:

```powershell
Get-FileHash typing-buddy-v1.0.0.zip -Algorithm SHA256
```

Compare the calculated hash with the value published in `SHA256SUMS.txt`.

