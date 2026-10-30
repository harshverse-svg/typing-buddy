"""test_pick_keys.py - Verify digit pick key rejection and normal number typing."""
from typing_buddy import app
from typing_buddy.app import build_pick_key_map, pick_index, state
from typing_buddy.settings import validate_settings


def test_digit_pick_keys_rejected_in_settings():
    # Attempting to configure digit pick keys must fail and fall back to F-keys
    settings = validate_settings({"pick_keys": ["1", "2", "3"]})
    assert settings["pick_keys"] == ["F2", "F3", "F4"]
    assert "1" not in settings["pick_keys"]
    assert "2" not in settings["pick_keys"]
    assert "3" not in settings["pick_keys"]


def test_typing_version_2_and_windows_10_with_popup_visible():
    # Setup mock active suggestions
    state.paused = False
    state.auto_paused = False
    state.word = "version"
    state.suggestions = ["version", "versioning", "versions"]

    # Valid pick keys (F2, F3, F4)
    app.PICK_KEYS = build_pick_key_map(["F2", "F3", "F4"])

    # VK codes for '1', '2', '0'
    VK_0 = 0x30
    VK_1 = 0x31
    VK_2 = 0x32
    VK_F2 = 0x71

    # While typing "version 2", pressing '2' (VK_2) must NOT pick a suggestion
    assert pick_index(VK_2) is None, "Pressing '2' while suggestions are visible must not trigger a pick"

    # F2 DOES trigger pick
    assert pick_index(VK_F2) == 0

    # Next: simulated typing of "Windows 10"
    state.word = ""  # next-word suggestions after "Windows "
    state.suggestions = ["and", "is", "for"]
    assert pick_index(VK_1) is None, "Pressing '1' in 'Windows 10' must not pick suggestion [1]"
    assert pick_index(VK_0) is None, "Pressing '0' in 'Windows 10' must not pick a suggestion"
