"""DeskBoard application-shell lifecycle ownership."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from deskboard.app.modes import AppMode


class QtApplicationLike(Protocol):
    def setQuitOnLastWindowClosed(self, enabled: bool) -> None: ...  # noqa: N802

    def exec(self) -> int: ...


class DashboardLike(Protocol):
    def show(self) -> None: ...

    def hide(self) -> None: ...

    def set_mode(self, mode: AppMode) -> None: ...


class SettingsLike(Protocol):
    def show(self) -> None: ...

    def close(self) -> None: ...

    def raise_(self) -> None: ...

    def activateWindow(self) -> None: ...  # noqa: N802

    def set_mode_state(self, mode: AppMode) -> None: ...


SettingsFactory = Callable[
    [Callable[[AppMode], None], Callable[[], None], Callable[[], None]],
    SettingsLike,
]


class DeskBoardApplication:
    """Own the one Dashboard and optional native Settings window."""

    def __init__(
        self,
        qt_application: QtApplicationLike,
        *,
        dashboard_factory: Callable[[], DashboardLike] | None = None,
        settings_factory: SettingsFactory | None = None,
    ) -> None:
        self.qt_application = qt_application
        self.qt_application.setQuitOnLastWindowClosed(False)
        self._dashboard_factory = dashboard_factory or self._default_dashboard_factory
        self._settings_factory = settings_factory or self._default_settings_factory
        self.dashboard = self._dashboard_factory()
        self._settings: SettingsLike | None = None
        self._mode = AppMode.INTERACTION
        self._started = False
        bridge = getattr(self.dashboard, "bridge", None)
        if bridge is not None:
            bridge.settingsRequested.connect(self.show_settings)

    @staticmethod
    def _default_dashboard_factory() -> DashboardLike:
        from deskboard.ui.dashboard.window import DashboardWindow

        return DashboardWindow()

    @staticmethod
    def _default_settings_factory(
        set_mode: Callable[[AppMode], None],
        show_dashboard: Callable[[], None],
        hide_dashboard: Callable[[], None],
    ) -> SettingsLike:
        from deskboard.ui.settings.window import SettingsWindow

        return SettingsWindow(set_mode, show_dashboard, hide_dashboard)

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
            )
        return self._settings

    def start(self, *, open_settings: bool = False) -> None:
        """Show the single Dashboard in the legal startup mode."""
        if not self._started:
            self.set_mode(AppMode.INTERACTION)
            self.dashboard.show()
            self._started = True
        if open_settings:
            self.show_settings()

    def run(self) -> int:
        return self.qt_application.exec()

    def set_mode(self, mode: AppMode) -> None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        self._mode = mode
        self.dashboard.set_mode(mode)
        if self._settings is not None:
            self._settings.set_mode_state(mode)

    def show_dashboard(self) -> None:
        self.dashboard.show()

    def hide_dashboard(self) -> None:
        self.dashboard.hide()

    def show_settings(self) -> None:
        settings = self.settings
        settings.set_mode_state(self._mode)
        settings.show()
        settings.raise_()
        settings.activateWindow()

    def close_settings(self) -> None:
        if self._settings is not None:
            self._settings.close()

    def __repr__(self) -> str:
        return f"DeskBoardApplication(mode={self._mode.value!r}, started={self._started!r})"


def as_qt_application(value: Any) -> QtApplicationLike:
    """Narrow a QApplication instance without importing Qt in this module."""
    return value
