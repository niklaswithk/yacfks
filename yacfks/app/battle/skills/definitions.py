from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Sequence
from yacfks.app.battle.skills.enums import EffectType, TargetScope, StackRule, TriggerType
from yacfks.app.battle.skills.conditions import SkillCondition


@dataclass(frozen=True)
class EffectSpec:
    """Effect descriptor for both hero and troop skills.

    target_scope: ENEMY_* scope (or CURRENT_TARGET / RANDOM_ENEMY_LINE) — which enemy troop
    type this effect targets.

    benefactor_scope: SELF_* scope (or None = all own troops) — which of the owner's troop
    types benefits from the effect. Used by build_phase_ecs to filter per attack phase.
    """
    effect_type:      EffectType
    effect_op:        int
    target_scope:     TargetScope | None = None
    benefactor_scope: TargetScope | None = None
    duration:         int = -1
    apply_delay:      int = 0
    stack_rule:       StackRule = StackRule.STACK


@dataclass(frozen=True)
class SkillLevelData:
    skill_id: int
    level: int
    values: dict[int, float]
    chance: float | None = None  # overrides RandomChanceCondition.chance when set


# ── Skill definitions ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SkillDefinition:
    """Common base for all skill definitions (hero and troop)."""
    id: int
    name: str
    trigger: TriggerType
    effects: list[EffectSpec]
    conditions: Sequence[SkillCondition]
    level_data: dict[int, SkillLevelData] | None = None


@dataclass(frozen=True)
class HeroSkillDefinition(SkillDefinition):
    """Hero skill definition.

    Hero-exclusive fields like status for cross-skill interactions (e.g. Sophia 2 Terror-skills)
    can be added here later.
    """


@dataclass(frozen=True)
class TroopSkillDefinition(SkillDefinition):
    """Troop skill definition.

    Troop-exclusive fields can be added here as needed.
    Troop skills always evaluate at level 1.
    """


# ── Hero skill selection (frontend-facing wrapper) ────────────────────────────

@dataclass
class HeroSkillSelection:
    """A user's selection of a hero skill at a specific level.

    Created by the frontend when a player picks a hero and configures their
    skill levels. Troop skills are never wrapped this way — they are implicit
    in the chosen troop tier.
    """
    definition: HeroSkillDefinition
    level: int
