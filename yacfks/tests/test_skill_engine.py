import pytest
from yacfks.app.battle.skills.skill_engine import SkillEngine
from yacfks.app.battle.skills.effect_collection import EffectCollection
from yacfks.app.battle.skills.enums import EffectType, TriggerType, TargetScope, StackRule
from yacfks.app.battle.skills.definitions import EffectSpec, SkillLevelData, StatusSpec
from yacfks.app.battle.skills.conditions import RandomChanceCondition, RequiresMinTurn
from yacfks.app.battle.phase_context import PhaseContext
from yacfks.app.battle.skills.statuses import ActiveEffect, ActiveStatus
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

# ── Test infrastructure ───────────────────────────────────────────────────────

# setup a battle state
def _state() -> BattleState:
    line = lambda: BattleLineState(1000)
    return BattleState(
        attacker_inf=line(), attacker_cav=line(), attacker_arch=line(),
        defender_inf=line(), defender_cav=line(), defender_arch=line(),
    )

# quick pahse context
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

# quickly inject ActiveEffect into battle state, shortcutting the skill engine shebang.
def _inject(
    state: BattleState, spec: EffectSpec, side: BattleSide, value: float,
    target_troops: frozenset[TroopType] | None = None,
) -> None:
    state.get_effects(side).append(ActiveEffect(
        effect_spec=spec, remaining_turns=-1, source_skill_id=0,
        host_side=side, target_troops=target_troops, value=value,
    ))


def _inject_specs(state: BattleState, specs: list[EffectSpec], values: list[float], side: BattleSide) -> None:
    for spec, value in zip(specs, values):
        _inject(state, spec, side, value)


def _phase_ecs(state: BattleState, att_type: TroopType = INF, target_type: TroopType = INF):
    return SE.build_phase_ecs(
        state.get_effects(ATT), state.get_effects(DEF),
        state.get_statuses(ATT), state.get_statuses(DEF),
        att_type, target_type,
    )


# ── Shared EffectSpecs ────────────────────────────────────────────────────────

_DUP_101 = EffectSpec(EffectType.DAMAGE_UP,  101)
_DUP_102 = EffectSpec(EffectType.DAMAGE_UP,  102)
_DEF_111 = EffectSpec(EffectType.DEFENSE_UP, 111)
_RNG_199 = EffectSpec(EffectType.DAMAGE_UP,  199, duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE)

# ── Skill factories ───────────────────────────────────────────────────────────

def _static_skill(spec: EffectSpec, values: list[float], skill_id: int = 1) -> HeroSkillDefinition:
    return HeroSkillDefinition(
        id=skill_id, name=f"Test-{skill_id}",
        trigger=TriggerType.STATIC,
        effects=[spec], conditions=[],
        level_data={1: SkillLevelData(skill_id=skill_id, level=1, values=values)},
    )


def _rng_ts_skill(spec: EffectSpec, values: list[float], chance: float = 0.5, skill_id: int = 2) -> HeroSkillDefinition:
    return HeroSkillDefinition(
        id=skill_id, name=f"RNG-{skill_id}",
        trigger=TriggerType.TURN_START,
        effects=[spec],
        conditions=[RandomChanceCondition(chance=chance)],
        level_data={1: SkillLevelData(skill_id=skill_id, level=1, values=values)},
    )


def _delayed_unique_skill(rng: bool = False, chance: float = 0.5) -> HeroSkillDefinition:
    spec = EffectSpec(EffectType.DAMAGE_UP, 199, duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE)
    return HeroSkillDefinition(
        id=9001, name="Test Debuff",
        trigger=TriggerType.TURN_START,
        effects=[spec],
        conditions=[RandomChanceCondition(chance=chance)] if rng else [],
        level_data={1: SkillLevelData(skill_id=9001, level=1, values=[40.0])},
    )


