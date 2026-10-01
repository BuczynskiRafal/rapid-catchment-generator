import dataclasses
import json
import os
import re
from pathlib import Path

import pytest

import rcg
from rcg.catchment import ApplyResult, ModelInfo, SubcatchmentParameters
from rcg.exceptions import ModelOperationError, ValidationError
from rcg.fuzzy.categories import LandCover, LandForm
from rcg.service import apply, inspect, preview, warm_up


def test_public_api():
    assert rcg.__version__ == "2.0.0"
    assert rcg.preview is preview
    assert rcg.apply is apply
    assert rcg.warm_up is warm_up
    assert rcg.inspect is inspect
    assert rcg.SubcatchmentParameters is SubcatchmentParameters
    assert rcg.ApplyResult is ApplyResult
    assert rcg.ModelInfo is ModelInfo
    assert rcg.LandForm is LandForm
    assert rcg.LandCover is LandCover
    assert set(rcg.__all__) <= set(dir(rcg))
    with pytest.raises(AttributeError):
        rcg.does_not_exist  # noqa: B018
    assert rcg.service.apply is apply  # submodules stay reachable after a bare `import rcg`


def test_warm_up_returns_the_shared_engine(engine):
    assert warm_up() is engine
    assert warm_up(engine) is engine


def test_preview_values(urban_params):
    p = urban_params
    assert p.land_form is LandForm.flats_and_plateaus
    assert p.land_cover is LandCover.urban_moderately_impervious
    assert p.area_ha == 5.0
    assert p.catchment_type == "urban"
    assert p.width_m == 111.8
    assert (p.n_imperv, p.n_perv) == (0.013, 0.15)
    assert p.s_imperv_mm == pytest.approx(1.27)
    assert p.s_perv_mm == pytest.approx(5.08)
    assert p.pct_zero == 50
    assert dict(p.infiltration) == {"Suction": 3.5, "Ksat": 0.5, "IMD": 0.25, "Param4": 7.0, "Param5": 0.0}


def test_preview_returns_only_builtin_scalars(urban_params):
    for f in dataclasses.fields(urban_params):
        value = getattr(urban_params, f.name)
        if f.name == "infiltration":
            assert all(type(v) is float for v in value.values())
        elif f.name not in ("land_form", "land_cover"):
            assert type(value) in (int, float, str), (f.name, type(value))
    json.dumps(urban_params.to_dict())


def test_preview_accepts_labels_and_enums(engine, urban_params):
    by_label = preview("5", "Flats and plateaus", "Urban, moderately impervious", engine=engine)
    by_enum = preview(5, LandForm.flats_and_plateaus, LandCover.urban_moderately_impervious, engine=engine)
    assert by_label == by_enum == urban_params


def test_preview_area_does_not_change_fuzzy_outputs(engine, urban_params):
    big = preview(500, "flats_and_plateaus", "urban_moderately_impervious", engine=engine)
    assert big.slope_pct == urban_params.slope_pct
    assert big.width_m == 1118.03


@pytest.mark.parametrize(
    ("area", "form", "cover", "field"),
    [
        (0, "flats_and_plateaus", "rural", "area"),
        (20_000, "flats_and_plateaus", "rural", "area"),
        (1, "flatlands", "rural", "land_form"),
        (1, "flats_and_plateaus", "city", "land_cover"),
    ],
)
def test_preview_validates(engine, area, form, cover, field):
    with pytest.raises(ValidationError) as info:
        preview(area, form, cover, engine=engine)
    assert info.value.field == field


def test_apply_single_and_sequence(example_inp, urban_params, forest_params):
    one = apply(example_inp, urban_params, backup=False)
    assert isinstance(one, ApplyResult)
    assert one.subcatchment_ids == ("S16",)
    two = apply(example_inp, (forest_params, urban_params), backup=False)
    assert two.subcatchment_ids == ("S17", "S18")


