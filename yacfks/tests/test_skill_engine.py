import pytest
from yacfks.app.battle.skills.skill_engine import SkillEngine
from yacfks.app.battle.skills.effect_collection import EffectCollection
from yacfks.app.battle.skills.enums import EffectType, TriggerType, TargetScope, StackRule
from yacfks.app.battle.skills.definitions import EffectSpec, SkillLevelData
from yacfks.app.battle.skills.conditions import RandomChanceCondition
from yacfks.app.battle.phase_context import PhaseContext
from yacfks.app.battle.skills.statuses import ActiveEffect
from yacfks.app.battle.battle_state import BattleState
from yacfks.app.battle.battle_line_state import BattleLineState
from yacfks.app.battle.skills.definitions import HeroSkillDefinition, TroopSkillDefinition, HeroSkillSelection
from yacfks.app.domains.enums import TroopType, BattleSide

# ── Skill engine, one instance for the whole module ───────────────────

SE = SkillEngine()

# ── Short aliases ─────────────────────────────────────────────────────────────

ATT  = BattleSide.ATTACKER
DEF  = BattleSide.DEFENDER
INF  = TroopType.INF
CAV  = TroopType.CAV
ARCH = TroopType.ARCH
ENEMY = TargetScope.ENEMY_ARMY

# ── Test infrastructure ───────────────────────────────────────────────────────

def _state() -> BattleState:
    line = lambda: BattleLineState(1000)
    return BattleState(
        attacker_inf=line(), attacker_cav=line(), attacker_arch=line(),
        defender_inf=line(), defender_cav=line(), defender_arch=line(),
    )


def _ctx(
    side: BattleSide = ATT,
    state: BattleState | None = None,
    *,
    att_type: TroopType | None = None,
    def_type: TroopType | None = None,
) -> PhaseContext:
    return PhaseContext(
        battle_context=None,
        battle_state=state or _state(),
        attacking_side=side,
        attacker_troop_type=att_type,
        defender_troop_type=def_type,
    )


def _sel(defn: HeroSkillDefinition, level: int = 1) -> HeroSkillSelection:
    return HeroSkillSelection(definition=defn, level=level)


def _inject(
    state: BattleState, spec: EffectSpec, side: BattleSide, value: float,
    target_troop: TroopType | None = None,
) -> None:
    state.get_effects(side).append(ActiveEffect(
        effect_spec=spec, remaining_turns=-1, source_skill_id=0,
        host_side=side, target_troop=target_troop, value=value,
    ))


def _inject_specs(state: BattleState, specs: list[EffectSpec], values: dict[int, float], side: BattleSide) -> None:
    for spec in specs:
        _inject(state, spec, side, values[spec.effect_op])


def _phase_ecs(state: BattleState, att_type: TroopType = INF, target_type: TroopType = INF):
    return SE.build_phase_ecs(state.get_effects(ATT), state.get_effects(DEF), att_type, target_type)


# ── Shared EffectSpecs ────────────────────────────────────────────────────────

_DUP_101 = EffectSpec(EffectType.DAMAGE_UP,  101, ENEMY)
_DUP_102 = EffectSpec(EffectType.DAMAGE_UP,  102, ENEMY)
_DEF_111 = EffectSpec(EffectType.DEFENSE_UP, 111, ENEMY)
_RNG_199 = EffectSpec(EffectType.DAMAGE_UP,  199, ENEMY, duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE)

# ── Skill factories ───────────────────────────────────────────────────────────

def _static_skill(spec: EffectSpec, values: dict, skill_id: int = 1) -> HeroSkillDefinition:
    return HeroSkillDefinition(
        id=skill_id, name=f"Test-{skill_id}",
        trigger=TriggerType.STATIC,
        effects=[spec], conditions=[],
        level_data={1: SkillLevelData(skill_id=skill_id, level=1, values=values)},
    )


def _rng_ts_skill(spec: EffectSpec, values: dict, chance: float = 0.5, skill_id: int = 2) -> HeroSkillDefinition:
    return HeroSkillDefinition(
        id=skill_id, name=f"RNG-{skill_id}",
        trigger=TriggerType.TURN_START,
        effects=[spec],
        conditions=[RandomChanceCondition(chance=chance)],
        level_data={1: SkillLevelData(skill_id=skill_id, level=1, values=values)},
    )


