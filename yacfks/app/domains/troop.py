from __future__ import annotations
from dataclasses import dataclass
from yacfks.app.domains.enums import TroopType
from yacfks.app.battle.skills.enums import TriggerType
from yacfks.app.battle.skills.definitions import SkillEffect, SkillLevelData
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

    # Troop skills are shared: if there's even 1 T7 in an ArmyLine, the whole line gets T7 skills.
    skills: list[TroopSkill]


@dataclass
class TroopStack:
    definition: TroopDefinition
    count: int


@dataclass(frozen=True)
class TroopSkill:
    id: int
    name: str
    trigger: TriggerType
    effects: list[SkillEffect]
    conditions: list[SkillCondition]
    level_data: dict[int, SkillLevelData] | None = None
