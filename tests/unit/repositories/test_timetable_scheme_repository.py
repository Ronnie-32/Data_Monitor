from __future__ import annotations

import sqlite3
from datetime import datetime, time

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.migrations.v001_initial import apply_v001
from deskboard.database.schema import get_schema_version, migrate
from deskboard.models.course import TimetableSchemePeriod
from deskboard.repositories.course_repository import CourseRepository


def test_fresh_schema_has_scheme_tables_and_no_legacy_class_periods():
    connection = connect_database(":memory:")
    migrate(connection)

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    }

    assert get_schema_version(connection) == 6
    assert "class_periods" not in tables
    assert {"timetable_schemes", "timetable_scheme_periods"} <= tables
    assert "timetable_scheme_id" in {
        row[1] for row in connection.execute("PRAGMA table_info(semesters)")
    }


def test_complete_legacy_periods_are_copied_and_bound_to_existing_semesters():
    connection = connect_database(":memory:")
    connection.execute("BEGIN")
    apply_v001(connection)
    connection.execute(
        "INSERT INTO semesters("
        "id, name, start_monday, total_weeks, is_active, created_at, updated_at) "
        "VALUES (1, 'Fall', '2026-09-07', 16, 1, 'now', 'now')"
    )
    periods = [(index, f"{7 + index:02d}:00", f"{8 + index:02d}:00") for index in range(1, 9)]
    connection.executemany(
        "INSERT INTO class_periods(period_no, start_time, end_time) VALUES (?, ?, ?)",
        periods,
    )
    connection.commit()

    migrate(connection)

    row = connection.execute(
        "SELECT id, timetable_scheme_id FROM semesters WHERE id = 1"
    ).fetchone()
    assert row[1] is not None
    scheme = CourseRepository(connection).get_timetable_scheme(row[1])
    assert scheme is not None and scheme.is_builtin is True
    assert [(item.period_no, item.start_time, item.end_time) for item in scheme.periods] == [
        (index, time(7 + index), time(8 + index)) for index in range(1, 9)
    ]


def test_repository_scheme_save_is_atomic_and_normalized():
    connection = connect_database(":memory:")
    migrate(connection)
    repository = CourseRepository(connection)
    now = datetime(2026, 8, 25, 10, 30)

    scheme = repository.create_timetable_scheme(
        name="Study",
        axis_mode="custom_periods",
        period_count=2,
        day_start=None,
        day_end=None,
        periods=(
            TimetableSchemePeriod(1, time(8), time(9)),
            TimetableSchemePeriod(2, time(10), time(11)),
        ),
        now=now,
    )
    assert scheme.periods[1].start_time == time(10)

    with pytest.raises(sqlite3.IntegrityError):
        repository.replace_timetable_scheme(
            scheme.id,
            name="Broken",
            axis_mode="custom_periods",
            period_count=2,
            day_start=None,
            day_end=None,
            periods=(TimetableSchemePeriod(1, time(8), time(9)),),
            now=now,
        )
    assert repository.get_timetable_scheme(scheme.id).name == "Study"
