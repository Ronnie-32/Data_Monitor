from __future__ import annotations

import sqlite3
from datetime import date, time

from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QSizePolicy

from deskboard.database.schema import migrate
from deskboard.infrastructure.clock import SystemClock
from deskboard.repositories.course_repository import CourseRepository
from deskboard.repositories.profile_repository import ProfileRepository
from deskboard.repositories.settings_repository import SettingsRepository
from deskboard.services.course_service import CourseService
from deskboard.services.profile_service import ProfileService
from deskboard.services.settings_service import SettingsService
from deskboard.ui.settings.course_page import CoursePage
from deskboard.ui.settings.window import SettingsWindow


def _set_period_row(page: CoursePage, row: int, start: int, end: int) -> None:
    start_edit = page.scheme_period_table.cellWidget(row, 1)
    end_edit = page.scheme_period_table.cellWidget(row, 2)
    start_edit.setTime(QTime(start, 0))
    end_edit.setTime(QTime(end, 0))


def _select_list_item_by_id(widget, item_id: int) -> None:
    for row in range(widget.count()):
        if widget.item(row).data(Qt.ItemDataRole.UserRole) == item_id:
            widget.setCurrentRow(row)
            return
    raise AssertionError(f"List item {item_id} was not found")


def test_profile_theme_preview_updates_settings_without_persisting_until_save():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    settings = SettingsService(SettingsRepository(connection))
    profiles = ProfileService(
        ProfileRepository(connection), SystemClock(), SettingsRepository(connection)
    )
    previewed = []
    window = SettingsWindow(
        lambda _mode: None,
        lambda: None,
        lambda: None,
        lambda: None,
        settings_service=settings,
        profile_service=profiles,
        on_profile_preview=previewed.append,
    )

    assert window.palette().color(QPalette.ColorRole.Window).name() == "#edf2f7"
    assert window.palette().color(QPalette.ColorRole.Base).name() == "#ffffff"

    window.profile_page.theme_combo.setCurrentIndex(
        window.profile_page.theme_combo.findData("ocean_night")
    )

    assert window.palette().color(QPalette.ColorRole.Window).name() == "#152030"
    assert window.palette().color(QPalette.ColorRole.Base).name() == "#1d2b3e"
    assert "#152030" in window.styleSheet()
    assert previewed[-1].theme_key == "ocean_night"
    assert profiles.current_profile.state.theme_key == "mist_blue"

    window.close()

    assert window.palette().color(QPalette.ColorRole.Window).name() == "#edf2f7"
    assert window.palette().color(QPalette.ColorRole.Base).name() == "#ffffff"
    assert previewed[-1].theme_key == "mist_blue"
    connection.close()
    del app


def test_courses_page_lists_reusable_schemes_and_binds_the_selected_semester():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    courses = CourseService(CourseRepository(connection), SystemClock())
    scheme = courses.create_timetable_scheme(
        "Shared day", axis_mode="uniform_day", period_count=6
    )
    courses.create_semester("Spring", date(2026, 2, 23), 16)
    second = courses.create_semester("Fall", date(2026, 9, 7), 16)

    page = CoursePage(courses)
    assert page.scheme_list.count() == 2
    assert page.semester_scheme_combo.findData(scheme.id) >= 0
    _select_list_item_by_id(page.semester_list, second.id)
    page.semester_scheme_combo.setCurrentIndex(
        page.semester_scheme_combo.findData(scheme.id)
    )

    assert page.bind_selected_semester_scheme() is True
    assert courses.require_semester(second.id).timetable_scheme_id == scheme.id
    page.deleteLater()
    connection.close()
    del app


