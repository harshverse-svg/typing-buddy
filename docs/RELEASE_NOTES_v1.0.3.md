# Typing Buddy v1.0.3 Release Notes

Typing Buddy v1.0.3 is a focused privacy, security, and stability release that transitions vocabulary learning to review-by-default, eliminates numeric pick key collisions, and strengthens zero-network security auditing.

### Key Highlights in v1.0.3

1. **Review-by-Default Word Learning (`new_word_mode: "review"`)**:
   - New words typed across Windows applications are held strictly in temporary RAM.
   - Pending words are never written to disk until explicitly approved via the Review Window.
   - Word-pair transitions (`bi`) are saved only when both words are already verified words.

2. **Pick Keys Hardening**:
   - Pick keys are now restricted to function keys (`F1`–`F12`) and `Tab`.
   - Numeric digits (`1`, `2`, `3`, etc.) are rejected with automatic fallback to prevent accidental key suppression when typing numbers while autocomplete is active.

3. **Strengthened Zero-Network Static Audit**:
   - `tools/check_no_network.py` now statically inspects AST nodes for banned network modules, dynamic imports, shell/process execution, network DLL references, and network URLs in `os.startfile`.
   - Backed by automated unit test suites (`tests/test_check_no_network.py`).

4. **Licensing & Attribution Transparency**:
   - Full upstream Harper and `harper-py` bindings attribution in `THIRD_PARTY_NOTICES.md`.
   - Complete SCOWL copyright notice reproduced in `wordpacks/NOTICE.md`.

### SHA256 Verification

Download hashes will be published with release assets in `SHA256SUMS.txt`.
Verify integrity on Windows PowerShell before running:
```powershell
Get-FileHash .\typing-buddy.zip -Algorithm SHA256
```
