import unittest
from abc import ABC
from fuzzy.categories import (
    Categories,
    LandForm,
    LandCover,
    Slope,
    Impervious,
    Catchments,
)


class TestCategories(unittest.TestCase):
    def setUp(self):
        self.categories = Categories()

    def test_class_inheritance(self):
        self.assertTrue(issubclass(Categories, ABC))

    def test_attributes(self):
        pass

    def test_marshes_and_lowlands(self):
        self.assertTrue(self.categories.marshes_and_lowlands, "marshes_and_lowlands")

    def test_flats_and_plateaus(self):
        self.assertTrue(self.categories.flats_and_plateaus, "flats_and_plateaus")

    def test_flats_and_plateaus_in_combination_with_hills(self):
        self.assertEqual(
            self.categories.flats_and_plateaus_in_combination_with_hills,
            "flats_and_plateaus_in_combination_with_hills",
        )

    def test_hills_with_gentle_slopes(self):
        self.assertTrue(
            self.categories.hills_with_gentle_slopes, "hills_with_gentle_slopes"
        )

    def test_steeper_hills_and_foothills(self):
        self.assertTrue(
            self.categories.steeper_hills_and_foothills, "steeper_hills_and_foothills"
        )

    def test_hills_and_outcrops_of_mountain_ranges(self):
        self.assertTrue(
            self.categories.hills_and_outcrops_of_mountain_ranges,
            "hills_and_outcrops_of_mountain_ranges",
        )

    def test_higher_hills(self):
        self.assertTrue(self.categories.higher_hills, "higher_hills")

    def test_mountains(self):
        self.assertTrue(self.categories.mountains, "mountains")

    def test_highest_mountains(self):
        self.assertTrue(self.categories.highest_mountains, "highest_mountains")

    def tearDown(self) -> None:
        del self.categories


class TestLandUse(unittest.TestCase):
    def setUp(self):
        self.land_form = LandForm()

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

    def test_marshes_and_lowlands(self):
        self.assertEqual(self.land_form.marshes_and_lowlands, "marshes_and_lowlands")

    def test_flats_and_plateaus(self):
        self.assertEqual(self.land_form.flats_and_plateaus, "flats_and_plateaus")

    def test_flats_and_plateaus_in_combination_with_hills(self):
        self.assertEqual(
            self.land_form.flats_and_plateaus_in_combination_with_hills,
            "flats_and_plateaus_in_combination_with_hills",
        )

    def test_hills_with_gentle_slopes(self):
        self.assertEqual(
            self.land_form.hills_with_gentle_slopes, "hills_with_gentle_slopes"
        )

    def test_steeper_hills_and_foothills(self):
        self.assertEqual(
            self.land_form.steeper_hills_and_foothills, "steeper_hills_and_foothills"
        )

    def test_hills_and_outcrops_of_mountain_ranges(self):
        self.assertEqual(
            self.land_form.hills_and_outcrops_of_mountain_ranges,
            "hills_and_outcrops_of_mountain_ranges",
        )

    def test_higher_hills(self):
        self.assertEqual(self.land_form.higher_hills, "higher_hills")

    def test_mountains(self):
        self.assertEqual(self.land_form.mountains, "mountains")

    def test_highest_mountains(self):
        self.assertEqual(self.land_form.highest_mountains, "highest_mountains")


