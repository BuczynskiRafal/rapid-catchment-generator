"""
Fuzzy logic rule definitions for catchment generation.

This module is the single source of truth for the rules that map land form and
land cover combinations to slope, impervious surface and catchment type.

The rules form a table with one cell per land cover x land form pair (14 x 9 = 126).
:data:`RULE_TABLE` lists it row by row, grouped by land cover; a row applies the same
outputs to several land forms of one land cover.
"""

from __future__ import annotations

import threading
from collections import Counter
from collections.abc import Sequence

from rcg.exceptions import RuleDefinitionError

from .categories import Catchments, Impervious, LandCover, LandForm, Slope
from .rule_engine import RuleEngine, rule

RuleRow = tuple[LandCover, tuple[LandForm, ...], Slope, Impervious, Catchments]
"""One table row: land cover, the land forms it covers, then slope, impervious and catchment."""

_C, _F, _S, _I, _K = LandCover, LandForm, Slope, Impervious, Catchments

# fmt: off
RULE_TABLE: tuple[RuleRow, ...] = (
    # (land cover, (land forms, ...),
    #     slope, impervious, catchment),
    (_C.permeable_areas, (_F.marshes_and_lowlands,),
        _S.marshes_and_lowlands, _I.marshes, _K.meadows),
    (_C.permeable_areas, (_F.flats_and_plateaus,),
        _S.flats_and_plateaus, _I.meadows, _K.meadows),
    (_C.permeable_areas, (_F.flats_and_plateaus_in_combination_with_hills,),
        _S.flats_and_plateaus_in_combination_with_hills, _I.arable, _K.meadows),
    (_C.permeable_areas, (_F.hills_with_gentle_slopes,),
        _S.hills_with_gentle_slopes, _I.arable, _K.arable),
    (_C.permeable_areas, (_F.steeper_hills_and_foothills,),
        _S.steeper_hills_and_foothills, _I.arable, _K.arable),
    (_C.permeable_areas, (_F.hills_and_outcrops_of_mountain_ranges,),
        _S.hills_and_outcrops_of_mountain_ranges, _I.arable, _K.arable),
    (_C.permeable_areas, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.steeper_hills_and_foothills, _I.mountains_vegetated, _K.mountains),

    (_C.permeable_terrain_on_plains, (_F.marshes_and_lowlands,),
        _S.marshes_and_lowlands, _I.marshes, _K.meadows),
    (_C.permeable_terrain_on_plains, (_F.flats_and_plateaus,),
        _S.flats_and_plateaus, _I.meadows, _K.meadows),
    (_C.permeable_terrain_on_plains, (_F.flats_and_plateaus_in_combination_with_hills,),
        _S.flats_and_plateaus_in_combination_with_hills, _I.arable, _K.meadows),
    (_C.permeable_terrain_on_plains, (_F.hills_with_gentle_slopes,),
        _S.hills_with_gentle_slopes, _I.arable, _K.arable),
    (_C.permeable_terrain_on_plains, (_F.steeper_hills_and_foothills,),
        _S.steeper_hills_and_foothills, _I.arable, _K.arable),
    (_C.permeable_terrain_on_plains, (_F.hills_and_outcrops_of_mountain_ranges,),
        _S.hills_and_outcrops_of_mountain_ranges, _I.arable, _K.arable),
    (_C.permeable_terrain_on_plains, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.steeper_hills_and_foothills, _I.mountains_vegetated, _K.mountains),

    (_C.mountains_vegetated, (_F.marshes_and_lowlands,),
        _S.flats_and_plateaus, _I.mountains_vegetated, _K.meadows),
    (_C.mountains_vegetated, (_F.flats_and_plateaus, _F.flats_and_plateaus_in_combination_with_hills, _F.hills_with_gentle_slopes, _F.steeper_hills_and_foothills),
        _S.steeper_hills_and_foothills, _I.mountains_vegetated, _K.mountains),
    (_C.mountains_vegetated, (_F.hills_and_outcrops_of_mountain_ranges,),
        _S.hills_and_outcrops_of_mountain_ranges, _I.mountains_vegetated, _K.mountains),
    (_C.mountains_vegetated, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.higher_hills, _I.mountains_rocky, _K.mountains),

    (_C.mountains_rocky, (_F.marshes_and_lowlands,),
        _S.flats_and_plateaus, _I.mountains_vegetated, _K.meadows),
    (_C.mountains_rocky, (_F.flats_and_plateaus,),
        _S.flats_and_plateaus, _I.mountains_rocky, _K.mountains),
    (_C.mountains_rocky, (_F.flats_and_plateaus_in_combination_with_hills,),
        _S.flats_and_plateaus_in_combination_with_hills, _I.mountains_rocky, _K.mountains),
    (_C.mountains_rocky, (_F.hills_with_gentle_slopes,),
        _S.hills_with_gentle_slopes, _I.mountains_rocky, _K.mountains),
    (_C.mountains_rocky, (_F.steeper_hills_and_foothills,),
        _S.steeper_hills_and_foothills, _I.mountains_rocky, _K.mountains),
    (_C.mountains_rocky, (_F.hills_and_outcrops_of_mountain_ranges,),
        _S.hills_and_outcrops_of_mountain_ranges, _I.mountains_rocky, _K.mountains),
    (_C.mountains_rocky, (_F.higher_hills,),
        _S.higher_hills, _I.mountains_rocky, _K.mountains),
    (_C.mountains_rocky, (_F.mountains, _F.highest_mountains),
        _S.mountains, _I.mountains_rocky, _K.mountains),

    (_C.urban_weakly_impervious, (_F.marshes_and_lowlands, _F.flats_and_plateaus),
        _S.marshes_and_lowlands, _I.urban_weakly_impervious, _K.urban),
    (_C.urban_weakly_impervious, (_F.flats_and_plateaus_in_combination_with_hills, _F.hills_with_gentle_slopes),
        _S.flats_and_plateaus_in_combination_with_hills, _I.urban_weakly_impervious, _K.urban),
    (_C.urban_weakly_impervious, (_F.steeper_hills_and_foothills, _F.hills_and_outcrops_of_mountain_ranges),
        _S.steeper_hills_and_foothills, _I.urban_highly_impervious, _K.urban),
    (_C.urban_weakly_impervious, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.higher_hills, _I.urban_moderately_impervious, _K.urban),

    (_C.urban_moderately_impervious, (_F.marshes_and_lowlands, _F.flats_and_plateaus),
        _S.marshes_and_lowlands, _I.urban_moderately_impervious, _K.urban),
    (_C.urban_moderately_impervious, (_F.flats_and_plateaus_in_combination_with_hills, _F.hills_with_gentle_slopes, _F.steeper_hills_and_foothills),
        _S.flats_and_plateaus_in_combination_with_hills, _I.urban_moderately_impervious, _K.urban),
    (_C.urban_moderately_impervious, (_F.hills_and_outcrops_of_mountain_ranges, _F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.hills_and_outcrops_of_mountain_ranges, _I.urban_moderately_impervious, _K.urban),

    (_C.urban_highly_impervious, (_F.marshes_and_lowlands,),
        _S.marshes_and_lowlands, _I.urban_highly_impervious, _K.urban),
    (_C.urban_highly_impervious, (_F.flats_and_plateaus,),
        _S.flats_and_plateaus, _I.urban_highly_impervious, _K.mountains),
    (_C.urban_highly_impervious, (_F.flats_and_plateaus_in_combination_with_hills,),
        _S.flats_and_plateaus_in_combination_with_hills, _I.urban_highly_impervious, _K.urban),
    (_C.urban_highly_impervious, (_F.hills_with_gentle_slopes, _F.steeper_hills_and_foothills, _F.hills_and_outcrops_of_mountain_ranges),
        _S.hills_with_gentle_slopes, _I.urban_highly_impervious, _K.urban),
    (_C.urban_highly_impervious, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.mountains, _I.urban_highly_impervious, _K.urban),

    (_C.suburban_weakly_impervious, (_F.marshes_and_lowlands,),
        _S.marshes_and_lowlands, _I.suburban_weakly_impervious, _K.suburban),
    (_C.suburban_weakly_impervious, (_F.flats_and_plateaus, _F.flats_and_plateaus_in_combination_with_hills),
        _S.flats_and_plateaus, _I.suburban_weakly_impervious, _K.suburban),
    (_C.suburban_weakly_impervious, (_F.hills_with_gentle_slopes, _F.steeper_hills_and_foothills),
        _S.hills_with_gentle_slopes, _I.suburban_weakly_impervious, _K.suburban),
    (_C.suburban_weakly_impervious, (_F.hills_and_outcrops_of_mountain_ranges,),
        _S.hills_and_outcrops_of_mountain_ranges, _I.suburban_weakly_impervious, _K.suburban),
    (_C.suburban_weakly_impervious, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.higher_hills, _I.suburban_weakly_impervious, _K.suburban),

    (_C.suburban_highly_impervious, (_F.marshes_and_lowlands, _F.flats_and_plateaus),
        _S.marshes_and_lowlands, _I.suburban_highly_impervious, _K.suburban),
    (_C.suburban_highly_impervious, (_F.flats_and_plateaus_in_combination_with_hills,),
        _S.flats_and_plateaus_in_combination_with_hills, _I.suburban_highly_impervious, _K.suburban),
    (_C.suburban_highly_impervious, (_F.hills_with_gentle_slopes, _F.steeper_hills_and_foothills, _F.hills_and_outcrops_of_mountain_ranges),
        _S.hills_with_gentle_slopes, _I.suburban_highly_impervious, _K.suburban),
    (_C.suburban_highly_impervious, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.higher_hills, _I.suburban_highly_impervious, _K.suburban),

    (_C.rural, (_F.marshes_and_lowlands,),
        _S.marshes_and_lowlands, _I.rural, _K.rural),
    (_C.rural, (_F.flats_and_plateaus,),
        _S.flats_and_plateaus, _I.rural, _K.rural),
    (_C.rural, (_F.flats_and_plateaus_in_combination_with_hills,),
        _S.flats_and_plateaus_in_combination_with_hills, _I.rural, _K.rural),
    (_C.rural, (_F.hills_with_gentle_slopes,),
        _S.hills_with_gentle_slopes, _I.rural, _K.rural),
    (_C.rural, (_F.steeper_hills_and_foothills,),
        _S.steeper_hills_and_foothills, _I.rural, _K.rural),
    (_C.rural, (_F.hills_and_outcrops_of_mountain_ranges,),
        _S.hills_and_outcrops_of_mountain_ranges, _I.rural, _K.rural),
    (_C.rural, (_F.higher_hills,),
        _S.higher_hills, _I.rural, _K.rural),
    (_C.rural, (_F.mountains,),
        _S.mountains, _I.rural, _K.rural),
    (_C.rural, (_F.highest_mountains,),
        _S.highest_mountains, _I.rural, _K.rural),

    (_C.forests, (_F.marshes_and_lowlands, _F.flats_and_plateaus),
        _S.flats_and_plateaus, _I.forests, _K.forests),
    (_C.forests, (_F.flats_and_plateaus_in_combination_with_hills, _F.hills_with_gentle_slopes),
        _S.flats_and_plateaus_in_combination_with_hills, _I.forests, _K.forests),
    (_C.forests, (_F.steeper_hills_and_foothills, _F.hills_and_outcrops_of_mountain_ranges),
        _S.hills_and_outcrops_of_mountain_ranges, _I.forests, _K.forests),
    (_C.forests, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.steeper_hills_and_foothills, _I.mountains_vegetated, _K.mountains),

    (_C.meadows, (_F.marshes_and_lowlands,),
        _S.marshes_and_lowlands, _I.meadows, _K.meadows),
    (_C.meadows, (_F.flats_and_plateaus, _F.flats_and_plateaus_in_combination_with_hills),
        _S.flats_and_plateaus, _I.meadows, _K.meadows),
    (_C.meadows, (_F.hills_with_gentle_slopes, _F.steeper_hills_and_foothills),
        _S.hills_with_gentle_slopes, _I.meadows, _K.meadows),
    (_C.meadows, (_F.hills_and_outcrops_of_mountain_ranges, _F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.steeper_hills_and_foothills, _I.mountains_vegetated, _K.mountains),

    (_C.arable, (_F.marshes_and_lowlands,),
        _S.flats_and_plateaus, _I.meadows, _K.meadows),
    (_C.arable, (_F.flats_and_plateaus, _F.flats_and_plateaus_in_combination_with_hills, _F.hills_with_gentle_slopes),
        _S.flats_and_plateaus_in_combination_with_hills, _I.arable, _K.arable),
    (_C.arable, (_F.steeper_hills_and_foothills, _F.hills_and_outcrops_of_mountain_ranges),
        _S.steeper_hills_and_foothills, _I.arable, _K.arable),
    (_C.arable, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.steeper_hills_and_foothills, _I.mountains_vegetated, _K.mountains),

    (_C.marshes, (_F.marshes_and_lowlands, _F.flats_and_plateaus, _F.flats_and_plateaus_in_combination_with_hills),
        _S.marshes_and_lowlands, _I.marshes, _K.meadows),
    (_C.marshes, (_F.hills_with_gentle_slopes, _F.steeper_hills_and_foothills, _F.hills_and_outcrops_of_mountain_ranges),
        _S.marshes_and_lowlands, _I.meadows, _K.meadows),
    (_C.marshes, (_F.higher_hills, _F.mountains, _F.highest_mountains),
        _S.steeper_hills_and_foothills, _I.mountains_vegetated, _K.mountains),
)
# fmt: on


def check_rule_table(table: Sequence[RuleRow]) -> None:
    """Make sure ``table`` has exactly one row for every land cover x land form pair.

    Raises
    ------
    RuleDefinitionError
        If a pair is missing or listed more than once.
    """
    cells = Counter((cover, form) for cover, forms, *_ in table for form in forms)
    missing = [f"{c.name}/{f.name}" for c in LandCover for f in LandForm if (c, f) not in cells]
    repeated = [f"{c.name}/{f.name}" for (c, f), n in cells.items() if n > 1]
    problems = []
    if missing:
        problems.append(f"missing {', '.join(missing)}")
    if repeated:
        problems.append(f"repeated {', '.join(repeated)}")
    if problems:
        raise RuleDefinitionError(f"The rule table must cover each land cover/land form pair once: {'; '.join(problems)}")


def define_all_rules(engine: RuleEngine, table: Sequence[RuleRow] = RULE_TABLE) -> RuleEngine:
    """Add every catchment rule to ``engine`` and build its skfuzzy rule systems.

    Parameters
    ----------
    engine : RuleEngine
        Engine to populate. It should be empty; rules are appended.
    table : sequence of RuleRow, optional
        Rules to add. Defaults to :data:`RULE_TABLE`.

    Returns
    -------
    RuleEngine
        The same engine, with rule systems built.

    Raises
    ------
    RuleDefinitionError
        If ``table`` misses a land cover/land form pair or repeats one.
    """
    check_rule_table(table)
    for cover, forms, slope, impervious, catchment in table:
        for form in forms:
            engine.add_rule(
                rule(f"{cover.name}_on_{form.name}")
                .when(land_cover=cover, land_form=form)
                .then(slope=slope, impervious=impervious, catchment=catchment)
                .build()
            )
    engine.build_rule_systems()
    return engine


_default_rules: RuleEngine | None = None
_default_rules_lock = threading.Lock()


def get_default_rules() -> RuleEngine:
    """Return the shared rule engine populated with :func:`define_all_rules` (built once)."""
    global _default_rules
    if _default_rules is None:
        with _default_rules_lock:
            if _default_rules is None:
                _default_rules = define_all_rules(RuleEngine())
    return _default_rules
