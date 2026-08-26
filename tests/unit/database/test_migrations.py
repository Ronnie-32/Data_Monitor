from __future__ import annotations

import sqlite3

import pytest

from deskboard.database import schema
from deskboard.database.connection import connect_database
from deskboard.database.migrations.v001_initial import apply_v001
from deskboard.database.migrations.v002_grid_48 import apply_v002
from deskboard.database.migrations.v003_profile_font import apply_v003
from deskboard.database.migrations.v004_timetable_schemes import apply_v004
from deskboard.database.schema import (
    CURRENT_SCHEMA_VERSION,
    MigrationError,
    get_schema_version,
    migrate,
)


def table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def test_fresh_migration_commits_current_version_and_second_run_is_noop(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    connection.execute("INSERT INTO app_settings(key, value) VALUES ('marker', 'kept')")
    connection.commit()

    migrate(connection)

    assert CURRENT_SCHEMA_VERSION == 6
    assert get_schema_version(connection) == 6
    assert connection.execute(
        "SELECT value FROM app_settings WHERE key = 'marker'"
    ).fetchone()[0] == "kept"


def test_migration_runner_rolls_back_all_ddl_on_failure(tmp_path, monkeypatch):
    connection = connect_database(tmp_path / "deskboard.db")

    def broken_migration(target: sqlite3.Connection) -> None:
        target.execute("CREATE TABLE partial_state(id INTEGER PRIMARY KEY)")
        raise RuntimeError("boom")

    monkeypatch.setattr(schema, "MIGRATIONS", {1: apply_v001, 2: broken_migration})

    with pytest.raises(RuntimeError, match="boom"):
        migrate(connection)

    assert table_names(connection) == set()
    assert connection.in_transaction is False


def test_v001_does_not_commit_its_own_transaction():
    connection = connect_database(":memory:")
    connection.execute("BEGIN")

    apply_v001(connection)
    connection.rollback()

    assert table_names(connection) == set()


def test_existing_v001_database_migrates_to_current_profile_and_timetable_contract(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    connection.execute("BEGIN")
    apply_v001(connection)
    connection.commit()

    migrate(connection)

    assert get_schema_version(connection) == 6
    assert connection.execute(
        "SELECT 1 FROM pragma_table_info('profiles') WHERE name = 'grid_columns'"
    ).fetchone() is not None
    assert "BETWEEN 1 AND 48" in connection.execute(
        "SELECT sql FROM sqlite_master WHERE name = 'profile_widgets'"
    ).fetchone()[0]
    assert connection.execute(
        "SELECT 1 FROM pragma_table_info('profiles') WHERE name = 'font_key'"
    ).fetchone() is not None
    assert connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'timetable_schemes'"
    ).fetchone() is not None
    assert connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'class_periods'"
    ).fetchone() is None


def test_existing_scheme_one_is_restored_as_scheme_one_on_upgrade():
    connection = connect_database(":memory:")
    apply_v001(connection)
    connection.executemany(
        "INSERT INTO class_periods(period_no, start_time, end_time) VALUES (?, ?, ?)",
        [
            (period_no, f"{7 + period_no:02d}:00:00", f"{8 + period_no:02d}:00:00")
            for period_no in range(1, 9)
        ],
    )
    connection.commit()

    connection.execute("BEGIN")
    apply_v002(connection)
    apply_v003(connection)
    apply_v004(connection)
    connection.execute("UPDATE schema_meta SET schema_version = 4 WHERE singleton = 1")
    connection.execute("UPDATE timetable_schemes SET name = '方案1'")
    connection.commit()

    migrate(connection)

    row = connection.execute(
        "SELECT name, is_builtin FROM timetable_schemes"
    ).fetchone()
    assert row[0] == "方案1"
    assert row[1] == 1


def test_existing_default_scheme_is_restored_to_scheme_one_on_upgrade():
    connection = connect_database(":memory:")
    apply_v001(connection)
    connection.executemany(
        "INSERT INTO class_periods(period_no, start_time, end_time) VALUES (?, ?, ?)",
        [
            (period_no, f"{7 + period_no:02d}:00:00", f"{8 + period_no:02d}:00:00")
            for period_no in range(1, 9)
        ],
    )
    connection.commit()

    connection.execute("BEGIN")
    apply_v002(connection)
    apply_v003(connection)
    apply_v004(connection)
    connection.execute("UPDATE schema_meta SET schema_version = 5 WHERE singleton = 1")
    before = connection.execute(
        "SELECT id, name FROM timetable_schemes WHERE is_builtin = 1"
    ).fetchone()
    connection.commit()

    migrate(connection)

    after = connection.execute(
        "SELECT id, name FROM timetable_schemes WHERE is_builtin = 1"
    ).fetchone()
    assert after[0] == before[0]
    assert after[1] == "方案1"
    assert get_schema_version(connection) == 6


