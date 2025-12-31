import math
import os
import tempfile

import pandas as pd
import pytest
from swmmio import Model

from rcg.fuzzy.categories import LandCover, LandForm
from rcg.fuzzy.engine import Prototype
from rcg.inp_manage.inp import BuildCatchments, SubcatchmentConfig


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
            test_model = BuildCatchments(inp_path, backup=False)
            subcatchment_id = test_model._get_new_subcatchment_id()

            with open(inp_path) as file:
                data = file.read()
                assert data.count(subcatchment_id) == 0

            with open(model_path) as file:
                data = file.read()
                assert data.count(subcatchment_id) == 0

    def test_add_timeseries(self, model_path):
        Model(model_path)
        test_model = BuildCatchments(model_path, backup=False)
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
        Model(model_path)
        test_model = BuildCatchments(model_path, backup=False)

        test_model.model.inp.timeseries = test_model.model.inp.timeseries.iloc[0:0]

        first_timeseries_name = test_model._get_timeseries()
        assert first_timeseries_name == "generator_series"

    def test_get_timeseries_with_existing(self, model_path):
        Model(model_path)
        test_model = BuildCatchments(model_path, backup=False)

        assert len(test_model.model.inp.timeseries) > 0

        first_timeseries_name = test_model._get_timeseries()
        assert first_timeseries_name == test_model.model.inp.timeseries.index[0]

    def test_add_raingage(self, model_path):
        Model(model_path)
        test_model = BuildCatchments(model_path, backup=False)

        test_model.model.inp.raingages = test_model.model.inp.raingages.iloc[0:0]

        test_model._add_raingage()

        assert len(test_model.model.inp.raingages) == 1
        assert test_model.model.inp.raingages.index[0] == "RG1"
        assert test_model.model.inp.raingages.loc["RG1", "RainType"] == "INTENSITY"
        assert test_model.model.inp.raingages.loc["RG1", "TimeIntrvl"] == "0:01"
        assert test_model.model.inp.raingages.loc["RG1", "SnowCatch"] == "1.0"
        assert test_model.model.inp.raingages.loc["RG1", "DataSource"] == "TIMESERIES"
        assert test_model.model.inp.raingages.loc["RG1", "DataSourceName"] == test_model._get_timeseries()

    def test_get_raingage_no_existing_raingages(self, model_path):
        Model(model_path)
        test_model = BuildCatchments(model_path, backup=False)

        test_model.model.inp.raingages = test_model.model.inp.raingages.iloc[0:0]

        assert len(test_model.model.inp.raingages) == 0
        raingage_name = test_model._get_raingage()
        assert raingage_name == "RG1"
        assert len(test_model.model.inp.raingages) == 1

    def test_get_raingage_with_existing_raingages(self, model_path):
        Model(model_path)
        test_model = BuildCatchments(model_path, backup=False)

        existing_raingage_name = test_model.model.inp.raingages.index[0]
        raingage_name = test_model._get_raingage()
        assert raingage_name == existing_raingage_name

    def test_get_outlet_no_existing_junctions(self, model_path):
        test_model = BuildCatchments(model_path, backup=False)

        test_model.model.inp.junctions = test_model.model.inp.junctions.iloc[0:0]

        assert len(test_model.model.inp.junctions) == 0

    def test_add_subarea_with_config(self, model_path):
        test_model = BuildCatchments(model_path, backup=False)

        land_form = LandForm.mountains
        land_cover = LandCover.urban_weakly_impervious

        config = SubcatchmentConfig(area=1.0, land_form=land_form, land_cover=land_cover)
        config.subcatchment_id = "test_subcatchment"
        config.prototype = Prototype(land_form, land_cover)

        test_model._add_subcatchment(config)
        test_model._add_subarea(config)

        assert config.subcatchment_id in test_model.model.inp.subareas.index
        new_subarea = test_model.model.inp.subareas.loc[config.subcatchment_id]

        # Use instance method instead of static method
        populate_key = config.prototype.get_linguistic(config.prototype.catchment_result)

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
        test_model = BuildCatchments(model_path, backup=False)
        test_model.model.inp.polygons = pd.DataFrame(columns=["X", "Y"])

        land_form = LandForm.flats_and_plateaus
        land_cover = LandCover.rural

        config = SubcatchmentConfig(area=1.0, land_form=land_form, land_cover=land_cover)
        config.subcatchment_id = "S1"
        config.prototype = Prototype(land_form, land_cover)

        test_model._add_coords(config)

        math.sqrt(config.area * 10_000)
        assert len(test_model.model.inp.polygons) == 4
        assert config.subcatchment_id in test_model.model.inp.polygons.index

    def test_add_subcatchment_public_api(self, model_path):
        with tempfile.TemporaryDirectory() as tempdir:
            model = Model(model_path)
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)

            test_model = BuildCatchments(inp_path, backup=False)
            initial_count = len(test_model.model.inp.subcatchments)

            test_model.add_subcatchment(area=5.5, land_form="flats_and_plateaus", land_cover="rural")

            assert len(test_model.model.inp.subcatchments) == initial_count + 1

    def test_backup_enabled_by_default(self, model_path):
        with tempfile.TemporaryDirectory() as tempdir:
            model = Model(model_path)
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)

            test_model = BuildCatchments(inp_path)
            assert test_model.backup_enabled is True

    def test_backup_can_be_disabled(self, model_path):
        with tempfile.TemporaryDirectory() as tempdir:
            model = Model(model_path)
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)

            test_model = BuildCatchments(inp_path, backup=False)
            assert test_model.backup_enabled is False

    def test_create_backup(self, model_path):
        with tempfile.TemporaryDirectory() as tempdir:
            model = Model(model_path)
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)

            test_model = BuildCatchments(inp_path, backup=True)
            backup_path = test_model._create_backup()

            assert backup_path.exists()
            assert ".rcg_backups" in str(backup_path)
            assert test_model.backup_path == backup_path

    def test_restore_backup(self, model_path):
        with tempfile.TemporaryDirectory() as tempdir:
            model = Model(model_path)
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)

            test_model = BuildCatchments(inp_path, backup=True)
            test_model._create_backup()

            # Read original content
            with open(inp_path) as f:
                original_content = f.read()

            # Modify the file
            with open(inp_path, "a") as f:
                f.write("\n; Modified content")

            # Restore backup
            test_model.restore_backup()

            # Check content is restored
            with open(inp_path) as f:
                restored_content = f.read()

            assert restored_content == original_content

    def test_context_manager_creates_backup(self, model_path):
        with tempfile.TemporaryDirectory() as tempdir:
            model = Model(model_path)
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)

            with BuildCatchments(inp_path, backup=True) as test_model:
                assert test_model.backup_path is not None
                assert test_model.backup_path.exists()

    def test_transaction_restores_on_error(self, model_path):
        with tempfile.TemporaryDirectory() as tempdir:
            model = Model(model_path)
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)

            test_model = BuildCatchments(inp_path, backup=True)

            # Read original content
            with open(inp_path) as f:
                original_content = f.read()

            # Transaction that fails
            try:
                with test_model.transaction():
                    # Modify file
                    with open(inp_path, "a") as f:
                        f.write("\n; Modified content")
                    # Raise an error to trigger rollback
                    raise ValueError("Intentional error")
            except ValueError:
                pass

            # Check content is restored
            with open(inp_path) as f:
                restored_content = f.read()

            assert restored_content == original_content

    def test_subcatchment_config_validation(self):
        with pytest.raises(ValueError, match="Area must be positive"):
            SubcatchmentConfig(area=-1.0, land_form=LandForm.mountains, land_cover=LandCover.forests)

    def test_subcatchment_config_creation(self):
        config = SubcatchmentConfig(area=10.0, land_form=LandForm.mountains, land_cover=LandCover.forests)
        assert config.area == 10.0
        assert config.land_form == LandForm.mountains
        assert config.land_cover == LandCover.forests
        assert config.prototype is None
        assert config.subcatchment_id is None
