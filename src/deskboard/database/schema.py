"""Explicit schema version inspection and transactional migration runner."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

from deskboard.database.migrations.v001_initial import apply_v001
from deskboard.database.migrations.v002_grid_48 import apply_v002
from deskboard.database.migrations.v003_profile_font import apply_v003
from deskboard.database.migrations.v004_timetable_schemes import apply_v004
from deskboard.database.migrations.v005_timetable_default_name import apply_v005
from deskboard.database.migrations.v006_restore_scheme_one_name import apply_v006
from deskboard.database.migrations.v007_uibe_defaults import apply_v007

CURRENT_SCHEMA_VERSION = 7

LOGICAL_TABLES = frozenset(
    {
        "schema_meta",
        "app_settings",
        "todos",
        "semesters",
        "timetable_schemes",
        "timetable_scheme_periods",
        "recurring_courses",
        "course_cancellations",
        "one_off_courses",
        "profiles",
        "profile_widgets",
        "weather_cities",
        "finance_preferences",
        "network_cache",
        "network_state",
    }
)

REPOSITORY_TABLE_OWNERSHIP = {
    "SettingsRepository": frozenset({"app_settings"}),
    "TodoRepository": frozenset({"todos"}),
    "CourseRepository": frozenset(
        {
            "semesters",
            "timetable_schemes",
            "timetable_scheme_periods",
            "recurring_courses",
            "course_cancellations",
            "one_off_courses",
        }
    ),
    "ProfileRepository": frozenset({"profiles", "profile_widgets"}),
    "WeatherRepository": frozenset({"weather_cities"}),
    "FinanceRepository": frozenset({"finance_preferences"}),
    "NetworkRepository": frozenset({"network_cache", "network_state"}),
}

MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {
    1: apply_v001,
    2: apply_v002,
    3: apply_v003,
    4: apply_v004,
    5: apply_v005,
    6: apply_v006,
    7: apply_v007,
}


class MigrationError(RuntimeError):
    """Raised when the on-disk schema cannot be migrated safely."""


def _user_tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    )
    return {str(row[0]) for row in rows}


def get_schema_version(connection: sqlite3.Connection) -> int:
    """Return 0 for an empty database, otherwise its validated version."""
    if "schema_meta" not in _user_tables(connection):
        return 0
    rows = connection.execute(
        "SELECT singleton, schema_version FROM schema_meta"
    ).fetchall()
    if len(rows) != 1 or rows[0][0] != 1:
        raise MigrationError("schema_meta must contain exactly one singleton row")
    version = rows[0][1]
    if not isinstance(version, int) or version < 1:
        raise MigrationError("schema_meta contains an invalid schema version")
    return version


def migrate(connection: sqlite3.Connection) -> None:
    """Migrate one connection atomically to the current supported schema."""
    if connection.in_transaction:
        raise MigrationError("Migration requires a connection with no active transaction")
    tables = _user_tables(connection)
    if tables and "schema_meta" not in tables:
        raise MigrationError("Non-empty database is missing schema_meta")
    version = get_schema_version(connection)
    if version > CURRENT_SCHEMA_VERSION:
        raise MigrationError(
            f"Database schema {version} is newer than supported {CURRENT_SCHEMA_VERSION}"
        )
    if version == CURRENT_SCHEMA_VERSION:
        if tables != LOGICAL_TABLES:
            raise MigrationError("Current schema table set does not match the current contract")
        return
    connection.execute("BEGIN IMMEDIATE")
    try:
        for target_version in range(version + 1, CURRENT_SCHEMA_VERSION + 1):
            migration = MIGRATIONS.get(target_version)
            if migration is None:
                raise MigrationError(f"Missing migration for version {target_version}")
            migration(connection)
        connection.execute(
            "UPDATE schema_meta SET schema_version = ? WHERE singleton = 1",
            (CURRENT_SCHEMA_VERSION,),
        )
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
