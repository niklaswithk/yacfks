from enum import Enum

class TroopType(Enum):
    INF = "infantry"
    CAV = "cavalry"
    ARCH = "archers"


class BattleMode(Enum):
    PVP = "pvp"
    BEAR = "bear"

class BattleSide(Enum):
    ATTACKER = "attacker"
    DEFENDER = "defender"

class StatType(Enum):
    ATTACK = "attack"
    LETHALITY = "lethality"
    HEALTH = "health"
    DEFENSE = "defense"


class WidgetMode(Enum):
    ATTACKER = "attacker"
    DEFENDER = "defender"

# for UI, will dictate how we handle stats and widgets in stats calculations.
class StatsInputMode(Enum):
    SOLO_REPORT = "solo"
    RALLY_REPORT = "rally"

