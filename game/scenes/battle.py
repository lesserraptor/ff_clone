import random
import json
import os
from pyglet.window import key
from game.engine import register_scene, ITEM_DATA
from game.battle.model import BattleModel
from game.battle.renderer import BattleRenderer
from game.battle.states import (
    PartyCommandState, CharCommandState, SpellSelectState, TargetState,
    ItemSelectState, RunOutcomeState,
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

        self.model = BattleModel(party_data, self.enemy_data, self.spells, engine.current_map, item_data=ITEM_DATA)
        self.renderer = BattleRenderer()
        
        self.state = "party_command"
        self.current_state_obj = PartyCommandState()
        self.current_party_idx = 0
        self.message = ""
        self.message_events = []
        self.message_log: list[str] = []
        self._members_remaining = 0
        
        self._init_state()

    def _init_state(self):
        self.state = "party_command"
        self.current_state_obj = PartyCommandState()
        self.current_party_idx = 0
        self._members_remaining = 0

    def update(self, delta_time):
        inpt = self.engine.input

        # Update death animations
        for enemy in self.model.enemies:
            if enemy.dying_timer > 0:
                enemy.dying_timer -= delta_time

        if self.state == "victory":
            result = self.current_state_obj.update(self.model, inpt, delta_time)
            if result:
                self._handle_result(result)
            return

        if self.state == "defeat":
            result = self.current_state_obj.update(self.model, inpt, delta_time)
            if result:
                self._handle_result(result)
            return

        if self.state == "message":
            result = self.current_state_obj.update(self.model, inpt, delta_time)
            if result:
                self._handle_result(result)
            return

        interactive_states = {
            "party_command", "char_command", "spell_select",
            "target_enemy_attack", "target_enemy_spell", "target_party",
            "item_select", "run_outcome", "execute", "flash",
        }
        if self.state in interactive_states:
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
        "advance": "_handle_advance",
        "flash": "_handle_flash",
        "process_events": "_handle_process_events",
        "command": "_handle_command",
        # New state-flow results
        "party_command": "_handle_party_command",
        "char_command": "_handle_char_command",
        "run_attempt": "_handle_run_attempt",
        "escape_failed": "_handle_escape_failed",
        "target_enemy_attack": "_handle_target_enemy_attack",
        "item_select": "_handle_item_select",
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
        if result.startswith("item_target:"):
            self._handle_item_target(result.split(":", 1)[1])
            return

    def _handle_reprocess(self):
        self._init_state()

    def _handle_party_command(self):
        self.state = "party_command"
        self.current_state_obj = PartyCommandState()

    def _handle_char_command(self):
        """Start per-member menu loop."""
        living = self.model.get_living_party()
        if not living:
            self._handle_defeat()
            return
        self.current_party_idx = self.model.party.index(living[0])
        self.state = "char_command"
        self.current_state_obj = CharCommandState(self.current_party_idx)

    def _handle_next_round(self):
        self.model.used_items.clear()
        self.message_log.clear()
        self.state = "party_command"
        self.current_state_obj = PartyCommandState()

    def _handle_next_action(self):
        self.state = "execute"
        self.current_state_obj = ExecuteState()

    def _handle_escape(self):
        self.engine.set_scene("overworld")

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
        spell = self.model.spells.get(spell_id, {})
        target_type = spell.get("target", "enemy")
        if target_type == "enemy":
            self.state = "target_enemy_spell"
        else:
            self.state = "target_party"
        self.current_state_obj = TargetState(
            member_idx=self.current_party_idx,
            target_type=target_type,
            spell_id=spell_id,
        )

    def _handle_command(self):
        self.state = "party_command"
        self.current_state_obj = PartyCommandState()

    def _handle_target_enemy_attack(self):
        self.state = "target_enemy_attack"
        self.current_state_obj = TargetState(
            member_idx=self.current_party_idx,
            target_type="enemy",
        )

    def _handle_item_select(self):
        inventory = self.engine.inventory
        self.state = "item_select"
        self.current_state_obj = ItemSelectState(
            member_idx=self.current_party_idx,
            inventory=inventory,
            item_data=ITEM_DATA,
        )

    def _handle_item_target(self, item_id):
        self.state = "target_party"
        self.current_state_obj = TargetState(
            member_idx=self.current_party_idx,
            target_type="ally",
            item_id=item_id,
        )

    def _handle_run_attempt(self):
        if random.random() < 0.5:
            self.state = "run_outcome"
            self.current_state_obj = RunOutcomeState(success=True)
        else:
            self.state = "run_outcome"
            self.current_state_obj = RunOutcomeState(success=False)

    def _handle_escape_failed(self):
        """Enemies get a free turn."""
        self.model.prepare_enemy_turn()
        self.state = "execute"
        self.current_state_obj = ExecuteState()

    def _handle_advance(self):
        living = self.model.get_living_party()
        # Find members who haven't acted yet
        remaining = [p for p in living
                     if not self.model.has_party_action(self.model.party.index(p))]

        if remaining:
            next_idx = self.model.party.index(remaining[0])
            self.current_party_idx = next_idx
            self.state = "char_command"
            self.current_state_obj = CharCommandState(self.current_party_idx)
        else:
            # All members have acted — execute battle
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
                    is_death=False,
                    apply_death=e.target,
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
        message = ""
        if self.state in ("message", "victory", "defeat", "run_outcome"):
            message = self.current_state_obj.get_message(self.model)
            # Track messages for scrolling log
            if message and (not self.message_log or self.message_log[-1] != message):
                self.message_log.append(message)
                if len(self.message_log) > 20:  # cap at 20
                    self.message_log = self.message_log[-20:]
        return message

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

        message = self._build_render_params()

        self.renderer.draw(
            model=self.model,
            state=self.state,
            scale=scale,
            width=w,
            height=h,
            state_obj=self.current_state_obj,
            flash_state=flash_state,
            message_log=self.message_log,
        )