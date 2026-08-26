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


def test_layout_round_trip_keeps_fixed_48_column_topology_when_window_resizes():
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


def test_runtime_default_layout_contains_all_widgets_without_overlap():
    state = default_layout_state(ProfileState())

    assert [widget.widget_key for widget in state.widgets] == [
        "todo",
        "today_agenda",
        "weather",
        "gold",
        "fx",
        "china_indices",
        "us_indices",
        "finance_overview",
    ]
    assert [(widget.x, widget.y, widget.w, widget.h) for widget in state.widgets] == [
        (0, 0, 24, 12),
        (24, 0, 24, 12),
        (0, 12, 48, 3),
        (0, 15, 12, 3),
        (12, 15, 12, 3),
        (24, 15, 12, 3),
        (36, 15, 12, 3),
        (0, 18, 48, 3),
    ]
    assert state.widgets[-1].visible is False


def test_runtime_default_layout_adds_missing_widgets_below_existing_profile_content():
    state = default_layout_state(
        ProfileState(widgets=(ProfileWidgetState("todo", True, 0, 0, 48, 32),))
    )

    assert state.widgets[0] == ProfileWidgetState("todo", True, 0, 0, 48, 32)
    assert all(widget.y >= 32 for widget in state.widgets[1:])
    assert {widget.widget_key for widget in state.widgets} == {
        "todo",
        "today_agenda",
        "weather",
        "gold",
        "fx",
        "china_indices",
        "us_indices",
        "finance_overview",
    }


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
    assert profile["columnCount"] == 48
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


def test_legacy_12_column_layout_is_scaled_to_the_48_column_topology():
    state = profile_state_from_layout(
        ProfileState(),
        {
            "columnCount": 12,
            "widgets": [
                {"widgetKey": "todo", "x": 1, "y": 2, "w": 5, "h": 3},
            ],
        },
    )

    assert state.widgets[0].x == 4
    assert state.widgets[0].y == 8
    assert state.widgets[0].w == 20
    assert state.widgets[0].h == 12
