from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "jarvis.db"


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_text TEXT NOT NULL,
                response_text TEXT NOT NULL,
                language TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def add_log(self, level: str, message: str) -> None:
        self.conn.execute("INSERT INTO logs(level, message) VALUES(?, ?)", (level, message))
        self.conn.commit()

    def save_memory(self, key: str, value: str) -> None:
        self.conn.execute(
            """
            INSERT INTO memory(key, value) VALUES(?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        self.conn.commit()

    def get_memory(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def add_history(self, command_text: str, response_text: str, language: str) -> None:
        self.conn.execute(
            "INSERT INTO history(command_text, response_text, language) VALUES(?, ?, ?)",
            (command_text, response_text, language),
        )
        self.conn.commit()

    def latest_history(self, limit: int = 30) -> Iterable[tuple]:
        return self.conn.execute(
            "SELECT command_text, response_text, language, created_at FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
