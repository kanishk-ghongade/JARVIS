from __future__ import annotations

import os
import platform
import subprocess
import webbrowser
from pathlib import Path
from typing import Callable

import pyautogui


class SystemController:
    def __init__(self, log: Callable[[str, str], None]) -> None:
        self.log = log

    def open_app(self, app_name: str) -> str:
        lower = app_name.lower()
        app_map = {
            "chrome": "start chrome",
            "notepad": "start notepad",
            "calculator": "start calc",
            "paint": "start mspaint",
            "explorer": "start explorer",
        }
        command = app_map.get(lower, f"start {app_name}")
        subprocess.Popen(command, shell=True)
        return f"Opening {app_name}"

    def close_app(self, app_name: str) -> str:
        executable = app_name if app_name.endswith(".exe") else f"{app_name}.exe"
        subprocess.Popen(f"taskkill /f /im {executable}", shell=True)
        return f"Closing {app_name}"

    def search_google(self, query: str) -> str:
        webbrowser.open(f"https://www.google.com/search?q={query.strip().replace(' ', '+')}")
        return f"Searching Google for {query}"

    def take_screenshot(self) -> str:
        path = Path.cwd() / "data" / "latest_screenshot.png"
        path.parent.mkdir(exist_ok=True, parents=True)
        pyautogui.screenshot(str(path))
        return f"Screenshot saved at {path}"

    def create_file(self, file_path: str, content: str = "") -> str:
        path = Path(file_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"File created: {path}"

    def delete_file(self, file_path: str) -> str:
        path = Path(file_path).expanduser()
        if path.exists():
            path.unlink()
            return f"Deleted file: {path}"
        return "File not found"

    def read_file(self, file_path: str) -> str:
        path = Path(file_path).expanduser()
        if not path.exists():
            return "File not found"
        return path.read_text(encoding="utf-8")[:1000]

    def open_folder(self, folder_path: str) -> str:
        path = Path(folder_path).expanduser()
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return f"Opening folder {path}"

    def volume_up(self) -> str:
        for _ in range(8):
            pyautogui.press("volumeup")
        return "Volume increased"

    def volume_down(self) -> str:
        for _ in range(8):
            pyautogui.press("volumedown")
        return "Volume decreased"

    def shutdown(self) -> str:
        if platform.system() == "Windows":
            subprocess.Popen("shutdown /s /t 5", shell=True)
            return "Shutting down the system in 5 seconds"
        return "Shutdown is supported on Windows target build"

    def restart(self) -> str:
        if platform.system() == "Windows":
            subprocess.Popen("shutdown /r /t 5", shell=True)
            return "Restarting system in 5 seconds"
        return "Restart is supported on Windows target build"

    def play_music(self, folder: str | None = None) -> str:
        music_dir = Path(folder) if folder else Path.home() / "Music"
        if not music_dir.exists():
            return "Music folder not found"
        tracks = [p for p in music_dir.iterdir() if p.suffix.lower() in {".mp3", ".wav"}]
        if not tracks:
            return "No tracks found"

        selected = tracks[0]
        if platform.system() == "Windows":
            os.startfile(selected)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(selected)])
        else:
            subprocess.Popen(["xdg-open", str(selected)])
        return f"Playing {selected.name}"
