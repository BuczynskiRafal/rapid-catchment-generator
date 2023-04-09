"""
This script provides a command-line interface for creating and adding multiple subcatchments
to an existing SWMM model. The user will be prompted to provide input for each subcatchment's
area, land use type, and land form type. The subcatchments will be added to the model
and the updated model will be saved.

Usage:
    python3 runner.py file_path

Example:
    python3 runner.py example.inp

Arguments:
    file_path: The path to the SWMM input file (INP) to which subcatchments will be added.

Functions:
    add_multiple_subcatchments: A recursive function that adds subcatchments to the model.
"""

import sys
from rcg.inp_manage.inp import BuildCatchments


def add_multiple_subcatchments(model):
    """
    Add multiple subcatchments to the given model recursively. The function calls itself
    and adds subcatchments to the model until the user decides to stop.

    Parameters
    ----------
    model : BuildCatchments
        An instance of the BuildCatchments class representing the SWMM model
        to which the subcatchments will be added.
    """
    model.add_subcatchment()

    user_input = input("Do you want to add another subcatchment? (y/n): ").lower()
    if user_input == "y":
        add_multiple_subcatchments(model)
    elif user_input == "n":
        print("Finished adding subcatchments.")
    else:
        print("Invalid input. Please enter 'y' or 'n'.")
        add_multiple_subcatchments(model)


# When this script is run as the main module, create a BuildCatchments instance using
# the provided file path, and then add multiple subcatchments to the model.
if __name__ == "__main__":
    user_model = BuildCatchments(file_path=sys.argv[1])
    add_multiple_subcatchments(user_model)
