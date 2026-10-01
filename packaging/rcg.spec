# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the ``rcg`` command-line tool (console application).

Build from the repository root (with PyInstaller installed; the GUI extra is not needed):

    pyinstaller packaging/rcg.spec

The result is a single-file console executable ``dist/rcg[.exe]``. Set
``RCG_ONEDIR=1`` for a folder build instead (faster start-up, fewer antivirus false
positives).

Runtime data: ``rcg/config/defaults.json`` (loaded relative to ``rcg/config/loader.py``)
and swmmio's section definitions (``swmmio/defs/*.yml``, read at import time).
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 - SPECPATH is injected by PyInstaller
ONEDIR = os.environ.get("RCG_ONEDIR") == "1"


def _not_tests(name: str) -> bool:
    return ".tests" not in name and not name.endswith(".conftest")


datas = [
    (str(ROOT / "rcg" / "config" / "defaults.json"), "rcg/config"),
    (str(ROOT / "rcg" / "example.inp"), "rcg"),
]
datas += collect_data_files("swmmio", excludes=["tests", "tests/**", "**/tests/**"])

hiddenimports = [
    *collect_submodules("skfuzzy", filter=_not_tests),
    *collect_submodules("swmmio", filter=_not_tests),
]

a = Analysis(
    [str(ROOT / "rcg" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # The console tool never needs Qt or a matplotlib GUI backend (rcg selects Agg).
    excludes=["tkinter", "PySide6", "shiboken6", "rcg.gui", "pytest", "pytestqt", "IPython", "notebook"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if ONEDIR:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="rcg",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, upx_exclude=[], name="rcg")
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="rcg",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
