import pytest

from rcg.fuzzy.categories import Catchments, Impervious, LandCover, LandForm, Slope


def test_land_form_values_are_1_to_9_in_order():
    assert [m.value for m in LandForm] == list(range(1, 10))
    assert LandForm.marshes_and_lowlands == 1
    assert LandForm.highest_mountains == 9


def test_land_cover_values_are_1_to_14_in_order():
    assert [m.value for m in LandCover] == list(range(1, 15))
    assert LandCover.urban_highly_impervious == 7
    assert LandCover.marshes == 14


@pytest.mark.parametrize(
    ("enum_cls", "count", "sample"),
    [
        (LandForm, 9, "flats_and_plateaus"),
        (LandCover, 14, "rural"),
        (Slope, 9, "highest_mountains"),
        (Impervious, 12, "urban_highly_impervious"),
        (Catchments, 7, "forests"),
    ],
)
def test_get_all_categories(enum_cls, count, sample):
    categories = enum_cls.get_all_categories()
    assert len(categories) == count
    assert sample in categories


def test_linguistic_enums_use_names_as_values():
    for enum_cls in (Slope, Impervious, Catchments):
        assert all(m.name == m.value for m in enum_cls)


def test_slope_terms_mirror_land_forms():
    assert Slope.get_all_categories() == LandForm.get_all_categories()


def test_impervious_terms_are_land_covers():
    # Impervious repeats land cover names; a renamed land cover must be renamed here too.
    assert set(Impervious.get_all_categories()) <= set(LandCover.get_all_categories())
