import os
import swmmio
import pandas as pd
import numpy as np

desired_width = 500
pd.set_option("display.width", desired_width)
np.set_printoptions(linewidth=desired_width)
pd.set_option("display.max_columns", 15)


class File:
    def __init__(self, raw_file):
        self.raw_file = raw_file
        self.file = File.copy_file(self, copy=self.raw_file)
        self.model = swmmio.Model(self.file)
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

    def empty_df(self):
        self.new_catchment = pd.DataFrame(
            data={},
            columns=[
                "Raingage",
                "Outlet",
                "Area",
                "PercImperv",
                "Width",
                "PercSlope",
                "CurbLength",
                "N-Imperv",
                "N-Perv",
                "S-Imperv",
                "S-Perv",
                "PctZero",
                "RouteTo",
                "coords",
            ],
            # index=["Name"],
        )

    def add_subcatchment_id(self, subcatchment_id):
        subcatchment = self.model.inp.subcatchments
        if subcatchment_id not in subcatchment.index:
            # subcatchments.loc["S2"] = subcatchments.loc["S1"].values
            self.model.subcatchments.dataframe.loc[subcatchment_id] = self.model.subcatchments.dataframe.iloc[:1, ]
            # self.new_catchment.iloc[:1,] = subcatchment_id
            print(self.new_catchment)
            # print(self.model.subcatchments.dataframe)
            # self.model.subcatchments.dataframe.loc[subcatchment_id] = self.new_catchment
            return self.model.subcatchments.dataframe

    def get_name(self, name):
        return self.model.subcatchments.dataframe.loc[name]

    def _add_subcatchments_feature(self, feature, value):
        subcatchment = self.model.inp.subcatchments
        subcatchment.loc[self.subcatchment_id, feature] = value
        swmmio.utils.modify_model.replace_inp_section(
            self.model.inp.path, "[SUBCATCHMENTS]", subcatchment
        )



data = File("example.inp")
# print(data.get_name("S1"))
data.add_subcatchment_id("S2")
# print(data.model.inp.subcatchments)
# print(data.model.inp.infiltration)
# print(data.model.inp.subareas)
# data.model.inp.subcatchments.to_excel('show.xlsx')
# print(data.model.subcatchments.dataframe)
