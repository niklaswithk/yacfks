import math
import pytest
from yacfks.app.battle.damage.damage_calc import compute_kills
from yacfks.app.domains.stats import EffectiveFinalStats


def make_stats(attack=100.0, lethality=100.0, health=100.0, defense=100.0) -> EffectiveFinalStats:
    return EffectiveFinalStats(attack=attack, lethality=lethality, health=health, defense=defense)


class TestComputeKills:

    def test_zero_attacker_returns_zero(self):
        assert compute_kills(0, 5000, make_stats(), make_stats()) == 0

    def test_zero_army_min_returns_zero(self):
        assert compute_kills(10000, 0, make_stats(), make_stats()) == 0

    def test_equal_stats_symmetric(self):
        # With identical stats and equal armies, kills should be deterministic
        kills = compute_kills(10000, 10000, make_stats(), make_stats())
        assert kills > 0

    def test_higher_attack_means_more_kills(self):
        low = compute_kills(10000, 10000, make_stats(attack=100), make_stats())
        high = compute_kills(10000, 10000, make_stats(attack=200), make_stats())
        assert high > low

    def test_higher_defender_health_means_fewer_kills(self):
        low_hp = compute_kills(10000, 10000, make_stats(), make_stats(health=100))
        high_hp = compute_kills(10000, 10000, make_stats(), make_stats(health=200))
        assert high_hp < low_hp

    def test_skill_mod_scales_kills(self):
        base = compute_kills(10000, 10000, make_stats(), make_stats(), skill_mod=1.0)
        boosted = compute_kills(10000, 10000, make_stats(), make_stats(), skill_mod=2.0)
        assert boosted == base * 2

    def test_uses_ceil(self):
        # troop_factor = sqrt(100 * 100) = 100
        # off = 1000 * 1000 / 100 = 10000
        # def = 10 * 10 / 100 = 1.0
        # raw = 100 * 10000 / 1.0 / 100 = 10000 → ceil(10000) = 10000
        kills = compute_kills(100, 100, make_stats(attack=1000, lethality=1000), make_stats(health=10, defense=10))
        assert kills == 10000

    def test_ceil_rounds_up(self):
        # troop_factor = sqrt(3 * 3) = 3
        # off = 100 * 100 / 100 = 100
        # def = 101 * 101 / 100 = 102.01
        # raw = 3 * 100 / 102.01 / 100 ≈ 0.02941 → ceil = 1
        kills = compute_kills(3, 3, make_stats(attack=100, lethality=100), make_stats(health=101, defense=101))
        expected = math.ceil(math.sqrt(9) * 100.0 / (101 * 101 / 100) / 100)
        assert kills == expected

    def test_larger_army_min_increases_kills(self):
        small = compute_kills(10000, 5000, make_stats(), make_stats())
        large = compute_kills(10000, 20000, make_stats(), make_stats())
        assert large > small

    def test_known_value_from_main(self):
        # Based on main.py: 11000 troops, army_min=5000, T6 INF stats, bear defense
        # T6 INF: attack=243, lethality=10; bear: health=83.333, defense=10
        # troop_factor = sqrt(11000 * 5000) ≈ 7416.198
        # off = 243 * 10 / 100 = 24.3
        # def = 83.333 * 10 / 100 = 8.3333
        # raw = 7416.198 * 24.3 / 8.3333 / 100 ≈ 216.2 → ceil = 217
        kills = compute_kills(11000, 5000, make_stats(attack=243, lethality=10), make_stats(health=83.333, defense=10))
        expected = math.ceil(math.sqrt(11000 * 5000) * (243 * 10 / 100) / (83.333 * 10 / 100) / 100)
        assert kills == expected
