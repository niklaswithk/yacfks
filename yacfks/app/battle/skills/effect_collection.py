from collections import defaultdict


class EffectCollection:

    def __init__(self):
        self.effects = defaultdict(lambda: defaultdict(float))
    

    def add(
        self,
        effect_type,
        effect_op,
        value: float
    ) -> None:
        self.effects[effect_type][effect_op] += value

    
    def resolve_multiplier(
        self,
        effect_type
    ) -> float:
        
        groups = self.effects.get(effect_type, {})

        multiplier = 1.0

        for total in groups.values():
            multiplier *= (1 + total / 100 )
        
        return multiplier


