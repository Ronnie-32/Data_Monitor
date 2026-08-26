"""Course-domain values independent of persistence and UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Literal

TimetableSchemeAxisMode = Literal["custom_periods", "uniform_day"]

DEFAULT_TIMETABLE_SCHEME_NAME = "方案1"

# ``datetime.time`` cannot represent 24:00.  This sentinel keeps comparisons
# and arithmetic monotonic while the persistence/presentation helpers render
# it as the user-facing ``24:00`` value.
END_OF_DAY = time(23, 59, 59, 999999)


@dataclass(frozen=True, slots=True)
class TimetableSchemePeriod:
    period_no: int
    start_time: time
    end_time: time

    @property
    def start(self) -> time:
        return self.start_time

    @property
    def end(self) -> time:
        return self.end_time


@dataclass(frozen=True, slots=True)
class TimetableScheme:
    id: int
    name: str
    axis_mode: TimetableSchemeAxisMode
    period_count: int
    day_start: time | None
    day_end: time | None
    is_builtin: bool
    periods: tuple[TimetableSchemePeriod, ...]
    created_at: datetime
    updated_at: datetime

    @property
    def visible_start(self) -> time | None:
        if self.axis_mode == "custom_periods":
            return self.periods[0].start_time if self.periods else None
        return self.day_start

    @property
    def visible_end(self) -> time | None:
        if self.axis_mode == "custom_periods":
            return self.periods[-1].end_time if self.periods else None
        return self.day_end

    @property
    def guide_count(self) -> int:
        return self.period_count


@dataclass(frozen=True, slots=True)
class Semester:
    id: int
    name: str
    start_monday: date
    total_weeks: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    timetable_scheme_id: int | None = None


@dataclass(frozen=True, slots=True)
class RecurringCourse:
    id: int
    semester_id: int
    name: str
    weekday: int
    start_time: time
    end_time: time
    start_week: int
    end_week: int
    classroom: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CourseCancellation:
    recurring_course_id: int
    occurrence_date: date


@dataclass(frozen=True, slots=True)
class OneOffCourse:
    id: int
    semester_id: int
    name: str
    course_date: date
    start_time: time
    end_time: time
    classroom: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ClassPeriod:
    period_no: int
    start_time: time
    end_time: time


@dataclass(frozen=True, slots=True)
class CourseOccurrence:
    """A normalized course instance for a concrete local calendar date."""

    course_id: int
    semester_id: int
    name: str
    occurrence_date: date
    start_time: time
    end_time: time
    classroom: str | None
    source: Literal["recurring", "one_off"]

    @property
    def id(self) -> int:
        """Return the source course ID for consumers that use generic IDs."""
        return self.course_id

    @property
    def type(self) -> str:
        """Return the semantic source name used by later presentation layers."""
        return self.source

    @property
    def date(self) -> date:
        return self.occurrence_date

    @property
    def start(self) -> time:
        return self.start_time

    @property
    def end(self) -> time:
        return self.end_time
