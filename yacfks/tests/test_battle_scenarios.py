"""
Integration tests against known community sim results.

Stats come from real rally battle reports (RALLY_REPORT mode), so all bonuses —
widgets, pets, etc. — are already baked in. Percentage inputs like "486.4%"
mean +486.4%, i.e. a multiplier of 1 + 4.864 = 5.864; use pct() to convert.

kingshotsimulator.com reference values are noted in comments. 
Small numeric divergences are expected most likely beacuse of rounding differences. floats can be tricky

Add new scenarios below; keep each scenario in its own class.
"""

import pytest
from itertools import pairwise
from yacfks.app.battle.battle_engine import BattleEngine
from yacfks.app.battle.battle_setup import BattleContext
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.army_config import ArmyConfiguration
from yacfks.app.domains.enums import TroopType, BattleSide, StatsInputMode
from yacfks.app.domains.stats import RawStatsBonuses
from yacfks.app.domains.troop import TroopStack
from yacfks.app.services.bonus_resolver import BonusResolver
from yacfks.app.repos.widget_repo import WidgetRepo
from yacfks.app.repos.troop_repo import get_troop
from yacfks.app.repos.hero_repo import amane_joiner, chenko_joiner, saul_joiner, hilde_joiner


# ── helpers ───────────────────────────────────────────────────────────────────

def pct(x: float) -> float:
    """Convert a percentage bonus (e.g. 486.4) to a stat multiplier (5.864)."""
    return 1.0 + x / 100.0


def make_army(inf: int, cav: int, arch: int) -> Army:
    return Army(
        infantry_line=ArmyLine.from_stacks(TroopType.INF,  [TroopStack(get_troop(TroopType.INF,  6), inf)]),
        cavalry_line =ArmyLine.from_stacks(TroopType.CAV,  [TroopStack(get_troop(TroopType.CAV,  6), cav)]),
        archer_line  =ArmyLine.from_stacks(TroopType.ARCH, [TroopStack(get_troop(TroopType.ARCH, 6), arch)]),
    )


def make_cfg(
    army: Army,
    side: BattleSide,
    inf_stats: tuple,
    cav_stats: tuple,
    arch_stats: tuple,
    joiner_heroes=None,
    leader_heroes=None,
) -> ArmyConfiguration:
    """
    inf_stats / cav_stats / arch_stats: (attack%, lethality%, health%, defense%)
    All values are percentage bonuses; pct() is applied internally.
    """

    def raw(t): 
        return RawStatsBonuses(attack=pct(t[0]), lethality=pct(t[1]), health=pct(t[2]), defense=pct(t[3]))
    
    return ArmyConfiguration(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=side,
        army=army,
        inf_raw_stats_bonuses=raw(inf_stats),
        cav_raw_stats_bonuses=raw(cav_stats),
        arch_raw_stats_bonuses=raw(arch_stats),
        leader_heroes=leader_heroes or [],
        joiner_heroes=joiner_heroes or [],
    )


def run_battle(att_cfg: ArmyConfiguration, def_cfg: ArmyConfiguration):
    ctx = BattleContext.from_army_configs(att_cfg, def_cfg, BonusResolver(WidgetRepo()))
    return BattleEngine().run(ctx)


# ── Scenario 1: T6 troops only, 2 Chenko 2 Amane vs 3 Saul 1 Hilde ───────
#
# Attacker: 50k INF / 20k CAV / 30k ARCH
#   Joiners: 2× Chenko L5 (DamageUp op=101 +25%), 2× Amane L5 (DamageUp op=102 +25%)
#   Numerator SkillMod contribution: 1.50 × 1.50 = 2.25
#
# Defender: 60k INF / 20k CAV / 20k ARCH
#   Joiners: 3× Saul L5 (DefenseUp op=112 +10%, op=113 +15%), 1× Hilde L5 (DamageUp op=102 +15%, DefenseUp op=112 +10%)
#   Denominator (vs attacker): (1.40) × (1.45) = 2.03   →  SkillMod att=2.25/2.03≈1.108
#   Numerator (vs defender):   1.15               →  SkillMod def=1.15/1.00=1.15
#
# kingshotsimulator.com: attacker wins, 26 018 INF / 20 000 CAV / 30 000 ARCH survive.
# yacfks:       attacker wins, 25 944 INF / 20 000 CAV / 30 000 ARCH survive.
# Δ = 74 INF (~0.3%) — expected rounding difference.

