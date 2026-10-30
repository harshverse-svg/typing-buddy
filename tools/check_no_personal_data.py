"""check_no_personal_data.py - Verify no private personal data is committed to the repository.

Checks:
1. No user data files exist in tracked repository files (user_data.json, personal_words.txt, stats.json, *.log).
2. No personal email addresses, phone numbers, or private user paths in repository files.
"""
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_FILENAMES = {
    "user_data.json",
    "personal_words.txt",
    "added_words.json",
    "stats.json",
    "predictor.log",
}

FORBIDDEN_EXTENSIONS = {".log"}

# Whitelisted example emails / domains
SAFE_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net",
    "domain.com", "users.noreply.github.com"
}

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b")
WIN_USER_PATH_REGEX = re.compile(r"[C-Z]:\\Users\\(?!Public\b|Default\b)[A-Za-z0-9_ -]+\\", re.IGNORECASE)
LOCAL_DEV_PATH_REGEX = re.compile(r"[A-Za-z]:[\\/]files\b", re.IGNORECASE)

# Standard phone number patterns (e.g., +1-555-123-4567, 555-123-4567, +91 98765 43210)
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

# Whitelisted fake phone numbers for documentation / examples
SAFE_PHONE_PATTERNS = {
    "555-0100", "555-0199", "123-456-7890", "555-123-4567"
}

EXEMPT_DIRS = {".git", ".pytest_cache", ".ruff_cache", ".venv", "venv", "__pycache__", "build", "dist"}


def get_target_files(root: Path) -> list[Path]:
    """Get list of files to check: git tracked files if git repo, otherwise all non-ignored files."""
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True
        )
        files = [root / line.strip() for line in res.stdout.splitlines() if line.strip()]
        if files:
            return files
    except Exception:
        pass

    # Fallback if git is not initialized yet: check all files skipping EXEMPT_DIRS and gitignored files
    gitignore = root / ".gitignore"
    ignored_names = set(FORBIDDEN_FILENAMES)
    if gitignore.exists():
        for line in gitignore.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                ignored_names.add(line.strip("/"))

    files = []
    for path in root.rglob("*"):
        if path.is_file():
            if any(part in EXEMPT_DIRS for part in path.parts):
                continue
            # If git is not initialized, don't flag local untracked files that .gitignore excludes
            if path.name in ignored_names:
                continue
            files.append(path)
    return files


def scan_file(file_path: Path) -> list[str]:
    violations = []
    # Check filename
    if file_path.name in FORBIDDEN_FILENAMES:
        violations.append(f"Forbidden user data file in repository files: {file_path}")
    if file_path.suffix.lower() in FORBIDDEN_EXTENSIONS:
        violations.append(f"Forbidden log file in repository files: {file_path}")

    # Check text content
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return violations

    is_check_script = "check_no_personal_data.py" in file_path.as_posix()
    is_test_script = "tests/" in file_path.as_posix()

    for line_num, line in enumerate(content.splitlines(), start=1):
        if is_check_script:
            continue

        # Email check
        for match in EMAIL_REGEX.finditer(line):
            domain = match.group(1).lower()
            if domain not in SAFE_EMAIL_DOMAINS:
                violations.append(f"{file_path}:{line_num}: Possible real email address: {match.group(0)}")

        # Phone check
        if not is_test_script:
            for match in PHONE_REGEX.finditer(line):
                phone = match.group(0)
                if not any(safe in phone for safe in SAFE_PHONE_PATTERNS):
                    # Ignore date-like or version-like sequences e.g. 2026.04.12
                    if not re.match(r"^\d{4}[-.]\d{2}[-.]\d{2}$", phone):
                        violations.append(f"{file_path}:{line_num}: Possible phone number: {phone}")

        # Private Windows user path check
        if not is_test_script:
            if WIN_USER_PATH_REGEX.search(line):
                if "<username>" not in line and "<name>" not in line and "Username" not in line and "%USERNAME%" not in line:
                    violations.append(f"{file_path}:{line_num}: Private Windows user path detected: {line.strip()}")
            if LOCAL_DEV_PATH_REGEX.search(line):
                violations.append(f"{file_path}:{line_num}: Hardcoded local development path detected: {line.strip()}")

    return violations


def main():
    root = Path(__file__).resolve().parent.parent
    files = get_target_files(root)
    violations = []

    for path in files:
        violations.extend(scan_file(path))

    if violations:
        print("FAIL: Personal data or user files found in repository:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)

    print(f"PASS: Verified {len(files)} repository files. No personal data or private user files found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
