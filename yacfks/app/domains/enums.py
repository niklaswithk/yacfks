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
