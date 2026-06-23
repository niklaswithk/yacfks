from dataclasses import dataclass
from yacfks.app.battle.skills.enums import EffectType, TargetScope

# keeping all/most general classes here as WIP, whne/iof things gets a bit more complex ill move into separate files

@dataclass(frozen=True)
class ActivationRule:
    is_rng: bool
    chance: float | None

@dataclass(frozen=True)
class Duration:
    turns: int

@dataclass(frozen=True)
class TargetRule:
    scope: TargetScope

@dataclass(frozen=True)
class SkillEffect:
    effect_type: EffectType
    effect_op: int

    target_rule: TargetRule
    duration: Duration


@dataclass(frozen=True)
class SkillLevelData:
    skill_id: int
    level: int
    activation_chance: float | None

    values: dict[int, float]

