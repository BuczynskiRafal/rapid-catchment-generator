"""
Rule Engine for fuzzy logic rules with clean DSL.

This module provides a clean, readable way to define and execute fuzzy logic rules,
replacing the monolithic rules.py with a more maintainable architecture.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

import skfuzzy as fuzz
from skfuzzy import control as ctrl
from skfuzzy.control import Antecedent, Consequent, Rule as SkfuzzyRule

from .categories import LandForm, LandCover, Slope, Impervious, Catchments
from .memberships import membership


@dataclass
class Condition:
    """Represents a single condition in a fuzzy rule."""
    variable: str
    value: Enum

    def to_skfuzzy(self) -> Any:
        """Convert condition to skfuzzy format."""
        if self.variable == "land_form":
            return membership.land_form_type[self.value.name]
        elif self.variable == "land_cover":
            return membership.land_cover_type[self.value.name]
        else:
            raise ValueError(f"Unknown variable: {self.variable}")


@dataclass
class FuzzyRule:
    """Represents a complete fuzzy rule with conditions and consequences."""
    name: str
    conditions: List[Condition]
    consequences: Dict[str, Enum]

    def build_antecedent(self) -> Antecedent:
        """Build the antecedent (IF part) of the rule."""
        if not self.conditions:
            raise ValueError("Rule must have at least one condition")

        skfuzzy_conditions = [cond.to_skfuzzy() for cond in self.conditions]
        antecedent = skfuzzy_conditions[0]
        for condition in skfuzzy_conditions[1:]:
            antecedent = antecedent & condition
        return antecedent

    def get_consequence(self, output_type: str) -> Optional[Consequent]:
        """Get the consequence for a specific output type."""
        if output_type not in self.consequences:
            return None

        consequence_value = self.consequences[output_type]

        if output_type == "slope":
            return membership.slope[consequence_value.value]
        elif output_type == "impervious":
            return membership.impervious[consequence_value.value]
        elif output_type == "catchment":
            return membership.catchment[consequence_value.value]
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
        self.conditions: List[Condition] = []
        self.consequences: Dict[str, Enum] = {}
        self.rule_name: str = ""

    def named(self, name: str) -> 'RuleBuilder':
        """Set the name of the rule."""
        self.rule_name = name
        return self

    def when(self, **conditions) -> 'RuleBuilder':
        """Add conditions to the rule."""
        for variable, value in conditions.items():
            if not isinstance(value, Enum):
                raise ValueError(f"Condition value must be an Enum, got {type(value)}")
            self.conditions.append(Condition(variable, value))
        return self

    def then(self, **consequences) -> 'RuleBuilder':
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
    """Main rule engine that manages and executes fuzzy rules."""
    def __init__(self):
        self.rules: List[FuzzyRule] = []
        self._rule_systems: Dict[str, List[SkfuzzyRule]] = {
            "slope": [],
            "impervious": [],
            "catchment": []
        }

    def add_rule(self, rule: FuzzyRule) -> None:
        """Add a fuzzy rule to the engine."""
        self.rules.append(rule)

    def build_rule_systems(self) -> None:
        """Build skfuzzy control systems from the defined rules."""
        self._rule_systems = {k: [] for k in self._rule_systems}  # Clear existing

        for rule in self.rules:
            antecedent = rule.build_antecedent()
            for output_type in self._rule_systems.keys():
                consequent = rule.get_consequence(output_type)
                if consequent:
                    skfuzzy_rule = ctrl.Rule(antecedent=antecedent, consequent=consequent)
                    self._rule_systems[output_type].append(skfuzzy_rule)

    @property
    def slope_rules(self) -> List[SkfuzzyRule]:
        """Get rules for slope calculation."""
        return self._rule_systems["slope"]

    @property
    def impervious_rules(self) -> List[SkfuzzyRule]:
        """Get rules for impervious calculation."""
        return self._rule_systems["impervious"]

    @property
    def catchment_rules(self) -> List[SkfuzzyRule]:
        """Get rules for catchment calculation."""
        return self._rule_systems["catchment"]

    def get_rule_count(self) -> Dict[str, int]:
        """Get count of rules for each output type."""
        return {
            "total": len(self.rules),
            **{name: len(rules) for name, rules in self._rule_systems.items()}
        }


def rule(name: str) -> RuleBuilder:
    """Create a new rule builder with the given name."""
    return RuleBuilder().named(name)


# Global rule engine instance
default_engine = RuleEngine()