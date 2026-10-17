import math

import pytest

from rcg.exceptions import RCGError, ValidationError
from rcg.fuzzy.categories import LandCover, LandForm
from rcg.validation import (
    max_area_ha,
    min_area_ha,
    validate_area,
    validate_inp_path,
    validate_land_cover,
    validate_land_form,
    validate_parameters,
)


def test_validation_error_is_an_rcg_error():
    assert issubclass(ValidationError, RCGError)


@pytest.mark.parametrize(("value", "expected"), [("5.5", 5.5), (5, 5.0), (0.01, 0.01), (0.0001, 0.0001), ("10000", 10_000.0)])
def test_validate_area_accepts(value, expected):
    result = validate_area(value)
    assert result == expected
    assert type(result) is float


@pytest.mark.parametrize("value", ["abc", "", None, 0, -1, "-0.5", math.nan, math.inf, 10_000.01, True, 0.00009, "1e-9"])
def test_validate_area_rejects(value):
    with pytest.raises(ValidationError) as info:
        validate_area(value)
    assert info.value.field == "area"


def test_area_limit_comes_from_defaults():
    assert max_area_ha() == 10_000
    assert min_area_ha() == 0.0001


def test_validate_parameters_accepts_preview_output(urban_params, forest_params):
    assert validate_parameters(urban_params) is urban_params
    assert validate_parameters(forest_params) is forest_params


@pytest.mark.parametrize("value", ["1.0", None, True])
def test_validate_parameters_rejects_non_numbers(urban_params, value):
    import dataclasses

    with pytest.raises(ValidationError, match="must be a number") as info:
        validate_parameters(dataclasses.replace(urban_params, n_imperv=value))
    assert info.value.field == "n_imperv"


def test_validate_parameters_rejects_other_types():
    with pytest.raises(ValidationError, match="Expected SubcatchmentParameters"):
        validate_parameters({"area_ha": 1})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [LandForm.flats_and_plateaus, "flats_and_plateaus", "FLATS_AND_PLATEAUS", "Flats and plateaus", " flats and PLATEAUS "],
)
def test_validate_land_form_accepts(value):
    assert validate_land_form(value) is LandForm.flats_and_plateaus


@pytest.mark.parametrize(
    "value",
    [
        LandCover.urban_moderately_impervious,
        "urban_moderately_impervious",
        "Urban, moderately impervious",
        "urban MODERATELY impervious",
    ],
)
def test_validate_land_cover_accepts(value):
    assert validate_land_cover(value) is LandCover.urban_moderately_impervious


def test_unknown_category_suggests_close_matches():
    with pytest.raises(ValidationError) as info:
        validate_land_cover("urban moderatly impervious")
    message = str(info.value)
    assert "Did you mean" in message
    assert "urban_moderately_impervious" in message
    assert info.value.field == "land_cover"


def test_unknown_category_without_close_match_lists_options():
    with pytest.raises(ValidationError) as info:
        validate_land_form("xyz")
    assert "Valid options" in str(info.value)
    assert "highest_mountains" in str(info.value)


@pytest.mark.parametrize("value", ["", "   ", 0, 10, True, 1.5, None, LandCover.rural])
def test_validate_land_form_rejects_wrong_types_and_empty(value):
    with pytest.raises(ValidationError):
        validate_land_form(value)


def test_validate_inp_path_ok(example_inp):
    assert validate_inp_path(str(example_inp)) == example_inp


def test_validate_inp_path_rejects(tmp_path):
    with pytest.raises(ValidationError, match="does not exist"):
        validate_inp_path(tmp_path / "missing.inp")
    with pytest.raises(ValidationError, match=r"\.inp"):
        validate_inp_path(tmp_path / "model.txt")
    (tmp_path / "dir.inp").mkdir()
    with pytest.raises(ValidationError, match="Not a file"):
        validate_inp_path(tmp_path / "dir.inp")
    (tmp_path / "empty.inp").write_text("", encoding="utf-8")
    with pytest.raises(ValidationError, match="empty"):
        validate_inp_path(tmp_path / "empty.inp")


