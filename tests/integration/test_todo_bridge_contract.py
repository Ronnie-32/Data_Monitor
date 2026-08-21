from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from deskboard.app.modes import AppMode
from deskboard.models.todo import Todo
from deskboard.ui.dashboard.bridge import DashboardBridge


def todo(todo_id: int, *, completed: bool = False) -> Todo:
    timestamp = datetime(2026, 8, 21, 9)
    return Todo(
        id=todo_id,
        content=f"Todo {todo_id}",
        deadline_date=None,
        deadline_time=None,
        planned_date=None,
        planned_start_time=None,
        planned_end_time=None,
        completed_at=timestamp if completed else None,
        display_order=todo_id,
        created_at=timestamp,
        updated_at=timestamp,
    )


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 21, 12)

    def today(self) -> date:
        return date(2026, 8, 21)


class FakeTodoService:
    def __init__(self) -> None:
        self.items = [todo(1), todo(2, completed=True)]
        self.calls: list[tuple[object, ...]] = []

    def add_quick(self, content: str) -> Todo:
        self.calls.append(("add", content))
        created = todo(3)
        self.items.insert(0, created)
        return created

    def set_completed(self, todo_id: int, completed: bool) -> Todo:
        self.calls.append(("complete", todo_id, completed))
        current = next(item for item in self.items if item.id == todo_id)
        replacement = todo(todo_id, completed=completed)
        self.items[self.items.index(current)] = replacement
        return replacement

    def reorder(self, ordered_ids: list[int]) -> None:
        self.calls.append(("reorder", ordered_ids))
        by_id = {item.id: item for item in self.items}
        self.items = [by_id[item_id] for item_id in ordered_ids]

    def get_dashboard_items(self) -> list[Todo]:
        return list(self.items)


def test_todo_commands_delegate_once_and_emit_refreshed_presented_state():
    service = FakeTodoService()
    bridge = DashboardBridge(todo_service=service, clock=FakeClock())
    events: list[list[dict[str, object]]] = []
    bridge.todosChanged.connect(events.append)

    bridge.addQuickTodo("new")
    bridge.toggleTodo(1)
    bridge.reorderTodos([2, 1, 3])

    assert service.calls == [
        ("add", "new"),
        ("complete", 1, True),
        ("reorder", [2, 1, 3]),
    ]
    assert len(events) == 3
    assert [item["id"] for item in events[-1]] == [2, 1, 3]
    assert set(events[-1][0]) == {
        "id",
        "content",
        "completed",
        "overdue",
        "deadlineText",
        "plannedText",
    }


def test_todo_commands_are_gated_to_interaction_mode():
    service = FakeTodoService()
    bridge = DashboardBridge(todo_service=service, clock=FakeClock())

    for mode in (AppMode.LOCKED, AppMode.LAYOUT_EDIT):
        bridge.publish_mode(mode)
        bridge.addQuickTodo("blocked")
        bridge.toggleTodo(1)
        bridge.reorderTodos([2, 1])

    assert service.calls == []


def test_ready_publishes_current_todos_and_bridge_has_no_persistence_logic():
    service = FakeTodoService()
    bridge = DashboardBridge(todo_service=service, clock=FakeClock())
    events: list[list[dict[str, object]]] = []
    bridge.todosChanged.connect(events.append)

    bridge.notifyReady()

    assert [item["id"] for item in events[-1]] == [1, 2]
    assert not hasattr(bridge, "_connection")
    assert not hasattr(bridge, "_repository")


def test_dashboard_todo_assets_use_bridge_commands_and_mode_gating():
    web_root = Path("src/deskboard/ui/dashboard/web")
    html = (web_root / "index.html").read_text(encoding="utf-8")
    javascript = (web_root / "js/widgets/todo.js").read_text(encoding="utf-8")
    css = (web_root / "css/widgets.css").read_text(encoding="utf-8")

    assert 'type="module"' in html
    assert "./js/widgets/todo.js" in html
    assert "./css/widgets.css" in html
    for command in ("addQuickTodo", "toggleTodo", "reorderTodos"):
        assert command in javascript
    assert 'dataset.mode === "interaction"' in javascript
    assert "Edit details" in html
    assert "Mark incomplete" in html
    assert "Delete" in html
    assert "overflow-y: auto" in css
    assert ".todo-item.is-completed" in css
    assert "text-decoration: line-through" not in css


def test_production_window_and_entrypoint_wire_todo_service_into_bridge():
    window_source = Path("src/deskboard/ui/dashboard/window.py").read_text(encoding="utf-8")
    main_source = Path("src/deskboard/main.py").read_text(encoding="utf-8")

    assert "todo_service=todo_service" in window_source
    assert "TodoService(TodoRepository(connection), clock)" in main_source
    assert "dashboard_factory=" in main_source
