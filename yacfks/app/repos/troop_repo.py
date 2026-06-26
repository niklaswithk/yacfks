from yacfks.app.domains.troop import TroopDefinition, TroopSkill
from yacfks.app.domains.enums import TroopType
from yacfks.app.battle.skills.enums import EffectType, TriggerType, TargetScope
from yacfks.app.battle.skills.definitions import Duration, TargetRule, SkillEffect, SkillLevelData
from yacfks.app.battle.skills.conditions import RandomChanceCondition, RequiresTargetTroopType

# ── shared skill building blocks ──────────────────────────────────────────────

_DURATION_1 = Duration(turns=1)
_SELF_TARGET = TargetRule(scope=TargetScope.SELF_ARMY)
_ENEMY_TARGET = TargetRule(scope=TargetScope.ENEMY_ARMY)

# INF T1+: +10% TROOP_DAMAGE_UP vs enemy cavalry (effect_op 201)
_INF_ANTI_CAV = TroopSkill(
    id=201,
    name="Anti-Cavalry Charge",
    trigger=TriggerType.ATTACK,
    effects=[
        SkillEffect(
            effect_type=EffectType.TROOP_DAMAGE_UP,
            effect_op=201,
            target_rule=_SELF_TARGET,
            duration=_DURATION_1,
        )
    ],
    conditions=[RequiresTargetTroopType(TroopType.CAV)],
    level_data={
        1: SkillLevelData(skill_id=201, level=1, values={201: 10.0})
    },
)

# CAV T1+: +10% TROOP_DAMAGE_UP vs enemy archers (effect_op 202)
_CAV_ANTI_ARCH = TroopSkill(
    id=202,
    name="Anti-Archer Charge",
    trigger=TriggerType.ATTACK,
    effects=[
        SkillEffect(
            effect_type=EffectType.TROOP_DAMAGE_UP,
            effect_op=202,
            target_rule=_SELF_TARGET,
            duration=_DURATION_1,
        )
    ],
    conditions=[RequiresTargetTroopType(TroopType.ARCH)],
    level_data={
        1: SkillLevelData(skill_id=202, level=1, values={202: 10.0})
    },
)

# ARCH T1+: +10% TROOP_DAMAGE_UP vs enemy infantry (effect_op 203)
_ARCH_ANTI_INF = TroopSkill(
    id=203,
    name="Anti-Infantry Volley",
    trigger=TriggerType.ATTACK,
    effects=[
        SkillEffect(
            effect_type=EffectType.TROOP_DAMAGE_UP,
            effect_op=203,
            target_rule=_SELF_TARGET,
            duration=_DURATION_1,
        )
    ],
    conditions=[RequiresTargetTroopType(TroopType.INF)],
    level_data={
        1: SkillLevelData(skill_id=203, level=1, values={203: 10.0})
    },
)

# T7 CAV retarget: 20% chance per attack phase to swap target to ARCH.
# RETARGET effects are routed to a dedicated handler (future); registered here for data completeness.
_CAV_T7_RETARGET = TroopSkill(
    id=301,
    name="Cavalry Flanking",
    trigger=TriggerType.ATTACK,
    effects=[
        SkillEffect(
            effect_type=EffectType.RETARGET,
            effect_op=301,
            target_rule=_ENEMY_TARGET,
            duration=Duration(turns=1),
        )
    ],
    conditions=[RandomChanceCondition(chance=0.20)],
    level_data={
        1: SkillLevelData(skill_id=301, level=1, values={301: 1.0})
    },
)

# ── troop definitions ─────────────────────────────────────────────────────────
# Base stats sourced from community data / main.py

_TROOPS: dict[tuple[TroopType, int, int], TroopDefinition] = {
    # Infantry — all tiers have _INF_ANTI_CAV (+10% vs enemy CAV)
    (TroopType.INF, 5, 0): TroopDefinition(
        troop_type=TroopType.INF, tier_major=5, tier_minor=0,
        base_attack=206, base_lethality=10, base_health=619, base_defense=10,
        skills=[_INF_ANTI_CAV],
    ),
    (TroopType.INF, 6, 0): TroopDefinition(
        troop_type=TroopType.INF, tier_major=6, tier_minor=0,
        base_attack=243, base_lethality=10, base_health=730, base_defense=10,
        skills=[_INF_ANTI_CAV],
    ),
    (TroopType.INF, 7, 0): TroopDefinition(
        troop_type=TroopType.INF, tier_major=7, tier_minor=0,
        base_attack=286, base_lethality=10, base_health=859, base_defense=10,
        skills=[_INF_ANTI_CAV],
    ),
    # Cavalry — all tiers have _CAV_ANTI_ARCH (+10% vs enemy ARCH); T7 also gets retarget
    (TroopType.CAV, 6, 0): TroopDefinition(
        troop_type=TroopType.CAV, tier_major=6, tier_minor=0,
        base_attack=730, base_lethality=10, base_health=243, base_defense=10,
        skills=[_CAV_ANTI_ARCH],
    ),
    (TroopType.CAV, 7, 0): TroopDefinition(
        troop_type=TroopType.CAV, tier_major=7, tier_minor=0,
        base_attack=859, base_lethality=10, base_health=286, base_defense=10,
        skills=[_CAV_ANTI_ARCH, _CAV_T7_RETARGET],
    ),
    # Archers — all tiers have _ARCH_ANTI_INF (+10% vs enemy INF)
    (TroopType.ARCH, 6, 0): TroopDefinition(
        troop_type=TroopType.ARCH, tier_major=6, tier_minor=0,
        base_attack=974, base_lethality=10, base_health=183, base_defense=10,
        skills=[_ARCH_ANTI_INF],
    ),
    (TroopType.ARCH, 7, 0): TroopDefinition(
        troop_type=TroopType.ARCH, tier_major=7, tier_minor=0,
        base_attack=1146, base_lethality=10, base_health=216, base_defense=10,
        skills=[_ARCH_ANTI_INF],
    ),
}


def get_troop(troop_type: TroopType, tier_major: int, tier_minor: int = 0) -> TroopDefinition:
    key = (troop_type, tier_major, tier_minor)
    troop = _TROOPS.get(key)
    if troop is None:
        raise KeyError(f"No troop data for {troop_type} T{tier_major}.{tier_minor}")
    return troop


def all_troops() -> list[TroopDefinition]:
    return list(_TROOPS.values())
