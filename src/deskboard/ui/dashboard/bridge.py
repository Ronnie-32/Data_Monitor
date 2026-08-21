"""QWebChannel bridge for shell state and Dashboard Todo commands."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import QObject, Signal, Slot

from deskboard.app.modes import AppMode
from deskboard.infrastructure.clock import Clock, SystemClock
from deskboard.models.todo import Todo
from deskboard.presentation.todo_presenter import present_todos


class TodoServiceLike(Protocol):
    def add_quick(self, content: str) -> Todo: ...

    def set_completed(self, todo_id: int, completed: bool) -> Todo: ...

    def reorder(self, ordered_ids: list[int]) -> None: ...

    def get_dashboard_items(self) -> list[Todo]: ...


class DashboardBridge(QObject):
    shellReady = Signal()
    modeChanged = Signal(str)
    settingsRequested = Signal()
    todosChanged = Signal(list)
    todoEditorRequested = Signal(int)
    todoDeleteRequested = Signal(int)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        todo_service: TodoServiceLike | None = None,
        clock: Clock | None = None,
    ) -> None:
        super().__init__(parent)
        self._todo_service = todo_service
        self._clock = clock or SystemClock()
        self._mode = AppMode.INTERACTION

    @Slot()
    def notifyReady(self) -> None:  # noqa: N802
        self.shellReady.emit()
        self.publish_todos()

    @Slot()
    def openSettings(self) -> None:  # noqa: N802
        self.settingsRequested.emit()

    def publish_mode(self, mode: AppMode) -> None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        self._mode = mode
        self.modeChanged.emit(mode.value)

    @Slot(str)
    def addQuickTodo(self, content: str) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        assert self._todo_service is not None
        self._todo_service.add_quick(content)
        self.publish_todos()

    @Slot(int)
    def toggleTodo(self, todo_id: int) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        assert self._todo_service is not None
        current = next(
            (todo for todo in self._todo_service.get_dashboard_items() if todo.id == todo_id),
            None,
        )
        if current is None:
            raise LookupError(f"Todo {todo_id} is not available on the Dashboard")
        self._todo_service.set_completed(todo_id, not current.is_completed)
        self.publish_todos()

    @Slot("QVariantList")
    def reorderTodos(self, ordered_ids: list[object]) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        ids = [_todo_id(value) for value in ordered_ids]
        assert self._todo_service is not None
        self._todo_service.reorder(ids)
        self.publish_todos()

    @Slot(int)
    def openTodoEditor(self, todo_id: int) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        self.todoEditorRequested.emit(_todo_id(todo_id))

    @Slot(int)
    def requestDeleteTodo(self, todo_id: int) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        self.todoDeleteRequested.emit(_todo_id(todo_id))

    def publish_todos(self) -> None:
        if self._todo_service is None:
            self.todosChanged.emit([])
            return
        payload = present_todos(
            self._todo_service.get_dashboard_items(),
            today=self._clock.today(),
            now=self._clock.now(),
        )
        self.todosChanged.emit(payload)

    def _todo_commands_enabled(self) -> bool:
        return self._mode is AppMode.INTERACTION and self._todo_service is not None


def _todo_id(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Todo IDs must be integers")
    if value <= 0:
        raise ValueError("Todo IDs must be positive")
    return value
