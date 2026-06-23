import math
from yacfks.app.domains.stats import EffectiveFinalStats
from yacfks.app.services.formulas import troop_factor, offensive_factor, defensive_factor


def compute_kills(
    attacking_count: int,
    army_min: int,
    attacking_stats: EffectiveFinalStats,
    defending_stats: EffectiveFinalStats,
    skill_mod: float = 1.0,
) -> int:
    """
    Kills = √(attacking_count × army_min) × (attacking_attack × attacking_lethality / 100)
            / (defending_health × defending_defense / 100)
            × skill_mod

    Parameters:
      attacking_count: Current troop count of the side doing damage
      army_min: Smaller of the two total armies (computed at battle start, constant)
      attacking_stats: Final stats of the attacking troop type (includes bonuses)
      defending_stats: Final stats of the defending troop type (includes bonuses)
      skill_mod: SkillMod multiplier (offensive effects / defensive effects)
    """
    if attacking_count <= 0 or army_min <= 0:
        return 0

    off = offensive_factor(attacking_stats.attack, attacking_stats.lethality)
    defense = defensive_factor(defending_stats.health, defending_stats.defense)
    tf = troop_factor(attacking_count, army_min)

    return math.ceil(tf * off / defense / 100 * skill_mod)
