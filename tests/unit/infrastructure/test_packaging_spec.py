from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parents[3] / "installer" / "deskboard.spec"
ISS_PATH = Path(__file__).resolve().parents[3] / "installer" / "deskboard.iss"


def test_pyinstaller_spec_explicitly_bundles_conda_sqlite_binary() -> None:
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    assert '"sqlite3.dll"' in spec_text
    assert 'conda_bin / name' in spec_text


def test_pyinstaller_spec_bundles_and_assigns_the_application_icon() -> None:
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    assert 'ICON_PATH = ASSET_ROOT / "deskboard-icon.ico"' in spec_text
    assert 'datas=[*web_data_files(), *app_asset_files()]' in spec_text
    assert 'icon=str(ICON_PATH)' in spec_text


def test_inno_setup_uses_the_same_application_icon() -> None:
    iss_text = ISS_PATH.read_text(encoding="utf-8")

    assert "SetupIconFile=..\\src\\deskboard\\assets\\deskboard-icon.ico" in iss_text
