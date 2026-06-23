from dataclasses import dataclass, field
from yacfks.app.battle.battle_line_state import BattleLineState
from yacfks.app.battle.skills.definitions import SkillEffect
from yacfks.app.domains.enums import BattleSide, TroopType


@dataclass
class ActiveEffect:
    source_skill_id: int
    effect_type: SkillEffect
    value: float
    expires_turn: int
    target_side: BattleSide
    target_troop: TroopType | None


@dataclass
class BattleState:

    attacker_inf: BattleLineState
    attacker_cav: BattleLineState
    attacker_arch: BattleLineState

    defender_inf: BattleLineState
    defender_cav: BattleLineState
    defender_arch: BattleLineState

    turn: int = 1
    active_effects: list[ActiveEffect] = field(default_factory=list)

    def get_line(self, side: BattleSide, troop_type: TroopType) -> BattleLineState:
        if side == BattleSide.ATTACKER:
            if troop_type == TroopType.INF:
                return self.attacker_inf
            if troop_type == TroopType.CAV:
                return self.attacker_cav
            if troop_type == TroopType.ARCH:
                return self.attacker_arch
        elif side == BattleSide.DEFENDER:
            if troop_type == TroopType.INF:
                return self.defender_inf
            if troop_type == TroopType.CAV:
                return self.defender_cav
            if troop_type == TroopType.ARCH:
                return self.defender_arch
        raise ValueError(f"Unknown side/type combo: {side}, {troop_type}")
