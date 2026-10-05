"""Units, infiltration method and rain gage interval of the written rows (``[OPTIONS]`` aware)."""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pytest
from swmmio.utils.dataframes import dataframe_from_inp

from rcg.catchment import ACRES_PER_HECTARE, FEET_PER_METRE, INFILTRATION_FIELDS, MM_PER_INCH, infiltration_for
from rcg.exceptions import ModelOperationError, ValidationError
from rcg.inp_manage import writer
from rcg.service import apply

FLOW_UNITS_LINE = "FLOW_UNITS           CMS"
INFILTRATION_LINE = "INFILTRATION         MODIFIED_GREEN_AMPT"


def set_options(path: Path, *, flow_units: str | None = "CMS", infiltration: str | None = "MODIFIED_GREEN_AMPT") -> None:
    text = path.read_text()
    text = text.replace(FLOW_UNITS_LINE, "" if flow_units is None else f"FLOW_UNITS           {flow_units}")
    text = text.replace(INFILTRATION_LINE, "" if infiltration is None else f"INFILTRATION         {infiltration}")
    path.write_text(text)


def new_row(path: Path, section: str, sid: str = "S16") -> list[str]:
    text = path.read_text()
    body = re.search(rf"(?ims)^\[{section}\](.*?)(?=^\[|\Z)", text)
    assert body, section
    rows = [line.split() for line in body.group(1).splitlines() if line.split() and line.split()[0] == sid]
    assert len(rows) == 1, (section, rows)
    return rows[0]


# --------------------------------------------------------------------------- units


@pytest.mark.parametrize("flow_units", ["CFS", "GPM", "MGD", None])
def test_us_unit_models_get_acres_feet_and_inches(example_inp, urban_params, flow_units):
    set_options(example_inp, flow_units=flow_units)
    result = apply(example_inp, urban_params, backup=False)
    assert result.flow_units == (flow_units or "CFS")  # SWMM's default is CFS

    sub = new_row(example_inp, "SUBCATCHMENTS")
    assert float(sub[3]) == pytest.approx(5.0 * ACRES_PER_HECTARE, abs=1e-6)
    assert float(sub[5]) == pytest.approx(urban_params.width_m * FEET_PER_METRE, abs=0.005)
    assert float(sub[4]) == round(urban_params.impervious_pct, 2)  # percentages are unit-free
    assert float(sub[6]) == round(urban_params.slope_pct, 2)

    area = new_row(example_inp, "SUBAREAS")
    assert float(area[1]) == urban_params.n_imperv
    assert float(area[3]) == pytest.approx(urban_params.s_imperv_mm / MM_PER_INCH, abs=1e-6)
    assert float(area[4]) == pytest.approx(urban_params.s_perv_mm / MM_PER_INCH, abs=1e-6)
    assert area[3:5] == ["0.05", "0.2"]


@pytest.mark.parametrize("flow_units", ["CMS", "LPS", "MLD"])
def test_si_unit_models_get_hectares_metres_and_millimetres(example_inp, urban_params, flow_units):
    set_options(example_inp, flow_units=flow_units)
    result = apply(example_inp, urban_params, backup=False)
    assert result.flow_units == flow_units
    sub = new_row(example_inp, "SUBCATCHMENTS")
    assert (sub[3], sub[5]) == ("5", "111.8")
    assert new_row(example_inp, "SUBAREAS")[3:5] == ["1.27", "5.08"]


def test_unknown_flow_units_are_refused(example_inp, urban_params):
    set_options(example_inp, flow_units="M3S")
    original = example_inp.read_bytes()
    with pytest.raises(ModelOperationError, match="unknown FLOW_UNITS 'M3S'"):
        apply(example_inp, urban_params)
    assert example_inp.read_bytes() == original


# --------------------------------------------------------------------------- infiltration


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        ("GREEN_AMPT", ["3.5", "0.5", "0.25", "7", "0"]),
        ("MODIFIED_GREEN_AMPT", ["3.5", "0.5", "0.25", "7", "0"]),
        ("HORTON", ["3", "0.5", "4", "7", "0"]),
        ("MODIFIED_HORTON", ["3", "0.5", "4", "7", "0"]),
        ("CURVE_NUMBER", ["80", "0.5", "7"]),
        (None, ["3", "0.5", "4", "7", "0"]),  # SWMM's default is HORTON
    ],
)
def test_infiltration_row_matches_the_model_method(example_inp, urban_params, method, expected):
    set_options(example_inp, infiltration=method)
    result = apply(example_inp, urban_params, backup=False)
    assert result.infiltration_method == (method or "HORTON")
    assert new_row(example_inp, "INFILTRATION")[1:] == expected
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert "S16" in dataframe_from_inp(str(example_inp), "[INFILTRATION]").index


