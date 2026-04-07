from __future__ import annotations

import queue
import tempfile
import threading
import wave
from dataclasses import dataclass
from typing import Callable, Optional

import pyttsx3
import speech_recognition as sr

from jarvis.config import CONFIG
from jarvis.utils import detect_language

try:
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover
    WhisperModel = None


@dataclass
class SpeechResult:
    text: str
    language: str


class SpeechService:
    def __init__(self, log: Callable[[str, str], None]):
        self.log = log
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts = pyttsx3.init()
        self.tts.setProperty("rate", 178)
        self._stop_event = threading.Event()
        self._audio_queue: queue.Queue[sr.AudioData] = queue.Queue(maxsize=8)
        self.listener_thread: Optional[threading.Thread] = None
        self.processor_thread: Optional[threading.Thread] = None
        self.on_speech: Optional[Callable[[SpeechResult], None]] = None
        self.whisper = None
        if WhisperModel is not None:
            try:
                self.whisper = WhisperModel("small", compute_type="int8")
            except Exception as exc:
                self.log("WARN", f"Whisper model load failed, offline STT disabled until model is available: {exc}")

    def speak(self, text: str, language: str = "en") -> None:
        self.log("INFO", f"Speaking: {text}")
        for voice in self.tts.getProperty("voices"):
            voice_name = getattr(voice, "name", "").lower()
            if language == "hi" and ("hindi" in voice_name or "india" in voice_name):
                self.tts.setProperty("voice", voice.id)
                break
            if language == "en" and "english" in voice_name:
                self.tts.setProperty("voice", voice.id)
        self.tts.say(text)
        self.tts.runAndWait()

    def start_continuous_listening(self, callback: Callable[[SpeechResult], None]) -> None:
        self.on_speech = callback
        self._stop_event.clear()
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.listener_thread.start()
        self.processor_thread.start()
        self.log("INFO", "Continuous listening started")

    def stop(self) -> None:
        self._stop_event.set()
        self.log("INFO", "Speech service stopping")

    def _listen_loop(self) -> None:
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            while not self._stop_event.is_set():
                try:
                    audio = self.recognizer.listen(source, phrase_time_limit=7, timeout=1)
                    if not self._audio_queue.full():
                        self._audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    continue
                except Exception as exc:
                    self.log("ERROR", f"Listen error: {exc}")

    def _process_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                audio = self._audio_queue.get(timeout=1)
            except queue.Empty:
                continue
            try:
                text = self._transcribe(audio)
                if not text:
                    continue
                if CONFIG.wake_word not in text.lower() and "jarvis" not in text.lower():
                    continue
                cleaned = text.lower().replace(CONFIG.wake_word, "").replace("jarvis", "").strip(" ,")
                cleaned = cleaned or "hello"
                lang = detect_language(cleaned)
                if self.on_speech:
                    self.on_speech(SpeechResult(text=cleaned, language=lang))
            except Exception as exc:
                self.log("ERROR", f"Processing error: {exc}")

    def _transcribe(self, audio: sr.AudioData) -> str:
        if self.whisper is None:
            self.log("WARN", "No offline Whisper model loaded; skipped transcription")
            return ""

        wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_wav:
            with wave.open(temp_wav.name, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(wav_bytes)
            segments, _ = self.whisper.transcribe(temp_wav.name, language=None, beam_size=1)
            return " ".join(seg.text for seg in segments).strip()
