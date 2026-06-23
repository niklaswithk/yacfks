from dataclasses import dataclass, field
from yacfks.app.battle.skills.statuses import ActiveStatus

@dataclass
class BattleLineState:
    troop_count: int
    statuses: list[ActiveStatus] = field(default_factory=list)
    pending_losses: int = 0

    @property
    def is_alive(self) -> bool:
        return self.troop_count > 0


