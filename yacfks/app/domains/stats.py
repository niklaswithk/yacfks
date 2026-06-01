from dataclasses import dataclass

@dataclass
class EffectiveBaseStats:
    base_attack: float
    base_lethality: float
    base_health: float
    base_defense: float

@dataclass
class EffectiveStatsBonuses:
    attack: float
    lethality: float
    health: float
    defense: float

@dataclass
class EffectiveFinalStats:
    attack: float
    lethality: float
    health: float
    defense: float