class TestLandForm(unittest.TestCase):
    def setUp(self) -> None:
        self.land_cover = LandCover()

    def test_medium_conditions(self):
        self.assertEqual(self.land_cover.medium_conditions, "medium_conditions")

    def test_permeable_areas(self):
        self.assertEqual(self.land_cover.permeable_areas, "permeable_areas")

    def test_permeable_terrain_on_plains(self):
        self.assertEqual(
            self.land_cover.permeable_terrain_on_plains, "permeable_terrain_on_plains"
        )

    def test_hilly(self):
        self.assertEqual(self.land_cover.hilly, "hilly")

    def test_mountains(self):
        self.assertEqual(self.land_cover.mountains, "mountains")

    def test_bare_rocky_slopes(self):
        self.assertEqual(self.land_cover.bare_rocky_slopes, "bare_rocky_slopes")

    def test_urban(self):
        self.assertEqual(self.land_cover.urban, "urban")

    def test_suburban(self):
        self.assertEqual(self.land_cover.suburban, "suburban")

    def test_rural(self):
        self.assertEqual(self.land_cover.rural, "rural")

    def test_forests(self):
        self.assertEqual(self.land_cover.forests, "forests")

    def test_meadows(self):
        self.assertEqual(self.land_cover.meadows, "meadows")

    def test_arable(self):
        self.assertEqual(self.land_cover.arable, "arable")

    def test_marshes(self):
        self.assertEqual(self.land_cover.marshes, "marshes")


class TestSlope(unittest.TestCase):
    def setUp(self):
        self.slope = Slope()

    def test_marshes_and_lowlands(self):
        self.assertEqual(self.slope.marshes_and_lowlands, "marshes_and_lowlands")

    def test_flats_and_plateaus(self):
        self.assertEqual(self.slope.flats_and_plateaus, "flats_and_plateaus")

    def test_flats_and_plateaus_in_combination_with_hills(self):
        self.assertEqual(
            self.slope.flats_and_plateaus_in_combination_with_hills,
            "flats_and_plateaus_in_combination_with_hills",
        )

    def test_hills_with_gentle_slopes(self):
        self.assertEqual(
            self.slope.hills_with_gentle_slopes, "hills_with_gentle_slopes"
        )

    def test_steeper_hills_and_foothills(self):
        self.assertEqual(
            self.slope.steeper_hills_and_foothills, "steeper_hills_and_foothills"
        )

    def test_hills_and_outcrops_of_mountain_ranges(self):
        self.assertEqual(
            self.slope.hills_and_outcrops_of_mountain_ranges,
            "hills_and_outcrops_of_mountain_ranges",
        )

    def test_higher_hills(self):
        self.assertEqual(self.slope.higher_hills, "higher_hills")

    def test_mountains(self):
        self.assertEqual(self.slope.mountains, "mountains")

    def test_highest_mountains(self):
        self.assertEqual(self.slope.highest_mountains, "highest_mountains")


class TestImpervious(unittest.TestCase):
    def setUp(self):
        self.impervious = Impervious()

    def test_marshes_attribute(self):
        self.assertEqual(self.impervious.marshes, "marshes")

    def test_arable_attribute(self):
        self.assertEqual(self.impervious.arable, "arable")

    def test_meadows_attribute(self):
        self.assertEqual(self.impervious.meadows, "meadows")

    def test_forests_attribute(self):
        self.assertEqual(self.impervious.forests, "forests")

    def test_rural_attribute(self):
        self.assertEqual(self.impervious.rural, "rural")

    def test_suburban_attribute(self):
        self.assertEqual(self.impervious.suburban, "suburban")

    def test_urban_attribute(self):
        self.assertEqual(self.impervious.urban, "urban")

    def test_hilly_attribute(self):
        self.assertEqual(self.impervious.hilly, "hilly")

    def test_mountains_attribute(self):
        self.assertEqual(self.impervious.mountains, "mountains")


class TestCatchments(unittest.TestCase):
    def test_urban(self):
        catchments = Catchments()
        self.assertEqual(catchments.urban, "urban")

    def test_suburban(self):
        catchments = Catchments()
        self.assertEqual(catchments.suburban, "suburban")

    def test_rural(self):
        catchments = Catchments()
        self.assertEqual(catchments.rural, "rural")

    def test_forests(self):
        catchments = Catchments()
        self.assertEqual(catchments.forests, "forests")

    def test_meadows(self):
        catchments = Catchments()
        self.assertEqual(catchments.meadows, "meadows")

    def test_arable(self):
        catchments = Catchments()
        self.assertEqual(catchments.arable, "arable")

    def test_mountains(self):
        catchments = Catchments()
        self.assertEqual(catchments.mountains, "mountains")


if __name__ == "__main__":
    unittest.main()
