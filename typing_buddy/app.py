"""app.py - Main application runtime, thread wiring, and event loops for typing-buddy."""
import argparse
import logging
import os
import queue
import sys
import threading
import time
import tkinter as tk
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from pynput import keyboard, mouse

from . import __version__, winapi
from .data_dir import init_user_data_files, resolve_data_dir
from .fuzzy import FuzzyEngine
from .grammar import (
    GrammarChecker,
    HarperChecker,
    NullChecker,
    TextTracker,
    compute_replacement_action,
    filter_issues_near_end,
)
from .overlay import Overlay
from .packs import get_enabled_pack_wordlists, get_non_english_pack_words, list_available_packs
from .predictor import Predictor
from .review_window import ReviewWindow, show_about_dialog, show_statistics_window
from .settings import Settings
from .snippets import SnippetsManager
from .stats import StatsTracker
from .tray import SystemTray

logger = logging.getLogger("typing_buddy")

# Virtual key constants
F_KEY_MAP = {f"f{i}": 0x6F + i for i in range(1, 13)}
VK_TAB = 0x09
WM_KEYDOWN, WM_SYSKEYDOWN = 0x0100, 0x0104
LLKHF_INJECTED = 0x10

MODS = {
    keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
    keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
    keyboard.Key.alt_gr, keyboard.Key.cmd, keyboard.Key.cmd_l,
    keyboard.Key.cmd_r
}


class State:
    def __init__(self):
        self.word = ""          # current word buffer
        self.prev = None        # previous finished word
        self.sentence_start = True
        self.punct_pending = False

        self.suggestions = []
        self.current_reason = None
        self.paused = False         # manual pause
        self.auto_paused = False    # automatic pause
        self.auto_pause_reason = ""
        self.injected = False
        self.mods = set()
        self.last_foreground_hwnd = 0

        # Post-space spelling or auto-capitalize correction: (original, replacement, expire_time)
        self.pending_correction = None

        # Active snippet expansion: (trigger, expansion)
        self.active_snippet = None

        # Active grammar issue: (issue, num_backspaces, retype_text, expire_time, snapshot_version)
        self.active_grammar = None


state = State()
ui_q = queue.Queue()       # -> popup window
job_q = queue.Queue()      # -> insert worker
req_q = queue.Queue()      # -> engine thread (learn / suggest)
grammar_q = queue.Queue()  # -> grammar worker thread

predictor: Optional[Predictor] = None
fuzzy_engine: Optional[FuzzyEngine] = None
grammar_checker: Optional[GrammarChecker] = None
text_tracker = TextTracker(max_chars=300)
overlay: Optional[Overlay] = None
listener: Optional[keyboard.Listener] = None
tray: Optional[SystemTray] = None
settings: Optional[Settings] = None
snippets_mgr: Optional[SnippetsManager] = None
stats_tracker: Optional[StatsTracker] = None
data_directory: Path = Path()

PICK_KEYS = {}


def is_active():
    return not (state.paused or state.auto_paused)


def build_pick_key_map(pick_keys_list):
    mapping = {}
    for idx, k_str in enumerate(pick_keys_list):
        vk = F_KEY_MAP.get(k_str.strip().lower())
        if vk is not None:
            mapping[vk] = idx
    return mapping


