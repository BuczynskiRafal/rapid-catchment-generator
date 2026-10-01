"""Golden regression test: the hydrological outputs must never drift.

``tests/golden/fuzzy_outcomes.json`` was captured from the reference implementation
for every land form x land cover combination (9 x 14 = 126). Any refactor of the
fuzzy engine, the rule set, the memberships or the SWMM parameter mapping must keep
this test green. If a change is *intended* to alter the numbers, regenerate the
fixture deliberately and explain why in the commit.

Deliberate difference from 1.x (see "Numerical changes vs 1.x" in docs/DESIGN.md):
1.x defined the rule ``mountains_vegetated x hills_and_outcrops_of_mountain_ranges``
twice (in its "Rule 3" loop and again as "Rule 4"), with different slope terms, so the
two rules were OR-ed. 2.0 keeps only the dedicated Rule 4, giving that one combination
slope 14.333 % instead of 1.x's 12.164 % (imperviousness and catchment type are
unchanged). The fixture holds the 2.0 value; ``test_rule_set_has_one_rule_per_combination``
guards against the duplicate coming back.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from rcg.fuzzy.categories import LandCover, LandForm

GOLDEN_PATH = Path(__file__).parent / "golden" / "fuzzy_outcomes.json"
GOLDEN = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
COMBOS = sorted(GOLDEN["combos"])

ABS_TOL = 1e-4


def _split(key: str) -> tuple[LandForm, LandCover]:
    form, cover = key.split("|")
    return LandForm[form], LandCover[cover]


def test_golden_covers_every_combination() -> None:
    expected = {f"{f.name}|{c.name}" for f in LandForm for c in LandCover}
    assert set(COMBOS) == expected


@pytest.mark.parametrize("key", COMBOS)
def test_parameters_match_golden(key: str, golden_preview) -> None:
    land_form, land_cover = _split(key)
    expected = GOLDEN["combos"][key]
    actual = golden_preview(land_form, land_cover)

    assert actual["catchment_type"] == expected["catchment_type"], key
    for name in ("slope", "impervious", "catchment", "s_imperv", "s_perv"):
        assert math.isclose(actual[name], expected[name], abs_tol=ABS_TOL), (key, name, actual[name], expected[name])
    for name in ("n_imperv", "n_perv", "pct_zero"):
        assert actual[name] == expected[name], (key, name)


def test_width_formula_matches_golden(golden_width) -> None:
    area = GOLDEN["area_ha_for_width"]
    assert math.isclose(golden_width(area), GOLDEN["width_for_5ha"], abs_tol=1e-9)


def test_rule_set_has_one_rule_per_combination() -> None:
    from collections import Counter

    from rcg.fuzzy.rule_definitions import get_default_rules

    rules = get_default_rules().rules
    pairs = Counter(
        (values["land_form"], values["land_cover"]) for values in ({c.variable: c.value for c in r.conditions} for r in rules)
    )
    assert len(rules) == 126 == len(LandForm) * len(LandCover)
    assert set(pairs.values()) == {1}
    assert pairs[(LandForm.hills_and_outcrops_of_mountain_ranges, LandCover.mountains_vegetated)] == 1
    assert math.isclose(
        GOLDEN["combos"]["hills_and_outcrops_of_mountain_ranges|mountains_vegetated"]["slope"], 14.333333, abs_tol=ABS_TOL
    )
