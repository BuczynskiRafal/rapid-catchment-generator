import time

import numpy as np
import pandas as pd
import skfuzzy as fuzz
from skfuzzy import control as ctrl


class ManningN:

    smooth_asphalt = 0.011
    smooth_concrete = 0.012
    ordinary_concrete_lining = 0.013
    good_wood = 0.014
    brick_with_cement_mortar = 0.014
    vitrified_clay = 0.015
    cast_iron = 0.015
    corrugated_metal_pipes = 0.024
    cement_rubble_surface = 0.024
    fallow_soils = 0.05
    residue_cover_below_20_percent = 0.06
    residue_cover_over_20_percent = 0.17
    range_natural = 0.13
    short_grass = 0.15
    prairie_grass = 0.15
    dense_grass = 0.24
    bermuda_grass = 0.41
    light_underbrush_wood = 0.40
    dense_underbrush_wood = 0.80


class DepressionStorage:
    impervious_surfaces = 0.10 * 25.4
    lawns = 0.20 * 25.4
    pasture = 0.20 * 25.4
    forest_litter = 0.30


class LandUse:
    marshes_and_lowlands = 1,
    flats_and_plateaus = 2,
    flats_and_plateaus_in_combination_with_hills = 3,
    hills_with_gentle_slopes = 4
    steeper_hills_and_foothills = 5
    hills_and_outcrops_of_mountain_ranges = 6
    higher_hills = 7
    mountains = 8
    highest_mountains = 9


class LandType:
    medium_conditions = 1
    permeable_areas = 2
    permeable_terrain_on_plains = 3
    hilly_terrain = 4
    mountainous_terrain = 5
    bare_rocky_slopes = 6
    urban = 7
    suburban = 8
    rural = 9
    forests = 10
    meadows = 11
    arable_land = 12
    marshes = 13


