from dataclasses import dataclass

@dataclass
class EffectiveBaseStats:
    attack: float
    lethality: float
    health: float
    defense: float

@dataclass
class RawStatsBonuses:
    attack: float
    lethality: float
    health: float
    defense: float

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
