"""tracker.py - In-memory RAM-only typed text tracker for sentence grammar context.

Privacy invariant:
This text is kept in volatile RAM only. It is NEVER written to disk, NEVER logged,
and NEVER exposed in error messages. It is immediately cleared on any unmodeled
keystroke, navigation, shortcut, mouse click, or pause event.
"""
import threading


class TextTracker:
    """Tracks recently typed sentence text in RAM with versioning for stale checks."""

    def __init__(self, max_chars: int = 300):
        self._max_chars = max_chars
        self._lock = threading.RLock()
        self._buffer = []
        self._version = 0

    @property
    def version(self) -> int:
        with self._lock:
            return self._version

    def get_text(self) -> str:
        """Return a copy of the current buffered sentence text."""
        with self._lock:
            return "".join(self._buffer)

    def append_char(self, ch: str):
        """Append a printable character or space."""
        if not ch:
            return
        with self._lock:
            self._buffer.append(ch)
            if len(self._buffer) > self._max_chars:
                # Drop oldest characters when over cap
                excess = len(self._buffer) - self._max_chars
                self._buffer = self._buffer[excess:]
            self._version += 1

    def handle_backspace(self):
        """Remove last character if buffer not empty."""
        with self._lock:
            if self._buffer:
                self._buffer.pop()
                self._version += 1

    def clear(self):
        """Clear all buffered text. Must be called on unmodeled keys, navigation, mouse clicks, and pause."""
        with self._lock:
            if self._buffer:
                self._buffer.clear()
                self._version += 1

    def start_new_sentence(self):
        """Start a new sentence after sentence terminator (. ! ?) + space or Enter."""
        with self._lock:
            self._buffer.clear()
            self._version += 1

    def word_count(self) -> int:
        """Count words in the current buffer."""
        with self._lock:
            text = "".join(self._buffer).strip()
            return len(text.split()) if text else 0

    def get_snapshot(self) -> tuple[str, int]:
        """Atomically return (text, version)."""
        with self._lock:
            return "".join(self._buffer), self._version

