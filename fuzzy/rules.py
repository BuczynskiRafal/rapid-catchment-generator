from fuzzy import categories

from skfuzzy import control as ctrl

from fuzzy.memberships import membership


class RulesSet:
    def __init__(self):
        self.rule1 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.medium_conditions]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.permeable_areas]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[
                        categories.land_form.permeable_terrain_on_plains
                    ]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.rural]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.marshes]
                )
            ),
        )
        self.rule2 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.medium_conditions]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.permeable_areas]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.rural]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[
                        categories.land_form.permeable_terrain_on_plains
                    ]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.marshes]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.urban]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.urban]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.suburban]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.suburban]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.suburban]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.urban]
                )
            ),
        )

        self.rule3 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.medium_conditions]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.permeable_areas]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.rural]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[
                        categories.land_form.permeable_terrain_on_plains
                    ]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.marshes]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.marshes]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.marshes]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.marshes]
                )
            ),
        )

        self.rule4 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.medium_conditions]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.permeable_areas]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[
                        categories.land_form.permeable_terrain_on_plains
                    ]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.rural]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.rural]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.urban]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.marshes]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.suburban]
                )
            ),
        )

        self.rule5 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.medium_conditions]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.permeable_areas]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[
                        categories.land_form.permeable_terrain_on_plains
                    ]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.bare_rocky_slopes]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.rural]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.urban]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.steeper_hills_and_foothills
                    ]
                    & membership.land_form_type[categories.land_form.suburban]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.marshes]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.marshes]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[
                        categories.land_form.permeable_terrain_on_plains
                    ]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.permeable_areas]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.medium_conditions]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.medium_conditions]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.permeable_areas]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.urban]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.suburban]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.rural]
                )
            ),
        )

        self.rule6 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.bare_rocky_slopes]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.medium_conditions]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[
                        categories.land_form.permeable_terrain_on_plains
                    ]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.permeable_areas]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.urban]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.suburban]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.rural]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.urban]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.suburban]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.rural]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_and_outcrops_of_mountain_ranges
                    ]
                    & membership.land_form_type[categories.land_form.mountains]
                )
            ),
        )

        self.rule7 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.bare_rocky_slopes]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.urban]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.suburban]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.rural]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_use_type[categories.land_use.marshes_and_lowlands]
                    & membership.land_form_type[categories.land_form.bare_rocky_slopes]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.flats_and_plateaus_in_combination_with_hills
                    ]
                    & membership.land_form_type[categories.land_form.bare_rocky_slopes]
                )
                | (
                    membership.land_use_type[
                        categories.land_use.hills_with_gentle_slopes
                    ]
                    & membership.land_form_type[categories.land_form.bare_rocky_slopes]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[categories.land_use.higher_hills]
                    & membership.land_form_type[categories.land_form.marshes]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[
                        categories.land_form.permeable_terrain_on_plains
                    ]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.forests]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.meadows]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.arable]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.marshes]
                )
                | (
                    membership.land_use_type[categories.land_use.flats_and_plateaus]
                    & membership.land_form_type[categories.land_form.bare_rocky_slopes]
                )
            ),
        )

        self.rule8 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.bare_rocky_slopes]
                )
                | (
                    membership.land_use_type[categories.land_use.mountains]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.permeable_areas]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[
                        categories.land_form.permeable_terrain_on_plains
                    ]
                )
            ),
        )

        self.rule9 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.hilly]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.bare_rocky_slopes]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.medium_conditions]
                )
                | (
                    membership.land_use_type[categories.land_use.highest_mountains]
                    & membership.land_form_type[categories.land_form.mountains]
                )
            ),
        )


class SlopeRule(RulesSet):
    def __init__(self):
        super().__init__()
        self.rule1.consequent = membership.slope[
            categories.slope_ctgr.marshes_and_lowlands
        ]
        self.rule2.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus
        ]
        self.rule3.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills
        ]
        self.rule4.consequent = membership.slope[
            categories.slope_ctgr.hills_with_gentle_slopes
        ]
        self.rule5.consequent = membership.slope[
            categories.slope_ctgr.steeper_hills_and_foothills
        ]
        self.rule6.consequent = membership.slope[
            categories.slope_ctgr.hills_and_outcrops_of_mountain_ranges
        ]
        self.rule7.consequent = membership.slope[categories.slope_ctgr.higher_hills]
        self.rule8.consequent = membership.slope[categories.slope_ctgr.mountains]
        self.rule9.consequent = membership.slope[
            categories.slope_ctgr.highest_mountains
        ]


class ImperviousRule(RulesSet):
    def __init__(self):
        super().__init__()
        self.rule1.consequent = membership.impervious[
            categories.impervious_ctgr.marshes
        ]
        self.rule2.consequent = membership.impervious[categories.impervious_ctgr.arable]
        self.rule3.consequent = membership.impervious[
            categories.impervious_ctgr.meadows
        ]
        self.rule4.consequent = membership.impervious[
            categories.impervious_ctgr.forests
        ]
        self.rule5.consequent = membership.impervious[categories.impervious_ctgr.rural]
        self.rule6.consequent = membership.impervious[
            categories.impervious_ctgr.suburban
        ]
        self.rule7.consequent = membership.impervious[categories.impervious_ctgr.urban]
        self.rule8.consequent = membership.impervious[categories.impervious_ctgr.hilly]
        self.rule9.consequent = membership.impervious[
            categories.impervious_ctgr.mountains
        ]


class CatchmentsRule(RulesSet):
    def __init__(self):
        super().__init__()
        self.rule1.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule2.consequent = membership.catchment[categories.catchment_ctgr.arable]
        self.rule3.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule4.consequent = membership.catchment[categories.catchment_ctgr.forests]
        self.rule5.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule6.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule7.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule8.consequent = membership.catchment[
            categories.catchment_ctgr.mountains
        ]
        self.rule9.consequent = membership.catchment[
            categories.catchment_ctgr.mountains
        ]


slope_rules = [rule for rule in vars(SlopeRule()).values()]
impervious_rules = [rule for rule in vars(ImperviousRule()).values()]
catchment_rules = [rule for rule in vars(CatchmentsRule()).values()]
