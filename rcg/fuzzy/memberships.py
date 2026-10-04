"""
Module defining fuzzy membership functions for RCG categories.

This module provides the Memberships class and factory functions for creating
membership function instances with proper dependency injection support.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum, IntEnum

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from ._lazy import lazy_singleton
from .categories import Catchments, Impervious, LandCover, LandForm, Slope


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

    @staticmethod
    def _add_terms(variable: ctrl.Antecedent | ctrl.Consequent, params: Mapping[Enum, Sequence[float]]) -> None:
        """Add one triangular term per category, named after the enum member."""
        for member, abc in params.items():
            variable[member.name] = fuzz.trimf(variable.universe, list(abc))

    @staticmethod
    def _peaks(enum_cls: type[IntEnum]) -> dict[Enum, tuple[int, int, int]]:
        """Triangles peaking at each member's value: ``[value - 1, value, value + 1]``."""
        return {member: (member.value - 1, member.value, member.value + 1) for member in enum_cls}

    def _populate_land_form(self) -> None:
        """Populate land form memberships with trimf functions."""
        self._add_terms(self.land_form_type, self._peaks(LandForm))

    def _populate_land_cover(self) -> None:
        """Populate land cover memberships with trimf functions."""
        self._add_terms(self.land_cover_type, self._peaks(LandCover))

    def _populate_slope(self) -> None:
        """Populate slope memberships with trimf functions."""
        params: dict[Enum, tuple[float, float, float]] = {
            Slope.marshes_and_lowlands: (0, 0, 1),
            Slope.flats_and_plateaus: (0, 1, 2.5),
            Slope.flats_and_plateaus_in_combination_with_hills: (1, 2.5, 5),
            Slope.hills_with_gentle_slopes: (2.5, 5, 8),
            Slope.steeper_hills_and_foothills: (5, 8, 15),
            Slope.hills_and_outcrops_of_mountain_ranges: (8, 15, 20),
            Slope.higher_hills: (15, 20, 30),
            Slope.mountains: (20, 30, 40),
            Slope.highest_mountains: (30, 50, 60),
        }
        self._add_terms(self.slope, params)

    def _populate_impervious(self) -> None:
        """Populate impervious memberships with trimf functions."""
        params: dict[Enum, tuple[float, float, float]] = {
            Impervious.marshes: (0, 0, 2),
            Impervious.arable: (0, 2, 4),
            Impervious.meadows: (2, 5, 8),
            Impervious.forests: (5, 7, 9),
            Impervious.rural: (7, 11, 15),
            Impervious.suburban_weakly_impervious: (10, 25, 40),
            Impervious.suburban_highly_impervious: (35, 50, 65),
            Impervious.urban_weakly_impervious: (30, 45, 60),
            Impervious.urban_moderately_impervious: (50, 65, 80),
            Impervious.urban_highly_impervious: (75, 85, 100),
            Impervious.mountains_rocky: (20, 40, 60),
            Impervious.mountains_vegetated: (5, 15, 25),
        }
        self._add_terms(self.impervious, params)

    def _populate_catchment(self) -> None:
        """Populate catchment memberships with trimf functions."""
        params: dict[Enum, tuple[float, float, float]] = {
            Catchments.urban: (0, 0, 15),
            Catchments.suburban: (0, 15, 30),
            Catchments.rural: (15, 30, 45),
            Catchments.forests: (30, 45, 60),
            Catchments.meadows: (45, 60, 75),
            Catchments.arable: (60, 75, 90),
            Catchments.mountains: (75, 87, 100),
        }
        self._add_terms(self.catchment, params)


def create_memberships() -> Memberships:
    """
    Factory function to create a new Memberships instance.

    Use this function when you need an isolated memberships instance,
    such as in tests or when you need custom configuration.

    Returns
    -------
    Memberships
        A new Memberships instance with all membership functions populated.

    Example
    -------
    >>> memberships = create_memberships()
    >>> # Use memberships.slope, memberships.impervious, etc.
    """
    return Memberships()


@lazy_singleton
def get_default_memberships() -> Memberships:
    """
    Get the default (shared) Memberships instance.

    This function provides lazy initialization of a shared memberships instance.
    Use this for backward compatibility or when a shared instance is acceptable.

    Returns
    -------
    Memberships
        The shared default Memberships instance.
    """
    return Memberships()
