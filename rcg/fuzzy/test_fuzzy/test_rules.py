import unittest
from skfuzzy import control as ctrl
from rcg.fuzzy.rules import slope_rules, impervious_rules, catchment_rules, RulesSet


class TestSlopeRules(unittest.TestCase):
    def setUp(self):
        self.rule_set = RulesSet()
        self.setup_rules = [
            rule for rule in dir(self.rule_set) if rule.startswith("rule")
        ]

    def test_slope_rules(self):
        self.assertIsInstance(slope_rules, list)
        self.assertIsInstance(slope_rules[0], ctrl.Rule)
        self.assertEqual(len(self.setup_rules), len(slope_rules))

    def test_impervious_rules(self):
        self.assertIsInstance(impervious_rules, list)
        self.assertIsInstance(impervious_rules[0], ctrl.Rule)
        self.assertEqual(len(self.setup_rules), len(impervious_rules))

    def test_catchment_rules(self):
        self.assertIsInstance(catchment_rules, list)
        self.assertIsInstance(catchment_rules[0], ctrl.Rule)
        self.assertEqual(len(self.setup_rules), len(catchment_rules))

    def tearDown(self) -> None:
        del self.rule_set
        del self.setup_rules
