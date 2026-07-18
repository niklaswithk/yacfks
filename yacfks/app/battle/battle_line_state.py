from dataclasses import dataclass

@dataclass
class BattleLineState:
    troop_count: int
    pending_losses: int = 0

    @property
    def is_alive(self) -> bool:
        return self.troop_count > 0
