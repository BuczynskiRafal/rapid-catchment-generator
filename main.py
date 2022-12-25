import sys
from inp_manage.inp import BuildCatchments

model = BuildCatchments(file_path=sys.argv[1])

if __name__ == "__main__":
    model.add_subcatchment()