def _make_turn_start_anti_cav_skill() -> TroopSkillDefinition:
    return TroopSkillDefinition(
        id=201, name="Master Brawler",
        trigger=TriggerType.TURN_START,
        effects=[EffectSpec(EffectType.TROOP_DAMAGE_UP, 301,
                            target_scopes=(TargetScope.ENEMY_CAVALRY,),
                            benefactor_scopes=(TargetScope.SELF_INFANTRY,), duration=1)],
        conditions=[],
        level_data={1: SkillLevelData(skill_id=301, level=1, values=[10.0])},
    )


def _make_ambusher_skill(chance: float = 0.20) -> TroopSkillDefinition:
    return TroopSkillDefinition(
        id=20, name="Ambusher",
        trigger=TriggerType.TROOP_SPECIAL,
        effects=[EffectSpec(EffectType.RETARGET, 0)],
        conditions=[RandomChanceCondition(chance=chance)],
        level_data={1: SkillLevelData(skill_id=20, level=1, values=[1.0])},
    )


# ── Per-troop-scope test data (Triton / Thrud patterns) ──────────────────────


#Oath of Power
_T_TRITON_SPECS = [
    EffectSpec(EffectType.DEFENSE_UP, 113, benefactor_scopes=(TargetScope.SELF_INFANTRY,)),
    EffectSpec(EffectType.DEFENSE_UP, 113, benefactor_scopes=(TargetScope.SELF_CAVALRY, TargetScope.SELF_ARCHERS)),
]
_T_TRITON_VALUES = [20.0, 30.0]  # INF=20%, CAV+ARCH=30% — positional; multi-scope collapses what were 3 effects into 2

# Battle Hunger
_T_THRUD_SPECS = [
    EffectSpec(EffectType.DAMAGE_UP,  113, benefactor_scopes=(TargetScope.SELF_INFANTRY, TargetScope.SELF_ARCHERS)),
    EffectSpec(EffectType.DEFENSE_UP, 113, benefactor_scopes=(TargetScope.SELF_INFANTRY, TargetScope.SELF_ARCHERS)),
]
_T_THRUD_VALUES = [15.0, 15.0]


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestStaticSkills:
    def test_creates_permanent_active_effect(self):
        state = _state()
        SE.evaluate_skills(
            [_sel(_static_skill(_DUP_101, [50.0]))], [],
            TriggerType.STATIC,
            _ctx(state=state)
        )
        assert len(state.attacker_active_effects) == 1
        assert state.attacker_active_effects[0].remaining_turns == -1

    def test_does_not_go_to_pending(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, [50.0]))], [], TriggerType.STATIC, _ctx(state=state))
        assert len(state.attacker_pending_effects) == 0

    # try eval a Static effect for a bunch of trigger types OTHER than Static, 
    # makes sure a Static effect does NOT go into ActiveEffect list
    @pytest.mark.parametrize("trigger", [TriggerType.TURN_START, TriggerType.PHASE, TriggerType.TROOP_SPECIAL])
    def test_does_not_fire_at_other_triggers(self, trigger):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, [50.0]))], [], trigger, _ctx(state=state))
        assert len(state.attacker_active_effects) == 0

    

