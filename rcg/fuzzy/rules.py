"""
The module contains a class with specific rules for class members and the consequences of their combinations. 
"""
from skfuzzy import control as ctrl
from . import categories
from .memberships import membership


class RulesSet:
    """
    RulesSet is a class representing a set of rules for all antecedent combinations.
    """

    def __init__(self) -> None:
        """Initialize a RulesSet object with predefined rules as string attributes."""
        self.rule1 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
                | (
                    membership.land_cover_type[categories.land_cover.mountains_rocky]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
            )
        )
        self.rule2 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.marshes]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.marshes]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.permeable_areas]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.permeable_areas]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.permeable_areas]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[
                        categories.land_cover.permeable_terrain_on_plains
                    ]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[
                        categories.land_cover.permeable_terrain_on_plains
                    ]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[
                        categories.land_cover.permeable_terrain_on_plains
                    ]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.forests]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.forests]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.forests]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.meadows]
                    & membership.land_form_type[
                        categories.land_form.hills_and_outcrops_of_mountain_ranges
                    ]
                )
                | (
                    membership.land_cover_type[categories.land_cover.meadows]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.meadows]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.meadows]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.arable]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.arable]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.arable]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.marshes]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
            )
        )

        self.rule3 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
                | (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus_in_combination_with_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.hills_and_outcrops_of_mountain_ranges]
                )
                | (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.hills_with_gentle_slopes]
                )
                | (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.steeper_hills_and_foothills]
                )
            )
        )
        self.rule4 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.hills_and_outcrops_of_mountain_ranges]
                )
            )
        )
        self.rule6 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.mountains_vegetated]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
            )
        )
        self.rule7 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_rocky]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
            )
        )
        self.rule8 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_rocky]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus_in_combination_with_hills]
                )
            )
        )
        self.rule9 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_rocky]
                    & membership.land_form_type[categories.land_form.hills_with_gentle_slopes]
                )
            )
        )
        self.rule10 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_rocky]
                    & membership.land_form_type[categories.land_form.steeper_hills_and_foothills]
                )
            )
        )
        self.rule11 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_rocky]
                    & membership.land_form_type[categories.land_form.hills_and_outcrops_of_mountain_ranges]
                )
            )
        )
        self.rule12 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_rocky]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
            )
        )
        self.rule13 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.mountains_rocky]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.mountains_rocky]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
            )
        )
        self.rule14 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
            )
        )
        self.rule15 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus_in_combination_with_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.hills_with_gentle_slopes]
                )
            )
        )
        self.rule16 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.steeper_hills_and_foothills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.hills_and_outcrops_of_mountain_ranges]
                )
            )
        )
        self.rule17 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
            )
        )
        self.rule18 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_moderately_impervious]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_moderately_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
            )
        )
        self.rule19 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_moderately_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus_in_combination_with_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_moderately_impervious]
                    & membership.land_form_type[categories.land_form.hills_with_gentle_slopes]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_moderately_impervious]
                    & membership.land_form_type[categories.land_form.steeper_hills_and_foothills]
                )
            )
        )
        self.rule20 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_moderately_impervious]
                    & membership.land_form_type[categories.land_form.hills_and_outcrops_of_mountain_ranges]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_moderately_impervious]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_moderately_impervious]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_moderately_impervious]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
            )
        )
        self.rule21 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
            )
        )
        self.rule22 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.rural]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
            )
        )
        self.rule23 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.rural]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
            )
        )
        self.rule24 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.rural]
                    & membership.land_form_type[
                        categories.land_form.flats_and_plateaus_in_combination_with_hills
                    ]
                )
            )
        )
        self.rule25 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.rural]
                    & membership.land_form_type[
                        categories.land_form.hills_with_gentle_slopes
                    ]
                )
            )
        )
        self.rule26 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.rural]
                    & membership.land_form_type[
                        categories.land_form.steeper_hills_and_foothills
                    ]
                )
            )
        )
        self.rule27 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.rural]
                    & membership.land_form_type[
                        categories.land_form.hills_and_outcrops_of_mountain_ranges
                    ]
                )
            )
        )
        self.rule28 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.rural]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
            )
        )
        self.rule29 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.rural]
                    & membership.land_form_type[categories.land_form.mountains]
                )
            )
        )
        self.rule30 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.rural]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
            )
        )
        self.rule31 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.forests]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
                | (
                    membership.land_cover_type[categories.land_cover.forests]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
            )
        )
        self.rule32 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.forests]
                    & membership.land_form_type[
                        categories.land_form.flats_and_plateaus_in_combination_with_hills
                    ]
                )
                | (
                    membership.land_cover_type[categories.land_cover.forests]
                    & membership.land_form_type[
                        categories.land_form.hills_with_gentle_slopes
                    ]
                )
            )
        )
        self.rule33 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.forests]
                    & membership.land_form_type[
                        categories.land_form.steeper_hills_and_foothills
                    ]
                )
                | (
                    membership.land_cover_type[categories.land_cover.forests]
                    & membership.land_form_type[
                        categories.land_form.hills_and_outcrops_of_mountain_ranges
                    ]
                )
            )
        )
        self.rule34 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.marshes]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
                | (
                    membership.land_cover_type[categories.land_cover.marshes]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
                | (
                    membership.land_cover_type[categories.land_cover.marshes]
                    & membership.land_form_type[
                        categories.land_form.flats_and_plateaus_in_combination_with_hills
                    ]
                )
            )
        )
        self.rule35 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.marshes]
                    & membership.land_form_type[
                        categories.land_form.hills_with_gentle_slopes
                    ]
                )
                | (
                    membership.land_cover_type[categories.land_cover.marshes]
                    & membership.land_form_type[
                        categories.land_form.steeper_hills_and_foothills
                    ]
                )
                | (
                    membership.land_cover_type[categories.land_cover.marshes]
                    & membership.land_form_type[
                        categories.land_form.hills_and_outcrops_of_mountain_ranges
                    ]
                )
            )
        )
        self.rule36 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.meadows]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
            )
        )
        self.rule37 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.meadows]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
                | (
                    membership.land_cover_type[categories.land_cover.meadows]
                    & membership.land_form_type[
                        categories.land_form.flats_and_plateaus_in_combination_with_hills
                    ]
                )
            )
        )
        self.rule38 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.meadows]
                    & membership.land_form_type[
                        categories.land_form.hills_with_gentle_slopes
                    ]
                )
                | (
                    membership.land_cover_type[categories.land_cover.meadows]
                    & membership.land_form_type[
                        categories.land_form.steeper_hills_and_foothills
                    ]
                )
            )
        )
        self.rule39 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.arable]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
            )
        )
        self.rule40 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.arable]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
                | (
                    membership.land_cover_type[categories.land_cover.arable]
                    & membership.land_form_type[
                        categories.land_form.flats_and_plateaus_in_combination_with_hills
                    ]
                )
                | (
                    membership.land_cover_type[categories.land_cover.arable]
                    & membership.land_form_type[
                        categories.land_form.hills_with_gentle_slopes
                    ]
                )
            )
        )
        self.rule41 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.arable]
                    & membership.land_form_type[
                        categories.land_form.steeper_hills_and_foothills
                    ]
                )
                | (
                    membership.land_cover_type[categories.land_cover.arable]
                    & membership.land_form_type[
                        categories.land_form.hills_and_outcrops_of_mountain_ranges
                    ]
                )
            )
        )
        self.rule42 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
            )
        )
        self.rule43 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.hills_with_gentle_slopes]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.steeper_hills_and_foothills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.hills_with_gentle_slopes]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.hills_and_outcrops_of_mountain_ranges]
                )
            )
        )
        self.rule44 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
            )
        )

        self.rule45 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.permeable_areas]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
                | (
                    membership.land_cover_type[
                        categories.land_cover.permeable_terrain_on_plains
                    ]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
            )
        )
        self.rule46 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.permeable_areas]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
                | (
                    membership.land_cover_type[
                        categories.land_cover.permeable_terrain_on_plains
                    ]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
            )
        )
        self.rule47 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.permeable_areas]
                    & membership.land_form_type[
                        categories.land_form.flats_and_plateaus_in_combination_with_hills
                    ]
                )
                | (
                    membership.land_cover_type[
                        categories.land_cover.permeable_terrain_on_plains
                    ]
                    & membership.land_form_type[
                        categories.land_form.flats_and_plateaus_in_combination_with_hills
                    ]
                )
            )
        )
        self.rule48 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.permeable_areas]
                    & membership.land_form_type[
                        categories.land_form.hills_with_gentle_slopes
                    ]
                )
                | (
                    membership.land_cover_type[
                        categories.land_cover.permeable_terrain_on_plains
                    ]
                    & membership.land_form_type[
                        categories.land_form.hills_with_gentle_slopes
                    ]
                )
            )
        )
        self.rule49 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.permeable_areas]
                    & membership.land_form_type[
                        categories.land_form.steeper_hills_and_foothills
                    ]
                )
                | (
                    membership.land_cover_type[
                        categories.land_cover.permeable_terrain_on_plains
                    ]
                    & membership.land_form_type[
                        categories.land_form.steeper_hills_and_foothills
                    ]
                )
            )
        )
        self.rule50 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.permeable_areas]
                    & membership.land_form_type[
                        categories.land_form.hills_and_outcrops_of_mountain_ranges
                    ]
                )
                | (
                    membership.land_cover_type[
                        categories.land_cover.permeable_terrain_on_plains
                    ]
                    & membership.land_form_type[
                        categories.land_form.hills_and_outcrops_of_mountain_ranges
                    ]
                )
            )
        )
        self.rule51 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.suburban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
            )
        )
        self.rule52 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.suburban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
                | (
                    membership.land_cover_type[categories.land_cover.suburban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus_in_combination_with_hills]
                )
            )
        )
        self.rule53 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.suburban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.hills_with_gentle_slopes]
                )
                | (
                    membership.land_cover_type[categories.land_cover.suburban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.steeper_hills_and_foothills]
                )
            )
        )
        self.rule54 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.suburban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.hills_and_outcrops_of_mountain_ranges]
                )
            )
        )
        self.rule55 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.suburban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.suburban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.suburban_weakly_impervious]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
            )
        )
        self.rule56 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.suburban_highly_impervious]
                    & membership.land_form_type[categories.land_form.marshes_and_lowlands]
                )
                | (
                    membership.land_cover_type[categories.land_cover.suburban_highly_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus]
                )
            )
        )
        self.rule57 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.suburban_highly_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus_in_combination_with_hills]
                )
            )
        )
        self.rule58 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.suburban_highly_impervious]
                    & membership.land_form_type[categories.land_form.hills_with_gentle_slopes]
                )
                | (
                    membership.land_cover_type[categories.land_cover.suburban_highly_impervious]
                    & membership.land_form_type[categories.land_form.steeper_hills_and_foothills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.suburban_highly_impervious]
                    & membership.land_form_type[categories.land_form.hills_and_outcrops_of_mountain_ranges]
                )
            )
        )
        self.rule59 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.suburban_highly_impervious]
                    & membership.land_form_type[categories.land_form.higher_hills]
                )
                | (
                    membership.land_cover_type[categories.land_cover.suburban_highly_impervious]
                    & membership.land_form_type[categories.land_form.mountains]
                )
                | (
                    membership.land_cover_type[categories.land_cover.suburban_highly_impervious]
                    & membership.land_form_type[categories.land_form.highest_mountains]
                )
            )
        )
        self.rule60 = ctrl.Rule(
            antecedent=(
                (
                    membership.land_cover_type[categories.land_cover.urban_highly_impervious]
                    & membership.land_form_type[categories.land_form.flats_and_plateaus_in_combination_with_hills]
                )

            )
        )


