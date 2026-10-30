# Privacy Policy & Architecture

**Typing Buddy is 100% offline and stores zero keystroke logs.**

We designed Typing Buddy from day one to operate strictly on your personal computer without internet connectivity, analytics, or surveillance capabilities.

---

## The Zero-Network Guarantee

The application's own code contains **no network code**:
- No HTTP or HTTPS requests
- No telemetry, usage statistics, or analytics pings
- No automatic updates or background downloads
- No socket connections or remote synchronization

You can independently verify this at any time by running our static Abstract Syntax Tree (AST) code audit tool from the repository root:

```cmd
python tools/check_no_network.py
```

> **Note on Verification Scope:**  
> The AST checker verifies that the `typing_buddy` application package contains no imports or invocations of standard or low-level networking libraries (`socket`, `urllib`, `http`, `requests`, `httpx`, `asyncio` network helpers, `os.system`, `subprocess`, `wininet`, `winhttp`, etc.). Third-party binary wheels and dependencies are not scanned by this AST tool. The entire project is free open-source software—we encourage you to read the source code.

---

## What Is Stored Locally on Your Computer

All user configuration, custom vocabulary, and personalized ranking data are stored locally in your Windows user profile at `%APPDATA%\typing-buddy\` (or the custom path specified by `--data-dir` or `TYPING_BUDDY_DATA_DIR`):

| File | What It Stores | Fields & Internal Structure | Why It Exists |
|---|---|---|---|
| `settings.json` | Application configuration | JSON object with configuration keys: `word_packs`, `pick_keys`, `new_word_mode`, `blocked_apps`, `popup_font_size`, `grammar_enabled`, etc. | Persists user preferences and hotkey configurations across sessions |
| `snippets.json` | Text expansion shortcuts | JSON object mapping trigger abbreviations to expansion strings (e.g., `{"btw": "by the way"}`) | Expands text shortcuts into predefined templates |
| `personal_words.txt` | Custom vocabulary words | Plain text file with one word per line: `word\tfrequency` (tab-separated) | Stores words you manually add or approve from the review window |
| `ignore_words.txt` | Suppressed words | Plain text file with one word per line | Permanently excludes deleted words from suggestion lists |
| `user_data.json` | Vocabulary usage and word-pair frequencies | JSON object containing two ranking dictionaries:<br>• `uni`: `{word: count}` (frequency of individual known words you type)<br>• `bi`: `{prev_word: {next_word: count}}` (word pairs: frequency of which known word followed which) | Adapts autocomplete rankings and next-word predictions to your personal writing style. **Note:** Word pairs are stored **only** when both words are already known words in your active dictionaries. |
| `added_words.json` | Review queue of discovered words | JSON array of objects: `[{"word": str, "date": str}, ...]` | Holds newly typed unknown words awaiting your explicit review and approval in the review window |
| `stats.json` | Productivity and usage metrics | JSON object with aggregate counters (`keystrokes_saved`, `suggestions_picked`, `corrections_picked`) grouped by `today`, `daily` (retained for up to 30 days), and `total` | Displays summary charts in the Statistics window |
| `predictor.log` | Diagnostic status messages | Rotating log entries (up to 3 backups, 1 MB each): timestamps, log levels, thread names, component events (e.g., startup, pack reload, sensitive state transitions) | Troubleshooting and technical diagnostics. Never logs typed sentences. |
| `.migrated` | Legacy migration status marker | Plain text flag (`migrated=true`) | Prevents repeated legacy data migrations from previous application folder layouts |

### What Is NEVER Stored or Logged
- **No typed sentences or phrases:** Full sentences or paragraphs are never written to disk or recorded in logs.
- **No raw key streams:** Raw keystrokes and scan codes are never journaled.
- **No clipboard history:** Clipboard contents are never logged or stored.
- **No password inputs (when detected):** When a password field is detected by Windows UI Automation or Win32 style checks, suggestion buffers are immediately flushed and autocomplete pauses.
- **No unknown words in word pairs:** Word-pair associations (`bi` in `user_data.json`) are recorded **only** when both words are already known words in your active word packs or personal word list. An unknown word is never saved as a key or value in word pairs.
- **No pending counters on disk:** Transient frequency counts for unknown words are held in volatile RAM only and are never saved to disk. Only words that reach the configured threshold enter the review queue (`added_words.json`).

---

## Important Safety Note for Sensitive Inputs

If you type a secret (such as a password) outside a field Typing Buddy detects, a word-like secret could be counted and, in auto-add mode, saved in `personal_words.txt`. Use the Pause key or the blocked-apps list for sensitive places.

By default, Typing Buddy uses `new_word_mode: "review"`, meaning that newly encountered words are placed into a review queue and **never** added to your personal word list without your explicit approval.

---

## How In-Memory Grammar Tracking Works

When grammar suggestions are enabled:
1. An in-memory text buffer (`TextTracker`) maintains a rolling window of recently typed characters within the active sentence (capped at 300 characters maximum).
2. This buffer exists **only in volatile RAM**. It is never written to a file, never stored in a database, and never emitted to logs.
3. The buffer is immediately erased and reset to empty whenever:
   - You click a mouse button
   - You press navigation keys (Arrows, Home, End, PageUp, PageDown)
   - You press Escape, Enter, or Tab
   - Typing Buddy is paused (automatically or manually)
   - The active window changes or a password field is detected

---

## How Typing Buddy Differs from a Keylogger

Because any utility that intercepts global keyboard input can look suspicious, here is how Typing Buddy differs fundamentally from keyloggers:

| Characteristic | Malicious Keylogger | Typing Buddy |
|---|---|---|
| **Network Traffic** | Exfiltrates keystrokes to remote servers | Zero network code; 100% offline |
| **Keystroke Storage** | Logs all typed characters to hidden files | Never writes typed text to disk |
| **Auditability** | Obfuscated closed-source binary | Fully readable, open-source Python code |
| **Volatile Buffers** | Preserves input across sessions | Empties buffers on focus switch, clicks, and navigation |
| **Password Safety** | Actively steals password fields | Auto-pauses on password fields (when detected); blocklist support |

---

## Password Protection & Safety Limits

Typing Buddy includes built-in protection against monitoring sensitive inputs:
1. **Windows UI Automation (UIA) Detection:** When entering a field flagged with `IsPasswordPropertyId = True`, Typing Buddy automatically pauses itself and clears all memory buffers.
2. **Win32 Password Style Check:** Standard edit controls with the `ES_PASSWORD` window style are detected and paused.
3. **Built-in Application Blocklist:** Common password managers (such as KeePass, 1Password, and Bitwarden) are paused by default.
4. **Browser and Electron Limitations:** Certain web browsers and Electron applications (such as Chromium text boxes or custom web components) do not always expose the standard Windows UIA password attribute.
5. **Your Safety Net:** Use the manual **Pause hotkey** (default `Pause/Break` key) or add sensitive applications to the `"blocked_apps"` array in `settings.json`.
