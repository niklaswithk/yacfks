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

    with pytest.raises(ValueError):
        ArmyLine(
            troop_type=TroopType.INF,
            troop_stacks=[
                inf_stack,
                cav_stack
            ]
        )

    with pytest.raises(ValueError):
        ArmyLine(
            troop_type=TroopType.INF,
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

    with pytest.raises(ValueError):
        Army(
            infantry_line=cav_line,
            cavalry_line=cav_line,
            archer_line=ArmyLine(
                troop_type=TroopType.ARCH,
                troop_stacks=[]
            )
        )
