from dataclasses import dataclass
from yacfks.app.domains.army import Army
from yacfks.app.domains.stats import RawStatsBonuses
from yacfks.app.domains.enums import StatsInputMode, BattleSide
from yacfks.app.domains.hero import HeroSelection

# a "wrapper" of sorts, for battle data input sectiopn in the frontend.
# An ArmyConfig represents what user will input in frontend for Attakcer or Defender for example.
# we'll see how we design the frontend, but Daryls and fraks sim are basucaly the same in terms of input UX.
# an Army can hold ArmyLines, which in turn holds TroopStacks, filled with troop data, like tiers, base stats and troop count
# then a list of Heroes and of course a section to add stats bonuses.
# lastly a "meta" toggle for stats input mode, which will dictate how we calc effective stats, widgets etc.
@dataclass
class ArmyConfiguration:

    # user inputs stats from either a rally report or solo report
    stats_mode: StatsInputMode
    battle_side: BattleSide

    # Army can hold ArmyLines, which in turn holds TroopStacks, filled with troop data, like tiers, base stats and troop count
    army: Army

    # the stats bonuses entered via frontend will be considered RawStatsBopnuses no matter what
    # the bonus resolver will then turn these into EffectiveStatsBonuses, and take care of any widget effect too if stats_mpde is "solo"
    inf_raw_stats_bonuses: RawStatsBonuses
    cav_raw_stats_bonuses: RawStatsBonuses
    arch_raw_stats_bonuses: RawStatsBonuses

    leader_heroes: list[HeroSelection]
    joiner_heroes: list[HeroSelection] 

    def __post_init__(self):

        #max 3 leader heroes. this should already be validated in frontend, but no harm doing it here too
        if len(self.leader_heroes) > 3:
            raise ValueError("Max 3 leader heroes!")
        
        # only allow 1 of each hero class/type for leader heroes, e.g. only 1 Inf hero in leader section, not 2.
        # should also be done already in frontned, but do it here too.
        present_types = set() # a set can only hold uniqeue distinct values, perfet for this.

        for h in self.leader_heroes:
            troop_type = h.hero.troop_type

            if troop_type in present_types:
                raise ValueError(f"There's alreay a leader hero present of type/class {troop_type}")
            
            present_types.add(troop_type)

        # max 4 joiners
        if len(self.joiner_heroes) > 4:
            raise ValueError("Max 4 joiner heroes allwoed!")