from yacfks.app.domains.army import ArmyLine, TroopStack
from yacfks.app.domains.stats import EffectiveBaseStats
from collections import defaultdict
import math

def normalize_army_line(line: ArmyLine) -> ArmyLine:
    """ Normalize an ArmyLine by merging together multiple troop stacks of different tiers
       into a singe troop stack, containing a total troop count of that particualr type and tier.
       So e.g. 1 troop stack of 5000 T6 inf and another stack of 1000 T6 inf will be merged into a single
       troop stack of 6000 T6 inf.
       NOTE: Make sure ARmyLine contains stacks of one troop type! Our models for Army and ArmyLine ensures this.
    """

    # init a simple functioning dict
    grouped = defaultdict(int)
    definitions = {}

    for stack in line.troop_stacks:

        # "key" here is tuple (a collection of uniqe values) where each key tuple is made up of troop type and tier
        # this way all T6 inf for exampe can be easlily grouped together, and be distinct/separate from both say T7 infantry.
        key = (
            stack.definition.troop_type,
            stack.definition.tier_major,
            stack.definition.tier_minor,
        )

        # every time we find a certain troop type and tier, we add the count to its entry in "grouped."
        # since "key" is troop type and tier, we can easily count all e.g. T6 infantry and T7 inf separateley, even if theres several collections of each..
        grouped[key] += stack.count

        definitions[key] = stack.definition

    normalized_stacks = []

    # now "grouped" wil have all e.g. T6 infantry grouped togheter, and all e.g. T7 inf groouped togheter, with their respective troop counts summed up.
    # we loop through "grouped" and create new proper stacks for them, now including a troop count, and those stacks will be returned in a new Army LIne.
    for key, total_count in grouped.items():

        normalized_stacks.append(
            TroopStack(
                definition=definitions[key],
                count=total_count,
            )
        )

    return ArmyLine(
        troop_type=line.troop_type,
        troop_stacks=normalized_stacks,
    )


# ArmyLine can contain multiple stacks of differnet tiers of the same troop type, and should be normalized already by normalize_army_line()
# so all e.g. T6 infatrny are 1 stack, all T7 infantry are 1 stack, etc
# lethality and defense always 10
def aggregate_base_stats(line: ArmyLine) -> EffectiveBaseStats:
    
    total_attack = 0.0
    total_health = 0.0

    stacks = line.troop_stacks

    # calc total attack and health
    for stack in stacks:
        total_attack += stack.count * stack.definition.base_attack
        total_health += stack.count * stack.definition.base_health

    if total_attack <= 0 or total_health <= 0:
        raise ValueError("Invalid army line: total attack/health must be > 0")
    
    attack_log_sum = 0.0
    health_log_sum = 0.0

    for stack in stacks:
        count = stack.count
        d = stack.definition

        attack_weight = (count * d.base_attack) / total_attack
        health_weight = (count * d.base_health) / total_health

        # log-space weighted geometric mean
        attack_log_sum += attack_weight * math.log(d.base_attack)
        health_log_sum += health_weight * math.log(d.base_health)
    
    effective_attack = math.exp(attack_log_sum)
    effective_health = math.exp(health_log_sum)

    # final rounding- skip this for now
    # effective_attack = round(effective_attack, 6)
    # effective_health = round(effective_health, 6)

    return EffectiveBaseStats(
        base_attack = effective_attack,
        base_lethality = 10.0,
        base_health = effective_health,
        base_defense = 10.0
        )