def test_unknown_infiltration_method_is_refused(example_inp, urban_params):
    set_options(example_inp, infiltration="PHILIP")
    with pytest.raises(ModelOperationError, match="unknown INFILTRATION method 'PHILIP'"):
        apply(example_inp, urban_params)


def test_infiltration_values_are_not_converted_for_us_units(example_inp, urban_params):
    set_options(example_inp, flow_units="CFS", infiltration="HORTON")
    apply(example_inp, urban_params, backup=False)
    assert new_row(example_inp, "INFILTRATION")[1:] == ["3", "0.5", "4", "7", "0"]


def test_infiltration_for_reads_defaults_json():
    assert infiltration_for("GREEN_AMPT") == {"Suction": 3.5, "Ksat": 0.5, "IMD": 0.25, "Param4": 7.0, "Param5": 0.0}
    assert infiltration_for("modified_green_ampt") == infiltration_for("GREEN_AMPT")
    assert infiltration_for("HORTON") == {"MaxRate": 3.0, "MinRate": 0.5, "Decay": 4.0, "DryTime": 7.0, "MaxInfil": 0.0}
    assert infiltration_for("MODIFIED_HORTON") == infiltration_for("HORTON")
    assert infiltration_for("CURVE_NUMBER") == {"CurveNum": 80.0, "Conductivity": 0.5, "DryTime": 7.0}
    with pytest.raises(ValidationError, match="Unknown infiltration method"):
        infiltration_for("PHILIP")


def test_infiltration_fields_label_the_leading_values():
    assert set(INFILTRATION_FIELDS) == {"HORTON", "MODIFIED_HORTON", "GREEN_AMPT", "MODIFIED_GREEN_AMPT", "CURVE_NUMBER"}
    assert INFILTRATION_FIELDS["GREEN_AMPT"] == (
        ("Suction head", "mm", "in"),
        ("Conductivity", "mm/h", "in/h"),
        ("Initial deficit", "–", "–"),
    )
    for method, fields in INFILTRATION_FIELDS.items():
        assert 0 < len(fields) <= len(infiltration_for(method)), method
        assert all(len(f) == 3 and all(isinstance(x, str) and x for x in f) for f in fields)
    assert len(INFILTRATION_FIELDS["HORTON"]) == 5
    assert len(INFILTRATION_FIELDS["CURVE_NUMBER"]) == 3


# --------------------------------------------------------------------------- rain gage interval


def drop_raingages(path: Path) -> None:
    text = re.sub(r"(?ims)^\[(RAINGAGES|SYMBOLS)\].*?(?=^\[|\Z)", "", path.read_text())
    path.write_text(re.sub(r"(?m)^(S\d+\s+)Raingage2", r"\1RG1      ", text))


def gage_row(path: Path) -> list[str]:
    return new_row(path, "RAINGAGES", "RG1")


def test_generated_storm_gage_is_hourly(example_inp, urban_params):
    text = re.sub(r"(?ims)^\[(RAINGAGES|SYMBOLS|TIMESERIES)\].*?(?=^\[|\Z)", "", example_inp.read_text())
    example_inp.write_text(re.sub(r"(?m)^(S\d+\s+)Raingage2", r"\1RG1      ", text))
    apply(example_inp, urban_params, backup=False)
    assert gage_row(example_inp) == ["RG1", "INTENSITY", "1:00", "1.0", "TIMESERIES", "generator_series"]
    assert writer.DESIGN_STORM[1][0] == "2:00", "the generated series is hourly"


def test_gage_interval_follows_an_existing_series(example_inp, urban_params):
    drop_raingages(example_inp)  # test_series is minute-spaced
    apply(example_inp, urban_params, backup=False)
    assert gage_row(example_inp)[2] == "0:01"


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        (["s 0:00 1", "s 0:15 2"], "0:15"),
        (["s 0.5 1", "s 1.0 2"], "0:30"),
        (["s 01/01/2020 23:00 1", "s 01/02/2020 01:00 2"], "2:00"),
        (["s 01/01/2020 0:00 1 0:05 2"], "0:05"),
        (["s 0:00:00 1", "s 6:00:00 2"], "6:00"),
        (['s FILE "rain.dat"'], "1:00"),
        (["s 0:00 1"], "1:00"),
        (["s 1:00 1", "s 1:00 2"], "1:00"),
        (["s 0:00 1", "s 0:00:30 2"], "1:00"),
        (["s JAN-01-2020 0:00 1", "s JAN-01-2020 1:00 2"], "1:00"),
        (["s 2020-01-01 0:00 1", "s 2020-01-01 0:10 2"], "1:00"),
        (["other 0:00 1", "s 0:00 1", "other 0:01 1", "S 0:20 2"], "0:20"),
    ],
)
def test_series_interval(rows, expected):
    doc = writer._InpDocument("[TIMESERIES]\n" + "\n".join(rows) + "\n")
    assert writer._series_interval(doc, "s") == expected
