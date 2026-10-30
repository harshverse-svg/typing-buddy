"""harper_adapter.py - Adapter for the Harper offline grammar checking engine."""
import logging
from typing import List, Optional

from .checker import GrammarChecker, Issue

logger = logging.getLogger("typing_buddy.grammar")

DEFAULT_LINT_KINDS = {"agreement", "wordchoice", "usage", "repetition", "miscellaneous"}


class HarperChecker(GrammarChecker):
    """Offline rule-based grammar checker using harper-py."""

    def __init__(
        self,
        lint_kinds: Optional[List[str]] = None,
        ignored_rules: Optional[List[str]] = None,
        dialect: str = "american",
        custom_words: Optional[List[str]] = None,
    ):
        self.lint_kinds = {k.lower() for k in (lint_kinds or DEFAULT_LINT_KINDS)}
        self.ignored_rules = {r.lower() for r in (ignored_rules or [])}
        self.dialect_str = (dialect or "american").lower()
        self.custom_words = list(custom_words or [])
        self._linter = None
        self._available = False

        self._init_engine()

    def _init_engine(self):
        try:
            import harper
            self._linter = harper.Linter()

            # Set dialect
            dialect_map = {
                "american": harper.Dialect.AMERICAN,
                "british": harper.Dialect.BRITISH,
                "australian": harper.Dialect.AUSTRALIAN,
                "canadian": harper.Dialect.CANADIAN,
                "indian": harper.Dialect.INDIAN,
            }
            chosen_dialect = dialect_map.get(self.dialect_str, harper.Dialect.AMERICAN)
            # Try setting dialect if supported on Linter
            try:
                if hasattr(self._linter, "set_dialect"):
                    self._linter.set_dialect(chosen_dialect)
            except Exception:
                pass

            # Disable SpellCheck and Misspell so Harper only checks grammar
            cfg = self._linter.get_lint_config()
            cfg["SpellCheck"] = False
            cfg["Misspell"] = False
            self._linter.set_lint_config(cfg)

            # Seed user dictionary with personal and non-English words
            if self.custom_words:
                try:
                    self._linter.import_words(self.custom_words)
                except Exception as e:
                    logger.debug("Failed to import custom words to Harper: %s", e)

            self._available = True
            logger.info("Harper grammar engine initialized successfully (dialect=%s).", self.dialect_str)
        except ImportError:
            logger.warning("harper-py is not installed. Grammar suggestions will be disabled.")
            self._available = False
        except Exception as e:
            logger.warning("Failed to initialize Harper grammar engine: %s", e)
            self._available = False

    def is_available(self) -> bool:
        return self._available and (self._linter is not None)

    def check(self, text: str) -> List[Issue]:
        """Analyze text and return filtered grammatical issues."""
        if not self.is_available() or not text:
            return []

        try:
            raw_lints = self._linter.lint(text)
        except Exception as e:
            logger.debug("Error during Harper linting: %s", e)
            return []

        issues = []
        for lint in raw_lints:
            kind_str = str(getattr(lint, "lint_kind", "")).lower()

            # 1. Strictly exclude spelling lints
            if "spell" in kind_str:
                continue

            # 2. Check allowed lint kinds
            if self.lint_kinds and kind_str not in self.lint_kinds:
                continue

            # 3. Check ignored rules
            msg = str(getattr(lint, "message", ""))
            rule_id = kind_str
            if rule_id in self.ignored_rules:
                continue

            # Extract replacements
            replacements = []
            suggestions = getattr(lint, "suggestions", [])
            for s in suggestions:
                rep = getattr(s, "replacement_text", "")
                if rep and rep not in replacements:
                    replacements.append(rep)

            if not replacements:
                continue

            span = getattr(lint, "span", None)
            if not span:
                continue

            start = getattr(span, "start", 0)
            end = getattr(span, "end", 0)
            if start < 0 or end <= start or end > len(text):
                continue

            issues.append(
                Issue(
                    start=start,
                    end=end,
                    kind=getattr(lint, "lint_kind", "Grammar"),
                    rule=rule_id,
                    message=msg,
                    replacements=replacements,
                )
            )

        return issues
