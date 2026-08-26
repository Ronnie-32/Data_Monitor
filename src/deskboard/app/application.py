"""DeskBoard application-shell lifecycle ownership."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from deskboard.app.modes import AppMode
from deskboard.app.startup import (
    DayRolloverSchedulerLike,
    StartupSettingsLike,
    determine_startup,
    remember_mode,
)


class QtApplicationLike(Protocol):
    def setQuitOnLastWindowClosed(self, enabled: bool) -> None: ...  # noqa: N802

    def exec(self) -> int: ...

    def quit(self) -> None: ...


class DashboardLike(Protocol):
    def show(self) -> None: ...

    def hide(self) -> None: ...

    def isVisible(self) -> bool: ...  # noqa: N802

    def set_mode(self, mode: AppMode) -> None: ...


class SettingsLike(Protocol):
    def show(self) -> None: ...

    def close(self) -> None: ...

    def raise_(self) -> None: ...

    def activateWindow(self) -> None: ...  # noqa: N802

    def set_mode_state(self, mode: AppMode) -> None: ...

    def open_todo_editor(self, todo_id: int) -> bool: ...

    def request_delete_todo(self, todo_id: int) -> bool: ...


SettingsFactory = Callable[
    [Callable[[AppMode], None], Callable[[], None], Callable[[], None], Callable[[], None]],
    SettingsLike,
]


class TrayLike(Protocol):
    def show(self) -> None: ...

    def hide(self) -> None: ...

    def sync_dashboard_visibility(self, visible: bool) -> None: ...


class InstanceGuardLike(Protocol):
    def close(self) -> None: ...


TrayFactory = Callable[
    [
        Callable[[], None],
        Callable[[], None],
        Callable[[], None],
        Callable[[], None],
        Callable[[], None],
    ],
    TrayLike,
]


class DeskBoardApplication:
    """Own the one Dashboard and optional native Settings window."""

    def __init__(
        self,
        qt_application: QtApplicationLike,
        *,
        dashboard_factory: Callable[[], DashboardLike] | None = None,
        settings_factory: SettingsFactory | None = None,
        tray_factory: TrayFactory | None = None,
        instance_guard: InstanceGuardLike,
        startup_settings: StartupSettingsLike | None = None,
        day_rollover_scheduler: DayRolloverSchedulerLike | None = None,
    ) -> None:
        self.qt_application = qt_application
        self.instance_guard = instance_guard
        self.qt_application.setQuitOnLastWindowClosed(False)
        self._dashboard_factory = dashboard_factory or self._default_dashboard_factory
        self._settings_factory = settings_factory or self._default_settings_factory
        self._startup_settings = startup_settings
        self._day_rollover_scheduler = day_rollover_scheduler
        self.dashboard = self._dashboard_factory()
        self._settings: SettingsLike | None = None
        self._mode = AppMode.INTERACTION
        self._started = False
        self._exiting = False
        selected_tray_factory = tray_factory or self._default_tray_factory
        self.tray = selected_tray_factory(
            self.toggle_dashboard,
            lambda: self.set_mode(AppMode.LOCKED),
            lambda: self.set_mode(AppMode.INTERACTION),
            self.show_settings,
            self.exit,
        )
        bridge = getattr(self.dashboard, "bridge", None)
        if bridge is not None:
            bridge.settingsRequested.connect(self.show_settings)
            bridge.todoEditorRequested.connect(self.open_todo_editor)
            bridge.todoDeleteRequested.connect(self.request_delete_todo)

    @staticmethod
    def _default_dashboard_factory() -> DashboardLike:
        from deskboard.ui.dashboard.window import DashboardWindow

        return DashboardWindow()

    @staticmethod
    def _default_settings_factory(
        set_mode: Callable[[AppMode], None],
        show_dashboard: Callable[[], None],
        hide_dashboard: Callable[[], None],
        exit_application: Callable[[], None],
    ) -> SettingsLike:
        from deskboard.ui.settings.window import SettingsWindow

        return SettingsWindow(
            set_mode,
            show_dashboard,
            hide_dashboard,
            exit_application,
        )

    @staticmethod
    def _default_tray_factory(
        toggle_dashboard: Callable[[], None],
        set_locked: Callable[[], None],
        set_interaction: Callable[[], None],
        show_settings: Callable[[], None],
        exit_application: Callable[[], None],
    ) -> TrayLike:
        from deskboard.ui.tray.tray_icon import TrayIcon

        return TrayIcon(
            toggle_dashboard,
            set_locked,
            set_interaction,
            show_settings,
            exit_application,
        )

    @property
    def mode(self) -> AppMode:
        return self._mode

    @property
    def settings(self) -> SettingsLike:
        if self._settings is None:
            self._settings = self._settings_factory(
                self.set_mode,
                self.show_dashboard,
                self.hide_dashboard,
                self.exit,
            )
        return self._settings

    def start(self, *, open_settings: bool | None = None) -> None:
        """Show the single Dashboard and apply the persisted launch policy."""
        if not self._started:
            decision = determine_startup(self._startup_settings)
            should_open_settings = (
                decision.open_settings if open_settings is None else open_settings
            )
            self.set_mode(decision.mode)
            self.dashboard.show()
            self.tray.sync_dashboard_visibility(True)
            self.tray.show()
            if self._day_rollover_scheduler is not None:
                self._day_rollover_scheduler.start()
            self._started = True
        else:
            should_open_settings = bool(open_settings)
        if should_open_settings:
            self.show_settings()

    def run(self) -> int:
        return self.qt_application.exec()

    def set_mode(self, mode: AppMode) -> None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        self._mode = mode
        remember_mode(self._startup_settings, mode)
        self.dashboard.set_mode(mode)
        if self._settings is not None:
            self._settings.set_mode_state(mode)

    def show_dashboard(self) -> None:
        self.dashboard.show()
        self.tray.sync_dashboard_visibility(True)

    def hide_dashboard(self) -> None:
        self.dashboard.hide()
        self.tray.sync_dashboard_visibility(False)

    def toggle_dashboard(self) -> None:
        if self.dashboard.isVisible():
            self.hide_dashboard()
        else:
            self.show_dashboard()

    def show_settings(self) -> None:
        settings = self.settings
        settings.set_mode_state(self._mode)
        settings.show()
        settings.raise_()
        settings.activateWindow()

    def close_settings(self) -> None:
        if self._settings is not None:
            self._settings.close()

    def open_todo_editor(self, todo_id: int) -> bool:
        return self.settings.open_todo_editor(todo_id)

    def request_delete_todo(self, todo_id: int) -> bool:
        return self.settings.request_delete_todo(todo_id)

    def exit(self) -> None:
        if self._exiting:
            return
        self._exiting = True
        if self._day_rollover_scheduler is not None:
            self._day_rollover_scheduler.stop()
        self.instance_guard.close()
        self.close_settings()
        self.dashboard.hide()
        self.tray.hide()
        self.qt_application.quit()

    def __repr__(self) -> str:
        return f"DeskBoardApplication(mode={self._mode.value!r}, started={self._started!r})"


def as_qt_application(value: Any) -> QtApplicationLike:
    """Narrow a QApplication instance without importing Qt in this module."""
    return value
