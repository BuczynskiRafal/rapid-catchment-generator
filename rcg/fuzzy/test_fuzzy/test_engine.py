import unittest
from skfuzzy.control import ControlSystem, ControlSystemSimulation
from rcg.fuzzy import categories
from rcg.fuzzy.engine import FuzzyEngine, Prototype, create_fuzzy_engine
from rcg.fuzzy.memberships import create_memberships, get_default_memberships


class TestFuzzyEngine(unittest.TestCase):
    def setUp(self):
        # Use default engine for backward compatibility tests
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
        # Use instance method instead of static method
        result = self.prototype.get_linguistic(
            result=self.prototype.catchment_result
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertIn(result, categories.Catchments.get_all_categories())

    def test_get_linguistic_with_custom_member(self):
        # Test with explicit member parameter
        memberships = get_default_memberships()
        result = self.prototype.get_linguistic(
            result=self.prototype.catchment_result,
            member=memberships.catchment
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)


    def tearDown(self) -> None:
        del self.prototype


class TestDependencyInjection(unittest.TestCase):
    """Test dependency injection capabilities."""

    def test_create_fuzzy_engine_with_defaults(self):
        engine = create_fuzzy_engine()
        self.assertIsNotNone(engine)
        self.assertIsNotNone(engine.memberships)

    def test_create_fuzzy_engine_with_custom_memberships(self):
        custom_memberships = create_memberships()
        engine = create_fuzzy_engine(memberships=custom_memberships)
        self.assertEqual(engine.memberships, custom_memberships)

    def test_prototype_with_custom_engine(self):
        custom_engine = create_fuzzy_engine()
        prototype = Prototype(
            land_form=categories.LandForm.flats_and_plateaus,
            land_cover=categories.LandCover.rural,
            engine=custom_engine
        )
        self.assertIsNotNone(prototype.slope_result)


if __name__ == "__main__":
    unittest.main()
