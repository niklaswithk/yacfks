from dataclasses import dataclass
from yacfks.app.domains.army import Army
from yacfks.app.domains.army_config import ArmyConfiguration
from yacfks.app.domains.stats import (
    EffectiveFinalStats,
    ArmyBonuses,
    ArmyBaseStats,
    ArmyFinalStats,
    )
from yacfks.app.services.bonus_resolver import BonusResolver
from yacfks.app.domains.hero import HeroSelection

@dataclass
class BattleContext:
    """
    Battle context, like stats and both sides armies (which in turn includes all troops and their base stats etc),
    All this wil be used to setup a battle.
    And most of these will be static throughout the entire battle, so it's good to have them all in one place.
    The troop count in the armies will of crouse change thtoughout the battle, as troops die off, but that will prob be 
    stored in battle_state and battle_line_state
    """
    attacker_army: Army
    defender_army: Army

    army_min: int

    # we dont necessarily need base stats and stats bonuses stored, bseide the effective final stats,
    # but the point is to make a sim that is more transparent aout what goes on under the hood
    # with damage calcs and so on, so its good to have all pieces of the puzzle saved inidivially
    # so we can display them easily in frontend later.
    # actually, might move the effective stats calculations to the frontend alltogehter,
    # with the backend / battle engine expecting finlized stats to work with. we'll see.
    attacker_base_stats: ArmyBaseStats
    defender_base_stats: ArmyBaseStats

    attacker_bonuses: ArmyBonuses
    defender_bonuses: ArmyBonuses

    attacker_final_stats: ArmyFinalStats
    defender_final_stats: ArmyFinalStats

    attacker_lead_heroes: list[HeroSelection]
    defender_lead_heroes: list[HeroSelection]

    attacker_joiner_heroes: list[HeroSelection]
    defender_joiner_heroes: list[HeroSelection]


    # factory, sets up a battelcontext from both sides' armyconfigs + a bonusresolver
    @classmethod
    def from_army_configs(
            cls,
            attacker_config: ArmyConfiguration,
            defender_config: ArmyConfiguration,
            bonus_resolver: BonusResolver
            ) -> "BattleContext":

        attacker_total = attacker_config.army.total_troop_count
        defender_total = defender_config.army.total_troop_count

        army_min = min(attacker_total, defender_total)
        
        a_base_stats = ArmyBaseStats(
            infantry=attacker_config.army.infantry_line.base_stats,
            cavalry=attacker_config.army.cavalry_line.base_stats,
            archers=attacker_config.army.archer_line.base_stats
        )

        d_base_stats = ArmyBaseStats(
            infantry=defender_config.army.infantry_line.base_stats,
            cavalry=defender_config.army.cavalry_line.base_stats,
            archers=defender_config.army.archer_line.base_stats
        )

        # get effective army stats bonuses
        a_eff_bonus = bonus_resolver.resolve(attacker_config)
        d_eff_bonus = bonus_resolver.resolve(defender_config)

        a_lead_heroes = [
            h for h in attacker_config.leader_heroes
        ]
        a_joiner_heroes = [
            h for h in attacker_config.joiner_heroes
        ]

        d_lead_heroes = [
            h for h in defender_config.leader_heroes
        ]

        d_joiner_heroes = [
            h for h in defender_config.joiner_heroes
        ]

        return cls(
            attacker_army = attacker_config.army,
            defender_army = defender_config.army,
            army_min=army_min,
            attacker_base_stats=a_base_stats,
            defender_base_stats=d_base_stats,
            attacker_bonuses=a_eff_bonus,
            defender_bonuses=d_eff_bonus,
            attacker_final_stats=cls.calculate_final_stats(a_base_stats, a_eff_bonus),
            defender_final_stats=cls.calculate_final_stats(d_base_stats, d_eff_bonus),
            attacker_lead_heroes=a_lead_heroes,
            attacker_joiner_heroes=a_joiner_heroes,
            defender_lead_heroes=d_lead_heroes,
            defender_joiner_heroes=d_joiner_heroes
        )
    

    @staticmethod
    def calculate_final_stats(base: ArmyBaseStats, bonus: ArmyBonuses) -> ArmyFinalStats:
        inf = EffectiveFinalStats(
            attack=base.infantry.attack * bonus.infantry.attack,
            lethality=base.infantry.lethality * bonus.infantry.lethality,
            health=base.infantry.health * bonus.infantry.health,
            defense=base.infantry.defense * bonus.infantry.defense
        )

        cav = EffectiveFinalStats(
            attack=base.cavalry.attack * bonus.cavalry.attack,
            lethality=base.cavalry.lethality * bonus.cavalry.lethality,
            health=base.cavalry.health * bonus.cavalry.health,
            defense=base.cavalry.defense * bonus.cavalry.defense
        )

        arch = EffectiveFinalStats(
            attack=base.archers.attack * bonus.archers.attack,
            lethality=base.archers.lethality * bonus.archers.lethality,
            health=base.archers.health * bonus.archers.health,
            defense=base.archers.defense * bonus.archers.defense
        )
        
        return ArmyFinalStats(
            infantry=inf,
            cavalry=cav,
            archers=arch
        )
