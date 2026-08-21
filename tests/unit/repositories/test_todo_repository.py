from __future__ import annotations

import sqlite3
from datetime import date, datetime, time

import pytest

from deskboard.database.connection import connect_database
from deskboard.database.schema import migrate
from deskboard.repositories.todo_repository import TodoRepository

NOW = datetime(2026, 8, 21, 9, 30)


def make_repository(tmp_path) -> tuple[TodoRepository, sqlite3.Connection]:
    connection = connect_database(tmp_path / "deskboard.db")
    migrate(connection)
    return TodoRepository(connection), connection


def test_repository_round_trips_supported_fields_and_completion_semantics(tmp_path):
    repository, _connection = make_repository(tmp_path)

    todo = repository.create(
        content="Write report",
        deadline_date=date(2026, 8, 22),
        deadline_time=time(18, 0),
        planned_date=date(2026, 8, 21),
        planned_start_time=time(14, 0),
        planned_end_time=time(15, 0),
        display_order=4,
        now=NOW,
    )

    assert repository.get(todo.id) == todo
    assert todo.content == "Write report"
    assert todo.deadline_date == date(2026, 8, 22)
    assert todo.deadline_time == time(18, 0)
    assert todo.planned_date == date(2026, 8, 21)
    assert todo.planned_start_time == time(14, 0)
    assert todo.planned_end_time == time(15, 0)
    assert todo.completed_at is None
    assert todo.is_completed is False
    assert todo.created_at == NOW == todo.updated_at


def test_reorder_is_atomic_and_preserves_unselected_history_positions(tmp_path):
    repository, connection = make_repository(tmp_path)
    first = repository.create(content="first", display_order=0, now=NOW)
    hidden = repository.create(content="hidden", display_order=1, now=NOW)
    third = repository.create(content="third", display_order=2, now=NOW)
    repository.set_completed(hidden.id, NOW)

    repository.reorder([third.id, first.id])

    assert [todo.content for todo in repository.list_all()] == ["third", "hidden", "first"]
    before = [(todo.id, todo.display_order) for todo in repository.list_all()]
    connection.execute(
        f"CREATE TRIGGER reject_reorder BEFORE UPDATE OF display_order ON todos "
        f"WHEN OLD.id = {first.id} BEGIN SELECT RAISE(ABORT, 'stop'); END"
    )
    connection.commit()

    with pytest.raises(Exception, match="stop"):
        repository.reorder([first.id, third.id])

    assert [(todo.id, todo.display_order) for todo in repository.list_all()] == before


@pytest.mark.parametrize("ordered_ids", [[1, 1], [999]])
def test_reorder_rejects_duplicate_or_unknown_ids_without_changes(tmp_path, ordered_ids):
    repository, _connection = make_repository(tmp_path)
    todo = repository.create(content="only", display_order=0, now=NOW)

    with pytest.raises(ValueError):
        repository.reorder(ordered_ids)

    assert repository.list_all() == [todo]
