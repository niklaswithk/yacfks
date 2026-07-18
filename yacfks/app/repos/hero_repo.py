from yacfks.app.domains.hero import HeroDefinition, HeroSelection
from yacfks.app.battle.skills.definitions import HeroSkillDefinition, HeroSkillSelection
from yacfks.app.domains.enums import TroopType
from yacfks.app.battle.skills.definitions import EffectSpec, SkillLevelData
from yacfks.app.battle.skills.conditions import RandomChanceCondition
from yacfks.app.battle.skills.enums import EffectType, StackRule, TargetScope, TriggerType


# ── Amane ─────────────────────────────────────────────────────────────────────

_amane_tri_phalanx = HeroSkillDefinition(
    id=1001,
    name="Tri-Phalanx",
    trigger=TriggerType.STATIC,
    effects=[
        EffectSpec(EffectType.DAMAGE_UP, 102, TargetScope.ENEMY_ARMY),
    ],
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
    trigger=TriggerType.STATIC,
    effects=[
        EffectSpec(EffectType.DAMAGE_UP, 101, TargetScope.ENEMY_ARMY),
    ],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=1002, level=5, values={101: 25.0}),
    },
)

CHENKO = HeroDefinition(id=2, name="Chenko", troop_type=TroopType.CAV)


def chenko_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=CHENKO,
        skills=[HeroSkillSelection(definition=_chenko_stand_of_arms, level=skill_level)],
    )


# ── Saul ──────────────────────────────────────────────────────────────────────

_saul_taskforce_training = HeroSkillDefinition(
    id=2001,
    name="Taskforce Training",
    trigger=TriggerType.STATIC,
    effects=[
        EffectSpec(EffectType.DEFENSE_UP, 112, TargetScope.ENEMY_ARMY),
        EffectSpec(EffectType.DEFENSE_UP, 113, TargetScope.ENEMY_ARMY),
    ],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=2001, level=5, values={112: 10.0, 113: 15.0}),
    },
)

SAUL = HeroDefinition(id=3, name="Saul", troop_type=TroopType.ARCH)


def saul_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=SAUL,
        skills=[HeroSkillSelection(definition=_saul_taskforce_training, level=skill_level)],
    )


# ── Hilde ─────────────────────────────────────────────────────────────────────

_hilde_noble_path = HeroSkillDefinition(
    id=2002,
    name="Noble Path",
    trigger=TriggerType.STATIC,
    effects=[
        EffectSpec(EffectType.DAMAGE_UP,  102, TargetScope.ENEMY_ARMY),
        EffectSpec(EffectType.DEFENSE_UP, 112, TargetScope.ENEMY_ARMY),
    ],
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
# Evil Eye: 50% chance per attack phase to inflict Cursed on current target.
# Duration=1, apply_delay=1: placed this turn, active next turn, expires after 1 turn.
# meaning attacks in turn N+1 against a target reasolved from phase X in turn N will benefit from the DamageUp.
# i.e. a pending debuff.

_petra_evil_eye = HeroSkillDefinition(
    id=3001,
    name="Evil Eye",
    trigger=TriggerType.PHASE,
    effects=[
        EffectSpec(
            EffectType.DAMAGE_UP, 102, TargetScope.CURRENT_TARGET,
            duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE,
        ),
    ],
    conditions=[RandomChanceCondition(chance=0.5)],
    level_data={
        5: SkillLevelData(skill_id=3001, level=5, values={102: 50.0}),
    },
)

PETRA = HeroDefinition(id=5, name="Petra", troop_type=TroopType.CAV)


def petra_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=PETRA,
        skills=[HeroSkillSelection(definition=_petra_evil_eye, level=skill_level)],
    )
