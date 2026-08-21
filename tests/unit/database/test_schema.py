from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import (
    LOGICAL_TABLES,
    REPOSITORY_TABLE_OWNERSHIP,
    get_schema_version,
    migrate,
)
from deskboard.infrastructure.paths import database_path
from deskboard.repositories.settings_repository import SettingsRepository


def open_migrated(path: Path) -> sqlite3.Connection:
    connection = connect_database(path)
    migrate(connection)
    return connection


def user_tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    )
    return {str(row[0]) for row in rows}


def test_connection_factory_enables_and_verifies_foreign_keys_per_connection(tmp_path):
    database = database_path(tmp_path)

    first = connect_database(database)
    second = connect_database(database)

    assert first.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert second.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert database.is_file()
    assert database == tmp_path / "DeskBoard" / "data" / "deskboard.db"


def test_v001_creates_exact_logical_tables_version_and_ownership(tmp_path):
    connection = open_migrated(tmp_path / "deskboard.db")

    assert user_tables(connection) == LOGICAL_TABLES
    assert len(LOGICAL_TABLES) == 14
    assert get_schema_version(connection) == 1
    assert REPOSITORY_TABLE_OWNERSHIP == {
        "SettingsRepository": frozenset({"app_settings"}),
        "TodoRepository": frozenset({"todos"}),
        "CourseRepository": frozenset(
            {
                "semesters",
                "recurring_courses",
                "course_cancellations",
                "one_off_courses",
                "class_periods",
            }
        ),
        "ProfileRepository": frozenset({"profiles", "profile_widgets"}),
        "WeatherRepository": frozenset({"weather_cities"}),
        "FinanceRepository": frozenset({"finance_preferences"}),
        "NetworkRepository": frozenset({"network_cache", "network_state"}),
    }
    owned_tables = set().union(*REPOSITORY_TABLE_OWNERSHIP.values())
    assert owned_tables == LOGICAL_TABLES - {"schema_meta"}


def test_cancellation_period_and_profile_widget_constraints(tmp_path):
    connection = open_migrated(tmp_path / "deskboard.db")
    connection.execute(
        "INSERT INTO semesters(id, name, start_monday, total_weeks, created_at, updated_at) "
        "VALUES (1, 'Fall', '2026-09-07', 16, 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO recurring_courses("
        "id, semester_id, name, weekday, start_time, end_time, start_week, end_week, "
        "created_at, updated_at) VALUES (1, 1, 'Stats', 1, '08:00', '09:30', 1, 16, "
        "'now', 'now')"
    )
    connection.execute(
        "INSERT INTO course_cancellations(recurring_course_id, occurrence_date) "
        "VALUES (1, '2026-09-07')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO course_cancellations(recurring_course_id, occurrence_date) "
            "VALUES (1, '2026-09-07')"
        )
    for invalid_period in (0, 9):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO class_periods(period_no, start_time, end_time) VALUES (?, ?, ?)",
                (invalid_period, "08:00", "09:30"),
            )
    connection.execute(
        "INSERT INTO profiles(id, name, is_builtin, created_at, updated_at) "
        "VALUES (1, 'Default', 1, 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO profile_widgets(profile_id, widget_key, visible, x, y, w, h) "
        "VALUES (1, 'weather', 1, 0, 0, 4, 3)"
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO profile_widgets(profile_id, widget_key, visible, x, y, w, h) "
            "VALUES (1, 'weather', 1, 1, 1, 4, 3)"
        )


