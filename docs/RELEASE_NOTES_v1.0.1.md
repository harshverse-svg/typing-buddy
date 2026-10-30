# Typing Buddy v1.0.1 Release Notes

Typing Buddy v1.0.1 is a maintenance release that streamlines the repository layout, fixes CLI argument parsing, and refines documentation with real measured benchmarks.

---

### Key Improvements in v1.0.1

- **Clean Package Layout:** Removed deprecated legacy root-level source files (`app.py`, `fuzzy.py`, `predictor.py`, `settings.py`, `tray.py`, etc.). All runtime modules and tests now import exclusively from the modern `typing_buddy` package.
- **CLI Argument Parsing Fix:** Resolved string formatting issue in `argparse` help string (`%APPDATA%` $\rightarrow$ `%%APPDATA%%`), ensuring `python -m typing_buddy --version` and `--help` execute without error.
- **Calibrated Documentation:** Updated performance and memory figures in documentation and `llms.txt` to match actual measured benchmarks (sub-millisecond suggestion latency, ~125 MB base memory footprint).
- **Setup Guidance:** Added Step 0 in installation documentation detailing Python setup and the vital "Add Python to PATH" checkbox for new users.
- **Known Limitations:** Documented environment considerations including Windows UIPI elevation requirements and non-standard input controls.

---

### Verification

Download and verify the package checksum using PowerShell:

```powershell
Get-FileHash typing-buddy-v1.0.1.zip -Algorithm SHA256
```

Compare the output with the checksum in `SHA256SUMS.txt`.