def _delayed_debuff_skill(rng: bool = False, chance: float = 0.5) -> HeroSkillDefinition:
    spec = EffectSpec(EffectType.DAMAGE_UP, 199, ENEMY, duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE)
    return HeroSkillDefinition(
        id=9001, name="Test Debuff",
        trigger=TriggerType.TURN_START,
        effects=[spec],
        conditions=[RandomChanceCondition(chance=chance)] if rng else [],
        level_data={1: SkillLevelData(skill_id=9001, level=1, values={199: 40.0})},
    )


def _make_turn_start_anti_cav_skill() -> TroopSkillDefinition:
    return TroopSkillDefinition(
        id=201, name="Anti-Cavalry Charge",
        trigger=TriggerType.TURN_START,
        effects=[EffectSpec(EffectType.TROOP_DAMAGE_UP, 201, TargetScope.ENEMY_CAVALRY,
                            benefactor_scope=TargetScope.SELF_INFANTRY, duration=1)],
        conditions=[],
        level_data={1: SkillLevelData(skill_id=201, level=1, values={201: 10.0})},
    )


def _make_ambusher_skill(chance: float = 0.20) -> TroopSkillDefinition:
    return TroopSkillDefinition(
        id=20, name="Ambusher",
        trigger=TriggerType.TROOP_SPECIAL,
        effects=[EffectSpec(EffectType.RETARGET, 0, TargetScope.ENEMY_ARMY)],
        conditions=[RandomChanceCondition(chance=chance)],
        level_data={1: SkillLevelData(skill_id=20, level=1, values={0: 1.0})},
    )


# ── Per-troop-scope test data (Triton / Thrud patterns) ──────────────────────

_T_TRITON_SPECS = [
    EffectSpec(EffectType.DEFENSE_UP, 301, ENEMY, benefactor_scope=TargetScope.SELF_INFANTRY),
    EffectSpec(EffectType.DEFENSE_UP, 302, ENEMY, benefactor_scope=TargetScope.SELF_CAVALRY),
    EffectSpec(EffectType.DEFENSE_UP, 302, ENEMY, benefactor_scope=TargetScope.SELF_ARCHERS),
]
_T_TRITON_VALUES = {301: 20.0, 302: 30.0}

_T_THRUD_SPECS = [
    EffectSpec(EffectType.DAMAGE_UP,  401, ENEMY, benefactor_scope=TargetScope.SELF_INFANTRY),
    EffectSpec(EffectType.DAMAGE_UP,  401, ENEMY, benefactor_scope=TargetScope.SELF_ARCHERS),
    EffectSpec(EffectType.DEFENSE_UP, 402, ENEMY, benefactor_scope=TargetScope.SELF_INFANTRY),
    EffectSpec(EffectType.DEFENSE_UP, 402, ENEMY, benefactor_scope=TargetScope.SELF_ARCHERS),
]
_T_THRUD_VALUES = {401: 15.0, 402: 15.0}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestStaticSkills:
    def test_creates_permanent_active_effect(self):
        state = _state()
        SE.evaluate_skills(
            [_sel(_static_skill(_DUP_101, {101: 50.0}))], [],
            TriggerType.STATIC,
            _ctx(state=state)
        )
        assert len(state.attacker_active_effects) == 1
        assert state.attacker_active_effects[0].remaining_turns == -1

    def test_does_not_go_to_pending(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, {101: 50.0}))], [], TriggerType.STATIC, _ctx(state=state))
        assert len(state.attacker_pending_effects) == 0

    @pytest.mark.parametrize("trigger", [TriggerType.TURN_START, TriggerType.PHASE, TriggerType.TROOP_SPECIAL])
    def test_does_not_fire_at_other_triggers(self, trigger):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, {101: 50.0}))], [], trigger, _ctx(state=state))
        assert len(state.attacker_active_effects) == 0

    def test_turn_start_skill_does_not_fire_at_phase(self):
        state = _state()
        SE.evaluate_skills([_sel(_rng_ts_skill(_RNG_199, {199: 40.0}))], [], TriggerType.PHASE,
                           _ctx(state=state), rng_fn=lambda: 0.0)
        assert len(state.attacker_pending_effects) == 0

