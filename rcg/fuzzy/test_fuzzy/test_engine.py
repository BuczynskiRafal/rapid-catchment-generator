import unittest
from skfuzzy.control import ControlSystem, ControlSystemSimulation
from rcg.fuzzy import categories
from rcg.fuzzy.engine import FuzzyEngine, Prototype
from rcg.fuzzy.memberships import membership


class TestFuzzyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FuzzyEngine()

    def test_slope_ctrl(self):
        self.assertIsNotNone(self.engine.slope_ctrl)
        self.assertIsInstance(self.engine.slope_ctrl, ControlSystem)

    def test_impervious_ctrl(self):
        self.assertIsNotNone(self.engine.impervious_ctrl)
        self.assertIsInstance(self.engine.impervious_ctrl, ControlSystem)

    def test_catchment_ctrl(self):
        self.assertIsNotNone(self.engine.catchment_ctrl)
        self.assertIsInstance(self.engine.catchment_ctrl, ControlSystem)

    def test_slope_sim(self):
        self.assertIsNotNone(self.engine.slope_sim)
        self.assertIsInstance(self.engine.slope_sim, ControlSystemSimulation)

    def test_impervious_sim(self):
        self.assertIsNotNone(self.engine.impervious_sim)
        self.assertIsInstance(self.engine.impervious_sim, ControlSystemSimulation)

    def test_catchment_sim(self):
        self.assertIsNotNone(self.engine.catchment_sim)
        self.assertIsInstance(self.engine.catchment_sim, ControlSystemSimulation)

    def test_compute_slope(self):
        result = self.engine.compute_slope(2, 10)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_compute_impervious(self):
        result = self.engine.compute_impervious(2, 10)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_compute_catchment(self):
        result = self.engine.compute_catchment(2, 10)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_compute_all(self):
        results = self.engine.compute_all(2, 10)
        self.assertIn('slope', results)
        self.assertIn('impervious', results)
        self.assertIn('catchment', results)

    def tearDown(self) -> None:
        del self.engine


class TestPrototype(unittest.TestCase):
    def setUp(self) -> None:
        self.prototype = Prototype(
            land_form=categories.LandForm.flats_and_plateaus,
            land_cover=categories.LandCover.rural,
        )

    def test_slope_result(self):
        self.assertIsNotNone(self.prototype.slope_result)
        self.assertIsInstance(self.prototype.slope_result, float)
        self.assertGreater(self.prototype.slope_result, 0)
        self.assertLess(self.prototype.slope_result, 100)

    def test_impervious_result(self):
        self.assertIsNotNone(self.prototype.impervious_result)
        self.assertIsInstance(self.prototype.impervious_result, float)
        self.assertGreater(self.prototype.impervious_result, 0)
        self.assertLess(self.prototype.impervious_result, 100)

    def test_catchment_result(self):
        self.assertIsNotNone(self.prototype.catchment_result)
        self.assertIsInstance(self.prototype.catchment_result, float)
        self.assertGreater(self.prototype.catchment_result, 0)
        self.assertLess(self.prototype.catchment_result, 100)

    def test_get_linguistic(self):
        result = Prototype.get_linguistic(
            result=self.prototype.catchment_result,
            member=membership.catchment
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertIn(result, categories.Catchments.get_all_categories())

    def tearDown(self) -> None:
        del self.prototype


if __name__ == "__main__":
    unittest.main()
