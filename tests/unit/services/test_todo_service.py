from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.infrastructure.clock import Clock
from deskboard.models.todo import TodoUpdate
from deskboard.repositories.todo_repository import TodoRepository
from deskboard.services.todo_service import TodoService


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 8, 21, 9, 30))


@pytest.fixture
def service(tmp_path, clock) -> TodoService:
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    return TodoService(TodoRepository(connection), clock)


def test_quick_add_is_content_only_trimmed_and_newest_is_top(service):
    first = service.add_quick(" first ")
    second = service.add_quick("second")

    assert first.content == "first"
    assert second.deadline_date is None
    assert second.deadline_time is None
    assert second.planned_date is None
    assert second.planned_start_time is None
    assert second.planned_end_time is None
    assert [todo.id for todo in service.get_dashboard_items()] == [second.id, first.id]
    with pytest.raises(ValueError, match="content"):
        service.add_quick("   ")


def test_agenda_quick_add_is_planned_for_today(clock):
    connection = connect_database(":memory:")
    migrate(connection)
    service = TodoService(TodoRepository(connection), clock)
    created = service.add_today("今天的日程")

    assert created.planned_date == clock.today()
    assert created.planned_start_time is None
    assert created.planned_end_time is None
    assert created.id in {item.id for item in service.get_for_agenda_date(clock.today())}


@pytest.mark.parametrize(
    ("update", "expected_date", "expected_time"),
    [
        (
            TodoUpdate(deadline_date=date(2026, 8, 25), deadline_time=time(18)),
            date(2026, 8, 25),
            time(18),
        ),
        (TodoUpdate(deadline_date=date(2026, 8, 25)), date(2026, 8, 25), None),
        (TodoUpdate(deadline_time=time(18)), date(2026, 8, 21), time(18)),
        (TodoUpdate(), None, None),
    ],
)
def test_deadline_legal_combinations_use_local_today(
    service, update, expected_date, expected_time
):
    todo = service.add_quick("deadline")

    updated = service.update(todo.id, update)

    assert updated.deadline_date == expected_date
    assert updated.deadline_time == expected_time


@pytest.mark.parametrize(
    ("update", "expected_date", "expected_start", "expected_end"),
    [
        (TodoUpdate(planned_date=date(2026, 8, 25)), date(2026, 8, 25), None, None),
        (
            TodoUpdate(planned_date=date(2026, 8, 25), planned_start_time=time(14)),
            date(2026, 8, 25),
            time(14),
            None,
        ),
        (
            TodoUpdate(
                planned_date=date(2026, 8, 25),
                planned_start_time=time(14),
                planned_end_time=time(15),
            ),
            date(2026, 8, 25),
            time(14),
            time(15),
        ),
        (TodoUpdate(planned_start_time=time(14)), date(2026, 8, 21), time(14), None),
    ],
)
def test_planned_legal_forms_use_local_today(
    service, update, expected_date, expected_start, expected_end
):
    todo = service.add_quick("planned")

    updated = service.update(todo.id, update)

    assert updated.planned_date == expected_date
    assert updated.planned_start_time == expected_start
    assert updated.planned_end_time == expected_end


@pytest.mark.parametrize(
    "update",
    [
        TodoUpdate(planned_end_time=time(15)),
        TodoUpdate(planned_start_time=time(15), planned_end_time=time(15)),
        TodoUpdate(planned_start_time=time(16), planned_end_time=time(15)),
    ],
)
def test_planned_range_validation_rejects_missing_or_non_later_end(service, update):
    todo = service.add_quick("invalid range")

    with pytest.raises(ValueError, match="planned"):
        service.update(todo.id, update)


