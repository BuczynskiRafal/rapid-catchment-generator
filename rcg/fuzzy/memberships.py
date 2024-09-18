"""
The module contains a class with specified fuzzy set membership limits.
"""
import numpy as np
import skfuzzy as fuzz

from skfuzzy import control as ctrl
from .categories import (
    land_form,
    land_cover,
    slope_ctgr,
    impervious_ctgr,
    catchment_ctgr,
)


class Memberships:
    """
    Memberships is a class that defines fuzzy membership functions for land use types,
    land cover types, slope, imperviousness, and catchment.
    """

    def __init__(self) -> None:
        """
        Memberships is a class that defines fuzzy membership functions for land use types,
        land cover types, slope, imperviousness, and catchment.
        """
        self.land_form_type = ctrl.Antecedent(np.arange(0, 10, 1), "land_form")
        self.land_cover_type = ctrl.Antecedent(np.arange(0, 14, 1), "land_cover")
        self.slope = ctrl.Consequent(np.arange(0, 60, 1), "slope")
        self.impervious = ctrl.Consequent(np.arange(0, 101, 1), "impervious")
        self.catchment = ctrl.Consequent(np.arange(1, 101, 1), "catchment")

    def populate_land_use(self):
        """
        Populate land use type with membership functions.
        """
        self.land_form_type[land_form.marshes_and_lowlands] = fuzz.trimf(
            self.land_form_type.universe, [0, 1, 2]
        )
        self.land_form_type[land_form.flats_and_plateaus] = fuzz.trimf(
            self.land_form_type.universe, [1, 2, 3]
        )
        self.land_form_type[
            land_form.flats_and_plateaus_in_combination_with_hills
        ] = fuzz.trimf(self.land_form_type.universe, [2, 3, 4])
        self.land_form_type[land_form.hills_with_gentle_slopes] = fuzz.trimf(
            self.land_form_type.universe, [3, 4, 5]
        )
        self.land_form_type[land_form.steeper_hills_and_foothills] = fuzz.trimf(
            self.land_form_type.universe, [4, 5, 6]
        )
        self.land_form_type[
            land_form.hills_and_outcrops_of_mountain_ranges
        ] = fuzz.trimf(self.land_form_type.universe, [5, 6, 7])
        self.land_form_type[land_form.higher_hills] = fuzz.trimf(
            self.land_form_type.universe, [6, 7, 8]
        )
        self.land_form_type[land_form.mountains] = fuzz.trimf(
            self.land_form_type.universe, [7, 8, 9]
        )
        self.land_form_type[land_form.highest_mountains] = fuzz.trimf(
            self.land_form_type.universe, [8, 9, 10]
        )
    def populate_land_cover(self) -> None:
        """
        Populate land form type with membership functions.
        """
        self.land_cover_type[land_cover.permeable_areas] = fuzz.trimf(
            self.land_cover_type.universe, [0, 1, 2]
        )
        self.land_cover_type[land_cover.permeable_terrain_on_plains] = fuzz.trimf(
            self.land_cover_type.universe, [1, 2, 3]
        )
        self.land_cover_type[land_cover.mountains_vegetated] = fuzz.trimf(
            self.land_cover_type.universe, [2, 3, 4]
        )
        self.land_cover_type[land_cover.mountains_rocky] = fuzz.trimf(
            self.land_cover_type.universe, [3, 4, 5]
        )
        self.land_cover_type[land_cover.urban_weakly_impervious] = fuzz.trimf(
            self.land_cover_type.universe, [4, 5, 6]
        )
        self.land_cover_type[land_cover.urban_moderately_impervious] = fuzz.trimf(
            self.land_cover_type.universe, [5, 6, 7]
        )
        self.land_cover_type[land_cover.urban_highly_impervious] = fuzz.trimf(
            self.land_cover_type.universe, [6, 7, 8]
        )
        self.land_cover_type[land_cover.suburban_weakly_impervious] = fuzz.trimf(
            self.land_cover_type.universe, [7, 8, 9]
        )
        self.land_cover_type[land_cover.suburban_highly_impervious] = fuzz.trimf(
            self.land_cover_type.universe, [8, 9, 10]
        )
        self.land_cover_type[land_cover.rural] = fuzz.trimf(
            self.land_cover_type.universe, [9, 10, 11]
        )
        self.land_cover_type[land_cover.forests] = fuzz.trimf(
            self.land_cover_type.universe, [10, 11, 12]
        )
        self.land_cover_type[land_cover.meadows] = fuzz.trimf(
            self.land_cover_type.universe, [11, 12, 13]
        )
        self.land_cover_type[land_cover.arable] = fuzz.trimf(
            self.land_cover_type.universe, [12, 13, 14]
        )
        self.land_cover_type[land_cover.marshes] = fuzz.trimf(
            self.land_cover_type.universe, [13, 14, 15]
        )


    def populate_slope(self) -> None:
        """Populate slope with membership functions."""
        self.slope[slope_ctgr.marshes_and_lowlands] = fuzz.trimf(
            self.slope.universe, [0, 0, 1]
        )
        self.slope[slope_ctgr.flats_and_plateaus] = fuzz.trimf(
            self.slope.universe, [0, 1, 2.5]
        )
        self.slope[
            slope_ctgr.flats_and_plateaus_in_combination_with_hills
        ] = fuzz.trimf(self.slope.universe, [1, 2.5, 5])
        self.slope[slope_ctgr.hills_with_gentle_slopes] = fuzz.trimf(
            self.slope.universe, [2.5, 5, 8]
        )
        self.slope[slope_ctgr.steeper_hills_and_foothills] = fuzz.trimf(
            self.slope.universe, [5, 8, 15]
        )
        self.slope[slope_ctgr.hills_and_outcrops_of_mountain_ranges] = fuzz.trimf(
            self.slope.universe, [8, 15, 20]
        )
        self.slope[slope_ctgr.higher_hills] = fuzz.trimf(
            self.slope.universe, [15, 20, 30]
        )
        self.slope[slope_ctgr.mountains] = fuzz.trimf(
            self.slope.universe, [20, 30, 40]
        )
        self.slope[slope_ctgr.highest_mountains] = fuzz.trimf(
            self.slope.universe, [30, 50, 60]
        )


    def populate_impervious(self) -> None:
        """Populate impervious with membership functions."""
        self.impervious[impervious_ctgr.marshes] = fuzz.trimf(
            self.impervious.universe, [0, 0, 2]
        )
        self.impervious[impervious_ctgr.arable] = fuzz.trimf(
            self.impervious.universe, [0, 2, 4]
        )
        self.impervious[impervious_ctgr.meadows] = fuzz.trimf(
            self.impervious.universe, [2, 5, 8]
        )
        self.impervious[impervious_ctgr.forests] = fuzz.trimf(
            self.impervious.universe, [5, 7, 9]
        )
        self.impervious[impervious_ctgr.rural] = fuzz.trimf(
            self.impervious.universe, [7, 11, 15]
        )
        self.impervious[impervious_ctgr.suburban_weakly_impervious] = fuzz.trimf(
            self.impervious.universe, [10, 25, 40]
        )
        self.impervious[impervious_ctgr.suburban_highly_impervious] = fuzz.trimf(
            self.impervious.universe, [35, 50, 65]
        )
        self.impervious[impervious_ctgr.urban_weakly_impervious] = fuzz.trimf(
            self.impervious.universe, [30, 45, 60]
        )
        self.impervious[impervious_ctgr.urban_moderately_impervious] = fuzz.trimf(
            self.impervious.universe, [50, 65, 80]
        )
        self.impervious[impervious_ctgr.urban_highly_impervious] = fuzz.trimf(
            self.impervious.universe, [75, 85, 100]
        )
        self.impervious[impervious_ctgr.mountains_rocky] = fuzz.trimf(
            self.impervious.universe, [20, 40, 60]
        )
        self.impervious[impervious_ctgr.mountains_vegetated] = fuzz.trimf(
            self.impervious.universe, [5, 15, 25]
        )


    def populate_catchment(self) -> None:
        """Populate catchment with membership functions."""
        self.catchment[catchment_ctgr.urban] = fuzz.trimf(
            self.catchment.universe, [0, 0, 15]
        )
        self.catchment[catchment_ctgr.suburban] = fuzz.trimf(
            self.catchment.universe, [0, 15, 30]
        )
        self.catchment[catchment_ctgr.rural] = fuzz.trimf(
            self.catchment.universe, [15, 30, 45]
        )
        self.catchment[catchment_ctgr.forests] = fuzz.trimf(
            self.catchment.universe, [30, 45, 60]
        )
        self.catchment[catchment_ctgr.meadows] = fuzz.trimf(
            self.catchment.universe, [45, 60, 75]
        )
        self.catchment[catchment_ctgr.arable] = fuzz.trimf(
            self.catchment.universe, [60, 75, 90]
        )
        self.catchment[catchment_ctgr.mountains] = fuzz.trimf(
            self.catchment.universe, [75, 87, 100]
        )


membership = Memberships()
membership.populate_land_use()
membership.populate_land_cover()
membership.populate_slope()
membership.populate_impervious()
membership.populate_catchment()
