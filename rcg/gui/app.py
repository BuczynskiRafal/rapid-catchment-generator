"""Application bootstrap: logging, QApplication, theme, main window."""

from __future__ import annotations

import logging
import signal
import sys
from collections.abc import Sequence
from pathlib import Path
from types import TracebackType

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QStandardPaths
from PySide6.QtGui import QFileOpenEvent, QIcon
from PySide6.QtWidgets import QApplication

from rcg.gui.main_window import APP_TITLE, MainWindow
from rcg.gui.resources import resource_path
from rcg.gui.theme import install_theme
from rcg.logging_config import log_file_path, setup_logging

__all__ = ["create_application", "main"]

ORGANIZATION = "BuczynskiRafal"
ORGANIZATION_DOMAIN = "github.com/BuczynskiRafal"
APP_USER_MODEL_ID = "BuczynskiRafal.RapidCatchmentGenerator"
LOG_FILE_NAME = "rcg-gui.log"
GUI_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

logger = logging.getLogger("rcg.gui")


def _set_application_identity() -> None:
    QCoreApplication.setOrganizationName(ORGANIZATION)
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(APP_TITLE)


def configure_logging() -> Path | None:
    """Log the ``rcg`` package to a rotating file in the per-user data folder.

    A windowed (frozen) build has no console, so the file is where tracebacks of
    unexpected errors end up; warnings also go to stderr when there is one. Returns the
    log path, or ``None`` if it is not writable. Safe to call more than once.
    """

    def setup(log_file: Path | None = None) -> None:
        setup_logging(
            logging.INFO,
            log_file=log_file,
            log_format=GUI_LOG_FORMAT,
            max_bytes=1_000_000,
            backup_count=3,
            console_level=logging.WARNING,
            propagate=True,
        )

    folder = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    if not folder:
        setup()
        return None
    try:
        setup(Path(folder) / LOG_FILE_NAME)
    except OSError:
        setup()
        logger.warning("Cannot write the log file in %s", folder, exc_info=True)
        return None
    return log_file_path()


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Return the (possibly existing) QApplication with identity, icon and theme set."""
    _set_application_identity()
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        app = QApplication(list(sys.argv if argv is None else argv))
    if sys.platform == "win32":  # group the taskbar button under our own icon
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except (AttributeError, OSError):
            pass
    icon_path = resource_path("icon.png")
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))
    install_theme(app)
    return app


class _FileOpenForwarder(QObject):
    """macOS delivers "Open with RCG" / dropped-on-Dock files as QFileOpenEvent, not argv."""

    def __init__(self, app: QApplication, window: MainWindow) -> None:
        super().__init__(app)
        self._window = window
        app.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.FileOpen and isinstance(event, QFileOpenEvent) and event.file():
            self._window.path_field.set_path(event.file())
            self._window.raise_()
            self._window.activateWindow()
            return True
        return False


def _model_argument(argv: Sequence[str]) -> str | None:
    """First positional argument ending in ``.inp`` (lets the OS 'Open with' the app)."""
    for arg in argv[1:]:
        if not arg.startswith("-") and arg.lower().endswith(".inp"):
            return arg
    return None


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``rcg-gui``; returns the process exit code."""
    args = list(sys.argv if argv is None else argv)
    _set_application_identity()
    log_path = configure_logging()
    app = create_application(args)
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Ctrl+C in a terminal closes the app

    window = MainWindow(log_path=log_path)
    _FileOpenForwarder(app, window)
    model = _model_argument(args)
    if model:
        window.path_field.set_path(model)

    previous_hook = sys.excepthook

    def excepthook(exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            previous_hook(exc_type, exc, tb)
            return
        logger.critical("Unhandled exception", exc_info=(exc_type, exc, tb))
        try:
            window.report_unexpected_error()
        except Exception:  # never let the hook itself raise
            pass

    sys.excepthook = excepthook
    try:
        window.show()
        return int(app.exec())
    finally:
        sys.excepthook = previous_hook
