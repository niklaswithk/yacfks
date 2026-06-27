from yacfks.app.domains.hero import (
    HeroDefinition,
    HeroSelection,
    HeroSkillDefinition,
    HeroSkillSelection,
)
from yacfks.app.domains.enums import TroopType
from yacfks.app.battle.skills.definitions import Duration, SkillEffect, SkillLevelData
from yacfks.app.battle.skills.conditions import RandomChanceCondition
from yacfks.app.battle.skills.enums import EffectType, StackRule, TargetScope, TriggerType
from yacfks.app.battle.skills.statuses import StatusDefinition, register_status

_PERMANENT = Duration(turns=0)

# ── Status definitions ────────────────────────────────────────────────────────
# Each hero skill applies a status. STACK rule lets multiple heroes of the same
# type each contribute their own instance (additive stacking via same effect_op).

AMANE_TRI_PHALANX_BUFF = register_status(StatusDefinition(
    id=1001,
    name="Tri-Phalanx",
    default_duration=-1,
    effects=[SkillEffect(EffectType.DAMAGE_UP, 102, TargetScope.SELF_ARMY, _PERMANENT)],
    stack_rule=StackRule.STACK,
))

CHENKO_STAND_OF_ARMS_BUFF = register_status(StatusDefinition(
    id=1002,
    name="Stand of Arms",
    default_duration=-1,
    effects=[SkillEffect(EffectType.DAMAGE_UP, 101, TargetScope.SELF_ARMY, _PERMANENT)],
    stack_rule=StackRule.STACK,
))

SAUL_TASKFORCE_BUFF = register_status(StatusDefinition(
    id=2001,
    name="Taskforce Training",
    default_duration=-1,
    effects=[
        SkillEffect(EffectType.DEFENSE_UP, 112, TargetScope.SELF_ARMY, _PERMANENT),
        SkillEffect(EffectType.DEFENSE_UP, 113, TargetScope.SELF_ARMY, _PERMANENT),
    ],
    stack_rule=StackRule.STACK,
))

HILDE_NOBLE_PATH_BUFF = register_status(StatusDefinition(
    id=2002,
    name="Noble Path",
    default_duration=-1,
    effects=[
        SkillEffect(EffectType.DAMAGE_UP,  102, TargetScope.SELF_ARMY, _PERMANENT),
        SkillEffect(EffectType.DEFENSE_UP, 112, TargetScope.SELF_ARMY, _PERMANENT),
    ],
    stack_rule=StackRule.STACK,
))

CURSED = register_status(StatusDefinition(
    id=3001,
    name="Cursed",
    default_duration=1,
    apply_delay=1,  # curse applied this turn becomes active next turn
    effects=[
        SkillEffect(EffectType.DAMAGE_UP, 103, TargetScope.CURRENT_TARGET, _PERMANENT),
    ],
    stack_rule=StackRule.UNIQUE,
))

# ── Amane ─────────────────────────────────────────────────────────────────────

_amane_tri_phalanx = HeroSkillDefinition(
    id=1001,
    name="Tri-Phalanx",
    trigger=TriggerType.ALWAYS,
    effects=[SkillEffect(EffectType.APPLY_STATUS, AMANE_TRI_PHALANX_BUFF.id, TargetScope.SELF_ARMY, _PERMANENT)],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=1001, level=5, values={102: 25.0}),
    },
)

AMANE = HeroDefinition(id=1, name="Amane", troop_type=TroopType.INF)


def amane_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=AMANE,
        skills=[HeroSkillSelection(definition=_amane_tri_phalanx, level=skill_level)],
    )


# ── Chenko ────────────────────────────────────────────────────────────────────

_chenko_stand_of_arms = HeroSkillDefinition(
    id=1002,
    name="Stand of Arms",
    trigger=TriggerType.ALWAYS,
    effects=[SkillEffect(EffectType.APPLY_STATUS, CHENKO_STAND_OF_ARMS_BUFF.id, TargetScope.SELF_ARMY, _PERMANENT)],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=1002, level=5, values={101: 25.0}),
    },
)

CHENKO = HeroDefinition(id=2, name="Chenko", troop_type=TroopType.INF)


def chenko_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=CHENKO,
        skills=[HeroSkillSelection(definition=_chenko_stand_of_arms, level=skill_level)],
    )


# ── Saul ──────────────────────────────────────────────────────────────────────

_saul_taskforce_training = HeroSkillDefinition(
    id=2001,
    name="Taskforce Training",
    trigger=TriggerType.ALWAYS,
    effects=[SkillEffect(EffectType.APPLY_STATUS, SAUL_TASKFORCE_BUFF.id, TargetScope.SELF_ARMY, _PERMANENT)],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=2001, level=5, values={112: 10.0, 113: 15.0}),
    },
)

SAUL = HeroDefinition(id=3, name="Saul", troop_type=TroopType.INF)


def saul_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=SAUL,
        skills=[HeroSkillSelection(definition=_saul_taskforce_training, level=skill_level)],
    )


# ── Hilde ─────────────────────────────────────────────────────────────────────

_hilde_noble_path = HeroSkillDefinition(
    id=2002,
    name="Noble Path",
    trigger=TriggerType.ALWAYS,
    effects=[SkillEffect(EffectType.APPLY_STATUS, HILDE_NOBLE_PATH_BUFF.id, TargetScope.SELF_ARMY, _PERMANENT)],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=2002, level=5, values={102: 15.0, 112: 10.0}),
    },
)

HILDE = HeroDefinition(id=4, name="Hilde", troop_type=TroopType.CAV)


def hilde_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=HILDE,
        skills=[HeroSkillSelection(definition=_hilde_noble_path, level=skill_level)],
    )


# ── Petra ─────────────────────────────────────────────────────────────────────

_petra_evil_eye = HeroSkillDefinition(
    id=3001,
    name="Evil Eye",
    trigger=TriggerType.ATTACK,  # rolls once per attack phase, not once per turn
    effects=[
        SkillEffect(EffectType.APPLY_STATUS, CURSED.id, TargetScope.CURRENT_TARGET, _PERMANENT),
    ],
    conditions=[RandomChanceCondition(chance=0.5)],
    level_data={
        5: SkillLevelData(skill_id=3001, level=5, values={103: 50.0}),
    },
)

PETRA = HeroDefinition(id=5, name="Petra", troop_type=TroopType.INF)


def petra_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=PETRA,
        skills=[HeroSkillSelection(definition=_petra_evil_eye, level=skill_level)],
    )
