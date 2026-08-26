"""Convert semantic timetable state into a JSON-friendly ViewModel."""

from __future__ import annotations

from typing import TypedDict

from deskboard.models.course import END_OF_DAY
from deskboard.services.timetable_service import TimetableEvent, TimetableGuide, TimetableWeek


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


class TimetableGuideViewModel(TypedDict, total=False):
    index: int
    start: str
    end: str
    label: str


class TimetableAxisViewModel(TypedDict, total=False):
    mode: str | None
    schemeId: int | None
    schemeName: str | None
    periodCount: int
    visibleStart: str | None
    visibleEnd: str | None
    guides: list[TimetableGuideViewModel]


class TimetableViewModel(TypedDict):
    weekLabel: str
    weekStart: str
    weekEnd: str
    headers: list[str]
    visibleStart: str | None
    visibleEnd: str | None
    configurationRequired: bool
    periods: list[TimetablePeriodViewModel]
    axis: TimetableAxisViewModel
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
        "axis": _present_axis(week),
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
    if value is None:
        return None
    if value == END_OF_DAY:
        return "24:00"
    return value.strftime("%H:%M")


def _present_axis(week: TimetableWeek) -> TimetableAxisViewModel:
    guides = [_present_guide(guide) for guide in week.guides]
    return {
        "mode": week.axis_mode,
        "schemeId": week.scheme_id,
        "schemeName": week.scheme_name,
        "periodCount": week.guide_count,
        "visibleStart": _time_text(week.visible_start),
        "visibleEnd": _time_text(week.visible_end),
        "guides": guides,
    }


def _present_guide(guide: TimetableGuide) -> TimetableGuideViewModel:
    result: TimetableGuideViewModel = {
        "index": guide.index,
        "start": _time_text(guide.start) or "",
        "end": _time_text(guide.end) or "",
    }
    if guide.label is not None:
        result["label"] = guide.label
    return result
