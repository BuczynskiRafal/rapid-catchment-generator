import copy
import threading
import time

import numpy as np
import pytest
from skfuzzy.control import ControlSystem, ControlSystemSimulation

from rcg.exceptions import FuzzyEngineError
from rcg.fuzzy.categories import Catchments, LandCover, LandForm
from rcg.fuzzy.engine import FuzzyEngine, Prototype, get_default_fuzzy_engine


def test_default_engine_is_shared(engine):
    assert isinstance(engine, FuzzyEngine)
    assert get_default_fuzzy_engine() is engine


def test_control_systems(engine):
    for name in ("slope", "impervious", "catchment"):
        assert isinstance(getattr(engine, f"{name}_ctrl"), ControlSystem)
        assert isinstance(getattr(engine, f"{name}_sim"), ControlSystemSimulation)


@pytest.mark.parametrize("method", ["compute_slope", "compute_impervious", "compute_catchment"])
def test_single_outputs_are_python_floats(engine, method):
    result = getattr(engine, method)(2, 10)
    assert type(result) is float
    assert result > 0


def test_compute_all_matches_single_outputs(engine):
    results = engine.compute_all(4, 11)
    assert set(results) == {"slope", "impervious", "catchment"}
    assert all(type(v) is float for v in results.values())
    assert results["slope"] == pytest.approx(engine.compute_slope(4, 11))
    assert results["impervious"] == pytest.approx(engine.compute_impervious(4, 11))


def test_compute_all_returns_a_copy(engine):
    first = engine.compute_all(2, 6)
    first["slope"] = -1.0
    assert engine.compute_all(2, 6)["slope"] != -1.0


@pytest.mark.parametrize(("land_form", "land_cover"), [(0, 5), (10, 5), (3, 0), (3, 15)])
def test_out_of_range_inputs_raise(engine, land_form, land_cover):
    with pytest.raises(FuzzyEngineError) as info:
        engine.compute_slope(land_form, land_cover)
    assert (info.value.land_form, info.value.land_cover) == (land_form, land_cover)
    assert isinstance(info.value, ValueError)  # 2.0.0 raised ValueError


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, "urban"),
        (15.0, "suburban"),
        (30.0, "rural"),
        (45.0, "forests"),
        (60.0, "meadows"),
        (75.0, "arable"),
        (90.0, "mountains"),
    ],
)
def test_classify_catchment(engine, score, expected):
    assert engine.classify_catchment(score) == expected


def test_classify_returns_known_type(engine):
    score = engine.compute_catchment(LandForm.flats_and_plateaus, LandCover.rural)
    assert engine.classify_catchment(score) in Catchments.get_all_categories()


def _second_engine(engine):
    """Another FuzzyEngine on the same default graphs, without the seconds-long build.

    Separate engines built from the default memberships and rules share skfuzzy's
    rule graph; only their simulations differ. Reusing the built control systems
    reproduces exactly that sharing.
    """
    other = copy.copy(engine)
    other.slope_sim = ControlSystemSimulation(engine.slope_ctrl)
    other.impervious_sim = ControlSystemSimulation(engine.impervious_ctrl)
    other.catchment_sim = ControlSystemSimulation(engine.catchment_ctrl)
    other._results = {}
    return other


def test_all_engines_share_one_lock(engine):
    other = _second_engine(engine)
    assert "_lock" not in vars(engine)
    assert engine._lock is other._lock is FuzzyEngine._lock


