"""Subcatchment value objects, the width formula, SWMM units and category labels."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, TypeVar

from rcg.exceptions import ValidationError
from rcg.fuzzy.categories import LandCover, LandForm

__all__ = [
    "ACRES_PER_HECTARE",
    "ApplyResult",
    "FEET_PER_METRE",
    "FLOW_UNITS_SI",
    "FLOW_UNITS_US",
    "INFILTRATION_FIELDS",
    "INFILTRATION_METHODS",
    "LAND_COVER_LABELS",
    "LAND_FORM_LABELS",
    "MM_PER_INCH",
    "LandCover",
    "LandForm",
    "ModelInfo",
    "SubcatchmentParameters",
    "infiltration_for",
    "label",
    "lookup_land_cover",
    "lookup_land_form",
    "width_m",
]

# --------------------------------------------------------------------------- SWMM units

FLOW_UNITS_SI = ("CMS", "LPS", "MLD")
"""SI flow units: areas in hectares, lengths in metres, depths in millimetres."""

FLOW_UNITS_US = ("CFS", "GPM", "MGD")
"""US customary flow units: areas in acres, lengths in feet, depths in inches."""

ACRES_PER_HECTARE = 2.4710538
FEET_PER_METRE = 3.2808399
MM_PER_INCH = 25.4

INFILTRATION_METHODS = ("HORTON", "MODIFIED_HORTON", "GREEN_AMPT", "MODIFIED_GREEN_AMPT", "CURVE_NUMBER")
"""Values of the ``INFILTRATION`` option understood by SWMM 5.1/5.2."""

_GREEN_AMPT_FIELDS = (
    ("Suction head", "mm", "in"),
    ("Conductivity", "mm/h", "in/h"),
    ("Initial deficit", "–", "–"),
)
_HORTON_FIELDS = (
    ("Max. infiltration rate", "mm/h", "in/h"),
    ("Min. infiltration rate", "mm/h", "in/h"),
    ("Decay constant", "1/h", "1/h"),
    ("Drying time", "days", "days"),
    ("Max. infiltration volume", "mm", "in"),
)
_CURVE_NUMBER_FIELDS = (
    ("Curve number", "–", "–"),
    ("Conductivity (unused)", "mm/h", "in/h"),
    ("Drying time", "days", "days"),
)

INFILTRATION_FIELDS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "HORTON": _HORTON_FIELDS,
    "MODIFIED_HORTON": _HORTON_FIELDS,
    "GREEN_AMPT": _GREEN_AMPT_FIELDS,
    "MODIFIED_GREEN_AMPT": _GREEN_AMPT_FIELDS,
    "CURVE_NUMBER": _CURVE_NUMBER_FIELDS,
}
"""``(label, SI unit, US unit)`` of the meaningful ``[INFILTRATION]`` fields per method.

