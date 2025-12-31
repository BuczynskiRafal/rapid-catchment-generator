"""
Protocol interfaces for RCG components.

This module defines abstract interfaces using Python's Protocol pattern,
enabling dependency injection and improved testability across the codebase.
"""
from typing import Protocol, Dict, List, Any, runtime_checkable

from skfuzzy.control import Antecedent, Consequent


@runtime_checkable
class IMemberships(Protocol):
    """
    Protocol for fuzzy membership function providers.

    Defines the interface for classes that provide fuzzy membership functions
    for land form, land cover, slope, impervious surface, and catchment calculations.
    """
    land_form_type: Antecedent
    land_cover_type: Antecedent
    slope: Consequent
    impervious: Consequent
    catchment: Consequent


@runtime_checkable
class IRuleEngine(Protocol):
    """
    Protocol for fuzzy rule engines.

    Defines the interface for rule engine implementations that manage
    fuzzy logic rules for catchment parameter calculations.
    """

    def add_rule(self, rule: Any) -> None:
        """Add a fuzzy rule to the engine."""
        ...

    def build_rule_systems(self) -> None:
        """Build skfuzzy control systems from defined rules."""
        ...

    @property
    def slope_rules(self) -> List[Any]:
        """Get rules for slope calculation."""
        ...

    @property
    def impervious_rules(self) -> List[Any]:
        """Get rules for impervious calculation."""
        ...

    @property
    def catchment_rules(self) -> List[Any]:
        """Get rules for catchment calculation."""
        ...


@runtime_checkable
class IFuzzyEngine(Protocol):
    """
    Protocol for fuzzy inference engines.

    Defines the interface for engines that compute catchment parameters
    using fuzzy logic inference.
    """

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
        ...

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
        ...

    def compute_catchment(self, land_form: int, land_cover: int) -> float:
        """
        Compute catchment type parameter using fuzzy inference.

        Parameters
        ----------
        land_form : int
            Land form category value (1-9)
        land_cover : int
            Land cover category value (1-14)

        Returns
        -------
        float
            Calculated catchment type value
        """
        ...

    def compute_all(self, land_form: int, land_cover: int) -> Dict[str, float]:
        """
        Compute all catchment parameters at once.

        Parameters
        ----------
        land_form : int
            Land form category value (1-9)
        land_cover : int
            Land cover category value (1-14)

        Returns
        -------
        Dict[str, float]
            Dictionary containing 'slope', 'impervious', and 'catchment' values
        """
        ...
