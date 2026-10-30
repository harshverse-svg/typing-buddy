"""stats.py - Keystrokes-saved and usage statistics tracking.

Privacy rule: Stores ONLY numeric counts and dates. NEVER stores words or text.
"""
import datetime
import json
import logging
import os
import threading
from typing import Dict

logger = logging.getLogger("typing_buddy.stats")


class StatsTracker:
    """Thread-safe statistics tracker saving per-day numeric counters."""

    def __init__(self, path: str = "stats.json"):
        self.path = os.path.abspath(path)
        self.lock = threading.RLock()
        self.days: Dict[str, Dict[str, int]] = {}
        self._unsaved = 0
        self.load()

    def _today(self) -> str:
        return datetime.date.today().isoformat()

    def load(self):
        with self.lock:
            if not os.path.exists(self.path):
                self.days = {}
                return
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.days = data
            except Exception as e:
                logger.warning("Could not load stats from %s: %s", self.path, e)
                self.days = {}

    def save(self):
        tmp = self.path + ".tmp"
        try:
            with self.lock:
                snapshot = dict(self.days)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
            os.replace(tmp, self.path)
            self._unsaved = 0
        except OSError as e:
            logger.error("Failed to save stats to %s: %s", self.path, e)

    def record_pick(self, typed_len: int, picked_len: int, is_correction: bool = False):
        """Record a suggestion or correction pick. Keystrokes saved = picked_len - typed_len."""
        saved = max(0, picked_len - typed_len)
        today = self._today()
        with self.lock:
            if today not in self.days:
                self.days[today] = {
                    "keystrokes_saved": 0,
                    "suggestions_picked": 0,
                    "corrections_picked": 0
                }
            day_entry = self.days[today]
            day_entry["keystrokes_saved"] += saved
            if is_correction:
                day_entry["corrections_picked"] += 1
            else:
                day_entry["suggestions_picked"] += 1

            self._unsaved += 1
            if self._unsaved >= 5:
                self.save()

    def get_summary(self) -> Dict[str, Dict[str, int]]:
        """Return dict with stats for 'today', 'last_7_days', and 'total'."""
        today_str = self._today()
        today_date = datetime.date.today()
        seven_days_ago = today_date - datetime.timedelta(days=7)

        summary = {
            "today": {"keystrokes_saved": 0, "suggestions_picked": 0, "corrections_picked": 0},
            "last_7_days": {"keystrokes_saved": 0, "suggestions_picked": 0, "corrections_picked": 0},
            "total": {"keystrokes_saved": 0, "suggestions_picked": 0, "corrections_picked": 0}
        }

        with self.lock:
            for day_str, counts in self.days.items():
                saved = counts.get("keystrokes_saved", 0)
                sugg = counts.get("suggestions_picked", 0)
                corr = counts.get("corrections_picked", 0)

                # Total
                summary["total"]["keystrokes_saved"] += saved
                summary["total"]["suggestions_picked"] += sugg
                summary["total"]["corrections_picked"] += corr

                # Today
                if day_str == today_str:
                    summary["today"]["keystrokes_saved"] += saved
                    summary["today"]["suggestions_picked"] += sugg
                    summary["today"]["corrections_picked"] += corr

                # Last 7 days
                try:
                    d = datetime.date.fromisoformat(day_str)
                    if d >= seven_days_ago:
                        summary["last_7_days"]["keystrokes_saved"] += saved
                        summary["last_7_days"]["suggestions_picked"] += sugg
                        summary["last_7_days"]["corrections_picked"] += corr
                except ValueError:
                    pass

        return summary

