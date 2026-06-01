from dataclasses import dataclass
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.widget import WidgetDefinition

@dataclass(frozen=True)
class HeroDefinition:

    id: int
    name: str
    troop_type: TroopType
    widget: WidgetDefinition
    