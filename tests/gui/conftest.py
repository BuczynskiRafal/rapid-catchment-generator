"""Fixtures for the headless GUI tests (pytest-qt, ``QT_QPA_PLATFORM=offscreen``).

Without PySide6 or pytest-qt the GUI tests are skipped, unless ``RCG_REQUIRE_GUI_TESTS``
is set (CI sets it): then a missing dependency fails the run instead of silently
skipping every GUI test.
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REQUIRE_ENV = "RCG_REQUIRE_GUI_TESTS"


def gui_tests_required(environ: Mapping[str, str] = os.environ) -> bool:
    """True when ``RCG_REQUIRE_GUI_TESTS`` is set to anything but empty, ``0``, ``false`` or ``no``."""
    return environ.get(REQUIRE_ENV, "").strip().lower() not in ("", "0", "false", "no")


def require_module(name: str, *, required: bool) -> ModuleType:
    """Import *name*; when it is missing, fail if *required*, otherwise skip."""
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        if required:
            pytest.fail(f"{name} is required for the GUI tests ({REQUIRE_ENV} is set) but cannot be imported: {exc}")
        pytest.skip(f"{name} is not installed; GUI tests skipped", allow_module_level=True)


require_module("PySide6", required=gui_tests_required())
require_module("pytestqt", required=gui_tests_required())

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtGui import QFont  # noqa: E402

EXAMPLE_INP = Path(__file__).resolve().parents[2] / "rcg" / "example.inp"
SCREENSHOT_ENV = "RCG_GUI_SCREENSHOT_DIR"
ENGINE_TIMEOUT_MS = 120_000


@pytest.fixture
def gui_requirements() -> SimpleNamespace:
    """The dependency check above, for testing it."""
    return SimpleNamespace(require_module=require_module, gui_tests_required=gui_tests_required)


@pytest.fixture(scope="session")
def rcg_app(qapp):
    """The pytest-qt QApplication, with the RCG identity, icon and theme installed."""
    from rcg.gui.app import create_application
    from rcg.gui.theme import install_theme

    app = create_application()
    if sys.platform == "darwin" and app.platformName() == "offscreen":
        # The offscreen platform has no font configuration and renders at 96 dpi, while
        # macOS lays out at 72: use the macOS system font at its real pixel size (13 px)
        # so screenshots and size checks match the application on a Mac.
        font = QFont(".AppleSystemUIFont")
        font.setPointSizeF(13 * 72 / app.primaryScreen().logicalDotsPerInch())
        app.setFont(font)
        install_theme(app)  # rebuild the style sheet for this font now, not on the next event loop pass
    return app


@pytest.fixture(scope="session")
def gui_engine():
    """The shared, warmed-up fuzzy engine (built once per session)."""
    from rcg import service

    return service.warm_up()


@pytest.fixture
def gui_settings(tmp_path: Path) -> QSettings:
    """Settings in a temporary INI file, so tests never touch the user's settings."""
    return QSettings(str(tmp_path / "rcg-gui.ini"), QSettings.Format.IniFormat)


@pytest.fixture
def model_copy(tmp_path: Path) -> Path:
    """A writable copy of the bundled example model."""
    target = tmp_path / "models" / "example.inp"
    target.parent.mkdir()
    shutil.copy2(EXAMPLE_INP, target)
    return target


@pytest.fixture
def window(qtbot, rcg_app, gui_engine, gui_settings) -> Iterator:
    """A shown main window whose engine is ready and whose first preview is displayed."""
    from rcg.gui.main_window import MainWindow

    win = MainWindow(gui_settings, engine=gui_engine)
    qtbot.addWidget(win)
    win.resize(1120, 740)
    win.show()
    qtbot.waitExposed(win)
    qtbot.waitUntil(lambda: win.engine_ready, timeout=ENGINE_TIMEOUT_MS)
    qtbot.waitUntil(lambda: win.current_parameters() is not None, timeout=10_000)
    yield win


@pytest.fixture
def screenshot_dirs(tmp_path: Path) -> list[Path]:
    """Where screenshots go: always the test's tmp dir, plus ``$RCG_GUI_SCREENSHOT_DIR`` if set."""
    dirs = [tmp_path]
    extra = os.environ.get(SCREENSHOT_ENV)
    if extra:
        path = Path(extra)
        path.mkdir(parents=True, exist_ok=True)
        dirs.append(path)
    return dirs
