from dataclasses import dataclass
from yacfks.app.battle.battle_line_state import BattleLineState
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.troop import TroopStack, TroopDefinition
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.stats import EffectiveFinalStats
import math

@dataclass
class BattleSnapshot:

    turn_number: int

    attacker_inf: int
    attacker_cav: int
    attacker_arch: int

    defender_inf: int
    defender_cav: int
    defender_arch: int