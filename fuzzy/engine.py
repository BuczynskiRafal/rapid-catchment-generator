import skfuzzy as fuzz
from fuzzy import categories

from fuzzy.rules import slope_rules, impervious_rules, catchment_rules
from fuzzy.categories import (
    land_form,
    land_cover,
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
    def __init__(self, land_form: categories.LandForm, land_cover: categories.LandCover):
        """The function takes in two inputs, land use and land form, and then uses the rules defined in the rules.py file to
        calculate the slope, impervious, and catchment values.

        :param land_form: categories.LandForm
        :type land_form: categories.LandForm
        :param land_cover: categories.LandCover
        :type land_cover: categories.LandCover
        """

        # calculate
        engine.slope_simulation.input[membership.land_form_type.label] = land_form
        engine.slope_simulation.input[membership.land_cover_type.label] = land_cover

        engine.impervious_simulation.input[membership.land_form_type.label] = land_form
        engine.impervious_simulation.input[membership.land_cover_type.label] = land_cover

        engine.catchment_simulation.input[membership.land_form_type.label] = land_form
        engine.catchment_simulation.input[membership.land_cover_type.label] = land_cover

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
