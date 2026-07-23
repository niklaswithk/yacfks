from yacfks.app.battle.battle_setup import BattleContext
from yacfks.app.battle.battle_state import BattleState
from yacfks.app.battle.battle_line_state import BattleLineState
from yacfks.app.battle.battle_snapshot import BattleSnapshot
from yacfks.app.battle.battle_result import BattleResult
from yacfks.app.battle.damage.damage_calc import compute_kills
from yacfks.app.battle.skills.skill_engine import SkillEngine
from yacfks.app.battle.phase_context import PhaseContext
from yacfks.app.battle.skills.enums import TriggerType
from yacfks.app.domains.enums import BattleSide, TroopType
from yacfks.app.battle.skills.definitions import TroopSkillDefinition, HeroSkillSelection

_TROOP_ORDER = [TroopType.INF, TroopType.CAV, TroopType.ARCH]


class BattleEngine:

    def __init__(self):
        self._skill_engine = SkillEngine()

    def run(self, context: BattleContext) -> BattleResult:
        # init a battle state using battle context/setup, i.e. turn 1.
        # for now, battle context is practically more or less frozen, while battle states and line states
        # will hold changes throught the battle.
        # im thinking about maybe merging battle context/state, but feels forced right now
        state = self._init_state(context)

        # STATIC skills fire once per battle — hero skills that write a permanent active effect.
        self._apply_skills(TriggerType.STATIC, context, state)
        
        # snapshots will hold lots of goodies, like mini battle reports per turn(BattleSnapshot).
        # one can iterate through them in a gui and see the flow of battle real-time.
        # for now it only holds troop counts and turn count. 
        # Can extend it later with effects from skills.
        # togehter with battle context, which holds lots of static data like stats bonuses etc
        # it can be made into a powerful visualiz<ton utility for damage formula, skills, flow of battle,
        # how it all connects during an actual battle.
        snapshots: list[BattleSnapshot] = []

        # main battle loop
        while True:
            self._run_turn(context, state)
            snapshots.append(self._snapshot(state))

            att_alive = any(
                state.get_line(BattleSide.ATTACKER, t).is_alive for t in _TROOP_ORDER
            )
            def_alive = any(
                state.get_line(BattleSide.DEFENDER, t).is_alive for t in _TROOP_ORDER
            )

            if not att_alive or not def_alive:
                break

            state.turn += 1

        return self._build_result(state, snapshots)

    # ── turn execution ────────────────────────────────────────────────────────

    def _run_turn(self, context: BattleContext, state: BattleState) -> None:
        # resolve target for both sides first, before we eval any skills (except Ambusher) and before any attack phases.
        # the special Ambusher (CAV RETARGET) rolls in _compute_side_targets, so not per phase.
        # evaluating and resolving targets once per beginning of turn, and locking them in, could have
        # some consequences for dynamic targeting skills using eg CURRENT_TARGET, if they roll per atack phase.
        # but ill lieave like this for now
        att_targets = self._compute_side_targets(context, state, BattleSide.ATTACKER, BattleSide.DEFENDER)
        def_targets = self._compute_side_targets(context, state, BattleSide.DEFENDER, BattleSide.ATTACKER)

        # TURN_START: per turn skills, fires once per turn for both sides.
        # hero and regular troop skills write duration=1 active effects that expire 
        # at turn end and are re-applied next turn.
        self._apply_skills(TriggerType.TURN_START, context, state)
        # EVERY_N_TURNS: reurring/fixed interval skills (e.g. Alcar, Sophia) — EveryNTurnsCondition filters by turn % n.
        # the trigger type here is a bit superflous, since the condition is what actually handles things while the trigger type
        # behaves just like TURN_START...
        # but ima leave it here for now, its more explcicit.
        # but gonan have to think about how we can merge/simplify the trigger type and the condition, maybe
        # a single condition class handling both min_turn and turn internval..?
        self._apply_skills(TriggerType.EVERY_N_TURNS, context, state)

        # TURN_START_PER_TROOP: for skills that are evaluated, rolled, etc, at start of turn but for every troop type present.
        # sort of like per attack phase skills, but clustered in start of turn, before attack phases.
        # because of dynamic targeting like CURRENT_TARGET, we pass the resolved targeting map per side
        self._apply_skills_per_troop(TriggerType.TURN_START_PER_TROOP, context, state, BattleSide.ATTACKER, att_targets)
        self._apply_skills_per_troop(TriggerType.TURN_START_PER_TROOP, context, state, BattleSide.DEFENDER, def_targets)

        # the actual damage exhange, Attacker goes first - might not be how it's done in-game, but that's how i do it.
        self._run_attack_phases(context, state, BattleSide.ATTACKER, BattleSide.DEFENDER, att_targets)
        self._run_attack_phases(context, state, BattleSide.DEFENDER, BattleSide.ATTACKER, def_targets)

        self._apply_losses(state)
        self._tick_statuses(state)

    def _apply_skills(
            self,
            trigger: TriggerType,
            context: BattleContext,
            state: BattleState
    ) -> None:

        for side in (BattleSide.ATTACKER, BattleSide.DEFENDER):
            phase_ctx = PhaseContext(
                battle_context=context,
                battle_state=state,
                attacking_side=side,
                attacker_troop_type=None,
                defender_troop_type=None,
            )
            hero_skills = self._hero_skills_for_side(context, side)
            troop_skills = self._all_troop_skills_for_side(context, side)
            self._skill_engine.evaluate_skills(hero_skills, troop_skills, trigger, phase_ctx)

    def _run_attack_phases(
        self,
        context: BattleContext,
        state: BattleState,
        att_side: BattleSide,
        def_side: BattleSide,
        targets: dict[TroopType, TroopType | None],
    ) -> None:
        
        # get stats for current phase attacker
        att_final_stats = (
            context.attacker_final_stats if att_side == BattleSide.ATTACKER
            else context.defender_final_stats
        )

        # # get stats for current phase defender
        def_final_stats = (
            context.defender_final_stats if att_side == BattleSide.ATTACKER
            else context.attacker_final_stats
        )

        # attack phases ar a-go
        for att_troop_type in _TROOP_ORDER:
            # get current state of the troop type/ArmyLine about to attack
            att_line = state.get_line(att_side, att_troop_type)
            if not att_line.is_alive:
                continue

            # get current target for current attacking troop type
            target_troop_type = targets[att_troop_type]
            if target_troop_type is None:
                break

            # get all hero skills for current phase attacker
            # hero skill effects will be applied laeter
            att_hero_skills = self._hero_skills_for_side(context, att_side)

            # get troop skills from current troop type about to attack. 
            # troop skill effects will be applied later
            att_troop_skills = self._troop_skills_for_line(context, att_side, att_troop_type)

            # create a phase context including the intial battle context/setup, current battle state,
            # and more
            phase_ctx = PhaseContext(
                battle_context=context,
                battle_state=state,
                attacking_side=att_side,
                attacker_troop_type=att_troop_type,
                defender_troop_type=target_troop_type,
            )

            # evaluate troop skills and phase-based hero skills, in the current phase context
            self._skill_engine.evaluate_skills(att_hero_skills, att_troop_skills, TriggerType.PHASE, phase_ctx)

            # Route all active effects from BattleState into phase ECs.
            num_ec, den_ec = self._skill_engine.build_phase_ecs(
                state.get_effects(att_side),
                state.get_effects(def_side),
                state.get_statuses(att_side),
                state.get_statuses(def_side),
                att_troop_type,
                target_troop_type,
            )

            skill_mod = self._skill_engine.compute_skill_mod(num_ec, den_ec)

            att_stats = att_final_stats.get_final_stats(att_troop_type)
            def_stats = def_final_stats.get_final_stats(target_troop_type)

            kills = compute_kills(
                attacking_count=att_line.troop_count,
                army_min=context.army_min,
                attacking_stats=att_stats,
                defending_stats=def_stats,
                skill_mod=skill_mod,
            )

            state.get_line(def_side, target_troop_type).pending_losses += kills

    # ── helpers ───────────────────────────────────────────────────────────────

    def _compute_side_targets(
        self,
        context: BattleContext,
        state: BattleState,
        phase_attacker: BattleSide,
        phase_defender: BattleSide,
    ) -> dict[TroopType, TroopType | None]:
        """Pre-compute attack targets for all three troop types on one side.

        Returns {att_type: target_type | None} where None means no valid target
        (all enemies dead). CAV's target is determined after rolling the Ambusher
        (RETARGET) skill so it's resolved exactly once, before any phase executes.
        """
        targets: dict[TroopType, TroopType | None] = {}
        for att_type in _TROOP_ORDER:
            if not state.get_line(phase_attacker, att_type).is_alive:
                targets[att_type] = None
                continue

            target = self._get_default_target(state, phase_defender)

            if att_type == TroopType.CAV and target is not None:
                cav_skills = self._troop_skills_for_line(context, phase_attacker, TroopType.CAV)
                # create a phase context with goodies for skills engine to evaluate Amubsher skill.
                phase_ctx = PhaseContext(
                    battle_context=context,
                    battle_state=state,
                    attacking_side=phase_attacker,
                    attacker_troop_type=TroopType.CAV,
                    defender_troop_type=target,
                )
                if self._skill_engine.collect_retarget(cav_skills, phase_ctx):
                    arch_line = state.get_line(phase_defender, TroopType.ARCH)
                    if arch_line.is_alive:
                        target = TroopType.ARCH

            # "targets" dict contains pairs of troop types for targeting, like INF vs INF, CAV vs ARCH etc.
            #  e.g. Defender CAV will target Attacker ARCH, or Attacker ARCH will target DEFENDER Inf, etc
            targets[att_type] = target
        return targets

    def _get_default_target(self, state: BattleState, def_side: BattleSide) -> TroopType | None:
        for candidate in _TROOP_ORDER:
            if state.get_line(def_side, candidate).is_alive:
                return candidate
        return None

    def _apply_losses(self, state: BattleState) -> None:
        for side in [BattleSide.ATTACKER, BattleSide.DEFENDER]:
            for t in _TROOP_ORDER:
                line = state.get_line(side, t)
                line.troop_count = max(0, line.troop_count - line.pending_losses)
                line.pending_losses = 0

    def _apply_skills_per_troop(
        self,
        trigger: TriggerType,
        context: BattleContext,
        state: BattleState,
        side: BattleSide,
        targets: dict[TroopType, TroopType | None],
    ) -> None:
        hero_skills = self._hero_skills_for_side(context, side)
        troop_skills = self._all_troop_skills_for_side(context, side)
        for att_type in _TROOP_ORDER:
            if not state.get_line(side, att_type).is_alive:
                continue
            phase_ctx = PhaseContext(
                battle_context=context,
                battle_state=state,
                attacking_side=side,
                attacker_troop_type=att_type,
                defender_troop_type=targets.get(att_type),
            )
            self._skill_engine.evaluate_skills(hero_skills, troop_skills, trigger, phase_ctx)

    def _tick_statuses(self, state: BattleState) -> None:
        for side in (BattleSide.ATTACKER, BattleSide.DEFENDER):
            surviving_effects = []
            for ae in state.get_effects(side):
                if ae.remaining_turns == -1:
                    surviving_effects.append(ae)
                    continue
                ae.remaining_turns -= 1
                if ae.remaining_turns > 0:
                    surviving_effects.append(ae)
            surviving_effects.extend(state.get_effects(side, pending=True))

            surviving_statuses = []
            for s in state.get_statuses(side):
                s.remaining_turns -= 1
                if s.remaining_turns > 0:
                    surviving_statuses.append(s)
            surviving_statuses.extend(state.get_statuses(side, pending=True))

            if side == BattleSide.ATTACKER:
                state.attacker_active_effects = surviving_effects
                state.attacker_pending_effects = []
                state.attacker_active_statuses = surviving_statuses
                state.attacker_pending_statuses = []
            else:
                state.defender_active_effects = surviving_effects
                state.defender_pending_effects = []
                state.defender_active_statuses = surviving_statuses
                state.defender_pending_statuses = []

    def _snapshot(self, state: BattleState) -> BattleSnapshot:
        return BattleSnapshot(
            turn_number=state.turn,
            attacker_inf=state.attacker_inf.troop_count,
            attacker_cav=state.attacker_cav.troop_count,
            attacker_arch=state.attacker_arch.troop_count,
            defender_inf=state.defender_inf.troop_count,
            defender_cav=state.defender_cav.troop_count,
            defender_arch=state.defender_arch.troop_count,
        )

    def _init_state(self, context: BattleContext) -> BattleState:
        return BattleState(
            attacker_inf=BattleLineState(context.attacker_army.infantry_line.troop_count),
            attacker_cav=BattleLineState(context.attacker_army.cavalry_line.troop_count),
            attacker_arch=BattleLineState(context.attacker_army.archer_line.troop_count),
            defender_inf=BattleLineState(context.defender_army.infantry_line.troop_count),
            defender_cav=BattleLineState(context.defender_army.cavalry_line.troop_count),
            defender_arch=BattleLineState(context.defender_army.archer_line.troop_count),
        )

    def _build_result(self, state: BattleState, snapshots: list[BattleSnapshot]) -> BattleResult:
        att_remaining = sum(state.get_line(BattleSide.ATTACKER, t).troop_count for t in _TROOP_ORDER)
        def_remaining = sum(state.get_line(BattleSide.DEFENDER, t).troop_count for t in _TROOP_ORDER)

        if att_remaining > 0 and def_remaining == 0:
            winner = "attacker"
        elif def_remaining > 0 and att_remaining == 0:
            winner = "defender"
        else:
            winner = "draw"

        return BattleResult(
            winner=winner,
            turns=state.turn,
            attacker_remaining=att_remaining,
            defender_remaining=def_remaining,
            snapshots=snapshots,
        )

    def _hero_skills_for_side(
        self, 
        context: BattleContext, 
        side: BattleSide
    ) -> list[HeroSkillSelection]:
        
        if side == BattleSide.ATTACKER:
            heroes = context.attacker_lead_heroes + context.attacker_joiner_heroes
        else:
            heroes = context.defender_lead_heroes + context.defender_joiner_heroes
        return [skill for hero in heroes for skill in hero.skills]

    def _troop_skills_for_line(
        self, context: BattleContext, side: BattleSide, troop_type: TroopType
    ) -> list[TroopSkillDefinition]:
        army = (
            context.attacker_army if side == BattleSide.ATTACKER else context.defender_army
        )
        return army.get_line(troop_type).troop_skills

    def _all_troop_skills_for_side(self, context: BattleContext, side: BattleSide) -> list[TroopSkillDefinition]:
        return [
            skill
            for troop_type in _TROOP_ORDER
            for skill in self._troop_skills_for_line(context, side, troop_type)
        ]
