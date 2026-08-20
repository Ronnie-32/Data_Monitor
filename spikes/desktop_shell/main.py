"""Throwaway Task 0 desktop-shell spike.

This file deliberately contains no production services or persistence.  It
only proves the shell assumptions that are hard to test with mocks: one
QWebEngineView, a native Settings window, a local QWebChannel/GridStack page,
and the candidate Windows window styles.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QTimer, QUrl, Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView


MODE_LOCKED = "locked"
MODE_INTERACTION = "interaction"


def auto_exit_seconds(arguments: list[str]) -> int | None:
    """Return a bounded evidence-run duration, if one was requested."""

    if "--smoke" in arguments:
        return 5
    prefix = "--auto-exit-seconds="
    for argument in arguments:
        if argument.startswith(prefix):
            seconds = int(argument.removeprefix(prefix))
            if seconds < 1 or seconds > 300:
                raise ValueError("auto-exit duration must be between 1 and 300 seconds")
            return seconds
    return None


def resource_path(*parts: str) -> Path:
    """Resolve source and PyInstaller onedir paths in the same way."""

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root.joinpath(*parts)


class EvidenceRecorder:
    """Keep a small in-memory event trace and write it on exit."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, event: str, **details: Any) -> None:
        self.events.append(
            {
                "at_utc": datetime.now(timezone.utc).isoformat(),
                "event": event,
                **details,
            }
        )

    def write(self) -> Path:
        path = Path(tempfile.gettempdir()) / "deskboard-task0-spike-evidence.json"
        path.write_text(
            json.dumps({"events": self.events}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path


class DashboardBridge(QObject):
    """Small QWebChannel bridge used only to prove both directions."""

    pythonValueChanged = Signal(str)

    def __init__(self, evidence: EvidenceRecorder) -> None:
        super().__init__()
        self._evidence = evidence
        self._value = "Python value has not been published yet."

    @Slot(str, result=str)
    def sendCommand(self, command: str) -> str:
        """Receive a command from JavaScript and return an acknowledgement."""

        self._evidence.record("js_command", command=command)
        acknowledgement = f"Python received: {command}"
        self.publishValue(acknowledgement)
        return acknowledgement

    @Slot(result=str)
    def currentValue(self) -> str:
        return self._value

    def publishValue(self, value: str) -> None:
        self._value = value
        self._evidence.record("python_value", value=value)
        self.pythonValueChanged.emit(value)


class SettingsWindow(QMainWindow):
    """Native Settings proof; it intentionally owns no QWebEngineView."""

    def __init__(self, dashboard: "DashboardWindow") -> None:
        super().__init__()
        self.dashboard = dashboard
        self.setWindowTitle("DeskBoard Task 0 — Native Settings")
        self.resize(440, 300)

        root = QWidget(self)
        layout = QVBoxLayout(root)
        title = QLabel("Native Settings window")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)
        layout.addWidget(
            QLabel(
                "This window is Qt Widgets only.\n"
                "Use it to switch the shell mode and show/hide the one Dashboard."
            )
        )

        mode_row = QHBoxLayout()
        locked = QPushButton("Locked (pass-through)")
        locked.clicked.connect(lambda: dashboard.set_mode(MODE_LOCKED))
        interaction = QPushButton("Interaction")
        interaction.clicked.connect(lambda: dashboard.set_mode(MODE_INTERACTION))
        mode_row.addWidget(locked)
        mode_row.addWidget(interaction)
        layout.addLayout(mode_row)

        visibility_row = QHBoxLayout()
        show_button = QPushButton("Show Dashboard")
        show_button.clicked.connect(dashboard.show_dashboard)
        hide_button = QPushButton("Hide Dashboard")
        hide_button.clicked.connect(dashboard.hide_dashboard)
        visibility_row.addWidget(show_button)
        visibility_row.addWidget(hide_button)
        layout.addLayout(visibility_row)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        self.setCentralWidget(root)
        dashboard.stateChanged.connect(self.update_status)
        self.update_status()

        # A native action is useful for a quick manual proof that Settings has
        # a conventional close path while the Dashboard itself has no close UI.
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.hide)
        self.addAction(close_action)

    @Slot()
    def update_status(self) -> None:
        self.status_label.setText(
            f"Mode: {self.dashboard.mode}\n"
            f"Dashboard visible: {self.dashboard.isVisible()}\n"
            f"WebEngine views in shell: {self.dashboard.webengine_count}"
        )


