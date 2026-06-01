from dataclasses import dataclass
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.troop import TroopStack, TroopDefinition
from yacfks.app.domains.enums import TroopType
from yacfks.app.services.army_utils import normalize_army_line, aggregate_base_stats
import math

@dataclass
class BattleLineState:
    army_line: ArmyLine
    troop_count: int
    pending_losses: int = 0

    @property
    def is_alive(self) -> bool:
        return self.troop_count > 0


