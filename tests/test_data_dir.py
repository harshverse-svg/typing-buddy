"""test_data_dir.py - Unit tests for data directory resolution, initialization, and migration."""
import tempfile
from pathlib import Path

from typing_buddy.data_dir import (
    _check_and_migrate_from_typing_suggest,
    init_user_data_files,
    resolve_data_dir,
)


def test_resolve_data_dir_custom():
    with tempfile.TemporaryDirectory() as tmp:
        custom = Path(tmp) / "custom_data"
        resolved = resolve_data_dir(str(custom))
        assert resolved == custom.resolve()
        assert resolved.exists()


def test_resolve_data_dir_env(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TYPING_BUDDY_DATA_DIR", tmp)
        resolved = resolve_data_dir()
        assert resolved == Path(tmp).resolve()


def test_resolve_data_dir_env_legacy_fallback(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.delenv("TYPING_BUDDY_DATA_DIR", raising=False)
        monkeypatch.setenv("TYPING_SUGGEST_DATA_DIR", tmp)
        resolved = resolve_data_dir()
        assert resolved == Path(tmp).resolve()


def test_init_user_data_files():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        init_user_data_files(data_dir)

        # Check initialized files from templates
        assert (data_dir / "settings.json").exists()
        assert (data_dir / "snippets.json").exists()
        assert (data_dir / "personal_words.txt").exists()
        assert (data_dir / ".migrated").exists()


def test_migrate_from_typing_suggest():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        old_dir = root / "typing-suggest"
        new_dir = root / "typing-buddy"
        old_dir.mkdir(parents=True)
        new_dir.mkdir(parents=True)

        # Create dummy user file in old dir
        (old_dir / "settings.json").write_text('{"migrated_test": true}', encoding="utf-8")
        (old_dir / "personal_words.txt").write_text("wordone\nwordtwo\n", encoding="utf-8")

        _check_and_migrate_from_typing_suggest(new_dir)

        # Verify copied over to new dir
        assert (new_dir / "settings.json").exists()
        assert '{"migrated_test": true}' in (new_dir / "settings.json").read_text(encoding="utf-8")
        assert (new_dir / "personal_words.txt").exists()

        # Verify old files were NOT deleted
        assert (old_dir / "settings.json").exists()
        assert (old_dir / "personal_words.txt").exists()
