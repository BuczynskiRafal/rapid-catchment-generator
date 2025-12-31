"""
Module defining fuzzy membership functions for RCG categories.
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from typing import Dict, List

from .categories import LandForm, LandCover, Slope, Impervious, Catchments


class Memberships:
    """
    Class defining fuzzy membership functions for land form, land cover, slope, impervious, and catchment.

    Example:
        memberships = Memberships()
        # Ready to use: memberships.slope, etc.
    """

    def __init__(self) -> None:
        # Define universes and variables
        self.land_form_type = ctrl.Antecedent(np.arange(0, 10, 1), "land_form")
        self.land_cover_type = ctrl.Antecedent(np.arange(0, 15, 1), "land_cover")
        self.slope = ctrl.Consequent(np.arange(0, 61, 1), "slope")
        self.impervious = ctrl.Consequent(np.arange(0, 101, 1), "impervious")
        self.catchment = ctrl.Consequent(np.arange(0, 101, 1), "catchment")

        # Auto-populate all memberships
        self._populate_land_form()
        self._populate_land_cover()
        self._populate_slope()
        self._populate_impervious()
        self._populate_catchment()

    def _populate_land_form(self) -> None:
        """Populate land form memberships with trimf functions."""
        params: Dict[str, List[int]] = {
            "marshes_and_lowlands": [0, 1, 2],
            "flats_and_plateaus": [1, 2, 3],
            "flats_and_plateaus_in_combination_with_hills": [2, 3, 4],
            "hills_with_gentle_slopes": [3, 4, 5],
            "steeper_hills_and_foothills": [4, 5, 6],
            "hills_and_outcrops_of_mountain_ranges": [5, 6, 7],
            "higher_hills": [6, 7, 8],
            "mountains": [7, 8, 9],
            "highest_mountains": [8, 9, 10],
        }
        for name, param in params.items():
            self.land_form_type[name] = fuzz.trimf(self.land_form_type.universe, param)

    def _populate_land_cover(self) -> None:
        """Populate land cover memberships with trimf functions."""
        params: Dict[str, List[int]] = {
            "permeable_areas": [0, 1, 2],
            "permeable_terrain_on_plains": [1, 2, 3],
            "mountains_vegetated": [2, 3, 4],
            "mountains_rocky": [3, 4, 5],
            "urban_weakly_impervious": [4, 5, 6],
            "urban_moderately_impervious": [5, 6, 7],
            "urban_highly_impervious": [6, 7, 8],
            "suburban_weakly_impervious": [7, 8, 9],
            "suburban_highly_impervious": [8, 9, 10],
            "rural": [9, 10, 11],
            "forests": [10, 11, 12],
            "meadows": [11, 12, 13],
            "arable": [12, 13, 14],
            "marshes": [13, 14, 15],
        }
        for name, param in params.items():
            self.land_cover_type[name] = fuzz.trimf(self.land_cover_type.universe, param)

    def _populate_slope(self) -> None:
        """Populate slope memberships with trimf functions."""
        params: Dict[str, List[float]] = {
            "marshes_and_lowlands": [0, 0, 1],
            "flats_and_plateaus": [0, 1, 2.5],
            "flats_and_plateaus_in_combination_with_hills": [1, 2.5, 5],
            "hills_with_gentle_slopes": [2.5, 5, 8],
            "steeper_hills_and_foothills": [5, 8, 15],
            "hills_and_outcrops_of_mountain_ranges": [8, 15, 20],
            "higher_hills": [15, 20, 30],
            "mountains": [20, 30, 40],
            "highest_mountains": [30, 50, 60],
        }
        for name, param in params.items():
            self.slope[name] = fuzz.trimf(self.slope.universe, param)

    def _populate_impervious(self) -> None:
        """Populate impervious memberships with trimf functions."""
        params: Dict[str, List[int]] = {
            "marshes": [0, 0, 2],
            "arable": [0, 2, 4],
            "meadows": [2, 5, 8],
            "forests": [5, 7, 9],
            "rural": [7, 11, 15],
            "suburban_weakly_impervious": [10, 25, 40],
            "suburban_highly_impervious": [35, 50, 65],
            "urban_weakly_impervious": [30, 45, 60],
            "urban_moderately_impervious": [50, 65, 80],
            "urban_highly_impervious": [75, 85, 100],
            "mountains_rocky": [20, 40, 60],
            "mountains_vegetated": [5, 15, 25],
        }
        for name, param in params.items():
            self.impervious[name] = fuzz.trimf(self.impervious.universe, param)

    def _populate_catchment(self) -> None:
        """Populate catchment memberships with trimf functions."""
        params: Dict[str, List[int]] = {
            "urban": [0, 0, 15],
            "suburban": [0, 15, 30],
            "rural": [15, 30, 45],
            "forests": [30, 45, 60],
            "meadows": [45, 60, 75],
            "arable": [60, 75, 90],
            "mountains": [75, 87, 100],
        }
        for name, param in params.items():
            self.catchment[name] = fuzz.trimf(self.catchment.universe, param)


membership = Memberships()
