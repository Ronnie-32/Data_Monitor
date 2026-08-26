from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from deskboard.database.schema import migrate
from deskboard.infrastructure.clock import Clock
from deskboard.models.course import ClassPeriod
from deskboard.repositories.course_repository import CourseRepository
from deskboard.repositories.network_repository import NetworkRepository
from deskboard.repositories.settings_repository import SettingsRepository
from deskboard.services.course_service import CourseService
from deskboard.services.refresh_service import DataRefreshService
from deskboard.services.settings_service import SettingsService
from deskboard.ui.settings.window import SettingsWindow


@dataclass
class FakeClock(Clock):
    current: datetime = datetime(2026, 8, 25, 10, 30)

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


def test_task25_mounts_native_course_data_status_and_about_pages():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    clock = FakeClock()
    settings = SettingsService(SettingsRepository(connection))
    course = CourseService(CourseRepository(connection), clock)
    refresh = DataRefreshService(NetworkRepository(connection), clock, providers=(), items=())

    window = SettingsWindow(
        lambda _mode: None,
        lambda: None,
        lambda: None,
        lambda: None,
        clock=clock,
        settings_service=settings,
        course_service=course,
        refresh_service=refresh,
        log_directory=Path(".") / "logs",
    )

    assert window.pages.widget(5).widget() is window.course_page
    assert window.pages.widget(6).widget() is window.data_status_page
    assert window.pages.widget(7).widget() is window.about_page
    assert window.course_page.add_semester("秋季学期", date(2026, 9, 7), 16)
    semester = course.list_semesters()[0]
    assert window.course_page.set_active_semester(semester.id)
    assert window.course_page.add_recurring_course(
        {
            "semester_id": semester.id,
            "name": "统计学",
            "weekday": 1,
            "start_time": time(8),
            "end_time": time(9),
            "start_week": 1,
            "end_week": 16,
            "classroom": "A101",
        }
    )
    assert window.course_page.save_periods(
        [ClassPeriod(index, time(8 + index), time(9 + index)) for index in range(1, 9)]
    )
    assert window.course_page.set_header_mode("date-only")
    assert settings.timetable_header_mode == "date"
    assert window.data_status_page.table.rowCount() == 0

    window.close()
    connection.close()
    del app
