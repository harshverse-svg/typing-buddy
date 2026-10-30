"""test_packs.py - Unit tests for word packs loading and discovery."""
from typing_buddy.packs import (
    get_enabled_pack_wordlists,
    get_non_english_pack_words,
    get_pack_info,
    list_available_packs,
)


def test_list_available_packs():
    packs = list_available_packs()
    pack_names = {p["name"] for p in packs}
    assert "en-basic" in pack_names
    assert "en-large" in pack_names
    assert "hinglish" in pack_names


def test_get_pack_info():
    info = get_pack_info("en-basic")
    assert info is not None
    assert info["name"] == "en-basic"
    assert info["word_count"] == 5000
    assert info["language"] == "en"


def test_get_enabled_pack_wordlists():
    paths = get_enabled_pack_wordlists(["en-basic", "hinglish"])
    assert len(paths) == 2
    assert all(p.exists() for p in paths)


def test_get_non_english_pack_words():
    words = get_non_english_pack_words(["en-basic", "hinglish"])
    assert len(words) > 0
    # en-basic words should not be included
    # hinglish words like 'bhai', 'hai' should be present
    assert "hai" in words
    assert "bhai" in words
