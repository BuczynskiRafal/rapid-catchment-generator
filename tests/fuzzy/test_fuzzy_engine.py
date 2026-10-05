import copy
import threading
import time

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