_S1_ATT_INF  = (486.4, 412.5, 412.5, 671.5)
_S1_ATT_CAV  = (522.7, 522.1, 501.4, 713.0)
_S1_ATT_ARCH = (438.4, 538.6, 474.5, 661.9)

_S1_DEF_INF  = (472.8, 330.4, 362.3, 429.4)
_S1_DEF_CAV  = (489.7, 313.5, 253.0, 439.8)
_S1_DEF_ARCH = (412.0, 295.6, 245.8, 356.8)


class TestScenario1:

    @pytest.fixture(scope="class")
    def result(self):
        att_cfg = make_cfg(
            army=make_army(50_000, 20_000, 30_000),
            side=BattleSide.ATTACKER,
            inf_stats=_S1_ATT_INF, cav_stats=_S1_ATT_CAV, arch_stats=_S1_ATT_ARCH,
            joiner_heroes=[chenko_joiner(5), chenko_joiner(5), amane_joiner(5), amane_joiner(5)],
        )
        def_cfg = make_cfg(
            army=make_army(60_000, 20_000, 20_000),
            side=BattleSide.DEFENDER,
            inf_stats=_S1_DEF_INF, cav_stats=_S1_DEF_CAV, arch_stats=_S1_DEF_ARCH,
            joiner_heroes=[saul_joiner(5), saul_joiner(5), saul_joiner(5), hilde_joiner(5)],
        )
        return run_battle(att_cfg, def_cfg)

    # ── qualitative outcome ───────────────────────────────────────────────────

    def test_attacker_wins(self, result):
        assert result.winner == "attacker"

    def test_defender_fully_eliminated(self, result):
        assert result.defender_remaining == 0

    def test_no_defender_inf_surviving(self, result):
        assert result.snapshots[-1].defender_inf == 0

    def test_no_defender_cav_surviving(self, result):
        assert result.snapshots[-1].defender_cav == 0

    def test_no_defender_arch_surviving(self, result):
        assert result.snapshots[-1].defender_arch == 0

    # ── attacker survivors ────────────────────────────────────────────────────

    def test_attacker_cav_took_no_losses(self, result):
        # CAV was never targeted — defender's INF targeting priority hit ATT INF only
        assert result.snapshots[-1].attacker_cav == 20_000

    def test_attacker_arch_took_no_losses(self, result):
        assert result.snapshots[-1].attacker_arch == 30_000

    def test_attacker_inf_survivors_within_expected_range(self, result):
        # Community sim: 26 018. Our sim: 25 944 (Δ=74, rounding).
        # Range is deliberately loose to tolerate minor formula adjustments.
        inf = result.snapshots[-1].attacker_inf
        assert 24_000 <= inf <= 28_000, f"ATT INF survivors out of expected range: {inf}"

    def test_attacker_total_survivors(self, result):
        # Community sim total: 76 018. Our sim: 75 944.
        total = result.attacker_remaining
        assert 74_000 <= total <= 78_000, f"ATT total survivors out of expected range: {total}"

    # ── turn count sanity ─────────────────────────────────────────────────────

    def test_battle_ends_within_reasonable_turns(self, result):
        # Community sim: ~31 turns. Allow some slack for minor kill-rate differences.
        assert 25 <= result.turns <= 40, f"Battle turn count unexpected: {result.turns}"

    def test_snapshot_count_matches_turns(self, result):
        assert len(result.snapshots) == result.turns

    # ── per-turn monotonicity ─────────────────────────────────────────────────

    def test_attacker_inf_count_never_increases(self, result):
        counts = [s.attacker_inf for s in result.snapshots]
        for turn, (a, b) in enumerate(pairwise(counts), 2):
            assert b <= a, f"ATT INF increased at turn {turn}"

    def test_defender_total_never_increases(self, result):
        totals = [s.defender_inf + s.defender_cav + s.defender_arch for s in result.snapshots]
        for turn, (a, b) in enumerate(pairwise(totals), 2):
            assert b <= a, f"DEF total increased at turn {turn}"


