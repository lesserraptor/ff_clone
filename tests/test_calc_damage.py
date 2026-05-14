"""Tests for damage calculation."""
from game.battle.engine import calc_damage


class TestCalcDamage:
    def test_atk_greater_than_def(self):
        assert calc_damage(10, 5) == 5

    def test_atk_equal_def(self):
        assert calc_damage(10, 10) == 1  # minimum 1

    def test_atk_less_than_def(self):
        assert calc_damage(5, 10) == 1  # minimum 1

    def test_zero_atk(self):
        assert calc_damage(0, 5) == 1  # minimum 1

    def test_high_values(self):
        assert calc_damage(999, 1) == 998

    def test_zero_both(self):
        assert calc_damage(0, 0) == 1  # minimum 1
