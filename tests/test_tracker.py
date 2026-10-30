"""test_tracker.py - Unit tests for RAM-only sentence text tracker."""
from typing_buddy.grammar import TextTracker


def test_tracker_append_and_backspace():
    tracker = TextTracker(max_chars=300)
    assert tracker.get_text() == ""
    assert tracker.version == 0

    tracker.append_char("H")
    tracker.append_char("i")
    assert tracker.get_text() == "Hi"
    assert tracker.version == 2

    tracker.handle_backspace()
    assert tracker.get_text() == "H"
    assert tracker.version == 3


def test_tracker_max_chars_cap():
    tracker = TextTracker(max_chars=10)
    for ch in "0123456789":
        tracker.append_char(ch)
    assert tracker.get_text() == "0123456789"

    tracker.append_char("A")
    # Oldest char '0' dropped
    assert tracker.get_text() == "123456789A"
    assert len(tracker.get_text()) == 10


def test_tracker_clear():
    tracker = TextTracker()
    tracker.append_char("a")
    tracker.append_char("b")
    v_before = tracker.version
    tracker.clear()
    assert tracker.get_text() == ""
    assert tracker.version == v_before + 1


def test_tracker_snapshot_and_word_count():
    tracker = TextTracker()
    for ch in "Hello world":
        tracker.append_char(ch)
    text, ver = tracker.get_snapshot()
    assert text == "Hello world"
    assert ver == 11
    assert tracker.word_count() == 2
