"""Convert Todo domain values into stable Dashboard display models."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TypedDict

from deskboard.models.todo import Todo


class TodoViewModel(TypedDict):
    id: int
    content: str
    completed: bool
    overdue: bool
    deadlineText: str
    plannedText: str


def present_todos(
    todos: list[Todo], *, today: date, now: datetime
) -> list[TodoViewModel]:
    return [present_todo(todo, today=today, now=now) for todo in todos]


def present_todo(todo: Todo, *, today: date, now: datetime) -> TodoViewModel:
    return {
        "id": todo.id,
        "content": todo.content,
        "completed": todo.is_completed,
        "overdue": _is_overdue(todo, today=today, now=now),
        "deadlineText": _deadline_text(todo.deadline_date, todo.deadline_time),
        "plannedText": _planned_text(
            todo.planned_date,
            todo.planned_start_time,
            todo.planned_end_time,
        ),
    }


def _is_overdue(todo: Todo, *, today: date, now: datetime) -> bool:
    if todo.is_completed or todo.deadline_date is None:
        return False
    if todo.deadline_date != today:
        return todo.deadline_date < today
    if todo.deadline_time is None:
        return False
    return datetime.combine(today, todo.deadline_time) < now


def _deadline_text(deadline_date: date | None, deadline_time: time | None) -> str:
    if deadline_date is None:
        return ""
    text = f"截止 {deadline_date:%m-%d}"
    if deadline_time is not None:
        text += f" {deadline_time:%H:%M}"
    return text


def _planned_text(
    planned_date: date | None,
    planned_start: time | None,
    planned_end: time | None,
) -> str:
    if planned_date is None:
        return ""
    text = f"计划 {planned_date:%m-%d}"
    if planned_start is not None:
        text += f" {planned_start:%H:%M}"
    if planned_end is not None:
        text += f"–{planned_end:%H:%M}"
    return text
