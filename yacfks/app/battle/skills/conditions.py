from dataclasses import dataclass
from yacfks.app.domains.enums import TroopType


@dataclass(frozen=True)
class SkillCondition:
    pass


@dataclass(frozen=True)
class RandomChanceCondition(SkillCondition):
    """Skill fires only when rng_fn() < chance. Range: [0.0, 1.0].

    Set chance=None when the trigger probability scales with skill level;
    in that case SkillLevelData.chance must be set for every level entry.
    """
    chance: float | None = None


@dataclass(frozen=True)
class RequiresFriendlyTroopType(SkillCondition):
    """Skill only activates if friendly troops of this type are present and alive."""
    troop_type: TroopType


@dataclass(frozen=True)
class RequiresTargetTroopType(SkillCondition):
    """Skill only activates when the current attack target is of this troop type."""
    troop_type: TroopType