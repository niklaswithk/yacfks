from dataclasses import dataclass
from yacfks.app.battle.battle_setup import BattleContext
from yacfks.app.battle.battle_state import BattleState
from yacfks.app.domains.enums import TroopType


@dataclass
class SkillContext:
    battle_context: BattleContext
    battle_state: BattleState
    # None during TURN_START evaluation (target not yet determined)
    attacker_troop_type: TroopType | None
    defender_troop_type: TroopType | None
