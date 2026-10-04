"""Fuzzy inference engine for SWMM subcatchment parameters.

The engine maps a land form and a land cover to a terrain slope, a percentage of
impervious surface and a catchment score that is classified into a catchment type.
Building the ``skfuzzy`` control systems takes a few seconds, so a shared default
engine is created lazily by :func:`get_default_fuzzy_engine`.
"""

from __future__ import annotations

import os
import threading
from typing import TYPE_CHECKING, ClassVar

# scikit-fuzzy imports matplotlib.pyplot; never let it pick (or probe) a GUI backend.
os.environ.setdefault("MPLBACKEND", "Agg")

import skfuzzy as fuzz  # noqa: E402
from skfuzzy import control as ctrl  # noqa: E402

from rcg.exceptions import FuzzyEngineError  # noqa: E402
from rcg.fuzzy._lazy import lazy_singleton  # noqa: E402
from rcg.fuzzy.categories import LandCover, LandForm  # noqa: E402

if TYPE_CHECKING:
    from rcg.fuzzy.memberships import Memberships
    from rcg.fuzzy.rule_engine import RuleEngine


class FuzzyEngine:
    """Fuzzy inference engine computing slope, imperviousness and catchment type.

    Instances are safe to share between threads. Every computation holds one lock
    shared by *all* engines: ``skfuzzy`` keeps intermediate results on the
    membership and rule graphs, which separate engines built from the default
    memberships share, so two engines computing at once could mix their inputs.

    Parameters
    ----------
    memberships : Memberships, optional
        Membership functions to use. Defaults to the shared instance.
    rule_engine : RuleEngine, optional
        Rule set to use. Defaults to the rules from ``rule_definitions``.

    Attributes
    ----------
    memberships : Memberships
        Membership functions used for inference.
    slope_sim, impervious_sim, catchment_sim : ctrl.ControlSystemSimulation
        Simulations for the three outputs.
    """

    _lock: ClassVar[threading.RLock] = threading.RLock()
    """Serialises computations of every engine (re-entrant: compute_all calls compute_*)."""

    def __init__(self, memberships: Memberships | None = None, rule_engine: RuleEngine | None = None) -> None:
        if memberships is None:
            from rcg.fuzzy.memberships import get_default_memberships

            memberships = get_default_memberships()
        self.memberships = memberships

        if rule_engine is None:
            from rcg.fuzzy.rule_definitions import get_default_rules

            rule_engine = get_default_rules()

        self.slope_ctrl = ctrl.ControlSystem(rule_engine.slope_rules)
        self.impervious_ctrl = ctrl.ControlSystem(rule_engine.impervious_rules)
        self.catchment_ctrl = ctrl.ControlSystem(rule_engine.catchment_rules)

        self.slope_sim = ctrl.ControlSystemSimulation(self.slope_ctrl)
        self.impervious_sim = ctrl.ControlSystemSimulation(self.impervious_ctrl)
        self.catchment_sim = ctrl.ControlSystemSimulation(self.catchment_ctrl)

        self._results: dict[tuple[int, int], dict[str, float]] = {}

    def compute_slope(self, land_form: int, land_cover: int) -> float:
        """Return the terrain slope in percent for the given category values."""
        return self._compute_single(self.slope_sim, land_form, land_cover, self.memberships.slope.label)

    def compute_impervious(self, land_form: int, land_cover: int) -> float:
        """Return the impervious surface share in percent for the given category values."""
        return self._compute_single(self.impervious_sim, land_form, land_cover, self.memberships.impervious.label)

    def compute_catchment(self, land_form: int, land_cover: int) -> float:
        """Return the raw catchment score (0-100) for the given category values."""
        return self._compute_single(self.catchment_sim, land_form, land_cover, self.memberships.catchment.label)

    def compute_all(self, land_form: int, land_cover: int) -> dict[str, float]:
        """Compute all three outputs.

        Parameters
        ----------
        land_form : int
            Land form category value (1-9).
        land_cover : int
            Land cover category value (1-14).

        Returns
        -------
        dict[str, float]
            ``slope``, ``impervious`` and ``catchment`` results. Results are memoised per
            input pair (inference is deterministic and there are only 126 pairs).
        """
        key = (int(land_form), int(land_cover))
        with self._lock:
            if key not in self._results:
                self._results[key] = {
                    "slope": self.compute_slope(land_form, land_cover),
                    "impervious": self.compute_impervious(land_form, land_cover),
                    "catchment": self.compute_catchment(land_form, land_cover),
                }
            return dict(self._results[key])

    def classify_catchment(self, score: float) -> str:
        """Return the catchment type whose membership is highest for ``score``.

        Parameters
        ----------
        score : float
            Raw catchment score as returned by :meth:`compute_catchment`.

        Returns
        -------
        str
            One of ``urban``, ``suburban``, ``rural``, ``forests``, ``meadows``,
            ``arable`` or ``mountains``. Ties resolve to the first term defined.
        """
        member = self.memberships.catchment
        degrees = {str(key): float(fuzz.interp_membership(member.universe, member[key].mf, score)) for key in member.terms}
        if not degrees:
            raise FuzzyEngineError("Catchment variable has no terms")
        return max(degrees, key=degrees.__getitem__)

    def _compute_single(self, sim: ctrl.ControlSystemSimulation, land_form: int, land_cover: int, output_label: str) -> float:
        self._validate_inputs(land_form, land_cover)
        with self._lock:
            sim.input[self.memberships.land_form_type.label] = int(land_form)
            sim.input[self.memberships.land_cover_type.label] = int(land_cover)
            sim.compute()
            return float(sim.output[output_label])

    @staticmethod
    def _validate_inputs(land_form: int, land_cover: int) -> None:
        if not (1 <= land_form <= len(LandForm)):
            raise FuzzyEngineError(
                f"Invalid land_form: {land_form}. Must be 1-{len(LandForm)}", land_form=land_form, land_cover=land_cover
            )
        if not (1 <= land_cover <= len(LandCover)):
            raise FuzzyEngineError(
                f"Invalid land_cover: {land_cover}. Must be 1-{len(LandCover)}", land_form=land_form, land_cover=land_cover
            )


