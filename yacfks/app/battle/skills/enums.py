from enum import Enum

class TriggerType(Enum):
    # Static are skills like Tri-Phalanx etc, static modifiers that are actiavgted once per battle
    STATIC = "static"
    # turn-based skills, for every turn
    TURN_START = "turn_start"
    # phase based skills, for every troop type attack phase
    PHASE = "phase"
    # for speical troop skills ambusher and volley
    TROOP_SPECIAL = "troop_special"
    

class StackRule(Enum):
    STACK = "stack"
    REFRESH = "refresh" # problematic, and hypothetical only. might remove
    UNIQUE = "unique" # there can be onlu one!


class EffectType(Enum):
    DAMAGE_UP = "DamageUp"
    DEFENSE_UP = "DefenseUp"
    OPP_DEFENSE_DOWN = "OppDefenseDown"
    OPP_DAMAGE_DOWN = "OppDamageDown"

    # assume these effect_types for troop skills
    TROOP_DAMAGE_UP = "TroopDamageUp"
    TROOP_DEFENSE_UP = "TroopDefenseUp"

    # special troop skills, ambusher and volley
    RETARGET = "retarget"
    EXTRA_ATTACK_PHASE = "extra_attack_phase"
    # are these a thing?:
    # TROOPOPPDMGDOWN = "TroopOppDamageDown"
    # TROOPOPPDEFDOWN = "TroopOppDefenseDown"


class TargetScope(Enum):
    # Own army — all troops or specific troop type
    SELF_ARMY     = "self_army"
    SELF_INFANTRY = "self_infantry"
    SELF_CAVALRY  = "self_cavalry"
    SELF_ARCHERS  = "self_archers"

    # Enemy army — all troops, specific troop type, or dynamic target
    ENEMY_ARMY          = "enemy_army"
    ENEMY_INFANTRY      = "enemy_infantry"
    ENEMY_CAVALRY       = "enemy_cavalry"
    ENEMY_ARCHERS       = "enemy_archers"

    # dynamic targeting
    CURRENT_TARGET      = "current_target"       # whichever enemy line is currently targeted
    RANDOM_ENEMY_LINE   = "random_enemy_line"    # randomly selected enemy troop type, prob doesnt appear in-game, but i'll leave it here if one ewants to try it out


    # ATTACKER_OF_STATUS_TARGET = "attacker_of_status_target"
    # DEFENDER_OF_STATUS_TARGET = "defender_of_status_target"