import pytest
from yacfks.app.battle.skills.skill_engine import SkillEngine
from yacfks.app.battle.skills.enums import EffectType, TriggerType, TargetScope, StackRule
from yacfks.app.battle.skills.definitions import SkillEffect, SkillLevelData
from yacfks.app.battle.skills.conditions import RandomChanceCondition, RequiresTargetTroopType
from yacfks.app.battle.skills.skill_context import SkillContext
from yacfks.app.battle.skills.statuses import ActiveStatus, StatusApplication, StatusDefinition, register_status
from yacfks.app.battle.battle_state import BattleState
from yacfks.app.battle.battle_line_state import BattleLineState
from yacfks.app.domains.hero import HeroSkillDefinition, HeroSkillSelection
from yacfks.app.domains.troop import TroopSkill
from yacfks.app.domains.enums import TroopType, BattleSide


# ── Test infrastructure ───────────────────────────────────────────────────────

SELF_TARGET = TargetScope.SELF_ARMY
ENEMY_TARGET = TargetScope.ENEMY_ARMY


def make_minimal_battle_state() -> BattleState:
    line = lambda: BattleLineState(1000)
    return BattleState(
        attacker_inf=line(), attacker_cav=line(), attacker_arch=line(),
        defender_inf=line(), defender_cav=line(), defender_arch=line(),
    )


def make_always_context(side: BattleSide = BattleSide.ATTACKER, state: BattleState = None) -> SkillContext:
    return SkillContext(
        battle_context=None,
        battle_state=state or make_minimal_battle_state(),
        attacking_side=side,
        attacker_troop_type=None,
        defender_troop_type=None,
    )


def make_hero_sel(defn: HeroSkillDefinition, level: int = 1) -> HeroSkillSelection:
    return HeroSkillSelection(definition=defn, level=level)


def engine() -> SkillEngine:
    return SkillEngine()


# ── Shared test StatusDefinitions (IDs 8100-8199) ────────────────────────────

_T_DAMAGE_UP_101 = register_status(StatusDefinition(
    id=8101, name="Test DamageUp 101", duration=-1,
    effects=[SkillEffect(EffectType.DAMAGE_UP, 101, SELF_TARGET)],
    stack_rule=StackRule.STACK,
))
_T_DAMAGE_UP_102 = register_status(StatusDefinition(
    id=8102, name="Test DamageUp 102", duration=-1,
    effects=[SkillEffect(EffectType.DAMAGE_UP, 102, SELF_TARGET)],
    stack_rule=StackRule.STACK,
))
_T_DEFENSE_UP_111 = register_status(StatusDefinition(
    id=8103, name="Test DefenseUp 111", duration=-1,
    effects=[SkillEffect(EffectType.DEFENSE_UP, 111, SELF_TARGET)],
    stack_rule=StackRule.STACK,
))
_T_TROOP_DAMAGE_UP_201 = register_status(StatusDefinition(
    id=8104, name="Test TroopDamageUp 201", duration=-1,
    effects=[SkillEffect(EffectType.TROOP_DAMAGE_UP, 201, SELF_TARGET)],
    stack_rule=StackRule.STACK,
))
_T_RNG_CURSE_199 = register_status(StatusDefinition(
    id=8105, name="Test RNG Curse 199", duration=1,
    apply_delay=1,  # curse activates next turn
    effects=[SkillEffect(EffectType.DAMAGE_UP, 199, ENEMY_TARGET)],
    stack_rule=StackRule.UNIQUE,
))


def _always_apply_status_skill(status_def: StatusDefinition, values: dict, skill_id: int = 1) -> HeroSkillDefinition:
    """ALWAYS skill that applies the given status on own side."""
    return HeroSkillDefinition(
        id=skill_id, name=f"Test-{status_def.name}",
        trigger=TriggerType.ALWAYS,
        status_applications=[StatusApplication(status_def, TargetScope.SELF_ARMY)],
        conditions=[],
        level_data={1: SkillLevelData(skill_id=skill_id, level=1, values=values)},
    )