The entries label the *leading* values of :func:`infiltration_for` in order, so
``zip(INFILTRATION_FIELDS[m], infiltration_for(m).values())`` pairs each label with
its value. The Green-Ampt row written by RCG has two more, trailing values
(``Param4=7``, ``Param5=0``) kept byte-identical with 1.x; SWMM ignores them for
Green-Ampt, so they carry no label. Values are written in the model's own units
(the SI or US column), without conversion.
"""


def base_infiltration_method(method: str) -> str:
    """Return the method whose defaults ``method`` uses (``MODIFIED_HORTON`` -> ``HORTON``).

    Raises
    ------
    ValidationError
        If ``method`` is not one of :data:`INFILTRATION_METHODS` (case-insensitive).
    """
    key = str(method).strip().upper()
    if key not in INFILTRATION_METHODS:
        raise ValidationError(
            f"Unknown infiltration method {method!r}; expected one of {', '.join(INFILTRATION_METHODS)}",
            field="infiltration_method",
            value=method,
        )
    return key.removeprefix("MODIFIED_")


def infiltration_for(method: str) -> dict[str, float]:
    """Return the ``[INFILTRATION]`` values RCG writes for a model using ``method``.

    Parameters
    ----------
    method : str
        SWMM infiltration method (case-insensitive), see :data:`INFILTRATION_METHODS`.

    Returns
    -------
    dict[str, float]
        Ordered ``{name: value}`` of the whole row, from ``infiltration_defaults`` in
        ``defaults.json`` (e.g. ``MaxRate, MinRate, Decay, DryTime, MaxInfil`` for
        Horton). See :data:`INFILTRATION_FIELDS` for labels and units.

    Raises
    ------
    ValidationError
        If ``method`` is unknown.
    """
    from rcg.config import load_defaults

    return dict(load_defaults().infiltration_by_method[base_infiltration_method(method)])


# --------------------------------------------------------------------------- categories

LAND_FORM_LABELS: Mapping[LandForm, str] = MappingProxyType(
    {
        LandForm.marshes_and_lowlands: "Marshes and lowlands",
        LandForm.flats_and_plateaus: "Flats and plateaus",
        LandForm.flats_and_plateaus_in_combination_with_hills: "Flats and plateaus in combination with hills",
        LandForm.hills_with_gentle_slopes: "Hills with gentle slopes",
        LandForm.steeper_hills_and_foothills: "Steeper hills and foothills",
        LandForm.hills_and_outcrops_of_mountain_ranges: "Hills and outcrops of mountain ranges",
        LandForm.higher_hills: "Higher hills",
        LandForm.mountains: "Mountains",
        LandForm.highest_mountains: "Highest mountains",
    }
)
"""Human-readable label for every land form, in enum order."""

LAND_COVER_LABELS: Mapping[LandCover, str] = MappingProxyType(
    {
        LandCover.permeable_areas: "Permeable areas",
        LandCover.permeable_terrain_on_plains: "Permeable terrain on plains",
        LandCover.mountains_vegetated: "Mountains, vegetated",
        LandCover.mountains_rocky: "Mountains, rocky",
        LandCover.urban_weakly_impervious: "Urban, weakly impervious",
        LandCover.urban_moderately_impervious: "Urban, moderately impervious",
        LandCover.urban_highly_impervious: "Urban, highly impervious",
        LandCover.suburban_weakly_impervious: "Suburban, weakly impervious",
        LandCover.suburban_highly_impervious: "Suburban, highly impervious",
        LandCover.rural: "Rural",
        LandCover.forests: "Forests",
        LandCover.meadows: "Meadows",
        LandCover.arable: "Arable",
        LandCover.marshes: "Marshes",
    }
)
"""Human-readable label for every land cover, in enum order."""

# Wording used by the README tables for the two mountain land covers.
_LAND_COVER_ALIASES: Mapping[str, LandCover] = MappingProxyType(
    {
        "vegetated_mountains": LandCover.mountains_vegetated,
        "rocky_mountains": LandCover.mountains_rocky,
        "rocky_hilly_mountains": LandCover.mountains_rocky,
    }
)

_E = TypeVar("_E", LandForm, LandCover)


def _normalise(text: str) -> str:
    """Fold a snake_case name or a human label to one comparable key."""
    return re.sub(r"[\s,\-_]+", "_", text.strip().lower()).strip("_")


def label(category: LandForm | LandCover) -> str:
    """Return the human-readable label of a land form or land cover.

    Examples
    --------
    >>> label(LandCover.urban_moderately_impervious)
    'Urban, moderately impervious'
    """
    if isinstance(category, LandForm):
        return LAND_FORM_LABELS[category]
    if isinstance(category, LandCover):
        return LAND_COVER_LABELS[category]
    raise TypeError(f"Expected LandForm or LandCover, got {type(category).__name__}")


def _lookup(enum_cls: type[_E], value: str, aliases: Mapping[str, _E]) -> _E | None:
    key = _normalise(value)
    for member in enum_cls:
        if member.name == key:
            return member
    return aliases.get(key)


def lookup_land_form(value: str) -> LandForm | None:
    """Resolve a snake_case name or human label to a :class:`LandForm` (case-insensitive).

    Returns ``None`` when nothing matches; :mod:`rcg.validation` turns that into a
    helpful error.
    """
    return _lookup(LandForm, value, {})


def lookup_land_cover(value: str) -> LandCover | None:
    """Resolve a snake_case name or human label to a :class:`LandCover` (case-insensitive).

    Returns ``None`` when nothing matches; :mod:`rcg.validation` turns that into a
    helpful error.
    """
    return _lookup(LandCover, value, _LAND_COVER_ALIASES)


def width_m(area_ha: float) -> float:
    """Return the characteristic width in metres: ``round(sqrt(area_ha * 10_000) / 2, 2)``."""
    return round(math.sqrt(area_ha * 10_000) / 2, 2)


@dataclass(frozen=True)
class SubcatchmentParameters:
    """Everything needed to write one subcatchment, as computed by :func:`rcg.preview`.

    Attributes
    ----------
    land_form, land_cover : LandForm, LandCover
        Input categories.
    area_ha : float
        Area in hectares.
    slope_pct : float
        Fuzzy slope result in percent (rounded to 2 dp when written).
    impervious_pct : float
        Fuzzy impervious share in percent (rounded to 2 dp when written).
    catchment_score : float
        Raw fuzzy catchment output (0-100).
    catchment_type : str
        Linguistic catchment class: ``urban``, ``suburban``, ``rural``, ``forests``,
        ``meadows``, ``arable`` or ``mountains``.
    width_m : float
        Characteristic width in metres, see :func:`width_m`.
    n_imperv, n_perv : float
        Manning's n for the impervious and pervious parts.
    s_imperv_mm, s_perv_mm : float
        Depression storage in millimetres.
    pct_zero : int
        Percent of impervious area without depression storage.
    infiltration : Mapping[str, float]
        Green-Ampt parameters ``Suction``, ``Ksat``, ``IMD``, ``Param4``, ``Param5``.
        Written only to models whose ``INFILTRATION`` is ``GREEN_AMPT`` or
        ``MODIFIED_GREEN_AMPT``; other methods get :func:`infiltration_for` instead.
    """

    land_form: LandForm
    land_cover: LandCover
    area_ha: float
    slope_pct: float
    impervious_pct: float
    catchment_score: float
    catchment_type: str
    width_m: float
    n_imperv: float
    n_perv: float
    s_imperv_mm: float
    s_perv_mm: float
    pct_zero: int
    infiltration: Mapping[str, float] = field(hash=False)

    def __post_init__(self) -> None:
        # Freeze the mapping so the dataclass is immutable all the way down.
        object.__setattr__(self, "infiltration", MappingProxyType(dict(self.infiltration)))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict (categories as snake_case names)."""
        return {
            "land_form": self.land_form.name,
            "land_cover": self.land_cover.name,
            "area_ha": self.area_ha,
            "slope_pct": self.slope_pct,
            "impervious_pct": self.impervious_pct,
            "catchment_score": self.catchment_score,
            "catchment_type": self.catchment_type,
            "width_m": self.width_m,
            "n_imperv": self.n_imperv,
            "n_perv": self.n_perv,
            "s_imperv_mm": self.s_imperv_mm,
            "s_perv_mm": self.s_perv_mm,
            "pct_zero": self.pct_zero,
            "infiltration": dict(self.infiltration),
        }


