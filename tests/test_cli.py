import json
import subprocess
import sys
from pathlib import Path

import pytest

from rcg import __version__
from rcg.cli import build_parser, main

REPO_ROOT = Path(__file__).resolve().parents[1]
ADD_ARGS = ["--area", "5", "--land-form", "flats_and_plateaus", "--land-cover", "urban_moderately_impervious"]


@pytest.fixture(autouse=True)
def _shared_engine(engine):
    """Make sure the CLI reuses the session engine instead of building its own."""


def run(capsys, *argv):
    code = main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def test_python_dash_m_help_and_version():
    help_run = subprocess.run([sys.executable, "-m", "rcg", "--help"], capture_output=True, text=True, cwd=REPO_ROOT)
    assert help_run.returncode == 0
    assert "add" in help_run.stdout and "list-options" in help_run.stdout and "inspect" in help_run.stdout
    version_run = subprocess.run([sys.executable, "-m", "rcg", "--version"], capture_output=True, text=True, cwd=REPO_ROOT)
    assert version_run.stdout.strip() == f"rcg {__version__}"


@pytest.mark.parametrize(
    ("argv", "handler"),
    [
        (["add", "x.inp", *ADD_ARGS], "_cmd_add"),
        (["preview", *ADD_ARGS], "_cmd_preview"),
        (["inspect", "x.inp"], "_cmd_inspect"),
        (["list-options"], "_cmd_list_options"),
    ],
)
def test_every_subcommand_has_a_handler(argv, handler):
    assert build_parser().parse_args(argv).handler.__name__ == handler


def test_add_json(capsys, example_inp):
    code, out, _ = run(capsys, "add", str(example_inp), *ADD_ARGS, "--json")
    assert code == 0
    data = json.loads(out)
    assert data["subcatchment_ids"] == ["S16"]
    assert data["raingage"] == "Raingage2"
    assert data["outlet"] == "O4"
    assert data["backup_path"]
    assert (data["flow_units"], data["infiltration_method"]) == ("CMS", "MODIFIED_GREEN_AMPT")
    assert data["parameters"]["catchment_type"] == "urban"
    floats = [v for v in data["parameters"].values() if isinstance(v, float)]
    floats += list(data["parameters"]["infiltration"].values())
    assert floats and all(round(v, 4) == v for v in floats)
    assert data["parameters"]["s_imperv_mm"] == 1.27  # 0.05 * 25.4 = 1.2700000000000002 in Python


def test_add_text_with_output_and_no_backup(capsys, example_inp, tmp_path):
    original = example_inp.read_bytes()
    out_file = tmp_path / "copy.inp"
    code, out, _ = run(capsys, "add", str(example_inp), *ADD_ARGS, "--output", str(out_file))
    assert code == 0
    assert "Added S16" in out
    assert "Backup" not in out
    assert example_inp.read_bytes() == original
    assert out_file.exists()

    code, out, _ = run(capsys, "add", str(example_inp), *ADD_ARGS, "--no-backup")
    assert code == 0
    assert not (example_inp.parent / ".rcg_backups").exists()


def test_add_accepts_human_labels(capsys, example_inp):
    argv = ["add", str(example_inp), "--area", "2", "--land-form", "Mountains", "--land-cover", "FORESTS", "--json"]
    code, out, _ = run(capsys, *argv)
    assert code == 0
    assert json.loads(out)["parameters"]["land_cover"] == "forests"


def test_preview_text_and_json(capsys):
    code, out, _ = run(capsys, "preview", *ADD_ARGS)
    assert code == 0
    assert "Catchment type     urban" in out
    code, out, _ = run(capsys, "preview", *ADD_ARGS, "--json")
    assert json.loads(out)["width_m"] == 111.8


def test_add_text_reports_us_units(capsys, example_inp):
    example_inp.write_text(example_inp.read_text().replace("FLOW_UNITS           CMS", "FLOW_UNITS           CFS"))
    code, out, _ = run(capsys, "add", str(example_inp), *ADD_ARGS, "--no-backup")
    assert code == 0
    assert "Flow units CFS (US units: acres, feet, inches), infiltration MODIFIED_GREEN_AMPT" in out


