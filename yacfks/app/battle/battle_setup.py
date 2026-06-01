from dataclasses import dataclass
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.troop import TroopStack, TroopDefinition
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.stats import EffectiveBaseStats, EffectiveStatsBonuses, EffectiveFinalStats, RawStatsBonuses
from yacfks.app.services.stat_calculator import StatCalculator
from yacfks.app.services.army_utils import normalize_army_line, aggregate_base_stats
import math

@dataclass
class BattleSetup:
    attacker: Army
    defender: Army

    army_min: int

    attacker_inf_stats_bonus: RawStatsBonuses
    attacker_cav_stats_bonus: RawStatsBonuses
    attacker_arch_stats_bonus: RawStatsBonuses

    defender_inf_stats_bonus: RawStatsBonuses
    defender_cav_stats_bonus: RawStatsBonuses
    defender_arch_stats_bonus: RawStatsBonuses

    attacker_inf_final_stats: EffectiveFinalStats
    attacker_cav_final_stats: EffectiveFinalStats
    attacker_arch_final_stats: EffectiveFinalStats

    defender_inf_final_stats: EffectiveFinalStats
    defender_cav_final_stats: EffectiveFinalStats
    defender_arch_final_stats: EffectiveFinalStats


# builder
def create_battle_setup(attacker: Army, defender: Army) -> BattleSetup:

    attacker_total = attacker.total_troop_count
    defender_total = defender.total_troop_count

    army_min = min(attacker_total, defender_total)

    attacker_inf_base_stats = aggregate_base_stats(normalize_army_line(attacker.infantry_line))
    attacker_cav_base_stats = aggregate_base_stats(normalize_army_line(attacker.cavalry_line))
    attacker_arch_base_stats = aggregate_base_stats(normalize_army_line(attacker.archer_line))

    defender_inf_base_stats = aggregate_base_stats(normalize_army_line(defender.infantry_line))
    defender_cav_base_stats = aggregate_base_stats(normalize_army_line(defender.cavalry_line))
    defender_arch_base_stats = aggregate_base_stats(normalize_army_line(defender.archer_line))


    return BattleSetup(
        attacker=attacker,
        defender=defender,
        army_min=army_min,
    )