"""overlay.py - Tkinter popup overlay for word suggestions and grammar fixes."""
import logging
import tkinter as tk
from typing import Callable, List, Optional

from . import winapi

logger = logging.getLogger("typing_buddy.overlay")


class Overlay:
    """Non-activating, topmost suggestion overlay clamped to the current monitor."""

    def __init__(
        self,
        root: tk.Tk,
        on_click_pick: Optional[Callable[[int], None]] = None,
        font_size: int = 12,
        opacity: float = 0.95,
        click_to_pick: bool = True,
    ):
        self.root = root
        self.on_click_pick = on_click_pick
        self.font_size = font_size
        self.opacity = opacity
        self.click_to_pick = click_to_pick

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", opacity)
        except Exception:
            pass

        self.container = tk.Frame(root, bg="#202124", padx=6, pady=4)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.items_frame = tk.Frame(self.container, bg="#202124")
        self.items_frame.pack(side=tk.TOP, fill=tk.X)

        self.reason_label = tk.Label(
            self.container,
            font=("Segoe UI", max(8, self.font_size - 3), "italic"),
            bg="#202124",
            fg="#9aa0a6",
            padx=4,
            pady=2,
            anchor="w",
            justify=tk.LEFT,
        )

        self.labels: List[tk.Label] = []
        self.styled = False
        self.keys = ["F2", "F3", "F4"]
        self.current_suggestions = []

        root.withdraw()

    def update_settings(self, font_size: int, opacity: float, click_to_pick: bool, pick_keys: List[str]):
        """Update appearance settings dynamically."""
        self.font_size = font_size
        self.opacity = opacity
        self.click_to_pick = click_to_pick
        self.keys = list(pick_keys)
        try:
            self.root.attributes("-alpha", opacity)
        except Exception:
            pass
        self.reason_label.config(font=("Segoe UI", max(8, self.font_size - 3), "italic"))

    def _no_focus_steal(self):
        hwnd = winapi.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
        winapi.set_window_no_focus_steal(hwnd)
        self.styled = True

    def _on_label_click(self, idx: int):
        if self.click_to_pick and self.on_click_pick:
            self.on_click_pick(idx)

    def show(self, suggestions: List[str], reason: Optional[str] = None):
        """Show the overlay with updated suggestions and optional grammar reason."""
        if not suggestions:
            self.hide()
            return

        self.current_suggestions = list(suggestions)

        # Ensure enough labels
        while len(self.labels) < len(suggestions):
            idx = len(self.labels)
            lbl = tk.Label(
                self.items_frame,
                font=("Segoe UI", self.font_size),
                bg="#202124",
                fg="#e8eaed",
                padx=8,
                pady=2,
                cursor="hand2" if self.click_to_pick else "",
            )
            lbl.bind("<Button-1>", lambda event, i=idx: self._on_label_click(i))
            lbl.pack(side=tk.LEFT, padx=3)
            self.labels.append(lbl)

        # Update labels content and visibility
        for i, lbl in enumerate(self.labels):
            if i < len(suggestions):
                k = self.keys[i] if i < len(self.keys) else f"F{i+2}"
                lbl.config(
                    text=f"{k} {suggestions[i]}",
                    font=("Segoe UI", self.font_size),
                    cursor="hand2" if self.click_to_pick else "",
                )
                lbl.pack(side=tk.LEFT, padx=3)
            else:
                lbl.pack_forget()

        # Update reason line if present
        if reason:
            self.reason_label.config(text=reason)
            self.reason_label.pack(side=tk.TOP, fill=tk.X, pady=(2, 0))
        else:
            self.reason_label.pack_forget()

        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()

        pos = winapi.caret_pos()
        if pos:
            target_x = pos[0]
            target_y = pos[1] + 6
        else:
            target_x = (self.root.winfo_screenwidth() - w) // 2
            target_y = self.root.winfo_screenheight() - h - 90

        wl, wt, wr, wb = winapi.get_monitor_work_area(target_x, target_y)

        # Clamp horizontally
        if target_x + w > wr:
            target_x = wr - w - 4
        if target_x < wl:
            target_x = wl + 4

        # Clamp vertically: if off-bottom, display above caret
        if target_y + h > wb:
            if pos and pos[1] - h - 6 >= wt:
                target_y = pos[1] - h - 6
            else:
                target_y = wb - h - 4
        if target_y < wt:
            target_y = wt + 4

        self.root.geometry(f"+{target_x}+{target_y}")
        self.root.deiconify()
        if not self.styled and winapi.IS_WINDOWS:
            self._no_focus_steal()

    def hide(self):
        self.root.withdraw()

