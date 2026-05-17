from abc import ABC, abstractmethod
from typing import Optional
import random
from game.battle.dataclasses import Actor, BattleEvent
from game.battle.model import BattleModel
from pyglet.window import key


class BattleState(ABC):
    @abstractmethod
    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        pass

    @abstractmethod
    def get_message(self, model: BattleModel) -> str:
        pass


class PartyCommandState(BattleState):
    """Initial FIGHT/RUN choice at party level."""
    def __init__(self):
        self.selection = 0
        self.options = ["Fight", "Run"]

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        if inpt.is_just_pressed(key.UP) or inpt.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.options)
        elif inpt.is_just_pressed(key.Z):
            if self.selection == 0:  # FIGHT
                living = model.get_living_party()
                if not living:
                    return "message:No party members!"
                return "char_command"
            else:  # RUN
                return "run_attempt"
        return None

    def get_message(self, model: BattleModel) -> str:
        return ""


class CharCommandState(BattleState):
    """Per-member FIGHT/MAGIC/ITEM choice."""
    def __init__(self, member_idx: int):
        self.member_idx = member_idx
        self.selection = 0
        self.options = ["Fight", "Magic", "Item"]

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        if not model.party[self.member_idx].alive:
            return "advance"

        if inpt.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.options)
        elif inpt.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.options)
        elif inpt.is_just_pressed(key.Z):
            if self.selection == 0:  # FIGHT
                living = model.get_living_enemies()
                if not living:
                    return "message:No enemies!"
                return "target_enemy_attack"
            elif self.selection == 1:  # MAGIC
                member = model.party[self.member_idx]
                if not member.spells:
                    return "message:No spells yet!"
                return "spell_select"
            else:  # ITEM
                return "item_select"
        elif inpt.is_just_pressed(key.X):
            # Cancel this member's action, go back to party command
            if self.member_idx in model.party_actions:
                del model.party_actions[self.member_idx]
            return "party_command"
        return None

    def get_message(self, model: BattleModel) -> str:
        return ""


class SpellSelectState(BattleState):
    def __init__(self, member_idx: int):
        self.member_idx = member_idx
        self.selection = 0

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        member = model.party[self.member_idx]
        spells = member.spells
        if not spells:
            return "char_command"

        if inpt.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(spells)
        elif inpt.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(spells)
        elif inpt.is_just_pressed(key.Z):
            spell_id = spells[self.selection]
            spell = model.spells.get(spell_id, {})
            mp_cost = spell.get("mp_cost", 0)
            if member.mp < mp_cost:
                return "message:Not enough MP!"
            return f"spell_target:{spell_id}"
        elif inpt.is_just_pressed(key.X):
            return "char_command"
        return None

    def get_message(self, model: BattleModel) -> str:
        return ""


class TargetState(BattleState):
    """Unified target selection for attack/magic/item."""
    def __init__(self, member_idx: int = 0, target_type: str = "enemy",
                 spell_id: str = "", item_id: str = ""):
        self.member_idx = member_idx
        self.target_type = target_type  # "enemy" or "ally"
        self.spell_id = spell_id
        self.item_id = item_id
        self.selection = 0

    def _get_targets(self, model: BattleModel) -> list[Actor]:
        if self.target_type == "enemy":
            return model.get_living_enemies()
        return model.get_living_party()

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        targets = self._get_targets(model)
        if not targets:
            return "char_command"

        if inpt.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(targets)
        elif inpt.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(targets)
        elif inpt.is_just_pressed(key.Z):
            target = targets[self.selection]
            if self.spell_id:
                target_idx = (model.party.index(target) if target in model.party
                              else model.enemies.index(target))
                model.queue_party_action(self.member_idx, "magic", target_idx, self.spell_id)
            elif self.item_id:
                target_idx = model.party.index(target)
                model.queue_party_action(self.member_idx, "item", target_idx, self.item_id)
            else:
                target_idx = model.enemies.index(target)
                model.queue_party_action(self.member_idx, "attack", target_idx)
            return "advance"
        elif inpt.is_just_pressed(key.X):
            if self.spell_id:
                return "spell_select"
            elif self.item_id:
                return "item_select"
            return "char_command"
        return None

    def get_message(self, model: BattleModel) -> str:
        return ""


