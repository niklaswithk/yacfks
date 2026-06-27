import random as _random
from typing import Callable

from yacfks.app.battle.skills.effect_collection import EffectCollection
from yacfks.app.battle.skills.enums import EffectType, TriggerType, TargetScope, StackRule
from yacfks.app.battle.skills.skill_context import SkillContext
from yacfks.app.battle.skills.statuses import ActiveStatus, StatusApplication
from yacfks.app.battle.skills.conditions import (
    RandomChanceCondition, RequiresFriendlyTroopType, RequiresTargetTroopType,
)
from yacfks.app.domains.hero import HeroSkillSelection
from yacfks.app.domains.troop import TroopSkill
from yacfks.app.domains.enums import BattleSide, TroopType

# ── Effect type classification ────────────────────────────────────────────────
# Relative to the current attack phase:
#   NUMERATOR effects increase the attacking side's kills
#   DENOMINATOR effects decrease the attacking side's kills

_NUMERATOR_EFFECT_TYPES = {
    EffectType.DAMAGE_UP,
    EffectType.TROOP_DAMAGE_UP,
    EffectType.OPP_DEFENSE_DOWN,
}

_DENOMINATOR_EFFECT_TYPES = {
    EffectType.DEFENSE_UP,
    EffectType.TROOP_DEFENSE_UP,
    EffectType.OPP_DAMAGE_DOWN,
}

# ── Scope groups ──────────────────────────────────────────────────────────────
# SELF and ENEMY here is relative to whichever side currently is skill "caller", as it were.
# so e.g. SELF can point to either Side A or Side B, so it's not for "Attacker" or "Defender" or "you" vs "them/someone else"
# BattleSIde keeps track of Attacker/Side A and Defender/SideB
_SELF_SCOPES = {
    TargetScope.SELF_ARMY,
    TargetScope.SELF_INFANTRY,
    TargetScope.SELF_CAVALRY,
    TargetScope.SELF_ARCHERS,
}
_ENEMY_SCOPES = {
    TargetScope.ENEMY_ARMY,
    TargetScope.ENEMY_INFANTRY,
    TargetScope.ENEMY_CAVALRY,
    TargetScope.ENEMY_ARCHERS,
    TargetScope.CURRENT_TARGET,
    TargetScope.RANDOM_ENEMY_LINE,
}

# Maps specific-troop scopes → TroopType; SELF_ARMY / ENEMY_ARMY → None (all troops)
_SCOPE_TO_TROOP: dict[TargetScope, TroopType] = {
    TargetScope.SELF_INFANTRY:  TroopType.INF,
    TargetScope.SELF_CAVALRY:   TroopType.CAV,
    TargetScope.SELF_ARCHERS:   TroopType.ARCH,
    TargetScope.ENEMY_INFANTRY: TroopType.INF,
    TargetScope.ENEMY_CAVALRY:  TroopType.CAV,
    TargetScope.ENEMY_ARCHERS:  TroopType.ARCH,
}

_TROOP_ORDER = [TroopType.INF, TroopType.CAV, TroopType.ARCH]


