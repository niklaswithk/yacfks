from dataclasses import dataclass
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.skills import Skill

@dataclass
class TroopDefinition:
    troop_type: TroopType
    tier_major: int
    tier_minor: int

    base_attack: float
    base_lethality: float
    base_health: float
    base_defense: float
    
    # troop skills are shared, so say you have lots of T6 and only 1 T7, the whole ArmyLine of that troop type gets the T7 skill.
    skills: list[Skill]

@dataclass
class TroopStack:
    definition: TroopDefinition
    count: int
