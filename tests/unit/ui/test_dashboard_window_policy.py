import ctypes

import pytest

from deskboard.app.modes import AppMode
from deskboard.ui.dashboard import window as window_module
from deskboard.ui.dashboard.window import DashboardWindow, native_hit_test


@pytest.mark.parametrize(
    ("point", "expected"),
    [
        ((1, 1), 13),
        ((50, 1), 12),
        ((99, 1), 14),
        ((1, 40), 10),
        ((99, 40), 11),
        ((1, 79), 16),
        ((50, 79), 15),
        ((99, 79), 17),
        ((50, 20), 2),
        ((50, 60), None),
    ],
)
def test_layout_edit_hit_test_covers_drag_region_edges_and_corners(point, expected):
    assert native_hit_test(AppMode.LAYOUT_EDIT, *point, (0, 0, 100, 80)) == expected


@pytest.mark.parametrize("mode", [AppMode.LOCKED, AppMode.INTERACTION])
def test_daily_modes_never_offer_native_move_or_resize(mode):
    assert native_hit_test(mode, 1, 1, (0, 0, 100, 80)) is None
    assert native_hit_test(mode, 50, 20, (0, 0, 100, 80)) is None


@pytest.mark.parametrize("mode", [AppMode.LOCKED, AppMode.INTERACTION])
def test_daily_modes_block_windows_minimize_commands(mode):
    assert window_module.should_block_daily_minimize(mode, window_module.WM_SYSCOMMAND, 0xF020)
    assert not window_module.should_block_daily_minimize(
        mode, window_module.WM_SYSCOMMAND, 0xF030
    )
    assert not window_module.should_block_daily_minimize(
        AppMode.LAYOUT_EDIT, window_module.WM_SYSCOMMAND, 0xF020
    )


def test_windows_pointer_style_and_shell_owner_are_separate_operations():
    source = open("src/deskboard/ui/dashboard/window.py", encoding="utf-8").read()

    assert "SWP_NOZORDER" in source
    assert "WindowStaysOnBottomHint" not in source
    assert "GWLP_HWNDPARENT" in source
    assert "GetShellWindow" in source
    assert "get_shell.argtypes = []" in source
    assert "get_shell.restype = ctypes.c_void_p" in source
    assert "set_window_pos.argtypes" in source
    assert "set_window_pos.restype = wintypes.BOOL" in source
    assert "set_long.argtypes" in source
    assert "set_long.restype = ctypes.c_ssize_t" in source
    assert "get_long.argtypes" in source
    assert "get_long.restype = ctypes.c_ssize_t" in source
    assert "GetWindowRect" in source
    assert "GetLastError" in source
    assert "GetShellWindow and GetDesktopWindow returned null; owner unchanged" in source
    assert "GetDesktopWindow" in source
    assert "SetParent" not in source
    assert "WorkerW" not in source


def test_hit_test_uses_physical_screen_coordinates_with_nonzero_origin():
    physical_rect = (2400, -300, 3900, 700)

    assert native_hit_test(AppMode.LAYOUT_EDIT, 2401, -299, physical_rect) == 13
    assert native_hit_test(AppMode.LAYOUT_EDIT, 3150, -299, physical_rect) == 12
    assert native_hit_test(AppMode.LAYOUT_EDIT, 3899, -299, physical_rect) == 14
    assert native_hit_test(AppMode.LAYOUT_EDIT, 2401, 699, physical_rect) == 16
    assert native_hit_test(AppMode.LAYOUT_EDIT, 3899, 699, physical_rect) == 17
    assert native_hit_test(AppMode.LAYOUT_EDIT, 3150, -280, physical_rect) == 2
    assert native_hit_test(AppMode.LAYOUT_EDIT, 3150, 200, physical_rect) is None


def test_hit_test_supports_negative_physical_window_origin():
    physical_rect = (-1600, -200, -400, 700)

    assert native_hit_test(AppMode.LAYOUT_EDIT, -1599, 100, physical_rect) == 10
    assert native_hit_test(AppMode.LAYOUT_EDIT, -401, 100, physical_rect) == 11


def test_null_shell_hwnd_is_logged_and_owner_is_left_unchanged(monkeypatch):
    errors = []

    def unexpected_call(*_args):
        raise AssertionError("owner mutation must not run without a shell HWND")

    monkeypatch.setattr(window_module.os, "name", "nt")
    monkeypatch.setattr(
        window_module,
        "_windows_user32",
        lambda: (lambda: 0, unexpected_call, unexpected_call, unexpected_call, None),
    )
    monkeypatch.setattr(window_module, "_windows_desktop_window", lambda: 0)
    monkeypatch.setattr(
        window_module.LOGGER,
        "error",
        lambda message, *args: errors.append(message % args if args else message),
    )
    fake_window = type(
        "FakeWindow",
        (),
        {"_mode": AppMode.INTERACTION, "winId": lambda self: 123},
    )()

    DashboardWindow._apply_windows_shell_owner(fake_window)

    assert errors == [
        "GetShellWindow and GetDesktopWindow returned null; owner unchanged"
    ]


