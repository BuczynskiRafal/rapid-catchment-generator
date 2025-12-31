"""
Rule Engine for fuzzy logic rules with clean DSL.

This module provides a clean, readable way to define and execute fuzzy logic rules,
replacing the monolithic rules.py with a more maintainable architecture.

Supports dependency injection for memberships to enable isolated testing.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from skfuzzy import control as ctrl
from skfuzzy.control import Antecedent, Consequent
from skfuzzy.control import Rule as SkfuzzyRule

if TYPE_CHECKING:
    from .memberships import Memberships


@dataclass
class Condition:
    """Represents a single condition in a fuzzy rule."""

    variable: str
    value: Enum

    def to_skfuzzy(self, memberships: "Memberships") -> Any:
        """
        Convert condition to skfuzzy format.

        Parameters
        ----------
        memberships : Memberships
            The memberships instance to use for conversion.

        Returns
        -------
        Any
            skfuzzy antecedent term.
        """
        if self.variable == "land_form":
            return memberships.land_form_type[self.value.name]
        elif self.variable == "land_cover":
            return memberships.land_cover_type[self.value.name]
        else:
            raise ValueError(f"Unknown variable: {self.variable}")


@dataclass
class FuzzyRule:
    """Represents a complete fuzzy rule with conditions and consequences."""

    name: str
    conditions: list[Condition]
    consequences: dict[str, Enum]

    def build_antecedent(self, memberships: "Memberships") -> Antecedent:
        """
        Build the antecedent (IF part) of the rule.

        Parameters
        ----------
        memberships : Memberships
            The memberships instance to use for building antecedents.

        Returns
        -------
        Antecedent
            Combined antecedent for all conditions.
        """
        if not self.conditions:
            raise ValueError("Rule must have at least one condition")

        skfuzzy_conditions = [cond.to_skfuzzy(memberships) for cond in self.conditions]
        antecedent = skfuzzy_conditions[0]
        for condition in skfuzzy_conditions[1:]:
            antecedent = antecedent & condition
        return antecedent

    def get_consequence(self, output_type: str, memberships: "Memberships") -> Optional[Consequent]:
        """
        Get the consequence for a specific output type.

        Parameters
        ----------
        output_type : str
            Type of output ('slope', 'impervious', or 'catchment').
        memberships : Memberships
            The memberships instance to use for consequences.

        Returns
        -------
        Optional[Consequent]
            The consequent term, or None if not defined.
        """
        if output_type not in self.consequences:
            return None

        consequence_value = self.consequences[output_type]

        if output_type == "slope":
            return memberships.slope[consequence_value.value]
        elif output_type == "impervious":
            return memberships.impervious[consequence_value.value]
        elif output_type == "catchment":
            return memberships.catchment[consequence_value.value]
        else:
            raise ValueError(f"Unknown output type: {output_type}")


class RuleBuilder:
    """Builder class for creating fuzzy rules with a fluent API.

    Example:
        rule("flat_urban")
            .when(land_form=LandForm.FLAT, land_cover=LandCover.URBAN)
            .then(slope=Slope.LOW, impervious=Impervious.HIGH)
            .build()
    """

    def __init__(self):
        self.conditions: list[Condition] = []
        self.consequences: dict[str, Enum] = {}
        self.rule_name: str = ""

    def named(self, name: str) -> "RuleBuilder":
        """Set the name of the rule."""
        self.rule_name = name
        return self

    def when(self, **conditions) -> "RuleBuilder":
        """Add conditions to the rule."""
        for variable, value in conditions.items():
            if not isinstance(value, Enum):
                raise ValueError(f"Condition value must be an Enum, got {type(value)}")
            self.conditions.append(Condition(variable, value))
        return self

    def then(self, **consequences) -> "RuleBuilder":
        """Set consequences for the rule."""
        for key, value in consequences.items():
            if not isinstance(value, Enum):
                raise ValueError(f"Consequence value must be an Enum, got {type(value)}")
            self.consequences[key] = value
        return self

    def build(self) -> FuzzyRule:
        """Build and validate the final rule."""
        if not self.conditions or not self.consequences:
            raise ValueError("Rule must have conditions and consequences")

        if not self.rule_name:
            self.rule_name = f"rule_{len(self.conditions)}_conditions"

        return FuzzyRule(self.rule_name, self.conditions.copy(), self.consequences.copy())


class RuleEngine:
    """
    Main rule engine that manages and executes fuzzy rules.

    Supports dependency injection for memberships to enable isolated testing.
    """

    def __init__(self, memberships: Optional["Memberships"] = None):
        """
        Initialize the rule engine.

        Parameters
        ----------
        memberships : Optional[Memberships]
            Memberships instance to use. If None, uses the default instance.
        """
        self.rules: list[FuzzyRule] = []
        self._rule_systems: dict[str, list[SkfuzzyRule]] = {"slope": [], "impervious": [], "catchment": []}
        self._memberships = memberships

    def _get_memberships(self) -> "Memberships":
        """Get the memberships instance, loading default if needed."""
        if self._memberships is None:
            from .memberships import get_default_memberships

            self._memberships = get_default_memberships()
        return self._memberships

    def add_rule(self, rule: FuzzyRule) -> None:
        """Add a fuzzy rule to the engine."""
        self.rules.append(rule)

    def build_rule_systems(self) -> None:
        """Build skfuzzy control systems from the defined rules."""
        self._rule_systems = {k: [] for k in self._rule_systems}  # Clear existing
        memberships = self._get_memberships()

        for rule in self.rules:
            antecedent = rule.build_antecedent(memberships)
            for output_type in self._rule_systems.keys():
                consequent = rule.get_consequence(output_type, memberships)
                if consequent:
                    skfuzzy_rule = ctrl.Rule(antecedent=antecedent, consequent=consequent)
                    self._rule_systems[output_type].append(skfuzzy_rule)

    @property
    def slope_rules(self) -> list[SkfuzzyRule]:
        """Get rules for slope calculation."""
        return self._rule_systems["slope"]

    @property
    def impervious_rules(self) -> list[SkfuzzyRule]:
        """Get rules for impervious calculation."""
        return self._rule_systems["impervious"]

    @property
    def catchment_rules(self) -> list[SkfuzzyRule]:
        """Get rules for catchment calculation."""
        return self._rule_systems["catchment"]

    def get_rule_count(self) -> dict[str, int]:
        """Get count of rules for each output type."""
        return {"total": len(self.rules), **{name: len(rules) for name, rules in self._rule_systems.items()}}


def rule(name: str) -> RuleBuilder:
    """Create a new rule builder with the given name."""
    return RuleBuilder().named(name)


# Cache for default rule engine instance (lazy initialization)
_default_rule_engine: Optional[RuleEngine] = None


def create_rule_engine(memberships: Optional["Memberships"] = None) -> RuleEngine:
    """
    Factory function to create a new RuleEngine instance.

    Use this function when you need an isolated rule engine instance,
    such as in tests or when you need custom configuration.

    Parameters
    ----------
    memberships : Optional[Memberships]
        Memberships instance to use. If None, uses the default instance.

    Returns
    -------
    RuleEngine
        A new RuleEngine instance.

    Example
    -------
    >>> from rcg.fuzzy.memberships import create_memberships
    >>> memberships = create_memberships()
    >>> engine = create_rule_engine(memberships)
    """
    return RuleEngine(memberships=memberships)


def get_default_rule_engine() -> RuleEngine:
    """
    Get the default (shared) RuleEngine instance.

    This function provides lazy initialization of a shared rule engine instance.
    Use this for backward compatibility or when a shared instance is acceptable.

    Returns
    -------
    RuleEngine
        The shared default RuleEngine instance.
    """
    global _default_rule_engine
    if _default_rule_engine is None:
        _default_rule_engine = RuleEngine()
    return _default_rule_engine


# Backward compatibility alias (deprecated - use create_rule_engine() or get_default_rule_engine())
default_engine = get_default_rule_engine()
