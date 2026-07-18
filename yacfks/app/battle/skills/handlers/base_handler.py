from abc import ABC, abstractmethod
from yacfks.app.battle.skills.effect_collection import EffectCollection
from yacfks.app.battle.phase_context import PhaseContext



class SkillHandler(ABC):

    @abstractmethod
    def apply(self, context: PhaseContext, effects: EffectCollection) -> None:
        pass


