from __future__ import annotations

import ctypes
import json
import os
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QIcon,
    QMouseEvent,
    QMoveEvent,
    QPainter,
    QPen,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMenu,
    QMessageBox,
    QStyle,
    QSystemTrayIcon,
    QWidget,
)

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "settings.json"
APP_NAME = "桌面图片贴"


def window_flags_for_mode(editing: bool) -> Qt.WindowType:
    if editing:
        return (
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
        )
    return (
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.Tool
        | Qt.WindowType.WindowTransparentForInput
    )


def normalize_geometry(
    saved: dict[str, Any], screen: tuple[int, int, int, int]
) -> tuple[int, int, int, int]:
    """Return a usable geometry that remains reachable on the primary screen."""
    screen_x, screen_y, screen_width, screen_height = screen
    default_width = min(900, screen_width)
    default_height = min(560, screen_height)
    try:
        width = max(240, min(int(saved.get("width", default_width)), screen_width))
        height = max(150, min(int(saved.get("height", default_height)), screen_height))
        x = int(saved.get("x", screen_x + (screen_width - width) // 2))
        y = int(saved.get("y", screen_y + (screen_height - height) // 2))
    except (TypeError, ValueError):
        width, height = default_width, default_height
        x = screen_x + (screen_width - width) // 2
        y = screen_y + (screen_height - height) // 2

    screen_right = screen_x + screen_width
    screen_bottom = screen_y + screen_height
    fully_offscreen = (
        x >= screen_right or y >= screen_bottom or x + width <= screen_x or y + height <= screen_y
    )
    if fully_offscreen:
        x = screen_x + (screen_width - width) // 2
        y = screen_y + (screen_height - height) // 2
    else:
        x = max(screen_x, min(x, screen_right - width))
        y = max(screen_y, min(y, screen_bottom - height))
    return x, y, width, height


def adjusted_drag_geometry(
    initial: tuple[int, int, int, int],
    delta: tuple[int, int],
    edges: frozenset[str],
    *,
    minimum_width: int = 240,
    minimum_height: int = 150,
) -> tuple[int, int, int, int]:
    """Calculate deterministic move/resize geometry for a mouse drag."""
    x, y, width, height = initial
    dx, dy = delta
    if not edges:
        return x + dx, y + dy, width, height

    if "left" in edges:
        applied_dx = min(dx, width - minimum_width)
        x += applied_dx
        width -= applied_dx
    elif "right" in edges:
        width = max(minimum_width, width + dx)

    if "top" in edges:
        applied_dy = min(dy, height - minimum_height)
        y += applied_dy
        height -= applied_dy
    elif "bottom" in edges:
        height = max(minimum_height, height + dy)
    return x, y, width, height


def fitted_content_rect(
    container_width: int,
    container_height: int,
    content_width: int,
    content_height: int,
) -> tuple[int, int, int, int]:
    """Fit content inside a container without changing its aspect ratio."""
    if min(container_width, container_height, content_width, content_height) <= 0:
        return 0, 0, 0, 0
    scale = min(
        container_width / content_width,
        container_height / content_height,
    )
    width = max(1, round(content_width * scale))
    height = max(1, round(content_height * scale))
    return (
        (container_width - width) // 2,
        (container_height - height) // 2,
        width,
        height,
    )


def load_config() -> dict[str, Any]:
    default = {"image": "", "geometry": {}, "autostart": False}
    try:
        loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default
    if not isinstance(loaded, dict):
        return default
    return {**default, **loaded}


def save_config(config: dict[str, Any]) -> None:
    temporary = CONFIG_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(CONFIG_PATH)


def image_path_from_config(config: dict[str, Any]) -> Path | None:
    value = config.get("image", "")
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = APP_DIR / candidate
    return candidate


def startup_file_path() -> Path | None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
        / "DesktopImagePin.cmd"
    )


def set_autostart(enabled: bool) -> bool:
    target = startup_file_path()
    if target is None:
        return False
    try:
        if enabled:
            launcher = APP_DIR / "start.vbs"
            target.write_text(
                f'@start "" wscript.exe "{launcher}"\n', encoding="utf-8"
            )
        elif target.exists():
            target.unlink()
    except OSError:
        return False
    return target.exists() == enabled


def _user32_functions() -> tuple[Any, ...]:
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    get_shell = user32.GetShellWindow
    get_shell.argtypes = []
    get_shell.restype = ctypes.c_void_p
    get_desktop = user32.GetDesktopWindow
    get_desktop.argtypes = []
    get_desktop.restype = ctypes.c_void_p
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
    return get_shell, get_desktop, get_long, set_long, set_window_pos


class ImageWindow(QWidget):
    editFinishRequested = Signal()

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self._config = config
        self._editing = False
        self._allow_close = False
        self._pixmap = QPixmap()
        self._svg_renderer: QSvgRenderer | None = None
        self._drag_origin: QPoint | None = None
        self._drag_geometry: QRect | None = None
        self._drag_edges: frozenset[str] = frozenset()
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_geometry)
        self.setWindowTitle(APP_NAME)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(240, 150)

        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        geometry = normalize_geometry(
            config.get("geometry", {}),
            (available.x(), available.y(), available.width(), available.height()),
        )
        self.setGeometry(*geometry)
        selected_image = image_path_from_config(config)
        if selected_image is not None:
            self.load_image(selected_image)
        self._apply_mode()

    @property
    def editing(self) -> bool:
        return self._editing

    @property
    def has_image(self) -> bool:
        return self._svg_renderer is not None or not self._pixmap.isNull()

    def load_image(self, path: Path) -> bool:
        if path.suffix.casefold() == ".svg":
            renderer = QSvgRenderer(str(path))
            if not renderer.isValid():
                return False
            self._svg_renderer = renderer
            self._pixmap = QPixmap()
            self.update()
            return True
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return False
        self._svg_renderer = None
        self._pixmap = pixmap
        self.update()
        return True

    def set_editing(self, enabled: bool) -> None:
        if self._editing == enabled:
            return
        self._editing = enabled
        self._drag_origin = None
        self._drag_geometry = None
        self._drag_edges = frozenset()
        self.unsetCursor()
        if not enabled:
            self._save_geometry()
        self._apply_mode()
        self.update()

    def _apply_mode(self) -> None:
        was_visible = self.isVisible()
        geometry = self.geometry()
        self.setWindowFlags(window_flags_for_mode(self._editing))
        self.setGeometry(geometry)
        self.setWindowTitle(
            f"{APP_NAME} — 编辑模式（拖标题栏移动，关闭窗口完成）"
            if self._editing
            else APP_NAME
        )
        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus if self._editing else Qt.FocusPolicy.NoFocus
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, not self._editing
        )
        if was_visible or not self.isVisible():
            self.show()
        if self._editing:
            self.raise_()
            self.activateWindow()
        self.repaint()
        QTimer.singleShot(0, self.update)
        QTimer.singleShot(0, self._apply_windows_mode)

    def _apply_windows_mode(self) -> None:
        if os.name != "nt" or not self.winId():
            return
        hwnd = int(self.winId())
        get_shell, get_desktop, get_long, set_long, set_window_pos = _user32_functions()
        gwlp_owner = -8
        gwl_exstyle = -20
        ws_ex_transparent = 0x00000020
        ws_ex_noactivate = 0x08000000
        ws_ex_toolwindow = 0x00000080
        swp_nosize = 0x0001
        swp_nomove = 0x0002
        swp_noactivate = 0x0010
        swp_framechanged = 0x0020

        exstyle = int(get_long(hwnd, gwl_exstyle))
        exstyle |= ws_ex_toolwindow
        if self._editing:
            exstyle &= ~(ws_ex_transparent | ws_ex_noactivate)
            owner = 0
        else:
            exstyle |= ws_ex_transparent | ws_ex_noactivate
            owner = int(get_shell() or get_desktop() or 0)
        set_long(hwnd, gwl_exstyle, exstyle)
        set_long(hwnd, gwlp_owner, owner)

        insert_after = 0 if self._editing else owner
        flags = swp_nosize | swp_nomove | swp_framechanged
        if not self._editing:
            flags |= swp_noactivate
        set_window_pos(hwnd, insert_after, 0, 0, 0, 0, flags)

    def _save_geometry(self) -> None:
        rect = self.geometry()
        self._config["geometry"] = {
            "x": rect.x(),
            "y": rect.y(),
            "width": rect.width(),
            "height": rect.height(),
        }
        try:
            save_config(self._config)
        except OSError:
            pass

    def restore_default_geometry(self) -> None:
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        x, y, width, height = normalize_geometry(
            {}, (available.x(), available.y(), available.width(), available.height())
        )
        self.setGeometry(x, y, width, height)
        self._save_geometry()

    def permit_close(self) -> None:
        self._allow_close = True

    def paintEvent(self, event: Any) -> None:
        del event
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        if self._svg_renderer is not None and self._svg_renderer.isValid():
            size = self._svg_renderer.defaultSize()
            target_values = fitted_content_rect(
                self.width(), self.height(), size.width(), size.height()
            )
            self._svg_renderer.render(painter, QRectF(*target_values))
        elif not self._pixmap.isNull():
            target_values = fitted_content_rect(
                self.width(),
                self.height(),
                self._pixmap.width(),
                self._pixmap.height(),
            )
            painter.drawPixmap(QRect(*target_values), self._pixmap)
        if self._editing:
            painter.setPen(QPen(QColor("#1683ff"), 3, Qt.PenStyle.DashLine))
            painter.drawRect(self.rect().adjusted(2, 2, -3, -3))
            message = "拖标题栏移动 · 拖窗口边框缩放 · 点右上角 × 或托盘完成"
            metrics = painter.fontMetrics()
            label = QRect(12, 12, metrics.horizontalAdvance(message) + 20, 32)
            painter.fillRect(label, QColor(15, 23, 42, 210))
            painter.setPen(QColor("white"))
            painter.drawText(label, Qt.AlignmentFlag.AlignCenter, message)

    def _edges_at(self, position: QPoint) -> frozenset[str]:
        margin = 12
        edges: set[str] = set()
        if position.x() <= margin:
            edges.add("left")
        elif position.x() >= self.width() - margin:
            edges.add("right")
        if position.y() <= margin:
            edges.add("top")
        elif position.y() >= self.height() - margin:
            edges.add("bottom")
        return frozenset(edges)

    def _set_resize_cursor(self, edges: frozenset[str]) -> None:
        if edges in (frozenset({"left"}), frozenset({"right"})):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edges in (frozenset({"top"}), frozenset({"bottom"})):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edges in (
            frozenset({"left", "top"}),
            frozenset({"right", "bottom"}),
        ):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edges:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._editing or event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        self._drag_origin = event.globalPosition().toPoint()
        self._drag_geometry = self.geometry()
        self._drag_edges = self._edges_at(event.position().toPoint())
        self._set_resize_cursor(self._drag_edges)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._editing:
            return super().mouseMoveEvent(event)
        if self._drag_origin is None or self._drag_geometry is None:
            self._set_resize_cursor(self._edges_at(event.position().toPoint()))
            return super().mouseMoveEvent(event)
        delta = event.globalPosition().toPoint() - self._drag_origin
        initial = self._drag_geometry
        geometry = adjusted_drag_geometry(
            (initial.x(), initial.y(), initial.width(), initial.height()),
            (delta.x(), delta.y()),
            self._drag_edges,
            minimum_width=self.minimumWidth(),
            minimum_height=self.minimumHeight(),
        )
        self.setGeometry(*geometry)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._editing and event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = None
            self._drag_geometry = None
            self._drag_edges = frozenset()
            self._save_geometry()
            self._set_resize_cursor(self._edges_at(event.position().toPoint()))
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self._drag_origin is None:
            self.unsetCursor()
        super().leaveEvent(event)

    def moveEvent(self, event: QMoveEvent) -> None:
        super().moveEvent(event)
        if self._editing:
            self._save_timer.start(250)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._editing:
            self._save_timer.start(250)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if (
            not self._editing
            and event.type() == QEvent.Type.WindowStateChange
            and self.isMinimized()
        ):
            QTimer.singleShot(0, self._restore_from_minimize)

    def _restore_from_minimize(self) -> None:
        if self._editing:
            return
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.show()
        self._apply_windows_mode()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close:
            self._save_geometry()
            event.accept()
        elif self._editing:
            event.ignore()
            self.editFinishRequested.emit()
        else:
            event.ignore()


class DesktopImageApp:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.app.setQuitOnLastWindowClosed(False)
        self.config = load_config()
        self.window = ImageWindow(self.config)
        self.tray = QSystemTrayIcon(self._tray_icon(), self.app)
        self.menu = QMenu()

        self.edit_action = QAction("编辑位置和大小", self.menu)
        self.edit_action.setCheckable(True)
        self.edit_action.toggled.connect(self._toggle_editing)
        self.window.editFinishRequested.connect(
            lambda: self.edit_action.setChecked(False)
        )
        self.menu.addAction(self.edit_action)

        choose_action = self.menu.addAction("选择其他图片…")
        choose_action.triggered.connect(self._choose_image)
        reset_action = self.menu.addAction("恢复默认大小和位置")
        reset_action.triggered.connect(self.window.restore_default_geometry)
        self.menu.addSeparator()

        self.autostart_action = QAction("开机自动启动", self.menu)
        self.autostart_action.setCheckable(True)
        target = startup_file_path()
        self.autostart_action.setChecked(bool(target and target.exists()))
        self.autostart_action.toggled.connect(self._toggle_autostart)
        self.menu.addAction(self.autostart_action)
        self.menu.addSeparator()

        exit_action = self.menu.addAction("退出")
        exit_action.triggered.connect(self._exit)
        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip("桌面图片贴：右键可编辑")
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()
        self.window.show()
        QTimer.singleShot(0, self.window._apply_windows_mode)
        if not self.window.has_image:
            QTimer.singleShot(0, self._choose_image)

    def _tray_icon(self) -> QIcon:
        icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
        return icon if not icon.isNull() else QIcon()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.edit_action.toggle()

    def _toggle_editing(self, enabled: bool) -> None:
        self.edit_action.setText("完成编辑" if enabled else "编辑位置和大小")
        self.window.set_editing(enabled)

    def _choose_image(self) -> None:
        current_image = image_path_from_config(self.config)
        path, _ = QFileDialog.getOpenFileName(
            None,
            "选择桌面图片",
            str(current_image.parent if current_image is not None else APP_DIR),
            "图片 (*.svg *.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not path:
            return
        selected = Path(path)
        if not self.window.load_image(selected):
            QMessageBox.warning(None, APP_NAME, "无法读取这张图片。")
            return
        try:
            self.config["image"] = str(selected.resolve())
            save_config(self.config)
            if not self.window.editing:
                self.edit_action.setChecked(True)
        except OSError:
            QMessageBox.warning(None, APP_NAME, "图片已显示，但配置保存失败。")

    def _toggle_autostart(self, enabled: bool) -> None:
        if set_autostart(enabled):
            self.config["autostart"] = enabled
            try:
                save_config(self.config)
            except OSError:
                pass
            return
        self.autostart_action.blockSignals(True)
        self.autostart_action.setChecked(not enabled)
        self.autostart_action.blockSignals(False)
        QMessageBox.warning(None, APP_NAME, "无法修改开机启动项。")

    def _exit(self) -> None:
        self.window.permit_close()
        self.window.close()
        self.tray.hide()
        self.app.quit()


def acquire_single_instance() -> int | None:
    if os.name != "nt":
        return 1
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_mutex = kernel32.CreateMutexW
    create_mutex.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    create_mutex.restype = ctypes.c_void_p
    handle = int(create_mutex(None, False, "Local\\DesktopImagePin.SingleInstance") or 0)
    if not handle or ctypes.get_last_error() == 183:
        return None
    return handle


def main() -> int:
    mutex = acquire_single_instance()
    if mutex is None:
        return 0
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    controller = DesktopImageApp(app)
    result = app.exec()
    del controller
    if os.name == "nt":
        ctypes.WinDLL("kernel32").CloseHandle(ctypes.c_void_p(mutex))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
