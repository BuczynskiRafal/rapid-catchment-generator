from skfuzzy import control as ctrl

from rules import RulesSet
from categories import LandUse, LandForm

simulation_ctrl = ctrl.ControlSystem(RulesSet.get_rules("slope"))

# compute
simulation = ctrl.ControlSystemSimulation(simulation_ctrl)

# calculate slope
simulation.input['land_use'] = LandUse.higher_hills
simulation.input['land_form'] = LandForm.permeable_areas
# result slope
simulation.compute()
result = simulation.output['slope']

print(result)
# slope.view(sim=simulation)