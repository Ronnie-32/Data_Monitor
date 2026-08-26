"""Expand persisted Profile geometry from the original 12-column grid."""

from __future__ import annotations

import sqlite3


def apply_v002(connection: sqlite3.Connection) -> None:
    """Add topology metadata and relax the widget width constraint to 48."""

    connection.execute(
        """
        ALTER TABLE profiles
        ADD COLUMN grid_columns INTEGER NOT NULL DEFAULT 12
        CHECK (grid_columns IN (12, 48))
        """
    )
    connection.execute("ALTER TABLE profile_widgets RENAME TO profile_widgets_v001")
    connection.execute(
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
            w INTEGER NOT NULL CHECK (w BETWEEN 1 AND 48),
            h INTEGER NOT NULL CHECK (h >= 1),
            config_json TEXT NOT NULL DEFAULT '{}',
            PRIMARY KEY (profile_id, widget_key),
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        INSERT INTO profile_widgets(
            profile_id, widget_key, visible, x, y, w, h, config_json
        )
        SELECT profile_id, widget_key, visible, x, y, w, h, config_json
        FROM profile_widgets_v001
        """
    )
    connection.execute("DROP TABLE profile_widgets_v001")