class SlopeRule(RulesSet):
    """
    SlopeRule is a class representing a set of consequences for all slope combinations.
    """
    def __init__(self):
        super().__init__()
        self.rule1.consequent = membership.slope[categories.slope_ctgr.flats_and_plateaus]
        self.rule2.consequent = membership.slope[categories.slope_ctgr.steeper_hills_and_foothills]
        self.rule3.consequent = membership.slope[categories.slope_ctgr.steeper_hills_and_foothills]
        self.rule4.consequent = membership.slope[categories.slope_ctgr.hills_and_outcrops_of_mountain_ranges]
        self.rule6.consequent = membership.slope[categories.slope_ctgr.higher_hills]
        self.rule7.consequent = membership.slope[categories.slope_ctgr.flats_and_plateaus]
        self.rule8.consequent = membership.slope[categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills]
        self.rule9.consequent = membership.slope[categories.slope_ctgr.hills_with_gentle_slopes]
        self.rule10.consequent = membership.slope[categories.slope_ctgr.steeper_hills_and_foothills]
        self.rule11.consequent = membership.slope[categories.slope_ctgr.hills_and_outcrops_of_mountain_ranges]
        self.rule12.consequent = membership.slope[categories.slope_ctgr.higher_hills]
        self.rule13.consequent = membership.slope[categories.slope_ctgr.mountains]
        self.rule14.consequent = membership.slope[categories.slope_ctgr.marshes_and_lowlands]
        self.rule15.consequent = membership.slope[categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills]
        self.rule16.consequent = membership.slope[categories.slope_ctgr.steeper_hills_and_foothills]
        self.rule17.consequent = membership.slope[categories.slope_ctgr.higher_hills]
        self.rule18.consequent = membership.slope[categories.slope_ctgr.marshes_and_lowlands]
        self.rule19.consequent = membership.slope[categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills]
        self.rule20.consequent = membership.slope[categories.slope_ctgr.hills_and_outcrops_of_mountain_ranges]
        self.rule21.consequent = membership.slope[categories.slope_ctgr.marshes_and_lowlands]
        self.rule22.consequent = membership.slope[categories.slope_ctgr.marshes_and_lowlands]
        self.rule23.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus
        ]
        self.rule24.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills
        ]
        self.rule25.consequent = membership.slope[
            categories.slope_ctgr.hills_with_gentle_slopes
        ]
        self.rule26.consequent = membership.slope[
            categories.slope_ctgr.steeper_hills_and_foothills
        ]
        self.rule27.consequent = membership.slope[
            categories.slope_ctgr.hills_and_outcrops_of_mountain_ranges
        ]
        self.rule28.consequent = membership.slope[categories.slope_ctgr.higher_hills]
        self.rule29.consequent = membership.slope[categories.slope_ctgr.mountains]
        self.rule30.consequent = membership.slope[categories.slope_ctgr.highest_mountains]
        self.rule31.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus
        ]
        self.rule32.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills
        ]
        self.rule33.consequent = membership.slope[
            categories.slope_ctgr.hills_and_outcrops_of_mountain_ranges
        ]
        self.rule34.consequent = membership.slope[
            categories.slope_ctgr.marshes_and_lowlands
        ]
        self.rule35.consequent = membership.slope[
            categories.slope_ctgr.marshes_and_lowlands
        ]
        self.rule36.consequent = membership.slope[
            categories.slope_ctgr.marshes_and_lowlands
        ]
        self.rule37.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus
        ]
        self.rule38.consequent = membership.slope[
            categories.slope_ctgr.hills_with_gentle_slopes
        ]
        self.rule39.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus
        ]
        self.rule40.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills
        ]
        self.rule41.consequent = membership.slope[
            categories.slope_ctgr.steeper_hills_and_foothills
        ]
        self.rule42.consequent = membership.slope[categories.slope_ctgr.flats_and_plateaus]
        self.rule43.consequent = membership.slope[categories.slope_ctgr.hills_with_gentle_slopes]
        self.rule44.consequent = membership.slope[categories.slope_ctgr.mountains]
        self.rule45.consequent = membership.slope[
            categories.slope_ctgr.marshes_and_lowlands
        ]
        self.rule46.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus
        ]
        self.rule47.consequent = membership.slope[
            categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills
        ]
        self.rule48.consequent = membership.slope[
            categories.slope_ctgr.hills_with_gentle_slopes
        ]
        self.rule49.consequent = membership.slope[
            categories.slope_ctgr.steeper_hills_and_foothills
        ]
        self.rule50.consequent = membership.slope[
            categories.slope_ctgr.hills_and_outcrops_of_mountain_ranges
        ]
        self.rule51.consequent = membership.slope[categories.slope_ctgr.marshes_and_lowlands]
        self.rule52.consequent = membership.slope[categories.slope_ctgr.flats_and_plateaus]
        self.rule53.consequent = membership.slope[categories.slope_ctgr.hills_with_gentle_slopes]
        self.rule54.consequent = membership.slope[categories.slope_ctgr.hills_and_outcrops_of_mountain_ranges]
        self.rule55.consequent = membership.slope[categories.slope_ctgr.higher_hills]
        self.rule56.consequent = membership.slope[categories.slope_ctgr.marshes_and_lowlands]
        self.rule57.consequent = membership.slope[categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills]
        self.rule58.consequent = membership.slope[categories.slope_ctgr.hills_with_gentle_slopes]
        self.rule59.consequent = membership.slope[categories.slope_ctgr.higher_hills]
        self.rule60.consequent = membership.slope[categories.slope_ctgr.flats_and_plateaus_in_combination_with_hills]


