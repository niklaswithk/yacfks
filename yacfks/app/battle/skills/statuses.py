from dataclasses import dataclass
from yacfks.app.battle.skills.definitions import SkillEffect
from yacfks.app.battle.skills.enums import StackRule

@dataclass(frozen=True)
class StatusDefinition:
    id: int
    name: str
    duration: int
    effects: list[SkillEffect]
    stack_rule: StackRule

@dataclass
class ActiveStatus:
    definition: StatusDefinition
    remaining_turns: int
    source_hero_id: int
