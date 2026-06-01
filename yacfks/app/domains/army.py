from dataclasses import dataclass
from yacfks.app.domains.troop import TroopStack
from yacfks.app.domains.enums import TroopType

@dataclass
class ArmyLine:
    troop_type: TroopType
    troop_stacks: list[TroopStack]

    # after an army line is init:d, ensure its troop stacks are all of the same type as itself.
    def __post_init__(self):
        for stack in self.troop_stacks:
            if stack.definition.troop_type != self.troop_type:
                raise ValueError(f"All troops in a line must be of the same troop type: expected {self.troop_type}, got {stack.definition.troop_type}")

@dataclass
class Army:
    infantry_line: ArmyLine
    cavalry_line: ArmyLine
    archer_line: ArmyLine

    # after an army is init:d, ensure its lines are of the correct troop types.
    def __post_init__(self):
        if self.infantry_line.troop_type != TroopType.INF:
            raise ValueError("Infantry line must contain infantry troops only")
        if self.cavalry_line.troop_type != TroopType.CAV:
            raise ValueError("Cavalry line must contain cavalry troops only")
        if self.archer_line.troop_type != TroopType.ARCH:
            raise ValueError("Archer line must contain archer troops only")
