"""Normalize the built-in timetable scheme name for existing databases."""

from __future__ import annotations

import sqlite3


def apply_v005(connection: sqlite3.Connection) -> None:
    """Rename only legacy built-in scheme labels; leave user schemes intact."""

    connection.execute(
        """
        UPDATE timetable_schemes
        SET name = 'Default方案'
        WHERE is_builtin = 1 AND trim(name) IN ('方案1', 'Legacy 8 periods')
        """
    )
