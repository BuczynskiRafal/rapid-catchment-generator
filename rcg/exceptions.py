"""
Custom exception hierarchy for RCG.

This module provides a structured exception hierarchy for the rapid-catchment-generator
project, enabling more precise error handling and better error messages.
"""


class RCGError(Exception):
    """
    Base exception for all RCG errors.

    All custom exceptions in the RCG project should inherit from this class
    to enable catching all RCG-related errors with a single except clause.

    Example
    -------
    >>> try:
    ...     # RCG operations
    ... except RCGError as e:
    ...     print(f"RCG error: {e}")
    """
    pass


class ValidationError(RCGError):
    """
    Exception raised for input validation errors.

    This exception is raised when user input fails validation checks,
    such as invalid file paths, out-of-range values, or invalid enum values.

    Attributes
    ----------
    field : str, optional
        Name of the field that failed validation.
    value : any, optional
        The invalid value that was provided.

    Example
    -------
    >>> raise ValidationError("Area must be positive", field="area", value=-5)
    """

    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigurationError(RCGError):
    """
    Exception raised for configuration-related errors.

    This exception is raised when there are issues with configuration files,
    missing configuration values, or invalid configuration formats.

    Attributes
    ----------
    config_file : str, optional
        Path to the configuration file that caused the error.

    Example
    -------
    >>> raise ConfigurationError("Invalid JSON format", config_file="rules.json")
    """

    def __init__(self, message: str, config_file: str = None):
        super().__init__(message)
        self.config_file = config_file


class FuzzyEngineError(RCGError):
    """
    Exception raised for fuzzy logic computation errors.

    This exception is raised when fuzzy inference fails, such as when
    there are no applicable rules for the given input or when computation
    produces invalid results.

    Attributes
    ----------
    land_form : int, optional
        Land form value that caused the error.
    land_cover : int, optional
        Land cover value that caused the error.

    Example
    -------
    >>> raise FuzzyEngineError("No rules match input", land_form=5, land_cover=10)
    """

    def __init__(self, message: str, land_form: int = None, land_cover: int = None):
        super().__init__(message)
        self.land_form = land_form
        self.land_cover = land_cover


class ModelOperationError(RCGError):
    """
    Exception raised for SWMM model operation errors.

    This exception is raised when operations on the SWMM model fail,
    such as when adding subcatchments, reading/writing INP files,
    or when model validation fails.

    Attributes
    ----------
    operation : str, optional
        Name of the operation that failed.
    model_path : str, optional
        Path to the model file.

    Example
    -------
    >>> raise ModelOperationError("Failed to add subcatchment", operation="add_subcatchment")
    """

    def __init__(self, message: str, operation: str = None, model_path: str = None):
        super().__init__(message)
        self.operation = operation
        self.model_path = model_path


class BackupError(RCGError):
    """
    Exception raised for backup/restore operation errors.

    This exception is raised when backup creation or restoration fails.

    Attributes
    ----------
    backup_path : str, optional
        Path to the backup file.

    Example
    -------
    >>> raise BackupError("Failed to create backup", backup_path="/path/to/backup.inp")
    """

    def __init__(self, message: str, backup_path: str = None):
        super().__init__(message)
        self.backup_path = backup_path


class RuleDefinitionError(RCGError):
    """
    Exception raised for fuzzy rule definition errors.

    This exception is raised when there are issues with defining fuzzy rules,
    such as missing conditions, invalid consequents, or duplicate rule names.

    Attributes
    ----------
    rule_name : str, optional
        Name of the rule that caused the error.

    Example
    -------
    >>> raise RuleDefinitionError("Rule has no conditions", rule_name="my_rule")
    """

    def __init__(self, message: str, rule_name: str = None):
        super().__init__(message)
        self.rule_name = rule_name
