from __future__ import annotations
from dataclasses import dataclass
from yacfks.app.domains.enums import TroopType
from yacfks.app.battle.skills.enums import TriggerType
from yacfks.app.battle.skills.definitions import SkillEffect, ActivationRule, SkillLevelData
from yacfks.app.battle.skills.conditions import SkillCondition

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
    skills: list[TroopSkill]

@dataclass
class TroopStack:
    definition: TroopDefinition
    count: int


@dataclass(frozen=True)
class TroopSkill:
    id: int
    name: str

    activation: ActivationRule
    trigger: TriggerType
    effects: list[SkillEffect]
    conditions: list[SkillCondition]
    level_data: dict[int, SkillLevelData] = None  # level → values per effect_op