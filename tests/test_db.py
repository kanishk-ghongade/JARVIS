from pathlib import Path

from jarvis.db import Database


def test_db_roundtrip(tmp_path: Path):
    db = Database(tmp_path / "jarvis.db")
    db.add_log("INFO", "hello")
    db.save_memory("name", "jarvis")
    assert db.get_memory("name") == "jarvis"
    db.add_history("open chrome", "Opening chrome", "en")
    rows = list(db.latest_history())
    assert rows
    assert rows[0][0] == "open chrome"
