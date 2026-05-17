"""Menu sub-states for the GBC-style menu system."""

from abc import ABC, abstractmethod
from pyglet.window import key
from game.engine import get_item, calc_party_stats
from game.ui import COLORS, draw_cursor
from game.sprites import get_sprite_atlas

_sprite_atlas = get_sprite_atlas()


class MenuState(ABC):
    """Base class for menu sub-states."""

    def __init__(self, menu):
        self.menu = menu
        self.engine = menu.engine

    @abstractmethod
    def update(self, inp):
        pass

    @abstractmethod
    def draw(self, w, h, scale):
        pass

    # ── helpers ──────────────────────────────────────────

    def draw_text(self, text, x, y, color, size, center=False):
        self.menu.draw_text(text, x, y, color, size, center)

    def draw_box(self, l, r, b, t, scale, fill=None, border=None):
        self.menu.draw_box(l, r, b, t, scale, fill, border)

    def text(self, key, text, x, y, color, size, anchor_x="left", anchor_y="center"):
        return self.menu._get_text(key, text, x, y, color, size, anchor_x, anchor_y)

    @property
    def party(self):
        return self.engine.party


# ======================================================================
#  MainMenuState
# ======================================================================

class MainMenuState(MenuState):
    """Main menu: left menu panel + right party list + gold bar."""

    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0
        self.options = ["Items", "Equip", "Status", "Save"]

    def update(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.options)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.options)
        elif inp.is_just_pressed(key.Z):
            name = self.options[self.selection].lower()
            if name == "items":
                self.menu.set_state("items")
            elif name == "equip":
                self.menu.set_state("equip")
            elif name == "status":
                self.menu.set_state("status")
            elif name == "save":
                self.menu.set_state("save")
        elif inp.is_just_pressed(key.X):
            self.engine.set_scene("overworld")

    def draw(self, w, h, scale):
        fs = int(7 * scale)
        fs2 = int(6 * scale)
        gold_color = (255, 215, 0)
        menu_w = 80 * scale
        party_l = menu_w

        # ── Party list — right 2/3, above gold bar ──
        self.draw_box(party_l, 240 * scale, 20 * scale, 160 * scale, scale)
        for i, m in enumerate(self.party):
            row_y = 146 * scale - i * 32 * scale
            sprite_x = party_l + 10 * scale
            _sprite_atlas.draw(m.name.lower(), sprite_x, row_y, scale)
            name_x = sprite_x + 12 * scale
            hp_color = (0, 180, 0) if m.hp > 0 else (100, 100, 100)
            self.draw_text(m.name, name_x, row_y, COLORS["text"], fs)
            hp_y = row_y - 9 * scale
            self.draw_text(f"HP {m.hp}/{m.hp_max}", name_x, hp_y, hp_color, fs2)
            if m.mp_max > 0:
                self.draw_text(f"MP {m.mp}/{m.mp_max}", name_x + 70 * scale, hp_y,
                               (80, 80, 200), fs2)

        # ── Main menu — left 1/3, above gold bar ──
        self.draw_box(0, menu_w, 20 * scale, 160 * scale, scale)
        for i, opt in enumerate(self.options):
            y = 146 * scale - i * 32 * scale
            c = COLORS["cursor"] if i == self.selection else COLORS["text"]
            self.draw_text(opt, 12 * scale, y, c, fs)
            if i == self.selection:
                draw_cursor(4 * scale, y, scale, COLORS["cursor"])

        # ── Gold bar — bottom right ──
        self.draw_box(120 * scale, 240 * scale, 0, 20 * scale, scale)
        gold_text = self.text(
            "gold_bar",
            f"{self.engine.gold}GP",
            180 * scale, 10 * scale,
            gold_color, fs,
            anchor_x="center", anchor_y="center",
        )
        gold_text.draw()


# ======================================================================
#  ItemsMenuState
# ======================================================================

