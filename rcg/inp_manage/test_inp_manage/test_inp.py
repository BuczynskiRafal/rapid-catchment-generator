import os
import pytest
import tempfile
from swmmio import Model
from rcg.inp_manage.inp import BuildCatchments


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
