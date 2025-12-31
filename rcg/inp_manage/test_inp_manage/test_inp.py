import os
import pytest
import tempfile
import math
import pandas as pd

from swmmio import Model
from rcg.inp_manage.inp import BuildCatchments, SubcatchmentConfig
from rcg.fuzzy.engine import Prototype
from rcg.fuzzy.categories import LandForm, LandCover


class TestBuildCatchments:
    @pytest.fixture
    def model_path(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "test_file.inp")

    def test_get_new_subcatchment_id(self, model_path):
        model = Model(model_path)
        with tempfile.TemporaryDirectory() as tempdir:
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)
            test_model = BuildCatchments(inp_path)
            subcatchment_id = test_model._get_new_subcatchment_id()

            with open(inp_path, "r") as file:
                data = file.read()
                assert data.count(subcatchment_id) == 0

            with open(model_path, "r") as file:
                data = file.read()
                assert data.count(subcatchment_id) == 0

    def test_add_timeseries(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)
        initial_timeseries_count = len(test_model.model.inp.timeseries)

        test_model._add_timeseries()

        assert len(test_model.model.inp.timeseries) == initial_timeseries_count + 12
        added_timeseries = test_model.model.inp.timeseries.tail(12)
        assert all(added_timeseries.index == "generator_series")
        assert list(added_timeseries["Time"]) == [
            "1:00",
            "2:00",
            "3:00",
            "4:00",
            "5:00",
            "6:00",
            "7:00",
            "8:00",
            "9:00",
            "10:00",
            "11:00",
            "12:00",
        ]
        assert list(added_timeseries["Value"]) == [
            "1",
            "2",
            "4",
            "4",
            "12",
            "13",
            "11",
            "20",
            "15",
            "10",
            "5",
            "3",
        ]

    def test_get_timeseries_no_existing(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        test_model.model.inp.timeseries = test_model.model.inp.timeseries.iloc[0:0]

        first_timeseries_name = test_model._get_timeseries()
        assert first_timeseries_name == "generator_series"

    def test_get_timeseries_with_existing(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        assert len(test_model.model.inp.timeseries) > 0

        first_timeseries_name = test_model._get_timeseries()
        assert first_timeseries_name == test_model.model.inp.timeseries.index[0]

    def test_add_raingage(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        test_model.model.inp.raingages = test_model.model.inp.raingages.iloc[0:0]

        test_model._add_raingage()

        assert len(test_model.model.inp.raingages) == 1
        assert test_model.model.inp.raingages.index[0] == "RG1"
        assert test_model.model.inp.raingages.loc["RG1", "RainType"] == "INTENSITY"
        assert test_model.model.inp.raingages.loc["RG1", "TimeIntrvl"] == "0:01"
        assert test_model.model.inp.raingages.loc["RG1", "SnowCatch"] == "1.0"
        assert test_model.model.inp.raingages.loc["RG1", "DataSource"] == "TIMESERIES"
        assert (
            test_model.model.inp.raingages.loc["RG1", "DataSourceName"]
            == test_model._get_timeseries()
        )

    def test_get_raingage_no_existing_raingages(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        test_model.model.inp.raingages = test_model.model.inp.raingages.iloc[0:0]

        assert len(test_model.model.inp.raingages) == 0
        raingage_name = test_model._get_raingage()
        assert raingage_name == "RG1"
        assert len(test_model.model.inp.raingages) == 1

    def test_get_raingage_with_existing_raingages(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        existing_raingage_name = test_model.model.inp.raingages.index[0]
        raingage_name = test_model._get_raingage()
        assert raingage_name == existing_raingage_name

    def test_get_outlet_no_existing_junctions(self, model_path):
        test_model = BuildCatchments(model_path)

        test_model.model.inp.junctions = test_model.model.inp.junctions.iloc[0:0]

        assert len(test_model.model.inp.junctions) == 0

    def test_add_subarea_with_config(self, model_path):
        test_model = BuildCatchments(model_path)

        land_form = LandForm.mountains
        land_cover = LandCover.urban_weakly_impervious

        config = SubcatchmentConfig(
            area=1.0,
            land_form=land_form,
            land_cover=land_cover
        )
        config.subcatchment_id = "test_subcatchment"
        config.prototype = Prototype(land_form, land_cover)

        test_model._add_subcatchment(config)
        test_model._add_subarea(config)

        assert config.subcatchment_id in test_model.model.inp.subareas.index
        new_subarea = test_model.model.inp.subareas.loc[config.subcatchment_id]

        populate_key = Prototype.get_linguistic(config.prototype.catchment_result)

        expected_manning = test_model.parameters.manning_coefficients[populate_key]
        expected_depression = test_model.parameters.depression_storage[populate_key]

        expected_values = {
            "N-Imperv": expected_manning[0],
            "N-Perv": expected_manning[1],
            "S-Imperv": expected_depression[0] * 25.4,
            "S-Perv": expected_depression[1] * 25.4,
            "PctZero": expected_depression[2],
            "RouteTo": "OUTLET",
        }

        for key, value in expected_values.items():
            assert new_subarea[key] == pytest.approx(value)

    def test_add_coords_with_config(self, model_path):
        test_model = BuildCatchments(model_path)
        test_model.model.inp.polygons = pd.DataFrame(columns=["X", "Y"])

        land_form = LandForm.flats_and_plateaus
        land_cover = LandCover.rural

        config = SubcatchmentConfig(
            area=1.0,
            land_form=land_form,
            land_cover=land_cover
        )
        config.subcatchment_id = "S1"
        config.prototype = Prototype(land_form, land_cover)

        test_model._add_coords(config)

        expected_side_length = math.sqrt(config.area * 10_000)
        assert len(test_model.model.inp.polygons) == 4
        assert config.subcatchment_id in test_model.model.inp.polygons.index

    def test_add_subcatchment_public_api(self, model_path):
        with tempfile.TemporaryDirectory() as tempdir:
            model = Model(model_path)
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)

            test_model = BuildCatchments(inp_path)
            initial_count = len(test_model.model.inp.subcatchments)

            test_model.add_subcatchment(
                area=5.5,
                land_form="flats_and_plateaus",
                land_cover="rural"
            )

            assert len(test_model.model.inp.subcatchments) == initial_count + 1

    def test_subcatchment_config_validation(self):
        with pytest.raises(ValueError, match="Area must be positive"):
            SubcatchmentConfig(
                area=-1.0,
                land_form=LandForm.mountains,
                land_cover=LandCover.forests
            )

    def test_subcatchment_config_creation(self):
        config = SubcatchmentConfig(
            area=10.0,
            land_form=LandForm.mountains,
            land_cover=LandCover.forests
        )
        assert config.area == 10.0
        assert config.land_form == LandForm.mountains
        assert config.land_cover == LandCover.forests
        assert config.prototype is None
        assert config.subcatchment_id is None
