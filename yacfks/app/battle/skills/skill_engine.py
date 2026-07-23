import random as _random
from typing import Callable

from yacfks.app.battle.skills.effect_collection import EffectCollection
from yacfks.app.battle.skills.enums import EffectType, TriggerType, TargetScope, StackRule
from yacfks.app.battle.phase_context import PhaseContext
from yacfks.app.battle.skills.statuses import ActiveEffect, ActiveStatus
from yacfks.app.battle.skills.definitions import EffectSpec, StatusSpec
from yacfks.app.battle.skills.conditions import (
    RandomChanceCondition, RequiresFriendlyTroopType, RequiresTargetTroopType, RequiresMinTurn,
    EveryNTurnsCondition,
)
from yacfks.app.battle.skills.definitions import SkillDefinition, HeroSkillSelection, TroopSkillDefinition, SkillLevelData
from yacfks.app.domains.enums import BattleSide, TroopType

# ── Effect type classification ────────────────────────────────────────────────
# Relative to the current attack phase:
#   NUMERATOR effects boosts the phase attacker SKillMod
#   DENOMINATOR effects (coming from phase defender/enemy side) decrease it

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

# Maps specific-troop scopes → TroopType; SELF_ARMY / ENEMY_ARMY → None (all troops)
_SCOPE_TO_TROOP: dict[TargetScope, TroopType] = {
    TargetScope.SELF_INFANTRY:  TroopType.INF,
    TargetScope.SELF_CAVALRY:   TroopType.CAV,
    TargetScope.SELF_ARCHERS:   TroopType.ARCH,
    TargetScope.ENEMY_INFANTRY: TroopType.INF,
    TargetScope.ENEMY_CAVALRY:  TroopType.CAV,
    TargetScope.ENEMY_ARCHERS:  TroopType.ARCH,
}

# default attack/targeting order
_TROOP_ORDER = [TroopType.INF, TroopType.CAV, TroopType.ARCH]


def _scopes_to_troops(scopes: tuple | None) -> frozenset | None:
    """Resolve a tuple of TargetScopes to a frozenset of TroopTypes, or None for 'any'."""
    if scopes is None:
        return None
    troops = frozenset(_SCOPE_TO_TROOP[s] for s in scopes if s in _SCOPE_TO_TROOP)
    return troops if troops else None



