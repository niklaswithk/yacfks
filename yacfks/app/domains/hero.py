from dataclasses import dataclass, field
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.widget import WidgetDefinition
from yacfks.app.battle.skills.definitions import HeroSkillSelection


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
    skills: list[HeroSkillSelection] = field(default_factory=list)