class PopulateFeatures:
    def __init__(self):
        self.land_use_type = ctrl.Antecedent(np.arange(0, 10, 1), 'land_use')
        self.land_form_type = ctrl.Antecedent(np.arange(0, 14, 1), 'land_form')
        self.slope = ctrl.Consequent(np.arange(1, 101, 1), 'slope')

    def define_rules(self):
        # Populate land use type with membership functions.
        self.land_use_type['marshes_and_lowlands'] = fuzz.trimf(self.land_use_type.universe, [0, 1, 2])
        self.land_use_type['flats_and_plateaus'] = fuzz.trimf(self.land_use_type.universe, [1, 2, 3])
        self.land_use_type['flats_and_plateaus_in_combination_with_hills'] = fuzz.trimf(self.land_use_type.universe, [2, 3, 4])
        self.land_use_type['hills_with_gentle_slopes'] = fuzz.trimf(self.land_use_type.universe, [3, 4, 5])
        self.land_use_type['steeper_hills_and_foothills'] = fuzz.trimf(self.land_use_type.universe, [4, 5, 6])
        self.land_use_type['hills_and_outcrops_of_mountain_ranges'] = fuzz.trimf(self.land_use_type.universe, [5, 6, 7])
        self.land_use_type['higher_hills'] = fuzz.trimf(self.land_use_type.universe, [6, 7, 8])
        self.land_use_type['mountains'] = fuzz.trimf(self.land_use_type.universe, [7, 8, 9])
        self.land_use_type['highest_mountains'] = fuzz.trimf(self.land_use_type.universe, [8, 9, 10])

        # Populate land form type with membership functions.
        self.land_form_type['medium_conditions'] = fuzz.trimf(self.land_form_type.universe, [0, 1, 2])
        self.land_form_type['permeable_areas'] = fuzz.trimf(self.land_form_type.universe, [1, 2, 3])
        self.land_form_type['permeable_terrain_on_plains'] = fuzz.trimf(self.land_form_type.universe, [2, 3, 4])
        self.land_form_type['hilly_terrain'] = fuzz.trimf(self.land_form_type.universe, [3, 4, 5])
        self.land_form_type['mountainous_terrain'] = fuzz.trimf(self.land_form_type.universe, [4, 5, 6])
        self.land_form_type['bare_rocky_slopes'] = fuzz.trimf(self.land_form_type.universe, [5, 6, 7])
        self.land_form_type['urban'] = fuzz.trimf(self.land_form_type.universe, [6, 7, 8])
        self.land_form_type['suburban'] = fuzz.trimf(self.land_form_type.universe, [7, 8, 9])
        self.land_form_type['rural'] = fuzz.trimf(self.land_form_type.universe, [8, 9, 10])
        self.land_form_type['forests'] = fuzz.trimf(self.land_form_type.universe, [9, 10, 11])
        self.land_form_type['meadows'] = fuzz.trimf(self.land_form_type.universe, [10, 11, 12])
        self.land_form_type['arable_land'] = fuzz.trimf(self.land_form_type.universe, [11, 12, 13])
        self.land_form_type['marshes'] = fuzz.trimf(self.land_form_type.universe, [12, 13, 14])

        # Populate slope with membership functions.
        self.slope['marshes_and_lowlands'] = fuzz.trimf(self.slope.universe, [0, 1.5, 3])
        self.slope['flats_and_plateaus'] = fuzz.trimf(self.slope.universe, [1.5, 3, 5])
        self.slope['flats_and_plateaus_in_combination_with_hills'] = fuzz.trimf(self.slope.universe, [3, 5, 7])
        self.slope['hills_with_gentle_self.slopes'] = fuzz.trimf(self.slope.universe, [5, 7, 8])
        self.slope['steeper_hills_and_foothills'] = fuzz.trimf(self.slope.universe, [7, 8, 10])
        self.slope['hills_and_outcrops_of_mountain_ranges'] = fuzz.trimf(self.slope.universe, [8, 10, 15])
        self.slope['higher_hills'] = fuzz.trimf(self.slope.universe, [10, 15, 20])
        self.slope['mountains'] = fuzz.trimf(self.slope.universe, [15, 20, 50])
        self.slope['highest_mountains'] = fuzz.trimf(self.slope.universe, [20, 50, 100])

        # Define rules for slope
        rule9 = ctrl.Rule(antecedent=((self.land_use_type['highest_mountains'] & self.land_form_type['hilly_terrain']) |
                                      (self.land_use_type['highest_mountains'] & self.land_form_type['bare_rocky_slopes']) |
                                      (self.land_use_type['highest_mountains'] & self.land_form_type['mountainous_terrain'])),
                          consequent=self.slope['highest_mountains'])

        rule8 = ctrl.Rule(antecedent=((self.land_use_type['mountains'] & self.land_form_type['hilly_terrain']) |
                                      (self.land_use_type['mountains'] & self.land_form_type['bare_rocky_slopes']) |
                                      (self.land_use_type['mountains'] & self.land_form_type['mountainous_terrain'])),
                          consequent=self.slope['mountains'])

        rule7 = ctrl.Rule(antecedent=((self.land_use_type['higher_hills'] & self.land_form_type['hilly_terrain']) |
                                      (self.land_use_type['higher_hills'] & self.land_form_type['bare_rocky_slopes']) |
                                      (self.land_use_type['higher_hills'] & self.land_form_type['mountainous_terrain'])),
                          consequent=self.slope['higher_hills'])

        rule6 = ctrl.Rule(
            antecedent=((self.land_use_type['hills_and_outcrops_of_mountain_ranges'] & self.land_form_type['hilly_terrain']) |
                        (self.land_use_type['hills_and_outcrops_of_mountain_ranges'] & self.land_form_type[
                            'bare_rocky_slopes']) |
                        (self.land_use_type['hills_and_outcrops_of_mountain_ranges'] & self.land_form_type[
                            'mountainous_terrain'])),
            consequent=self.slope['hills_and_outcrops_of_mountain_ranges'])

        rule5 = ctrl.Rule(
            antecedent=((self.land_use_type['steeper_hills_and_foothills'] & self.land_form_type['medium_conditions']) |
                        (self.land_use_type['steeper_hills_and_foothills'] & self.land_form_type['permeable_areas']) |
                        (self.land_use_type['steeper_hills_and_foothills'] & self.land_form_type['hilly_terrain']) |
                        (self.land_use_type['steeper_hills_and_foothills'] & self.land_form_type['forests']) |
                        (self.land_use_type['steeper_hills_and_foothills'] & self.land_form_type['rural']) |
                        (self.land_use_type['steeper_hills_and_foothills'] & self.land_form_type['suburban'])),
            consequent=self.slope['steeper_hills_and_foothills'])

        rule4 = ctrl.Rule(
            antecedent=((self.land_use_type['hills_with_gentle_slopes'] & self.land_form_type['medium_conditions']) |
                        (self.land_use_type['hills_with_gentle_slopes'] & self.land_form_type['permeable_areas']) |
                        (self.land_use_type['hills_with_gentle_slopes'] & self.land_form_type['hilly_terrain']) |
                        (self.land_use_type['hills_with_gentle_slopes'] & self.land_form_type['forests']) |
                        (self.land_use_type['hills_with_gentle_slopes'] & self.land_form_type['rural']) |
                        (self.land_use_type['hills_with_gentle_slopes'] & self.land_form_type['rural']) |
                        (self.land_use_type['hills_with_gentle_slopes'] & self.land_form_type['suburban'])),
            consequent=self.slope['hills_with_gentle_slopes'])

        rule3 = ctrl.Rule(antecedent=((self.land_use_type['flats_and_plateaus_in_combination_with_hills'] & self.land_form_type[
            'medium_conditions']) |
                                      (self.land_use_type['flats_and_plateaus_in_combination_with_hills'] & self.land_form_type[
                                          'permeable_areas']) |
                                      (self.land_use_type['flats_and_plateaus_in_combination_with_hills'] & self.land_form_type[
                                          'rural']) |
                                      (self.land_use_type['flats_and_plateaus_in_combination_with_hills'] & self.land_form_type[
                                          'forests']) |
                                      (self.land_use_type['flats_and_plateaus_in_combination_with_hills'] & self.land_form_type[
                                          'arable_land']) |
                                      (self.land_use_type['flats_and_plateaus_in_combination_with_hills'] & self.land_form_type[
                                          'marshes'])),
                          consequent=self.slope['flats_and_plateaus_in_combination_with_hills'])

        rule2 = ctrl.Rule(antecedent=((self.land_use_type['flats_and_plateaus'] & self.land_form_type['medium_conditions']) |
                                      (self.land_use_type['flats_and_plateaus'] & self.land_form_type['permeable_areas']) |
                                      (self.land_use_type['flats_and_plateaus'] & self.land_form_type['rural']) |
                                      (self.land_use_type['flats_and_plateaus'] & self.land_form_type['forests']) |
                                      (self.land_use_type['flats_and_plateaus'] & self.land_form_type['arable_land']) |
                                      (self.land_use_type['flats_and_plateaus'] & self.land_form_type['meadows']) |
                                      (self.land_use_type['flats_and_plateaus'] & self.land_form_type['marshes'])),
                          consequent=self.slope['flats_and_plateaus'])

        rule1 = ctrl.Rule(antecedent=((self.land_use_type['marshes_and_lowlands'] & self.land_form_type['medium_conditions']) |
                                      (self.land_use_type['marshes_and_lowlands'] & self.land_form_type['permeable_areas']) |
                                      (self.land_use_type['marshes_and_lowlands'] & self.land_form_type['rural']) |
                                      (self.land_use_type['marshes_and_lowlands'] & self.land_form_type['forests']) |
                                      (self.land_use_type['marshes_and_lowlands'] & self.land_form_type['arable_land']) |
                                      (self.land_use_type['marshes_and_lowlands'] & self.land_form_type['meadows']) |
                                      (self.land_use_type['marshes_and_lowlands'] & self.land_form_type['marshes'])),
                          consequent=self.slope['marshes_and_lowlands'])

        return [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9]

    def prepare_controller(self):
        return ctrl.ControlSystem(self.define_rules())

    def compute_controller(self):
        return ctrl.ControlSystemSimulation(self.prepare_controller())

    def calculate(self, percent_slope, percent_impervious, percent_zero_imperv):
        simulation = self.compute_controller()
        simulation.input["percent_slope"] = percent_slope
        simulation.input["percent_impervious"] = percent_impervious
        simulation.input["percent_zero_imperv"] = percent_zero_imperv
        simulation.compute()
        return simulation.output["subcatchment"]

