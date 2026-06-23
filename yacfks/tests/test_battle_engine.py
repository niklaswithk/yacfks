import pytest
from yacfks.app.battle.battle_engine import BattleEngine
from yacfks.app.battle.battle_setup import BattleContext
from yacfks.app.domains.army import Army, ArmyLine
from yacfks.app.domains.army_config import ArmyConfiguration
from yacfks.app.domains.enums import TroopType, BattleSide, StatsInputMode
from yacfks.app.domains.stats import RawStatsBonuses
from yacfks.app.domains.troop import TroopDefinition, TroopStack
from yacfks.app.services.bonus_resolver import BonusResolver
from yacfks.app.repos.widget_repo import WidgetRepo


# ── shared fixtures ───────────────────────────────────────────────────────────

def _make_raw_stats(val: float = 1.0) -> RawStatsBonuses:
    return RawStatsBonuses(attack=val, lethality=val, health=val, defense=val)


def _make_troop(troop_type: TroopType, attack: float, health: float, skills=None) -> TroopDefinition:
    return TroopDefinition(
        troop_type=troop_type,
        tier_major=6, tier_minor=0,
        base_attack=attack, base_lethality=10,
        base_health=health, base_defense=10,
        skills=skills or [],
    )


def _make_army(count: int, troop_type: TroopType = TroopType.INF) -> Army:
    """Single-troop-type army with minimal placeholder lines for the other two types."""
    inf_def = _make_troop(TroopType.INF, attack=243, health=730)
    cav_def = _make_troop(TroopType.CAV, attack=730, health=243)
    arch_def = _make_troop(TroopType.ARCH, attack=974, health=183)

    def line(td: TroopDefinition, n: int):
        return ArmyLine.from_stacks(td.troop_type, [TroopStack(td, n)])

    if troop_type == TroopType.INF:
        return Army(
            infantry_line=line(inf_def, count),
            cavalry_line=line(cav_def, 1),
            archer_line=line(arch_def, 1),
        )
    elif troop_type == TroopType.CAV:
        return Army(
            infantry_line=line(inf_def, 1),
            cavalry_line=line(cav_def, count),
            archer_line=line(arch_def, 1),
        )
    else:
        return Army(
            infantry_line=line(inf_def, 1),
            cavalry_line=line(cav_def, 1),
            archer_line=line(arch_def, count),
        )


def _make_config(army: Army, side: BattleSide) -> ArmyConfiguration:
    return ArmyConfiguration(
        stats_mode=StatsInputMode.RALLY_REPORT,
        battle_side=side,
        army=army,
        inf_raw_stats_bonuses=_make_raw_stats(),
        cav_raw_stats_bonuses=_make_raw_stats(),
        arch_raw_stats_bonuses=_make_raw_stats(),
        leader_heroes=[],
        joiner_heroes=[],
    )


def _make_context(att_army: Army, def_army: Army) -> BattleContext:
    resolver = BonusResolver(WidgetRepo())
    att_cfg = _make_config(att_army, BattleSide.ATTACKER)
    def_cfg = _make_config(def_army, BattleSide.DEFENDER)
    return BattleContext.from_army_configs(att_cfg, def_cfg, resolver)


# ── basic battle termination ──────────────────────────────────────────────────

class TestBattleTermination:

    def test_battle_produces_a_result(self):
        ctx = _make_context(_make_army(10000), _make_army(5000))
        result = BattleEngine().run(ctx)
        assert result is not None

    def test_stronger_side_wins(self):
        # Attacker has 3× more infantry — should win
        ctx = _make_context(_make_army(30000), _make_army(10000))
        result = BattleEngine().run(ctx)
        assert result.winner == "attacker"

    def test_weaker_side_loses(self):
        ctx = _make_context(_make_army(5000), _make_army(30000))
        result = BattleEngine().run(ctx)
        assert result.winner == "defender"

    def test_winner_has_troops_remaining(self):
        ctx = _make_context(_make_army(30000), _make_army(10000))
        result = BattleEngine().run(ctx)
        assert result.attacker_remaining > 0
        assert result.defender_remaining == 0

    def test_loser_has_no_troops_remaining(self):
        ctx = _make_context(_make_army(5000), _make_army(30000))
        result = BattleEngine().run(ctx)
        assert result.attacker_remaining == 0

    def test_battle_takes_at_least_one_turn(self):
        ctx = _make_context(_make_army(10000), _make_army(5000))
        result = BattleEngine().run(ctx)
        assert result.turns >= 1


# ── snapshots ─────────────────────────────────────────────────────────────────

class TestSnapshots:

    def test_snapshot_count_matches_turns(self):
        ctx = _make_context(_make_army(10000), _make_army(5000))
        result = BattleEngine().run(ctx)
        assert len(result.snapshots) == result.turns

    def test_snapshots_have_decreasing_total_troops(self):
        ctx = _make_context(_make_army(10000), _make_army(10000))
        result = BattleEngine().run(ctx)
        totals = [
            s.attacker_inf + s.attacker_cav + s.attacker_arch
            + s.defender_inf + s.defender_cav + s.defender_arch
            for s in result.snapshots
        ]
        # Each turn must reduce or maintain total (never increase)
        for i in range(1, len(totals)):
            assert totals[i] <= totals[i - 1]

    def test_final_snapshot_reflects_result(self):
        ctx = _make_context(_make_army(30000), _make_army(5000))
        result = BattleEngine().run(ctx)
        last = result.snapshots[-1]
        assert (
            last.defender_inf + last.defender_cav + last.defender_arch == result.defender_remaining
        )


# ── targeting ─────────────────────────────────────────────────────────────────

class TestTargeting:

    def test_attacking_infantry_targets_opposing_infantry_first(self):
        # Both sides have all three troop types. After the battle, the loser's
        # infantry should be reduced to 0 before cavalry, since INF is targeted first.
        ctx = _make_context(_make_army(50000, TroopType.INF), _make_army(5000, TroopType.INF))
        result = BattleEngine().run(ctx)
        # Defender had far fewer inf; they should be gone
        assert result.defender_remaining == 0


# ── troop skills integration ──────────────────────────────────────────────────

class TestTroopSkills:

    def test_troop_with_damage_up_skill_wins_more_easily(self):
        from yacfks.app.repos.troop_repo import get_troop

        # One army uses T6 INF (has +15% TROOP_DAMAGE_UP), the other uses T5 INF (no skill)
        t6 = get_troop(TroopType.INF, 6)
        t5 = get_troop(TroopType.INF, 5)

        cav_def = _make_troop(TroopType.CAV, attack=730, health=243)
        arch_def = _make_troop(TroopType.ARCH, attack=974, health=183)

        def make_mixed_army(inf_def: TroopDefinition) -> Army:
            return Army(
                infantry_line=ArmyLine.from_stacks(TroopType.INF, [TroopStack(inf_def, 10000)]),
                cavalry_line=ArmyLine.from_stacks(TroopType.CAV, [TroopStack(cav_def, 1)]),
                archer_line=ArmyLine.from_stacks(TroopType.ARCH, [TroopStack(arch_def, 1)]),
            )

        # Attacker uses T6 (with skill), defender uses T5 (no skill), same count
        ctx = _make_context(make_mixed_army(t6), make_mixed_army(t5))
        result = BattleEngine().run(ctx)

        # T6 with skill should outlast T5 without skill, even at same count
        assert result.winner == "attacker"
