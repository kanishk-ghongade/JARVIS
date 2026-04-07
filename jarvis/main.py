from __future__ import annotations

import traceback

from jarvis.brain import Brain
from jarvis.db import Database
from jarvis.speech import SpeechResult, SpeechService
from jarvis.system_control import SystemController
from jarvis.ui import JarvisUI


class JarvisApp:
    def __init__(self) -> None:
        self.db = Database()
        self.controller = SystemController(self._log)
        self.brain = Brain(self.db, self.controller, self._log)
        self.speech = SpeechService(self._log)
        self.ui = JarvisUI(on_start=self.start, on_stop=self.stop, on_text_command=self.run_text_command)

    def _log(self, level: str, message: str) -> None:
        self.db.add_log(level, message)
        self.ui.post("logs", f"[{level}] {message}")

    def start(self) -> None:
        if not self.ui.ask_password_if_needed():
            return
        self.ui.set_status("Listening")
        self.speech.start_continuous_listening(self._on_speech)
        self._log("INFO", "Assistant started")

    def stop(self) -> None:
        self.speech.stop()
        self.ui.set_status("Stopped")
        self._log("INFO", "Assistant stopped")

    def run_text_command(self, text: str) -> None:
        if not text:
            return
        lang = "hi" if any("\u0900" <= ch <= "\u097F" for ch in text) else "en"
        self._handle(text, lang)

    def _on_speech(self, result: SpeechResult) -> None:
        self.ui.set_status("Processing")
        self._handle(result.text, result.language)

    def _handle(self, text: str, language: str) -> None:
        try:
            self.ui.post("history", f"YOU ({language}): {text}")
            answer = self.brain.respond(text, language)
            self.ui.post("history", f"JARVIS: {answer}")
            self.ui.set_status("Speaking")
            self.speech.speak(answer, language)
            self.ui.set_status("Listening")
        except Exception as exc:
            self._log("ERROR", f"Command error: {exc}\n{traceback.format_exc()}")
            self.ui.post("history", "JARVIS: Sorry, I had an internal error")
            self.ui.set_status("Listening")

    def run(self) -> None:
        self.ui.run()


def main() -> None:
    JarvisApp().run()


if __name__ == "__main__":
    main()
