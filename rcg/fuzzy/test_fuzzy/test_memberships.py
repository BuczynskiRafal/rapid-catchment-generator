import unittest

from skfuzzy import control as ctrl

from rcg.fuzzy.memberships import Memberships, membership


class TestMemberships(unittest.TestCase):
    def setUp(self):
        self.memberships = Memberships()

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

    def test_membership_land_form_terms(self):
        terms = list(self.memberships.land_form_type.terms)
        self.assertEqual(len(terms), 9)
        self.assertIn("marshes_and_lowlands", terms)
        self.assertIn("highest_mountains", terms)

    def test_membership_land_cover_terms(self):
        terms = list(self.memberships.land_cover_type.terms)
        self.assertEqual(len(terms), 14)
        self.assertIn("forests", terms)
        self.assertIn("urban_highly_impervious", terms)

    def test_membership_slope_terms(self):
        terms = list(self.memberships.slope.terms)
        self.assertEqual(len(terms), 9)

    def test_membership_impervious_terms(self):
        terms = list(self.memberships.impervious.terms)
        self.assertEqual(len(terms), 12)

    def test_membership_catchment_terms(self):
        terms = list(self.memberships.catchment.terms)
        self.assertEqual(len(terms), 7)
        self.assertIn("urban", terms)
        self.assertIn("mountains", terms)

    def test_global_membership_instance(self):
        self.assertIsNotNone(membership)
        self.assertIsInstance(membership, Memberships)

    def tearDown(self) -> None:
        del self.memberships


if __name__ == "__main__":
    unittest.main()
