"""Fuzzy inference engine for SWMM subcatchment parameters.

The engine maps a land form and a land cover to a terrain slope, a percentage of
impervious surface and a catchment score that is classified into a catchment type.
A precompiled static table is used for standard lookups, while dynamic ``skfuzzy``
control systems are compiled lazily if custom memberships or rules are supplied.
"""

from __future__ import annotations

import os
import threading
import warnings
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np

# scikit-fuzzy imports matplotlib.pyplot; never let it pick (or probe) a GUI backend.
os.environ.setdefault("MPLBACKEND", "Agg")

from rcg.exceptions import FuzzyEngineError  # noqa: E402
from rcg.fuzzy._lazy import lazy_singleton  # noqa: E402
from rcg.fuzzy._static_table import STATIC_TABLE  # noqa: E402
from rcg.fuzzy.categories import LandCover, LandForm  # noqa: E402

if TYPE_CHECKING:
    from skfuzzy import control as ctrl

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
    """

    _lock: ClassVar[threading.RLock] = threading.RLock()
    """Serialises computations of every engine."""

    def __init__(
        self,
        memberships: Memberships | None = None,
        rule_engine: RuleEngine | None = None,
    ) -> None:
        self._results: dict[tuple[int, int], dict[str, float]] = {}
        self._slope_ctrl: ctrl.ControlSystem | None = None
        self._impervious_ctrl: ctrl.ControlSystem | None = None
        self._catchment_ctrl: ctrl.ControlSystem | None = None
        self._slope_sim: ctrl.ControlSystemSimulation | None = None
        self._impervious_sim: ctrl.ControlSystemSimulation | None = None
        self._catchment_sim: ctrl.ControlSystemSimulation | None = None

        if memberships is None and rule_engine is None:
            self._is_static: bool = True
            self._memberships: Memberships | None = None
            self._rule_engine: RuleEngine | None = None
        else:
            self._is_static = False
            from rcg.fuzzy.memberships import get_default_memberships

            default_memberships = get_default_memberships()
            if memberships is None:
                memberships = default_memberships
            self._memberships = memberships

            if rule_engine is None:
                if memberships is default_memberships:
                    from rcg.fuzzy.rule_definitions import get_default_rules

                    rule_engine = get_default_rules()
                    self._is_static = True
                else:
                    from rcg.fuzzy.rule_definitions import define_all_rules
                    from rcg.fuzzy.rule_engine import RuleEngine

                    rule_engine = define_all_rules(RuleEngine(memberships=memberships))
            self._rule_engine = rule_engine

    def _is_dynamic_ready(self) -> bool:
        return None not in (
            self._slope_ctrl,
            self._impervious_ctrl,
            self._catchment_ctrl,
            self._slope_sim,
            self._impervious_sim,
            self._catchment_sim,
        )

    def _reset_dynamic(self, *, clear_controls: bool = False) -> None:
        self._is_static = False
        if clear_controls:
            self._slope_ctrl = None
            self._impervious_ctrl = None
            self._catchment_ctrl = None
            self._slope_sim = None
            self._impervious_sim = None
            self._catchment_sim = None
        self._results.clear()

    @property
    def memberships(self) -> Memberships:
        if self._memberships is None:
            from rcg.fuzzy.memberships import get_default_memberships

            self._memberships = get_default_memberships()
        return self._memberships

    @memberships.setter
    def memberships(self, value: Memberships) -> None:
        with self._lock:
            self._memberships = value
            from rcg.fuzzy.rule_definitions import define_all_rules
            from rcg.fuzzy.rule_engine import RuleEngine

            self._rule_engine = define_all_rules(RuleEngine(memberships=value))
            self._reset_dynamic(clear_controls=True)

    @property
    def rule_engine(self) -> RuleEngine:
        if self._rule_engine is None:
            from rcg.fuzzy.rule_definitions import get_default_rules

            self._rule_engine = get_default_rules()
        return self._rule_engine

    @rule_engine.setter
    def rule_engine(self, value: RuleEngine) -> None:
        with self._lock:
            self._rule_engine = value
            if hasattr(value, "_get_memberships"):
                self._memberships = value._get_memberships()
            self._reset_dynamic(clear_controls=True)

    def _ensure_dynamic(self) -> None:
        if self._is_dynamic_ready():
            return
        with self._lock:
            if self._is_dynamic_ready():
                return
            from skfuzzy import control as ctrl

            rule_eng = self.rule_engine

            if self._slope_ctrl is None:
                self._slope_ctrl = ctrl.ControlSystem(rule_eng.slope_rules)
            if self._impervious_ctrl is None:
                self._impervious_ctrl = ctrl.ControlSystem(rule_eng.impervious_rules)
            if self._catchment_ctrl is None:
                self._catchment_ctrl = ctrl.ControlSystem(rule_eng.catchment_rules)

            if self._slope_sim is None:
                self._slope_sim = ctrl.ControlSystemSimulation(self._slope_ctrl)
            if self._impervious_sim is None:
                self._impervious_sim = ctrl.ControlSystemSimulation(self._impervious_ctrl)
            if self._catchment_sim is None:
                self._catchment_sim = ctrl.ControlSystemSimulation(self._catchment_ctrl)

    @property
    def slope_ctrl(self) -> ctrl.ControlSystem:
        if self._slope_ctrl is None:
            self._ensure_dynamic()
        assert self._slope_ctrl is not None
        return self._slope_ctrl

    @slope_ctrl.setter
    def slope_ctrl(self, value: ctrl.ControlSystem) -> None:
        with self._lock:
            self._slope_ctrl = value
            self._slope_sim = None
            self._reset_dynamic()

    @property
    def impervious_ctrl(self) -> ctrl.ControlSystem:
        if self._impervious_ctrl is None:
            self._ensure_dynamic()
        assert self._impervious_ctrl is not None
        return self._impervious_ctrl

    @impervious_ctrl.setter
    def impervious_ctrl(self, value: ctrl.ControlSystem) -> None:
        with self._lock:
            self._impervious_ctrl = value
            self._impervious_sim = None
            self._reset_dynamic()

    @property
    def catchment_ctrl(self) -> ctrl.ControlSystem:
        if self._catchment_ctrl is None:
            self._ensure_dynamic()
        assert self._catchment_ctrl is not None
        return self._catchment_ctrl

    @catchment_ctrl.setter
    def catchment_ctrl(self, value: ctrl.ControlSystem) -> None:
        with self._lock:
            self._catchment_ctrl = value
            self._catchment_sim = None
            self._reset_dynamic()

    @property
    def slope_sim(self) -> ctrl.ControlSystemSimulation:
        if self._slope_sim is None:
            self._ensure_dynamic()
        assert self._slope_sim is not None
        return self._slope_sim

    @slope_sim.setter
    def slope_sim(self, value: ctrl.ControlSystemSimulation) -> None:
        with self._lock:
            self._slope_sim = value
            self._reset_dynamic()

    @property
    def impervious_sim(self) -> ctrl.ControlSystemSimulation:
        if self._impervious_sim is None:
            self._ensure_dynamic()
        assert self._impervious_sim is not None
        return self._impervious_sim

    @impervious_sim.setter
    def impervious_sim(self, value: ctrl.ControlSystemSimulation) -> None:
        with self._lock:
            self._impervious_sim = value
            self._reset_dynamic()

    @property
    def catchment_sim(self) -> ctrl.ControlSystemSimulation:
        if self._catchment_sim is None:
            self._ensure_dynamic()
        assert self._catchment_sim is not None
        return self._catchment_sim

    @catchment_sim.setter
    def catchment_sim(self, value: ctrl.ControlSystemSimulation) -> None:
        with self._lock:
            self._catchment_sim = value
            self._reset_dynamic()

    def compute_slope(self, land_form: int, land_cover: int) -> float:
        """Return the terrain slope in percent for the given category values."""
        return self.compute_all(land_form, land_cover)["slope"]

    def compute_impervious(self, land_form: int, land_cover: int) -> float:
        """Return the impervious surface share in percent for the given category values."""
        return self.compute_all(land_form, land_cover)["impervious"]

    def compute_catchment(self, land_form: int, land_cover: int) -> float:
        """Return the raw catchment score (0-100) for the given category values."""
        return self.compute_all(land_form, land_cover)["catchment"]

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
        self._validate_inputs(land_form, land_cover)
        key = (int(land_form), int(land_cover))
        with self._lock:
            if key not in self._results:
                if self._is_static:
                    slope, imperv, catchment, _ = STATIC_TABLE[key]
                    self._results[key] = {
                        "slope": slope,
                        "impervious": imperv,
                        "catchment": catchment,
                    }
                else:
                    self._ensure_dynamic()
                    self._results[key] = {
                        "slope": self._compute_single(self.slope_sim, land_form, land_cover, self.memberships.slope.label),
                        "impervious": self._compute_single(
                            self.impervious_sim, land_form, land_cover, self.memberships.impervious.label
                        ),
                        "catchment": self._compute_single(
                            self.catchment_sim, land_form, land_cover, self.memberships.catchment.label
                        ),
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
        if self._is_static:
            if 0.0 <= score <= 7.5:
                return "urban"
            if 7.5 < score <= 22.5:
                return "suburban"
            if 22.5 < score <= 37.5:
                return "rural"
            if 37.5 < score <= 52.5:
                return "forests"
            if 52.5 < score <= 67.5:
                return "meadows"
            if 67.5 < score <= 245.0 / 3.0:
                return "arable"
            if 245.0 / 3.0 < score < 100.0:
                return "mountains"
            return "urban"

        self._ensure_dynamic()
        import skfuzzy as fuzz

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
    def _validate_inputs(land_form: Any, land_cover: Any) -> None:
        if isinstance(land_form, bool) or not isinstance(land_form, (int, np.integer)):
            valid_lc = (
                int(land_cover) if isinstance(land_cover, (int, np.integer)) and not isinstance(land_cover, bool) else None
            )
            raise FuzzyEngineError(
                f"land_form must be an integer (1-{len(LandForm)}), got {type(land_form).__name__}: {land_form!r}",
                land_form=None,
                land_cover=valid_lc,
            )
        if isinstance(land_cover, bool) or not isinstance(land_cover, (int, np.integer)):
            raise FuzzyEngineError(
                f"land_cover must be an integer (1-{len(LandCover)}), got {type(land_cover).__name__}: {land_cover!r}",
                land_form=int(land_form),
                land_cover=None,
            )
        lf = int(land_form)
        lc = int(land_cover)
        if not (1 <= lf <= len(LandForm)):
            raise FuzzyEngineError(
                f"Invalid land_form: {land_form}. Must be 1-{len(LandForm)}",
                land_form=lf,
                land_cover=lc,
            )
        if not (1 <= lc <= len(LandCover)):
            raise FuzzyEngineError(
                f"Invalid land_cover: {land_cover}. Must be 1-{len(LandCover)}",
                land_form=lf,
                land_cover=lc,
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
    slope_result : float
        Defuzzified slope output in percent.
    impervious_result : float
        Defuzzified impervious surface share in percent.
    catchment_result : float
        Defuzzified catchment score (0-100).
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

    .. deprecated:: 2.1
        Call ``FuzzyEngine(memberships=..., rule_engine=...)`` directly.

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
    warnings.warn("create_fuzzy_engine is deprecated; call FuzzyEngine(...) instead", DeprecationWarning, stacklevel=2)
    return FuzzyEngine(memberships=memberships, rule_engine=rule_engine)


@lazy_singleton
def get_default_fuzzy_engine() -> FuzzyEngine:
    """Return the shared engine, building it on first use (thread-safe)."""
    return FuzzyEngine()
