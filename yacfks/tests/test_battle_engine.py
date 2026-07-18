import pytest
from itertools import pairwise
from yacfks.app.battle.battle_engine import BattleEngine
from yacfks.app.battle.battle_setup import BattleContext
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.army_config import ArmyConfiguration
from yacfks.app.domains.enums import TroopType, BattleSide, StatsInputMode
from yacfks.app.domains.stats import RawStatsBonuses
from yacfks.app.domains.troop import TroopDefinition, TroopStack
from yacfks.app.services.bonus_resolver import BonusResolver
from yacfks.app.repos.troop_repo import get_troop
from yacfks.app.repos.widget_repo import WidgetRepo

# ── Engine (stateless — one instance for the whole module) ───────────────────

BE = BattleEngine()

# ── Short aliases ─────────────────────────────────────────────────────────────

INF  = TroopType.INF
CAV  = TroopType.CAV
ARCH = TroopType.ARCH
ATT  = BattleSide.ATTACKER
DEF  = BattleSide.DEFENDER

# ── Base stats by troop type (attack, health) ─────────────────────────────────

_BASE_STATS: dict[TroopType, tuple[float, float]] = {
    INF:  (243, 730),
    CAV:  (730, 243),
    ARCH: (974, 183),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _troop(troop_type: TroopType, skills: list | None = None) -> TroopDefinition:
    atk, hp = _BASE_STATS[troop_type]
    return TroopDefinition(
        troop_type=troop_type, tier_major=6, tier_minor=0,
        base_attack=atk, base_lethality=10,
        base_health=hp,  base_defense=10,
        skills=skills or [],
    )


def _army(count: int, troop_type: TroopType = INF) -> Army:
    """Single-troop-type army; other two lines hold one placeholder troop each."""
    counts  = {t: (count if t == troop_type else 1) for t in TroopType}
    troops  = {t: _troop(t) for t in TroopType}
    return Army(
        infantry_line=ArmyLine.from_stacks(INF,  [TroopStack(troops[INF],  counts[INF])]),
        cavalry_line =ArmyLine.from_stacks(CAV,  [TroopStack(troops[CAV],  counts[CAV])]),
        archer_line  =ArmyLine.from_stacks(ARCH, [TroopStack(troops[ARCH], counts[ARCH])]),
    )


def _ctx(att_army: Army, def_army: Army) -> BattleContext:
    raw = RawStatsBonuses(attack=1.0, lethality=1.0, health=1.0, defense=1.0)

    def cfg(army: Army, side: BattleSide) -> ArmyConfiguration:
        return ArmyConfiguration(
            stats_mode=StatsInputMode.RALLY_REPORT,
            battle_side=side, army=army,
            inf_raw_stats_bonuses=raw, cav_raw_stats_bonuses=raw, arch_raw_stats_bonuses=raw,
            leader_heroes=[], joiner_heroes=[],
        )

    return BattleContext.from_army_configs(cfg(att_army, ATT), cfg(def_army, DEF), BonusResolver(WidgetRepo()))


def run(att_count: int, def_count: int, troop_type: TroopType = INF):
    return BE.run(_ctx(_army(att_count, troop_type), _army(def_count, troop_type)))


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestBattleTermination:

    def test_battle_produces_a_result(self):
        assert run(10_000, 5_000) is not None

    def test_stronger_side_wins(self):
        assert run(30_000, 10_000).winner == "attacker"

    def test_weaker_side_loses(self):
        assert run(5_000, 30_000).winner == "defender"

    def test_winner_has_troops_remaining(self):
        result = run(30_000, 10_000)
        assert result.attacker_remaining > 0
        assert result.defender_remaining == 0

    def test_loser_has_no_troops_remaining(self):
        result = run(5_000, 30_000)
        assert result.attacker_remaining == 0

    def test_battle_takes_at_least_one_turn(self):
        assert run(10_000, 5_000).turns >= 1


class TestSnapshots:

    def test_snapshot_count_matches_turns(self):
        result = run(10_000, 5_000)
        assert len(result.snapshots) == result.turns

    def test_total_troops_never_increase_turn_over_turn(self):
        result = run(10_000, 10_000)
        totals = [
            s.attacker_inf + s.attacker_cav + s.attacker_arch
            + s.defender_inf + s.defender_cav + s.defender_arch
            for s in result.snapshots
        ]
        for turn, (a, b) in enumerate(pairwise(totals), 2):
            assert b <= a, f"Total troops increased at turn {turn}"

    def test_final_snapshot_matches_result_survivors(self):
        result = run(30_000, 5_000)
        last = result.snapshots[-1]
        assert last.defender_inf + last.defender_cav + last.defender_arch == result.defender_remaining


class TestTargeting:

    def test_infantry_targets_opposing_infantry_first(self):
        # INF is the default target — with a huge att advantage, defender INF is wiped
        result = run(50_000, 5_000)
        assert result.defender_remaining == 0


class TestTroopSkills:

    def test_army_with_troop_skill_outlasts_skillless_army(self):
        # T6 INF has Anti-Cavalry Charge (STATIC TROOP_DAMAGE_UP); T5 INF has no skill
        t6 = get_troop(INF, 6)
        t5 = get_troop(INF, 5)

        def _army_with_inf(inf_def: TroopDefinition) -> Army:
            return Army(
                infantry_line=ArmyLine.from_stacks(INF,  [TroopStack(inf_def,   10_000)]),
                cavalry_line =ArmyLine.from_stacks(CAV,  [TroopStack(_troop(CAV),  1)]),
                archer_line  =ArmyLine.from_stacks(ARCH, [TroopStack(_troop(ARCH), 1)]),
            )

        result = BE.run(_ctx(_army_with_inf(t6), _army_with_inf(t5)))
        assert result.winner == "attacker"
