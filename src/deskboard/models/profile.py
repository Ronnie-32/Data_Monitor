"""Profile domain values for visual and spatial Dashboard configuration."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from numbers import Real

PROFILE_WIDGET_KEYS = (
    "weather",
    "todo",
    "today_agenda",
    "gold",
    "fx",
    "china_indices",
    "us_indices",
    "finance_overview",
)

PROFILE_THEME_KEYS = (
    "mist_blue",
    "mint_breeze",
    "almond_sand",
    "lavender_cloud",
    "ocean_night",
    "graphite_night",
    "rose_dusk",
    "high_contrast",
    "terra_signal",
    "endfield_industrial",
    "starrail_astral",
    "wuthering_tide",
)
PROFILE_FONT_KEYS = (
    "system_ui",
    "yahei",
    "noto_sans",
    "source_han_sans",
    "source_han_serif",
)
DEFAULT_PROFILE_THEME_KEY = "mist_blue"
DEFAULT_PROFILE_FONT_KEY = "system_ui"
PROFILE_GRID_COLUMNS = 48
LEGACY_PROFILE_GRID_COLUMNS = 12
PROFILE_GRID_SCALE = PROFILE_GRID_COLUMNS // LEGACY_PROFILE_GRID_COLUMNS

DEFAULT_PROFILE_NAME = "Default"
MAX_USER_PROFILES = 8


@dataclass(frozen=True, slots=True)
class ProfileWidgetState:
    """Persisted state for one approved widget type."""

    widget_key: str
    visible: bool = True
    x: int = 0
    y: int = 0
    w: int = 1
    h: int = 1
    config: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.widget_key not in PROFILE_WIDGET_KEYS:
            raise ValueError(f"Unsupported Profile widget key: {self.widget_key}")
        if type(self.visible) is not bool:
            raise TypeError("Profile widget visible must be a bool")
        _validate_int(self.x, "Profile widget x", minimum=0)
        _validate_int(self.y, "Profile widget y", minimum=0)
        _validate_int(self.w, "Profile widget w", minimum=1, maximum=PROFILE_GRID_COLUMNS)
        _validate_int(self.h, "Profile widget h", minimum=1)
        if self.x + self.w > PROFILE_GRID_COLUMNS:
            raise ValueError(
                "Profile widget geometry must fit within the 48-column grid"
            )
        if not isinstance(self.config, Mapping):
            raise TypeError("Profile widget config must be a mapping")
        config = dict(self.config)
        try:
            json.dumps(config, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError) as error:
            raise ValueError("Profile widget config must be JSON-serializable") from error
        object.__setattr__(self, "config", config)

    @property
    def display_config(self) -> Mapping[str, object]:
        """Compatibility name for the widget-specific display configuration."""

        return self.config


@dataclass(frozen=True, slots=True)
class ProfileState:
    """Only the visual/spatial state that a Profile is allowed to own."""

    window_x: int | None = None
    window_y: int | None = None
    window_width: int | None = None
    window_height: int | None = None
    theme_key: str = DEFAULT_PROFILE_THEME_KEY
    font_key: str = DEFAULT_PROFILE_FONT_KEY
    panel_opacity: float = 1.0
    widgets: tuple[ProfileWidgetState, ...] = ()

    def __post_init__(self) -> None:
        _validate_optional_int(self.window_x, "Profile window x")
        _validate_optional_int(self.window_y, "Profile window y")
        _validate_optional_int(self.window_width, "Profile window width", minimum=1)
        _validate_optional_int(self.window_height, "Profile window height", minimum=1)
        if self.theme_key not in PROFILE_THEME_KEYS:
            raise ValueError(f"Unsupported Profile theme: {self.theme_key}")
        if self.font_key not in PROFILE_FONT_KEYS:
            raise ValueError(f"Unsupported Profile font: {self.font_key}")
        if isinstance(self.panel_opacity, bool) or not isinstance(self.panel_opacity, Real):
            raise TypeError("Profile panel opacity must be a number")
        if not 0 <= float(self.panel_opacity) <= 1:
            raise ValueError("Profile panel opacity must be between 0 and 1")
        widgets = tuple(self.widgets)
        if any(not isinstance(widget, ProfileWidgetState) for widget in widgets):
            raise TypeError("Profile widgets must be ProfileWidgetState values")
        widget_keys = [widget.widget_key for widget in widgets]
        if len(widget_keys) != len(set(widget_keys)):
            raise ValueError("Profile widget keys must be unique")
        object.__setattr__(self, "panel_opacity", float(self.panel_opacity))
        object.__setattr__(self, "widgets", widgets)

    @property
    def opacity(self) -> float:
        """Short name used by presentation callers."""

        return self.panel_opacity

    @property
    def widget_states(self) -> tuple[ProfileWidgetState, ...]:
        return self.widgets


@dataclass(frozen=True, slots=True)
class Profile:
    """A named Profile and its persisted visual state."""

    id: int
    name: str
    is_builtin: bool
    state: ProfileState
    created_at: datetime
    updated_at: datetime


def _validate_int(
    value: object, label: str, *, minimum: int | None = None, maximum: int | None = None
) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must be at most {maximum}")


def _validate_optional_int(
    value: object, label: str, *, minimum: int | None = None
) -> None:
    if value is not None:
        _validate_int(value, label, minimum=minimum)


# Clear aliases for callers that prefer the shorter terminology.
ProfileWidget = ProfileWidgetState
WidgetState = ProfileWidgetState
