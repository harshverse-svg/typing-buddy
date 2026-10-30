"""tray.py - System tray icon and menu using pystray and Pillow."""
import logging
import os
import queue
import threading
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw

import winapi

logger = logging.getLogger("predictor.tray")

COLOR_ACTIVE = "#2ecc71"       # Green
COLOR_MANUAL_PAUSE = "#95a5a6" # Grey
COLOR_AUTO_PAUSE = "#e67e22"   # Orange


def create_tray_image(color: str) -> Image.Image:
    """Generate a clean colored circle icon with transparency."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Circle outline and fill
    draw.ellipse([6, 6, 58, 58], fill=color, outline="#1e272e", width=2)
    return img


class SystemTray:
    """System tray manager running in its own detached thread."""

    def __init__(self, ui_q: queue.Queue, on_toggle_pause: Callable[[], None],
                 on_quit: Callable[[], None]):
        self.ui_q = ui_q
        self.on_toggle_pause = on_toggle_pause
        self.on_quit = on_quit
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
                self.icon.title = "Typing Predictor (Paused)"
            elif self.is_auto_paused:
                self.icon.icon = self._img_auto
                self.icon.title = "Typing Predictor (Auto-Paused: Sensitive Field)"
            else:
                self.icon.icon = self._img_active
                self.icon.title = "Typing Predictor (Active)"
            self.icon.update_menu()
        except Exception as e:
            logger.debug("Error updating tray icon state: %s", e)

    def _build_menu(self):
        def pause_text(item):
            return "Resume" if self.is_paused else "Pause"

        def is_autostart(item):
            return winapi.is_start_with_windows_enabled()

        return pystray.Menu(
            pystray.MenuItem(pause_text, lambda item: self.on_toggle_pause()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open words.txt", lambda item: self._open_file("words.txt")),
            pystray.MenuItem("Open settings.json", lambda item: self._open_file("settings.json")),
            pystray.MenuItem("Review new words", lambda item: self.ui_q.put(("review_words", None))),
            pystray.MenuItem("Statistics", lambda item: self.ui_q.put(("show_stats", None))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Reload settings", lambda item: self.ui_q.put(("reload_settings", None))),
            pystray.MenuItem("Reload word lists", lambda item: self.ui_q.put(("reload_wordlists", None))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start with Windows", self._toggle_autostart, checked=is_autostart),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda item: self.on_quit())
        )

    def run(self):
        """Start the system tray icon."""
        try:
            self.icon = pystray.Icon(
                "TypingPredictor",
                self._img_active,
                "Typing Predictor (Active)",
                self._build_menu()
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

