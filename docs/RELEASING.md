# Release Process & Checklist

This document details the standardized release procedure for Typing Buddy.

---

## Pre-Flight Checklist

Before cutting a release, verify all code quality and security gates pass locally:

```cmd
pytest
ruff check .
python tools/check_no_network.py
python tools/check_no_personal_data.py
```

All 4 commands must pass with zero errors.

---

## Step 1: Bump Version Numbers

Update the version string across project metadata:

1. **`pyproject.toml`**: `version = "X.Y.Z"`
2. **`typing_buddy/__init__.py`**: `__version__ = "X.Y.Z"`
3. **`CITATION.cff`**: `version: X.Y.Z` and `date-released: YYYY-MM-DD`

---

## Step 2: Update Documentation & Release Notes

1. **`CHANGELOG.md`**:
   - Add a new `## [X.Y.Z] - YYYY-MM-DD` section following Keep a Changelog conventions.
2. **`docs/RELEASE_NOTES_vX.Y.Z.md`**:
   - Draft dedicated release notes covering highlights, fixes, and verification steps.
3. **`README.md` & `docs/install.md`**:
   - Add the new version row to the top of the **All versions** table and mark it `(Latest)`.
   - Update prior rows to point to tag-based download URLs.

---

## Step 3: Commit and Push to Main

```cmd
git add pyproject.toml typing_buddy/__init__.py CITATION.cff CHANGELOG.md docs/ README.md
git commit -m "chore(release): prepare vX.Y.Z release"
git push origin main
```

Confirm that the CI workflow succeeds on `main`.

---

## Step 4: Create and Push the Tag

Create an annotated git tag and push it to trigger the automated release workflow:

```cmd
git tag -a vX.Y.Z -m "Typing Buddy vX.Y.Z release"
git push origin vX.Y.Z
```

The GitHub Actions workflow (`.github/workflows/release.yml`) will:
1. Build a clean release archive containing no `.venv`, no user files, and no `__pycache__`.
2. Embed a `VERSION` text file inside the archive.
3. Produce both `typing-buddy-vX.Y.Z.zip` and the permanent `typing-buddy.zip`.
4. Generate `SHA256SUMS.txt` with hashes for both files.
5. Publish the release with `make_latest: true` (or `make_latest: false` for pre-release tags like `-rc`, `-beta`, `-alpha`).
6. Validate that all required assets are present on GitHub Releases.

---

## Step 5: Post-Release Verification

After the GitHub Actions workflow completes:

### 1. Apply Detailed Release Notes
```cmd
gh release edit vX.Y.Z --notes-file docs/RELEASE_NOTES_vX.Y.Z.md
```

### 2. Confirm "Latest" Mark
```cmd
gh release list
gh api repos/harshverse-svg/typing-buddy/releases/latest --jq .tag_name
```
The output must show `vX.Y.Z`.

### 3. Test Permanent Direct Download Link
```cmd
curl -sIL https://github.com/harshverse-svg/typing-buddy/releases/latest/download/typing-buddy.zip
```
Ensure HTTP response ends in `HTTP/2 200` with `content-type: application/zip` or `octet-stream`.

### 4. Verify Checksum and Archive Contents
Download `typing-buddy.zip`, calculate its hash, and confirm it matches `SHA256SUMS.txt`:
```powershell
Get-FileHash typing-buddy.zip -Algorithm SHA256
```
Inspect the archive contents to verify:
- `VERSION` file is present and matches `vX.Y.Z`.
- Source code, assets, wordpacks, and batch scripts are included.
- No personal files (`user_data.json`, `stats.json`, `predictor.log`) or virtual environments are packaged.
