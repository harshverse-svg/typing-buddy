"""test_stats.py - Unit tests for keystrokes-saved and pick statistics."""
import os
import tempfile

from stats import StatsTracker


def test_stats_recording_and_summary():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        path = f.name
    try:
        tracker = StatsTracker(path)
        # Type 'rec', pick 'receive' (len 7 - len 3 = 4 saved)
        tracker.record_pick(typed_len=3, picked_len=7, is_correction=False)
        # Correction pick
        tracker.record_pick(typed_len=5, picked_len=5, is_correction=True)
        tracker.save()

        summary = tracker.get_summary()
        today = summary["today"]
        assert today["keystrokes_saved"] == 4
        assert today["suggestions_picked"] == 1
        assert today["corrections_picked"] == 1
        assert summary["total"]["keystrokes_saved"] == 4
    finally:
        for p in (path, path + ".tmp"):
            if os.path.exists(p):
                os.remove(p)

