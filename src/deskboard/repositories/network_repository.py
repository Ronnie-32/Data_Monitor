"""SQLite owner for successful network payloads and attempt state."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

NetworkLastStatus = Literal["never", "success", "error"]


@dataclass(frozen=True, slots=True)
class NetworkCacheEntry:
    cache_key: str
    payload: object
    success_at: datetime


@dataclass(frozen=True, slots=True)
class NetworkState:
    cache_key: str
    last_attempt_at: datetime | None
    last_status: NetworkLastStatus
    last_error_summary: str | None


class NetworkRepository:
    """Persist only ``network_cache`` and ``network_state``."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def get_cache(self, cache_key: str) -> NetworkCacheEntry | None:
        key = _validated_key(cache_key)
        row = self._connection.execute(
            "SELECT cache_key, payload_json, success_at FROM network_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return self._cache_from_row(row, key)

    def get_state(self, cache_key: str) -> NetworkState | None:
        key = _validated_key(cache_key)
        row = self._connection.execute(
            """
            SELECT cache_key, last_attempt_at, last_status, last_error_summary
            FROM network_state WHERE cache_key = ?
            """,
            (key,),
        ).fetchone()
        if row is None:
            return None
        status = str(row[2])
        if status not in {"never", "success", "error"}:
            raise ValueError(f"Unknown network state status: {status}")
        return _state_from_row(row, status)

    def list_cache(self) -> list[NetworkCacheEntry]:
        rows = self._connection.execute(
            "SELECT cache_key, payload_json, success_at FROM network_cache ORDER BY cache_key"
        )
        return [self._cache_from_row(row, str(row[0])) for row in rows]

    def list_state(self) -> list[NetworkState]:
        rows = self._connection.execute(
            """
            SELECT cache_key, last_attempt_at, last_status, last_error_summary
            FROM network_state ORDER BY cache_key
            """
        )
        return [_state_from_row(row, str(row[2])) for row in rows]

    def save_success(self, cache_key: str, payload: object, success_at: datetime) -> None:
        key = _validated_key(cache_key)
        timestamp = _datetime_text(success_at)
        try:
            payload_json = json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as error:
            raise ValueError(f"Network payload for {key} must be JSON-serializable") from error
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute(
                """
                INSERT INTO network_cache(cache_key, payload_json, success_at)
                VALUES (?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    success_at = excluded.success_at
                """,
                (key, payload_json, timestamp),
            )
            self._upsert_state(
                key,
                timestamp,
                "success",
                None,
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise

    record_success = save_success
    get_cached = get_cache
    get_attempt_state = get_state

    def record_failure(
        self,
        cache_key: str,
        attempted_at: datetime,
        error_summary: str,
    ) -> None:
        key = _validated_key(cache_key)
        if not isinstance(error_summary, str) or not error_summary.strip():
            raise ValueError("network error summary must not be empty")
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._upsert_state(key, _datetime_text(attempted_at), "error", error_summary.strip())
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise

    def _upsert_state(
        self,
        key: str,
        attempted_at: str | None,
        status: NetworkLastStatus,
        error_summary: str | None,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO network_state(
                cache_key, last_attempt_at, last_status, last_error_summary
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                last_attempt_at = excluded.last_attempt_at,
                last_status = excluded.last_status,
                last_error_summary = excluded.last_error_summary
            """,
            (key, attempted_at, status, error_summary),
        )

    def _cache_from_row(
        self, row: sqlite3.Row | tuple[object, ...], key: str
    ) -> NetworkCacheEntry:
        try:
            payload = json.loads(str(row[1]))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"Cached network payload is not valid JSON: {key}") from error
        return NetworkCacheEntry(key, payload, _parse_datetime(row[2], "success_at"))


def _state_from_row(
    row: sqlite3.Row | tuple[object, ...], status: str | None = None
) -> NetworkState:
    selected_status = str(row[2]) if status is None else status
    if selected_status not in {"never", "success", "error"}:
        raise ValueError(f"Unknown network state status: {selected_status}")
    return NetworkState(
        cache_key=str(row[0]),
        last_attempt_at=(
            None if row[1] is None else _parse_datetime(row[1], "last_attempt_at")
        ),
        last_status=selected_status,  # type: ignore[arg-type]
        last_error_summary=None if row[3] is None else str(row[3]),
    )


def _validated_key(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("network cache key must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError("network cache key must not be empty")
    return normalized


def _datetime_text(value: datetime) -> str:
    if not isinstance(value, datetime):
        raise TypeError("network timestamps must be datetime values")
    return value.isoformat(timespec="microseconds")


def _parse_datetime(value: object, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError(f"Stored network {field} is not a valid datetime") from error
    return parsed