class SkillEngine:

    def evaluate_skills(
        self,
        hero_skills: list[HeroSkillSelection],
        troop_skills: list[TroopSkillDefinition],
        trigger: TriggerType,
        context: PhaseContext | None,
        rng_fn: Callable[[], float] = _random.random,
    ) -> None:
        
        """Evaluate all skills for the given trigger, writing ActiveEffects to BattleState."""
        for sel in hero_skills:
            self._apply_skill(sel.definition, sel.level, trigger, context, rng_fn)
        for skill in troop_skills:
            self._apply_skill(skill, 1, trigger, context, rng_fn)

    def _apply_skill(
        self,
        skill_def: SkillDefinition,
        level: int,
        trigger: TriggerType,
        context: PhaseContext | None,
        rng_fn,
    ) -> None:
        if skill_def.trigger != trigger:
            return
        if skill_def.level_data is None:
            return
        level_entry = skill_def.level_data.get(level)
        if level_entry is None:
            return
        if not self._check_conditions(skill_def.conditions, context, rng_fn, level_entry):
            return
        # statuses before effects: _apply_effect resolves target_troop from status when required_status_id is set
        for status_spec in skill_def.statuses:
            self._apply_status(status_spec, skill_def.id, context)

        # indexes skill effects and applies effects
        # iteravley using the count as index. that way we can map an effect to an effect value 
        # in level data,  while level data can stay flexible enough to allow different 
        # effect_types and value increase pairs per skill level.
        # Ordering matters though, since this is a positional lookup, 
        # and requires skill level effect values to be defined in same order as effects, so be careful.
        # might change to eg a tuple key or explicit effect ID field, so ordering doesnt matter, but for now this will do.
        for i, spec in enumerate(skill_def.effects):
            self._apply_effect(spec, i, skill_def.id, level_entry, context, rng_fn)

    def _apply_effect(
            self,
            spec: EffectSpec,
            effect_index: int,
            source_skill_id: int,
            level_entry: SkillLevelData,
            context: PhaseContext | None,
            rng_fn,
        ) -> None:
        
        if context is None or context.battle_state is None:
            return

        host_side = context.attacking_side
        state = context.battle_state

        # set targeting: status-gated effects inherit target from the status; others resolve from target_scopes.
        target_troops: frozenset | None
        if spec.required_status_id is not None:
            all_statuses = state.get_statuses(host_side) + state.get_statuses(host_side, pending=True)
            matched = next((s for s in all_statuses if s.status_spec.id == spec.required_status_id), None)
            target_troops = matched.target_troops if matched is not None else None
        else:
            scopes = spec.target_scopes
            if scopes is None:
                target_troops = None
            elif scopes[0] == TargetScope.PHASE_TARGET:
                t = context.defender_troop_type
                target_troops = frozenset({t}) if t is not None else None
            # RANDOM_ENEMY_LINE: choosing a random live enemy troop type.
            elif scopes[0] == TargetScope.RANDOM_ENEMY_LINE:
                enemy_side = BattleSide.DEFENDER if host_side == BattleSide.ATTACKER else BattleSide.ATTACKER
                live = [t for t in _TROOP_ORDER if state.get_line(enemy_side, t).is_alive]
                if not live:
                    return
                target_troops = frozenset({live[int(rng_fn() * len(live))]})
            else:
                target_troops = _scopes_to_troops(scopes)

        value = level_entry.values[effect_index]

        all_existing_effects = state.get_effects(host_side) + state.get_effects(host_side, pending=True)

        # UNIQUE effects are globally singular: only one instance of a given (skill_id, effect_op)
        # can exist at all, regardless of which target_troops it was placed for.
        # Example: Evil Eye — first proc wins and sets the target; any further procs this turn are
        # blocked even if they'd target a different troop type.
        # All other rules compare the full (skill_id, effect_op, target_troops) key so that separate
        # troop-type instances can coexist.
        if spec.stack_rule == StackRule.UNIQUE:
            existing = next(
                (ae for ae in all_existing_effects
                 if ae.source_skill_id == source_skill_id and ae.effect_spec.effect_op == spec.effect_op),
                None,
            )
        else:
            existing = next(
                (ae for ae in all_existing_effects
                 if (ae.source_skill_id, ae.effect_spec.effect_op, ae.target_troops)
                    == (source_skill_id, spec.effect_op, target_troops)),
                None,
            )

        # if the current skill effect already exists in battle states' list of ActiveEffects,
        # parse stacking rules
        # default we fall through, i.e. stackable
        if existing is not None:
            rule = spec.stack_rule
            if rule == StackRule.UNIQUE:
                # there can be onyl one!
                return
            if rule == StackRule.REFRESH:
                # the condition check in _apply_skill should ensure we only get here
                # if the skill rolls true, but needs more work still - what if one wants a skill to be both
                # stackable and refresh type?
                # currently this implementation is just wierd...
                # would need a way to track individual instances of same skill_id, so correct one is refreshed,
                #  like a skill_instance_id or something.
                # going  by a key tuple with like skill_id, troop target etc wont be enough to be disctinct.
                # since REFRESH type is just hypothetical, might just drop this type..
                existing.remaining_turns = spec.duration
                return

        # if stackabale, or dont already exist, we create a new ActiveEffect and mutaate the battle state,
        # adding the new ACtiveEffect to the BattleState's list of ActiveEffects on the skill host/callers side
        new_effect = ActiveEffect(
            effect_spec=spec,
            remaining_turns=spec.duration,
            source_skill_id=source_skill_id,
            host_side=host_side,
            target_troops=target_troops,
            value=value,
        )
        # here we handle skill effects that migt have a delay.
        # if delay, add it as a pending effect in  the ActiveEffect list
        if spec.apply_delay == 0:
            state.get_effects(host_side).append(new_effect)
        else:
            state.get_effects(host_side, pending=True).append(new_effect)

    def _check_conditions(self, conditions, context: PhaseContext | None, rng_fn, level_entry=None) -> bool:
        """
        Handle skill effect conditions, like RNG, troop types required etc.
        """
        for condition in conditions:
            if isinstance(condition, RandomChanceCondition):
                # first try to get trigger chance value from skill level, if there is one present.
                # else, we expect it to be in RandomChanceCondition.chance instance var.
                chance = (
                    level_entry.chance
                    if level_entry is not None and level_entry.chance is not None
                    else condition.chance
                )
                if chance is None or rng_fn() >= chance:
                    return False
            elif isinstance(condition, RequiresTargetTroopType):
                if context is None or context.defender_troop_type is None:
                    return False
                if context.defender_troop_type != condition.troop_type:
                    return False
            elif isinstance(condition, RequiresFriendlyTroopType):
                if context is None or context.battle_state is None:
                    return False
                if not context.battle_state.get_line(context.attacking_side, condition.troop_type).is_alive:
                    return False
            elif isinstance(condition, RequiresMinTurn):
                if context is None or context.battle_state is None:
                    return False
                if context.battle_state.turn < condition.min_turn:
                    return False
            elif isinstance(condition, EveryNTurnsCondition):
                if context is None or context.battle_state is None:
                    return False
                if context.battle_state.turn % condition.n != 0:
                    return False
        return True

    def _apply_status(
        self,
        status_spec: StatusSpec,
        source_skill_id: int,
        context: PhaseContext | None,
    ) -> None:
        if context is None or context.battle_state is None:
            return

        host_side = context.attacking_side
        state = context.battle_state

        scopes = status_spec.target_scopes
        target_troops: frozenset | None
        if scopes is None:
            target_troops = None
        elif scopes[0] == TargetScope.PHASE_TARGET:
            t = context.defender_troop_type
            target_troops = frozenset({t}) if t is not None else None
        else:
            target_troops = _scopes_to_troops(scopes)

        all_existing = state.get_statuses(host_side) + state.get_statuses(host_side, pending=True)

        if status_spec.stack_rule == StackRule.UNIQUE:
            already = next(
                (s for s in all_existing
                 if s.source_skill_id == source_skill_id and s.status_spec.id == status_spec.id),
                None,
            )
            if already is not None:
                return

        new_status = ActiveStatus(
            status_spec=status_spec,
            remaining_turns=status_spec.duration,
            source_skill_id=source_skill_id,
            host_side=host_side,
            target_troops=target_troops,
        )
        if status_spec.apply_delay == 0:
            state.get_statuses(host_side).append(new_status)
        else:
            state.get_statuses(host_side, pending=True).append(new_status)

    def build_phase_ecs(
        self,
        att_active_effects: list[ActiveEffect],
        def_active_effects: list[ActiveEffect],
        att_active_statuses: list[ActiveStatus],
        def_active_statuses: list[ActiveStatus],
        att_troop_type: TroopType,
        target_troop_type: TroopType,
    ) -> tuple[EffectCollection, EffectCollection]:
        """
        Route a side's active effects into (numerator_ec, denominator_ec) for one attack phase.

        effect_type decides both numerator/denominator placement AND which side's SkillMod
        an effect goes into:

          NUMERATOR (DAMAGE_UP, OPP_DEFENSE_DOWN, TROOP_DAMAGE_UP):
            owned by the phase attacker → sourced from att_active_effects.
            target_troop filters which enemy troop type must be targeted for the effect to apply.
            benefactor_scope filters which of the owner's/SELF troop types must be attacking for it to apply.

          DENOMINATOR (DEFENSE_UP, OPP_DAMAGE_DOWN, TROOP_DEFENSE_UP):
            owned by the phase defender → sourced from def_active_effects.
            target_troop filters which of the attacker's troop types must be attacking.
            benefactor_scope filters which of the owner's/SELF troop types must be under attack.

        Effects with required_status_id are skipped unless that status is present in the
        relevant side's active statuses (att_active_statuses for numerator, def_active_statuses
        for denominator).
        """
        numerator_ec = EffectCollection()
        denominator_ec = EffectCollection()

        # fetch all applicable numerator effects from phase attacker
        for ae in att_active_effects:
            spec = ae.effect_spec
            if spec.required_status_id is not None:
                if not any(s.status_spec.id == spec.required_status_id for s in att_active_statuses):
                    continue
            benefactor_troops = _scopes_to_troops(spec.benefactor_scopes)
            if spec.effect_type in _NUMERATOR_EFFECT_TYPES:
                if ae.target_troops is None or target_troop_type in ae.target_troops:
                    if benefactor_troops is None or att_troop_type in benefactor_troops:
                        numerator_ec.add(spec.effect_type, spec.effect_op, ae.value)

        # fetch all applicable denominator effects from phase defender
        for ae in def_active_effects:
            spec = ae.effect_spec
            if spec.required_status_id is not None:
                if not any(s.status_spec.id == spec.required_status_id for s in def_active_statuses):
                    continue
            benefactor_troops = _scopes_to_troops(spec.benefactor_scopes)
            if spec.effect_type in _DENOMINATOR_EFFECT_TYPES:
                if ae.target_troops is None or att_troop_type in ae.target_troops:
                    if benefactor_troops is None or target_troop_type in benefactor_troops:
                        denominator_ec.add(spec.effect_type, spec.effect_op, ae.value)

        return numerator_ec, denominator_ec

    def collect_retarget(
        self,
        troop_skills: list[TroopSkillDefinition],
        context: PhaseContext | None,
        rng_fn: Callable[[], float] = _random.random,
    ) -> bool:
        """Returns True if a RETARGET troop skill rolls true.
        It's really only for Ambusher CAV skill.

        Called during target pre-computation at beginning of turn, before any attack phases
        takes place.
        """
        for skill in troop_skills:
            if skill.trigger != TriggerType.TROOP_SPECIAL:
                continue
            if not any(eff.effect_type == EffectType.RETARGET for eff in skill.effects):
                continue
            if self._check_conditions(skill.conditions, context, rng_fn):
                return True
        return False

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
