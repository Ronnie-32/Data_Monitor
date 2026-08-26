from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.infrastructure.clock import Clock
from deskboard.models.course import ClassPeriod
from deskboard.repositories.course_repository import CourseRepository
from deskboard.services.course_service import CourseService


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 8, 21, 9, 30))


@pytest.fixture
def service(tmp_path, clock):
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    return CourseService(CourseRepository(connection), clock)


def add_active_semester(service, *, start=date(2026, 9, 7), total_weeks=16):
    semester = service.create_semester(
        name="秋季学期",
        start_monday=start,
        total_weeks=total_weeks,
    )
    service.set_active_semester(semester.id)
    return service.get_active_semester()


def add_recurring(service, semester_id, **overrides):
    values = {
        "semester_id": semester_id,
        "name": "统计学",
        "weekday": 1,
        "start_time": time(8),
        "end_time": time(9, 30),
        "start_week": 1,
        "end_week": 16,
        "classroom": "A101",
    }
    values.update(overrides)
    return service.create_recurring_course(**values)


def uibe_periods() -> list[ClassPeriod]:
    return [
        ClassPeriod(1, time(8), time(9, 30)),
        ClassPeriod(2, time(9, 50), time(11, 20)),
        ClassPeriod(3, time(11, 30), time(12, 10)),
        ClassPeriod(4, time(13, 30), time(15)),
        ClassPeriod(5, time(15, 20), time(16, 50)),
        ClassPeriod(6, time(17), time(17, 40)),
        ClassPeriod(7, time(18, 30), time(20)),
        ClassPeriod(8, time(20, 10), time(20, 50)),
    ]


def test_active_semester_allows_zero_or_one_but_not_two(service):
    service.set_active_semester(None)
    assert service.get_active_semester() is None
    first = service.create_semester(
        name="春季", start_monday=date(2026, 2, 23), total_weeks=16
    )
    second = service.create_semester(
        name="秋季", start_monday=date(2026, 9, 7), total_weeks=16
    )

    service.set_active_semester(first.id)
    assert service.get_active_semester().id == first.id
    with pytest.raises(ValueError, match="active"):
        service.set_active_semester(second.id, require_empty=True)

    service.set_active_semester(None)
    service.set_active_semester(second.id)
    assert service.get_active_semester().id == second.id


def test_semester_requires_monday_and_positive_total_weeks(service):
    with pytest.raises(ValueError, match="Monday"):
        service.create_semester(
            name="错误学期", start_monday=date(2026, 9, 8), total_weeks=16
        )
    with pytest.raises(ValueError, match="week"):
        service.create_semester(
            name="错误学期", start_monday=date(2026, 9, 7), total_weeks=0
        )


def test_teaching_week_is_monday_based_and_excludes_outside_dates(service):
    semester = add_active_semester(service, total_weeks=2)

    assert service.get_teaching_week(semester.start_monday) == 1
    assert service.get_teaching_week(semester.start_monday + timedelta(days=6)) == 1
    assert service.get_teaching_week(semester.start_monday + timedelta(days=7)) == 2
    assert service.get_teaching_week(semester.start_monday - timedelta(days=1)) is None
    assert service.get_teaching_week(semester.start_monday + timedelta(days=14)) is None


def test_default_period_configuration_is_uibe_and_valid_periods_are_exactly_one_to_eight(
    service,
):
    assert service.get_class_periods() == uibe_periods()
    assert service.has_configured_class_periods() is True

    periods = [
        ClassPeriod(period_no=index, start_time=time(7 + index), end_time=time(8 + index))
        for index in range(1, 9)
    ]
    service.save_class_periods(periods)

    assert service.has_configured_class_periods() is True
    assert service.get_class_periods() == periods


@pytest.mark.parametrize(
    "periods",
    [
        [ClassPeriod(index, time(8), time(9)) for index in range(1, 8)],
        [ClassPeriod(index, time(8), time(9)) for index in range(1, 9)]
        + [ClassPeriod(8, time(10), time(11))],
        [ClassPeriod(0, time(8), time(9))]
        + [ClassPeriod(index, time(9), time(10)) for index in range(2, 9)],
        [ClassPeriod(9, time(8), time(9))]
        + [ClassPeriod(index, time(9), time(10)) for index in range(1, 8)],
        [ClassPeriod(index, time(9), time(8)) for index in range(1, 9)],
    ],
)
def test_invalid_period_sets_are_rejected_without_partial_activation(service, periods):
    with pytest.raises(ValueError):
        service.save_class_periods(periods)
    assert service.get_class_periods() == uibe_periods()
    assert service.has_configured_class_periods() is True


