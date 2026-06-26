from __future__ import annotations
from dataclasses import dataclass
from yacfks.app.battle.skills.definitions import SkillEffect
from yacfks.app.battle.skills.enums import StackRule
from yacfks.app.domains.enums import BattleSide, TroopType


@dataclass(frozen=True)
class StatusDefinition:
    """
    Immutable template describing what a status IS and what effects it contributes.
    Does not hold numeric values — those are resolved at apply-time and live in ActiveStatus.
    """
    id: int
    name: str
    default_duration: int        # turns the status persists; -1 = entire battle
    effects: list[SkillEffect]   # effect type + op templates (no values here)
    stack_rule: StackRule
    apply_delay: int = 0         # 0 = active this turn, 1 = active next turn, etc.


@dataclass
class ActiveStatus:
    """
    A live instance of a status tracked in BattleState.
    Self-contained: carries resolved values, target info, and source at apply-time.
    """
    definition: StatusDefinition
    remaining_turns: int
    source_skill_id: int
    target_side: BattleSide           # which side's troops carry this status
    target_troop: TroopType | None    # None = applies to all troop types on that side
    effect_values: dict[int, float]   # effect_op → numeric value resolved when status was applied


# ── Global status registry ────────────────────────────────────────────────────
# Skills reference statuses by ID via APPLY_STATUS effects.
# Call register_status() when defining a StatusDefinition (e.g., in hero_repo/status_repo).

_STATUS_REGISTRY: dict[int, StatusDefinition] = {}


def register_status(status: StatusDefinition) -> StatusDefinition:
    _STATUS_REGISTRY[status.id] = status
    return status


def get_status(status_id: int) -> StatusDefinition | None:
    return _STATUS_REGISTRY.get(status_id)
