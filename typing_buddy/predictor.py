"""predictor.py - Fast word completion, next-word prediction, and vocabulary learning."""
import bisect
import datetime
import gzip
import heapq
import json
import logging
import os
import re
import threading
from collections import defaultdict
from typing import Callable, Dict, Optional, Set

logger = logging.getLogger("typing_buddy.predictor")
WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*")


def _open(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return open(path, "r", encoding="utf-8-sig", errors="ignore")


def _field_int(parts, key, default=1):
    for p in parts:
        if p.startswith(key + "="):
            try:
                return int(p[len(key) + 1:])
            except ValueError:
                pass
    return default


def load_wordlist(path):
    """Return (freq: {word: int}, bigrams: {prev: {next: int}})."""
    freq = {}
    bigrams = defaultdict(dict)
    last = None
    if not os.path.exists(path):
        return freq, bigrams
    try:
        with _open(path) as f:
            for line in f:
                raw = line.strip()
                if not raw or raw.startswith("#") or raw.startswith("dictionary="):
                    continue
                if raw.startswith("word="):            # .combined format
                    parts = raw.split(",")
                    w = parts[0][5:].lower()
                    if WORD_RE.fullmatch(w):
                        freq[w] = max(freq.get(w, 0), _field_int(parts[1:], "f"))
                        last = w
                    else:
                        last = None
                elif raw.startswith("bigram="):
                    if last:
                        parts = raw.split(",")
                        nxt = parts[0][7:].lower()
                        if WORD_RE.fullmatch(nxt):
                            bigrams[last][nxt] = _field_int(parts[1:], "f")
                elif "=" in raw:
                    continue
                else:                                  # plain "word [number]"
                    tokens = raw.split()
                    w = tokens[0].lower()
                    if not WORD_RE.fullmatch(w):
                        continue
                    fr = int(tokens[-1]) if len(tokens) > 1 and tokens[-1].isdigit() else 1
                    freq[w] = max(freq.get(w, 0), fr)
    except Exception as e:
        logger.warning("Error reading wordlist %s: %s", path, e)
    return freq, bigrams


class Predictor:
    # Default settings (can be updated from Settings)
    LENGTH_BONUS = 0.02          # favour longer words (set 0 to turn off)
    CACHE_K = 30                 # candidates cached per prefix
    AUTO_ADD_NEW_WORDS = False   # Legacy flag, kept in sync with new_word_mode == "auto"
    NEW_WORD_MODE = "review"     # "review" (default), "auto", or "off"
    NEW_WORD_MIN_COUNT = 3       # only after typing them this many times
    NEW_WORD_FREQ = 120          # number written next to an auto-added word
    LEARN_RANKING = True         # usage nudges ranking (user_data.json only)

    def __init__(
        self,
        paths,
        learn_file: Optional[str] = None,
        user_path="user_data.json",
        added_path="added_words.json",
        ignore_path="ignore_words.txt",
        new_word_mode: str = "review",
    ):
        if isinstance(paths, str):
            paths = [paths]
        self.paths = [str(p) for p in paths]
        self.lock = threading.RLock()
        self.freq: Dict[str, int] = {}
        self.bigrams = defaultdict(dict)
        self.user_path = str(user_path)
        self.added_path = str(added_path)
        self.ignore_path = str(ignore_path)
        self.new_word_mode = new_word_mode if new_word_mode in ("review", "auto", "off") else "review"
        self.AUTO_ADD_NEW_WORDS = (self.new_word_mode == "auto")

        # Extension point for context rankers
        self.ranker_hook: Optional[Callable[[str, Optional[str], int, float], float]] = None

        self.ignore_words: Set[str] = set()
        self._load_ignore_words()

        for p in self.paths:
            f, b = load_wordlist(p)
            for w, fr in f.items():
                if w not in self.ignore_words:
                    self.freq[w] = max(self.freq.get(w, 0), fr)
            for prev, d in b.items():
                self.bigrams[prev].update(d)

        self.maxf = max(self.freq.values(), default=1) or 1

        # Personal file that receives auto-added words (NEVER a pack file)
        if learn_file:
            self.learn_file = str(learn_file)
        else:
            self.learn_file = next(
                (p for p in self.paths if not p.endswith(".gz") and not p.endswith(".combined")),
                None,
            )

        self.last_auto_added_word: Optional[str] = None
        self.uni = defaultdict(int)
        self.bi = defaultdict(lambda: defaultdict(int))
        self.pending = {}
        self._unsaved = 0
        self._load_user()
        self.keys = sorted(set(self.freq) | set(self.uni))
        self._cache = {}

    def _load_ignore_words(self):
        self.ignore_words.clear()
        if os.path.exists(self.ignore_path):
            try:
                with open(self.ignore_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                    for line in f:
                        w = line.strip().lower()
                        if w and not w.startswith("#"):
                            self.ignore_words.add(w)
            except OSError as e:
                logger.warning("Could not load ignore list: %s", e)

    def prewarm(self):
        """Precompute candidate completions for 2- and 3-letter prefixes."""
        with self.lock:
            keys = list(self.keys)
        for L in (2, 3):
            groups = defaultdict(list)
            for w in keys:
                if len(w) > L:
                    groups[w[:L]].append(w)
            for p, ws in groups.items():
                if p not in self._cache:
                    self._cache[p] = self._top(ws, len(p))

    def _static(self, w, plen):
        s = self.freq.get(w, 0) / self.maxf
        if plen:
            s += self.LENGTH_BONUS * min(max(len(w) - plen, 0), 8)
        return s

    def _top(self, words, plen):
        return heapq.nlargest(self.CACHE_K, words, key=lambda w: self._static(w, plen))

    def _score(self, w, prev, plen):
        s = self._static(w, plen)
        if self.LEARN_RANKING:
            s += 1.5 * min(self.uni.get(w, 0), 20) / 20
        if prev:
            if self.LEARN_RANKING:
                s += 2.0 * min(self.bi.get(prev, {}).get(w, 0), 10) / 10
            s += 1.0 * self.bigrams.get(prev, {}).get(w, 0) / self.maxf
        if self.ranker_hook:
            try:
                s = self.ranker_hook(w, prev, plen, s)
            except Exception:
                pass
        return s

    @staticmethod
    def _match_case(w, prefix):
        if len(prefix) > 1 and prefix.isupper():
            return w.upper()
        if prefix[:1].isupper():
            return w.capitalize()
        return w

    def suggest(self, prefix, prev=None, n=3):
        """Completions for prefix, or next-word guesses if prefix is empty."""
        p = prefix.lower()
        plen = len(p)
        with self.lock:
            if p:
                top = self._cache.get(p)
                if top is None:
                    lo = bisect.bisect_left(self.keys, p)
                    hi = bisect.bisect_left(self.keys, p + "\U0010ffff")
                    top = self._top(self.keys[lo:hi], plen)
                    self._cache[p] = top
                cands = dict.fromkeys(w for w in top if w != p and w not in self.ignore_words)
                if self.LEARN_RANKING:
                    for w in self.uni:
                        if w.startswith(p) and w != p and w not in self.ignore_words:
                            cands[w] = None
                if prev:
                    for d in (self.bi.get(prev, {}), self.bigrams.get(prev, {})):
                        for w in d:
                            if w.startswith(p) and w != p and w not in self.ignore_words:
                                cands[w] = None
            elif prev:
                cands = dict.fromkeys(w for w in self.bi.get(prev, {}) if w not in self.ignore_words)
                cands.update(dict.fromkeys(w for w in self.bigrams.get(prev, {}) if w not in self.ignore_words))
            else:
                return []
            best = heapq.nlargest(n, cands, key=lambda w: self._score(w, prev, plen))
        return [self._match_case(w, prefix) for w in best]

    def is_known_word(self, word: Optional[str]) -> bool:
        """Return True if word is in active wordlist dictionaries or personal word file."""
        if not word:
            return False
        return word.strip().lower() in self.freq

    def learn(self, word, prev=None):
        """Learn usage counts for known words and handle new vocabulary learning.

        - In 'review' mode (default): after being typed NEW_WORD_MIN_COUNT times,
          an unknown word is queued in added_words.json for user approval. Nothing
          is written to personal_words.txt automatically.
        - In 'auto' mode: after NEW_WORD_MIN_COUNT times, it is auto-added to personal_words.txt.
        - In 'off' mode: unknown words are completely ignored.
        - Pending counters for unknown words are kept in-memory only.
        - Word pairs (bigrams) are only stored when BOTH words are already known words.
        """
        if not (2 <= len(word) <= 25) or not WORD_RE.fullmatch(word):
            return
        w_low = word.lower()
        with self.lock:
            if w_low in self.ignore_words:
                return

            # Handle unknown words
            if not self.is_known_word(w_low):
                if self.new_word_mode == "off":
                    return
                n = self.pending.get(w_low, 0) + 1
                if n < self.NEW_WORD_MIN_COUNT:
                    self.pending[w_low] = n
                    # In-memory only: do not mark dirty or save to disk
                    return
                # Reached threshold
                self.pending.pop(w_low, None)
                if self.new_word_mode == "auto":
                    self._add_word(w_low)
                elif self.new_word_mode == "review":
                    self._queue_for_review(w_low)
                return

            # Known word: update ranking
            if self.LEARN_RANKING:
                self.uni[w_low] += 1
                # Word pairs: store a pair only when BOTH words are already known words.
                # Never use an unknown word as a key or value.
                if prev and self.is_known_word(prev):
                    p_low = prev.lower()
                    self.bi[p_low][w_low] += 1
                self._dirty()

    def _queue_for_review(self, word):
        """Queue an unknown word for user review in added_words.json without adding to personal_words.txt."""
        self._record_added_word(word)
        logger.info("Queued unknown word for user review: %s", word)

    def keep_word(self, word):
        """Approve a word from the review queue: add to personal word file and active dictionary."""
        w = word.strip().lower()
        with self.lock:
            if w in self.ignore_words:
                self.ignore_words.remove(w)
            self._add_word(w)
            self.save()

    def _add_word(self, word):
        self.freq[word] = self.NEW_WORD_FREQ
        bisect.insort(self.keys, word)
        for i in range(1, len(word) + 1):
            self._cache.pop(word[:i], None)

        self.last_auto_added_word = word
        self._record_added_word(word)

        if not self.learn_file:
            return
        try:
            need_nl = False
            if os.path.exists(self.learn_file) and os.path.getsize(self.learn_file):
                with open(self.learn_file, "rb") as f:
                    f.seek(-1, os.SEEK_END)
                    need_nl = f.read(1) != b"\n"
            with open(self.learn_file, "a", encoding="utf-8") as f:
                if need_nl:
                    f.write("\n")
                f.write(f"{word}\t{self.NEW_WORD_FREQ}\n")
            logger.info("Added new word to %s: %s", self.learn_file, word)
        except OSError as e:
            logger.error("Could not add word to file: %s", e)

    def _record_added_word(self, word):
        try:
            records = []
            if os.path.exists(self.added_path):
                with open(self.added_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            records.append({"word": word, "date": now})
            tmp = self.added_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            os.replace(tmp, self.added_path)
        except Exception as e:
            logger.warning("Failed to record added word to %s: %s", self.added_path, e)

    def remove_word(self, word):
        """Delete word from personal word file, in-memory list, cache, and add to ignore list."""
        w = word.strip().lower()
        with self.lock:
            self.freq.pop(w, None)
            self.uni.pop(w, None)
            self.pending.pop(w, None)
            if w in self.keys:
                self.keys.remove(w)
            for i in range(1, len(w) + 1):
                self._cache.pop(w[:i], None)

            self.ignore_words.add(w)
            try:
                with open(self.ignore_path, "a", encoding="utf-8") as f:
                    f.write(f"{w}\n")
            except OSError as e:
                logger.error("Could not append to %s: %s", self.ignore_path, e)

            try:
                if os.path.exists(self.added_path):
                    with open(self.added_path, "r", encoding="utf-8") as f:
                        records = json.load(f)
                    records = [r for r in records if r.get("word") != w]
                    tmp = self.added_path + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(records, f, indent=2)
                    os.replace(tmp, self.added_path)
            except Exception as e:
                logger.warning("Could not update %s: %s", self.added_path, e)

            if self.learn_file and os.path.exists(self.learn_file):
                try:
                    with open(self.learn_file, "r", encoding="utf-8-sig", errors="ignore") as f:
                        lines = f.readlines()
                    filtered = []
                    removed = False
                    for line in lines:
                        tokens = line.strip().split()
                        if tokens and tokens[0].lower() == w and not removed:
                            removed = True
                            continue
                        filtered.append(line)
                    tmp = self.learn_file + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        f.writelines(filtered)
                    os.replace(tmp, self.learn_file)
                    logger.info("Removed %s from %s", w, self.learn_file)
                except OSError as e:
                    logger.error("Could not rewrite %s: %s", self.learn_file, e)

            self.save()

    def remove_last_added(self) -> Optional[str]:
        """Remove the most recently auto-added word."""
        if self.last_auto_added_word:
            w = self.last_auto_added_word
            self.remove_word(w)
            self.last_auto_added_word = None
            return w
        return None

    def _dirty(self):
        self._unsaved += 1
        if self._unsaved >= 50:
            self.save()

    def _load_user(self):
        try:
            with open(self.user_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Only load frequency counts for known words
            for w, c in data.get("uni", {}).items():
                if self.is_known_word(w) and isinstance(c, int):
                    self.uni[w] = c
            # Only load word pairs where BOTH words are known words
            for p, d in data.get("bi", {}).items():
                if self.is_known_word(p) and isinstance(d, dict):
                    for nxt, c in d.items():
                        if self.is_known_word(nxt) and isinstance(c, int):
                            self.bi[p][nxt] = c
        except (OSError, ValueError):
            pass

    def save(self):
        tmp = self.user_path + ".tmp"
        try:
            with self.lock:
                data = {
                    "uni": dict(self.uni),
                    "bi": {k: dict(v) for k, v in self.bi.items()},
                }
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, self.user_path)
            self._unsaved = 0
        except OSError as e:
            logger.error("Could not save user data: %s", e)

    def reset_user_data(self):
        with self.lock:
            self.uni.clear()
            self.bi.clear()
            self.pending.clear()
        try:
            os.remove(self.user_path)
        except OSError:
            pass
