"""Centralized paths for DeskBoard-owned runtime files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    data: Path
    logs: Path
    database: Path


def app_data_root(local_appdata: str | os.PathLike[str] | None = None) -> Path:
    """Return ``%LOCALAPPDATA%\\DeskBoard`` without creating it."""
    base = Path(local_appdata) if local_appdata is not None else _local_appdata_from_environment()
    return base / "DeskBoard"


def _local_appdata_from_environment() -> Path:
    value = os.environ.get("LOCALAPPDATA")
    if not value:
        raise RuntimeError("LOCALAPPDATA is required for DeskBoard runtime paths")
    return Path(value)


def data_dir(local_appdata: str | os.PathLike[str] | None = None) -> Path:
    return app_data_root(local_appdata) / "data"


def logs_dir(local_appdata: str | os.PathLike[str] | None = None) -> Path:
    return app_data_root(local_appdata) / "logs"


def database_path(local_appdata: str | os.PathLike[str] | None = None) -> Path:
    return data_dir(local_appdata) / "deskboard.db"


def ensure_runtime_dirs(local_appdata: str | os.PathLike[str] | None = None) -> RuntimePaths:
    """Create only the approved data and log directories and return all paths."""
    root = app_data_root(local_appdata)
    data = root / "data"
    logs = root / "logs"
    data.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    return RuntimePaths(root=root, data=data, logs=logs, database=data / "deskboard.db")
