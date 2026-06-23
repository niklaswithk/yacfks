import pytest
from yacfks.app.battle.skills.skill_engine import SkillEngine
from yacfks.app.battle.skills.enums import EffectType, TriggerType, TargetScope
from yacfks.app.battle.skills.definitions import (
    ActivationRule, Duration, TargetRule, SkillEffect, SkillLevelData,
)
from yacfks.app.battle.skills.conditions import RequiresFriendlyTroopType, RequiresTargetTroopType
from yacfks.app.battle.skills.skill_context import SkillContext
from yacfks.app.domains.hero import HeroSkillDefinition, HeroSkillSelection
from yacfks.app.domains.troop import TroopSkill
from yacfks.app.domains.enums import TroopType


def make_skill_context(defender_troop_type: TroopType) -> SkillContext:
    return SkillContext(
        battle_context=None,
        battle_state=None,
        attacker_troop_type=None,
        defender_troop_type=defender_troop_type,
    )


# ── helpers ──────────────────────────────────────────────────────────────────

ALWAYS = ActivationRule(is_rng=False, chance=None)
RNG_50 = ActivationRule(is_rng=True, chance=0.5)
DURATION_1 = Duration(turns=1)
SELF_TARGET = TargetRule(scope=TargetScope.SELF_ARMY)
ENEMY_TARGET = TargetRule(scope=TargetScope.ENEMY_ARMY)

DAMAGE_UP_EFFECT_OP = 101


def make_damage_up_effect(op: int = DAMAGE_UP_EFFECT_OP) -> SkillEffect:
    return SkillEffect(
        effect_type=EffectType.DAMAGE_UP,
        effect_op=op,
        target_rule=SELF_TARGET,
        duration=DURATION_1,
    )


def make_defense_up_effect(op: int = 111) -> SkillEffect:
    return SkillEffect(
        effect_type=EffectType.DEFENSE_UP,
        effect_op=op,
        target_rule=ENEMY_TARGET,
        duration=DURATION_1,
    )


def make_level_data(op: int, value: float, level: int = 1) -> dict:
    return {level: SkillLevelData(skill_id=1, level=level, activation_chance=None, values={op: value})}


def make_static_damage_up_skill(
    skill_id: int = 1,
    op: int = DAMAGE_UP_EFFECT_OP,
    value: float = 30.0,
    level: int = 1,
    trigger: TriggerType = TriggerType.ALWAYS,
) -> HeroSkillDefinition:
    return HeroSkillDefinition(
        id=skill_id,
        name="Test DamageUp",
        activation=ALWAYS,
        trigger=trigger,
        effects=[make_damage_up_effect(op)],
        conditions=[],
        level_data=make_level_data(op, value, level),
    )


def make_rng_damage_up_skill(
    op: int = DAMAGE_UP_EFFECT_OP,
    value: float = 50.0,
    chance: float = 0.5,
) -> HeroSkillDefinition:
    return HeroSkillDefinition(
        id=2,
        name="Test RNG DamageUp",
        activation=ActivationRule(is_rng=True, chance=chance),
        trigger=TriggerType.TURN_START,
        effects=[make_damage_up_effect(op)],
        conditions=[],
        level_data=make_level_data(op, value),
    )


def make_hero_sel(defn: HeroSkillDefinition, level: int = 1) -> HeroSkillSelection:
    return HeroSkillSelection(definition=defn, level=level)


def engine() -> SkillEngine:
    return SkillEngine()


# ── no-skill baseline ─────────────────────────────────────────────────────────

class TestNoSkills:
    def test_empty_skills_returns_unit_mod(self):
        att_ec, def_ec = engine().collect_effects([], [], TriggerType.TURN_START, context=None)
        assert engine().compute_skill_mod(att_ec, def_ec) == 1.0


# ── static ALWAYS skills ──────────────────────────────────────────────────────

