import os
import swmmio
import pandas as pd
import numpy as np
desired_width=320
pd.set_option('display.width', desired_width)
np.set_printoptions(linewidth=desired_width)
pd.set_option('display.max_columns',10)


class File:

    def __init__(self, raw_file):
        self.raw_file = raw_file
        self.file = File.copy_file(self, copy=self.raw_file)
        self.model=swmmio.Model(self.file)
        self.new_catchment = None

    def copy_file(self, copy=None, suffix="copy"):
        """
        > This function takes a SWMM input file and creates a copy of it with a suffix added to the end of the file name

        :param copy: the path to the file you want to copy. If you don't specify one, it will use the raw_file
        :param suffix: the suffix to add to the end of the file name, defaults to copy (optional)
        :return: The new path of the copied file.
        """
        if copy is None:
            copy = self.raw_file
        baseline = swmmio.Model(copy)
        new_path = os.path.join(baseline.inp.name + "_" + suffix + ".inp")
        baseline.inp.save(new_path)
        return new_path

    def get_name(self):
        pass

    def add_subcatchment_id(self, name):
        subcatchment = self.model.inp.subcatchments
        self.model.inp.subcatchments.loc[name]

    def _add_subcatchments_feature(self, feature, value):
        subcatchment = self.model.inp.subcatchments
        subcatchment.loc[self.subcatchment_id, feature] = value
        swmmio.utils.modify_model.replace_inp_section(
            self.model.inp.path, "[SUBCATCHMENTS]", subcatchment
        )

data = File('example.inp')
print(data.model.inp.subcatchments)
# print(data.model.inp.infiltration)
print(data.model.inp.subareas)
# data.model.inp.subcatchments.to_excel('show.xlsx')
# print(data.model.subcatchments.dataframe)