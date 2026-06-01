from dataclasses import dataclass
from yacfks.app.domains.enums import StatType, WidgetMode

@dataclass(frozen=True)
class WidgetDefinition:

    hero_id: int
    affected_stat: StatType
    widget_mode: WidgetMode