"""Course-domain values independent of persistence and UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Literal


@dataclass(frozen=True, slots=True)
class Semester:
    id: int
    name: str
    start_monday: date
    total_weeks: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


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
