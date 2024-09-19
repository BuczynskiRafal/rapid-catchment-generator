import skfuzzy as fuzz
from rcg.fuzzy import categories
from .rules import slope_rules, impervious_rules, catchment_rules

from skfuzzy import control as ctrl
from rcg.fuzzy.memberships import Memberships, membership

class FuzzyEngine:
    """
    FuzzyEngine returns the result of calculating the slope, impervious, and catchment values.
    """

    def __init__(self):
        """
        Initializes FuzzyEngine with the control systems and simulations for slope, impervious, and catchment.
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
    """
    Prototype is a class that calculates the slope, impervious, and catchment values based on given land form and
    land cover categories using fuzzy logic rules defined in rules.py.
    """
    def __init__(self, land_form: categories.LandForm, land_cover: categories.LandCover):
        """
        Initializes a Prototype instance with the given land_form and land_cover.

        Parameters
        ----------
        land_form : categories.LandForm
            Land form category to be used for the fuzzy logic calculation.
        land_cover : categories.LandCover
            Land cover category to be used for the fuzzy logic calculation.
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
    def get_populate(result: float, member: Memberships = membership.catchment):
        """
        Returns the linguistic variable of the given member category based on the result.

        Parameters
        ----------
        result : float
            The result of the fuzzy logic calculation.
        member : membership, optional
            Membership category to be used, by default membership.catchment.

        Returns
        -------
        str
            Linguistic variable of the member category.
        """
        populate = {
            key: fuzz.interp_membership(member.universe, member[key].mf, result)
            for key in member.terms
        }
        return max(populate, key=populate.get)