class TestStaticAlwaysSkills:
    def test_always_skill_fires_on_turn_start(self):
        skill = make_static_damage_up_skill(value=50.0)
        att_ec, _ = engine().collect_effects([make_hero_sel(skill)], [], TriggerType.TURN_START, context=None)
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.5)

    def test_always_skill_does_not_fire_on_attack_trigger(self):
        # ALWAYS skills are evaluated once at TURN_START, not re-evaluated per attack phase
        # (prevents double-counting when the engine merges turn-start + phase collections)
        skill = make_static_damage_up_skill(value=50.0)
        att_ec, _ = engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ATTACK, context=None)
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_turn_start_skill_does_not_fire_on_attack(self):
        skill = make_static_damage_up_skill(value=50.0, trigger=TriggerType.TURN_START)
        att_ec, _ = engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ATTACK, context=None)
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_attack_skill_does_not_fire_on_turn_start(self):
        skill = make_static_damage_up_skill(value=50.0, trigger=TriggerType.ATTACK)
        att_ec, _ = engine().collect_effects([make_hero_sel(skill)], [], TriggerType.TURN_START, context=None)
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)


# ── RNG skills ────────────────────────────────────────────────────────────────

class TestRngSkills:
    def test_rng_skill_activates_when_roll_below_chance(self):
        skill = make_rng_damage_up_skill(value=50.0, chance=0.5)
        att_ec, _ = engine().collect_effects(
            [make_hero_sel(skill)], [], TriggerType.TURN_START,
            context=None, rng_fn=lambda: 0.0  # always success
        )
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.5)

    def test_rng_skill_does_not_activate_when_roll_at_or_above_chance(self):
        skill = make_rng_damage_up_skill(value=50.0, chance=0.5)
        att_ec, _ = engine().collect_effects(
            [make_hero_sel(skill)], [], TriggerType.TURN_START,
            context=None, rng_fn=lambda: 0.5  # exactly at threshold → miss
        )
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_rng_skill_with_100_chance_always_fires(self):
        skill = make_rng_damage_up_skill(value=50.0, chance=1.0)
        att_ec, _ = engine().collect_effects(
            [make_hero_sel(skill)], [], TriggerType.TURN_START,
            context=None, rng_fn=lambda: 0.9999
        )
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.5)


# ── effect routing ────────────────────────────────────────────────────────────

class TestEffectRouting:
    def test_damage_up_goes_to_att_ec(self):
        skill = make_static_damage_up_skill()
        att_ec, def_ec = engine().collect_effects([make_hero_sel(skill)], [], TriggerType.TURN_START, context=None)
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) > 1.0
        assert def_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_defense_up_goes_to_def_ec(self):
        defn = HeroSkillDefinition(
            id=3, name="DefenseUp", activation=ALWAYS, trigger=TriggerType.ALWAYS,
            effects=[make_defense_up_effect(op=111)],
            conditions=[],
            level_data={1: SkillLevelData(skill_id=3, level=1, activation_chance=None, values={111: 25.0})},
        )
        att_ec, def_ec = engine().collect_effects([make_hero_sel(defn)], [], TriggerType.TURN_START, context=None)
        assert def_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.25)
        assert att_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)


# ── multiple skills stacking ──────────────────────────────────────────────────

class TestSkillStacking:
    def test_same_op_stacks_additively(self):
        s1 = make_static_damage_up_skill(skill_id=1, op=101, value=50.0)
        s2 = make_static_damage_up_skill(skill_id=2, op=101, value=30.0)
        att_ec, _ = engine().collect_effects(
            [make_hero_sel(s1), make_hero_sel(s2)], [], TriggerType.TURN_START, context=None
        )
        # same op → additive: (1 + 80/100) = 1.8
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.8)

    def test_different_ops_stack_multiplicatively(self):
        s1 = make_static_damage_up_skill(skill_id=1, op=101, value=50.0)
        s2 = make_static_damage_up_skill(skill_id=2, op=102, value=50.0)
        att_ec, _ = engine().collect_effects(
            [make_hero_sel(s1), make_hero_sel(s2)], [], TriggerType.TURN_START, context=None
        )
        # different ops → multiplicative: 1.5 * 1.5 = 2.25
        assert att_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(2.25)