def _rng_ts_apply_status_skill(
    status_def: StatusDefinition,
    values: dict,
    chance: float = 0.5,
    skill_id: int = 2,
    target: TargetScope = None,
) -> HeroSkillDefinition:
    """TURN_START RNG skill that applies the given status."""
    return HeroSkillDefinition(
        id=skill_id, name=f"RNG-{status_def.name}",
        trigger=TriggerType.TURN_START,
        status_applications=[StatusApplication(status_def, target or TargetScope.SELF_ARMY)],
        conditions=[RandomChanceCondition(chance=chance)],
        level_data={1: SkillLevelData(skill_id=skill_id, level=1, values=values)},
    )


def _collect_numerator(state, att_side=BattleSide.ATTACKER, att_type=TroopType.INF, def_side=BattleSide.DEFENDER, target_type=TroopType.INF):
    return engine().collect_phase_effects(state.active_statuses, att_side, att_type, def_side, target_type)[0]


def _collect_denominator(state, att_side=BattleSide.ATTACKER, att_type=TroopType.INF, def_side=BattleSide.DEFENDER, target_type=TroopType.INF):
    return engine().collect_phase_effects(state.active_statuses, att_side, att_type, def_side, target_type)[1]


# ── No-skill baseline ─────────────────────────────────────────────────────────

class TestNoSkills:
    def test_empty_skills_returns_unit_mod(self):
        from yacfks.app.battle.skills.effect_collection import EffectCollection
        assert engine().compute_skill_mod(EffectCollection(), EffectCollection()) == 1.0


# ── ALWAYS skills: fire once, create permanent statuses ───────────────────────

class TestAlwaysSkills:
    def test_always_skill_creates_permanent_active_status(self):
        state = make_minimal_battle_state()
        skill = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0})
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ALWAYS, make_always_context(state=state))
        assert len(state.active_statuses) == 1
        assert state.active_statuses[0].remaining_turns == -1

    def test_always_skill_does_not_go_to_pending(self):
        state = make_minimal_battle_state()
        skill = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0})
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ALWAYS, make_always_context(state=state))
        assert len(state.pending_statuses) == 0

    def test_always_skill_does_not_fire_at_turn_start(self):
        state = make_minimal_battle_state()
        skill = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0})
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.TURN_START, make_always_context(state=state))
        assert len(state.active_statuses) == 0

    def test_always_skill_does_not_fire_at_attack(self):
        state = make_minimal_battle_state()
        skill = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0})
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ATTACK, make_always_context(state=state))
        assert len(state.active_statuses) == 0

    def test_turn_start_skill_does_not_fire_at_attack(self):
        state = make_minimal_battle_state()
        skill = _rng_ts_apply_status_skill(_T_RNG_CURSE_199, {199: 40.0})
        engine().collect_effects(
            [make_hero_sel(skill)], [], TriggerType.ATTACK,
            make_always_context(state=state), rng_fn=lambda: 0.0,
        )
        assert len(state.pending_statuses) == 0

    def test_attack_skill_does_not_fire_at_turn_start(self):
        state = make_minimal_battle_state()
        ctx = make_always_context(state=state)
        ctx.defender_troop_type = TroopType.CAV
        troop_skill = _make_anti_cav_skill()
        engine().collect_effects([], [troop_skill], TriggerType.TURN_START, ctx)
        assert len(state.active_statuses) == 0


# ── RNG gate via RandomChanceCondition ────────────────────────────────────────

