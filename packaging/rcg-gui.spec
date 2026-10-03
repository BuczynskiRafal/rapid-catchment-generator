# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the windowed RCG desktop application.

Build from the repository root (with the ``gui`` extra and PyInstaller installed):

    pyinstaller packaging/rcg-gui.spec

* Windows / Linux: a single-file executable ``dist/RCG[.exe]``.
  Set ``RCG_ONEDIR=1`` for a folder build instead (faster start-up, fewer antivirus
  false positives).
* macOS: an application bundle ``dist/RCG.app`` (folder build; PyInstaller does not
  support single-file app bundles). Converting ``icon.png`` to ``.icns`` needs Pillow.

Runtime data: ``rcg/config/defaults.json`` (loaded relative to ``rcg/config/loader.py``)
and ``rcg/gui/resources/*`` (loaded via importlib.resources, falling back to
``sys._MEIPASS/rcg/gui/resources``).
"""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 - SPECPATH is injected by PyInstaller
RESOURCES = ROOT / "rcg" / "gui" / "resources"
ONEDIR = sys.platform == "darwin" or os.environ.get("RCG_ONEDIR") == "1"
ICON = str(RESOURCES / ("icon.ico" if sys.platform == "win32" else "icon.png"))


def _not_tests(name: str) -> bool:
    return ".tests" not in name and not name.endswith(".conftest")


datas = [
    (str(ROOT / "rcg" / "config" / "defaults.json"), "rcg/config"),
    *[(str(path), "rcg/gui/resources") for path in sorted(RESOURCES.iterdir()) if path.suffix in {".md", ".png", ".ico"}],
]
# swmmio reads its section definitions (defs/*.yml) at import time.
datas += collect_data_files("swmmio", excludes=["tests", "tests/**", "**/tests/**"])

hiddenimports = [
    *collect_submodules("skfuzzy", filter=_not_tests),
    *collect_submodules("swmmio", filter=_not_tests),
]

a = Analysis(
    [str(ROOT / "rcg" / "gui" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "pytestqt", "IPython", "notebook"],
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
        name="RCG",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=ICON,
    )
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, upx_exclude=[], name="RCG")
    if sys.platform == "darwin":
        app = BUNDLE(
            coll,
            name="RCG.app",
            icon=ICON,
            bundle_identifier="io.github.buczynskirafal.rcg",
            info_plist={
                "CFBundleDisplayName": "Rapid Catchment Generator",
                "NSHighResolutionCapable": True,
                "NSRequiresAquaSystemAppearance": False,  # follow the system dark mode
                "CFBundleDocumentTypes": [
                    {"CFBundleTypeName": "SWMM model", "CFBundleTypeExtensions": ["inp"], "CFBundleTypeRole": "Editor"}
                ],
            },
        )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="RCG",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=ICON,
    )
