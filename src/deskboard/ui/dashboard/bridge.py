"""Minimal QWebChannel bridge for application-shell state."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from deskboard.app.modes import AppMode


class DashboardBridge(QObject):
    shellReady = Signal()
    modeChanged = Signal(str)
    settingsRequested = Signal()
    windowMoveRequested = Signal()
    windowResizeRequested = Signal()

    @Slot()
    def notifyReady(self) -> None:  # noqa: N802
        self.shellReady.emit()

    @Slot()
    def openSettings(self) -> None:  # noqa: N802
        self.settingsRequested.emit()

    @Slot()
    def beginWindowMove(self) -> None:  # noqa: N802
        self.windowMoveRequested.emit()

    @Slot()
    def beginWindowResize(self) -> None:  # noqa: N802
        self.windowResizeRequested.emit()

    def publish_mode(self, mode: AppMode) -> None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        self.modeChanged.emit(mode.value)
