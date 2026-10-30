# Contributing to Typing Buddy

Thank you for your interest in contributing to Typing Buddy!

Typing Buddy is an offline, privacy-first typing assistant for Windows. We welcome contributions that improve speed, accuracy, word coverage, and stability.

---

## Code of Conduct

All contributors and participants are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Architectural Ground Rules

Before opening a pull request, ensure your proposed changes adhere to these fundamental principles:

1. **Zero Network Code:** The core application package (`typing_buddy`) must **never** perform network requests, telemetry, background checks, or imports from network modules (`urllib`, `requests`, `socket`, `http`, etc.).
2. **Strict Privacy:** Typed text must remain volatile and in-memory only. Do not add code that writes sentences or keystrokes to disk or logs.
3. **Non-Blocking Hook:** The low-level Windows keyboard hook (`win32_filter` and `on_press`) must never execute slow work, file I/O, regex searches, or UI Automation checks. All slow or asynchronous operations must be queued to background worker threads.
4. **Offline Word Packs:** Word packs must be bundled offline in `wordpacks/` and require zero network downloading.

---

## Development Setup

1. **Clone the repository:**
   ```cmd
   git clone https://github.com/harshverse-svg/typing-buddy.git
   cd typing-buddy
   ```

2. **Create a virtual environment:**
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies in editable mode:**
   ```cmd
   pip install -e ".[dev,grammar]"
   ```

---

## Running Verification & Tests

Before submitting changes, ensure all automated tests and safety verifiers pass:

```cmd
:: Run test suite
pytest -v

:: Verify zero network code in package
python tools/check_no_network.py

:: Verify no personal or sensitive data in files
python tools/check_no_personal_data.py

:: Run linter
ruff check .
```

---

## Contributing to Word Packs

We welcome vocabulary improvements, especially for multilingual and colloquial packs like `wordpacks/hinglish`!

### Adding Words to an Existing Pack
1. Open the pack's `words.txt` file (e.g., `wordpacks/hinglish/words.txt`).
2. Add lowercase entries (one per line) formatted as `word frequency` or simply `word` (default frequency is 1).
3. Ensure entries are in lowercase and stripped of special characters or punctuation.
4. Keep entries culturally respectful and relevant for day-to-day typing.

### Creating a New Pack
1. Create a folder in `wordpacks/<pack-id>/` (e.g. `wordpacks/medical/`).
2. Add a `pack.json` with metadata:
   ```json
   {
     "id": "medical",
     "name": "Medical Terminology",
     "description": "Common medical, clinical, and anatomical terms",
     "language": "en",
     "words_file": "words.txt",
     "default_enabled": false
   }
   ```
3. Add `words.txt`.
4. Test that `python -m typing_buddy packs list` discovers your new pack.

---

## Submitting a Pull Request

1. Create a feature branch: `git checkout -b feature/my-feature-name`.
2. Commit your changes with clear, descriptive commit messages.
3. Push to your fork and submit a Pull Request to `main`.
4. Fill out the Pull Request template completely.