def test_validate_inp_path_upper_case_extension(tmp_path):
    path = tmp_path / "MODEL.INP"
    path.write_text("[TITLE]\n", encoding="utf-8")
    assert validate_inp_path(path) == path


def test_validate_output_path(tmp_path):
    assert validate_inp_path(tmp_path / "new.inp", must_exist=False) == tmp_path / "new.inp"
    with pytest.raises(ValidationError, match="Directory does not exist"):
        validate_inp_path(tmp_path / "nope" / "new.inp", must_exist=False)
    (tmp_path / "folder.inp").mkdir()
    with pytest.raises(ValidationError, match="Not a file"):
        validate_inp_path(tmp_path / "folder.inp", must_exist=False)


# --------------------------------------------------------------------------- category integer codes (WP4.2, F-21)


@pytest.mark.parametrize("code", list(range(1, 10)))
def test_validate_land_form_accepts_integer_codes(code):
    result = validate_land_form(code)
    assert result is LandForm(code)
    assert isinstance(result, LandForm)


@pytest.mark.parametrize("code", list(range(1, 15)))
def test_validate_land_cover_accepts_integer_codes(code):
    result = validate_land_cover(code)
    assert result is LandCover(code)
    assert isinstance(result, LandCover)


def test_validate_categories_accept_numpy_integers():
    import numpy as np

    assert validate_land_form(np.int32(1)) is LandForm.marshes_and_lowlands
    assert validate_land_form(np.int64(9)) is LandForm.highest_mountains
    assert validate_land_cover(np.int32(1)) is LandCover.permeable_areas
    assert validate_land_cover(np.int64(14)) is LandCover.marshes


@pytest.mark.parametrize("code", [-5, -1, 0, 10, 15, 100])
def test_validate_land_form_rejects_invalid_integer_codes(code):
    with pytest.raises(ValidationError) as info:
        validate_land_form(code)
    assert info.value.field == "land_form"
    assert f"Invalid land form code {code}" in str(info.value)
    assert "Valid integer codes are 1-9." in str(info.value)


@pytest.mark.parametrize("code", [-5, -1, 0, 15, 20, 100])
def test_validate_land_cover_rejects_invalid_integer_codes(code):
    with pytest.raises(ValidationError) as info:
        validate_land_cover(code)
    assert info.value.field == "land_cover"
    assert f"Invalid land cover code {code}" in str(info.value)
    assert "Valid integer codes are 1-14." in str(info.value)


@pytest.mark.parametrize("val", [True, False])
def test_validate_categories_reject_booleans(val):
    with pytest.raises(ValidationError) as info1:
        validate_land_form(val)
    assert info1.value.field == "land_form"
    assert "Land form must be a LandForm, integer code or string, got bool" in str(info1.value)

    with pytest.raises(ValidationError) as info2:
        validate_land_cover(val)
    assert info2.value.field == "land_cover"
    assert "Land cover must be a LandCover, integer code or string, got bool" in str(info2.value)


# --------------------------------------------------------------------------- validate_parameters expansion (WP4.1, F-20)


def test_validate_parameters_rejects_invalid_land_form(urban_params):
    import dataclasses

    with pytest.raises(ValidationError) as info:
        validate_parameters(dataclasses.replace(urban_params, land_form=10))  # type: ignore[arg-type]
    assert info.value.field == "land_form"

    with pytest.raises(ValidationError) as info:
        validate_parameters(dataclasses.replace(urban_params, land_form="unknown_form"))  # type: ignore[arg-type]
    assert info.value.field == "land_form"


def test_validate_parameters_rejects_invalid_land_cover(urban_params):
    import dataclasses

    with pytest.raises(ValidationError) as info:
        validate_parameters(dataclasses.replace(urban_params, land_cover=20))  # type: ignore[arg-type]
    assert info.value.field == "land_cover"

    with pytest.raises(ValidationError) as info:
        validate_parameters(dataclasses.replace(urban_params, land_cover="unknown_cover"))  # type: ignore[arg-type]
    assert info.value.field == "land_cover"


