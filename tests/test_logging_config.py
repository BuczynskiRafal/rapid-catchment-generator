"""Logging configuration shared by the CLI and the desktop app (``rcg.logging_config``)."""

from __future__ import annotations

import io
import logging
import sys

import pytest

from rcg.logging_config import get_logger, log_file_path, set_log_level, setup_logging

NAME = "rcg.test_logging"  # a child logger, so the real "rcg" configuration is not touched


@pytest.fixture
def clean_logger():
    logger = logging.getLogger(NAME)
    yield logger
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True


def test_console_and_file_levels(clean_logger, tmp_path, monkeypatch):
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stderr)
    log = tmp_path / "logs" / "rcg.log"
    setup_logging(logging.INFO, NAME, log_file=log, log_format="%(levelname)s %(message)s", console_level=logging.WARNING)
    clean_logger.info("to the file only")
    clean_logger.warning("to both")
    assert stderr.getvalue() == "WARNING to both\n"
    assert log.read_text(encoding="utf-8") == "INFO to the file only\nWARNING to both\n"
    assert log_file_path(NAME) == log
    assert clean_logger.propagate is False


def test_console_follows_the_current_stderr(clean_logger, monkeypatch):
    setup_logging(logging.WARNING, NAME, log_format="%(message)s")
    later = io.StringIO()
    monkeypatch.setattr(sys, "stderr", later)  # swapped after setup, as pytest and IDEs do
    clean_logger.warning("hello")
    assert later.getvalue() == "hello\n"


def test_second_call_replaces_only_its_own_handlers(clean_logger, tmp_path):
    foreign = logging.NullHandler()
    clean_logger.addHandler(foreign)
    setup_logging(logging.INFO, NAME, log_file=tmp_path / "a.log")
    setup_logging(logging.DEBUG, NAME, log_file=tmp_path / "b.log", propagate=True)
    files = [h for h in clean_logger.handlers if isinstance(h, logging.FileHandler)]
    assert [h.baseFilename for h in files] == [str(tmp_path / "b.log")]
    assert foreign in clean_logger.handlers
    assert (clean_logger.level, clean_logger.propagate) == (logging.DEBUG, True)


def test_unwritable_log_file_leaves_the_logger_unchanged(clean_logger, tmp_path):
    setup_logging(logging.INFO, NAME)
    before = list(clean_logger.handlers)
    blocker = tmp_path / "file"
    blocker.write_text("")
    with pytest.raises(OSError):
        setup_logging(logging.DEBUG, NAME, log_file=blocker / "rcg.log")  # parent is a file
    assert clean_logger.handlers == before
    assert clean_logger.level == logging.INFO


def test_no_console_without_stderr(clean_logger, monkeypatch):
    monkeypatch.setattr(sys, "stderr", None)  # windowed build
    setup_logging(logging.INFO, NAME)
    assert clean_logger.handlers == []
    assert log_file_path(NAME) is None


def test_set_log_level(clean_logger):
    setup_logging(logging.INFO, NAME)
    set_log_level(logging.ERROR, "test_logging")
    assert get_logger("test_logging") is clean_logger
    assert clean_logger.level == logging.ERROR
    assert all(h.level == logging.ERROR for h in clean_logger.handlers)


def test_cli_logs_warnings_to_stderr(capsys):
    from rcg.cli import main

    assert main(["list-options"]) == 0
    get_logger("cli").warning("careful")
    get_logger("cli").info("hidden")
    assert capsys.readouterr().err == "WARNING rcg.cli: careful\n"
