"""
Fuzzy logic rule definitions for catchment generation.

This module contains rules that determine slope, impervious surface, and catchment
characteristics based on land form and land cover combinations.
"""
from .rule_engine import rule, default_engine
from .categories import LandForm, LandCover, Slope, Impervious, Catchments


def define_all_rules():
    """
    Define fuzzy logic rules for catchment parameter calculation.

    Creates rules that map land form and land cover combinations to appropriate
    slope, impervious surface, and catchment type values.
    """

    # Rule 1: Mountains on lowlands
    default_engine.add_rule(
        rule("mountains_vegetated_on_marshes")
        .when(land_cover=LandCover.mountains_vegetated, land_form=LandForm.marshes_and_lowlands)
        .then(slope=Slope.flats_and_plateaus, impervious=Impervious.mountains_vegetated, catchment=Catchments.meadows)
        .build()
    )

    default_engine.add_rule(
        rule("mountains_rocky_on_marshes")
        .when(land_cover=LandCover.mountains_rocky, land_form=LandForm.marshes_and_lowlands)
        .then(slope=Slope.flats_and_plateaus, impervious=Impervious.mountains_vegetated, catchment=Catchments.meadows)
        .build()
    )

    # Rule 2: Complex mountain and natural terrain rule
    for land_cover_val, land_form_val in [
        (LandCover.marshes, LandForm.mountains),
        (LandCover.marshes, LandForm.highest_mountains),
        (LandCover.permeable_areas, LandForm.mountains),
        (LandCover.permeable_areas, LandForm.highest_mountains),
        (LandCover.permeable_areas, LandForm.higher_hills),
        (LandCover.permeable_terrain_on_plains, LandForm.higher_hills),
        (LandCover.permeable_terrain_on_plains, LandForm.mountains),
        (LandCover.permeable_terrain_on_plains, LandForm.highest_mountains),
        (LandCover.forests, LandForm.higher_hills),
        (LandCover.forests, LandForm.mountains),
        (LandCover.forests, LandForm.highest_mountains),
        (LandCover.meadows, LandForm.hills_and_outcrops_of_mountain_ranges),
        (LandCover.meadows, LandForm.higher_hills),
        (LandCover.meadows, LandForm.mountains),
        (LandCover.meadows, LandForm.highest_mountains),
        (LandCover.arable, LandForm.higher_hills),
        (LandCover.arable, LandForm.mountains),
        (LandCover.arable, LandForm.highest_mountains),
        (LandCover.marshes, LandForm.higher_hills)
    ]:
        default_engine.add_rule(
            rule(f"steep_terrain_{land_cover_val.name}_{land_form_val.name}")
            .when(land_cover=land_cover_val, land_form=land_form_val)
            .then(slope=Slope.steeper_hills_and_foothills, impervious=Impervious.mountains_vegetated, catchment=Catchments.mountains)
            .build()
        )

    # Rule 3: Mountains vegetated on various terrains
    for land_form_val in [
        LandForm.flats_and_plateaus,
        LandForm.flats_and_plateaus_in_combination_with_hills,
        LandForm.hills_and_outcrops_of_mountain_ranges,
        LandForm.hills_with_gentle_slopes,
        LandForm.steeper_hills_and_foothills
    ]:
        default_engine.add_rule(
            rule(f"mountains_vegetated_on_{land_form_val.name}")
            .when(land_cover=LandCover.mountains_vegetated, land_form=land_form_val)
            .then(slope=Slope.steeper_hills_and_foothills, impervious=Impervious.mountains_vegetated, catchment=Catchments.mountains)
            .build()
        )

    # Rule 4: Mountains vegetated on hills and outcrops
    default_engine.add_rule(
        rule("mountains_vegetated_on_hills_outcrops")
        .when(land_cover=LandCover.mountains_vegetated, land_form=LandForm.hills_and_outcrops_of_mountain_ranges)
        .then(slope=Slope.hills_and_outcrops_of_mountain_ranges, impervious=Impervious.mountains_vegetated, catchment=Catchments.mountains)
        .build()
    )

    # Rule 6: Mountains vegetated on high terrain
    for land_form_val in [LandForm.higher_hills, LandForm.mountains, LandForm.highest_mountains]:
        default_engine.add_rule(
            rule(f"mountains_vegetated_high_{land_form_val.name}")
            .when(land_cover=LandCover.mountains_vegetated, land_form=land_form_val)
            .then(slope=Slope.higher_hills, impervious=Impervious.mountains_rocky, catchment=Catchments.mountains)
            .build()
        )

    # Rule 7: Mountains rocky on flats
    default_engine.add_rule(
        rule("mountains_rocky_on_flats")
        .when(land_cover=LandCover.mountains_rocky, land_form=LandForm.flats_and_plateaus)
        .then(slope=Slope.flats_and_plateaus, impervious=Impervious.mountains_rocky, catchment=Catchments.mountains)
        .build()
    )

    # Rule 8: Mountains rocky on combination hills
    default_engine.add_rule(
        rule("mountains_rocky_on_combo_hills")
        .when(land_cover=LandCover.mountains_rocky, land_form=LandForm.flats_and_plateaus_in_combination_with_hills)
        .then(slope=Slope.flats_and_plateaus_in_combination_with_hills, impervious=Impervious.mountains_rocky, catchment=Catchments.mountains)
        .build()
    )

    # Rule 9: Mountains rocky on gentle slopes
    default_engine.add_rule(
        rule("mountains_rocky_on_gentle_slopes")
        .when(land_cover=LandCover.mountains_rocky, land_form=LandForm.hills_with_gentle_slopes)
        .then(slope=Slope.hills_with_gentle_slopes, impervious=Impervious.mountains_rocky, catchment=Catchments.mountains)
        .build()
    )

    # Rule 10: Mountains rocky on steeper hills
    default_engine.add_rule(
        rule("mountains_rocky_on_steeper_hills")
        .when(land_cover=LandCover.mountains_rocky, land_form=LandForm.steeper_hills_and_foothills)
        .then(slope=Slope.steeper_hills_and_foothills, impervious=Impervious.mountains_rocky, catchment=Catchments.mountains)
        .build()
    )

    # Rule 11: Mountains rocky on hills and outcrops
    default_engine.add_rule(
        rule("mountains_rocky_on_hills_outcrops")
        .when(land_cover=LandCover.mountains_rocky, land_form=LandForm.hills_and_outcrops_of_mountain_ranges)
        .then(slope=Slope.hills_and_outcrops_of_mountain_ranges, impervious=Impervious.mountains_rocky, catchment=Catchments.mountains)
        .build()
    )

    # Rule 12: Mountains rocky on higher hills
    default_engine.add_rule(
        rule("mountains_rocky_on_higher_hills")
        .when(land_cover=LandCover.mountains_rocky, land_form=LandForm.higher_hills)
        .then(slope=Slope.higher_hills, impervious=Impervious.mountains_rocky, catchment=Catchments.mountains)
        .build()
    )

    # Rule 13: Mountains rocky on mountains
    for land_form_val in [LandForm.mountains, LandForm.highest_mountains]:
        default_engine.add_rule(
            rule(f"mountains_rocky_on_{land_form_val.name}")
            .when(land_cover=LandCover.mountains_rocky, land_form=land_form_val)
            .then(slope=Slope.mountains, impervious=Impervious.mountains_rocky, catchment=Catchments.mountains)
            .build()
        )

    # Rule 14: Urban weakly impervious on low terrain
    for land_form_val in [LandForm.marshes_and_lowlands, LandForm.flats_and_plateaus]:
        default_engine.add_rule(
            rule(f"urban_weak_on_{land_form_val.name}")
            .when(land_cover=LandCover.urban_weakly_impervious, land_form=land_form_val)
            .then(slope=Slope.marshes_and_lowlands, impervious=Impervious.urban_weakly_impervious, catchment=Catchments.urban)
            .build()
        )

    # Rule 15: Urban weakly impervious on moderate terrain
    for land_form_val in [LandForm.flats_and_plateaus_in_combination_with_hills, LandForm.hills_with_gentle_slopes]:
        default_engine.add_rule(
            rule(f"urban_weak_moderate_{land_form_val.name}")
            .when(land_cover=LandCover.urban_weakly_impervious, land_form=land_form_val)
            .then(slope=Slope.flats_and_plateaus_in_combination_with_hills, impervious=Impervious.urban_weakly_impervious, catchment=Catchments.urban)
            .build()
        )

    # Rule 16: Urban weakly impervious on steep terrain
    for land_form_val in [LandForm.steeper_hills_and_foothills, LandForm.hills_and_outcrops_of_mountain_ranges]:
        default_engine.add_rule(
            rule(f"urban_weak_steep_{land_form_val.name}")
            .when(land_cover=LandCover.urban_weakly_impervious, land_form=land_form_val)
            .then(slope=Slope.steeper_hills_and_foothills, impervious=Impervious.urban_highly_impervious, catchment=Catchments.urban)
            .build()
        )

    # Rule 17: Urban weakly impervious on high terrain
    for land_form_val in [LandForm.higher_hills, LandForm.mountains, LandForm.highest_mountains]:
        default_engine.add_rule(
            rule(f"urban_weak_high_{land_form_val.name}")
            .when(land_cover=LandCover.urban_weakly_impervious, land_form=land_form_val)
            .then(slope=Slope.higher_hills, impervious=Impervious.urban_moderately_impervious, catchment=Catchments.urban)
            .build()
        )

    # Rule 18: Urban moderately impervious on low terrain
    for land_form_val in [LandForm.marshes_and_lowlands, LandForm.flats_and_plateaus]:
        default_engine.add_rule(
            rule(f"urban_moderate_low_{land_form_val.name}")
            .when(land_cover=LandCover.urban_moderately_impervious, land_form=land_form_val)
            .then(slope=Slope.marshes_and_lowlands, impervious=Impervious.urban_moderately_impervious, catchment=Catchments.urban)
            .build()
        )

    # Rule 19: Urban moderately impervious on moderate terrain
    for land_form_val in [LandForm.flats_and_plateaus_in_combination_with_hills, LandForm.hills_with_gentle_slopes, LandForm.steeper_hills_and_foothills]:
        default_engine.add_rule(
            rule(f"urban_moderate_terrain_{land_form_val.name}")
            .when(land_cover=LandCover.urban_moderately_impervious, land_form=land_form_val)
            .then(slope=Slope.flats_and_plateaus_in_combination_with_hills, impervious=Impervious.urban_moderately_impervious, catchment=Catchments.urban)
            .build()
        )

    # Rule 20: Urban moderately impervious on high terrain
    for land_form_val in [LandForm.hills_and_outcrops_of_mountain_ranges, LandForm.higher_hills, LandForm.mountains, LandForm.highest_mountains]:
        default_engine.add_rule(
            rule(f"urban_moderate_high_{land_form_val.name}")
            .when(land_cover=LandCover.urban_moderately_impervious, land_form=land_form_val)
            .then(slope=Slope.hills_and_outcrops_of_mountain_ranges, impervious=Impervious.urban_moderately_impervious, catchment=Catchments.urban)
            .build()
        )

    # Rule 21: Urban highly impervious on marshes
    default_engine.add_rule(
        rule("urban_highly_on_marshes")
        .when(land_cover=LandCover.urban_highly_impervious, land_form=LandForm.marshes_and_lowlands)
        .then(slope=Slope.marshes_and_lowlands, impervious=Impervious.urban_highly_impervious, catchment=Catchments.urban)
        .build()
    )

    # Rules 22-30: Rural on all terrain types
    rural_mappings = [
        (LandForm.marshes_and_lowlands, Slope.marshes_and_lowlands),
        (LandForm.flats_and_plateaus, Slope.flats_and_plateaus),
        (LandForm.flats_and_plateaus_in_combination_with_hills, Slope.flats_and_plateaus_in_combination_with_hills),
        (LandForm.hills_with_gentle_slopes, Slope.hills_with_gentle_slopes),
        (LandForm.steeper_hills_and_foothills, Slope.steeper_hills_and_foothills),
        (LandForm.hills_and_outcrops_of_mountain_ranges, Slope.hills_and_outcrops_of_mountain_ranges),
        (LandForm.higher_hills, Slope.higher_hills),
        (LandForm.mountains, Slope.mountains),
        (LandForm.highest_mountains, Slope.highest_mountains)
    ]

    for land_form_val, slope_val in rural_mappings:
        default_engine.add_rule(
            rule(f"rural_on_{land_form_val.name}")
            .when(land_cover=LandCover.rural, land_form=land_form_val)
            .then(slope=slope_val, impervious=Impervious.rural, catchment=Catchments.rural)
            .build()
        )

    # Rule 31: Forests on low terrain
    for land_form_val in [LandForm.marshes_and_lowlands, LandForm.flats_and_plateaus]:
        default_engine.add_rule(
            rule(f"forests_low_{land_form_val.name}")
            .when(land_cover=LandCover.forests, land_form=land_form_val)
            .then(slope=Slope.flats_and_plateaus, impervious=Impervious.forests, catchment=Catchments.forests)
            .build()
        )

    # Rule 32: Forests on moderate terrain
    for land_form_val in [LandForm.flats_and_plateaus_in_combination_with_hills, LandForm.hills_with_gentle_slopes]:
        default_engine.add_rule(
            rule(f"forests_moderate_{land_form_val.name}")
            .when(land_cover=LandCover.forests, land_form=land_form_val)
            .then(slope=Slope.flats_and_plateaus_in_combination_with_hills, impervious=Impervious.forests, catchment=Catchments.forests)
            .build()
        )

    # Rule 33: Forests on steep terrain
    for land_form_val in [LandForm.steeper_hills_and_foothills, LandForm.hills_and_outcrops_of_mountain_ranges]:
        default_engine.add_rule(
            rule(f"forests_steep_{land_form_val.name}")
            .when(land_cover=LandCover.forests, land_form=land_form_val)
            .then(slope=Slope.hills_and_outcrops_of_mountain_ranges, impervious=Impervious.forests, catchment=Catchments.forests)
            .build()
        )

    # Rule 34: Marshes on low terrain
    for land_form_val in [LandForm.marshes_and_lowlands, LandForm.flats_and_plateaus, LandForm.flats_and_plateaus_in_combination_with_hills]:
        default_engine.add_rule(
            rule(f"marshes_low_{land_form_val.name}")
            .when(land_cover=LandCover.marshes, land_form=land_form_val)
            .then(slope=Slope.marshes_and_lowlands, impervious=Impervious.marshes, catchment=Catchments.meadows)
            .build()
        )

    # Rule 35: Marshes on hilly terrain
    for land_form_val in [LandForm.hills_with_gentle_slopes, LandForm.steeper_hills_and_foothills, LandForm.hills_and_outcrops_of_mountain_ranges]:
        default_engine.add_rule(
            rule(f"marshes_hilly_{land_form_val.name}")
            .when(land_cover=LandCover.marshes, land_form=land_form_val)
            .then(slope=Slope.marshes_and_lowlands, impervious=Impervious.meadows, catchment=Catchments.meadows)
            .build()
        )

    # Rule 36: Meadows on marshes
    default_engine.add_rule(
        rule("meadows_on_marshes")
        .when(land_cover=LandCover.meadows, land_form=LandForm.marshes_and_lowlands)
        .then(slope=Slope.marshes_and_lowlands, impervious=Impervious.meadows, catchment=Catchments.meadows)
        .build()
    )

    # Rule 37: Meadows on flat terrain
    for land_form_val in [LandForm.flats_and_plateaus, LandForm.flats_and_plateaus_in_combination_with_hills]:
        default_engine.add_rule(
            rule(f"meadows_flat_{land_form_val.name}")
            .when(land_cover=LandCover.meadows, land_form=land_form_val)
            .then(slope=Slope.flats_and_plateaus, impervious=Impervious.meadows, catchment=Catchments.meadows)
            .build()
        )

    # Rule 38: Meadows on hilly terrain
    for land_form_val in [LandForm.hills_with_gentle_slopes, LandForm.steeper_hills_and_foothills]:
        default_engine.add_rule(
            rule(f"meadows_hilly_{land_form_val.name}")
            .when(land_cover=LandCover.meadows, land_form=land_form_val)
            .then(slope=Slope.hills_with_gentle_slopes, impervious=Impervious.meadows, catchment=Catchments.meadows)
            .build()
        )

    # Rule 39: Arable on marshes
    default_engine.add_rule(
        rule("arable_on_marshes")
        .when(land_cover=LandCover.arable, land_form=LandForm.marshes_and_lowlands)
        .then(slope=Slope.flats_and_plateaus, impervious=Impervious.meadows, catchment=Catchments.meadows)
        .build()
    )

    # Rule 40: Arable on moderate terrain
    for land_form_val in [LandForm.flats_and_plateaus, LandForm.flats_and_plateaus_in_combination_with_hills, LandForm.hills_with_gentle_slopes]:
        default_engine.add_rule(
            rule(f"arable_moderate_{land_form_val.name}")
            .when(land_cover=LandCover.arable, land_form=land_form_val)
            .then(slope=Slope.flats_and_plateaus_in_combination_with_hills, impervious=Impervious.arable, catchment=Catchments.arable)
            .build()
        )

    # Rule 41: Arable on steep terrain
    for land_form_val in [LandForm.steeper_hills_and_foothills, LandForm.hills_and_outcrops_of_mountain_ranges]:
        default_engine.add_rule(
            rule(f"arable_steep_{land_form_val.name}")
            .when(land_cover=LandCover.arable, land_form=land_form_val)
            .then(slope=Slope.steeper_hills_and_foothills, impervious=Impervious.arable, catchment=Catchments.arable)
            .build()
        )

    # Rule 42: Urban highly impervious on flats (special case)
    default_engine.add_rule(
        rule("urban_highly_on_flats_special")
        .when(land_cover=LandCover.urban_highly_impervious, land_form=LandForm.flats_and_plateaus)
        .then(slope=Slope.flats_and_plateaus, impervious=Impervious.urban_highly_impervious, catchment=Catchments.mountains)
        .build()
    )

    # Rule 43: Urban highly impervious on gentle terrain
    for land_form_val in [LandForm.hills_with_gentle_slopes, LandForm.steeper_hills_and_foothills, LandForm.hills_and_outcrops_of_mountain_ranges]:
        default_engine.add_rule(
            rule(f"urban_highly_gentle_{land_form_val.name}")
            .when(land_cover=LandCover.urban_highly_impervious, land_form=land_form_val)
            .then(slope=Slope.hills_with_gentle_slopes, impervious=Impervious.urban_highly_impervious, catchment=Catchments.urban)
            .build()
        )

    # Rule 44: Urban highly impervious on high terrain
    for land_form_val in [LandForm.higher_hills, LandForm.mountains, LandForm.highest_mountains]:
        default_engine.add_rule(
            rule(f"urban_highly_high_{land_form_val.name}")
            .when(land_cover=LandCover.urban_highly_impervious, land_form=land_form_val)
            .then(slope=Slope.mountains, impervious=Impervious.urban_highly_impervious, catchment=Catchments.urban)
            .build()
        )

    # Rule 45: Permeable areas on marshes
    for land_cover_val in [LandCover.permeable_areas, LandCover.permeable_terrain_on_plains]:
        default_engine.add_rule(
            rule(f"{land_cover_val.name}_on_marshes")
            .when(land_cover=land_cover_val, land_form=LandForm.marshes_and_lowlands)
            .then(slope=Slope.marshes_and_lowlands, impervious=Impervious.marshes, catchment=Catchments.meadows)
            .build()
        )

    # Rule 46: Permeable areas on flats
    for land_cover_val in [LandCover.permeable_areas, LandCover.permeable_terrain_on_plains]:
        default_engine.add_rule(
            rule(f"{land_cover_val.name}_on_flats")
            .when(land_cover=land_cover_val, land_form=LandForm.flats_and_plateaus)
            .then(slope=Slope.flats_and_plateaus, impervious=Impervious.meadows, catchment=Catchments.meadows)
            .build()
        )

    # Rule 47: Permeable areas on combination hills
    for land_cover_val in [LandCover.permeable_areas, LandCover.permeable_terrain_on_plains]:
        default_engine.add_rule(
            rule(f"{land_cover_val.name}_on_combo_hills")
            .when(land_cover=land_cover_val, land_form=LandForm.flats_and_plateaus_in_combination_with_hills)
            .then(slope=Slope.flats_and_plateaus_in_combination_with_hills, impervious=Impervious.arable, catchment=Catchments.meadows)
            .build()
        )

    # Rule 48: Permeable areas on gentle slopes
    for land_cover_val in [LandCover.permeable_areas, LandCover.permeable_terrain_on_plains]:
        default_engine.add_rule(
            rule(f"{land_cover_val.name}_on_gentle_slopes")
            .when(land_cover=land_cover_val, land_form=LandForm.hills_with_gentle_slopes)
            .then(slope=Slope.hills_with_gentle_slopes, impervious=Impervious.arable, catchment=Catchments.arable)
            .build()
        )

    # Rule 49: Permeable areas on steeper hills
    for land_cover_val in [LandCover.permeable_areas, LandCover.permeable_terrain_on_plains]:
        default_engine.add_rule(
            rule(f"{land_cover_val.name}_on_steeper_hills")
            .when(land_cover=land_cover_val, land_form=LandForm.steeper_hills_and_foothills)
            .then(slope=Slope.steeper_hills_and_foothills, impervious=Impervious.arable, catchment=Catchments.arable)
            .build()
        )

    # Rule 50: Permeable areas on hills and outcrops
    for land_cover_val in [LandCover.permeable_areas, LandCover.permeable_terrain_on_plains]:
        default_engine.add_rule(
            rule(f"{land_cover_val.name}_on_hills_outcrops")
            .when(land_cover=land_cover_val, land_form=LandForm.hills_and_outcrops_of_mountain_ranges)
            .then(slope=Slope.hills_and_outcrops_of_mountain_ranges, impervious=Impervious.arable, catchment=Catchments.arable)
            .build()
        )

    # Rules 51-55: Suburban weakly impervious
    default_engine.add_rule(
        rule("suburban_weak_on_marshes")
        .when(land_cover=LandCover.suburban_weakly_impervious, land_form=LandForm.marshes_and_lowlands)
        .then(slope=Slope.marshes_and_lowlands, impervious=Impervious.suburban_weakly_impervious, catchment=Catchments.suburban)
        .build()
    )

    for land_form_val in [LandForm.flats_and_plateaus, LandForm.flats_and_plateaus_in_combination_with_hills]:
        default_engine.add_rule(
            rule(f"suburban_weak_flat_{land_form_val.name}")
            .when(land_cover=LandCover.suburban_weakly_impervious, land_form=land_form_val)
            .then(slope=Slope.flats_and_plateaus, impervious=Impervious.suburban_weakly_impervious, catchment=Catchments.suburban)
            .build()
        )

    for land_form_val in [LandForm.hills_with_gentle_slopes, LandForm.steeper_hills_and_foothills]:
        default_engine.add_rule(
            rule(f"suburban_weak_hilly_{land_form_val.name}")
            .when(land_cover=LandCover.suburban_weakly_impervious, land_form=land_form_val)
            .then(slope=Slope.hills_with_gentle_slopes, impervious=Impervious.suburban_weakly_impervious, catchment=Catchments.suburban)
            .build()
        )

    default_engine.add_rule(
        rule("suburban_weak_on_outcrops")
        .when(land_cover=LandCover.suburban_weakly_impervious, land_form=LandForm.hills_and_outcrops_of_mountain_ranges)
        .then(slope=Slope.hills_and_outcrops_of_mountain_ranges, impervious=Impervious.suburban_weakly_impervious, catchment=Catchments.suburban)
        .build()
    )

    for land_form_val in [LandForm.higher_hills, LandForm.mountains, LandForm.highest_mountains]:
        default_engine.add_rule(
            rule(f"suburban_weak_high_{land_form_val.name}")
            .when(land_cover=LandCover.suburban_weakly_impervious, land_form=land_form_val)
            .then(slope=Slope.higher_hills, impervious=Impervious.suburban_weakly_impervious, catchment=Catchments.suburban)
            .build()
        )

    # Rules 56-59: Suburban highly impervious
    for land_form_val in [LandForm.marshes_and_lowlands, LandForm.flats_and_plateaus]:
        default_engine.add_rule(
            rule(f"suburban_highly_low_{land_form_val.name}")
            .when(land_cover=LandCover.suburban_highly_impervious, land_form=land_form_val)
            .then(slope=Slope.marshes_and_lowlands, impervious=Impervious.suburban_highly_impervious, catchment=Catchments.suburban)
            .build()
        )

    default_engine.add_rule(
        rule("suburban_highly_on_combo_hills")
        .when(land_cover=LandCover.suburban_highly_impervious, land_form=LandForm.flats_and_plateaus_in_combination_with_hills)
        .then(slope=Slope.flats_and_plateaus_in_combination_with_hills, impervious=Impervious.suburban_highly_impervious, catchment=Catchments.suburban)
        .build()
    )

    for land_form_val in [LandForm.hills_with_gentle_slopes, LandForm.steeper_hills_and_foothills, LandForm.hills_and_outcrops_of_mountain_ranges]:
        default_engine.add_rule(
            rule(f"suburban_highly_hilly_{land_form_val.name}")
            .when(land_cover=LandCover.suburban_highly_impervious, land_form=land_form_val)
            .then(slope=Slope.hills_with_gentle_slopes, impervious=Impervious.suburban_highly_impervious, catchment=Catchments.suburban)
            .build()
        )

    for land_form_val in [LandForm.higher_hills, LandForm.mountains, LandForm.highest_mountains]:
        default_engine.add_rule(
            rule(f"suburban_highly_high_{land_form_val.name}")
            .when(land_cover=LandCover.suburban_highly_impervious, land_form=land_form_val)
            .then(slope=Slope.higher_hills, impervious=Impervious.suburban_highly_impervious, catchment=Catchments.suburban)
            .build()
        )

    # Rule 60: Urban highly impervious on combination hills
    default_engine.add_rule(
        rule("urban_highly_on_combo_hills")
        .when(land_cover=LandCover.urban_highly_impervious, land_form=LandForm.flats_and_plateaus_in_combination_with_hills)
        .then(slope=Slope.flats_and_plateaus_in_combination_with_hills, impervious=Impervious.urban_highly_impervious, catchment=Catchments.urban)
        .build()
    )

    # Build the rule systems for skfuzzy
    default_engine.build_rule_systems()


# Initialize rules when module is imported
if __name__ != "__main__":
    define_all_rules()