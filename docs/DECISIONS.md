# Project Architectural Decisions

This document records the architectural and design decisions made for the `typing-suggest` open-source project.

---

## 1. User Data Directory Separation

### Decision
Store all user-generated and runtime-modified files in `%APPDATA%\typing-suggest` on Windows (fallback to `~/.config/typing-suggest` on POSIX environments). Provide command-line `--data-dir PATH` and environment variable `TYPING_SUGGEST_DATA_DIR` overrides.

### Rationale
In earlier phases, user files (`user_data.json`, `words.txt`, `settings.json`, `stats.json`) resided directly alongside the application source code. For a public open-source repository, this created two severe risks:
1. Accidental commits of personal data (personal email addresses, custom snippets, sensitive words, usage history).
2. Upgrades or Git pulls overwriting personal configurations.

The repository now ships only generic example files (`settings.example.json`, `snippets.example.json`, `personal_words.example.txt`). On first launch, if the data directory lacks these files, they are safely initialized from the examples.

### One-Time Migration
If legacy files (`user_data.json`, `words.txt`, `settings.json`, etc.) exist in the program directory from previous development versions, the application prompts the user and copies (never deletes or moves) them to the `%APPDATA%\typing-suggest` directory. The program directory files are left untouched.

---

## 2. Word Packs Architecture (Zero-Network)

### Decision
Bundle optional word packs directly in the repository under `wordpacks/<pack-id>/` with a clear `pack.json` manifest. Users enable or disable packs via `settings.json` or the system tray menu.

### Rationale
To guarantee complete user privacy and air-gapped security, the application contains **no network code**. Downloading packs over HTTP was explicitly rejected.
Shipped packs:
- `en-basic`: ~5,000 top English words (~50 KB), active by default.
- `en-large`: ~150,000 English words (~2 MB), optional for users desiring comprehensive vocabulary.
- `hinglish`: ~450 common Romanized Hindi conversational words (~5 KB), community-extendable.

New auto-learned words are appended **only** to `personal_words.txt` in the user's data directory, never to shipped pack files.

---

## 3. Project Licensing & LGPL Dependencies

### Decision
License this project under the **MIT License**.

### Analysis of Dependencies:
- `pynput` is licensed under **LGPL-3.0**.
- `pystray` is licensed under **LGPL-3.0** (or GPL-3.0).
- `Pillow` is licensed under **Historical Permission Notice and Disclaimer (HPND)** (permissive BSD-style).
- `comtypes` is licensed under **MIT License**.
- `harper-py` is licensed under **Apache-2.0**.

### Rationale & LGPL Implications:
Under LGPL-3.0, applications that use LGPL libraries via standard dynamic linking (such as Python imports from standard `site-packages`) are classified as "Works that Use the Library". Distributing the application as pure Python source code under the MIT license fully complies with LGPL-3.0 requirements:
- End users can modify or upgrade the underlying `pynput` and `pystray` packages independently via `pip`.
- No proprietary restrictions are imposed on the LGPL components.
- Detailed notices and license texts are provided in `THIRD_PARTY_NOTICES.md`.
- **Note on standalone `.exe` packaging:** If a downstream distributor packages this project into a single-file executable (e.g. with PyInstaller), LGPL-3.0 requires them to provide either object files / source code allowing relinking, or ensure dynamic linking to external shared libraries. Because of this and antivirus false-alarm issues with packed executables, this project deliberately distributes clean Python source packages and wheels rather than bundled `.exe` binaries.

---

## 4. Grammar Engine Integration (Harper)

### Decision
Integrate the offline, rule-based [Harper](https://github.com/Automattic/harper) engine via `harper-py` (pinned at `0.2.0`). Wrap it behind a decoupled `GrammarChecker` abstract interface, providing both `HarperChecker` and `NullChecker`.

### Rules & Scoping:
1. **Grammar only, never spelling:** Harper's `SpellCheck` and `Misspell` lints are disabled in configuration and filtered out in the adapter. Spelling is exclusively handled by our high-performance fuzzy engine.
2. **Selective Lint Kinds:** Only high-confidence grammatical rules (e.g. Subject-Verb Agreement, Word Repetition, A vs. An, common word choice confusions) are enabled by default. Stylistic and readability lints are disabled to prevent noisy popups.
3. **RAM-Only Text Tracker:** Context is tracked only in volatile RAM (`TextTracker`), capped at 300 characters, version-incremented on every change, and immediately discarded upon any non-character or unmodeled event (mouse click, arrows, shortcuts, pause).
4. **Zero Telemetry / Zero Models:** Harper runs entirely offline in pure native code without GPU requirements or machine learning models.



---

## 7. Project Rename to Typing Buddy & Desktop Integration

### Decision
Rename the project and Python package from `typing-suggest` to `typing-buddy`.
Update the data folder to `%APPDATA%\typing-buddy\` with automatic one-time safe migration from legacy `%APPDATA%\typing-suggest\`.
Provide desktop shell integration via `tools/create_shortcuts.ps1` (Desktop, Start Menu, Startup shortcut) and single-instance mutex guard `TypingBuddy_SingleInstance_Mutex`.

### Rationale
"Typing Buddy" establishes a distinct, friendly open-source identity. Shell shortcuts allow end users to launch the assistant as a standard native Windows application without ever opening a terminal. Migrating from the registry Run key to the Windows Startup folder unifies the auto-start mechanism and prevents duplicate instances.
