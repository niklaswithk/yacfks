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
    make_saul_widget
    )
from yacfks.app.domains.enums import BattleSide, StatsInputMode
from yacfks.app.domains.hero import HeroSelection

def test_complete_army_config_success():
    inf_stats = make_random_raw_stats()
    cav_stats = make_random_raw_stats()
    arch_stats = make_random_raw_stats()


    selected_leader_heroes = [
        HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), 5),
        HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), 2),
        HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), 6),
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

    assert len(armyconf.leader_heroes) == 3
    assert len(armyconf.joiner_heroes) == 4

def test_reject_more_than_3_leader_heroes():
    # try 4 leader heroes and assert failure with valueerror
    with pytest.raises(ValueError, match="Max 3 leader heroes!"):
        inf_stats = make_random_raw_stats()
        cav_stats = make_random_raw_stats()
        arch_stats = make_random_raw_stats()


        selected_leader_heroes = [
            HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), 5),
            HeroSelection(make_cav_hero("Hilde", make_hilde_widget()), 2),
            HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), 6),
            HeroSelection(make_arch_hero("Saul", make_saul_widget()), 6),
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


def test_reject_leader_hero_class_duplicates():
    # try 2 leader heroes of same troop type, which must fail since its not allowed
    with pytest.raises(ValueError):
        inf_stats = make_random_raw_stats()
        cav_stats = make_random_raw_stats()
        arch_stats = make_random_raw_stats()


        selected_leader_heroes = [
            HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), 5),
            HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), 6),
            HeroSelection(make_arch_hero("Saul", make_saul_widget()), 6),
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


def test_reject_more_than_4_joiner_heroes():
    # try 2 leader heroes of same type, which must fail since its not allowed
    with pytest.raises(ValueError):
        inf_stats = make_random_raw_stats()
        cav_stats = make_random_raw_stats()
        arch_stats = make_random_raw_stats()


        selected_leader_heroes = [
            HeroSelection(make_inf_hero("Withcer :P", make_witcher_widget()), 5),
            HeroSelection(make_arch_hero("Marlin", make_marlin_widget()), 6),
            HeroSelection(make_arch_hero("Saul", make_saul_widget()), 6),
        ]
        selected_joiner_heroes = [
            HeroSelection(make_cav_hero("Chenko")),
            HeroSelection(make_cav_hero("Chenko")),
            HeroSelection(make_arch_hero("Amane")),
            HeroSelection(make_arch_hero("Amane")),
            HeroSelection(make_cav_hero("Chenko")),
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
