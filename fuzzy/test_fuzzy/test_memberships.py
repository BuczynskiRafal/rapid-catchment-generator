import unittest

from skfuzzy import control as ctrl
from fuzzy.memberships import Memberships
from fuzzy.categories import LandForm, LandCover, Slope, Impervious, Catchments


class TestMemberships(unittest.TestCase):
    def setUp(self):
        self.memberships = Memberships()
        self.memberships.populate_land_use()
        self.memberships.populate_land_form()
        self.memberships.populate_slope()
        self.memberships.populate_impervious()
        self.memberships.populate_catchment()

    def test_membership_has_attributes(self):
        self.assertIsNotNone(self.memberships.land_form_type)
        self.assertIsNotNone(self.memberships.land_cover_type)
        self.assertIsNotNone(self.memberships.slope)
        self.assertIsNotNone(self.memberships.impervious)
        self.assertIsNotNone(self.memberships.catchment)

    def test_membership_antecedent(self):
        self.assertIsInstance(self.memberships.land_form_type, ctrl.Antecedent)
        self.assertIsInstance(self.memberships.land_cover_type, ctrl.Antecedent)

    def test_membership_consequent(self):
        self.assertIsInstance(self.memberships.slope, ctrl.Consequent)
        self.assertIsInstance(self.memberships.impervious, ctrl.Consequent)
        self.assertIsInstance(self.memberships.catchment, ctrl.Consequent)

    def test_memberships_labels(self):
        self.assertEqual(self.memberships.land_form_type.label, "land_form")
        self.assertEqual(self.memberships.land_cover_type.label, "land_cover")
        self.assertEqual(self.memberships.slope.label, "slope")
        self.assertEqual(self.memberships.impervious.label, "impervious")
        self.assertEqual(self.memberships.catchment.label, "catchment")

    def test_membership_populate_land_use(self):
        land_use_list = list(vars(LandForm()))
        self.assertIsNotNone(self.memberships.land_form_type)
        self.assertIsNotNone(self.memberships.land_form_type.universe)
        self.assertEqual(list(self.memberships.land_form_type.terms), land_use_list)

    def test_membership_populate_land_form(self):
        land_form_list = list(vars(LandCover()))
        self.assertIsNotNone(self.memberships.land_cover_type)
        self.assertIsNotNone(self.memberships.land_cover_type.universe)
        self.assertEqual(list(self.memberships.land_cover_type.terms), land_form_list)

    def test_membership_populate_slope(self):
        slope_list = list(vars(Slope()))
        self.assertIsNotNone(self.memberships.slope)
        self.assertIsNotNone(self.memberships.slope.universe)
        self.assertEqual(list(self.memberships.slope.terms), slope_list)

    def test_membership_populate_impervious(self):
        impervious_list = list(vars(Impervious()))
        self.assertIsNotNone(self.memberships.impervious)
        self.assertIsNotNone(self.memberships.impervious.universe)
        self.assertEqual(list(self.memberships.impervious.terms), impervious_list)

    def test_membership_populate_catchment(self):
        catchment_list = list(vars(Catchments()))
        self.assertIsNotNone(self.memberships.catchment)
        self.assertIsNotNone(self.memberships.catchment.universe)
        self.assertEqual(list(self.memberships.catchment.terms), catchment_list)

    def tearDown(self) -> None:
        del self.memberships


if __name__ == "__main__":
    unittest.main()
