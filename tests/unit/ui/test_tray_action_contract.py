from pathlib import Path

from deskboard.ui.tray.tray_icon import (
    APPROVED_TRAY_ACTIONS,
    APPROVED_TRAY_COMMANDS,
    TrayCommand,
)


def test_tray_exposes_only_the_approved_minimal_commands():
    assert APPROVED_TRAY_COMMANDS == (
        TrayCommand.TOGGLE_DASHBOARD,
        TrayCommand.LOCKED,
        TrayCommand.INTERACTION,
        TrayCommand.OPEN_SETTINGS,
        TrayCommand.EXIT,
    )
    assert {command.value for command in APPROVED_TRAY_COMMANDS} == {
        "toggle_dashboard",
        "locked",
        "interaction",
        "open_settings",
        "exit",
    }
    assert [(action.command, action.label) for action in APPROVED_TRAY_ACTIONS] == [
        (TrayCommand.TOGGLE_DASHBOARD, "Hide Dashboard"),
        (TrayCommand.LOCKED, "Locked"),
        (TrayCommand.INTERACTION, "Interaction"),
        (TrayCommand.OPEN_SETTINGS, "Open Settings"),
        (TrayCommand.EXIT, "Exit DeskBoard"),
    ]


def test_tray_source_has_left_click_settings_and_no_forbidden_actions():
    source = Path("src/deskboard/ui/tray/tray_icon.py").read_text(encoding="utf-8")

    assert "ActivationReason.Trigger" in source
    assert "application.windowIcon()" in source
    assert "show_settings" in source
    assert "self._menu = QMenu()" in source
    assert "for description in APPROVED_TRAY_ACTIONS" in source
    for forbidden in ("profile", "layout_edit", "refresh", "finance"):
        assert forbidden not in source.lower()


def test_settings_general_exposes_the_same_application_exit_callback():
    source = Path("src/deskboard/ui/settings/window.py").read_text(encoding="utf-8")

    assert '("Exit DeskBoard", exit_application)' in source
