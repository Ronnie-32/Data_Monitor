"""Frameless Dashboard shell with the one production QWebEngineView."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer, QUrl, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

from deskboard.app.modes import AppMode
from deskboard.ui.dashboard.bridge import DashboardBridge

WM_NCHITTEST = 0x0084
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17
RESIZE_BORDER = 8
DRAG_REGION_HEIGHT = 44
LOGGER = logging.getLogger(__name__)


def _windows_user32() -> tuple[Any, ...]:
    """Load the small Win32 surface used by the Dashboard with 64-bit-safe types."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    get_shell = user32.GetShellWindow
    get_shell.argtypes = []
    get_shell.restype = ctypes.c_void_p
    get_long = user32.GetWindowLongPtrW
    get_long.argtypes = [ctypes.c_void_p, ctypes.c_int]
    get_long.restype = ctypes.c_ssize_t
    set_long = user32.SetWindowLongPtrW
    set_long.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
    set_long.restype = ctypes.c_ssize_t
    set_window_pos = user32.SetWindowPos
    set_window_pos.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    set_window_pos.restype = wintypes.BOOL
    get_window_rect = user32.GetWindowRect
    get_window_rect.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.RECT)]
    get_window_rect.restype = wintypes.BOOL
    return (
        get_shell,
        get_long,
        set_long,
        set_window_pos,
        get_window_rect,
    )


def _log_last_error(operation: str) -> None:
    import ctypes

    LOGGER.error("%s failed; GetLastError=%d", operation, ctypes.get_last_error())


def native_hit_test(
    mode: AppMode,
    screen_x: int,
    screen_y: int,
    window_rect: tuple[int, int, int, int],
) -> int | None:
    """Return a hit code using one physical Win32 screen-coordinate space."""
    window_left, window_top, window_right, window_bottom = window_rect
    width = window_right - window_left
    height = window_bottom - window_top
    if mode is not AppMode.LAYOUT_EDIT or width <= 0 or height <= 0:
        return None
    x = screen_x - window_left
    y = screen_y - window_top
    left = x < RESIZE_BORDER
    right = x >= width - RESIZE_BORDER
    top = y < RESIZE_BORDER
    bottom = y >= height - RESIZE_BORDER
    if top and left:
        return HTTOPLEFT
    if top and right:
        return HTTOPRIGHT
    if bottom and left:
        return HTBOTTOMLEFT
    if bottom and right:
        return HTBOTTOMRIGHT
    if left:
        return HTLEFT
    if right:
        return HTRIGHT
    if top:
        return HTTOP
    if bottom:
        return HTBOTTOM
    if y < DRAG_REGION_HEIGHT:
        return HTCAPTION
    return None