class TestRngSkills:
    @pytest.mark.parametrize("roll,expected_count", [(0.0, 1), (0.5, 0)])
    def test_rng_gate(self, roll, expected_count):
        state = _state()
        SE.evaluate_skills([_sel(_rng_ts_skill(_DUP_101, {101: 50.0}, chance=0.5))], [],
                           TriggerType.TURN_START, _ctx(state=state), rng_fn=lambda: roll)
        assert len(state.attacker_active_effects) == expected_count

    def test_100_chance_always_fires(self):
        state = _state()
        SE.evaluate_skills([_sel(_rng_ts_skill(_DUP_101, {101: 50.0}, chance=1.0))], [],
                           TriggerType.TURN_START, _ctx(state=state), rng_fn=lambda: 0.9999)
        assert len(state.attacker_active_effects) == 1

    def test_two_skills_get_separate_rolls(self):
        state = _state()
        s1 = _rng_ts_skill(_DUP_101, {101: 20.0}, chance=0.5, skill_id=1)
        s2 = _rng_ts_skill(_DUP_102, {102: 30.0}, chance=0.5, skill_id=2)
        rolls = iter([0.0, 0.9])  # s1 hits, s2 misses
        SE.evaluate_skills([_sel(s1), _sel(s2)], [], TriggerType.TURN_START,
                           _ctx(state=state), rng_fn=lambda: next(rolls))
        assert len(state.attacker_active_effects) == 1
        assert state.attacker_active_effects[0].source_skill_id == 1


class TestEffectRouting:
    def test_damage_up_on_attacker_goes_to_numerator(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, {101: 30.0}))], [], TriggerType.STATIC, _ctx(ATT, state))
        n_ec, d_ec = _phase_ecs(state)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.30)
        assert d_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_defense_up_on_defender_goes_to_denominator(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DEF_111, {111: 25.0}, skill_id=3))], [], TriggerType.STATIC, _ctx(DEF, state))
        n_ec, d_ec = _phase_ecs(state)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.25)
        assert n_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)

    def test_attacker_buff_absent_when_defender_is_phase_attacker(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, {101: 50.0}))], [], TriggerType.STATIC, _ctx(ATT, state))
        n_ec, _ = SE.build_phase_ecs(state.get_effects(DEF), state.get_effects(ATT), INF, INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_defender_defense_absent_when_defender_is_phase_attacker(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DEF_111, {111: 25.0}, skill_id=3))], [], TriggerType.STATIC, _ctx(DEF, state))
        _, d_ec = SE.build_phase_ecs(state.get_effects(DEF), state.get_effects(ATT), INF, INF)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)


class TestSkillStacking:
    def test_same_op_stacks_additively(self):
        state = _state()
        s1 = _static_skill(_DUP_101, {101: 50.0}, skill_id=1)
        s2 = _static_skill(_DUP_101, {101: 30.0}, skill_id=2)
        SE.evaluate_skills([_sel(s1), _sel(s2)], [], TriggerType.STATIC, _ctx(state=state))
        n_ec, _ = _phase_ecs(state)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.8)

    def test_different_ops_stack_multiplicatively(self):
        state = _state()
        s1 = _static_skill(_DUP_101, {101: 50.0}, skill_id=1)
        s2 = _static_skill(_DUP_102, {102: 50.0}, skill_id=2)
        SE.evaluate_skills([_sel(s1), _sel(s2)], [], TriggerType.STATIC, _ctx(state=state))
        n_ec, _ = _phase_ecs(state)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(2.25)


class TestComputeSkillMod:
    def test_no_effects_returns_one(self):
        assert SE.compute_skill_mod(EffectCollection(), EffectCollection()) == pytest.approx(1.0)

    def test_damage_up_increases_mod(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, {101: 50.0}))], [], TriggerType.STATIC, _ctx(state=state))
        assert SE.compute_skill_mod(*_phase_ecs(state)) == pytest.approx(1.5)

    def test_defense_up_decreases_mod(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DEF_111, {111: 100.0}, skill_id=3))], [], TriggerType.STATIC, _ctx(DEF, state))
        assert SE.compute_skill_mod(*_phase_ecs(state)) == pytest.approx(0.5)

    def test_amane_plus_chenko(self):
        state = _state()
        s1 = _static_skill(_DUP_102, {102: 50.0}, skill_id=1)
        s2 = _static_skill(_DUP_101, {101: 50.0}, skill_id=2)
        SE.evaluate_skills([_sel(s1), _sel(s2)], [], TriggerType.STATIC, _ctx(state=state))
        assert SE.compute_skill_mod(*_phase_ecs(state)) == pytest.approx(2.25)


