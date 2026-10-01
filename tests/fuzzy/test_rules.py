import pytest
from skfuzzy import control as ctrl

from rcg.fuzzy.categories import Catchments, Impervious, LandCover, LandForm, Slope
from rcg.fuzzy.rule_definitions import get_default_rules
from rcg.fuzzy.rule_engine import FuzzyRule, RuleEngine, create_rule_engine, rule


@pytest.fixture(scope="module")
def rules() -> RuleEngine:
    return get_default_rules()


@pytest.mark.parametrize("output", ["slope_rules", "impervious_rules", "catchment_rules"])
def test_rule_systems_are_built(rules, output):
    built = getattr(rules, output)
    assert built
    assert all(isinstance(r, ctrl.Rule) for r in built)


def test_rule_count(rules):
    counts = rules.get_rule_count()
    assert set(counts) == {"total", "slope", "impervious", "catchment"}
    assert counts["total"] > 50
    # Every rule defines all three consequences.
    assert counts["slope"] == counts["impervious"] == counts["catchment"] == counts["total"]


def test_every_combination_is_covered_by_a_rule(rules):
    covered = set()
    for r in rules.rules:
        values = {c.variable: c.value for c in r.conditions}
        covered.add((values["land_form"], values["land_cover"]))
    assert covered == {(f, c) for f in LandForm for c in LandCover}


def test_rule_names_are_unique(rules):
    names = [r.name for r in rules.rules]
    assert len(names) == len(set(names))


def test_default_rules_are_built_once(rules):
    assert get_default_rules() is rules


def test_builder_creates_rule():
    built = (
        rule("test_rule")
        .when(land_form=LandForm.flats_and_plateaus, land_cover=LandCover.rural)
        .then(slope=Slope.flats_and_plateaus, impervious=Impervious.rural, catchment=Catchments.rural)
        .build()
    )
    assert isinstance(built, FuzzyRule)
    assert built.name == "test_rule"
    assert len(built.conditions) == 2


def test_builder_requires_conditions():
    with pytest.raises(ValueError):
        rule("empty_rule").then(slope=Slope.flats_and_plateaus).build()


def test_builder_requires_consequences():
    with pytest.raises(ValueError):
        rule("no_consequence").when(land_form=LandForm.mountains).build()


def test_builder_rejects_non_enum_values():
    with pytest.raises(ValueError):
        rule("bad").when(land_form="mountains")


def test_create_rule_engine_is_empty():
    engine = create_rule_engine()
    assert engine.rules == []
    assert engine.get_rule_count()["total"] == 0
