from __future__ import annotations
from dataclasses import dataclass, field
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
    required_status_id: int | None = None  # if set, effect is gated on this status being active


@dataclass(frozen=True)
class StatusSpec:
    """Blueprint for a named status a skill can place (e.g. Cursed, Terror).

    Very similar to EffectSpec, but unlike EffectSpec, StatusSpec carries no numeric value.
    It's a named marker/tag that gates/informs dependent effects via 
    required_status_id on EffectSpec.
    """
    id:           int
    name:         str
    target_scope: TargetScope | None = None  # None = ENEMY_ARMY (any enemy)
    duration:     int = 1
    apply_delay:  int = 0
    stack_rule:   StackRule = StackRule.UNIQUE


@dataclass(frozen=True)
class SkillLevelData:
    skill_id: int
    level: int
    values: list[float]  # one value per effect in skill_def.effects, by position
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
    statuses:   list[StatusSpec] = field(default_factory=list)

    def __post_init__(self) -> None:
        # safeguard to make sure number of skill effects matches number of level data entries
        if self.level_data is None:
            return
        n = len(self.effects)
        for lvl, entry in self.level_data.items():
            if len(entry.values) != n:
                raise ValueError(
                    f"Skill '{self.name}' (id={self.id}) level {lvl}: "
                    f"values has {len(entry.values)} entries but skill has {n} effects"
                )


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
