"""Dashboard-owned serialization and validation for the fixed GridStack layout."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime

from deskboard.models.profile import (
    LEGACY_PROFILE_GRID_COLUMNS,
    PROFILE_GRID_COLUMNS,
    PROFILE_GRID_SCALE,
    PROFILE_WIDGET_KEYS,
    ProfileState,
    ProfileWidgetState,
)

GRID_COLUMN_COUNT = PROFILE_GRID_COLUMNS

_DEFAULT_WIDGET_LAYOUT = (
    ProfileWidgetState("todo", True, 0, 0, 24, 12),
    ProfileWidgetState("today_agenda", True, 24, 0, 24, 12),
    ProfileWidgetState("weather", True, 0, 12, 48, 3),
    ProfileWidgetState("gold", True, 0, 15, 12, 3),
    ProfileWidgetState("fx", True, 12, 15, 12, 3),
    ProfileWidgetState("china_indices", True, 24, 15, 12, 3),
    ProfileWidgetState("us_indices", True, 36, 15, 12, 3),
    # The category cards already cover the enabled finance items. Keep the
    # combined view available in Layout Edit, but do not repeat it by default.
    ProfileWidgetState("finance_overview", False, 0, 18, 48, 3),
)


class LayoutStateError(ValueError):
    """Raised when a Web layout payload is outside the approved topology."""


def serialize_layout(state: ProfileState) -> dict[str, object]:
    """Return the JSON-safe layout portion of a Profile state."""

    if not isinstance(state, ProfileState):
        raise TypeError("state must be a ProfileState")
    return {
        "columnCount": GRID_COLUMN_COUNT,
        "window": _window_payload(state),
        "widgets": [_widget_payload(widget) for widget in state.widgets],
    }


def present_profile_state(
    state: ProfileState,
    *,
    profile_id: int | None = None,
    name: str | None = None,
    is_builtin: bool | None = None,
    updated_at: datetime | None = None,
) -> dict[str, object]:
    """Present a Profile without exposing SQLite rows or timestamps."""

    del updated_at  # Timestamps are persistence details, not Dashboard state.
    payload: dict[str, object] = serialize_layout(state)
    payload.update(
        {
            "id": profile_id,
            "name": name,
            "isBuiltin": is_builtin,
            "themeKey": state.theme_key,
            "fontKey": state.font_key,
            "panelOpacity": state.panel_opacity,
        }
    )
    return payload


def layout_with_window_geometry(
    layout: Mapping[str, object], geometry: tuple[int, int, int, int]
) -> dict[str, object]:
    """Copy a Web layout and replace only its native outer-window geometry."""

    _validate_geometry(geometry)
    result = dict(layout)
    result["window"] = {
        "x": geometry[0],
        "y": geometry[1],
        "width": geometry[2],
        "height": geometry[3],
    }
    return result


def profile_state_from_layout(
    base_state: ProfileState,
    layout: Mapping[str, object],
) -> ProfileState:
    """Merge one saved Web layout into the current visual Profile state."""

    if not isinstance(base_state, ProfileState):
        raise TypeError("base_state must be a ProfileState")
    if not isinstance(layout, Mapping):
        raise TypeError("layout must be a mapping")
    column_count = layout.get("columnCount", GRID_COLUMN_COUNT)
    if column_count not in (LEGACY_PROFILE_GRID_COLUMNS, GRID_COLUMN_COUNT):
        raise LayoutStateError("Dashboard layout must use exactly 48 columns")
    scale = PROFILE_GRID_SCALE if column_count == LEGACY_PROFILE_GRID_COLUMNS else 1

    raw_widgets = layout.get("widgets")
    if not isinstance(raw_widgets, Sequence) or isinstance(raw_widgets, (str, bytes)):
        raise LayoutStateError("Dashboard layout widgets must be a list")
    base_by_key = {widget.widget_key: widget for widget in base_state.widgets}
    widgets: list[ProfileWidgetState] = []
    seen: set[str] = set()
    for raw_widget in raw_widgets:
        if not isinstance(raw_widget, Mapping):
            raise LayoutStateError("Dashboard layout widget must be an object")
        widget_key = raw_widget.get("widgetKey", raw_widget.get("widget_key"))
        if not isinstance(widget_key, str) or widget_key not in PROFILE_WIDGET_KEYS:
            raise LayoutStateError(f"Unsupported Dashboard widget key: {widget_key}")
        if widget_key in seen:
            raise LayoutStateError(f"Duplicate Dashboard widget key: {widget_key}")
        seen.add(widget_key)
        previous = base_by_key.get(widget_key)
        try:
            visible = raw_widget.get("visible", previous.visible if previous else True)
            if type(visible) is not bool:
                raise TypeError("visible must be a bool")
            x = _scaled_layout_int(raw_widget, "x", previous.x if previous else 0, scale)
            y = _scaled_layout_int(raw_widget, "y", previous.y if previous else 0, scale)
            w = _scaled_layout_int(raw_widget, "w", previous.w if previous else 1, scale)
            h = _scaled_layout_int(raw_widget, "h", previous.h if previous else 1, scale)
            config = raw_widget.get("config", previous.config if previous else {})
            widgets.append(
                ProfileWidgetState(
                    widget_key=widget_key,
                    visible=visible,
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                    config=config if isinstance(config, Mapping) else {},
                )
            )
        except (TypeError, ValueError) as error:
            raise LayoutStateError(f"Invalid geometry for Dashboard widget {widget_key}") from error

    # Keep approved widget state that is not rendered by this task's current
    # Dashboard shell; later widget tasks can expose it without losing data on
    # an earlier layout save.
    widgets.extend(widget for widget in base_state.widgets if widget.widget_key not in seen)

    window = layout.get("window")
    window_values = (
        _window_values(window) if window is not None else _state_window_values(base_state)
    )
    return ProfileState(
        window_x=window_values[0],
        window_y=window_values[1],
        window_width=window_values[2],
        window_height=window_values[3],
        theme_key=base_state.theme_key,
        font_key=base_state.font_key,
        panel_opacity=base_state.panel_opacity,
        widgets=tuple(widgets),
    )


def default_layout_state(base_state: ProfileState | None = None) -> ProfileState:
    """Return runtime defaults for the current Dashboard widget shell."""

    base = base_state or ProfileState()
    widgets = list(base.widgets)
    existing_keys = {widget.widget_key for widget in widgets}
    for default_widget in _DEFAULT_WIDGET_LAYOUT:
        if default_widget.widget_key in existing_keys:
            continue
        placed = default_widget
        while any(_widgets_overlap(placed, widget) for widget in widgets):
            placed = replace(placed, y=placed.y + 1)
        widgets.append(placed)
        existing_keys.add(placed.widget_key)
    return ProfileState(
        window_x=base.window_x,
        window_y=base.window_y,
        window_width=base.window_width,
        window_height=base.window_height,
        theme_key=base.theme_key,
        font_key=base.font_key,
        panel_opacity=base.panel_opacity,
        widgets=tuple(widgets or _DEFAULT_WIDGET_LAYOUT),
    )


def _widgets_overlap(left: ProfileWidgetState, right: ProfileWidgetState) -> bool:
    return (
        left.x < right.x + right.w
        and left.x + left.w > right.x
        and left.y < right.y + right.h
        and left.y + left.h > right.y
    )


def _scaled_layout_int(
    raw_widget: Mapping[str, object],
    key: str,
    fallback: int,
    scale: int,
) -> int:
    value = _layout_int(raw_widget.get(key, fallback), key)
    return value * scale if key in raw_widget else value


def _widget_payload(widget: ProfileWidgetState) -> dict[str, object]:
    return {
        "widgetKey": widget.widget_key,
        "visible": widget.visible,
        "x": widget.x,
        "y": widget.y,
        "w": widget.w,
        "h": widget.h,
        "config": dict(widget.config),
    }


def _window_payload(state: ProfileState) -> dict[str, int | None]:
    return {
        "x": state.window_x,
        "y": state.window_y,
        "width": state.window_width,
        "height": state.window_height,
    }


def _state_window_values(
    state: ProfileState,
) -> tuple[int | None, int | None, int | None, int | None]:
    return state.window_x, state.window_y, state.window_width, state.window_height


def _window_values(value: object) -> tuple[int, int, int, int]:
    if not isinstance(value, Mapping):
        raise LayoutStateError("Dashboard window geometry must be an object")
    values = tuple(
        _layout_int(value.get(key), key)
        for key in ("x", "y", "width", "height")
    )
    _validate_geometry(values)
    return values  # type: ignore[return-value]


def _validate_geometry(value: tuple[object, object, object, object]) -> None:
    x, y, width, height = value
    _layout_int(x, "window x")
    _layout_int(y, "window y")
    if _layout_int(width, "window width") < 1:
        raise LayoutStateError("Dashboard window width must be positive")
    if _layout_int(height, "window height") < 1:
        raise LayoutStateError("Dashboard window height must be positive")


def _layout_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"Dashboard layout {label} must be an integer")
    return value
