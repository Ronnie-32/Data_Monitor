"""SQLite persistence owner for global ``finance_preferences`` only."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from deskboard.models.finance import FinancePreference


class FinanceRepository:
    """Persist enable/order preferences, never finance market payloads."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def ensure_items(self, item_keys: Iterable[str]) -> list[FinancePreference]:
        keys = _validated_keys(item_keys)
        if not keys:
            return self.list_preferences()
        current = self.list_preferences()
        existing_keys = {item.item_key for item in current}
        missing = tuple(key for key in keys if key not in existing_keys)
        if not missing:
            return current
        next_order = max((item.display_order for item in current), default=-1) + 1
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.executemany(
                """
                INSERT INTO finance_preferences(item_key, enabled, display_order)
                VALUES (?, 1, ?)
                """,
                ((key, next_order + index) for index, key in enumerate(missing)),
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.list_preferences()

    seed_items = ensure_items

    def get(self, item_key: str) -> FinancePreference | None:
        key = _validated_key(item_key)
        row = self._connection.execute(
            """
            SELECT item_key, enabled, display_order
            FROM finance_preferences
            WHERE item_key = ?
            """,
            (key,),
        ).fetchone()
        return None if row is None else _preference_from_row(row)

    def require(self, item_key: str) -> FinancePreference:
        key = _validated_key(item_key)
        preference = self.get(key)
        if preference is None:
            raise LookupError(f"Finance preference {key} does not exist")
        return preference

    def list_preferences(self) -> list[FinancePreference]:
        rows = self._connection.execute(
            """
            SELECT item_key, enabled, display_order
            FROM finance_preferences
            ORDER BY display_order, item_key
            """
        )
        return [_preference_from_row(row) for row in rows]

    def set_enabled(self, item_key: str, enabled: bool) -> FinancePreference:
        key = _validated_key(item_key)
        if type(enabled) is not bool:
            raise TypeError("Finance preference enabled must be a bool")
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            cursor = self._connection.execute(
                "UPDATE finance_preferences SET enabled = ? WHERE item_key = ?",
                (int(enabled), key),
            )
            if cursor.rowcount != 1:
                raise LookupError(f"Finance preference {key} does not exist")
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.require(key)

    update_enabled = set_enabled

    def reorder(self, ordered_keys: Iterable[str]) -> list[FinancePreference]:
        keys = _validated_keys(ordered_keys)
        current = self.list_preferences()
        current_keys = tuple(item.item_key for item in current)
        if len(keys) != len(current_keys) or set(keys) != set(current_keys):
            raise ValueError(
                "Finance preference reorder must contain exactly all stored item keys"
            )
        if not keys:
            return []
        offset = max(item.display_order for item in current) + len(current) + 1
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute(
                "UPDATE finance_preferences SET display_order = display_order + ?",
                (offset,),
            )
            self._connection.executemany(
                "UPDATE finance_preferences SET display_order = ? WHERE item_key = ?",
                ((index, key) for index, key in enumerate(keys)),
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.list_preferences()

    reorder_items = reorder


def _preference_from_row(row: sqlite3.Row | tuple[object, ...]) -> FinancePreference:
    return FinancePreference(
        item_key=str(row[0]),
        enabled=bool(row[1]),
        display_order=int(row[2]),
    )


def _validated_key(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("Finance preference item key must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError("Finance preference item key must not be empty")
    if any(char.isspace() or char in "/\\" for char in normalized):
        raise ValueError("Finance preference item key must not contain path separators")
    return normalized


def _validated_keys(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("Finance preference keys must be an iterable of strings")
    keys = tuple(_validated_key(value) for value in values)
    if len(keys) != len(set(keys)):
        raise ValueError("Finance preference keys must be unique")
    return keys
