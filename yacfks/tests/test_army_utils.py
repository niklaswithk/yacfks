import pytest
from yacfks.app.domains.army import ArmyLine
from yacfks.app.domains.troop import TroopDefinition, TroopStack
from yacfks.app.domains.enums import TroopType
from yacfks.app.services.army_utils import normalize_army_line, aggregate_base_stats
from yacfks.tests.helpers import make_troop_definition

# test so that an Army line containging several infantry stacks of different Tiers normalize correctly.
def test_norm_army_lines_merges_same_tier():
    # create a test ArmyLine with several "rows" or stacks of infantry, different tiers.
    # 2 stacks are T6 infantry, but different troop counts.
    # 1 stack is T5
    line = ArmyLine(
        troop_type=TroopType.INF,
        troop_stacks=[
            # 1 stackk of 6000 T6 inf
            TroopStack(
                definition=make_troop_definition(
                    troop_type=TroopType.INF,
                    attack=243,
                    health=730
                ),
                count=6000
            ),
            # 1 stack of 1000 T6 inf
            TroopStack(
                definition=make_troop_definition(
                    troop_type=TroopType.INF,
                    attack=243,
                    health=730
                ),
                count=1000
            ),
            # 1 stack of 500 T5 inf
            TroopStack(
                definition=make_troop_definition(
                    troop_type=TroopType.INF,
                    tier_major=5,
                    tier_minor=0,
                    attack=206,
                    health=619
                ),
                count=500
            )
        ]
    )

    # send the test armyLine into the normalize funtion
    norm_line = normalize_army_line(line)

    # the normalized amry line should contain 2 troop stacks, 1 for the combined T6 inf, 1 for the T5 inf.
    assert len(norm_line.troop_stacks) == 2

    # make sure one of the stacks is T6 inf with a combined count of 7000.
    assert any(
        s.count == 7000 and s.definition.troop_type == TroopType.INF and s.definition.tier_major == 6
        for s in norm_line.troop_stacks

    )

    # make sure one of the stacks is T5 inf with a count of 500
    assert any(
        s.count == 500 and s.definition.troop_type == TroopType.INF and s.definition.tier_major == 5
        for s in norm_line.troop_stacks
    )

# test so that the normalization func doesnt merge different tiers
def test_norm_army_lines_doesnt_merge_diff_tiers():
    # create a test ArmyLine with 2 row/stacks of inf, different tiers
    line = ArmyLine(
        troop_type=TroopType.INF,
        troop_stacks=[
            # 1 stackk of 1000 T6 inf
            TroopStack(
                definition=make_troop_definition(
                    troop_type=TroopType.INF,
                    attack=243,
                    health=730),
                count=1000
            ),
            # 1 stack of 1500 T5 inf
            TroopStack(
                definition=make_troop_definition(
                    troop_type=TroopType.INF,
                    tier_major=5,
                    tier_minor=0,
                    attack=206,
                    health=619),
                count=1500
            )
        ]
    )

    # send the test armyLine into the normalize function
    norm_line = normalize_army_line(line)

    # the normalized army line should contain 2 troop stacks, 1 for T6 inf and 1 for T5 inf.
    assert len(norm_line.troop_stacks) == 2

    # make sure the stacks looks as expected - 1 stack of 1000 T6 inf, 1 stack of 1500 T5 inf
    assert any(
        s.count == 1000 and s.definition.troop_type == TroopType.INF and s.definition.tier_major == 6
        for s in norm_line.troop_stacks
    )
    assert any(
        s.count == 1500 and s.definition.troop_type == TroopType.INF and s.definition.tier_major == 5
        for s in norm_line.troop_stacks
    )

# test aggregation of base stats works in a simple case with 1 troop typ and tier, basic sanity test.
def test_agg_base_stats_simple():
    # create a test ArmyLine wirth 1 stack of T6 inf, but with simple fake test stats for easy math verification.
    line = ArmyLine(
        troop_type=TroopType.INF,
        troop_stacks=[
            TroopStack(
                definition=make_troop_definition(
                    troop_type=TroopType.INF,
                    tier_major=6,
                    tier_minor=0,
                    attack=100,
                    health=200
                ),
                count=1000
            )
        ]
    )

    # aggregate the base stats of the army line
    agg_stats = aggregate_base_stats(line)

    # in this simple test case with 1 single troop stack of T6 inf, with fake and simple base stats of 100 attack and 200 health,
    # the math will be really simple - the effective base attack and health should just be the same as the stacks' base stats, since we dont combine stats
    # from different troop tiers.

    # we use pytest.approx, since we still deal with floats, and they can get messy with extrreme precisions
    # for example, the effetive base attack might be for example 100.00000000000004 and not exaclty 100.
    assert agg_stats.attack == pytest.approx(100)
    assert agg_stats.health == pytest.approx(200)
    assert agg_stats.lethality == pytest.approx(10)
    assert agg_stats.defense == pytest.approx(10)

# now for some real tests, with real base stats and mixing tiers.
def test_agg_base_stats_multiple_tiers():
    # create a test ArmyLine wirth 2 stacks of inf, different tiers and real base stats.
    line = ArmyLine(
        troop_type=TroopType.INF,
        troop_stacks=[
            # 1 stack of T6 inf, 6000 troops
            TroopStack(
                definition=make_troop_definition(
                    troop_type=TroopType.INF,
                    tier_major=6,
                    tier_minor=0,
                    attack=243,
                    health=730
                ),
                count=6000
            ),
            # 1 stack of T5 inf, 5000 troops.
            TroopStack(
                definition=make_troop_definition(
                    troop_type=TroopType.INF,
                    tier_major=5,
                    tier_minor=0,
                    attack=206,
                    health=619
                ),
                count=5000
            )
        ]
    )

    # aggregate the base stats of the army line
    agg_stats = aggregate_base_stats(line)

    # the game uses a weighted geomtric mean to combine stats from different tiers, where the weight for each tier is the
    # proportion of the total attack/health contributions that each tier provides.

    # the combined base stats should in this case be higher than the T5 inf, but lower than the T6 inf.
    assert 206 < agg_stats.attack < 243
    assert 619 < agg_stats.health < 730

    # make sure the combined attack and health are as expected.
    # base lehtality and def is always 10.
    assert agg_stats.attack == pytest.approx(226.93800)
    assert agg_stats.health == pytest.approx(681.81063)
    assert agg_stats.lethality == pytest.approx(10)
    assert agg_stats.defense == pytest.approx(10)

# test to send an empty armyline into the aggreagte func, should raise an error
def test_agg_empty_army_line():
    line = ArmyLine(
        troop_type=TroopType.INF,
        troop_stacks=[]
    )

    with pytest.raises(ValueError):
        aggregate_base_stats(line)
