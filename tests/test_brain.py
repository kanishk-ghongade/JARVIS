from pathlib import Path

from jarvis.brain import Brain
from jarvis.db import Database


class FakeController:
    def open_app(self, app_name: str) -> str:
        return f"open:{app_name}"

    def close_app(self, app_name: str) -> str:
        return f"close:{app_name}"

    def search_google(self, query: str) -> str:
        return f"search:{query}"

    def take_screenshot(self) -> str:
        return "shot"

    def shutdown(self) -> str:
        return "shutdown"

    def restart(self) -> str:
        return "restart"

    def open_folder(self, folder_path: str) -> str:
        return f"folder:{folder_path}"

    def play_music(self, folder=None) -> str:
        return "music"

    def volume_up(self) -> str:
        return "up"

    def volume_down(self) -> str:
        return "down"

    def create_file(self, file_path: str, content: str = "") -> str:
        return f"create:{file_path}:{content}"

    def delete_file(self, file_path: str) -> str:
        return f"delete:{file_path}"

    def read_file(self, file_path: str) -> str:
        return f"read:{file_path}"


def test_predefined_commands(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    brain = Brain(db, FakeController(), lambda *_: None)

    assert brain.respond("open chrome") == "open:chrome"
    assert brain.respond("search on google python") == "search:python"
    assert brain.respond("take screenshot") == "shot"
    assert brain.respond("increase volume") == "up"
    assert brain.respond("decrease volume") == "down"
    assert brain.respond("create file notes.txt with hello") == "create:notes.txt:hello"


def test_offline_fallback(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    brain = Brain(db, FakeController(), lambda *_: None)
    answer = brain.respond("random unhandled prompt", "en")
    assert "offline" in answer.lower() or "control" in answer.lower()
