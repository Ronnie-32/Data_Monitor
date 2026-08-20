from pathlib import Path

from deskboard.infrastructure.paths import (
    app_data_root,
    database_path,
    data_dir,
    ensure_runtime_dirs,
    logs_dir,
)


def test_runtime_paths_are_under_localappdata(monkeypatch, tmp_path):
    local_appdata = tmp_path / "LocalAppData"
    monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))

    root = app_data_root()
    assert root == local_appdata / "DeskBoard"
    assert data_dir() == root / "data"
    assert logs_dir() == root / "logs"
    assert database_path() == root / "data" / "deskboard.db"
    paths = (root, data_dir(), logs_dir(), database_path())
    assert all(str(path).startswith(str(local_appdata)) for path in paths)


def test_ensure_runtime_dirs_creates_only_data_and_logs(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))

    paths = ensure_runtime_dirs()

    assert paths.root.is_dir()
    assert paths.data.is_dir()
    assert paths.logs.is_dir()
    assert paths.database == paths.data / "deskboard.db"
    assert not Path(paths.database).exists()


def test_missing_localappdata_fails_clearly(monkeypatch):
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    try:
        app_data_root()
    except RuntimeError as exc:
        assert "LOCALAPPDATA" in str(exc)
    else:
        raise AssertionError("app_data_root must not silently choose another config root")