def test_dashboard_includes_all_incomplete_and_only_completed_today(service, clock):
    overdue = service.add_quick("overdue deadline")
    overdue = service.update(overdue.id, TodoUpdate(deadline_date=date(2026, 8, 1)))
    past = service.update(
        service.add_quick("past planned").id,
        TodoUpdate(planned_date=date(2026, 8, 1)),
    )
    today = service.update(
        service.add_quick("today planned").id,
        TodoUpdate(planned_date=date(2026, 8, 21)),
    )
    future = service.update(
        service.add_quick("future planned").id,
        TodoUpdate(planned_date=date(2026, 9, 1)),
    )
    service.set_completed(today.id, True)

    assert {item.id for item in service.get_dashboard_items()} == {
        overdue.id,
        past.id,
        today.id,
        future.id,
    }
    clock.current = datetime(2026, 8, 22, 0, 1)
    assert today.id not in {item.id for item in service.get_dashboard_items()}


def test_completion_and_field_updates_never_change_manual_order(service):
    first = service.add_quick("first")
    middle = service.add_quick("middle")
    last = service.add_quick("last")
    original = [item.id for item in service.get_dashboard_items()]

    service.set_completed(middle.id, True)
    service.update(first.id, TodoUpdate(deadline_date=date(2026, 8, 1)))
    service.update(last.id, TodoUpdate(planned_date=date(2026, 9, 1)))

    assert [item.id for item in service.get_dashboard_items()] == original


def test_reorder_changes_only_requested_manual_sequence(service):
    first = service.add_quick("first")
    second = service.add_quick("second")
    third = service.add_quick("third")

    service.reorder([first.id, third.id, second.id])

    assert [item.id for item in service.get_dashboard_items()] == [first.id, third.id, second.id]


def test_incomplete_completed_restore_and_permanent_delete(service):
    keep = service.add_quick("keep")
    completed = service.add_quick("completed")

    completed = service.set_completed(completed.id, True)
    assert completed.is_completed
    assert [item.id for item in service.get_completed_history()] == [completed.id]
    assert keep.id not in {item.id for item in service.get_completed_history()}

    restored = service.restore(completed.id)
    assert restored.completed_at is None
    assert {item.id for item in service.get_dashboard_items()} == {keep.id, completed.id}
    assert service.get_completed_history() == []

    service.delete(completed.id)
    assert completed.id not in {item.id for item in service.get_dashboard_items()}
    with pytest.raises(LookupError):
        service.delete(completed.id)


def test_get_for_date_uses_planned_date_only_and_manual_order(service):
    deadline_only = service.update(
        service.add_quick("deadline only").id,
        TodoUpdate(deadline_date=date(2026, 8, 21)),
    )
    planned = service.update(
        service.add_quick("planned").id,
        TodoUpdate(planned_date=date(2026, 8, 21), planned_start_time=time(10)),
    )
    other_day = service.update(
        service.add_quick("other").id,
        TodoUpdate(planned_date=date(2026, 8, 22)),
    )

    items = service.get_for_date(date(2026, 8, 21))

    assert [item.id for item in items] == [planned.id]
    assert deadline_only.id not in {item.id for item in items}
    assert other_day.id not in {item.id for item in items}


def test_get_for_agenda_date_includes_planned_or_deadline_date(service):
    deadline_only = service.update(
        service.add_quick("deadline only").id,
        TodoUpdate(deadline_date=date(2026, 8, 21)),
    )
    planned = service.update(
        service.add_quick("planned").id,
        TodoUpdate(planned_date=date(2026, 8, 21)),
    )
    other_day = service.update(
        service.add_quick("other").id,
        TodoUpdate(deadline_date=date(2026, 8, 22)),
    )

    items = service.get_for_agenda_date(date(2026, 8, 21))

    assert [item.id for item in items] == [planned.id, deadline_only.id]
    assert other_day.id not in {item.id for item in items}


def test_service_uses_injected_clock_and_rejects_missing_ids(service, clock):
    typed_clock: Clock = clock
    assert typed_clock.today() == date(2026, 8, 21)
    todo = service.add_quick("clocked")
    assert todo.created_at == clock.current

    with pytest.raises(LookupError):
        service.update(999, TodoUpdate(content="missing"))
    with pytest.raises(LookupError):
        service.set_completed(999, True)
    with pytest.raises(LookupError):
        service.restore(999)