class DashboardWindow(QMainWindow):
    """Frameless, small panel with exactly one QWebEngineView."""

    stateChanged = Signal()

    def __init__(self, evidence: EvidenceRecorder) -> None:
        super().__init__()
        self.evidence = evidence
        self.mode = MODE_INTERACTION
        self.webengine_count = 1
        self._settings: SettingsWindow | None = None

        self.setWindowTitle("DeskBoard Task 0 Dashboard")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnBottomHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(480, 300)
        self.resize(900, 560)

        self.view = QWebEngineView(self)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setCentralWidget(self.view)
        self.bridge = DashboardBridge(evidence)
        self.channel = QWebChannel(self.view.page())
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)
        self.view.loadFinished.connect(self._page_loaded)
        self.view.setUrl(QUrl.fromLocalFile(str(resource_path("index.html"))))
        self.evidence.record("dashboard_constructed", webengine_count=self.webengine_count)

    @property
    def settings(self) -> SettingsWindow:
        if self._settings is None:
            self._settings = SettingsWindow(self)
        return self._settings

    def _page_loaded(self, ok: bool) -> None:
        self.evidence.record(
            "page_loaded",
            ok=ok,
            url=self.view.url().toString(),
            title=self.view.title(),
        )
        if ok:
            QTimer.singleShot(300, lambda: self.bridge.publishValue("Python says hello"))

    @Slot(str)
    def set_mode(self, mode: str) -> None:
        if mode not in {MODE_LOCKED, MODE_INTERACTION}:
            raise ValueError(f"unsupported spike mode: {mode}")
        self.mode = mode
        passthrough = mode == MODE_LOCKED
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, passthrough)
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, passthrough)
        self._set_windows_pointer_passthrough(passthrough)
        self.evidence.record("mode_changed", mode=mode, pointer_passthrough=passthrough)
        self.show()
        self.stateChanged.emit()

    def _set_windows_pointer_passthrough(self, enabled: bool) -> None:
        """Apply the candidate native style; manual Windows proof is required."""

        if os.name != "nt" or not self.winId():
            return
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = int(self.winId())
        get_long = user32.GetWindowLongPtrW
        set_long = user32.SetWindowLongPtrW
        get_long.argtypes = [ctypes.c_void_p, ctypes.c_int]
        get_long.restype = ctypes.c_longlong
        set_long.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_longlong]
        set_long.restype = ctypes.c_longlong
        exstyle_index = -20  # GWL_EXSTYLE
        ws_ex_transparent = 0x00000020
        ws_ex_layered = 0x00080000
        exstyle = int(get_long(hwnd, exstyle_index))
        if enabled:
            exstyle |= ws_ex_transparent | ws_ex_layered
        else:
            exstyle &= ~ws_ex_transparent
        set_long(hwnd, exstyle_index, exstyle)
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
        self.evidence.record(
            "windows_pointer_style",
            enabled=enabled,
            hwnd=hwnd,
            candidate="Qt WindowTransparentForInput + WS_EX_TRANSPARENT",
        )

    @Slot()
    def show_dashboard(self) -> None:
        self.show()
        self.evidence.record("dashboard_visibility", visible=True)
        self.stateChanged.emit()

    @Slot()
    def hide_dashboard(self) -> None:
        self.hide()
        self.evidence.record("dashboard_visibility", visible=False)
        self.stateChanged.emit()

    @Slot()
    def open_settings(self) -> None:
        self.settings.show()
        self.settings.raise_()
        self.settings.activateWindow()
        self.evidence.record("settings_opened")

    def showEvent(self, event: Any) -> None:  # noqa: N802 (Qt API)
        super().showEvent(event)
        self._set_windows_pointer_passthrough(self.mode == MODE_LOCKED)


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("DeskBoard Task 0 Spike")
    evidence = EvidenceRecorder()
    dashboard = DashboardWindow(evidence)
    dashboard.show()
    if "--start-locked" in sys.argv:
        dashboard.set_mode(MODE_LOCKED)
    dashboard.open_settings()
    evidence.record("startup", mode=dashboard.mode)
    if "--start-hidden" in sys.argv:
        dashboard.hide_dashboard()

    duration = auto_exit_seconds(sys.argv)
    if duration is not None:
        QTimer.singleShot(duration * 1_000, app.quit)

    exit_code = app.exec()
    evidence.record("process_exit", exit_code=exit_code)
    evidence_path = evidence.write()
    print(json.dumps({"evidence_path": str(evidence_path), "events": len(evidence.events)}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(run())
