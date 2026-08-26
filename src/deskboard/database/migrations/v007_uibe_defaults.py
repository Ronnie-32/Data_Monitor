"""Seed and normalize the user-facing UIBE timetable sample defaults."""

from __future__ import annotations

import sqlite3

DEFAULT_TIMESTAMP = "1970-01-01T00:00:00"
UIBE_PERIODS = (
    (1, "08:00:00", "09:30:00"),
    (2, "09:50:00", "11:20:00"),
    (3, "11:30:00", "12:10:00"),
    (4, "13:30:00", "15:00:00"),
    (5, "15:20:00", "16:50:00"),
    (6, "17:00:00", "17:40:00"),
    (7, "18:30:00", "20:00:00"),
    (8, "20:10:00", "20:50:00"),
)
LEGACY_BUILTIN_NAMES = frozenset({"方案1", "Default方案", "Legacy 8 periods"})


def apply_v007(connection: sqlite3.Connection) -> None:
    """Make the single UIBE sample scheme and sample semester the defaults.

    Existing user-created schemes remain untouched.  Only the known generated
    aliases and an unbound, identical ``UIBE copy`` are removed; semesters
    bound to a removed alias are rebound before deletion.
    """

    canonical_id = _find_canonical_scheme(connection)
    created_default = canonical_id is None
    if canonical_id is None:
        canonical_id = _create_uibe_scheme(connection)
    else:
        connection.execute(
            """
            UPDATE timetable_schemes
            SET name = 'UIBE', is_builtin = 1
            WHERE id = ?
            """,
            (canonical_id,),
        )

    _remove_generated_duplicates(connection, canonical_id)
    _normalize_sample_semesters(
        connection,
        canonical_id,
        bind_unbound=created_default,
    )


def _find_canonical_scheme(connection: sqlite3.Connection) -> int | None:
    row = connection.execute(
        "SELECT id FROM timetable_schemes WHERE trim(name) = 'UIBE' ORDER BY id LIMIT 1"
    ).fetchone()
    if row is not None:
        return int(row[0])

    row = connection.execute(
        """
        SELECT id
        FROM timetable_schemes
        WHERE is_builtin = 1 AND trim(name) IN (?, ?, ?)
        ORDER BY id
        LIMIT 1
        """,
        tuple(sorted(LEGACY_BUILTIN_NAMES)),
    ).fetchone()
    return None if row is None else int(row[0])


def _create_uibe_scheme(connection: sqlite3.Connection) -> int:
    cursor = connection.execute(
        """
        INSERT INTO timetable_schemes(
            name, axis_mode, period_count, day_start, day_end,
            is_builtin, created_at, updated_at
        ) VALUES ('UIBE', 'custom_periods', 8, NULL, NULL, 1, ?, ?)
        """,
        (DEFAULT_TIMESTAMP, DEFAULT_TIMESTAMP),
    )
    scheme_id = int(cursor.lastrowid)
    connection.executemany(
        """
        INSERT INTO timetable_scheme_periods(
            scheme_id, period_no, start_time, end_time
        ) VALUES (?, ?, ?, ?)
        """,
        [(scheme_id, *period) for period in UIBE_PERIODS],
    )
    return scheme_id


def _remove_generated_duplicates(
    connection: sqlite3.Connection,
    canonical_id: int,
) -> None:
    rows = connection.execute(
        "SELECT id, name, is_builtin FROM timetable_schemes WHERE id <> ?",
        (canonical_id,),
    ).fetchall()
    for scheme_id, name, is_builtin in rows:
        normalized_name = str(name).strip()
        is_legacy_builtin = (
            int(is_builtin) == 1 and normalized_name in LEGACY_BUILTIN_NAMES
        )
        is_unbound_copy = (
            normalized_name == "UIBE copy"
            and _scheme_is_unbound(connection, int(scheme_id))
            and _same_scheme_payload(connection, canonical_id, int(scheme_id))
        )
        if not (is_legacy_builtin or is_unbound_copy):
            continue
        connection.execute(
            "UPDATE semesters SET timetable_scheme_id = ? WHERE timetable_scheme_id = ?",
            (canonical_id, scheme_id),
        )
        connection.execute("DELETE FROM timetable_schemes WHERE id = ?", (scheme_id,))


def _scheme_is_unbound(connection: sqlite3.Connection, scheme_id: int) -> bool:
    row = connection.execute(
        "SELECT 1 FROM semesters WHERE timetable_scheme_id = ? LIMIT 1",
        (scheme_id,),
    ).fetchone()
    return row is None


def _same_scheme_payload(
    connection: sqlite3.Connection,
    first_id: int,
    second_id: int,
) -> bool:
    first = connection.execute(
        """
        SELECT axis_mode, period_count, day_start, day_end
        FROM timetable_schemes
        WHERE id = ?
        """,
        (first_id,),
    ).fetchone()
    second = connection.execute(
        """
        SELECT axis_mode, period_count, day_start, day_end
        FROM timetable_schemes
        WHERE id = ?
        """,
        (second_id,),
    ).fetchone()
    if first != second:
        return False
    first_periods = connection.execute(
        """
        SELECT period_no, start_time, end_time
        FROM timetable_scheme_periods
        WHERE scheme_id = ?
        ORDER BY period_no
        """,
        (first_id,),
    ).fetchall()
    second_periods = connection.execute(
        """
        SELECT period_no, start_time, end_time
        FROM timetable_scheme_periods
        WHERE scheme_id = ?
        ORDER BY period_no
        """,
        (second_id,),
    ).fetchall()
    return first_periods == second_periods


def _normalize_sample_semesters(
    connection: sqlite3.Connection,
    canonical_id: int,
    *,
    bind_unbound: bool,
) -> None:
    connection.execute(
        "UPDATE semesters SET name = '样例' WHERE trim(name) = '大三上'"
    )
    has_semester = connection.execute("SELECT 1 FROM semesters LIMIT 1").fetchone()
    if has_semester is not None:
        if bind_unbound:
            connection.execute(
                """
                UPDATE semesters
                SET timetable_scheme_id = ?
                WHERE timetable_scheme_id IS NULL
                """,
                (canonical_id,),
            )
        return
    connection.execute(
        """
        INSERT INTO semesters(
            name, start_monday, total_weeks, is_active, created_at, updated_at,
            timetable_scheme_id
        ) VALUES ('样例', '2026-08-03', 16, 1, ?, ?, ?)
        """,
        (DEFAULT_TIMESTAMP, DEFAULT_TIMESTAMP, canonical_id),
    )
