# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-04-12

### Fixed
- Fixed unescaped `%APPDATA%` formatting token in `typing_buddy/app.py` CLI parser causing `ValueError` during `--version` and `--help`.
- Updated test suite imports to directly reference `typing_buddy` package instead of deprecated root module names.
- Cleaned up root repository layout by removing deprecated flat files (`app.py`, `fuzzy.py`, `predictor.py`, etc.).
- Adjusted documentation and README performance claims to reflect measured benchmark latencies and resource numbers.
- Added explicit Step 0 to installation guide for configuring Python on Windows PATH.
- Documented Known Limitations regarding Windows-only architecture, admin elevation, and non-standard caret fields.

## [1.0.0] - 2026-04-12

### Changed
- **Renamed from Typing Suggest to Typing Buddy.**
  - Package renamed from `typing_suggest` to `typing_buddy`.
  - Data directory updated to `%APPDATA%\typing-buddy\` with automatic one-time safe migration from legacy `%APPDATA%\typing-suggest\`.
  - Environment variable updated to `TYPING_BUDDY_DATA_DIR` (with fallback to `TYPING_SUGGEST_DATA_DIR`).

### Added
- **Desktop & Start Menu Integration:**
  - Distinctive, friendly multi-resolution brand icon (`assets/typing-buddy.ico`).
  - Automated shortcut installer script (`tools/create_shortcuts.ps1`) supporting Desktop, Start Menu search, and Startup.
  - Interactive prompts in `install.bat` and silent automation via `install.bat /silent`.
  - Single startup mechanism via Startup folder shortcut, cleaning legacy Run registry keys.
  - Single-instance mutex guard (`TypingBuddy_SingleInstance_Mutex`) to prevent duplicate processes.
- **Offline Grammar Suggestions (Harper Integration):**
  - Real-time sentence-level grammar feedback powered by Harper (`harper-py`).
  - Strict allow-list of grammatical categories (`Agreement`, `WordChoice`, `Usage`, `Miscellaneous`, `Repetition`).
  - False-positive prevention for casual chats, abbreviations, and Hinglish dialogue.
  - Dedicated background grammar worker thread with 150 ms debounce and coalescing.
  - Subtitle explanations (`grammar_show_reason`) rendered below replacement pills.
- **Modular Offline Word Packs:**
  - Bundled `en-basic` (5,000 common words, ~120 MB RAM footprint).
  - Optional `en-large` (~150,000 words, ~330 MB RAM footprint).
  - Bundled `hinglish` pack (320+ colloquial Roman-script Hindi terms) with automated Harper dictionary seeding.
  - Dynamic tray submenu for switching word packs on the fly with background dictionary reloading.
  - CLI management tool: `python -m typing_buddy packs list`.
- **Clean User Data Separation:**
  - Standard user profile directory at `%APPDATA%\typing-buddy\` (configurable via `--data-dir` or `TYPING_BUDDY_DATA_DIR`).
  - Automatic one-time safe copy migration from legacy program folders and previous data locations.
  - Shipped sanitized examples (`settings.example.json`, `snippets.example.json`, `personal_words.example.txt`).
- **Windows Convenience Scripts:**
  - `install.bat`: Interactive installer checking Python >= 3.10, setting up `.venv`, creating shortcuts, and offering optional grammar.
  - `start.bat`: Headless background launcher via `pythonw`.
  - `uninstall.bat`: Clean uninstaller removing shortcuts, startup entries, and user data.
- **Safety & Verification Tools:**
  - `tools/check_no_network.py`: AST parser guaranteeing zero network imports.
  - `tools/check_no_personal_data.py`: Pre-commit/CI scanner preventing sensitive file leaks.
- **Full Test Suite & CI:**
  - Unit tests for all components with 100% pass rate.
  - GitHub Actions CI matrix across Python 3.10, 3.11, and 3.12 on Windows.
