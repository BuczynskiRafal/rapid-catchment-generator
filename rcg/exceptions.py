"""Exception hierarchy for RCG.

Every error raised on purpose by the library derives from :class:`RCGError`, so callers
(the CLI, the GUI) can show ``str(error)`` to the user and treat anything else as a bug.
"""

from __future__ import annotations

from typing import Any


class RCGError(Exception):
    """Base class for all RCG errors."""


class ValidationError(RCGError):
    """Invalid user input (area, category, file path, ...).

    Attributes
    ----------
    field : str or None
        Name of the offending input.
    value : Any
        The rejected value.
    """

    def __init__(self, message: str, field: str | None = None, value: Any = None) -> None:
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigurationError(RCGError):
    """A packaged configuration file is missing or malformed.

    Attributes
    ----------
    config_file : str or None
        Path of the offending file.
    """

    def __init__(self, message: str, config_file: str | None = None) -> None:
        super().__init__(message)
        self.config_file = config_file


class FuzzyEngineError(RCGError, ValueError):
    """Fuzzy inference failed or was given inputs outside the category ranges.

    Also a :class:`ValueError`: 2.0.0 raised plain ``ValueError`` for out-of-range inputs.

    Attributes
    ----------
    land_form, land_cover : int or None
        Inputs that caused the failure.
    """

    def __init__(self, message: str, land_form: int | None = None, land_cover: int | None = None) -> None:
        super().__init__(message)
        self.land_form = land_form
        self.land_cover = land_cover


class ModelOperationError(RCGError):
    """Reading, editing or writing a SWMM model failed.

    Attributes
    ----------
    operation : str or None
        Step that failed (``read``, ``verify``, ``backup``, ``write``, ...).
    model_path : str or None
        Model file involved.
    """

    def __init__(self, message: str, operation: str | None = None, model_path: str | None = None) -> None:
        super().__init__(message)
        self.operation = operation
        self.model_path = model_path


class BackupError(RCGError):
    """Creating or restoring a backup failed.

    Attributes
    ----------
    backup_path : str or None
        Backup file involved.
    """

    def __init__(self, message: str, backup_path: str | None = None) -> None:
        super().__init__(message)
        self.backup_path = backup_path


class RuleDefinitionError(RCGError, ValueError):
    """A fuzzy rule is malformed.

    Also a :class:`ValueError`: 2.0.0 raised plain ``ValueError`` for these mistakes.

    Attributes
    ----------
    rule_name : str or None
        Name of the offending rule.
    """

    def __init__(self, message: str, rule_name: str | None = None) -> None:
        super().__init__(message)
        self.rule_name = rule_name
