"""Native Settings UI for semesters, courses, cancellations, and timetable options."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping, Sequence
from datetime import date, time, timedelta
from typing import Any

from PySide6.QtCore import QDate, QSignalBlocker, Qt, QTime
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from deskboard.infrastructure.clock import Clock, SystemClock
from deskboard.models.course import (
    DEFAULT_TIMETABLE_SCHEME_NAME,
    END_OF_DAY,
    ClassPeriod,
    OneOffCourse,
    RecurringCourse,
    Semester,
    TimetableScheme,
    TimetableSchemePeriod,
)
from deskboard.services.settings_service import (
    DEFAULT_TIMETABLE_HEADER_MODE,
    normalize_timetable_header_mode,
)
from deskboard.ui.settings.i18n import (
    SUPPORTED_LANGUAGES,
    translate_text,
    translate_widget_tree,
)

WEEKDAY_NAMES = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
COURSE_LIST_HEIGHT = 196
HEADER_MODES = (
    ("Weekday only", "weekday"),
    ("Weekday + date", "weekday_date"),
    ("Date only", "date"),
)


class _SaveCancelDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, *, language: str = "zh_CN") -> None:
        super().__init__(parent)
        self._language = language if language in SUPPORTED_LANGUAGES else "zh_CN"

    def _button_box(self) -> QDialogButtonBox:
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        save = buttons.button(QDialogButtonBox.StandardButton.Save)
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if save is not None:
            save.setText(translate_text("Save", self._language))
        if cancel is not None:
            cancel.setText(translate_text("Cancel", self._language))
        buttons.accepted.connect(self._accept_values)
        buttons.rejected.connect(self.reject)
        return buttons

    def _accept_values(self) -> None:
        self.accept()


class SemesterEditorDialog(_SaveCancelDialog):
    def __init__(
        self,
        *,
        today: date,
        semester: Semester | None = None,
        language: str = "zh_CN",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent, language=language)
        self.setWindowTitle(translate_text("Edit Semester", self._language))
        self.setModal(True)
        self.resize(420, 220)
        initial_monday = semester.start_monday if semester else _monday(today)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(semester.name if semester else "", self)
        self.name_edit.setMaxLength(120)
        form.addRow("Name", self.name_edit)
        self.start_date_edit = QDateEdit(_to_qdate(initial_monday), self)
        self.start_date_edit.setCalendarPopup(True)
        form.addRow("Start Monday", self.start_date_edit)
        self.total_weeks_spin = QSpinBox(self)
        self.total_weeks_spin.setRange(1, 99)
        self.total_weeks_spin.setValue(semester.total_weeks if semester else 16)
        form.addRow("Total weeks", self.total_weeks_spin)
        layout.addLayout(form)
        self.error_label = QLabel(self)
        self.error_label.setStyleSheet("color: #b43f49;")
        layout.addWidget(self.error_label)
        layout.addWidget(self._button_box())
        translate_widget_tree(self, self._language)

    def values(self) -> dict[str, object]:
        return {
            "name": self.name_edit.text().strip(),
            "start_monday": _from_qdate(self.start_date_edit.date()),
            "total_weeks": self.total_weeks_spin.value(),
        }

    def _accept_values(self) -> None:
        values = self.values()
        if not values["name"]:
            self.error_label.setText(
                translate_text("Semester name must not be empty", self._language)
            )
            return
        if values["start_monday"].weekday() != 0:  # type: ignore[union-attr]
            self.error_label.setText(
                translate_text("Start date must be a Monday", self._language)
            )
            return
        self.accept()


class RecurringCourseEditorDialog(_SaveCancelDialog):
    def __init__(
        self,
        *,
        semesters: Sequence[Semester],
        course: RecurringCourse | None = None,
        language: str = "zh_CN",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent, language=language)
        self.setWindowTitle(translate_text("Edit Recurring Course", self._language))
        self.setModal(True)
        self.resize(460, 360)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.semester_combo = QComboBox(self)
        for semester in semesters:
            self.semester_combo.addItem(semester.name, semester.id)
        if course is not None:
            _select_data(self.semester_combo, course.semester_id)
        form.addRow("Semester", self.semester_combo)
        self.name_edit = QLineEdit(course.name if course else "", self)
        form.addRow("Course name", self.name_edit)
        self.weekday_combo = QComboBox(self)
        for number, label in enumerate(WEEKDAY_NAMES, start=1):
            self.weekday_combo.addItem(label, number)
        _select_data(self.weekday_combo, course.weekday if course else 1)
        form.addRow("Weekday", self.weekday_combo)
        self.start_time_edit = _time_edit(course.start_time if course else time(8))
        self.end_time_edit = _time_edit(course.end_time if course else time(9))
        form.addRow("Start time", self.start_time_edit)
        form.addRow("End time", self.end_time_edit)
        self.start_week_spin = QSpinBox(self)
        self.start_week_spin.setRange(1, 99)
        self.start_week_spin.setValue(course.start_week if course else 1)
        self.end_week_spin = QSpinBox(self)
        self.end_week_spin.setRange(1, 99)
        self.end_week_spin.setValue(course.end_week if course else 16)
        form.addRow("Start week", self.start_week_spin)
        form.addRow("End week", self.end_week_spin)
        self.classroom_edit = QLineEdit(course.classroom or "" if course else "", self)
        form.addRow("Classroom", self.classroom_edit)
        layout.addLayout(form)
        self.error_label = QLabel(self)
        self.error_label.setStyleSheet("color: #b43f49;")
        layout.addWidget(self.error_label)
        layout.addWidget(self._button_box())
        translate_widget_tree(self, self._language)

    def values(self) -> dict[str, object]:
        return {
            "semester_id": int(self.semester_combo.currentData()),
            "name": self.name_edit.text().strip(),
            "weekday": int(self.weekday_combo.currentData()),
            "start_time": _from_qtime(self.start_time_edit.time()),
            "end_time": _from_qtime(self.end_time_edit.time()),
            "start_week": self.start_week_spin.value(),
            "end_week": self.end_week_spin.value(),
            "classroom": self.classroom_edit.text().strip() or None,
        }

    def _accept_values(self) -> None:
        values = self.values()
        if not values["name"]:
            self.error_label.setText(
                translate_text("Course name must not be empty", self._language)
            )
            return
        if values["end_time"] <= values["start_time"]:  # type: ignore[operator]
            self.error_label.setText(
                translate_text(
                    "End time must be later than start time", self._language
                )
            )
            return
        if values["end_week"] < values["start_week"]:  # type: ignore[operator]
            self.error_label.setText(
                translate_text(
                    "End week must not be before start week", self._language
                )
            )
            return
        self.accept()


class OneOffCourseEditorDialog(_SaveCancelDialog):
    def __init__(
        self,
        *,
        semesters: Sequence[Semester],
        today: date,
        course: OneOffCourse | None = None,
        language: str = "zh_CN",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent, language=language)
        self.setWindowTitle(translate_text("Edit One-off Course", self._language))
        self.setModal(True)
        self.resize(460, 320)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.semester_combo = QComboBox(self)
        for semester in semesters:
            self.semester_combo.addItem(semester.name, semester.id)
        if course is not None:
            _select_data(self.semester_combo, course.semester_id)
        form.addRow("Semester", self.semester_combo)
        self.name_edit = QLineEdit(course.name if course else "", self)
        form.addRow("Course name", self.name_edit)
        self.date_edit = QDateEdit(
            _to_qdate(course.course_date if course else today),
            self,
        )
        self.date_edit.setCalendarPopup(True)
        form.addRow("Course date", self.date_edit)
        self.start_time_edit = _time_edit(course.start_time if course else time(8))
        self.end_time_edit = _time_edit(course.end_time if course else time(9))
        form.addRow("Start time", self.start_time_edit)
        form.addRow("End time", self.end_time_edit)
        self.classroom_edit = QLineEdit(course.classroom or "" if course else "", self)
        form.addRow("Classroom", self.classroom_edit)
        layout.addLayout(form)
        self.error_label = QLabel(self)
        self.error_label.setStyleSheet("color: #b43f49;")
        layout.addWidget(self.error_label)
        layout.addWidget(self._button_box())
        translate_widget_tree(self, self._language)

    def values(self) -> dict[str, object]:
        return {
            "semester_id": int(self.semester_combo.currentData()),
            "name": self.name_edit.text().strip(),
            "course_date": _from_qdate(self.date_edit.date()),
            "start_time": _from_qtime(self.start_time_edit.time()),
            "end_time": _from_qtime(self.end_time_edit.time()),
            "classroom": self.classroom_edit.text().strip() or None,
        }

    def _accept_values(self) -> None:
        values = self.values()
        if not values["name"]:
            self.error_label.setText(
                translate_text("Course name must not be empty", self._language)
            )
            return
        if values["end_time"] <= values["start_time"]:  # type: ignore[operator]
            self.error_label.setText(
                translate_text(
                    "End time must be later than start time", self._language
                )
            )
            return
        self.accept()


class CancellationDialog(_SaveCancelDialog):
    def __init__(
        self,
        *,
        courses: Sequence[RecurringCourse],
        today: date,
        language: str = "zh_CN",
        parent: QWidget | None = None,
        title: str = "Cancel Course Occurrence",
    ) -> None:
        super().__init__(parent, language=language)
        self.setWindowTitle(translate_text(title, self._language))
        self.setModal(True)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.course_combo = QComboBox(self)
        for course in courses:
            self.course_combo.addItem(
                f"{course.name} · {WEEKDAY_NAMES[course.weekday - 1]}", course.id
            )
        form.addRow("Recurring course", self.course_combo)
        self.date_edit = QDateEdit(_to_qdate(today), self)
        self.date_edit.setCalendarPopup(True)
        form.addRow("Occurrence date", self.date_edit)
        layout.addLayout(form)
        self.error_label = QLabel(self)
        self.error_label.setStyleSheet("color: #b43f49;")
        layout.addWidget(self.error_label)
        layout.addWidget(self._button_box())
        translate_widget_tree(self, self._language)

    def values(self) -> tuple[int, date]:
        return int(self.course_combo.currentData()), _from_qdate(self.date_edit.date())

    def _accept_values(self) -> None:
        if self.course_combo.currentData() is None:
            self.error_label.setText(
                translate_text("Choose a recurring course", self._language)
            )
            return
        self.accept()


def _configure_course_list(widget: QListWidget) -> None:
    """Keep course collections scannable without consuming the whole page."""

    widget.setFixedHeight(COURSE_LIST_HEIGHT)
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    widget.setUniformItemSizes(True)
    widget.setWordWrap(False)
    widget.setTextElideMode(Qt.TextElideMode.ElideRight)
    widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)


class CoursePage(QWidget):
    """Manage the course domain through CourseService only."""

    def __init__(
        self,
        course_service: Any | None,
        settings_service: Any | None = None,
        clock: Clock | None = None,
        *,
        confirm_delete: Callable[[str], bool] | None = None,
        on_changed: Callable[[], object] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = course_service
        self._settings = settings_service
        self._clock = clock or SystemClock()
        self._confirm_delete = confirm_delete or self._show_delete_confirmation
        self._on_changed = on_changed
        stored_language = getattr(settings_service, "ui_language", "zh_CN")
        self._language = (
            stored_language if stored_language in SUPPORTED_LANGUAGES else "zh_CN"
        )
        self._period_snapshot: list[ClassPeriod] = []
        self._scheme_snapshot: TimetableScheme | None = None
        self._scheme_period_cache: tuple[TimetableSchemePeriod, ...] = ()
        self.setObjectName("courseSettingsPage")

        layout = QVBoxLayout(self)
        heading = QLabel("Courses and timetable", self)
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(heading)
        self.status_label = QLabel(self)
        self.status_label.setWordWrap(False)
        layout.addWidget(self.status_label)
        self.tabs = QTabWidget(self)
        self._build_semester_tab()
        self._build_recurring_tab()
        self._build_one_off_tab()
        self._build_timetable_tab()
        layout.addWidget(self.tabs, 1)
        self.refresh()

    def _build_semester_tab(self) -> None:
        page = QWidget(self.tabs)
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Semesters", page))
        self.semester_list = QListWidget(page)
        _configure_course_list(self.semester_list)
        layout.addWidget(self.semester_list)
        controls = QHBoxLayout()
        for title, callback in (
            ("Add", self.add_semester),
            ("Edit", self.edit_semester),
            ("Delete", self.delete_semester),
        ):
            button = QPushButton(title, page)
            button.clicked.connect(callback)
            controls.addWidget(button)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.semester_list.currentRowChanged.connect(self._semester_selected)
        active = QGroupBox("Active semester", page)
        active_form = QFormLayout(active)
        self.active_semester_combo = QComboBox(active)
        self.active_semester_combo.currentIndexChanged.connect(self._active_changed)
        active_form.addRow("Use", self.active_semester_combo)
        self.semester_scheme_combo = QComboBox(active)
        self.semester_scheme_combo.setObjectName("semesterTimetableSchemeCombo")
        active_form.addRow("Timetable scheme", self.semester_scheme_combo)
        self.bind_scheme_button = QPushButton("Bind selected scheme", active)
        self.bind_scheme_button.clicked.connect(self.bind_selected_semester_scheme)
        active_form.addRow("", self.bind_scheme_button)
        layout.addWidget(active)
        layout.addStretch(1)
        self.tabs.addTab(page, "Semesters")

    def _build_recurring_tab(self) -> None:
        page = QWidget(self.tabs)
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Weekly recurring courses", page))
        self.recurring_list = QListWidget(page)
        _configure_course_list(self.recurring_list)
        layout.addWidget(self.recurring_list)
        controls = QHBoxLayout()
        for title, callback in (
            ("Add", self.add_recurring_course),
            ("Edit", self.edit_recurring_course),
            ("Delete", self.delete_recurring_course),
            ("Cancel occurrence", self.cancel_occurrence),
            ("Restore occurrence", self.restore_occurrence),
        ):
            button = QPushButton(title, page)
            button.clicked.connect(callback)
            controls.addWidget(button)
        controls.addStretch(1)
        layout.addLayout(controls)
        layout.addStretch(1)
        self.tabs.addTab(page, "Recurring")

    def _build_one_off_tab(self) -> None:
        page = QWidget(self.tabs)
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("One-off courses and reschedules", page))
        self.one_off_list = QListWidget(page)
        _configure_course_list(self.one_off_list)
        layout.addWidget(self.one_off_list)
        controls = QHBoxLayout()
        for title, callback in (
            ("Add", self.add_one_off_course),
            ("Edit", self.edit_one_off_course),
            ("Delete", self.delete_one_off_course),
        ):
            button = QPushButton(title, page)
            button.clicked.connect(callback)
            controls.addWidget(button)
        controls.addStretch(1)
        layout.addLayout(controls)
        layout.addStretch(1)
        self.tabs.addTab(page, "One-off")

    def _build_timetable_tab(self) -> None:
        page = QWidget(self.tabs)
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Reusable timetable schemes", page))

        scheme_group = QGroupBox("Timetable schemes", page)
        scheme_layout = QVBoxLayout(scheme_group)
        self.scheme_list = QListWidget(scheme_group)
        self.scheme_list.setObjectName("timetableSchemeList")
        _configure_course_list(self.scheme_list)
        self.scheme_list.currentRowChanged.connect(self._scheme_selected)
        scheme_layout.addWidget(self.scheme_list)
        scheme_actions = QHBoxLayout()
        for title, callback in (
            ("Add scheme", self.create_scheme),
            ("Duplicate", self.duplicate_scheme),
            ("Rename", self.rename_scheme),
            ("Delete", self.delete_scheme),
        ):
            button = QPushButton(title, scheme_group)
            button.clicked.connect(lambda _checked=False, callback=callback: callback())
            scheme_actions.addWidget(button)
        scheme_actions.addStretch(1)
        scheme_layout.addLayout(scheme_actions)
        scheme_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        layout.addWidget(scheme_group)

        editor = QGroupBox("Scheme editor (Save / Cancel)", page)
        editor_form = QFormLayout(editor)
        self.scheme_name_edit = QLineEdit(editor)
        self.scheme_name_edit.setObjectName("timetableSchemeNameEdit")
        editor_form.addRow("Name", self.scheme_name_edit)
        self.scheme_axis_mode_combo = QComboBox(editor)
        self.scheme_axis_mode_combo.setObjectName("timetableSchemeAxisModeCombo")
        self.scheme_axis_mode_combo.addItem("Custom school periods", "custom_periods")
        self.scheme_axis_mode_combo.addItem("Uniform day (no school times)", "uniform_day")
        self.scheme_axis_mode_combo.currentIndexChanged.connect(
            lambda _index: self._refresh_scheme_editor_rows()
        )
        editor_form.addRow("Axis", self.scheme_axis_mode_combo)
        self.scheme_period_count_spin = QSpinBox(editor)
        self.scheme_period_count_spin.setObjectName("timetableSchemePeriodCount")
        self.scheme_period_count_spin.setRange(1, 24)
        self.scheme_period_count_spin.setValue(8)
        self.scheme_period_count_spin.valueChanged.connect(
            lambda _value: self._refresh_scheme_editor_rows()
        )
        editor_form.addRow("Guide / period count", self.scheme_period_count_spin)

        self.scheme_day_start_edit = QLineEdit("00:00", editor)
        self.scheme_day_start_edit.setObjectName("timetableSchemeDayStart")
        self.scheme_day_end_edit = QLineEdit("24:00", editor)
        self.scheme_day_end_edit.setObjectName("timetableSchemeDayEnd")
        day_row = QHBoxLayout()
        day_row.addWidget(self.scheme_day_start_edit)
        day_row.addWidget(QLabel("to", editor))
        day_row.addWidget(self.scheme_day_end_edit)
        editor_form.addRow("Uniform day range", day_row)

        self.scheme_period_table = QTableWidget(editor)
        self.scheme_period_table.setObjectName("timetableSchemePeriodTable")
        self.scheme_period_table.setColumnCount(3)
        self.scheme_period_table.setHorizontalHeaderLabels(("Period", "Start", "End"))
        self.scheme_period_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.scheme_period_table.setAlternatingRowColors(True)
        self.scheme_period_table.setWordWrap(False)
        self.scheme_period_table.verticalHeader().setVisible(False)
        self.scheme_period_table.verticalHeader().setDefaultSectionSize(44)
        self.scheme_period_table.verticalHeader().setMinimumSectionSize(44)
        header = self.scheme_period_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.scheme_period_table.setColumnWidth(0, 82)
        self.scheme_period_table.setMinimumHeight(190)
        editor_form.addRow("Custom period rows", self.scheme_period_table)
        editor_buttons = QHBoxLayout()
        save_scheme = QPushButton("Save scheme", editor)
        save_scheme.clicked.connect(self.save_scheme)
        cancel_scheme = QPushButton("Cancel", editor)
        cancel_scheme.clicked.connect(self.cancel_scheme)
        editor_buttons.addWidget(save_scheme)
        editor_buttons.addWidget(cancel_scheme)
        editor_buttons.addStretch(1)
        editor_form.addRow("", editor_buttons)
        self.scheme_status_label = QLabel(editor)
        self.scheme_status_label.setObjectName("timetableSchemeStatus")
        self.scheme_status_label.setWordWrap(True)
        self.scheme_status_label.setMinimumHeight(28)
        editor_form.addRow("", self.scheme_status_label)
        layout.addWidget(editor)

        # Kept as an internal compatibility editor for old callers/tests;
        # visible Task 31 editing is performed by the scheme controls above.
        self.period_start_edits: list[QTimeEdit] = []
        self.period_end_edits: list[QTimeEdit] = []
        for number in range(1, 9):
            start = _time_edit(time(8))
            end = _time_edit(time(9))
            self.period_start_edits.append(start)
            self.period_end_edits.append(end)
            start.setVisible(False)
            end.setVisible(False)

        header_group = QGroupBox("Timetable header", page)
        header_form = QFormLayout(header_group)
        self.header_mode_combo = QComboBox(header_group)
        for label, mode in HEADER_MODES:
            self.header_mode_combo.addItem(label, mode)
        self.header_mode_combo.currentIndexChanged.connect(self._header_mode_changed)
        header_form.addRow("Column labels", self.header_mode_combo)
        layout.addWidget(header_group)
        layout.addStretch(1)
        self.tabs.addTab(page, "Timetable")

    def refresh(self) -> None:
        if self._service is None:
            self.status_label.setText(
                translate_text("Course service unavailable", self._language)
            )
            return
        try:
            semesters = list(self._service.list_semesters())
            active = self._service.get_active_semester()
            recurring = list(self._service.list_recurring_courses())
            one_off = list(self._service.list_one_off_courses())
            periods = list(self._service.get_class_periods())
            list_schemes = getattr(self._service, "list_timetable_schemes", None)
            schemes = list(list_schemes()) if callable(list_schemes) else []
        except (LookupError, TypeError, ValueError, AttributeError) as error:
            self.status_label.setText(str(error))
            return
        self._fill_schemes(schemes)
        self._fill_semesters(semesters, active, schemes)
        semester_names = {semester.id: semester.name for semester in semesters}
        self._fill_recurring(recurring, semester_names)
        self._fill_one_off(one_off, semester_names)
        self._load_periods(periods)
        self._load_header_mode()
        self._semester_selected(self.semester_list.currentRow())
        configured = bool(active and active.timetable_scheme_id) or (
            len(periods) == 8 and {item.period_no for item in periods} == set(range(1, 9))
        )
        self.status_label.setText(self._summary_text(
            len(semesters), len(recurring), len(one_off), len(schemes), configured
        ))

    def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            return
        self._language = language
        self.refresh()

    def _summary_text(
        self,
        semesters: int,
        recurring: int,
        one_off: int,
        schemes: int,
        configured: bool,
    ) -> str:
        if self._language == "zh_CN":
            return (
                f"{semesters} 个学期 · {recurring} 个每周课程 · "
                f"{one_off} 个单次课程 · {schemes} 个方案 · "
                f"时间轴{'已配置' if configured else '未配置'}"
            )
        return (
            f"{semesters} semesters · {recurring} recurring · "
            f"{one_off} one-off · schemes {schemes} · "
            f"axis {'configured' if configured else 'not configured'}"
        )

    def _fill_schemes(self, schemes: Sequence[TimetableScheme]) -> None:
        selected = self._selected_id(self.scheme_list)
        with QSignalBlocker(self.scheme_list):
            self.scheme_list.clear()
            for scheme in schemes:
                mode_label = translate_text(
                    "custom" if scheme.axis_mode == "custom_periods" else "uniform",
                    self._language,
                )
                item = QListWidgetItem(
                    f"{scheme.name} · {mode_label} · {scheme.period_count}",
                    self.scheme_list,
                )
                item.setToolTip(item.text())
                item.setData(Qt.ItemDataRole.UserRole, scheme.id)
                if scheme.id == selected:
                    self.scheme_list.setCurrentItem(item)
            if self.scheme_list.currentItem() is None and self.scheme_list.count():
                self.scheme_list.setCurrentRow(0)
        self._scheme_selected(self.scheme_list.currentRow())

    def _fill_semesters(
        self,
        semesters: Sequence[Semester],
        active: Semester | None,
        schemes: Sequence[TimetableScheme] = (),
    ) -> None:
        selected = self._selected_id(self.semester_list)
        target = selected
        if target is None:
            target = active.id if active else (semesters[0].id if semesters else None)
        with (
            QSignalBlocker(self.active_semester_combo),
            QSignalBlocker(self.semester_list),
            QSignalBlocker(self.semester_scheme_combo),
        ):
            self.semester_list.clear()
            self.active_semester_combo.clear()
            self.active_semester_combo.addItem(
                translate_text("No active semester", self._language), None
            )
            for semester in semesters:
                weeks = (
                    f"{semester.total_weeks} 周"
                    if self._language == "zh_CN"
                    else f"{semester.total_weeks} weeks"
                )
                label = (
                    f"{semester.name} · {semester.start_monday:%Y-%m-%d} · "
                    f"{weeks}"
                )
                item = QListWidgetItem(label, self.semester_list)
                item.setToolTip(label)
                item.setData(Qt.ItemDataRole.UserRole, semester.id)
                self.active_semester_combo.addItem(semester.name, semester.id)
                if semester.id == target:
                    self.semester_list.setCurrentItem(item)
            _select_data(self.active_semester_combo, active.id if active else None)
            self.semester_scheme_combo.clear()
            self.semester_scheme_combo.addItem(
                translate_text("Unbound / configure first", self._language), None
            )
            for scheme in schemes:
                self.semester_scheme_combo.addItem(scheme.name, scheme.id)
            if self.semester_list.currentRow() < 0 and self.semester_list.count():
                self.semester_list.setCurrentRow(0)

    def _fill_recurring(
        self, courses: Sequence[RecurringCourse], semester_names: Mapping[int, str]
    ) -> None:
        selected = self._selected_id(self.recurring_list)
        self.recurring_list.clear()
        for course in courses:
            week_range = (
                f"第{course.start_week}–{course.end_week}周"
                if self._language == "zh_CN"
                else f"W{course.start_week}–W{course.end_week}"
            )
            label = (
                f"{course.name} · {semester_names.get(course.semester_id, '?')} · "
                f"{WEEKDAY_NAMES[course.weekday - 1]} "
                f"{course.start_time:%H:%M}–{course.end_time:%H:%M} · "
                f"{week_range}"
            )
            if course.classroom:
                label += f" · {course.classroom}"
            item = QListWidgetItem(label, self.recurring_list)
            item.setToolTip(label)
            item.setData(Qt.ItemDataRole.UserRole, course.id)
            if course.id == selected:
                self.recurring_list.setCurrentItem(item)

    def _fill_one_off(
        self, courses: Sequence[OneOffCourse], semester_names: Mapping[int, str]
    ) -> None:
        selected = self._selected_id(self.one_off_list)
        self.one_off_list.clear()
        for course in courses:
            label = (
                f"{course.name} · {semester_names.get(course.semester_id, '?')} · "
                f"{course.course_date:%Y-%m-%d} {course.start_time:%H:%M}–{course.end_time:%H:%M}"
            )
            if course.classroom:
                label += f" · {course.classroom}"
            item = QListWidgetItem(label, self.one_off_list)
            item.setToolTip(label)
            item.setData(Qt.ItemDataRole.UserRole, course.id)
            if course.id == selected:
                self.one_off_list.setCurrentItem(item)

    def _load_periods(self, periods: Sequence[ClassPeriod]) -> None:
        self._period_snapshot = list(periods)
        by_number = {period.period_no: period for period in periods}
        for number, (start, end) in enumerate(
            zip(self.period_start_edits, self.period_end_edits, strict=True), start=1
        ):
            period = by_number.get(number)
            start.setTime(_to_qtime(period.start_time if period else time(8)))
            end.setTime(_to_qtime(period.end_time if period else time(9)))

    def _load_header_mode(self) -> None:
        mode = DEFAULT_TIMETABLE_HEADER_MODE
        if self._settings is not None:
            try:
                mode = str(self._settings.timetable_header_mode)
            except (AttributeError, TypeError, ValueError):
                try:
                    mode = str(self._settings.get("timetable.header_mode", mode))
                except (AttributeError, TypeError, ValueError):
                    pass
        try:
            mode = normalize_timetable_header_mode(mode)
        except (TypeError, ValueError):
            mode = DEFAULT_TIMETABLE_HEADER_MODE
        with QSignalBlocker(self.header_mode_combo):
            _select_data(self.header_mode_combo, mode)

    def _scheme_selected(self, _index: int) -> None:
        scheme_id = self._selected_id(self.scheme_list)
        scheme = (
            self._service.get_timetable_scheme(scheme_id)
            if self._service is not None and scheme_id is not None
            else None
        )
        self._load_scheme_editor(scheme)

    def _semester_selected(self, index: int) -> None:
        if self._service is None or index < 0:
            return
        item = self.semester_list.item(index)
        if item is None:
            return
        semester_id = item.data(Qt.ItemDataRole.UserRole)
        if semester_id is None:
            return
        semester = self._service.get_semester(int(semester_id))
        if semester is None:
            return
        with QSignalBlocker(self.semester_scheme_combo):
            _select_data(self.semester_scheme_combo, semester.timetable_scheme_id)
        if semester.timetable_scheme_id is not None:
            self._select_scheme_for_id(semester.timetable_scheme_id)

    def _select_scheme_for_id(self, scheme_id: int) -> None:
        for row in range(self.scheme_list.count()):
            item = self.scheme_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) != scheme_id:
                continue
            with QSignalBlocker(self.scheme_list):
                self.scheme_list.setCurrentRow(row)
            self._scheme_selected(row)
            return

    def _load_scheme_for_active_semester(self, active: Semester | None) -> None:
        if active is not None and active.timetable_scheme_id is not None:
            self._select_scheme_for_id(active.timetable_scheme_id)

    def _load_scheme_editor(self, scheme: TimetableScheme | None) -> None:
        self._scheme_snapshot = scheme
        with QSignalBlocker(self.scheme_axis_mode_combo), QSignalBlocker(
            self.scheme_period_count_spin
        ):
            self.scheme_name_edit.setText(scheme.name if scheme else "")
            self.scheme_axis_mode_combo.setCurrentIndex(
                max(
                    0,
                    self.scheme_axis_mode_combo.findData(
                        scheme.axis_mode if scheme else "uniform_day"
                    ),
                )
            )
            self.scheme_period_count_spin.setValue(scheme.period_count if scheme else 8)
        self.scheme_day_start_edit.setText(
            _time_text(scheme.day_start if scheme and scheme.day_start else time(0))
        )
        self.scheme_day_end_edit.setText(
            _time_text(scheme.day_end if scheme and scheme.day_end else END_OF_DAY)
        )
        self._refresh_scheme_editor_rows(scheme.periods if scheme else ())

    def _refresh_scheme_editor_rows(
        self, periods: Sequence[TimetableSchemePeriod] | None = None
    ) -> None:
        if periods is None:
            periods = self._read_period_editor_rows() or self._scheme_period_cache
        else:
            periods = tuple(periods)
        self._scheme_period_cache = tuple(periods)
        custom = self.scheme_axis_mode_combo.currentData() == "custom_periods"
        self.scheme_period_table.setVisible(custom)
        self.scheme_period_table.setRowCount(self.scheme_period_count_spin.value() if custom else 0)
        by_number = {item.period_no: item for item in periods}
        for row in range(self.scheme_period_table.rowCount()):
            number = row + 1
            self.scheme_period_table.setItem(row, 0, QTableWidgetItem(str(number)))
            item = by_number.get(number)
            default_start, default_end = _default_period_range(
                number, self.scheme_period_count_spin.value()
            )
            start = _time_edit(item.start_time if item else default_start)
            end = _time_edit(item.end_time if item else default_end)
            self.scheme_period_table.setCellWidget(row, 1, start)
            self.scheme_period_table.setCellWidget(row, 2, end)
            self.scheme_period_table.setRowHeight(row, 44)

    def _read_period_editor_rows(self) -> tuple[TimetableSchemePeriod, ...]:
        rows: list[TimetableSchemePeriod] = []
        for row in range(self.scheme_period_table.rowCount()):
            start = self.scheme_period_table.cellWidget(row, 1)
            end = self.scheme_period_table.cellWidget(row, 2)
            if isinstance(start, QTimeEdit) and isinstance(end, QTimeEdit):
                rows.append(
                    TimetableSchemePeriod(
                        row + 1,
                        _from_qtime(start.time()),
                        _from_qtime(end.time()),
                    )
                )
        return tuple(rows)

    def _scheme_editor_values(self) -> dict[str, object]:
        mode = self.scheme_axis_mode_combo.currentData()
        periods: list[TimetableSchemePeriod] = []
        if mode == "custom_periods":
            for row in range(self.scheme_period_table.rowCount()):
                start = self.scheme_period_table.cellWidget(row, 1)
                end = self.scheme_period_table.cellWidget(row, 2)
                if not isinstance(start, QTimeEdit) or not isinstance(end, QTimeEdit):
                    raise ValueError("Custom period editor is incomplete")
                periods.append(
                    TimetableSchemePeriod(
                        row + 1,
                        _from_qtime(start.time()),
                        _from_qtime(end.time()),
                    )
                )
        return {
            "name": self.scheme_name_edit.text().strip(),
            "axis_mode": mode,
            "period_count": self.scheme_period_count_spin.value(),
            "periods": periods,
            "day_start": self.scheme_day_start_edit.text().strip(),
            "day_end": self.scheme_day_end_edit.text().strip(),
        }

    def create_scheme(self, name: str | None = None) -> bool:
        if self._service is None:
            return False
        name = name or DEFAULT_TIMETABLE_SCHEME_NAME
        return self._run_change(
            lambda: self._service.create_timetable_scheme(
                name,
                axis_mode="uniform_day",
                period_count=8,
                day_start="00:00",
                day_end="24:00",
            ),
            "Timetable scheme created",
        )

    def duplicate_scheme(self, name: str | None = None) -> bool:
        if self._service is None:
            return False
        scheme_id = self._selected_id(self.scheme_list)
        if scheme_id is None:
            return False
        scheme = self._service.get_timetable_scheme(scheme_id)
        if scheme is None:
            return False
        duplicate_name = name or (
            f"{scheme.name} 副本"
            if self._language == "zh_CN"
            else f"{scheme.name} copy"
        )
        return self._run_change(
            lambda: self._service.duplicate_timetable_scheme(scheme_id, duplicate_name),
            "Timetable scheme duplicated",
        )

    def rename_scheme(self, name: str | None = None) -> bool:
        if self._service is None:
            return False
        scheme_id = self._selected_id(self.scheme_list)
        if scheme_id is None:
            return False
        scheme = self._service.get_timetable_scheme(scheme_id)
        if scheme is None:
            return False
        name = self._name_input("Rename timetable scheme", name)
        if name is None:
            return False
        return self._run_change(
            lambda: self._service.rename_timetable_scheme(scheme_id, name),
            "Timetable scheme renamed",
        )

    def delete_scheme(self, scheme_id: int | None = None) -> bool:
        if self._service is None:
            return False
        scheme_id = scheme_id or self._selected_id(self.scheme_list)
        if scheme_id is None:
            return False
        scheme = self._service.get_timetable_scheme(scheme_id)
        if scheme is None or not self._confirm_delete(f"timetable scheme {scheme.name}"):
            return False
        return self._run_change(
            lambda: self._service.delete_timetable_scheme(scheme_id, confirmed=True),
            "Timetable scheme deleted; affected semesters are unbound",
        )

    def save_scheme(
        self,
        scheme_id: int | None = None,
        values: Mapping[str, object] | None = None,
    ) -> bool:
        if isinstance(scheme_id, bool):
            scheme_id = None
        if self._service is None:
            return False
        scheme_id = scheme_id or self._selected_id(self.scheme_list)
        if scheme_id is None:
            self.scheme_status_label.setText(
                translate_text(
                    "Select a timetable scheme before saving", self._language
                )
            )
            return False
        try:
            selected = dict(values or self._scheme_editor_values())
        except (TypeError, ValueError) as error:
            self.scheme_status_label.setText(
                translate_text(str(error), self._language)
            )
            return False
        return self._run_change(
            lambda: self._service.save_timetable_scheme(
                scheme_id,
                str(selected["name"]),
                axis_mode=selected["axis_mode"],
                period_count=int(selected["period_count"]),
                periods=selected.get("periods"),
                day_start=selected.get("day_start"),
                day_end=selected.get("day_end"),
            ),
            "Timetable scheme saved",
            detail_label=self.scheme_status_label,
        )

    def cancel_scheme(self) -> None:
        scheme_id = self._selected_id(self.scheme_list)
        scheme = (
            self._service.get_timetable_scheme(scheme_id)
            if self._service is not None and scheme_id is not None
            else self._scheme_snapshot
        )
        self._load_scheme_editor(scheme)
        self.status_label.setText(
            translate_text("Timetable scheme edits cancelled", self._language)
        )

    def bind_selected_semester_scheme(
        self,
        semester_id: int | None = None,
        scheme_id: int | None = None,
    ) -> bool:
        if self._service is None:
            return False
        active = self._service.get_active_semester()
        selected_semester = semester_id or self._selected_id(self.semester_list)
        if selected_semester is None and active is not None:
            selected_semester = active.id
        if selected_semester is None:
            return False
        if scheme_id is None:
            scheme_id = self.semester_scheme_combo.currentData()
        if scheme_id is not None:
            scheme_id = int(scheme_id)
        return self._run_change(
            lambda: self._service.bind_semester_timetable_scheme(selected_semester, scheme_id),
            "Semester timetable scheme binding saved",
        )

    bind_semester_scheme = bind_selected_semester_scheme

    def add_semester(
        self,
        name: str | None = None,
        start_monday: date | None = None,
        total_weeks: int | None = None,
    ) -> bool:
        if self._service is None:
            return False
        if name is None or start_monday is None or total_weeks is None:
            dialog = SemesterEditorDialog(
                today=self._clock.today(), language=self._language, parent=self
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            values = dialog.values()
        else:
            values = {"name": name, "start_monday": start_monday, "total_weeks": total_weeks}
        return self._run_change(
            lambda: self._service.create_semester(**values),
            "Semester saved",
        )

    def edit_semester(
        self,
        semester_id: int | None = None,
        values: Mapping[str, object] | None = None,
    ) -> bool:
        if self._service is None:
            return False
        semester_id = semester_id or self._selected_id(self.semester_list)
        if semester_id is None:
            return False
        semester = self._service.get_semester(semester_id)
        if semester is None:
            return False
        if values is None:
            dialog = SemesterEditorDialog(
                today=self._clock.today(),
                semester=semester,
                language=self._language,
                parent=self,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            values = dialog.values()
        return self._run_change(
            lambda: self._service.update_semester(semester_id, **dict(values)),
            "Semester updated",
        )

    def delete_semester(self, semester_id: int | None = None) -> bool:
        if self._service is None:
            return False
        semester_id = semester_id or self._selected_id(self.semester_list)
        if semester_id is None:
            return False
        semester = self._service.get_semester(semester_id)
        if semester is None or not self._confirm_delete(f"semester {semester.name}"):
            return False
        return self._run_change(
            lambda: self._service.delete_semester(semester_id),
            "Semester deleted",
        )

    def set_active_semester(self, semester_id: int | None) -> bool:
        if self._service is None:
            return False
        return self._run_change(
            lambda: self._service.set_active_semester(semester_id),
            "Active semester updated",
        )

    def add_recurring_course(self, values: Mapping[str, object] | None = None, **kwargs) -> bool:
        if self._service is None:
            return False
        values = dict(values or kwargs)
        if not values:
            dialog = RecurringCourseEditorDialog(
                semesters=self._service.list_semesters(),
                language=self._language,
                parent=self,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            values = dialog.values()
        return self._run_change(
            lambda: self._service.create_recurring_course(**values),
            "Recurring course saved",
        )

    def edit_recurring_course(
        self,
        course_id: int | None = None,
        values: Mapping[str, object] | None = None,
    ) -> bool:
        if self._service is None:
            return False
        course_id = course_id or self._selected_id(self.recurring_list)
        if course_id is None:
            return False
        course = self._service.get_recurring_course(course_id)
        if course is None:
            return False
        if values is None:
            dialog = RecurringCourseEditorDialog(
                semesters=self._service.list_semesters(),
                course=course,
                language=self._language,
                parent=self,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            values = dialog.values()
        return self._run_change(
            lambda: self._service.update_recurring_course(course_id, **dict(values)),
            "Recurring course updated",
        )

    def delete_recurring_course(self, course_id: int | None = None) -> bool:
        if self._service is None:
            return False
        course_id = course_id or self._selected_id(self.recurring_list)
        if course_id is None:
            return False
        course = self._service.get_recurring_course(course_id)
        if course is None or not self._confirm_delete(f"recurring course {course.name}"):
            return False
        return self._run_change(
            lambda: self._service.delete_recurring_course(course_id),
            "Recurring course deleted",
        )

    def cancel_occurrence(
        self,
        course_id: int | None = None,
        occurrence_date: date | None = None,
    ) -> bool:
        if self._service is None:
            return False
        if course_id is None or occurrence_date is None:
            dialog = CancellationDialog(
                courses=self._service.list_recurring_courses(),
                today=self._clock.today(),
                language=self._language,
                parent=self,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            course_id, occurrence_date = dialog.values()
        return self._run_change(
            lambda: self._service.cancel_occurrence(course_id, occurrence_date),
            "Occurrence cancelled",
        )

    def restore_occurrence(
        self,
        course_id: int | None = None,
        occurrence_date: date | None = None,
    ) -> bool:
        if self._service is None:
            return False
        if course_id is None or occurrence_date is None:
            dialog = CancellationDialog(
                courses=self._service.list_recurring_courses(),
                today=self._clock.today(),
                language=self._language,
                parent=self,
                title="Restore Course Occurrence",
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            course_id, occurrence_date = dialog.values()
        return self._run_change(
            lambda: self._service.uncancel_occurrence(course_id, occurrence_date),
            "Occurrence restored",
        )

    def add_one_off_course(self, values: Mapping[str, object] | None = None, **kwargs) -> bool:
        if self._service is None:
            return False
        values = dict(values or kwargs)
        if not values:
            dialog = OneOffCourseEditorDialog(
                semesters=self._service.list_semesters(),
                today=self._clock.today(),
                language=self._language,
                parent=self,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            values = dialog.values()
        return self._run_change(
            lambda: self._service.create_one_off_course(**values),
            "One-off course saved",
        )

    def edit_one_off_course(
        self,
        course_id: int | None = None,
        values: Mapping[str, object] | None = None,
    ) -> bool:
        if self._service is None:
            return False
        course_id = course_id or self._selected_id(self.one_off_list)
        if course_id is None:
            return False
        course = self._service.get_one_off_course(course_id)
        if course is None:
            return False
        if values is None:
            dialog = OneOffCourseEditorDialog(
                semesters=self._service.list_semesters(),
                today=self._clock.today(),
                course=course,
                language=self._language,
                parent=self,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            values = dialog.values()
        return self._run_change(
            lambda: self._service.update_one_off_course(course_id, **dict(values)),
            "One-off course updated",
        )

    def delete_one_off_course(self, course_id: int | None = None) -> bool:
        if self._service is None:
            return False
        course_id = course_id or self._selected_id(self.one_off_list)
        if course_id is None:
            return False
        course = self._service.get_one_off_course(course_id)
        if course is None or not self._confirm_delete(f"one-off course {course.name}"):
            return False
        return self._run_change(
            lambda: self._service.delete_one_off_course(course_id),
            "One-off course deleted",
        )

    def save_periods(self, periods: Sequence[ClassPeriod] | None = None) -> bool:
        if self._service is None:
            return False
        selected = list(periods) if periods is not None else self._period_values()
        return self._run_change(
            lambda: self._service.save_class_periods(selected),
            "Class periods saved",
        )

    def cancel_periods(self) -> None:
        self._load_periods(self._period_snapshot)
        self.status_label.setText(
            translate_text("Class-period edits cancelled", self._language)
        )

    def set_header_mode(self, mode: str) -> bool:
        try:
            normalized = normalize_timetable_header_mode(mode)
        except (TypeError, ValueError) as error:
            self.status_label.setText(str(error))
            return False
        try:
            if self._settings is not None:
                setter = getattr(self._settings, "set_timetable_header_mode", None)
                if callable(setter):
                    setter(normalized)
                else:
                    self._settings.set("timetable.header_mode", normalized)
        except (LookupError, TypeError, ValueError) as error:
            self.status_label.setText(str(error))
            return False
        header_label = next(
            (
                label
                for label, value in HEADER_MODES
                if value == normalized
            ),
            normalized,
        )
        self.status_label.setText(
            f"{translate_text('Timetable header', self._language)}："
            f"{translate_text(header_label, self._language)}"
        )
        if self._on_changed is not None:
            self._on_changed()
        return True

    def _header_mode_changed(self, index: int) -> None:
        if index >= 0:
            self.set_header_mode(str(self.header_mode_combo.itemData(index)))

    def _active_changed(self, index: int) -> None:
        if index >= 0 and self._service is not None:
            self.set_active_semester(self.active_semester_combo.itemData(index))

    def _period_values(self) -> list[ClassPeriod]:
        return [
            ClassPeriod(
                period_no=index,
                start_time=_from_qtime(start.time()),
                end_time=_from_qtime(end.time()),
            )
            for index, (start, end) in enumerate(
                zip(self.period_start_edits, self.period_end_edits, strict=True), start=1
            )
        ]

    def _run_change(
        self,
        action: Callable[[], object],
        message: str,
        *,
        detail_label: QLabel | None = None,
    ) -> bool:
        try:
            action()
        except (LookupError, TypeError, ValueError, sqlite3.Error) as error:
            text = str(error)
            self.status_label.setText(translate_text(text, self._language))
            if detail_label is not None:
                detail_label.setText(
                    f"{translate_text('Save failed: ', self._language)}"
                    f"{translate_text(text, self._language)}"
                )
            return False
        self.refresh()
        localized_message = translate_text(message, self._language)
        self.status_label.setText(localized_message)
        if detail_label is not None:
            detail_label.setText(localized_message)
        if self._on_changed is not None:
            self._on_changed()
        return True

    @staticmethod
    def _selected_id(widget: QListWidget) -> int | None:
        item = widget.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return None if value is None else int(value)

    def _name_input(self, title: str, name: str | None) -> str | None:
        if name is not None:
            return name.strip() or None
        value, accepted = QInputDialog.getText(
            self.window(),
            translate_text(title, self._language),
            translate_text("Scheme name:", self._language),
        )
        return value.strip() if accepted and value.strip() else None

    def _show_delete_confirmation(self, label: str) -> bool:
        localized_label = label
        for source in (
            "timetable scheme",
            "recurring course",
            "one-off course",
            "semester",
        ):
            prefix = f"{source} "
            if label.startswith(prefix):
                localized_label = (
                    f"{translate_text(source, self._language)} "
                    f"{label[len(prefix):]}"
                )
                break
        answer = QMessageBox.question(
            self if self.isVisible() else None,
            translate_text("Delete course data?", self._language),
            (
                f"删除 {localized_label}？此操作无法撤销。"
                if self._language == "zh_CN"
                else f"Delete {localized_label}? This cannot be undone."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes


def _monday(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _time_edit(value: time) -> QTimeEdit:
    editor = QTimeEdit(_to_qtime(value))
    editor.setDisplayFormat("HH:mm")
    editor.setMinimumHeight(36)
    editor.setMinimumWidth(128)
    editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return editor


def _default_period_range(period_no: int, period_count: int) -> tuple[time, time]:
    """Return a valid, non-overlapping starter range for a custom scheme."""

    day_start = 8 * 60
    latest = 23 * 60 + 59
    if period_count <= 16:
        start_minutes = day_start + (period_no - 1) * 60
        end_minutes = min(latest, start_minutes + 60)
    else:
        slot = max(1, (latest - day_start) // period_count)
        start_minutes = day_start + (period_no - 1) * slot
        end_minutes = min(latest, start_minutes + slot)
    if end_minutes <= start_minutes:
        end_minutes = min(latest, start_minutes + 1)
    return _minutes_to_time(start_minutes), _minutes_to_time(end_minutes)


def _minutes_to_time(minutes: int) -> time:
    minutes = max(0, min(23 * 60 + 59, minutes))
    return time(minutes // 60, minutes % 60)


def _time_text(value: time) -> str:
    return "24:00" if value == END_OF_DAY else value.strftime("%H:%M")


def _to_qdate(value: date) -> QDate:
    return QDate(value.year, value.month, value.day)


def _from_qdate(value: QDate) -> date:
    return date(value.year(), value.month(), value.day())


def _to_qtime(value: time) -> QTime:
    return QTime(value.hour, value.minute, value.second)


def _from_qtime(value: QTime) -> time:
    return time(value.hour(), value.minute(), value.second())


def _select_data(combo: QComboBox, value: object) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)
