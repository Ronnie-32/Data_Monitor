from datetime import date, time

import pytest

from deskboard.ui.dialogs.todo_editor import build_todo_update

TODAY = date(2026, 8, 21)


def test_editor_requires_non_blank_content():
    with pytest.raises(ValueError, match="content"):
        build_todo_update(content="  ", today=TODAY)


def test_editor_defaults_deadline_date_when_only_time_is_enabled():
    update = build_todo_update(
        content="Submit report",
        today=TODAY,
        deadline_time=time(18, 30),
    )

    assert update.content == "Submit report"
    assert update.deadline_date == TODAY
    assert update.deadline_time == time(18, 30)


def test_editor_supports_planned_date_point_and_range_semantics():
    date_only = build_todo_update(
        content="Date only",
        today=TODAY,
        planned_date=date(2026, 8, 23),
    )
    point = build_todo_update(
        content="Point",
        today=TODAY,
        planned_start_time=time(9),
    )
    time_range = build_todo_update(
        content="Range",
        today=TODAY,
        planned_date=date(2026, 8, 24),
        planned_start_time=time(9),
        planned_end_time=time(10, 30),
    )

    assert (date_only.planned_date, date_only.planned_start_time) == (
        date(2026, 8, 23),
        None,
    )
    assert (point.planned_date, point.planned_start_time, point.planned_end_time) == (
        TODAY,
        time(9),
        None,
    )
    assert (time_range.planned_start_time, time_range.planned_end_time) == (
        time(9),
        time(10, 30),
    )


def test_editor_rejects_end_without_start_and_non_increasing_range():
    with pytest.raises(ValueError, match="requires.*start"):
        build_todo_update(
            content="Missing start",
            today=TODAY,
            planned_end_time=time(10),
        )
    with pytest.raises(ValueError, match="later"):
        build_todo_update(
            content="Bad range",
            today=TODAY,
            planned_start_time=time(10),
            planned_end_time=time(10),
        )
