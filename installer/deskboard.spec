"""PyInstaller onedir specification for the production DeskBoard build."""

# PyInstaller injects SPECPATH, Analysis, PYZ, EXE, and COLLECT while loading a spec.
# ruff: noqa: F821
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
SOURCE_ROOT = ROOT / "src"
WEB_ROOT = SOURCE_ROOT / "deskboard" / "ui" / "dashboard" / "web"
ASSET_ROOT = SOURCE_ROOT / "deskboard" / "assets"
ICON_PATH = ASSET_ROOT / "deskboard-icon.ico"


def web_data_files() -> list[tuple[str, str]]:
    """Keep the local Dashboard frontend beside its Python package at runtime."""
    files: list[tuple[str, str]] = []
    for source in WEB_ROOT.rglob("*"):
        if not source.is_file():
            continue
        relative_parent = source.relative_to(WEB_ROOT).parent
        destination = Path("deskboard/ui/dashboard/web") / relative_parent
        files.append((str(source), destination.as_posix()))
    return files


def app_asset_files() -> list[tuple[str, str]]:
    """Bundle the runtime icon beside the packaged deskboard package."""
    return [
        (str(source), "deskboard/assets")
        for source in ASSET_ROOT.iterdir()
        if source.is_file()
    ]


conda_bin = Path(sys.base_prefix) / "Library" / "bin"
conda_dll_names = (
    "ffi.dll",
    "libcrypto-3-x64.dll",
    "libexpat.dll",
    "liblzma.dll",
    "libssl-3-x64.dll",
    # Match the Anaconda _sqlite3.pyd shipped by this build environment.
    # Without an explicit entry, PyInstaller can resolve an unrelated
    # sqlite3.dll from PATH and produce a package that cannot import sqlite3.
    "sqlite3.dll",
)
conda_binaries = [
    (str(conda_bin / name), ".")
    for name in conda_dll_names
    if (conda_bin / name).is_file()
]


a = Analysis(
    [str(SOURCE_ROOT / "deskboard" / "__main__.py")],
    pathex=[str(SOURCE_ROOT)],
    binaries=conda_binaries,
    datas=[*web_data_files(), *app_asset_files()],
    hiddenimports=[
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DeskBoard",
    icon=str(ICON_PATH),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DeskBoard",
)