# ── compute_skill_mod ─────────────────────────────────────────────────────────

class TestComputeSkillMod:
    def test_no_effects_returns_one(self):
        from yacfks.app.battle.skills.effect_collection import EffectCollection
        assert engine().compute_skill_mod(EffectCollection(), EffectCollection()) == pytest.approx(1.0)

    def test_damage_up_increases_mod(self):
        skill = make_static_damage_up_skill(value=50.0)
        att_ec, def_ec = engine().collect_effects([make_hero_sel(skill)], [], TriggerType.TURN_START, context=None)
        assert engine().compute_skill_mod(att_ec, def_ec) == pytest.approx(1.5)

    def test_defense_up_decreases_mod(self):
        defn = HeroSkillDefinition(
            id=3, name="DefenseUp", activation=ALWAYS, trigger=TriggerType.ALWAYS,
            effects=[make_defense_up_effect(op=111)],
            conditions=[],
            level_data={1: SkillLevelData(skill_id=3, level=1, activation_chance=None, values={111: 100.0})},
        )
        att_ec, def_ec = engine().collect_effects([make_hero_sel(defn)], [], TriggerType.TURN_START, context=None)
        # def_ec DEFENSE_UP = 2.0 → skill_mod = 1.0 / 2.0 = 0.5
        assert engine().compute_skill_mod(att_ec, def_ec) == pytest.approx(0.5)

    def test_amane_plus_chenko_example(self):
        # Community example: Amane op=102 +50%, Chenko op=101 +50% → DamageUp = 2.25
        s1 = make_static_damage_up_skill(skill_id=1, op=102, value=50.0)
        s2 = make_static_damage_up_skill(skill_id=2, op=101, value=50.0)
        att_ec, def_ec = engine().collect_effects(
            [make_hero_sel(s1), make_hero_sel(s2)], [], TriggerType.TURN_START, context=None
        )
        assert engine().compute_skill_mod(att_ec, def_ec) == pytest.approx(2.25)


# ── troop skills ──────────────────────────────────────────────────────────────

def _make_anti_cav_skill() -> TroopSkill:
    """INF T1+ skill: +10% TROOP_DAMAGE_UP, only when targeting CAV."""
    return TroopSkill(
        id=201, name="Anti-Cavalry Charge",
        activation=ALWAYS,
        trigger=TriggerType.ATTACK,
        effects=[SkillEffect(
            effect_type=EffectType.TROOP_DAMAGE_UP,
            effect_op=201,
            target_rule=SELF_TARGET,
            duration=DURATION_1,
        )],
        conditions=[RequiresTargetTroopType(TroopType.CAV)],
        level_data={1: SkillLevelData(skill_id=201, level=1, activation_chance=None, values={201: 10.0})},
    )


class TestTroopSkills:
    def test_troop_damage_up_fires_when_target_matches(self):
        ctx = make_skill_context(defender_troop_type=TroopType.CAV)
        att_ec, _ = engine().collect_effects([], [_make_anti_cav_skill()], TriggerType.ATTACK, context=ctx)
        assert att_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP) == pytest.approx(1.10)

    def test_troop_damage_up_does_not_fire_when_target_is_wrong(self):
        ctx = make_skill_context(defender_troop_type=TroopType.INF)
        att_ec, _ = engine().collect_effects([], [_make_anti_cav_skill()], TriggerType.ATTACK, context=ctx)
        assert att_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP) == pytest.approx(1.0)

    def test_troop_damage_up_does_not_fire_when_no_context(self):
        att_ec, _ = engine().collect_effects([], [_make_anti_cav_skill()], TriggerType.ATTACK, context=None)
        assert att_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP) == pytest.approx(1.0)

    def test_troop_skill_mod_includes_troop_damage_up_on_correct_target(self):
        ctx = make_skill_context(defender_troop_type=TroopType.CAV)
        att_ec, def_ec = engine().collect_effects([], [_make_anti_cav_skill()], TriggerType.ATTACK, context=ctx)
        assert engine().compute_skill_mod(att_ec, def_ec) == pytest.approx(1.10)
