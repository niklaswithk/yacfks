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


@dataclass(frozen=True)
class RequiresMinTurn(SkillCondition):
    """Skill does not evaluate before battle turn reaches min_turn.

    Use min_turn=2 for skills that skip turn 1 (e.g. Petra Evil Eye).
    """
    min_turn: int


@dataclass(frozen=True)
class EveryNTurnsCondition(SkillCondition):
    """Skill fires only on turns that are exact multiples of n (turn % n == 0).

    Pair with TriggerType.EVERY_N_TURNS.
    Can stack with RequiresMinTurn eg EveryNTurnsCondition(n=2) + RequiresMinTurn(4) fires
    on turns 4, 6, 8 etc
    """
    n: int