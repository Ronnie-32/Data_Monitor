"""Move legacy class-period data into reusable timetable schemes."""

from __future__ import annotations

import sqlite3
from datetime import time


def apply_v004(connection: sqlite3.Connection) -> None:
    """Create scheme storage, migrate a complete legacy axis, then retire it."""

    connection.execute(
        """
        CREATE TABLE timetable_schemes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL CHECK (length(trim(name)) > 0),
            axis_mode TEXT NOT NULL CHECK (axis_mode IN ('custom_periods', 'uniform_day')),
            period_count INTEGER NOT NULL CHECK (period_count BETWEEN 1 AND 24),
            day_start TEXT,
            day_end TEXT,
            is_builtin INTEGER NOT NULL DEFAULT 0 CHECK (is_builtin IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CHECK (
                axis_mode = 'custom_periods'
                OR (day_start IS NOT NULL AND day_end IS NOT NULL AND day_end > day_start)
            )
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE timetable_scheme_periods (
            scheme_id INTEGER NOT NULL,
            period_no INTEGER NOT NULL CHECK (period_no BETWEEN 1 AND 24),
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            PRIMARY KEY (scheme_id, period_no),
            FOREIGN KEY (scheme_id) REFERENCES timetable_schemes(id) ON DELETE CASCADE,
            CHECK (end_time > start_time)
        )
        """
    )
    connection.execute(
        """
        ALTER TABLE semesters
        ADD COLUMN timetable_scheme_id INTEGER
        REFERENCES timetable_schemes(id) ON DELETE SET NULL
        """
    )

    legacy = _complete_legacy_periods(connection)
    if legacy is not None:
        now = "1970-01-01T00:00:00"
        cursor = connection.execute(
            """
            INSERT INTO timetable_schemes(
                name, axis_mode, period_count, day_start, day_end,
                is_builtin, created_at, updated_at
            ) VALUES (?, 'custom_periods', 8, NULL, NULL, 1, ?, ?)
            """,
            ("方案1", now, now),
        )
        scheme_id = int(cursor.lastrowid)
        connection.executemany(
            """
            INSERT INTO timetable_scheme_periods(scheme_id, period_no, start_time, end_time)
            VALUES (?, ?, ?, ?)
            """,
            (
                (scheme_id, period_no, start_text, end_text)
                for period_no, start_text, end_text in legacy
            ),
        )
        connection.execute(
            "UPDATE semesters SET timetable_scheme_id = ? WHERE timetable_scheme_id IS NULL",
            (scheme_id,),
        )

    # The old table is migration input only.  Steady-state code must have one
    # source of truth, so leave no legacy table behind for new repositories.
    connection.execute("DROP TABLE IF EXISTS class_periods")


def _complete_legacy_periods(
    connection: sqlite3.Connection,
) -> list[tuple[int, str, str]] | None:
    if not _table_exists(connection, "class_periods"):
        return None
    rows = connection.execute(
        "SELECT period_no, start_time, end_time FROM class_periods ORDER BY period_no"
    ).fetchall()
    if len(rows) != 8 or [int(row[0]) for row in rows] != list(range(1, 9)):
        return None
    normalized: list[tuple[int, str, str]] = []
    previous_end: time | None = None
    for row in rows:
        try:
            start_text = str(row[1])
            end_text = str(row[2])
            start = time.fromisoformat(start_text)
            end = time.fromisoformat(end_text)
        except (TypeError, ValueError):
            return None
        if end <= start or (previous_end is not None and start < previous_end):
            return None
        normalized.append((int(row[0]), start_text, end_text))
        previous_end = end
    return normalized


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone()
        is not None
    )