def test_preview_json_is_rounded_for_presentation(capsys, urban_params):
    code, out, _ = run(capsys, "preview", *ADD_ARGS, "--json")
    data = json.loads(out)
    assert data["slope_pct"] == round(urban_params.slope_pct, 4)
    assert data["catchment_score"] == round(urban_params.catchment_score, 4)


def test_inspect_text_and_json(capsys, example_inp):
    code, out, _ = run(capsys, "inspect", str(example_inp))
    assert code == 0
    assert "Flow units         CMS (SI: hectares, metres, millimetres)" in out
    assert "Infiltration       MODIFIED_GREEN_AMPT" in out
    assert "Subcatchments      15" in out
    assert "Rain gage          Raingage2" in out
    assert "Outlet             O4" in out
    code, out, _ = run(capsys, "inspect", str(example_inp), "--json")
    data = json.loads(out)
    assert data["subcatchment_count"] == 15 and data["is_metric"] is True and data["outlet"] == "O4"


def test_inspect_model_without_gage_or_nodes(capsys, tmp_path):
    path = tmp_path / "bare.inp"
    path.write_text("[TITLE]\nbare\n")
    code, out, _ = run(capsys, "inspect", str(path))
    assert code == 0
    assert "Flow units         CFS (US: acres, feet, inches)" in out
    assert "none (RG1 will be created)" in out
    assert "none (each new subcatchment drains to itself)" in out


def test_inspect_errors(capsys, tmp_path):
    with pytest.raises(SystemExit) as info:
        main(["inspect", str(tmp_path / "missing.inp")])
    assert info.value.code == 2
    notes = tmp_path / "notes.inp"
    notes.write_text("just some notes\n")
    code, _, err = run(capsys, "inspect", str(notes))
    assert code == 1
    assert "not a SWMM model" in err


def test_list_options(capsys):
    code, out, _ = run(capsys, "list-options")
    assert code == 0
    assert "highest_mountains" in out and "Urban, moderately impervious" in out
    code, out, _ = run(capsys, "list-options", "--json")
    data = json.loads(out)
    assert len(data["land_forms"]) == 9 and len(data["land_covers"]) == 14


@pytest.mark.parametrize(
    "argv",
    [
        ["preview", "--area", "-1", "--land-form", "flats_and_plateaus", "--land-cover", "rural"],
        ["preview", "--area", "1", "--land-form", "flatz", "--land-cover", "rural"],
        ["add", "missing.inp", *ADD_ARGS],
        [],
        ["add"],
    ],
)
def test_usage_and_validation_errors_exit_2(capsys, argv):
    with pytest.raises(SystemExit) as info:
        main(argv)
    assert info.value.code == 2
    assert "error" in capsys.readouterr().err


def test_did_you_mean_is_shown(capsys):
    with pytest.raises(SystemExit):
        main(["preview", "--area", "1", "--land-form", "flats_and_plateaus", "--land-cover", "urban moderatly impervious"])
    assert "Did you mean: urban_moderately_impervious" in capsys.readouterr().err


def test_model_errors_exit_1(capsys, tmp_path):
    bad = tmp_path / "bad.inp"
    bad.write_text("[SUBCATCHMENTS]\nS1 RG1 O1 1 2 3 4 5 6 7 8 9 10 11 12\n[OPTIONS]\nnot\toptions\tat all\n")
    code, _, err = run(capsys, "add", str(bad), *ADD_ARGS)
    assert code == 1
    assert "rcg: error:" in err


def test_unexpected_errors_exit_1(capsys, example_inp, monkeypatch):
    import rcg.service

    def explode(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(rcg.service, "apply", explode)
    code, _, _ = run(capsys, "add", str(example_inp), *ADD_ARGS)
    assert code == 1
