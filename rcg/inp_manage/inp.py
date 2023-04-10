import math
import swmmio
import pandas as pd
import numpy as np

from typing import List, Tuple, Optional
from rcg.fuzzy.engine import Prototype
from rcg.fuzzy.categories import LandForm, LandCover
from swmmio.utils.modify_model import replace_inp_section

desired_width = 500
pd.set_option("display.width", desired_width)
np.set_printoptions(linewidth=desired_width)
pd.set_option("display.max_columns", 15)


class BuildCatchments:
    """
    BuildCatchments is a class for creating and managing catchment areas in a SWMM model.

    This class uses the `swmmio` library to load and manipulate SWMM models. It provides
    methods to generate new subcatchment IDs, add new subcatchments, and manage the
    subcatchments in the model.

    Attributes
    ----------
    file_path : str
        The file path of the SWMM input file.
    model : swmmio.Model
        The SWMM model object loaded from the input file.
    """

    def __init__(self, file_path: str) -> None:
        self.file = file_path
        self.model = swmmio.Model(self.file)

    def _get_new_subcatchment_id(self, counter: int = 1) -> str:
        """
        Generate a unique subcatchment ID based on the existing subcatchments in the model.

        This method creates a new subcatchment ID by appending a number to the prefix 'S'.
        It checks the current number of subcatchments in the model and adds the `counter` value
        to generate a new ID. If the generated ID already exists in the model, the method
        increments the `counter` and tries again until a unique ID is found.

        Parameters
        ----------
        counter : int, optional
            The counter that is used to generate the new subcatchment ID. The default value is 1.

        Returns
        -------
        str
            The unique subcatchment ID generated by this method.
        """
        while True:
            name = "S" + f"{len(self.model.inp.subcatchments) + counter}"
            if name not in self.model.inp.subcatchments.index:
                return name
            counter += 1

    @staticmethod
    def _get_area() -> float:
        """
        Prompt the user to input the area of the subcatchment and return it as a float.

        This method asks the user to input the area of the subcatchment. It validates
        the input to ensure that it is a number (either an integer or a float) and
        then returns the area as a float.

        Returns
        -------
        float
            The area of the subcatchment entered by the user.
        """
        area = input("Enter the area of the subcatchment: ")

        while True:
            try:
                area = float(area)
                break
            except ValueError:
                print("Area must be a number.")
                area = input("Enter the area of the subcatchment: ")
            if float(area) < 0:
                print("Area must be greater than zero.")
                area = input("Enter the area of the subcatchment: ")

        return area

    @staticmethod
    def _get_land_form():
        """
        Prompt the user to input the land use type for the subcatchment and return it as a string.

        This method presents a list of land use type options to the user and asks them to
        choose one. The input is validated to ensure that it is one of the available options.
        The chosen land use type is then returned as a string.

        Returns
        -------
        str
            The land use type for the subcatchment entered by the user.
        """
        land_form_options = [
            "marshes_and_lowlands",
            "flats_and_plateaus",
            "flats_and_plateaus_in_combination_with_hills",
            "hills_with_gentle_slopes",
            "steeper_hills_and_foothills",
            "hills_and_outcrops_of_mountain_ranges",
            "higher_hills",
            "mountains",
            "highest_mountains",
        ]
        land_form = ""
        while land_form not in land_form_options:
            land_form = input(
                "Enter the land use type (choose one):\n{}\n:".format(
                    "\n".join(land_form_options)
                )
            )
        return land_form

    @staticmethod
    def _get_land_cover() -> str:
        """
        Prompt the user to input the land cover type for the subcatchment and return it as a string.

        This method presents a list of land cover type options to the user and asks them to
        choose one. The input is validated to ensure that it is one of the available options.
        The chosen land cover type is then returned as a string.

        Returns
        -------
        str
            The land cover type for the subcatchment entered by the user.
        """
        land_cover_options = [
            "medium_conditions",
            "permeable_areas",
            "permeable_terrain_on_plains",
            "hilly",
            "mountains",
            "bare_rocky_slopes",
            "urban",
            "suburban",
            "rural",
            "forests",
            "meadows",
            "arable",
            "marshes",
        ]
        land_cover = ""
        while land_cover not in land_cover_options:
            land_cover = input(
                "Enter the land cover type (choose one):\n{}\n:".format(
                    "\n".join(land_cover_options)
                )
            )
        return land_cover

    def _get_subcatchment_values(self) -> Tuple[float, Prototype]:
        """
        Collect user input for area, land form, and land cover of the subcatchment and return a tuple.

        This method prompts the user for input on area, land form, and land cover of the subcatchment
        by calling the respective helper methods. It then creates a Prototype instance using the
        provided land form and land cover values.

        Returns
        -------
        Tuple[float, Prototype]
            A tuple containing the subcatchment area (float) and the Prototype instance with the
            land form and land cover attributes.
        """
        area = self._get_area()
        land_form = self._get_land_form()
        land_cover = self._get_land_cover()

        prototype_result = Prototype(
            land_form=getattr(LandForm, land_form),
            land_cover=getattr(LandCover, land_cover),
        )
        return area, prototype_result

    def _add_timeseries(self) -> None:
        """
        Add a predefined time series to the SWMM model's input data.

        This method creates a new time series DataFrame with specific values for "Date", "Time", and "Value".
        It then concatenates this new time series DataFrame to the existing time series data in the model's
        input data.

        Note: This method does not save the changes to the model, so the model should be saved after calling
        this method to persist the changes.
        """
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
        self.model.inp.timeseries = pd.concat([self.model.inp.timeseries, timeseries])

    def _get_timeseries(self) -> str:
        """
        Retrieve the name of the first time series in the SWMM model's input data.

        This method checks if the model has any existing time series. If there are no time series,
        it calls the `_add_timeseries` method to add a predefined time series to the model. Then,
        it returns the name of the first time series in the model's input data.

        Returns
        -------
        str
            The name of the first time series in the SWMM model's input data.
        """
        if len(self.model.inp.timeseries) == 0:
            self._add_timeseries()
        return self.model.inp.timeseries.index[0]

    def _add_raingage(self) -> None:
        """
        Add a predefined raingage to the SWMM model's input data.

        This method creates a new raingage data frame with the specified properties and
        adds it to the model's input data. The `_get_timeseries` method is called to retrieve
        the name of the first time series in the model's input data and use it as the
        DataSourceName for the new raingage.
        """
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
        Get the name of the first raingage in the SWMM model's input data.

        If there are no raingages in the model's input data, the `_add_raingage` method
        is called to create and add a new raingage before returning its name.

        Returns
        -------
        str
            The name of the first raingage in the model's input data.
        """
        if len(self.model.inp.raingages) == 0:
            self._add_raingage()
        return self.model.inp.raingages.index[0]

    def _get_outlet(self) -> Optional[str]:
        """
        Get the name of the first junction in the SWMM model's input data.

        If there are no junctions in the model's input data, None is returned.

        Returns
        -------
        Optional[str]
            The name of the first junction in the model's input data, or None if there are no junctions.
        """
        if len(self.model.inp.junctions) == 0:
            return None
        return self.model.inp.junctions.index[0]

    def _add_subcatchment(self, subcatchment_id: str, catchment_values: Tuple[float, Prototype]) -> None:
        """
        Add a new subcatchment to the SWMM model's input data.

        The function adds values such as subcatchment ID, area, percent slope, and percent impervious.
        If there is no outlet in the model, the current subcatchment is set as its own outlet.

        Parameters
        ----------
        subcatchment_id : str
            The unique ID of the subcatchment to be added.
        catchment_values : Tuple[float, Prototype]
            A tuple containing the area of the subcatchment and a Prototype object with slope and imperviousness results.

        Returns
        -------
        None
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

    def _add_subarea(self, subcatchment_id: str, prototype: Prototype) -> None:
        """
        Add a new subarea to the SWMM model's input data.

        The method populates subarea values based on the given subcatchment ID and Prototype object.
        It calculates the values for the Manning's coefficient, depression storage, and other subarea
        parameters using predefined mappings based on the land use type.

        Parameters
        ----------
        subcatchment_id : str
            The unique ID of the subcatchment to add the subarea to.
        prototype : Prototype
            A Prototype object with slope, imperviousness, and land use type results.

        Returns
        -------
        None
        """
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

        populate_key = Prototype.get_populate(prototype.catchment_result)

        self.model.inp.subareas.loc[subcatchment_id] = {
            "N-Imperv": map_mannings[populate_key][0],
            "N-Perv": map_mannings[populate_key][1],
            "S-Imperv": map_depression[populate_key][0] * 25.4,
            "S-Perv": map_depression[populate_key][1] * 25.4,
            "PctZero": map_depression[populate_key][2],
            "RouteTo": "OUTLET",
        }
        replace_inp_section(self.model.inp.path, "[SUBAREAS]", self.model.inp.subareas)

    def _get_existing_coordinates(self) -> List[Tuple[float, float]]:
        """
        Retrieves the existing coordinates for the last subcatchment in the SWMM model's input data.

        Returns
        -------
        List[Tuple[float, float]]
            A list of tuples containing the X and Y coordinates of the existing polygons.
        """
        if len(self.model.inp.polygons) < 4:
            return [
                (0, 0),
                (0, 5),
                (5, 5),
                (5, 0),
            ]
        else:
            return [
                (self.model.inp.polygons["X"].iloc[-1], self.model.inp.polygons["Y"].iloc[-1]),
                (self.model.inp.polygons["X"].iloc[-2], self.model.inp.polygons["Y"].iloc[-2]),
                (self.model.inp.polygons["X"].iloc[-3], self.model.inp.polygons["Y"].iloc[-3]),
                (self.model.inp.polygons["X"].iloc[-4], self.model.inp.polygons["Y"].iloc[-4]),
            ]

    def _add_coords(self, subcatchment_id: str) -> None:
        """
        Adds coordinates for a subcatchment to the SWMM model's input data.

        If existing polygons don't exist, it generates new coordinates for the subcatchment.
        The new coordinates are based on the existing polygons or created with a default offset.

        Parameters
        ----------
        subcatchment_id : str
            The unique ID of the subcatchment to add the coordinates to.

        Returns
        -------
        None
        """
        exist = self._get_existing_coordinates()

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

    def get_subcatchment_name(self, name: str) -> pd.DataFrame:
        """
        Takes a subcatchment id (name) and returns the subcatchment dataframe row with that name (index).

        Parameters
        ----------
        name : str
            The name of the subcatchment.

        Returns
        -------
        pd.DataFrame
            The dataframe row of the subcatchment with the given name.

        Raises
        ------
        KeyError
            If the subcatchment with the given name doesn't exist in the model.
        """
        try:
            return self.model.subcatchments.dataframe.loc[name]
        except KeyError:
            raise KeyError(f"Subcatchment with name: {name} doesn't exist")

    def _add_infiltration(self, subcatchment_id: str) -> None:
        """
        Adds infiltration parameters for a given subcatchment to the model's input data.

        Parameters
        ----------
        subcatchment_id : str
            The name (ID) of the subcatchment.

        Returns
        -------
        None
        """
        infiltration_parameters = {
            "Suction": 3.5,
            "Ksat": 0.5,
            "IMD": 0.25,
            "Param4": 7,
            "Param5": 0,
        }
        self.model.inp.infiltration.loc[subcatchment_id] = infiltration_parameters
        self.model.inp.infiltration.index.names = ["Subcatchment"]
        replace_inp_section(
            self.model.inp.path, "[INFILTRATION]", self.model.inp.infiltration
        )

    def add_subcatchment(self) -> None:
        """
        Adds a new subcatchment to the project, including its subarea, coordinates, and infiltration parameters.

        Returns
        -------
        None
        """
        subcatchment_id = self._get_new_subcatchment_id()
        catchment_values = self._get_subcatchment_values()
        self._add_subcatchment(subcatchment_id, catchment_values)
        self._add_subarea(subcatchment_id, catchment_values[1])
        self._add_coords(subcatchment_id)
        self._add_infiltration(subcatchment_id)
