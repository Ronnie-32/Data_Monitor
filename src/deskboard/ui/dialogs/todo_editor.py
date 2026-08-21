"""Native structured Todo editor and Qt-independent input normalization."""

from __future__ import annotations

from datetime import date, time

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTimeEdit,
    QVBoxLayout,
)

from deskboard.models.todo import Todo, TodoUpdate


def build_todo_update(
    *,
    content: str,
    today: date,
    deadline_date: date | None = None,
    deadline_time: time | None = None,
    planned_date: date | None = None,
    planned_start_time: time | None = None,
    planned_end_time: time | None = None,
) -> TodoUpdate:
    """Validate native editor values and make time-only defaults explicit."""
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("Todo content must not be empty")
    if deadline_time is not None and deadline_date is None:
        deadline_date = today
    if planned_end_time is not None and planned_start_time is None:
        raise ValueError("planned end requires a planned start")
    if planned_end_time is not None and planned_end_time <= planned_start_time:
        raise ValueError("planned end must be later than planned start")
    if planned_start_time is not None and planned_date is None:
        planned_date = today
    return TodoUpdate(
        content=normalized_content,
        deadline_date=deadline_date,
        deadline_time=deadline_time,
        planned_date=planned_date,
        planned_start_time=planned_start_time,
        planned_end_time=planned_end_time,
    )


class TodoEditorDialog(QDialog):
    """Edit all V1 Todo detail fields with explicit Save/Cancel behavior."""

    def __init__(self, todo: Todo, today: date, parent=None) -> None:
        super().__init__(parent)
        self._today = today
        self.todo_update: TodoUpdate | None = None
        self.setWindowTitle("Edit Todo")
        self.setModal(True)
        self.resize(440, 360)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Todo details", self))
        form = QFormLayout()
        self.content_edit = QLineEdit(todo.content, self)
        self.content_edit.setMaxLength(500)
        form.addRow("Content", self.content_edit)

        self.deadline_date_enabled, self.deadline_date_edit = self._date_row(
            form, "Deadline date", todo.deadline_date
        )
        self.deadline_time_enabled, self.deadline_time_edit = self._time_row(
            form, "Deadline time", todo.deadline_time
        )
        self.planned_date_enabled, self.planned_date_edit = self._date_row(
            form, "Planned date", todo.planned_date
        )
        self.planned_start_enabled, self.planned_start_edit = self._time_row(
            form, "Planned start", todo.planned_start_time
        )
        self.planned_end_enabled, self.planned_end_edit = self._time_row(
            form, "Planned end", todo.planned_end_time
        )
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._accept_values)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _date_row(
        self, form: QFormLayout, label: str, value: date | None
    ) -> tuple[QCheckBox, QDateEdit]:
        enabled = QCheckBox("Set", self)
        editor = QDateEdit(self)
        editor.setCalendarPopup(True)
        initial = value or self._today
        editor.setDate(QDate(initial.year, initial.month, initial.day))
        enabled.setChecked(value is not None)
        editor.setEnabled(enabled.isChecked())
        enabled.toggled.connect(editor.setEnabled)
        form.addRow(label, enabled)
        form.addRow("", editor)
        return enabled, editor

    def _time_row(
        self, form: QFormLayout, label: str, value: time | None
    ) -> tuple[QCheckBox, QTimeEdit]:
        enabled = QCheckBox("Set", self)
        editor = QTimeEdit(self)
        editor.setDisplayFormat("HH:mm")
        initial = value or time(9)
        editor.setTime(QTime(initial.hour, initial.minute, initial.second))
        enabled.setChecked(value is not None)
        editor.setEnabled(enabled.isChecked())
        enabled.toggled.connect(editor.setEnabled)
        form.addRow(label, enabled)
        form.addRow("", editor)
        return enabled, editor

    def _accept_values(self) -> None:
        try:
            self.todo_update = build_todo_update(
                content=self.content_edit.text(),
                today=self._today,
                deadline_date=self._date_value(
                    self.deadline_date_enabled, self.deadline_date_edit
                ),
                deadline_time=self._time_value(
                    self.deadline_time_enabled, self.deadline_time_edit
                ),
                planned_date=self._date_value(
                    self.planned_date_enabled, self.planned_date_edit
                ),
                planned_start_time=self._time_value(
                    self.planned_start_enabled, self.planned_start_edit
                ),
                planned_end_time=self._time_value(
                    self.planned_end_enabled, self.planned_end_edit
                ),
            )
        except (TypeError, ValueError) as error:
            QMessageBox.warning(self, "Invalid Todo", str(error))
            return
        self.accept()

    @staticmethod
    def _date_value(enabled: QCheckBox, editor: QDateEdit) -> date | None:
        value = editor.date()
        return date(value.year(), value.month(), value.day()) if enabled.isChecked() else None

    @staticmethod
    def _time_value(enabled: QCheckBox, editor: QTimeEdit) -> time | None:
        value = editor.time()
        return time(value.hour(), value.minute(), value.second()) if enabled.isChecked() else None
