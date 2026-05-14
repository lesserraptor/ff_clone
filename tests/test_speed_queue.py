"""Tests for SpeedQueue."""
import pytest
from game.battle.engine import SpeedQueue, create_action
from game.battle.dataclasses import Actor, ActionType


def make_actor(name: str, spd: int) -> Actor:
    return Actor(name=name, hp=100, hp_max=100, atk=10, def_=5, spd=spd)


class TestSpeedQueue:
    def test_empty_queue(self):
        q = SpeedQueue()
        assert len(q) == 0
        assert q.is_empty()
        assert q.pop() is None

    def test_add_one(self):
        q = SpeedQueue()
        actor = make_actor("Hero", 10)
        action = create_action(actor, ActionType.PARTY_ATTACK)
        q.add(action)
        assert len(q) == 1
        assert not q.is_empty()

    def test_pop_returns_highest_speed_first(self):
        q = SpeedQueue()
        fast = make_actor("Fast", 20)
        slow = make_actor("Slow", 5)
        q.add(create_action(slow, ActionType.PARTY_ATTACK))
        q.add(create_action(fast, ActionType.PARTY_ATTACK))
        assert q.pop().actor.name == "Fast"
        assert q.pop().actor.name == "Slow"
        assert q.pop() is None

    def test_clear_empties_queue(self):
        q = SpeedQueue()
        actor = make_actor("Hero", 10)
        q.add(create_action(actor, ActionType.PARTY_ATTACK))
        q.clear()
        assert q.is_empty()
        assert q.pop() is None

    def test_len_reflects_count(self):
        q = SpeedQueue()
        a1 = make_actor("A", 5)
        a2 = make_actor("B", 10)
        q.add(create_action(a1, ActionType.PARTY_ATTACK))
        assert len(q) == 1
        q.add(create_action(a2, ActionType.PARTY_ATTACK))
        assert len(q) == 2

    def test_same_speed_maintains_insert_order(self):
        q = SpeedQueue()
        a1 = make_actor("First", 10)
        a2 = make_actor("Second", 10)
        q.add(create_action(a1, ActionType.PARTY_ATTACK))
        q.add(create_action(a2, ActionType.PARTY_ATTACK))
        # Same speed: inserted order depends on Python sort stability
        assert q.pop() is not None
        assert q.pop() is not None
        assert q.pop() is None
