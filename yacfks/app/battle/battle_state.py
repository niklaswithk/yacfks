# from __future__ import annotations
from dataclasses import dataclass, field
from yacfks.app.battle.battle_line_state import BattleLineState
from yacfks.app.battle.skills.statuses import ActiveEffect, ActiveStatus
from yacfks.app.domains.enums import BattleSide, TroopType


@dataclass
class BattleState:

    attacker_inf: BattleLineState
    attacker_cav: BattleLineState
    attacker_arch: BattleLineState

    defender_inf: BattleLineState
    defender_cav: BattleLineState
    defender_arch: BattleLineState

    turn: int = 1
    attacker_active_effects:   list[ActiveEffect]  = field(default_factory=list)
    attacker_pending_effects:  list[ActiveEffect]  = field(default_factory=list)
    defender_active_effects:   list[ActiveEffect]  = field(default_factory=list)
    defender_pending_effects:  list[ActiveEffect]  = field(default_factory=list)
    attacker_active_statuses:  list[ActiveStatus]  = field(default_factory=list)
    attacker_pending_statuses: list[ActiveStatus]  = field(default_factory=list)
    defender_active_statuses:  list[ActiveStatus]  = field(default_factory=list)
    defender_pending_statuses: list[ActiveStatus]  = field(default_factory=list)

    def get_effects(self, side: BattleSide, *, pending: bool = False) -> list[ActiveEffect]:
        if side == BattleSide.ATTACKER:
            return self.attacker_pending_effects if pending else self.attacker_active_effects
        return self.defender_pending_effects if pending else self.defender_active_effects

    def get_statuses(self, side: BattleSide, *, pending: bool = False) -> list[ActiveStatus]:
        if side == BattleSide.ATTACKER:
            return self.attacker_pending_statuses if pending else self.attacker_active_statuses
        return self.defender_pending_statuses if pending else self.defender_active_statuses

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
