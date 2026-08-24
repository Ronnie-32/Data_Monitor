from __future__ import annotations

from datetime import date, datetime, time

from deskboard.models.todo import Todo
from deskboard.presentation.dashboard_state import present_dashboard_state
from deskboard.services.agenda_service import Agenda, AgendaItem


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 21, 12)

    def today(self) -> date:
        return date(2026, 8, 21)


def todo(todo_id: int, content: str) -> Todo:
    timestamp = datetime(2026, 8, 21, 9)
    return Todo(
        id=todo_id,
        content=content,
        deadline_date=None,
        deadline_time=None,
        planned_date=date(2026, 8, 21),
        planned_start_time=time(9),
        planned_end_time=None,
        completed_at=None,
        display_order=todo_id,
        created_at=timestamp,
        updated_at=timestamp,
    )


class FakeTodoService:
    def __init__(self) -> None:
        self.calls = 0
        self.items = [todo(1, "复习")]

    def get_dashboard_items(self) -> list[Todo]:
        self.calls += 1
        return list(self.items)


class FakeAgendaService:
    def __init__(self) -> None:
        self.calls: list[date] = []
        self.agenda = Agenda(
            date=date(2026, 8, 21),
            timed_items=[
                AgendaItem(
                    id=7,
                    type="course",
                    title="统计学",
                    date=date(2026, 8, 21),
                    start=time(10),
                    end=time(11),
                    time_kind="range",
                    classroom="A101",
                )
            ],
        )

    def get_today(self, day: date) -> Agenda:
        self.calls.append(day)
        return self.agenda


def test_dashboard_state_is_one_python_owned_coarse_snapshot():
    todo_service = FakeTodoService()
    agenda_service = FakeAgendaService()

    state = present_dashboard_state(
        todo_service=todo_service,
        agenda_service=agenda_service,
        clock=FakeClock(),
    )

    assert set(state) == {
        "app",
        "profile",
        "widgets",
        "todos",
        "agenda",
        "weather",
        "finance",
        "networkStatus",
    }
    assert state["app"] == {"mode": "interaction", "today": "2026-08-21"}
    assert state["todos"][0]["content"] == "复习"
    assert state["agenda"]["timedItems"][0] == {
        "id": 7,
        "type": "course",
        "title": "统计学",
        "date": "2026-08-21",
        "start": "10:00",
        "end": "11:00",
        "timeKind": "range",
        "completed": False,
        "conflict": False,
        "classroom": "A101",
    }
    assert todo_service.calls == 1
    assert agenda_service.calls == [date(2026, 8, 21)]


def test_dashboard_state_rebuild_uses_new_service_state_without_js_rules():
    todo_service = FakeTodoService()
    agenda_service = FakeAgendaService()
    first = present_dashboard_state(
        todo_service=todo_service,
        agenda_service=agenda_service,
        clock=FakeClock(),
    )

    todo_service.items = [todo(2, "新事项")]
    second = present_dashboard_state(
        todo_service=todo_service,
        agenda_service=agenda_service,
        clock=FakeClock(),
    )

    assert first["todos"][0]["content"] == "复习"
    assert second["todos"][0]["content"] == "新事项"
    assert todo_service.calls == 2
    assert agenda_service.calls == [date(2026, 8, 21), date(2026, 8, 21)]
