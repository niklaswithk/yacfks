from yacfks.app.domains.hero import HeroDefinition, HeroSelection
from yacfks.app.battle.skills.definitions import HeroSkillDefinition, HeroSkillSelection
from yacfks.app.domains.enums import TroopType
from yacfks.app.battle.skills.definitions import EffectSpec, SkillLevelData, StatusSpec
from yacfks.app.battle.skills.conditions import RandomChanceCondition, RequiresMinTurn
from yacfks.app.battle.skills.enums import EffectType, StackRule, TargetScope, TriggerType


# ── Amane ─────────────────────────────────────────────────────────────────────

_amane_tri_phalanx = HeroSkillDefinition(
    id=1001,
    name="Tri-Phalanx",
    trigger=TriggerType.STATIC,
    effects=[
        EffectSpec(EffectType.DAMAGE_UP, 102),
    ],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=1001, level=5, values=[25.0]),
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
        EffectSpec(EffectType.DAMAGE_UP, 101),
    ],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=1002, level=5, values=[25.0]),
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
        EffectSpec(EffectType.DEFENSE_UP, 112),
        EffectSpec(EffectType.DEFENSE_UP, 113),
    ],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=2001, level=5, values=[10.0, 15.0]),
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
        EffectSpec(EffectType.DAMAGE_UP, 102),
        EffectSpec(EffectType.DEFENSE_UP, 112),
    ],
    conditions=[],
    level_data={
        5: SkillLevelData(skill_id=2002, level=5, values=[15.0, 10.0]),
    },
)

HILDE = HeroDefinition(id=4, name="Hilde", troop_type=TroopType.CAV)


def hilde_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=HILDE,
        skills=[HeroSkillSelection(definition=_hilde_noble_path, level=skill_level)],
    )


# ── Thrud ─────────────────────────────────────────────────────────────────────
# Ancestral Guidance: STATIC skill with two effects — DamageUp and OppDamageDown.
# Both scale identically: 5% / 10% / 15% / 20% / 25% per skill level.
# DamageUp contributes when Thrud's side is phase attacker (numerator).
# OppDamageDown contributes when Thrud's side is phase defender (denominator — reduces enemy damage).
# values=[DamageUp_val, OppDamageDown_val] — positional, one per effect in effects list.

_thrud_ancestral_guidance = HeroSkillDefinition(
    id=4001,
    name="Ancestral Guidance",
    trigger=TriggerType.STATIC,
    effects=[
        EffectSpec(EffectType.DAMAGE_UP, 102),
        EffectSpec(EffectType.OPP_DAMAGE_DOWN, 201),
    ],
    conditions=[],
    level_data={
        1: SkillLevelData(skill_id=4001, level=1, values=[5.0,  5.0]),
        2: SkillLevelData(skill_id=4001, level=2, values=[10.0, 10.0]),
        3: SkillLevelData(skill_id=4001, level=3, values=[15.0, 15.0]),
        4: SkillLevelData(skill_id=4001, level=4, values=[20.0, 20.0]),
        5: SkillLevelData(skill_id=4001, level=5, values=[25.0, 25.0]),
    },
)

THRUD = HeroDefinition(id=6, name="Thrud", troop_type=TroopType.INF)


def thrud_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=THRUD,
        skills=[HeroSkillSelection(definition=_thrud_ancestral_guidance, level=skill_level)],
    )


# ── Petra ─────────────────────────────────────────────────────────────────────
# Evil Eye: fires at TURN_START_PER_TROOP (once per live troop type, after targeting).
# 50% chance per troop roll. Skips turn 1 (RequiresMinTurn=2).
# On proc: places Cursed on PHASE_TARGET (duration=1, UNIQUE, apply_delay=0 → active same turn).
# DamageUp is gated by Cursed (required_status_id) and resolves target_troop from that status,
# so the +50% applies to the exact enemy troop type that was cursed this turn.

# currently trying Cursed being UNIQUE, but might stack.
# would be interesting turnout if it's placed during CAV's attack phase and CAV AMbusher has triggerd :)
_CURSED_STATUS_ID = 1

_petra_evil_eye = HeroSkillDefinition(
    id=3001,
    name="Evil Eye",
    trigger=TriggerType.TURN_START_PER_TROOP,
    statuses=[
        StatusSpec(
            id=_CURSED_STATUS_ID, name="Cursed",
            target_scopes=(TargetScope.PHASE_TARGET,),
            duration=1, apply_delay=0, stack_rule=StackRule.UNIQUE,
        ),
    ],
    effects=[
        EffectSpec(
            EffectType.DAMAGE_UP, 102,
            required_status_id=_CURSED_STATUS_ID,
            duration=1, apply_delay=0, stack_rule=StackRule.UNIQUE,
        ),
    ],
    conditions=[RandomChanceCondition(chance=0.5), RequiresMinTurn(min_turn=2)],
    level_data={
        5: SkillLevelData(skill_id=3001, level=5, values=[50.0]),
    },
)

PETRA = HeroDefinition(id=5, name="Petra", troop_type=TroopType.CAV)


def petra_joiner(skill_level: int = 5) -> HeroSelection:
    return HeroSelection(
        hero=PETRA,
        skills=[HeroSkillSelection(definition=_petra_evil_eye, level=skill_level)],
    )
