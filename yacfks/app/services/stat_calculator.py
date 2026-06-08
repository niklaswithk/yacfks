from yacfks.app.domains.stats import EffectiveBaseStats, EffectiveFinalStats, EffectiveStatsBonuses

# maybe ill just move this  into battle setup, probably all params will be readily available there anyway.
# the messy handling of calcing all EffectiveStatsBonuses depending on user input is handled elsewhere anyway in a bonus resolver.
class StatCalculator:
    @staticmethod
    def build_final_stats(base: EffectiveBaseStats, bonus: EffectiveStatsBonuses) -> EffectiveFinalStats:
        return EffectiveFinalStats(
            attack=base.attack * bonus.attack,
            lethality=base.lethality * bonus.lethality,
            health=base.health * bonus.health,
            defense=base.defense * bonus.defense
        )


# will be replaced by a bonus resolver, creating EffectiveStatsBonuses based on various input methis via UI.
# wont be as simple as below anyhow
    # @staticmethod
    # # calcs effective stats bonuses, with support for widgets and bear trap level bonus to attack
    # def build_effective_stats_bonuses(
    #     attack_bonus: float = 1,
    #     widget_attack_bonus: float = 1,
    #     bear_lvl_bonus: float = 0,
    #     lethality_bonus: float = 1,
    #     widget_lethality_bonus: float = 1,
    #     health_bonus: float = 1,
    #     widget_health_bonus: float = 1,
    #     defense_bonus: float = 1,
    #     widget_defense_bonus: float = 1

    # ) -> EffectiveStatsBonuses:

    #     return EffectiveStatsBonuses(
    #         attack=attack_bonus * widget_attack_bonus + bear_lvl_bonus,
    #         lethality=lethality_bonus * widget_lethality_bonus,
    #         health=health_bonus * widget_health_bonus,
    #         defense=defense_bonus * widget_defense_bonus
    #     )
