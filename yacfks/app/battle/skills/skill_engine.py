import random as _random
from typing import Callable

from yacfks.app.battle.skills.effect_collection import EffectCollection
from yacfks.app.battle.skills.enums import EffectType, TriggerType, TargetScope
from yacfks.app.battle.skills.skill_context import SkillContext
from yacfks.app.battle.skills.conditions import RequiresFriendlyTroopType, RequiresTargetTroopType
from yacfks.app.domains.hero import HeroSkillSelection
from yacfks.app.domains.troop import TroopSkill

# Effect types that are own-side buffs (go into attacker's EffectCollection)
_OWN_SIDE_EFFECTS = {
    EffectType.DAMAGE_UP,
    EffectType.TROOP_DAMAGE_UP,
    EffectType.OPP_DEFENSE_DOWN,
}

# Effect types that are opponent-side debuffs (go into defender's EffectCollection)
_ENEMY_SIDE_EFFECTS = {
    EffectType.DEFENSE_UP,
    EffectType.TROOP_DEFENSE_UP,
    EffectType.OPP_DAMAGE_DOWN,
}


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

        Returns (att_ec, def_ec):
          att_ec — own-side buffs (DAMAGE_UP, OPP_DEFENSE_DOWN, TROOP_DAMAGE_UP)
          def_ec — opponent-side buffs (DEFENSE_UP, OPP_DAMAGE_DOWN, TROOP_DEFENSE_UP)

        Callers combine these into skill_mod:
            skill_mod = (att_ec.DamageUp * att_ec.OppDefenseDown * att_ec.TroopDamageUp)
                      / (def_ec.DefenseUp * def_ec.OppDamageDown * def_ec.TroopDefenseUp)
        """
        att_ec = EffectCollection()
        def_ec = EffectCollection()

        for hero_sel in hero_skills:
            self._apply_skill(
                trigger=trigger,
                skill_trigger=hero_sel.definition.trigger,
                activation=hero_sel.definition.activation,
                effects=hero_sel.definition.effects,
                conditions=hero_sel.definition.conditions,
                level_data=hero_sel.definition.level_data,
                level=hero_sel.level,
                context=context,
                att_ec=att_ec,
                def_ec=def_ec,
                rng_fn=rng_fn,
            )

        for troop_skill in troop_skills:
            self._apply_skill(
                trigger=trigger,
                skill_trigger=troop_skill.trigger,
                activation=troop_skill.activation,
                effects=troop_skill.effects,
                conditions=troop_skill.conditions,
                level_data=troop_skill.level_data,
                level=1,  # troop skills have a single implicit level
                context=context,
                att_ec=att_ec,
                def_ec=def_ec,
                rng_fn=rng_fn,
            )

        return att_ec, def_ec

    def _apply_skill(
        self,
        trigger,
        skill_trigger,
        activation,
        effects,
        conditions,
        level_data,
        level,
        context,
        att_ec,
        def_ec,
        rng_fn,
    ):
        # ALWAYS skills are evaluated at TURN_START (once per turn, result merged into all phases).
        # ATTACK skills roll independently for each attack phase.
        # Any other trigger must match exactly.
        if skill_trigger == TriggerType.ALWAYS:
            if trigger != TriggerType.TURN_START:
                return
        elif skill_trigger != trigger:
            return

        if not self._check_conditions(conditions, context):
            return

        if activation.is_rng:
            chance = self._resolve_chance(activation, level_data, level)
            if rng_fn() >= chance:
                return

        if level_data is None:
            return

        level_entry = level_data.get(level)
        if level_entry is None:
            return

        for effect in effects:
            value = level_entry.values.get(effect.effect_op)
            if value is None:
                continue

            if effect.effect_type in _OWN_SIDE_EFFECTS:
                att_ec.add(effect.effect_type, effect.effect_op, value)
            elif effect.effect_type in _ENEMY_SIDE_EFFECTS:
                def_ec.add(effect.effect_type, effect.effect_op, value)
            # RETARGET and APPLY_STATUS are handled by dedicated handlers (future)

    def _check_conditions(self, conditions, context: SkillContext) -> bool:
        for condition in conditions:
            if isinstance(condition, RequiresTargetTroopType):
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

    def _resolve_chance(self, activation, level_data, level) -> float:
        if activation.chance is not None:
            return activation.chance
        if level_data and level in level_data:
            return level_data[level].activation_chance or 0.0
        return 0.0

    def compute_skill_mod(
        self,
        att_ec: EffectCollection,
        def_ec: EffectCollection,
    ) -> float:
        numerator = (
            att_ec.resolve_multiplier(EffectType.DAMAGE_UP)
            * att_ec.resolve_multiplier(EffectType.TROOP_DAMAGE_UP)
            * att_ec.resolve_multiplier(EffectType.OPP_DEFENSE_DOWN)
        )
        denominator = (
            def_ec.resolve_multiplier(EffectType.DEFENSE_UP)
            * def_ec.resolve_multiplier(EffectType.TROOP_DEFENSE_UP)
            * def_ec.resolve_multiplier(EffectType.OPP_DAMAGE_DOWN)
        )
        return numerator / denominator
