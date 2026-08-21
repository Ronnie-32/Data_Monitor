"""SQLite owner for the small ``app_settings`` key/value table."""

from __future__ import annotations

import sqlite3


class SettingsRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, key: str) -> str | None:
        row = self._connection.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (self._validated_key(key),),
        ).fetchone()
        return None if row is None else str(row[0])

    def set(self, key: str, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("setting value must be a string")
        self._connection.execute(
            """
            INSERT INTO app_settings(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (self._validated_key(key), value),
        )
        self._connection.commit()

    def delete(self, key: str) -> bool:
        cursor = self._connection.execute(
            "DELETE FROM app_settings WHERE key = ?",
            (self._validated_key(key),),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _validated_key(key: str) -> str:
        if not isinstance(key, str):
            raise TypeError("setting key must be a string")
        if not key.strip():
            raise ValueError("setting key must not be empty")
        return key
