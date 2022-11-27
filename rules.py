import categories

from skfuzzy import control as ctrl

from memberships import membership
# from categories import land_use, land_form, slope_ctgr, impervious_ctgr

class RulesSet:

    def __init__(self, member):
        self.rule1 = ctrl.Rule(antecedent=(   (membership.land_use_type[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.medium_conditions])|
                                              (membership.land_use_typ[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.permeable_areas])  |
                                              (membership.land_use_typ[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.permeable_terrain_on_plains])  |
                                              (membership.land_use_typ[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.rural])               |
                                              (membership.land_use_typ[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.forests])             |
                                              (membership.land_use_typ[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.arable_land])         |
                                              (membership.land_use_typ[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.meadows])             |
                                              (membership.land_use_typ[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.marshes])),
                                consequent=getattr(membership, member)['marshes_and_lowlands'])

        self.rule2 = ctrl.Rule(antecedent=(  (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.medium_conditions])     |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.permeable_areas])       |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.rural])                    |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.forests])                  |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.arable_land])              |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.meadows])                  |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.permeable_terrain_on_plains])|
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.marshes])|
                                (membership.land_use_type[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.urban]) |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.urban]) |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.suburban]) |
                                (membership.land_use_type[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.suburban])|
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.suburban])|
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.urban])),
                  consequent=getattr(membership, member)['flats_and_plateaus'])

        self.rule3 = ctrl.Rule(antecedent=(
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.medium_conditions])   |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.permeable_areas])     |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.rural])                  |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.forests])                |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.arable_land])            |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.permeable_terrain_on_plains])            |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.marshes])|
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.meadows])|
                                (membership.land_use_type[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.hilly_terrain]) |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.hilly_terrain]) |
                                (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.hilly_terrain]) |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.meadows]) |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.arable_land]) |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.marshes]) |
                                (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.marshes]) |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.hilly_terrain])|
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.meadows])|
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.arable_land])|
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.marshes])),
                  consequent=getattr(membership, member)['flats_and_plateaus_in_combination_with_hills'])


        self.rule4 = ctrl.Rule(antecedent=((membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.medium_conditions])   |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.permeable_areas])     |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.permeable_terrain_on_plains])     |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.hilly_terrain])       |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.mountainous_terrain])       |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.forests])                |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.rural])                  |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.rural])                  |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.urban])                  |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.marshes])                  |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.meadows])                  |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.arable_land])                  |
                              (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.suburban])),
                  consequent=getattr(membership, member)['hills_with_gentle_slopes'])

        self.rule5 = ctrl.Rule(antecedent=(
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.medium_conditions])    |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.permeable_areas])      |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.permeable_terrain_on_plains])      |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.mountainous_terrain])      |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.bare_rocky_slopes])      |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.hilly_terrain])        |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.forests])                 |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.rural])                   |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.urban])                   |
                                (membership.land_use_type[categories.land_use.steeper_hills_and_foothills] & membership.land_form_type[categories.land_form.suburban])|
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.mountainous_terrain])|
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.mountainous_terrain])|
                                (membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.arable_land])|
                                (membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.marshes])|
                                (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.meadows])|
                                (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.forests])|
                                (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.marshes])|
                                (membership.land_use_type[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.mountainous_terrain])|
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.permeable_terrain_on_plains])|
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.permeable_areas])|
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.medium_conditions])|
                                (membership.land_use_type[categories.land_use.mountains]    & membership.land_form_type[categories.land_form.medium_conditions])|
                                (membership.land_use_type[categories.land_use.mountains]    & membership.land_form_type[categories.land_form.permeable_areas])|
                                (membership.land_use_type[categories.land_use.mountains]    & membership.land_form_type[categories.land_form.meadows])|
                                (membership.land_use_type[categories.land_use.mountains]    & membership.land_form_type[categories.land_form.urban])|
                                (membership.land_use_type[categories.land_use.mountains]    & membership.land_form_type[categories.land_form.suburban])|
                                (membership.land_use_type[categories.land_use.mountains]    & membership.land_form_type[categories.land_form.rural])),
                  consequent=getattr(membership, member)['steeper_hills_and_foothills'])


        self.rule6 = ctrl.Rule(antecedent=((membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.hilly_terrain]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.bare_rocky_slopes]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.medium_conditions]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.permeable_terrain_on_plains]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.permeable_areas]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.urban]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.suburban]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.rural]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.forests]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.meadows]) |
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.arable_land]) |
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.urban]) |
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.suburban]) |
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.rural]) |
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.forests])|
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.arable_land])|
                              (membership.land_use_type[categories.land_use.hills_and_outcrops_of_mountain_ranges] & membership.land_form_type[categories.land_form.mountainous_terrain])),
                  consequent=getattr(membership, member)['hills_and_outcrops_of_mountain_ranges'])


        self.rule7 = ctrl.Rule(antecedent=(  (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.hilly_terrain]) |
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.bare_rocky_slopes]) |
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.urban]) |
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.suburban]) |
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.rural]) |
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.forests]) |
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.mountainous_terrain])|
                                (membership.land_use_type[categories.land_use.marshes_and_lowlands] & membership.land_form_type[categories.land_form.bare_rocky_slopes]) |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus_in_combination_with_hills] & membership.land_form_type[categories.land_form.bare_rocky_slopes]) |
                                (membership.land_use_type[categories.land_use.hills_with_gentle_slopes] & membership.land_form_type[categories.land_form.bare_rocky_slopes]) |
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.arable_land]) |
                                (membership.land_use_type[categories.land_use.higher_hills] & membership.land_form_type[categories.land_form.marshes]) |
                                (membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.permeable_terrain_on_plains]) |
                                (membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.forests]) |
                                (membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.meadows]) |
                                (membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.arable_land]) |
                                (membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.marshes]) |
                                (membership.land_use_type[categories.land_use.flats_and_plateaus] & membership.land_form_type[categories.land_form.bare_rocky_slopes])),
                  consequent=getattr(membership, member)['higher_hills'])


        self.rule8 = ctrl.Rule(antecedent=((membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.hilly_terrain]) |
                              (membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.bare_rocky_slopes]) |
                              (membership.land_use_type[categories.land_use.mountains] & membership.land_form_type[categories.land_form.mountainous_terrain])|
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.permeable_areas]) |
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.permeable_terrain_on_plains])),
                  consequent=getattr(membership, member)['mountains'])


        self.rule9 = ctrl.Rule(antecedent=((membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.hilly_terrain]) |
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.bare_rocky_slopes]) |
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.medium_conditions]) |
                              (membership.land_use_type[categories.land_use.highest_mountains] & membership.land_form_type[categories.land_form.mountainous_terrain])),
                  consequent=getattr(membership, member)['highest_mountains'])

    @staticmethod
    def get_rules(member):
        return [rule for rule in vars(RulesSet(member))]