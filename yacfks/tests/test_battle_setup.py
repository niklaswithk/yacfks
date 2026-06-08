import pytest
from yacfks.tests.helpers import ( 
    make_random_raw_stats,
    make_mock_army_config,
    make_witcher_widget,
    make_marlin_widget,
    make_hilde_widget,
    make_arch_hero,
    make_inf_hero,
    make_cav_hero,
    make_mock_army_t6,
    make_saul_widget,
    make_petra_widget
    )
from yacfks.app.domains.enums import BattleSide, StatsInputMode, TroopType
from yacfks.app.domains.hero import HeroSelection
from yacfks.app.battle.battle_setup import BattleContext
from yacfks.app.repos.widget_repo import WidgetRepo
from yacfks.app.services.bonus_resolver import BonusResolver
from yacfks.app.domains.stats import RawStatsBonuses

def test_accept_simple_valid_pvp_battle_setup():
    # just abasic sanity test, 2 identical armies with idential configs and heroes etc
    # no widgets, identicla simple stats
    # just to make sure a battle context can be set up with simple conditions without crashing

    # set up widget repo
    wr = WidgetRepo()
    # set up the bonus resolver
    br = BonusResolver(wr)
    
    #some simple RawStats, emulating user input via frontend
    # lets re-use for all troop types and for both attacker/defender, easy to calc and verify/assert later
    # might do a helper for this one
    basic_raw_st = RawStatsBonuses(
        attack=2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )

    # some leader heroes
    lead_h = [
        HeroSelection(make_inf_hero("Amadeus")),
        HeroSelection(make_cav_hero("Hilde")),
        HeroSelection(make_arch_hero("Marlin"))
    ]
    
    #some joiner heroes
    joiner_h = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Amane")),
        HeroSelection(make_cav_hero("Amane"))
    ]
    # create a test army config for attacker
    attacker = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=basic_raw_st,
        cav_stats=basic_raw_st,
        arch_stats=basic_raw_st,
        leader_heroes=lead_h,
        joiner_heroes=joiner_h
    )

    # create another test army for defender
    defender = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=basic_raw_st,
        cav_stats=basic_raw_st,
        arch_stats=basic_raw_st,
        leader_heroes=lead_h,
        joiner_heroes=joiner_h
    )

    # crate the battle context!
    context = BattleContext.from_army_configs(attacker_config=attacker, defender_config=defender, bonus_resolver=br)

    # our make_mock_army_t6(), sued for both attacker and defender above, creates an army with 3000 troops total
    assert context.army_min == 3000


    assert len(context.attacker_lead_heroes) == 3
    assert len(context.defender_lead_heroes) == 3

    assert len(context.attacker_joiner_heroes) == 4
    assert len(context.defender_joiner_heroes) == 4

    # assert attacker armies/troops, we already test this in other places, making sure Armylines work correctly.
    assert all(
        s_inf.count == 1000 and s_inf.definition.troop_type == TroopType.INF and s_inf.definition.tier_major == 6
        for s_inf in context.attacker_army.infantry_line.troop_stacks
    )

    assert all(
        s_cav.count == 1000 and s_cav.definition.troop_type == TroopType.CAV and s_cav.definition.tier_major == 6
        for s_cav in context.attacker_army.cavalry_line.troop_stacks
    )

    assert all(
        s_arch.count == 1000 and s_arch.definition.troop_type == TroopType.ARCH and s_arch.definition.tier_major == 6
        for s_arch in context.attacker_army.archer_line.troop_stacks
    )

    # attacker final stats
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(486.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(1460.0)

    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(1460.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(486.0)

    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(1948.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(366.0)

    # defender final stats
    assert context.defender_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(486.0)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(1460.0)

    assert context.defender_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(1460.0)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(486.0)

    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(1948.0)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(366.0)


def test_accept_simple_valid_pvp_battle_setup_with_widgets_rally_report_mode():
    # another basic sanity test, 2 identical armies with idential configs and heroes etc
    # WITH widgets, and identical simple stats. and RALLY report mode.
    # this time, since we do RALLY report mode, the RAWstatsbonuses must be unaffected, since the widget effects
    # are alreay accounted for when user inputs stats from rally report, so we don't do any futher calc/manipulation of RawStatsBonuses,
    # they will just become EffectiveStatsBonuses directly

    # set up widget repo
    wr = WidgetRepo()
    # set up the bonus resolver
    br = BonusResolver(wr)
    
    #some simple RawStats, emulating user input via frontend
    # lets re-use for all troop types and for both attacker/defender, easy to calc and verify/assert later
    # might do a helper for this one
    basic_raw_st = RawStatsBonuses(
        attack=2.0,
        lethality=2.0,
        health=2.0,
        defense=2.0
    )

    # some leader heroes
    lead_h = [
        HeroSelection(make_inf_hero("Amadeus", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6)
    ]
    
    #some joiner heroes
    joiner_h = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Amane")),
        HeroSelection(make_cav_hero("Amane"))
    ]
    # create a test army config for attacker
    attacker = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=basic_raw_st,
        cav_stats=basic_raw_st,
        arch_stats=basic_raw_st,
        leader_heroes=lead_h,
        joiner_heroes=joiner_h
    )

    # create another test army for defender
    defender = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=basic_raw_st,
        cav_stats=basic_raw_st,
        arch_stats=basic_raw_st,
        leader_heroes=lead_h,
        joiner_heroes=joiner_h
    )

    # crate the battle context!
    context = BattleContext.from_army_configs(attacker_config=attacker, defender_config=defender, bonus_resolver=br)

    # our make_mock_army_t6(), sued for both attacker and defender above, creates an army with 3000 troops total
    assert context.army_min == 3000


    assert len(context.attacker_lead_heroes) == 3
    assert len(context.defender_lead_heroes) == 3

    assert len(context.attacker_joiner_heroes) == 4
    assert len(context.defender_joiner_heroes) == 4

    # assert attacker armies/troops, we already test this in other places, making sure Armylines work correctly.
    assert all(
        s_inf.count == 1000 and s_inf.definition.troop_type == TroopType.INF and s_inf.definition.tier_major == 6
        for s_inf in context.attacker_army.infantry_line.troop_stacks
    )

    assert all(
        s_cav.count == 1000 and s_cav.definition.troop_type == TroopType.CAV and s_cav.definition.tier_major == 6
        for s_cav in context.attacker_army.cavalry_line.troop_stacks
    )

    assert all(
        s_arch.count == 1000 and s_arch.definition.troop_type == TroopType.ARCH and s_arch.definition.tier_major == 6
        for s_arch in context.attacker_army.archer_line.troop_stacks
    )

    # attacker final stats
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(486.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(1460.0)

    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(1460.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(486.0)

    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(1948.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(20.0)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(366.0)

    # defender final stats
    assert context.defender_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(486.0)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(1460.0)

    assert context.defender_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(1460.0)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(486.0)

    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(1948.0)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(20.0)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(366.0)


def test_accept_complex_valid_pvp_battle_setup_no_widgets():
    # Try some more real-world stats bonuses, but with no widgets.
    # RALLY report mode, so RawStatsBonuses goes straginht into EffectiveStatsBonuses.

    # set up widget repo
    wr = WidgetRepo()
    # set up the bonus resolver
    br = BonusResolver(wr)
    
    #attacker raw stats - inf
    att_inf_raw_st = RawStatsBonuses(
        attack=9.666,
        lethality=6.381,
        health=7.183,
        defense=7.715
    )
    #attacker raw stats - cav
    att_cav_raw_st = RawStatsBonuses(
        attack=11.267,
        lethality=8.784,
        health=6.014,
        defense=8.130
    )
    #attacker raw stats - arch
    att_arch_raw_st = RawStatsBonuses(
        attack=11.056,
        lethality=8.601,
        health=5.745,
        defense=7.619
    )

    #defender raw stats - inf
    def_inf_raw_st = RawStatsBonuses(
        attack=9.771,
        lethality=6.508,
        health=7.221,
        defense=7.783
    )
    #defender raw stats - cav
    def_cav_raw_st = RawStatsBonuses(
        attack=10.563,
        lethality=7.888,
        health=6.149,
        defense=8.520
    )
    #defender raw stats - arch
    def_arch_raw_st = RawStatsBonuses(
        attack=9.950,
        lethality=7.916,
        health=6.234,
        defense=8.009
    )

    # some leader heroes
    lead_h = [
        HeroSelection(make_inf_hero("Amadeus")),
        HeroSelection(make_cav_hero("Hilde")),
        HeroSelection(make_arch_hero("Marlin"))
    ]
    
    #some joiner heroes
    joiner_h = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Amane")),
        HeroSelection(make_cav_hero("Amane"))
    ]
    # create a test army config for attacker
    attacker = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=att_inf_raw_st,
        cav_stats=att_cav_raw_st,
        arch_stats=att_arch_raw_st,
        leader_heroes=lead_h,
        joiner_heroes=joiner_h
    )

    # create another test army for defender
    defender = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=def_inf_raw_st,
        cav_stats=def_cav_raw_st,
        arch_stats=def_arch_raw_st,
        leader_heroes=lead_h,
        joiner_heroes=joiner_h
    )

    # crate the battle context!
    context = BattleContext.from_army_configs(attacker_config=attacker, defender_config=defender, bonus_resolver=br)

    # our make_mock_army_t6(), sued for both attacker and defender above, creates an army with 3000 troops total
    assert context.army_min == 3000


    assert len(context.attacker_lead_heroes) == 3
    assert len(context.defender_lead_heroes) == 3

    assert len(context.attacker_joiner_heroes) == 4
    assert len(context.defender_joiner_heroes) == 4

    # assert attacker armies/troops, we already test this in other places, making sure Armylines work correctly.
    assert all(
        s_inf.count == 1000 and s_inf.definition.troop_type == TroopType.INF and s_inf.definition.tier_major == 6
        for s_inf in context.attacker_army.infantry_line.troop_stacks
    )

    assert all(
        s_cav.count == 1000 and s_cav.definition.troop_type == TroopType.CAV and s_cav.definition.tier_major == 6
        for s_cav in context.attacker_army.cavalry_line.troop_stacks
    )

    assert all(
        s_arch.count == 1000 and s_arch.definition.troop_type == TroopType.ARCH and s_arch.definition.tier_major == 6
        for s_arch in context.attacker_army.archer_line.troop_stacks
    )

    # attacker final stats
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(2348.838)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(63.810)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(77.150)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(5243.590)

    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(8224.910)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(87.840)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(81.300)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(1461.402)

    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(10768.544)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(86.010)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(76.190)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(1051.335)

    # defender final stats
    assert context.defender_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(2374.353)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(65.080)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(77.830)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(5271.330)

    assert context.defender_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(7710.990)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(78.880)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(85.200)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(1494.207)

    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(9691.300)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(79.160)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(80.090)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(1140.822)


def test_accept_complex_valid_pvp_battle_setup_with_widgets_solo_report_mode():
    # Try some more real-world stats bonuses, but WITH widgets and SOLO report mode
    # Here we expect the RawStatsBonuses to transform into EffectiveStatsBonuses with widget effects taken into account.

    # set up widget repo
    wr = WidgetRepo()
    # set up the bonus resolver
    br = BonusResolver(wr)
    
    #attacker raw stats - inf
    att_inf_raw_st = RawStatsBonuses(
        attack=9.666,
        lethality=6.381,
        health=7.183,
        defense=7.715
    )
    #attacker raw stats - cav
    att_cav_raw_st = RawStatsBonuses(
        attack=11.267,
        lethality=8.784,
        health=6.014,
        defense=8.130
    )
    #attacker raw stats - arch
    att_arch_raw_st = RawStatsBonuses(
        attack=11.056,
        lethality=8.601,
        health=5.745,
        defense=7.619
    )

    #defender raw stats - inf
    def_inf_raw_st = RawStatsBonuses(
        attack=9.771,
        lethality=6.508,
        health=7.221,
        defense=7.783
    )
    #defender raw stats - cav
    def_cav_raw_st = RawStatsBonuses(
        attack=10.563,
        lethality=7.888,
        health=6.149,
        defense=8.520
    )
    #defender raw stats - arch
    def_arch_raw_st = RawStatsBonuses(
        attack=9.950,
        lethality=7.916,
        health=6.234,
        defense=8.009
    )

    # some leader heroes
    lead_h = [
        HeroSelection(make_inf_hero("Amadeus", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6)
    ]
    
    #some joiner heroes
    joiner_h = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Amane")),
        HeroSelection(make_cav_hero("Amane"))
    ]
    # create a test army config for attacker
    attacker = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=att_inf_raw_st,
        cav_stats=att_cav_raw_st,
        arch_stats=att_arch_raw_st,
        leader_heroes=lead_h,
        joiner_heroes=joiner_h
    )

    # create another test army for defender
    defender = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=def_inf_raw_st,
        cav_stats=def_cav_raw_st,
        arch_stats=def_arch_raw_st,
        leader_heroes=lead_h,
        joiner_heroes=joiner_h
    )

    # crate the battle context!
    context = BattleContext.from_army_configs(attacker_config=attacker, defender_config=defender, bonus_resolver=br)

    # our make_mock_army_t6(), sued for both attacker and defender above, creates an army with 3000 troops total
    assert context.army_min == 3000


    assert len(context.attacker_lead_heroes) == 3
    assert len(context.defender_lead_heroes) == 3

    assert len(context.attacker_joiner_heroes) == 4
    assert len(context.defender_joiner_heroes) == 4

    # assert attacker armies/troops, we already test this in other places, making sure Armylines work correctly.
    assert all(
        s_inf.count == 1000 and s_inf.definition.troop_type == TroopType.INF and s_inf.definition.tier_major == 6
        for s_inf in context.attacker_army.infantry_line.troop_stacks
    )

    assert all(
        s_cav.count == 1000 and s_cav.definition.troop_type == TroopType.CAV and s_cav.definition.tier_major == 6
        for s_cav in context.attacker_army.cavalry_line.troop_stacks
    )

    assert all(
        s_arch.count == 1000 and s_arch.definition.troop_type == TroopType.ARCH and s_arch.definition.tier_major == 6
        for s_arch in context.attacker_army.archer_line.troop_stacks
    )

    # attacker final stats
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(2583.722)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(70.191)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(77.150)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(5243.590)

    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(9047.401)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(96.624)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(81.300)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(1461.402)

    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(11845.398)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(94.611)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(76.190)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(1051.335)

    # defender final stats
    assert context.defender_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(2374.353)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(65.080)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(77.830)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(5798.463)

    assert context.defender_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(7710.990)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(78.880)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(85.200)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(1643.628)

    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(9691.300)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(79.160)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(80.090)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(1254.904)


