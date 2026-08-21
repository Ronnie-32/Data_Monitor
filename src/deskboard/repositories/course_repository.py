"""SQLite persistence owner for semester and course-domain records."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import date, datetime, time

from deskboard.models.course import (
    ClassPeriod,
    CourseCancellation,
    OneOffCourse,
    RecurringCourse,
    Semester,
)


class CourseRepository:
    """Persist only the five tables owned by the course domain."""

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
    ) -> Semester:
        cursor = self._connection.execute(
            """
            INSERT INTO semesters(
                name, start_monday, total_weeks, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                _date_text(start_monday),
                total_weeks,
                int(is_active),
                _datetime_text(now),
                _datetime_text(now),
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
        allowed = {"name", "start_monday", "total_weeks"}
        if not fields.keys() <= allowed:
            raise ValueError("Unsupported Semester field update")
        serialized = {key: _serialize(value) for key, value in fields.items()}
        assignments = ", ".join(f"{key} = ?" for key in serialized)
        values = [*serialized.values(), _datetime_text(now), semester_id]
        self._connection.execute(
            f"UPDATE semesters SET {assignments}, updated_at = ? WHERE id = ?", values
        )
        self._connection.commit()
        return self.require_semester(semester_id)

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
        period_rows = list(periods)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute("DELETE FROM class_periods")
            self._connection.executemany(
                "INSERT INTO class_periods(period_no, start_time, end_time) VALUES (?, ?, ?)",
                (
                    (period.period_no, _time_text(period.start_time), _time_text(period.end_time))
                    for period in period_rows
                ),
            )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise

    def save_class_periods(self, periods: Iterable[ClassPeriod]) -> None:
        self.replace_class_periods(periods)

    def list_class_periods(self) -> list[ClassPeriod]:
        rows = self._connection.execute(
            "SELECT period_no, start_time, end_time FROM class_periods ORDER BY period_no"
        )
        return [
            ClassPeriod(
                period_no=int(row[0]),
                start_time=time.fromisoformat(str(row[1])),
                end_time=time.fromisoformat(str(row[2])),
            )
            for row in rows
        ]

    def get_class_periods(self) -> list[ClassPeriod]:
        return self.list_class_periods()


_SEMESTER_COLUMNS = (
    "id, name, start_monday, total_weeks, is_active, created_at, updated_at"
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


def _time_text(value: time) -> str:
    return value.isoformat(timespec="seconds")


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
    )


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
