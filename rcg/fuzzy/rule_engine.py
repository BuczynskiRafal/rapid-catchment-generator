"""
Rule Engine for fuzzy logic rules with clean DSL.

This module provides a small builder DSL for fuzzy rules and compiles them to skfuzzy;
the rule set itself lives in ``rule_definitions``.

Supports dependency injection for memberships to enable isolated testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from skfuzzy import control as ctrl
from skfuzzy.control import Antecedent, Consequent
from skfuzzy.control import Rule as SkfuzzyRule

from rcg.exceptions import RuleDefinitionError

if TYPE_CHECKING:
    from .memberships import Memberships


@dataclass
class Condition:
    """Represents a single condition in a fuzzy rule."""

    variable: str
    value: Enum

    def to_skfuzzy(self, memberships: Memberships) -> Any:
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

        Raises
        ------
        RuleDefinitionError
            If the variable or its term does not exist.
        """
        return memberships.term(self.variable, self.value.name)


@dataclass
class FuzzyRule:
    """Represents a complete fuzzy rule with conditions and consequences."""

    name: str
    conditions: list[Condition]
    consequences: dict[str, Enum]

    def build_antecedent(self, memberships: Memberships) -> Antecedent:
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
            raise RuleDefinitionError("Rule must have at least one condition", rule_name=self.name)

        skfuzzy_conditions = [cond.to_skfuzzy(memberships) for cond in self.conditions]
        antecedent = skfuzzy_conditions[0]
        for condition in skfuzzy_conditions[1:]:
            antecedent = antecedent & condition
        return antecedent

    def get_consequence(self, output_type: str, memberships: Memberships) -> Consequent | None:
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
        Consequent | None
            The consequent term, or None if not defined.
        """
        if output_type not in self.consequences:
            return None
        return memberships.term(output_type, self.consequences[output_type].name)


class RuleBuilder:
    """Builder class for creating fuzzy rules with a fluent API.

    Example:
        rule("flat_urban")
            .when(land_form=LandForm.FLAT, land_cover=LandCover.URBAN)
            .then(slope=Slope.LOW, impervious=Impervious.HIGH)
            .build()
    """

    def __init__(self) -> None:
        self.conditions: list[Condition] = []
        self.consequences: dict[str, Enum] = {}
        self.rule_name: str = ""

    def named(self, name: str) -> RuleBuilder:
        """Set the name of the rule."""
        self.rule_name = name
        return self

    def when(self, **conditions) -> RuleBuilder:
        """Add conditions to the rule."""
        for variable, value in conditions.items():
            if not isinstance(value, Enum):
                raise RuleDefinitionError(f"Condition value must be an Enum, got {type(value)}", rule_name=self.rule_name)
            self.conditions.append(Condition(variable, value))
        return self

    def then(self, **consequences) -> RuleBuilder:
        """Set consequences for the rule."""
        for key, value in consequences.items():
            if not isinstance(value, Enum):
                raise RuleDefinitionError(f"Consequence value must be an Enum, got {type(value)}", rule_name=self.rule_name)
            self.consequences[key] = value
        return self

    def build(self) -> FuzzyRule:
        """Build and validate the final rule."""
        if not self.conditions or not self.consequences:
            raise RuleDefinitionError("Rule must have conditions and consequences", rule_name=self.rule_name)

        if not self.rule_name:
            self.rule_name = f"rule_{len(self.conditions)}_conditions"

        return FuzzyRule(self.rule_name, self.conditions.copy(), self.consequences.copy())


class RuleEngine:
    """
    Main rule engine that manages and executes fuzzy rules.

    Supports dependency injection for memberships to enable isolated testing.
    """

    def __init__(self, memberships: Memberships | None = None):
        """
        Initialize the rule engine.

        Parameters
        ----------
        memberships : Memberships, optional
            Memberships instance to use. If None, uses the default instance.
        """
        self.rules: list[FuzzyRule] = []
        self._rule_systems: dict[str, list[SkfuzzyRule]] = {"slope": [], "impervious": [], "catchment": []}
        self._memberships = memberships

    def _get_memberships(self) -> Memberships:
        """Get the memberships instance, loading default if needed."""
        if self._memberships is None:
            from .memberships import get_default_memberships

            self._memberships = get_default_memberships()
        return self._memberships

    def add_rule(self, rule: FuzzyRule) -> None:
        """Add a fuzzy rule to the engine."""
        self.rules.append(rule)

    def build_rule_systems(self) -> None:
        """Build skfuzzy control systems from the defined rules.

        Raises
        ------
        RuleDefinitionError
            If a rule names an unknown variable, term or output; the message names the rule.
        """
        self._rule_systems = {k: [] for k in self._rule_systems}  # Clear existing
        memberships = self._get_memberships()

        for rule in self.rules:
            try:
                unknown = sorted(set(rule.consequences) - set(self._rule_systems))
                if unknown:
                    raise RuleDefinitionError(
                        f"Unknown output {', '.join(map(repr, unknown))}; expected one of {', '.join(self._rule_systems)}"
                    )
                antecedent = rule.build_antecedent(memberships)
                for output_type in self._rule_systems:
                    consequent = rule.get_consequence(output_type, memberships)
                    if consequent:
                        skfuzzy_rule = ctrl.Rule(antecedent=antecedent, consequent=consequent)
                        self._rule_systems[output_type].append(skfuzzy_rule)
            except RuleDefinitionError as e:
                raise RuleDefinitionError(f"Rule {rule.name!r}: {e}", rule_name=rule.name) from e

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


def create_rule_engine(memberships: Memberships | None = None) -> RuleEngine:
    """Create a new, empty :class:`RuleEngine`.

    Parameters
    ----------
    memberships : Memberships, optional
        Membership functions to use. Defaults to the shared instance.

    Returns
    -------
    RuleEngine
        An engine without rules; populate it with ``add_rule`` and call
        ``build_rule_systems``.
    """
    return RuleEngine(memberships=memberships)
