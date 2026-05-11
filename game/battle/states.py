from abc import ABC, abstractmethod
from typing import Optional
import random
from game.battle.dataclasses import Actor, BattleEvent
from game.battle.model import BattleModel


class BattleState(ABC):
    @abstractmethod
    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        pass

    @abstractmethod
    def get_message(self, model: BattleModel) -> str:
        pass


class CommandState(BattleState):
    def __init__(self, member_idx: int = 0):
        self.member_idx = member_idx
        self.selection = 0
        self.options = ["FIGHT", "MAGIC", "ITEM", "RUN"]

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        from game.input import UP, DOWN, Z, X

        if inpt.is_just_pressed(DOWN):
            self.selection = (self.selection + 1) % len(self.options)
        elif inpt.is_just_pressed(Z):
            return self._handle_selection(model, self.selection)
        elif inpt.is_just_pressed(X):
            if self.member_idx in model.party_actions:
                del model.party_actions[self.member_idx]
            return "reprocess"
        return None

    def _handle_selection(self, model: BattleModel, idx: int) -> Optional[str]:
        if idx == 0:
            living = model.get_living_enemies()
            if living:
                return "target_enemy"
            return "message:No enemies!"
        elif idx == 1:
            member = model.party[self.member_idx]
            if not member.spells:
                return "message:No spells yet!"
            return "spell_select"
        elif idx == 2:
            return "message:No items yet!"
        elif idx == 3:
            if random.random() < 0.5:
                return "escape"
            return "message:Can't escape!"
        return None

    def get_message(self, model: BattleModel) -> str:
        return ""


class SpellSelectState(BattleState):
    def __init__(self, member_idx: int):
        self.member_idx = member_idx
        self.selection = 0

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        from game.input import UP, DOWN, Z, X

        member = model.party[self.member_idx]
        spells = member.spells
        if not spells:
            return "command"

        if inpt.is_just_pressed(DOWN):
            self.selection = (self.selection + 1) % len(spells)
        elif inpt.is_just_pressed(UP):
            self.selection = (self.selection - 1) % len(spells)
        elif inpt.is_just_pressed(Z):
            spell_id = spells[self.selection]
            spell = model.spells.get(spell_id, {})
            mp_cost = spell.get("mp_cost", 0)
            if member.mp < mp_cost:
                return "message:Not enough MP!"
            return f"spell_target:{spell_id}"
        elif inpt.is_just_pressed(X):
            return "command"
        return None

    def get_message(self, model: BattleModel) -> str:
        return ""


class TargetState(BattleState):
    def __init__(self, for_magic: bool = False, spell_id: str = "", member_idx: int = 0):
        self.for_magic = for_magic
        self.spell_id = spell_id
        self.member_idx = member_idx
        self.selection = 0

    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        from game.input import UP, DOWN, Z, X

        if self.for_magic:
            spell = model.spells.get(self.spell_id, {})
            target_type = spell.get("target", "enemy")
            if target_type == "enemy":
                targets = model.get_living_enemies()
            else:
                targets = model.get_living_party()
        else:
            targets = model.get_living_enemies()

        if not targets:
            return "command"

        if inpt.is_just_pressed(DOWN):
            self.selection = (self.selection + 1) % len(targets)
        elif inpt.is_just_pressed(UP):
            self.selection = (self.selection - 1) % len(targets)
        elif inpt.is_just_pressed(Z):
            target = targets[self.selection]
            if self.for_magic:
                target_idx = (model.party.index(target) if target in model.party 
                             else model.enemies.index(target))
                model.queue_party_action(self.member_idx, "magic", target_idx, self.spell_id)
            else:
                target_idx = model.enemies.index(target)
                model.queue_party_action(self.member_idx, "attack", target_idx)
            return "advance"
        elif inpt.is_just_pressed(X):
            if self.for_magic:
                return "spell_select"
            return "command"
        return None

    def get_message(self, model: BattleModel) -> str:
        return ""


class ExecuteState(BattleState):
    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        action = model.process_next_action()
        if not action:
            return "next_round"
        return "flash"

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
        from game.input import Z

        self.timer += delta_time
        if self.timer >= self.duration or inpt.is_just_pressed(Z):
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
    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        from game.input import Z
        if inpt.is_just_pressed(Z):
            return "victory_confirm"
        return None

    def get_message(self, model: BattleModel) -> str:
        return f"VICTORY! +{model.rewards['xp']} XP  +{model.rewards['gold']} G"


class DefeatState(BattleState):
    def update(self, model: BattleModel, input_state, delta_time: float) -> Optional[str]:
        inpt = input_state
        from game.input import Z
        if inpt.is_just_pressed(Z):
            return "defeat_confirm"
        return None

    def get_message(self, model: BattleModel) -> str:
        return "DEFEAT"