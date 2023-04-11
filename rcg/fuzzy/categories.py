"""The module contains classes specified in the RCG divided into categories. """
from abc import ABC
from typing import List


class Categories(ABC):
    """
    Categories is an abstract base class that defines the interface for a category.
    """

    def __init__(self) -> None:
        """Initialize a Categories object with predefined category attributes as strings."""
        self.marshes_and_lowlands = "marshes_and_lowlands"
        self.flats_and_plateaus = "flats_and_plateaus"
        self.flats_and_plateaus_in_combination_with_hills = (
            "flats_and_plateaus_in_combination_with_hills"
        )
        self.hills_with_gentle_slopes = "hills_with_gentle_slopes"
        self.steeper_hills_and_foothills = "steeper_hills_and_foothills"
        self.hills_and_outcrops_of_mountain_ranges = (
            "hills_and_outcrops_of_mountain_ranges"
        )
        self.higher_hills = "higher_hills"
        self.mountains = "mountains"
        self.highest_mountains = "highest_mountains"


class LandForm:
    """
    LandForm is a class representing various categories of land use types.

    Enum Attributes:
        - marshes_and_lowlands (int): Numeric value for marshes and lowlands land use type.
        - flats_and_plateaus (int): Numeric value for flats and plateaus land use type.
        - flats_and_plateaus_in_combination_with_hills (int): Numeric value
          for flats and plateaus in combination with hills land use type.
        - hills_with_gentle_slopes (int): Numeric value for hills with gentle slopes land use type.
        - steeper_hills_and_foothills (int): Numeric value for steeper
          hills and foothills land use type.
        - hills_and_outcrops_of_mountain_ranges (int): Numeric value
          for hills and outcrops of mountain ranges land use type.
        - higher_hills (int): Numeric value for higher hills land use type.
        - mountains (int): Numeric value for mountains land use type.
        - highest_mountains (int): Numeric value for highest mountains land use type.
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

    def __init__(self) -> None:
        """Initialize a LandForm object with predefined land use types as string attributes."""
        self.marshes_and_lowlands = "marshes_and_lowlands"
        self.flats_and_plateaus = "flats_and_plateaus"
        self.flats_and_plateaus_in_combination_with_hills = (
            "flats_and_plateaus_in_combination_with_hills"
        )
        self.hills_with_gentle_slopes = "hills_with_gentle_slopes"
        self.steeper_hills_and_foothills = "steeper_hills_and_foothills"
        self.hills_and_outcrops_of_mountain_ranges = (
            "hills_and_outcrops_of_mountain_ranges"
        )
        self.higher_hills = "higher_hills"
        self.mountains = "mountains"
        self.highest_mountains = "highest_mountains"

    def __str__(self) -> str:
        """
        Returns a string representation of the LandForm object.
        """
        return (
            f"{self.marshes_and_lowlands} {self.flats_and_plateaus} "
            f"{self.flats_and_plateaus_in_combination_with_hills} {self.hills_with_gentle_slopes} "
            f"{self.steeper_hills_and_foothills} {self.hills_and_outcrops_of_mountain_ranges} "
            f"{self.higher_hills} {self.mountains} {self.highest_mountains}"
        )

    def get_all_categories(self) -> List[str]:
        """
        Returns a list of all land form types.

        Returns:
            - List[str]: A list of strings representing all land form types.
        """
        return [
            self.marshes_and_lowlands,
            self.flats_and_plateaus,
            self.flats_and_plateaus_in_combination_with_hills,
            self.hills_with_gentle_slopes,
            self.steeper_hills_and_foothills,
            self.hills_and_outcrops_of_mountain_ranges,
            self.higher_hills,
            self.mountains,
            self.highest_mountains,
        ]


class LandCover:
    """
    LandCover is a class representing various categories of land cover types.

    Class attributes are used for returning numeric values for the fuzzy engine, while attributes
    defined in the __init__ method return string values for each land cover type.

    Class Attributes:
        - medium_conditions (int): Numeric value for medium conditions land cover type.
        - permeable_areas (int): Numeric value for permeable areas land cover type.
        - permeable_terrain_on_plains (int): Numeric value for permeable terrain on plains land cover type.
        - hilly (int): Numeric value for hilly land cover type.
        - mountains (int): Numeric value for mountains land cover type.
        - bare_rocky_slopes (int): Numeric value for bare rocky slopes land cover type.
        - urban (int): Numeric value for urban land cover type.
        - suburban (int): Numeric value for suburban land cover type.
        - rural (int): Numeric value for rural land cover type.
        - forests (int): Numeric value for forests land cover type.
        - meadows (int): Numeric value for meadows land cover type.
        - arable (int): Numeric value for arable land cover type.
        - marshes (int): Numeric value for marshes land cover type.

    Attributes:
        - medium_conditions (str): Medium conditions land cover type.
        - permeable_areas (str): Permeable areas land cover type.
        - permeable_terrain_on_plains (str): Permeable terrain on plains land cover type.
        - hilly (str): Hilly land cover type.
        - mountains (str): Mountains land cover type.
        - bare_rocky_slopes (str): Bare rocky slopes land cover type.
        - urban (str): Urban land cover type.
        - suburban (str): Suburban land cover type.
        - rural (str): Rural land cover type.
        - forests (str): Forests land cover type.
        - meadows (str): Meadows land cover type.
        - arable (str): Arable land cover type.
        - marshes (str): Marshes land cover type.
    """

    medium_conditions = 1
    permeable_areas = 2
    permeable_terrain_on_plains = 3
    hilly = 4
    mountains = 5
    bare_rocky_slopes = 6
    urban = 7
    suburban = 8
    rural = 9
    forests = 10
    meadows = 11
    arable = 12
    marshes = 13

    def __init__(self) -> None:
        """Initialize a LandCover object with predefined land cover types as string attributes."""
        self.medium_conditions = "medium_conditions"
        self.permeable_areas = "permeable_areas"
        self.permeable_terrain_on_plains = "permeable_terrain_on_plains"
        self.hilly = "hilly"
        self.mountains = "mountains"
        self.bare_rocky_slopes = "bare_rocky_slopes"
        self.urban = "urban"
        self.suburban = "suburban"
        self.rural = "rural"
        self.forests = "forests"
        self.meadows = "meadows"
        self.arable = "arable"
        self.marshes = "marshes"

    def __str__(self) -> str:
        """Return a string representation of the LandCover object."""
        return (
            f"{self.medium_conditions}: {self.medium_conditions}"
            f"\n{self.permeable_areas}: {self.permeable_areas}"
            f"\n{self.permeable_terrain_on_plains}: {self.permeable_terrain_on_plains}"
            f"\n{self.hilly}: {self.hilly}"
            f"\n{self.mountains}: {self.mountains}"
            f"\n{self.bare_rocky_slopes}: {self.bare_rocky_slopes}"
            f"\n{self.urban}: {self.urban}"
            f"\n{self.suburban}: {self.suburban}"
            f"\n{self.rural}: {self.rural}"
            f"\n{self.forests}: {self.forests}"
            f"\n{self.meadows}: {self.meadows}"
            f"\n{self.arable}: {self.arable}"
            f"\n{self.marshes}: {self.marshes}"
        )

    def get_all_categories(self) -> List[str]:
        """
        Returns a list of all land cover types.

        Returns:
            - List[str]: A list of strings representing all land cover types.
        """
        return [
            self.medium_conditions,
            self.permeable_areas,
            self.permeable_terrain_on_plains,
            self.hilly,
            self.mountains,
            self.bare_rocky_slopes,
            self.urban,
            self.suburban,
            self.rural,
            self.forests,
            self.meadows,
            self.arable,
            self.marshes,
        ]


class Slope:
    """
    Slope is a class representing various categories of land slope types.

    Attributes:
        - marshes_and_lowlands (str): Marshes and lowlands land slope type.
        - flats_and_plateaus (str): Flats and plateaus land slope type.
        - flats_and_plateaus_in_combination_with_hills (str): Flats and plateaus in combination with hills land slope type.
        - hills_with_gentle_slopes (str): Hills with gentle slopes land slope type.
        - steeper_hills_and_foothills (str): Steeper hills and foothills land slope type.
        - hills_and_outcrops_of_mountain_ranges (str): Hills and outcrops of mountain ranges land slope type.
        - higher_hills (str): Higher hills land slope type.
        - mountains (str): Mountains land slope type.
        - highest_mountains (str): Highest mountains land slope type.
    """

    def __init__(self) -> None:
        """
        Initializes a Slope object with predefined land slope types as string attributes.
        """
        self.marshes_and_lowlands = "marshes_and_lowlands"
        self.flats_and_plateaus = "flats_and_plateaus"
        self.flats_and_plateaus_in_combination_with_hills = (
            "flats_and_plateaus_in_combination_with_hills"
        )
        self.hills_with_gentle_slopes = "hills_with_gentle_slopes"
        self.steeper_hills_and_foothills = "steeper_hills_and_foothills"
        self.hills_and_outcrops_of_mountain_ranges = (
            "hills_and_outcrops_of_mountain_ranges"
        )
        self.higher_hills = "higher_hills"
        self.mountains = "mountains"
        self.highest_mountains = "highest_mountains"

    def __str__(self) -> str:
        """
        Returns a string representation of the land slope types.
        """
        return f"{self.marshes_and_lowlands}, {self.flats_and_plateaus}, {self.flats_and_plateaus_in_combination_with_hills}, {self.hills_with_gentle_slopes}, {self.steeper_hills_and_foothills}, {self.hills_and_outcrops_of_mountain_ranges}, {self.higher_hills}, {self.mountains}, {self.highest_mountains}"

    def get_all_categories(self) -> List[str]:
        """
        Returns a list of all land slope types.

        Returns:
            - List[str]: A list of strings representing all land slope types.
        """
        return [
            self.marshes_and_lowlands,
            self.flats_and_plateaus,
            self.flats_and_plateaus_in_combination_with_hills,
            self.hills_with_gentle_slopes,
            self.steeper_hills_and_foothills,
            self.hills_and_outcrops_of_mountain_ranges,
            self.higher_hills,
            self.mountains,
            self.highest_mountains,
        ]


class Impervious:
    """
    Impervious is a class representing various categories of land impervious types.

    Attributes:
        - marshes (str): Marsh land impervious type.
        - arable (str): Arable land impervious type.
        - meadows (str): Meadow land impervious type.
        - forests (str): Forest land impervious type.
        - rural (str): Rural land impervious type.
        - suburban (str): Suburban land impervious type.
        - urban (str): Urban land impervious type.
        - mountains (str): Mountain land impervious type.
        - hilly (str): Hilly land impervious type.
    """

    def __init__(self) -> None:
        """
        Initializes an Impervious object with predefined land impervious types as string attributes.
        """
        self.marshes = "marshes"
        self.arable = "arable"
        self.meadows = "meadows"
        self.forests = "forests"
        self.rural = "rural"
        self.suburban = "suburban"
        self.urban = "urban"
        self.mountains = "mountains"
        self.hilly = "hilly"

    def __str__(self) -> str:
        """
        Returns a string representation of the impervious types.
        """
        return f"{self.marshes}, {self.arable}, {self.meadows}, {self.forests}, {self.rural}, {self.suburban}, {self.urban}, {self.mountains}, {self.hilly}"

    def get_all_categories(self) -> List[str]:
        """
        Returns a dictionary containing all impervious type attributes as key-value pairs.

        Returns:
            - List[str]: A list of strings representing all Impervious types.
        """
        return [
            self.marshes,
            self.arable,
            self.meadows,
            self.forests,
            self.rural,
            self.suburban,
            self.urban,
            self.mountains,
            self.hilly,
        ]


class Catchments:
    """
    The Catchments class represents different types of catchment categories
    that can be found within a catchment area.

    Attributes:
        - urban (str): Urban catchment type.
        - suburban (str): Suburban catchment type.
        - rural (str): Rural catchment type.
        - forests (str): Forest catchment type.
        - meadows (str): Meadow catchment type.
        - arable (str): Arable catchment type.
        - mountains (str): Mountain catchment type.
    """

    def __init__(self) -> None:
        """
        Initializes a Catchments object with predefined catchment types as string attributes.
        """
        self.urban = "urban"
        self.suburban = "suburban"
        self.rural = "rural"
        self.forests = "forests"
        self.meadows = "meadows"
        self.arable = "arable"
        self.mountains = "mountains"

    def __str__(self) -> str:
        return f"{self.urban}, {self.suburban}, {self.rural}, {self.forests}, {self.meadows}, {self.arable}, {self.mountains}"

    def get_all_categories(self) -> List[str]:
        """
        Returns a list of all available catchment types in the Catchments object.

        Returns:
            - List[str]: A list of strings representing all catchment types.
        """
        return [
            self.urban,
            self.suburban,
            self.rural,
            self.forests,
            self.meadows,
            self.arable,
            self.mountains,
        ]


land_form = LandForm()
land_cover = LandCover()
slope_ctgr = Slope()
impervious_ctgr = Impervious()
catchment_ctgr = Catchments()
