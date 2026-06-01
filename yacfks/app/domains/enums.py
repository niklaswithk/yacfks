from enum import Enum

class TroopType(Enum):
    INF = "infantry"
    CAV = "cavalry"
    ARCH = "archers"

class SkillOpType(Enum):
    DMGUP = "DamageUp"
    DEFUP = "DefenseUp"
    OPPDEFDOWN = "OppDefenseDown"
    OPPDMGDOWN = "OppDamageDown"
    TROOPDMGUP = "TroopDamageUp"

class BattleMode(Enum):
    ATTACK = "attack"
    DEFENSE = "defense"

class StatType(Enum):
    ATTACK = "attack"
    LETHALITY = "lethality"
    HEALTH = "health"
    DEFENSE = "defense"


class WidgetMode(Enum):
    ATTACK = "attack"
    DEFENSE = "defense"

class StatsInputMode(Enum):
    SOLO_REPORT = "solo"
    RALLY_REPORT = "rally"