class ItemsMenuState(MenuState):
    """Full-screen items list with inline target-selection overlay."""

    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0
        self._targeting = False
        self._target_idx = 0

    # ── helpers ──────────────────────────────────────────

    def _alive_indices(self):
        return [i for i, p in enumerate(self.party) if p.hp > 0]

    def _apply_item(self, target_idx):
        entry = self.engine.inventory[self.selection]
        item_def = get_item(entry["id"])
        if not item_def:
            return
        effect = item_def.get("effect")
        target = self.party[target_idx]
        if effect == "heal":
            target.hp = min(target.hp_max, target.hp + item_def["value"])
        elif effect == "mana":
            target.mp = min(target.mp_max, target.mp + item_def["value"])
        elif effect == "revive":
            target.hp = item_def["value"]
            target.alive = True
        elif effect == "restore_all":
            target.hp = target.hp_max
            target.mp = target.mp_max
        elif effect == "full_restore":
            target.hp = target.hp_max
            target.mp = target.mp_max
            target.status = []
        elif effect == "cure_status":
            if target.status and item_def["value"] in target.status:
                target.status.remove(item_def["value"])
        self.engine.remove_item(entry["id"])
        self._targeting = False

    # ── update ───────────────────────────────────────────

    def update(self, inp):
        items = self.engine.inventory

        if self._targeting:
            self._update_targeting(inp)
            return

        if not items:
            if inp.is_just_pressed(key.X):
                self.menu.set_state("main")
            return

        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(items)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(items)
        elif inp.is_just_pressed(key.Z):
            entry = items[self.selection]
            item_def = get_item(entry["id"])
            if item_def and item_def.get("type") == "consumable":
                self._targeting = True
                self._target_idx = 0
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def _update_targeting(self, inp):
        targets = self.party  # include all members
        if inp.is_just_pressed(key.DOWN):
            self._target_idx = (self._target_idx + 1) % len(targets)
        elif inp.is_just_pressed(key.UP):
            self._target_idx = (self._target_idx - 1) % len(targets)
        elif inp.is_just_pressed(key.Z):
            self._apply_item(self._target_idx)
        elif inp.is_just_pressed(key.X):
            self._targeting = False

    # ── draw ─────────────────────────────────────────────

    def draw(self, w, h, scale):
        fs = int(7 * scale)
        fs2 = int(6 * scale)
        box_l, box_r = 40 * scale, 200 * scale

        # ── Items list panel ──
        self.draw_box(box_l, box_r, 0, 160 * scale, scale)
        title_t = self.text(
            "items_title", "ITEMS",
            120 * scale, 152 * scale, COLORS["text"], int(8 * scale),
            anchor_x="center", anchor_y="center",
        )
        title_t.draw()

        items = self.engine.inventory
        if not items:
            empty_t = self.text(
                "items_empty", "No items",
                120 * scale, 80 * scale, (150, 150, 150), fs,
                anchor_x="center", anchor_y="center",
            )
            empty_t.draw()
        else:
            for i, entry in enumerate(items[:8]):
                y = 140 * scale - i * 17 * scale
                item_def = get_item(entry["id"])
                name = item_def["name"] if item_def else entry["id"]
                c = COLORS["cursor"] if i == self.selection else COLORS["text"]
                if i == self.selection and not self._targeting:
                    draw_cursor(box_l + 8 * scale, y, scale, COLORS["cursor"])
                self.draw_text(f"{name} x{entry['qty']}", box_l + 16 * scale, y, c, fs2)

        help_t = self.text(
            "items_help",
            "[Z] Use  [X] Back",
            120 * scale, 8 * scale,
            (150, 150, 150), int(5 * scale),
            anchor_x="center", anchor_y="center",
        )
        help_t.draw()

        # ── Targeting overlay ──
        if self._targeting:
            ol_l = 60 * scale
            ol_r = 180 * scale
            ol_b = 40 * scale
            ol_t = 120 * scale
            self.draw_box(ol_l, ol_r, ol_b, ol_t, scale)
            target_title = self.text(
                "items_target_title", "Use on whom?",
                (ol_l + ol_r) // 2, ol_t - 10 * scale,
                COLORS["text"], fs,
                anchor_x="center", anchor_y="center",
            )
            target_title.draw()
            for i, m in enumerate(self.party):
                y = ol_t - 28 * scale - i * 17 * scale
                c = COLORS["cursor"] if i == self._target_idx else COLORS["text"]
                if i == self._target_idx:
                    draw_cursor(ol_l + 8 * scale, y, scale, COLORS["cursor"])
                hp_str = f"HP {m.hp}/{m.hp_max}"
                alive_color = (0, 180, 0) if m.hp > 0 else (100, 100, 100)
                self.draw_text(m.name, ol_l + 16 * scale, y, c, fs2)
                self.draw_text(hp_str, ol_l + 64 * scale, y, alive_color, fs2)


