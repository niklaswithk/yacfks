import pytest
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.troop import TroopDefinition, TroopStack
from yacfks.app.domains.enums import TroopType

# try create an armyLine with stacks of different troop types - must raise an error since this is not allowed.
def test_army_line_rejects_mixed_troop_types():
    inf_stack = TroopStack(definition=TroopDefinition(
        troop_type=TroopType.INF,
        tier_major=6,
        tier_minor=0,
        base_attack=243,
        base_lethality=10,
        base_health=730,
        base_defense=10,
        skills=[]
    ), count=5000)

    cav_stack = TroopStack(definition=TroopDefinition(
        troop_type=TroopType.CAV,
        tier_major=6,
        tier_minor=0,
        base_attack=730,
        base_lethality=10,
        base_health=243,
        base_defense=10,
        skills=[]
    ), count=5000)

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
