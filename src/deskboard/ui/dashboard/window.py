"""Frameless Dashboard shell with the one production QWebEngineView."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

from deskboard.app.modes import AppMode
from deskboard.ui.dashboard.bridge import DashboardBridge


class DashboardWindow(QMainWindow):
    """Small desktop panel; widget rendering remains intentionally empty."""

    def __init__(self) -> None:
        super().__init__()
        self._mode = AppMode.INTERACTION
        self.setWindowTitle("DeskBoard")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(760, 460)

        self.view = QWebEngineView(self)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setCentralWidget(self.view)
        self.bridge = DashboardBridge(self)
        self.channel = QWebChannel(self.view.page())
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)
        self.bridge.shellReady.connect(lambda: self.bridge.publish_mode(self._mode))
        self.bridge.windowMoveRequested.connect(self._begin_system_move)
        self.bridge.windowResizeRequested.connect(self._begin_system_resize)
        self.view.setUrl(QUrl.fromLocalFile(str(self.web_page_path())))
        self._apply_mode_window_state(was_visible=False)

    @staticmethod
    def web_page_path() -> Path:
        return Path(__file__).resolve().parent / "web" / "index.html"

    @property
    def mode(self) -> AppMode:
        return self._mode

    @Slot(object)
    def set_mode(self, mode: AppMode) -> None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        was_visible = self.isVisible()
        self._mode = mode
        self._apply_mode_window_state(was_visible=was_visible)
        self.bridge.publish_mode(mode)

    def _apply_mode_window_state(self, *, was_visible: bool) -> None:
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self._mode is AppMode.LAYOUT_EDIT:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags |= Qt.WindowType.WindowStaysOnBottomHint
        self.setWindowFlags(flags)
        passthrough = self._mode is AppMode.LOCKED
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, passthrough)
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, passthrough)
        self._set_windows_pointer_passthrough(passthrough)
        if was_visible:
            self.show()

    def _begin_system_move(self) -> None:
        if self._mode is not AppMode.LAYOUT_EDIT:
            return
        handle = self.windowHandle()
        if handle is not None:
            handle.startSystemMove()

    def _begin_system_resize(self) -> None:
        if self._mode is not AppMode.LAYOUT_EDIT:
            return
        handle = self.windowHandle()
        if handle is not None:
            edges = Qt.Edge.RightEdge | Qt.Edge.BottomEdge
            handle.startSystemResize(edges)

    def _set_windows_pointer_passthrough(self, enabled: bool) -> None:
        """Apply the Windows style accepted by the Task 0 manual spike."""
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
        exstyle_index = -20
        ws_ex_transparent = 0x00000020
        ws_ex_layered = 0x00080000
        exstyle = int(get_long(hwnd, exstyle_index))
        if enabled:
            exstyle |= ws_ex_transparent | ws_ex_layered
        else:
            exstyle &= ~ws_ex_transparent
        set_long(hwnd, exstyle_index, exstyle)
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)

    def showEvent(self, event: Any) -> None:  # noqa: N802
        super().showEvent(event)
        self._set_windows_pointer_passthrough(self._mode is AppMode.LOCKED)
