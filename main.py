from fuzzy.engine import Prototype
from fuzzy.categories import LandUse, LandForm


calc = Prototype(
    land_use=LandUse.flats_and_plateaus, land_form=LandForm.permeable_areas
)


if __name__ == "__main__":
    print(calc.slope_result)
    print(calc.impervious_result)
    print(calc.catchment_result)
    print(calc.get_populate(result=calc.catchment_result))
