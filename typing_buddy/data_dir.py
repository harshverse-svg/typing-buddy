"""data_dir.py - Manage application data directory, file initialization, and migration."""
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger("typing_buddy.data_dir")

DEFAULT_APP_DIR_NAME = "typing-buddy"
LEGACY_APP_DIR_NAME = "typing-suggest"


def get_default_data_dir() -> Path:
    """Return platform-standard application data directory."""
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / DEFAULT_APP_DIR_NAME
        return Path.home() / "AppData" / "Roaming" / DEFAULT_APP_DIR_NAME
    # Non-Windows fallback (for unit tests / portability)
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / DEFAULT_APP_DIR_NAME
    return Path.home() / ".config" / DEFAULT_APP_DIR_NAME


def resolve_data_dir(custom_path: Optional[str] = None) -> Path:
    """Resolve data directory path based on CLI flag, environment variable, or default."""
    if custom_path:
        p = Path(custom_path).resolve()
    elif os.environ.get("TYPING_BUDDY_DATA_DIR"):
        p = Path(os.environ["TYPING_BUDDY_DATA_DIR"]).resolve()
    elif os.environ.get("TYPING_SUGGEST_DATA_DIR"):
        p = Path(os.environ["TYPING_SUGGEST_DATA_DIR"]).resolve()
    else:
        p = get_default_data_dir().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_program_dir() -> Path:
    """Return repository/program root directory."""
    return Path(__file__).resolve().parent.parent


def init_user_data_files(data_dir: Path, interactive_migrate: bool = True):
    """Initialize missing configuration files from shipped templates and perform one-time migration."""
    data_dir.mkdir(parents=True, exist_ok=True)
    program_dir = get_program_dir()

    migration_marker = data_dir / ".migrated"
    if not migration_marker.exists():
        # 1. Migrate from old %APPDATA%\typing-suggest if it exists
        _check_and_migrate_from_typing_suggest(data_dir)
        # 2. Migrate from legacy program folder if existing
        _check_and_migrate_legacy_files(program_dir, data_dir)
        try:
            migration_marker.write_text("migrated=true\n", encoding="utf-8")
        except OSError:
            pass

    # Ensure required files exist by copying shipped examples if missing
    file_mappings = [
        ("settings.example.json", "settings.json"),
        ("snippets.example.json", "snippets.json"),
        ("personal_words.example.txt", "personal_words.txt"),
    ]

    for example_name, target_name in file_mappings:
        target_path = data_dir / target_name
        example_path = program_dir / example_name
        if not target_path.exists() and example_path.exists():
            try:
                shutil.copy2(example_path, target_path)
                logger.info("Initialized %s from %s", target_path, example_name)
            except OSError as e:
                logger.warning("Could not copy example file %s: %s", example_name, e)


def _check_and_migrate_from_typing_suggest(data_dir: Path):
    """One-time safe copy migration from %APPDATA%/typing-suggest to %APPDATA%/typing-buddy."""
    try:
        parent_dir = data_dir.parent
        old_data_dir = parent_dir / LEGACY_APP_DIR_NAME
        if old_data_dir.exists() and old_data_dir != data_dir:
            files_to_copy = [
                "settings.json",
                "snippets.json",
                "personal_words.txt",
                "ignore_words.txt",
                "user_data.json",
                "added_words.json",
                "stats.json",
                "predictor.log",
            ]
            for fname in files_to_copy:
                src = old_data_dir / fname
                dst = data_dir / fname
                if src.exists() and not dst.exists():
                    try:
                        shutil.copy2(src, dst)
                        logger.info("Migrated file from typing-suggest: %s -> %s", src, dst)
                    except OSError as e:
                        logger.warning("Could not copy legacy typing-suggest file %s: %s", src, e)
    except Exception as e:
        logger.debug("Safe migration check from typing-suggest encountered error: %s", e)


def _check_and_migrate_legacy_files(program_dir: Path, data_dir: Path):
    """Copy existing files from legacy project root to user data directory without deleting originals."""
    legacy_files = [
        ("words.txt", "personal_words.txt"),
        ("user_data.json", "user_data.json"),
        ("settings.json", "settings.json"),
        ("snippets.json", "snippets.json"),
        ("added_words.json", "added_words.json"),
        ("stats.json", "stats.json"),
        ("ignore_words.txt", "ignore_words.txt"),
    ]

    migrated_any = False
    for src_name, dest_name in legacy_files:
        src_path = program_dir / src_name
        dest_path = data_dir / dest_name
        if src_path.exists() and not dest_path.exists():
            try:
                shutil.copy2(src_path, dest_path)
                logger.info("Migrated legacy %s -> %s", src_name, dest_path)
                migrated_any = True
            except OSError as e:
                logger.warning("Failed to migrate %s: %s", src_name, e)

    if migrated_any:
        logger.info("Legacy migration complete. Shipped files preserved in program directory.")