# ── Scenario 2: T6 only, no heroes — simple baseline ──────────────────────
#
# Attacker: 55k INF / 20k CAV / 30k ARCH  (no heroes)
# Defender: 60k INF / 20k CAV / 20k ARCH  (no heroes)
# army_min = 100 000
#
# kingshotsimulator.com: attacker wins, 27 842 INF / 20 000 CAV / 30 000 ARCH
#   survive (total 77 842).
# yacfks: 27 756 INF / 20 000 CAV / 30 000 ARCH (total 77 756).
# Δ = 86 INF (~0.3%) — same systematic rounding offset seen in Scenario 1 (Δ=74).

_S2_ATT_INF  = (597.6, 386.7, 413.9, 573.1)
_S2_ATT_CAV  = (486.5, 327.6, 271.2, 476.2)
_S2_ATT_ARCH = (510.8, 374.6, 300.3, 494.6)

_S2_DEF_INF  = (472.8, 362.3, 429.4, 330.4)
_S2_DEF_CAV  = (489.7, 253.0, 439.8, 313.5)
_S2_DEF_ARCH = (412.0, 245.8, 356.8, 295.6)


class TestScenario2:

    @pytest.fixture(scope="class")
    def result(self):
        att_cfg = make_cfg(
            army=make_army(55_000, 20_000, 30_000),
            side=BattleSide.ATTACKER,
            inf_stats=_S2_ATT_INF, cav_stats=_S2_ATT_CAV, arch_stats=_S2_ATT_ARCH,
        )
        def_cfg = make_cfg(
            army=make_army(60_000, 20_000, 20_000),
            side=BattleSide.DEFENDER,
            inf_stats=_S2_DEF_INF, cav_stats=_S2_DEF_CAV, arch_stats=_S2_DEF_ARCH,
        )
        return run_battle(att_cfg, def_cfg)

    # ── qualitative outcome ───────────────────────────────────────────────────

    def test_attacker_wins(self, result):
        assert result.winner == "attacker"

    def test_defender_fully_eliminated(self, result):
        assert result.defender_remaining == 0

    # ── attacker survivors ────────────────────────────────────────────────────

    def test_attacker_cav_took_no_losses(self, result):
        assert result.snapshots[-1].attacker_cav == 20_000

    def test_attacker_arch_took_no_losses(self, result):
        assert result.snapshots[-1].attacker_arch == 30_000

    def test_attacker_inf_survivors_within_expected_range(self, result):
        # Community sim: 27 842. Our sim: 27 756 (Δ=86, ~0.3% rounding offset).
        inf = result.snapshots[-1].attacker_inf
        assert 26_000 <= inf <= 29_000, f"ATT INF survivors out of expected range: {inf}"

    def test_attacker_total_survivors(self, result):
        # Community sim total: 77 842. Our sim: 77 756.
        total = result.attacker_remaining
        assert 75_000 <= total <= 80_000, f"ATT total survivors out of expected range: {total}"

    # ── turn count sanity ─────────────────────────────────────────────────────

    def test_battle_ends_in_expected_turns(self, result):
        assert 35 <= result.turns <= 45, f"Battle turn count unexpected: {result.turns}"

    def test_snapshot_count_matches_turns(self, result):
        assert len(result.snapshots) == result.turns

    # ── per-turn monotonicity ─────────────────────────────────────────────────

    def test_attacker_inf_count_never_increases(self, result):
        counts = [s.attacker_inf for s in result.snapshots]
        for turn, (a, b) in enumerate(pairwise(counts), 2):
            assert b <= a, f"ATT INF increased at turn {turn}"

    def test_defender_total_never_increases(self, result):
        totals = [s.defender_inf + s.defender_cav + s.defender_arch for s in result.snapshots]
        for turn, (a, b) in enumerate(pairwise(totals), 2):
            assert b <= a, f"DEF total increased at turn {turn}"
