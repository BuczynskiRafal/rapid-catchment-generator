# run script with python3 main.py file_path
import sys
from inp_manage.inp import BuildCatchments


def add_multiple_subcatchments(model):
    """Add a multiple subcatchments to the model.

    :param model: SWMM model
    """
    model.add_subcatchment()
    add_multiple_subcatchments(model)


# This is a way to run the script from the command line.
if __name__ == "__main__":
    model = BuildCatchments(file_path=sys.argv[1])
    add_multiple_subcatchments(model)