class TestTurnStartTroopSkills:
    def test_creates_active_effect_with_turn_duration(self):
        state = _state()
        SE.evaluate_skills([], [_make_turn_start_anti_cav_skill()], TriggerType.TURN_START, _ctx(state=state))
        assert len(state.attacker_active_effects) == 1
        assert state.attacker_active_effects[0].remaining_turns == 1

    @pytest.mark.parametrize("trigger", [TriggerType.PHASE, TriggerType.TROOP_SPECIAL])
    def test_does_not_fire_at_wrong_trigger(self, trigger):
        state = _state()
        SE.evaluate_skills([], [_make_turn_start_anti_cav_skill()], trigger, _ctx(state=state))
        assert len(state.attacker_active_effects) == 0

    def test_contributes_when_attacking_correct_enemy_type(self):
        state = _state()
        SE.evaluate_skills([], [_make_turn_start_anti_cav_skill()], TriggerType.TURN_START, _ctx(state=state))
        n_ec, _ = _phase_ecs(state, INF, CAV)
        assert n_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP) == pytest.approx(1.10)

    @pytest.mark.parametrize("att,tgt", [
        pytest.param(INF, INF, id="wrong-target"),
        pytest.param(CAV, CAV, id="wrong-benefactor"),
    ])
    def test_absent_when_scope_does_not_match(self, att, tgt):
        state = _state()
        SE.evaluate_skills([], [_make_turn_start_anti_cav_skill()], TriggerType.TURN_START, _ctx(state=state))
        n_ec, _ = _phase_ecs(state, att, tgt)
        assert n_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP) == pytest.approx(1.0)


class TestCollectRetarget:
    def test_returns_true_when_rng_passes(self):
        assert SE.collect_retarget([_make_ambusher_skill(chance=0.5)], _ctx(), rng_fn=lambda: 0.0) is True

    def test_returns_false_when_rng_fails(self):
        assert SE.collect_retarget([_make_ambusher_skill(chance=0.5)], _ctx(), rng_fn=lambda: 0.5) is False

    def test_returns_false_with_no_skills(self):
        assert SE.collect_retarget([], _ctx()) is False

    def test_skips_non_troop_special_trigger(self):
        # a TURN_START troop skill with RETARGET effect must not be picked up
        wrong_trigger = TroopSkillDefinition(
            id=99, name="Wrong Trigger",
            trigger=TriggerType.TURN_START,
            effects=[EffectSpec(EffectType.RETARGET, 0, TargetScope.ENEMY_ARMY)],
            conditions=[],
            level_data={1: SkillLevelData(skill_id=99, level=1, values={0: 1.0})},
        )
        assert SE.collect_retarget([wrong_trigger], _ctx(), rng_fn=lambda: 0.0) is False

    def test_skips_troop_special_without_retarget_effect(self):
        # a TROOP_SPECIAL skill that is not a RETARGET (e.g. future Volley) must not fire here
        volley_like = TroopSkillDefinition(
            id=98, name="Volley-like",
            trigger=TriggerType.TROOP_SPECIAL,
            effects=[EffectSpec(EffectType.EXTRA_ATTACK_PHASE, 0, TargetScope.ENEMY_ARMY)],
            conditions=[],
            level_data={1: SkillLevelData(skill_id=98, level=1, values={0: 1.0})},
        )
        assert SE.collect_retarget([volley_like], _ctx(), rng_fn=lambda: 0.0) is False


