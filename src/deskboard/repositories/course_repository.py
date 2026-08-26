"""SQLite persistence owner for semester and course-domain records."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import date, datetime, time

from deskboard.models.course import (
    END_OF_DAY,
    ClassPeriod,
    CourseCancellation,
    OneOffCourse,
    RecurringCourse,
    Semester,
    TimetableScheme,
    TimetableSchemeAxisMode,
    TimetableSchemePeriod,
)


class CourseRepository:
    """Persist only the semester, timetable-scheme, and course-domain tables."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create_semester(
        self,
        *,
        name: str,
        start_monday: date,
        total_weeks: int,
        now: datetime,
        is_active: bool = False,
        timetable_scheme_id: int | None = None,
    ) -> Semester:
        if timetable_scheme_id is not None:
            self.require_timetable_scheme(timetable_scheme_id)
        cursor = self._connection.execute(
            """
            INSERT INTO semesters(
                name, start_monday, total_weeks, is_active, created_at, updated_at,
                timetable_scheme_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                _date_text(start_monday),
                total_weeks,
                int(is_active),
                _datetime_text(now),
                _datetime_text(now),
                timetable_scheme_id,
            ),
        )
        self._connection.commit()
        return self.require_semester(int(cursor.lastrowid))

    def get_semester(self, semester_id: int) -> Semester | None:
        row = self._connection.execute(
            f"SELECT {_SEMESTER_COLUMNS} FROM semesters WHERE id = ?", (semester_id,)
        ).fetchone()
        return None if row is None else _semester_from_row(row)

    def require_semester(self, semester_id: int) -> Semester:
        semester = self.get_semester(semester_id)
        if semester is None:
            raise LookupError(f"Semester {semester_id} does not exist")
        return semester

    def list_semesters(self) -> list[Semester]:
        rows = self._connection.execute(
            f"SELECT {_SEMESTER_COLUMNS} FROM semesters ORDER BY start_monday, id"
        )
        return [_semester_from_row(row) for row in rows]

    def get_active_semester(self) -> Semester | None:
        row = self._connection.execute(
            f"SELECT {_SEMESTER_COLUMNS} FROM semesters WHERE is_active = 1"
        ).fetchone()
        return None if row is None else _semester_from_row(row)

    def set_active_semester(
        self, semester_id: int | None, now: datetime
    ) -> Semester | None:
        if semester_id is not None:
            self.require_semester(semester_id)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute(
                "UPDATE semesters SET is_active = 0, updated_at = ? WHERE is_active = 1",
                (_datetime_text(now),),
            )
            if semester_id is not None:
                self._connection.execute(
                    "UPDATE semesters SET is_active = 1, updated_at = ? WHERE id = ?",
                    (_datetime_text(now), semester_id),
                )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.get_active_semester()

    def update_semester(
        self, semester_id: int, fields: dict[str, object], now: datetime
    ) -> Semester:
        self.require_semester(semester_id)
        if not fields:
            return self.require_semester(semester_id)
        allowed = {"name", "start_monday", "total_weeks", "timetable_scheme_id"}
        if not fields.keys() <= allowed:
            raise ValueError("Unsupported Semester field update")
        if fields.get("timetable_scheme_id") is not None:
            self.require_timetable_scheme(int(fields["timetable_scheme_id"]))
        serialized = {key: _serialize(value) for key, value in fields.items()}
        assignments = ", ".join(f"{key} = ?" for key in serialized)
        values = [*serialized.values(), _datetime_text(now), semester_id]
        self._connection.execute(
            f"UPDATE semesters SET {assignments}, updated_at = ? WHERE id = ?", values
        )
        self._connection.commit()
        return self.require_semester(semester_id)

    # Timetable schemes and semester bindings.
    def create_timetable_scheme(
        self,
        *,
        name: str,
        axis_mode: TimetableSchemeAxisMode,
        period_count: int,
        day_start: time | None,
        day_end: time | None,
        periods: Iterable[TimetableSchemePeriod],
        now: datetime,
        is_builtin: bool = False,
    ) -> TimetableScheme:
        period_rows = tuple(periods)
        _require_scheme_row_shape(axis_mode, period_count, period_rows)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            cursor = self._connection.execute(
                """
                INSERT INTO timetable_schemes(
                    name, axis_mode, period_count, day_start, day_end,
                    is_builtin, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    axis_mode,
                    period_count,
                    _time_text(day_start),
                    _time_text(day_end),
                    int(is_builtin),
                    _datetime_text(now),
                    _datetime_text(now),
                ),
            )
            scheme_id = int(cursor.lastrowid)
            self._insert_scheme_periods(scheme_id, period_rows)
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.require_timetable_scheme(scheme_id)

    def get_timetable_scheme(self, scheme_id: int) -> TimetableScheme | None:
        row = self._connection.execute(
            f"SELECT {_SCHEME_COLUMNS} FROM timetable_schemes WHERE id = ?",
            (scheme_id,),
        ).fetchone()
        return None if row is None else self._scheme_from_row(row)

    def require_timetable_scheme(self, scheme_id: int) -> TimetableScheme:
        scheme = self.get_timetable_scheme(scheme_id)
        if scheme is None:
            raise LookupError(f"Timetable scheme {scheme_id} does not exist")
        return scheme

    def list_timetable_schemes(self) -> list[TimetableScheme]:
        rows = self._connection.execute(
            f"SELECT {_SCHEME_COLUMNS} FROM timetable_schemes ORDER BY name, id"
        )
        return [self._scheme_from_row(row) for row in rows]

    def replace_timetable_scheme(
        self,
        scheme_id: int,
        *,
        name: str,
        axis_mode: TimetableSchemeAxisMode,
        period_count: int,
        day_start: time | None,
        day_end: time | None,
        periods: Iterable[TimetableSchemePeriod],
        now: datetime,
    ) -> TimetableScheme:
        self.require_timetable_scheme(scheme_id)
        period_rows = tuple(periods)
        _require_scheme_row_shape(axis_mode, period_count, period_rows)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute(
                """
                UPDATE timetable_schemes
                SET name = ?, axis_mode = ?, period_count = ?, day_start = ?, day_end = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    name,
                    axis_mode,
                    period_count,
                    _time_text(day_start),
                    _time_text(day_end),
                    _datetime_text(now),
                    scheme_id,
                ),
            )
            self._connection.execute(
                "DELETE FROM timetable_scheme_periods WHERE scheme_id = ?", (scheme_id,)
            )
            self._insert_scheme_periods(scheme_id, period_rows)
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        return self.require_timetable_scheme(scheme_id)

    def rename_timetable_scheme(self, scheme_id: int, name: str, now: datetime) -> TimetableScheme:
        self.require_timetable_scheme(scheme_id)
        self._connection.execute(
            "UPDATE timetable_schemes SET name = ?, updated_at = ? WHERE id = ?",
            (name, _datetime_text(now), scheme_id),
        )
        self._connection.commit()
        return self.require_timetable_scheme(scheme_id)

    def duplicate_timetable_scheme(
        self, scheme_id: int, *, name: str, now: datetime
    ) -> TimetableScheme:
        source = self.require_timetable_scheme(scheme_id)
        return self.create_timetable_scheme(
            name=name,
            axis_mode=source.axis_mode,
            period_count=source.period_count,
            day_start=source.day_start,
            day_end=source.day_end,
            periods=source.periods,
            now=now,
            is_builtin=False,
        )

    def delete_timetable_scheme(self, scheme_id: int) -> None:
        cursor = self._connection.execute(
            "DELETE FROM timetable_schemes WHERE id = ?", (scheme_id,)
        )
        if cursor.rowcount != 1:
            self._connection.rollback()
            raise LookupError(f"Timetable scheme {scheme_id} does not exist")
        self._connection.commit()

    def bind_semester_timetable_scheme(
        self, semester_id: int, scheme_id: int | None, now: datetime
    ) -> Semester:
        self.require_semester(semester_id)
        if scheme_id is not None:
            self.require_timetable_scheme(scheme_id)
        self._connection.execute(
            """
            UPDATE semesters SET timetable_scheme_id = ?, updated_at = ? WHERE id = ?
            """,
            (scheme_id, _datetime_text(now), semester_id),
        )
        self._connection.commit()
        return self.require_semester(semester_id)

    def get_timetable_scheme_for_semester(self, semester_id: int) -> TimetableScheme | None:
        semester = self.require_semester(semester_id)
        return (
            None
            if semester.timetable_scheme_id is None
            else self.get_timetable_scheme(semester.timetable_scheme_id)
        )

    def get_active_timetable_scheme(self) -> TimetableScheme | None:
        semester = self.get_active_semester()
        return None if semester is None else self.get_timetable_scheme_for_semester(semester.id)

    def _insert_scheme_periods(
        self, scheme_id: int, periods: Iterable[TimetableSchemePeriod]
    ) -> None:
        self._connection.executemany(
            """
            INSERT INTO timetable_scheme_periods(scheme_id, period_no, start_time, end_time)
            VALUES (?, ?, ?, ?)
            """,
            (
                (
                    scheme_id,
                    period.period_no,
                    _time_text(period.start_time),
                    _time_text(period.end_time),
                )
                for period in periods
            ),
        )

    def _scheme_from_row(self, row: sqlite3.Row | tuple[object, ...]) -> TimetableScheme:
        period_rows = self._connection.execute(
            """
            SELECT period_no, start_time, end_time
            FROM timetable_scheme_periods
            WHERE scheme_id = ? ORDER BY period_no
            """,
            (int(row[0]),),
        )
        periods = tuple(
            TimetableSchemePeriod(
                period_no=int(period[0]),
                start_time=_time_from_text(period[1]),
                end_time=_time_from_text(period[2]),
            )
            for period in period_rows
        )
        return TimetableScheme(
            id=int(row[0]),
            name=str(row[1]),
            axis_mode=str(row[2]),  # type: ignore[arg-type]
            period_count=int(row[3]),
            day_start=_time_from_text(row[4]),
            day_end=_time_from_text(row[5]),
            is_builtin=bool(row[6]),
            periods=periods,
            created_at=datetime.fromisoformat(str(row[7])),
            updated_at=datetime.fromisoformat(str(row[8])),
        )

    def delete_semester(self, semester_id: int) -> None:
        cursor = self._connection.execute(
            "DELETE FROM semesters WHERE id = ?", (semester_id,)
        )
        if cursor.rowcount != 1:
            self._connection.rollback()
            raise LookupError(f"Semester {semester_id} does not exist")
        self._connection.commit()

    def create_recurring_course(
        self,
        *,
        semester_id: int,
        name: str,
        weekday: int,
        start_time: time,
        end_time: time,
        start_week: int,
        end_week: int,
        now: datetime,
        classroom: str | None = None,
    ) -> RecurringCourse:
        cursor = self._connection.execute(
            """
            INSERT INTO recurring_courses(
                semester_id, name, weekday, start_time, end_time, start_week, end_week,
                classroom, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                semester_id,
                name,
                weekday,
                _time_text(start_time),
                _time_text(end_time),
                start_week,
                end_week,
                classroom,
                _datetime_text(now),
                _datetime_text(now),
            ),
        )
        self._connection.commit()
        return self.require_recurring_course(int(cursor.lastrowid))

    def get_recurring_course(self, course_id: int) -> RecurringCourse | None:
        row = self._connection.execute(
            f"SELECT {_RECURRING_COLUMNS} FROM recurring_courses WHERE id = ?",
            (course_id,),
        ).fetchone()
        return None if row is None else _recurring_from_row(row)

    def require_recurring_course(self, course_id: int) -> RecurringCourse:
        course = self.get_recurring_course(course_id)
        if course is None:
            raise LookupError(f"Recurring course {course_id} does not exist")
        return course

    def list_recurring_courses(self, semester_id: int | None = None) -> list[RecurringCourse]:
        if semester_id is None:
            rows = self._connection.execute(
                f"SELECT {_RECURRING_COLUMNS} FROM recurring_courses "
                "ORDER BY semester_id, weekday, start_time, id"
            )
        else:
            rows = self._connection.execute(
                f"SELECT {_RECURRING_COLUMNS} FROM recurring_courses "
                "WHERE semester_id = ? ORDER BY weekday, start_time, id",
                (semester_id,),
            )
        return [_recurring_from_row(row) for row in rows]

    def update_recurring_course(
        self, course_id: int, fields: dict[str, object], now: datetime
    ) -> RecurringCourse:
        self.require_recurring_course(course_id)
        if not fields:
            return self.require_recurring_course(course_id)
        allowed = {
            "semester_id",
            "name",
            "weekday",
            "start_time",
            "end_time",
            "start_week",
            "end_week",
            "classroom",
        }
        if not fields.keys() <= allowed:
            raise ValueError("Unsupported recurring course field update")
        serialized = {key: _serialize(value) for key, value in fields.items()}
        assignments = ", ".join(f"{key} = ?" for key in serialized)
        values = [*serialized.values(), _datetime_text(now), course_id]
        self._connection.execute(
            f"UPDATE recurring_courses SET {assignments}, updated_at = ? WHERE id = ?",
            values,
        )
        self._connection.commit()
        return self.require_recurring_course(course_id)

    def delete_recurring_course(self, course_id: int) -> None:
        cursor = self._connection.execute(
            "DELETE FROM recurring_courses WHERE id = ?", (course_id,)
        )
        if cursor.rowcount != 1:
            self._connection.rollback()
            raise LookupError(f"Recurring course {course_id} does not exist")
        self._connection.commit()

    def add_cancellation(
        self, recurring_course_id: int, occurrence_date: date
    ) -> CourseCancellation:
        self._connection.execute(
            """
            INSERT OR IGNORE INTO course_cancellations(
                recurring_course_id, occurrence_date
            ) VALUES (?, ?)
            """,
            (recurring_course_id, _date_text(occurrence_date)),
        )
        self._connection.commit()
        return self.require_cancellation(recurring_course_id, occurrence_date)

    def get_cancellation(
        self, recurring_course_id: int, occurrence_date: date
    ) -> CourseCancellation | None:
        row = self._connection.execute(
            """
            SELECT recurring_course_id, occurrence_date
            FROM course_cancellations
            WHERE recurring_course_id = ? AND occurrence_date = ?
            """,
            (recurring_course_id, _date_text(occurrence_date)),
        ).fetchone()
        return None if row is None else _cancellation_from_row(row)

    def require_cancellation(
        self, recurring_course_id: int, occurrence_date: date
    ) -> CourseCancellation:
        cancellation = self.get_cancellation(recurring_course_id, occurrence_date)
        if cancellation is None:
            raise LookupError("Course cancellation does not exist")
        return cancellation

    def list_cancellations(
        self, recurring_course_id: int | None = None
    ) -> list[CourseCancellation]:
        if recurring_course_id is None:
            rows = self._connection.execute(
                """
                SELECT recurring_course_id, occurrence_date
                FROM course_cancellations
                ORDER BY occurrence_date, recurring_course_id
                """
            )
        else:
            rows = self._connection.execute(
                """
                SELECT recurring_course_id, occurrence_date
                FROM course_cancellations
                WHERE recurring_course_id = ?
                ORDER BY occurrence_date
                """,
                (recurring_course_id,),
            )
        return [_cancellation_from_row(row) for row in rows]

    def is_cancelled(self, recurring_course_id: int, occurrence_date: date) -> bool:
        return self.get_cancellation(recurring_course_id, occurrence_date) is not None

    def remove_cancellation(self, recurring_course_id: int, occurrence_date: date) -> bool:
        cursor = self._connection.execute(
            """
            DELETE FROM course_cancellations
            WHERE recurring_course_id = ? AND occurrence_date = ?
            """,
            (recurring_course_id, _date_text(occurrence_date)),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def create_one_off_course(
        self,
        *,
        semester_id: int,
        name: str,
        course_date: date,
        start_time: time,
        end_time: time,
        now: datetime,
        classroom: str | None = None,
    ) -> OneOffCourse:
        cursor = self._connection.execute(
            """
            INSERT INTO one_off_courses(
                semester_id, name, course_date, start_time, end_time, classroom,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                semester_id,
                name,
                _date_text(course_date),
                _time_text(start_time),
                _time_text(end_time),
                classroom,
                _datetime_text(now),
                _datetime_text(now),
            ),
        )
        self._connection.commit()
        return self.require_one_off_course(int(cursor.lastrowid))

    def get_one_off_course(self, course_id: int) -> OneOffCourse | None:
        row = self._connection.execute(
            f"SELECT {_ONE_OFF_COLUMNS} FROM one_off_courses WHERE id = ?", (course_id,)
        ).fetchone()
        return None if row is None else _one_off_from_row(row)

    def require_one_off_course(self, course_id: int) -> OneOffCourse:
        course = self.get_one_off_course(course_id)
        if course is None:
            raise LookupError(f"One-off course {course_id} does not exist")
        return course

    def list_one_off_courses(self, semester_id: int | None = None) -> list[OneOffCourse]:
        if semester_id is None:
            rows = self._connection.execute(
                f"SELECT {_ONE_OFF_COLUMNS} FROM one_off_courses "
                "ORDER BY semester_id, course_date, start_time, id"
            )
        else:
            rows = self._connection.execute(
                f"SELECT {_ONE_OFF_COLUMNS} FROM one_off_courses "
                "WHERE semester_id = ? ORDER BY course_date, start_time, id",
                (semester_id,),
            )
        return [_one_off_from_row(row) for row in rows]

    def update_one_off_course(
        self, course_id: int, fields: dict[str, object], now: datetime
    ) -> OneOffCourse:
        self.require_one_off_course(course_id)
        if not fields:
            return self.require_one_off_course(course_id)
        allowed = {
            "semester_id",
            "name",
            "course_date",
            "start_time",
            "end_time",
            "classroom",
        }
        if not fields.keys() <= allowed:
            raise ValueError("Unsupported one-off course field update")
        serialized = {key: _serialize(value) for key, value in fields.items()}
        assignments = ", ".join(f"{key} = ?" for key in serialized)
        values = [*serialized.values(), _datetime_text(now), course_id]
        self._connection.execute(
            f"UPDATE one_off_courses SET {assignments}, updated_at = ? WHERE id = ?",
            values,
        )
        self._connection.commit()
        return self.require_one_off_course(course_id)

    def delete_one_off_course(self, course_id: int) -> None:
        cursor = self._connection.execute(
            "DELETE FROM one_off_courses WHERE id = ?", (course_id,)
        )
        if cursor.rowcount != 1:
            self._connection.rollback()
            raise LookupError(f"One-off course {course_id} does not exist")
        self._connection.commit()

    def replace_class_periods(self, periods: Iterable[ClassPeriod]) -> None:
        # Compatibility for the pre-Task-31 public service surface.  New
        # writes still go through the scheme tables; no legacy table is used.
        period_rows = tuple(
            TimetableSchemePeriod(item.period_no, item.start_time, item.end_time)
            for item in periods
        )
        existing = next(
            (
                scheme
                for scheme in self.list_timetable_schemes()
                if scheme.is_builtin and scheme.axis_mode == "custom_periods"
            ),
            None,
        )
        if existing is None:
            self.create_timetable_scheme(
                name="方案1",
                axis_mode="custom_periods",
                period_count=len(period_rows),
                day_start=None,
                day_end=None,
                periods=period_rows,
                now=datetime.now(),
                is_builtin=True,
            )
        else:
            self.replace_timetable_scheme(
                existing.id,
                name=existing.name,
                axis_mode="custom_periods",
                period_count=len(period_rows),
                day_start=None,
                day_end=None,
                periods=period_rows,
                now=datetime.now(),
            )

    def save_class_periods(self, periods: Iterable[ClassPeriod]) -> None:
        self.replace_class_periods(periods)

    def list_class_periods(self) -> list[ClassPeriod]:
        scheme = self.get_active_timetable_scheme()
        if scheme is None:
            scheme = next(
                (
                    item
                    for item in self.list_timetable_schemes()
                    if item.axis_mode == "custom_periods"
                ),
                None,
            )
        if scheme is None or scheme.axis_mode != "custom_periods":
            return []
        return [
            ClassPeriod(period.period_no, period.start_time, period.end_time)
            for period in scheme.periods
        ]

    def get_class_periods(self) -> list[ClassPeriod]:
        return self.list_class_periods()


_SEMESTER_COLUMNS = (
    "id, name, start_monday, total_weeks, is_active, created_at, updated_at, "
    "timetable_scheme_id"
)
_SCHEME_COLUMNS = (
    "id, name, axis_mode, period_count, day_start, day_end, is_builtin, "
    "created_at, updated_at"
)
_RECURRING_COLUMNS = (
    "id, semester_id, name, weekday, start_time, end_time, start_week, end_week, "
    "classroom, created_at, updated_at"
)
_ONE_OFF_COLUMNS = (
    "id, semester_id, name, course_date, start_time, end_time, classroom, "
    "created_at, updated_at"
)


def _date_text(value: date) -> str:
    return value.isoformat()


def _time_text(value: time | None) -> str | None:
    if value is None:
        return None
    if value == END_OF_DAY:
        return "24:00"
    return value.isoformat(timespec="seconds")


def _time_from_text(value: object) -> time | None:
    if value is None:
        return None
    text = str(value)
    if text in {"24:00", "24:00:00"}:
        return END_OF_DAY
    return time.fromisoformat(text)


def _datetime_text(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _serialize(value: object) -> object:
    if isinstance(value, datetime):
        return _datetime_text(value)
    if isinstance(value, date):
        return _date_text(value)
    if isinstance(value, time):
        return _time_text(value)
    return value


def _semester_from_row(row: sqlite3.Row | tuple[object, ...]) -> Semester:
    return Semester(
        id=int(row[0]),
        name=str(row[1]),
        start_monday=date.fromisoformat(str(row[2])),
        total_weeks=int(row[3]),
        is_active=bool(row[4]),
        created_at=datetime.fromisoformat(str(row[5])),
        updated_at=datetime.fromisoformat(str(row[6])),
        timetable_scheme_id=None if row[7] is None else int(row[7]),
    )


def _require_scheme_row_shape(
    axis_mode: TimetableSchemeAxisMode,
    period_count: int,
    periods: tuple[TimetableSchemePeriod, ...],
) -> None:
    if axis_mode not in ("custom_periods", "uniform_day"):
        raise sqlite3.IntegrityError("unsupported timetable scheme axis mode")
    if isinstance(period_count, bool) or not isinstance(period_count, int):
        raise sqlite3.IntegrityError("period_count must be an integer")
    if not 1 <= period_count <= 24:
        raise sqlite3.IntegrityError("period_count must be between 1 and 24")
    if axis_mode == "custom_periods" and len(periods) != period_count:
        raise sqlite3.IntegrityError(
            "custom_periods requires exactly one row per configured period"
        )
    if axis_mode == "custom_periods":
        if [period.period_no for period in periods] != list(range(1, period_count + 1)):
            raise sqlite3.IntegrityError("custom periods must be numbered 1 through period_count")
        previous_end: time | None = None
        for period in periods:
            if period.end_time <= period.start_time:
                raise sqlite3.IntegrityError("custom period end must be later than start")
            if previous_end is not None and period.start_time < previous_end:
                raise sqlite3.IntegrityError("custom periods must not overlap")
            previous_end = period.end_time
    if axis_mode == "uniform_day" and periods:
        raise sqlite3.IntegrityError("uniform_day cannot store period rows")


def _recurring_from_row(row: sqlite3.Row | tuple[object, ...]) -> RecurringCourse:
    return RecurringCourse(
        id=int(row[0]),
        semester_id=int(row[1]),
        name=str(row[2]),
        weekday=int(row[3]),
        start_time=time.fromisoformat(str(row[4])),
        end_time=time.fromisoformat(str(row[5])),
        start_week=int(row[6]),
        end_week=int(row[7]),
        classroom=None if row[8] is None else str(row[8]),
        created_at=datetime.fromisoformat(str(row[9])),
        updated_at=datetime.fromisoformat(str(row[10])),
    )


def _cancellation_from_row(row: sqlite3.Row | tuple[object, ...]) -> CourseCancellation:
    return CourseCancellation(
        recurring_course_id=int(row[0]),
        occurrence_date=date.fromisoformat(str(row[1])),
    )


def _one_off_from_row(row: sqlite3.Row | tuple[object, ...]) -> OneOffCourse:
    return OneOffCourse(
        id=int(row[0]),
        semester_id=int(row[1]),
        name=str(row[2]),
        course_date=date.fromisoformat(str(row[3])),
        start_time=time.fromisoformat(str(row[4])),
        end_time=time.fromisoformat(str(row[5])),
        classroom=None if row[6] is None else str(row[6]),
        created_at=datetime.fromisoformat(str(row[7])),
        updated_at=datetime.fromisoformat(str(row[8])),
    )
