"""The module contains classes specified in the RCG divided into categories."""

from enum import Enum, IntEnum


class LandForm(IntEnum):
    """
    Land form categories with integer values.

    Defines terrain types from 1-9 representing different topographic features
    from flat lowlands to highest mountains.
    """

    marshes_and_lowlands = 1
    flats_and_plateaus = 2
    flats_and_plateaus_in_combination_with_hills = 3
    hills_with_gentle_slopes = 4
    steeper_hills_and_foothills = 5
    hills_and_outcrops_of_mountain_ranges = 6
    higher_hills = 7
    mountains = 8
    highest_mountains = 9

    @classmethod
    def get_all_categories(cls) -> list[str]:
        """
        Return list of all land form names.

        Returns
        -------
        List[str]
            List of all available land form category names
        """
        return [member.name for member in cls]


class LandCover(IntEnum):
    """
    Land cover categories with integer values.

    Defines surface cover types from 1-14 representing different
    land use and vegetation characteristics affecting runoff.
    """

    permeable_areas = 1
    permeable_terrain_on_plains = 2
    mountains_vegetated = 3
    mountains_rocky = 4
    urban_weakly_impervious = 5
    urban_moderately_impervious = 6
    urban_highly_impervious = 7
    suburban_weakly_impervious = 8
    suburban_highly_impervious = 9
    rural = 10
    forests = 11
    meadows = 12
    arable = 13
    marshes = 14

    @classmethod
    def get_all_categories(cls) -> list[str]:
        """Return list of all land cover names."""
        return [member.name for member in cls]


class Slope(Enum):
    """Slope categories."""

    marshes_and_lowlands = "marshes_and_lowlands"
    flats_and_plateaus = "flats_and_plateaus"
    flats_and_plateaus_in_combination_with_hills = "flats_and_plateaus_in_combination_with_hills"
    hills_with_gentle_slopes = "hills_with_gentle_slopes"
    steeper_hills_and_foothills = "steeper_hills_and_foothills"
    hills_and_outcrops_of_mountain_ranges = "hills_and_outcrops_of_mountain_ranges"
    higher_hills = "higher_hills"
    mountains = "mountains"
    highest_mountains = "highest_mountains"

    @classmethod
    def get_all_categories(cls) -> list[str]:
        """Return list of all slope types."""
        return [member.value for member in cls]


class Impervious(Enum):
    """Impervious surface categories."""

    marshes = "marshes"
    arable = "arable"
    meadows = "meadows"
    forests = "forests"
    rural = "rural"
    suburban_weakly_impervious = "suburban_weakly_impervious"
    suburban_highly_impervious = "suburban_highly_impervious"
    urban_weakly_impervious = "urban_weakly_impervious"
    urban_moderately_impervious = "urban_moderately_impervious"
    urban_highly_impervious = "urban_highly_impervious"
    mountains_rocky = "mountains_rocky"
    mountains_vegetated = "mountains_vegetated"

    @classmethod
    def get_all_categories(cls) -> list[str]:
        """Return list of all impervious types."""
        return [member.value for member in cls]


class Catchments(Enum):
    """Catchment categories."""

    urban = "urban"
    suburban = "suburban"
    rural = "rural"
    forests = "forests"
    meadows = "meadows"
    arable = "arable"
    mountains = "mountains"

    @classmethod
    def get_all_categories(cls) -> list[str]:
        """Return list of all catchment types."""
        return [member.value for member in cls]


land_form = LandForm
land_cover = LandCover
slope_ctgr = Slope
impervious_ctgr = Impervious
catchment_ctgr = Catchments
