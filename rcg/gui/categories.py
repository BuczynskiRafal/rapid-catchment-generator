"""Human-facing text of the window: category labels and descriptions, catchment types,
infiltration methods.

Labels come from the core (:func:`rcg.catchment.label`). Only some descriptions are
condensed from the README: those of the land forms and of the first nine land covers
(permeable areas to suburban, highly impervious), which the README describes in
detail. The descriptions of the other five land covers (rural, forests,
meadows, arable, marshes) were written for this window; they say what kind of surface
the category stands for and make no claim about the computed values. The one-line
hints under the pickers are written for this window.

Options are kept in the enums' natural order, which encodes increasing steepness
(land form) and a deliberate grouping of land covers; never sort them alphabetically.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from rcg.catchment import label
from rcg.fuzzy.categories import LandCover, LandForm

__all__ = [
    "CATCHMENT_TYPE_LABELS",
    "LAND_COVER_HINTS",
    "LAND_FORM_HINTS",
    "INFILTRATION_METHOD_LABELS",
    "CategoryOption",
    "catchment_type_label",
    "infiltration_method_label",
    "land_cover_options",
    "land_form_options",
]

LAND_FORM_DESCRIPTIONS: Mapping[LandForm, str] = MappingProxyType(
    {
        LandForm.marshes_and_lowlands: "Flat, often water-saturated ground with slow drainage and high water retention "
        "(wetlands, floodplains).",
        LandForm.flats_and_plateaus: "Large flat or gently elevated areas with minimal slope; water spreads out and drains "
        "slowly and evenly.",
        LandForm.flats_and_plateaus_in_combination_with_hills: "Flat terrain interspersed with gentle hills: water is "
        "retained on the flats and runs off faster on the slopes.",
        LandForm.hills_with_gentle_slopes: "Low-gradient rolling hills; moderate runoff with some infiltration.",
        LandForm.steeper_hills_and_foothills: "Moderate to steep slopes, often at the foot of mountain ranges; fast, "
        "high runoff.",
        LandForm.hills_and_outcrops_of_mountain_ranges: "Foothills with rocky outcrops and uneven terrain; moderate "
        "slopes, mixed infiltration and runoff.",
        LandForm.higher_hills: "Elevated hills with pronounced slopes; water runs off quickly and infiltration is limited.",
        LandForm.mountains: "Steep, high terrain with rocky ground; little infiltration and high runoff.",
        LandForm.highest_mountains: "The most rugged high-altitude terrain (cliffs, snow, ice); almost all precipitation "
        "runs off.",
    }
)

LAND_COVER_DESCRIPTIONS: Mapping[LandCover, str] = MappingProxyType(
    {
        LandCover.permeable_areas: "Mostly natural, highly permeable surfaces; most rainfall infiltrates and runoff is "
        "minimal.",
        LandCover.permeable_terrain_on_plains: "Open, flat or gently sloping permeable land such as fields, meadows and "
        "prairies.",
        LandCover.mountains_vegetated: "Mountain slopes with dense vegetation that absorbs water and limits erosion.",
        LandCover.mountains_rocky: "Rocky hills and mountains with sparse vegetation; little infiltration, high runoff.",
        LandCover.urban_weakly_impervious: "Urban areas with roughly 30-60 % impervious cover; gardens and green spaces "
        "remain common.",
        LandCover.urban_moderately_impervious: "Medium-density urban areas with roughly 50-80 % impervious cover.",
        LandCover.urban_highly_impervious: "Dense city cores and industrial zones with roughly 75-100 % impervious cover.",
        LandCover.suburban_weakly_impervious: "Low-density suburbs with roughly 10-40 % impervious cover and large yards.",
        LandCover.suburban_highly_impervious: "Denser suburbs with roughly 35-65 % impervious cover (multi-family housing, "
        "shopping centres).",
        LandCover.rural: "Villages and farmsteads: scattered buildings among largely permeable land.",
        LandCover.forests: "Woodland with a dense canopy and litter layer; high retention and slow, rough overland flow.",
        LandCover.meadows: "Grassland and pasture with continuous vegetation cover.",
        LandCover.arable: "Cultivated fields; permeable soil that is often bare or compacted between crops.",
        LandCover.marshes: "Wetlands and water-saturated ground with very high retention.",
    }
)

# One-line hints shown under the pickers (short enough for the minimum window width);
# the full description above is the tooltip.
LAND_FORM_HINTS: Mapping[LandForm, str] = MappingProxyType(
    {
        LandForm.marshes_and_lowlands: "Flat, water-saturated ground; slow drainage",
        LandForm.flats_and_plateaus: "Flat or gently raised land; minimal slope",
        LandForm.flats_and_plateaus_in_combination_with_hills: "Flats with gentle hills; mixed runoff",
        LandForm.hills_with_gentle_slopes: "Low, rolling hills; moderate runoff",
        LandForm.steeper_hills_and_foothills: "Moderate to steep slopes; fast runoff",
        LandForm.hills_and_outcrops_of_mountain_ranges: "Foothills with rocky outcrops; uneven terrain",
        LandForm.higher_hills: "Pronounced slopes; limited infiltration",
        LandForm.mountains: "Steep, rocky terrain; high runoff",
        LandForm.highest_mountains: "Cliffs, snow and ice; nearly all water runs off",
    }
)

LAND_COVER_HINTS: Mapping[LandCover, str] = MappingProxyType(
    {
        LandCover.permeable_areas: "Natural surfaces; most rainfall infiltrates",
        LandCover.permeable_terrain_on_plains: "Fields, meadows and prairies on flat land",
        LandCover.mountains_vegetated: "Densely vegetated mountain slopes",
        LandCover.mountains_rocky: "Rocky, sparsely vegetated slopes",
        LandCover.urban_weakly_impervious: "Urban, roughly 30-60 % impervious",
        LandCover.urban_moderately_impervious: "Urban, roughly 50-80 % impervious",
        LandCover.urban_highly_impervious: "City cores, industry; 75-100 % impervious",
        LandCover.suburban_weakly_impervious: "Low-density suburbs; 10-40 % impervious",
        LandCover.suburban_highly_impervious: "Denser suburbs; 35-65 % impervious",
        LandCover.rural: "Villages and farmsteads among open land",
        LandCover.forests: "Woodland with a dense canopy",
        LandCover.meadows: "Grassland and pasture",
        LandCover.arable: "Cultivated fields, often bare between crops",
        LandCover.marshes: "Wetlands, water-saturated ground",
    }
)

CATCHMENT_TYPE_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "urban": "Urban",
        "suburban": "Suburban",
        "rural": "Rural",
        "forests": "Forests",
        "meadows": "Meadows",
        "arable": "Arable",
        "mountains": "Mountains",
    }
)

INFILTRATION_METHOD_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "HORTON": "Horton",
        "MODIFIED_HORTON": "Modified Horton",
        "GREEN_AMPT": "Green-Ampt",
        "MODIFIED_GREEN_AMPT": "Modified Green-Ampt",
        "CURVE_NUMBER": "Curve Number",
    }
)


@dataclass(frozen=True)
class CategoryOption:
    """One entry of a category combo box."""

    member: LandForm | LandCover
    label: str
    description: str
    hint: str


def land_form_options() -> tuple[CategoryOption, ...]:
    """Return every land form in enum order (flattest first)."""
    return tuple(CategoryOption(m, label(m), LAND_FORM_DESCRIPTIONS.get(m, ""), LAND_FORM_HINTS.get(m, "")) for m in LandForm)


def land_cover_options() -> tuple[CategoryOption, ...]:
    """Return every land cover in enum order."""
    return tuple(
        CategoryOption(m, label(m), LAND_COVER_DESCRIPTIONS.get(m, ""), LAND_COVER_HINTS.get(m, "")) for m in LandCover
    )


def catchment_type_label(catchment_type: str) -> str:
    """Return the display label of a linguistic catchment type (``"urban"`` -> ``"Urban"``)."""
    return CATCHMENT_TYPE_LABELS.get(catchment_type, catchment_type.replace("_", " ").capitalize())


def infiltration_method_label(method: str) -> str:
    """Return the display label of a SWMM infiltration method (``"MODIFIED_HORTON"`` -> ``"Modified Horton"``)."""
    key = method.strip().upper()
    return INFILTRATION_METHOD_LABELS.get(key, key.replace("_", " ").title())
