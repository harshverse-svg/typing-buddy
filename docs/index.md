---
layout: default
title: "Typing Buddy — The Offline, Privacy-First Typing Assistant for Windows"
description: "Instant autocomplete, word suggestions, fuzzy typo corrections, and offline grammar checker for Windows. 100% offline, zero network code, and strict in-memory privacy."
---

# Typing Buddy

**The offline, privacy-first typing assistant and autocomplete for Windows.**

[Download Latest Release](https://github.com/harshverse-svg/typing-buddy/releases/latest) • [View on GitHub](https://github.com/harshverse-svg/typing-buddy) • [Privacy Policy](https://github.com/harshverse-svg/typing-buddy/blob/main/PRIVACY.md)

---

## Highlights

- **100% Offline:** No cloud connections, no telemetry, no tracking. Verified with automated AST code scanning.
- **System-Wide Autocomplete:** Instant completions as you type in Notepad, Word, browsers, chat apps, and editors.
- **Fuzzy Typo Corrections:** Intelligent Damerau-Levenshtein distance matching with keyboard layout weighting.
- **Offline Grammar Checker:** Integrated sentence-level grammar linting powered by the offline Harper engine.
- **Hinglish Support:** Bundled multilingual word pack for colloquial Romanized Hindi typing.
- **RAM-Only Privacy:** Transient sentence buffer is capped at 300 characters in RAM and wiped on clicks or navigation.

---

## Quick Installation

1. Download the latest release zip from our [GitHub Releases](https://github.com/harshverse-svg/typing-buddy/releases/latest).
2. Extract the folder and double-click `install.bat`.
3. Launch Typing Buddy from your Desktop icon or Start menu.

---

## How It Works

Typing Buddy monitors keystrokes locally via non-blocking Windows hooks. Predictions are matched against pre-indexed trie dictionaries and offline grammar linters. Keystrokes are never saved or sent over networks.

For full architectural details and settings reference, visit the [Typing Buddy Repository](https://github.com/harshverse-svg/typing-buddy).
