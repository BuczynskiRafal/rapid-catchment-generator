import os
import unittest
import tempfile
import swmmio
from inp_manage.inp import BuildCatchments


class TestBuildCatchments(unittest.TestCase):
    def setUp(self):
        self.model_path = "test_file.inp"

    def test_get_new_subcatchment_id(self):
        model = swmmio.Model(self.model_path)
        with tempfile.TemporaryDirectory() as tempdir:
            inp_path = os.path.join(tempdir, f"{model.inp.name}.inp")
            model.inp.save(inp_path)
            test_model = BuildCatchments(inp_path)
            subcatchment_id = test_model._get_new_subcatchment_id()

            with open(inp_path, "r") as file:
                data = file.read()
                self.assertEqual(data.count(subcatchment_id), 0)

            with open(self.model_path, "r") as file:
                data = file.read()
                self.assertEqual(data.count(subcatchment_id), 0)
