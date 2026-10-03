"""Shared fixtures for the test-suite.

Building the fuzzy engine takes several seconds, so one engine is shared by the
whole session; tests that write files work on temporary copies of the models.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_INP = REPO_ROOT / "rcg" / "example.inp"
LEGACY_INP = Path(__file__).resolve().parent / "inp_manage" / "test_file.inp"


@pytest.fixture(scope="session")
def engine():
    """The shared default :class:`~rcg.fuzzy.engine.FuzzyEngine` (built once per session)."""
    from rcg.fuzzy.engine import get_default_fuzzy_engine

    return get_default_fuzzy_engine()


@pytest.fixture(scope="session")
def urban_params(engine):
    """Parameters of a 5 ha urban subcatchment on flats."""
    from rcg.service import preview

    return preview(5.0, "flats_and_plateaus", "urban_moderately_impervious", engine=engine)


@pytest.fixture(scope="session")
def forest_params(engine):
    """Parameters of a 2.5 ha forest subcatchment in the mountains."""
    from rcg.service import preview

    return preview(2.5, "mountains", "forests", engine=engine)


@pytest.fixture
def example_inp(tmp_path: Path) -> Path:
    """A writable copy of ``rcg/example.inp`` in a fresh temporary directory."""
    target = tmp_path / "example.inp"
    shutil.copy2(EXAMPLE_INP, target)
    return target


@pytest.fixture
def legacy_inp(tmp_path: Path) -> Path:
    """A writable copy of a 1.x-written model (duplicate ``[POLYGONS]`` section included)."""
    target = tmp_path / "legacy.inp"
    shutil.copy2(LEGACY_INP, target)
    return target


@pytest.fixture(scope="session")
def golden_preview(engine) -> Callable:
    """Return ``preview(land_form, land_cover) -> dict`` bound to the shared engine.

    This indirection is the single place the golden test touches the production API,
    so the API can evolve without rewriting the test.
    """
    from rcg.service import preview

    def _preview(land_form, land_cover) -> dict:
        p = preview(5.0, land_form, land_cover, engine=engine)
        return {
            "slope": p.slope_pct,
            "impervious": p.impervious_pct,
            "catchment": p.catchment_score,
            "catchment_type": p.catchment_type,
            "n_imperv": p.n_imperv,
            "n_perv": p.n_perv,
            "s_imperv": p.s_imperv_mm,
            "s_perv": p.s_perv_mm,
            "pct_zero": p.pct_zero,
        }

    return _preview


@pytest.fixture(scope="session")
def golden_width() -> Callable[[float], float]:
    """Return the characteristic-width formula used when writing [SUBCATCHMENTS]."""
    from rcg.catchment import width_m

    return width_m