class TestRngSkills:
    def test_rng_skill_creates_status_when_roll_below_chance(self):
        state = make_minimal_battle_state()
        skill = _rng_ts_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0}, chance=0.5)
        engine().collect_effects(
            [make_hero_sel(skill)], [], TriggerType.TURN_START,
            make_always_context(state=state), rng_fn=lambda: 0.0,
        )
        assert len(state.active_statuses) == 1

    def test_rng_skill_creates_no_status_when_roll_at_or_above_chance(self):
        state = make_minimal_battle_state()
        skill = _rng_ts_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0}, chance=0.5)
        engine().collect_effects(
            [make_hero_sel(skill)], [], TriggerType.TURN_START,
            make_always_context(state=state), rng_fn=lambda: 0.5,
        )
        assert len(state.active_statuses) == 0

    def test_rng_skill_with_100_chance_always_fires(self):
        state = make_minimal_battle_state()
        skill = _rng_ts_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0}, chance=1.0)
        engine().collect_effects(
            [make_hero_sel(skill)], [], TriggerType.TURN_START,
            make_always_context(state=state), rng_fn=lambda: 0.9999,
        )
        assert len(state.active_statuses) == 1

    def test_two_skills_get_separate_rolls(self):
        # Two independent skills each get their own RNG roll
        state = make_minimal_battle_state()
        s1 = _rng_ts_apply_status_skill(_T_DAMAGE_UP_101, {101: 20.0}, chance=0.5, skill_id=1)
        s2 = _rng_ts_apply_status_skill(_T_DAMAGE_UP_102, {102: 30.0}, chance=0.5, skill_id=2)
        rolls = iter([0.0, 0.9])  # s1 hits, s2 misses
        engine().collect_effects(
            [make_hero_sel(s1), make_hero_sel(s2)], [], TriggerType.TURN_START,
            make_always_context(state=state), rng_fn=lambda: next(rolls),
        )
        assert len(state.active_statuses) == 1
        assert state.active_statuses[0].definition.id == 8101


# ── Effect routing through collect_phase_effects ──────────────────────────────

class TestEffectRouting:
    def test_damage_up_on_attacker_goes_to_numerator(self):
        state = make_minimal_battle_state()
        skill = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 30.0})
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ALWAYS, make_always_context(BattleSide.ATTACKER, state))
        n_ec, d_ec = engine().collect_phase_effects(state.active_statuses, BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.30)
        assert d_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_defense_up_on_defender_goes_to_denominator_when_attacker_attacks(self):
        state = make_minimal_battle_state()
        skill = _always_apply_status_skill(_T_DEFENSE_UP_111, {111: 25.0}, skill_id=3)
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ALWAYS, make_always_context(BattleSide.DEFENDER, state))
        n_ec, d_ec = engine().collect_phase_effects(state.active_statuses, BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.25)
        assert n_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)

    def test_attacker_damage_up_not_in_numerator_when_defender_attacks(self):
        state = make_minimal_battle_state()
        skill = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0})
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ALWAYS, make_always_context(BattleSide.ATTACKER, state))
        n_ec, _ = engine().collect_phase_effects(state.active_statuses, BattleSide.DEFENDER, TroopType.INF, BattleSide.ATTACKER, TroopType.INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_defender_defense_up_not_in_denominator_when_defender_attacks(self):
        state = make_minimal_battle_state()
        skill = _always_apply_status_skill(_T_DEFENSE_UP_111, {111: 25.0}, skill_id=3)
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ALWAYS, make_always_context(BattleSide.DEFENDER, state))
        _, d_ec = engine().collect_phase_effects(state.active_statuses, BattleSide.DEFENDER, TroopType.INF, BattleSide.ATTACKER, TroopType.INF)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)


# ── Stacking ──────────────────────────────────────────────────────────────────

