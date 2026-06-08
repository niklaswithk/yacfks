from __future__ import annotations
from dataclasses import dataclass
from yacfks.app.domains.enums import TroopType

# base blass for stats
@dataclass
class Stats:
    attack: float
    lethality: float
    health: float
    defense: float



# Effective base stats is dual-use in a sense, will hold base stats after aggreagting stats from all present troop tiers (per type ofcourse)
# If all are same tiers, Effective base stats will simply just be the hardcoded base stats, unweighted/as-is.
# If differnet tiers, Effective base stats will be weighted based on tier contribtion to a stat total
@dataclass
class EffectiveBaseStats(Stats):
    pass



# stats bonuses as they come from user via frontend.
# may or may not already account for widget, depending on input.
# our bonus resolver will handle all input cases.
# "Raw" might be a misnomer since the frontend should convert user input (i.e. perctangees) into proper multipliers, accountiong for the base,
# so stats coming from the fronend into the backed are not tecnhcially "raw". 
@dataclass
class RawStatsBonuses(Stats):

    # small helper function, for cases where we simply want to cast
    # RawStatsBonuses into EffectiveStatsBonuses, like when input mode is "rally"
    def straight_to_effective(self) -> EffectiveStatsBonuses:
        return EffectiveStatsBonuses(
            attack=self.attack,
            lethality=self.lethality,
            health=self.health,
            defense=self.defense
        )



# Effective stats bonuses, after bonues resolver has handled "RawStatsBonuses" coming from frontend
# We ALWAYS end up here with bonuses no matter what, via the bonus reolsver.
# If input mode is "solo battle report" and user inputs stats and then Heroes with widgets, we need to calc
# for widgets in order to turn RawStatsBonuses --> EffectiveStatsBonuses
# # If input mode is "solo battle report" and user inputs stats and NO widgets, then 
# RawStatsBonuses can straight up become EffectiveStatsBonuses, no need to calc for widgets.
# if input mode is "rally battle report" then widgets and everything else is already accounted for, the game
# has already done that for us, so RawStatsBonuses can easily become EffectiveStatsBonuses straight up.
# maybe later pets and other buffs will be added, whcih will require handling akin to widgets, but all that will go
# into bonus resolver duties and we'll still end up with EffectiveStatsBonuses
@dataclass
class EffectiveStatsBonuses(Stats):
    pass


# EffectiveFinalStats is FINALLY the result of EffectiveBaseStats * EffectiveStatsBonuses
@dataclass
class EffectiveFinalStats(Stats):
    pass


# every instance of EffectiveBaseStats, RawStatsBonuses etc and so on are per troop type, i.e. ArmyLine.
# so we'll just wrap the EffectiveStatsBonuses for all troop types in ArmyBonuses below, so we can pass it all into a battle setup or something..
# So each siude, attacker and defender, will have their own copy of this going into batlle :)
#might move this class later to Army or something, but it's good here for now, since it for the moment only hold stats bonuses
@dataclass
class ArmyBonuses:
    infantry: EffectiveStatsBonuses
    cavalry: EffectiveStatsBonuses
    archers: EffectiveStatsBonuses

    def get_bonus(
            self,
            troop_type: TroopType
    ) -> EffectiveStatsBonuses:
        
        if troop_type == TroopType.INF:
            return self.infantry
        
        if troop_type == TroopType.CAV:
            return self.cavalry
        
        if troop_type == TroopType.ARCH:
            return self.archers


# same as above but for base stats
@dataclass
class ArmyBaseStats:
    infantry: EffectiveBaseStats
    cavalry: EffectiveBaseStats
    archers: EffectiveBaseStats

    def get_base_stats(
            self,
            troop_type: TroopType
    ) -> EffectiveBaseStats:
        
        if troop_type == TroopType.INF:
            return self.infantry
        
        if troop_type == TroopType.CAV:
            return self.cavalry
        
        if troop_type == TroopType.ARCH:
            return self.archers
        

# same as above but for effecti final stats
@dataclass
class ArmyFinalStats:
    infantry: EffectiveFinalStats
    cavalry: EffectiveFinalStats
    archers: EffectiveFinalStats

    def get_final_stats(
            self,
            troop_type: TroopType
    ) -> EffectiveFinalStats:
        
        if troop_type == TroopType.INF:
            return self.infantry
        
        if troop_type == TroopType.CAV:
            return self.cavalry
        
        if troop_type == TroopType.ARCH:
            return self.archers