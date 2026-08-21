"""Initial complete V1 schema migration."""

from __future__ import annotations

import sqlite3

V001_STATEMENTS = (
    """
    CREATE TABLE schema_meta (
        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
        schema_version INTEGER NOT NULL CHECK (schema_version >= 1)
    )
    """,
    """
    CREATE TABLE app_settings (
        key TEXT PRIMARY KEY CHECK (length(trim(key)) > 0),
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE todos (
        id INTEGER PRIMARY KEY,
        content TEXT NOT NULL CHECK (length(trim(content)) > 0),
        deadline_date TEXT,
        deadline_time TEXT,
        planned_date TEXT,
        planned_start_time TEXT,
        planned_end_time TEXT,
        completed_at TEXT,
        display_order INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK (planned_end_time IS NULL OR planned_start_time IS NOT NULL),
        CHECK (
            planned_end_time IS NULL
            OR planned_start_time IS NULL
            OR planned_end_time > planned_start_time
        )
    )
    """,
    """
    CREATE TABLE semesters (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL CHECK (length(trim(name)) > 0),
        start_monday TEXT NOT NULL,
        total_weeks INTEGER NOT NULL CHECK (total_weeks > 0),
        is_active INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE UNIQUE INDEX one_active_semester ON semesters(is_active) WHERE is_active = 1",
    """
    CREATE TABLE recurring_courses (
        id INTEGER PRIMARY KEY,
        semester_id INTEGER NOT NULL,
        name TEXT NOT NULL CHECK (length(trim(name)) > 0),
        weekday INTEGER NOT NULL CHECK (weekday BETWEEN 1 AND 7),
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        start_week INTEGER NOT NULL CHECK (start_week >= 1),
        end_week INTEGER NOT NULL CHECK (end_week >= start_week),
        classroom TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE,
        CHECK (end_time > start_time)
    )
    """,
    """
    CREATE TABLE course_cancellations (
        recurring_course_id INTEGER NOT NULL,
        occurrence_date TEXT NOT NULL,
        PRIMARY KEY (recurring_course_id, occurrence_date),
        FOREIGN KEY (recurring_course_id)
            REFERENCES recurring_courses(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE one_off_courses (
        id INTEGER PRIMARY KEY,
        semester_id INTEGER NOT NULL,
        name TEXT NOT NULL CHECK (length(trim(name)) > 0),
        course_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        classroom TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE,
        CHECK (end_time > start_time)
    )
    """,
    """
    CREATE TABLE class_periods (
        period_no INTEGER PRIMARY KEY CHECK (period_no BETWEEN 1 AND 8),
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        CHECK (end_time > start_time)
    )
    """,
    """
    CREATE TABLE profiles (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0),
        is_builtin INTEGER NOT NULL DEFAULT 0 CHECK (is_builtin IN (0, 1)),
        window_x INTEGER,
        window_y INTEGER,
        window_width INTEGER CHECK (window_width IS NULL OR window_width > 0),
        window_height INTEGER CHECK (window_height IS NULL OR window_height > 0),
        theme_key TEXT NOT NULL DEFAULT 'mist_blue',
        panel_opacity REAL NOT NULL DEFAULT 1.0 CHECK (panel_opacity BETWEEN 0 AND 1),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE UNIQUE INDEX one_builtin_profile ON profiles(is_builtin) WHERE is_builtin = 1",
    """
    CREATE TABLE profile_widgets (
        profile_id INTEGER NOT NULL,
        widget_key TEXT NOT NULL CHECK (
            widget_key IN (
                'weather', 'todo', 'today_agenda', 'gold', 'fx',
                'china_indices', 'us_indices', 'finance_overview'
            )
        ),
        visible INTEGER NOT NULL CHECK (visible IN (0, 1)),
        x INTEGER NOT NULL CHECK (x >= 0),
        y INTEGER NOT NULL CHECK (y >= 0),
        w INTEGER NOT NULL CHECK (w BETWEEN 1 AND 12),
        h INTEGER NOT NULL CHECK (h >= 1),
        config_json TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (profile_id, widget_key),
        FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE weather_cities (
        city_key TEXT PRIMARY KEY CHECK (length(trim(city_key)) > 0),
        display_name TEXT NOT NULL CHECK (length(trim(display_name)) > 0),
        source_city_id TEXT NOT NULL,
        display_order INTEGER NOT NULL UNIQUE,
        is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1))
    )
    """,
    "CREATE UNIQUE INDEX one_primary_weather_city ON weather_cities(is_primary) "
    "WHERE is_primary = 1",
    """
    CREATE TABLE finance_preferences (
        item_key TEXT PRIMARY KEY CHECK (length(trim(item_key)) > 0),
        enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
        display_order INTEGER NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE network_cache (
        cache_key TEXT PRIMARY KEY CHECK (length(trim(cache_key)) > 0),
        payload_json TEXT NOT NULL,
        success_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE network_state (
        cache_key TEXT PRIMARY KEY CHECK (length(trim(cache_key)) > 0),
        last_attempt_at TEXT,
        last_status TEXT NOT NULL DEFAULT 'never'
            CHECK (last_status IN ('never', 'success', 'error')),
        last_error_summary TEXT
    )
    """,
    "INSERT INTO schema_meta(singleton, schema_version) VALUES (1, 1)",
)


def apply_v001(connection: sqlite3.Connection) -> None:
    """Apply v001 inside the transaction owned by the migration runner."""
    for statement in V001_STATEMENTS:
        connection.execute(statement)
