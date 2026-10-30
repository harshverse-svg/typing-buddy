"""check_docs_version.py - CI validator to ensure docs never hardcode old release zip download links in install instructions."""
import re
import sys
from pathlib import Path

# Match specific versioned archive download links in installation instructions
OLD_ZIP_PATTERN = re.compile(r"typing-buddy-v1\.0\.[0-9]+\.zip", re.IGNORECASE)

FILES_TO_CHECK = [
    Path("README.md"),
    Path("docs/install.md"),
    Path("docs/index.md"),
    Path("llms.txt"),
]


def check_file(path: Path) -> list[str]:
    violations = []
    if not path.exists():
        return [f"File {path} does not exist"]

    lines = path.read_text(encoding="utf-8").splitlines()
    in_all_versions_table = False

    for idx, line in enumerate(lines, start=1):
        # We allow historical version links inside the 'All Versions' table
        if "## All Versions" in line or "| Version |" in line:
            in_all_versions_table = True
        elif in_all_versions_table and line.startswith("## "):
            in_all_versions_table = False

        if in_all_versions_table:
            continue

        match = OLD_ZIP_PATTERN.search(line)
        if match:
            violations.append(
                f"{path}:{idx}: Found hard-coded specific versioned zip '{match.group(0)}'. "
                f"Use the permanent latest link instead."
            )
    return violations


def main():
    root = Path(__file__).resolve().parent.parent
    all_violations = []

    for rel_path in FILES_TO_CHECK:
        file_path = root / rel_path
        all_violations.extend(check_file(file_path))

    if all_violations:
        print("FAIL: Found hard-coded old versioned download links in documentation:")
        for v in all_violations:
            print(f"  - {v}")
        sys.exit(1)

    print("PASS: Documentation install instructions contain no hard-coded old version download links.")
    sys.exit(0)


if __name__ == "__main__":
    main()