def test_accept_complex_valid_pvp_battle_setup_with_stacking_widgets_solo_report_mode():
    # Try some more real-world stats bonuses, but WITH widgets and SOLO report mode
    # here, we have 2 widget for attacker that should each boost attack by 10% each, so they will stack additilvey
    # with each other first (10 + 10 = 20%) and then compound attack stats
    # Here we expect the RawStatsBonuses to transform into EffectiveStatsBonuses with widget effects taken into account.

    # set up widget repo
    wr = WidgetRepo()
    # set up the bonus resolver
    br = BonusResolver(wr)
    
    #attacker raw stats - inf
    att_inf_raw_st = RawStatsBonuses(
        attack=9.666,
        lethality=6.381,
        health=7.183,
        defense=7.715
    )
    #attacker raw stats - cav
    att_cav_raw_st = RawStatsBonuses(
        attack=11.267,
        lethality=8.784,
        health=6.014,
        defense=8.130
    )
    #attacker raw stats - arch
    att_arch_raw_st = RawStatsBonuses(
        attack=11.056,
        lethality=8.601,
        health=5.745,
        defense=7.619
    )

    #defender raw stats - inf
    def_inf_raw_st = RawStatsBonuses(
        attack=9.771,
        lethality=6.508,
        health=7.221,
        defense=7.783
    )
    #defender raw stats - cav
    def_cav_raw_st = RawStatsBonuses(
        attack=10.563,
        lethality=7.888,
        health=6.149,
        defense=8.520
    )
    #defender raw stats - arch
    def_arch_raw_st = RawStatsBonuses(
        attack=9.950,
        lethality=7.916,
        health=6.234,
        defense=8.009
    )

    # some leader heroes for attacker
    lead_h_att = [
        HeroSelection(make_inf_hero("Amadeus", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Petra", make_petra_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6)
    ]

    # some leader heroes for defender
    lead_h_def = [
        HeroSelection(make_inf_hero("Amadeus", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6)
    ]
    
    #some joiner heroes
    joiner_h = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Amane")),
        HeroSelection(make_cav_hero("Amane"))
    ]
    # create a test army config for attacker
    attacker = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=att_inf_raw_st,
        cav_stats=att_cav_raw_st,
        arch_stats=att_arch_raw_st,
        leader_heroes=lead_h_att,
        joiner_heroes=joiner_h
    )

    # create another test army for defender
    defender = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=def_inf_raw_st,
        cav_stats=def_cav_raw_st,
        arch_stats=def_arch_raw_st,
        leader_heroes=lead_h_def,
        joiner_heroes=joiner_h
    )

    # crate the battle context!
    context = BattleContext.from_army_configs(attacker_config=attacker, defender_config=defender, bonus_resolver=br)

    # our make_mock_army_t6(), sued for both attacker and defender above, creates an army with 3000 troops total
    assert context.army_min == 3000


    assert len(context.attacker_lead_heroes) == 3
    assert len(context.defender_lead_heroes) == 3

    assert len(context.attacker_joiner_heroes) == 4
    assert len(context.defender_joiner_heroes) == 4

    # assert attacker armies/troops, we already test this in other places, making sure Armylines work correctly.
    assert all(
        s_inf.count == 1000 and s_inf.definition.troop_type == TroopType.INF and s_inf.definition.tier_major == 6
        for s_inf in context.attacker_army.infantry_line.troop_stacks
    )

    assert all(
        s_cav.count == 1000 and s_cav.definition.troop_type == TroopType.CAV and s_cav.definition.tier_major == 6
        for s_cav in context.attacker_army.cavalry_line.troop_stacks
    )

    assert all(
        s_arch.count == 1000 and s_arch.definition.troop_type == TroopType.ARCH and s_arch.definition.tier_major == 6
        for s_arch in context.attacker_army.archer_line.troop_stacks
    )

    # attacker final stats
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(2818.606)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(70.191)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(77.150)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(5243.590)

    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(9869.892)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(96.624)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(81.300)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(1461.402)

    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(12922.253)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(94.611)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(76.190)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(1051.335)

    # defender final stats
    assert context.defender_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(2374.353)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(65.080)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(77.830)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(5798.463)

    assert context.defender_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(7710.990)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(78.880)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(85.200)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(1643.628)

    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(9691.300)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(79.160)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(80.090)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(1254.904)


