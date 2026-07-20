from yacfks.app.domains.troop import TroopDefinition
from yacfks.app.battle.skills.definitions import TroopSkillDefinition
from yacfks.app.domains.enums import TroopType
from yacfks.app.battle.skills.enums import EffectType, TriggerType, TargetScope
from yacfks.app.battle.skills.definitions import EffectSpec, SkillLevelData
from yacfks.app.battle.skills.conditions import RandomChanceCondition

# ── shared skill building blocks ──────────────────────────────────────────────

# I'ma give all troop DamageUp's effect_op 301 for now, since they will never stack with each other,
# but only with hero skills
# INF T1+: +10% TROOP_DAMAGE_UP vs enemy cavalry
_INF_MASTER_BRAWLER = TroopSkillDefinition(
    id=1301,
    name="Master Brawler",
    trigger=TriggerType.TURN_START,
    effects=[
        EffectSpec(
            effect_type=EffectType.TROOP_DAMAGE_UP,
            effect_op=301,
            target_scope=TargetScope.ENEMY_CAVALRY,
            benefactor_scope=TargetScope.SELF_INFANTRY,
            duration=1,
        )
    ],
    conditions=[],
    level_data={
        1: SkillLevelData(skill_id=1301, level=1, values=[10.0])
    },
)

# CAV T1+: +10% TROOP_DAMAGE_UP vs enemy archers
_CAV_CHARGE = TroopSkillDefinition(
    id=2301,
    name="Charge",
    trigger=TriggerType.TURN_START,
    effects=[
        EffectSpec(
            effect_type=EffectType.TROOP_DAMAGE_UP,
            effect_op=301,
            target_scope=TargetScope.ENEMY_ARCHERS,
            benefactor_scope=TargetScope.SELF_CAVALRY,
            duration=1,
        )
    ],
    conditions=[],
    level_data={
        1: SkillLevelData(skill_id=2301, level=1, values=[10.0])
    },
)

# ARCH T1+: +10% TROOP_DAMAGE_UP vs enemy infantry
_ARCH_RANGED_STRIKE = TroopSkillDefinition(
    id=3301,
    name="Ranged Strike",
    trigger=TriggerType.TURN_START,
    effects=[
        EffectSpec(
            effect_type=EffectType.TROOP_DAMAGE_UP,
            effect_op=301,
            target_scope=TargetScope.ENEMY_INFANTRY,
            benefactor_scope=TargetScope.SELF_ARCHERS,
            duration=1,
        )
    ],
    conditions=[],
    level_data={
        1: SkillLevelData(skill_id=3301, level=1, values=[10.0])
    },
)

# T7+ CAV Ambusher, special retargeting skill: 20% chance per attack phase to swap target to ENEMY_ARCH.
# Speical troop skill with ad-hoc handling
_CAV_AMBUSHER= TroopSkillDefinition(
    id=20,
    name="Ambusher",
    trigger=TriggerType.TROOP_SPECIAL,
    effects=[
        EffectSpec(
            effect_type=EffectType.RETARGET,
            effect_op=0,
            target_scope=TargetScope.ENEMY_ARMY # contributes nothing here, speical skill.
                                                # I should make target_scope optional and default to ENEMY_ARMY

        )
    ],
    conditions=[RandomChanceCondition(chance=0.20)],
    # level data does nothing for this speical skill, but troop skills are so much like hero skills
    # that i really don't want to make an adhoc class for a few speical troop skills...
    level_data={
        1: SkillLevelData(skill_id=20, level=1, values=[1.0])
    },
)

# ── troop definitions ─────────────────────────────────────────────────────────
# Base stats sourced from Daryl https://kingshotsimulator.com/troop-base-stats

_TROOPS: dict[tuple[TroopType, int, int], TroopDefinition] = {
    # Infantry — all tiers have _INF_MASTER_BRAWLER (+10% vs enemy CAV)
    (TroopType.INF, 5, 0): TroopDefinition(
        troop_type=TroopType.INF, tier_major=5, tier_minor=0,
        base_attack=206, base_lethality=10, base_health=619, base_defense=10,
        skills=[_INF_MASTER_BRAWLER],
    ),
    (TroopType.INF, 6, 0): TroopDefinition(
        troop_type=TroopType.INF, tier_major=6, tier_minor=0,
        base_attack=243, base_lethality=10, base_health=730, base_defense=10,
        skills=[_INF_MASTER_BRAWLER],
    ),
    (TroopType.INF, 7, 0): TroopDefinition(
        troop_type=TroopType.INF, tier_major=7, tier_minor=0,
        base_attack=286, base_lethality=10, base_health=859, base_defense=10,
        skills=[_INF_MASTER_BRAWLER],
    ),
    # Cavalry — all tiers have _CAV_CHARGE (+10% vs enemy ARCH); T7+ also gets Ambusher
    (TroopType.CAV, 6, 0): TroopDefinition(
        troop_type=TroopType.CAV, tier_major=6, tier_minor=0,
        base_attack=730, base_lethality=10, base_health=243, base_defense=10,
        skills=[_CAV_CHARGE],
    ),
    (TroopType.CAV, 7, 0): TroopDefinition(
        troop_type=TroopType.CAV, tier_major=7, tier_minor=0,
        base_attack=859, base_lethality=10, base_health=286, base_defense=10,
        skills=[_CAV_CHARGE, _CAV_AMBUSHER],
    ),
    # Archers — all tiers have _ARCH_RANGED_STRIKE (+10% vs enemy INF)
    (TroopType.ARCH, 6, 0): TroopDefinition(
        troop_type=TroopType.ARCH, tier_major=6, tier_minor=0,
        base_attack=974, base_lethality=10, base_health=183, base_defense=10,
        skills=[_ARCH_RANGED_STRIKE],
    ),
    (TroopType.ARCH, 7, 0): TroopDefinition(
        troop_type=TroopType.ARCH, tier_major=7, tier_minor=0,
        base_attack=1146, base_lethality=10, base_health=216, base_defense=10,
        skills=[_ARCH_RANGED_STRIKE],
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