#
# obj = PopulateFeatures()
# calc = obj.calculate(percent_slope=10, percent_impervious=10, percent_zero_imperv=10)
# print(obj.subcatchment.view(sim=calc))


def fuzzy_logic(s, i):
    slope = ctrl.Antecedent(np.arange(0, 100 + 1, 1), 'slope')
    impervious = ctrl.Antecedent(np.arange(0, 100 + 0.1, 0.1), 'impervious')
    catchment_category = ctrl.Consequent(np.arange(1, 101, 1), 'category')

    # Populate slope with membership functions.
    slope['marshes_and_lowlands'] = fuzz.zmf(slope.universe, 0, 5)
    slope['flats_and_plateaus'] = fuzz.pimf(slope.universe, 0, 10, 10, 20)
    slope['flats_and_plateaus_in_combination_with_hills'] = fuzz.smf(slope.universe, 10, 40)
    slope['hills_with_gentle_slopes'] = fuzz.smf(slope.universe, 10, 60)
    slope['steeper_hills_and_foothills'] = fuzz.smf(slope.universe, 15, 60)

    """
    6 Hills and outcrops of mountain ranges
    7 Higher hills
    8 Mountains
    9 Highest mountains
    """


    # Populate velocity with membership functions.
    impervious['low'] = fuzz.zmf(impervious.universe, 0,10)
    impervious['medium'] = fuzz.pimf(impervious.universe, 0, 10,  10, 20)
    impervious['high'] = fuzz.smf(impervious.universe, 10, 20)

    # Populate diamter
    catchment_category['C1'] = fuzz.zmf(catchment_category.universe, 1, 50)
    catchment_category['C2'] = fuzz.pimf(catchment_category.universe, 1, 50, 50, 100)
    catchment_category['C3'] = fuzz.smf(catchment_category.universe, 50, 100)

    # Define rules
    r1 = ctrl.Rule(slope['marshes_and_lowlands'] & impervious['low'], catchment_category['C1'])
    r2 = ctrl.Rule(slope['marshes_and_lowlands'] & impervious['medium'], catchment_category['C1'])
    r3 = ctrl.Rule(slope['flats_and_plateaus'] & impervious['low'], catchment_category['C1'])
    r4 = ctrl.Rule(slope['flats_and_plateaus'] & impervious['low'], catchment_category['C1'])

    r5 = ctrl.Rule(slope['flats_and_plateaus_in_combination_with_hills'] & impervious['medium'], catchment_category['C2'])

    r6 = ctrl.Rule(slope['hills_with_gentle_slopes'] & impervious['medium'], catchment_category['C3'])
    r7 = ctrl.Rule(slope['hills_with_gentle_slopes'] & impervious['high'], catchment_category['C3'])
    r8 = ctrl.Rule(slope['steeper_hills_and_foothills'] & impervious['high'], catchment_category['C3'])
    r9 = ctrl.Rule(slope['steeper_hills_and_foothills'] & impervious['high'], catchment_category['C3'])

    diameter_ctrl = ctrl.ControlSystem([r1, r2, r3, r4, r5, r6, r7, r8, r9])

    # compute
    diameters = ctrl.ControlSystemSimulation(diameter_ctrl)

    # calculate
    diameters.input['slope'] = s
    diameters.input['impervious'] = i

    diameters.compute()
    return diameters.output['diameter']

