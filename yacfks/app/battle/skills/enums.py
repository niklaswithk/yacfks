from enum import Enum

class TriggerType(Enum):
    ALWAYS = "always"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    ATTACK = "attack"

class StackRule(Enum):
    STACK = "stack"
    REFRESH = "refresh"
    UNIQUE = "unique"
    REPLACE = "replace"


class EffectType(Enum):
    DAMAGE_UP = "DamageUp"
    DEFENSE_UP = "DefenseUp"
    OPP_DEFENSE_DOWN = "OppDefenseDown"
    OPP_DAMAGE_DOWN = "OppDamageDown"
    TROOP_DAMAGE_UP = "TroopDamageUp"
    TROOP_DEFENSE_UP = "TroopDefenseUp"

    RETARGET = "retarget" #for T7 cav, might restruct this
    # are these a thing?:
    # TROOPOPPDMGDOWN = "TroopOppDamageDown"
    # TROOPOPPDEFDOWN = "TroopOppDefenseDown"
    APPLY_STATUS = "apply_status"


class TargetScope(Enum):
    SELF_ARMY = "self_army"
    ENEMY_ARMY = "enemy_army"
    CURRENT_TARGET = "current_target"
    RANDOM_ENEMY_LINE = "random_enemy_line"
    ATTACKER_OF_STATUS_TARGET = "attacker_of_status_target"
    DEFENDER_OF_STATUS_TARGET = "defender_of_status_target"

    # SELF_INFANTRY = "self_infantry"
    # SELF_CAVALRY = "self_cavalry"
    # SELF_ARCHERS = "self_archers"

    # ENEMY_INFANTRY = "enemy_infantry"
    # ENEMY_CAVALRY = "enemy_cavalry"
    # ENEMY_ARCHERS = "enemy_archers"