def refresh():
    """Request suggestions from engine thread or refresh active items."""
    if not is_active():
        state.suggestions = []
        state.current_reason = None
        state.pending_correction = None
        state.active_snippet = None
        state.active_grammar = None
        ui_q.put(("hide", None))
        return

    # 1. Check snippet trigger
    if state.word and snippets_mgr:
        expansion = snippets_mgr.get_expansion(state.word)
        if expansion:
            state.active_snippet = (state.word, expansion)
            state.active_grammar = None
            state.pending_correction = None
            display_snip = expansion.replace("\n", " ").strip()
            if len(display_snip) > 28:
                display_snip = display_snip[:25] + "..."
            sugg = [f"⚡ {display_snip}"]
            state.suggestions = sugg
            state.current_reason = None
            ui_q.put(("show", (sugg, None)))
            return
        else:
            state.active_snippet = None

    # 2. Check post-space correction/capitalize
    if state.pending_correction:
        orig, corr, exp_time = state.pending_correction
        if time.time() < exp_time:
            state.suggestions = [corr]
            state.current_reason = None
            ui_q.put(("show", ([corr], None)))
            return
        else:
            state.pending_correction = None

    # 3. Check active grammar issue
    if state.active_grammar:
        issue, n_bs, retype, exp_time, snap_ver = state.active_grammar
        if time.time() < exp_time and snap_ver == text_tracker.version:
            disp_repl = issue.replacements[0]
            sugg = [f"✎ {disp_repl}"]
            reason = issue.message if (settings and settings.grammar_show_reason) else None
            state.suggestions = sugg
            state.current_reason = reason
            ui_q.put(("show", (sugg, reason)))
            return
        else:
            state.active_grammar = None

    # 4. Normal prefix suggestions
    min_p = settings.min_prefix if settings else 2
    if (0 < len(state.word) < min_p) or not (state.word or state.prev):
        state.suggestions = []
        state.current_reason = None
        ui_q.put(("hide", None))
        return

    req_q.put(("suggest", state.word, state.prev))


def reset(clear_prev=True):
    state.word = ""
    state.pending_correction = None
    state.active_snippet = None
    state.active_grammar = None
    text_tracker.clear()
    if clear_prev:
        state.prev = None
        state.sentence_start = False
    refresh()


def finish_word():
    w = state.word.lower().strip("'’-")
    if w and predictor:
        req_q.put(("learn", w, state.prev))
        state.prev = w
    state.word = ""


def engine():
    """Engine thread performing ranking, fuzzy lookups, and learning away from hook."""
    winapi.set_current_thread_low_priority()
    while True:
        try:
            jobs = [req_q.get()]
            while True:
                try:
                    jobs.append(req_q.get_nowait())
                except queue.Empty:
                    break

            latest = None
            for j in jobs:
                if j[0] == "learn":
                    if predictor:
                        predictor.learn(j[1], j[2])
                elif j[0] == "suggest":
                    latest = j

            if latest and is_active() and not state.active_snippet and not state.pending_correction and not state.active_grammar:
                _, word, prev = latest
                max_sugg = settings.max_suggestions if settings else 3
                sugg = predictor.suggest(word, prev, max_sugg) if predictor else []

                # While typing: fuzzy candidates if normal prefix results < max_sugg
                if settings and settings.fuzzy_enabled and fuzzy_engine and fuzzy_engine.is_ready:
                    if len(word) >= 3 and len(sugg) < max_sugg:
                        fuzzy_cands = fuzzy_engine.fuzzy_prefix(
                            word, existing_suggestions=sugg, n=max_sugg - len(sugg)
                        )
                        sugg.extend(fuzzy_cands)

                # Stale check
                if (word, prev) == (state.word, state.prev) and is_active() and not state.active_snippet and not state.active_grammar:
                    state.suggestions = sugg
                    state.current_reason = None
                    ui_q.put(("show", (sugg, None)) if sugg else ("hide", None))
        except Exception as e:
            logger.error("Error in engine loop: %s", e)


def grammar_worker():
    """Dedicated background thread checking grammar with debounce."""
    winapi.set_current_thread_low_priority()
    while True:
        try:
            item = grammar_q.get()
            # Coalesce requests: drain newer requests
            while True:
                try:
                    item = grammar_q.get_nowait()
                except queue.Empty:
                    break

            text_snapshot, ver = item
            # Debounce by 150 ms
            time.sleep(0.15)

            # Check if tracker changed during sleep
            if text_tracker.version != ver or not is_active():
                continue

            if not (settings and settings.grammar_enabled) or not grammar_checker or not grammar_checker.is_available():
                continue

            # Need at least 2 words
            if len(text_snapshot.split()) < 2:
                continue

            # Skip grammar if spelling correction or snippet is active
            if state.pending_correction or state.active_snippet or state.word:
                continue

            issues = grammar_checker.check(text_snapshot)
            max_back = settings.grammar_max_words_back if settings else 3
            near_issues = filter_issues_near_end(issues, text_snapshot, max_words_back=max_back)

            if near_issues and text_tracker.version == ver and is_active():
                best_issue = near_issues[-1]  # Most recent issue near end
                action = compute_replacement_action(best_issue, text_snapshot, max_tail_len=40)
                if action:
                    n_bs, retype = action
                    state.active_grammar = (best_issue, n_bs, retype, time.time() + 4.0, ver)
                    refresh()

        except Exception as e:
            logger.debug("Error in grammar worker: %s", e)


