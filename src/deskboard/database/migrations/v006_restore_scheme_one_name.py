"""Restore the user's original built-in timetable scheme and label."""

from __future__ import annotations

import sqlite3


def apply_v006(connection: sqlite3.Connection) -> None:
    """Prefer the user's existing ``方案1`` and remove the generated default.

    A previous build could have both a user-created ``方案1`` and the generated
    built-in ``Default方案``.  In that case the user scheme is promoted and all
    semesters bound to the generated row are moved without touching its period
    data.  If no user scheme exists, the generated built-in row is simply
    renamed so its data and ID survive the migration.
    """

    rows = connection.execute(
        """
        SELECT id, name, is_builtin, created_at
        FROM timetable_schemes
        ORDER BY id
        """
    ).fetchall()
    scheme_one_rows = [row for row in rows if str(row[1]).strip() == "方案1"]
    legacy_rows = [
        row
        for row in rows
        if int(row[2]) == 1
        and str(row[1]).strip() in {"Default方案", "Legacy 8 periods"}
    ]

    canonical = _choose_canonical_scheme(scheme_one_rows, legacy_rows)
    if canonical is None:
        return
    canonical_id = int(canonical[0])
    connection.execute(
        "UPDATE timetable_schemes SET name = '方案1', is_builtin = 1 WHERE id = ?",
        (canonical_id,),
    )

    stale_ids = {
        int(row[0])
        for row in legacy_rows
        if int(row[0]) != canonical_id
    }
    # A v006 build may already have renamed the generated row to 方案1.  Its
    # epoch timestamp identifies that migration-created duplicate; preserve a
    # real user/built-in scheme with the same display name.
    if any(int(row[2]) == 0 for row in scheme_one_rows):
        stale_ids.update(
            int(row[0])
            for row in scheme_one_rows
            if int(row[0]) != canonical_id
            and int(row[2]) == 1
            and str(row[3]) == "1970-01-01T00:00:00"
        )

    for stale_id in stale_ids:
        connection.execute(
            "UPDATE semesters SET timetable_scheme_id = ? WHERE timetable_scheme_id = ?",
            (canonical_id, stale_id),
        )
        connection.execute("DELETE FROM timetable_schemes WHERE id = ?", (stale_id,))


def _choose_canonical_scheme(scheme_one_rows, legacy_rows):
    if scheme_one_rows:
        user_rows = [row for row in scheme_one_rows if int(row[2]) == 0]
        has_generated_duplicate = any(
            str(row[3]) == "1970-01-01T00:00:00" for row in scheme_one_rows
        )
        if user_rows and (legacy_rows or has_generated_duplicate):
            return user_rows[0]
        builtin_rows = [row for row in scheme_one_rows if int(row[2]) == 1]
        return builtin_rows[0] if builtin_rows else user_rows[0]
    return legacy_rows[0] if legacy_rows else None
