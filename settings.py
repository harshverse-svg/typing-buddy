"""settings.py - Configuration management with validation and auto-reload."""
import copy
import json
import logging
import os
import threading
import time

logger = logging.getLogger("predictor.settings")

DEFAULT_SETTINGS = {
    "word_files": ["words.txt", "words_main.txt"],
    "min_prefix": 2,
    "max_suggestions": 3,
    "pick_keys": ["F2", "F3", "F4"],
    "tab_picks_first": True,
    "pause_key": "pause",
    "auto_add_new_words": True,
    "new_word_min_count": 3,
    "new_word_freq": 120,
    "learn_ranking": True,
    "length_bonus": 0.02,
    "autocorrect_mode": "suggest",  # "suggest" or "off"
    "fuzzy_enabled": True,
    "blocked_apps": ["keepass.exe", "1password.exe", "bitwarden.exe", "enpass.exe"],
    "blocked_title_words": ["password"],
    "popup_font_size": 12,
    "popup_opacity": 0.95,
    "popup_click_to_pick": True,
    "auto_capitalize": "off",  # "off" or "suggest"
    "remove_last_added_hotkey": "",
    "date_format": "%Y-%m-%d",
    "time_format": "%H:%M",
}

VALID_F_KEYS = {f"f{i}": f"F{i}" for i in range(1, 13)}