class ImperviousRule(RulesSet):
    """
    ImperviousRule is a class representing a set of consequences for all slope combinations.
    """
    def __init__(self):
        super().__init__()
        self.rule1.consequent = membership.impervious[categories.impervious_ctgr.mountains_vegetated]
        self.rule2.consequent = membership.impervious[categories.impervious_ctgr.mountains_vegetated]
        self.rule3.consequent = membership.impervious[categories.impervious_ctgr.mountains_vegetated]
        self.rule4.consequent = membership.impervious[categories.impervious_ctgr.mountains_vegetated]
        self.rule6.consequent = membership.impervious[categories.impervious_ctgr.mountains_rocky]
        self.rule7.consequent = membership.impervious[categories.impervious_ctgr.mountains_rocky]
        self.rule8.consequent = membership.impervious[categories.impervious_ctgr.mountains_rocky]
        self.rule9.consequent = membership.impervious[categories.impervious_ctgr.mountains_rocky]
        self.rule10.consequent = membership.impervious[categories.impervious_ctgr.mountains_rocky]
        self.rule11.consequent = membership.impervious[categories.impervious_ctgr.mountains_rocky]
        self.rule12.consequent = membership.impervious[categories.impervious_ctgr.mountains_rocky]
        self.rule13.consequent = membership.impervious[categories.impervious_ctgr.mountains_rocky]
        self.rule14.consequent = membership.impervious[categories.impervious_ctgr.urban_weakly_impervious]
        self.rule15.consequent = membership.impervious[categories.impervious_ctgr.urban_weakly_impervious]
        self.rule16.consequent = membership.impervious[categories.impervious_ctgr.urban_highly_impervious]
        self.rule17.consequent = membership.impervious[categories.impervious_ctgr.urban_moderately_impervious]
        self.rule18.consequent = membership.impervious[categories.impervious_ctgr.urban_moderately_impervious]
        self.rule19.consequent = membership.impervious[categories.impervious_ctgr.urban_moderately_impervious]
        self.rule20.consequent = membership.impervious[categories.impervious_ctgr.urban_moderately_impervious]
        self.rule21.consequent = membership.impervious[categories.impervious_ctgr.urban_highly_impervious]
        self.rule22.consequent = membership.impervious[categories.impervious_ctgr.rural]
        self.rule23.consequent = membership.impervious[
            categories.impervious_ctgr.rural
        ]
        self.rule24.consequent = membership.impervious[categories.impervious_ctgr.rural]
        self.rule25.consequent = membership.impervious[categories.impervious_ctgr.rural]
        self.rule26.consequent = membership.impervious[ categories.impervious_ctgr.rural ]
        self.rule27.consequent = membership.impervious[
            categories.impervious_ctgr.rural
        ]
        self.rule28.consequent = membership.impervious[
            categories.impervious_ctgr.rural
        ]
        self.rule29.consequent = membership.impervious[
            categories.impervious_ctgr.rural
        ]
        self.rule30.consequent = membership.impervious[
            categories.impervious_ctgr.rural
        ]
        self.rule31.consequent = membership.impervious[
            categories.impervious_ctgr.forests
        ]
        self.rule32.consequent = membership.impervious[
            categories.impervious_ctgr.forests
        ]
        self.rule33.consequent = membership.impervious[
            categories.impervious_ctgr.forests
        ]
        self.rule34.consequent = membership.impervious[
            categories.impervious_ctgr.marshes
        ]
        self.rule35.consequent = membership.impervious[
            categories.impervious_ctgr.meadows
        ]
        self.rule36.consequent = membership.impervious[
            categories.impervious_ctgr.meadows
        ]
        self.rule37.consequent = membership.impervious[
            categories.impervious_ctgr.meadows
        ]
        self.rule38.consequent = membership.impervious[
            categories.impervious_ctgr.meadows
        ]
        self.rule39.consequent = membership.impervious[
            categories.impervious_ctgr.meadows
        ]
        self.rule40.consequent = membership.impervious[
            categories.impervious_ctgr.arable
        ]
        self.rule41.consequent = membership.impervious[
            categories.impervious_ctgr.arable
        ]
        self.rule42.consequent = membership.impervious[categories.impervious_ctgr.urban_highly_impervious]
        self.rule43.consequent = membership.impervious[categories.impervious_ctgr.urban_highly_impervious]
        self.rule44.consequent = membership.impervious[categories.impervious_ctgr.urban_highly_impervious]
        self.rule45.consequent = membership.impervious[
            categories.impervious_ctgr.marshes
        ]
        self.rule46.consequent = membership.impervious[
            categories.impervious_ctgr.meadows
        ]
        self.rule47.consequent = membership.impervious[
            categories.impervious_ctgr.arable
        ]
        self.rule48.consequent = membership.impervious[
            categories.impervious_ctgr.arable
        ]
        self.rule49.consequent = membership.impervious[
            categories.impervious_ctgr.arable
        ]
        self.rule50.consequent = membership.impervious[
            categories.impervious_ctgr.arable
        ]
        self.rule51.consequent = membership.impervious[categories.impervious_ctgr.suburban_weakly_impervious]
        self.rule52.consequent = membership.impervious[categories.impervious_ctgr.suburban_weakly_impervious]
        self.rule53.consequent = membership.impervious[categories.impervious_ctgr.suburban_weakly_impervious]
        self.rule54.consequent = membership.impervious[categories.impervious_ctgr.suburban_weakly_impervious]
        self.rule55.consequent = membership.impervious[categories.impervious_ctgr.suburban_weakly_impervious]
        self.rule56.consequent = membership.impervious[categories.impervious_ctgr.suburban_highly_impervious]
        self.rule57.consequent = membership.impervious[categories.impervious_ctgr.suburban_highly_impervious]
        self.rule58.consequent = membership.impervious[categories.impervious_ctgr.suburban_highly_impervious]
        self.rule59.consequent = membership.impervious[categories.impervious_ctgr.suburban_highly_impervious]
        self.rule60.consequent = membership.impervious[categories.impervious_ctgr.urban_highly_impervious]