class TestRngSkills:
    @pytest.mark.parametrize("roll,expected_count", [(0.0, 1), (0.5, 0)])
    def test_rng_gate(self, roll, expected_count):
        state = _state()
        SE.evaluate_skills([_sel(_rng_ts_skill(_DUP_101, [50.0], chance=0.5))], [],
                           TriggerType.TURN_START, _ctx(state=state), rng_fn=lambda: roll)
        assert len(state.attacker_active_effects) == expected_count

    def test_100_chance_always_fires(self):
        state = _state()
        SE.evaluate_skills([_sel(_rng_ts_skill(_DUP_101, [50.0], chance=1.0))], [],
                           TriggerType.TURN_START, _ctx(state=state), rng_fn=lambda: 0.9999)
        assert len(state.attacker_active_effects) == 1

    def test_two_skills_get_separate_rolls(self):
        state = _state()
        s1 = _rng_ts_skill(_DUP_101, [20.0], chance=0.5, skill_id=1)
        s2 = _rng_ts_skill(_DUP_102, [30.0], chance=0.5, skill_id=2)
        rolls = iter([0.0, 0.9])  # s1 hits, s2 misses
        SE.evaluate_skills([_sel(s1), _sel(s2)], [], TriggerType.TURN_START,
                           _ctx(state=state), rng_fn=lambda: next(rolls))
        assert len(state.attacker_active_effects) == 1
        assert state.attacker_active_effects[0].source_skill_id == 1

    # try eval an RNG skill with TURN_START trigger for PHASE trigger point
    # the RNG always rolls true.
    # this way we enusre that even if a skill will def roll true, the wrong trigger type blocks any furhter eval/apply of the skill.
    # makeing sure that rolls happens only after evaluationg trigger types.
    def test_turn_start_skill_does_not_fire_at_phase(self):
            state = _state()
            SE.evaluate_skills([_sel(_rng_ts_skill(_RNG_199, [40.0]))], [], TriggerType.PHASE,
                            _ctx(state=state), rng_fn=lambda: 0.0)
            assert len(state.attacker_pending_effects) == 0

class TestEffectRouting:
    def test_damage_up_on_attacker_goes_to_numerator(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, [30.0]))], [], TriggerType.STATIC, _ctx(ATT, state))
        n_ec, d_ec = _phase_ecs(state)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.30)
        assert d_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_defense_up_on_defender_goes_to_denominator(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DEF_111, [25.0], skill_id=3))], [], TriggerType.STATIC, _ctx(DEF, state))
        n_ec, d_ec = _phase_ecs(state)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.25)
        assert n_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)

    def test_attacker_buff_absent_when_defender_is_phase_attacker(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, [50.0]))], [], TriggerType.STATIC, _ctx(ATT, state))
        n_ec, _ = SE.build_phase_ecs(
            state.get_effects(DEF), state.get_effects(ATT),
            state.get_statuses(DEF), state.get_statuses(ATT),
            INF, INF,
        )
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_defender_defense_absent_when_defender_is_phase_attacker(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DEF_111, [25.0], skill_id=3))], [], TriggerType.STATIC, _ctx(DEF, state))
        _, d_ec = SE.build_phase_ecs(
            state.get_effects(DEF), state.get_effects(ATT),
            state.get_statuses(DEF), state.get_statuses(ATT),
            INF, INF,
        )
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.0)


class TestSkillStacking:
    def test_same_op_stacks_additively(self):
        state = _state()
        s1 = _static_skill(_DUP_101, [50.0], skill_id=1)
        s2 = _static_skill(_DUP_101, [30.0], skill_id=2)
        SE.evaluate_skills([_sel(s1), _sel(s2)], [], TriggerType.STATIC, _ctx(state=state))
        n_ec, _ = _phase_ecs(state)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.8)

    def test_different_ops_stack_multiplicatively(self):
        state = _state()
        s1 = _static_skill(_DUP_101, [50.0], skill_id=1)
        s2 = _static_skill(_DUP_102, [50.0], skill_id=2)
        SE.evaluate_skills([_sel(s1), _sel(s2)], [], TriggerType.STATIC, _ctx(state=state))
        n_ec, _ = _phase_ecs(state)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(2.25)


