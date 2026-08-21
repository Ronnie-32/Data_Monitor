"""Derive the view-only Today Agenda from Todo and Course services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Literal

from deskboard.models.course import CourseOccurrence
from deskboard.models.todo import Todo
from deskboard.services.course_service import CourseService
from deskboard.services.todo_service import TodoService

AgendaItemType = Literal["course", "todo"]
AgendaTimeKind = Literal["point", "range", "date_only"]


@dataclass(frozen=True, slots=True)
class AgendaItem:
    """A semantic agenda row; it contains no layout or persistence details."""

    id: int
    type: AgendaItemType
    title: str
    date: date
    start: time | None
    end: time | None
    time_kind: AgendaTimeKind
    completed: bool = False
    conflict: bool = False
    classroom: str | None = None
    source: str | None = None

    @property
    def item_type(self) -> AgendaItemType:
        return self.type

    @property
    def start_time(self) -> time | None:
        return self.start

    @property
    def end_time(self) -> time | None:
        return self.end

    @property
    def name(self) -> str:
        """Course-friendly alias for consumers that use the domain name."""
        return self.title

    @property
    def content(self) -> str:
        """Todo-friendly alias for consumers that use Todo content."""
        return self.title


@dataclass(slots=True)
class Agenda:
    """Derived sections for one local calendar day."""

    date: date
    timed_items: list[AgendaItem] = field(default_factory=list)
    date_only_items: list[AgendaItem] = field(default_factory=list)

    @property
    def timed(self) -> list[AgendaItem]:
        return self.timed_items

    @property
    def date_only(self) -> list[AgendaItem]:
        return self.date_only_items

    @property
    def today_items(self) -> list[AgendaItem]:
        return self.date_only_items

    @property
    def items(self) -> list[AgendaItem]:
        return [*self.timed_items, *self.date_only_items]


class AgendaService:
    """Combine existing Todo/Course views without persisting generic events."""

    def __init__(self, todo_service: TodoService, course_service: CourseService) -> None:
        self._todo_service = todo_service
        self._course_service = course_service

    def get_today(self, day: date) -> Agenda:
        _validate_date(day)
        course_items = [
            _course_item(occurrence)
            for occurrence in self._course_service.get_occurrences_for_date(day)
        ]
        todo_items = [
            _todo_item(todo, day)
            for todo in self._todo_service.get_for_date(day)
            if todo.planned_date == day
        ]

        timed_items = [
            item
            for item in [*course_items, *todo_items]
            if item.time_kind != "date_only"
        ]
        date_only_items = [
            item for item in todo_items if item.time_kind == "date_only"
        ]
        timed_items.sort(key=_timed_sort_key)
        timed_items = _mark_conflicts(timed_items)
        return Agenda(
            date=day,
            timed_items=timed_items,
            date_only_items=date_only_items,
        )


def _course_item(occurrence: CourseOccurrence) -> AgendaItem:
    return AgendaItem(
        id=occurrence.course_id,
        type="course",
        title=occurrence.name,
        date=occurrence.occurrence_date,
        start=occurrence.start_time,
        end=occurrence.end_time,
        time_kind="range",
        classroom=occurrence.classroom,
        source=occurrence.source,
    )


def _todo_item(todo: Todo, day: date) -> AgendaItem:
    if todo.planned_start_time is None:
        time_kind: AgendaTimeKind = "date_only"
    elif todo.planned_end_time is None:
        time_kind = "point"
    else:
        time_kind = "range"
    return AgendaItem(
        id=todo.id,
        type="todo",
        title=todo.content,
        date=day,
        start=todo.planned_start_time,
        end=todo.planned_end_time,
        time_kind=time_kind,
        completed=todo.is_completed,
        source="todo",
    )


def _timed_sort_key(item: AgendaItem) -> tuple[time, time, int, int]:
    start = item.start or time.min
    end = item.end or start
    return (start, end, 0 if item.type == "course" else 1, item.id)


def _mark_conflicts(items: list[AgendaItem]) -> list[AgendaItem]:
    courses = [item for item in items if item.type == "course"]
    result = list(items)
    for index, item in enumerate(result):
        if item.type != "todo":
            continue
        if any(_overlaps(item, course) for course in courses):
            result[index] = _with_conflict(item)
            for course_index, course in enumerate(result):
                if course.type == "course" and _overlaps(item, course):
                    result[course_index] = _with_conflict(course)
    return result


def _with_conflict(item: AgendaItem) -> AgendaItem:
    return AgendaItem(
        id=item.id,
        type=item.type,
        title=item.title,
        date=item.date,
        start=item.start,
        end=item.end,
        time_kind=item.time_kind,
        completed=item.completed,
        conflict=True,
        classroom=item.classroom,
        source=item.source,
    )


def _overlaps(first: AgendaItem, second: AgendaItem) -> bool:
    if first.date != second.date or first.start is None or second.start is None:
        return False
    if first.end is None:
        return second.start <= first.start < (second.end or second.start)
    if second.end is None:
        return first.start <= second.start < first.end
    return first.start < second.end and second.start < first.end


def _validate_date(value: object) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError("Agenda day must be a date")
