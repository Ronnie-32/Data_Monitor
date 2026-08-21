"""SQLite connection factory for DeskBoard persistence."""

from __future__ import annotations

import sqlite3
from os import PathLike
from pathlib import Path


def connect_database(database: str | PathLike[str]) -> sqlite3.Connection:
    """Open a database and prove foreign-key enforcement for this connection."""
    database_text = str(database)
    if database_text != ":memory:":
        Path(database).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_text)
    connection.execute("PRAGMA foreign_keys = ON")
    enabled = connection.execute("PRAGMA foreign_keys").fetchone()
    if enabled is None or enabled[0] != 1:
        connection.close()
        raise RuntimeError("SQLite foreign-key enforcement could not be enabled")
    return connection
