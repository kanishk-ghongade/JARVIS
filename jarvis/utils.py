from __future__ import annotations

import datetime as dt


def detect_language(text: str) -> str:
    devanagari = any("\u0900" <= ch <= "\u097F" for ch in text)
    hindi_keywords = ["kya", "batao", "samay", "kholo", "band", "maujood", "मौसम", "समय"]
    lower = text.lower()
    if devanagari or any(k in lower for k in hindi_keywords):
        return "hi"
    return "en"


def now_time_string(language: str) -> str:
    now = dt.datetime.now()
    if language == "hi":
        return f"अभी समय {now.strftime('%I:%M %p')} है"
    return f"The current time is {now.strftime('%I:%M %p')}"
