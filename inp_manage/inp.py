import math
import swmmio
import pandas as pd
import numpy as np

from fuzzy.engine import Prototype
from fuzzy.categories import LandUse, LandForm
from swmmio.utils.modify_model import replace_inp_section

desired_width = 500
pd.set_option("display.width", desired_width)
np.set_printoptions(linewidth=desired_width)
pd.set_option("display.max_columns", 15)


class BuildCatchments:
    def __init__(self, file_path: str) -> None:
        self.file = file_path
        self.model = swmmio.Model(self.file)

    def _get_new_subcatchment_id(self, counter: int = 1) -> str:
        """
        Create new subcatchment id (subcatchment name) using len of all subcatchments in model
        and create name using value +1, if it is already in the model then add 1 to the value.
        :param counter: This is the counter that is used to generate the new subcatchment ID, defaults to 1 (optional)
        :return: The name of the new subcatchment.
        """
        name = "S" + f"{len(self.model.inp.subcatchments) + counter}"
        if name not in self.model.inp.subcatchments.index:
            return name
        else:
            counter += 1
            return self._get_new_subcatchment_id(counter=counter)

    def _get_subcatchment_values(self):
        """
        The function takes the user input and returns a dictionary with the area, slope and imperviousness of the
        subcatchment
        :return (dict): The area, slope and imperviousness of the subcatchment.
        """
        area = input("Enter the area of the subcatchment: ")
        land_use = input(
            "Enter the land use type (choose:\n"
            "marshes_and_lowlands\n"
            "flats_and_plateaus\n"
            "flats_and_plateaus_in_combination_with_hills\n"
            "hills_with_gentle_slopes\n"
            "steeper_hills_and_foothills\n"
            "hills_and_outcrops_of_mountain_ranges\n"
            "higher_hills\n"
            "mountains\n"
            "highest_mountains\n:"
        )
        land_form = input(
            "Enter the land form type (choose:\n"
            "medium_conditions\n"
            "permeable_areas\n"
            "permeable_terrain_on_plains\n"
            "hilly\n"
            "mountains\n"
            "bare_rocky_slopes\n"
            "urban\n"
            "suburban\n"
            "rural\n"
            "forests\n"
            "meadows\n"
            "arable \n"
            "marshes\n:"
        )
        prototype_result = Prototype(
            land_use=getattr(LandUse, land_use), land_form=getattr(LandForm, land_form)
        )
        return (area, prototype_result)

    def _add_timeseries(self):
        timeseries = pd.DataFrame(
            data={
                "Date": [None for _ in range(12)],
                "Time": [
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
                ],
                "Value": [
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
                ],
            },
            index=["generator_series" for _ in range(12)],
        )
        timeseries.index.names = ["Name"]
        pd.concat([self.model.inp.timeseries, timeseries])

    def _get_timeseries(self):
        if len(self.model.inp.timeseries) == 0:
            self._add_timeseries()
        return self.model.inp.timeseries.index[0]

    def _add_raingage(self) -> str:
        raingage = pd.DataFrame(
            data={
                "RainType": ["INTENSITY"],
                "TimeIntrvl": ["1:00"],
                "SnowCatch": ["1.0"],
                "DataSource": ["TIMESERIES"],
                "DataSourceName": [self._get_timeseries()],
            },
            index=["RG1"],
        )
        raingage.index.names = ["Name"]
        self.model.inp.raingages = raingage

    def _get_raingage(self) -> str:
        """
        This function returns the name of the rain gage.
        :return: The name of the rain gage.
        """
        if len(self.model.inp.raingages) == 0:
            self._add_raingage()
        return self.model.inp.raingages.index[0]

    def _get_outlet(self):
        if len(self.model.inp.junctions) == 0:
            return None
        return self.model.inp.junctions.index[0]

    def _add_subcatchment(self, subcatchment_id, catchment_values) -> None:
        """
        Adds a new subcatchment to the model.
        The function adds values such as subcatchment id, area, percent slope, percent impervious.
        :return: None
        """
        if self._get_outlet() is None:
            outlet = subcatchment_id
        else:
            outlet = self._get_outlet()
        self.model.inp.subcatchments.loc[subcatchment_id] = {
            "Name": subcatchment_id,
            "Raingage": self._get_raingage(),
            "Outlet": outlet,
            "Area": catchment_values[0],
            "PercImperv": catchment_values[1].impervious_result,
            "Width": math.sqrt((float(catchment_values[0]) * 10_000)),
            "PercSlope": catchment_values[1].slope_result,
            "CurbLength": 0,
        }
        replace_inp_section(
            self.model.inp.path, "[SUBCATCHMENTS]", self.model.inp.subcatchments
        )
        return None

    def _add_subarea(self, subcatchment_id: str, prototype: Prototype) -> None:
        map_mannings = {
            "urban": (0.013, 0.15),
            "suburban": (0.013, 0.24),
            "rural": (0.013, 0.41),
            "forests": (0.40, 0.80),
            "meadows": (0.15, 0.41),
            "arable": (0.06, 0.17),
            "mountains": (0.013, 0.05),
        }
        map_depression = {
            "urban": (0.05, 0.20, 90),
            "suburban": (0.05, 0.20, 80),
            "rural": (0.05, 0.20, 70),
            "forests": (0.05, 0.30, 5),
            "meadows": (0.05, 0.20, 10),
            "arable": (0.05, 0.20, 10),
            "mountains": (0.05, 0.20, 80),
        }
        self.model.inp.subareas.loc[subcatchment_id] = {
            "N-Imperv": map_mannings[
                Prototype.get_populate(prototype.catchment_result)
            ][0],
            "N-Perv": map_mannings[Prototype.get_populate(prototype.catchment_result)][
                1
            ],
            "S-Imperv": map_depression[
                Prototype.get_populate(prototype.catchment_result)
            ][0]
            * 25.4,
            "S-Perv": map_depression[
                Prototype.get_populate(prototype.catchment_result)
            ][1]
            * 25.4,
            "PctZero": map_depression[
                Prototype.get_populate(prototype.catchment_result)
            ][2],
            "RouteTo": "OUTLET",
        }
        replace_inp_section(self.model.inp.path, "[SUBAREAS]", self.model.inp.subareas)

    def _add_coords(self, subcatchment_id):
        exist = [
            (self.model.inp.polygons["X"][-1], self.model.inp.polygons["Y"][-1]),
            (self.model.inp.polygons["X"][-2], self.model.inp.polygons["Y"][-2]),
            (self.model.inp.polygons["X"][-3], self.model.inp.polygons["Y"][-3]),
            (self.model.inp.polygons["X"][-4], self.model.inp.polygons["Y"][-4]),
        ]
        coords = pd.DataFrame(
            data={
                "X": [exist[0][0], exist[1][0], exist[2][0], exist[3][0]],
                "Y": [
                    exist[0][1] - 5,
                    exist[1][1] - 5,
                    exist[2][1] - 5,
                    exist[3][1] - 5,
                ],
            },
            index=[subcatchment_id for _ in range(4)],
        )
        coords.index.names = ["Name"]
        self.model.inp.polygons = pd.concat([self.model.inp.polygons, coords])
        replace_inp_section(self.model.inp.path, "[POLYGONS]", self.model.inp.polygons)

    def get_subcatchment_name(self, name) -> pd.DataFrame:
        """
        Takes a subcatchment id (name) and returns the subcatchment dataframe row with that name (index)

        :param name: The name of the subcatchment
        :type name: str
        :return: The dataframe of the subcatchment with the name given.
        """
        try:
            return self.model.subcatchments.dataframe.loc[name]
        except KeyError:
            raise KeyError(f"Subcatchment with name: {name} doesn't exist")

    def _add_infiltration(self, subcatchment_id: str) -> None:
        self.model.inp.infiltration.loc[subcatchment_id] = {
            "Suction": 3.5,
            "Ksat": 0.5,
            "IMD": 0.25,
            "Param4": 7,
            "Param5": 0,
        }
        self.model.inp.infiltration.index.names = ["Subcatchment"]
        replace_inp_section(
            self.model.inp.path, "[INFILTRATION]", self.model.inp.infiltration
        )

    def add_subcatchment(self) -> None:
        """
        Add new subcatchment to the project:
        :return: None
        """
        subcatchment_id = self._get_new_subcatchment_id()
        catchment_values = self._get_subcatchment_values()
        self._add_subcatchment(subcatchment_id, catchment_values)
        self._add_subarea(subcatchment_id, catchment_values[1])
        self._add_coords(subcatchment_id)
        self._add_infiltration(subcatchment_id)
        return None
