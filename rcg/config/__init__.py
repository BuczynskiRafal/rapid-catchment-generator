"""
Configuration management for RCG.

This package provides JSON-based configuration for fuzzy rules and default parameters.
"""
from .loader import ConfigLoader, RuleConfig, load_rules_config, load_defaults_config

__all__ = ["ConfigLoader", "RuleConfig", "load_rules_config", "load_defaults_config"]
