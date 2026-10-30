"""settings.py - Configuration management with validation and auto-reload."""
import copy
import json
import logging
import os
import threading
import time
from typing import Any, Dict

logger = logging.getLogger("typing_buddy.settings")

DEFAULT_SETTINGS: Dict[str, Any] = {
    "word_packs": ["en-basic"],
    "personal_word_file": "personal_words.txt",
    "min_prefix": 2,
    "max_suggestions": 3,
    "pick_keys": ["F2", "F3", "F4"],
    "tab_picks_first": True,
    "pause_key": "pause",
    "new_word_mode": "review",  # "review" (default), "auto", or "off"
    "auto_add_new_words": False,  # Kept in sync with new_word_mode == "auto" for backward compatibility
    "new_word_min_count": 3,
    "new_word_freq": 120,
    "learn_ranking": True,
    "length_bonus": 0.02,
    "autocorrect_mode": "suggest",  # "suggest" or "off"
    "fuzzy_enabled": True,
    "blocked_apps": ["keepass.exe", "1password.exe", "bitwarden.exe"],
    "blocked_title_words": ["password"],
    "popup_font_size": 12,
    "popup_opacity": 0.95,
    "popup_click_to_pick": True,
    "auto_capitalize": "off",  # "off" or "suggest"
    "remove_last_added_hotkey": "",
    "date_format": "%Y-%m-%d",
    "time_format": "%H:%M",
    "grammar_enabled": True,
    "grammar_lint_kinds": ["Agreement", "Repetition", "WordChoice", "Usage", "Miscellaneous"],
    "grammar_ignored_rules": [],
    "grammar_dialect": "american",
    "grammar_max_words_back": 3,
    "grammar_show_reason": True,
}

VALID_PICK_KEYS = {f"f{i}": f"F{i}" for i in range(1, 13)}
VALID_PICK_KEYS["tab"] = "Tab"
VALID_F_KEYS = VALID_PICK_KEYS  # Backward compatibility alias
VALID_DIALECTS = {"american", "british", "australian", "canadian", "indian"}


