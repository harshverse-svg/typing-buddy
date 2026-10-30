"""tray.py - System tray icon and menu using pystray and Pillow."""
import logging
import os
import queue
import threading
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw

from . import winapi
from .packs import list_available_packs

logger = logging.getLogger("typing_buddy.tray")

COLOR_ACTIVE = "#22c55e"       # Vibrant Green
COLOR_MANUAL_PAUSE = "#94a3b8" # Slate Grey
COLOR_AUTO_PAUSE = "#f97316"   # Orange


def create_tray_image(status_color: str) -> Image.Image:
    """Generate the branded Typing Buddy key icon with a status indicator badge."""
    size = 64
    scale = 4
    canvas_size = size * scale
    im = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    pad = int(canvas_size * 0.08)
    radius = int(canvas_size * 0.22)
    box = [pad, pad, canvas_size - pad, canvas_size - pad]

    # Base squircle
    draw.rounded_rectangle(box, radius=radius, fill=(37, 99, 235, 255), outline=(30, 64, 175, 255), width=int(canvas_size * 0.025))

    # Inner key cap
    inner_pad = int(canvas_size * 0.14)
    inner_rad = int(canvas_size * 0.16)
    inner_box = [inner_pad, inner_pad, canvas_size - inner_pad, canvas_size - inner_pad]
    draw.rounded_rectangle(inner_box, radius=inner_rad, fill=(59, 130, 246, 255))

    # Center cursor bar
    cx, cy = canvas_size // 2, canvas_size // 2
    bar_w = int(canvas_size * 0.09)
    bar_h = int(canvas_size * 0.44)
    bar_x = cx - int(canvas_size * 0.12)
    bar_y = cy - bar_h // 2
    draw.rounded_rectangle(
        [bar_x - bar_w // 2, bar_y, bar_x + bar_w // 2, bar_y + bar_h],
        radius=bar_w // 2,
        fill=(255, 255, 255, 255)
    )

    # Sparkle star
    sx = cx + int(canvas_size * 0.15)
    sy = cy - int(canvas_size * 0.02)
    r_outer = int(canvas_size * 0.18)
    r_inner = int(canvas_size * 0.05)
    star_points = [
        (sx, sy - r_outer),
        (sx + r_inner, sy - r_inner),
        (sx + r_outer, sy),
        (sx + r_inner, sy + r_inner),
        (sx, sy + r_outer),
        (sx - r_inner, sy + r_inner),
        (sx - r_outer, sy),
        (sx - r_inner, sy - r_inner),
    ]
    draw.polygon(star_points, fill=(251, 191, 36, 255))

    # Status indicator badge on bottom right
    badge_r = int(canvas_size * 0.16)
    bx = canvas_size - pad - badge_r
    by = canvas_size - pad - badge_r
    draw.ellipse([bx - badge_r - scale * 3, by - badge_r - scale * 3,
                  bx + badge_r + scale * 3, by + badge_r + scale * 3],
                 fill=(15, 23, 42, 255))
    draw.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=status_color)

    return im.resize((size, size), Image.Resampling.LANCZOS)


