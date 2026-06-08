from dataclasses import dataclass
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.widget import WidgetDefinition

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
    # see above
    hero: HeroDefinition

    # the widget level set in the UI
    # this value is used to get the effect/boost from a certain widget level, which we store in data in widget repo.
    widget_level: int = 0
    #skills come later, someting like this (llooks like Daryls sim does this, judging by local storage in browser):
    # skill_levels={
    #     1: 5,
    #     2: 3,
    #     3: 5
    # }
