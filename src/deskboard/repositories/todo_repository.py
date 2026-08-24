"""SQLite persistence owner for Todo records."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, time

from deskboard.models.todo import Todo


class TodoRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(
        self,
        *,
        content: str,
        display_order: int,
        now: datetime,
        deadline_date: date | None = None,
        deadline_time: time | None = None,
        planned_date: date | None = None,
        planned_start_time: time | None = None,
        planned_end_time: time | None = None,
    ) -> Todo:
        cursor = self._connection.execute(
            """
            INSERT INTO todos(
                content, deadline_date, deadline_time, planned_date,
                planned_start_time, planned_end_time, completed_at,
                display_order, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                content,
                _date_text(deadline_date),
                _time_text(deadline_time),
                _date_text(planned_date),
                _time_text(planned_start_time),
                _time_text(planned_end_time),
                display_order,
                _datetime_text(now),
                _datetime_text(now),
            ),
        )
        self._connection.commit()
        return self.require(int(cursor.lastrowid))

    def get(self, todo_id: int) -> Todo | None:
        row = self._connection.execute(
            f"SELECT {_COLUMNS} FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
        return None if row is None else _todo_from_row(row)

    def require(self, todo_id: int) -> Todo:
        todo = self.get(todo_id)
        if todo is None:
            raise LookupError(f"Todo {todo_id} does not exist")
        return todo

    def top_display_order(self) -> int:
        row = self._connection.execute("SELECT MIN(display_order) FROM todos").fetchone()
        return 0 if row is None or row[0] is None else int(row[0]) - 1

    def update_fields(self, todo_id: int, fields: dict[str, object], now: datetime) -> Todo:
        self.require(todo_id)
        if not fields:
            return self.require(todo_id)
        allowed = {
            "content",
            "deadline_date",
            "deadline_time",
            "planned_date",
            "planned_start_time",
            "planned_end_time",
        }
        if not fields.keys() <= allowed:
            raise ValueError("Unsupported Todo field update")
        serialized = {key: _serialize(value) for key, value in fields.items()}
        assignments = ", ".join(f"{key} = ?" for key in serialized)
        values = [*serialized.values(), _datetime_text(now), todo_id]
        self._connection.execute(
            f"UPDATE todos SET {assignments}, updated_at = ? WHERE id = ?", values
        )
        self._connection.commit()
        return self.require(todo_id)

    def set_completed(
        self,
        todo_id: int,
        completed_at: datetime | None,
        updated_at: datetime | None = None,
    ) -> Todo:
        self.require(todo_id)
        if updated_at is None:
            if completed_at is None:
                raise ValueError("updated_at is required when restoring a Todo")
            updated_at = completed_at
        self._connection.execute(
            "UPDATE todos SET completed_at = ?, updated_at = ? WHERE id = ?",
            (_datetime_text(completed_at), _datetime_text(updated_at), todo_id),
        )
        self._connection.commit()
        return self.require(todo_id)

    def delete(self, todo_id: int) -> None:
        cursor = self._connection.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cursor.rowcount != 1:
            self._connection.rollback()
            raise LookupError(f"Todo {todo_id} does not exist")
        self._connection.commit()

    def list_all(self) -> list[Todo]:
        return self._list("1 = 1", ())

    def list_dashboard(self, day: date) -> list[Todo]:
        return self._list(
            "completed_at IS NULL OR substr(completed_at, 1, 10) = ?", (day.isoformat(),)
        )

    def list_completed(self) -> list[Todo]:
        return self._list("completed_at IS NOT NULL", ())

    def list_incomplete(self) -> list[Todo]:
        return self._list("completed_at IS NULL", ())

    def list_for_date(self, day: date) -> list[Todo]:
        return self._list("planned_date = ?", (day.isoformat(),))

    def list_for_agenda_date(self, day: date) -> list[Todo]:
        day_text = day.isoformat()
        return self._list(
            "planned_date = ? OR deadline_date = ?",
            (day_text, day_text),
        )

    def reorder(self, ordered_ids: list[int]) -> None:
        if len(ordered_ids) != len(set(ordered_ids)):
            raise ValueError("Todo reorder IDs must be unique")
        current = self.list_all()
        known_ids = {todo.id for todo in current}
        if not set(ordered_ids) <= known_ids:
            raise ValueError("Todo reorder contains an unknown ID")
        selected = iter(ordered_ids)
        selected_ids = set(ordered_ids)
        final_ids = [next(selected) if todo.id in selected_ids else todo.id for todo in current]
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.executemany(
                "UPDATE todos SET display_order = ? WHERE id = ?",
                ((position, todo_id) for position, todo_id in enumerate(final_ids)),
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise

    def _list(self, where: str, parameters: tuple[object, ...]) -> list[Todo]:
        rows = self._connection.execute(
            f"SELECT {_COLUMNS} FROM todos WHERE {where} ORDER BY display_order, id",
            parameters,
        )
        return [_todo_from_row(row) for row in rows]


_COLUMNS = (
    "id, content, deadline_date, deadline_time, planned_date, planned_start_time, "
    "planned_end_time, completed_at, display_order, created_at, updated_at"
)


def _date_text(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _time_text(value: time | None) -> str | None:
    return None if value is None else value.isoformat(timespec="seconds")


def _datetime_text(datetime_value: datetime | None) -> str | None:
    return None if datetime_value is None else datetime_value.isoformat(timespec="microseconds")


def _serialize(value: object) -> object:
    if isinstance(value, datetime):
        return _datetime_text(value)
    if isinstance(value, date):
        return _date_text(value)
    if isinstance(value, time):
        return _time_text(value)
    return value


def _todo_from_row(row: sqlite3.Row | tuple[object, ...]) -> Todo:
    return Todo(
        id=int(row[0]),
        content=str(row[1]),
        deadline_date=None if row[2] is None else date.fromisoformat(str(row[2])),
        deadline_time=None if row[3] is None else time.fromisoformat(str(row[3])),
        planned_date=None if row[4] is None else date.fromisoformat(str(row[4])),
        planned_start_time=None if row[5] is None else time.fromisoformat(str(row[5])),
        planned_end_time=None if row[6] is None else time.fromisoformat(str(row[6])),
        completed_at=None if row[7] is None else datetime.fromisoformat(str(row[7])),
        display_order=int(row[8]),
        created_at=datetime.fromisoformat(str(row[9])),
        updated_at=datetime.fromisoformat(str(row[10])),
    )
