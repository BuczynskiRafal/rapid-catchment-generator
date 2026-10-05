"""Deprecated 1.x entry point kept for backward compatibility.

Use :func:`rcg.preview` and :func:`rcg.apply` instead::

    import rcg

    rcg.apply("model.inp", rcg.preview(5.0, "flats_and_plateaus", "urban_moderately_impervious"))
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path

from rcg.catchment import ApplyResult
from rcg.config import load_defaults
from rcg.fuzzy.categories import LandCover, LandForm

__all__ = ["BuildCatchments", "ModelParameters"]


def _manning() -> dict[str, tuple[float, float]]:
    return dict(load_defaults().manning_coefficients)


def _storage() -> dict[str, tuple[float, float, int]]:
    return dict(load_defaults().depression_storage)


def _infiltration() -> dict[str, float]:
    return dict(load_defaults().infiltration)


@dataclass
class ModelParameters:
    """Default SWMM parameters per catchment type, read from ``defaults.json``.

    Attributes
    ----------
    manning_coefficients : dict[str, tuple[float, float]]
        ``(n_imperv, n_perv)`` per catchment type.
    depression_storage : dict[str, tuple[float, float, int]]
        ``(s_imperv_in, s_perv_in, pct_zero)`` per catchment type (depths in inches).
    infiltration_defaults : dict[str, float]
        Green-Ampt parameters.
    """

    manning_coefficients: dict[str, tuple[float, float]] = field(default_factory=_manning)
    depression_storage: dict[str, tuple[float, float, int]] = field(default_factory=_storage)
    infiltration_defaults: dict[str, float] = field(default_factory=_infiltration)


class BuildCatchments:
    """Deprecated: add subcatchments to a SWMM model file.

    Parameters
    ----------
    file_path : str or Path
        SWMM ``.inp`` file, updated in place.
    backup : bool, optional
        Keep a timestamped backup before each write (default ``True``).

    .. deprecated:: 2.0
        Use :func:`rcg.preview` and :func:`rcg.apply`.
    """

    def __init__(self, file_path: str | Path, backup: bool = True) -> None:
        warnings.warn(
            "BuildCatchments is deprecated; use rcg.preview() and rcg.apply() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.file_path = Path(file_path)
        self.backup_enabled = backup
        self.parameters = ModelParameters()
        self.last_result: ApplyResult | None = None

    def add_subcatchment(self, area: float, land_form: LandForm | str, land_cover: LandCover | str) -> ApplyResult:
        """Compute and append one subcatchment.

        Parameters
        ----------
        area : float
            Area in hectares.
        land_form : LandForm or str
            Land form (enum, snake_case name or human label).
        land_cover : LandCover or str
            Land cover (enum, snake_case name or human label).

        Returns
        -------
        ApplyResult
            What was written.
        """
        from rcg.service import apply, preview

        self.last_result = apply(self.file_path, preview(area, land_form, land_cover), backup=self.backup_enabled)
        return self.last_result