def test_existing_scheme_one_replaces_generated_default_without_losing_its_periods():
    connection = connect_database(":memory:")
    apply_v001(connection)
    connection.commit()

    connection.execute("BEGIN")
    apply_v002(connection)
    apply_v003(connection)
    apply_v004(connection)
    scheme_one = connection.execute(
        """
        INSERT INTO timetable_schemes(
            name, axis_mode, period_count, day_start, day_end,
            is_builtin, created_at, updated_at
        ) VALUES ('方案1', 'custom_periods', 2, NULL, NULL, 0, 'now', 'now')
        RETURNING id
        """
    ).fetchone()[0]
    generated_default = connection.execute(
        """
        INSERT INTO timetable_schemes(
            name, axis_mode, period_count, day_start, day_end,
            is_builtin, created_at, updated_at
        ) VALUES ('Default方案', 'custom_periods', 2, NULL, NULL, 1, 'now', 'now')
        RETURNING id
        """
    ).fetchone()[0]
    connection.executemany(
        """
        INSERT INTO timetable_scheme_periods(scheme_id, period_no, start_time, end_time)
        VALUES (?, ?, ?, ?)
        """,
        [
            (scheme_one, 1, "07:00:00", "08:00:00"),
            (scheme_one, 2, "08:10:00", "09:10:00"),
            (generated_default, 1, "10:00:00", "11:00:00"),
            (generated_default, 2, "11:00:00", "12:00:00"),
        ],
    )
    semester_id = connection.execute(
        """
        INSERT INTO semesters(
            name, start_monday, total_weeks, is_active, created_at, updated_at,
            timetable_scheme_id
        ) VALUES ('Current', '2026-08-24', 16, 1, 'now', 'now', ?)
        RETURNING id
        """,
        (generated_default,),
    ).fetchone()[0]
    connection.execute("UPDATE schema_meta SET schema_version = 5 WHERE singleton = 1")
    connection.commit()

    migrate(connection)

    builtins = connection.execute(
        "SELECT id, name FROM timetable_schemes WHERE is_builtin = 1"
    ).fetchall()
    periods = connection.execute(
        """
        SELECT period_no, start_time, end_time
        FROM timetable_scheme_periods
        WHERE scheme_id = ?
        ORDER BY period_no
        """,
        (scheme_one,),
    ).fetchall()
    bound_scheme_id = connection.execute(
        "SELECT timetable_scheme_id FROM semesters WHERE id = ?", (semester_id,)
    ).fetchone()[0]

    assert builtins == [(scheme_one, "方案1")]
    assert periods == [
        (1, "07:00:00", "08:00:00"),
        (2, "08:10:00", "09:10:00"),
    ]
    assert bound_scheme_id == scheme_one
    assert connection.execute(
        "SELECT 1 FROM timetable_schemes WHERE id = ?", (generated_default,)
    ).fetchone() is None
def test_future_schema_version_is_rejected(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    connection.execute("UPDATE schema_meta SET schema_version = 7 WHERE singleton = 1")
    connection.commit()

    with pytest.raises(MigrationError, match="newer"):
        migrate(connection)


def test_nonempty_database_without_schema_meta_is_rejected(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    connection.execute("CREATE TABLE unknown_table(id INTEGER PRIMARY KEY)")
    connection.commit()

    with pytest.raises(MigrationError, match="schema_meta"):
        migrate(connection)


def test_empty_or_invalid_schema_meta_is_rejected(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    connection.execute(
        "CREATE TABLE schema_meta(singleton INTEGER PRIMARY KEY, schema_version INTEGER NOT NULL)"
    )
    connection.commit()

    with pytest.raises(MigrationError, match="exactly one"):
        get_schema_version(connection)


def test_current_version_with_missing_tables_is_rejected(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    connection.execute(
        "CREATE TABLE schema_meta("
        "singleton INTEGER PRIMARY KEY, schema_version INTEGER NOT NULL)"
    )
    connection.execute(
        "INSERT INTO schema_meta(singleton, schema_version) VALUES (1, 5)"
    )
    connection.commit()

    with pytest.raises(MigrationError, match="table set"):
        migrate(connection)
