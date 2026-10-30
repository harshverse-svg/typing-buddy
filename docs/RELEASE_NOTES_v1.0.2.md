# Typing Buddy v1.0.2 Release Notes

Typing Buddy v1.0.2 enhances the installation experience with a permanent direct download link, automated release asset validation, and comprehensive setup guidance.

---

### Highlights in v1.0.2

- **Permanent Direct Download Link:** Releases now provide a fixed-name `typing-buddy.zip` alongside the versioned `typing-buddy-v1.0.2.zip`. Users and automated downloaders can always retrieve the latest stable package from:
  `https://github.com/harshverse-svg/typing-buddy/releases/latest/download/typing-buddy.zip`
- **Release Verification & Validation:** The GitHub Actions release workflow automatically verifies that both zip assets and `SHA256SUMS.txt` are successfully published, failing the workflow if any asset is missing.
- **Embedded Version Identifier:** Each release zip archive now contains a clean `VERSION` text file recording the release tag.
- **Comprehensive Installation Guide:** New step-by-step instructions (`docs/install.md` and `README.md`) designed for non-technical Windows users, covering unblocking, extraction, running `install.bat`, and finding the notification area tray icon.
- **Installation Troubleshooting:** Added detailed solutions for common Windows setup obstacles: SmartScreen prompts, Smart App Control enforcement on unsigned software, antivirus keyboard-hook false positives, path resolution in PowerShell, and diagnostic steps when the tray icon is hidden.
- **Release Maintenance Guide:** Added `docs/RELEASING.md` documenting the maintainer checklist and release validation procedures.

---

### Verification

Download and verify the archive checksum using PowerShell:

```powershell
cd $HOME\Downloads
Get-FileHash .\typing-buddy.zip -Algorithm SHA256
```

Compare the output hash against the corresponding entry in `SHA256SUMS.txt`.
