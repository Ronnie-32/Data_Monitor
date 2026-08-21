from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.course import ClassPeriod
from deskboard.models.todo import TodoUpdate
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


@pytest.fixture
def services(tmp_path):
    clock = FakeClock(datetime(2026, 8, 21, 15, 0))
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    todo_service = TodoService(TodoRepository(connection), clock)
    course_service = CourseService(CourseRepository(connection), clock)
    return todo_service, course_service, clock


def _periods() -> list[ClassPeriod]:
    return [
        ClassPeriod(period_no=index, start_time=time(7 + index), end_time=time(8 + index))
        for index in range(1, 9)
    ]


def _active_semester(course_service: CourseService, *, total_weeks: int = 4):
    return course_service.create_semester(
        "秋季学期", date(2026, 8, 17), total_weeks, active=True
    )


def test_current_week_has_monday_to_sunday_scope_and_teaching_label(services):
    _, course_service, _ = services
    semester = _active_semester(course_service)
    course_service.save_class_periods(_periods())

    week = TimetableService(course_service, _todo_service(services)).get_current_week(
        date(2026, 8, 21)
    )

    assert week.week_start == date(2026, 8, 17)
    assert week.week_end == date(2026, 8, 23)
    assert week.week_dates == [date(2026, 8, day) for day in range(17, 24)]
    assert week.week_label == "第 1 周"
    assert semester.id == course_service.get_active_semester().id


def _todo_service(services) -> TodoService:
    return services[0]


def test_outside_teaching_range_blanks_label_but_keeps_matching_one_off(services):
    _, course_service, _ = services
    semester = _active_semester(course_service, total_weeks=1)
    course_service.save_class_periods(_periods())
    one_off = course_service.create_one_off_course(
        semester.id, "假期补课", date(2026, 8, 24), time(9), time(10)
    )

    week = TimetableService(course_service, _todo_service(services)).get_current_week(
        date(2026, 8, 24)
    )

    assert week.week_label == ""
    assert [event.id for event in week.events] == [one_off.id]


@pytest.mark.parametrize(
    ("header_mode", "expected"),
    [
        ("weekday", "周一"),
        ("weekday_date", "周一 08-17"),
        ("date", "08-17"),
    ],
)
def test_header_modes_are_domain_owned_and_have_no_navigation_state(
    services, header_mode, expected
):
    _, course_service, _ = services
    _active_semester(course_service)
    course_service.save_class_periods(_periods())

    week = TimetableService(course_service, _todo_service(services)).get_current_week(
        date(2026, 8, 21), header_mode=header_mode
    )

    assert week.headers[0] == expected
    assert not hasattr(week, "previous_week")
    assert not hasattr(week, "next_week")


def test_unconfigured_periods_return_configuration_required_without_bounds(services):
    _, course_service, _ = services
    _active_semester(course_service)

    week = TimetableService(course_service, _todo_service(services)).get_current_week(
        date(2026, 8, 21)
    )

    assert week.configuration_required is True
    assert week.visible_start is None
    assert week.visible_end is None
    assert week.events == []


def test_timetable_preserves_course_times_and_filters_wholly_outside_events(services):
    todo_service, course_service, _ = services
    semester = _active_semester(course_service)
    course_service.save_class_periods(_periods())
    course = course_service.create_recurring_course(
        semester.id, "统计学", 5, time(8, 30), time(9, 20), 1, 4
    )
    before = todo_service.add_quick("过早事项")
    todo_service.update(
        before.id,
        TodoUpdate(
            planned_date=date(2026, 8, 21),
            planned_start_time=time(7, 30),
            planned_end_time=time(7, 45),
        ),
    )
    after = todo_service.add_quick("过晚事项")
    todo_service.update(
        after.id,
        TodoUpdate(
            planned_date=date(2026, 8, 21),
            planned_start_time=time(16, 30),
            planned_end_time=time(17),
        ),
    )

    week = TimetableService(course_service, todo_service).get_current_week(date(2026, 8, 21))

    assert week.visible_start == time(8)
    assert week.visible_end == time(16)
    assert [(event.title, event.start, event.end) for event in week.events] == [
        ("统计学", time(8, 30), time(9, 20))
    ]
    assert week.events[0].id == course.id


def test_timetable_supports_point_range_and_excludes_date_only_or_deadline_todos(services):
    todo_service, course_service, _ = services
    _active_semester(course_service)
    course_service.save_class_periods(_periods())
    point = todo_service.add_quick("点任务")
    todo_service.update(
        point.id,
        TodoUpdate(planned_date=date(2026, 8, 21), planned_start_time=time(10)),
    )
    ranged = todo_service.add_quick("区间任务")
    todo_service.update(
        ranged.id,
        TodoUpdate(
            planned_date=date(2026, 8, 21),
            planned_start_time=time(11),
            planned_end_time=time(12),
        ),
    )
    date_only = todo_service.add_quick("日期任务")
    todo_service.update(date_only.id, TodoUpdate(planned_date=date(2026, 8, 21)))
    deadline = todo_service.add_quick("截止任务")
    todo_service.update(deadline.id, TodoUpdate(deadline_date=date(2026, 8, 21)))
    other_week = todo_service.add_quick("下周任务")
    todo_service.update(
        other_week.id,
        TodoUpdate(planned_date=date(2026, 8, 28), planned_start_time=time(10)),
    )

    week = TimetableService(course_service, todo_service).get_current_week(date(2026, 8, 21))

    assert [(event.title, event.time_kind, event.start, event.end) for event in week.events] == [
        ("点任务", "point", time(10), None),
        ("区间任务", "range", time(11), time(12)),
    ]


def test_completed_past_todo_remains_and_overlap_is_metadata_only(services):
    todo_service, course_service, clock = services
    semester = _active_semester(course_service)
    course_service.save_class_periods(_periods())
    course = course_service.create_recurring_course(
        semester.id, "概率论", 5, time(9), time(10), 1, 4
    )
    todo = todo_service.add_quick("冲突复习")
    todo_service.update(
        todo.id,
        TodoUpdate(
            planned_date=date(2026, 8, 21),
            planned_start_time=time(9, 30),
            planned_end_time=time(10, 30),
        ),
    )
    todo_service.set_completed(todo.id, True)
    clock.current = datetime(2026, 8, 21, 15)

    week = TimetableService(course_service, todo_service).get_current_week(date(2026, 8, 21))

    course_event = next(
        event for event in week.events if event.type == "course" and event.id == course.id
    )
    todo_event = next(
        event for event in week.events if event.type == "todo" and event.id == todo.id
    )
    assert course_event.conflict is True
    assert todo_event.conflict is True
    assert todo_event.completed is True
    assert todo_event.end == time(10, 30)
    assert todo_service.get(todo.id).planned_end_time == time(10, 30)
