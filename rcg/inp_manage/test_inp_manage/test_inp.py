import os
import pytest
import tempfile
import unittest.mock

from unittest.mock import patch
from swmmio import Model
from rcg.inp_manage.inp import BuildCatchments
from rcg.fuzzy.engine import Prototype
from rcg.fuzzy.categories import LandForm, LandCover


class TestBuildCatchments:
    @pytest.fixture
    def model_path(self):
        return r"C:\Users\Dell\Documents\Git\rapid-catchment-generator\rcg\inp_manage\test_inp_manage\test_file.inp"

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

    def test_get_area_valid_input(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        with patch("builtins.input", return_value="10.5"):
            area = test_model._get_area()
            assert area == 10.5

    def test_get_area_invalid_input(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        with patch("builtins.input", side_effect=["abc", "10.5"]):
            area = test_model._get_area()
            assert area == 10.5

    def test_get_land_form_valid_input(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        with patch("builtins.input", return_value="hills_with_gentle_slopes"):
            land_form = test_model._get_land_form()
            assert land_form == "hills_with_gentle_slopes"

    def test_get_land_form_invalid_input(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        with patch(
            "builtins.input",
            side_effect=["invalid_land_form", "hills_with_gentle_slopes"],
        ):
            land_form = test_model._get_land_form()
            assert land_form == "hills_with_gentle_slopes"

    def test_get_land_cover_valid_input(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        with patch("builtins.input", return_value="urban"):
            land_cover = test_model._get_land_cover()
            assert land_cover == "urban"

    def test_get_land_cover_invalid_input(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        with patch(
            "builtins.input",
            side_effect=["invalid_land_cover", "urban"],
        ):
            land_cover = test_model._get_land_cover()
            assert land_cover == "urban"

    def test_get_subcatchment_values(self, model_path):
        model = Model(model_path)
        test_model = BuildCatchments(model_path)

        with patch.object(test_model, "_get_area", return_value=10.0), patch.object(
            test_model, "_get_land_form", return_value="hills_with_gentle_slopes"
        ), patch.object(test_model, "_get_land_cover", return_value="urban"):
            area, prototype = test_model._get_subcatchment_values()
            assert area == 10.0
            assert isinstance(prototype, Prototype)
            assert hasattr(prototype, "slope_result")
            assert hasattr(prototype, "impervious_result")
            assert hasattr(prototype, "catchment_result")

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
        assert test_model.model.inp.raingages.loc["RG1", "TimeIntrvl"] == "1:00"
        assert test_model.model.inp.raingages.loc["RG1", "SnowCatch"] == "1.0"
        assert test_model.model.inp.raingages.loc["RG1", "DataSource"] == "TIMESERIES"
        assert test_model.model.inp.raingages.loc["RG1", "DataSourceName"] == test_model._get_timeseries()

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

        # Usuń istniejące junctions
        test_model.model.inp.junctions = test_model.model.inp.junctions.iloc[0:0]

        assert len(test_model.model.inp.junctions) == 0
        outlet = test_model._get_outlet()
        assert outlet is None

    def test_get_outlet_with_existing_junctions(self, model_path):
        test_model = BuildCatchments(model_path)

        existing_junction_name = test_model.model.inp.junctions.index[0]
        outlet = test_model._get_outlet()
        assert outlet == existing_junction_name

