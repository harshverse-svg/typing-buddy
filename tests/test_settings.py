"""test_settings.py - Unit tests for settings validation and loading."""
import json
import os
import tempfile

from typing_buddy.settings import DEFAULT_SETTINGS, Settings, validate_settings


def test_validate_defaults():
    cleaned = validate_settings({})
    assert cleaned == DEFAULT_SETTINGS


def test_validate_valid_overrides():
    raw = {
        "min_prefix": 3,
        "max_suggestions": 5,
        "pick_keys": ["F1", "F2", "F3", "F4", "F5"],
        "tab_picks_first": False,
        "pause_key": "scroll_lock",
        "popup_font_size": 16,
        "popup_opacity": 0.8,
        "autocorrect_mode": "off",
        "fuzzy_enabled": False,
        "blocked_apps": ["notepad.exe"],
        "blocked_title_words": ["secret"]
    }
    cleaned = validate_settings(raw)
    assert cleaned["min_prefix"] == 3
    assert cleaned["max_suggestions"] == 5
    assert cleaned["pick_keys"] == ["F1", "F2", "F3", "F4", "F5"]
    assert cleaned["tab_picks_first"] is False
    assert cleaned["pause_key"] == "scroll_lock"
    assert cleaned["popup_font_size"] == 16
    assert cleaned["popup_opacity"] == 0.8
    assert cleaned["autocorrect_mode"] == "off"
    assert cleaned["fuzzy_enabled"] is False
    assert cleaned["blocked_apps"] == ["notepad.exe"]
    assert cleaned["blocked_title_words"] == ["secret"]


def test_validate_invalid_values_fallback():
    raw = {
        "min_prefix": -5,            # invalid range -> default
        "max_suggestions": 100,      # invalid range -> default
        "pick_keys": ["F2", "F2"],   # duplicates -> default
        "tab_picks_first": "yes",    # not bool -> default
        "popup_font_size": 1,        # < 8 -> default
        "popup_opacity": 5.0,        # > 1.0 -> default
        "autocorrect_mode": "magic", # not suggest/off -> default
        "word_packs": "invalid"      # not a list -> default
    }
    cleaned = validate_settings(raw)
    assert cleaned["min_prefix"] == DEFAULT_SETTINGS["min_prefix"]
    assert cleaned["max_suggestions"] == DEFAULT_SETTINGS["max_suggestions"]
    assert cleaned["pick_keys"] == DEFAULT_SETTINGS["pick_keys"]
    assert cleaned["tab_picks_first"] == DEFAULT_SETTINGS["tab_picks_first"]
    assert cleaned["popup_font_size"] == DEFAULT_SETTINGS["popup_font_size"]
    assert cleaned["popup_opacity"] == DEFAULT_SETTINGS["popup_opacity"]
    assert cleaned["autocorrect_mode"] == DEFAULT_SETTINGS["autocorrect_mode"]
    assert cleaned["word_packs"] == DEFAULT_SETTINGS["word_packs"]


def test_settings_file_load_and_reload():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "settings.json")
        cfg = Settings(path)
        assert os.path.exists(path)
        assert cfg.min_prefix == 2

        # Change file on disk
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"min_prefix": 4}, f)

        cfg.reload()
        assert cfg.min_prefix == 4


def test_pick_keys_digits_rejected():
    raw = {"pick_keys": ["1", "2", "3"]}
    cleaned = validate_settings(raw)
    assert cleaned["pick_keys"] == ["F2", "F3", "F4"], "Digits must be rejected and fall back to defaults"


def test_pick_keys_f_keys_and_tab_allowed():
    raw = {"pick_keys": ["f1", "tab", "F12"]}
    cleaned = validate_settings(raw)
    assert cleaned["pick_keys"] == ["F1", "Tab", "F12"]


def test_new_word_mode_validation():
    for mode in ("review", "auto", "off"):
        cleaned = validate_settings({"new_word_mode": mode})
        assert cleaned["new_word_mode"] == mode

    # Invalid mode falls back to default "review"
    cleaned = validate_settings({"new_word_mode": "invalid_mode"})
    assert cleaned["new_word_mode"] == "review"


def test_new_word_mode_legacy_upgrade_path():
    # If legacy auto_add_new_words is false, set mode to off
    cleaned = validate_settings({"auto_add_new_words": False})
    assert cleaned["new_word_mode"] == "off"

    # If legacy auto_add_new_words is true and new_word_mode omitted, default to review
    cleaned = validate_settings({"auto_add_new_words": True})
    assert cleaned["new_word_mode"] == "review"