def test_custom_period_editor_has_non_overlapping_defaults_and_save_round_trip():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    courses = CourseService(CourseRepository(connection), SystemClock())
    scheme = courses.create_timetable_scheme(
        "Custom periods", axis_mode="uniform_day", period_count=4
    )

    dashboard_updates = []
    page = CoursePage(courses, on_changed=lambda: dashboard_updates.append(True))
    _select_list_item_by_id(page.scheme_list, scheme.id)
    page.scheme_axis_mode_combo.setCurrentIndex(
        page.scheme_axis_mode_combo.findData("custom_periods")
    )
    page.scheme_period_count_spin.setValue(4)

    assert page.scheme_period_table.rowCount() == 4
    assert not page.scheme_period_table.verticalHeader().isVisible()
    assert all(page.scheme_period_table.rowHeight(row) >= 44 for row in range(4))
    assert all(
        page.scheme_period_table.cellWidget(row, column).minimumWidth() >= 128
        for row in range(4)
        for column in (1, 2)
    )
    defaults = [
        (
            page.scheme_period_table.cellWidget(row, 1).time().toString("HH:mm"),
            page.scheme_period_table.cellWidget(row, 2).time().toString("HH:mm"),
        )
        for row in range(4)
    ]
    assert defaults == [
        ("08:00", "09:00"),
        ("09:00", "10:00"),
        ("10:00", "11:00"),
        ("11:00", "12:00"),
    ]

    assert page.save_scheme() is True
    assert dashboard_updates == [True]
    saved = courses.require_timetable_scheme(scheme.id)
    assert [(item.start_time, item.end_time) for item in saved.periods] == [
        (time(8), time(9)),
        (time(9), time(10)),
        (time(10), time(11)),
        (time(11), time(12)),
    ]
    page.deleteLater()
    connection.close()
    del app


def test_timetable_scheme_list_is_compact_and_leaves_room_for_editor():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    courses = CourseService(CourseRepository(connection), SystemClock())
    courses.create_timetable_scheme("方案1", axis_mode="uniform_day", period_count=8)

    page = CoursePage(courses)

    assert page.scheme_list.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Fixed
    assert page.scheme_list.maximumHeight() <= 200
    assert page.scheme_list.minimumHeight() >= 150
    page.deleteLater()
    connection.close()
    del app


def test_course_lists_are_compact_and_keep_each_item_on_one_line():
    app = QApplication.instance() or QApplication([])
    page = CoursePage(None)

    assert page.status_label.wordWrap() is False
    for course_list in (
        page.semester_list,
        page.recurring_list,
        page.one_off_list,
        page.scheme_list,
    ):
        assert course_list.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Fixed
        assert 170 <= course_list.minimumHeight() <= 220
        assert course_list.maximumHeight() == course_list.minimumHeight()
        assert course_list.wordWrap() is False
        assert course_list.textElideMode() == Qt.TextElideMode.ElideRight
        assert (
            course_list.horizontalScrollBarPolicy()
            == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

    page.deleteLater()
    del app


def test_new_default_scheme_uses_default_name_and_can_be_saved():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    courses = CourseService(CourseRepository(connection), SystemClock())
    page = CoursePage(courses)

    assert page.create_scheme() is True
    created = courses.list_timetable_schemes()[-1]
    assert created.name == "UIBE"

    page.scheme_name_edit.setText("UIBE")
    assert page.save_scheme() is True
    assert courses.require_timetable_scheme(created.id).name == "UIBE"
    page.deleteLater()
    connection.close()
    del app


def test_semester_selection_refreshes_scheme_binding_editor():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    courses = CourseService(CourseRepository(connection), SystemClock())
    first_scheme = courses.create_timetable_scheme("First", axis_mode="uniform_day")
    second_scheme = courses.create_timetable_scheme("Second", axis_mode="uniform_day")
    first = courses.create_semester("Spring", date(2026, 2, 23), 16, active=True)
    second = courses.create_semester("Fall", date(2026, 9, 7), 16)
    courses.bind_semester_timetable_scheme(first.id, first_scheme.id)
    courses.bind_semester_timetable_scheme(second.id, second_scheme.id)

    page = CoursePage(courses)
    _select_list_item_by_id(page.semester_list, second.id)
    assert page.semester_scheme_combo.currentData() == second_scheme.id
    assert page.scheme_list.currentItem().data(Qt.ItemDataRole.UserRole) == second_scheme.id
    assert page.scheme_name_edit.text() == "Second"

    _select_list_item_by_id(page.semester_list, first.id)
    assert page.semester_scheme_combo.currentData() == first_scheme.id
    assert page.scheme_name_edit.text() == "First"
    page.deleteLater()
    connection.close()
    del app


def test_invalid_scheme_save_reports_validation_near_editor():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    courses = CourseService(CourseRepository(connection), SystemClock())
    courses.create_timetable_scheme("Custom periods", axis_mode="uniform_day", period_count=2)

    page = CoursePage(courses)
    page.scheme_axis_mode_combo.setCurrentIndex(
        page.scheme_axis_mode_combo.findData("custom_periods")
    )
    page.scheme_period_count_spin.setValue(2)
    _set_period_row(page, 0, 8, 9)
    _set_period_row(page, 1, 8, 9)

    assert page.save_scheme() is False
    assert "overlap" in page.scheme_status_label.text().lower()
    page.deleteLater()
    connection.close()
    del app