class TestSkillStacking:
    def test_same_op_stacks_additively(self):
        state = make_minimal_battle_state()
        ctx = make_always_context(state=state)
        s1 = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0}, skill_id=1)
        s2 = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 30.0}, skill_id=2)
        engine().collect_effects([make_hero_sel(s1), make_hero_sel(s2)], [], TriggerType.ALWAYS, ctx)
        n_ec, _ = engine().collect_phase_effects(state.active_statuses, BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.8)

    def test_different_ops_stack_multiplicatively(self):
        state = make_minimal_battle_state()
        ctx = make_always_context(state=state)
        s1 = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0}, skill_id=1)
        s2 = _always_apply_status_skill(_T_DAMAGE_UP_102, {102: 50.0}, skill_id=2)
        engine().collect_effects([make_hero_sel(s1), make_hero_sel(s2)], [], TriggerType.ALWAYS, ctx)
        n_ec, _ = engine().collect_phase_effects(state.active_statuses, BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(2.25)


# ── Per-troop-scope effect routing (Triton / Thrud patterns) ─────────────────
# A single StatusDefinition can carry effects with different troop-type scopes.
# Each effect's own scope determines which attack phases it contributes to.

# Triton-like: different defense bonuses depending on which troop type is targeted
_T_TRITON_LIKE = register_status(StatusDefinition(
    id=8201, name="Test Oath-like", duration=-1,
    effects=[
        SkillEffect(EffectType.DEFENSE_UP, 301, TargetScope.SELF_INFANTRY),  # 20%
        SkillEffect(EffectType.DEFENSE_UP, 302, TargetScope.SELF_CAVALRY),  # 30%
        SkillEffect(EffectType.DEFENSE_UP, 302, TargetScope.SELF_ARCHERS),  # 30%
    ],
    stack_rule=StackRule.STACK,
))

# Thrud-like: both offensive (DAMAGE_UP) and defensive (DEFENSE_UP) effects on same troop types
_T_THRUD_LIKE = register_status(StatusDefinition(
    id=8202, name="Test Hunger-like", duration=-1,
    effects=[
        SkillEffect(EffectType.DAMAGE_UP,  401, TargetScope.SELF_INFANTRY),  # +15% offense INF
        SkillEffect(EffectType.DAMAGE_UP,  401, TargetScope.SELF_ARCHERS),  # +15% offense ARCH
        SkillEffect(EffectType.DEFENSE_UP, 402, TargetScope.SELF_INFANTRY),  # +15% defense INF
        SkillEffect(EffectType.DEFENSE_UP, 402, TargetScope.SELF_ARCHERS),  # +15% defense ARCH
    ],
    stack_rule=StackRule.STACK,
))


def _inject_status(state: BattleState, status_def: StatusDefinition, side: BattleSide, values: dict) -> None:
    """Directly plant an ActiveStatus into active_statuses for routing tests."""
    from yacfks.app.battle.skills.statuses import ActiveStatus
    state.active_statuses.append(ActiveStatus(
        definition=status_def,
        remaining_turns=-1,
        source_skill_id=status_def.id,
        target_side=side,
        target_troop=None,  # army-wide — per-effect scopes drive the troop filter
        effect_values=values,
    ))


class TestTroopScopedEffects:
    """Verify that per-effect troop scopes route correctly in collect_phase_effects."""

    # ── Triton-like ──────────────────────────────────────────────────────────

    def test_triton_inf_effect_goes_to_denominator_only_when_inf_is_target(self):
        state = make_minimal_battle_state()
        _inject_status(state, _T_TRITON_LIKE, BattleSide.DEFENDER, {301: 20.0, 302: 30.0})
        # Side A attacks Side B INF → op 301 (20%) contributes to denominator
        _, d_ec = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.20)

    def test_triton_cav_effect_goes_to_denominator_only_when_cav_is_target(self):
        state = make_minimal_battle_state()
        _inject_status(state, _T_TRITON_LIKE, BattleSide.DEFENDER, {301: 20.0, 302: 30.0})
        # Side A attacks Side B CAV → op 302 (30%) contributes to denominator
        _, d_ec = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.CAV)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.30)

    def test_triton_arch_effect_goes_to_denominator_only_when_arch_is_target(self):
        state = make_minimal_battle_state()
        _inject_status(state, _T_TRITON_LIKE, BattleSide.DEFENDER, {301: 20.0, 302: 30.0})
        _, d_ec = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.ARCH)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.30)

    def test_triton_inf_effect_absent_when_cav_is_target(self):
        # op 301 (INF-scoped 20%) should NOT appear when the target is CAV
        state = make_minimal_battle_state()
        _inject_status(state, _T_TRITON_LIKE, BattleSide.DEFENDER, {301: 20.0, 302: 30.0})
        _, d_ec = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.CAV)
        # Only op 302 (30%) contributes; op 301 (20%) is absent → no additive mix
        # 1.30 not 1.50 (which would be 20%+30% combined)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.30)

    def test_triton_status_on_attacker_does_not_affect_denominator(self):
        # Triton on Side A should not reduce Side A's OWN attack phases
        state = make_minimal_battle_state()
        _inject_status(state, _T_TRITON_LIKE, BattleSide.ATTACKER, {301: 20.0, 302: 30.0})
        _, d_ec = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)

    # ── Thrud-like ────────────────────────────────────────────────────────────

    def test_thrud_damage_up_goes_to_numerator_when_inf_attacks(self):
        state = make_minimal_battle_state()
        _inject_status(state, _T_THRUD_LIKE, BattleSide.ATTACKER, {401: 15.0, 402: 15.0})
        n_ec, _ = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.15)

    def test_thrud_damage_up_absent_when_cav_attacks(self):
        # Thrud only buffs INF and ARCH; CAV attack phase should see no DAMAGE_UP
        state = make_minimal_battle_state()
        _inject_status(state, _T_THRUD_LIKE, BattleSide.ATTACKER, {401: 15.0, 402: 15.0})
        n_ec, _ = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.CAV, BattleSide.DEFENDER, TroopType.INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_thrud_damage_up_goes_to_numerator_when_arch_attacks(self):
        state = make_minimal_battle_state()
        _inject_status(state, _T_THRUD_LIKE, BattleSide.ATTACKER, {401: 15.0, 402: 15.0})
        n_ec, _ = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.ARCH, BattleSide.DEFENDER, TroopType.INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.15)

    def test_thrud_defense_up_goes_to_denominator_when_inf_is_attacked(self):
        state = make_minimal_battle_state()
        _inject_status(state, _T_THRUD_LIKE, BattleSide.DEFENDER, {401: 15.0, 402: 15.0})
        # Side A attacks Side B INF → Thrud's DEFENSE_UP for INF → denominator
        _, d_ec = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.15)

    def test_thrud_defense_up_absent_when_cav_is_attacked(self):
        state = make_minimal_battle_state()
        _inject_status(state, _T_THRUD_LIKE, BattleSide.DEFENDER, {401: 15.0, 402: 15.0})
        _, d_ec = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.CAV)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)

    def test_thrud_both_sides_have_thrud_independent(self):
        # Side A: Thrud buffs ATT INF offense; Side B: Thrud buffs DEF INF defense
        # Both active simultaneously in the same phase (ATT=INF targets DEF=INF)
        state = make_minimal_battle_state()
        _inject_status(state, _T_THRUD_LIKE, BattleSide.ATTACKER, {401: 15.0, 402: 15.0})
        _inject_status(state, _T_THRUD_LIKE, BattleSide.DEFENDER, {401: 15.0, 402: 15.0})
        n_ec, d_ec = engine().collect_phase_effects(state.active_statuses,
            BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP)  == pytest.approx(1.15)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.15)


