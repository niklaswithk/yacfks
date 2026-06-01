from yacfks.app.domains.stats import EffectiveBaseStats, EffectiveFinalStats, EffectiveStatsBonuses

class StatCalculator:
    @staticmethod
    def build_final_stats(base: EffectiveBaseStats, bonus: EffectiveStatsBonuses) -> EffectiveFinalStats:
        return EffectiveFinalStats(
            attack=base.attack * bonus.attack,
            lethality=base.lethality * bonus.lethality,
            health=base.health * bonus.health,
            defense=base.defense * bonus.defense
        )


    @staticmethod
    # calcs effective stats bonuses, with support for widgets and bear trap level bonus to attack
    def build_effective_stats_bonuses(
        attack_bonus: float = 1,
        widget_attack_bonus: float = 1,
        bear_lvl_bonus: float = 0,
        lethality_bonus: float = 1,
        widget_lethality_bonus: float = 1,
        health_bonus: float = 1,
        widget_health_bonus: float = 1,
        defense_bonus: float = 1,
        widget_defense_bonus: float = 1

    ) -> EffectiveStatsBonuses:

        return EffectiveStatsBonuses(
            attack=attack_bonus * widget_attack_bonus + bear_lvl_bonus,
            lethality=lethality_bonus * widget_lethality_bonus,
            health=health_bonus * widget_health_bonus,
            defense=defense_bonus * widget_defense_bonus
        )