def test_null_shell_hwnd_falls_back_to_desktop_window(monkeypatch):
    set_window_pos_calls = []

    def set_window_pos(*args):
        set_window_pos_calls.append(args)
        return True

    monkeypatch.setattr(window_module.os, "name", "nt")
    monkeypatch.setattr(
        window_module,
        "_windows_user32",
        lambda: (
            lambda: 0,
            lambda *_args: 0,
            lambda *_args: 789,
            set_window_pos,
            None,
        ),
    )
    monkeypatch.setattr(window_module, "_windows_desktop_window", lambda: 456)
    fake_window = type(
        "FakeWindow",
        (),
        {"_mode": AppMode.INTERACTION, "winId": lambda self: 123},
    )()

    assert DashboardWindow._apply_windows_shell_owner(fake_window) is True
    assert set_window_pos_calls[0][0:2] == (123, 0)
    assert set_window_pos_calls[0][-1] & 0x0004  # SWP_NOZORDER


def test_owner_api_failure_logs_windows_error_and_skips_refresh(monkeypatch):
    errors = []

    def failing_set_long(*_args):
        ctypes.set_last_error(5)
        return 0

    def unexpected_refresh(*_args):
        raise AssertionError("frame refresh must not run after owner mutation failure")

    monkeypatch.setattr(window_module.os, "name", "nt")
    monkeypatch.setattr(
        window_module,
        "_windows_user32",
        lambda: (lambda: 456, lambda *_args: 0, failing_set_long, unexpected_refresh, None),
    )
    monkeypatch.setattr(
        window_module.LOGGER,
        "error",
        lambda message, *args: errors.append(message % args if args else message),
    )
    fake_window = type(
        "FakeWindow",
        (),
        {"_mode": AppMode.INTERACTION, "winId": lambda self: 123},
    )()

    DashboardWindow._apply_windows_shell_owner(fake_window)

    assert errors == [
        "SetWindowLongPtrW(GWLP_HWNDPARENT) failed; GetLastError=5"
    ]


def test_daily_owner_is_reinserted_above_shell_below_normal_windows(monkeypatch):
    set_window_pos_calls = []

    def set_window_pos(*args):
        set_window_pos_calls.append(args)
        return True

    monkeypatch.setattr(window_module.os, "name", "nt")
    monkeypatch.setattr(
        window_module,
        "_windows_user32",
        lambda: (
            lambda: 456,
            lambda *_args: 456,
            lambda *_args: 456,
            set_window_pos,
            None,
        ),
    )
    fake_window = type(
        "FakeWindow",
        (),
        {"_mode": AppMode.INTERACTION, "winId": lambda self: 123},
    )()

    DashboardWindow._apply_windows_shell_owner(fake_window)

    assert len(set_window_pos_calls) == 1
    assert set_window_pos_calls[0][0:2] == (123, 456)
    assert not (set_window_pos_calls[0][-1] & 0x0004)  # SWP_NOZORDER


def test_layout_owner_zero_does_not_mask_setter_and_confirmation_failures(
    monkeypatch,
):
    errors = []
    get_long_calls = 0

    def failing_get_long(*_args):
        nonlocal get_long_calls
        get_long_calls += 1
        if get_long_calls == 1:
            return 456
        ctypes.set_last_error(1400)
        return 0

    def failing_set_long(*_args):
        ctypes.set_last_error(1400)
        return 0

    def unexpected_refresh(*_args):
        raise AssertionError("frame refresh must not run after owner mutation failure")

    monkeypatch.setattr(window_module.os, "name", "nt")
    monkeypatch.setattr(
        window_module,
        "_windows_user32",
        lambda: (
            lambda: 456,
            failing_get_long,
            failing_set_long,
            unexpected_refresh,
            None,
        ),
    )
    monkeypatch.setattr(
        window_module.LOGGER,
        "error",
        lambda message, *args: errors.append(message % args if args else message),
    )
    fake_window = type(
        "FakeWindow",
        (),
        {"_mode": AppMode.LAYOUT_EDIT, "winId": lambda self: 123},
    )()

    DashboardWindow._apply_windows_shell_owner(fake_window)

    assert get_long_calls == 2
    assert errors == [
        "SetWindowLongPtrW(GWLP_HWNDPARENT) failed; GetLastError=1400"
    ]