# ======================================================================
#  StatusMenuState
# ======================================================================

class StatusMenuState(MenuState):
    """Full-screen party status overview — 4 stacked panels."""

    def update(self, inp):
        if inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def draw(self, w, h, scale):
        fs = int(7 * scale)
        fs2 = int(6 * scale)
        panel_l = 4 * scale
        panel_r = 236 * scale
        panel_h = 34 * scale
        gap = 2 * scale
        title_y = 155 * scale

        title_t = self.text(
            "status_title", "STATUS",
            120 * scale, title_y, COLORS["text"], int(8 * scale),
            anchor_x="center", anchor_y="center",
        )
        title_t.draw()

        for i, m in enumerate(self.party):
            # Panel box
            pb = 14 * scale + i * (panel_h + gap)
            pt = pb + panel_h
            self.draw_box(panel_l, panel_r, pb, pt, scale)

            row_cy = (pb + pt) // 2
            # Sprite
            _sprite_atlas.draw(m.name.lower(), panel_l + 12 * scale, row_cy + 2 * scale, scale)
            tx = panel_l + 24 * scale

            # Row 1: name + LV
            r1y = row_cy + 7 * scale
            r2y = row_cy - 7 * scale

            self.draw_text(f"{m.name}  LV{m.lvl}", tx, r1y, COLORS["text"], fs)

            # HP / MP
            hp_color = (0, 180, 0) if m.hp > 0 else (100, 100, 100)
            self.draw_text(f"HP {m.hp}/{m.hp_max}", tx + 64 * scale, r1y, hp_color, fs2)
            mp_color = (80, 80, 200) if m.mp_max > 0 else (100, 100, 100)
            self.draw_text(f"MP {m.mp}/{m.mp_max}", tx + 64 * scale, r2y, mp_color, fs2)

            # ATK / DEF / MAG / SPD
            self.draw_text(f"ATK {m.atk:3d}  DEF {m.def_:3d}", tx + 124 * scale, r1y,
                           COLORS["text"], fs2)
            self.draw_text(f"MAG {m.mag:3d}  SPD {m.spd:3d}", tx + 124 * scale, r2y,
                           COLORS["text"], fs2)

        help_t = self.text(
            "status_help", "[X] Back",
            120 * scale, 4 * scale, (150, 150, 150), int(5 * scale),
            anchor_x="center", anchor_y="center",
        )
        help_t.draw()


# ======================================================================
#  EquipCharSelectState
# ======================================================================

