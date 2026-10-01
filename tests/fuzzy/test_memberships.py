import pytest
from skfuzzy import control as ctrl

from rcg.fuzzy.categories import Catchments, Impervious, LandCover, LandForm, Slope
from rcg.fuzzy.memberships import Memberships, create_memberships, get_default_memberships


@pytest.fixture(scope="module")
def memberships() -> Memberships:
    return get_default_memberships()


def test_variable_types(memberships):
    assert isinstance(memberships.land_form_type, ctrl.Antecedent)
    assert isinstance(memberships.land_cover_type, ctrl.Antecedent)
    for consequent in (memberships.slope, memberships.impervious, memberships.catchment):
        assert isinstance(consequent, ctrl.Consequent)


def test_labels(memberships):
    assert memberships.land_form_type.label == "land_form"
    assert memberships.land_cover_type.label == "land_cover"
    assert memberships.slope.label == "slope"
    assert memberships.impervious.label == "impervious"
    assert memberships.catchment.label == "catchment"


@pytest.mark.parametrize(
    ("attr", "enum_cls"),
    [
        ("land_form_type", LandForm),
        ("land_cover_type", LandCover),
        ("slope", Slope),
        ("impervious", Impervious),
        ("catchment", Catchments),
    ],
)
def test_terms_match_categories(memberships, attr, enum_cls):
    assert set(getattr(memberships, attr).terms) == {m.name for m in enum_cls}


def test_default_instance_is_shared_and_factory_is_fresh(memberships):
    assert get_default_memberships() is memberships
    assert create_memberships() is not memberships
