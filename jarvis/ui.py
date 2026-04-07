from __future__ import annotations

import queue
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import Callable

from jarvis.config import CONFIG


class JarvisUI:
    def __init__(self, on_start: Callable[[], None], on_stop: Callable[[], None], on_text_command: Callable[[str], None]):
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_text_command = on_text_command
        self.queue: queue.Queue[tuple[str, str]] = queue.Queue()

        self.root = tk.Tk()
        self.root.title("JARVIS Assistant")
        self.root.geometry("920x620")

        self.status_var = tk.StringVar(value="Idle")
        self._build_layout()
        self.root.after(250, self._drain_queue)

    def _build_layout(self) -> None:
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="JARVIS Control Panel", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(top, textvariable=self.status_var, fg="blue", font=("Segoe UI", 11)).pack(anchor="w")

        controls = tk.Frame(self.root)
        controls.pack(fill="x", padx=10)

        tk.Button(controls, text="Start Listening", command=self.on_start, width=18).pack(side="left", padx=5)
        tk.Button(controls, text="Stop", command=self.on_stop, width=10).pack(side="left", padx=5)

        self.command_entry = tk.Entry(controls)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=6)
        tk.Button(
            controls,
            text="Run Text Command",
            command=lambda: self.on_text_command(self.command_entry.get().strip()),
            width=16,
        ).pack(side="left")

        panels = tk.PanedWindow(self.root, sashwidth=8)
        panels.pack(fill="both", expand=True, padx=10, pady=10)

        self.history = scrolledtext.ScrolledText(panels, height=25)
        self.history.insert("end", "Command history will appear here...\n")

        self.logs = scrolledtext.ScrolledText(panels, height=25)
        self.logs.insert("end", "System logs will appear here...\n")

        panels.add(self.history)
        panels.add(self.logs)

    def ask_password_if_needed(self) -> bool:
        if not CONFIG.security_password_hash:
            return True
        dialog = tk.Toplevel(self.root)
        dialog.title("Security Check")
        tk.Label(dialog, text="Enter JARVIS password").pack(padx=20, pady=12)
        password_entry = tk.Entry(dialog, show="*")
        password_entry.pack(padx=20, pady=8)

        result = {"ok": False}

        def submit() -> None:
            if CONFIG.verify_password(password_entry.get().strip()):
                result["ok"] = True
                dialog.destroy()
            else:
                messagebox.showerror("Invalid", "Incorrect password")

        tk.Button(dialog, text="Unlock", command=submit).pack(pady=10)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return result["ok"]

    def post(self, panel: str, message: str) -> None:
        self.queue.put((panel, message))

    def set_status(self, value: str) -> None:
        self.status_var.set(value)

    def _drain_queue(self) -> None:
        while not self.queue.empty():
            panel, message = self.queue.get_nowait()
            widget = self.history if panel == "history" else self.logs
            widget.insert("end", message + "\n")
            widget.see("end")
        self.root.after(250, self._drain_queue)

    def run(self) -> None:
        self.root.mainloop()
