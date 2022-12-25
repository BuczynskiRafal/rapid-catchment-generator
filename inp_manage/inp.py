import os
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

    def _get_subcatchment_values(self) -> dict:
        """
        The function takes the user input and returns a dictionary with the area, slope and imperviousness of the
        subcatchment
        :return (dict): The area, slope and imperviousness of the subcatchment.
        """
        area = input("Enter the area of the subcatchment: ")
        land_use = input("Enter the land use type (choose:\nmarshes_and_lowlands\n"
                         "flats_and_plateaus\n"
                         "flats_and_plateaus_in_combination_with_hills\n"
                         "hills_with_gentle_slopes\n"
                         "steeper_hills_and_foothills\n"
                         "hills_and_outcrops_of_mountain_ranges\n"
                         "higher_hills\n"
                         "mountains\n"
                         "highest_mountains\n:")
        land_form = input("Enter the land form type (choose: medium_conditions\n"
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
                          "marshes\n:")
        calculate = Prototype(land_use=getattr(LandUse, land_use), land_form=getattr(LandForm, land_form))
        return {
            "Area": area,
            "PercSlope": calculate.slope_result,
            "PercImperv": calculate.impervious_result,
        }

    def _add_subcatchment(self) -> None:
        """
        Adds a new subcatchment to the model.
        The function adds values such as subcatchment id, area, percent slope, percent impervious.
        :return: None
        """
        subcatchment_id = self._get_new_subcatchment_id()
        catchment_values = self._get_subcatchment_values()
        self.model.inp.subcatchments.loc[subcatchment_id] = {
            "Name": subcatchment_id,
            "Raingage": "1",
            "Outlet": "J1",
            "Area": catchment_values["Area"],
            "PercImperv": catchment_values["PercImperv"],
            "Width": 500,
            "PercSlope": catchment_values["PercSlope"],
            "CurbLength": 0,
        }
        replace_inp_section(self.model.inp.path, "[SUBCATCHMENTS]", self.model.inp.subcatchments)
        return None

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

    def add_subcatchment(self) -> None:
        """
        Add new subcatchment to the project:
        :return: None
        """
        self._add_subcatchment()
        return None
