import arcade
from game.battle.model import BattleModel
from game.battle.dataclasses import BattleEvent, ActionType
from game.text import create_text
from game.ui import COLORS, draw_window, draw_hp_bar, draw_mp_bar, draw_cursor


class BattleRenderer:
    def __init__(self):
        self._prev_scale = 0
        self._option_texts = {}
        self._message_text = None
        self._hp_texts = {}
        self._enemy_hp_texts = {}
        self._spell_texts = {}
        self._mp_text = None
        self._instruction_text = None
        self._centered_text = None
        self._current_state = ""

    def _get_text(self, cache: dict, key: str, text: str, x: float, y: float, color, size: int, anchor_x="left", anchor_y="center"):
        scale = self._prev_scale
        if scale != self._prev_scale or key not in cache:
            cache[key] = create_text(text, x, y, color, size, anchor_x=anchor_x, anchor_y=anchor_y)
        else:
            cache[key].text = text
            cache[key].color = color
        return cache[key]

    def _get_text_simple(self, cache: dict, key: str, text: str, x: float, y: float, color, size: int, anchor_y="center"):
        if self._prev_scale not in cache:
            cache[self._prev_scale] = {}
        scale_cache = cache[self._prev_scale]
        if key not in scale_cache:
            scale_cache[key] = create_text(text, x, y, color, size, anchor_y=anchor_y)
        else:
            scale_cache[key].text = text
            scale_cache[key].color = color
            scale_cache[key].x = x
            scale_cache[key].y = y
        return scale_cache[key]

    def draw(self, model: BattleModel, state: str, scale: float, width: int, height: int, 
             message: str = "", flash_state = None, options = None, selection = 0,
             current_member_idx = 0, target_idx = 0, is_magic = False, spell_id = ""):
        
        self._current_state = state
        
        arcade.draw_lrbt_rectangle_filled(0, width, 0, height, (0, 0, 0))
        
        self.draw_enemy_area(model, width, height, scale)
        self.draw_party_area(model, width, height, scale)
        
        if state == "command":
            self.draw_command_bar(width, height, scale, options or [], selection)
            self.draw_party_indicator(model, width, height, scale, current_member_idx)
        elif state == "spell_select":
            self.draw_command_bar(width, height, scale, options or [], selection)
            self.draw_party_indicator(model, width, height, scale, current_member_idx)
            self.draw_spell_list(model, width, height, scale, current_member_idx, selection)
        elif state == "target":
            self.draw_target_selection(model, width, height, scale, target_idx, is_magic, spell_id)
        elif state == "execute":
            self.draw_centered_text(width, height, scale, "BATTLE!", arcade.color.YELLOW, 12)
        elif state == "flash":
            self.draw_action_highlight(model, width, height, scale, flash_state)
        
        if message:
            self.draw_message_box(width, height, scale, message)
        elif state == "victory":
            self.draw_centered_box(width, height, scale, f"VICTORY! +{model.rewards['xp']} XP  +{model.rewards['gold']} G", arcade.color.YELLOW)
            self.draw_instruction(width, height, scale, "Press Z")
        elif state == "defeat":
            self.draw_centered_box(width, height, scale, "DEFEAT", arcade.color.RED)
            self.draw_instruction(width, height, scale, "Press Z")
        
        self._prev_scale = scale

    def draw_enemy_area(self, model: BattleModel, w: int, h: int, scale: float):
        area_top = h * 3 // 4
        draw_window(0, h // 4, w, area_top - h // 4, scale, (60, 0, 0))
        
        enemies = model.enemies
        enemy_count = len(enemies)
        spacing = w / (enemy_count + 1)
        
        for i, enemy in enumerate(enemies):
            cx = spacing * (i + 1)
            cy = h * 3 // 4 - 20 * scale
            color = arcade.color.RED if enemy.alive else (80, 80, 80)
            size = 16 * scale
            arcade.draw_lrbt_rectangle_filled(cx - size // 2, cx + size // 2, cy - size // 2, cy + size // 2, color)
            
            font_size = int(6 * scale)
            hp_str = f"{enemy.name} {enemy.hp}/{enemy.hp_max}"
            text = self._get_text_simple(self._enemy_hp_texts, i, hp_str, cx, cy - size, color, font_size, anchor_y="center")
            text.draw()

    def draw_party_area(self, model: BattleModel, w: int, h: int, scale: float):
        area_bottom = h // 4
        draw_window(0, 0, w, area_bottom, scale, (0, 0, 60))
        
        box_w = w // 4 - 4 * scale
        box_h = area_bottom - 8 * scale
        
        for i, member in enumerate(model.party):
            col = i % 4
            x = 8 * scale + col * (box_w + 4 * scale)
            y = 4 * scale
            color = arcade.color.GREEN if member.alive else (120, 120, 120)
            arcade.draw_lrbt_rectangle_outline(x, x + box_w, y, y + box_h, color[:3], int(scale))
            
            font_size = int(5 * scale)
            alive_color = arcade.color.WHITE if member.alive else (120, 120, 120)
            mp_color = arcade.color.CYAN if member.alive else (80, 80, 80)
            self._get_text_simple(self._hp_texts, f"{i}_name", member.name, x + 4 * scale, y + box_h - 8 * scale, alive_color, font_size)
            self._hp_texts[self._prev_scale][f"{i}_name"].draw()
            
            bar_y = y + 4 * scale
            bar_width = box_w - 16 * scale
            draw_hp_bar(member.hp, member.hp_max, x + 4 * scale, bar_y, scale, width=bar_width, height=3 * scale)
            self._get_text_simple(self._hp_texts, f"{i}_hp", f"{member.hp}/{member.hp_max}", x + box_w - 8 * scale, bar_y + 2 * scale, alive_color, font_size - 1)
            self._hp_texts[self._prev_scale][f"{i}_hp"].draw()
            
            if member.mp_max > 0:
                mp_bar_y = bar_y + 6 * scale
                draw_mp_bar(member.mp, member.mp_max, x + 4 * scale, mp_bar_y, scale, width=bar_width, height=3 * scale)
                self._get_text_simple(self._hp_texts, f"{i}_mp", f"{member.mp}/{member.mp_max}", x + box_w - 8 * scale, mp_bar_y + 2 * scale, mp_color, font_size - 1)
                self._hp_texts[self._prev_scale][f"{i}_mp"].draw()

    def draw_command_bar(self, w: int, h: int, scale: float, options: list, selection: int):
        cmd_h = h // 4
        draw_window(0, 0, w, cmd_h, scale, (30, 30, 30))
        
        for i, option in enumerate(options):
            x = 24 * scale + i * 48 * scale
            y = 8 * scale
            color = COLORS["cursor"] if i == selection else COLORS["text"]
            text = self._get_text_simple(self._option_texts, i, option, x, y, color, int(8 * scale), anchor_y="center")
            text.draw()

    def draw_party_indicator(self, model: BattleModel, w: int, h: int, scale: float, member_idx: int):
        if member_idx >= len(model.party):
            return
        col = member_idx % 4
        box_w = w // 4 - 4 * scale
        x = 8 * scale + col * (box_w + 4 * scale)
        y = 4 * scale
        box_h = h // 4 - 8 * scale
        arcade.draw_lrbt_rectangle_outline(x, x + box_w, y, y + box_h, COLORS["cursor"], int(scale * 2))

    def draw_spell_list(self, model: BattleModel, w: int, h: int, scale: float, member_idx: int, selection: int):
        if member_idx >= len(model.party):
            return
        member = model.party[member_idx]
        spells = member.spells
        
        spell_h = h // 4
        draw_window(0, spell_h, w, 40 * scale, scale, (20, 20, 40))
        box_x = 16 * scale
        box_w = w - 32 * scale
        box_y = spell_h + 4 * scale
        box_h = 32 * scale
        draw_window(box_x, box_y, box_w, box_h, scale, (20, 20, 40), (100, 200, 255))
        
        font_size = int(6 * scale)
        if self._mp_text is None or self._prev_scale != scale:
            self._mp_text = create_text(f"{member.name}  MP {member.mp}/{member.mp_max}", 24 * scale, box_y + box_h - 8 * scale, (100, 200, 255), font_size)
        else:
            self._mp_text.text = f"{member.name}  MP {member.mp}/{member.mp_max}"
        self._mp_text.draw()
        
        for i, spell_id in enumerate(spells):
            spell = model.spells.get(spell_id, {})
            name = spell.get("name", spell_id)
            mp_cost = spell.get("mp_cost", 0)
            y = box_y + box_h - 24 * scale - i * 12 * scale
            can_cast = member.mp >= mp_cost
            color = COLORS["cursor"] if i == selection else (COLORS["text"] if can_cast else (100, 100, 100))
            if i == selection:
                draw_cursor(24 * scale, y, scale)
            text = self._get_text_simple(self._spell_texts, i, f"{name}  MP-{mp_cost}", 32 * scale, y, color, font_size)
            text.draw()

    def draw_target_selection(self, model: BattleModel, w: int, h: int, scale: float, target_idx: int, is_magic: bool, spell_id: str):
        if is_magic and spell_id:
            spell = model.spells.get(spell_id, {})
            target_type = spell.get("target", "enemy") if spell else "enemy"
            if target_type == "enemy":
                self._draw_target_enemies(model, w, h, scale, target_idx)
            else:
                self._draw_target_party(model, w, h, scale, target_idx)
        else:
            self._draw_target_enemies(model, w, h, scale, target_idx)

    def _draw_target_enemies(self, model: BattleModel, w: int, h: int, scale: float, selection: int):
        alive = model.get_living_enemies()
        if not alive:
            return
        target = alive[selection]
        idx = model.enemies.index(target)
        enemy_count = len(model.enemies)
        spacing = w / (enemy_count + 1)
        cx = spacing * (idx + 1)
        cy = h * 3 // 4 - 20 * scale
        size = 20 * scale
        arcade.draw_lrbt_rectangle_outline(cx - size // 2, cx + size // 2, cy - size // 2, cy + size // 2, COLORS["cursor"], int(scale * 2))

    def _draw_target_party(self, model: BattleModel, w: int, h: int, scale: float, selection: int):
        alive = model.get_living_party()
        if not alive:
            return
        target = alive[selection]
        idx = model.party.index(target)
        box_w = w // 4 - 4 * scale
        x = 8 * scale + idx * (box_w + 4 * scale)
        y = 4 * scale
        box_h = h // 4 - 8 * scale
        arcade.draw_lrbt_rectangle_outline(x, x + box_w, y, y + box_h, COLORS["cursor"], int(scale * 2))

    def draw_action_highlight(self, model: BattleModel, w: int, h: int, scale: float, flash_state):
        if not flash_state or not flash_state.elapsed:
            return
        action = model.current_action
        if not action:
            return
        if action.action_type == ActionType.PARTY_ATTACK:
            for i, member in enumerate(model.party):
                if member.name == action.actor.name:
                    col = i % 4
                    box_w = w // 4 - 4 * scale
                    x = 8 * scale + col * (box_w + 4 * scale)
                    y = 4 * scale
                    box_h = h // 4 - 8 * scale
                    if flash_state.flash_count % 2 == 0:
                        arcade.draw_lrbt_rectangle_outline(x, x + box_w, y, y + box_h, COLORS["cursor"], int(scale * 2))
                    break
        elif action.action_type == ActionType.ENEMY_ATTACK:
            for i, enemy in enumerate(model.enemies):
                if enemy.name == action.actor.name:
                    enemy_count = len(model.enemies)
                    spacing = w / (enemy_count + 1)
                    cx = spacing * (i + 1)
                    cy = h * 3 // 4 - 20 * scale
                    size = 16 * scale
                    if flash_state.flash_count % 2 == 0:
                        arcade.draw_lrbt_rectangle_outline(cx - size // 2, cx + size // 2, cy - size // 2, cy + size // 2, COLORS["enemy"], int(scale * 2))
                    break

    def draw_centered_text(self, w: int, h: int, scale: float, text: str, color, size: int):
        if self._centered_text is None or self._prev_scale != scale:
            self._centered_text = create_text(text, w // 2, h // 2, color, int(size * scale), anchor_x="center", anchor_y="center")
        else:
            self._centered_text.text = text
            self._centered_text.color = color
        self._centered_text.draw()

    def draw_message_box(self, w: int, h: int, scale: float, message: str):
        box_h = 24 * scale
        box_y = h // 2 - box_h // 2
        draw_window(16 * scale, box_y, w - 32 * scale, box_h, scale)
        
        if self._message_text is None or self._prev_scale != scale:
            self._message_text = create_text(message, w // 2, box_y + box_h // 2, COLORS["text"], int(8 * scale), anchor_x="center", anchor_y="center")
        else:
            self._message_text.text = message
        self._message_text.draw()

    def draw_centered_box(self, w: int, h: int, scale: float, text: str, color):
        box_w = w - 32 * scale
        box_h = 40 * scale
        bx = 16 * scale
        by = h // 2 - box_h // 2
        draw_window(bx, by, box_w, box_h, scale, (0, 0, 0), color)
        if self._centered_text is None or self._prev_scale != scale:
            self._centered_text = create_text(text, w // 2, h // 2, color, int(8 * scale), anchor_x="center", anchor_y="center")
        else:
            self._centered_text.text = text
            self._centered_text.color = color
        self._centered_text.draw()

    def draw_instruction(self, w: int, h: int, scale: float, text: str):
        if self._instruction_text is None or self._prev_scale != scale:
            self._instruction_text = create_text(text, w // 2, h // 2 - 16 * scale, COLORS["text"], int(6 * scale), anchor_x="center")
        else:
            self._instruction_text.text = text
            self._instruction_text.y = h // 2 - 16 * scale
        self._instruction_text.draw()