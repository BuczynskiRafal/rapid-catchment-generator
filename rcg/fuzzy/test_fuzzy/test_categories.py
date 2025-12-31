import unittest
from rcg.fuzzy.categories import (
    LandForm,
    LandCover,
    Slope,
    Impervious,
    Catchments,
)


class TestLandForm(unittest.TestCase):
    def test_is_int_enum(self):
        self.assertEqual(int(LandForm.marshes_and_lowlands), 1)

    def test_marshes_and_lowlands_value(self):
        self.assertEqual(LandForm.marshes_and_lowlands, 1)

    def test_flats_and_plateaus_value(self):
        self.assertEqual(LandForm.flats_and_plateaus, 2)

    def test_flats_and_plateaus_in_combination_with_hills_value(self):
        self.assertEqual(LandForm.flats_and_plateaus_in_combination_with_hills, 3)

    def test_hills_with_gentle_slopes_value(self):
        self.assertEqual(LandForm.hills_with_gentle_slopes, 4)

    def test_steeper_hills_and_foothills_value(self):
        self.assertEqual(LandForm.steeper_hills_and_foothills, 5)

    def test_hills_and_outcrops_of_mountain_ranges_value(self):
        self.assertEqual(LandForm.hills_and_outcrops_of_mountain_ranges, 6)

    def test_higher_hills_value(self):
        self.assertEqual(LandForm.higher_hills, 7)

    def test_mountains_value(self):
        self.assertEqual(LandForm.mountains, 8)

    def test_highest_mountains_value(self):
        self.assertEqual(LandForm.highest_mountains, 9)

    def test_get_all_categories(self):
        categories = LandForm.get_all_categories()
        self.assertEqual(len(categories), 9)
        self.assertIn("marshes_and_lowlands", categories)
        self.assertIn("highest_mountains", categories)


class TestLandCover(unittest.TestCase):
    def test_permeable_areas_value(self):
        self.assertEqual(LandCover.permeable_areas, 1)

    def test_urban_highly_impervious_value(self):
        self.assertEqual(LandCover.urban_highly_impervious, 7)

    def test_marshes_value(self):
        self.assertEqual(LandCover.marshes, 14)

    def test_get_all_categories(self):
        categories = LandCover.get_all_categories()
        self.assertEqual(len(categories), 14)
        self.assertIn("forests", categories)
        self.assertIn("rural", categories)


class TestSlope(unittest.TestCase):
    def test_marshes_and_lowlands(self):
        self.assertEqual(Slope.marshes_and_lowlands.value, "marshes_and_lowlands")

    def test_highest_mountains(self):
        self.assertEqual(Slope.highest_mountains.value, "highest_mountains")

    def test_get_all_categories(self):
        categories = Slope.get_all_categories()
        self.assertEqual(len(categories), 9)


class TestImpervious(unittest.TestCase):
    def test_marshes(self):
        self.assertEqual(Impervious.marshes.value, "marshes")

    def test_urban_highly_impervious(self):
        self.assertEqual(Impervious.urban_highly_impervious.value, "urban_highly_impervious")

    def test_get_all_categories(self):
        categories = Impervious.get_all_categories()
        self.assertEqual(len(categories), 12)


class TestCatchments(unittest.TestCase):
    def test_urban(self):
        self.assertEqual(Catchments.urban.value, "urban")

    def test_mountains(self):
        self.assertEqual(Catchments.mountains.value, "mountains")

    def test_get_all_categories(self):
        categories = Catchments.get_all_categories()
        self.assertEqual(len(categories), 7)
        self.assertIn("urban", categories)
        self.assertIn("forests", categories)


if __name__ == "__main__":
    unittest.main()
