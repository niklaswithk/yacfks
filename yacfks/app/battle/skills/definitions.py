from __future__ import annotations
from dataclasses import dataclass
from yacfks.app.battle.skills.enums import EffectType, TargetScope


@dataclass(frozen=True)
class Duration:
    turns: int


@dataclass(frozen=True)
class SkillEffect:
    effect_type:      EffectType
    effect_op:        int
    scope:            TargetScope
    duration:         Duration
    benefactor_scope: TargetScope | None = None  # restricts which own troop type benefits from enemy-side effects; None = all


@dataclass(frozen=True)
class SkillLevelData:
    skill_id: int
    level: int
    values: dict[int, float]
