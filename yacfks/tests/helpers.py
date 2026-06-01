
from yacfks.app.domains.troop import TroopDefinition


def make_troop_definition(
    troop_type,
    attack,
    health,
    tier_major=6,
    tier_minor=0,
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