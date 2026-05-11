import random
import json
import os
from game.input import UP, DOWN, LEFT, RIGHT, Z, X
from game.engine import register_scene, SPELL_DATA
from game.battle.model import BattleModel
from game.battle.renderer import BattleRenderer
from game.battle.states import (
    CommandState, SpellSelectState, TargetState, 
    ExecuteState, FlashState, MessageState, VictoryState, DefeatState
)


DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "enemies.json")


def load_enemies():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


@register_scene("battle")
class BattleScene:
    def __init__(self, engine):
        self.engine = engine
        self.enemy_data = load_enemies()
        self.spells = SPELL_DATA

        party_data = []
        for p in engine.party:
            party_data.append({
                "name": p.get("name", ""),
                "hp": p.get("hp", p.get("hp_max", 50)),
                "hp_max": p.get("hp_max", 50),
                "mp": p.get("mp", 0),
                "mp_max": p.get("mp_max", 0),
                "atk": p.get("atk", 10),
                "def": p.get("def", 5),
                "spd": p.get("spd", 10),
                "alive": p.get("hp", p.get("hp_max", 50)) > 0,
                "lvl": p.get("lvl", p.get("level", 1)),
                "exp": p.get("exp", p.get("xp", 0)),
                "exp_next": p.get("exp_next", p.get("xp_next", 100)),
                "spells": p.get("spells", []),
            })

        self.model = BattleModel(party_data, self.enemy_data, self.spells, engine.current_map)
        self.renderer = BattleRenderer()
        
        self.state = "command"
        self.current_state_obj = CommandState(0)
        self.current_party_idx = 0
        self.message = ""
        self.message_events = []
        self._members_visited = set()  # Track which members we've prompted this round
        
        self._init_state()

    def _init_state(self):
        living = self.model.get_living_party()
        if living:
            self.current_party_idx = self.model.party.index(living[0])
        else:
            self.current_party_idx = 0
        self.state = "command"
        self.current_state_obj = CommandState(self.current_party_idx)
        self._members_remaining = len(living)  # How many members to prompt this round

    def update(self, delta_time):
        inpt = self.engine.input
        
        if self.state == "victory":
            if inpt.is_just_pressed(Z):
                self._apply_victory()
                self.engine.set_scene("overworld")
            return

        if self.state == "defeat":
            if inpt.is_just_pressed(Z):
                for p in self.engine.party:
                    p["hp"] = p["hp_max"]
                    p["alive"] = True
                self.engine.set_scene("title")
            return

        if self.state == "message":
            result = self.current_state_obj.update(self.model, inpt, delta_time)
            if result:
                self._handle_result(result)
            return

        if self.state in ("command", "spell_select", "target", "execute", "flash"):
            result = self.current_state_obj.update(self.model, inpt, delta_time)
            if result:
                self._handle_result(result)

    def _handle_result(self, result: str):
        if result == "reprocess":
            self._init_state()
            return

        if result == "next_round":
            self.current_party_idx = 0
            living = self.model.get_living_party()
            if living:
                self.current_party_idx = self.model.party.index(living[0])
            self.state = "command"
            self.current_state_obj = CommandState(self.current_party_idx)
            return

        if result == "next_action":
            self.state = "execute"
            self.current_state_obj = ExecuteState()
            return

        if result == "escape":
            self.state = "message"
            self.message = "Got away safely!"
            self.current_state_obj = MessageState()
            self.message_events = []
            return

        if result.startswith("message:"):
            msg = result.split(":", 1)[1]
            self.state = "message"
            self.message = msg
            self.current_state_obj = MessageState()
            self.message_events = []
            return

        if result == "victory":
            self.state = "victory"
            self.current_state_obj = VictoryState()
            return

        if result == "defeat":
            self.state = "defeat"
            self.current_state_obj = DefeatState()
            return

        if result == "victory_confirm":
            self._apply_victory()
            self.engine.set_scene("overworld")
            return

        if result == "defeat_confirm":
            for p in self.engine.party:
                p["hp"] = p["hp_max"]
                p["alive"] = True
            self.engine.set_scene("title")
            return

        if result == "spell_select":
            self.state = "spell_select"
            self.current_state_obj = SpellSelectState(self.current_party_idx)
            return

        if result.startswith("spell_target:"):
            spell_id = result.split(":", 1)[1]
            self.state = "target"
            self.current_state_obj = TargetState(for_magic=True, spell_id=spell_id, member_idx=self.current_party_idx)
            return

        if result == "target_enemy":
            self.state = "target"
            self.current_state_obj = TargetState(for_magic=False, member_idx=self.current_party_idx)
            return

        if result == "advance":
            self._members_remaining -= 1
            
            if self._members_remaining > 0:
                # Find next living member
                living = self.model.get_living_party()
                next_idx = None
                start_idx = self.current_party_idx
                for _ in range(len(living)):
                    start_idx = (start_idx + 1) % len(living)
                    m = living[start_idx]
                    idx = self.model.party.index(m)
                    if idx != self.current_party_idx:  # Don't go back to current
                        next_idx = idx
                        break
                
                if next_idx is not None:
                    self.current_party_idx = next_idx
                    self.state = "command"
                    self.current_state_obj = CommandState(self.current_party_idx)
            else:
                # All members have acted - execute battle
                self.model.prepare_battle()
                self.state = "execute"
                
                self.current_state_obj = ExecuteState()
            return

        if result == "flash":
            
            self.current_state_obj = FlashState()
            return

        if result == "process_events":
            action = self.model.current_action
            events = self.model.execute_action(action)
            
            # Build combined event list with death messages
            all_events = list(events)
            for e in events:
                if e.is_death and e.death_message:
                    from game.battle.dataclasses import BattleEvent
                    all_events.append(BattleEvent(
                        message=e.death_message,
                        actor=e.target,
                        is_death=False
                    ))
            
            if events:
                self.message = events[0].message
            
            victory, defeat = self.model.check_battle_end()
            if victory or defeat:
                self.state = "message"
                self.current_state_obj = MessageState()
                self.current_state_obj.events = all_events
                self.current_state_obj.current_idx = 0
                return
            
            if events:
                self.state = "message"
                self.current_state_obj = MessageState()
                self.current_state_obj.events = all_events
                self.current_state_obj.current_idx = 0
                self.message = self.current_state_obj.get_message(self.model)
            else:
                self.state = "execute"
                
                self.current_state_obj = ExecuteState()
            return

    def _apply_victory(self):
        xp = self.model.rewards["xp"]
        gold = self.model.rewards["gold"]
        
        for p in self.model.party:
            if p.alive:
                p.exp += xp
                while p.exp >= p.exp_next:
                    p.exp -= p.exp_next
                    p.lvl += 1
                    p.exp_next = int(p.exp_next * 1.5)
                    p.hp_max += 5
                    p.hp = p.hp_max
                    p.atk += 2
                    p.def_ += 1
        
        party_dicts = []
        for p in self.model.party:
            party_dicts.append({
                "name": p.name,
                "hp": p.hp,
                "hp_max": p.hp_max,
                "mp": p.mp,
                "mp_max": p.mp_max,
                "atk": p.atk,
                "def": p.def_,
                "spd": p.spd,
                "alive": p.alive,
                "lvl": p.lvl,
                "exp": p.exp,
                "exp_next": p.exp_next,
                "spells": p.spells,
            })
        
        self.engine.party = party_dicts
        self.engine.gold = self.engine.gold + gold

    def draw(self):
        w, h = self.engine.get_size()
        scale = self.engine.get_scale()

        flash_state = None
        if isinstance(self.current_state_obj, FlashState):
            flash_state = self.current_state_obj

        options = ["FIGHT", "MAGIC", "ITEM", "RUN"]
        selection = 0
        target_idx = 0
        is_magic = False
        spell_id = ""
        message = ""

        if isinstance(self.current_state_obj, CommandState):
            selection = self.current_state_obj.selection
        elif isinstance(self.current_state_obj, SpellSelectState):
            selection = self.current_state_obj.selection
        elif isinstance(self.current_state_obj, TargetState):
            target_idx = self.current_state_obj.selection
            is_magic = self.current_state_obj.for_magic
            spell_id = self.current_state_obj.spell_id
        elif isinstance(self.current_state_obj, MessageState):
            message = self.current_state_obj.get_message(self.model)
        else:
            message = ""
        
        if self.state == "message":
            message = self.current_state_obj.get_message(self.model)
        elif self.state == "command":
            selection = self.current_state_obj.selection
        elif self.state == "spell_select":
            selection = self.current_state_obj.selection
        elif self.state == "target":
            target_idx = self.current_state_obj.selection
            is_magic = self.current_state_obj.for_magic
            spell_id = self.current_state_obj.spell_id
        elif self.state == "victory":
            message = self.current_state_obj.get_message(self.model)
        elif self.state == "defeat":
            message = self.current_state_obj.get_message(self.model)
        else:
            message = ""

        self.renderer.draw(
            model=self.model,
            state=self.state,
            scale=scale,
            width=w,
            height=h,
            message=message,
            flash_state=flash_state,
            options=options,
            selection=selection,
            current_member_idx=self.current_party_idx,
            target_idx=target_idx,
            is_magic=is_magic,
            spell_id=spell_id,
        )