class TestComputeSkillMod:
    def test_no_effects_returns_one(self):
        assert SE.compute_skill_mod(EffectCollection(), EffectCollection()) == pytest.approx(1.0)

    def test_damage_up_increases_mod(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, [50.0]))], [], TriggerType.STATIC, _ctx(state=state))
        assert SE.compute_skill_mod(*_phase_ecs(state)) == pytest.approx(1.5)

    def test_defense_up_decreases_mod(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DEF_111, [100.0], skill_id=3))], [], TriggerType.STATIC, _ctx(DEF, state))
        assert SE.compute_skill_mod(*_phase_ecs(state)) == pytest.approx(0.5)

    def test_amane_plus_chenko(self):
        state = _state()
        s1 = _static_skill(_DUP_102, [50.0], skill_id=1)
        s2 = _static_skill(_DUP_101, [50.0], skill_id=2)
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
            effects=[EffectSpec(EffectType.RETARGET, 0)],
            conditions=[],
            level_data={1: SkillLevelData(skill_id=99, level=1, values=[1.0])},
        )
        assert SE.collect_retarget([wrong_trigger], _ctx(), rng_fn=lambda: 0.0) is False

    def test_skips_troop_special_without_retarget_effect(self):
        # a TROOP_SPECIAL skill that is not a RETARGET (e.g. future Volley) must not fire here
        volley_like = TroopSkillDefinition(
            id=98, name="Volley-like",
            trigger=TriggerType.TROOP_SPECIAL,
            effects=[EffectSpec(EffectType.EXTRA_ATTACK_PHASE, 0)],
            conditions=[],
            level_data={1: SkillLevelData(skill_id=98, level=1, values=[1.0])},
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
        SE.evaluate_skills([_sel(_delayed_unique_skill())], [], TriggerType.TURN_START, context=ctx)

    def test_delayed_effect_goes_to_pending_not_active(self):
        state = _state()
        SE.evaluate_skills([_sel(_delayed_unique_skill())], [], TriggerType.TURN_START, _ctx(state=state))
        assert len(state.attacker_pending_effects) == 1
        assert len(state.attacker_active_effects) == 0

    def test_immediate_effect_goes_to_active(self):
        state = _state()
        SE.evaluate_skills([_sel(_static_skill(_DUP_101, [30.0]))], [], TriggerType.STATIC, _ctx(state=state))
        assert len(state.attacker_active_effects) == 1
        assert len(state.attacker_pending_effects) == 0

    def test_pending_effect_fields(self):
        state = _state()
        SE.evaluate_skills([_sel(_delayed_unique_skill())], [], TriggerType.TURN_START, _ctx(state=state))
        ae = state.attacker_pending_effects[0]
        assert ae.source_skill_id == 9001
        assert ae.host_side == ATT
        assert ae.value == 40.0
        assert ae.remaining_turns == 1

    def test_rng_miss_creates_no_effect(self):
        state = _state()
        SE.evaluate_skills([_sel(_delayed_unique_skill(rng=True, chance=0.5))], [],
                           TriggerType.TURN_START, _ctx(state=state), rng_fn=lambda: 0.9)
        assert len(state.attacker_pending_effects) == 0

    def test_unique_does_not_stack_twice(self):
        state = _state()
        sel = _sel(_delayed_unique_skill())
        SE.evaluate_skills([sel, sel], [], TriggerType.TURN_START, _ctx(state=state))
        assert len(state.attacker_pending_effects) == 1

    def test_explicit_delay_zero_is_immediate(self):
        instant_spec = EffectSpec(EffectType.DAMAGE_UP, 198, duration=1, apply_delay=0, stack_rule=StackRule.UNIQUE)
        skill = HeroSkillDefinition(
            id=9002, name="Instant",
            trigger=TriggerType.TURN_START, effects=[instant_spec], conditions=[],
            level_data={1: SkillLevelData(skill_id=9002, level=1, values=[25.0])},
        )
        state = _state()
        SE.evaluate_skills([_sel(skill)], [], TriggerType.TURN_START, _ctx(state=state))
        assert len(state.attacker_active_effects) == 1
        assert len(state.attacker_pending_effects) == 0


# ── Evil Eye (Petra) ──────────────────────────────────────────────────────────

_CURSED_ID = 1

def _evil_eye_skill(chance: float = 1.0) -> HeroSkillSelection:
    defn = HeroSkillDefinition(
        id=3001, name="Evil Eye",
        trigger=TriggerType.TURN_START_PER_TROOP,
        statuses=[StatusSpec(
            id=_CURSED_ID, name="Cursed",
            target_scopes=(TargetScope.CURRENT_TARGET,),
            duration=1, apply_delay=0, stack_rule=StackRule.UNIQUE,
        )],
        effects=[EffectSpec(
            EffectType.DAMAGE_UP, 102,
            required_status_id=_CURSED_ID,
            duration=1, apply_delay=0, stack_rule=StackRule.UNIQUE,
        )],
        conditions=[RandomChanceCondition(chance=chance), RequiresMinTurn(min_turn=2)],
        level_data={5: SkillLevelData(skill_id=3001, level=5, values=[50.0])},
    )
    return _sel(defn, level=5)


class TestEvilEye:
    """
    TURN_START_PER_TROOP skill — Petra's Evil Eye pattern.

    On proc: places Cursed status (CURRENT_TARGET, duration=1, UNIQUE) immediately.
    DamageUp effect is gated by Cursed (required_status_id) and resolves target_troop
    from the Cursed status. Both are apply_delay=0, so they are active the same turn.
    Skips turn 1 (RequiresMinTurn=2).
    """

    def test_does_not_fire_at_phase_trigger(self):
        state = _state()
        state.turn = 2
        SE.evaluate_skills([_evil_eye_skill()], [], TriggerType.PHASE,
                           _ctx(state=state, def_type=INF), rng_fn=lambda: 0.0)
        assert len(state.attacker_active_statuses) == 0
        assert len(state.attacker_active_effects) == 0

    def test_does_not_fire_on_turn_1(self):
        state = _state()  # turn=1 by default
        SE.evaluate_skills([_evil_eye_skill()], [], TriggerType.TURN_START_PER_TROOP,
                           _ctx(state=state, def_type=INF), rng_fn=lambda: 0.0)
        assert len(state.attacker_active_statuses) == 0
        assert len(state.attacker_active_effects) == 0

    def test_rng_miss_places_nothing(self):
        state = _state()
        state.turn = 2
        SE.evaluate_skills([_evil_eye_skill(chance=0.5)], [], TriggerType.TURN_START_PER_TROOP,
                           _ctx(state=state, def_type=INF), rng_fn=lambda: 0.9)
        assert len(state.attacker_active_statuses) == 0
        assert len(state.attacker_active_effects) == 0

    def test_proc_places_cursed_status_immediately(self):
        state = _state()
        state.turn = 2
        SE.evaluate_skills([_evil_eye_skill()], [], TriggerType.TURN_START_PER_TROOP,
                           _ctx(state=state, def_type=INF), rng_fn=lambda: 0.0)
        assert len(state.attacker_active_statuses) == 1
        s = state.attacker_active_statuses[0]
        assert s.status_spec.id == _CURSED_ID
        assert s.target_troops == frozenset({INF})

    def test_proc_places_damage_up_effect_immediately(self):
        state = _state()
        state.turn = 2
        SE.evaluate_skills([_evil_eye_skill()], [], TriggerType.TURN_START_PER_TROOP,
                           _ctx(state=state, def_type=INF), rng_fn=lambda: 0.0)
        assert len(state.attacker_active_effects) == 1
        ae = state.attacker_active_effects[0]
        assert ae.value == 50.0
        assert ae.target_troops == frozenset({INF})  # resolved from Cursed status

    @pytest.mark.parametrize("target", [INF, CAV, ARCH])
    def test_effect_target_troop_matches_current_target(self, target):
        state = _state()
        state.turn = 2
        SE.evaluate_skills([_evil_eye_skill()], [], TriggerType.TURN_START_PER_TROOP,
                           _ctx(state=state, def_type=target), rng_fn=lambda: 0.0)
        assert state.attacker_active_effects[0].target_troops == frozenset({target})

    def test_unique_blocks_second_proc_on_same_skill(self):
        state = _state()
        state.turn = 2
        skill = _evil_eye_skill()
        ctx = _ctx(state=state, def_type=INF)
        SE.evaluate_skills([skill], [], TriggerType.TURN_START_PER_TROOP, ctx, rng_fn=lambda: 0.0)
        SE.evaluate_skills([skill], [], TriggerType.TURN_START_PER_TROOP, ctx, rng_fn=lambda: 0.0)
        assert len(state.attacker_active_statuses) == 1
        assert len(state.attacker_active_effects) == 1

    def test_damage_up_absent_when_cursed_not_present(self):
        # Effect with required_status_id but no matching status in state → not included in EC.
        state = _state()
        spec = EffectSpec(EffectType.DAMAGE_UP, 102, required_status_id=_CURSED_ID,
                          duration=1, apply_delay=0, stack_rule=StackRule.UNIQUE)
        _inject(state, spec, ATT, value=50.0, target_troops=frozenset({INF}))
        # no status in state — gate blocks
        n_ec, _ = _phase_ecs(state, att_type=INF, target_type=INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.0)

    def test_damage_up_present_when_cursed_is_active(self):
        state = _state()
        spec = EffectSpec(EffectType.DAMAGE_UP, 102, required_status_id=_CURSED_ID,
                          duration=1, apply_delay=0, stack_rule=StackRule.UNIQUE)
        _inject(state, spec, ATT, value=50.0, target_troops=frozenset({INF}))
        # manually add the Cursed status
        state.attacker_active_statuses.append(ActiveStatus(
            status_spec=StatusSpec(id=_CURSED_ID, name="Cursed"),
            remaining_turns=1, source_skill_id=3001,
            host_side=ATT, target_troops=frozenset({INF}),
        ))
        n_ec, _ = _phase_ecs(state, att_type=INF, target_type=INF)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.5)

    def test_full_proc_contributes_to_skill_mod(self):
        state = _state()
        state.turn = 2
        SE.evaluate_skills([_evil_eye_skill()], [], TriggerType.TURN_START_PER_TROOP,
                           _ctx(state=state, def_type=INF), rng_fn=lambda: 0.0)
        n_ec, d_ec = _phase_ecs(state, att_type=INF, target_type=INF)
        assert SE.compute_skill_mod(n_ec, d_ec) == pytest.approx(1.5)