def test_recurring_course_occurs_every_week_on_matching_weekday(service):
    semester = add_active_semester(service)
    recurring = add_recurring(service, semester.id)

    first_monday = semester.start_monday
    second_monday = first_monday + timedelta(days=7)
    assert service.get_occurrences_for_date(first_monday)[0].course_id == recurring.id
    assert service.get_occurrences_for_date(second_monday)[0].occurrence_date == second_monday
    assert service.get_occurrences_for_date(first_monday + timedelta(days=1)) == []


def test_recurring_course_respects_week_range_without_odd_even_filter(service):
    semester = add_active_semester(service, total_weeks=4)
    recurring = add_recurring(service, semester.id, start_week=2, end_week=3)

    assert service.get_occurrences_for_date(semester.start_monday) == []
    assert len(service.get_occurrences_for_date(semester.start_monday + timedelta(days=7))) == 1
    assert len(service.get_occurrences_for_date(semester.start_monday + timedelta(days=14))) == 1
    assert service.get_occurrences_for_date(semester.start_monday + timedelta(days=21)) == []
    assert recurring.id in {
        occurrence.course_id
        for occurrence in service.get_occurrences_for_week(
            semester.start_monday + timedelta(days=7)
        )
        if occurrence.occurrence_date == semester.start_monday + timedelta(days=7)
    }


def test_cancellation_suppresses_only_one_occurrence_and_is_idempotent(service):
    semester = add_active_semester(service)
    recurring = add_recurring(service, semester.id)
    cancelled_day = semester.start_monday + timedelta(days=7)

    service.cancel_occurrence(recurring.id, cancelled_day)
    service.cancel_occurrence(recurring.id, cancelled_day)

    assert service.get_occurrences_for_date(cancelled_day) == []
    assert len(service.get_occurrences_for_date(semester.start_monday)) == 1
    assert len(service.get_occurrences_for_date(cancelled_day + timedelta(days=7))) == 1


def test_one_off_course_appears_only_on_explicit_date_and_supports_reschedule(service):
    semester = add_active_semester(service)
    recurring = add_recurring(service, semester.id)
    original_day = semester.start_monday
    replacement_day = original_day + timedelta(days=2)
    one_off = service.create_one_off_course(
        semester_id=semester.id,
        name="补课",
        course_date=replacement_day,
        start_time=time(14),
        end_time=time(15),
    )
    service.cancel_occurrence(recurring.id, original_day)

    original = service.get_occurrences_for_date(original_day)
    replacement = service.get_occurrences_for_date(replacement_day)
    assert original == []
    assert [(item.course_id, item.source) for item in replacement] == [
        (one_off.id, "one_off")
    ]
    assert service.get_occurrences_for_date(replacement_day + timedelta(days=1)) == []


def test_outside_semester_range_keeps_matching_one_off_but_not_recurring(service):
    semester = add_active_semester(service, total_weeks=2)
    add_recurring(service, semester.id)
    outside_day = semester.start_monday + timedelta(days=21)
    one_off = service.create_one_off_course(
        semester_id=semester.id,
        name="假期补课",
        course_date=outside_day,
        start_time=time(10),
        end_time=time(11),
    )

    assert service.get_teaching_week(outside_day) is None
    occurrences = service.get_occurrences_for_date(outside_day)
    assert [item.course_id for item in occurrences] == [one_off.id]
    assert all(item.source == "one_off" for item in occurrences)
    assert [item.course_id for item in service.get_occurrences_for_week(outside_day)] == [
        one_off.id
    ]


@pytest.mark.parametrize(
    "values",
    [
        {"weekday": 0},
        {"weekday": 8},
        {"start_time": time(9), "end_time": time(9)},
        {"start_time": time(10), "end_time": time(9)},
        {"start_week": 0},
        {"start_week": 3, "end_week": 2},
    ],
)
def test_recurring_course_validation_rejects_invalid_fields(service, values):
    semester = add_active_semester(service)
    with pytest.raises((TypeError, ValueError)):
        add_recurring(service, semester.id, **values)


def test_one_off_validation_rejects_non_later_end_and_blank_classroom_is_none(service):
    semester = add_active_semester(service)
    with pytest.raises(ValueError, match="end"):
        service.create_one_off_course(
            semester_id=semester.id,
            name="错误补课",
            course_date=semester.start_monday,
            start_time=time(10),
            end_time=time(10),
        )
    one_off = service.create_one_off_course(
        semester_id=semester.id,
        name="空教室",
        course_date=semester.start_monday,
        start_time=time(10),
        end_time=time(11),
        classroom="   ",
    )
    assert one_off.classroom is None


def test_service_uses_the_injected_local_clock_for_timestamps(service, clock):
    typed_clock: Clock = clock
    semester = service.create_semester(
        name="时钟学期", start_monday=date(2026, 9, 7), total_weeks=16
    )
    assert typed_clock.today() == date(2026, 8, 21)
    assert semester.created_at == clock.current
