import pytest

from rcg.config import load_defaults
from rcg.inp_manage.inp import BuildCatchments, ModelParameters


def test_model_parameters_come_from_defaults_json():
    params = ModelParameters()
    defaults = load_defaults()
    assert params.manning_coefficients == dict(defaults.manning_coefficients)
    assert params.depression_storage == dict(defaults.depression_storage)
    assert params.infiltration_defaults == dict(defaults.infiltration)
    params.manning_coefficients["urban"] = (1.0, 1.0)  # a private copy, defaults untouched
    assert load_defaults().manning_coefficients["urban"] == (0.013, 0.15)


def test_build_catchments_is_deprecated_and_delegates(example_inp, engine):
    with pytest.warns(DeprecationWarning, match="rcg.apply"):
        builder = BuildCatchments(str(example_inp), backup=False)
    result = builder.add_subcatchment(5.0, "flats_and_plateaus", "urban_moderately_impervious")
    assert result.subcatchment_ids == ("S16",)
    assert result.backup_path is None
    assert builder.last_result is result
    assert "S16" in example_inp.read_text()


def test_build_catchments_backup_by_default(legacy_inp, engine):
    with pytest.warns(DeprecationWarning):
        builder = BuildCatchments(legacy_inp)
    assert builder.add_subcatchment(1.0, "mountains", "forests").backup_path is not None