@dataclass(frozen=True)
class ApplyResult:
    """Outcome of :func:`rcg.apply`.

    Attributes
    ----------
    output_path : Path
        File that was written, fully resolved (symbolic links followed).
    backup_path : Path or None
        Copy of the file that was overwritten (the source when updating in place,
        otherwise the previous ``output_path``), or ``None`` when no file was
        overwritten or backups were turned off.
    subcatchment_ids : tuple[str, ...]
        Ids of the added subcatchments, in input order.
    raingage : str
        Rain gage assigned to the new subcatchments.
    outlet : str
        Outlet assigned to the new subcatchments. When the model has no outfalls or
        junctions each subcatchment drains to itself and this is the first new id.
    flow_units : str
        ``FLOW_UNITS`` of the model. For US units (``CFS``, ``GPM``, ``MGD``) the area
        was written in acres, the width in feet and depression storage in inches.
    infiltration_method : str
        ``INFILTRATION`` option of the model; it decided the ``[INFILTRATION]`` row.
    """

    output_path: Path
    backup_path: Path | None
    subcatchment_ids: tuple[str, ...]
    raingage: str
    outlet: str
    flow_units: str = "CMS"
    infiltration_method: str = "GREEN_AMPT"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict (paths as strings)."""
        return {
            "output_path": str(self.output_path),
            "backup_path": None if self.backup_path is None else str(self.backup_path),
            "subcatchment_ids": list(self.subcatchment_ids),
            "raingage": self.raingage,
            "outlet": self.outlet,
            "flow_units": self.flow_units,
            "infiltration_method": self.infiltration_method,
        }


@dataclass(frozen=True)
class ModelInfo:
    """What :func:`rcg.inspect` reads from a SWMM model, without changing it.

    Attributes
    ----------
    path : Path
        The model file, fully resolved (symbolic links followed).
    flow_units : str
        ``FLOW_UNITS`` from ``[OPTIONS]`` (``CFS`` when absent, as in SWMM).
    is_metric : bool
        ``True`` for SI flow units (``CMS``, ``LPS``, ``MLD``); US units (``CFS``,
        ``GPM``, ``MGD``) make :func:`rcg.apply` write acres, feet and inches.
    infiltration_method : str
        ``INFILTRATION`` from ``[OPTIONS]`` (``HORTON`` when absent, as in SWMM).
    subcatchment_count : int
        Number of subcatchments already in the model.
    raingage : str or None
        Rain gage :func:`rcg.apply` would assign, or ``None`` when it would create ``RG1``.
    outlet : str or None
        Outlet :func:`rcg.apply` would assign, or ``None`` when each new subcatchment
        would drain to itself (no outfalls or junctions).
    size_bytes : int
        File size in bytes.
    """

    path: Path
    flow_units: str
    is_metric: bool
    infiltration_method: str
    subcatchment_count: int
    raingage: str | None
    outlet: str | None
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict (path as a string)."""
        return {
            "path": str(self.path),
            "flow_units": self.flow_units,
            "is_metric": self.is_metric,
            "infiltration_method": self.infiltration_method,
            "subcatchment_count": self.subcatchment_count,
            "raingage": self.raingage,
            "outlet": self.outlet,
            "size_bytes": self.size_bytes,
        }