class CatchmentsRule(RulesSet):
    """
    CatchmentsRule is a class representing a set of consequences for all slope combinations.
    """
    def __init__(self):
        super().__init__()
        self.rule1.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule2.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule3.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule4.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule6.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule7.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule8.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule9.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule10.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule11.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule12.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule13.consequent = membership.catchment[categories.catchment_ctgr.mountains]
        self.rule14.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule15.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule16.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule17.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule18.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule19.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule20.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule21.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule22.consequent = membership.catchment[categories.catchment_ctgr.rural]

        self.rule23.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule24.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule25.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule26.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule27.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule28.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule29.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule30.consequent = membership.catchment[categories.catchment_ctgr.rural]
        self.rule31.consequent = membership.catchment[categories.catchment_ctgr.forests]
        self.rule32.consequent = membership.catchment[categories.catchment_ctgr.forests]
        self.rule33.consequent = membership.catchment[categories.catchment_ctgr.forests]
        self.rule34.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule35.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule36.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule37.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule38.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule39.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule40.consequent = membership.catchment[categories.catchment_ctgr.arable]
        self.rule41.consequent = membership.catchment[categories.catchment_ctgr.arable]
        self.rule42.consequent = membership.catchment[
            categories.catchment_ctgr.mountains
        ]
        self.rule43.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule44.consequent = membership.catchment[categories.catchment_ctgr.urban]
        self.rule45.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule46.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule47.consequent = membership.catchment[categories.catchment_ctgr.meadows]
        self.rule48.consequent = membership.catchment[categories.catchment_ctgr.arable]
        self.rule49.consequent = membership.catchment[categories.catchment_ctgr.arable]
        self.rule50.consequent = membership.catchment[categories.catchment_ctgr.arable]
        self.rule51.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule52.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule53.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule54.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule55.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule56.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule57.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule58.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule59.consequent = membership.catchment[categories.catchment_ctgr.suburban]
        self.rule60.consequent = membership.catchment[categories.catchment_ctgr.urban]


slope_rules = [rule for rule in vars(SlopeRule()).values()]
impervious_rules = [rule for rule in vars(ImperviousRule()).values()]
catchment_rules = [rule for rule in vars(CatchmentsRule()).values()]