class EquipCharSelectState(MenuState):
    """Party member selection for equipment management."""

    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0

    def update(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.party)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.party)
        elif inp.is_just_pressed(key.Z):
            self.menu.set_state("equip_detail", char_idx=self.selection)
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def draw(self, w, h, scale):
        fs = int(7 * scale)
        fs2 = int(6 * scale)
        party_l = 40 * scale

        title_t = self.text(
            "equip_cs_title", "Select character",
            120 * scale, 155 * scale, COLORS["text"], int(8 * scale),
            anchor_x="center", anchor_y="center",
        )
        title_t.draw()

        self.draw_box(party_l, 240 * scale, 20 * scale, 150 * scale, scale)
        for i, m in enumerate(self.party):
            row_y = 138 * scale - i * 32 * scale
            sprite_x = party_l + 10 * scale
            _sprite_atlas.draw(m.name.lower(), sprite_x, row_y, scale)
            name_x = sprite_x + 14 * scale
            c = COLORS["cursor"] if i == self.selection else COLORS["text"]
            if i == self.selection:
                draw_cursor(party_l + 4 * scale, row_y, scale, COLORS["cursor"])
            hp_color = (0, 180, 0) if m.hp > 0 else (100, 100, 100)
            self.draw_text(m.name, name_x, row_y, c, fs)
            self.draw_text(f"HP {m.hp}/{m.hp_max}", name_x + 70 * scale, row_y,
                           hp_color, fs2)

        help_t = self.text(
            "equip_cs_help", "[Z] Select  [X] Back",
            120 * scale, 8 * scale, (150, 150, 150), int(5 * scale),
            anchor_x="center", anchor_y="center",
        )
        help_t.draw()


# ======================================================================
#  EquipDetailState
# ======================================================================

