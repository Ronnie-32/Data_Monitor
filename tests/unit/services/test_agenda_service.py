from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.todo import TodoUpdate
from deskboard.repositories.course_repository import CourseRepository
from deskboard.repositories.todo_repository import TodoRepository
from deskboard.services.agenda_service import AgendaService
from deskboard.services.course_service import CourseService
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


def _active_semester(course_service: CourseService, *, total_weeks: int = 4):
    return course_service.create_semester(
        "秋季学期", date(2026, 8, 17), total_weeks, active=True
    )


def test_today_agenda_merges_and_sorts_courses_and_timed_todos(services):
    todo_service, course_service, _ = services
    semester = _active_semester(course_service)
    course_service.create_recurring_course(
        semester.id, "统计学", 5, time(9), time(10), 1, 4, "A101"
    )
    point = todo_service.add_quick("晨间复习")
    todo_service.update(
        point.id,
        TodoUpdate(planned_date=date(2026, 8, 21), planned_start_time=time(8, 30)),
    )
    ranged = todo_service.add_quick("整理笔记")
    todo_service.update(
        ranged.id,
        TodoUpdate(
            planned_date=date(2026, 8, 21),
            planned_start_time=time(11),
            planned_end_time=time(12),
        ),
    )

    agenda = AgendaService(todo_service, course_service).get_today(date(2026, 8, 21))

    assert [item.title for item in agenda.timed_items] == ["晨间复习", "统计学", "整理笔记"]
    assert [item.type for item in agenda.timed_items] == ["todo", "course", "todo"]
    assert agenda.timed_items[0].time_kind == "point"
    assert agenda.timed_items[0].end is None
    assert agenda.timed_items[1].classroom == "A101"
    assert agenda.timed_items[2].time_kind == "range"


def test_today_agenda_filters_by_date_and_includes_today_deadlines(services):
    todo_service, course_service, _ = services
    deadline = todo_service.add_quick("仅截止日期")
    todo_service.update(deadline.id, TodoUpdate(deadline_date=date(2026, 8, 21)))
    unplanned = todo_service.add_quick("无计划时间")
    today = todo_service.add_quick("今天")
    todo_service.update(today.id, TodoUpdate(planned_date=date(2026, 8, 21)))
    tomorrow = todo_service.add_quick("明天")
    todo_service.update(tomorrow.id, TodoUpdate(planned_date=date(2026, 8, 22)))

    agenda = AgendaService(todo_service, course_service).get_today(date(2026, 8, 21))

    assert [item.title for item in agenda.date_only_items] == ["今天", "仅截止日期"]
    assert deadline.id in {item.id for item in agenda.items}
    assert unplanned.id not in {item.id for item in agenda.items}
    assert tomorrow.id not in {item.id for item in agenda.items}


def test_today_deadline_is_shown_even_when_planned_date_is_another_day(services):
    todo_service, course_service, _ = services
    deadline = todo_service.add_quick("今天到期但计划在明天")
    todo_service.update(
        deadline.id,
        TodoUpdate(
            deadline_date=date(2026, 8, 21),
            planned_date=date(2026, 8, 22),
            planned_start_time=time(10),
        ),
    )

    agenda = AgendaService(todo_service, course_service).get_today(date(2026, 8, 21))

    item = next(item for item in agenda.items if item.id == deadline.id)
    assert item.time_kind == "date_only"
    assert item.start is None
    assert item.end is None


def test_date_only_todos_follow_manual_order_after_all_timed_items(services):
    todo_service, course_service, _ = services
    first_date_only = todo_service.add_quick("先添加的日期事项")
    todo_service.update(first_date_only.id, TodoUpdate(planned_date=date(2026, 8, 21)))
    timed = todo_service.add_quick("定时事项")
    todo_service.update(
        timed.id,
        TodoUpdate(planned_date=date(2026, 8, 21), planned_start_time=time(8)),
    )
    second_date_only = todo_service.add_quick("后添加的日期事项")
    todo_service.update(second_date_only.id, TodoUpdate(planned_date=date(2026, 8, 21)))
    todo_service.reorder([first_date_only.id, second_date_only.id, timed.id])

    agenda = AgendaService(todo_service, course_service).get_today(date(2026, 8, 21))

    assert [item.title for item in agenda.items] == [
        "定时事项",
        "先添加的日期事项",
        "后添加的日期事项",
    ]


def test_completed_scheduled_todo_and_past_items_remain_visible(services):
    todo_service, course_service, clock = services
    todo = todo_service.add_quick("已完成课程准备")
    todo_service.update(
        todo.id,
        TodoUpdate(planned_date=date(2026, 8, 21), planned_start_time=time(9)),
    )
    todo_service.set_completed(todo.id, True)
    clock.current = datetime(2026, 8, 21, 16)

    agenda = AgendaService(todo_service, course_service).get_today(date(2026, 8, 21))

    assert len(agenda.timed_items) == 1
    assert agenda.timed_items[0].completed is True


def test_agenda_marks_course_and_todo_overlap_without_rescheduling(services):
    todo_service, course_service, _ = services
    semester = _active_semester(course_service)
    course_service.create_recurring_course(
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

    agenda = AgendaService(todo_service, course_service).get_today(date(2026, 8, 21))

    assert {item.title for item in agenda.timed_items if item.conflict} == {
        "概率论",
        "冲突复习",
    }
    assert todo_service.get(todo.id).planned_start_time == time(9, 30)


def test_agenda_does_not_persist_a_generic_event_table(services):
    todo_service, course_service, _ = services
    AgendaService(todo_service, course_service).get_today(date(2026, 8, 21))
    tables = {
        row[0]
        for row in todo_service._repository._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert "events" not in tables
    assert "schedule" not in tables
