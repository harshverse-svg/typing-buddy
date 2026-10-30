"""snippets.py - Text shortcuts / snippet expansion.

Features:
- Map short trigger words to expanded text (e.g. "addr" -> "123 Example Street").
- Dynamic placeholders: {date} and {time}.
- Short single-line snippets (<= 200 chars) are typed directly.
- Multi-line or long snippets (> 200 chars) are inserted via clipboard paste (Ctrl+V)
  to avoid sending messages via Enter in chat applications.
- Clipboard save and restore.
- Snippets are NEVER learned from or logged.
"""
import datetime
import json
import logging
import os
import threading
from typing import Optional

logger = logging.getLogger("typing_buddy.snippets")

DEFAULT_SNIPPETS = {
    "addr": "123 Example Street, Springfield",
    "sig": "Best regards,\nYour Name",
    "today": "Today is {date}",
    "now": "Current time: {time}"
}


class SnippetsManager:
    """Manages trigger expansions with placeholder formatting."""

    def __init__(self, path: str = "snippets.json", date_format: str = "%Y-%m-%d",
                 time_format: str = "%H:%M", create_if_missing: bool = True):
        self.path = os.path.abspath(path)
        self.date_format = date_format
        self.time_format = time_format
        self.lock = threading.RLock()
        self.snippets = {}
        self.load(create_if_missing=create_if_missing)

    def load(self, create_if_missing: bool = True):
        with self.lock:
            if not os.path.exists(self.path):
                if create_if_missing:
                    try:
                        with open(self.path, "w", encoding="utf-8") as f:
                            json.dump(DEFAULT_SNIPPETS, f, indent=2)
                        self.snippets = dict(DEFAULT_SNIPPETS)
                        logger.info("Created default snippets at %s", self.path)
                    except OSError as e:
                        logger.warning("Could not create %s: %s", self.path, e)
                return
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    self.snippets = {k.lower().strip(): str(v) for k, v in raw.items()}
                logger.info("Loaded %d snippets from %s", len(self.snippets), self.path)
            except Exception as e:
                logger.warning("Error loading snippets from %s: %s", self.path, e)

    def update_formats(self, date_format: str, time_format: str):
        with self.lock:
            self.date_format = date_format
            self.time_format = time_format

    def get_expansion(self, trigger: str) -> Optional[str]:
        """Return formatted expansion for trigger, or None if trigger is not a snippet."""
        if not trigger:
            return None
        low = trigger.lower().strip()
        with self.lock:
            raw = self.snippets.get(low)
            if raw is None:
                return None

        # Format placeholders
        now = datetime.datetime.now()
        date_str = now.strftime(self.date_format)
        time_str = now.strftime(self.time_format)

        expanded = raw.replace("{date}", date_str).replace("{time}", time_str)
        return expanded

    @staticmethod
    def is_multiline_or_long(text: str) -> bool:
        """True if snippet exceeds 200 characters or contains newlines."""
        return len(text) > 200 or "\n" in text or "\r" in text

