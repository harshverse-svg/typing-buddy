## Description

Briefly describe the change and the rationale behind it.

## Type of Change

- [ ] Bug fix (non-breaking fix for an existing issue)
- [ ] New feature (e.g. new word pack or configuration option)
- [ ] Documentation update
- [ ] Performance optimization

## Verification Checklist

- [ ] `pytest -v` passes with no failures.
- [ ] `python tools/check_no_network.py` passes (zero network imports).
- [ ] `python tools/check_no_personal_data.py` passes (no sensitive user data).
- [ ] Keyboard hook remains non-blocking; no slow I/O added to main/hook thread.
- [ ] No telemetry, analytics, or network requests introduced.
- [ ] No persistent keystroke or sentence logging added to disk.
- [ ] If adding or changing word packs, words are lowercase, clean, and tested.