class TestTroopScopedEffects:
    """Verify that per-effect troop scopes route correctly in build_phase_ecs."""

    # ── Triton-like (per-benefactor DEFENSE_UP) ───────────────────────────────

    @pytest.mark.parametrize("target,expected", [
        pytest.param(INF,  1.20, id="inf-target-op301"),
        pytest.param(CAV,  1.30, id="cav-target-op302"),
        pytest.param(ARCH, 1.30, id="arch-target-op302"),
    ])
    def test_triton_denominator_scales_with_target(self, target, expected):
        state = _state()
        _inject_specs(state, _T_TRITON_SPECS, _T_TRITON_VALUES, DEF)
        _, d_ec = _phase_ecs(state, INF, target)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(expected)

    def test_triton_inf_op_absent_when_cav_is_target(self):
        # op 301 (20% INF) must not bleed into CAV result — only op 302 (30%) applies
        state = _state()
        _inject_specs(state, _T_TRITON_SPECS, _T_TRITON_VALUES, DEF)
        _, d_ec = _phase_ecs(state, INF, CAV)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.30)

    def test_triton_on_attacker_does_not_affect_denominator(self):
        state = _state()
        _inject_specs(state, _T_TRITON_SPECS, _T_TRITON_VALUES, ATT)
        _, d_ec = _phase_ecs(state)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)

    # ── Thrud-like (INF+ARCH only) ────────────────────────────────────────────

    @pytest.mark.parametrize("att_type,expected", [
        pytest.param(INF,  1.15, id="inf-attacker"),
        pytest.param(ARCH, 1.15, id="arch-attacker"),
        pytest.param(CAV,  1.0,  id="cav-attacker-no-buff"),
    ])
    def test_thrud_damage_up_by_attacker_type(self, att_type, expected):
        state = _state()
        _inject_specs(state, _T_THRUD_SPECS, _T_THRUD_VALUES, ATT)
        n_ec, _ = _phase_ecs(state, att_type, INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(expected)

    @pytest.mark.parametrize("target,expected", [
        pytest.param(INF, 1.15, id="inf-target"),
        pytest.param(CAV, 1.0,  id="cav-target-no-buff"),
    ])
    def test_thrud_defense_up_by_target_type(self, target, expected):
        state = _state()
        _inject_specs(state, _T_THRUD_SPECS, _T_THRUD_VALUES, DEF)
        _, d_ec = _phase_ecs(state, INF, target)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(expected)

    def test_both_sides_have_thrud_independent(self):
        state = _state()
        _inject_specs(state, _T_THRUD_SPECS, _T_THRUD_VALUES, ATT)
        _inject_specs(state, _T_THRUD_SPECS, _T_THRUD_VALUES, DEF)
        n_ec, d_ec = _phase_ecs(state, INF, INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP)  == pytest.approx(1.15)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.15)


class TestApplyEffect:
    def test_no_battle_state_does_not_crash(self):
        ctx = PhaseContext(battle_context=None, battle_state=None,
                          attacking_side=ATT, attacker_troop_type=None, defender_troop_type=None)
        SE.evaluate_skills([_sel(_delayed_debuff_skill())], [], TriggerType.TURN_START, context=ctx)

    def test_delayed_effect_goes_to_pending_not_active(self):
        state = _state()
        SE.evaluate_skills([_sel(_delayed_debuff_skill())], [], TriggerType.TURN_START, _ctx(state=state))
        assert len(state.attacker_pending_effects) == 1
        assert len(state.attacker_active_effects) == 0

    def test_immediate_effect_goes_to_active(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, {101: 30.0}))], [], TriggerType.STATIC, _ctx(state=state))
        assert len(state.attacker_active_effects) == 1
        assert len(state.attacker_pending_effects) == 0

    def test_pending_effect_fields(self):
        state = _state()
        SE.evaluate_skills([_sel(_delayed_debuff_skill())], [], TriggerType.TURN_START, _ctx(state=state))
        ae = state.attacker_pending_effects[0]
        assert ae.source_skill_id == 9001
        assert ae.host_side == ATT
        assert ae.value == 40.0
        assert ae.remaining_turns == 1

    def test_rng_miss_creates_no_effect(self):
        state = _state()
        SE.evaluate_skills([_sel(_delayed_debuff_skill(rng=True, chance=0.5))], [],
                           TriggerType.TURN_START, _ctx(state=state), rng_fn=lambda: 0.9)
        assert len(state.attacker_pending_effects) == 0

    def test_unique_does_not_stack_twice(self):
        state = _state()
        sel = _sel(_delayed_debuff_skill())
        SE.evaluate_skills([sel, sel], [], TriggerType.TURN_START, _ctx(state=state))
        assert len(state.attacker_pending_effects) == 1

    def test_explicit_delay_zero_is_immediate(self):
        instant_spec = EffectSpec(EffectType.DAMAGE_UP, 198, ENEMY, duration=1, apply_delay=0, stack_rule=StackRule.UNIQUE)
        skill = HeroSkillDefinition(
            id=9002, name="Instant",
            trigger=TriggerType.TURN_START, effects=[instant_spec], conditions=[],
            level_data={1: SkillLevelData(skill_id=9002, level=1, values={198: 25.0})},
        )
        state = _state()
        SE.evaluate_skills([_sel(skill)], [], TriggerType.TURN_START, _ctx(state=state))
        assert len(state.attacker_active_effects) == 1
        assert len(state.attacker_pending_effects) == 0


