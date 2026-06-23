from dataclasses import dataclass
from yacfks.app.battle.battle_line_state import BattleLineState
from yacfks.app.battle.battle_snapshot import BattleSnapshot
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.troop import TroopStack, TroopDefinition
from yacfks.app.domains.enums import TroopType
from yacfks.app.domains.stats import EffectiveFinalStats
import math

@dataclass
class BattleResult:

    winner: str
    turns: int
    attacker_remaining: int
    defender_remaining: int
    snapshots: list[BattleSnapshot]