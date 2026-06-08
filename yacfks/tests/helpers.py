
from yacfks.app.domains.troop import TroopDefinition, TroopStack
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.army_config import ArmyConfiguration
from yacfks.app.domains.hero import HeroDefinition, HeroSelection
from yacfks.app.domains.widget import WidgetDefinition
from yacfks.app.domains.enums import StatType, BattleSide, TroopType, StatsInputMode
from yacfks.app.domains.stats import RawStatsBonuses
import random


def make_troop_definition(
    troop_type: TroopType,
    attack: int,
    health: int,
    tier_major: int = 6,
    tier_minor: int = 0,
):
    return TroopDefinition(
        troop_type=troop_type,
        tier_major=tier_major,
        tier_minor=tier_minor,
        base_attack=attack,
        base_lethality=10,
        base_health=health,
        base_defense=10,
        skills=[],
    )

def make_custom_widget(
        id: int,
        name: str,
        hero_id: int,
        stat: StatType,
        mode:BattleSide) -> WidgetDefinition:
    
    return WidgetDefinition(
        id=id,
        name=name,
        hero_id=hero_id,
        affected_stat=stat,
        widget_mode=mode
    )

def make_witcher_widget() -> WidgetDefinition:
    return WidgetDefinition(
        100,
        "Aegis of Fate",
        100,
        StatType.ATTACK,
        BattleSide.ATTACKER
    )

def make_petra_widget() -> WidgetDefinition:
    return WidgetDefinition(
        101,
        "Fate's Writ",
        101,
        StatType.ATTACK,
        BattleSide.ATTACKER
    )

def make_marlin_widget() -> WidgetDefinition:
    return WidgetDefinition(
        102,
        "Mistweaver",
        102,
        StatType.LETHALITY,
        BattleSide.ATTACKER
    )

def make_hilde_widget() -> WidgetDefinition:
    return WidgetDefinition(
        103,
        "Mistweaver",
        103,
        StatType.HEALTH,
        BattleSide.DEFENDER
    )

def make_jabel_widget() -> WidgetDefinition:
    return WidgetDefinition(
        104,
        "Greaves of Faith",
        104,
        StatType.LETHALITY,
        BattleSide.DEFENDER
    )


def make_saul_widget() -> WidgetDefinition:
    return WidgetDefinition(
        105,
        "Rabbitgear Cannon",
        105,
        StatType.ATTACK,
        BattleSide.DEFENDER
    )

def make_zoe_widget() -> WidgetDefinition:
    return WidgetDefinition(
        106,
        "The Unrighteous",
        106,
        StatType.ATTACK,
        BattleSide.DEFENDER
    )


def make_jaeger_widget() -> WidgetDefinition:

    return WidgetDefinition(
        107,
        "Wanderwail",
        107,
        StatType.HEALTH,
        BattleSide.DEFENDER
    )


def make_inf_hero(name: str, widget: WidgetDefinition | None = None) -> HeroDefinition:
    return HeroDefinition(
        id = random.randrange(0,100),
        name=name,
        troop_type=TroopType.INF,
        widget=widget
    )

def make_cav_hero(name: str, widget: WidgetDefinition | None = None) -> HeroDefinition:
    return HeroDefinition(
        id = random.randrange(0,100),
        name=name,
        troop_type=TroopType.CAV,
        widget=widget
    )

def make_arch_hero(name: str, widget: WidgetDefinition | None = None) -> HeroDefinition:
    return HeroDefinition(
        id = random.randrange(0,100),
        name=name,
        troop_type=TroopType.ARCH,
        widget=widget
    )

def make_hero_selection(hero:HeroDefinition, widget_level: int) -> HeroSelection:
    return HeroSelection(
        hero = hero,
        widget_level=widget_level
    )

def make_mock_army_t6() -> Army:
    return Army(
        infantry_line=ArmyLine.from_stacks(
            troop_type=TroopType.INF,
            troop_stacks=[
                TroopStack(
                    definition=TroopDefinition(
                        troop_type=TroopType.INF,
                        tier_major=6,
                        tier_minor=0,
                        base_attack=243,
                        base_lethality=10,
                        base_defense=10,
                        base_health=730,
                        skills=[]
                    ), count=1000
                )
            ]
        ),
        cavalry_line=ArmyLine.from_stacks(
            troop_type=TroopType.CAV,
            troop_stacks=[
                TroopStack(
                    definition=TroopDefinition(
                        troop_type=TroopType.CAV,
                        tier_major=6,
                        tier_minor=0,
                        base_attack=730,
                        base_lethality=10,
                        base_defense=10,
                        base_health=243,
                        skills=[]
                    ), count=1000
                )
            ]
        ),
        archer_line=ArmyLine.from_stacks(
            troop_type=TroopType.ARCH,
            troop_stacks=[
                TroopStack(
                    definition=TroopDefinition(
                        troop_type=TroopType.ARCH,
                        tier_major=6,
                        tier_minor=0,
                        base_attack=974,
                        base_lethality=10,
                        base_defense=10,
                        base_health=183,
                        skills=[]
                    ), count=1000
                )
            ]
        )
    )

def make_mock_army_config(
        stats_mode: StatsInputMode,
        battle_side: BattleSide,
        army: Army,
        inf_stats: RawStatsBonuses,
        cav_stats: RawStatsBonuses,
        arch_stats: RawStatsBonuses,
        leader_heroes: list[HeroSelection],
        joiner_heroes: list[HeroSelection] = []
        ) -> ArmyConfiguration:
    
    return ArmyConfiguration(
        stats_mode=stats_mode,
        battle_side=battle_side,
        army=army,
        inf_raw_stats_bonuses=inf_stats,
        cav_raw_stats_bonuses=cav_stats,
        arch_raw_stats_bonuses=arch_stats,
        leader_heroes=leader_heroes,
        joiner_heroes=joiner_heroes
    )

def make_random_raw_stats() -> RawStatsBonuses:
    return RawStatsBonuses(
        attack=random.uniform(2.0, 10.0),
        lethality=random.uniform(2.0, 10.0),
        health=random.uniform(2.0, 10.0),
        defense=random.uniform(2.0, 10.0)
    )
