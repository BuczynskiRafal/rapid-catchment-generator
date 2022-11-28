from abc import ABC


class Categories(ABC):
    """Categories is an abstract base class that defines the interface for a category."""

    def __init__(self):
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


class LandUse:
    """LandUse is a Categories class that has 9 categories of land use type.
    Class attribute is for return numeric value for fuzzy engine.
    Attribute in init return string value categories of land use type.
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

    def __init__(self):
        """Attribute in init return string value categories of land use type."""
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
    """LandType is a categories class that has 13 categories of land form type.
    Class attribute is for return numeric value for fuzzy engine.
    Attribute in init return string value categories of land form type.
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

    def __init__(self):
        """Attribute in init return string value categories of land form type."""
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


class Slope:
    """Slope is a categories class that has 9 categories of land slope type.
    Attribute in init return string value categories of land slope type.
    """

    def __init__(self):
        """Attribute in init return string value categories of land slope type."""
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


class Impervious:
    """Impervious is a categories class that has 9 categories of land impervious type.
    Attribute in init return string value categories of land impervious type.
    """

    def __init__(self):
        """Attribute in init return string value categories of land impervious type."""
        self.marshes = "marshes"
        self.arable = "arable"
        self.meadows = "meadows"
        self.forests = "forests"
        self.rural = "rural"
        self.suburban = "suburban"
        self.urban = "urban"
        self.hilly = "hilly"
        self.mountains = "mountains"


class Catchments:
    """Impervious is a categories class that has 9 categories of land impervious type.
    Attribute in init return string value categories of land impervious type.
    """

    def __init__(self):
        self.urban = "urban"
        self.suburban = "suburban"
        self.rural = "rural"
        self.forests = "forests"
        self.meadows = "meadows"
        self.arable = "arable"
        self.mountains = "mountains"


land_use = LandUse()
land_form = LandForm()
slope_ctgr = Slope()
impervious_ctgr = Impervious()
catchment_ctgr = Catchments()
#
# with open("r", "w") as file:
#     for i in vars(land_use):
#         for s in vars(land_form):
#             file.write(f"(membership.land_use_type[categories.land_use.{i}] & membership.land_form_type[categories.land_form.{s}]) |" + "\n")
