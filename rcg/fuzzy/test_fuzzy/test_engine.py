import unittest
from skfuzzy.control import ControlSystem, ControlSystemSimulation
from rcg.fuzzy import categories
from rcg.fuzzy.engine import FuzzyEngine, Prototype
from rcg.fuzzy.memberships import membership


class TestFuzzyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FuzzyEngine()

    def test_slope_simulation_ctrl(self):
        self.assertIsNotNone(self.engine.slope_simulation_ctrl)
        self.assertIsInstance(self.engine.slope_simulation_ctrl, ControlSystem)

    def test_impervious_simulation_ctrl(self):
        self.assertIsNotNone(self.engine.impervious_simulation_ctrl)
        self.assertIsInstance(self.engine.impervious_simulation_ctrl, ControlSystem)

    def test_catchment_simulation_ctrl(self):
        self.assertIsNotNone(self.engine.catchment_simulation_ctrl)
        self.assertIsInstance(self.engine.catchment_simulation_ctrl, ControlSystem)

    def test_compute_slope_simulation(self):
        self.assertIsNotNone(self.engine.slope_simulation)
        self.assertIsInstance(self.engine.slope_simulation, ControlSystemSimulation)

    def test_compute_impervious_simulation(self):
        self.assertIsNotNone(self.engine.impervious_simulation)
        self.assertIsInstance(
            self.engine.impervious_simulation, ControlSystemSimulation
        )

    def test_compute_catchment_simulation(self):
        self.assertIsNotNone(self.engine.catchment_simulation)
        self.assertIsInstance(self.engine.catchment_simulation, ControlSystemSimulation)

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

    def test_get_populate(self):
        self.assertIsNotNone(
            Prototype.get_populate(
                result=self.prototype.slope_result, member=membership.slope
            )
        )
        self.assertIsNotNone(
            Prototype.get_populate(
                result=self.prototype.impervious_result, member=membership.impervious
            )
        )
        self.assertIsNotNone(
            Prototype.get_populate(
                result=self.prototype.catchment_result, member=membership.catchment
            )
        )

        self.assertIsInstance(
            Prototype.get_populate(
                result=self.prototype.slope_result, member=membership.slope
            ),
            str,
        )
        self.assertIsInstance(
            Prototype.get_populate(
                result=self.prototype.impervious_result, member=membership.impervious
            ),
            str,
        )
        self.assertIsInstance(
            Prototype.get_populate(
                result=self.prototype.catchment_result, member=membership.catchment
            ),
            str,
        )

    def tearDown(self) -> None:
        del self.prototype
