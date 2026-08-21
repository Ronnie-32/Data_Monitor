from __future__ import annotations

import sqlite3

import pytest

from deskboard.database import schema
from deskboard.database.connection import connect_database
from deskboard.database.migrations.v001_initial import apply_v001
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

    assert CURRENT_SCHEMA_VERSION == 1
    assert get_schema_version(connection) == 1
    assert connection.execute(
        "SELECT value FROM app_settings WHERE key = 'marker'"
    ).fetchone()[0] == "kept"


def test_migration_runner_rolls_back_all_ddl_on_failure(tmp_path, monkeypatch):
    connection = connect_database(tmp_path / "deskboard.db")

    def broken_migration(target: sqlite3.Connection) -> None:
        target.execute("CREATE TABLE partial_state(id INTEGER PRIMARY KEY)")
        raise RuntimeError("boom")

    monkeypatch.setattr(schema, "MIGRATIONS", {1: broken_migration})

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


def test_future_schema_version_is_rejected(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    connection.execute("UPDATE schema_meta SET schema_version = 2 WHERE singleton = 1")
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
        "INSERT INTO schema_meta(singleton, schema_version) VALUES (1, 1)"
    )
    connection.commit()

    with pytest.raises(MigrationError, match="table set"):
        migrate(connection)
