from __future__ import annotations
from dataclasses import dataclass, field
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.widget import WidgetDefinition
from yacfks.app.battle.skills.enums import TriggerType
from yacfks.app.battle.skills.definitions import SkillEffect, SkillLevelData
from yacfks.app.battle.skills.conditions import SkillCondition


@dataclass(frozen=True)
class HeroDefinition:
    id: int
    name: str
    troop_type: TroopType
    widget: WidgetDefinition | None = None


@dataclass
class HeroSelection:
    hero: HeroDefinition
    widget_level: int = 0
    skills: list["HeroSkillSelection"] = field(default_factory=list)


@dataclass(frozen=True)
class HeroSkillDefinition:
    id: int
    name: str
    trigger: TriggerType
    effects: list[SkillEffect]
    conditions: list[SkillCondition]
    level_data: dict[int, SkillLevelData] | None = None


@dataclass
class HeroSkillSelection:
    definition: HeroSkillDefinition
    level: int