class DashboardWindow(QMainWindow):
    """Small desktop panel; widget rendering remains intentionally empty."""

    def __init__(self) -> None:
        super().__init__()
        self._mode = AppMode.INTERACTION
        self._layout_window_state: bool | None = None
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
        layout_edit = self._mode is AppMode.LAYOUT_EDIT
        if self._layout_window_state is None or self._layout_window_state != layout_edit:
            flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
            if layout_edit:
                flags |= Qt.WindowType.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            self._layout_window_state = layout_edit
        passthrough = self._mode is AppMode.LOCKED
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, passthrough)
        has_input_passthrough = bool(
            self.windowFlags() & Qt.WindowType.WindowTransparentForInput
        )
        if has_input_passthrough != passthrough:
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, passthrough)
        self._set_windows_pointer_passthrough(passthrough)
        if was_visible:
            self.show()
        self._apply_windows_shell_owner()

    def _set_windows_pointer_passthrough(self, enabled: bool) -> None:
        """Apply the Windows style accepted by the Task 0 manual spike."""
        if os.name != "nt" or not self.winId():
            return
        import ctypes

        hwnd = int(self.winId())
        _, get_long, set_long, set_window_pos, _ = _windows_user32()
        exstyle_index = -20
        ws_ex_transparent = 0x00000020
        ws_ex_layered = 0x00080000
        SWP_NOZORDER = 0x0004
        ctypes.set_last_error(0)
        exstyle = int(get_long(hwnd, exstyle_index))
        if exstyle == 0 and ctypes.get_last_error():
            _log_last_error("GetWindowLongPtrW")
            return
        if enabled:
            exstyle |= ws_ex_transparent | ws_ex_layered
        else:
            exstyle &= ~ws_ex_transparent
        ctypes.set_last_error(0)
        previous = int(set_long(hwnd, exstyle_index, exstyle))
        if previous == 0 and ctypes.get_last_error():
            _log_last_error("SetWindowLongPtrW")
            return
        flags = 0x0001 | 0x0002 | SWP_NOZORDER | 0x0010 | 0x0020
        if not set_window_pos(hwnd, 0, 0, 0, 0, 0, flags):
            _log_last_error("SetWindowPos")

    def _apply_windows_shell_owner(self) -> None:
        """Keep daily modes above the shell without raising above normal apps."""
        if os.name != "nt" or not self.winId():
            return
        import ctypes

        hwnd = int(self.winId())
        GWLP_HWNDPARENT = -8
        get_shell, get_long, set_long, set_window_pos, _ = _windows_user32()
        owner = 0
        if self._mode is not AppMode.LAYOUT_EDIT:
            owner = int(get_shell() or 0)
            if not owner:
                LOGGER.error("GetShellWindow returned a null HWND; owner unchanged")
                return
        ctypes.set_last_error(0)
        current_owner = int(get_long(hwnd, GWLP_HWNDPARENT))
        if current_owner == 0 and ctypes.get_last_error():
            _log_last_error("GetWindowLongPtrW(GWLP_HWNDPARENT)")
            return
        if current_owner == owner:
            return
        ctypes.set_last_error(0)
        previous = int(set_long(hwnd, GWLP_HWNDPARENT, owner))
        setter_error = ctypes.get_last_error()
        if previous == 0 and setter_error:
            ctypes.set_last_error(0)
            confirmed_owner = int(get_long(hwnd, GWLP_HWNDPARENT))
            confirmation_error = ctypes.get_last_error()
            if (
                confirmed_owner == 0
                and confirmation_error
                or confirmed_owner != owner
            ):
                LOGGER.error(
                    "SetWindowLongPtrW(GWLP_HWNDPARENT) failed; GetLastError=%d",
                    setter_error,
                )
                return
        SWP_NOZORDER = 0x0004
        flags = 0x0001 | 0x0002 | SWP_NOZORDER | 0x0010 | 0x0020
        if not set_window_pos(hwnd, 0, 0, 0, 0, 0, flags):
            _log_last_error("SetWindowPos")

    def nativeEvent(self, event_type: Any, message: Any) -> tuple[bool, int]:  # noqa: N802
        if os.name == "nt" and self._mode is AppMode.LAYOUT_EDIT:
            import ctypes
            from ctypes import wintypes

            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_NCHITTEST:
                _, _, _, _, get_window_rect = _windows_user32()
                rect = wintypes.RECT()
                if not get_window_rect(msg.hWnd, ctypes.byref(rect)):
                    _log_last_error("GetWindowRect")
                    return super().nativeEvent(event_type, message)
                l_param = int(msg.lParam)
                global_x = ctypes.c_short(l_param & 0xFFFF).value
                global_y = ctypes.c_short((l_param >> 16) & 0xFFFF).value
                hit = native_hit_test(
                    self._mode,
                    global_x,
                    global_y,
                    (rect.left, rect.top, rect.right, rect.bottom),
                )
                if hit is not None:
                    return True, hit
        return super().nativeEvent(event_type, message)

    def showEvent(self, event: Any) -> None:  # noqa: N802
        super().showEvent(event)
        self._set_windows_pointer_passthrough(self._mode is AppMode.LOCKED)
        QTimer.singleShot(0, self._apply_windows_shell_owner)
