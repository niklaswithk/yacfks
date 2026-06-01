import sys
import math


# determine army size by adding up all the troops per type
def army_size(inf_count: int = 0, cav_count: int = 0, arch_count: int = 0) -> int:
    return inf_count + cav_count  + arch_count

# determine the smaller army size, which will be used later as a scaling factor when calcing the diminish return troop factor
def get_army_min(army1: int, army2: int) -> int:
    return min(army1, army2)

def troop_factor(remaining_unit_type: int, army_min: int) -> float:
    return math.sqrt(remaining_unit_type * army_min)

# attack stats, widget skill that boosts attack, and potentially a  bear level bonus (flat additive)
def effective_attack_bonus(attack_bonus: float = 0, widget_skill_bonus: float = 0, bear_lvl_bonus: float = 0) -> float:
    return (1 + attack_bonus) * (1 + widget_skill_bonus) + bear_lvl_bonus

# lethality stats and widget skill that boosts lethality
def effective_lethality_bonus(lethality_bonus: float = 0, widget_skill_bonus: float = 0) -> float:
    return (1 + lethality_bonus) * (1 + widget_skill_bonus)

# health stats and widget skill that boosts health
def effective_health_bonus(health_bonus: float = 0, widget_skill_bonus: float = 0) -> float:
    return (1 + health_bonus) * (1 + widget_skill_bonus)

# defense stats and widget skill that boosts defense
def effective_defense_bonus(defense_bonus: float = 0, widget_skill_bonus: float = 0) -> float:
    return (1 + defense_bonus) * (1 + widget_skill_bonus)

# get the effective attack by multiplying a troop base Attack with the effective Attack bonus
def effective_attack(base_attack: float, eff_attack_bonus: float = 1.0) -> float:
    return base_attack * eff_attack_bonus

# get the effective lethality by multiplying a troop base Lethality with the effective Lethality bonus
def effective_lethality(base_lethality: float, eff_lethality_bonus: float = 1.0) -> float:
    return base_lethality * eff_lethality_bonus

# get the effective health by multiplying a troop base Health with the effective Health bonus
def effective_health(base_health: float, eff_health_bonus: float = 1.0) -> float:
    return base_health * eff_health_bonus

# get the effective defense by multiplying a troop base Defense with the effective Defense bonus
def effective_defense(base_defense: float, eff_defense_bonus: float = 1.0) -> float:
    return base_defense * eff_defense_bonus

# calc the final "offensive factor" that will be used in the dmg formula
# the division by 100 is probably a design choice, yet another scaling factor, to dial down the damage and keep a reasonable battle pace, while still allowing large stats bonuses.
# So seeing large numbers in stats bonuses makes people feel good and pay more $$$,
# but in the end it scales down so damage/combat doesnt just explode from large stats bonuses, whcih would make battle go on for like only 3 turns or something :)
# yes we do the same dividion by 100 for the defensive factor, but it is the denominator in the stats ratio part of the dmg formula so it has to scale the same,
# and the reason they scale stats to begin with probably is that in the end, the result from the damage formula is the actual numbers of enemy troops killed, 
# so casuatlies has stay reasonable while still allowing for crazy large stats bonuses
def offensive_factor(eff_attack: float, eff_lethality: float) -> float:
    return eff_attack * eff_lethality / 100

# calc the final "offensive factor" that will be used in the dmg formula
def defensive_factor(eff_health: float, eff_defense: float) -> float:
    return eff_health * eff_defense / 100

