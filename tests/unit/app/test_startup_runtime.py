from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from deskboard.app.modes import AppMode
from deskboard.app.startup import (
    FIRST_RUN_COMPLETED_SETTING,
    LAST_MODE_SETTING,
    DayRolloverScheduler,
    determine_startup,
    recover_window_geometry,
)
from deskboard.infrastructure.clock import (
    milliseconds_until_next_local_midnight,
    next_local_midnight,
)


class FakeSettings:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self.values = dict(values or {})

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.values.get(key, default)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value


class FakeSignal:
    def __init__(self) -> None:
        self.callback = None

    def connect(self, callback) -> None:
        self.callback = callback

    def emit(self) -> None:
        if self.callback is not None:
            self.callback()


class FakeTimer:
    def __init__(self) -> None:
        self.timeout = FakeSignal()
        self.single_shot = False
        self.starts: list[int] = []
        self.stop_calls = 0

    def setSingleShot(self, enabled: bool) -> None:  # noqa: N802
        self.single_shot = enabled

    def start(self, milliseconds: int) -> None:
        self.starts.append(milliseconds)

    def stop(self) -> None:
        self.stop_calls += 1


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


def test_first_run_opens_settings_once_and_marks_the_run_complete():
    settings = FakeSettings()

    decision = determine_startup(settings)

    assert decision.mode is AppMode.INTERACTION
    assert decision.open_settings is True
    assert decision.dashboard_visible is True
    assert settings.values[FIRST_RUN_COMPLETED_SETTING] == "true"


def test_later_start_restores_daily_mode_but_never_restores_hidden_dashboard():
    settings = FakeSettings(
        {
            FIRST_RUN_COMPLETED_SETTING: "true",
            LAST_MODE_SETTING: AppMode.LOCKED.value,
            "dashboard.visible": "false",
        }
    )

    decision = determine_startup(settings)

    assert decision.mode is AppMode.LOCKED
    assert decision.open_settings is False
    assert decision.dashboard_visible is True


def test_layout_edit_is_recovered_as_interaction_after_restart():
    settings = FakeSettings(
        {
            FIRST_RUN_COMPLETED_SETTING: "true",
            LAST_MODE_SETTING: AppMode.LAYOUT_EDIT.value,
        }
    )

    assert determine_startup(settings).mode is AppMode.INTERACTION


def test_day_rollover_scheduler_uses_one_local_midnight_timer():
    clock = FakeClock(datetime(2026, 8, 25, 23, 59, 58))
    timer = FakeTimer()
    rollovers: list[date] = []
    scheduler = DayRolloverScheduler(clock, lambda: rollovers.append(clock.today()), timer=timer)

    scheduler.start()

    assert timer.single_shot is True
    assert len(timer.starts) == 1
    assert timer.starts[0] > 0

    clock.current = datetime(2026, 8, 26, 0, 0, 1)
    timer.timeout.emit()

    assert rollovers == [date(2026, 8, 26)]
    assert len(timer.starts) == 2

    scheduler.stop()
    assert timer.stop_calls == 1


def test_clock_rollover_interval_uses_the_next_naive_local_midnight():
    current = datetime(2026, 8, 25, 23, 59, 58, 500000)

    assert next_local_midnight(current) == datetime(2026, 8, 26)
    assert milliseconds_until_next_local_midnight(current) == 1500


def test_fully_offscreen_geometry_is_clamped_to_the_primary_work_area():
    assert recover_window_geometry((2000, 100, 400, 300), (0, 0, 1920, 1080)) == (
        1520,
        100,
        400,
        300,
    )
    assert recover_window_geometry((-500, -400, 400, 300), (0, 0, 1920, 1080)) == (
        0,
        0,
        400,
        300,
    )


def test_partially_visible_geometry_is_not_repositioned():
    geometry = (1800, 100, 400, 300)

    assert recover_window_geometry(geometry, (0, 0, 1920, 1080)) == geometry