class EquipDetailState(MenuState):
    """Equipment detail & change screen — 4 layered panels."""

    def __init__(self, menu, char_idx=0):
        super().__init__(menu)
        self.char_idx = char_idx
        self.slots = ["Weapon", "Armor", "Helm", "Shield", "Accessory"]
        self.slot_keys = ["weapon", "armor", "helm", "shield", "accessory"]
        self.slot_types = ["weapon", "armor", "helm", "shield", "accessory"]
        self.selection = 0
        self.phase = "slots"  # "slots" | "items"
        self._preview_stats = None  # (preview_atk, preview_def, preview_mag, change_atk, change_def, change_mag) | None
        self._slot_selection = 0

    # ── helpers ──────────────────────────────────────────

    @property
    def _member(self):
        return self.party[self.char_idx]

    @staticmethod
    def _item_bonuses(item_id):
        """Return (atk_bonus, def_bonus, mag_bonus) for an item id or None."""
        if not item_id:
            return (0, 0, 0)
        from game.engine import WEAPON_DATA, ARMOR_DATA
        w = WEAPON_DATA.get(item_id)
        if w:
            return (w.get("atk", 0), 0, w.get("mag", 0))
        a = ARMOR_DATA.get(item_id)
        if a:
            return (a.get("atk", 0), a.get("def", 0), a.get("mag", 0))
        return (0, 0, 0)

    def _compute_preview(self, item_def):
        """Calculate stat preview if item_def is equipped in selected slot."""
        member = self._member
        slot_key = self.slot_keys[self.selection]
        cur_id = getattr(member, slot_key)
        cur_a, cur_d, cur_m = self._item_bonuses(cur_id)
        new_a, new_d, new_m = self._item_bonuses(item_def["id"])
        da, dd, dm = new_a - cur_a, new_d - cur_d, new_m - cur_m
        return (
            member.atk + da,
            member.def_ + dd,
            member.mag + dm,
            da, dd, dm,
        )

    def _equip_items(self):
        """Inventory items matching current slot type."""
        slot_type = self.slot_types[self.selection]
        results = []
        for entry in self.engine.inventory:
            item_def = get_item(entry["id"])
            if item_def and item_def.get("type") == slot_type:
                results.append(entry)
        return results

    def _do_equip(self, item_idx):
        items = self._equip_items()
        if item_idx >= len(items):
            return
        entry = items[item_idx]
        slot_key = self.slot_keys[self.selection]
        setattr(self._member, slot_key, entry["id"])
        calc_party_stats(self.party)
        self.phase = "slots"
        self._preview_stats = None

    # ── update ───────────────────────────────────────────

    def update(self, inp):
        if self.phase == "slots":
            self._update_slots(inp)
        elif self.phase == "items":
            self._update_items(inp)

    def _update_slots(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.slots)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.slots)
        elif inp.is_just_pressed(key.Z):
            if self._equip_items():
                self._slot_selection = self.selection
                self.phase = "items"
                self.selection = 0
                self._preview_stats = None
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("equip")

    def _update_items(self, inp):
        items = self._equip_items()
        if not items:
            self.phase = "slots"
            self.selection = 0
            return
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(items)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(items)
        elif inp.is_just_pressed(key.Z):
            self._do_equip(self.selection)
        elif inp.is_just_pressed(key.X):
            self.phase = "slots"
            self.selection = self._slot_selection
            self._preview_stats = None

        # Refresh preview each frame
        if self.selection < len(items):
            item_def = get_item(items[self.selection]["id"])
            if item_def:
                self._preview_stats = self._compute_preview(item_def)
            else:
                self._preview_stats = None

    # ── draw ─────────────────────────────────────────────

    def _draw_panel1_stats(self, scale):
        """Panel 1 — character stats (left 1/2, bottom 3/4)."""
        member = self._member
        fs = int(6 * scale)
        self.draw_box(0, 120 * scale, 0, 120 * scale, scale)
        if self._preview_stats:
            pa, pd, pm, da, dd, dm = self._preview_stats
            self.draw_text(f"STR: {member.atk} -> {pa}", 8 * scale, 104 * scale,
                           COLORS["text"], fs)
            self.draw_text(f"DEF: {member.def_} -> {pd}", 8 * scale, 92 * scale,
                           COLORS["text"], fs)
            self.draw_text(f"AGI: {member.spd}", 8 * scale, 80 * scale,
                           COLORS["text"], fs)
            self.draw_text(f"MAG: {member.mag} -> {pm}", 8 * scale, 68 * scale,
                           COLORS["text"], fs)
        else:
            self.draw_text(f"STR: {member.atk}", 8 * scale, 104 * scale,
                           COLORS["text"], fs)
            self.draw_text(f"DEF: {member.def_}", 8 * scale, 92 * scale,
                           COLORS["text"], fs)
            self.draw_text(f"AGI: {member.spd}", 8 * scale, 80 * scale,
                           COLORS["text"], fs)
            self.draw_text(f"MAG: {member.mag}", 8 * scale, 68 * scale,
                           COLORS["text"], fs)

    def _draw_panel2_identity(self, scale):
        """Panel 2 — character identifier (left 1/3, top 1/4)."""
        member = self._member
        fs = int(6 * scale)
        fs_sm = int(5 * scale)
        self.draw_box(0, 80 * scale, 120 * scale, 160 * scale, scale)
        _sprite_atlas.draw(member.name.lower(), 28 * scale, 150 * scale, scale)
        self.draw_text(member.name, 44 * scale, 150 * scale, COLORS["text"], fs)
        hp_color = (0, 180, 0) if member.hp > 0 else (100, 100, 100)
        self.draw_text(f"HP {member.hp}/{member.hp_max}", 44 * scale, 138 * scale,
                       hp_color, fs_sm)

    def _draw_panel3_items(self, scale):
        """Panel 3 — equipment list (right 2/3, full height)."""
        fs_sm = int(5 * scale)
        self.draw_box(80 * scale, 240 * scale, 0, 160 * scale, scale)
        items = self._equip_items()
        if not items:
            return
        visible = min(len(items), 9)
        for i in range(visible):
            entry = items[i]
            item_def = get_item(entry["id"])
            if not item_def:
                continue
            y = 154 * scale - i * 14 * scale
            c = COLORS["cursor"] if (self.phase == "items" and i == self.selection) \
                else COLORS["text"]
            if self.phase == "items" and i == self.selection:
                draw_cursor(88 * scale, y, scale, COLORS["cursor"])
            parts = []
            if item_def.get("atk"):
                parts.append(f"ATK+{item_def['atk']}")
            if item_def.get("def"):
                parts.append(f"DEF+{item_def['def']}")
            if item_def.get("mag"):
                parts.append(f"MAG+{item_def['mag']}")
            stat_str = " ".join(parts)
            self.draw_text(f"{item_def['name']} {stat_str}", 96 * scale, y, c, fs_sm)

    def _draw_panel4_equipped(self, scale):
        """Panel 4 — currently equipped slots (right 2/3, bottom 3/4)."""
        member = self._member
        fs = int(6 * scale)
        fs_sm = int(4 * scale)
        self.draw_box(80 * scale, 240 * scale, 0, 120 * scale, scale)
        for i, slot_name in enumerate(self.slots):
            y = 112 * scale - i * 22 * scale
            slot_key = self.slot_keys[i]
            curr_id = getattr(member, slot_key)
            curr_item = get_item(curr_id)
            curr_name = curr_item["name"] if curr_item else "None"
            if self.phase == "slots":
                c = COLORS["cursor"] if i == self.selection else COLORS["text"]
                if i == self.selection:
                    draw_cursor(88 * scale, y, scale, COLORS["cursor"])
            else:
                c = COLORS["text"]
            self.draw_text(f"{slot_name}:", 96 * scale, y + 5 * scale, c, fs)
            self.draw_text(curr_name, 96 * scale, y - 5 * scale,
                           (100, 100, 100), fs_sm)

    def draw(self, w, h, scale):
        # Draw order: Panel 1 → Panel 2 → Panel 3 → Panel 4 (front)
        self._draw_panel1_stats(scale)
        self._draw_panel2_identity(scale)
        self._draw_panel3_items(scale)
        self._draw_panel4_equipped(scale)

        # Help text at very bottom
        if self.phase == "slots":
            help_text = "[Z] Equip  [X] Back"
        else:
            help_text = "[Z] Confirm  [X] Cancel"
        help_t = self.text(
            "equip_detail_help", help_text,
            160 * scale, 6 * scale, (150, 150, 150), int(5 * scale),
            anchor_x="center", anchor_y="center",
        )
        help_t.draw()


