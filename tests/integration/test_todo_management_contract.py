from __future__ import annotations

import sqlite3
from datetime import date, datetime

from PySide6.QtWidgets import QApplication, QMessageBox

from deskboard.database.schema import migrate
from deskboard.infrastructure.clock import Clock
from deskboard.repositories.todo_repository import TodoRepository
from deskboard.services.todo_service import TodoService
from deskboard.ui.settings.todo_page import TodoPage
from deskboard.ui.settings.window import SettingsWindow


class FakeClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 8, 21, 12)

    def today(self) -> date:
        return date(2026, 8, 21)


def test_settings_todo_page_separates_restores_and_confirms_permanent_delete():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    service = TodoService(TodoRepository(connection), FakeClock())
    incomplete = service.add_quick("Incomplete")
    completed = service.add_quick("Completed")
    service.set_completed(completed.id, True)
    confirmations: list[tuple[int, str]] = []

    def confirm(todo_id: int, content: str) -> bool:
        confirmations.append((todo_id, content))
        return True

    page = TodoPage(service, FakeClock(), confirm_delete=confirm)
    page.refresh()

    assert page.incomplete_ids() == [incomplete.id]
    assert page.completed_ids() == [completed.id]

    page.restore_todo(completed.id)
    assert set(page.incomplete_ids()) == {incomplete.id, completed.id}
    assert page.completed_ids() == []

    service.set_completed(completed.id, True)
    page.refresh()
    page.delete_todo(completed.id)

    assert confirmations == [(completed.id, "Completed")]
    assert service.get_completed_history() == []
    assert {todo.id for todo in service.get_incomplete_items()} == {incomplete.id}
    page.close()
    connection.close()
    del app


def test_delete_is_cancelled_when_confirmation_is_declined():
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    service = TodoService(TodoRepository(connection), FakeClock())
    todo = service.add_quick("Keep me")
    page = TodoPage(service, FakeClock(), confirm_delete=lambda _id, _content: False)

    assert page.delete_todo(todo.id) is False
    assert service.get_incomplete_items()[0].id == todo.id
    page.close()
    connection.close()
    del app


def test_default_delete_confirmation_is_cancel_safe(monkeypatch):
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    service = TodoService(TodoRepository(connection), FakeClock())
    page = TodoPage(service, FakeClock())
    observed: list[tuple[object, str, QMessageBox.StandardButton]] = []

    def decline(parent, title, _text, _buttons, default_button):
        observed.append((parent, title, default_button))
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(QMessageBox, "question", decline)

    assert page._show_delete_confirmation(1, "Keep me") is False
    assert observed == [
        (None, "Delete Todo permanently?", QMessageBox.StandardButton.Cancel)
    ]
    page.close()
    connection.close()
    del app


def test_hidden_settings_delete_uses_top_level_confirmation_and_deletes(monkeypatch):
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    service = TodoService(TodoRepository(connection), FakeClock())
    todo = service.add_quick("Delete from Dashboard")
    page = TodoPage(service, FakeClock())
    observed_parents: list[object] = []

    def accept(parent, _title, _text, _buttons, _default_button):
        observed_parents.append(parent)
        return QMessageBox.StandardButton.Yes

    monkeypatch.setattr(QMessageBox, "question", accept)

    assert page.isVisible() is False
    assert page.delete_todo(todo.id) is True
    assert observed_parents == [None]
    assert service.get_incomplete_items() == []
    page.close()
    connection.close()
    del app


def test_settings_window_delete_route_uses_shared_service_when_window_is_hidden(monkeypatch):
    app = QApplication.instance() or QApplication([])
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    service = TodoService(TodoRepository(connection), FakeClock())
    todo = service.add_quick("Settings route")

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )
    window = SettingsWindow(
        lambda _mode: None,
        lambda: None,
        lambda: None,
        lambda: None,
        todo_service=service,
        clock=FakeClock(),
    )

    assert window.isVisible() is False
    assert window.request_delete_todo(todo.id) is True
    assert service.get_incomplete_items() == []
    window.close()
    connection.close()
    del app
