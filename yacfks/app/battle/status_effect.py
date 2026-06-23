from dataclasses import dataclass
from yacfks.app.domains.enums import TroopType
from yacfks.app.battle.skills.enums import EffectType

@dataclass
class StatusEffect:
    effect_type: EffectType
    op_id: int
    value: float
    duration: int
    target_troop: TroopType | None = None



