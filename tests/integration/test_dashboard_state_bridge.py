from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path

from deskboard.app.modes import AppMode
from deskboard.models.todo import Todo
from deskboard.services.agenda_service import Agenda, AgendaItem
from deskboard.ui.dashboard.bridge import DashboardBridge


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
        planned_date=None,
        planned_start_time=None,
        planned_end_time=None,
        completed_at=None,
        display_order=todo_id,
        created_at=timestamp,
        updated_at=timestamp,
    )


class FakeTodoService:
    def __init__(self) -> None:
        self.items = [todo(1, "第一项")]
        self.calls = 0

    def get_dashboard_items(self) -> list[Todo]:
        self.calls += 1
        return list(self.items)


class FakeAgendaService:
    def __init__(self) -> None:
        self.calls = 0

    def get_today(self, day: date) -> Agenda:
        self.calls += 1
        return Agenda(
            date=day,
            timed_items=[
                AgendaItem(
                    id=2,
                    type="todo",
                    title="按时复习",
                    date=day,
                    start=time(13),
                    end=None,
                    time_kind="point",
                )
            ],
        )


def test_initial_state_is_requested_once_as_one_coarse_payload():
    todo_service = FakeTodoService()
    agenda_service = FakeAgendaService()
    bridge = DashboardBridge(
        todo_service=todo_service,
        agenda_service=agenda_service,
        clock=FakeClock(),
    )
    states: list[dict[str, object]] = []
    bridge.stateChanged.connect(states.append)

    bridge.requestInitialState()

    assert len(states) == 1
    assert set(states[0]) == {
        "app",
        "profile",
        "widgets",
        "todos",
        "agenda",
        "weather",
        "finance",
        "networkStatus",
    }
    assert states[0]["agenda"]["timedItems"][0]["title"] == "按时复习"
    assert todo_service.calls == 1
    assert agenda_service.calls == 1


def test_service_side_todo_refresh_emits_python_presented_agenda():
    todo_service = FakeTodoService()
    agenda_service = FakeAgendaService()
    bridge = DashboardBridge(
        todo_service=todo_service,
        agenda_service=agenda_service,
        clock=FakeClock(),
    )
    agenda_events: list[dict[str, object]] = []
    bridge.agendaChanged.connect(agenda_events.append)

    bridge.publish_todos()

    assert len(agenda_events) == 1
    assert agenda_events[0]["timedItems"][0]["start"] == "13:00"


def test_timetable_request_is_title_command_only_and_mode_gated():
    bridge = DashboardBridge(clock=FakeClock())
    requests: list[bool] = []
    bridge.weeklyTimetableRequested.connect(lambda: requests.append(True))

    bridge.publish_mode(AppMode.LOCKED)
    bridge.requestWeeklyTimetable()
    bridge.publish_mode(AppMode.INTERACTION)
    bridge.requestWeeklyTimetable()

    assert requests == [True]


def test_dashboard_web_assets_use_store_and_view_only_agenda_contract():
    web_root = Path("src/deskboard/ui/dashboard/web")
    html = (web_root / "index.html").read_text(encoding="utf-8")
    app = (web_root / "js/app.js").read_text(encoding="utf-8")
    bridge = (web_root / "js/bridge.js").read_text(encoding="utf-8")
    store = (web_root / "js/store.js").read_text(encoding="utf-8")
    agenda = (web_root / "js/widgets/agenda.js").read_text(encoding="utf-8")

    assert './js/app.js' in html
    assert "requestInitialState" in app
    assert "stateChanged" in bridge
    assert "createStore" in store
    assert "agendaChanged" in bridge
    assert "requestWeeklyTimetable" in agenda
    assert "requestDeleteTodo" not in agenda
    assert "toggleTodo" not in agenda
    assert "get_occurrences" not in app
    assert "planned" not in app