def validate_settings(raw: dict) -> dict:
    """Validate raw dict against expected types and ranges. Returns a clean dict."""
    cleaned = copy.deepcopy(DEFAULT_SETTINGS)

    if not isinstance(raw, dict):
        logger.warning("Settings content is not a JSON object. Using defaults.")
        return cleaned

    # word_files: list of str, non-empty
    if "word_files" in raw:
        val = raw["word_files"]
        if isinstance(val, list) and len(val) > 0 and all(isinstance(x, str) and x.strip() for x in val):
            cleaned["word_files"] = [x.strip() for x in val]
        else:
            logger.warning("Invalid 'word_files'. Must be non-empty list of strings. Using default.")

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

    # pick_keys: list of F1..F12, no duplicates
    if "pick_keys" in raw:
        val = raw["pick_keys"]
        if isinstance(val, list) and 1 <= len(val) <= 12:
            canonical = []
            seen = set()
            valid = True
            for k in val:
                if isinstance(k, str) and k.strip().lower() in VALID_F_KEYS:
                    norm = VALID_F_KEYS[k.strip().lower()]
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
                logger.warning("Invalid 'pick_keys'. Must be unique F1-F12 keys of length >= max_suggestions. Using default.")
        else:
            logger.warning("Invalid 'pick_keys' format. Using default.")

    # tab_picks_first: bool
    if "tab_picks_first" in raw:
        val = raw["tab_picks_first"]
        if isinstance(val, bool):
            cleaned["tab_picks_first"] = val
        else:
            logger.warning("Invalid 'tab_picks_first'. Must be bool. Using default.")

    # pause_key: str
    if "pause_key" in raw:
        val = raw["pause_key"]
        if isinstance(val, str) and val.strip():
            cleaned["pause_key"] = val.strip().lower()
        else:
            logger.warning("Invalid 'pause_key'. Must be non-empty string. Using default.")

    # auto_add_new_words: bool
    if "auto_add_new_words" in raw:
        val = raw["auto_add_new_words"]
        if isinstance(val, bool):
            cleaned["auto_add_new_words"] = val
        else:
            logger.warning("Invalid 'auto_add_new_words'. Must be bool. Using default.")

    # new_word_min_count: int >= 1
    if "new_word_min_count" in raw:
        val = raw["new_word_min_count"]
        if isinstance(val, int) and val >= 1:
            cleaned["new_word_min_count"] = val
        else:
            logger.warning("Invalid 'new_word_min_count'. Must be int >= 1. Using default.")

    # new_word_freq: int 1..250
    if "new_word_freq" in raw:
        val = raw["new_word_freq"]
        if isinstance(val, int) and 1 <= val <= 250:
            cleaned["new_word_freq"] = val
        else:
            logger.warning("Invalid 'new_word_freq'. Must be int 1..250. Using default.")

    # learn_ranking: bool
    if "learn_ranking" in raw:
        val = raw["learn_ranking"]
        if isinstance(val, bool):
            cleaned["learn_ranking"] = val
        else:
            logger.warning("Invalid 'learn_ranking'. Must be bool. Using default.")

    # length_bonus: float 0.0..1.0
    if "length_bonus" in raw:
        val = raw["length_bonus"]
        if isinstance(val, (int, float)) and 0.0 <= float(val) <= 1.0:
            cleaned["length_bonus"] = float(val)
        else:
            logger.warning("Invalid 'length_bonus'. Must be float 0.0..1.0. Using default.")

    # autocorrect_mode: "suggest" or "off"
    if "autocorrect_mode" in raw:
        val = raw["autocorrect_mode"]
        if val in ("suggest", "off"):
            cleaned["autocorrect_mode"] = val
        else:
            logger.warning("Invalid 'autocorrect_mode'. Must be 'suggest' or 'off'. Using default.")

    # fuzzy_enabled: bool
    if "fuzzy_enabled" in raw:
        val = raw["fuzzy_enabled"]
        if isinstance(val, bool):
            cleaned["fuzzy_enabled"] = val
        else:
            logger.warning("Invalid 'fuzzy_enabled'. Must be bool. Using default.")

    # blocked_apps: list of str
    if "blocked_apps" in raw:
        val = raw["blocked_apps"]
        if isinstance(val, list) and all(isinstance(x, str) for x in val):
            cleaned["blocked_apps"] = [x.strip().lower() for x in val if x.strip()]
        else:
            logger.warning("Invalid 'blocked_apps'. Must be list of strings. Using default.")

    # blocked_title_words: list of str
    if "blocked_title_words" in raw:
        val = raw["blocked_title_words"]
        if isinstance(val, list) and all(isinstance(x, str) for x in val):
            cleaned["blocked_title_words"] = [x.strip().lower() for x in val if x.strip()]
        else:
            logger.warning("Invalid 'blocked_title_words'. Must be list of strings. Using default.")

    # popup_font_size: int 8..32
    if "popup_font_size" in raw:
        val = raw["popup_font_size"]
        if isinstance(val, int) and 8 <= val <= 32:
            cleaned["popup_font_size"] = val
        else:
            logger.warning("Invalid 'popup_font_size'. Must be int 8..32. Using default.")

    # popup_opacity: float 0.1..1.0
    if "popup_opacity" in raw:
        val = raw["popup_opacity"]
        if isinstance(val, (int, float)) and 0.1 <= float(val) <= 1.0:
            cleaned["popup_opacity"] = float(val)
        else:
            logger.warning("Invalid 'popup_opacity'. Must be float 0.1..1.0. Using default.")

    # popup_click_to_pick: bool
    if "popup_click_to_pick" in raw:
        val = raw["popup_click_to_pick"]
        if isinstance(val, bool):
            cleaned["popup_click_to_pick"] = val
        else:
            logger.warning("Invalid 'popup_click_to_pick'. Must be bool. Using default.")

    # auto_capitalize: "off" or "suggest"
    if "auto_capitalize" in raw:
        val = raw["auto_capitalize"]
        if val in ("off", "suggest"):
            cleaned["auto_capitalize"] = val
        else:
            logger.warning("Invalid 'auto_capitalize'. Must be 'off' or 'suggest'. Using default.")

    # remove_last_added_hotkey: str
    if "remove_last_added_hotkey" in raw:
        val = raw["remove_last_added_hotkey"]
        if isinstance(val, str):
            cleaned["remove_last_added_hotkey"] = val.strip()

    # date_format and time_format
    if "date_format" in raw and isinstance(raw["date_format"], str) and raw["date_format"]:
        cleaned["date_format"] = raw["date_format"]
    if "time_format" in raw and isinstance(raw["time_format"], str) and raw["time_format"]:
        cleaned["time_format"] = raw["time_format"]

    return cleaned


class Settings:
    """Thread-safe application settings manager with file watching."""

    def __init__(self, path="settings.json"):
        self.path = os.path.abspath(path)
        self.lock = threading.RLock()
        self._data = copy.deepcopy(DEFAULT_SETTINGS)
        self._last_mtime = 0
        self._callbacks = []
        self._watcher_stop = threading.Event()
        self._watcher_thread = None

        self.load(create_if_missing=True)

    def load(self, create_if_missing=False):
        """Load and validate settings from disk."""
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
                logger.warning("Failed to load settings from %s: %s. Keeping previous settings.", self.path, e)

    def _save_default(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SETTINGS, f, indent=2)
            self._last_mtime = os.path.getmtime(self.path)
            logger.info("Created default settings file at %s", self.path)
        except OSError as e:
            logger.warning("Failed to create default settings file: %s", e)

    def reload(self):
        """Force reload from disk and notify listeners."""
        self.load(create_if_missing=False)
        self._notify()

    def add_change_callback(self, cb):
        """Register a callback when settings change."""
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

    def start_watcher(self, interval=2.0):
        """Start background thread checking for settings.json mtime changes."""
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

