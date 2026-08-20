# PyInstaller onedir proof for the throwaway Task 0 shell.
# Run from the repository root:
#   .venv\Scripts\python.exe -m PyInstaller --clean --noconfirm spikes\desktop_shell\spike.spec

import sys
from pathlib import Path


ROOT = Path(SPECPATH)
SPIKE = ROOT

datas = [
    (str(SPIKE / "index.html"), "."),
    (str(SPIKE / "qwebchannel.js"), "."),
    (str(SPIKE / "vendor" / "gridstack"), "vendor/gridstack"),
]

# The current Task 0 baseline uses a Conda-distributed Python. Its stdlib
# extension modules resolve these DLLs from <base_prefix>/Library/bin at
# development time, so include them explicitly in the portable onedir proof.
conda_bin = Path(sys.base_prefix) / "Library" / "bin"
binaries = [
    (str(conda_bin / name), ".")
    for name in ("ffi.dll", "libcrypto-3-x64.dll", "liblzma.dll")
    if (conda_bin / name).is_file()
]

a = Analysis(
    [str(SPIKE / "main.py")],
    pathex=[str(SPIKE)],
    binaries=binaries,
    datas=datas,
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
    name="deskboard-task0-spike",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="deskboard-task0-spike",
)