class SystemTray:
    """System tray manager running in its own detached thread."""

    def __init__(
        self,
        ui_q: queue.Queue,
        on_toggle_pause: Callable[[], None],
        on_toggle_pack: Callable[[str, bool], None],
        on_toggle_grammar: Callable[[], None],
        on_quit: Callable[[], None],
        settings_obj=None,
        grammar_available: bool = True,
    ):
        self.ui_q = ui_q
        self.on_toggle_pause = on_toggle_pause
        self.on_toggle_pack = on_toggle_pack
        self.on_toggle_grammar = on_toggle_grammar
        self.on_quit = on_quit
        self.settings = settings_obj
        self.grammar_available = grammar_available

        self.icon: Optional[pystray.Icon] = None
        self.is_paused = False
        self.is_auto_paused = False
        self.lock = threading.RLock()

        self._img_active = create_tray_image(COLOR_ACTIVE)
        self._img_manual = create_tray_image(COLOR_MANUAL_PAUSE)
        self._img_auto = create_tray_image(COLOR_AUTO_PAUSE)

    def _open_file(self, filename: str):
        path = os.path.abspath(filename)
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                logger.error("Could not open file %s: %s", path, e)
        else:
            logger.warning("File %s does not exist to open", path)

    def _toggle_autostart(self, item):
        current = winapi.is_start_with_windows_enabled()
        winapi.toggle_start_with_windows(not current)
        if self.icon:
            self.icon.update_menu()

    def set_state(self, paused: bool, auto_paused: bool):
        """Update tray icon image based on paused / auto-paused status."""
        with self.lock:
            if paused == self.is_paused and auto_paused == self.is_auto_paused:
                return
            self.is_paused = paused
            self.is_auto_paused = auto_paused

        if not self.icon:
            return

        try:
            if self.is_paused:
                self.icon.icon = self._img_manual
                self.icon.title = "Typing Buddy (Paused)"
            elif self.is_auto_paused:
                self.icon.icon = self._img_auto
                self.icon.title = "Typing Buddy (Auto-Paused: Sensitive Field)"
            else:
                self.icon.icon = self._img_active
                self.icon.title = "Typing Buddy (Active)"
            self.icon.update_menu()
        except Exception as e:
            logger.debug("Error updating tray icon state: %s", e)

    def _build_wordpacks_menu(self):
        items = []
        available = list_available_packs()

        for pack in available:
            p_id = pack.get("id", pack.get("name"))
            title = f"{pack.get('name')} ({pack.get('word_count', 0):,} words)"

            def make_handler(target_id):
                def handler(item):
                    current_enabled = target_id in (self.settings.word_packs if self.settings else [])
                    self.on_toggle_pack(target_id, not current_enabled)
                return handler

            def make_checker(target_id):
                return lambda item: target_id in (self.settings.word_packs if self.settings else [])

            items.append(
                pystray.MenuItem(title, make_handler(p_id), checked=make_checker(p_id))
            )

        return pystray.Menu(*items)

    def _build_menu(self):
        def pause_text(item):
            return "Resume" if self.is_paused else "Pause"

        def is_autostart(item):
            return winapi.is_start_with_windows_enabled()

        def is_grammar_enabled(item):
            return bool(self.settings and self.settings.grammar_enabled)

        grammar_label = "Grammar suggestions" if self.grammar_available else "Grammar suggestions (not installed)"

        return pystray.Menu(
            pystray.MenuItem(pause_text, lambda item: self.on_toggle_pause()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Word packs", self._build_wordpacks_menu()),
            pystray.MenuItem(
                grammar_label,
                lambda item: self.on_toggle_grammar() if self.grammar_available else None,
                checked=is_grammar_enabled,
                enabled=self.grammar_available,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open personal words", lambda item: self.ui_q.put(("open_personal_words", None))),
            pystray.MenuItem("Open settings.json", lambda item: self.ui_q.put(("open_settings", None))),
            pystray.MenuItem("Review new words", lambda item: self.ui_q.put(("review_words", None))),
            pystray.MenuItem("Statistics", lambda item: self.ui_q.put(("show_stats", None))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Reload settings", lambda item: self.ui_q.put(("reload_settings", None))),
            pystray.MenuItem("Reload word lists", lambda item: self.ui_q.put(("reload_wordlists", None))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start with Windows", self._toggle_autostart, checked=is_autostart),
            pystray.MenuItem("About", lambda item: self.ui_q.put(("show_about", None))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda item: self.on_quit()),
        )

    def run(self):
        """Start the system tray icon."""
        try:
            self.icon = pystray.Icon(
                "TypingBuddy",
                self._img_active,
                "Typing Buddy (Active)",
                self._build_menu(),
            )
            self.icon.run_detached()
            logger.info("System tray initialized.")
        except Exception as e:
            logger.error("Failed to start system tray icon: %s", e)

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
