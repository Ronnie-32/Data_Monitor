from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.course import ClassPeriod
from deskboard.models.todo import TodoUpdate
from deskboard.presentation.timetable_presenter import present_timetable
from deskboard.repositories.course_repository import CourseRepository
from deskboard.repositories.todo_repository import TodoRepository
from deskboard.services.course_service import CourseService
from deskboard.services.timetable_service import TimetableService
from deskboard.services.todo_service import TodoService


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


def test_timetable_presenter_exposes_semantics_not_css_pixels(tmp_path):
    clock = FakeClock(datetime(2026, 8, 21, 15))
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    todo_service = TodoService(TodoRepository(connection), clock)
    course_service = CourseService(CourseRepository(connection), clock)
    semester = course_service.create_semester(
        "秋季学期", date(2026, 8, 17), 4, active=True
    )
    course_service.save_class_periods(
        [
            ClassPeriod(index, time(7 + index), time(8 + index))
            for index in range(1, 9)
        ]
    )
    course = course_service.create_recurring_course(
        semester.id, "统计学", 5, time(8, 30), time(9, 20), 1, 4, "A101"
    )
    todo = todo_service.add_quick("复习")
    todo_service.update(
        todo.id,
        TodoUpdate(
            planned_date=date(2026, 8, 21),
            planned_start_time=time(9),
            planned_end_time=time(10),
        ),
    )
    todo_service.set_completed(todo.id, True)

    view_model = present_timetable(
        TimetableService(course_service, todo_service).get_current_week(
            date(2026, 8, 21)
        )
    )

    assert view_model["weekLabel"] == "第 1 周"
    assert view_model["visibleStart"] == "08:00"
    assert view_model["visibleEnd"] == "16:00"
    course_item = next(
        item
        for item in view_model["events"]
        if item["type"] == "course" and item["id"] == course.id
    )
    todo_item = next(
        item
        for item in view_model["events"]
        if item["type"] == "todo" and item["id"] == todo.id
    )
    assert course_item["type"] == "course"
    assert course_item["start"] == "08:30"
    assert course_item["end"] == "09:20"
    assert course_item["classroom"] == "A101"
    assert todo_item["timeKind"] == "range"
    assert todo_item["completed"] is True
    assert todo_item["conflict"] is True
    assert all("top" not in item and "left" not in item for item in view_model["events"])
