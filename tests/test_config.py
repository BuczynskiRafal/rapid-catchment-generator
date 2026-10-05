import json

import pytest

from rcg.config import DEFAULTS_PATH, load_defaults
from rcg.exceptions import ConfigurationError


def test_packaged_defaults():
    defaults = load_defaults()
    assert set(defaults.manning_coefficients) == {"urban", "suburban", "rural", "forests", "meadows", "arable", "mountains"}
    assert defaults.manning_coefficients["urban"] == (0.013, 0.15)
    assert defaults.depression_storage["forests"] == (0.05, 0.30, 5)
    assert dict(defaults.infiltration) == {"Suction": 3.5, "Ksat": 0.5, "IMD": 0.25, "Param4": 7.0, "Param5": 0.0}
    assert defaults.validation_limits["area_max_hectares"] == 10000
    assert defaults.validation_limits["area_min_hectares"] == 0.0001


def test_infiltration_defaults_per_method():
    by_method = load_defaults().infiltration_by_method
    assert list(by_method) == ["GREEN_AMPT", "HORTON", "CURVE_NUMBER"]
    assert by_method["GREEN_AMPT"] is load_defaults().infiltration
    assert list(by_method["HORTON"].items()) == [
        ("MaxRate", 3.0),
        ("MinRate", 0.5),
        ("Decay", 4.0),
        ("DryTime", 7.0),
        ("MaxInfil", 0.0),
    ]
    assert list(by_method["CURVE_NUMBER"].items()) == [("CurveNum", 80.0), ("Conductivity", 0.5), ("DryTime", 7.0)]
    with pytest.raises(TypeError):
        by_method["HORTON"]["MaxRate"] = 1.0  # type: ignore[index]


def test_green_ampt_numbers_are_byte_identical_in_defaults_json():
    raw = json.loads(DEFAULTS_PATH.read_text(encoding="utf-8"))["infiltration_defaults"]["GREEN_AMPT"]
    assert json.dumps(raw) == '{"Suction": 3.5, "Ksat": 0.5, "IMD": 0.25, "Param4": 7, "Param5": 0}'


def test_defaults_are_cached_and_read_only():
    assert load_defaults() is load_defaults(DEFAULTS_PATH)
    with pytest.raises(TypeError):
        load_defaults().manning_coefficients["urban"] = (1.0, 1.0)  # type: ignore[index]


@pytest.mark.parametrize(
    ("content", "match"),
    [
        ("{not json", "Invalid JSON"),
        ("[]", "JSON object"),
        (json.dumps({"manning_coefficients": {}}), "Missing section"),
        (
            json.dumps(
                {
                    "manning_coefficients": {"urban": [0.1]},
                    "depression_storage": {"urban": [1, 2, 3]},
                    "infiltration_defaults": {},
                    "validation_limits": {},
                }
            ),
            "Malformed",
        ),
        (
            json.dumps(
                {
                    "manning_coefficients": {"urban": [0.1, 0.2]},
                    "depression_storage": {"rural": [1, 2, 3]},
                    "infiltration_defaults": {},
                    "validation_limits": {},
                }
            ),
            "same catchment types",
        ),
    ],
)
def test_malformed_defaults(tmp_path, content, match):
    path = tmp_path / "defaults.json"
    path.write_text(content)
    with pytest.raises(ConfigurationError, match=match):
        load_defaults(path)


VALID = {
    "manning_coefficients": {"urban": [0.1, 0.2]},
    "depression_storage": {"urban": [1, 2, 3]},
    "validation_limits": {},
}


@pytest.mark.parametrize(
    ("infiltration", "match"),
    [
        ({"GREEN_AMPT": {"Suction": 1}, "HORTON": {"MaxRate": 1}}, "must define CURVE_NUMBER"),
        ({"GREEN_AMPT": 3.5, "HORTON": {}, "CURVE_NUMBER": {}}, "'GREEN_AMPT' must be an object"),
        ({"GREEN_AMPT": {"Suction": "x"}, "HORTON": {}, "CURVE_NUMBER": {}}, "Malformed"),
    ],
)
def test_malformed_infiltration_defaults(tmp_path, infiltration, match):
    path = tmp_path / "defaults.json"
    path.write_text(json.dumps({**VALID, "infiltration_defaults": infiltration}))
    with pytest.raises(ConfigurationError, match=match):
        load_defaults(path)


def test_missing_defaults_file(tmp_path):
    with pytest.raises(ConfigurationError, match="Cannot read"):
        load_defaults(tmp_path / "nope.json")