class ItemSelectState(BattleState):
    """Browse inventory and pick an item."""
    def __init__(self, member_idx: int, inventory: list, item_data: dict):
        self.member_idx = member_idx
        self.selection = 0
        self.inventory = inventory
        self.item_data = item_data
        self.items = [inv for inv in inventory if inv["qty"] > 0]

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        if not self.items:
            return "message:No items!"
        if inpt.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.items)
        elif inpt.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.items)
        elif inpt.is_just_pressed(key.Z):
            item = self.items[self.selection]
            item_id = item["id"]
            item_def = self.item_data.get(item_id, {})
            effect = item_def.get("effect", "")
            if effect in ("heal", "revive", "cure_status", "mana", "full_restore", "restore_all"):
                return f"item_target:{item_id}"
            return "message:Can't use that here!"
        elif inpt.is_just_pressed(key.X):
            return "char_command"
        return None

    def get_message(self, model: BattleModel) -> str:
        return ""


class RunOutcomeState(BattleState):
    """Show run attempt result."""
    def __init__(self, success: bool):
        self.success = success
        self.selection = 0
        self.timer = 0.0
        self.duration = 2.0

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        self.timer += delta_time
        if self.timer >= self.duration or inpt.is_just_pressed(key.Z):
            if self.success:
                return "escape"
            return "escape_failed"
        return None

    def get_message(self, model: BattleModel) -> str:
        if self.success:
            return "Run away!!!"
        return "The enemy blocks the way!!"


class ExecuteState(BattleState):
    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        action = model.process_next_action()
        if not action:
            return "next_round"
        return "process_events"

    def get_message(self, model: BattleModel) -> str:
        return "BATTLE!"


class FlashState(BattleState):
    def __init__(self):
        self.flash_count = 4
        self.flash_timer = 0.15
        self.elapsed = 0.0

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        self.elapsed += delta_time
        if self.elapsed >= self.flash_timer:
            self.flash_count -= 1
            self.elapsed = 0
            if self.flash_count <= 0:
                return "process_events"
        return None

    def get_message(self, model: BattleModel) -> str:
        return ""


class MessageState(BattleState):
    def __init__(self):
        self.events: list[BattleEvent] = []
        self.current_idx = 0
        self.timer = 0.0
        self.duration = 1.5

    def set_events(self, events: list[BattleEvent]) -> None:
        self.events = events
        self.current_idx = 0

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        if not self.events:
            self.current_idx = 0
            victory, defeat = model.check_battle_end()
            if victory:
                return "victory"
            if defeat:
                return "defeat"
            return "next_action"

        self.timer += delta_time
        if self.timer >= self.duration or inpt.is_just_pressed(key.Z):
            # Apply pending death BEFORE advancing past death message
            if self.current_idx < len(self.events):
                evt = self.events[self.current_idx]
                if evt.apply_death is not None:
                    evt.apply_death.alive = False
                    evt.apply_death.dying_timer = 0.5
            self.current_idx += 1
            self.timer = 0
            if self.current_idx >= len(self.events):
                victory, defeat = model.check_battle_end()
                if victory:
                    return "victory"
                if defeat:
                    return "defeat"
                return "next_action"
        return None

    def get_message(self, model: BattleModel) -> str:
        if self.current_idx < len(self.events):
            return self.events[self.current_idx].message
        return ""


class VictoryState(BattleState):
    def __init__(self):
        self.timer = 0.0
        self.duration = 0.5  # brief pause before showing

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        self.timer += delta_time
        if self.timer >= self.duration and inpt.is_just_pressed(key.Z):
            return "victory_confirm"
        return None

    def get_message(self, model: BattleModel) -> str:
        lines = ["Victory!"]
        if model.rewards["gold"] > 0:
            lines.append(f"Received {model.rewards['gold']} GP")
        if model.rewards["xp"] > 0:
            lines.append(f"Received {model.rewards['xp']} EXP")
        for item_id in model.rewards.get("items", []):
            item_def = model.item_data.get(item_id, {})
            name = item_def.get("name", item_id)
            lines.append(f"Received {name}!")
        lines.append("Press Z")
        return "\n".join(lines)


class DefeatState(BattleState):
    def __init__(self):
        self.timer = 0.0
        self.duration = 0.5

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        self.timer += delta_time
        if self.timer >= self.duration and inpt.is_just_pressed(key.Z):
            return "defeat_confirm"
        return None

    def get_message(self, model: BattleModel) -> str:
        return "Defeat..."
