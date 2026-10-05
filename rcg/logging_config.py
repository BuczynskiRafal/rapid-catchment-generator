"""Logging helpers for RCG.

Library modules log through :func:`get_logger` and never configure handlers
themselves; applications (CLI, GUI) decide where records go, e.g. with
:func:`setup_logging`.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

__all__ = [
    "DEFAULT_DATE_FORMAT",
    "DEFAULT_FORMAT",
    "LOGGER_NAME",
    "get_logger",
    "log_file_path",
    "set_log_level",
    "setup_logging",
]

DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOGGER_NAME = "rcg"
_OWNED = "_rcg_setup_logging"  # marks the handlers setup_logging installed (replaced on the next call)

# Library etiquette: stay silent unless the application configures logging.
logging.getLogger(LOGGER_NAME).addHandler(logging.NullHandler())


def get_logger(name: str | None = None) -> logging.Logger:
    """Return the ``rcg`` logger, or its child ``rcg.<name>``.

    Examples
    --------
    >>> get_logger("fuzzy.engine").name
    'rcg.fuzzy.engine'
    """
    return logging.getLogger(LOGGER_NAME if name is None else f"{LOGGER_NAME}.{name}")


class _StderrHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """Write to whatever ``sys.stderr`` is at emit time (tests, IDEs and pythonw swap it)."""

    @property  # type: ignore[override]
    def stream(self) -> Any:
        return sys.stderr

    @stream.setter
    def stream(self, _value: Any) -> None:  # StreamHandler.__init__ assigns it
        pass


def setup_logging(
    level: int = logging.INFO,
    name: str = LOGGER_NAME,
    log_file: Path | None = None,
    log_format: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    *,
    console_level: int | None = None,
    propagate: bool = False,
) -> logging.Logger:
    """Configure a logger for an application: stderr output plus an optional rotating file.

    Calling it again replaces the handlers an earlier call installed (and closes them);
    handlers added by anyone else are left alone. The CLI and the desktop app both
    configure logging through this function.

    Parameters
    ----------
    level : int
        Level of the logger and of the file, e.g. ``logging.DEBUG``.
    name : str
        Logger to configure (default ``"rcg"``).
    log_file : Path, optional
        Also write records to this file (rotated at ``max_bytes``, ``backup_count`` kept).
    log_format, date_format : str
        Record and timestamp formats.
    max_bytes, backup_count : int
        Rotation settings for ``log_file``.
    console_level : int, optional
        Level of the stderr output; defaults to ``level``. No stderr handler is added
        when the process has no ``sys.stderr`` (a windowed build).
    propagate : bool, optional
        Let records reach the root logger's handlers too (default ``False``).

    Returns
    -------
    logging.Logger
        The configured logger.

    Raises
    ------
    OSError
        If ``log_file`` cannot be opened. The logger is left unchanged then.
    """
    formatter = logging.Formatter(log_format, datefmt=date_format)
    handlers: list[logging.Handler] = []
    if log_file is not None:  # first: if the file cannot be opened, nothing has changed yet
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"))
        handlers[-1].setLevel(level)
    if sys.stderr is not None:
        console = _StderrHandler()
        console.setLevel(level if console_level is None else console_level)
        handlers.append(console)

    logger = logging.getLogger(name)
    for old in [h for h in logger.handlers if getattr(h, _OWNED, False)]:
        logger.removeHandler(old)
        old.close()
    for handler in handlers:
        handler.setFormatter(formatter)
        setattr(handler, _OWNED, True)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = propagate
    return logger


def log_file_path(name: str = LOGGER_NAME) -> Path | None:
    """Return the file :func:`setup_logging` writes the logger *name* to, if any."""
    for handler in logging.getLogger(name).handlers:
        if getattr(handler, _OWNED, False) and isinstance(handler, RotatingFileHandler):
            return Path(handler.baseFilename)
    return None


def set_log_level(level: int, name: str | None = None) -> None:
    """Set the level of an RCG logger and of its handlers."""
    logger = get_logger(name)
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
