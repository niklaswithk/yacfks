from __future__ import annotations
from dataclasses import dataclass, field
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.widget import WidgetDefinition
from yacfks.app.battle.skills.enums import TriggerType
from yacfks.app.battle.skills.definitions import SkillEffect, ActivationRule, SkillLevelData
from yacfks.app.battle.skills.conditions import SkillCondition

# basci represnation of what a Hero is in database:)
# skills will be added later
@dataclass(frozen=True)
class HeroDefinition:

    id: int
    name: str
    troop_type: TroopType
    #skills come later
    widget: WidgetDefinition | None = None # widget optional since, well not all heroes have them


# a represenation of Hero selection in UI.
@dataclass
class HeroSelection:
    hero: HeroDefinition
    widget_level: int = 0
    skills: list["HeroSkillSelection"] = field(default_factory=list)


@dataclass(frozen=True)
class HeroSkillDefinition:
    id: int
    name: str

    activation: ActivationRule
    trigger: TriggerType
    effects: list[SkillEffect]
    conditions: list[SkillCondition]
    level_data: dict[int, SkillLevelData] = None  # level → values per effect_op


@dataclass
class HeroSkillSelection:
    definition: HeroSkillDefinition
    level: int