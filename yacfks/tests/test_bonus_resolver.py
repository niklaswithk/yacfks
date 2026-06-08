import pytest
from yacfks.tests.helpers import ( 
    make_mock_army_config,
    make_witcher_widget,
    make_marlin_widget,
    make_hilde_widget,
    make_arch_hero,
    make_inf_hero,
    make_cav_hero,
    make_mock_army_t6,
    make_petra_widget,
    make_saul_widget
    )
from yacfks.app.domains.enums import StatsInputMode, BattleSide
from yacfks.app.domains.stats import RawStatsBonuses
from yacfks.app.domains.hero import HeroSelection
from yacfks.app.services.bonus_resolver import BonusResolver
from yacfks.app.repos.widget_repo import WidgetRepo

# try rally stats, i.e. treat stats input as-is
def test_rally_stats_used_as_is_no_widget_as_attacker():
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P")),
        HeroSelection(make_cav_hero("Hilde")),
        HeroSelection(make_arch_hero("Marlin")),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_rally_stats_used_as_is_no_widget_as_defender():
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P")),
        HeroSelection(make_cav_hero("Hilde")),
        HeroSelection(make_arch_hero("Marlin")),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_rally_stats_used_as_is_with_widget_as_attacker():
    # if we recive stats + one or more widgets in "rally" report mode, the bonus resover must
    # ignore the widgets and treat the incoming stats as-is, treating them as already effective stats bonuses,
    # since stats from a rally report has already accounted for the widget effects/bonues
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_rally_stats_used_as_is_with_widget_as_defender():
    # if we recive stats + one or more widgets in "rally" report mode, the bonus resover must
    # ignore the widgets and treat the incoming stats as-is, treating them as already effective stats bonuses,
    # since stats from a rally report has already accounted for the widget effects/bonues
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_rally_stats_used_as_is_with_joiner_widget_as_attacker():
    # if we recive stats + one or more widgets in "rally" report mode, the bonus resover must
    # ignore the widgets and treat the incoming stats as-is, treating them as already effective stats bonuses,
    # since stats from a rally report has already accounted for the widget effects/bonues
    # if we also get joiner heroes with widgets, they will also be disregarded.
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_rally_stats_used_as_is_with_joiner_widget_as_defender():
    # if we recive stats + one or more widgets in "rally" report mode, the bonus resover must
    # ignore the widgets and treat the incoming stats as-is, treating them as already effective stats bonuses,
    # since stats from a rally report has already accounted for the widget effects/bonues
    # if we also get joiner heroes with widgets, they will also be disregarded.
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_rally_stats_used_as_is_no_lead_heroes():

    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
    ]
    selected_joiner_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


# solo stats mode
def test_solo_stats_with_widgets_as_attacker():
    # if we recive stats + one or more widgets in "solo" report mode, the bonus resover must
    # take the widget effects/bonuses into account when calcing the effective bonus stats
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.2)
    assert ab.infantry.lethality == pytest.approx(2.2)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.2)
    assert ab.cavalry.lethality == pytest.approx(2.2)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.2)
    assert ab.archers.lethality == pytest.approx(2.2)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_solo_stats_with_widgets_as_defender():
    # if we recive stats + one or more widgets in "solo" report mode, the bonus resover must
    # take the widget effects/bonuses into account when calcing the effective bonus stats
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.2)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.2)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.2)
    assert ab.archers.defense == pytest.approx(2.0)


def test_solo_stats_without_widgets_as_attacker():
    # if we recive stats + one or more widgets in "solo" report mode, the bonus resover must
    # take the widget effects/bonuses into account when calcing the effective bonus stats
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P")),
        HeroSelection(make_cav_hero("Hilde",)),
        HeroSelection(make_arch_hero("Marlin")),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_solo_stats_without_widgets_as_defender():
    # if we recive stats + one or more widgets in "solo" report mode, the bonus resover must
    # take the widget effects/bonuses into account when calcing the effective bonus stats
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P")),
        HeroSelection(make_cav_hero("Hilde",)),
        HeroSelection(make_arch_hero("Marlin")),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_solo_stats_with_joiner_widgets_as_attacker():
    # if joiner heroes have widgets they must be diregarded, as only leader hero widgets boost stats
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P")),
        HeroSelection(make_cav_hero("Hilde",)),
        HeroSelection(make_arch_hero("Marlin")),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_solo_stats_with_joiner_widgets_as_defender():
    # if joiner heroes have widgets they must be diregarded, as only leader hero widgets boost stats
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P")),
        HeroSelection(make_cav_hero("Hilde",)),
        HeroSelection(make_arch_hero("Marlin")),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_solo_stats_with_widgets_2_leader_heroes():
    # if Attacker and 1 lead amadeus w/ widget + 1 lead hilde w/ widget and another amadeus w/ widget in joiners,
    # we must only acount for lead amadeus widget when calcing effective bonuses since:
    # - Amaedus widget is an Attacker widget and is active when we are Attacker (boosting the "attack" stat bonus)
    # - Hilde widget is Defender widget and its skill wont be active if we are Attacker
    # - joiner amadeus widget doesnt work etiher since widget from joiner heroes wont ever apply
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.2)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.2)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.2)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_solo_stats_no_leader_heroes():
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
    ]
    selected_joiner_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.0)
    assert ab.infantry.lethality == pytest.approx(2.0)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.0)
    assert ab.cavalry.lethality == pytest.approx(2.0)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.0)
    assert ab.archers.lethality == pytest.approx(2.0)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


def test_solo_stats_with_same_stat_widgets_as_attacker():
    # If we have 2 widgets that boost the same stat, amek sure they stack additivley first THEN compound the affected stat
    inf_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    cav_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    arch_stats = RawStatsBonuses(
        attack = 2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )
    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Petra", make_petra_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6),
    ]
    selected_joiner_heroes = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_arch_hero("Amane")),
        HeroSelection(make_arch_hero("Amane"))
    ]
    

    armyconf = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=inf_stats,
        cav_stats=cav_stats,
        arch_stats=arch_stats,
        leader_heroes=selected_leader_heroes,
        joiner_heroes=selected_joiner_heroes
    )

    wr = WidgetRepo()
    resolver = BonusResolver(wr)
    
    ab = resolver.resolve(armyconf)
    
    assert ab.infantry.attack == pytest.approx(2.4)
    assert ab.infantry.lethality == pytest.approx(2.2)
    assert ab.infantry.health == pytest.approx(2.0)
    assert ab.infantry.defense == pytest.approx(2.0)

    assert ab.cavalry.attack == pytest.approx(2.4)
    assert ab.cavalry.lethality == pytest.approx(2.2)
    assert ab.cavalry.health == pytest.approx(2.0)
    assert ab.cavalry.defense == pytest.approx(2.0)

    assert ab.archers.attack == pytest.approx(2.4)
    assert ab.archers.lethality == pytest.approx(2.2)
    assert ab.archers.health == pytest.approx(2.0)
    assert ab.archers.defense == pytest.approx(2.0)


