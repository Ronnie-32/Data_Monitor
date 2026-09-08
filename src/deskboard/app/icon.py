"""Shared application icon path for source and packaged runs."""

from pathlib import Path

APP_ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "deskboard-icon.ico"


def deskboard_icon_path() -> Path:
    """Return the bundled Windows icon used by the app and system tray."""
    return APP_ICON_PATH
