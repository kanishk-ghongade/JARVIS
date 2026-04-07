import datetime as dt
import json
import os
import queue
import re
import socket
import sqlite3
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import pyautogui
import pyttsx3
import requests
import sounddevice as sd
import tkinter as tk
from faster_whisper import WhisperModel
from scipy.io.wavfile import write
from tkinter import messagebox, simpledialog, ttk

APP_NAME = "JARVIS"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "jarvis.db"
AUDIO_PATH = DATA_DIR / "input.wav"
CONFIG_PATH = DATA_DIR / "config.json"


DEFAULT_CONFIG = {
    "wake_word": "hey jarvis",
    "language_mode": "auto",  # auto | en | hi
    "password_enabled": False,
    "password": "",
    "openai_api_key": "",
    "weather_city": "Delhi",
}


@dataclass
class AssistantResponse:
    text: str
    speak: bool = True


class Storage:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                speaker TEXT NOT NULL,
                message TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def add_history(self, speaker: str, message: str):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO history (ts, speaker, message) VALUES (?, ?, ?)",
            (dt.datetime.now().isoformat(), speaker, message),
        )
        self.conn.commit()

    def recent_history(self, limit: int = 50):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT ts, speaker, message FROM history ORDER BY id DESC LIMIT ?", (limit,)
        )
        return list(reversed(cur.fetchall()))

    def set_memory(self, key: str, value: str):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO memory(key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, dt.datetime.now().isoformat()),
        )
        self.conn.commit()

    def get_memory(self, key: str) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM memory WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None


class TTS:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.lock = threading.Lock()

    def speak(self, text: str):
        with self.lock:
            self.engine.say(text)
            self.engine.runAndWait()


class WhisperSTT:
    def __init__(self):
        self.model = WhisperModel("small", compute_type="int8")

    def record_and_transcribe(self, seconds: int = 4, sample_rate: int = 16000) -> str:
        recording = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
        sd.wait()
        write(str(AUDIO_PATH), sample_rate, recording)
        segments, _ = self.model.transcribe(str(AUDIO_PATH), beam_size=1)
        text = " ".join(segment.text for segment in segments).strip().lower()
        return text


class CommandEngine:
    def __init__(self, storage: Storage, log: Callable[[str], None]):
        self.storage = storage
        self.log = log

    def execute(self, text: str) -> AssistantResponse:
        t = text.lower().strip()

        if any(x in t for x in ["time", "samay", "time batao"]):
            now = dt.datetime.now().strftime("%I:%M %p")
            return AssistantResponse(f"The time is {now}")

        if any(x in t for x in ["open chrome", "chrome kholo"]):
            return self._open_app("chrome", ["start", "chrome"])

        if "open notepad" in t or "notepad kholo" in t:
            return self._open_app("notepad", ["start", "notepad"])

        if any(x in t for x in ["search on google", "google search", "google par search"]):
            query = re.sub(r".*(search on google|google search|google par search)", "", t).strip()
            if not query:
                return AssistantResponse("What should I search on Google?")
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            subprocess.Popen(["start", url], shell=True)
            return AssistantResponse(f"Searching Google for {query}")

        if "take screenshot" in t or "screenshot lo" in t:
            file_path = DATA_DIR / f"screenshot_{int(time.time())}.png"
            pyautogui.screenshot(str(file_path))
            return AssistantResponse(f"Screenshot saved to {file_path}")

        if "shutdown system" in t or "system band" in t:
            subprocess.Popen(["shutdown", "/s", "/t", "15"], shell=True)
            return AssistantResponse("System will shutdown in 15 seconds")

        if "restart system" in t:
            subprocess.Popen(["shutdown", "/r", "/t", "15"], shell=True)
            return AssistantResponse("System will restart in 15 seconds")

        if "increase volume" in t or "volume badhao" in t:
            for _ in range(10):
                pyautogui.press("volumeup")
            return AssistantResponse("Volume increased")

        if "decrease volume" in t or "volume kam" in t:
            for _ in range(10):
                pyautogui.press("volumedown")
            return AssistantResponse("Volume decreased")

        if "open folder" in t or "folder kholo" in t:
            folder = str(Path.home())
            subprocess.Popen(["explorer", folder])
            return AssistantResponse(f"Opened folder {folder}")

        if "play music" in t or "music chalao" in t:
            music_dir = Path.home() / "Music"
            subprocess.Popen(["explorer", str(music_dir)])
            return AssistantResponse("Opened music folder")

        if "create file" in t:
            file_name = f"jarvis_note_{int(time.time())}.txt"
            p = Path.home() / "Desktop" / file_name
            p.write_text("Created by JARVIS", encoding="utf-8")
            return AssistantResponse(f"Created file {p}")

        if "delete file" in t:
            return AssistantResponse("Please specify file delete workflows in dashboard for safety.")

        if "tell weather" in t or "weather batao" in t:
            return self._weather()

        if "send email" in t:
            return AssistantResponse("Email workflow is enabled. Configure SMTP settings in config to send mail.")

        if t.startswith("remember "):
            payload = t.removeprefix("remember ").strip()
            if ":" in payload:
                key, value = [p.strip() for p in payload.split(":", 1)]
                self.storage.set_memory(key, value)
                return AssistantResponse(f"I will remember that {key} is {value}")
            return AssistantResponse("Use format: remember key: value")

        if t.startswith("what do you remember about"):
            key = t.replace("what do you remember about", "").strip()
            value = self.storage.get_memory(key)
            if value:
                return AssistantResponse(f"You told me {key} is {value}")
            return AssistantResponse("I don't have that in memory yet.")

        return self._offline_brain(t)

    def _open_app(self, name: str, cmd: list[str]) -> AssistantResponse:
        try:
            subprocess.Popen(cmd, shell=True)
            return AssistantResponse(f"Opening {name}")
        except Exception as e:
            self.log(str(e))
            return AssistantResponse(f"Could not open {name}")

    def _weather(self) -> AssistantResponse:
        try:
            city = self.storage.get_memory("weather_city") or "Delhi"
            r = requests.get(f"https://wttr.in/{city}?format=3", timeout=8)
            if r.ok:
                return AssistantResponse(r.text)
        except Exception as e:
            self.log(f"Weather error: {e}")
        return AssistantResponse("I am offline, weather service unavailable right now.")

    def _offline_brain(self, text: str) -> AssistantResponse:
        canned = {
            "hello": "Hello! I am ready.",
            "hi": "Hi! How can I help?",
            "kaise ho": "Main theek hoon. Aap bataiye.",
            "who are you": "I am JARVIS, your local AI assistant.",
        }
        for k, v in canned.items():
            if k in text:
                return AssistantResponse(v)
        return AssistantResponse("Command not recognized. Please try again.")


class JarvisUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("JARVIS Assistant")
        self.root.geometry("900x600")

        self.config = self._load_config()
        self.storage = Storage(DB_PATH)
        self.tts = TTS()
        self.stt = WhisperSTT()
        self.engine = CommandEngine(self.storage, self._add_log)

        self.status_var = tk.StringVar(value="Idle")
        self.history_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.running = False

        self._build_ui()
        self._load_history()

        if self.config.get("password_enabled"):
            self._enforce_password()

    def _load_config(self):
        if CONFIG_PATH.exists():
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_PATH.read_text(encoding="utf-8"))}
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        return DEFAULT_CONFIG.copy()

    def _build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Status:").pack(side="left")
        ttk.Label(top, textvariable=self.status_var, foreground="green").pack(side="left", padx=8)
        ttk.Button(top, text="Start", command=self.start).pack(side="left", padx=4)
        ttk.Button(top, text="Stop", command=self.stop).pack(side="left", padx=4)
        ttk.Button(top, text="Speak Text", command=self._manual_input).pack(side="left", padx=4)

        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=3)
        main.add(right, weight=2)

        ttk.Label(left, text="Command History").pack(anchor="w")
        self.history = tk.Text(left, wrap="word")
        self.history.pack(fill="both", expand=True)

        ttk.Label(right, text="Logs").pack(anchor="w")
        self.logs = tk.Text(right, wrap="word", foreground="#1f4f1f")
        self.logs.pack(fill="both", expand=True)

    def _load_history(self):
        for ts, speaker, msg in self.storage.recent_history(100):
            self.history.insert("end", f"[{ts}] {speaker}: {msg}\n")
        self.history.see("end")

    def _enforce_password(self):
        pwd = simpledialog.askstring("JARVIS Lock", "Enter password:", show="*")
        if pwd != self.config.get("password"):
            messagebox.showerror("Access Denied", "Invalid password")
            self.root.destroy()

    def _add_history(self, speaker: str, message: str):
        self.storage.add_history(speaker, message)
        self.history.insert("end", f"[{dt.datetime.now().strftime('%H:%M:%S')}] {speaker}: {message}\n")
        self.history.see("end")

    def _add_log(self, message: str):
        self.logs.insert("end", f"{dt.datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.logs.see("end")

    def _manual_input(self):
        text = simpledialog.askstring("Command", "Type a command")
        if text:
            self._process_command(text)

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        self.status_var.set("Listening")

    def stop(self):
        self.running = False
        self.status_var.set("Stopped")

    def _listen_loop(self):
        wake_word = self.config.get("wake_word", "hey jarvis")
        self._add_log("Voice loop started")
        while self.running:
            try:
                text = self.stt.record_and_transcribe()
                if not text:
                    continue
                self._add_log(f"Heard: {text}")
                if wake_word in text:
                    command = text.split(wake_word, 1)[-1].strip()
                    if not command:
                        self._speak("Yes, I am listening.")
                        continue
                    self._process_command(command)
            except Exception as e:
                self._add_log(f"Listening error: {e}")
                time.sleep(1)

    def _process_command(self, cmd: str):
        self.status_var.set("Processing")
        self._add_history("User", cmd)
        resp = self.engine.execute(cmd)
        self._add_history("JARVIS", resp.text)
        if resp.speak:
            self._speak(resp.text)
        self.status_var.set("Listening" if self.running else "Idle")

    def _speak(self, text: str):
        self.status_var.set("Speaking")
        threading.Thread(target=self.tts.speak, args=(text,), daemon=True).start()


def check_internet(host="8.8.8.8", port=53, timeout=1):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False


def main():
    root = tk.Tk()
    app = JarvisUI(root)
    app._add_log(f"Internet: {'Online' if check_internet() else 'Offline'}")
    root.mainloop()


if __name__ == "__main__":
    main()
