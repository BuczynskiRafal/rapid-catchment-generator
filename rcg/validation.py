"""Input validation shared by the service, the CLI and the GUI.

Every validator raises :class:`rcg.exceptions.ValidationError` with a message that can
be shown to a user as-is.
"""

from __future__ import annotations

import difflib
import math
import numbers
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TypeVar

from rcg.catchment import (
    KNOWN_INFILTRATION_KEYS,
    LAND_COVER_LABELS,
    LAND_FORM_LABELS,
    SubcatchmentParameters,
    lookup_land_cover,
    lookup_land_form,
)
from rcg.config import load_defaults
from rcg.exceptions import ValidationError
from rcg.fuzzy.categories import LandCover, LandForm

__all__ = [
    "KNOWN_INFILTRATION_KEYS",
    "max_area_ha",
    "min_area_ha",
    "validate_area",
    "validate_inp_path",
    "validate_land_cover",
    "validate_land_form",
    "validate_parameters",
]

_E = TypeVar("_E", LandForm, LandCover)


def max_area_ha() -> float:
    """Return the largest accepted area in hectares (``validation_limits`` in ``defaults.json``)."""
    return float(load_defaults().validation_limits.get("area_max_hectares", 10_000))


def min_area_ha() -> float:
    """Return the smallest accepted area in hectares (``validation_limits`` in ``defaults.json``).

    The limit keeps every written area visible at the writer's six-decimal precision.
    """
    return float(load_defaults().validation_limits.get("area_min_hectares", 0.0001))


def validate_area(value: float | int | str) -> float:
    """Validate a subcatchment area in hectares.

    Parameters
    ----------
    value : float, int or str
        Area; strings are parsed as floats.

    Returns
    -------
    float
        The area as a Python float.

    Raises
    ------
    ValidationError
        If the value is not a finite number in ``[min_area_ha(), max_area_ha()]``.
    """
    if isinstance(value, bool):
        raise ValidationError(f"Area must be a number, got: {value!r}", field="area", value=value)
    try:
        area = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"Area must be a number, got: {value!r}", field="area", value=value) from None
    if not math.isfinite(area) or area <= 0:
        raise ValidationError(f"Area must be a positive number of hectares, got: {value!r}", field="area", value=value)
    minimum = min_area_ha()
    if area < minimum:
        raise ValidationError(f"Area must be at least {minimum:g} ha, got: {area:g}", field="area", value=value)
    limit = max_area_ha()
    if area > limit:
        raise ValidationError(f"Area must not exceed {limit:g} ha, got: {area:g}", field="area", value=value)
    return area