def pick_index(vk):
    if not is_active():
        return None

    idx = PICK_KEYS.get(vk)
    has_active_item = bool(state.word or state.pending_correction or state.active_snippet or state.active_grammar)
    if vk == VK_TAB and has_active_item and (settings and settings.tab_picks_first):
        idx = 0

    s = state.suggestions
    if idx is None or idx >= len(s):
        return None

    # Stale verification: suggestion must start with current word (or be snippet / correction / grammar)
    if state.word and not state.active_snippet and not state.pending_correction and not state.active_grammar:
        clean_s = s[idx].lstrip("~")
        if not clean_s.lower().startswith(state.word.lower()):
            if not s[idx].startswith("~"):
                return None

    return idx


# ---------------- keyboard hook ----------------
def win32_filter(msg, data):
    state.injected = bool(data.flags & LLKHF_INJECTED)
    if state.injected or msg not in (WM_KEYDOWN, WM_SYSKEYDOWN) or not is_active():
        return True

    idx = pick_index(data.vkCode)
    if idx is not None:
        kind = "normal"
        payload = None
        if state.active_snippet and idx == 0:
            kind = "snippet"
            payload = state.active_snippet
        elif state.pending_correction and idx == 0:
            kind = "correction"
            payload = state.pending_correction
        elif state.active_grammar and idx == 0:
            kind = "grammar"
            payload = state.active_grammar

        job_q.put((idx, kind, payload, state.word))
        listener.suppress_event()
    return True


def on_press(key):
    if state.injected:
        return

    # Check pause hotkey
    pause_key_name = str(settings.pause_key if settings else "pause").lower()
    is_pause = False
    if pause_key_name in ("pause", "break") and key == keyboard.Key.pause:
        is_pause = True

    if is_pause:
        state.paused = not state.paused
        logger.info("MANUAL PAUSE: %s", "PAUSED" if state.paused else "RESUMED")
        if tray:
            tray.set_state(state.paused, state.auto_paused)
        reset()
        return

    if not is_active():
        return

    if key in MODS:
        state.mods.add(key)
        return
    if state.mods:
        reset()
        return

    # Non-pick keystroke cancels pending corrections and grammar fixes
    state.pending_correction = None
    state.active_grammar = None

    ch = getattr(key, "char", None)
    if ch and ch.isprintable() and not ch.isspace():
        if ch.isalpha() or ch in "'’":
            state.word += ch
            state.punct_pending = False
            text_tracker.append_char(ch)
        else:
            finish_word()
            text_tracker.append_char(ch)
            if ch in ".!?":
                state.punct_pending = True
                state.prev = None
                grammar_q.put(text_tracker.get_snapshot())
            else:
                state.punct_pending = False
    elif key == keyboard.Key.space:
        finished = state.word.lower().strip("'’-")
        current_word_raw = state.word
        was_sentence_start = state.sentence_start
        finish_word()
        text_tracker.append_char(" ")

        # Update sentence_start
        if state.punct_pending:
            state.sentence_start = True
            state.punct_pending = False
            text_tracker.start_new_sentence()
        else:
            state.sentence_start = False

        # 1. Auto-capitalize check
        cap_candidate = None
        if settings and settings.auto_capitalize == "suggest" and finished:
            i_contractions = {"i": "I", "i'm": "I'm", "i'll": "I'll", "i'd": "I'd", "i've": "I've"}
            if finished in i_contractions and current_word_raw != i_contractions[finished]:
                cap_candidate = i_contractions[finished]
            elif was_sentence_start and current_word_raw and not current_word_raw[0].isupper():
                cap_candidate = current_word_raw.capitalize()

        if cap_candidate:
            state.pending_correction = (current_word_raw, cap_candidate, time.time() + 3.0)
        elif settings and settings.autocorrect_mode == "suggest" and settings.fuzzy_enabled and fuzzy_engine and fuzzy_engine.is_ready:
            # 2. Spelling correction check
            if len(finished) >= 4 and predictor and finished not in predictor.freq and finished not in predictor.uni:
                corrections = fuzzy_engine.correct_word(finished, learned_words=set(predictor.uni.keys()), n=1)
                if corrections:
                    state.pending_correction = (current_word_raw, corrections[0], time.time() + 3.0)

        # 3. Trigger grammar check after Space
        if not state.pending_correction:
            grammar_q.put(text_tracker.get_snapshot())

    elif key == keyboard.Key.backspace:
        text_tracker.handle_backspace()
        if state.word:
            state.word = state.word[:-1]
        else:
            state.prev = None
    elif key in (keyboard.Key.enter,):
        finish_word()
        state.prev = None
        state.sentence_start = True
        state.punct_pending = False
        text_tracker.start_new_sentence()
    else:
        # Navigation / arrows / delete / unmodeled keys: clear tracker
        finish_word()
        state.prev = None
        state.punct_pending = False
        text_tracker.clear()

    refresh()


