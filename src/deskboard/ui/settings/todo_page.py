"""Native Settings Todo management page."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from deskboard.infrastructure.clock import Clock
from deskboard.models.todo import Todo, TodoUpdate
from deskboard.ui.dialogs.todo_editor import TodoEditorDialog


class TodoManagementService(Protocol):
    def get(self, todo_id: int) -> Todo: ...

    def get_incomplete_items(self) -> list[Todo]: ...

    def get_completed_history(self) -> list[Todo]: ...

    def update(self, todo_id: int, update: TodoUpdate) -> Todo: ...

    def set_completed(self, todo_id: int, completed: bool) -> Todo: ...

    def restore(self, todo_id: int) -> Todo: ...

    def delete(self, todo_id: int) -> None: ...


ConfirmDelete = Callable[[int, str], bool]
EditorFactory = Callable[[Todo, object, QWidget | None], TodoEditorDialog]


class TodoPage(QWidget):
    """Two simple Todo views backed by the shared application service."""

    def __init__(
        self,
        service: TodoManagementService,
        clock: Clock,
        parent: QWidget | None = None,
        *,
        confirm_delete: ConfirmDelete | None = None,
        editor_factory: EditorFactory | None = None,
        on_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._clock = clock
        self._confirm_delete = confirm_delete or self._show_delete_confirmation
        self._editor_factory = editor_factory or TodoEditorDialog
        self._on_changed = on_changed or (lambda: None)

        layout = QVBoxLayout(self)
        heading = QLabel("Todo", self)
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(heading)
        self.tabs = QTabWidget(self)
        self.incomplete_list = QListWidget(self.tabs)
        self.completed_list = QListWidget(self.tabs)
        self.tabs.addTab(self._list_panel(self.incomplete_list, completed=False), "Incomplete")
        self.tabs.addTab(self._list_panel(self.completed_list, completed=True), "Completed history")
        layout.addWidget(self.tabs, 1)
        self.refresh()

    def _list_panel(self, todo_list: QListWidget, *, completed: bool) -> QWidget:
        panel = QWidget(self.tabs)
        layout = QVBoxLayout(panel)
        layout.addWidget(todo_list, 1)
        actions = QHBoxLayout()
        edit = QPushButton("Edit details", panel)
        edit.clicked.connect(lambda: self._edit_selected(todo_list))
        actions.addWidget(edit)
        if completed:
            restore = QPushButton("Restore to incomplete", panel)
            restore.clicked.connect(lambda: self._restore_selected(todo_list))
            actions.addWidget(restore)
        else:
            complete = QPushButton("Mark complete", panel)
            complete.clicked.connect(lambda: self._complete_selected(todo_list))
            actions.addWidget(complete)
        delete = QPushButton("Delete permanently", panel)
        delete.clicked.connect(lambda: self._delete_selected(todo_list))
        actions.addWidget(delete)
        actions.addStretch(1)
        layout.addLayout(actions)
        return panel

    def refresh(self) -> None:
        self._fill(self.incomplete_list, self._service.get_incomplete_items())
        self._fill(self.completed_list, self._service.get_completed_history())

    @staticmethod
    def _fill(widget: QListWidget, todos: list[Todo]) -> None:
        widget.clear()
        for todo in todos:
            item = QListWidgetItem(todo.content, widget)
            item.setData(Qt.ItemDataRole.UserRole, todo.id)

    def incomplete_ids(self) -> list[int]:
        return self._ids(self.incomplete_list)

    def completed_ids(self) -> list[int]:
        return self._ids(self.completed_list)

    @staticmethod
    def _ids(widget: QListWidget) -> list[int]:
        return [
            int(widget.item(index).data(Qt.ItemDataRole.UserRole))
            for index in range(widget.count())
        ]

    def open_editor(self, todo_id: int) -> bool:
        todo = self._service.get(todo_id)
        dialog_parent = self if self.isVisible() else None
        dialog = self._editor_factory(todo, self._clock.today(), dialog_parent)
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.todo_update is None:
            return False
        self._service.update(todo_id, dialog.todo_update)
        self._after_change()
        return True

    def delete_todo(self, todo_id: int) -> bool:
        todo = self._service.get(todo_id)
        if not self._confirm_delete(todo_id, todo.content):
            return False
        self._service.delete(todo_id)
        self._after_change()
        return True

    def restore_todo(self, todo_id: int) -> None:
        self._service.restore(todo_id)
        self._after_change()

    def _after_change(self) -> None:
        self.refresh()
        self._on_changed()

    def _selected_id(self, widget: QListWidget) -> int | None:
        item = widget.currentItem()
        return None if item is None else int(item.data(Qt.ItemDataRole.UserRole))

    def _edit_selected(self, widget: QListWidget) -> None:
        todo_id = self._selected_id(widget)
        if todo_id is not None:
            self.open_editor(todo_id)

    def _delete_selected(self, widget: QListWidget) -> None:
        todo_id = self._selected_id(widget)
        if todo_id is not None:
            self.delete_todo(todo_id)

    def _restore_selected(self, widget: QListWidget) -> None:
        todo_id = self._selected_id(widget)
        if todo_id is not None:
            self.restore_todo(todo_id)

    def _complete_selected(self, widget: QListWidget) -> None:
        todo_id = self._selected_id(widget)
        if todo_id is not None:
            self._service.set_completed(todo_id, True)
            self._after_change()

    def _show_delete_confirmation(self, _todo_id: int, content: str) -> bool:
        parent = self if self.isVisible() else QApplication.activeWindow()
        if parent is not None and not parent.isVisible():
            parent = None
        result = QMessageBox.question(
            parent,
            "Delete Todo permanently?",
            f'Delete "{content}" permanently? This cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return result is QMessageBox.StandardButton.Yes
