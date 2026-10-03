"""End to end: preview -> apply on a copy of rcg/example.inp -> reload with swmmio -> run SWMM."""

import re

import pytest
import swmmio

import rcg

pyswmm = pytest.importorskip("pyswmm")


def test_apply_then_simulate(example_inp, engine):
    params = [
        rcg.preview(5.5, "flats_and_plateaus", "urban_moderately_impervious", engine=engine),
        rcg.preview(12, "Hills with gentle slopes", "Meadows", engine=engine),
    ]
    result = rcg.apply(example_inp, params)

    model = swmmio.Model(str(example_inp))
    for sid in result.subcatchment_ids:
        assert sid in model.inp.subcatchments.index
        assert sid in model.inp.subareas.index
        assert sid in model.inp.infiltration.index
        assert sid in model.inp.polygons.index

    with pyswmm.Simulation(str(example_inp)) as sim:
        subcatchments = pyswmm.Subcatchments(sim)
        ids = {s.subcatchmentid for s in subcatchments}
        assert set(result.subcatchment_ids) <= ids
        new = subcatchments[result.subcatchment_ids[0]]
        assert new.area == pytest.approx(5.5)
        peak = 0.0
        for _ in sim:
            peak = max(peak, new.runoff)
    assert peak > 0
    assert result.backup_path is not None and result.backup_path.exists()


def test_us_units_and_horton_model_runs_in_swmm(example_inp, engine):
    """A CFS + HORTON model gets acres, feet, inches and a Horton row that SWMM accepts."""
    text = example_inp.read_text()
    text = text.replace("FLOW_UNITS           CMS", "FLOW_UNITS           CFS")
    text = text.replace("INFILTRATION         MODIFIED_GREEN_AMPT", "INFILTRATION         HORTON")
    # Existing rows must be valid for the model's method, too.
    text = re.sub(r"(?m)^(S\d+)\s+3\.5\s+0\.5\s+0\.25\s+7\s+0\s*$", r"\1    3   0.5   4   7   0", text)
    example_inp.write_text(text)

    params = rcg.preview(5.5, "flats_and_plateaus", "urban_moderately_impervious", engine=engine)
    result = rcg.apply(example_inp, params, backup=False)
    assert (result.flow_units, result.infiltration_method) == ("CFS", "HORTON")
    sid = result.subcatchment_ids[0]

    with pyswmm.Simulation(str(example_inp)) as sim:
        new = pyswmm.Subcatchments(sim)[sid]
        assert new.area == pytest.approx(5.5 * 2.4710538, abs=1e-6)  # acres
        assert new.width == pytest.approx(params.width_m * 3.2808399, abs=0.01)  # feet
        for _ in sim:
            pass
        stats = new.statistics
    assert stats["runoff"] > 0
    assert stats["infiltration"] > 0
