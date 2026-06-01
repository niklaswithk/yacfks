import pytest
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.troop import TroopStack
from yacfks.app.domains.enums import TroopType
from yacfks.tests.helpers import make_troop_definition

# try create an armyLine with stacks of different troop types - must raise an error since this is not allowed.
def test_army_line_rejects_mixed_troop_types():
    inf_stack = TroopStack(
        definition=make_troop_definition(
            troop_type=TroopType.INF,
            attack=243,
            health=730
    ), count=5000)

    cav_stack = TroopStack(
        definition=make_troop_definition(
            troop_type=TroopType.CAV,
            attack=730,
            health=243
    ), count=5000)

    # Infatry line cant contain cav, so we expect an error
    with pytest.raises(ValueError):
        ArmyLine(
            troop_type=TroopType.INF,
            troop_stacks=[
                inf_stack,
                cav_stack
            ]
        )

    # arhcer line cant contain cav or inf, so we expect an error
    with pytest.raises(ValueError):
        ArmyLine(
            troop_type=TroopType.ARCH,
            troop_stacks=[
                inf_stack,
                cav_stack
            ]
        )

# try to create an Amry with wrong troop types in some ARmyLines - must raise an error since this is not allowed.
def test_army_rejects_mixed_line_types():
    cav_line = ArmyLine(
        troop_type=TroopType.CAV,
        troop_stacks=[]
    )

    # basically same as aboe, but for Army, basic sanity test.
    # An army cant have any army lines where troop types are mixed, e.g the inf line in an Army cant contain cavalry
    with pytest.raises(ValueError):
        Army(
            infantry_line=cav_line,
            cavalry_line=cav_line,
            archer_line=ArmyLine(
                troop_type=TroopType.ARCH,
                troop_stacks=[]
            )
        )

# more explicit army test for mixed lines - inf line contains wrong troop type.
def test_army_rejects_wrong_infantry_line():
    cav_line = ArmyLine(
        troop_type=TroopType.CAV,
        troop_stacks=[]
    )

    with pytest.raises(ValueError):
        Army(
            infantry_line=cav_line,
            cavalry_line=ArmyLine(
                troop_type=TroopType.CAV,
                troop_stacks=[]
            ),
            archer_line=ArmyLine(
                troop_type=TroopType.ARCH,
                troop_stacks=[]
            )
        )

# more explicit army test for mixed lines - cav line contains wrong troop type.
def test_army_rejects_wrong_cavalry_line():
    inf_line = ArmyLine(
        troop_type=TroopType.INF,
        troop_stacks=[]
    )

    with pytest.raises(ValueError):
        Army(
            infantry_line=ArmyLine(
                troop_type=TroopType.INF,
                troop_stacks=[]
            ),
            cavalry_line=inf_line,
            archer_line=ArmyLine(
                troop_type=TroopType.ARCH,
                troop_stacks=[]
            )
        )

# more explicit army test for mixed lines - archer line contains wrong troop type.
def test_army_rejects_wrong_archer_line():
    inf_line = ArmyLine(
        troop_type=TroopType.INF,
        troop_stacks=[]
    )

    with pytest.raises(ValueError):
        Army(
            infantry_line=ArmyLine(
                troop_type=TroopType.INF,
                troop_stacks=[]
            ),
            cavalry_line=ArmyLine(
                troop_type=TroopType.CAV,
                troop_stacks=[]
            ),
            archer_line=inf_line
        )

def test_army_line_accepts_correct_line_types():
    # test that an army with correct line types is accepted, basic sanity test.
    inf_stack1 = TroopStack(
        definition=make_troop_definition(
            troop_type=TroopType.INF,
            attack=243,
            health=730
    ), count=6000)

    inf_stack2 = TroopStack(
        definition=make_troop_definition(
            troop_type=TroopType.INF,
            tier_major=5,
            tier_minor=0,
            attack=206,
            health=619
    ), count=500)

    line = ArmyLine(
        troop_type=TroopType.INF,
        troop_stacks=[
            inf_stack1,
            inf_stack2
        ]
    )

    # the ArmyLine above should accept the 2 infantry troop stacks, so we check that the line has 2 stacks.
    assert len(line.troop_stacks) == 2

def test_army_accepts_correct_line_types():
    army = Army(
        infantry_line=ArmyLine(
            troop_type=TroopType.INF,
            troop_stacks=[],
        ),
        cavalry_line=ArmyLine(
            troop_type=TroopType.CAV,
            troop_stacks=[],
        ),
        archer_line=ArmyLine(
            troop_type=TroopType.ARCH,
            troop_stacks=[],
        ),
    )

    assert army.infantry_line.troop_type == TroopType.INF