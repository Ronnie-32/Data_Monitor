from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parents[3] / "installer" / "deskboard.spec"


def test_pyinstaller_spec_explicitly_bundles_conda_sqlite_binary() -> None:
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    assert '"sqlite3.dll"' in spec_text
    assert 'conda_bin / name' in spec_text
