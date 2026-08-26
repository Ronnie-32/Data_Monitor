from __future__ import annotations

from datetime import date, datetime, time

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.models.course import TimetableSchemePeriod
from deskboard.repositories.course_repository import CourseRepository
from deskboard.services.course_service import CourseService


def service() -> CourseService:
    connection = connect_database(":memory:")
    migrate(connection)
    return CourseService(CourseRepository(connection), _Clock())


class _Clock:
    def now(self) -> datetime:
        return datetime(2026, 8, 25, 10, 30)

    def today(self) -> date:
        return date(2026, 8, 25)


def test_custom_scheme_accepts_gaps_and_boundary_counts():
    target = service()
    periods = [
        TimetableSchemePeriod(index, time(7 + index), time(8 + index))
        for index in range(1, 9)
    ]
    scheme = target.create_timetable_scheme(
        "Eight",
        axis_mode="custom_periods",
        period_count=8,
        periods=periods,
    )
    assert scheme.axis_mode == "custom_periods"
    assert scheme.visible_start == time(8)
    assert scheme.visible_end == time(16)

    one = target.create_timetable_scheme(
        "One",
        axis_mode="custom_periods",
        period_count=1,
        periods=[TimetableSchemePeriod(1, time(12), time(13))],
    )
    assert one.period_count == 1


@pytest.mark.parametrize(
    "periods",
    [
        [TimetableSchemePeriod(1, time(8), time(9))],
        [TimetableSchemePeriod(2, time(8), time(9)), TimetableSchemePeriod(1, time(9), time(10))],
        [TimetableSchemePeriod(1, time(8), time(10)), TimetableSchemePeriod(2, time(9), time(11))],
    ],
)
def test_invalid_custom_rows_never_activate(periods):
    target = service()
    with pytest.raises((TypeError, ValueError)):
        target.create_timetable_scheme(
            "Invalid",
            axis_mode="custom_periods",
            period_count=2,
            periods=periods,
        )
    assert target.list_timetable_schemes() == []


def test_uniform_scheme_has_full_day_default_and_no_period_semantics():
    target = service()
    scheme = target.create_timetable_scheme(
        "No school periods",
        axis_mode="uniform_day",
        period_count=6,
    )
    assert scheme.day_start == time(0)
    assert scheme.day_end == target.day_end_of_day
    assert scheme.periods == ()
    assert scheme.guide_count == 6


def test_scheme_reuse_and_confirmed_bound_delete_unbinds_semesters():
    target = service()
    scheme = target.create_timetable_scheme(
        "Shared",
        axis_mode="uniform_day",
        period_count=4,
    )
    first = target.create_semester("Fall", date(2026, 9, 7), 16)
    second = target.create_semester("Spring", date(2027, 2, 22), 16)
    target.bind_semester_timetable_scheme(first.id, scheme.id)
    target.bind_semester_timetable_scheme(second.id, scheme.id)
    assert target.get_timetable_scheme_for_semester(second.id).id == scheme.id

    with pytest.raises(ValueError, match="confirm"):
        target.delete_timetable_scheme(scheme.id)
    target.delete_timetable_scheme(scheme.id, confirmed=True)
    assert target.get_semester(first.id).timetable_scheme_id is None
    assert target.get_semester(second.id).timetable_scheme_id is None
