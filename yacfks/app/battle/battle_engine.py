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
        # Attacker attacks, then defender attacks. Casualties applied at the end.
        self._run_side_attacks(context, state, BattleSide.ATTACKER, BattleSide.DEFENDER)
        self._run_side_attacks(context, state, BattleSide.DEFENDER, BattleSide.ATTACKER)
        self._apply_losses(state)

    def _run_side_attacks(
        self,
        context: BattleContext,
        state: BattleState,
        att_side: BattleSide,
        def_side: BattleSide,
    ) -> None:
        att_hero_skills = self._hero_skills_for_side(context, att_side)
        def_hero_skills = self._hero_skills_for_side(context, def_side)
        skill_ctx = SkillContext(
            battle_context=context,
            battle_state=state,
            attacker_troop_type=None,
            defender_troop_type=None,
        )

        # Roll TURN_START effects: offensive from attacking side, defensive from defending side
        turn_att_ec, _ = self._skill_engine.collect_effects(
            att_hero_skills, [], TriggerType.TURN_START, skill_ctx
        )
        _, turn_def_ec = self._skill_engine.collect_effects(
            def_hero_skills, [], TriggerType.TURN_START, skill_ctx
        )

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
                break  # all defender lines dead

            troop_skills = self._troop_skills_for_line(context, att_side, att_type)

            skill_ctx.attacker_troop_type = att_type
            skill_ctx.defender_troop_type = target_type

            # Roll ATTACK effects per phase: offensive from attacking side, defensive from defending side
            phase_att_ec, _ = self._skill_engine.collect_effects(
                att_hero_skills, troop_skills, TriggerType.ATTACK, skill_ctx
            )
            _, phase_def_ec = self._skill_engine.collect_effects(
                def_hero_skills, [], TriggerType.ATTACK, skill_ctx
            )

            # Merge turn-start + phase collections (keeping offensive and defensive separate)
            merged_att_ec = _merge(turn_att_ec, phase_att_ec)
            merged_def_ec = _merge(turn_def_ec, phase_def_ec)

            skill_mod = self._skill_engine.compute_skill_mod(merged_att_ec, merged_def_ec)

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


def _merge(ec1, ec2):
    """Combine two EffectCollections into a new one (non-destructive)."""
    from yacfks.app.battle.skills.effect_collection import EffectCollection
    merged = EffectCollection()
    for effect_type, ops in ec1.effects.items():
        for op, total in ops.items():
            merged.add(effect_type, op, total)
    for effect_type, ops in ec2.effects.items():
        for op, total in ops.items():
            merged.add(effect_type, op, total)
    return merged
