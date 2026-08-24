from __future__ import annotations

from datetime import datetime

from deskboard.models.profile import ProfileState, ProfileWidgetState
from deskboard.presentation.layout_state import (
    GRID_COLUMN_COUNT,
    default_layout_state,
    layout_with_window_geometry,
    present_profile_state,
    profile_state_from_layout,
    serialize_layout,
)


def sample_state() -> ProfileState:
    return ProfileState(
        window_x=40,
        window_y=60,
        window_width=960,
        window_height=720,
        widgets=(
            ProfileWidgetState("todo", True, 0, 0, 5, 6),
            ProfileWidgetState("today_agenda", True, 5, 0, 7, 6),
        ),
    )


def test_layout_round_trip_keeps_fixed_12_column_topology_when_window_resizes():
    original = sample_state()
    saved = serialize_layout(original)

    resized = layout_with_window_geometry(saved, (100, 120, 1280, 800))
    restored = profile_state_from_layout(original, resized)

    assert resized["columnCount"] == GRID_COLUMN_COUNT
    assert restored.widgets == original.widgets
    assert (
        restored.window_x,
        restored.window_y,
        restored.window_width,
        restored.window_height,
    ) == (100, 120, 1280, 800)


def test_runtime_default_widgets_are_narrower_and_centered_with_room_between_them():
    state = default_layout_state(ProfileState())

    assert [(widget.x, widget.w) for widget in state.widgets] == [(1, 5), (6, 5)]


def test_profile_presentation_contains_only_dashboard_owned_layout_fields():
    state = sample_state()
    profile = present_profile_state(
        state,
        profile_id=3,
        name="Study",
        is_builtin=False,
        updated_at=datetime(2026, 8, 21, 9, 30),
    )

    assert profile["id"] == 3
    assert profile["name"] == "Study"
    assert profile["isBuiltin"] is False
    assert profile["columnCount"] == 12
    assert profile["widgets"][0] == {
        "widgetKey": "todo",
        "visible": True,
        "x": 0,
        "y": 0,
        "w": 5,
        "h": 6,
        "config": {},
    }
    assert "createdAt" not in profile
    assert "updatedAt" not in profile
