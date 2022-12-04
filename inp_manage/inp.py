import os
import swmmio
import pandas as pd
import numpy as np
desired_width=320
pd.set_option('display.width', desired_width)
np.set_printoptions(linewidth=desired_width)
pd.set_option('display.max_columns',10)


def prepare_copy(file_patch='example.inp'):
    baseline = swmmio.Model(file_patch)
    newfilepath = os.path.join(baseline.inp.name + "_" + 'copy2' + '.inp')
    baseline.inp.save(newfilepath)
    return newfilepath


file = prepare_copy()


model = swmmio.Model(file)
subcatchments = model.inp.subcatchments
subareas = model.inp.subareas
print(subcatchments)
# print(subareas)
