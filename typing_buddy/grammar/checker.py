"""checker.py - Grammar checker interfaces, Issue data structure, and NullChecker."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Issue:
    """A grammar lint issue found in typed text."""
    start: int
    end: int
    kind: str
    rule: str
    message: str
    replacements: List[str] = field(default_factory=list)


class GrammarChecker(ABC):
    """Abstract interface for offline grammar engines."""

    @abstractmethod
    def check(self, text: str) -> List[Issue]:
        """Analyze text and return grammar issues."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """True if the underlying engine is installed and ready."""
        pass


class NullChecker(GrammarChecker):
    """Fallback checker used when Harper is not installed or disabled."""

    def check(self, text: str) -> List[Issue]:
        return []

    def is_available(self) -> bool:
        return False


def filter_issues_near_end(issues: List[Issue], text: str, max_words_back: int = 3) -> List[Issue]:
    """Only keep issues whose span ends inside the last max_words_back words of text."""
    if not issues or not text:
        return []

    # Find character boundary for the last N words
    # Split text into tokens and track indices
    words = text.split()
    if not words:
        return []

    # If sentence has fewer than 2 words, skip (prevents partial false alarms)
    if len(words) < 2:
        return []

    # Find start position of the target_words block from the right
    # To be safe, find start index of the Nth word from the end
    word_start_idx = 0
    words_from_end = 0
    in_word = False
    for i in range(len(text) - 1, -1, -1):
        ch = text[i]
        if not ch.isspace() and not in_word:
            in_word = True
            words_from_end += 1
            if words_from_end >= max_words_back:
                word_start_idx = i
                break
        elif ch.isspace():
            in_word = False

    near_end = []
    text_len = len(text)
    for issue in issues:
        # Span must lie entirely inside text and end after word_start_idx
        if 0 <= issue.start < issue.end <= text_len:
            if issue.end >= word_start_idx and issue.replacements:
                near_end.append(issue)

    return near_end


def compute_replacement_action(issue: Issue, text: str, max_tail_len: int = 40) -> Optional[Tuple[int, str]]:
    """Compute (backspaces, retype_text) for applying a grammar replacement.

    Returns None if the tail is too long (> max_tail_len) or invalid.
    """
    if not (0 <= issue.start < issue.end <= len(text)):
        return None
    if not issue.replacements:
        return None

    tail = text[issue.start:]
    if len(tail) > max_tail_len:
        return None

    num_backspaces = len(tail)
    best_replacement = issue.replacements[0]
    remainder = text[issue.end:]
    retype_text = best_replacement + remainder

    return num_backspaces, retype_text