def on_release(key):
    state.mods.discard(key)


def on_click(x, y, button, pressed):
    if pressed:
        # Caret moved; reset word buffer and clear RAM tracker
        reset(clear_prev=True)


# ---------------- insert worker ----------------
def worker():
    """Worker thread that executes backspaces and synthetic text insertion."""
    kb = keyboard.Controller()
    while True:
        try:
            idx, kind, payload, typed_word = job_q.get()

            if kind == "snippet" and payload:
                trigger, expansion = payload
                for _ in range(len(typed_word)):
                    kb.tap(keyboard.Key.backspace)

                if snippets_mgr and snippets_mgr.is_multiline_or_long(expansion):
                    old_clip = winapi.get_clipboard_text()
                    if winapi.set_clipboard_text(expansion):
                        with kb.pressed(keyboard.Key.ctrl):
                            kb.tap("v")
                        time.sleep(0.06)
                        if old_clip is not None:
                            winapi.set_clipboard_text(old_clip)
                    else:
                        safe_text = expansion.replace("\n", " ").replace("\r", "")
                        kb.type(safe_text + " ")
                else:
                    kb.type(expansion + " ")

                if stats_tracker:
                    stats_tracker.record_pick(len(trigger), len(expansion), is_correction=False)
                state.word = ""
                state.active_snippet = None
                text_tracker.clear()

            elif kind == "correction" and payload:
                orig, corr, _ = payload
                for _ in range(len(orig) + 1):
                    kb.tap(keyboard.Key.backspace)
                kb.type(corr + " ")
                low = corr.lower()
                req_q.put(("learn", low, state.prev))
                state.prev = low
                state.word = ""
                state.pending_correction = None
                if stats_tracker:
                    stats_tracker.record_pick(len(orig), len(corr), is_correction=True)
                # Update text tracker
                text_tracker.clear()

            elif kind == "grammar" and payload:
                issue, n_bs, retype, _, snap_ver = payload
                # Verify tracker version immediately before applying
                if snap_ver == text_tracker.version:
                    for _ in range(n_bs):
                        kb.tap(keyboard.Key.backspace)
                    kb.type(retype)
                    if stats_tracker:
                        stats_tracker.record_pick(n_bs, len(retype), is_correction=True)
                state.active_grammar = None
                text_tracker.clear()

            else:
                # Normal or prefix fuzzy insertion
                if idx < len(state.suggestions):
                    chosen = state.suggestions[idx].lstrip("~")
                    typed_len = len(state.word)
                    for _ in range(typed_len):
                        kb.tap(keyboard.Key.backspace)
                    kb.type(chosen + " ")
                    low = chosen.lower()
                    req_q.put(("learn", low, state.prev))
                    state.prev = low
                    state.word = ""
                    if stats_tracker:
                        stats_tracker.record_pick(typed_len, len(chosen), is_correction=False)
                    text_tracker.clear()

            refresh()
        except Exception as e:
            logger.error("Error in insert worker loop: %s", e)


