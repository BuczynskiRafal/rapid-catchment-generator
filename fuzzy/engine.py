import skfuzzy as fuzz
from fuzzy import categories

from fuzzy.rules import slope_rules, impervious_rules, catchment_rules
from fuzzy.categories import (
    land_use,
    land_form,
    slope_ctgr,
    impervious_ctgr,
    catchment_ctgr,
)

from skfuzzy import control as ctrl
from fuzzy.memberships import membership


class FuzzyEngine:
    """FuzzyEngine returns result of calculation the slope, impervious, and catchment values."""

    def __init__(self):
        """
        The function takes in two inputs, land use and land form, and then uses the rules defined in the rules.py file to
        calculate the slope, impervious, and catchment values.

        :param land_use: categories.LandUse
        :type land_use: categories.LandUse
        :param land_form: categories.LandForm
        :type land_form: categories.LandForm
        """
        self.slope_simulation_ctrl = ctrl.ControlSystem(slope_rules)
        self.impervious_simulation_ctrl = ctrl.ControlSystem(impervious_rules)
        self.catchment_simulation_ctrl = ctrl.ControlSystem(catchment_rules)

        # compute
        self.slope_simulation = ctrl.ControlSystemSimulation(self.slope_simulation_ctrl)
        self.impervious_simulation = ctrl.ControlSystemSimulation(
            self.impervious_simulation_ctrl
        )
        self.catchment_simulation = ctrl.ControlSystemSimulation(
            self.catchment_simulation_ctrl
        )


engine = FuzzyEngine()


class Prototype:

    def __init__(self, land_use: categories.LandUse, land_form: categories.LandForm):
        """The function takes in two inputs, land use and land form, and then uses the rules defined in the rules.py file to
        calculate the slope, impervious, and catchment values.

        :param land_use: categories.LandUse
        :type land_use: categories.LandUse
        :param land_form: categories.LandForm
        :type land_form: categories.LandForm"""

        # calculate
        engine.slope_simulation.input[membership.land_use_type.label] = land_use
        engine.slope_simulation.input[membership.land_form_type.label] = land_form

        engine.impervious_simulation.input[membership.land_use_type.label] = land_use
        engine.impervious_simulation.input[membership.land_form_type.label] = land_form

        engine.catchment_simulation.input[membership.land_use_type.label] = land_use
        engine.catchment_simulation.input[membership.land_form_type.label] = land_form

        # get slope result
        engine.slope_simulation.compute()
        self.slope_result = engine.slope_simulation.output[membership.slope.label]

        # get impervious result
        engine.impervious_simulation.compute()
        self.impervious_result = engine.impervious_simulation.output[
            membership.impervious.label
        ]

        # get catchment result
        engine.catchment_simulation.compute()
        self.catchment_result = engine.catchment_simulation.output[
            membership.catchment.label
        ]

    @staticmethod
    def get_populate(result: float, member: membership = membership.catchment):
        """
        > get_populate takes a result and a membership, and returns the lingustic variable of member category.

        :param result: the result of the fuzzy logic calculation
        :type result: float
        :param member: membership = membership.catchment
        :type member: membership
        :return: Lingustic variable, member category
        """
        populate = {
            key: fuzz.interp_membership(member.universe, member[key].mf, result)
            for key in member.terms
        }
        return max(populate, key=populate.get)