def validate_settings(raw: dict) -> dict:
    """Validate raw dictionary against expected types and ranges. Returns clean dictionary."""
    cleaned = copy.deepcopy(DEFAULT_SETTINGS)

    if not isinstance(raw, dict):
        logger.warning("Settings content is not a JSON object. Using defaults.")
        return cleaned

    # word_packs: list of str
    if "word_packs" in raw:
        val = raw["word_packs"]
        if isinstance(val, list) and all(isinstance(x, str) and x.strip() for x in val):
            cleaned["word_packs"] = [x.strip() for x in val]
        else:
            logger.warning("Invalid 'word_packs'. Must be list of strings. Using default.")

    # personal_word_file: str
    if "personal_word_file" in raw:
        val = raw["personal_word_file"]
        if isinstance(val, str) and val.strip():
            cleaned["personal_word_file"] = val.strip()

    # min_prefix: int 1..10
    if "min_prefix" in raw:
        val = raw["min_prefix"]
        if isinstance(val, int) and 1 <= val <= 10:
            cleaned["min_prefix"] = val
        else:
            logger.warning("Invalid 'min_prefix'. Must be int between 1 and 10. Using default.")

    # max_suggestions: int 1..9
    if "max_suggestions" in raw:
        val = raw["max_suggestions"]
        if isinstance(val, int) and 1 <= val <= 9:
            cleaned["max_suggestions"] = val
        else:
            logger.warning("Invalid 'max_suggestions'. Must be int between 1 and 9. Using default.")

    # pick_keys: list of F1..F12 and Tab, no duplicates
    if "pick_keys" in raw:
        val = raw["pick_keys"]
        if isinstance(val, list) and 1 <= len(val) <= 13:
            canonical = []
            seen = set()
            valid = True
            for k in val:
                if isinstance(k, str) and k.strip().lower() in VALID_PICK_KEYS:
                    norm = VALID_PICK_KEYS[k.strip().lower()]
                    if norm in seen:
                        valid = False
                        break
                    seen.add(norm)
                    canonical.append(norm)
                else:
                    valid = False
                    break
            if valid and len(canonical) >= cleaned["max_suggestions"]:
                cleaned["pick_keys"] = canonical
            else:
                logger.warning("Invalid 'pick_keys'. Using default.")
        else:
            logger.warning("Invalid 'pick_keys' format. Using default.")

    # tab_picks_first: bool
    if "tab_picks_first" in raw and isinstance(raw["tab_picks_first"], bool):
        cleaned["tab_picks_first"] = raw["tab_picks_first"]

    # pause_key: str
    if "pause_key" in raw and isinstance(raw["pause_key"], str) and raw["pause_key"].strip():
        cleaned["pause_key"] = raw["pause_key"].strip().lower()

    # new_word_mode: "review", "auto", "off"
    if "new_word_mode" in raw and raw["new_word_mode"] in ("review", "auto", "off"):
        cleaned["new_word_mode"] = raw["new_word_mode"]
    elif "auto_add_new_words" in raw:
        if raw["auto_add_new_words"] is False:
            cleaned["new_word_mode"] = "off"
        else:
            cleaned["new_word_mode"] = "review"
    else:
        if "new_word_mode" in raw:
            logger.warning("Invalid 'new_word_mode'. Must be 'review', 'auto', or 'off'. Using default.")

    # auto_add_new_words: backward compatibility sync with new_word_mode
    cleaned["auto_add_new_words"] = (cleaned["new_word_mode"] == "auto")

    # new_word_min_count: int >= 1
    if "new_word_min_count" in raw and isinstance(raw["new_word_min_count"], int) and raw["new_word_min_count"] >= 1:
        cleaned["new_word_min_count"] = raw["new_word_min_count"]

    # new_word_freq: int 1..250
    if "new_word_freq" in raw and isinstance(raw["new_word_freq"], int) and 1 <= raw["new_word_freq"] <= 250:
        cleaned["new_word_freq"] = raw["new_word_freq"]

    # learn_ranking: bool
    if "learn_ranking" in raw and isinstance(raw["learn_ranking"], bool):
        cleaned["learn_ranking"] = raw["learn_ranking"]

    # length_bonus: float 0.0..1.0
    if "length_bonus" in raw and isinstance(raw["length_bonus"], (int, float)) and 0.0 <= float(raw["length_bonus"]) <= 1.0:
        cleaned["length_bonus"] = float(raw["length_bonus"])

    # autocorrect_mode: "suggest" or "off"
    if "autocorrect_mode" in raw and raw["autocorrect_mode"] in ("suggest", "off"):
        cleaned["autocorrect_mode"] = raw["autocorrect_mode"]

    # fuzzy_enabled: bool
    if "fuzzy_enabled" in raw and isinstance(raw["fuzzy_enabled"], bool):
        cleaned["fuzzy_enabled"] = raw["fuzzy_enabled"]

    # blocked_apps: list of str
    if "blocked_apps" in raw and isinstance(raw["blocked_apps"], list):
        cleaned["blocked_apps"] = [x.strip().lower() for x in raw["blocked_apps"] if isinstance(x, str) and x.strip()]

    # blocked_title_words: list of str
    if "blocked_title_words" in raw and isinstance(raw["blocked_title_words"], list):
        cleaned["blocked_title_words"] = [x.strip().lower() for x in raw["blocked_title_words"] if isinstance(x, str) and x.strip()]

    # popup_font_size: int 8..32
    if "popup_font_size" in raw and isinstance(raw["popup_font_size"], int) and 8 <= raw["popup_font_size"] <= 32:
        cleaned["popup_font_size"] = raw["popup_font_size"]

    # popup_opacity: float 0.1..1.0
    if "popup_opacity" in raw and isinstance(raw["popup_opacity"], (int, float)) and 0.1 <= float(raw["popup_opacity"]) <= 1.0:
        cleaned["popup_opacity"] = float(raw["popup_opacity"])

    # popup_click_to_pick: bool
    if "popup_click_to_pick" in raw and isinstance(raw["popup_click_to_pick"], bool):
        cleaned["popup_click_to_pick"] = raw["popup_click_to_pick"]

    # auto_capitalize: "off" or "suggest"
    if "auto_capitalize" in raw and raw["auto_capitalize"] in ("off", "suggest"):
        cleaned["auto_capitalize"] = raw["auto_capitalize"]

    # remove_last_added_hotkey: str
    if "remove_last_added_hotkey" in raw and isinstance(raw["remove_last_added_hotkey"], str):
        cleaned["remove_last_added_hotkey"] = raw["remove_last_added_hotkey"].strip()

    # date_format / time_format
    if "date_format" in raw and isinstance(raw["date_format"], str) and raw["date_format"]:
        cleaned["date_format"] = raw["date_format"]
    if "time_format" in raw and isinstance(raw["time_format"], str) and raw["time_format"]:
        cleaned["time_format"] = raw["time_format"]

    # Grammar settings
    if "grammar_enabled" in raw and isinstance(raw["grammar_enabled"], bool):
        cleaned["grammar_enabled"] = raw["grammar_enabled"]

    if "grammar_lint_kinds" in raw and isinstance(raw["grammar_lint_kinds"], list):
        cleaned["grammar_lint_kinds"] = [x.strip() for x in raw["grammar_lint_kinds"] if isinstance(x, str) and x.strip()]

    if "grammar_ignored_rules" in raw and isinstance(raw["grammar_ignored_rules"], list):
        cleaned["grammar_ignored_rules"] = [x.strip() for x in raw["grammar_ignored_rules"] if isinstance(x, str) and x.strip()]

    if "grammar_dialect" in raw and isinstance(raw["grammar_dialect"], str):
        dia = raw["grammar_dialect"].strip().lower()
        if dia in VALID_DIALECTS:
            cleaned["grammar_dialect"] = dia

    if "grammar_max_words_back" in raw and isinstance(raw["grammar_max_words_back"], int) and 1 <= raw["grammar_max_words_back"] <= 10:
        cleaned["grammar_max_words_back"] = raw["grammar_max_words_back"]

    if "grammar_show_reason" in raw and isinstance(raw["grammar_show_reason"], bool):
        cleaned["grammar_show_reason"] = raw["grammar_show_reason"]

    return cleaned


