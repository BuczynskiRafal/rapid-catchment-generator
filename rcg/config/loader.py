"""Load the canonical default parameters from ``defaults.json``.

``defaults.json`` is the single source of truth for Manning coefficients,
depression storage, infiltration defaults (per SWMM infiltration method) and
validation limits.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from types import MappingProxyType
from typing import Any

from rcg.exceptions import ConfigurationError

DEFAULTS_PATH = Path(__file__).resolve().with_name("defaults.json")

INFILTRATION_DEFAULT_METHODS = ("GREEN_AMPT", "HORTON", "CURVE_NUMBER")
"""Infiltration methods ``defaults.json`` must define (``MODIFIED_*`` reuse these)."""


@dataclass(frozen=True)
class Defaults:
    """Read-only view of ``defaults.json``.

    Attributes
    ----------
    manning_coefficients : Mapping[str, tuple[float, float]]
        ``(n_imperv, n_perv)`` per catchment type.
    depression_storage : Mapping[str, tuple[float, float, int]]
        ``(s_imperv_in, s_perv_in, pct_zero)`` per catchment type. Storage depths are in
        inches, as in 1.x; callers convert to millimetres.
    infiltration : Mapping[str, float]
        Green-Ampt parameters (``Suction``, ``Ksat``, ``IMD``, ``Param4``, ``Param5``);
        the same mapping as ``infiltration_by_method["GREEN_AMPT"]``.
    infiltration_by_method : Mapping[str, Mapping[str, float]]
        Ordered ``[INFILTRATION]`` values for ``GREEN_AMPT``, ``HORTON`` and
        ``CURVE_NUMBER`` (the ``MODIFIED_*`` variants share their base method's row).
    validation_limits : Mapping[str, Any]
        Input validation limits (``area_max_hectares``, ...).
    """

    manning_coefficients: Mapping[str, tuple[float, float]]
    depression_storage: Mapping[str, tuple[float, float, int]]
    infiltration: Mapping[str, float]
    infiltration_by_method: Mapping[str, Mapping[str, float]]
    validation_limits: Mapping[str, Any]


def _section(data: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    try:
        section = data[key]
    except KeyError as e:
        raise ConfigurationError(f"Missing section '{key}' in defaults file", config_file=str(path)) from e
    if not isinstance(section, dict):
        raise ConfigurationError(f"Section '{key}' must be an object", config_file=str(path))
    return {k: v for k, v in section.items() if k != "description"}


def _object(value: Any, key: str, path: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"'{key}' must be an object", config_file=str(path))
    return value


def _parse(data: dict[str, Any], path: Path) -> Defaults:
    try:
        manning = {k: (float(v[0]), float(v[1])) for k, v in _section(data, "manning_coefficients", path).items()}
        storage = {k: (float(v[0]), float(v[1]), int(v[2])) for k, v in _section(data, "depression_storage", path).items()}
        infiltration = {
            method.upper(): MappingProxyType({k: float(v) for k, v in _object(values, method, path).items()})
            for method, values in _section(data, "infiltration_defaults", path).items()
        }
    except (TypeError, ValueError, IndexError) as e:
        raise ConfigurationError(f"Malformed value in defaults file: {e}", config_file=str(path)) from e

    if set(manning) != set(storage):
        raise ConfigurationError(
            "manning_coefficients and depression_storage must define the same catchment types", config_file=str(path)
        )
    missing = [m for m in INFILTRATION_DEFAULT_METHODS if m not in infiltration]
    if missing:
        raise ConfigurationError(f"infiltration_defaults must define {', '.join(missing)}", config_file=str(path))
    return Defaults(
        manning_coefficients=MappingProxyType(manning),
        depression_storage=MappingProxyType(storage),
        infiltration=infiltration["GREEN_AMPT"],
        infiltration_by_method=MappingProxyType(infiltration),
        validation_limits=MappingProxyType(_section(data, "validation_limits", path)),
    )


def load_defaults(path: str | Path | None = None) -> Defaults:
    """Load the default parameters (cached per file).

    Parameters
    ----------
    path : str or Path, optional
        JSON file to read. Defaults to the packaged ``defaults.json``.

    Returns
    -------
    Defaults
        Parsed, read-only defaults.

    Raises
    ------
    ConfigurationError
        If the file cannot be read or is malformed.
    """
    return _load(DEFAULTS_PATH if path is None else Path(path).resolve())


@cache
def _load(path: Path) -> Defaults:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise ConfigurationError(f"Cannot read defaults file: {e}", config_file=str(path)) from e
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in defaults file: {e}", config_file=str(path)) from e
    if not isinstance(data, dict):
        raise ConfigurationError("Defaults file must contain a JSON object", config_file=str(path))
    return _parse(data, path)