# ── compute_skill_mod ─────────────────────────────────────────────────────────

class TestComputeSkillMod:
    def test_no_effects_returns_one(self):
        from yacfks.app.battle.skills.effect_collection import EffectCollection
        assert engine().compute_skill_mod(EffectCollection(), EffectCollection()) == pytest.approx(1.0)

    def test_damage_up_increases_mod(self):
        state = make_minimal_battle_state()
        s = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0})
        engine().collect_effects([make_hero_sel(s)], [], TriggerType.ALWAYS, make_always_context(state=state))
        n_ec, d_ec = engine().collect_phase_effects(state.active_statuses, BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert engine().compute_skill_mod(n_ec, d_ec) == pytest.approx(1.5)

    def test_defense_up_decreases_mod(self):
        state = make_minimal_battle_state()
        s = _always_apply_status_skill(_T_DEFENSE_UP_111, {111: 100.0}, skill_id=3)
        engine().collect_effects([make_hero_sel(s)], [], TriggerType.ALWAYS, make_always_context(BattleSide.DEFENDER, state))
        n_ec, d_ec = engine().collect_phase_effects(state.active_statuses, BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert engine().compute_skill_mod(n_ec, d_ec) == pytest.approx(0.5)

    def test_amane_plus_chenko_example(self):
        state = make_minimal_battle_state()
        ctx = make_always_context(state=state)
        s1 = _always_apply_status_skill(_T_DAMAGE_UP_102, {102: 50.0}, skill_id=1)
        s2 = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 50.0}, skill_id=2)
        engine().collect_effects([make_hero_sel(s1), make_hero_sel(s2)], [], TriggerType.ALWAYS, ctx)
        n_ec, d_ec = engine().collect_phase_effects(state.active_statuses, BattleSide.ATTACKER, TroopType.INF, BattleSide.DEFENDER, TroopType.INF)
        assert engine().compute_skill_mod(n_ec, d_ec) == pytest.approx(2.25)


