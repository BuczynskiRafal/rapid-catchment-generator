"""Packaged configuration (``defaults.json``) and its loader."""

from .loader import DEFAULTS_PATH, Defaults, load_defaults

__all__ = ["DEFAULTS_PATH", "Defaults", "load_defaults"]
