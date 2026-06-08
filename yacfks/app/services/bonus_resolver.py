from yacfks.app.domains.army_config import ArmyConfiguration
from yacfks.app.domains.enums import StatsInputMode, StatType
from yacfks.app.domains.stats import ArmyBonuses, RawStatsBonuses, EffectiveStatsBonuses
from yacfks.app.repos.widget_repo import WidgetRepo

class BonusResolver:
    """
     Resolves effective stats bonuses, using either a simple case of stats from a rally report,
     or helping account for widgets if stats input comes from a solo battle report.
     Values for stats/widget bonuses are assumed to already account for the base (we're talking relative increases here people, they're simply multipliers >= 1)
    """
    # might have more stuff here, like loading Pet or bear data or something in teh future, for now only work with widgets
    def __init__(self, widget_repo: WidgetRepo):
        self.widget_repo = widget_repo
    

    def resolve(self, config: ArmyConfiguration) -> ArmyBonuses:
        if config.stats_mode == StatsInputMode.SOLO_REPORT:
            return self._resolve_solo_stats(config)
        # if not solo report then it's rally report
        else:
            return self._resolve_rally_stats(config)
            


    def _resolve_rally_stats(self, config: ArmyConfiguration) -> ArmyBonuses:
        # just straigh to effective stats bonuses, since widgets etc are all accounted for in rally battle reports.
        return ArmyBonuses(
            infantry=config.inf_raw_stats_bonuses.straight_to_effective(),
            cavalry=config.cav_raw_stats_bonuses.straight_to_effective(),
            archers=config.arch_raw_stats_bonuses.straight_to_effective()
        )



    def _resolve_solo_stats(self, config: ArmyConfiguration) -> ArmyBonuses:

        # for now, if no leader heroes present we can just retrun stats bonuses as is.
        # this might need changing later, if we need to calc other stuff too besides leader hero widgets,
        #  not sure if e.g. pet bonuses show up in solo reports, but they should
        if not config.leader_heroes:
            return ArmyBonuses(
                infantry=config.inf_raw_stats_bonuses.straight_to_effective(),
                cavalry=config.cav_raw_stats_bonuses.straight_to_effective(),
                archers=config.arch_raw_stats_bonuses.straight_to_effective()
            )
        
        # here we have a dict of lists for every stat that a widget can boost, so we can have a list of all attack boosts for isntance
        # if there are like 2 active widgets in the rally that boosts attack, and another list of all lehtality boosts.
        # widget skills with same effects stack additivley with each other first, and then their combined effects/miltiplier
        # stack the concernced stat bonus multiplicitavely
        active_widget_effects = {
            StatType.ATTACK: [],
            StatType.LETHALITY: [],
            StatType.HEALTH: [],
            StatType.DEFENSE: []
        }

        # for every hero in leader heroes, look up the widget (if any, if hero doesnt have widget for any reason, skip and move on to next hero)
        # see if its active for this side of battle (i.e. if ArmyCOnfig is for Attacker than widget must be an Attacker widget, 
        # if Defender - > Defender Widget) and fetch its bonus value.
        # the add the bonus value to the correct stats list in active_widget_effects, i.e. if widget boosts Lethlity, its value goes into the Lethality
        # list in active_widget_effects.
        for h in config.leader_heroes:
            widget = h.hero.widget

            if widget is None:
                continue

            if widget.widget_mode != config.battle_side:
                continue

            effect = self.widget_repo.get_bonus(h.widget_level)
            active_widget_effects[widget.affected_stat].append(effect)

        # now we have all active widget widget effects gropued per concerned stat in active_widget_effects.
        # we loop them all and stack same effects additiviley if there are several same effects present,
        # so we can easily use them later multiplying  stats bonuses
        # if a stat is unaffected, i.e. theres no widget active boosting the stat, 
        # the widget multiplier for that stat will default to 1
        widget_multipliers = {
                stat: self._combine_widget_effects(effects)
                for stat, effects in active_widget_effects.items()
            }
        
        return ArmyBonuses(
            infantry=self._calc_raw_to_effective(config.inf_raw_stats_bonuses, widget_multipliers),
            cavalry=self._calc_raw_to_effective(config.cav_raw_stats_bonuses, widget_multipliers),
            archers=self._calc_raw_to_effective(config.arch_raw_stats_bonuses, widget_multipliers)
        )



    # combine widget effects, in case some active widgets boost same stat
    def _combine_widget_effects(self, effects: list[float]) -> float:
        total_widget_bonus = 0.0

        # in case "effects" list is empty, return 1
        if not effects:
            return 1.0
        # loop through all effects and remove the base temporalriy, we add the base back later
        for effect in effects:
            total_widget_bonus += (effect - 1)
            
        return 1.0 + total_widget_bonus



    # returining an EffectiveStatsBonuses by simply multiplyting each "raw " stats bonus with respective
    # widget multipler.
    def _calc_raw_to_effective(self, raw: RawStatsBonuses, w: dict[StatType, float]) -> EffectiveStatsBonuses:
        return EffectiveStatsBonuses(
            attack=raw.attack * w[StatType.ATTACK],
            lethality=raw.lethality * w[StatType.LETHALITY],
            health=raw.health * w[StatType.HEALTH],
            defense=raw.defense * w[StatType.DEFENSE]
        )
