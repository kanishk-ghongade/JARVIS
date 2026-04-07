from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class JarvisConfig:
    wake_word: str = "hey jarvis"
    assistant_name: str = "JARVIS"
    default_language: str = "en"
    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
    news_api_key: str = os.getenv("NEWS_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    user_email: str = os.getenv("JARVIS_EMAIL", "")
    user_email_password: str = os.getenv("JARVIS_EMAIL_PASSWORD", "")
    security_password_hash: str = os.getenv("JARVIS_PASSWORD_HASH", "")

    def verify_password(self, password: str) -> bool:
        if not self.security_password_hash:
            return True
        return hashlib.sha256(password.encode("utf-8")).hexdigest() == self.security_password_hash


CONFIG = JarvisConfig()
