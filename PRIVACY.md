# Privacy Policy & Architecture

**Typing Buddy is 100% offline and stores zero keystroke logs.**

We designed Typing Buddy from day one to operate strictly on your personal computer without internet connectivity, analytics, or surveillance capabilities.

---

## The Zero-Network Guarantee

Typing Buddy contains **zero network code**:
- No HTTP or HTTPS requests
- No telemetry, usage statistics, or analytics pings
- No automatic updates or background downloads
- No socket connections or remote sync

You can independently verify this at any time by running our automated AST code verification tool from the repository root:

```cmd
python tools/check_no_network.py
```

This tool inspects every Python file in the codebase using Python's Abstract Syntax Tree (AST) parser to ensure that no networking modules (`urllib`, `requests`, `socket`, `http`, `asyncio`, etc.) are imported anywhere in the application.

---

## What Is Stored Locally on Your Computer

All user configuration and personalized data are stored locally in your Windows user profile at `%APPDATA%\typing-buddy\` (or the path specified by `--data-dir` / `TYPING_BUDDY_DATA_DIR`):

| File | What It Stores | Why It Exists |
|---|---|---|
| `settings.json` | Key-value application preferences | UI dimensions, hotkeys, enabled word packs |
| `snippets.json` | Text abbreviations and expansions | User-defined snippet shortcuts |
| `personal_words.txt` | Custom vocabulary words (one word per line) | Words you explicitly add or repeatedly type |
| `ignore_words.txt` | Words to exclude from suggestions | Custom suppression list |
| `user_data.json` | Frequency counts of individual words | Frequency weights to prioritize words you use often |
| `stats.json` | Aggregate suggestion acceptances and keystroke counts | Daily keystroke savings summary shown in review window |
| `predictor.log` | Diagnostic status messages (e.g. startup, reload) | Troubleshooting issues |

### What Is NEVER Stored or Logged
- **No typed sentences or phrases:** Full text is never written to disk.
- **No full key sequences:** Raw keystroke streams are never recorded or journaled.
- **No clipboard history:** Clipboard contents are never read or stored.
- **No password inputs:** Password fields are ignored, and buffers are flushed.

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
| **Password Safety** | Actively steals password fields | Auto-pauses on password fields; blocklist support |

---

## Password Protection & Safety Limits

Typing Buddy includes built-in protection against monitoring sensitive inputs:
1. **Windows UI Automation (UIA) Detection:** When entering a field flagged with `IsPasswordPropertyId = True`, Typing Buddy automatically pauses itself and clears all memory buffers.
2. **Built-in Application Blocklist:** Common password managers (such as KeePass, 1Password, and Bitwarden) are paused by default.
3. **Browser and Electron Limitations:** Certain web browsers and Electron applications (such as Chromium text boxes or custom web components) do not always expose the standard Windows UIA password attribute.
4. **Your Safety Net:** Use the manual **Pause hotkey** (default `Pause` key or user-configured hotkey) or add sensitive applications to the `"blocked_apps"` array in `settings.json`.