class Prototype:
    """Legacy wrapper exposing the 1.x result attributes.

    Parameters
    ----------
    land_form : LandForm
        Land form category.
    land_cover : LandCover
        Land cover category.
    engine : FuzzyEngine, optional
        Engine to use. Defaults to the shared engine.

    Attributes
    ----------
    slope_result, impervious_result, catchment_result : float
        Fuzzy outputs.
    """

    def __init__(self, land_form: LandForm, land_cover: LandCover, engine: FuzzyEngine | None = None) -> None:
        self._engine = engine if engine is not None else get_default_fuzzy_engine()
        results = self._engine.compute_all(land_form.value, land_cover.value)
        self.slope_result = results["slope"]
        self.impervious_result = results["impervious"]
        self.catchment_result = results["catchment"]

    def get_linguistic(self, result: float) -> str:
        """Return the catchment type for a raw catchment score."""
        return self._engine.classify_catchment(result)


def create_fuzzy_engine(memberships: Memberships | None = None, rule_engine: RuleEngine | None = None) -> FuzzyEngine:
    """Create a new, independent :class:`FuzzyEngine`.

    Parameters
    ----------
    memberships : Memberships, optional
        Membership functions to use. Defaults to the shared instance.
    rule_engine : RuleEngine, optional
        Rule set to use. Defaults to the rules from ``rule_definitions``.

    Returns
    -------
    FuzzyEngine
        A freshly built engine.
    """
    return FuzzyEngine(memberships=memberships, rule_engine=rule_engine)


@lazy_singleton
def get_default_fuzzy_engine() -> FuzzyEngine:
    """Return the shared engine, building it on first use (thread-safe)."""
    return FuzzyEngine()
