from dataclasses import dataclass
from yacfks.app.domains.enums import StatType, BattleSide

# this will represnt widgets in database
@dataclass(frozen=True)
class WidgetDefinition:

    id: int
    name: str
    hero_id: int
    affected_stat: StatType
    widget_mode: BattleSide

# this will represent the calc result of a widget contribtuin to stats for a sim/hero slecetion..
# if a user inputs a hero with widget & level we'l need to account for it in bonus_resolver, when calcing the final sats bonuses,
# and things can get coimplex fast.
# treating the widget contrib explicity wil make things more strucutred in code when we
# calc stats bonuses with widgets.
# prob not needed, on second thought :)
# @dataclass(frozen=True)
# class WidgetContribution:
#     stat: StatType
#     effect: float
