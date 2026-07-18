# from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from yacfks.app.domains.troop import TroopStack
from yacfks.app.domains.enums import TroopType
from yacfks.app.battle.skills.definitions import TroopSkillDefinition
from yacfks.app.domains.stats import EffectiveBaseStats
import math


@dataclass
class ArmyLine:
    troop_type: TroopType
    troop_stacks: list[TroopStack]
    base_stats: EffectiveBaseStats

    # calc troop count as a property of the line, so we don't have to sum it up in lots of plcaes
    @property
    def troop_count(self) -> int:
        return sum(stack.count for stack in self.troop_stacks)

    # a simple check to see if there are any troops left or they all dead :)
    # if troop count is greater than 0, this function returns TRUE, else FALSE
    @property
    def is_alive(self) -> bool:
        return self.troop_count > 0
    
    @property
    def troop_skills(self) -> list[TroopSkillDefinition]:
        skills: dict[int, TroopSkillDefinition] = {}

        #loop all troop stacks in ArmyLine, and for each skill add the SkillDef to skills dict aboceve, 
        # going by skill id. This way we don't get duplicate skills, if one skill appears more than once
        # it will simply replace other instances of it in the dict, so the skills dict will always contain discint troop skills
        # so if an ArmyLine has e-g. T6 inf and T7 inf stacks, then three skills would be present, but only 2 skill would be unique/distinct
        # since the T7 inf has 1 skill that's same as T6 inf, so the skills dict will only contain 2 troop skills not 3
        for stack in self.troop_stacks:
            for skill in stack.definition.skills:
                skills[skill.id] = skill
        
        return list(skills.values())


    # after an army line is init:d, ensure its troop stacks are all of the same type as itself.
    def __post_init__(self):
        for stack in self.troop_stacks:
            if stack.definition.troop_type != self.troop_type:
                raise ValueError(f"All troops in a line must be of the same troop type: expected {self.troop_type}, got {stack.definition.troop_type}")


    # a custom factory, create an ArmyLine by providing troop type and a list of troop stacks,
    # and then the factory will normalize and calc the effective base stats in one goe,
    @classmethod
    def from_stacks(
        cls,
        troop_type: TroopType,
        troop_stacks: list[TroopStack]
        ) -> "ArmyLine":

        #normalize the troop stacks
        normalized = cls._normalize_stacks(troop_stacks)
        base_stats = cls._aggregate_base_stats(normalized)

        return cls(
            troop_type=troop_type,
            troop_stacks=normalized,
            base_stats=base_stats
        )

    

    @staticmethod
    def _normalize_stacks(troop_stacks: list[TroopStack]) -> list[TroopStack]:
        """ Normalize an ArmyLine by merging together multiple troop stacks of different tiers
        into a singe troop stack, containing a total troop count of that particualr type and tier.
        So e.g. 1 troop stack of 5000 T6 inf and another stack of 1000 T6 inf will be merged into a single
        troop stack of 6000 T6 inf.
        NOTE: Make sure ARmyLine contains stacks of one troop type! Our models for Army and ArmyLine ensures this.
        """

        # init a simple functioning dict
        grouped = defaultdict(int)
        definitions = {}

        for stack in troop_stacks:

            # "key" here is tuple holding troop type and tier, so each troop type + tier will have its own uniqeue key
            # this way all T6 inf for exampe can be easlily grouped together, and be distinct/separate from both say T7 infantry or T10.1 archers
            # we can use this key to group troop counts if we have several "rows" of troop stacks from frontend that are of same type and tier, 
            # like e.g. one row of 1000 T6 inf and another row of 5000 T6 inf. These 2 rows would both match the same key.
            key = (
                stack.definition.troop_type,
                stack.definition.tier_major,
                stack.definition.tier_minor,
            )

            # every time we find a certain troop type and tier, we add the count to its entry in the "grouped" dictionary.
            # since "key" is troop type and tier, we can easily count all e.g. T6 infantry and T7 inf separateley, even if theres several of each.
            grouped[key] += stack.count

            # save the various distinct troop definitions in another dict
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

        return normalized_stacks


    @staticmethod
    def _aggregate_base_stats(troop_stacks: list[TroopStack]) -> EffectiveBaseStats:
        total_attack = 0.0
        total_health = 0.0

        # calc total attack and health
        for stack in troop_stacks:
            total_attack += stack.count * stack.definition.base_attack
            total_health += stack.count * stack.definition.base_health

        # if total_attack <= 0 or total_health <= 0:
        #     raise ValueError("Invalid army line: total attack/health must be > 0")
        
        attack_log_sum = 0.0
        health_log_sum = 0.0

        for stack in troop_stacks:
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
            attack = effective_attack,
            lethality = 10.0,
            health = effective_health,
            defense = 10.0
            )

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

    # put an alive check for whole army too, will prob be useful :)
    # on second thought, BattleLineState now tracks this, so can prob be removed...some day..
    @property
    def is_alive(self) -> bool:
        return self.total_troop_count > 0

    def get_line(self, troop_type: TroopType) -> "ArmyLine":
        if troop_type == TroopType.INF:
            return self.infantry_line
        if troop_type == TroopType.CAV:
            return self.cavalry_line
        if troop_type == TroopType.ARCH:
            return self.archer_line
        raise ValueError(f"Unknown troop type: {troop_type}")

    # after an army is init:d, ensure its lines are of the correct troop types.
    def __post_init__(self):
        if self.infantry_line.troop_type != TroopType.INF:
            raise ValueError("Infantry line must contain infantry troops only")
        if self.cavalry_line.troop_type != TroopType.CAV:
            raise ValueError("Cavalry line must contain cavalry troops only")
        if self.archer_line.troop_type != TroopType.ARCH:
            raise ValueError("Archer line must contain archer troops only")
        if self.total_troop_count <= 0:
            raise ValueError("Army must contain at least one troop")
