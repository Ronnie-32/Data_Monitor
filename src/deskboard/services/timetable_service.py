"""Derive the semantic current-week timetable from Todo and Course services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Literal

from deskboard.models.course import (
    END_OF_DAY,
    ClassPeriod,
    CourseOccurrence,
    TimetableScheme,
    TimetableSchemePeriod,
)
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


@dataclass(frozen=True, slots=True)
class TimetableGuide:
    """A normalized visual reference; it is not a school-period event."""

    index: int
    start: time
    end: time
    label: str | None = None


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
    axis_mode: str | None = None
    scheme_id: int | None = None
    scheme_name: str | None = None
    guide_count: int = 0
    guides: list[TimetableGuide] = field(default_factory=list)

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
        has_scheme_api = callable(
            getattr(self._course_service, "get_active_timetable_scheme", None)
        )
        scheme = _active_scheme(self._course_service)
        axis = _axis_from_scheme(scheme) if scheme is not None else None
        if axis is None and not has_scheme_api:
            # Compatibility for lightweight fakes and the pre-scheme API. The
            # production CourseService resolves only the active semester's
            # bound scheme above.
            periods = _configured_periods(
                self._course_service.get_class_periods()
                if hasattr(self._course_service, "get_class_periods")
                else []
            )
            if periods is not None:
                axis = _axis_from_legacy_periods(periods)
        week_label = _week_label(self._course_service, day)
        headers = [_format_header(current, normalized_mode) for current in week_dates]

        if axis is None:
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

        (
            axis_mode,
            periods,
            visible_start,
            visible_end,
            guides,
            scheme_id,
            scheme_name,
            guide_count,
        ) = axis
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
            axis_mode=axis_mode,
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            guide_count=guide_count,
            guides=guides,
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
        for name in ("get_occurrences_for_week", "get_teaching_week")
    ) and (
        hasattr(value, "get_class_periods")
        or hasattr(value, "get_active_timetable_scheme")
    )


def _looks_like_todo_service(value: object) -> bool:
    return hasattr(value, "get_for_date")


def _configured_periods(periods: list[ClassPeriod]) -> list[ClassPeriod] | None:
    normalized = sorted(periods, key=lambda period: period.period_no)
    if len(normalized) != 8 or [period.period_no for period in normalized] != list(range(1, 9)):
        return None
    return normalized


def _active_scheme(course_service: object) -> TimetableScheme | None:
    getter = getattr(course_service, "get_active_timetable_scheme", None)
    if not callable(getter):
        return None
    scheme = getter()
    return scheme if isinstance(scheme, TimetableScheme) else None


def _axis_from_legacy_periods(
    periods: list[ClassPeriod],
) -> tuple[
    str,
    list[ClassPeriod],
    time,
    time,
    list[TimetableGuide],
    int | None,
    str | None,
    int,
]:
    guides = [
        TimetableGuide(item.period_no, item.start_time, item.end_time, str(item.period_no))
        for item in periods
    ]
    return (
        "custom_periods",
        periods,
        periods[0].start_time,
        periods[-1].end_time,
        guides,
        None,
        None,
        len(periods),
    )


def _axis_from_scheme(
    scheme: TimetableScheme,
) -> tuple[
    str,
    list[ClassPeriod],
    time,
    time,
    list[TimetableGuide],
    int | None,
    str | None,
    int,
] | None:
    if scheme.axis_mode == "custom_periods":
        if (
            len(scheme.periods) != scheme.period_count
            or [item.period_no for item in scheme.periods]
            != list(range(1, scheme.period_count + 1))
            or not _valid_scheme_periods(scheme.periods)
        ):
            return None
        periods = [
            ClassPeriod(item.period_no, item.start_time, item.end_time)
            for item in scheme.periods
        ]
        guides = [
            TimetableGuide(item.period_no, item.start_time, item.end_time, str(item.period_no))
            for item in scheme.periods
        ]
        return (
            "custom_periods",
            periods,
            periods[0].start_time,
            periods[-1].end_time,
            guides,
            scheme.id,
            scheme.name,
            scheme.period_count,
        )
    if scheme.axis_mode != "uniform_day":
        return None
    if (
        scheme.periods
        or scheme.day_start is None
        or scheme.day_end is None
        or scheme.day_end <= scheme.day_start
        or not 1 <= scheme.period_count <= 24
    ):
        return None
    return (
        "uniform_day",
        [],
        scheme.day_start,
        scheme.day_end,
        _uniform_guides(scheme.day_start, scheme.day_end, scheme.period_count),
        scheme.id,
        scheme.name,
        scheme.period_count,
    )


def _valid_scheme_periods(periods: tuple[TimetableSchemePeriod, ...]) -> bool:
    previous_end: time | None = None
    for item in periods:
        if item.end_time <= item.start_time:
            return False
        if previous_end is not None and item.start_time < previous_end:
            return False
        previous_end = item.end_time
    return True


def _uniform_guides(start: time, end: time, count: int) -> list[TimetableGuide]:
    start_seconds = _clock_seconds(start)
    end_seconds = _clock_seconds(end)
    guides: list[TimetableGuide] = []
    for index in range(count):
        lower = _time_from_seconds(
            round(start_seconds + (end_seconds - start_seconds) * index / count)
        )
        upper = _time_from_seconds(
            round(start_seconds + (end_seconds - start_seconds) * (index + 1) / count)
        )
        guides.append(TimetableGuide(index + 1, lower, upper, None))
    return guides


def _clock_seconds(value: time) -> float:
    if value == END_OF_DAY:
        return 24 * 60 * 60
    return value.hour * 3600 + value.minute * 60 + value.second + value.microsecond / 1_000_000


def _time_from_seconds(value: int) -> time:
    if value >= 24 * 60 * 60:
        return END_OF_DAY
    hours, remainder = divmod(max(0, value), 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hours, minutes, seconds)


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
