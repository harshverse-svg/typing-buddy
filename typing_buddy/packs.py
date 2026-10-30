"""packs.py - Word pack management for Typing Buddy (offline, zero-network)."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("typing_buddy.packs")


def get_wordpacks_dir() -> Path:
    """Return the repository/shipped wordpacks directory."""
    return Path(__file__).resolve().parent.parent / "wordpacks"


def list_available_packs() -> List[Dict]:
    """Scan wordpacks/ directory and return metadata of all valid packs."""
    packs_dir = get_wordpacks_dir()
    available = []
    if not packs_dir.exists():
        return available

    for subdir in sorted(packs_dir.iterdir()):
        if subdir.is_dir():
            manifest = subdir / "pack.json"
            wordlist = subdir / "words.txt"
            if manifest.exists() and wordlist.exists():
                try:
                    with open(manifest, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta["path"] = str(wordlist)
                    meta["id"] = subdir.name
                    available.append(meta)
                except Exception as e:
                    logger.warning("Error reading pack %s: %s", subdir.name, e)
    return available


def get_pack_info(pack_id: str) -> Optional[Dict]:
    """Return pack metadata by ID or None."""
    for p in list_available_packs():
        if p.get("id") == pack_id or p.get("name") == pack_id:
            return p
    return None


def get_enabled_pack_wordlists(enabled_ids: List[str]) -> List[Path]:
    """Return ordered list of wordlist Paths for enabled packs."""
    packs_dir = get_wordpacks_dir()
    paths = []
    for pid in enabled_ids:
        p_path = packs_dir / pid / "words.txt"
        if p_path.exists():
            paths.append(p_path)
        else:
            logger.warning("Enabled pack '%s' not found at %s", pid, p_path)
    return paths


def get_non_english_pack_words(enabled_ids: List[str]) -> List[str]:
    """Return list of all words from non-English enabled packs (e.g. Hinglish).

    Used to seed Harper's custom dictionary so foreign words aren't flagged as grammar errors.
    """
    words = []
    packs_dir = get_wordpacks_dir()
    for pid in enabled_ids:
        info = get_pack_info(pid)
        if info and info.get("language") != "en":
            wpath = packs_dir / pid / "words.txt"
            if wpath.exists():
                try:
                    with open(wpath, "r", encoding="utf-8-sig", errors="ignore") as f:
                        for line in f:
                            raw = line.strip()
                            if raw and not raw.startswith("#"):
                                parts = raw.split()
                                if parts:
                                    words.append(parts[0].lower())
                except OSError as e:
                    logger.warning("Error reading non-english pack %s: %s", pid, e)
    return words

