import random
import json
import os
from pyglet.window import key
from game.engine import register_scene
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
        import game.engine; self.spells = game.engine.SPELL_DATA

        party_data = []
        for p in engine.party:
            party_data.append({
                "name": p.name,
                "hp": p.hp,
                "hp_max": p.hp_max,
                "mp": p.mp,
                "mp_max": p.mp_max,
                "atk": p.atk,
                "def": p.def_,
                "spd": p.spd,
                "alive": p.hp > 0,
                "lvl": p.lvl,
                "exp": p.exp,
                "exp_next": p.exp_next,
                "spells": p.spells,
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
            if inpt.is_just_pressed(key.Z):
                self._apply_victory()
                self.engine.set_scene("overworld")
            return

        if self.state == "defeat":
            if inpt.is_just_pressed(key.Z):
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

    RESULT_DISPATCH = {
        "reprocess": "_handle_reprocess",
        "next_round": "_handle_next_round",
        "next_action": "_handle_next_action",
        "escape": "_handle_escape",
        "victory": "_handle_victory",
        "defeat": "_handle_defeat",
        "victory_confirm": "_handle_victory_confirm",
        "defeat_confirm": "_handle_defeat_confirm",
        "spell_select": "_handle_spell_select",
        "target_enemy": "_handle_target_enemy",
        "advance": "_handle_advance",
        "flash": "_handle_flash",
        "process_events": "_handle_process_events",
    }

    def _handle_result(self, result: str):
        handler_name = self.RESULT_DISPATCH.get(result)
        if handler_name is not None:
            getattr(self, handler_name)()
            return
        if result.startswith("message:"):
            self._handle_message(result.split(":", 1)[1])
            return
        if result.startswith("spell_target:"):
            self._handle_spell_target(result.split(":", 1)[1])
            return

    def _handle_reprocess(self):
        self._init_state()

    def _handle_next_round(self):
        self.current_party_idx = 0
        living = self.model.get_living_party()
        if living:
            self.current_party_idx = self.model.party.index(living[0])
        self.state = "command"
        self.current_state_obj = CommandState(self.current_party_idx)

    def _handle_next_action(self):
        self.state = "execute"
        self.current_state_obj = ExecuteState()

    def _handle_escape(self):
        self.state = "message"
        self.message = "Got away safely!"
        self.current_state_obj = MessageState()
        self.message_events = []

    def _handle_message(self, msg):
        self.state = "message"
        self.message = msg
        self.current_state_obj = MessageState()
        self.message_events = []

    def _handle_victory(self):
        self.state = "victory"
        self.current_state_obj = VictoryState()

    def _handle_defeat(self):
        self.state = "defeat"
        self.current_state_obj = DefeatState()

    def _handle_victory_confirm(self):
        self._apply_victory()
        self.engine.set_scene("overworld")

    def _handle_defeat_confirm(self):
        for p in self.engine.party:
            p["hp"] = p["hp_max"]
            p["alive"] = True
        self.engine.set_scene("title")

    def _handle_spell_select(self):
        self.state = "spell_select"
        self.current_state_obj = SpellSelectState(self.current_party_idx)

    def _handle_spell_target(self, spell_id):
        self.state = "target"
        self.current_state_obj = TargetState(for_magic=True, spell_id=spell_id, member_idx=self.current_party_idx)

    def _handle_target_enemy(self):
        self.state = "target"
        self.current_state_obj = TargetState(for_magic=False, member_idx=self.current_party_idx)

    def _handle_advance(self):
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

    def _handle_flash(self):
        self.current_state_obj = FlashState()

    def _handle_process_events(self):
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

    def _build_render_params(self):
        options = ["FIGHT", "MAGIC", "ITEM", "RUN"]
        selection = 0
        target_idx = 0
        is_magic = False
        spell_id = ""
        message = ""

        if self.state == "command":
            selection = self.current_state_obj.selection
        elif self.state == "spell_select":
            selection = self.current_state_obj.selection
        elif self.state == "target":
            target_idx = self.current_state_obj.selection
            is_magic = self.current_state_obj.for_magic
            spell_id = self.current_state_obj.spell_id
        elif self.state == "message":
            message = self.current_state_obj.get_message(self.model)
        elif self.state in ("victory", "defeat"):
            message = self.current_state_obj.get_message(self.model)

        return options, selection, target_idx, is_magic, spell_id, message

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
        
        from game.dataclasses import PartyMember
        from game.battle.dataclasses import actor_to_dict
        self.engine.party = [PartyMember.from_dict(actor_to_dict(p)) for p in self.model.party]
        self.engine.gold = self.engine.gold + gold

    def draw(self):
        w, h = self.engine.get_size()
        scale = self.engine.get_scale()

        flash_state = None
        if isinstance(self.current_state_obj, FlashState):
            flash_state = self.current_state_obj

        options, selection, target_idx, is_magic, spell_id, message = self._build_render_params()

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