# ======================================================================
#  SaveMenuState
# ======================================================================

class SaveMenuState(MenuState):
    """3-slot save screen — full-width slots."""

    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0
        self._saves = []

    def _load_saves(self):
        if self._saves:
            return
        from game.save import get_all_saves, init_db
        init_db()
        self._saves = get_all_saves()

    def update(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % 3
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % 3
        elif inp.is_just_pressed(key.Z):
            from game.save import save_game
            name = f"Slot {self.selection + 1}"
            state = self.engine.get_state()
            save_game(self.selection, name, state, int(self.engine.play_time))
            self.menu.set_state("main")
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def draw(self, w, h, scale):
        self._load_saves()

        fs = int(7 * scale)
        fs2 = int(6 * scale)

        title_t = self.text(
            "save_title", "SAVE GAME",
            120 * scale, 155 * scale, COLORS["text"], int(8 * scale),
            anchor_x="center", anchor_y="center",
        )
        title_t.draw()

        slot_heights = [53, 54, 53]
        slot_top = 0
        for i in range(3):
            sh = slot_heights[i] * scale
            tb = slot_top * scale
            tt = tb + sh
            slot_top += slot_heights[i]

            border = COLORS["cursor"] if i == self.selection else COLORS["box_border"]
            self.draw_box(0, 240 * scale, int(tb), int(tt), scale, border=border)

            cy = int((tb + tt) // 2)
            exists = any(s["slot"] == i for s in self._saves)
            if exists:
                for s in self._saves:
                    if s["slot"] == i:
                        self.draw_text(f"Slot {i + 1}: {s['name']}", 16 * scale,
                                       cy + 6 * scale, COLORS["text"], fs)
                        self.draw_text(f"Play Time: {int(s['play_time'])}s",
                                       16 * scale, cy - 7 * scale,
                                       (100, 100, 100), fs2)
                        break
            else:
                self.draw_text(f"Slot {i + 1}: [Empty]", 16 * scale, cy,
                               COLORS["text"], fs)

        help_t = self.text(
            "save_help", "[Z] Save  [X] Back",
            120 * scale, 4 * scale, (150, 150, 150), int(5 * scale),
            anchor_x="center", anchor_y="center",
        )
        help_t.draw()
