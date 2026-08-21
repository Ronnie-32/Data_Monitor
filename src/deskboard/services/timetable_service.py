"""Derive the semantic current-week timetable from Todo and Course services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Literal

from deskboard.models.course import ClassPeriod, CourseOccurrence
from deskboard.models.todo import Todo
from deskboard.services.course_service import CourseService
from deskboard.services.todo_service import TodoService

TimetableEventType = Literal["course", "todo"]
TimetableTimeKind = Literal["point", "range"]


@dataclass(frozen=True, slots=True)
class TimetableEvent:
    """A renderable semantic event without CSS coordinates."""

    id: int
    type: TimetableEventType
    title: str
    date: date
    start: time
    end: time | None
    time_kind: TimetableTimeKind
    completed: bool = False
    conflict: bool = False
    classroom: str | None = None
    source: str | None = None

    @property
    def item_type(self) -> TimetableEventType:
        return self.type

    @property
    def start_time(self) -> time:
        return self.start

    @property
    def end_time(self) -> time | None:
        return self.end

    @property
    def name(self) -> str:
        return self.title

    @property
    def content(self) -> str:
        return self.title


@dataclass(slots=True)
class TimetableWeek:
    """Current Monday-Sunday semantic timetable state."""

    week_start: date
    week_end: date
    week_dates: list[date]
    week_label: str
    events: list[TimetableEvent]
    periods: list[ClassPeriod]
    visible_start: time | None
    visible_end: time | None
    configuration_required: bool = False
    header_mode: str = "weekday_date"
    headers: list[str] = field(default_factory=list)

    @property
    def monday(self) -> date:
        return self.week_start

    @property
    def sunday(self) -> date:
        return self.week_end

    @property
    def dates(self) -> list[date]:
        return self.week_dates

    @property
    def items(self) -> list[TimetableEvent]:
        return self.events

    @property
    def state(self) -> str:
        return "configuration_required" if self.configuration_required else "ready"


class TimetableService:
    """Own current-week scope, visible bounds, and conflict metadata."""

    def __init__(
        self,
        todo_service: TodoService | CourseService,
        course_service: CourseService | TodoService,
    ) -> None:
        # Accept both natural positional orders while keeping explicit keyword names.
        if _looks_like_course_service(todo_service) and _looks_like_todo_service(
            course_service
        ):
            todo_service, course_service = course_service, todo_service
        if not _looks_like_todo_service(todo_service) or not _looks_like_course_service(
            course_service
        ):
            raise TypeError("TimetableService requires TodoService and CourseService")
        self._todo_service = todo_service
        self._course_service = course_service

    def get_current_week(
        self, day: date, *, header_mode: str = "weekday_date"
    ) -> TimetableWeek:
        _validate_date(day, "Timetable day")
        normalized_mode = _normalize_header_mode(header_mode)
        week_start = day - timedelta(days=day.weekday())
        week_dates = [week_start + timedelta(days=offset) for offset in range(7)]
        periods = _configured_periods(self._course_service.get_class_periods())
        week_label = _week_label(self._course_service, day)
        headers = [_format_header(current, normalized_mode) for current in week_dates]

        if periods is None:
            return TimetableWeek(
                week_start=week_start,
                week_end=week_dates[-1],
                week_dates=week_dates,
                week_label=week_label,
                events=[],
                periods=[],
                visible_start=None,
                visible_end=None,
                configuration_required=True,
                header_mode=normalized_mode,
                headers=headers,
            )

        visible_start = periods[0].start_time
        visible_end = periods[-1].end_time
        events = self._build_events(
            day=day,
            week_start=week_start,
            week_end=week_dates[-1],
            visible_start=visible_start,
            visible_end=visible_end,
        )
        return TimetableWeek(
            week_start=week_start,
            week_end=week_dates[-1],
            week_dates=week_dates,
            week_label=week_label,
            events=_mark_conflicts(events),
            periods=periods,
            visible_start=visible_start,
            visible_end=visible_end,
            configuration_required=False,
            header_mode=normalized_mode,
            headers=headers,
        )

    def _build_events(
        self,
        *,
        day: date,
        week_start: date,
        week_end: date,
        visible_start: time,
        visible_end: time,
    ) -> list[TimetableEvent]:
        events: list[TimetableEvent] = []
        for occurrence in self._course_service.get_occurrences_for_week(day):
            if not week_start <= occurrence.occurrence_date <= week_end:
                continue
            if not _within_range(
                occurrence.start_time,
                occurrence.end_time,
                visible_start,
                visible_end,
            ):
                continue
            events.append(_course_event(occurrence))

        current = week_start
        while current <= week_end:
            for todo in self._todo_service.get_for_date(current):
                if todo.planned_date != current or todo.planned_start_time is None:
                    continue
                if not _within_range(
                    todo.planned_start_time,
                    todo.planned_end_time,
                    visible_start,
                    visible_end,
                ):
                    continue
                events.append(_todo_event(todo, current))
            current += timedelta(days=1)
        events.sort(key=_event_sort_key)
        return events


def _looks_like_course_service(value: object) -> bool:
    return all(
        hasattr(value, name)
        for name in ("get_class_periods", "get_occurrences_for_week", "get_teaching_week")
    )


def _looks_like_todo_service(value: object) -> bool:
    return hasattr(value, "get_for_date")


def _configured_periods(periods: list[ClassPeriod]) -> list[ClassPeriod] | None:
    normalized = sorted(periods, key=lambda period: period.period_no)
    if len(normalized) != 8 or [period.period_no for period in normalized] != list(range(1, 9)):
        return None
    return normalized


def _week_label(course_service: CourseService, day: date) -> str:
    teaching_week = course_service.get_teaching_week(day)
    return "" if teaching_week is None else f"第 {teaching_week} 周"


def _course_event(occurrence: CourseOccurrence) -> TimetableEvent:
    return TimetableEvent(
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


def _todo_event(todo: Todo, day: date) -> TimetableEvent:
    time_kind: TimetableTimeKind = (
        "point" if todo.planned_end_time is None else "range"
    )
    return TimetableEvent(
        id=todo.id,
        type="todo",
        title=todo.content,
        date=day,
        start=todo.planned_start_time,  # type: ignore[arg-type]
        end=todo.planned_end_time,
        time_kind=time_kind,
        completed=todo.is_completed,
        source="todo",
    )


def _within_range(
    start: time,
    end: time | None,
    visible_start: time,
    visible_end: time,
) -> bool:
    if end is None:
        return visible_start <= start <= visible_end
    return end > visible_start and start < visible_end


def _event_sort_key(event: TimetableEvent) -> tuple[date, time, time, int, int]:
    return (
        event.date,
        event.start,
        event.end or event.start,
        0 if event.type == "course" else 1,
        event.id,
    )


def _mark_conflicts(events: list[TimetableEvent]) -> list[TimetableEvent]:
    result = list(events)
    courses = [event for event in result if event.type == "course"]
    for index, event in enumerate(result):
        if event.type != "todo":
            continue
        overlapping = [course for course in courses if _overlaps(event, course)]
        if not overlapping:
            continue
        result[index] = _with_conflict(event)
        for course_index, course in enumerate(result):
            if course.type == "course" and _overlaps(event, course):
                result[course_index] = _with_conflict(course)
    return result


def _with_conflict(event: TimetableEvent) -> TimetableEvent:
    return TimetableEvent(
        id=event.id,
        type=event.type,
        title=event.title,
        date=event.date,
        start=event.start,
        end=event.end,
        time_kind=event.time_kind,
        completed=event.completed,
        conflict=True,
        classroom=event.classroom,
        source=event.source,
    )


def _overlaps(first: TimetableEvent, second: TimetableEvent) -> bool:
    if first.date != second.date:
        return False
    if first.end is None:
        return second.start <= first.start < (second.end or second.start)
    if second.end is None:
        return first.start <= second.start < first.end
    return first.start < second.end and second.start < first.end


def _normalize_header_mode(value: str) -> str:
    aliases = {
        "weekday": "weekday",
        "weekday_only": "weekday",
        "weekdayOnly": "weekday",
        "weekday_date": "weekday_date",
        "weekday+date": "weekday_date",
        "weekday_date_combined": "weekday_date",
        "date": "date",
        "date_only": "date",
        "dateOnly": "date",
    }
    try:
        return aliases[value]
    except KeyError as error:
        raise ValueError("Unsupported timetable header mode") from error


def _format_header(day: date, mode: str) -> str:
    weekday = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")[day.weekday()]
    if mode == "weekday":
        return weekday
    if mode == "date":
        return day.strftime("%m-%d")
    return f"{weekday} {day:%m-%d}"


def _validate_date(value: object, label: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError(f"{label} must be a date")
