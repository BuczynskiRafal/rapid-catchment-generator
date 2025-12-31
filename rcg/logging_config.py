"""
Centralized logging configuration for RCG.

This module provides a unified logging setup for the rapid-catchment-generator
project, ensuring consistent log formatting and handling across all modules.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Package logger name
LOGGER_NAME = "rcg"


def setup_logging(
    level: int = logging.INFO,
    name: str = LOGGER_NAME,
    log_file: Optional[Path] = None,
    log_format: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Set up centralized logging configuration.

    Creates and configures a logger with console output and optional file output.
    Uses RotatingFileHandler for file logging to manage log file sizes.

    Parameters
    ----------
    level : int
        Logging level (e.g., logging.DEBUG, logging.INFO).
        Default is logging.INFO.
    name : str
        Logger name. Default is "rcg".
    log_file : Optional[Path]
        Path to log file. If provided, logs will also be written to this file.
    log_format : str
        Log message format string.
    date_format : str
        Date format string for log timestamps.
    max_bytes : int
        Maximum size of log file before rotation (default: 10 MB).
    backup_count : int
        Number of backup log files to keep (default: 5).

    Returns
    -------
    logging.Logger
        Configured logger instance.

    Example
    -------
    >>> from rcg.logging_config import setup_logging
    >>> logger = setup_logging(level=logging.DEBUG)
    >>> logger.info("Application started")
    """
    # Get or create logger
    logger = logging.getLogger(name)

    # Clear any existing handlers
    logger.handlers.clear()

    # Set level
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if log_file is specified
    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    If no name is provided, returns the root RCG logger.
    If a name is provided, returns a child logger of the RCG logger.

    Parameters
    ----------
    name : Optional[str]
        Module name for the logger. If None, returns the root RCG logger.

    Returns
    -------
    logging.Logger
        Logger instance.

    Example
    -------
    >>> from rcg.logging_config import get_logger
    >>> logger = get_logger("fuzzy.engine")
    >>> logger.debug("Computing fuzzy values...")
    """
    if name is None:
        return logging.getLogger(LOGGER_NAME)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def set_log_level(level: int, name: Optional[str] = None) -> None:
    """
    Set the logging level for a logger.

    Parameters
    ----------
    level : int
        Logging level (e.g., logging.DEBUG, logging.INFO).
    name : Optional[str]
        Logger name. If None, sets level for root RCG logger.

    Example
    -------
    >>> from rcg.logging_config import set_log_level
    >>> import logging
    >>> set_log_level(logging.DEBUG)
    """
    logger = get_logger(name)
    logger.setLevel(level)

    # Also update all handlers
    for handler in logger.handlers:
        handler.setLevel(level)


# Default logger instance (lazy initialization)
_default_logger: Optional[logging.Logger] = None


def get_default_logger() -> logging.Logger:
    """
    Get the default RCG logger, initializing if necessary.

    This function provides a convenient way to get a pre-configured logger
    without explicitly calling setup_logging().

    Returns
    -------
    logging.Logger
        The default RCG logger.
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging()
    return _default_logger
