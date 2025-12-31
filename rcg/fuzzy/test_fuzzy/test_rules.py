import unittest

from skfuzzy import control as ctrl

from rcg.fuzzy.categories import Catchments, Impervious, LandCover, LandForm, Slope
from rcg.fuzzy.rule_engine import FuzzyRule, default_engine, rule


class TestRuleEngine(unittest.TestCase):
    def test_slope_rules_exist(self):
        self.assertIsInstance(default_engine.slope_rules, list)
        self.assertGreater(len(default_engine.slope_rules), 0)

    def test_slope_rules_are_ctrl_rules(self):
        self.assertIsInstance(default_engine.slope_rules[0], ctrl.Rule)

    def test_impervious_rules_exist(self):
        self.assertIsInstance(default_engine.impervious_rules, list)
        self.assertGreater(len(default_engine.impervious_rules), 0)

    def test_impervious_rules_are_ctrl_rules(self):
        self.assertIsInstance(default_engine.impervious_rules[0], ctrl.Rule)

    def test_catchment_rules_exist(self):
        self.assertIsInstance(default_engine.catchment_rules, list)
        self.assertGreater(len(default_engine.catchment_rules), 0)

    def test_catchment_rules_are_ctrl_rules(self):
        self.assertIsInstance(default_engine.catchment_rules[0], ctrl.Rule)

    def test_rule_count(self):
        counts = default_engine.get_rule_count()
        self.assertIn("total", counts)
        self.assertIn("slope", counts)
        self.assertIn("impervious", counts)
        self.assertIn("catchment", counts)
        self.assertGreater(counts["total"], 50)


class TestRuleBuilder(unittest.TestCase):
    def test_build_simple_rule(self):
        test_rule = (
            rule("test_rule")
            .when(land_form=LandForm.flats_and_plateaus, land_cover=LandCover.rural)
            .then(slope=Slope.flats_and_plateaus, impervious=Impervious.rural, catchment=Catchments.rural)
            .build()
        )
        self.assertIsInstance(test_rule, FuzzyRule)
        self.assertEqual(test_rule.name, "test_rule")
        self.assertEqual(len(test_rule.conditions), 2)

    def test_rule_requires_conditions(self):
        with self.assertRaises(ValueError):
            rule("empty_rule").then(slope=Slope.flats_and_plateaus).build()

    def test_rule_requires_consequences(self):
        with self.assertRaises(ValueError):
            rule("no_consequence").when(land_form=LandForm.mountains).build()


if __name__ == "__main__":
    unittest.main()
