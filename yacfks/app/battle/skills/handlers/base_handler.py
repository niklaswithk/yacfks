from abc import ABC, abstractmethod
from yacfks.app.battle.skills.effect_collection import EffectCollection
from yacfks.app.battle.skills.skill_context import SkillContext



class SkillHandler(ABC):
    
    @abstractmethod
    def apply(self, context: SkillContext, effects: EffectCollection) -> None:
        pass


