from pathlib import Path

from deskboard.app.icon import deskboard_icon_path


def test_main_assigns_the_shared_icon_to_qapplication():
    source = Path("src/deskboard/main.py").read_text(encoding="utf-8")

    assert "from PySide6.QtGui import QIcon" in source
    assert "qt_application.setWindowIcon(QIcon(str(deskboard_icon_path())))" in source


def test_application_icon_assets_are_bundled_as_a_multisize_ico():
    icon_path = deskboard_icon_path()
    assert icon_path == Path("src/deskboard/assets/deskboard-icon.ico").resolve()
    assert icon_path.is_file()
    assert icon_path.with_suffix(".png").is_file()

    icon_bytes = icon_path.read_bytes()
    assert icon_bytes[:4] == b"\x00\x00\x01\x00"
    assert int.from_bytes(icon_bytes[4:6], "little") == 7
