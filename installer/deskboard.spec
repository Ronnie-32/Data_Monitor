"""PyInstaller onedir specification for the production DeskBoard build."""

# PyInstaller injects SPECPATH, Analysis, PYZ, EXE, and COLLECT while loading a spec.
# ruff: noqa: F821
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
SOURCE_ROOT = ROOT / "src"
WEB_ROOT = SOURCE_ROOT / "deskboard" / "ui" / "dashboard" / "web"


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


conda_bin = Path(sys.base_prefix) / "Library" / "bin"
conda_dll_names = (
    "ffi.dll",
    "libcrypto-3-x64.dll",
    "libexpat.dll",
    "liblzma.dll",
    "libssl-3-x64.dll",
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
    datas=web_data_files(),
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