# ── Evil Eye (Petra) ──────────────────────────────────────────────────────────

class TestEvilEye:
    """
    PHASE skill with CURRENT_TARGET scope and apply_delay=1 — Petra's Evil Eye pattern.

    Separate from TestApplyEffect (which tests the general delayed/pending mechanism with
    ENEMY scope). This class focuses on CURRENT_TARGET resolution and per-target UNIQUE
    stacking: two fires on INF → 1 effect; one fire on INF + one on CAV → 2 effects.
    """

    def _skill(self, chance: float = 1.0) -> HeroSkillSelection:
        defn = HeroSkillDefinition(
            id=3001, name="Evil Eye",
            trigger=TriggerType.PHASE,
            effects=[EffectSpec(
                EffectType.DAMAGE_UP, 102, TargetScope.CURRENT_TARGET,
                duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE,
            )],
            conditions=[RandomChanceCondition(chance=chance)],
            level_data={5: SkillLevelData(skill_id=3001, level=5, values={102: 50.0})},
        )
        return _sel(defn, level=5)

    def test_does_not_fire_at_turn_start(self):
        state = _state()
        SE.evaluate_skills([self._skill()], [], TriggerType.TURN_START,
                           _ctx(state=state, def_type=INF), rng_fn=lambda: 0.0)
        assert len(state.attacker_pending_effects) == 0

    def test_effect_is_pending_not_active_on_placement_turn(self):
        state = _state()
        SE.evaluate_skills([self._skill()], [], TriggerType.PHASE,
                           _ctx(state=state, def_type=INF), rng_fn=lambda: 0.0)
        assert len(state.attacker_active_effects) == 0
        assert len(state.attacker_pending_effects) == 1

    @pytest.mark.parametrize("target", [INF, CAV, ARCH])
    def test_effect_target_troop_matches_current_target(self, target):
        state = _state()
        SE.evaluate_skills([self._skill()], [], TriggerType.PHASE,
                           _ctx(state=state, def_type=target), rng_fn=lambda: 0.0)
        assert state.attacker_pending_effects[0].target_troop == target

    def test_unique_blocks_second_placement_on_same_target(self):
        state = _state()
        skill = self._skill()
        ctx = _ctx(state=state, def_type=INF)
        SE.evaluate_skills([skill], [], TriggerType.PHASE, ctx, rng_fn=lambda: 0.0)
        SE.evaluate_skills([skill], [], TriggerType.PHASE, ctx, rng_fn=lambda: 0.0)
        assert len(state.attacker_pending_effects) == 1

    def test_unique_blocks_second_proc_even_on_different_target(self):
        # First proc targets INF, second would target CAV — still blocked because UNIQUE
        # is globally singular for a given (skill_id, effect_op), regardless of target_troop.
        # The first proc's target_troop is preserved; the second roll success is not an activation.
        state = _state()
        skill = self._skill()
        SE.evaluate_skills([skill], [], TriggerType.PHASE, _ctx(state=state, def_type=INF), rng_fn=lambda: 0.0)
        SE.evaluate_skills([skill], [], TriggerType.PHASE, _ctx(state=state, def_type=CAV), rng_fn=lambda: 0.0)
        assert len(state.attacker_pending_effects) == 1
        assert state.attacker_pending_effects[0].target_troop == INF  # first proc's target wins

    def test_active_effect_routes_to_numerator_for_matching_target(self):
        state = _state()
        _inject(state,
                EffectSpec(EffectType.DAMAGE_UP, 102, TargetScope.CURRENT_TARGET,
                           duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE),
                ATT, value=50.0, target_troop=INF)
        num_ec, den_ec = _phase_ecs(state, att_type=CAV, target_type=INF)
        assert SE.compute_skill_mod(num_ec, den_ec) == pytest.approx(1.5)

    def test_active_effect_excluded_for_wrong_target(self):
        state = _state()
        _inject(state,
                EffectSpec(EffectType.DAMAGE_UP, 102, TargetScope.CURRENT_TARGET,
                           duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE),
                ATT, value=50.0, target_troop=INF)
        num_ec, den_ec = _phase_ecs(state, att_type=CAV, target_type=CAV)
        assert SE.compute_skill_mod(num_ec, den_ec) == 1.0
