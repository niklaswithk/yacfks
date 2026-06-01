import math
import pytest

from yacfks.app.services.formulas import (
    army_size,
    get_army_min,
    troop_factor,
    effective_attack_bonus,
    effective_lethality_bonus,
    effective_health_bonus,
    effective_defense_bonus,
    offensive_factor,
    defensive_factor
)

def test_army_size_default():
    assert army_size() == 0

def test_army_size():
    assert army_size(6000, 6000, 6000) == 18000

def test_get_army_min():
    assert get_army_min(18000, 5000) == 5000

def test_troop_factor():
    assert troop_factor(6000, 5000) == pytest.approx(math.sqrt(6000 * 5000)) #pytest.approx is better for evaluationg floating point numbers, rather than exaxt comparison

def test_effective_attack_bonus_default():
    assert effective_attack_bonus() == pytest.approx(1.0)

def test_effective_lethality_bonus_default():
    assert effective_lethality_bonus() == pytest.approx(1.0)

def test_effective_health_bonus_default():
    assert effective_health_bonus() == pytest.approx(1.0)

def test_effective_defense_bonus_default():
    assert effective_defense_bonus() == pytest.approx(1.0)

def test_effective_attack_bonus_with_some_values():
    # test with some stats taken from in-game: 1005.6% attack, 25% bear level bonus, 7.5% from widget
    # the values we pass into the formula functions are supposed to be what you see in battle reports
    # which are actually relative increases (hinted by the '+' sign you see in battle reports), since they increase troops base stats multiplicatively.
    # The function takes care of that, by accouting for the base and making the effective stat bonus a relative increase,
    #  so don't have to do that elsewhere in the code,
    # so we simply have to just use values as we see them in-game
    # bear level bonus is a flat additive increase to attack, AFTER accouting for the widget.
    assert effective_attack_bonus(attack_bonus=10.056, bear_lvl_bonus=0.25, widget_skill_bonus=0.075) == pytest.approx((1 + 10.056) * (1 + 0.075) + 0.25)

def test_effective_lethality_bonus_with_some_values():
    # test with some stats taken from in-game: 760.1% lethality, 10% from widget
    assert effective_lethality_bonus(lethality_bonus=7.601, widget_skill_bonus=0.1) == pytest.approx((1 + 7.601) * (1 + 0.1))

def test_effective_health_bonus_with_some_values():
    # test with some stats taken from in-game: 672.0% health, 12.5% from widget
    assert effective_health_bonus(health_bonus=6.72, widget_skill_bonus=0.125) == pytest.approx((1 + 6.72) * (1 + 0.125))

def test_effective_defense_bonus_with_some_values():
    # test with some stats taken from in-game: 643.4% defense, 15% from widget
    assert effective_defense_bonus(defense_bonus=6.434, widget_skill_bonus=0.15) == pytest.approx((1 + 6.434) * (1 + 0.15))

