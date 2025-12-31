"""
Fuzzy logic engine for SWMM catchment parameter calculation.

This module provides the core fuzzy inference system that calculates slope,
impervious surface percentage, and catchment type based on land form and land cover inputs.

Supports dependency injection for memberships and rule engine to enable isolated testing.
"""

from typing import TYPE_CHECKING, Optional

import skfuzzy as fuzz
from skfuzzy import control as ctrl

from rcg.fuzzy import categories

if TYPE_CHECKING:
    from rcg.fuzzy.memberships import Memberships
    from rcg.fuzzy.rule_engine import RuleEngine


class FuzzyEngine:
    """
    Fuzzy inference engine for calculating SWMM catchment parameters.

    Uses fuzzy logic rules to determine appropriate slope, impervious surface percentage,
    and catchment type values based on combinations of land form and land cover characteristics.

    Supports dependency injection for memberships and rule engine to enable isolated testing.

    Attributes
    ----------
    slope_ctrl : ctrl.ControlSystem
        Control system for slope calculation (terrain steepness)
    impervious_ctrl : ctrl.ControlSystem
        Control system for impervious surface calculation (runoff characteristics)
    catchment_ctrl : ctrl.ControlSystem
        Control system for catchment type classification (land use categorization)
    slope_sim : ctrl.ControlSystemSimulation
        Simulation instance for slope inference
    impervious_sim : ctrl.ControlSystemSimulation
        Simulation instance for impervious surface inference
    catchment_sim : ctrl.ControlSystemSimulation
        Simulation instance for catchment type inference
    memberships : Memberships
        The memberships instance used for fuzzy computations.
    """

    def __init__(self, memberships: Optional["Memberships"] = None, rule_engine: Optional["RuleEngine"] = None):
        """
        Initialize fuzzy control systems for catchment parameter calculation.

        Creates control systems and simulation instances for slope, impervious surface,
        and catchment type calculations using predefined fuzzy rules.

        Parameters
        ----------
        memberships : Optional[Memberships]
            Memberships instance to use. If None, uses the default instance.
        rule_engine : Optional[RuleEngine]
            Rule engine to use. If None, uses the default engine from rule_definitions.
        """
        # Load dependencies
        if memberships is None:
            from rcg.fuzzy.memberships import get_default_memberships

            memberships = get_default_memberships()
        self.memberships = memberships

        if rule_engine is None:
            from .rule_definitions import default_engine

            rule_engine = default_engine

        # Create control systems from rule definitions
        self.slope_ctrl = ctrl.ControlSystem(rule_engine.slope_rules)
        self.impervious_ctrl = ctrl.ControlSystem(rule_engine.impervious_rules)
        self.catchment_ctrl = ctrl.ControlSystem(rule_engine.catchment_rules)

        # Create simulation instances for inference
        self.slope_sim = ctrl.ControlSystemSimulation(self.slope_ctrl)
        self.impervious_sim = ctrl.ControlSystemSimulation(self.impervious_ctrl)
        self.catchment_sim = ctrl.ControlSystemSimulation(self.catchment_ctrl)

    def compute_slope(self, land_form: int, land_cover: int) -> float:
        """
        Compute slope parameter using fuzzy inference.

        Parameters
        ----------
        land_form : int
            Land form category value (1-9)
        land_cover : int
            Land cover category value (1-14)

        Returns
        -------
        float
            Calculated slope value
        """
        return self._compute_single(self.slope_sim, land_form, land_cover, self.memberships.slope.label)

    def compute_impervious(self, land_form: int, land_cover: int) -> float:
        """
        Compute impervious surface parameter using fuzzy inference.

        Parameters
        ----------
        land_form : int
            Land form category value (1-9)
        land_cover : int
            Land cover category value (1-14)

        Returns
        -------
        float
            Calculated impervious surface percentage
        """
        return self._compute_single(self.impervious_sim, land_form, land_cover, self.memberships.impervious.label)

    def compute_catchment(self, land_form: int, land_cover: int) -> float:
        """Compute catchment type parameter using fuzzy inference."""
        return self._compute_single(self.catchment_sim, land_form, land_cover, self.memberships.catchment.label)

    def compute_all(self, land_form: int, land_cover: int) -> dict[str, float]:
        """
        Compute all catchment parameters at once.

        Args:
            land_form: Land form category value (1-9)
            land_cover: Land cover category value (1-14)

        Returns:
            Dictionary containing calculated slope, impervious, and catchment values
        """
        self._validate_inputs(land_form, land_cover)

        return {
            "slope": self.compute_slope(land_form, land_cover),
            "impervious": self.compute_impervious(land_form, land_cover),
            "catchment": self.compute_catchment(land_form, land_cover),
        }

    def _compute_single(self, sim: ctrl.ControlSystemSimulation, land_form: int, land_cover: int, output_label: str) -> float:
        """DRY helper for single parameter computation."""
        self._set_inputs(sim, land_form, land_cover)
        sim.compute()
        return sim.output[output_label]

    def _set_inputs(self, sim: ctrl.ControlSystemSimulation, land_form: int, land_cover: int):
        """Set inputs for fuzzy simulation."""
        sim.input[self.memberships.land_form_type.label] = land_form
        sim.input[self.memberships.land_cover_type.label] = land_cover

    def _validate_inputs(self, land_form: int, land_cover: int):
        """Validate input ranges for enum values."""
        if not (1 <= land_form <= 9):
            raise ValueError(f"Invalid land_form: {land_form}. Must be 1-9")
        if not (1 <= land_cover <= 14):
            raise ValueError(f"Invalid land_cover: {land_cover}. Must be 1-14")


