from dataclasses import dataclass
from yacfks.app.battle.battle_setup import BattleSetup
from yacfks.app.battle.battle_line_state import BattleLineState
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.troop import TroopStack, TroopDefinition
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.stats import EffectiveFinalStats
from yacfks.app.services.army_utils import normalize_army_line, aggregate_base_stats
import math

@dataclass
class BattleState:
    setup: BattleSetup

    turn: int = 1

    attacker_inf: BattleLineState
    attacker_cav: BattleLineState
    attacker_arch: BattleLineState

    defender_inf: BattleLineState
    defender_cav: BattleLineState
    defender_arch: BattleLineState