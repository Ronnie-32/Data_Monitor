"""Business rules for semesters, courses, cancellations, and class periods."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime, time, timedelta

from deskboard.infrastructure.clock import Clock, SystemClock
from deskboard.models.course import (
    DEFAULT_TIMETABLE_SCHEME_NAME,
    END_OF_DAY,
    ClassPeriod,
    CourseOccurrence,
    OneOffCourse,
    RecurringCourse,
    Semester,
    TimetableScheme,
    TimetableSchemeAxisMode,
    TimetableSchemePeriod,
)
from deskboard.repositories.course_repository import CourseRepository

_UNSET = object()


class CourseService:
    """Own course-domain validation and date-derived occurrence semantics."""

    def __init__(self, repository: CourseRepository, clock: Clock | None = None) -> None:
        self._repository = repository
        self._clock = clock or SystemClock()

    # Semester CRUD and active-state management.
    def create_semester(
        self,
        name: str,
        start_monday: date,
        total_weeks: int,
        *,
        active: bool = False,
        is_active: bool | None = None,
        timetable_scheme_id: int | None = None,
    ) -> Semester:
        if is_active is not None:
            active = is_active
        name = _required_text(name, "Semester name")
        _validate_start_monday(start_monday)
        _validate_total_weeks(total_weeks)
        if timetable_scheme_id is not None:
            self._repository.require_timetable_scheme(timetable_scheme_id)
        semester = self._repository.create_semester(
            name=name,
            start_monday=start_monday,
            total_weeks=total_weeks,
            now=self._clock.now(),
            is_active=False,
            timetable_scheme_id=timetable_scheme_id,
        )
        if active:
            return self.set_active_semester(semester.id)
        return semester

    def get_semester(self, semester_id: int) -> Semester | None:
        return self._repository.get_semester(semester_id)

    def require_semester(self, semester_id: int) -> Semester:
        return self._repository.require_semester(semester_id)

    def list_semesters(self) -> list[Semester]:
        return self._repository.list_semesters()

    def get_active_semester(self) -> Semester | None:
        return self._repository.get_active_semester()

    def set_active_semester(
        self, semester_id: int | None, *, require_empty: bool = False
    ) -> Semester | None:
        if semester_id is not None:
            self._repository.require_semester(semester_id)
        current = self._repository.get_active_semester()
        if require_empty and current is not None and current.id != semester_id:
            raise ValueError("Another semester is already active")
        return self._repository.set_active_semester(semester_id, self._clock.now())

    def update_semester(
        self,
        semester_id: int,
        *,
        name: str | object = _UNSET,
        start_monday: date | object = _UNSET,
        total_weeks: int | object = _UNSET,
        timetable_scheme_id: int | None | object = _UNSET,
    ) -> Semester:
        current = self._repository.require_semester(semester_id)
        next_name = current.name if name is _UNSET else name
        next_start = current.start_monday if start_monday is _UNSET else start_monday
        next_total = current.total_weeks if total_weeks is _UNSET else total_weeks
        next_scheme_id = (
            current.timetable_scheme_id
            if timetable_scheme_id is _UNSET
            else timetable_scheme_id
        )
        next_name = _required_text(next_name, "Semester name")
        _validate_start_monday(next_start)
        _validate_total_weeks(next_total)
        if next_scheme_id is not None:
            self._repository.require_timetable_scheme(next_scheme_id)
        fields = {
            key: value
            for key, value in {
                "name": name,
                "start_monday": start_monday,
                "total_weeks": total_weeks,
                "timetable_scheme_id": timetable_scheme_id,
            }.items()
            if value is not _UNSET
        }
        return self._repository.update_semester(semester_id, fields, self._clock.now())

    def delete_semester(self, semester_id: int) -> None:
        self._repository.delete_semester(semester_id)

    # Recurring-course CRUD.
    def create_recurring_course(
        self,
        semester_id: int,
        name: str,
        weekday: int,
        start_time: time,
        end_time: time,
        start_week: int,
        end_week: int,
        classroom: str | None = None,
    ) -> RecurringCourse:
        self._repository.require_semester(semester_id)
        name = _required_text(name, "Course name")
        classroom = _optional_text(classroom, "Classroom")
        _validate_weekday(weekday)
        _validate_time_range(start_time, end_time)
        _validate_week_range(start_week, end_week)
        return self._repository.create_recurring_course(
            semester_id=semester_id,
            name=name,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            start_week=start_week,
            end_week=end_week,
            classroom=classroom,
            now=self._clock.now(),
        )

    def get_recurring_course(self, course_id: int) -> RecurringCourse | None:
        return self._repository.get_recurring_course(course_id)

    def require_recurring_course(self, course_id: int) -> RecurringCourse:
        return self._repository.require_recurring_course(course_id)

    def list_recurring_courses(self, semester_id: int | None = None) -> list[RecurringCourse]:
        return self._repository.list_recurring_courses(semester_id)

    def update_recurring_course(
        self,
        course_id: int,
        *,
        semester_id: int | object = _UNSET,
        name: str | object = _UNSET,
        weekday: int | object = _UNSET,
        start_time: time | object = _UNSET,
        end_time: time | object = _UNSET,
        start_week: int | object = _UNSET,
        end_week: int | object = _UNSET,
        classroom: str | None | object = _UNSET,
    ) -> RecurringCourse:
        current = self._repository.require_recurring_course(course_id)
        next_semester_id = current.semester_id if semester_id is _UNSET else semester_id
        next_name = current.name if name is _UNSET else name
        next_weekday = current.weekday if weekday is _UNSET else weekday
        next_start_time = current.start_time if start_time is _UNSET else start_time
        next_end_time = current.end_time if end_time is _UNSET else end_time
        next_start_week = current.start_week if start_week is _UNSET else start_week
        next_end_week = current.end_week if end_week is _UNSET else end_week
        next_classroom = current.classroom if classroom is _UNSET else classroom
        self._repository.require_semester(next_semester_id)
        next_name = _required_text(next_name, "Course name")
        next_classroom = _optional_text(next_classroom, "Classroom")
        _validate_weekday(next_weekday)
        _validate_time_range(next_start_time, next_end_time)
        _validate_week_range(next_start_week, next_end_week)
        fields = {
            key: value
            for key, value in {
                "semester_id": semester_id,
                "name": name,
                "weekday": weekday,
                "start_time": start_time,
                "end_time": end_time,
                "start_week": start_week,
                "end_week": end_week,
                "classroom": next_classroom if classroom is not _UNSET else _UNSET,
            }.items()
            if value is not _UNSET
        }
        return self._repository.update_recurring_course(
            course_id, fields, self._clock.now()
        )

    def delete_recurring_course(self, course_id: int) -> None:
        self._repository.delete_recurring_course(course_id)

    # Cancellation and one-off course CRUD.
    def cancel_occurrence(self, course_id: int, occurrence_date: date) -> None:
        course = self._repository.require_recurring_course(course_id)
        semester = self._repository.require_semester(course.semester_id)
        _validate_date(occurrence_date, "Occurrence date")
        teaching_week = _teaching_week(semester, occurrence_date)
        if teaching_week is None:
            raise ValueError("Occurrence date is outside the semester teaching range")
        if occurrence_date.isoweekday() != course.weekday:
            raise ValueError("Occurrence date does not match the course weekday")
        if not course.start_week <= teaching_week <= course.end_week:
            raise ValueError("Occurrence date is outside the course week range")
        self._repository.add_cancellation(course_id, occurrence_date)

    def uncancel_occurrence(self, course_id: int, occurrence_date: date) -> bool:
        self._repository.require_recurring_course(course_id)
        _validate_date(occurrence_date, "Occurrence date")
        return self._repository.remove_cancellation(course_id, occurrence_date)

    def is_occurrence_cancelled(self, course_id: int, occurrence_date: date) -> bool:
        return self._repository.is_cancelled(course_id, occurrence_date)

    def create_one_off_course(
        self,
        semester_id: int,
        name: str,
        course_date: date,
        start_time: time,
        end_time: time,
        classroom: str | None = None,
    ) -> OneOffCourse:
        self._repository.require_semester(semester_id)
        name = _required_text(name, "Course name")
        classroom = _optional_text(classroom, "Classroom")
        _validate_date(course_date, "Course date")
        _validate_time_range(start_time, end_time)
        return self._repository.create_one_off_course(
            semester_id=semester_id,
            name=name,
            course_date=course_date,
            start_time=start_time,
            end_time=end_time,
            classroom=classroom,
            now=self._clock.now(),
        )

    def get_one_off_course(self, course_id: int) -> OneOffCourse | None:
        return self._repository.get_one_off_course(course_id)

    def require_one_off_course(self, course_id: int) -> OneOffCourse:
        return self._repository.require_one_off_course(course_id)

    def list_one_off_courses(self, semester_id: int | None = None) -> list[OneOffCourse]:
        return self._repository.list_one_off_courses(semester_id)

    def update_one_off_course(
        self,
        course_id: int,
        *,
        semester_id: int | object = _UNSET,
        name: str | object = _UNSET,
        course_date: date | object = _UNSET,
        start_time: time | object = _UNSET,
        end_time: time | object = _UNSET,
        classroom: str | None | object = _UNSET,
    ) -> OneOffCourse:
        current = self._repository.require_one_off_course(course_id)
        next_semester_id = current.semester_id if semester_id is _UNSET else semester_id
        next_name = current.name if name is _UNSET else name
        next_date = current.course_date if course_date is _UNSET else course_date
        next_start_time = current.start_time if start_time is _UNSET else start_time
        next_end_time = current.end_time if end_time is _UNSET else end_time
        next_classroom = current.classroom if classroom is _UNSET else classroom
        self._repository.require_semester(next_semester_id)
        next_name = _required_text(next_name, "Course name")
        next_classroom = _optional_text(next_classroom, "Classroom")
        _validate_date(next_date, "Course date")
        _validate_time_range(next_start_time, next_end_time)
        fields = {
            key: value
            for key, value in {
                "semester_id": semester_id,
                "name": name,
                "course_date": course_date,
                "start_time": start_time,
                "end_time": end_time,
                "classroom": next_classroom if classroom is not _UNSET else _UNSET,
            }.items()
            if value is not _UNSET
        }
        return self._repository.update_one_off_course(course_id, fields, self._clock.now())

    def delete_one_off_course(self, course_id: int) -> None:
        self._repository.delete_one_off_course(course_id)

    # Reusable timetable schemes and semester bindings.
    @property
    def day_end_of_day(self) -> time:
        return END_OF_DAY

    def create_timetable_scheme(
        self,
        name: str,
        *,
        axis_mode: TimetableSchemeAxisMode = "custom_periods",
        period_count: int | None = None,
        periods: Iterable[TimetableSchemePeriod | ClassPeriod | Mapping[str, object]] | None = None,
        day_start: time | str | None = None,
        day_end: time | str | None = None,
        is_builtin: bool = False,
    ) -> TimetableScheme:
        normalized_name = _required_text(name, "Timetable scheme name")
        normalized_mode, count, normalized_periods, start, end = _normalize_scheme(
            axis_mode=axis_mode,
            period_count=period_count,
            periods=periods,
            day_start=day_start,
            day_end=day_end,
        )
        return self._repository.create_timetable_scheme(
            name=normalized_name,
            axis_mode=normalized_mode,
            period_count=count,
            day_start=start,
            day_end=end,
            periods=normalized_periods,
            now=self._clock.now(),
            is_builtin=is_builtin,
        )

    def get_timetable_scheme(self, scheme_id: int) -> TimetableScheme | None:
        return self._repository.get_timetable_scheme(scheme_id)

    def require_timetable_scheme(self, scheme_id: int) -> TimetableScheme:
        return self._repository.require_timetable_scheme(scheme_id)

    def list_timetable_schemes(self) -> list[TimetableScheme]:
        return self._repository.list_timetable_schemes()

    # Short names keep the scheme API convenient for Settings and integrations.
    create_scheme = create_timetable_scheme
    get_scheme = get_timetable_scheme
    require_scheme = require_timetable_scheme
    list_schemes = list_timetable_schemes

    def save_timetable_scheme(
        self,
        scheme_id: int,
        name: str,
        *,
        axis_mode: TimetableSchemeAxisMode,
        period_count: int | None = None,
        periods: Iterable[TimetableSchemePeriod | ClassPeriod | Mapping[str, object]] | None = None,
        day_start: time | str | None = None,
        day_end: time | str | None = None,
    ) -> TimetableScheme:
        normalized_name = _required_text(name, "Timetable scheme name")
        normalized_mode, count, normalized_periods, start, end = _normalize_scheme(
            axis_mode=axis_mode,
            period_count=period_count,
            periods=periods,
            day_start=day_start,
            day_end=day_end,
        )
        return self._repository.replace_timetable_scheme(
            scheme_id,
            name=normalized_name,
            axis_mode=normalized_mode,
            period_count=count,
            day_start=start,
            day_end=end,
            periods=normalized_periods,
            now=self._clock.now(),
        )

    update_timetable_scheme = save_timetable_scheme
    save_scheme = save_timetable_scheme
    update_scheme = save_timetable_scheme

    def duplicate_timetable_scheme(self, scheme_id: int, name: str) -> TimetableScheme:
        normalized_name = _required_text(name, "Timetable scheme name")
        return self._repository.duplicate_timetable_scheme(
            scheme_id, name=normalized_name, now=self._clock.now()
        )

    duplicate_scheme = duplicate_timetable_scheme

    def rename_timetable_scheme(self, scheme_id: int, name: str) -> TimetableScheme:
        return self._repository.rename_timetable_scheme(
            scheme_id, _required_text(name, "Timetable scheme name"), self._clock.now()
        )

    rename_scheme = rename_timetable_scheme

    def delete_timetable_scheme(self, scheme_id: int, *, confirmed: bool = False) -> None:
        scheme = self._repository.require_timetable_scheme(scheme_id)
        bound = any(
            semester.timetable_scheme_id == scheme.id for semester in self.list_semesters()
        )
        if bound and not confirmed:
            raise ValueError("Deleting a bound timetable scheme requires confirmation")
        self._repository.delete_timetable_scheme(scheme_id)

    delete_scheme = delete_timetable_scheme

    def bind_semester_timetable_scheme(
        self, semester_id: int, scheme_id: int | None
    ) -> Semester:
        if scheme_id is not None:
            self._repository.require_timetable_scheme(scheme_id)
        return self._repository.bind_semester_timetable_scheme(
            semester_id, scheme_id, self._clock.now()
        )

    # Friendly aliases used by Settings and external callers.
    bind_semester_scheme = bind_semester_timetable_scheme

    def get_timetable_scheme_for_semester(self, semester_id: int) -> TimetableScheme | None:
        return self._repository.get_timetable_scheme_for_semester(semester_id)

    def get_active_timetable_scheme(self) -> TimetableScheme | None:
        return self._repository.get_active_timetable_scheme()

    def get_semester_scheme_state(self, semester_id: int) -> dict[str, object]:
        semester = self._repository.require_semester(semester_id)
        scheme = self.get_timetable_scheme_for_semester(semester_id)
        return {
            "semesterId": semester.id,
            "schemeId": semester.timetable_scheme_id,
            "schemeName": scheme.name if scheme else None,
            "configured": scheme is not None,
        }

    # Compatibility surface for Tasks 9–25.  It writes the built-in legacy
    # scheme rather than resurrecting the retired class_periods table.
    def save_class_periods(self, periods: Iterable[ClassPeriod]) -> list[ClassPeriod]:
        normalized = [_coerce_period(period) for period in periods]
        if len(normalized) != 8 or {period.period_no for period in normalized} != set(range(1, 9)):
            raise ValueError("Configured class periods must contain unique period numbers 1..8")
        for period in normalized:
            _validate_period(period)
        normalized.sort(key=lambda period: period.period_no)
        existing = next(
            (
                scheme
                for scheme in self.list_timetable_schemes()
                if scheme.is_builtin and scheme.axis_mode == "custom_periods"
            ),
            None,
        )
        scheme_periods = tuple(
            TimetableSchemePeriod(item.period_no, item.start_time, item.end_time)
            for item in normalized
        )
        if existing is None:
            existing = self.create_timetable_scheme(
                DEFAULT_TIMETABLE_SCHEME_NAME,
                axis_mode="custom_periods",
                period_count=8,
                periods=scheme_periods,
                is_builtin=True,
            )
        else:
            existing = self.save_timetable_scheme(
                existing.id,
                existing.name,
                axis_mode="custom_periods",
                period_count=8,
                periods=scheme_periods,
            )
        for semester in self.list_semesters():
            self.bind_semester_timetable_scheme(semester.id, existing.id)
        return [
            ClassPeriod(item.period_no, item.start_time, item.end_time)
            for item in existing.periods
        ]

    def replace_class_periods(self, periods: Iterable[ClassPeriod]) -> list[ClassPeriod]:
        return self.save_class_periods(periods)

    def get_class_periods(self) -> list[ClassPeriod]:
        return self._repository.list_class_periods()

    def list_class_periods(self) -> list[ClassPeriod]:
        return self.get_class_periods()

    def get_periods(self) -> list[ClassPeriod]:
        return self.get_class_periods()

    def has_configured_class_periods(self) -> bool:
        periods = self.get_class_periods()
        return len(periods) == 8 and {period.period_no for period in periods} == set(range(1, 9))

    # Date-derived course views.
    def get_teaching_week(self, day: date) -> int | None:
        _validate_date(day, "Teaching date")
        semester = self._repository.get_active_semester()
        return None if semester is None else _teaching_week(semester, day)

    def get_occurrences_for_date(self, day: date) -> list[CourseOccurrence]:
        _validate_date(day, "Occurrence date")
        semester = self._repository.get_active_semester()
        if semester is None:
            return []

        occurrences = [
            _one_off_occurrence(course, day)
            for course in self._repository.list_one_off_courses(semester.id)
            if course.course_date == day
        ]
        teaching_week = _teaching_week(semester, day)
        if teaching_week is not None:
            for course in self._repository.list_recurring_courses(semester.id):
                if course.weekday != day.isoweekday():
                    continue
                if not course.start_week <= teaching_week <= course.end_week:
                    continue
                if self._repository.is_cancelled(course.id, day):
                    continue
                occurrences.append(_recurring_occurrence(course, semester.id, day))
        occurrences.sort(key=_occurrence_sort_key)
        return occurrences

    def get_occurrences_for_week(self, day: date) -> list[CourseOccurrence]:
        _validate_date(day, "Week date")
        monday = day - timedelta(days=day.weekday())
        occurrences: list[CourseOccurrence] = []
        for offset in range(7):
            occurrences.extend(self.get_occurrences_for_date(monday + timedelta(days=offset)))
        return occurrences


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    result = value.strip()
    if not result:
        raise ValueError(f"{label} must not be empty")
    return result


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    result = value.strip()
    return result or None


def _validate_date(value: object, label: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError(f"{label} must be a date")


def _validate_start_monday(value: object) -> None:
    _validate_date(value, "start_monday")
    if value.weekday() != 0:
        raise ValueError("start_monday must be a Monday")


def _validate_total_weeks(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("total_weeks must be greater than zero")


def _validate_weekday(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 7:
        raise ValueError("weekday must be between 1 and 7")


def _validate_time_range(start: object, end: object) -> None:
    if not isinstance(start, time) or not isinstance(end, time):
        raise TypeError("Course start and end must be times")
    if end <= start:
        raise ValueError("Course end_time must be later than start_time")


def _validate_week_range(start: object, end: object) -> None:
    if (
        isinstance(start, bool)
        or not isinstance(start, int)
        or isinstance(end, bool)
        or not isinstance(end, int)
    ):
        raise TypeError("Course weeks must be integers")
    if start < 1 or end < start:
        raise ValueError("Course week range is invalid")


def _validate_period(period: ClassPeriod) -> None:
    if not isinstance(period.period_no, int) or isinstance(period.period_no, bool):
        raise TypeError("period_no must be an integer")
    _validate_time_range(period.start_time, period.end_time)


def _normalize_scheme(
    *,
    axis_mode: TimetableSchemeAxisMode,
    period_count: int | None,
    periods: Iterable[TimetableSchemePeriod | ClassPeriod | Mapping[str, object]] | None,
    day_start: time | str | None,
    day_end: time | str | None,
) -> tuple[
    TimetableSchemeAxisMode,
    int,
    tuple[TimetableSchemePeriod, ...],
    time | None,
    time | None,
]:
    if axis_mode not in ("custom_periods", "uniform_day"):
        raise ValueError("axis_mode must be custom_periods or uniform_day")
    raw_periods = tuple(_coerce_scheme_period(item) for item in (periods or ()))
    if period_count is None:
        period_count = len(raw_periods) if axis_mode == "custom_periods" else 8
    if isinstance(period_count, bool) or not isinstance(period_count, int):
        raise TypeError("period_count must be an integer")
    if not 1 <= period_count <= 24:
        raise ValueError("period_count must be between 1 and 24")

    if axis_mode == "custom_periods":
        if len(raw_periods) != period_count:
            raise ValueError("custom_periods requires exactly period_count rows")
        expected_numbers = list(range(1, period_count + 1))
        if [item.period_no for item in raw_periods] != expected_numbers:
            raise ValueError("custom period numbers must be increasing from 1")
        previous_end: time | None = None
        for item in raw_periods:
            if not isinstance(item.period_no, int) or isinstance(item.period_no, bool):
                raise TypeError("period_no must be an integer")
            _validate_time_range(item.start_time, item.end_time)
            if previous_end is not None and item.start_time < previous_end:
                raise ValueError("custom periods must not overlap")
            previous_end = item.end_time
        return axis_mode, period_count, raw_periods, None, None

    if raw_periods:
        raise ValueError("uniform_day stores no school-period rows")
    normalized_start = _coerce_clock(day_start, "day_start") if day_start is not None else time(0)
    normalized_end = (
        _coerce_clock(day_end, "day_end", allow_end_of_day=True)
        if day_end is not None
        else END_OF_DAY
    )
    if normalized_end <= normalized_start:
        raise ValueError("day_end must be later than day_start")
    return axis_mode, period_count, (), normalized_start, normalized_end


def _coerce_scheme_period(value: object) -> TimetableSchemePeriod:
    if isinstance(value, TimetableSchemePeriod):
        return value
    if isinstance(value, ClassPeriod):
        return TimetableSchemePeriod(value.period_no, value.start_time, value.end_time)
    if isinstance(value, Mapping):
        try:
            return TimetableSchemePeriod(
                period_no=value["period_no"],  # type: ignore[arg-type]
                start_time=_coerce_clock(value["start_time"], "start_time"),
                end_time=_coerce_clock(value["end_time"], "end_time"),
            )
        except KeyError as error:
            raise TypeError("Period mapping is missing a required field") from error
    try:
        period_no, start_time, end_time = value  # type: ignore[misc]
    except (TypeError, ValueError) as error:
        raise TypeError("Scheme period must be a three-item value") from error
    return TimetableSchemePeriod(
        period_no=period_no,
        start_time=_coerce_clock(start_time, "start_time"),
        end_time=_coerce_clock(end_time, "end_time"),
    )


def _coerce_clock(value: object, label: str, *, allow_end_of_day: bool = False) -> time:
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        text = value.strip()
        if allow_end_of_day and text in {"24:00", "24:00:00"}:
            return END_OF_DAY
        try:
            return time.fromisoformat(text)
        except ValueError as error:
            raise ValueError(f"{label} must be HH:MM") from error
    raise TypeError(f"{label} must be a time")


def _coerce_period(value: object) -> ClassPeriod:
    if isinstance(value, ClassPeriod):
        return value
    if isinstance(value, Mapping):
        try:
            return ClassPeriod(
                period_no=value["period_no"],
                start_time=value["start_time"],
                end_time=value["end_time"],
            )
        except KeyError as error:
            raise TypeError("Period mapping is missing a required field") from error
    try:
        period_no, start_time, end_time = value  # type: ignore[misc]
    except (TypeError, ValueError) as error:
        raise TypeError("Period must be a ClassPeriod or a three-item value") from error
    return ClassPeriod(period_no=period_no, start_time=start_time, end_time=end_time)


def _teaching_week(semester: Semester, day: date) -> int | None:
    delta_days = (day - semester.start_monday).days
    if delta_days < 0 or delta_days >= semester.total_weeks * 7:
        return None
    return delta_days // 7 + 1


def _recurring_occurrence(
    course: RecurringCourse, semester_id: int, day: date
) -> CourseOccurrence:
    return CourseOccurrence(
        course_id=course.id,
        semester_id=semester_id,
        name=course.name,
        occurrence_date=day,
        start_time=course.start_time,
        end_time=course.end_time,
        classroom=course.classroom,
        source="recurring",
    )


def _one_off_occurrence(course: OneOffCourse, day: date) -> CourseOccurrence:
    return CourseOccurrence(
        course_id=course.id,
        semester_id=course.semester_id,
        name=course.name,
        occurrence_date=day,
        start_time=course.start_time,
        end_time=course.end_time,
        classroom=course.classroom,
        source="one_off",
    )


def _occurrence_sort_key(occurrence: CourseOccurrence) -> tuple[date, time, time, str, int]:
    return (
        occurrence.occurrence_date,
        occurrence.start_time,
        occurrence.end_time,
        occurrence.source,
        occurrence.course_id,
    )
