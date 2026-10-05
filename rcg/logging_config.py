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

DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOGGER_NAME = "rcg"

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


def setup_logging(
    level: int = logging.INFO,
    name: str = LOGGER_NAME,
    log_file: Path | None = None,
    log_format: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure a logger for an application: stderr output plus an optional rotating file.

    Existing handlers on that logger are replaced and propagation is turned off.

    Parameters
    ----------
    level : int
        Logging level, e.g. ``logging.DEBUG``.
    name : str
        Logger to configure (default ``"rcg"``).
    log_file : Path, optional
        Also write records to this file (rotated at ``max_bytes``, ``backup_count`` kept).
    log_format, date_format : str
        Record and timestamp formats.
    max_bytes, backup_count : int
        Rotation settings for ``log_file``.

    Returns
    -------
    logging.Logger
        The configured logger.
    """
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(level)
    formatter = logging.Formatter(log_format, datefmt=date_format)

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def set_log_level(level: int, name: str | None = None) -> None:
    """Set the level of an RCG logger and of its handlers."""
    logger = get_logger(name)
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
