"""Convert semantic timetable state into a JSON-friendly ViewModel."""

from __future__ import annotations

from typing import TypedDict

from deskboard.services.timetable_service import TimetableEvent, TimetableWeek


class TimetableEventViewModel(TypedDict, total=False):
    id: int
    type: str
    title: str
    date: str
    start: str
    end: str | None
    timeKind: str
    completed: bool
    conflict: bool
    classroom: str


class TimetablePeriodViewModel(TypedDict):
    period: int
    start: str
    end: str


class TimetableViewModel(TypedDict):
    weekLabel: str
    weekStart: str
    weekEnd: str
    headers: list[str]
    visibleStart: str | None
    visibleEnd: str | None
    configurationRequired: bool
    periods: list[TimetablePeriodViewModel]
    events: list[TimetableEventViewModel]


def present_timetable(
    week: TimetableWeek, *, header_mode: str | None = None
) -> TimetableViewModel:
    headers = week.headers
    if header_mode is not None and header_mode != week.header_mode:
        from deskboard.services.timetable_service import _format_header, _normalize_header_mode

        normalized_mode = _normalize_header_mode(header_mode)
        headers = [_format_header(day, normalized_mode) for day in week.week_dates]
    return {
        "weekLabel": week.week_label,
        "weekStart": week.week_start.isoformat(),
        "weekEnd": week.week_end.isoformat(),
        "headers": headers,
        "visibleStart": _time_text(week.visible_start),
        "visibleEnd": _time_text(week.visible_end),
        "configurationRequired": week.configuration_required,
        "periods": [
            {
                "period": period.period_no,
                "start": _time_text(period.start_time),
                "end": _time_text(period.end_time),
            }
            for period in week.periods
        ],
        "events": [present_timetable_event(event) for event in week.events],
    }


def present_timetable_event(event: TimetableEvent) -> TimetableEventViewModel:
    view_model: TimetableEventViewModel = {
        "id": event.id,
        "type": event.type,
        "title": event.title,
        "date": event.date.isoformat(),
        "start": _time_text(event.start),
        "end": _time_text(event.end),
        "timeKind": event.time_kind,
        "completed": event.completed,
        "conflict": event.conflict,
    }
    if event.classroom:
        view_model["classroom"] = event.classroom
    return view_model


def present_timetable_week(
    week: TimetableWeek, *, header_mode: str | None = None
) -> TimetableViewModel:
    return present_timetable(week, header_mode=header_mode)


def _time_text(value) -> str | None:
    return None if value is None else value.strftime("%H:%M")