# ── Multi-effect skills ───────────────────────────────────────────────────────

def _ancestral_guidance_skill(level: int = 5) -> HeroSkillSelection:
    """Thrud's Ancestral Guidance: DamageUp + OppDamageDown, same values per level."""
    defn = HeroSkillDefinition(
        id=4001, name="Ancestral Guidance",
        trigger=TriggerType.STATIC,
        effects=[
            EffectSpec(EffectType.DAMAGE_UP,       102),
            EffectSpec(EffectType.OPP_DAMAGE_DOWN, 201),
        ],
        conditions=[],
        level_data={
            1: SkillLevelData(skill_id=4001, level=1, values=[5.0,  5.0]),
            5: SkillLevelData(skill_id=4001, level=5, values=[25.0, 25.0]),
        },
    )
    return _sel(defn, level=level)


def _asymmetric_skill() -> HeroSkillSelection:
    """Two effects, different types, different values at level 5 — tests positional routing."""
    defn = HeroSkillDefinition(
        id=4002, name="Asymmetric",
        trigger=TriggerType.STATIC,
        effects=[
            EffectSpec(EffectType.DAMAGE_UP,       102),
            EffectSpec(EffectType.OPP_DAMAGE_DOWN, 201),
        ],
        conditions=[],
        level_data={5: SkillLevelData(skill_id=4002, level=5, values=[25.0, 20.0])},
    )
    return _sel(defn, level=5)


