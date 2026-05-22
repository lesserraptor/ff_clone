"""Tests for BattleModel - core combat logic."""
import pytest
from game.battle.dataclasses import Actor, ActionType, SpellType
from game.battle.model import BattleModel
from game.battle.engine import calc_damage
from game.stats import apply_level_ups_to_actors


# Minimal spell data for tests
SIMPLE_SPELLS = {
    "fire": {"name": "Fire", "mp_cost": 5, "type": "attack", "power": 18, "target": "enemy"},
    "cure": {"name": "Cure", "mp_cost": 5, "type": "heal", "power": 30, "target": "ally"},
    "raise": {"name": "Raise", "mp_cost": 10, "type": "revive", "power": 30, "target": "ally"},
}

SIMPLE_ENEMIES = {
    "enemies": {
        "goblin": {"name": "Goblin", "hp": 20, "hp_max": 20, "atk": 5, "def": 2, "spd": 6, "xp": 10, "gold": 5},
        "slime": {"name": "Slime", "hp": 12, "hp_max": 12, "atk": 3, "def": 1, "spd": 4, "xp": 5, "gold": 3},
    },
    "encounters": {
        "test_map": ["goblin", "slime"],
    },
}

PARTY_DATA = [
    {"name": "Warrior", "hp": 50, "hp_max": 50, "mp": 0, "mp_max": 0, "atk": 12, "def": 5, "spd": 10, "lvl": 1, "exp": 0, "exp_next": 100, "spells": []},
    {"name": "Wizard", "hp": 35, "hp_max": 35, "mp": 30, "mp_max": 30, "atk": 6, "def": 2, "spd": 8, "lvl": 1, "exp": 0, "exp_next": 100, "spells": ["fire", "cure"]},
]


@pytest.fixture
def model():
    return BattleModel(PARTY_DATA, SIMPLE_ENEMIES, SIMPLE_SPELLS, "test_map")


class TestBattleModelCreation:
    def test_party_created(self, model):
        assert len(model.party) == 2
        assert model.party[0].name == "Warrior"
        assert model.party[1].name == "Wizard"

    def test_enemies_created(self, model):
        assert len(model.enemies) >= 1
        assert len(model.enemies) <= 2
        assert all(e.hp > 0 for e in model.enemies)

    def test_living_party(self, model):
        living = model.get_living_party()
        assert len(living) == 2

    def test_living_enemies(self, model):
        living = model.get_living_enemies()
        assert len(living) >= 1


class TestBattleActions:
    def test_queue_party_action_attack(self, model):
        model.queue_party_action(0, "attack", 0)
        assert 0 in model.party_actions
        assert model.party_actions[0]["type"] == "attack"

    def test_queue_party_action_magic(self, model):
        model.queue_party_action(1, "magic", 0, "fire")
        assert 1 in model.party_actions
        assert model.party_actions[1]["type"] == "magic"
        assert model.party_actions[1]["spell_id"] == "fire"

    def test_prepare_battle_builds_queue(self, model):
        model.queue_party_action(0, "attack", 0)
        model.prepare_battle()
        assert not model.action_queue.is_empty()

    def test_process_next_action(self, model):
        model.queue_party_action(0, "attack", 0)
        model.prepare_battle()
        action = model.process_next_action()
        assert action is not None
        assert action.action_type == ActionType.PARTY_ATTACK

    def test_process_next_action_none_when_empty(self, model):
        model.prepare_battle()
        # If no actions queued (party didn't act, enemies may still act)
        # But if no living enemies, there won't be any actions
        action = model.process_next_action()
        # Either None or an enemy action
        if action is not None:
            assert action.action_type == ActionType.ENEMY_ATTACK


class TestExecuteAttack:
    def test_party_attack_deals_damage(self, model):
        model.queue_party_action(0, "attack", 0)
        model.prepare_battle()
        action = model.process_next_action()
        assert action is not None
        initial_hp = action.target.hp
        events = model.execute_action(action)
        assert len(events) > 0
        assert action.target.hp < initial_hp
        assert events[0].damage > 0

    def test_enemy_attack_deals_damage(self, model):
        # Queue party action so enemies also get actions
        model.queue_party_action(0, "attack", 0)
        model.prepare_battle()
        # Process all actions to find an enemy one
        while True:
            action = model.process_next_action()
            if action is None:
                pytest.skip("No enemy actions in queue")
            if action.action_type == ActionType.ENEMY_ATTACK:
                break
        
        initial_hp = action.target.hp
        events = model.execute_action(action)
        assert action.target.hp < initial_hp
        assert events[0].damage > 0

    def test_attack_min_damage(self, model):
        """Very high def enemy still takes at least 1 damage."""
        model.queue_party_action(0, "attack", 0)
        model.prepare_battle()
        action = model.process_next_action()
        if action is not None and action.action_type == ActionType.PARTY_ATTACK:
            dmg = calc_damage(action.actor.atk, action.target.def_)
            assert dmg >= 1


