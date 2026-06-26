from __future__ import annotations
from yacfks.app.battle.battle_setup import BattleContext
from yacfks.app.battle.battle_state import BattleState
from yacfks.app.battle.battle_line_state import BattleLineState
from yacfks.app.battle.battle_snapshot import BattleSnapshot
from yacfks.app.battle.battle_result import BattleResult
from yacfks.app.battle.damage.damage_calc import compute_kills
from yacfks.app.battle.skills.skill_engine import SkillEngine
from yacfks.app.battle.skills.skill_context import SkillContext
from yacfks.app.battle.skills.enums import TriggerType
from yacfks.app.domains.enums import BattleSide, TroopType
from yacfks.app.domains.hero import HeroSkillSelection

_TROOP_ORDER = [TroopType.INF, TroopType.CAV, TroopType.ARCH]
_TARGET_PRIORITY = [TroopType.INF, TroopType.CAV, TroopType.ARCH]


class BattleEngine:

    def __init__(self):
        self._skill_engine = SkillEngine()

    def run(self, context: BattleContext) -> BattleResult:
        state = self._init_state(context)

        # ALWAYS skills fire exactly once per battle: create permanent statuses now.
        # These go directly into active_statuses (SELF scope → immediate).
        self._apply_always_skills(context, state)

        snapshots: list[BattleSnapshot] = []

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
        # TURN_START fires once per turn: evaluate hero skills for both sides.
        # Results land in pending_statuses (enemy-scope) or active_statuses (self-scope).
        self._apply_turn_start_skills(context, state)

        # Each side runs its 3 attack phases.
        self._run_side_attacks(context, state, BattleSide.ATTACKER, BattleSide.DEFENDER)
        self._run_side_attacks(context, state, BattleSide.DEFENDER, BattleSide.ATTACKER)

        self._apply_losses(state)
        self._tick_statuses(state)

    def _apply_always_skills(self, context: BattleContext, state: BattleState) -> None:
        for side in (BattleSide.ATTACKER, BattleSide.DEFENDER):
            skill_ctx = SkillContext(
                battle_context=context,
                battle_state=state,
                attacking_side=side,
                attacker_troop_type=None,
                defender_troop_type=None,
            )
            self._skill_engine.collect_effects(
                self._hero_skills_for_side(context, side), [],
                TriggerType.ALWAYS, skill_ctx,
            )

    def _apply_turn_start_skills(self, context: BattleContext, state: BattleState) -> None:
        for side in (BattleSide.ATTACKER, BattleSide.DEFENDER):
            skill_ctx = SkillContext(
                battle_context=context,
                battle_state=state,
                attacking_side=side,
                attacker_troop_type=None,
                defender_troop_type=None,
            )
            self._skill_engine.collect_effects(
                self._hero_skills_for_side(context, side), [],
                TriggerType.TURN_START, skill_ctx,
            )

    def _run_side_attacks(
        self,
        context: BattleContext,
        state: BattleState,
        att_side: BattleSide,
        def_side: BattleSide,
    ) -> None:
        att_hero_skills = self._hero_skills_for_side(context, att_side)

        att_final_stats = (
            context.attacker_final_stats if att_side == BattleSide.ATTACKER
            else context.defender_final_stats
        )
        def_final_stats = (
            context.defender_final_stats if att_side == BattleSide.ATTACKER
            else context.attacker_final_stats
        )

        for att_type in _TROOP_ORDER:
            att_line = state.get_line(att_side, att_type)
            if not att_line.is_alive:
                continue

            target_type = self._get_target(state, def_side)
            if target_type is None:
                break

            troop_skills = self._troop_skills_for_line(context, att_side, att_type)

            skill_ctx = SkillContext(
                battle_context=context,
                battle_state=state,
                attacking_side=att_side,
                attacker_troop_type=att_type,
                defender_troop_type=target_type,
            )

            # Evaluate ATTACK-trigger hero skills and troop skills for the attacker.
            # Hero skills producing statuses write to battle_state (context carries the state).
            # Defender hero ATTACK skills fire when the defender's own _run_side_attacks runs,
            # so we do NOT evaluate def_hero_skills here (attacking_side would be wrong).
            phase_numerator_ec, _ = self._skill_engine.collect_effects(
                att_hero_skills, troop_skills, TriggerType.ATTACK, skill_ctx
            )

            # Status-derived effects: read from active_statuses for this exact phase
            status_numerator_ec, status_denominator_ec = self._skill_engine.collect_phase_effects(
                state.active_statuses,
                att_side=att_side, att_type=att_type,
                def_side=def_side, target_type=target_type,
            )

            merged_numerator = _merge(phase_numerator_ec, status_numerator_ec)
            merged_denominator = _merge(status_denominator_ec)

            skill_mod = self._skill_engine.compute_skill_mod(merged_numerator, merged_denominator)

            att_stats = att_final_stats.get_final_stats(att_type)
            def_stats = def_final_stats.get_final_stats(target_type)

            kills = compute_kills(
                attacking_count=att_line.troop_count,
                army_min=context.army_min,
                attacking_stats=att_stats,
                defending_stats=def_stats,
                skill_mod=skill_mod,
            )

            state.get_line(def_side, target_type).pending_losses += kills

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_target(self, state: BattleState, def_side: BattleSide) -> TroopType | None:
        for candidate in _TARGET_PRIORITY:
            if state.get_line(def_side, candidate).is_alive:
                return candidate
        return None

    def _apply_losses(self, state: BattleState) -> None:
        for side in [BattleSide.ATTACKER, BattleSide.DEFENDER]:
            for t in _TROOP_ORDER:
                line = state.get_line(side, t)
                line.troop_count = max(0, line.troop_count - line.pending_losses)
                line.pending_losses = 0

    def _tick_statuses(self, state: BattleState) -> None:
        # Pending enemy-scope statuses (curses etc.) become active for the next turn.
        state.active_statuses.extend(state.pending_statuses)
        state.pending_statuses = []

        surviving = []
        for status in state.active_statuses:
            if status.remaining_turns == -1:  # permanent
                surviving.append(status)
                continue
            status.remaining_turns -= 1
            if status.remaining_turns > 0:
                surviving.append(status)
        state.active_statuses = surviving

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
        self, context: BattleContext, side: BattleSide
    ) -> list[HeroSkillSelection]:
        if side == BattleSide.ATTACKER:
            heroes = context.attacker_lead_heroes + context.attacker_joiner_heroes
        else:
            heroes = context.defender_lead_heroes + context.defender_joiner_heroes
        return [skill for hero in heroes for skill in hero.skills]

    def _troop_skills_for_line(
        self, context: BattleContext, side: BattleSide, troop_type: TroopType
    ):
        army = (
            context.attacker_army if side == BattleSide.ATTACKER else context.defender_army
        )
        return army.get_line(troop_type).troop_skills


def _merge(*collections):
    """Combine any number of EffectCollections into one (non-destructive)."""
    from yacfks.app.battle.skills.effect_collection import EffectCollection
    merged = EffectCollection()
    for ec in collections:
        for effect_type, ops in ec.effects.items():
            for op, total in ops.items():
                merged.add(effect_type, op, total)
    return merged
