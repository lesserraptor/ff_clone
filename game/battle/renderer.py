import arcade
from game.battle.model import BattleModel
from game.battle.dataclasses import BattleEvent, ActionType
from game.text import create_text, wrap_text
from game.ui import COLORS, draw_window, draw_hp_bar, draw_cursor, draw_bordered_box
from game.sprites import get_sprite_atlas


# Base gameboy resolution
BW, BH = 240, 160
MENU_H = int(BH * 0.55)  # 88
CHAR_BOX_W = int(BW * 2 / 5)  # 96
ENEMY_BOX_X = CHAR_BOX_W  # 96
ENEMY_BOX_W = BW - CHAR_BOX_W  # 144
BORDER_PX = 6
ROW_H = MENU_H // 4  # 22


class BattleRenderer:
    def __init__(self):
        self._prev_scale = 0
        self._texts = {}
        self._sprite_atlas = get_sprite_atlas()

    def _text(self, key, text, x, y, color, size, anchor_x="left", anchor_y="center", multiline=False, width=None):
        s = self._prev_scale
        if s not in self._texts:
            self._texts[s] = {}
        cache = self._texts[s]
        if key not in cache:
            cache[key] = create_text(text, x, y, color, size, anchor_x=anchor_x, anchor_y=anchor_y, width=width, multiline=multiline)
        else:
            t = cache[key]
            t.text = text
            t.x = x
            t.y = y
            t.color = color
            t.multiline = multiline
            t.width = width
        cache[key].draw()
        return cache[key]

    # ------------------------------------------------------------------ #
    #  Main dispatch                                                      #
    # ------------------------------------------------------------------ #
    def draw(self, model: BattleModel, state: str, scale: float, width: int, height: int,
             state_obj=None, flash_state=None, message_log=None):
        self._prev_scale = scale

        # 1. Background (full screen)
        self.draw_background(width, height, scale)

        # 2. Enemy sprites in top 45 %
        self.draw_enemies(model, width, height, scale)

        # 3. Dispatch menu-area drawing by state
        dispatch = {
            "party_command": self._draw_party_command,
            "run_outcome": lambda *a, **kw: self._draw_run_outcome(*a, **kw, message_log=message_log),
            "message": lambda *a, **kw: self._draw_message(*a, **kw, message_log=message_log),
            "char_command": self._draw_char_command,
            "target_enemy_attack": self._draw_target_enemies,
            "spell_select": self._draw_spell_select,
            "item_select": self._draw_item_select,
            "execute": self._draw_execute,
            "victory": lambda *a, **kw: self._draw_victory(*a, **kw, message_log=message_log),
            "defeat": lambda *a, **kw: self._draw_defeat(*a, **kw, message_log=message_log),
        }
        # Dynamic states: target_enemy_spell, target_party, flash
        if state == "flash":
            # During flash, draw previous menu state beneath
            pass
        elif state.startswith("target_enemy"):
            self._draw_target_enemies(model, scale, width, height, state_obj)
        elif state.startswith("target_party"):
            self._draw_target_party(model, scale, width, height, state_obj)
        elif state in dispatch:
            dispatch[state](model, scale, width, height, state_obj)
        else:
            self._draw_message(model, scale, width, height, state_obj)

        # 4. Flash overlay (drawn on top of everything)
        if flash_state is not None or state == "flash":
            self._draw_flash(model, scale, width, height, flash_state)

    # ------------------------------------------------------------------ #
    #  Background                                                         #
    # ------------------------------------------------------------------ #
    def draw_background(self, w, h, scale):
        """Flat light background."""
        arcade.draw_lrbt_rectangle_filled(0, w, 0, h, (200, 200, 200))

    # ------------------------------------------------------------------ #
    #  Enemy sprites (top 45%)                                            #
    # ------------------------------------------------------------------ #
    def draw_enemies(self, model, w, h, scale):
        enemies = model.enemies
        if not enemies:
            return
        spacing = w / (len(enemies) + 1)
        cy = int(h * 0.72)
        for i, enemy in enumerate(enemies):
            cx = spacing * (i + 1)
            sprite_id = enemy.name.lower().replace(" ", "_")
            if self._sprite_atlas.has_sprite(sprite_id):
                if enemy.alive:
                    self._sprite_atlas.draw(sprite_id, cx, cy, scale * 1.2)
                elif enemy.dying_timer > 0:
                    self._draw_death_animation(sprite_id, cx, cy, scale * 1.2, enemy.dying_timer, 0.5)

    def _draw_death_animation(self, sprite_id: str, cx: float, cy: float, scale: float, dying_timer: float, duration: float):
        progress = 1.0 - (dying_timer / duration)  # 0.0 to 1.0
        texture = self._sprite_atlas.get_texture(sprite_id)
        if not texture:
            return

        tw = texture.width
        th = texture.height
        sw = tw * scale
        sh = th * scale

        if progress < 0.7:
            # Phase 1: collapse to center — top and bottom both pull to midpoint
            p = progress / 0.7
            h = sh * (1 - p) + 2 * p  # lerp from full height to 2px
            w = sw
            center_y = cy
        else:
            # Phase 2: horizontal collapse to center point
            p = (progress - 0.7) / 0.3
            h = 2
            w = sw * (1 - p)  # shrink width to 0
            center_y = cy

        if w > 0 and h > 0:
            arcade.draw_texture_rect(texture, arcade.XYWH(cx, center_y, max(w, 1), max(h, 1)), pixelated=True)

    # ------------------------------------------------------------------ #
    #  Party command (Phase 1)                                             #
    # ------------------------------------------------------------------ #
    def _draw_party_command(self, model, scale, w, h, state_obj):
        me = int(scale)  # multiplier
        bm = BORDER_PX * me  # border width in pixels

        # --- Enemy name box (right 3/5, drawn first = behind) ---
        ex = ENEMY_BOX_X * me
        ew = ENEMY_BOX_W * me
        eh = MENU_H * me
        draw_window(ex, 0, ew, eh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        # Group enemies
        groups = {}
        for e in model.get_living_enemies():
            groups[e.name] = groups.get(e.name, 0) + 1
        lines = [f"{n}   {c}" if c > 1 else n for n, c in groups.items()]
        line_h = int(10 * scale)
        start_y = eh - bm - line_h
        for li, line in enumerate(lines):
            y = start_y - li * line_h
            self._text(f"enemy_group_{li}", line, ex + 2 * bm, y,
                       COLORS["text"], int(7 * scale), anchor_y="center")

        # --- Character box (left 2/5, drawn on top) ---
        cw = CHAR_BOX_W * me
        ch = MENU_H * me
        draw_window(0, 0, cw, ch, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        row_h = ROW_H * me
        for mi, member in enumerate(model.party):
            ry = (len(model.party) - 1 - mi) * row_h
            sprite_id = member.name.lower()
            # Sprite center in row
            scx = bm + 10 * me
            scy = ry + row_h // 2
            if member.alive:
                if not self._sprite_atlas.draw(sprite_id, scx, scy, scale):
                    # fallback
                    sz = 8 * me
                    arcade.draw_lrbt_rectangle_filled(scx - sz, scx + sz,
                                                       scy - sz, scy + sz,
                                                        (48, 48, 48))
            else:
                # Dead = gray box
                sz = 8 * me
                arcade.draw_lrbt_rectangle_filled(scx - sz, scx + sz,
                                                  scy - sz, scy + sz,
                                                  (120, 120, 120))
            # HP text beside sprite
            hp_color = COLORS["text"] if member.alive else (120, 120, 120)
            hp_str = f"{member.hp}/{member.hp_max}"
            if not member.alive:
                hp_str = "DEAD"
            self._text(f"pc_hp_{mi}", hp_str, scx + 14 * me, scy,
                       hp_color, int(6 * scale), anchor_y="center")

        # --- Action box (overlapping both) ---
        ax = ENEMY_BOX_X * me - bm
        aw = int(80 * scale)
        ah = int(40 * scale)
        ay = (MENU_H * me - ah) // 2
        # Clamp
        ax = max(0, ax)
        draw_window(ax, ay, aw, ah, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        sel = state_obj.selection if state_obj else 0
        opts = state_obj.options if state_obj else ["Fight", "Run"]
        opt_y = ay + 8 * me
        opt_h = (ah - 16 * me) // 2
        for oi, opt in enumerate(opts):
            oy = opt_y + (len(opts) - 1 - oi) * opt_h + opt_h // 2
            color = COLORS["cursor"] if oi == sel else COLORS["text"]
            self._text(f"pc_opt_{oi}", opt, ax + 20 * me, oy,
                       color, int(7 * scale), anchor_y="center")
            if oi == sel:
                draw_cursor(ax + 6 * me, oy, scale, COLORS["cursor"])

    # ------------------------------------------------------------------ #
    #  Run outcome (Phase 2)                                              #
    # ------------------------------------------------------------------ #
    def _draw_run_outcome(self, model, scale, w, h, state_obj, message_log=None):
        self._draw_full_message_box(scale, w, h, state_obj, message_log)

    # ------------------------------------------------------------------ #
    #  Message (battle events during execution)                           #
    # ------------------------------------------------------------------ #
    def _draw_message(self, model, scale, w, h, state_obj, message_log=None):
        self._draw_full_message_box(scale, w, h, state_obj, message_log)

    def _draw_full_message_box(self, scale, w, h, state_obj, message_log=None):
        """Full-width box with scrolling + text wrapping message log."""
        me = int(scale)
        mh = MENU_H * me
        mw = w
        draw_window(0, 0, mw, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        if not message_log:
            return

        font_size = int(7 * scale)
        padding = 8 * me
        available_w = mw - 2 * padding
        line_h = font_size + 2 * me

        # Build flat list of wrapped lines from all messages, with blank line separators
        display_lines = []
        for i, msg in enumerate(message_log):
            wrapped = wrap_text(msg, available_w, font_size, scale)
            display_lines.extend(wrapped if wrapped else [""])
            if i < len(message_log) - 1:
                display_lines.append("")  # blank line between messages

        # Calculate lines that fit from bottom up
        bottom_margin = 14 * me  # border_w + font_descender_buffer
        # anchor_y="bottom": text extends UPWARD from y. Text bottom at bottom_margin.
        # Text EXTENDS upward by ~font_size. So first line occupies bottom_margin .. bottom_margin+font_size.
        bottom_y = bottom_margin
        text_area_h = (mh - padding) - (bottom_y + line_h)
        max_lines = max(1, text_area_h // line_h + 1)
        visible = display_lines[-max_lines:]

        for i, line in enumerate(visible):
            y = bottom_y + (len(visible) - 1 - i) * line_h
            self._text(f"log_{i}", line, padding, y,
                       COLORS["text"], font_size,
                       anchor_x="left", anchor_y="bottom")

    # ------------------------------------------------------------------ #
    #  Char command (Phase 3 — per member)                                #
    # ------------------------------------------------------------------ #
    def _draw_char_command(self, model, scale, w, h, state_obj):
        me = int(scale)
        bm = BORDER_PX * me
        mh = MENU_H * me
        member_idx = state_obj.member_idx if state_obj else 0
        member = model.party[member_idx] if member_idx < len(model.party) else None

        # --- Character box (left 2/5, single character) ---
        cw = CHAR_BOX_W * me
        draw_window(0, 0, cw, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        if member:
            sprite_id = member.name.lower()
            scx = bm + 14 * me
            scy = bm + (mh - 2 * bm) // 2
            if member.alive:
                if not self._sprite_atlas.draw(sprite_id, scx, scy, scale * 1.5):
                    sz = 12 * me
                    arcade.draw_lrbt_rectangle_filled(scx - sz, scx + sz,
                                                       scy - sz, scy + sz,
                                                        (48, 48, 48))
            else:
                sz = 12 * me
                arcade.draw_lrbt_rectangle_filled(scx - sz, scx + sz,
                                                  scy - sz, scy + sz,
                                                  (120, 120, 120))
            # Name
            nm_color = COLORS["text"] if member.alive else (120, 120, 120)
            self._text(f"cc_name", member.name[:7], scx + 12 * me, scy + 10 * me,
                       nm_color, int(7 * scale), anchor_y="center")
            # HP
            if member.alive:
                hp_str = f"HP {member.hp}/{member.hp_max}"
                self._text(f"cc_hp", hp_str, scx + 12 * me, scy - 2 * me,
                           COLORS["text"], int(6 * scale), anchor_y="center")
                # MP
                if member.mp_max > 0:
                    mp_str = f"MP {member.mp}/{member.mp_max}"
                    self._text(f"cc_mp", mp_str, scx + 12 * me, scy - 10 * me,
                               (120, 120, 120), int(6 * scale), anchor_y="center")
            else:
                self._text(f"cc_dead", "DEAD", scx + 12 * me, scy,
                           (120, 120, 120), int(7 * scale), anchor_y="center")

        # --- Options box (right 3/5) ---
        ox = ENEMY_BOX_X * me
        ow = ENEMY_BOX_W * me
        draw_window(ox, 0, ow, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        sel = state_obj.selection if state_obj else 0
        opts = state_obj.options if hasattr(state_obj, 'options') else ["Fight", "Magic", "Item"]
        opt_h = (mh - 2 * bm) // len(opts)
        for oi, opt in enumerate(opts):
            oy = bm + (len(opts) - 1 - oi) * opt_h + opt_h // 2
            color = COLORS["cursor"] if oi == sel else COLORS["text"]
            self._text(f"cc_opt_{oi}", opt, ox + 4 * bm, oy,
                       color, int(7 * scale), anchor_y="center")
            if oi == sel:
                draw_cursor(ox + bm, oy, scale, COLORS["cursor"])

    # ------------------------------------------------------------------ #
    #  Spell select (replaces options box)                                #
    # ------------------------------------------------------------------ #
    def _draw_spell_select(self, model, scale, w, h, state_obj):
        me = int(scale)
        bm = BORDER_PX * me
        mh = MENU_H * me
        member_idx = state_obj.member_idx if state_obj else 0
        member = model.party[member_idx] if member_idx < len(model.party) else None

        # Draw char box (same as char_command)
        cw = CHAR_BOX_W * me
        draw_window(0, 0, cw, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        if member:
            sprite_id = member.name.lower()
            scx = bm + 14 * me
            scy = bm + (mh - 2 * bm) // 2
            if member.alive:
                if not self._sprite_atlas.draw(sprite_id, scx, scy, scale * 1.5):
                    sz = 12 * me
                    arcade.draw_lrbt_rectangle_filled(scx - sz, scx + sz,
                                                       scy - sz, scy + sz,
                                                        (48, 48, 48))
            nm_color = COLORS["text"] if member.alive else (120, 120, 120)
            self._text(f"ss_name", member.name[:7], scx + 12 * me, scy + 10 * me,
                       nm_color, int(7 * scale), anchor_y="center")
            hp_str = f"HP {member.hp}/{member.hp_max}" if member.alive else "DEAD"
            self._text(f"ss_hp", hp_str, scx + 12 * me, scy - 2 * me,
                       nm_color, int(6 * scale), anchor_y="center")

        # Spell list in options area
        ox = ENEMY_BOX_X * me
        ow = ENEMY_BOX_W * me
        draw_window(ox, 0, ow, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        spells = member.spells if member else []
        sel = state_obj.selection if state_obj else 0
        line_h = int(10 * scale)
        start_y = mh - bm - line_h
        for si, spell_id in enumerate(spells):
            spell = model.spells.get(spell_id, {})
            name = spell.get("name", spell_id)
            mp_cost = spell.get("mp_cost", 0)
            y = start_y - si * line_h
            can_cast = member and member.mp >= mp_cost
            color = COLORS["cursor"] if si == sel else (COLORS["text"] if can_cast else (120, 120, 120))
            self._text(f"ss_spell_{si}", f"{name}  MP{mp_cost}", ox + 3 * bm, y,
                       color, int(6 * scale), anchor_y="center")
            if si == sel:
                draw_cursor(ox + bm, y, scale, COLORS["cursor"])

    # ------------------------------------------------------------------ #
    #  Target enemies (left 3/5 overlay)                                  #
    # ------------------------------------------------------------------ #
    def _draw_target_enemies(self, model, scale, w, h, state_obj):
        me = int(scale)
        bm = BORDER_PX * me
        mh = MENU_H * me
        con_margin = int(20 * scale)
        tbox_w = int(BW * 3 / 5) * me  # left 3/5
        draw_window(0, 0, tbox_w, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        sel = state_obj.selection if state_obj else 0
        targets = model.get_living_enemies()
        if not targets:
            self._text("te_none", "No targets", bm, mh // 2,
                       (120, 120, 120), int(7 * scale), anchor_y="center")
            return
        line_h = int(12 * scale)
        start_y = mh - bm - line_h
        for ti, target in enumerate(targets):
            y = start_y - ti * line_h
            color = COLORS["cursor"] if ti == sel else COLORS["text"]
            self._text(f"te_{ti}", target.name, tbox_w // 2, y,
                       color, int(7 * scale), anchor_x="center", anchor_y="center")
            if ti == sel:
                draw_cursor(bm, y, scale, COLORS["cursor"])

    # ------------------------------------------------------------------ #
    #  Target party (left 3/5 overlay)                                    #
    # ------------------------------------------------------------------ #
    def _draw_target_party(self, model, scale, w, h, state_obj):
        me = int(scale)
        bm = BORDER_PX * me
        mh = MENU_H * me
        tbox_w = int(BW * 3 / 5) * me
        draw_window(0, 0, tbox_w, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        sel = state_obj.selection if state_obj else 0
        targets = model.get_living_party()
        if not targets:
            self._text("tp_none", "No targets", bm, mh // 2,
                       (120, 120, 120), int(7 * scale), anchor_y="center")
            return
        line_h = int(12 * scale)
        start_y = mh - bm - line_h
        for ti, target in enumerate(targets):
            y = start_y - ti * line_h
            color = COLORS["cursor"] if ti == sel else COLORS["text"]
            label = f"{target.name}  {target.hp}/{target.hp_max}"
            self._text(f"tp_{ti}", label, bm, y,
                       color, int(7 * scale), anchor_y="center")
            if ti == sel:
                draw_cursor(bm, y, scale, COLORS["cursor"])

    # ------------------------------------------------------------------ #
    #  Item select                                                        #
    # ------------------------------------------------------------------ #
    def _draw_item_select(self, model, scale, w, h, state_obj):
        me = int(scale)
        bm = BORDER_PX * me
        mh = MENU_H * me
        member_idx = state_obj.member_idx if state_obj else 0
        member = model.party[member_idx] if member_idx < len(model.party) else None

        # Char box (left)
        cw = CHAR_BOX_W * me
        draw_window(0, 0, cw, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        if member:
            scx = bm + 14 * me
            scy = bm + (mh - 2 * bm) // 2
            nm_color = COLORS["text"] if member.alive else (120, 120, 120)
            self._text(f"is_name", member.name[:7], scx, scy,
                       nm_color, int(7 * scale), anchor_y="center")

        # Item list (right)
        ox = ENEMY_BOX_X * me
        ow = ENEMY_BOX_W * me
        draw_window(ox, 0, ow, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        sel = state_obj.selection if state_obj else 0
        items = state_obj.items if hasattr(state_obj, 'items') else []
        if not items:
            self._text("is_empty", "No items", ox + 2 * bm, mh // 2,
                       (120, 120, 120), int(7 * scale), anchor_y="center")
            return
        line_h = int(10 * scale)
        start_y = mh - bm - line_h
        for ii, item in enumerate(items):
            y = start_y - ii * line_h
            item_def = model.item_data.get(item["id"], {})
            name = item_def.get("name", item["id"])
            label = f"{name} x{item['qty']}"
            color = COLORS["cursor"] if ii == sel else COLORS["text"]
            self._text(f"is_item_{ii}", label, ox + 3 * bm, y,
                       color, int(6 * scale), anchor_y="center")
            if ii == sel:
                draw_cursor(ox + bm, y, scale, COLORS["cursor"])

    # ------------------------------------------------------------------ #
    #  Execute (battle in progress)                                       #
    # ------------------------------------------------------------------ #
    def _draw_execute(self, model, scale, w, h, state_obj):
        """Full-width message box during execution."""
        me = int(scale)
        mh = MENU_H * me
        draw_window(0, 0, w, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        self._text("exec_title", "BATTLE!", w // 2, mh // 2,
                   (24, 24, 24), int(8 * scale),
                   anchor_x="center", anchor_y="center")

    # ------------------------------------------------------------------ #
    #  Victory                                                            #
    # ------------------------------------------------------------------ #
    def _draw_victory(self, model, scale, w, h, state_obj, message_log=None):
        me = int(scale)
        mh = MENU_H * me
        draw_window(0, 0, w, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        msg = state_obj.get_message(model) if state_obj else "Victory!"
        lines = msg.split("\n")
        line_h = int(10 * scale)
        total_h = len(lines) * line_h
        start_y = (mh - total_h) // 2 + total_h - line_h
        for li, line in enumerate(lines):
            color = (24, 24, 24) if li == 0 else (48, 48, 48) if "GP" in line or "EXP" in line else COLORS["text"]
            self._text(f"vic_{li}", line, 8 * me, start_y - li * line_h,
                       color, int(7 * scale), anchor_y="center")

    # ------------------------------------------------------------------ #
    #  Defeat                                                             #
    # ------------------------------------------------------------------ #
    def _draw_defeat(self, model, scale, w, h, state_obj, message_log=None):
        me = int(scale)
        mh = MENU_H * me
        draw_window(0, 0, w, mh, scale,
                    fill_color=COLORS["box_fill"], border_color=COLORS["box_border"])
        msg = state_obj.get_message(model) if state_obj else "Defeat..."
        self._text("defeat_msg", msg, w // 2, mh // 2,
                   (48, 48, 48), int(8 * scale),
                   anchor_x="center", anchor_y="center")

    # ------------------------------------------------------------------ #
    #  Flash highlight                                                    #
    # ------------------------------------------------------------------ #
    def _draw_flash(self, model, scale, w, h, flash_state=None):
        """Draw gold/red outline on acting actor (toggled by flash_state)."""
        action = model.current_action
        if not action:
            return
        is_on = True
        if flash_state is not None:
            is_on = flash_state.flash_count % 2 == 0
        if not is_on:
            return
        if action.action_type in (ActionType.PARTY_ATTACK, ActionType.PARTY_MAGIC, ActionType.USE_ITEM):
            for mi, member in enumerate(model.party):
                if member.name == action.actor.name:
                    me = int(scale)
                    scx = int(8 * scale) + 10 * me
                    scy = (len(model.party) - 1 - mi) * ROW_H * me + ROW_H * me // 2
                    sz = 10 * me
                    arcade.draw_lrbt_rectangle_outline(scx - sz - 2 * me,
                                                       scx + sz + 2 * me,
                                                       scy - sz - 2 * me,
                                                       scy + sz + 2 * me,
                                                        (24, 24, 24), int(scale * 2))
                    break
        elif action.action_type == ActionType.ENEMY_ATTACK:
            for ei, enemy in enumerate(model.enemies):
                if enemy.name == action.actor.name:
                    enemies = model.enemies
                    spacing = w / (len(enemies) + 1)
                    cx = spacing * (ei + 1)
                    cy = int(h * 0.72)
                    sz = 14 * int(scale)
                    arcade.draw_lrbt_rectangle_outline(cx - sz, cx + sz,
                                                       cy - sz, cy + sz,
                                                        (48, 48, 48), int(scale * 2))
                    break