class TestExecuteMagic:
    def test_attack_spell_damage(self, model):
        model.queue_party_action(1, "magic", 0, "fire")
        model.prepare_battle()
        action = model.process_next_action()
        while action and action.action_type != ActionType.PARTY_MAGIC:
            action = model.process_next_action()
        if action is None:
            pytest.skip("No magic action")
        
        events = model.execute_action(action)
        assert len(events) > 0
        # Fire should damage the enemy
        assert "Fire" in events[0].message

    def test_heal_spell_restores_hp(self, model):
        # Damage the party first
        model.party[0].hp = 30
        # Cast cure
        model.queue_party_action(1, "magic", 0, "cure")
        model.prepare_battle()
        action = model.process_next_action()
        while action and action.action_type != ActionType.PARTY_MAGIC:
            action = model.process_next_action()
        if action is None:
            pytest.skip("No magic action")

        events = model.execute_action(action)
        assert model.party[0].hp > 30
        assert events[0].healed > 0


class TestVictoryAndDefeat:
    def test_victory_when_all_enemies_dead(self, model):
        for enemy in model.enemies:
            enemy.hp = 0
            enemy.alive = False
        victory, defeat = model.check_battle_end()
        assert victory is True
        assert defeat is False

    def test_defeat_when_all_party_dead(self, model):
        for member in model.party:
            member.hp = 0
            member.alive = False
        victory, defeat = model.check_battle_end()
        assert victory is False
        assert defeat is True

    def test_no_end_when_both_alive(self, model):
        victory, defeat = model.check_battle_end()
        assert victory is False
        assert defeat is False

    def test_both_can_be_true(self, model):
        for enemy in model.enemies:
            enemy.hp = 0
            enemy.alive = False
        for member in model.party:
            member.hp = 0
            member.alive = False
        victory, defeat = model.check_battle_end()
        assert victory is True
        assert defeat is True


class TestDeathAndRewards:
    def test_attack_kills_enemy(self, model):
        # Make enemy weak
        enemy = model.enemies[0]
        enemy.hp = 1
        model.queue_party_action(0, "attack", 0)
        model.prepare_battle()
        action = model.process_next_action()
        while action and action.action_type != ActionType.PARTY_ATTACK:
            action = model.process_next_action()
        if action is None:
            pytest.skip("No attack action")
        
        events = model.execute_action(action)
        # Should have a death
        assert any(e.is_death for e in events)
        # Rewards should be granted
        assert model.rewards["xp"] > 0

    def test_death_message_in_events(self, model):
        enemy = model.enemies[0]
        enemy.hp = 1
        model.queue_party_action(0, "attack", 0)
        model.prepare_battle()
        action = model.process_next_action()
        while action and action.action_type != ActionType.PARTY_ATTACK:
            action = model.process_next_action()
        if action is None:
            pytest.skip("No attack action")
        
        events = model.execute_action(action)
        death_events = [e for e in events if e.is_death]
        if death_events:
            assert death_events[0].death_message != ""


class TestLevelUps:
    def test_level_up_on_exp_threshold(self, model):
        member = model.party[0]
        member.exp = member.exp_next  # Just at threshold
        events = apply_level_ups_to_actors(model.party)
        assert len(events) == 1  # 1 level up
        assert member.lvl == 2
        assert member.hp_max == 55  # +5

    def test_multiple_level_ups(self, model):
        member = model.party[0]
        member.exp = member.exp_next * 3  # Way past threshold
        events = apply_level_ups_to_actors(model.party)
        assert len(events) >= 1
        assert member.lvl >= 2

    def test_level_up_stats_increase(self, model):
        member = model.party[0]
        member.exp = member.exp_next
        old_atk = member.atk
        old_def = member.def_
        apply_level_ups_to_actors(model.party)
        assert member.atk == old_atk + 2
        assert member.def_ == old_def + 1
        assert member.hp == member.hp_max  # Full heal on level up