@pytest.mark.parametrize("score", [0.0, 0, 42.5, 100, 100.0])
def test_validate_parameters_accepts_valid_catchment_score(urban_params, score):
    import dataclasses

    p = dataclasses.replace(urban_params, catchment_score=score)
    assert validate_parameters(p) is p


@pytest.mark.parametrize("score", [-1.0, -0.001, 100.001, 150.0, float("nan"), float("inf"), float("-inf"), True, "50"])
def test_validate_parameters_rejects_invalid_catchment_score(urban_params, score):
    import dataclasses

    with pytest.raises(ValidationError) as info:
        validate_parameters(dataclasses.replace(urban_params, catchment_score=score))  # type: ignore[arg-type]
    assert info.value.field == "catchment_score"


@pytest.mark.parametrize("valid_type", ["urban", "suburban", "rural", "forests", "meadows", "arable", "mountains"])
def test_validate_parameters_accepts_valid_catchment_types(urban_params, valid_type):
    import dataclasses

    p = dataclasses.replace(urban_params, catchment_type=valid_type)
    assert validate_parameters(p) is p


@pytest.mark.parametrize("invalid_type", ["industrial", "commercial", "", "URBAN", None, 123])
def test_validate_parameters_rejects_invalid_catchment_types(urban_params, invalid_type):
    import dataclasses

    with pytest.raises(ValidationError) as info:
        validate_parameters(dataclasses.replace(urban_params, catchment_type=invalid_type))  # type: ignore[arg-type]
    assert info.value.field == "catchment_type"
    assert "Invalid catchment_type" in str(info.value)


# --------------------------------------------------------------------------- polymorphic infiltration validation (WP4.3, F-19)


@pytest.mark.parametrize(
    "custom_infil",
    [
        {"MaxRate": 3.0, "MinRate": 0.5, "Decay": 4.0, "DryTime": 7.0, "MaxInfil": 0.0},
        {"CurvNo": 80.0, "Conductivity": 0.5, "DryTime": 7.0},
        {"CurveNum": 80.0, "Conductivity": 0.5, "DryTime": 7.0},
        {"Suction": 3.5, "Ksat": 0.5, "IMD": 0.25},
        {},
    ],
)
def test_validate_parameters_accepts_polymorphic_infiltration(urban_params, custom_infil):
    import dataclasses

    p = dataclasses.replace(urban_params, infiltration=custom_infil)
    assert validate_parameters(p) is p


def test_validate_parameters_rejects_unknown_infiltration_keys(urban_params):
    import dataclasses

    with pytest.raises(ValidationError) as info:
        validate_parameters(dataclasses.replace(urban_params, infiltration={"UnknownKey": 1.0}))
    assert info.value.field == "infiltration[UnknownKey]"
    assert "Unknown infiltration parameter 'UnknownKey'" in str(info.value)


def test_validate_parameters_rejects_negative_and_nonfinite_infiltration(urban_params):
    import dataclasses

    with pytest.raises(ValidationError) as info1:
        validate_parameters(dataclasses.replace(urban_params, infiltration={"MaxRate": -1.0}))
    assert info1.value.field == "infiltration[MaxRate]"
    assert "must be >= 0" in str(info1.value)

    with pytest.raises(ValidationError) as info2:
        validate_parameters(dataclasses.replace(urban_params, infiltration={"CurvNo": float("nan")}))
    assert info2.value.field == "infiltration[CurvNo]"
    assert "must be a finite number" in str(info2.value)


def test_validate_parameters_rejects_non_mapping_infiltration(urban_params):
    import dataclasses

    p = dataclasses.replace(urban_params)
    object.__setattr__(p, "infiltration", [("MaxRate", 1.0)])
    with pytest.raises(ValidationError) as info:
        validate_parameters(p)
    assert info.value.field == "infiltration"
    assert "must be a mapping" in str(info.value)
