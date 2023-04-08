import numpy as np
import skfuzzy as fuzz

from skfuzzy import control as ctrl
from fuzzy.categories import (
    land_form,
    land_cover,
    slope_ctgr,
    impervious_ctgr,
    catchment_ctgr,
)


class Memberships:
    def __init__(self):
        """Ready for use members."""
        self.land_form_type = ctrl.Antecedent(np.arange(0, 10, 1), "land_form")
        self.land_cover_type = ctrl.Antecedent(np.arange(0, 14, 1), "land_cover")
        self.slope = ctrl.Consequent(np.arange(1, 101, 1), "slope")
        self.impervious = ctrl.Consequent(np.arange(1, 101, 1), "impervious")
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
        self.land_form_type[land_form.hills_and_outcrops_of_mountain_ranges] = fuzz.trimf(
            self.land_form_type.universe, [5, 6, 7]
        )
        self.land_form_type[land_form.higher_hills] = fuzz.trimf(
            self.land_form_type.universe, [6, 7, 8]
        )
        self.land_form_type[land_form.mountains] = fuzz.trimf(
            self.land_form_type.universe, [7, 8, 9]
        )
        self.land_form_type[land_form.highest_mountains] = fuzz.trimf(
            self.land_form_type.universe, [8, 9, 10]
        )

    def populate_land_form(self):
        """
        Populate land form type with membership functions.
        """
        self.land_cover_type[land_cover.medium_conditions] = fuzz.trimf(
            self.land_cover_type.universe, [0, 1, 2]
        )
        self.land_cover_type[land_cover.permeable_areas] = fuzz.trimf(
            self.land_cover_type.universe, [1, 2, 3]
        )
        self.land_cover_type[land_cover.permeable_terrain_on_plains] = fuzz.trimf(
            self.land_cover_type.universe, [2, 3, 4]
        )
        self.land_cover_type[land_cover.hilly] = fuzz.trimf(
            self.land_cover_type.universe, [3, 4, 5]
        )
        self.land_cover_type[land_cover.mountains] = fuzz.trimf(
            self.land_cover_type.universe, [4, 5, 6]
        )
        self.land_cover_type[land_cover.bare_rocky_slopes] = fuzz.trimf(
            self.land_cover_type.universe, [5, 6, 7]
        )
        self.land_cover_type[land_cover.urban] = fuzz.trimf(
            self.land_cover_type.universe, [6, 7, 8]
        )
        self.land_cover_type[land_cover.suburban] = fuzz.trimf(
            self.land_cover_type.universe, [7, 8, 9]
        )
        self.land_cover_type[land_cover.rural] = fuzz.trimf(
            self.land_cover_type.universe, [8, 9, 10]
        )
        self.land_cover_type[land_cover.forests] = fuzz.trimf(
            self.land_cover_type.universe, [9, 10, 11]
        )
        self.land_cover_type[land_cover.meadows] = fuzz.trimf(
            self.land_cover_type.universe, [10, 11, 12]
        )
        self.land_cover_type[land_cover.arable] = fuzz.trimf(
            self.land_cover_type.universe, [11, 12, 13]
        )
        self.land_cover_type[land_cover.marshes] = fuzz.trimf(
            self.land_cover_type.universe, [12, 13, 14]
        )

    def populate_slope(self):
        """Populate slope with membership functions."""
        self.slope[slope_ctgr.marshes_and_lowlands] = fuzz.trimf(
            self.slope.universe, [0, 0, 5]
        )
        self.slope[slope_ctgr.flats_and_plateaus] = fuzz.trimf(
            self.slope.universe, [0, 5, 10]
        )
        self.slope[
            slope_ctgr.flats_and_plateaus_in_combination_with_hills
        ] = fuzz.trimf(self.slope.universe, [5, 10, 15])
        self.slope[slope_ctgr.hills_with_gentle_slopes] = fuzz.trimf(
            self.slope.universe, [10, 15, 20]
        )
        self.slope[slope_ctgr.steeper_hills_and_foothills] = fuzz.trimf(
            self.slope.universe, [15, 20, 25]
        )
        self.slope[slope_ctgr.hills_and_outcrops_of_mountain_ranges] = fuzz.trimf(
            self.slope.universe, [20, 30, 40]
        )
        self.slope[slope_ctgr.higher_hills] = fuzz.trimf(
            self.slope.universe, [30, 45, 60]
        )
        self.slope[slope_ctgr.mountains] = fuzz.trimf(self.slope.universe, [45, 60, 80])
        self.slope[slope_ctgr.highest_mountains] = fuzz.trimf(
            self.slope.universe, [60, 80, 100]
        )

    def populate_impervious(self):
        """Populate impervious with membership functions."""
        self.impervious[impervious_ctgr.marshes] = fuzz.trimf(
            self.impervious.universe, [0, 0, 5]
        )
        self.impervious[impervious_ctgr.arable] = fuzz.trimf(
            self.impervious.universe, [0, 5, 10]
        )
        self.impervious[impervious_ctgr.meadows] = fuzz.trimf(
            self.impervious.universe, [5, 10, 15]
        )
        self.impervious[impervious_ctgr.forests] = fuzz.trimf(
            self.impervious.universe, [10, 15, 20]
        )
        self.impervious[impervious_ctgr.rural] = fuzz.trimf(
            self.impervious.universe, [15, 20, 25]
        )
        self.impervious[impervious_ctgr.suburban] = fuzz.trimf(
            self.impervious.universe, [20, 25, 30]
        )
        self.impervious[impervious_ctgr.urban] = fuzz.trimf(
            self.impervious.universe, [25, 30, 35]
        )
        self.impervious[impervious_ctgr.mountains] = fuzz.trimf(
            self.impervious.universe, [30, 65, 100]
        )
        self.impervious[impervious_ctgr.hilly] = fuzz.trimf(
            self.impervious.universe, [50, 100, 100]
        )

    def populate_catchment(self):
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
membership.populate_land_form()
membership.populate_slope()
membership.populate_impervious()
membership.populate_catchment()
