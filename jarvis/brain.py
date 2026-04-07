from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import TYPE_CHECKING, Callable

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

from jarvis.config import CONFIG
from jarvis.db import Database
from jarvis.utils import now_time_string

if TYPE_CHECKING:
    from jarvis.system_control import SystemController

FALLBACK_PATH = Path(__file__).resolve().parent.parent / "data" / "fallback_responses.json"


class Brain:
    def __init__(self, db: Database, controller: SystemController, log: Callable[[str, str], None]) -> None:
        self.db = db
        self.controller = controller
        self.log = log
        self.fallback = self._load_fallback()

    def _load_fallback(self) -> dict:
        if FALLBACK_PATH.exists():
            return json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))
        defaults = {
            "en": "I can handle offline tasks like opening apps, screenshots, files, and system controls.",
            "hi": "मैं ऑफलाइन कार्य जैसे ऐप खोलना, स्क्रीनशॉट लेना, फाइल बनाना और सिस्टम कंट्रोल कर सकता हूं।",
        }
        FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        FALLBACK_PATH.write_text(json.dumps(defaults, ensure_ascii=False, indent=2), encoding="utf-8")
        return defaults

    def respond(self, text: str, language: str = "en") -> str:
        lower = text.lower()
        response = ""
        try:
            if any(k in lower for k in ["open chrome", "chrome kholo", "open browser"]):
                response = self.controller.open_app("chrome")
                return response
            if "open notepad" in lower:
                response = self.controller.open_app("notepad")
                return response
            if "close" in lower and "chrome" in lower:
                response = self.controller.close_app("chrome")
                return response
            if "search on google" in lower or "google" in lower and "search" in lower:
                query = lower.replace("search on google", "").replace("search", "").strip() or "jarvis assistant"
                response = self.controller.search_google(query)
                return response
            if "time" in lower or "samay" in lower or "time batao" in lower:
                response = now_time_string(language)
                return response
            if "screenshot" in lower:
                response = self.controller.take_screenshot()
                return response
            if "shutdown" in lower:
                response = self.controller.shutdown()
                return response
            if "restart" in lower:
                response = self.controller.restart()
                return response
            if "open folder" in lower or "folder kholo" in lower:
                folder = text.split("folder", 1)[-1].strip() or str(Path.home())
                response = self.controller.open_folder(folder)
                return response
            if "play music" in lower:
                response = self.controller.play_music()
                return response
            if "increase volume" in lower or "volume badhao" in lower:
                response = self.controller.volume_up()
                return response
            if "decrease volume" in lower or "volume kam" in lower:
                response = self.controller.volume_down()
                return response
            if lower.startswith("create file"):
                payload = text.replace("create file", "", 1).strip()
                path, _, content = payload.partition(" with ")
                response = self.controller.create_file(path.strip(), content.strip())
                return response
            if lower.startswith("delete file"):
                path = text.replace("delete file", "", 1).strip()
                response = self.controller.delete_file(path)
                return response
            if lower.startswith("read file"):
                path = text.replace("read file", "", 1).strip()
                response = self.controller.read_file(path)
                return response
            if "weather" in lower or "मौसम" in lower:
                response = self.get_weather(language)
                return response
            if "send email" in lower:
                response = self.send_email_demo(language)
                return response
            response = self.online_or_fallback(text, language)
            return response
        finally:
            self.db.add_history(text, response or "processed", language)

    def online_or_fallback(self, text: str, language: str) -> str:
        if CONFIG.openai_api_key:
            return f"Online AI configured. Query captured: {text}"
        return self.fallback.get(language, self.fallback["en"])

    def get_weather(self, language: str) -> str:
        if not CONFIG.weather_api_key or requests is None:
            return "Weather API key missing. Offline mode active."
        try:
            res = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": "Delhi", "appid": CONFIG.weather_api_key, "units": "metric"},
                timeout=8,
            )
            res.raise_for_status()
            payload = res.json()
            temp = payload["main"]["temp"]
            desc = payload["weather"][0]["description"]
            if language == "hi":
                return f"वर्तमान तापमान {temp}°C है और मौसम {desc} है"
            return f"Current weather is {desc} with {temp}°C"
        except Exception as exc:
            self.log("WARN", f"Weather fetch failed: {exc}")
            return "Unable to fetch weather right now."

    def send_email_demo(self, language: str) -> str:
        if not CONFIG.user_email or not CONFIG.user_email_password:
            return "Email credentials are not configured."
        try:
            msg = EmailMessage()
            msg["Subject"] = "Test email from JARVIS"
            msg["From"] = CONFIG.user_email
            msg["To"] = CONFIG.user_email
            msg.set_content("This is an automated email from JARVIS.")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
                smtp.login(CONFIG.user_email, CONFIG.user_email_password)
                smtp.send_message(msg)
            return "Email sent successfully"
        except Exception as exc:
            self.log("ERROR", f"Email send failed: {exc}")
            return "Email could not be sent"
