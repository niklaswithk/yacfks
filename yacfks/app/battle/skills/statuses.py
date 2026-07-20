from dataclasses import dataclass
from yacfks.app.battle.skills.definitions import EffectSpec, StatusSpec
from yacfks.app.domains.enums import BattleSide, TroopType

# still gonna need to move/reorganize class def's better.

@dataclass
class ActiveStatus:
    """A live instance of a StatusSpec tracked in BattleState.

    Statuses are named markers/tags (e.g. Cursed, Terror) that gate or inform
    dependent effects via required_status_id on EffectSpec.
    """
    status_spec:     StatusSpec
    remaining_turns: int
    source_skill_id: int
    host_side:       BattleSide
    target_troop:    TroopType | None  # resolved from status_spec.target_scope at apply-time


@dataclass
class ActiveEffect:
    """
    A live instance of an EffectSpec tracked in BattleState.
    One ActiveEffect per EffectSpec — each independently carries its placement,
    remaining lifetime, and resolved numeric value.
    """
    effect_spec:     EffectSpec
    remaining_turns: int                 # -1 = permanent
    source_skill_id: int
    host_side:       BattleSide
    target_troop:    TroopType | None    # None = all troop types on that side
    value:           float               # resolved numeric value at apply-time
