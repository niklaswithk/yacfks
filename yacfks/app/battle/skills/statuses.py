from __future__ import annotations
from dataclasses import dataclass
from yacfks.app.battle.skills.definitions import EffectSpec
from yacfks.app.domains.enums import BattleSide, TroopType

# "statuses"...leftover from eariler model/framework...turned out to be more of a mess.
# now we treat effects as firstclass objects, and statuses...well, we'll see..
# will need some cleanuo/reorg/refact....some day...

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
