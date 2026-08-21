"""Todo business semantics independent of UI."""

from __future__ import annotations

from datetime import date, time

from deskboard.infrastructure.clock import Clock
from deskboard.models.todo import UNSET, Todo, TodoUpdate
from deskboard.repositories.todo_repository import TodoRepository


class TodoService:
    def __init__(self, repository: TodoRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def add_quick(self, content: str) -> Todo:
        return self._repository.create(
            content=_content(content),
            display_order=self._repository.top_display_order(),
            now=self._clock.now(),
        )

    def get(self, todo_id: int) -> Todo:
        return self._repository.require(todo_id)

    def update(self, todo_id: int, update: TodoUpdate) -> Todo:
        current = self._repository.require(todo_id)
        fields: dict[str, object] = {}
        for field_name in (
            "content",
            "deadline_date",
            "deadline_time",
            "planned_date",
            "planned_start_time",
            "planned_end_time",
        ):
            value = getattr(update, field_name)
            if value is not UNSET:
                fields[field_name] = value
        if "content" in fields:
            fields["content"] = _content(fields["content"])

        deadline_date = fields.get("deadline_date", current.deadline_date)
        deadline_time = fields.get("deadline_time", current.deadline_time)
        if deadline_time is not None and deadline_date is None:
            deadline_date = self._clock.today()
            fields["deadline_date"] = deadline_date

        planned_date = fields.get("planned_date", current.planned_date)
        planned_start = fields.get("planned_start_time", current.planned_start_time)
        planned_end = fields.get("planned_end_time", current.planned_end_time)
        _validate_planned(planned_date, planned_start, planned_end)
        if planned_start is not None and planned_date is None:
            fields["planned_date"] = self._clock.today()

        return self._repository.update_fields(todo_id, fields, self._clock.now())

    def set_completed(self, todo_id: int, completed: bool) -> Todo:
        now = self._clock.now()
        return self._repository.set_completed(todo_id, now if completed else None, now)

    def delete(self, todo_id: int) -> None:
        self._repository.delete(todo_id)

    def restore(self, todo_id: int) -> Todo:
        todo = self._repository.require(todo_id)
        if not todo.is_completed:
            return todo
        return self._repository.set_completed(todo_id, None, self._clock.now())

    def reorder(self, ordered_ids: list[int]) -> None:
        self._repository.reorder(ordered_ids)

    def get_dashboard_items(self) -> list[Todo]:
        return self._repository.list_dashboard(self._clock.today())

    def get_completed_history(self) -> list[Todo]:
        return self._repository.list_completed()

    def get_incomplete_items(self) -> list[Todo]:
        return self._repository.list_incomplete()

    def get_for_date(self, day: date) -> list[Todo]:
        return self._repository.list_for_date(day)


def _content(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("Todo content must be a string")
    content = value.strip()
    if not content:
        raise ValueError("Todo content must not be empty")
    return content


def _validate_planned(
    planned_date: object, planned_start: object, planned_end: object
) -> None:
    if planned_date is not None and not isinstance(planned_date, date):
        raise TypeError("planned date must be a date")
    if planned_start is not None and not isinstance(planned_start, time):
        raise TypeError("planned start must be a time")
    if planned_end is not None and not isinstance(planned_end, time):
        raise TypeError("planned end must be a time")
    if planned_end is not None and planned_start is None:
        raise ValueError("planned end requires a planned start")
    if planned_end is not None and planned_end <= planned_start:
        raise ValueError("planned end must be later than planned start")
