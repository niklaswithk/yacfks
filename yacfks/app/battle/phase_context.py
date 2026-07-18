from dataclasses import dataclass
from yacfks.app.battle.battle_setup import BattleContext
from yacfks.app.battle.battle_state import BattleState
from yacfks.app.domains.enums import TroopType, BattleSide


@dataclass
class PhaseContext:
    battle_context: BattleContext | None
    battle_state: BattleState | None
    # attaking_side is a bit confusing name i know, it's not Attacker, but dyanmic and set to whicheer side,
    # Attacker or Defender, that us curreently dealing damage against the other side in a given turn
    # i.e. whose attack phase it is
    # maybe another naming coinvention here, attacking_side, defending_side, attacker_troop_type etc etc...we're barrelling towards a misunderstadning
    attacking_side: BattleSide

    # None during ALWAYS/TURN_START evaluation (no active attack phase)
    attacker_troop_type: TroopType | None
    defender_troop_type: TroopType | None