# ---------------- sensitive context checker (password / blocked apps) ----------------
def sensitive_checker():
    winapi.set_current_thread_low_priority()
    while True:
        try:
            time.sleep(0.25)
            curr_hwnd = winapi.get_foreground_hwnd()
            if curr_hwnd != state.last_foreground_hwnd:
                state.last_foreground_hwnd = curr_hwnd
                ui_q.put(("hide", None))

            blocked_a = settings.blocked_apps if settings else []
            blocked_t = settings.blocked_title_words if settings else []
            sensitive, reason = winapi.check_sensitive_state(blocked_a, blocked_t)

            if sensitive != state.auto_paused:
                state.auto_paused = sensitive
                state.auto_pause_reason = reason
                if sensitive:
                    logger.info("AUTO-PAUSED: %s", reason)
                    ui_q.put(("hide", None))
                    reset()
                else:
                    logger.info("AUTO-PAUSE RESUMED")

                if tray:
                    tray.set_state(state.paused, state.auto_paused)
        except Exception as e:
            logger.debug("Error in sensitive checker: %s", e)


def reload_wordlists():
    """Reload predictor dictionaries and packs in the background."""
    global predictor, fuzzy_engine
    personal_file = data_directory / (settings.personal_word_file if settings else "personal_words.txt")
    pack_paths = get_enabled_pack_wordlists(settings.word_packs if settings else ["en-basic"])
    all_paths = [str(personal_file)] + [str(p) for p in pack_paths]

    new_pred = Predictor(
        all_paths,
        learn_file=str(personal_file),
        user_path=str(data_directory / "user_data.json"),
        added_path=str(data_directory / "added_words.json"),
        ignore_path=str(data_directory / "ignore_words.txt"),
    )
    new_pred.prewarm()

    if predictor:
        with predictor.lock:
            predictor.freq = new_pred.freq
            predictor.keys = new_pred.keys
            predictor._cache = new_pred._cache
            predictor.learn_file = new_pred.learn_file
    else:
        predictor = new_pred

    if fuzzy_engine:
        fuzzy_engine.build_index_async(predictor.freq)
    logger.info("Reloaded %d words across enabled packs: %s", len(predictor.keys), settings.word_packs if settings else [])


