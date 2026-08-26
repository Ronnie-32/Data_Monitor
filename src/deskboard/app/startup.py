"""Startup decisions and low-frequency local-day runtime scheduling."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from deskboard.app.modes import AppMode
from deskboard.infrastructure.clock import milliseconds_until_next_local_midnight

FIRST_RUN_COMPLETED_SETTING = "startup.first_run_completed"
LAST_MODE_SETTING = "startup.last_mode"


class StartupSettingsLike(Protocol):
    def get(self, key: str, default: str | None = None) -> str | None: ...

    def set(self, key: str, value: str) -> None: ...


class TimerSignalLike(Protocol):
    def connect(self, callback: Callable[[], None]) -> object: ...


class TimerLike(Protocol):
    timeout: TimerSignalLike

    def setSingleShot(self, enabled: bool) -> None: ...  # noqa: N802

    def start(self, milliseconds: int) -> None: ...

    def stop(self) -> None: ...


class DayRolloverSchedulerLike(Protocol):
    def start(self) -> None: ...

    def stop(self) -> None: ...


@dataclass(frozen=True, slots=True)
class StartupDecision:
    mode: AppMode
    open_settings: bool
    dashboard_visible: bool


def determine_startup(settings: StartupSettingsLike | None) -> StartupDecision:
    """Resolve one launch without restoring a hidden Dashboard state."""

    if settings is None:
        return StartupDecision(AppMode.INTERACTION, False, True)

    first_run = _is_first_run(settings.get(FIRST_RUN_COMPLETED_SETTING))
    raw_mode = settings.get(LAST_MODE_SETTING)
    try:
        mode = AppMode(raw_mode) if raw_mode is not None else AppMode.INTERACTION
    except ValueError:
        mode = AppMode.INTERACTION
    if mode is AppMode.LAYOUT_EDIT:
        mode = AppMode.INTERACTION

    if first_run:
        settings.set(FIRST_RUN_COMPLETED_SETTING, "true")
    return StartupDecision(mode, first_run, True)


def remember_mode(settings: StartupSettingsLike | None, mode: AppMode) -> None:
    """Persist the last daily/layout mode through the SQLite-backed settings."""

    if settings is not None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        settings.set(LAST_MODE_SETTING, mode.value)


def is_fully_offscreen(
    geometry: tuple[int, int, int, int],
    work_area: tuple[int, int, int, int],
) -> bool:
    """Return whether a rectangle has no intersection with the work area."""

    x, y, width, height = geometry
    area_x, area_y, area_width, area_height = work_area
    return (
        x + width <= area_x
        or x >= area_x + area_width
        or y + height <= area_y
        or y >= area_y + area_height
    )


def recover_window_geometry(
    geometry: tuple[int, int, int, int],
    work_area: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    """Move only fully off-screen geometry into the primary work area.

    A partially visible Dashboard is intentionally left untouched.  The
    function changes position only; V1 does not resize a user's Profile or
    turn this recovery into multi-monitor layout management.
    """

    if not is_fully_offscreen(geometry, work_area):
        return geometry

    x, y, width, height = geometry
    area_x, area_y, area_width, area_height = work_area
    maximum_x = area_x + max(area_width - width, 0)
    maximum_y = area_y + max(area_height - height, 0)
    return (
        min(max(x, area_x), maximum_x),
        min(max(y, area_y), maximum_y),
        width,
        height,
    )


class DayRolloverScheduler:
    """Schedule one Qt timer for each Windows-local midnight."""

    def __init__(
        self,
        clock,
        callback: Callable[[], None],
        *,
        timer: TimerLike | None = None,
    ) -> None:
        if timer is None:
            from PySide6.QtCore import QTimer

            timer = QTimer()
        self._clock = clock
        self._callback = callback
        self._timer = timer
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._started = False
        self._last_date: date | None = None

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._last_date = self._clock.today()
        self._schedule_next_midnight()

    def stop(self) -> None:
        self._started = False
        self._timer.stop()

    def _schedule_next_midnight(self) -> None:
        if self._started:
            milliseconds = milliseconds_until_next_local_midnight(self._clock.now())
            # A coarse timer may wake slightly early.  Avoid a tight loop if
            # that happens in the final millisecond before the date changes.
            if self._last_date == self._clock.today():
                milliseconds = max(milliseconds, 1_000)
            self._timer.start(milliseconds)

    def _on_timeout(self) -> None:
        if not self._started:
            return
        current_date = self._clock.today()
        if self._last_date != current_date:
            self._last_date = current_date
            self._callback()
        self._schedule_next_midnight()


def _is_first_run(value: str | None) -> bool:
    return value is None or value.strip().casefold() not in {"1", "true", "yes", "on"}