def test_concurrent_computations_on_two_engines_agree(engine, monkeypatch):
    other = _second_engine(engine)
    pairs = [(f, c) for f in range(1, 10) for c in (1, 12)]
    expected = {p: engine.compute_slope(*p) for p in pairs}
    results: dict = {}

    # skfuzzy stores inputs on the shared antecedents under the key 'current' before
    # computing; a short pause there lets another engine overwrite them unless one
    # lock serialises all engines (per-engine locks mix inputs reliably this way).
    original_compute = ControlSystemSimulation.compute

    def slow_compute(sim):
        time.sleep(0.002)
        return original_compute(sim)

    monkeypatch.setattr(ControlSystemSimulation, "compute", slow_compute)

    def work(eng, chunk):
        for p in chunk:
            results[(id(eng), p)] = eng.compute_slope(*p)

    # Two threads per engine, each engine over all pairs: the engines always interleave.
    threads = [threading.Thread(target=work, args=(eng, pairs[i::2])) for eng in (engine, other) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == 2 * len(pairs)
    for (_, p), value in results.items():
        assert value == expected[p], p


def test_prototype_legacy_wrapper(engine):
    proto = Prototype(LandForm.flats_and_plateaus, LandCover.rural, engine=engine)
    assert 0 < proto.slope_result < 100
    assert 0 < proto.impervious_result < 100
    assert 0 < proto.catchment_result < 100
    assert proto.get_linguistic(proto.catchment_result) == engine.classify_catchment(proto.catchment_result)


def test_create_fuzzy_engine_is_deprecated(monkeypatch):
    from rcg.fuzzy import engine as engine_module

    built = []
    monkeypatch.setattr(engine_module, "FuzzyEngine", lambda **kwargs: built.append(kwargs) or "engine")
    with pytest.warns(DeprecationWarning, match="FuzzyEngine"):
        assert engine_module.create_fuzzy_engine() == "engine"
    assert built == [{"memberships": None, "rule_engine": None}]


# ===========================================================================
# WP2.2: Strict int type validation & cache bypass prevention (F-12 / N-3)
# ===========================================================================


@pytest.mark.parametrize(
    ("land_form", "land_cover"),
    [
        (True, 1),
        (False, 1),
        (1, True),
        (1, False),
        (True, True),
        (False, False),
    ],
)
def test_validation_rejects_bools(engine, land_form, land_cover):
    """Bools must be strictly rejected even though bool subclasses int in Python."""
    with pytest.raises(FuzzyEngineError) as exc_info:
        engine.compute_all(land_form, land_cover)
    assert isinstance(exc_info.value, ValueError)
    assert "must be an integer" in str(exc_info.value)
    assert "bool" in str(exc_info.value)

    # Verify single output methods also reject bools
    with pytest.raises(FuzzyEngineError):
        engine.compute_slope(land_form, land_cover)


@pytest.mark.parametrize(
    ("land_form", "land_cover"),
    [
        (1.0, 1),
        (1, 1.0),
        (1.5, 6),
        (2, 6.7),
        (9.1, 1),
        (1, 14.1),
        (float("nan"), 1),
        (1, float("inf")),
    ],
)
def test_validation_rejects_floats(engine, land_form, land_cover):
    """Floats (whole, fractional, NaN, inf) must be strictly rejected."""
    with pytest.raises(FuzzyEngineError) as exc_info:
        engine.compute_all(land_form, land_cover)
    assert isinstance(exc_info.value, ValueError)
    assert "must be an integer" in str(exc_info.value)
    assert "float" in str(exc_info.value)


@pytest.mark.parametrize(
    ("land_form", "land_cover"),
    [
        ("1", 1),
        (1, "1"),
        ("flats_and_plateaus", 1),
        (None, 1),
        (1, None),
        ([1], 1),
        (1, (1,)),
    ],
)
def test_validation_rejects_strings_and_none(engine, land_form, land_cover):
    """Strings, None, and collection types must be strictly rejected."""
    with pytest.raises(FuzzyEngineError) as exc_info:
        engine.compute_all(land_form, land_cover)
    assert isinstance(exc_info.value, ValueError)
    assert "must be an integer" in str(exc_info.value)


def test_validation_runs_before_cache_lookup():
    """Invalid types must be rejected even after valid entries are cached.

    Prior to F-12/N-3, compute_all looked up self._results[(int(lf), int(lc))]
    before validating, allowing True, 1.0, 1.9, '1', and 9.1 to retrieve cached
    results if (1, 1) or (9, 1) was already computed.
    """
    engine = FuzzyEngine()
    # Pre-populate cache with valid integers
    res11 = engine.compute_all(1, 1)
    res91 = engine.compute_all(9, 1)
    assert (1, 1) in engine._results
    assert (9, 1) in engine._results

    # Bools: True casts to 1, but must raise
    with pytest.raises(FuzzyEngineError, match="must be an integer.*bool"):
        engine.compute_all(True, 1)
    with pytest.raises(FuzzyEngineError, match="must be an integer.*bool"):
        engine.compute_all(1, True)
    with pytest.raises(FuzzyEngineError, match="must be an integer.*bool"):
        engine.compute_all(True, True)

    # Floats: 1.0, 1.9, 9.1 cast to 1 or 9, but must raise
    with pytest.raises(FuzzyEngineError, match="must be an integer.*float"):
        engine.compute_all(1.0, 1)
    with pytest.raises(FuzzyEngineError, match="must be an integer.*float"):
        engine.compute_all(1.9, 1.9)
    with pytest.raises(FuzzyEngineError, match="must be an integer.*float"):
        engine.compute_all(9.1, 1.0)

    # Strings: '1' casts to 1, but must raise
    with pytest.raises(FuzzyEngineError, match="must be an integer.*str"):
        engine.compute_all("1", 1)
    with pytest.raises(FuzzyEngineError, match="must be an integer.*str"):
        engine.compute_all("1", "1")

    # Verify cache content was not corrupted
    assert engine.compute_all(1, 1) == res11
    assert engine.compute_all(9, 1) == res91


def test_validation_accepts_valid_integers_and_numpy_scalars(engine):
    """Python ints, IntEnum, and NumPy integer scalars must be accepted."""
    # Standard Python int
    res_int = engine.compute_all(2, 7)
    assert res_int["catchment"] == pytest.approx(5.0)

    # IntEnum
    res_enum = engine.compute_all(LandForm.flats_and_plateaus, LandCover.urban_highly_impervious)
    assert res_enum == res_int

    # NumPy integer scalar types
    res_np64 = engine.compute_all(np.int64(2), np.int64(7))
    assert res_np64 == res_int

    res_np32 = engine.compute_all(np.int32(2), np.int32(7))
    assert res_np32 == res_int

    res_np8 = engine.compute_all(np.int8(2), np.uint8(7))
    assert res_np8 == res_int


# ===========================================================================
# WP2.3: Custom memberships propagation (F-13)
# ===========================================================================


def test_custom_memberships_propagates_to_rule_engine():
    """F-13: Passing custom memberships must compile rules bound to that instance."""
    from rcg.fuzzy.memberships import create_memberships

    custom_memberships = create_memberships()

    engine = FuzzyEngine(memberships=custom_memberships)

    assert engine.memberships is custom_memberships
    assert engine.rule_engine._get_memberships() is custom_memberships
    assert engine._is_static is False
    res = engine.compute_all(1, 1)
    assert "slope" in res


# ===========================================================================
# WP2.4: Single outputs delegation & cache reuse (F-25)
# ===========================================================================


def test_single_outputs_delegate_to_compute_all_and_cache():
    """F-25: compute_slope/impervious/catchment must delegate to compute_all and reuse cache."""
    engine = FuzzyEngine()
    assert (2, 5) not in engine._results

    # First call delegates to compute_all, populating all 3 values in _results
    slope = engine.compute_slope(2, 5)
    assert (2, 5) in engine._results
    cached_entry = engine._results[(2, 5)]
    assert cached_entry["slope"] == slope

    # Subsequent single calls read from the same cache
    imperv = engine.compute_impervious(2, 5)
    assert imperv == cached_entry["impervious"]

    catchment = engine.compute_catchment(2, 5)
    assert catchment == cached_entry["catchment"]

    # Verify no recursion error even on fresh unprimed engine
    fresh_engine = FuzzyEngine()
    assert fresh_engine.compute_slope(3, 8) > 0
    assert fresh_engine.compute_impervious(3, 8) > 0
    assert fresh_engine.compute_catchment(3, 8) > 0


# ===========================================================================
# WP2.5: Static table vs dynamic FIS engine equivalence (F-11)
# ===========================================================================


def test_static_table_matches_fis_engine():
    """F-11: Verify STATIC_TABLE matches the full dynamic FIS engine for all 126 combinations."""
    from rcg.fuzzy._static_table import STATIC_TABLE

    engine = FuzzyEngine()
    engine._ensure_dynamic()
    engine._is_static = False

    for land_form in range(1, 10):
        for land_cover in range(1, 15):
            key = (land_form, land_cover)
            assert key in STATIC_TABLE, f"Missing key {key} in STATIC_TABLE"
            expected_slope, expected_imperv, expected_catchment, expected_type = STATIC_TABLE[key]

            actual = engine.compute_all(land_form, land_cover)
            actual_type = engine.classify_catchment(actual["catchment"])

            assert actual["slope"] == pytest.approx(expected_slope, rel=1e-5), f"Slope mismatch at {key}"
            assert actual["impervious"] == pytest.approx(expected_imperv, rel=1e-5), f"Impervious mismatch at {key}"
            assert actual["catchment"] == pytest.approx(expected_catchment, rel=1e-5), f"Catchment score mismatch at {key}"
            assert actual_type == expected_type, f"Catchment type mismatch at {key}"


def test_rule_34_flats_urban_highly_impervious(engine):
    """F-01: Rule 34 (flats_and_plateaus + urban_highly_impervious) must be classified as urban."""
    result = engine.compute_all(2, 7)
    assert result["catchment"] == pytest.approx(5.0)
    assert engine.classify_catchment(result["catchment"]) == "urban"


# ===========================================================================
# WP2.6: State mutation cache invalidation & dynamic transitions
# ===========================================================================


def test_simulation_setter_invalidates_cache_and_forces_dynamic():
    """Setting a simulation switches engine to dynamic mode and clears memoized results."""
    from unittest.mock import MagicMock

    engine = FuzzyEngine()
    initial_res = engine.compute_all(1, 1)
    assert (1, 1) in engine._results
    assert engine._is_static is True

    mock_sim = MagicMock()
    mock_sim.input = {}
    mock_sim.output = {"slope": 99.9}
    engine.slope_sim = mock_sim

    assert engine._is_static is False
    assert len(engine._results) == 0

    recomputed = engine.compute_all(1, 1)
    assert recomputed["slope"] == pytest.approx(99.9)
    assert recomputed["slope"] != initial_res["slope"]


def test_memberships_setter_recompiles_rules_and_invalidates_cache():
    """Assigning new memberships recompiles rule engine, invalidates cache, and updates FIS outputs."""
    import skfuzzy as fuzz

    from rcg.fuzzy.memberships import create_memberships

    engine = FuzzyEngine()
    res_static = engine.compute_all(1, 1)
    assert (1, 1) in engine._results
    assert engine._is_static is True

    custom = create_memberships()
    # Shift marshes_and_lowlands triangle peak from 0.0 to 20.0
    custom.slope["marshes_and_lowlands"] = fuzz.trimf(custom.slope.universe, [10, 20, 30])
    engine.memberships = custom

    assert engine._is_static is False
    assert len(engine._results) == 0
    assert engine.rule_engine._get_memberships() is custom

    res_dynamic_11 = engine.compute_all(1, 1)
    res_dynamic_12 = engine.compute_all(1, 2)

    assert res_dynamic_11["slope"] == pytest.approx(20.0, rel=1e-3)
    assert res_dynamic_11["slope"] != pytest.approx(res_static["slope"])
    assert res_dynamic_12["slope"] == pytest.approx(20.0, rel=1e-3)


def test_control_system_setter_switches_to_dynamic_and_invalidates_cache():
    """Assigning a control system switches engine to dynamic mode and clears memoized results."""
    from skfuzzy import control as ctrl

    engine = FuzzyEngine()
    engine.compute_all(1, 1)
    assert (1, 1) in engine._results
    assert engine._is_static is True

    custom_ctrl = ctrl.ControlSystem(engine.rule_engine.slope_rules)
    engine.slope_ctrl = custom_ctrl

    assert engine._is_static is False
    assert len(engine._results) == 0
    assert engine.slope_ctrl is custom_ctrl
    assert engine._slope_sim is None

    sim = engine.slope_sim
    assert sim is not None
    assert engine._slope_sim is sim

    recomputed = engine.compute_all(1, 1)
    assert (1, 1) in engine._results
    assert "slope" in recomputed


def test_rule_engine_setter_switches_to_dynamic_and_invalidates_cache():
    """Assigning a rule engine switches engine to dynamic mode and clears memoized results."""
    from rcg.fuzzy.rule_definitions import get_default_rules

    engine = FuzzyEngine()
    engine.compute_all(1, 1)
    assert (1, 1) in engine._results
    assert engine._is_static is True

    custom_rules = get_default_rules()
    engine.rule_engine = custom_rules

    assert engine._is_static is False
    assert len(engine._results) == 0
    assert engine.rule_engine is custom_rules
    assert engine._slope_ctrl is None
    assert engine._slope_sim is None