class Settings:
    """Thread-safe application settings manager with file watching."""

    def __init__(self, path: str = "settings.json"):
        self.path = os.path.abspath(path)
        self.lock = threading.RLock()
        self._data = copy.deepcopy(DEFAULT_SETTINGS)
        self._last_mtime = 0
        self._callbacks = []
        self._watcher_stop = threading.Event()
        self._watcher_thread = None

        self.load(create_if_missing=True)

    def load(self, create_if_missing: bool = False):
        with self.lock:
            if not os.path.exists(self.path):
                if create_if_missing:
                    self._save_default()
                else:
                    return
            try:
                mtime = os.path.getmtime(self.path)
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._data = validate_settings(raw)
                self._last_mtime = mtime
                logger.info("Settings loaded from %s", self.path)
            except Exception as e:
                logger.warning("Failed to load settings from %s: %s", self.path, e)

    def _save_default(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SETTINGS, f, indent=2)
            self._last_mtime = os.path.getmtime(self.path)
            logger.info("Created default settings file at %s", self.path)
        except OSError as e:
            logger.warning("Failed to create default settings file: %s", e)

    def save(self):
        with self.lock:
            tmp = self.path + ".tmp"
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2)
                os.replace(tmp, self.path)
                self._last_mtime = os.path.getmtime(self.path)
            except OSError as e:
                logger.error("Failed to save settings to %s: %s", self.path, e)

    def set_value(self, key: str, value: Any):
        with self.lock:
            self._data[key] = value
            self.save()
            self._notify()

    def reload(self):
        self.load(create_if_missing=False)
        self._notify()

    def add_change_callback(self, cb):
        with self.lock:
            self._callbacks.append(cb)

    def _notify(self):
        snapshot = self.get_all()
        for cb in self._callbacks:
            try:
                cb(snapshot)
            except Exception as e:
                logger.exception("Error in settings change callback: %s", e)

    def get_all(self) -> dict:
        with self.lock:
            return copy.deepcopy(self._data)

    def __getattr__(self, name):
        with self.lock:
            if name in self._data:
                return self._data[name]
        raise AttributeError(f"'Settings' object has no attribute '{name}'")

    def __getitem__(self, item):
        with self.lock:
            return self._data[item]

    def start_watcher(self, interval: float = 2.0):
        if self._watcher_thread and self._watcher_thread.is_alive():
            return

        def _watch():
            while not self._watcher_stop.is_set():
                time.sleep(interval)
                try:
                    if os.path.exists(self.path):
                        mtime = os.path.getmtime(self.path)
                        if mtime != self._last_mtime:
                            self.load(create_if_missing=False)
                            self._notify()
                except Exception as e:
                    logger.debug("Error checking settings mtime: %s", e)

        self._watcher_stop.clear()
        self._watcher_thread = threading.Thread(target=_watch, daemon=True, name="SettingsWatcher")
        self._watcher_thread.start()

    def stop_watcher(self):
        self._watcher_stop.set()
