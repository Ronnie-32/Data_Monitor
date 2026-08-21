"""Minimal system tray actions for the DeskBoard application shell."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


class TrayCommand(Enum):
    TOGGLE_DASHBOARD = "toggle_dashboard"
    LOCKED = "locked"
    INTERACTION = "interaction"
    OPEN_SETTINGS = "open_settings"
    EXIT = "exit"


@dataclass(frozen=True)
class TrayActionDescription:
    command: TrayCommand
    label: str


APPROVED_TRAY_ACTIONS = (
    TrayActionDescription(TrayCommand.TOGGLE_DASHBOARD, "Hide Dashboard"),
    TrayActionDescription(TrayCommand.LOCKED, "Locked"),
    TrayActionDescription(TrayCommand.INTERACTION, "Interaction"),
    TrayActionDescription(TrayCommand.OPEN_SETTINGS, "Open Settings"),
    TrayActionDescription(TrayCommand.EXIT, "Exit DeskBoard"),
)
APPROVED_TRAY_COMMANDS = tuple(action.command for action in APPROVED_TRAY_ACTIONS)


class TrayIcon(QSystemTrayIcon):
    """Own the approved compact tray menu and no domain actions."""

    def __init__(
        self,
        toggle_dashboard: Callable[[], None],
        set_locked: Callable[[], None],
        set_interaction: Callable[[], None],
        show_settings: Callable[[], None],
        exit_application: Callable[[], None],
    ) -> None:
        application = QApplication.instance()
        if application is None:
            raise RuntimeError("TrayIcon requires an active QApplication")
        icon = application.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        super().__init__(icon)
        self.setToolTip("DeskBoard")
        self._show_settings = show_settings

        self._menu = QMenu()
        callbacks = {
            TrayCommand.TOGGLE_DASHBOARD: toggle_dashboard,
            TrayCommand.LOCKED: set_locked,
            TrayCommand.INTERACTION: set_interaction,
            TrayCommand.OPEN_SETTINGS: show_settings,
            TrayCommand.EXIT: exit_application,
        }
        self._actions = {}
        for description in APPROVED_TRAY_ACTIONS:
            if description.command in {TrayCommand.LOCKED, TrayCommand.OPEN_SETTINGS}:
                self._menu.addSeparator()
            action = QAction(description.label, self._menu)
            action.triggered.connect(callbacks[description.command])
            self._menu.addAction(action)
            self._actions[description.command] = action
        self._toggle_action = self._actions[TrayCommand.TOGGLE_DASHBOARD]
        self.setContextMenu(self._menu)
        self.activated.connect(self._handle_activation)

    def _handle_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_settings()

    def sync_dashboard_visibility(self, visible: bool) -> None:
        self._toggle_action.setText("Hide Dashboard" if visible else "Show Dashboard")