def test_semester_recurring_course_and_profile_deletes_cascade(tmp_path):
    connection = open_migrated(tmp_path / "deskboard.db")
    connection.execute(
        "INSERT INTO semesters(id, name, start_monday, total_weeks, created_at, updated_at) "
        "VALUES (1, 'Fall', '2026-09-07', 16, 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO recurring_courses("
        "id, semester_id, name, weekday, start_time, end_time, start_week, end_week, "
        "created_at, updated_at) VALUES (1, 1, 'Stats', 1, '08:00', '09:30', 1, 16, "
        "'now', 'now')"
    )
    connection.execute(
        "INSERT INTO course_cancellations(recurring_course_id, occurrence_date) "
        "VALUES (1, '2026-09-07')"
    )
    connection.execute(
        "INSERT INTO one_off_courses("
        "id, semester_id, name, course_date, start_time, end_time, created_at, updated_at) "
        "VALUES (1, 1, 'Review', '2026-09-08', '10:00', '11:00', 'now', 'now')"
    )
    connection.execute("DELETE FROM recurring_courses WHERE id = 1")
    assert connection.execute("SELECT COUNT(*) FROM course_cancellations").fetchone()[0] == 0
    connection.execute(
        "INSERT INTO recurring_courses("
        "id, semester_id, name, weekday, start_time, end_time, start_week, end_week, "
        "created_at, updated_at) VALUES (2, 1, 'Stats', 1, '08:00', '09:30', 1, 16, "
        "'now', 'now')"
    )
    connection.execute(
        "INSERT INTO course_cancellations(recurring_course_id, occurrence_date) "
        "VALUES (2, '2026-09-14')"
    )
    connection.execute("DELETE FROM semesters WHERE id = 1")
    for table in ("recurring_courses", "course_cancellations", "one_off_courses"):
        assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0

    connection.execute(
        "INSERT INTO profiles(id, name, is_builtin, created_at, updated_at) "
        "VALUES (1, 'Default', 1, 'now', 'now')"
    )
    connection.execute(
        "INSERT INTO profile_widgets(profile_id, widget_key, visible, x, y, w, h) "
        "VALUES (1, 'todo', 1, 0, 0, 4, 3)"
    )
    connection.execute("DELETE FROM profiles WHERE id = 1")
    assert connection.execute("SELECT COUNT(*) FROM profile_widgets").fetchone()[0] == 0


def test_schema_has_no_legacy_backup_event_or_soft_delete_storage(tmp_path):
    connection = open_migrated(tmp_path / "deskboard.db")

    assert not ({"schedule_items", "events", "database_backups"} & user_tables(connection))
    for table in LOGICAL_TABLES:
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        assert "deleted_at" not in columns


def test_profile_widget_columns_use_the_specified_spatial_vocabulary(tmp_path):
    connection = open_migrated(tmp_path / "deskboard.db")

    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(profile_widgets)")
    }

    assert {"x", "y", "w", "h"} <= columns
    assert not ({"grid_x", "grid_y", "grid_width", "grid_height"} & columns)


def test_profile_limit_is_not_hidden_in_persistence(tmp_path):
    connection = open_migrated(tmp_path / "deskboard.db")
    rows = [(1, "Default", 1, "now", "now")]
    rows.extend((index + 2, f"User {index}", 0, "now", "now") for index in range(9))

    connection.executemany(
        "INSERT INTO profiles(id, name, is_builtin, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )

    assert connection.execute("SELECT COUNT(*) FROM profiles").fetchone()[0] == 10


def test_settings_repository_is_sqlite_only_get_set_delete(tmp_path):
    database = tmp_path / "DeskBoard" / "data" / "deskboard.db"
    connection = open_migrated(database)
    repository = SettingsRepository(connection)

    assert repository.get("autostart") is None
    repository.set("autostart", "false")
    repository.set("autostart", "true")
    assert repository.get("autostart") == "true"
    assert repository.delete("autostart") is True
    assert repository.delete("autostart") is False
    assert repository.get("autostart") is None
    assert [path for path in database.parents[1].rglob("*") if path.is_file()] == [database]


def test_settings_repository_source_accesses_only_its_owned_table():
    source = Path("src/deskboard/repositories/settings_repository.py").read_text(
        encoding="utf-8"
    )

    assert "app_settings" in source
    for forbidden_table in LOGICAL_TABLES - {"schema_meta", "app_settings"}:
        assert forbidden_table not in source