class SkillEngine:

    def collect_effects(
        self,
        hero_skills: list[HeroSkillSelection],
        troop_skills: list[TroopSkill],
        trigger: TriggerType,
        context: SkillContext,
        rng_fn: Callable[[], float] = _random.random,
    ) -> tuple[EffectCollection, EffectCollection]:
        """
        Evaluate all skills for a given trigger point.

        Hero skills (ALWAYS / TURN_START / ATTACK): apply their StatusDefinitions to
        context.battle_state; these calls return empty ECs.

        Troop skills (ATTACK trigger): currently uses direct effect routing → contribute to the
        returned (numerator_ec, denominator_ec) immediately.
        """
        numerator_ec = EffectCollection()
        denominator_ec = EffectCollection()

        for hero_sel in hero_skills:
            self._apply_hero_skill(
                trigger=trigger,
                defn=hero_sel.definition,
                level=hero_sel.level,
                context=context,
                rng_fn=rng_fn,
            )

        for troop_skill in troop_skills:
            self._apply_troop_skill(
                trigger=trigger,
                skill=troop_skill,
                context=context,
                numerator_ec=numerator_ec,
                denominator_ec=denominator_ec,
                rng_fn=rng_fn,
            )

        return numerator_ec, denominator_ec

    def _apply_hero_skill(self, trigger, defn, level, context, rng_fn):
        # ALWAYS fires exactly once per battle (called with TriggerType.ALWAYS at battle start).
        # TURN_START and ATTACK must match the current trigger point exactly.
        if defn.trigger == TriggerType.ALWAYS:
            if trigger != TriggerType.ALWAYS:
                return
        elif defn.trigger != trigger:
            return

        if not self._check_conditions(defn.conditions, context, rng_fn):
            return

        if defn.level_data is None:
            return

        level_entry = defn.level_data.get(level)
        if level_entry is None:
            return

        for app in defn.status_applications:
            self._apply_status(app, level_entry, context, rng_fn)

    def _apply_troop_skill(self, trigger, skill, context, numerator_ec, denominator_ec, rng_fn):
        if skill.trigger != trigger:
            return

        if not self._check_conditions(skill.conditions, context, rng_fn):
            return

        if skill.level_data is None:
            return

        level_entry = skill.level_data.get(1)
        if level_entry is None:
            return

        for effect in skill.effects:
            value = level_entry.values.get(effect.effect_op)
            if value is None:
                continue

            if effect.effect_type in _NUMERATOR_EFFECT_TYPES:
                numerator_ec.add(effect.effect_type, effect.effect_op, value)
            elif effect.effect_type in _DENOMINATOR_EFFECT_TYPES:
                denominator_ec.add(effect.effect_type, effect.effect_op, value)
            # RETARGET handled separately (future implementeation)

    def _apply_status(self, app: StatusApplication, level_entry, context: SkillContext, rng_fn) -> None:
        if context is None or context.battle_state is None:
            return

        status_def = app.status
        # attacking side in a given turn can be either Attacker or Defender, since both sides deals damage during a turn.
        # defendind side is just the other side that's currently not the attacking side.
        att_side = context.attacking_side
        def_side = BattleSide.DEFENDER if att_side == BattleSide.ATTACKER else BattleSide.ATTACKER
        scope = app.scope

        # Resolve target side and troop type from placement scope
        if scope in _SELF_SCOPES:
            target_side = att_side
            target_troop = _SCOPE_TO_TROOP.get(scope)  # None for SELF_ARMY
        elif scope == TargetScope.CURRENT_TARGET:
            target_side = def_side
            target_troop = context.defender_troop_type
        # currently there's no RANDOM targeting from what I can tell implemented in game - but maybe it will come in the future? :)
        elif scope == TargetScope.RANDOM_ENEMY_LINE:
            target_side = def_side
            live = [t for t in _TROOP_ORDER if context.battle_state.get_line(def_side, t).is_alive]
            if not live:
                return
            target_troop = live[int(rng_fn() * len(live))]
        elif scope in _ENEMY_SCOPES:
            target_side = def_side
            target_troop = _SCOPE_TO_TROOP.get(scope)  # None for ENEMY_ARMY
        else:
            return  # ATTACKER/DEFENDER_OF_STATUS_TARGET — future

        # Resolve effect values from level_data, keyed by each status effect's effect_op
        effect_values: dict[int, float] = {}
        for eff in status_def.effects:
            v = level_entry.values.get(eff.effect_op)
            if v is not None:
                effect_values[eff.effect_op] = v

        state = context.battle_state

        # apply_delay == 0: status is active this turn (own buffs, immediate enemy debuffs, i.e. goes into numerator/denominator in same turn as triggered).
        # apply_delay > 0: status goes to pending and activates next turn (e.g. Zoe's or Jaegers 1st skill, both have a 1-turn delay)
        immediate = status_def.apply_delay == 0

        existing = [
            s for s in state.pending_statuses + state.active_statuses
            if s.definition.id == status_def.id
            and s.target_side == target_side
            and s.target_troop == target_troop
        ]

        if existing:
            rule = status_def.stack_rule
            # i.e. non-stackable
            if rule == StackRule.UNIQUE:
                return
            # I once thought Jaegers THe Temepest was of REFRESH type, now not so sure, maybe no skill workds this way, but ill support it
            if rule == StackRule.REFRESH:
                existing[0].remaining_turns = status_def.duration
                return
            if rule == StackRule.REPLACE:
                state.pending_statuses = [
                    s for s in state.pending_statuses
                    if not (s.definition.id == status_def.id and s.target_side == target_side and s.target_troop == target_troop)
                ]
                state.active_statuses = [
                    s for s in state.active_statuses
                    if not (s.definition.id == status_def.id and s.target_side == target_side and s.target_troop == target_troop)
                ]
            # STACK: stackable, fall through and add another instance

        new_status = ActiveStatus(
            definition=status_def,
            remaining_turns=status_def.duration,
            source_skill_id=status_def.id,
            target_side=target_side,
            target_troop=target_troop,
            effect_values=effect_values,
        )
        if immediate:
            state.active_statuses.append(new_status)
        else:
            state.pending_statuses.append(new_status)

    def _check_conditions(self, conditions, context: SkillContext, rng_fn) -> bool:
        for condition in conditions:
            if isinstance(condition, RandomChanceCondition):
                if rng_fn() >= condition.chance:
                    return False
            elif isinstance(condition, RequiresTargetTroopType):
                if context is None or context.defender_troop_type is None:
                    return False
                if context.defender_troop_type != condition.troop_type:
                    return False
            elif isinstance(condition, RequiresFriendlyTroopType):
                if context is None:
                    return False
                army = (
                    context.battle_context.attacker_army
                    if context.attacker_troop_type is not None
                    else None
                )
                if army is None:
                    return False
                line = army.get_line(condition.troop_type)
                if not line.is_alive:
                    return False
        return True

    def collect_phase_effects(
        self,
        active_statuses: list[ActiveStatus],
        att_side: BattleSide,
        att_type: TroopType,
        def_side: BattleSide,
        target_type: TroopType,
    ) -> tuple[EffectCollection, EffectCollection]:
        """
        For a specific attack phase, read all active statuses and route their effects
        into (numerator_ec, denominator_ec).

        Routing rules per status effect:
          NUMERATOR effects (DAMAGE_UP, TROOP_DAMAGE_UP, OPP_DEFENSE_DOWN):
            - SELF scope + status on att_side  → numerator  (own troops attacking)
            - ENEMY scope + status on def_side → numerator  (enemy troops debuffed)
          DENOMINATOR effects (DEFENSE_UP, TROOP_DEFENSE_UP, OPP_DAMAGE_DOWN):
            - SELF scope + status on def_side  → denominator  (defending side's own buffs)
        """
        numerator_ec = EffectCollection()
        denominator_ec = EffectCollection()

        for status in active_statuses:
            for eff in status.definition.effects:
                value = status.effect_values.get(eff.effect_op)
                if value is None:
                    continue

                scope = eff.scope

                # Per-effect troop filter: use the effect's own specific-troop scope when present
                # (e.g. SELF_INFANTRY → INF), falling back to the status's target_troop for
                # statuses that were applied with an army-wide scope (SELF_ARMY → None = all squads).
                eff_troop = _SCOPE_TO_TROOP.get(scope)
                troop_filter = eff_troop if eff_troop is not None else status.target_troop

                if eff.effect_type in _NUMERATOR_EFFECT_TYPES:
                    if scope in _SELF_SCOPES and status.target_side == att_side:
                        if troop_filter is None or troop_filter == att_type:
                            numerator_ec.add(eff.effect_type, eff.effect_op, value)
                    elif scope in _ENEMY_SCOPES and status.target_side == def_side:
                        if troop_filter is None or troop_filter == target_type:
                            benefactor_troop = _SCOPE_TO_TROOP.get(eff.benefactor_scope) if eff.benefactor_scope else None
                            if benefactor_troop is None or benefactor_troop == att_type:
                                numerator_ec.add(eff.effect_type, eff.effect_op, value)

                elif eff.effect_type in _DENOMINATOR_EFFECT_TYPES:
                    if scope in _SELF_SCOPES and status.target_side == def_side:
                        if troop_filter is None or troop_filter == target_type:
                            denominator_ec.add(eff.effect_type, eff.effect_op, value)

        return numerator_ec, denominator_ec

    def compute_skill_mod(
        self,
        numerator_ec: EffectCollection,
        denominator_ec: EffectCollection,
    ) -> float:
        numerator = (
            numerator_ec.resolve_multiplier(EffectType.DAMAGE_UP)
            * numerator_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP)
            * numerator_ec.resolve_multiplier(EffectType.OPP_DEFENSE_DOWN)
        )
        denominator = (
            denominator_ec.resolve_multiplier(EffectType.DEFENSE_UP)
            * denominator_ec.resolve_multiplier(EffectType.TROOP_DEFENSE_UP)
            * denominator_ec.resolve_multiplier(EffectType.OPP_DAMAGE_DOWN)
        )
        return numerator / denominator
