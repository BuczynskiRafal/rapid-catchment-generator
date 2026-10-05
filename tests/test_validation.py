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


@pytest.mark.parametrize("value", ["", "   ", 6, None, LandCover.rural])
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
    (tmp_path / "empty.inp").write_text("")
    with pytest.raises(ValidationError, match="empty"):
        validate_inp_path(tmp_path / "empty.inp")


def test_validate_inp_path_upper_case_extension(tmp_path):
    path = tmp_path / "MODEL.INP"
    path.write_text("[TITLE]\n")
    assert validate_inp_path(path) == path


def test_validate_output_path(tmp_path):
    assert validate_inp_path(tmp_path / "new.inp", must_exist=False) == tmp_path / "new.inp"
    with pytest.raises(ValidationError, match="Directory does not exist"):
        validate_inp_path(tmp_path / "nope" / "new.inp", must_exist=False)
    (tmp_path / "folder.inp").mkdir()
    with pytest.raises(ValidationError, match="Not a file"):
        validate_inp_path(tmp_path / "folder.inp", must_exist=False)
