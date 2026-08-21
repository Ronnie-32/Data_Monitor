from __future__ import annotations

from datetime import date, datetime, time

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.course import ClassPeriod
from deskboard.repositories.course_repository import CourseRepository


@pytest.fixture
def repository(tmp_path):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    return CourseRepository(connection)


def test_course_repository_round_trips_all_course_domain_records(repository):
    now = datetime(2026, 8, 21, 9, 30)

    semester = repository.create_semester(
        name="秋季学期",
        start_monday=date(2026, 9, 7),
        total_weeks=16,
        now=now,
    )
    recurring = repository.create_recurring_course(
        semester_id=semester.id,
        name="统计学",
        weekday=1,
        start_time=time(8),
        end_time=time(9, 30),
        start_week=1,
        end_week=16,
        classroom="A101",
        now=now,
    )
    one_off = repository.create_one_off_course(
        semester_id=semester.id,
        name="补课",
        course_date=date(2026, 9, 12),
        start_time=time(10),
        end_time=time(11),
        classroom=None,
        now=now,
    )
    cancellation = repository.add_cancellation(
        recurring.id, date(2026, 9, 14)
    )
    periods = [
        ClassPeriod(period_no=index, start_time=time(7 + index), end_time=time(8 + index))
        for index in range(1, 9)
    ]
    repository.replace_class_periods(periods)

    assert repository.require_semester(semester.id) == semester
    assert repository.require_recurring_course(recurring.id) == recurring
    assert repository.require_one_off_course(one_off.id) == one_off
    assert cancellation.recurring_course_id == recurring.id
    assert cancellation.occurrence_date == date(2026, 9, 14)
    assert repository.list_cancellations(recurring.id) == [cancellation]
    assert repository.list_class_periods() == periods


def test_course_repository_active_semester_and_cancellation_are_idempotent(repository):
    now = datetime(2026, 8, 21, 9, 30)
    first = repository.create_semester(
        name="春季", start_monday=date(2026, 2, 23), total_weeks=16, now=now
    )
    second = repository.create_semester(
        name="秋季", start_monday=date(2026, 9, 7), total_weeks=16, now=now
    )

    repository.set_active_semester(first.id, now)
    active = repository.get_active_semester()
    assert active is not None
    assert active.id == first.id
    assert active.is_active is True
    repository.set_active_semester(second.id, now)
    assert repository.get_active_semester().id == second.id
    repository.set_active_semester(None, now)
    assert repository.get_active_semester() is None

    recurring = repository.create_recurring_course(
        semester_id=first.id,
        name="课程",
        weekday=1,
        start_time=time(8),
        end_time=time(9),
        start_week=1,
        end_week=16,
        now=now,
    )
    repository.add_cancellation(recurring.id, date(2026, 3, 2))
    repository.add_cancellation(recurring.id, date(2026, 3, 2))
    assert repository.list_cancellations(recurring.id) == [
        repository.list_cancellations(recurring.id)[0]
    ]


def test_course_repository_update_and_delete_operations(repository):
    now = datetime(2026, 8, 21, 9, 30)
    semester = repository.create_semester(
        name="原名称", start_monday=date(2026, 9, 7), total_weeks=16, now=now
    )
    updated = repository.update_semester(
        semester.id,
        {"name": "新名称", "total_weeks": 18},
        now,
    )
    assert updated.name == "新名称"
    assert updated.total_weeks == 18

    with pytest.raises(LookupError):
        repository.delete_semester(999)
    repository.delete_semester(semester.id)
    assert repository.get_semester(semester.id) is None


def test_course_repository_source_owns_only_course_tables():
    from pathlib import Path

    source = Path("src/deskboard/repositories/course_repository.py").read_text(
        encoding="utf-8"
    )
    for table in (
        "semesters",
        "recurring_courses",
        "course_cancellations",
        "one_off_courses",
        "class_periods",
    ):
        assert table in source
    for forbidden_table in ("todos", "app_settings", "profiles", "network_cache"):
        assert forbidden_table not in source
