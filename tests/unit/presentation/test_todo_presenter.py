from datetime import date, datetime, time

from deskboard.models.todo import Todo
from deskboard.presentation.todo_presenter import present_todo, present_todos


def make_todo(**overrides) -> Todo:
    values = {
        "id": 1,
        "content": "Prepare notes",
        "deadline_date": None,
        "deadline_time": None,
        "planned_date": None,
        "planned_start_time": None,
        "planned_end_time": None,
        "completed_at": None,
        "display_order": 3,
        "created_at": datetime(2026, 8, 20, 9),
        "updated_at": datetime(2026, 8, 20, 9),
    }
    values.update(overrides)
    return Todo(**values)


def test_present_todo_exposes_only_dashboard_owned_display_fields():
    view_model = present_todo(
        make_todo(
            deadline_date=date(2026, 8, 21),
            deadline_time=time(18, 30),
            planned_date=date(2026, 8, 22),
            planned_start_time=time(9),
            planned_end_time=time(10),
        ),
        today=date(2026, 8, 21),
        now=datetime(2026, 8, 21, 12),
    )

    assert view_model == {
        "id": 1,
        "content": "Prepare notes",
        "completed": False,
        "overdue": False,
        "deadlineText": "截止 08-21 18:30",
        "plannedText": "计划 08-22 09:00–10:00",
    }
    assert "display_order" not in view_model
    assert "completed_at" not in view_model


def test_completed_today_has_completed_state_without_strikethrough_flag():
    view_model = present_todo(
        make_todo(completed_at=datetime(2026, 8, 21, 10)),
        today=date(2026, 8, 21),
        now=datetime(2026, 8, 21, 12),
    )

    assert view_model["completed"] is True
    assert "strikethrough" not in view_model
    assert "textDecoration" not in view_model


def test_overdue_is_computed_in_python_for_incomplete_items_only():
    overdue = make_todo(deadline_date=date(2026, 8, 20))
    completed = make_todo(
        id=2,
        deadline_date=date(2026, 8, 20),
        completed_at=datetime(2026, 8, 21, 8),
    )

    payload = present_todos(
        [overdue, completed],
        today=date(2026, 8, 21),
        now=datetime(2026, 8, 21, 12),
    )

    assert payload[0]["overdue"] is True
    assert payload[1]["overdue"] is False

