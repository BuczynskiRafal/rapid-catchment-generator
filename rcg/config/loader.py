"""
Configuration loader for RCG.

This module provides utilities for loading JSON configuration files,
including rules and default parameters.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from rcg.exceptions import ConfigurationError


@dataclass
class RuleConfig:
    """
    Configuration for a single fuzzy rule.

    Attributes
    ----------
    name : str
        Unique identifier for the rule.
    conditions : Dict[str, str]
        Mapping of variable names to condition values (land_form, land_cover).
    consequences : Dict[str, str]
        Mapping of output types to consequence values (slope, impervious, catchment).
    """

    name: str
    conditions: dict[str, str]
    consequences: dict[str, str]


@dataclass
class DefaultsConfig:
    """
    Configuration for default parameters.

    Attributes
    ----------
    manning_coefficients : Dict[str, Tuple[float, float]]
        Manning's n coefficients for each catchment type.
    depression_storage : Dict[str, Tuple[float, float, int]]
        Depression storage parameters for each catchment type.
    infiltration_defaults : Dict[str, Any]
        Default infiltration parameters.
    validation_limits : Dict[str, Any]
        Validation limits for input parameters.
    """

    manning_coefficients: dict[str, tuple[float, float]] = field(default_factory=dict)
    depression_storage: dict[str, tuple[float, float, int]] = field(default_factory=dict)
    infiltration_defaults: dict[str, Any] = field(default_factory=dict)
    validation_limits: dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    """
    Loader for JSON configuration files.

    Provides caching and validation of configuration data.

    Attributes
    ----------
    config_dir : Path
        Directory containing configuration files.

    Example
    -------
    >>> loader = ConfigLoader()
    >>> rules = loader.load_rules()
    >>> defaults = loader.load_defaults()
    """

    _instance: Optional["ConfigLoader"] = None
    _rules_cache: Optional[list[RuleConfig]] = None
    _defaults_cache: Optional[DefaultsConfig] = None

    def __new__(cls, config_dir: Optional[Path] = None) -> "ConfigLoader":
        """Singleton pattern for configuration loader."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration loader.

        Parameters
        ----------
        config_dir : Optional[Path]
            Directory containing configuration files.
            Defaults to the package's config directory.
        """
        if self._initialized:
            return

        if config_dir is None:
            config_dir = Path(__file__).parent
        self.config_dir = config_dir
        self._initialized = True

    def load_rules(self, force_reload: bool = False) -> list[RuleConfig]:
        """
        Load fuzzy rules from configuration.

        Parameters
        ----------
        force_reload : bool
            If True, bypasses the cache and reloads from file.

        Returns
        -------
        List[RuleConfig]
            List of rule configurations.

        Raises
        ------
        ConfigurationError
            If the rules file is invalid or cannot be read.
        """
        if self._rules_cache is not None and not force_reload:
            return self._rules_cache

        rules_path = self.config_dir / "rules.json"

        if not rules_path.exists():
            # Return empty list if no config file (use programmatic rules)
            return []

        try:
            with open(rules_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in rules file: {e}", config_file=str(rules_path)) from e
        except OSError as e:
            raise ConfigurationError(f"Cannot read rules file: {e}", config_file=str(rules_path)) from e

        rules = []
        for rule_data in data.get("rules", []):
            try:
                rule = RuleConfig(name=rule_data["name"], conditions=rule_data["when"], consequences=rule_data["then"])
                rules.append(rule)
            except KeyError as e:
                raise ConfigurationError(f"Missing required field in rule: {e}", config_file=str(rules_path)) from e

        self._rules_cache = rules
        return rules

    def load_defaults(self, force_reload: bool = False) -> DefaultsConfig:
        """
        Load default parameters from configuration.

        Parameters
        ----------
        force_reload : bool
            If True, bypasses the cache and reloads from file.

        Returns
        -------
        DefaultsConfig
            Default configuration parameters.

        Raises
        ------
        ConfigurationError
            If the defaults file is invalid or cannot be read.
        """
        if self._defaults_cache is not None and not force_reload:
            return self._defaults_cache

        defaults_path = self.config_dir / "defaults.json"

        if not defaults_path.exists():
            # Return empty defaults if no config file
            return DefaultsConfig()

        try:
            with open(defaults_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in defaults file: {e}", config_file=str(defaults_path)) from e
        except OSError as e:
            raise ConfigurationError(f"Cannot read defaults file: {e}", config_file=str(defaults_path)) from e

        # Convert list values to tuples for manning coefficients and depression storage
        manning = {}
        for key, value in data.get("manning_coefficients", {}).items():
            if key != "description" and isinstance(value, list):
                manning[key] = tuple(value)

        depression = {}
        for key, value in data.get("depression_storage", {}).items():
            if key != "description" and isinstance(value, list):
                depression[key] = tuple(value)

        defaults = DefaultsConfig(
            manning_coefficients=manning,
            depression_storage=depression,
            infiltration_defaults=data.get("infiltration_defaults", {}),
            validation_limits=data.get("validation_limits", {}),
        )

        self._defaults_cache = defaults
        return defaults

    def clear_cache(self) -> None:
        """Clear all cached configuration data."""
        self._rules_cache = None
        self._defaults_cache = None


# Module-level convenience functions


def load_rules_config(config_dir: Optional[Path] = None) -> list[RuleConfig]:
    """
    Load fuzzy rules from configuration.

    Parameters
    ----------
    config_dir : Optional[Path]
        Directory containing configuration files.

    Returns
    -------
    List[RuleConfig]
        List of rule configurations.
    """
    loader = ConfigLoader(config_dir)
    return loader.load_rules()


def load_defaults_config(config_dir: Optional[Path] = None) -> DefaultsConfig:
    """
    Load default parameters from configuration.

    Parameters
    ----------
    config_dir : Optional[Path]
        Directory containing configuration files.

    Returns
    -------
    DefaultsConfig
        Default configuration parameters.
    """
    loader = ConfigLoader(config_dir)
    return loader.load_defaults()
