from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.course import TimetableSchemePeriod
from deskboard.repositories.course_repository import CourseRepository
from deskboard.repositories.todo_repository import TodoRepository
from deskboard.services.course_service import CourseService
from deskboard.services.timetable_service import TimetableService
from deskboard.services.todo_service import TodoService
from deskboard.ui.dashboard.bridge import DashboardBridge


@dataclass
class _Clock:
    current: datetime = datetime(2026, 8, 25, 10, 30)

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


def test_bridge_presents_axis_metadata_without_exposing_scheme_rows():
    connection = connect_database(":memory:")
    migrate(connection)
    clock = _Clock()
    courses = CourseService(CourseRepository(connection), clock)
    todos = TodoService(TodoRepository(connection), clock)
    semester = courses.create_semester("Fall", date(2026, 8, 24), 4, active=True)
    scheme = courses.create_timetable_scheme(
        "Gapped custom",
        axis_mode="custom_periods",
        period_count=2,
        periods=(
            TimetableSchemePeriod(1, time(8), time(9)),
            TimetableSchemePeriod(2, time(10), time(11)),
        ),
    )
    courses.bind_semester_timetable_scheme(semester.id, scheme.id)
    bridge = DashboardBridge(
        timetable_service=TimetableService(todos, courses),
        clock=clock,
    )
    payloads: list[dict[str, object]] = []
    bridge.timetableChanged.connect(payloads.append)

    bridge.requestWeeklyTimetable()

    payload = payloads[-1]
    assert payload["axis"]["mode"] == "custom_periods"
    assert payload["axis"]["periodCount"] == 2
    assert payload["axis"]["visibleStart"] == "08:00"
    assert payload["axis"]["visibleEnd"] == "11:00"
    assert payload["axis"]["guides"][0]["label"] == "1"
    assert "periods" in payload
    assert "timetable_scheme_periods" not in str(payload)
