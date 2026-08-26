from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.todo import TodoUpdate
from deskboard.repositories.course_repository import CourseRepository
from deskboard.repositories.todo_repository import TodoRepository
from deskboard.services.course_service import CourseService
from deskboard.services.timetable_service import TimetableService
from deskboard.services.todo_service import TodoService


@dataclass
class _Clock:
    current: datetime = datetime(2026, 8, 25, 10, 30)

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


def test_timetable_uses_uniform_axis_metadata_and_continuous_bounds():
    connection = connect_database(":memory:")
    migrate(connection)
    clock = _Clock()
    courses = CourseService(CourseRepository(connection), clock)
    todos = TodoService(TodoRepository(connection), clock)
    semester = courses.create_semester("Fall", date(2026, 8, 24), 4, active=True)
    scheme = courses.create_timetable_scheme(
        "Uniform",
        axis_mode="uniform_day",
        period_count=4,
        day_start=time(8),
        day_end=time(20),
    )
    courses.bind_semester_timetable_scheme(semester.id, scheme.id)
    course = courses.create_recurring_course(
        semester.id, "Actual time", 2, time(9, 15), time(10, 5), 1, 4
    )
    todo = todos.add_quick("inside")
    todos.update(
        todo.id,
        TodoUpdate(planned_date=date(2026, 8, 25), planned_start_time=time(19, 30)),
    )

    week = TimetableService(todos, courses).get_current_week(date(2026, 8, 25))
    assert week.axis_mode == "uniform_day"
    assert week.visible_start == time(8)
    assert week.visible_end == time(20)
    assert week.periods == []
    assert week.guide_count == 4
    assert [(item.id, item.start) for item in week.events] == [
        (course.id, time(9, 15)),
        (todo.id, time(19, 30)),
    ]


def test_unbound_global_scheme_does_not_bypass_active_semester_configuration():
    connection = connect_database(":memory:")
    migrate(connection)
    clock = _Clock()
    courses = CourseService(CourseRepository(connection), clock)
    todos = TodoService(TodoRepository(connection), clock)
    courses.create_semester("Fall", date(2026, 8, 24), 4, active=True)
    courses.create_timetable_scheme("Unused", axis_mode="uniform_day", period_count=4)

    week = TimetableService(todos, courses).get_current_week(date(2026, 8, 25))

    assert week.configuration_required is True
    assert week.visible_start is None
    assert week.visible_end is None
