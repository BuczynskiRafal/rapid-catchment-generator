import dataclasses
import json
from pathlib import Path

import pytest

from rcg.catchment import (
    LAND_COVER_LABELS,
    LAND_FORM_LABELS,
    ApplyResult,
    label,
    lookup_land_cover,
    lookup_land_form,
    width_m,
)
from rcg.fuzzy.categories import LandCover, LandForm


def test_every_category_has_a_unique_label():
    assert list(LAND_FORM_LABELS) == list(LandForm)
    assert list(LAND_COVER_LABELS) == list(LandCover)
    assert len(set(LAND_FORM_LABELS.values())) == len(LandForm)
    assert len(set(LAND_COVER_LABELS.values())) == len(LandCover)


def test_label():
    assert label(LandCover.urban_moderately_impervious) == "Urban, moderately impervious"
    assert label(LandForm.flats_and_plateaus) == "Flats and plateaus"
    with pytest.raises(TypeError):
        label("urban")  # type: ignore[arg-type]


@pytest.mark.parametrize("member", list(LandForm))
def test_land_form_round_trips_through_name_and_label(member):
    assert lookup_land_form(member.name) is member
    assert lookup_land_form(LAND_FORM_LABELS[member]) is member
    assert lookup_land_form(LAND_FORM_LABELS[member].upper()) is member


@pytest.mark.parametrize("member", list(LandCover))
def test_land_cover_round_trips_through_name_and_label(member):
    assert lookup_land_cover(member.name) is member
    assert lookup_land_cover(LAND_COVER_LABELS[member]) is member
    assert lookup_land_cover(f"  {LAND_COVER_LABELS[member].lower()}  ") is member


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Urban moderately impervious", LandCover.urban_moderately_impervious),
        ("URBAN_MODERATELY_IMPERVIOUS", LandCover.urban_moderately_impervious),
        ("urban-moderately-impervious", LandCover.urban_moderately_impervious),
        ("Vegetated mountains", LandCover.mountains_vegetated),
        ("Rocky hilly mountains", LandCover.mountains_rocky),
        ("urban", None),
        ("", None),
    ],
)
def test_lookup_land_cover_variants(text, expected):
    assert lookup_land_cover(text) is expected


def test_width_formula():
    assert width_m(5.0) == 111.8
    assert width_m(1.0) == 50.0
    assert type(width_m(5)) is float


def test_parameters_are_immutable_and_json_ready(urban_params):
    with pytest.raises(dataclasses.FrozenInstanceError):
        urban_params.area_ha = 1.0  # type: ignore[misc]
    with pytest.raises(TypeError):
        urban_params.infiltration["Ksat"] = 1.0  # type: ignore[index]
    data = urban_params.to_dict()
    assert data["land_form"] == "flats_and_plateaus"
    assert data["land_cover"] == "urban_moderately_impervious"
    assert json.loads(json.dumps(data)) == data
    assert hash(urban_params) == hash(urban_params)


def test_apply_result_to_dict():
    result = ApplyResult(Path("a.inp"), None, ("S1",), "RG1", "O1", "CFS", "HORTON")
    assert result.to_dict() == {
        "output_path": "a.inp",
        "backup_path": None,
        "subcatchment_ids": ["S1"],
        "raingage": "RG1",
        "outlet": "O1",
        "flow_units": "CFS",
        "infiltration_method": "HORTON",
    }