def main():
    global predictor, fuzzy_engine, grammar_checker, overlay, listener, tray, settings, snippets_mgr, stats_tracker, data_directory, PICK_KEYS

    parser = argparse.ArgumentParser(description="Typing Buddy - Windows Typing Assistant")
    parser.add_argument("--data-dir", help="Path to user data directory (defaults to %APPDATA%\\typing-buddy)")
    parser.add_argument("--version", action="version", version=f"Typing Buddy {__version__}")
    subparsers = parser.add_subparsers(dest="subcommand")

    packs_parser = subparsers.add_parser("packs", help="Manage word packs")
    packs_parser.add_argument("action", choices=["list"], help="Action to perform")

    args = parser.parse_args()

    # Handle CLI subcommands
    if args.subcommand == "packs" and args.action == "list":
        data_dir = resolve_data_dir(args.data_dir)
        init_user_data_files(data_dir)
        cfg = Settings(str(data_dir / "settings.json"))
        enabled = set(cfg.word_packs)
        print("Available Word Packs:")
        for p in list_available_packs():
            is_on = "[ENABLED]" if p["name"] in enabled else "[DISABLED]"
            print(f"  {is_on:11} {p['name']:12} - {p.get('description', '')} ({p.get('word_count', 0):,} words)")
        sys.exit(0)

    # Single-instance mutex check
    mutex, already_running = winapi.create_single_instance_mutex("Local\\TypingBuddy_SingleInstance_Mutex")
    if already_running:
        logger.info("Another instance of Typing Buddy is already running. Exiting.")
        sys.exit(0)

    # Initialize data directory
    data_directory = resolve_data_dir(args.data_dir)
    init_user_data_files(data_directory)
    logger.info("User data directory: %s", data_directory)

    # Setup file logger in data directory
    log_file = data_directory / "predictor.log"
    file_handler = RotatingFileHandler(str(log_file), maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s"))
    logger.addHandler(file_handler)

    # Load settings from data directory
    settings = Settings(str(data_directory / "settings.json"))
    settings.start_watcher(interval=2.0)
    PICK_KEYS = build_pick_key_map(settings.pick_keys)

    snippets_mgr = SnippetsManager(
        str(data_directory / "snippets.json"),
        date_format=settings.date_format,
        time_format=settings.time_format,
    )
    stats_tracker = StatsTracker(str(data_directory / "stats.json"))

    # Word list paths: personal_words.txt in data_dir + enabled wordpacks
    personal_file = data_directory / settings.personal_word_file
    pack_paths = get_enabled_pack_wordlists(settings.word_packs)
    all_word_paths = [str(personal_file)] + [str(p) for p in pack_paths]

    predictor = Predictor(
        all_word_paths,
        learn_file=str(personal_file),
        user_path=str(data_directory / "user_data.json"),
        added_path=str(data_directory / "added_words.json"),
        ignore_path=str(data_directory / "ignore_words.txt"),
    )
    predictor.LENGTH_BONUS = settings.length_bonus
    predictor.AUTO_ADD_NEW_WORDS = settings.auto_add_new_words
    predictor.NEW_WORD_MIN_COUNT = settings.new_word_min_count
    predictor.NEW_WORD_FREQ = settings.new_word_freq
    predictor.LEARN_RANKING = settings.learn_ranking

    logger.info("Loaded %d words across enabled packs: %s", len(predictor.keys), settings.word_packs)
    threading.Thread(target=predictor.prewarm, daemon=True, name="PredictorPrewarm").start()

    fuzzy_engine = FuzzyEngine(ignore_path=str(data_directory / "ignore_words.txt"))
    if settings.fuzzy_enabled:
        fuzzy_engine.build_index_async(predictor.freq)

    # Initialize Grammar Checker
    non_english_words = get_non_english_pack_words(settings.word_packs)
    personal_words = list(predictor.freq.keys())[:500]  # seed with personal vocabulary
    custom_seed = list(set(non_english_words + personal_words))

    grammar_checker = HarperChecker(
        lint_kinds=settings.grammar_lint_kinds,
        ignored_rules=settings.grammar_ignored_rules,
        dialect=settings.grammar_dialect,
        custom_words=custom_seed,
    )
    if not grammar_checker.is_available():
        grammar_checker = NullChecker()

    # Settings change callback
    def on_settings_changed(new_data):
        global PICK_KEYS
        PICK_KEYS = build_pick_key_map(new_data.get("pick_keys", []))
        if predictor:
            predictor.LENGTH_BONUS = new_data.get("length_bonus", 0.02)
            predictor.AUTO_ADD_NEW_WORDS = new_data.get("auto_add_new_words", True)
            predictor.NEW_WORD_MIN_COUNT = new_data.get("new_word_min_count", 3)
            predictor.NEW_WORD_FREQ = new_data.get("new_word_freq", 120)
            predictor.LEARN_RANKING = new_data.get("learn_ranking", True)
        if snippets_mgr:
            snippets_mgr.update_formats(
                new_data.get("date_format", "%Y-%m-%d"),
                new_data.get("time_format", "%H:%M"),
            )
        if overlay:
            overlay.update_settings(
                font_size=new_data.get("popup_font_size", 12),
                opacity=new_data.get("popup_opacity", 0.95),
                click_to_pick=new_data.get("popup_click_to_pick", True),
                pick_keys=new_data.get("pick_keys", ["F2", "F3", "F4"]),
            )
        logger.info("Settings updated.")

    settings.add_change_callback(on_settings_changed)

    # Start background threads
    threading.Thread(target=engine, daemon=True, name="EngineThread").start()
    threading.Thread(target=worker, daemon=True, name="InsertWorker").start()
    threading.Thread(target=grammar_worker, daemon=True, name="GrammarWorker").start()
    threading.Thread(target=sensitive_checker, daemon=True, name="SensitiveChecker").start()

    listener = keyboard.Listener(
        on_press=on_press, on_release=on_release, win32_event_filter=win32_filter
    )
    listener.start()
    mouse.Listener(on_click=on_click).start()

    # Tkinter UI on main thread
    root = tk.Tk()

    def on_click_pick(idx):
        kind = "normal"
        payload = None
        if state.active_snippet and idx == 0:
            kind = "snippet"
            payload = state.active_snippet
        elif state.pending_correction and idx == 0:
            kind = "correction"
            payload = state.pending_correction
        elif state.active_grammar and idx == 0:
            kind = "grammar"
            payload = state.active_grammar
        job_q.put((idx, kind, payload, state.word))

    overlay = Overlay(
        root,
        on_click_pick=on_click_pick,
        font_size=settings.popup_font_size,
        opacity=settings.popup_opacity,
        click_to_pick=settings.popup_click_to_pick,
    )
    overlay.keys = list(settings.pick_keys)

    # System Tray
    def on_tray_toggle_pause():
        state.paused = not state.paused
        logger.info("Tray toggled pause: %s", state.paused)
        if tray:
            tray.set_state(state.paused, state.auto_paused)
        reset()

    def on_tray_toggle_pack(pack_id, enable):
        current = list(settings.word_packs)
        if enable and pack_id not in current:
            current.append(pack_id)
        elif not enable and pack_id in current:
            current.remove(pack_id)
        settings.set_value("word_packs", current)
        threading.Thread(target=reload_wordlists, daemon=True, name="PackReloader").start()

    def on_tray_toggle_grammar():
        new_val = not bool(settings.grammar_enabled)
        settings.set_value("grammar_enabled", new_val)
        logger.info("Grammar suggestions toggled: %s", new_val)

    def on_tray_quit():
        logger.info("Quit requested via system tray.")
        ui_q.put(("quit", None))

    tray = SystemTray(
        ui_q=ui_q,
        on_toggle_pause=on_tray_toggle_pause,
        on_toggle_pack=on_tray_toggle_pack,
        on_toggle_grammar=on_tray_toggle_grammar,
        on_quit=on_tray_quit,
        settings_obj=settings,
        grammar_available=grammar_checker.is_available(),
    )
    tray.run()

    def poll_ui():
        try:
            while True:
                kind, payload = ui_q.get_nowait()
                if kind == "show":
                    sugg_list, reason_text = payload
                    overlay.show(sugg_list, reason=reason_text)
                elif kind == "hide":
                    overlay.hide()
                elif kind == "review_words":
                    ReviewWindow(
                        root,
                        added_path=str(data_directory / "added_words.json"),
                        on_delete_word=predictor.remove_word,
                    )
                elif kind == "show_stats":
                    show_statistics_window(root, stats_tracker.get_summary())
                elif kind == "show_about":
                    show_about_dialog(root)
                elif kind == "open_personal_words":
                    p = str(data_directory / settings.personal_word_file)
                    if os.path.exists(p):
                        os.startfile(p)
                elif kind == "open_settings":
                    p = str(data_directory / "settings.json")
                    if os.path.exists(p):
                        os.startfile(p)
                elif kind == "reload_settings":
                    settings.reload()
                elif kind == "reload_wordlists":
                    threading.Thread(target=reload_wordlists, daemon=True).start()
                elif kind == "quit":
                    root.destroy()
                    return
        except queue.Empty:
            pass
        root.after(15, poll_ui)

    root.after(15, poll_ui)

    logger.info("Typing Buddy %s running. Tray icon active.", __version__)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        if tray:
            tray.stop()
        if predictor:
            predictor.save()
        if stats_tracker:
            stats_tracker.save()
        if settings:
            settings.stop_watcher()


if __name__ == "__main__":
    main()
