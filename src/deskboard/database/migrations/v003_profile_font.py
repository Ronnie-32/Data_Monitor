"""Persist the selected Dashboard font alongside Profile visual state."""

from __future__ import annotations

import sqlite3


def apply_v003(connection: sqlite3.Connection) -> None:
    """Add the installed-font key without rewriting existing Profile rows."""

    connection.execute(
        """
        ALTER TABLE profiles
        ADD COLUMN font_key TEXT NOT NULL DEFAULT 'system_ui'
        """
    )