# ── Troop skills (ATTACK trigger, direct EC routing) ──────────────────────────

def _make_anti_cav_skill() -> TroopSkill:
    return TroopSkill(
        id=201, name="Anti-Cavalry Charge",
        trigger=TriggerType.ATTACK,
        effects=[SkillEffect(EffectType.TROOP_DAMAGE_UP, 201, SELF_TARGET)],
        conditions=[RequiresTargetTroopType(TroopType.CAV)],
        level_data={1: SkillLevelData(skill_id=201, level=1, values={201: 10.0})},
    )


def make_skill_context(defender_troop_type: TroopType) -> SkillContext:
    return SkillContext(
        battle_context=None,
        battle_state=None,
        attacking_side=BattleSide.ATTACKER,
        attacker_troop_type=None,
        defender_troop_type=defender_troop_type,
    )


class TestTroopSkills:
    def test_troop_damage_up_fires_when_target_matches(self):
        ctx = make_skill_context(defender_troop_type=TroopType.CAV)
        n_ec, _ = engine().collect_effects([], [_make_anti_cav_skill()], TriggerType.ATTACK, context=ctx)
        assert n_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP) == pytest.approx(1.10)

    def test_troop_damage_up_does_not_fire_when_target_is_wrong(self):
        ctx = make_skill_context(defender_troop_type=TroopType.INF)
        n_ec, _ = engine().collect_effects([], [_make_anti_cav_skill()], TriggerType.ATTACK, context=ctx)
        assert n_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP) == pytest.approx(1.0)

    def test_troop_damage_up_does_not_fire_when_no_context(self):
        n_ec, _ = engine().collect_effects([], [_make_anti_cav_skill()], TriggerType.ATTACK, context=None)
        assert n_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP) == pytest.approx(1.0)

    def test_troop_skill_mod_includes_troop_damage_up_on_correct_target(self):
        ctx = make_skill_context(defender_troop_type=TroopType.CAV)
        n_ec, d_ec = engine().collect_effects([], [_make_anti_cav_skill()], TriggerType.ATTACK, context=ctx)
        assert engine().compute_skill_mod(n_ec, d_ec) == pytest.approx(1.10)


# ── APPLY_STATUS write path ───────────────────────────────────────────────────

_TEST_CURSE_STATUS = register_status(StatusDefinition(
    id=9001,
    name="TestCurse",
    duration=1,
    apply_delay=1,  # curse activates next turn
    effects=[SkillEffect(EffectType.DAMAGE_UP, 199, ENEMY_TARGET)],
    stack_rule=StackRule.UNIQUE,
))


