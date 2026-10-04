import pytest
from skfuzzy import control as ctrl

from rcg.exceptions import RuleDefinitionError
from rcg.fuzzy.categories import Catchments, Impervious, LandCover, LandForm, Slope
from rcg.fuzzy.rule_definitions import RULE_TABLE, check_rule_table, define_all_rules, get_default_rules
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


def test_rule_table_has_one_row_per_cell():
    check_rule_table(RULE_TABLE)  # does not raise
    assert sum(len(forms) for _, forms, *_ in RULE_TABLE) == len(LandForm) * len(LandCover)


def test_rule_table_missing_cell_is_rejected():
    cover, forms, *outputs = RULE_TABLE[0]
    table = (*RULE_TABLE[1:], (cover, forms[1:], *outputs))
    with pytest.raises(RuleDefinitionError, match=f"missing {cover.name}/{forms[0].name}"):
        define_all_rules(create_rule_engine(), table)


def test_rule_table_repeated_cell_is_rejected():
    with pytest.raises(RuleDefinitionError, match="repeated"):
        define_all_rules(create_rule_engine(), (*RULE_TABLE, RULE_TABLE[0]))


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


def test_builder_errors_are_rule_definition_errors():
    with pytest.raises(RuleDefinitionError) as info:
        rule("bad").when(land_form="mountains")
    assert info.value.rule_name == "bad"
    assert isinstance(info.value, ValueError)  # 2.0.0 raised ValueError


@pytest.mark.parametrize(
    ("built", "message"),
    [
        (
            rule("r").when(slope_form=LandForm.mountains).then(slope=Slope.mountains).build(),
            "Unknown fuzzy variable 'slope_form'",
        ),
        (rule("r").when(land_form=LandCover.rural).then(slope=Slope.mountains).build(), "'land_form' has no term 'rural'"),
        (rule("r").when(land_form=LandForm.mountains).then(slpoe=Slope.mountains).build(), "Unknown output 'slpoe'"),
    ],
)
def test_build_rule_systems_names_the_bad_rule(built, message):
    engine = create_rule_engine()
    engine.add_rule(built)
    with pytest.raises(RuleDefinitionError, match=message) as info:
        engine.build_rule_systems()
    assert info.value.rule_name == "r"
    assert str(info.value).startswith("Rule 'r': ")