def test_apply_validates_inputs(example_inp, urban_params, tmp_path):
    with pytest.raises(ValidationError, match="At least one"):
        apply(example_inp, [])
    with pytest.raises(ValidationError, match="SubcatchmentParameters"):
        apply(example_inp, [{"area": 1}])  # type: ignore[list-item]
    with pytest.raises(ValidationError, match="does not exist"):
        apply(tmp_path / "missing.inp", urban_params)
    with pytest.raises(ValidationError, match="Directory does not exist"):
        apply(example_inp, urban_params, output_path=tmp_path / "nope" / "out.inp")
    with pytest.raises(ValidationError, match=r"\.inp"):
        apply(example_inp, urban_params, output_path=tmp_path / "out.txt")


def test_apply_rejects_hand_made_parameters_with_bad_area(example_inp, urban_params):
    with pytest.raises(ValidationError):
        apply(example_inp, dataclasses.replace(urban_params, area_ha=-1.0))


# --------------------------------------------------------------------------- inspect


def test_inspect_example(example_inp):
    info = inspect(example_inp)
    assert info == ModelInfo(
        path=Path(os.path.realpath(example_inp)),
        flow_units="CMS",
        is_metric=True,
        infiltration_method="MODIFIED_GREEN_AMPT",
        subcatchment_count=15,
        raingage="Raingage2",
        outlet="O4",
        size_bytes=example_inp.stat().st_size,
    )
    assert json.loads(json.dumps(info.to_dict()))["path"] == str(info.path)
    with pytest.raises(dataclasses.FrozenInstanceError):
        info.flow_units = "CFS"  # type: ignore[misc]


def test_inspect_predicts_what_apply_uses(example_inp, urban_params):
    info = inspect(example_inp)
    result = apply(example_inp, urban_params, backup=False)
    assert (result.raingage, result.outlet) == (info.raingage, info.outlet)
    assert (result.flow_units, result.infiltration_method) == (info.flow_units, info.infiltration_method)
    assert result.output_path == info.path
    assert inspect(example_inp).subcatchment_count == info.subcatchment_count + 1


def test_inspect_model_without_gage_nodes_and_options(tmp_path):
    path = tmp_path / "bare.inp"
    path.write_text("[TITLE]\nbare\n\n[SUBCATCHMENTS]\ns1 RG O 1 1 1 1 0\nS2 RG O 1 1 1 1 0\n")
    info = inspect(path)
    assert (info.flow_units, info.is_metric, info.infiltration_method) == ("CFS", False, "HORTON")
    assert (info.subcatchment_count, info.raingage, info.outlet) == (2, None, None)


def test_inspect_falls_back_to_the_last_junction(example_inp):
    example_inp.write_text(re.sub(r"(?ims)^\[OUTFALLS\].*?(?=^\[)", "", example_inp.read_text()))
    assert inspect(example_inp).outlet == "J3"


def test_inspect_resolves_symlinks(example_inp, tmp_path):
    link = tmp_path / "link.inp"
    link.symlink_to(example_inp)
    assert inspect(link).path == Path(os.path.realpath(example_inp))


def test_inspect_errors(tmp_path):
    with pytest.raises(ValidationError, match="does not exist"):
        inspect(tmp_path / "missing.inp")
    with pytest.raises(ValidationError, match=r"\.inp"):
        inspect(tmp_path / "model.txt")
    epanet = tmp_path / "net.inp"
    epanet.write_text("[TITLE]\n[JUNCTIONS]\n J1 1\n[PIPES]\n P1 J1 J2 1 1 1\n")
    with pytest.raises(ModelOperationError, match="EPANET"):
        inspect(epanet)
    odd = tmp_path / "odd.inp"
    odd.write_text("[OPTIONS]\nFLOW_UNITS FURLONGS\n")
    with pytest.raises(ModelOperationError, match="FLOW_UNITS"):
        inspect(odd)


def test_apply_validates_every_value(example_inp, urban_params):
    with pytest.raises(ValidationError) as info:
        apply(example_inp, dataclasses.replace(urban_params, n_perv=float("nan")))
    assert info.value.field == "n_perv"