def _finite(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number, got: {value!r}", field=field_name, value=value)
    number = float(value)
    if not math.isfinite(number):
        raise ValidationError(f"{field_name} must be a finite number, got: {value!r}", field=field_name, value=value)
    return number


# field -> (lower bound, lower bound inclusive, upper bound) for every numeric value written.
_PARAMETER_BOUNDS: dict[str, tuple[float, bool, float]] = {
    "impervious_pct": (0.0, True, 100.0),
    "slope_pct": (0.0, True, math.inf),
    "width_m": (0.0, False, math.inf),
    "n_imperv": (0.0, False, math.inf),
    "n_perv": (0.0, False, math.inf),
    "s_imperv_mm": (0.0, True, math.inf),
    "s_perv_mm": (0.0, True, math.inf),
    "pct_zero": (0.0, True, 100.0),
}


def validate_parameters(parameters: SubcatchmentParameters) -> SubcatchmentParameters:
    """Check every value of ``parameters`` before it is written to a model.

    :func:`rcg.preview` always produces valid values; this guards hand-made or
    modified :class:`~rcg.catchment.SubcatchmentParameters`.

    Returns
    -------
    SubcatchmentParameters
        The same object.

    Raises
    ------
    ValidationError
        If a value is not a finite number or is outside its SWMM range: valid
        categories (``land_form`` and ``land_cover``), area within the accepted
        limits, ``0 <= impervious_pct <= 100``, ``slope_pct >= 0``,
        ``0 <= catchment_score <= 100``, valid ``catchment_type``,
        ``width_m > 0``, Manning's n ``> 0``, depression storage ``>= 0``,
        ``0 <= pct_zero <= 100`` and infiltration values ``>= 0`` for known keys.
    """
    if not isinstance(parameters, SubcatchmentParameters):
        raise ValidationError(
            f"Expected SubcatchmentParameters, got {type(parameters).__name__}", field="parameters", value=parameters
        )
    validate_land_form(parameters.land_form)
    validate_land_cover(parameters.land_cover)
    validate_area(_finite(parameters.area_ha, "area_ha"))
    score = _finite(parameters.catchment_score, "catchment_score")
    if not (0.0 <= score <= 100.0):
        raise ValidationError(
            f"catchment_score must be between 0 and 100, got: {score}",
            field="catchment_score",
            value=score,
        )
    valid_types = {"urban", "suburban", "rural", "forests", "meadows", "arable", "mountains"}
    if not isinstance(parameters.catchment_type, str) or parameters.catchment_type not in valid_types:
        raise ValidationError(
            f"Invalid catchment_type {parameters.catchment_type!r}; expected one of {', '.join(sorted(valid_types))}",
            field="catchment_type",
            value=parameters.catchment_type,
        )
    for name, (low, inclusive, high) in _PARAMETER_BOUNDS.items():
        value = _finite(getattr(parameters, name), name)
        if value < low or (value == low and not inclusive) or value > high:
            lower = f"{'>=' if inclusive else '>'} {low:g}"
            bounds = lower if math.isinf(high) else f"{lower} and <= {high:g}"
            raise ValidationError(f"{name} must be {bounds}, got: {value!r}", field=name, value=value)
    if not isinstance(parameters.infiltration, Mapping):
        raise ValidationError(
            f"infiltration must be a mapping, got {type(parameters.infiltration).__name__}",
            field="infiltration",
            value=parameters.infiltration,
        )
    for key, raw in parameters.infiltration.items():
        if not isinstance(key, str) or key not in KNOWN_INFILTRATION_KEYS:
            raise ValidationError(
                f"Unknown infiltration parameter {key!r}. Valid parameters are: {', '.join(sorted(KNOWN_INFILTRATION_KEYS))}",
                field=f"infiltration[{key}]",
                value=key,
            )
        value = _finite(raw, f"infiltration[{key}]")
        if value < 0:
            raise ValidationError(
                f"infiltration[{key}] must be >= 0, got: {value!r}", field=f"infiltration[{key}]", value=value
            )
    return parameters


def _validate_category(
    value: object,
    enum_cls: type[_E],
    lookup: Callable[[str], _E | None],
    labels: Mapping[_E, str],
    field_name: str,
) -> _E:
    what = field_name.replace("_", " ")
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, (int, numbers.Integral)) and not isinstance(value, bool):
        try:
            return enum_cls(int(value))
        except ValueError:
            raise ValidationError(
                f"Invalid {what} code {value}. Valid integer codes are 1-{len(enum_cls)}.",
                field=field_name,
                value=value,
            ) from None
    if not isinstance(value, str):
        raise ValidationError(
            f"{what.capitalize()} must be a {enum_cls.__name__}, integer code or string, got {type(value).__name__}",
            field=field_name,
            value=value,
        )
    if not value.strip():
        raise ValidationError(f"{what.capitalize()} cannot be empty.", field=field_name, value=value)
    member = lookup(value)
    if member is not None:
        return member

    candidates = {m.name.lower(): m for m in enum_cls}
    candidates.update({lbl.lower(): m for m, lbl in labels.items()})
    close = difflib.get_close_matches(value.strip().lower(), list(candidates), n=6, cutoff=0.6)
    suggestions = list(dict.fromkeys(candidates[c].name for c in close))[:3]
    if suggestions:
        hint = f"Did you mean: {', '.join(suggestions)}?"
    else:
        hint = f"Valid options: {', '.join(m.name for m in enum_cls)}"
    raise ValidationError(f"Unknown {what} {value!r}. {hint}", field=field_name, value=value)


def validate_land_form(value: LandForm | int | str) -> LandForm:
    """Resolve a land form given as enum, integer code (1-9), snake_case name or human label (case-insensitive).

    Raises
    ------
    ValidationError
        If the value does not name a land form; the message suggests close matches.
    """
    return _validate_category(value, LandForm, lookup_land_form, LAND_FORM_LABELS, "land_form")


def validate_land_cover(value: LandCover | int | str) -> LandCover:
    """Resolve a land cover given as enum, integer code (1-14), snake_case name or human label (case-insensitive).

    Raises
    ------
    ValidationError
        If the value does not name a land cover; the message suggests close matches.
    """
    return _validate_category(value, LandCover, lookup_land_cover, LAND_COVER_LABELS, "land_cover")


def validate_inp_path(path: str | Path, *, must_exist: bool = True) -> Path:
    """Validate the path of a SWMM ``.inp`` file.

    Parameters
    ----------
    path : str or Path
        Path to check.
    must_exist : bool, optional
        When ``True`` (default) the file must exist, be readable and non-empty.
        When ``False`` only the extension, the parent directory and that the path is
        not a directory are checked (used for output paths).

    Returns
    -------
    Path
        The path, with ``~`` expanded.

    Raises
    ------
    ValidationError
        If the path is unusable.
    """
    p = Path(path).expanduser()

    def error(message: str) -> ValidationError:
        return ValidationError(message, field="inp_path", value=path)

    if p.suffix.lower() != ".inp":
        raise error(f"Expected a SWMM .inp file, got: {str(path)!r}")
    if not must_exist:
        if not p.parent.is_dir():
            raise error(f"Directory does not exist: {str(p.parent)!r}")
        if p.exists() and not p.is_file():
            raise error(f"Not a file: {str(path)!r}")
        return p
    if not p.exists():
        raise error(f"File does not exist: {str(path)!r}")
    if not p.is_file():
        raise error(f"Not a file: {str(path)!r}")
    try:
        with p.open("rb") as fh:
            empty = not fh.read(1)
    except OSError as e:
        raise error(f"Cannot read {str(path)!r}: {e.strerror or e}") from e
    if empty:
        raise error(f"File is empty: {str(path)!r}")
    return p
