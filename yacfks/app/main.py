from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.troop import TroopStack, TroopDefinition
from yacfks.app.domains.enums import TroopType
from yacfks.app.services.army_utils import normalize_army_line, aggregate_base_stats
import math

TROOPS = {
    "infantry": [
        TroopDefinition(
            troop_type=TroopType.INF,
            tier_major=5,
            tier_minor=0,
            base_attack=206,
            base_lethality=10,
            base_health=619,
            base_defense=10,
            skills=[]
        ),
        TroopDefinition(
            troop_type=TroopType.INF,
            tier_major=6,
            tier_minor=0,
            base_attack=243,
            base_lethality=10,
            base_health=730,
            base_defense=10,
            skills=[]
        )
    ]
}

def main():
    stack1 = TroopStack(definition=TROOPS["infantry"][0], count=5000)
    stack2 = TroopStack(definition=TROOPS["infantry"][1], count=6000)
    # stack3 = TroopStack(definition=TROOPS["infantry"][1], count=1000)

    line1 = ArmyLine(troop_type=TroopType.INF, troop_stacks=[stack1, stack2])

    normalized_line = normalize_army_line(line1)
    aggregated_stats = aggregate_base_stats(normalized_line)

    troop_factor = math.sqrt(11000 * 5000)

    offensive_factor = (aggregated_stats.attack * aggregated_stats.lethality / 100)
    bear_defensive_factor = (83.333 * 10 / 100)
    bear_dmg_per_turn = troop_factor * offensive_factor / bear_defensive_factor / 100
    print(aggregated_stats)
    print(troop_factor)
    print(offensive_factor)
    print(bear_defensive_factor)
    print(bear_dmg_per_turn)
    print(bear_dmg_per_turn * 10)
    print(math.ceil(bear_dmg_per_turn * 10))


if __name__ == "__main__":
    main()
