"""Convert Agenda domain values into stable, JSON-friendly display models."""

from __future__ import annotations

from typing import TypedDict

from deskboard.services.agenda_service import Agenda, AgendaItem


class AgendaItemViewModel(TypedDict, total=False):
    id: int
    type: str
    title: str
    date: str
    start: str | None
    end: str | None
    timeKind: str
    completed: bool
    conflict: bool
    classroom: str


class AgendaViewModel(TypedDict):
    date: str
    timedItems: list[AgendaItemViewModel]
    dateOnlyItems: list[AgendaItemViewModel]


def present_agenda(agenda: Agenda) -> AgendaViewModel:
    return {
        "date": agenda.date.isoformat(),
        "timedItems": [present_agenda_item(item) for item in agenda.timed_items],
        "dateOnlyItems": [present_agenda_item(item) for item in agenda.date_only_items],
    }


def present_today_agenda(agenda: Agenda) -> AgendaViewModel:
    return present_agenda(agenda)


def present_agenda_item(item: AgendaItem) -> AgendaItemViewModel:
    view_model: AgendaItemViewModel = {
        "id": item.id,
        "type": item.type,
        "title": item.title,
        "date": item.date.isoformat(),
        "start": _time_text(item.start),
        "end": _time_text(item.end),
        "timeKind": _time_kind_text(item.time_kind),
        "completed": item.completed,
        "conflict": item.conflict,
    }
    if item.classroom:
        view_model["classroom"] = item.classroom
    return view_model


def _time_text(value) -> str | None:
    return None if value is None else value.strftime("%H:%M")


def _time_kind_text(value: str) -> str:
    return "dateOnly" if value == "date_only" else value
