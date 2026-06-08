from yacfks.tests.helpers import make_custom_widget
import pytest
from yacfks.app.domains.enums import StatType, BattleSide

def test_valid_widget():
    widget = make_custom_widget(
        1,
        "test widget",
        23,
        StatType.ATTACK,
        BattleSide.ATTACKER
    )

    assert widget.affected_stat == StatType.ATTACK
    assert widget.widget_mode == BattleSide.ATTACKER
