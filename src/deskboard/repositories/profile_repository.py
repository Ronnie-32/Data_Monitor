"""SQLite persistence owner for ``profiles`` and ``profile_widgets``."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime

from deskboard.models.profile import (
    DEFAULT_PROFILE_NAME,
    Profile,
    ProfileState,
    ProfileWidgetState,
)


class ProfileRepository:
    """Persist only visual/spatial Profile state."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @property
    def connection(self) -> sqlite3.Connection:
        """Expose the owned connection for service-level settings coordination."""

        return self._connection

    def ensure_default(self, state: ProfileState, now: datetime) -> Profile:
        existing = self.get_builtin()
        if existing is not None:
            return existing
        if self.get_by_name(DEFAULT_PROFILE_NAME) is not None:
            raise ValueError("A non-built-in Profile already uses the Default name")
        return self.create(DEFAULT_PROFILE_NAME, state, now, is_builtin=True)

    def create(
        self,
        name: str,
        state: ProfileState,
        now: datetime,
        *,
        is_builtin: bool = False,
    ) -> Profile:
        cursor = self._connection.cursor()
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            cursor.execute(
                """
                INSERT INTO profiles(
                    name, is_builtin, window_x, window_y, window_width, window_height,
                    theme_key, panel_opacity, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    int(is_builtin),
                    state.window_x,
                    state.window_y,
                    state.window_width,
                    state.window_height,
                    state.theme_key,
                    state.panel_opacity,
                    _datetime_text(now),
                    _datetime_text(now),
                ),
            )
            profile_id = int(cursor.lastrowid)
            self._insert_widgets(profile_id, state.widgets)
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.require(profile_id)

    def get(self, profile_id: int) -> Profile | None:
        row = self._connection.execute(
            f"SELECT {_PROFILE_COLUMNS} FROM profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        return None if row is None else self._profile_from_row(row)

    def require(self, profile_id: int) -> Profile:
        profile = self.get(profile_id)
        if profile is None:
            raise LookupError(f"Profile {profile_id} does not exist")
        return profile

    def get_builtin(self) -> Profile | None:
        row = self._connection.execute(
            f"SELECT {_PROFILE_COLUMNS} FROM profiles WHERE is_builtin = 1"
        ).fetchone()
        return None if row is None else self._profile_from_row(row)

    def get_by_name(self, name: str) -> Profile | None:
        row = self._connection.execute(
            f"SELECT {_PROFILE_COLUMNS} FROM profiles WHERE name = ?", (name,)
        ).fetchone()
        return None if row is None else self._profile_from_row(row)

    def list_profiles(self) -> list[Profile]:
        rows = self._connection.execute(
            f"SELECT {_PROFILE_COLUMNS} FROM profiles ORDER BY is_builtin DESC, id"
        )
        return [self._profile_from_row(row) for row in rows]

    def save_state(self, profile_id: int, state: ProfileState, now: datetime) -> None:
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            cursor = self._connection.execute(
                """
                UPDATE profiles
                SET window_x = ?, window_y = ?, window_width = ?, window_height = ?,
                    theme_key = ?, panel_opacity = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    state.window_x,
                    state.window_y,
                    state.window_width,
                    state.window_height,
                    state.theme_key,
                    state.panel_opacity,
                    _datetime_text(now),
                    profile_id,
                ),
            )
            if cursor.rowcount != 1:
                self._connection.rollback()
                raise LookupError(f"Profile {profile_id} does not exist")
            self._connection.execute(
                "DELETE FROM profile_widgets WHERE profile_id = ?", (profile_id,)
            )
            self._insert_widgets(profile_id, state.widgets)
            self._connection.commit()
        except BaseException:
            if self._connection.in_transaction:
                self._connection.rollback()
            raise

    def rename(self, profile_id: int, name: str, now: datetime) -> None:
        cursor = self._connection.execute(
            "UPDATE profiles SET name = ?, updated_at = ? WHERE id = ?",
            (name, _datetime_text(now), profile_id),
        )
        if cursor.rowcount != 1:
            self._connection.rollback()
            raise LookupError(f"Profile {profile_id} does not exist")
        self._connection.commit()

    def delete(self, profile_id: int) -> None:
        cursor = self._connection.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        if cursor.rowcount != 1:
            self._connection.rollback()
            raise LookupError(f"Profile {profile_id} does not exist")
        self._connection.commit()

    def _insert_widgets(
        self, profile_id: int, widgets: Iterable[ProfileWidgetState]
    ) -> None:
        self._connection.executemany(
            """
            INSERT INTO profile_widgets(
                profile_id, widget_key, visible, x, y, w, h, config_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    profile_id,
                    widget.widget_key,
                    int(widget.visible),
                    widget.x,
                    widget.y,
                    widget.w,
                    widget.h,
                    json.dumps(
                        dict(widget.config),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
                for widget in widgets
            ),
        )

    def _profile_from_row(self, row: sqlite3.Row | tuple[object, ...]) -> Profile:
        profile_id = int(row[0])
        widget_rows = self._connection.execute(
            """
            SELECT widget_key, visible, x, y, w, h, config_json
            FROM profile_widgets
            WHERE profile_id = ?
            ORDER BY y, x, widget_key
            """,
            (profile_id,),
        )
        widgets = tuple(
            ProfileWidgetState(
                widget_key=str(widget_row[0]),
                visible=bool(widget_row[1]),
                x=int(widget_row[2]),
                y=int(widget_row[3]),
                w=int(widget_row[4]),
                h=int(widget_row[5]),
                config=_config_from_json(widget_row[6]),
            )
            for widget_row in widget_rows
        )
        state = ProfileState(
            window_x=None if row[3] is None else int(row[3]),
            window_y=None if row[4] is None else int(row[4]),
            window_width=None if row[5] is None else int(row[5]),
            window_height=None if row[6] is None else int(row[6]),
            theme_key=str(row[7]),
            panel_opacity=float(row[8]),
            widgets=widgets,
        )
        return Profile(
            id=profile_id,
            name=str(row[1]),
            is_builtin=bool(row[2]),
            state=state,
            created_at=datetime.fromisoformat(str(row[9])),
            updated_at=datetime.fromisoformat(str(row[10])),
        )


_PROFILE_COLUMNS = (
    "id, name, is_builtin, window_x, window_y, window_width, window_height, "
    "theme_key, panel_opacity, created_at, updated_at"
)


def _config_from_json(value: object) -> dict[str, object]:
    try:
        config = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("Stored Profile widget config is not valid JSON") from error
    if not isinstance(config, dict):
        raise ValueError("Stored Profile widget config must be an object")
    return config


def _datetime_text(value: datetime) -> str:
    if not isinstance(value, datetime):
        raise TypeError("Profile timestamps must be datetime values")
    return value.isoformat(timespec="microseconds")
