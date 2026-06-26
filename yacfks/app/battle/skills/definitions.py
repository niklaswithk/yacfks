from dataclasses import dataclass
from yacfks.app.battle.skills.enums import EffectType, TargetScope


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
    values: dict[int, float]