class Prototype:
    """
    Backward-compatible wrapper for calculating catchment parameters.

    Calculates slope, impervious surface, and catchment type values
    from land form and land cover inputs using fuzzy logic inference.
    """

    def __init__(self, land_form: categories.LandForm, land_cover: categories.LandCover, engine: Optional[FuzzyEngine] = None):
        """
        Calculate catchment parameters for given land characteristics.

        Parameters
        ----------
        land_form : LandForm
            Land form category enum value.
        land_cover : LandCover
            Land cover category enum value.
        engine : Optional[FuzzyEngine]
            FuzzyEngine instance. If None, uses the default global engine.
        """
        # Use dependency injection or fall back to global for backward compatibility
        if engine is None:
            engine = get_default_fuzzy_engine()

        # Store reference to engine for get_linguistic
        self._engine = engine

        # Extract enum values and compute results
        results = engine.compute_all(land_form.value, land_cover.value)

        # Store results as instance attributes for backward compatibility
        self.slope_result = results["slope"]
        self.impervious_result = results["impervious"]
        self.catchment_result = results["catchment"]

    def get_linguistic(self, result: float, member=None) -> str:
        """
        Convert numeric fuzzy result to linguistic category name.

        Parameters
        ----------
        result : float
            Numeric output from fuzzy inference.
        member : Optional
            Membership function to use for conversion. Defaults to catchment.

        Returns
        -------
        str
            Name of the category with highest membership value.
        """
        if member is None:
            member = self._engine.memberships.catchment

        populate: dict[str, float] = {
            key: fuzz.interp_membership(member.universe, member[key].mf, result) for key in member.terms
        }
        if not populate:
            raise ValueError("No terms in the membership function")
        return max(populate, key=populate.get)


# Cache for default fuzzy engine instance (lazy initialization)
_default_fuzzy_engine: Optional[FuzzyEngine] = None


def create_fuzzy_engine(
    memberships: Optional["Memberships"] = None, rule_engine: Optional["RuleEngine"] = None
) -> FuzzyEngine:
    """
    Factory function to create a new FuzzyEngine instance.

    Use this function when you need an isolated fuzzy engine instance,
    such as in tests or when you need custom configuration.

    Parameters
    ----------
    memberships : Optional[Memberships]
        Memberships instance to use. If None, uses the default instance.
    rule_engine : Optional[RuleEngine]
        Rule engine to use. If None, uses the default engine.

    Returns
    -------
    FuzzyEngine
        A new FuzzyEngine instance.

    Example
    -------
    >>> from rcg.fuzzy.memberships import create_memberships
    >>> from rcg.fuzzy.rule_engine import create_rule_engine
    >>> memberships = create_memberships()
    >>> rule_engine = create_rule_engine(memberships)
    >>> # Define rules on rule_engine...
    >>> rule_engine.build_rule_systems()
    >>> engine = create_fuzzy_engine(memberships, rule_engine)
    """
    return FuzzyEngine(memberships=memberships, rule_engine=rule_engine)


def get_default_fuzzy_engine() -> FuzzyEngine:
    """
    Get the default (shared) FuzzyEngine instance.

    This function provides lazy initialization of a shared fuzzy engine instance.
    Use this for backward compatibility or when a shared instance is acceptable.

    Returns
    -------
    FuzzyEngine
        The shared default FuzzyEngine instance.
    """
    global _default_fuzzy_engine
    if _default_fuzzy_engine is None:
        _default_fuzzy_engine = FuzzyEngine()
    return _default_fuzzy_engine


# Backward compatibility aliases (deprecated - use create_fuzzy_engine() or get_default_fuzzy_engine())
_default_engine = get_default_fuzzy_engine()
engine = _default_engine
