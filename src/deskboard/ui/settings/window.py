"""Native eight-page Settings shell."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from deskboard.app.modes import AppMode

if TYPE_CHECKING:
    from deskboard.infrastructure.clock import Clock
    from deskboard.ui.settings.todo_page import TodoManagementService, TodoPage


class SettingsWindow(QMainWindow):
    PAGE_TITLES = (
        "General",
        "Profiles",
        "Weather",
        "Finance",
        "Todo",
        "Courses",
        "Data Status",
        "About",
    )

    def __init__(
        self,
        set_mode: Callable[[AppMode], None],
        show_dashboard: Callable[[], None],
        hide_dashboard: Callable[[], None],
        exit_application: Callable[[], None],
        *,
        todo_service: TodoManagementService | None = None,
        clock: Clock | None = None,
        on_todos_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._set_mode = set_mode
        self.todo_page: TodoPage | None = None
        self.setWindowTitle("DeskBoard Settings")
        self.resize(760, 520)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        root = QWidget(self)
        layout = QHBoxLayout(root)
        self.navigation = QListWidget(root)
        self.pages = QStackedWidget(root)
        self.navigation.setFixedWidth(150)
        for title in self.PAGE_TITLES:
            self.navigation.addItem(title)
            if title == "Todo" and todo_service is not None and clock is not None:
                from deskboard.ui.settings.todo_page import TodoPage

                self.todo_page = TodoPage(
                    todo_service,
                    clock,
                    self,
                    on_changed=on_todos_changed,
                )
                page = self.todo_page
            else:
                page = self._build_page(
                    title,
                    show_dashboard,
                    hide_dashboard,
                    exit_application,
                )
            self.pages.addWidget(page)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        layout.addWidget(self.navigation)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)

    def _build_page(
        self,
        title: str,
        show_dashboard: Callable[[], None],
        hide_dashboard: Callable[[], None],
        exit_application: Callable[[], None],
    ) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        heading = QLabel(title, page)
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(heading)
        if title == "General":
            layout.addWidget(QLabel("Dashboard visibility and shell mode", page))
            for label, callback in (
                ("Show Dashboard", show_dashboard),
                ("Hide Dashboard", hide_dashboard),
                ("Locked", lambda: self._set_mode(AppMode.LOCKED)),
                ("Interaction", lambda: self._set_mode(AppMode.INTERACTION)),
                ("Layout Edit", lambda: self._set_mode(AppMode.LAYOUT_EDIT)),
                ("Exit DeskBoard", exit_application),
            ):
                button = QPushButton(label, page)
                button.clicked.connect(callback)
                layout.addWidget(button)
            self.mode_label = QLabel(page)
            layout.addWidget(self.mode_label)
        else:
            layout.addWidget(QLabel("This page is a native shell for a later task.", page))
        layout.addStretch(1)
        return page

    def set_mode_state(self, mode: AppMode) -> None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        self.mode_label.setText(f"Current mode: {mode.value}")

    def open_todo_editor(self, todo_id: int) -> bool:
        if self.todo_page is None:
            return False
        return self.todo_page.open_editor(todo_id)

    def request_delete_todo(self, todo_id: int) -> bool:
        if self.todo_page is None:
            return False
        return self.todo_page.delete_todo(todo_id)

    def showEvent(self, event) -> None:  # noqa: N802
        if self.todo_page is not None:
            self.todo_page.refresh()
        super().showEvent(event)