def test_accept_complex_valid_pvp_battle_setup_with_stacking_widgets_mixed_report_mode():
    # Try some more real-world stats bonuses, but WITH widgets and RALLY report mode for attacker, solo for defender.
    # here, we also have 2 widgets for attacker that should each boost attack by 10% each, BUT since we do RALLY report mode, that shouldnt matter 
    # when we get the final stats for attacker, since all that will already be accounted for in a rally report.
    # For defender stats, we have SOLo report mode, so the raw stats bonues will be transmuted to effective/final stats taking the widget(s) into account.

    # set up widget repo
    wr = WidgetRepo()
    # set up the bonus resolver
    br = BonusResolver(wr)
    
    #attacker raw stats - inf
    # here we assume the user has chosen RALLY report mode when inputing attacker stats
    att_inf_raw_st = RawStatsBonuses(
        attack=9.666,
        lethality=6.381,
        health=7.183,
        defense=7.715
    )
    #attacker raw stats - cav
    # here we assume the user has chosen RALLY report mode when inputing attacker stats
    att_cav_raw_st = RawStatsBonuses(
        attack=11.267,
        lethality=8.784,
        health=6.014,
        defense=8.130
    )
    #attacker raw stats - arch
    # here we assume the user has chosen RALLY report mode when inputing attacker stats
    att_arch_raw_st = RawStatsBonuses(
        attack=11.056,
        lethality=8.601,
        health=5.745,
        defense=7.619
    )

    #defender raw stats - inf
    def_inf_raw_st = RawStatsBonuses(
        attack=9.771,
        lethality=6.508,
        health=7.221,
        defense=7.783
    )
    #defender raw stats - cav
    def_cav_raw_st = RawStatsBonuses(
        attack=10.563,
        lethality=7.888,
        health=6.149,
        defense=8.520
    )
    #defender raw stats - arch
    def_arch_raw_st = RawStatsBonuses(
        attack=9.950,
        lethality=7.916,
        health=6.234,
        defense=8.009
    )

    # some leader heroes for attacker
    lead_h_att = [
        HeroSelection(make_inf_hero("Amadeus", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Petra", make_petra_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6)
    ]

    # some leader heroes for defender
    lead_h_def = [
        HeroSelection(make_inf_hero("Amadeus", make_witcher_widget()), widget_level=6),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), widget_level=6),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), widget_level=6)
    ]
    
    #some joiner heroes
    joiner_h = [
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Chenko")),
        HeroSelection(make_cav_hero("Amane")),
        HeroSelection(make_cav_hero("Amane"))
    ]
    # create a test army config for attacker
    # here we assume the user has chosen RALLY report mode when inputing attacker stats
    attacker = make_mock_army_config(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=BattleSide.ATTACKER,
        army=make_mock_army_t6(),
        inf_stats=att_inf_raw_st,
        cav_stats=att_cav_raw_st,
        arch_stats=att_arch_raw_st,
        leader_heroes=lead_h_att,
        joiner_heroes=joiner_h
    )

    # create another test army for defender
    # here we assume the user has chosen SOLO report mode when inputing defender stats
    defender = make_mock_army_config(
        stats_mode=StatsInputMode.SOLO_REPORT,
        battle_side=BattleSide.DEFENDER,
        army=make_mock_army_t6(),
        inf_stats=def_inf_raw_st,
        cav_stats=def_cav_raw_st,
        arch_stats=def_arch_raw_st,
        leader_heroes=lead_h_def,
        joiner_heroes=joiner_h
    )

    # crate the battle context!
    context = BattleContext.from_army_configs(attacker_config=attacker, defender_config=defender, bonus_resolver=br)

    # our make_mock_army_t6(), sued for both attacker and defender above, creates an army with 3000 troops total
    assert context.army_min == 3000


    assert len(context.attacker_lead_heroes) == 3
    assert len(context.defender_lead_heroes) == 3

    assert len(context.attacker_joiner_heroes) == 4
    assert len(context.defender_joiner_heroes) == 4

    # assert attacker armies/troops, we already test this in other places, making sure Armylines work correctly.
    assert all(
        s_inf.count == 1000 and s_inf.definition.troop_type == TroopType.INF and s_inf.definition.tier_major == 6
        for s_inf in context.attacker_army.infantry_line.troop_stacks
    )

    assert all(
        s_cav.count == 1000 and s_cav.definition.troop_type == TroopType.CAV and s_cav.definition.tier_major == 6
        for s_cav in context.attacker_army.cavalry_line.troop_stacks
    )

    assert all(
        s_arch.count == 1000 and s_arch.definition.troop_type == TroopType.ARCH and s_arch.definition.tier_major == 6
        for s_arch in context.attacker_army.archer_line.troop_stacks
    )

    # attacker final stats
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(2348.838)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(63.810)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(77.150)
    assert context.attacker_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(5243.590)

    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(8224.910)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(87.840)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(81.300)
    assert context.attacker_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(1461.402)

    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(10768.544)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(86.010)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(76.190)
    assert context.attacker_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(1051.335)

    # defender final stats
    assert context.defender_final_stats.get_final_stats(TroopType.INF).attack == pytest.approx(2374.353)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).lethality == pytest.approx(65.080)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).defense == pytest.approx(77.830)
    assert context.defender_final_stats.get_final_stats(TroopType.INF).health == pytest.approx(5798.463)

    assert context.defender_final_stats.get_final_stats(TroopType.CAV).attack == pytest.approx(7710.990)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).lethality == pytest.approx(78.880)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).defense == pytest.approx(85.200)
    assert context.defender_final_stats.get_final_stats(TroopType.CAV).health == pytest.approx(1643.628)

    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).attack == pytest.approx(9691.300)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).lethality == pytest.approx(79.160)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).defense == pytest.approx(80.090)
    assert context.defender_final_stats.get_final_stats(TroopType.ARCH).health == pytest.approx(1254.904)