out = fuzzy_logic(s=5, i=10)



class FuzzyCatchments:
    def __init__(
        self,
        area:int,
        width:int,
        percent_slope:str,
        percent_impervious:str,
        n_imperv: ManningN,
        n_perv:ManningN,
        destore_imperv:DepressionStorage,
        destore_perv:DepressionStorage,
        percent_zero_imperv:str,
    ):
        self.area = area
        self.width = width
        self.percent_slope = percent_slope
        self.percent_impervious = percent_impervious
        self.n_imperv = n_imperv
        self.n_perv = n_perv
        self.destore_imperv = destore_imperv
        self.destore_perv = destore_perv
        self.percent_zero_imperv = percent_zero_imperv

    #     memberships = PopulateFeatures()
    #
    #     memberships.percent_slope['low'] = fuzz.zmf(memberships.percent_slope.universe, 0, 100 / 2)
    #     memberships.percent_slope['medium'] = fuzz.pimf(memberships.percent_slope.universe, 0, 100 / 2, 100 / 2, 100 + 1)
    #     memberships.percent_slope['high'] = fuzz.smf(memberships.percent_slope.universe, 100 / 2, 100 + 1)
    #
    #     memberships.percent_impervious['low'] = fuzz.zmf(memberships.percent_impervious.universe, 0, 100 / 2)
    #     memberships.percent_impervious['medium'] = fuzz.pimf(memberships.percent_impervious.universe, 0, 100 / 2, 100 / 2, 100 + 1)
    #     memberships.percent_impervious['high'] = fuzz.smf(memberships.percent_impervious.universe, 100 / 2, 100 + 1)
    #
    #     memberships.percent_zero_imperv['low'] = fuzz.zmf(memberships.percent_zero_imperv.universe, 0, 100 / 2)
    #     memberships.percent_zero_imperv['medium'] = fuzz.pimf(memberships.percent_zero_imperv.universe, 0, 100 / 2, 100 / 2, 100 + 1)
    #     memberships.percent_zero_imperv['high'] = fuzz.smf(memberships.percent_zero_imperv.universe, 100 / 2, 100 + 1)
    #
    #     memberships.subcatchment['1'] = fuzz.zmf(memberships.subcatchment.universe, 0, 100 / 2)
    #     memberships.subcatchment['2'] = fuzz.pimf(memberships.subcatchment.universe, 0, 100 / 2, 100 / 2, 100 + 1)
    #     memberships.subcatchment['3'] = fuzz.smf(memberships.subcatchment.universe, 100 / 2, 100 + 1)
    #
    # def define_rules(self):
    #     r_1 = ctrl.Rule(self.percent_slope['low'] & self.percent_impervious['low'] & self.percent_zero_imperv['low'], self.subcatchment['1'])
    #     r_2 = ctrl.Rule(self.percent_slope['medium'] & self.percent_impervious['medium'] & self.percent_zero_imperv['medium'], self.subcatchment['2'])
    #     r_3 = ctrl.Rule(self.percent_slope['high'] & self.percent_impervious['high'] & self.percent_zero_imperv['high'], self.subcatchment['3'])
    #     return [r_1, r_2, r_3]
    #
    # def prepare_controller(self):
    #     return ctrl.ControlSystem(self.define_rules())
    #
    # def compute_controller(self):
    #     return ctrl.ControlSystemSimulation(self.prepare_controller())
    #
    # def calculate(self, percent_slope, percent_impervious, percent_zero_imperv):
    #     simulation = self.compute_controller()
    #     simulation.input[self.percent_slope] = percent_slope
    #     simulation.input[self.percent_impervious] = percent_impervious
    #     simulation.input[self.percent_zero_imperv] = percent_zero_imperv
    #     simulation.compute()
    #     return simulation.output[self.subcatchment]