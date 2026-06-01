from dataclasses import dataclass
from yacfks.app.domains.troop import TroopStack
from yacfks.app.domains.enums import TroopType

@dataclass
class ArmyLine:
    troop_type: TroopType
    troop_stacks: list[TroopStack]

    # calc troop count as a property of the line, so we don't have to sum it up in lots of plcaes
    @property
    def troop_count(self) -> int:
        return sum(stack.count for stack in self.troop_stacks)

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

    # calc total troop count as a property of the army, so we don't have to sum it up in lots of plcaes
    @property
    def total_troop_count(self) -> int:
        return(
            self.infantry_line.troop_count
            + self.cavalry_line.troop_count
            + self.archer_line.troop_count
        )

    # calc troop count per troop type as properties
    @property
    def infantry_count(self) -> int:
        return self.infantry_line.troop_count

    @property
    def cavalry_count(self) -> int:
        return self.cavalry_line.troop_count

    @property
    def archer_count(self) -> int:
        return self.archer_line.troop_count

    # after an army is init:d, ensure its lines are of the correct troop types.
    def __post_init__(self):
        if self.infantry_line.troop_type != TroopType.INF:
            raise ValueError("Infantry line must contain infantry troops only")
        if self.cavalry_line.troop_type != TroopType.CAV:
            raise ValueError("Cavalry line must contain cavalry troops only")
        if self.archer_line.troop_type != TroopType.ARCH:
            raise ValueError("Archer line must contain archer troops only")
