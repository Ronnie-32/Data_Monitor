"""SQLite persistence owner for the global ``weather_cities`` configuration."""

from __future__ import annotations

import sqlite3

from deskboard.models.weather import WeatherCity


class WeatherRepository:
    """Persist city identity/order/primary state, never Weather payloads."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def create_city(
        self,
        *,
        city_key: str,
        display_name: str,
        source_city_id: str,
        display_order: int,
        is_primary: bool = False,
    ) -> WeatherCity:
        key = _text(city_key, "Weather city key")
        name = _text(display_name, "Weather city display name")
        source_id = _text(source_city_id, "Weather source city ID")
        order = _order(display_order)
        primary = _primary(is_primary)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            existing = self._connection.execute(
                "SELECT COUNT(*) FROM weather_cities"
            ).fetchone()
            if existing is None:
                raise RuntimeError("Could not inspect weather city configuration")
            should_be_primary = primary or int(existing[0]) == 0
            if should_be_primary:
                self._connection.execute("UPDATE weather_cities SET is_primary = 0")
            self._connection.execute(
                """
                INSERT INTO weather_cities(
                    city_key, display_name, source_city_id, display_order, is_primary
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (key, name, source_id, order, int(should_be_primary)),
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.require_city(key)

    def get_city(self, city_key: str) -> WeatherCity | None:
        key = _key(city_key)
        row = self._connection.execute(
            """
            SELECT city_key, display_name, source_city_id, display_order, is_primary
            FROM weather_cities WHERE city_key = ?
            """,
            (key,),
        ).fetchone()
        return None if row is None else _city_from_row(row)

    def require_city(self, city_key: str) -> WeatherCity:
        city = self.get_city(city_key)
        if city is None:
            raise LookupError(f"Weather city {city_key} does not exist")
        return city

    def list_cities(self) -> list[WeatherCity]:
        rows = self._connection.execute(
            """
            SELECT city_key, display_name, source_city_id, display_order, is_primary
            FROM weather_cities ORDER BY display_order, city_key
            """
        )
        return [_city_from_row(row) for row in rows]

    def get_primary(self) -> WeatherCity | None:
        row = self._connection.execute(
            """
            SELECT city_key, display_name, source_city_id, display_order, is_primary
            FROM weather_cities WHERE is_primary = 1
            """
        ).fetchone()
        return None if row is None else _city_from_row(row)

    def update_city(
        self,
        city_key: str,
        *,
        display_name: str | None = None,
        source_city_id: str | None = None,
        display_order: int | None = None,
        is_primary: bool | None = None,
    ) -> WeatherCity:
        key = _key(city_key)
        current = self.require_city(key)
        name = current.display_name if display_name is None else _text(
            display_name, "Weather city display name"
        )
        source_id = current.source_city_id if source_city_id is None else _text(
            source_city_id, "Weather source city ID"
        )
        order = current.display_order if display_order is None else _order(display_order)
        primary = current.is_primary if is_primary is None else _primary(is_primary)
        if not primary and current.is_primary:
            remaining = [city for city in self.list_cities() if city.city_key != key]
            if remaining:
                raise ValueError("Cannot unset the primary city while cities remain")
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            if primary:
                self._connection.execute("UPDATE weather_cities SET is_primary = 0")
            self._connection.execute(
                """
                UPDATE weather_cities
                SET display_name = ?, source_city_id = ?, display_order = ?, is_primary = ?
                WHERE city_key = ?
                """,
                (name, source_id, order, int(primary), key),
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.require_city(key)

    def set_primary(self, city_key: str) -> WeatherCity:
        key = _key(city_key)
        self.require_city(key)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute("UPDATE weather_cities SET is_primary = 0")
            self._connection.execute(
                "UPDATE weather_cities SET is_primary = 1 WHERE city_key = ?",
                (key,),
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.require_city(key)

    def reorder_cities(self, ordered_keys: tuple[str, ...] | list[str]) -> list[WeatherCity]:
        keys = tuple(_key(key) for key in ordered_keys)
        current = self.list_cities()
        current_keys = tuple(city.city_key for city in current)
        if len(keys) != len(set(keys)) or set(keys) != set(current_keys):
            raise ValueError("Weather city reorder must contain exactly all city keys")
        if not keys:
            return []
        offset = max(city.display_order for city in current) + len(current) + 1
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute(
                "UPDATE weather_cities SET display_order = display_order + ?",
                (offset,),
            )
            self._connection.executemany(
                "UPDATE weather_cities SET display_order = ? WHERE city_key = ?",
                ((index, key) for index, key in enumerate(keys)),
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.list_cities()

    def delete_city(self, city_key: str) -> None:
        key = _key(city_key)
        city = self.require_city(key)
        remaining = [item for item in self.list_cities() if item.city_key != key]
        replacement = remaining[0].city_key if city.is_primary and remaining else None
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            cursor = self._connection.execute(
                "DELETE FROM weather_cities WHERE city_key = ?", (key,)
            )
            if cursor.rowcount != 1:
                raise LookupError(f"Weather city {key} does not exist")
            if replacement is not None:
                self._connection.execute(
                    "UPDATE weather_cities SET is_primary = 1 WHERE city_key = ?",
                    (replacement,),
                )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise


def _city_from_row(row: sqlite3.Row | tuple[object, ...]) -> WeatherCity:
    return WeatherCity(
        city_key=str(row[0]),
        display_name=str(row[1]),
        source_city_id=str(row[2]),
        display_order=int(row[3]),
        is_primary=bool(row[4]),
    )


def _key(value: object) -> str:
    return _text(value, "Weather city key")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    if field == "Weather city key" and any(
        char.isspace() or char in "/\\" for char in normalized
    ):
        raise ValueError("Weather city key must not contain whitespace or path separators")
    return normalized


def _order(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Weather city display_order must be an integer")
    if value < 0:
        raise ValueError("Weather city display_order must not be negative")
    return value


def _primary(value: object) -> bool:
    if type(value) is not bool:
        raise TypeError("Weather city is_primary must be a bool")
    return value