class TestMultiEffectSkills:
    """Skills with multiple effects, potentially sharing op IDs or having per-effect values."""

    # ── Ancestral Guidance pattern (DamageUp + OppDamageDown, same values) ──────

    def test_both_effects_placed(self):
        state = _state()
        SE.evaluate_skills([_ancestral_guidance_skill()], [], TriggerType.STATIC, _ctx(state=state))
        assert len(state.attacker_active_effects) == 2

    def test_damage_up_routes_to_numerator(self):
        state = _state()
        SE.evaluate_skills([_ancestral_guidance_skill()], [], TriggerType.STATIC, _ctx(ATT, state))
        n_ec, _ = _phase_ecs(state)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.25)

    def test_opp_damage_down_routes_to_denominator_when_att_is_defending(self):
        # OppDamageDown is a DENOMINATOR type: contributes when its owner's side is phase defender.
        # ATT has the skill; when DEF side is phase attacker, ATT's effects are def_active_effects.
        state = _state()
        SE.evaluate_skills([_ancestral_guidance_skill()], [], TriggerType.STATIC, _ctx(ATT, state))
        _, d_ec = SE.build_phase_ecs(
            state.get_effects(DEF), state.get_effects(ATT),
            state.get_statuses(DEF), state.get_statuses(ATT),
            INF, INF,
        )
        assert d_ec.resolve_multiplier(EffectType.OPP_DAMAGE_DOWN) == pytest.approx(1.25)

    def test_damage_up_value_scales_with_level(self):
        state1, state5 = _state(), _state()
        SE.evaluate_skills([_ancestral_guidance_skill(level=1)], [], TriggerType.STATIC, _ctx(state=state1))
        SE.evaluate_skills([_ancestral_guidance_skill(level=5)], [], TriggerType.STATIC, _ctx(state=state5))
        n1, _ = _phase_ecs(state1)
        n5, _ = _phase_ecs(state5)
        assert n1.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.05)
        assert n5.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.25)

    # ── Asymmetric values (different value per effect position) ──────────────────

    def test_asymmetric_damage_up_value(self):
        state = _state()
        SE.evaluate_skills([_asymmetric_skill()], [], TriggerType.STATIC, _ctx(ATT, state))
        n_ec, _ = _phase_ecs(state)
        assert n_ec.resolve_multiplier(EffectType.DAMAGE_UP) == pytest.approx(1.25)

    def test_asymmetric_opp_damage_down_value(self):
        state = _state()
        SE.evaluate_skills([_asymmetric_skill()], [], TriggerType.STATIC, _ctx(ATT, state))
        _, d_ec = SE.build_phase_ecs(
            state.get_effects(DEF), state.get_effects(ATT),
            state.get_statuses(DEF), state.get_statuses(ATT),
            INF, INF,
        )
        assert d_ec.resolve_multiplier(EffectType.OPP_DAMAGE_DOWN) == pytest.approx(1.20)

    def test_asymmetric_values_do_not_bleed_across_effects(self):
        # position 0 = 25% DamageUp, position 1 = 20% OppDamageDown — values must not swap
        state = _state()
        SE.evaluate_skills([_asymmetric_skill()], [], TriggerType.STATIC, _ctx(ATT, state))
        effects = state.attacker_active_effects
        damage_up_ae    = next(ae for ae in effects if ae.effect_spec.effect_type == EffectType.DAMAGE_UP)
        opp_dmg_down_ae = next(ae for ae in effects if ae.effect_spec.effect_type == EffectType.OPP_DAMAGE_DOWN)
        assert damage_up_ae.value    == pytest.approx(25.0)
        assert opp_dmg_down_ae.value == pytest.approx(20.0)

    # ── Triton pattern (same op, same type, different benefactor scope + value) ──

    def test_triton_same_op_different_values_by_position(self):
        # Both are DefenseUp 113 but INF gets 20%, CAV/ARCH get 30%.
        # benefactor_scope on DENOMINATOR effects gates by target_troop_type (which defender troop
        # is under attack), not by att_troop_type.
        state = _state()
        for spec, val in zip(_T_TRITON_SPECS, _T_TRITON_VALUES):
            _inject(state, spec, DEF, val)
        # enemy INF targets DEF's INF → SELF_INF effect (20%) applies
        _, d_ec = _phase_ecs(state, att_type=INF, target_type=INF)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.20)
        # enemy INF targets DEF's CAV → SELF_CAV effect (30%) applies
        _, d_ec = _phase_ecs(state, att_type=INF, target_type=CAV)
        assert d_ec.resolve_multiplier(EffectType.DEFENSE_UP) == pytest.approx(1.30)
