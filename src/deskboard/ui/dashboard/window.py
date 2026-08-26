"""Frameless Dashboard shell with the one production QWebEngineView."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, Qt, QTimer, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QInputDialog, QMainWindow

from deskboard.app.modes import AppMode
from deskboard.app.startup import recover_window_geometry
from deskboard.infrastructure.clock import Clock
from deskboard.models.profile import ProfileState
from deskboard.presentation.layout_state import (
    LayoutStateError,
    default_layout_state,
    layout_with_window_geometry,
    profile_state_from_layout,
    serialize_layout,
)
from deskboard.ui.dashboard.bridge import (
    AgendaServiceLike,
    DashboardBridge,
    FinancePresenterLike,
    NetworkStatusServiceLike,
    ProfileServiceLike,
    RefreshServiceLike,
    SettingsServiceLike,
    TimetableServiceLike,
    TodoServiceLike,
    WeatherPresenterLike,
)

WM_NCHITTEST = 0x0084
WM_NCLBUTTONDOWN = 0x00A1
WM_SYSCOMMAND = 0x0112
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17
# Keep the native window gutter outside GridStack's 4px item resize-handle
# inset, otherwise resizing an edge widget can resize/reposition the window.
RESIZE_BORDER = 4
DRAG_REGION_TOP = 32
DRAG_REGION_COMPACT_TOP = 12
DRAG_REGION_HEIGHT = 30
EDIT_TOOLBAR_PRIMARY_HEIGHT = 46
EDIT_TOOLBAR_SECONDARY_HEIGHT = 44
DRAG_REGION_SIDE_INSET = 18
DRAG_REGION_LEFT_RATIO = 1 / 3
DRAG_REGION_RIGHT_RATIO = 1 / 4
SC_MINIMIZE = 0xF020
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LayoutEditSnapshot:
    state: ProfileState
    geometry: tuple[int, int, int, int]
    previous_mode: AppMode


def should_block_daily_minimize(mode: AppMode, message: int, w_param: int) -> bool:
    """Keep Windows Show Desktop from minimizing the daily Dashboard."""
    return (
        mode is not AppMode.LAYOUT_EDIT
        and message == WM_SYSCOMMAND
        and (w_param & 0xFFF0) == SC_MINIMIZE
    )


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


def _windows_desktop_window() -> int:
    """Return the always-present desktop HWND for shell-owner fallback."""
    import ctypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    get_desktop = user32.GetDesktopWindow
    get_desktop.argtypes = []
    get_desktop.restype = ctypes.c_void_p
    return int(get_desktop() or 0)


def _log_last_error(operation: str) -> None:
    import ctypes

    LOGGER.error("%s failed; GetLastError=%d", operation, ctypes.get_last_error())


def begin_native_window_drag(hwnd: int, screen_x: int, screen_y: int) -> bool:
    """Start a native caption drag after a WebEngine toolbar pointer press."""

    if os.name != "nt" or not hwnd:
        return False
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    release_capture = user32.ReleaseCapture
    release_capture.argtypes = []
    release_capture.restype = wintypes.BOOL
    send_message = user32.SendMessageW
    send_message.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_size_t,
        ctypes.c_ssize_t,
    ]
    send_message.restype = ctypes.c_ssize_t
    point = (int(screen_x) & 0xFFFF) | ((int(screen_y) & 0xFFFF) << 16)
    release_capture()
    send_message(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, point)
    return True


def native_hit_test(
    mode: AppMode,
    screen_x: int,
    screen_y: int,
    window_rect: tuple[int, int, int, int],
    toolbar_rect: tuple[int, int, int, int] | None = None,
    toolbar_rects: tuple[tuple[int, int, int, int], ...] | None = None,
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
    if toolbar_rects is not None:
        for reserved_rect in toolbar_rects:
            toolbar_left, toolbar_top, toolbar_right, toolbar_bottom = reserved_rect
            if toolbar_left <= x < toolbar_right and toolbar_top <= y < toolbar_bottom:
                return None
        if toolbar_rects and toolbar_rects[0][1] <= y < (
            toolbar_rects[0][1] + EDIT_TOOLBAR_PRIMARY_HEIGHT
        ):
            return HTCAPTION
        return None
    if toolbar_rect is not None:
        toolbar_left, toolbar_top, toolbar_right, toolbar_bottom = toolbar_rect
        if toolbar_left <= x < toolbar_right and toolbar_top <= y < toolbar_bottom:
            return None
    drag_left = max(
        DRAG_REGION_SIDE_INSET,
        min(180, int(width * DRAG_REGION_LEFT_RATIO)),
    )
    drag_right = max(
        DRAG_REGION_SIDE_INSET,
        min(140, int(width * DRAG_REGION_RIGHT_RATIO)),
    )
    drag_top = DRAG_REGION_COMPACT_TOP if width <= 420 else DRAG_REGION_TOP
    if (
        drag_top <= y < drag_top + DRAG_REGION_HEIGHT
        and drag_left <= x < width - drag_right
    ):
        return HTCAPTION
    return None


def layout_toolbar_rect(width: int) -> tuple[int, int, int, int]:
    """Return the primary action rectangle for legacy hit-test callers."""

    return layout_toolbar_control_rects(width)[0]


def layout_toolbar_control_rects(
    width: int,
) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    """Return action and visibility rectangles in window-client coordinates."""

    drag_top = DRAG_REGION_COMPACT_TOP if width <= 420 else DRAG_REGION_TOP
    shell_inset = 12 if width <= 420 else 32
    shell_left = min(shell_inset, max(0, width // 2))
    shell_right = max(shell_left, width - shell_inset)
    action_width = 150 if width <= 420 else 190
    action_left = max(shell_left, shell_right - action_width)
    action_rect = (
        action_left,
        drag_top,
        shell_right,
        drag_top + EDIT_TOOLBAR_PRIMARY_HEIGHT,
    )
    visibility_rect = (
        shell_left,
        drag_top + EDIT_TOOLBAR_PRIMARY_HEIGHT - 2,
        shell_right,
        drag_top + EDIT_TOOLBAR_PRIMARY_HEIGHT + EDIT_TOOLBAR_SECONDARY_HEIGHT,
    )
    return action_rect, visibility_rect


class DashboardWindow(QMainWindow):
    """Small desktop panel with one Python-owned web render surface."""

    def __init__(
        self,
        *,
        todo_service: TodoServiceLike | None = None,
        agenda_service: AgendaServiceLike | None = None,
        timetable_service: TimetableServiceLike | None = None,
        profile_service: ProfileServiceLike | None = None,
        clock: Clock | None = None,
        weather_presenter: WeatherPresenterLike | None = None,
        finance_presenter: FinancePresenterLike | None = None,
        network_status_service: NetworkStatusServiceLike | None = None,
        refresh_service: RefreshServiceLike | None = None,
        settings_service: SettingsServiceLike | None = None,
    ) -> None:
        super().__init__()
        self._mode = AppMode.INTERACTION
        self._layout_window_state: bool | None = None
        self._profile_service = profile_service
        self._active_profile_state = self._load_profile_state()
        self._layout_snapshot: LayoutEditSnapshot | None = None
        self._shell_owner_retry_count = 0
        self._daily_visibility_guard = QTimer(self)
        self._daily_visibility_guard.setInterval(500)
        self._daily_visibility_guard.timeout.connect(self._guard_daily_visibility)
        self.setWindowTitle("DeskBoard")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(360, 220)
        self.resize(760, 460)
        self._apply_profile_window_geometry()

        self.view = QWebEngineView(self)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setCentralWidget(self.view)
        self.bridge = DashboardBridge(
            self,
            todo_service=todo_service,
            agenda_service=agenda_service,
            timetable_service=timetable_service,
            profile_service=profile_service,
            clock=clock,
            weather_presenter=weather_presenter,
            finance_presenter=finance_presenter,
            network_status_service=network_status_service,
            refresh_service=refresh_service,
            settings_service=settings_service,
        )
        self.bridge.layoutEditRequested.connect(self.enter_layout_edit)
        self.bridge.layoutSaveRequested.connect(self._save_layout_from_web)
        self.bridge.layoutCancelRequested.connect(self.cancel_layout_edit)
        self.bridge.windowDragRequested.connect(self._begin_window_drag)
        self.bridge.set_profile_state(self._active_profile_state)
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

    @property
    def profile_state(self) -> ProfileState:
        return self._active_profile_state

    def refresh_date_dependent_state(self) -> None:
        """Recompute local-date Dashboard views after Python crosses midnight."""

        self.bridge.publish_todos()

    @Slot(object)
    def set_mode(self, mode: AppMode) -> None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        if self._mode is AppMode.LAYOUT_EDIT and mode is not AppMode.LAYOUT_EDIT:
            self.cancel_layout_edit()
            if self._mode is mode:
                return
        if mode is AppMode.LAYOUT_EDIT and self._mode is not AppMode.LAYOUT_EDIT:
            self._begin_layout_edit()
        was_visible = self.isVisible()
        self._mode = mode
        self._apply_mode_window_state(was_visible=was_visible)
        self.bridge.publish_mode(mode)

    def enter_layout_edit(self) -> None:
        """Enter Layout Edit through the same guarded transition as Settings."""

        if self._mode is not AppMode.LAYOUT_EDIT:
            self.set_mode(AppMode.LAYOUT_EDIT)

    @Slot(int, int)
    def _begin_window_drag(self, screen_x: int, screen_y: int) -> None:
        if self._mode is AppMode.LAYOUT_EDIT:
            begin_native_window_drag(int(self.winId()), screen_x, screen_y)

    def cancel_layout_edit(self) -> None:
        """Restore the pre-edit in-memory snapshot without writing SQLite."""

        snapshot = self._layout_snapshot
        if snapshot is None:
            return
        self._active_profile_state = snapshot.state
        self._apply_window_geometry(snapshot.geometry)
        self.bridge.set_profile_state(snapshot.state)
        self.bridge.publish_profile_state(snapshot.state)
        self._finish_layout_edit(snapshot.previous_mode)

    def apply_profile_state(self, state: ProfileState) -> None:
        """Apply a switched/reloaded Profile to the Dashboard render surface."""

        if not isinstance(state, ProfileState):
            raise TypeError("state must be a ProfileState")
        if self._mode is AppMode.LAYOUT_EDIT:
            self.cancel_layout_edit()
        self._active_profile_state = default_layout_state(state)
        self._apply_profile_window_geometry()
        self.bridge.set_profile_state(self._active_profile_state)
        self.bridge.publish_profile_state(self._active_profile_state)

    def preview_profile_state(self, state: ProfileState) -> None:
        """Preview theme/font changes without persisting or changing geometry."""

        if not isinstance(state, ProfileState):
            raise TypeError("state must be a ProfileState")
        self.bridge.set_profile_state(state)
        self.bridge.publish_profile_state(state)

    def _begin_layout_edit(self) -> None:
        if self._layout_snapshot is not None:
            return
        previous_mode = self._mode
        if previous_mode not in (AppMode.LOCKED, AppMode.INTERACTION):
            previous_mode = AppMode.INTERACTION
        geometry = self._window_geometry()
        snapshot_layout = layout_with_window_geometry(
            serialize_layout(self._active_profile_state), geometry
        )
        snapshot_state = profile_state_from_layout(self._active_profile_state, snapshot_layout)
        self._layout_snapshot = LayoutEditSnapshot(snapshot_state, geometry, previous_mode)

    def _save_layout_from_web(self, layout_state: dict[str, object]) -> None:
        if self._mode is not AppMode.LAYOUT_EDIT or self._layout_snapshot is None:
            return
        try:
            saved_layout = layout_with_window_geometry(layout_state, self._window_geometry())
            state = profile_state_from_layout(self._active_profile_state, saved_layout)
        except (LayoutStateError, TypeError, ValueError) as error:
            LOGGER.warning("Ignoring invalid Dashboard layout payload: %s", error)
            return

        if self._profile_service is not None:
            current = self._profile_service.current_profile
            if current.is_builtin:
                name, accepted = QInputDialog.getText(
                    self,
                    "Save As Profile",
                    "Profile name:",
                )
                if not accepted or not name.strip():
                    return
                try:
                    profile = self._profile_service.save_as(name, state)
                except (TypeError, ValueError) as error:
                    LOGGER.warning("Could not save Dashboard Profile: %s", error)
                    return
                state = profile.state
            else:
                try:
                    self._profile_service.save_current(state)
                except (TypeError, ValueError) as error:
                    LOGGER.warning("Could not save Dashboard Profile: %s", error)
                    return

        self._active_profile_state = state
        self.bridge.set_profile_state(state)
        self.bridge.publish_profile_state(state)
        previous_mode = self._layout_snapshot.previous_mode
        self._finish_layout_edit(previous_mode)

    def _finish_layout_edit(self, mode: AppMode) -> None:
        self._layout_snapshot = None
        was_visible = self.isVisible()
        self._mode = mode
        self._apply_mode_window_state(was_visible=was_visible)
        self.bridge.publish_mode(mode)

    def _load_profile_state(self) -> ProfileState:
        if self._profile_service is None:
            return default_layout_state()
        return default_layout_state(self._profile_service.current_profile.state)

    def _window_geometry(self) -> tuple[int, int, int, int]:
        rect = self.geometry()
        return rect.x(), rect.y(), rect.width(), rect.height()

    def _apply_profile_window_geometry(self) -> None:
        state = self._active_profile_state
        if None not in (state.window_x, state.window_y, state.window_width, state.window_height):
            geometry = (
                state.window_x,
                state.window_y,
                state.window_width,
                state.window_height,
            )
            work_area = self._primary_work_area()
            if work_area is not None:
                geometry = recover_window_geometry(geometry, work_area)
            self._apply_window_geometry(geometry)

    @staticmethod
    def _primary_work_area() -> tuple[int, int, int, int] | None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return None
        rect = screen.availableGeometry()
        return rect.x(), rect.y(), rect.width(), rect.height()

    def _apply_window_geometry(self, geometry: tuple[int, int, int, int]) -> None:
        self.setGeometry(*geometry)

    def _apply_mode_window_state(self, *, was_visible: bool) -> None:
        layout_edit = self._mode is AppMode.LAYOUT_EDIT
        if self._layout_window_state is None or self._layout_window_state != layout_edit:
            flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
            if layout_edit:
                flags |= Qt.WindowType.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            self._layout_window_state = layout_edit
        if layout_edit:
            self._daily_visibility_guard.stop()
            self.showNormal()
            self.show()
            self.raise_()
            self.activateWindow()
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

    def _apply_windows_shell_owner(self) -> bool:
        """Keep daily modes above the shell without raising above normal apps."""
        if os.name != "nt" or not self.winId():
            return True
        if hasattr(self, "isVisible") and not self.isVisible():
            return True
        import ctypes

        hwnd = int(self.winId())
        GWLP_HWNDPARENT = -8
        get_shell, get_long, set_long, set_window_pos, _ = _windows_user32()
        owner = 0
        can_reinsert_after_owner = False
        if self._mode is not AppMode.LAYOUT_EDIT:
            owner = int(get_shell() or 0)
            if not owner:
                owner = _windows_desktop_window()
                if not owner:
                    LOGGER.error(
                        "GetShellWindow and GetDesktopWindow returned null; owner unchanged"
                    )
                    return False
            else:
                can_reinsert_after_owner = True
        ctypes.set_last_error(0)
        current_owner = int(get_long(hwnd, GWLP_HWNDPARENT))
        if current_owner == 0 and ctypes.get_last_error():
            _log_last_error("GetWindowLongPtrW(GWLP_HWNDPARENT)")
            return False
        if current_owner != owner:
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
                    return False
        SWP_NOZORDER = 0x0004
        flags = 0x0001 | 0x0002 | 0x0010 | 0x0020
        insert_after = owner if can_reinsert_after_owner else 0
        if not can_reinsert_after_owner:
            flags |= SWP_NOZORDER
        if not set_window_pos(hwnd, insert_after, 0, 0, 0, 0, flags):
            _log_last_error("SetWindowPos")
            return False
        return True

    def event(self, event: QEvent) -> bool:
        handled = super().event(event)
        if (
            event.type() is QEvent.Type.WindowActivate
            and self._mode is not AppMode.LAYOUT_EDIT
        ):
            QTimer.singleShot(0, self._apply_windows_shell_owner)
        elif (
            event.type() is QEvent.Type.WindowDeactivate
            and self._mode is not AppMode.LAYOUT_EDIT
        ):
            QTimer.singleShot(0, self._restore_daily_visibility)
        return handled

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        super().changeEvent(event)
        if (
            event.type() is QEvent.Type.WindowStateChange
            and self._mode is not AppMode.LAYOUT_EDIT
            and self.isMinimized()
        ):
            QTimer.singleShot(0, self._restore_daily_visibility)

    def nativeEvent(self, event_type: Any, message: Any) -> tuple[bool, int]:  # noqa: N802
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            msg = wintypes.MSG.from_address(int(message))
            if should_block_daily_minimize(self._mode, msg.message, int(msg.wParam)):
                return True, 0
            if self._mode is not AppMode.LAYOUT_EDIT and msg.message == 0x0005:
                if int(msg.wParam) == 1:  # SIZE_MINIMIZED
                    QTimer.singleShot(0, self._restore_daily_visibility)
            if self._mode is not AppMode.LAYOUT_EDIT:
                return super().nativeEvent(event_type, message)
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
                    toolbar_rects=layout_toolbar_control_rects(rect.right - rect.left),
                )
                if hit is not None:
                    return True, hit
        return super().nativeEvent(event_type, message)

    def _restore_daily_visibility(self) -> None:
        if self._mode is AppMode.LAYOUT_EDIT:
            return
        native_iconic = self._is_windows_iconic()
        if native_iconic:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)
            show_window = user32.ShowWindow
            show_window.argtypes = [ctypes.c_void_p, ctypes.c_int]
            show_window.restype = wintypes.BOOL
            show_window(int(self.winId()), 9)  # SW_RESTORE
        if self.isMinimized() or native_iconic:
            self.showNormal()
        if not self.isVisible():
            self.show()
        self._apply_windows_shell_owner()

    def _guard_daily_visibility(self) -> None:
        if self._mode is AppMode.LAYOUT_EDIT:
            self._daily_visibility_guard.stop()
            return
        if self._is_windows_iconic():
            self._restore_daily_visibility()
        elif not self.isVisible():
            self._daily_visibility_guard.stop()

    def _is_windows_iconic(self) -> bool:
        if os.name != "nt" or not self.winId():
            return False
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        is_iconic = user32.IsIconic
        is_iconic.argtypes = [ctypes.c_void_p]
        is_iconic.restype = wintypes.BOOL
        return bool(is_iconic(int(self.winId())))

    def showEvent(self, event: Any) -> None:  # noqa: N802
        super().showEvent(event)
        self._set_windows_pointer_passthrough(self._mode is AppMode.LOCKED)
        if self._mode is not AppMode.LAYOUT_EDIT:
            self._daily_visibility_guard.start()
        self._shell_owner_retry_count = 0
        QTimer.singleShot(0, self._apply_shell_owner_with_retry)

    def _apply_shell_owner_with_retry(self) -> None:
        if not self.isVisible():
            return
        if self._apply_windows_shell_owner():
            return
        if self._shell_owner_retry_count >= 10:
            return
        self._shell_owner_retry_count += 1
        QTimer.singleShot(100, self._apply_shell_owner_with_retry)