def _make_enemy_apply_status_skill(rng: bool = False, chance: float = 0.5) -> HeroSkillDefinition:
    conditions = [RandomChanceCondition(chance=chance)] if rng else []
    return HeroSkillDefinition(
        id=9001, name="Test Evil Eye",
        trigger=TriggerType.TURN_START,
        status_applications=[StatusApplication(_TEST_CURSE_STATUS, TargetScope.ENEMY_ARMY)],
        conditions=conditions,
        level_data={1: SkillLevelData(skill_id=9001, level=1, values={199: 40.0})},
    )


def _make_status_context(state: BattleState) -> SkillContext:
    return SkillContext(
        battle_context=None, battle_state=state,
        attacking_side=BattleSide.ATTACKER,
        attacker_troop_type=TroopType.INF, defender_troop_type=TroopType.INF,
    )


class TestApplyStatus:
    def test_apply_status_no_battle_state_does_not_crash(self):
        skill = _make_enemy_apply_status_skill()
        ctx = SkillContext(
            battle_context=None, battle_state=None,
            attacking_side=BattleSide.ATTACKER,
            attacker_troop_type=None, defender_troop_type=None,
        )
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.TURN_START, context=ctx)

    def test_delayed_status_goes_to_pending_not_active(self):
        # apply_delay=1 → pending (activates next turn)
        state = make_minimal_battle_state()
        engine().collect_effects(
            [make_hero_sel(_make_enemy_apply_status_skill())], [],
            TriggerType.TURN_START, _make_status_context(state),
        )
        assert len(state.pending_statuses) == 1
        assert len(state.active_statuses) == 0

    def test_immediate_status_goes_to_active(self):
        # apply_delay=0 (default) → active immediately
        state = make_minimal_battle_state()
        skill = _always_apply_status_skill(_T_DAMAGE_UP_101, {101: 30.0})
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.ALWAYS, make_always_context(state=state))
        assert len(state.active_statuses) == 1
        assert len(state.pending_statuses) == 0

    def test_pending_status_has_correct_target_and_values(self):
        state = make_minimal_battle_state()
        engine().collect_effects(
            [make_hero_sel(_make_enemy_apply_status_skill())], [],
            TriggerType.TURN_START, _make_status_context(state),
        )
        s = state.pending_statuses[0]
        assert s.definition.id == 9001
        assert s.target_side == BattleSide.DEFENDER
        assert s.effect_values == {199: 40.0}
        assert s.remaining_turns == 1

    def test_rng_miss_creates_no_status(self):
        state = make_minimal_battle_state()
        engine().collect_effects(
            [make_hero_sel(_make_enemy_apply_status_skill(rng=True, chance=0.5))], [],
            TriggerType.TURN_START, _make_status_context(state),
            rng_fn=lambda: 0.9,
        )
        assert len(state.pending_statuses) == 0

    def test_unique_does_not_stack_twice(self):
        state = make_minimal_battle_state()
        sel = make_hero_sel(_make_enemy_apply_status_skill())
        engine().collect_effects([sel, sel], [], TriggerType.TURN_START, _make_status_context(state))
        assert len(state.pending_statuses) == 1

    def test_explicit_delay_zero_on_enemy_scope_is_immediate(self):
        # Skill designer can choose apply_delay=0 on an enemy-scoped status
        # for instant effects that take hold the same turn they're applied.
        instant_curse = register_status(StatusDefinition(
            id=9002, name="ImmediateCurse", duration=1,
            apply_delay=0,
            effects=[SkillEffect(EffectType.DAMAGE_UP, 198, ENEMY_TARGET)],
            stack_rule=StackRule.UNIQUE,
        ))
        skill = HeroSkillDefinition(
            id=9002, name="Instant Terror",
            trigger=TriggerType.TURN_START,
            status_applications=[StatusApplication(instant_curse, TargetScope.ENEMY_ARMY)],
            conditions=[],
            level_data={1: SkillLevelData(skill_id=9002, level=1, values={198: 25.0})},
        )
        state = make_minimal_battle_state()
        engine().collect_effects([make_hero_sel(skill)], [], TriggerType.TURN_START, _make_status_context(state))
        assert len(state.active_statuses) == 1
        assert len(state.pending_statuses) == 0
