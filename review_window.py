"""review_window.py - Review and manage auto-added words."""
import json
import logging
import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

logger = logging.getLogger("predictor.review")


class ReviewWindow:
    """Tkinter window to review, keep, or delete auto-added words."""

    def __init__(self, master: tk.Tk, added_path: str = "added_words.json",
                 on_delete_word: Optional[Callable[[str], None]] = None):
        self.master = master
        self.added_path = os.path.abspath(added_path)
        self.on_delete_word = on_delete_word

        self.window = tk.Toplevel(master)
        self.window.title("Review Auto-Added Words")
        self.window.geometry("450x380")
        self.window.minsize(380, 260)

        self._build_ui()
        self._load_words()

    def _build_ui(self):
        frame = ttk.Frame(self.window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl = ttk.Label(frame, text="Auto-added words awaiting your review:", font=("Segoe UI", 10, "bold"))
        lbl.pack(anchor=tk.W, pady=(0, 8))

        columns = ("word", "date")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("word", text="Word")
        self.tree.heading("date", text="Added Date")
        self.tree.column("word", width=180, anchor=tk.W)
        self.tree.column("date", width=180, anchor=tk.W)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, in_=self.tree)

        btn_frame = ttk.Frame(frame, padding=(0, 10, 0, 0))
        btn_frame.pack(fill=tk.X)

        self.btn_keep = ttk.Button(btn_frame, text="Keep (Approve)", command=self._keep_selected)
        self.btn_keep.pack(side=tk.LEFT, padx=4)

        self.btn_delete = ttk.Button(btn_frame, text="Delete & Ignore", command=self._delete_selected)
        self.btn_delete.pack(side=tk.LEFT, padx=4)

        self.btn_close = ttk.Button(btn_frame, text="Close", command=self.window.destroy)
        self.btn_close.pack(side=tk.RIGHT, padx=4)

    def _load_words(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(self.added_path):
            return

        try:
            with open(self.added_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            if isinstance(records, list):
                for r in records:
                    w = r.get("word", "")
                    d = r.get("date", "")
                    if w:
                        self.tree.insert("", tk.END, values=(w, d))
        except Exception as e:
            logger.error("Failed to load %s: %s", self.added_path, e)

    def _save_records(self, records):
        tmp = self.added_path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            os.replace(tmp, self.added_path)
        except OSError as e:
            logger.error("Failed to save %s: %s", self.added_path, e)

    def _keep_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = selected[0]
        word = self.tree.item(item, "values")[0]

        # Remove from added_words.json
        if os.path.exists(self.added_path):
            try:
                with open(self.added_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                records = [r for r in records if r.get("word") != word]
                self._save_records(records)
            except Exception as e:
                logger.error("Error keeping word: %s", e)

        self.tree.delete(item)

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = selected[0]
        word = self.tree.item(item, "values")[0]

        if messagebox.askyesno("Delete Word", f"Delete '{word}' from word list and never suggest it again?"):
            if self.on_delete_word:
                self.on_delete_word(word)
            self._keep_selected()  # Also removes from added_words.json


def show_statistics_window(master: tk.Tk, stats_summary: dict):
    """Small Tk window showing keystrokes saved, suggestions picked, and corrections."""
    win = tk.Toplevel(master)
    win.title("Typing Predictor Statistics")
    win.geometry("380x280")
    win.resizable(False, False)

    frame = ttk.Frame(win, padding=16)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Your Typing Statistics", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 12))

    tree = ttk.Treeview(frame, columns=("period", "saved", "picks", "corrs"), show="headings", height=4)
    tree.heading("period", text="Period")
    tree.heading("saved", text="Keystrokes Saved")
    tree.heading("picks", text="Picks")
    tree.heading("corrs", text="Corrections")

    tree.column("period", width=100, anchor=tk.W)
    tree.column("saved", width=110, anchor=tk.E)
    tree.column("picks", width=60, anchor=tk.E)
    tree.column("corrs", width=70, anchor=tk.E)
    tree.pack(fill=tk.BOTH, expand=True)

    periods = [("Today", "today"), ("Last 7 Days", "last_7_days"), ("All-Time Total", "total")]
    for label, key in periods:
        data = stats_summary.get(key, {})
        tree.insert("", tk.END, values=(
            label,
            f"{data.get('keystrokes_saved', 0):,}",
            f"{data.get('suggestions_picked', 0):,}",
            f"{data.get('corrections_picked', 0):,}"
        ))

    btn = ttk.Button(frame, text="Close", command=win.destroy)
    btn.pack(anchor=tk.E, pady=(12, 0))

