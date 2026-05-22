"""Menu sub-states for the GBC-style menu system."""

import time
from abc import ABC, abstractmethod
from pyglet.window import key
from game.data import get_item
from game.stats import calc_party_stats
from game.ui import COLORS, draw_cursor
from game.sprites import get_sprite_atlas
from game.scenes.menu_layout import get_menu_layout

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

    def __init__(self, menu, phase="menu", char_idx=0):
        super().__init__(menu)
        self.selection = 0
        self.options = ["Items", "Equip", "Status", "Save"]
        self._phase = phase
        self._char_selection = char_idx
        # ── Sprite animation ──
        self._anim_interval = 8 / 60  # seconds between sprite toggles (~15fps); increase to slow down
        self._anim_next_toggle = time.monotonic() + self._anim_interval  # first toggle after one interval
        self._anim_frame = 0

    def update(self, inp):
        now = time.monotonic()
        if now >= self._anim_next_toggle:
            self._anim_next_toggle = now + self._anim_interval
            self._anim_frame = 1 - self._anim_frame
        if self._phase == "equip_char":
            if inp.is_just_pressed(key.DOWN):
                self._char_selection = (self._char_selection + 1) % len(self.party)
            elif inp.is_just_pressed(key.UP):
                self._char_selection = (self._char_selection - 1) % len(self.party)
            elif inp.is_just_pressed(key.Z):
                self.menu.set_state("equip_detail", char_idx=self._char_selection)
            elif inp.is_just_pressed(key.X):
                self._phase = "menu"
                self.selection = 2
            return

        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.options)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.options)
        elif inp.is_just_pressed(key.Z):
            name = self.options[self.selection].lower()
            if name == "items":
                self.menu.set_state("items")
            elif name == "equip":
                self._phase = "equip_char"
                self._char_selection = 0
            elif name == "status":
                self.menu.set_state("status")
            elif name == "save":
                self.menu.set_state("save")
        elif inp.is_just_pressed(key.X):
            self.engine.set_scene("overworld")

    def draw(self, w, h, scale):
        L = get_menu_layout()
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(L.fonts.NORMAL7 * scale)        # menu option text
        FS2 = int(L.fonts.NORMAL6 * scale)       # sub-text / stats
        FS_SM = int(L.fonts.SMALL5 * scale)      # HP/MP numbers

        # ──── Screen / panel dimensions ────
        SCREEN_W = L.screen.WIDTH * scale        # full screen width
        SCREEN_H = L.screen.HEIGHT * scale       # full screen height
        MENU_W = L.main.MENU_W * scale           # left menu panel width
        MENU_L = L.main.MENU_L * scale           # left edge of menu panel
        PARTY_L = MENU_W                         # (= right edge of menu panel)
        GOLD_H = L.main.GOLD_H * scale           # gold bar height
        GOLD_B = L.main.GOLD_B * scale           # gold bar bottom

        # ──── Menu panel rows ────
        MENU_ROW_1 = L.main.MENU_ROW_1 * scale   # first option Y
        MENU_ROW_GAP = L.main.MENU_ROW_GAP * scale

        # ──── Party panel rows ────
        PARTY_ROW_1 = L.main.PARTY_ROW_1 * scale # first party member Y
        PARTY_ROW_GAP = L.main.PARTY_ROW_GAP * scale

        # ──── Party panel offsets ────
        SPRITE_X_OFF = L.main.SPRITE_X_OFF * scale
        NAME_X_OFF = L.main.NAME_X_OFF * scale
        HP_Y_OFF = L.main.HP_Y_OFF * scale
        HP_CUR_Y_OFF = L.main.HP_CUR_Y_OFF * scale
        HP_MAX_Y_OFF = L.main.HP_MAX_Y_OFF * scale
        MP_COL_OFF = L.main.MP_COL_OFF * scale
        CURSOR_PARTY_OFF = L.main.CURSOR_PARTY_OFF * scale

        # ──── Menu panel offsets ────
        TEXT_OFF = L.main.TEXT_OFF * scale
        CURSOR_OFF = L.main.CURSOR_OFF * scale

        # ──── Gold bar ────
        GOLD_TEXT_CX = MENU_W // 2
        GOLD_TEXT_CY = GOLD_H // 2

        # ════════════════════════ DRAW ════════════════════════
        # ── Party list — right 2/3, full height ──
        self.draw_box(PARTY_L, SCREEN_W, 0, SCREEN_H, scale)
        for i, m in enumerate(self.party):
            row_y = PARTY_ROW_1 - i * PARTY_ROW_GAP
            sprite_x = PARTY_L + SPRITE_X_OFF
            _sprite_atlas.draw(f"{m.name.lower()}_dn_{self._anim_frame}", sprite_x, row_y, scale)
            name_x = sprite_x + NAME_X_OFF
            self.draw_text(m.name, name_x, row_y, COLORS["text"], FS)
            hp_y = row_y + HP_Y_OFF
            self.draw_text(f"HP{m.hp:4d}/", name_x, hp_y + HP_CUR_Y_OFF, COLORS["text"], FS_SM)
            self.draw_text(f"  {m.hp_max:4d}", name_x, hp_y + HP_MAX_Y_OFF, COLORS["text"], FS_SM)
            if m.mp_max > 0:
                mp_x = name_x + MP_COL_OFF
                self.draw_text(f"MP{m.mp:4d}/", mp_x, hp_y + HP_CUR_Y_OFF, COLORS["text"], FS_SM)
                self.draw_text(f"  {m.mp_max:4d}", mp_x, hp_y + HP_MAX_Y_OFF, COLORS["text"], FS_SM)
            if self._phase == "equip_char" and i == self._char_selection:
                draw_cursor(PARTY_L + CURSOR_PARTY_OFF, row_y, scale, COLORS["cursor"])

        # ── Main menu — left 1/3, above gold bar ──
        self.draw_box(MENU_L, MENU_W, GOLD_H, SCREEN_H, scale)
        for i, opt in enumerate(self.options):
            y = MENU_ROW_1 - i * MENU_ROW_GAP
            c = COLORS["cursor"] if (i == self.selection and self._phase == "menu") else COLORS["text"]
            self.draw_text(opt, TEXT_OFF, y, c, FS)
            if i == self.selection and self._phase == "menu":
                draw_cursor(CURSOR_OFF, y, scale, COLORS["cursor"])

        # ── Gold bar — bottom left ──
        self.draw_box(MENU_L, MENU_W, GOLD_B, GOLD_H, scale)
        gold_text = self.text(
            "gold_bar",
            f"{self.engine.gold}GP",
            GOLD_TEXT_CX, GOLD_TEXT_CY,
            COLORS["text"], FS,
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
        L = get_menu_layout()
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(L.fonts.NORMAL7 * scale)      # heading / overlay title
        FS2 = int(L.fonts.NORMAL6 * scale)     # item names / sub-text
        FS_SM = int(L.fonts.SMALL5 * scale)    # help text
        FS_TITLE = int(L.fonts.TITLE8 * scale) # "ITEMS" title

        # ──── Items panel ────
        PANEL_L = L.items.PANEL_L * scale
        PANEL_R = L.items.PANEL_R * scale
        PANEL_B = L.items.PANEL_B * scale
        PANEL_T = L.items.PANEL_T * scale

        # ──── Title ────
        TITLE_X = L.items.TITLE_X * scale
        TITLE_Y = L.items.TITLE_Y * scale

        # ──── Empty state ────
        EMPTY_X = L.items.EMPTY_X * scale
        EMPTY_Y = L.items.EMPTY_Y * scale
        EMPTY_COLOR = (150, 150, 150)

        # ──── Item rows ────
        ITEM_ROW_1 = L.items.ITEM_ROW_1 * scale
        ITEM_GAP = L.items.ITEM_GAP * scale
        ITEM_CURSOR_OFF = L.items.ITEM_CURSOR_OFF * scale
        ITEM_TEXT_OFF = L.items.ITEM_TEXT_OFF * scale
        ITEM_MAX_VISIBLE = L.items.ITEM_MAX_VISIBLE

        # ──── Help text ────
        HELP_X = L.items.HELP_X * scale
        HELP_Y = L.items.HELP_Y * scale
        HELP_COLOR = (150, 150, 150)

        # ──── Targeting overlay ────
        OL_L = L.items.OL_L * scale
        OL_R = L.items.OL_R * scale
        OL_B = L.items.OL_B * scale
        OL_T = L.items.OL_T * scale
        OL_TITLE_OFF = L.items.OL_TITLE_OFF * scale
        OL_FIRST_Y_OFF = L.items.OL_FIRST_Y_OFF * scale
        OL_TARGET_GAP = L.items.OL_TARGET_GAP * scale
        OL_CURSOR_OFF = L.items.OL_CURSOR_OFF * scale
        OL_NAME_OFF = L.items.OL_NAME_OFF * scale
        OL_HP_OFF = L.items.OL_HP_OFF * scale
        OL_Y_ADJ = L.items.OL_Y_ADJ * scale

        # ════════════════════════ DRAW ════════════════════════
        # ── Items list panel ──
        self.draw_box(PANEL_L, PANEL_R, PANEL_B, PANEL_T, scale)

        items = self.engine.inventory
        if not items:
            empty_t = self.text(
                "items_empty", "No items",
                EMPTY_X, EMPTY_Y, EMPTY_COLOR, FS,
                anchor_x="center", anchor_y="center",
            )
            empty_t.draw()
        else:
            for i, entry in enumerate(items[:ITEM_MAX_VISIBLE]):
                y = ITEM_ROW_1 - i * ITEM_GAP
                item_def = get_item(entry["id"])
                name = item_def["name"] if item_def else entry["id"]
                c = COLORS["cursor"] if i == self.selection else COLORS["text"]
                if i == self.selection and not self._targeting:
                    draw_cursor(PANEL_L + ITEM_CURSOR_OFF, y, scale, COLORS["cursor"])
                self.draw_text(f"{name} x{entry['qty']}", PANEL_L + ITEM_TEXT_OFF, y, c, FS2)

        #help_t = self.text(
            #"items_help",
            #"[Z] Use  [X] Back",
            #HELP_X, HELP_Y,
            #HELP_COLOR, FS_SM,
            #anchor_x="center", anchor_y="center",
        #)
        #help_t.draw()

        # ── Targeting overlay ──
        if self._targeting:
            OL_CX = (OL_L + OL_R) // 2
            OL_TITLE_Y = OL_T + OL_TITLE_OFF
            self.draw_box(OL_L, OL_R, OL_B, OL_T, scale)
            target_title = self.text(
                "items_target_title", "Use on whom?",
                OL_CX, OL_TITLE_Y,
                COLORS["text"], FS,
                anchor_x="center", anchor_y="center",
            )
            target_title.draw()
            for i, m in enumerate(self.party):
                y = OL_T + OL_FIRST_Y_OFF - i * OL_TARGET_GAP
                c = COLORS["cursor"] if i == self._target_idx else COLORS["text"]
                if i == self._target_idx:
                    draw_cursor(OL_L + OL_CURSOR_OFF, y, scale, COLORS["cursor"])
                self.draw_text(m.name, OL_L + OL_NAME_OFF, y + OL_Y_ADJ, c, FS2)
                self.draw_text(f"HP{m.hp:4d}", OL_L + OL_HP_OFF, y + OL_Y_ADJ, COLORS["text"], FS2)
                self.draw_text(f"  {m.hp_max:4d}", OL_L + OL_HP_OFF, y - OL_Y_ADJ, COLORS["text"], FS2)


# ======================================================================
#  StatusMenuState
# ======================================================================

class StatusMenuState(MenuState):
    """Full-screen party status overview — 4 stacked panels."""

    def __init__(self, menu):
        super().__init__(menu)
        # ── Sprite animation ──
        self._anim_interval = 8 / 60  # seconds between sprite toggles (~15fps); increase to slow down
        self._anim_next_toggle = time.monotonic() + self._anim_interval
        self._anim_frame = 0

    def update(self, inp):
        now = time.monotonic()
        if now >= self._anim_next_toggle:
            self._anim_next_toggle = now + self._anim_interval
            self._anim_frame = 1 - self._anim_frame
        if inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def draw(self, w, h, scale):
        L = get_menu_layout()
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(L.fonts.NORMAL7 * scale)      # names / level
        FS2 = int(L.fonts.NORMAL6 * scale)     # stats
        FS_TITLE = int(L.fonts.TITLE8 * scale) # "STATUS" title
        FS_SM = int(L.fonts.SMALL5 * scale)    # help text

        # ──── Panel dimensions ────
        PANEL_L = L.status.PANEL_L * scale
        PANEL_R = L.status.PANEL_R * scale
        PANEL_H = L.status.PANEL_H * scale
        PANEL_GAP = L.status.PANEL_GAP * scale

        # ──── Title ────
        TITLE_X = L.status.TITLE_X * scale
        TITLE_Y = L.status.TITLE_Y * scale

        # ──── First panel bottom ────
        FIRST_PB = L.status.FIRST_PB * scale

        # ──── Within each member panel ────
        SPRITE_OFF = L.status.SPRITE_OFF * scale
        SPRITE_Y_OFF = L.status.SPRITE_Y_OFF * scale
        TEXT_X_OFF = L.status.TEXT_X_OFF * scale

        # ──── Row Y offsets from panel vertical center ────
        R1_OFF = L.status.R1_OFF * scale
        R2_OFF = L.status.R2_OFF * scale
        R3_OFF = L.status.R3_OFF * scale
        R4_OFF = L.status.R4_OFF * scale

        # ──── Column X offsets from text start (tx) ────
        COL1_OFF = L.status.COL1_OFF * scale
        COL2_OFF = L.status.COL2_OFF * scale

        # ──── Help text ────
        HELP_X = L.status.HELP_X * scale
        HELP_Y = L.status.HELP_Y * scale
        HELP_COLOR = (150, 150, 150)

        # ════════════════════════ DRAW ════════════════════════
        title_t = self.text(
            "status_title", "STATUS",
            TITLE_X, TITLE_Y, COLORS["text"], FS_TITLE,
            anchor_x="center", anchor_y="center",
        )
        title_t.draw()

        for i, m in enumerate(self.party):
            # Panel box
            pb = FIRST_PB + i * (PANEL_H + PANEL_GAP)
            pt = pb + PANEL_H
            self.draw_box(PANEL_L, PANEL_R, pb, pt, scale)

            row_cy = (pb + pt) // 2
            # Sprite
            _sprite_atlas.draw(f"{m.name.lower()}_dn_{self._anim_frame}", PANEL_L + SPRITE_OFF, row_cy + SPRITE_Y_OFF, scale)
            tx = PANEL_L + TEXT_X_OFF

            # 4 rows for name + two-line HP/MP + stats
            r1y = row_cy + R1_OFF
            r2y = row_cy + R2_OFF
            r3y = row_cy + R3_OFF
            r4y = row_cy + R4_OFF

            self.draw_text(f"{m.name} LV{m.lvl}", tx, r1y, COLORS["text"], FS)

            self.draw_text(f"HP{m.hp:4d}", tx + COL1_OFF, r1y, COLORS["text"], FS2)
            self.draw_text(f"  {m.hp_max:4d}", tx + COL1_OFF, r2y, COLORS["text"], FS2)
            self.draw_text(f"MP{m.mp:4d}", tx + COL1_OFF, r3y, COLORS["text"], FS2)
            self.draw_text(f"  {m.mp_max:4d}", tx + COL1_OFF, r4y, COLORS["text"], FS2)

            self.draw_text(f"ATK {m.atk:3d}", tx + COL2_OFF, r1y, COLORS["text"], FS2)
            self.draw_text(f"DEF {m.def_:3d}", tx + COL2_OFF, r2y, COLORS["text"], FS2)
            self.draw_text(f"MAG {m.mag:3d}", tx + COL2_OFF, r3y, COLORS["text"], FS2)
            self.draw_text(f"SPD {m.spd:3d}", tx + COL2_OFF, r4y, COLORS["text"], FS2)

        help_t = self.text(
            "status_help", "[X] Back",
            HELP_X, HELP_Y, HELP_COLOR, FS_SM,
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
        # ── Sprite animation ──
        self._anim_interval = 8 / 60  # seconds between sprite toggles (~15fps); increase to slow down
        self._anim_next_toggle = time.monotonic() + self._anim_interval
        self._anim_frame = 0

    def update(self, inp):
        now = time.monotonic()
        if now >= self._anim_next_toggle:
            self._anim_next_toggle = now + self._anim_interval
            self._anim_frame = 1 - self._anim_frame
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.party)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.party)
        elif inp.is_just_pressed(key.Z):
            self.menu.set_state("equip_detail", char_idx=self.selection)
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def draw(self, w, h, scale):
        L = get_menu_layout()
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(L.fonts.NORMAL7 * scale)      # character names
        FS2 = int(L.fonts.NORMAL6 * scale)     # (unused currently)
        FS_SM = int(L.fonts.SMALL5 * scale)    # HP numbers
        FS_TITLE = int(L.fonts.TITLE8 * scale) # title
        FS_HELP = int(L.fonts.SMALL5 * scale)  # help text

        # ──── Panel / screen dimensions ────
        SCREEN_R = L.screen.RIGHT * scale
        PARTY_L = L.equip_char.PARTY_L * scale
        PANEL_B = L.equip_char.PANEL_B * scale
        PANEL_T = L.equip_char.PANEL_T * scale

        # ──── Title ────
        TITLE_X = L.equip_char.TITLE_X * scale
        TITLE_Y = L.equip_char.TITLE_Y * scale

        # ──── Party rows ────
        ROW_1 = L.equip_char.ROW_1 * scale
        ROW_GAP = L.equip_char.ROW_GAP * scale
        SPRITE_OFF = L.equip_char.SPRITE_OFF * scale
        NAME_OFF = L.equip_char.NAME_OFF * scale
        CURSOR_OFF = L.equip_char.CURSOR_OFF * scale
        HP_Y_OFF = L.equip_char.HP_Y_OFF * scale
        HP_CUR_OFF = L.equip_char.HP_CUR_OFF * scale
        HP_MAX_OFF = L.equip_char.HP_MAX_OFF * scale

        # ──── Help text ────
        HELP_X = L.equip_char.HELP_X * scale
        HELP_Y = L.equip_char.HELP_Y * scale
        HELP_COLOR = (150, 150, 150)

        # ════════════════════════ DRAW ════════════════════════
        title_t = self.text(
            "equip_cs_title", "Select character",
            TITLE_X, TITLE_Y, COLORS["text"], FS_TITLE,
            anchor_x="center", anchor_y="center",
        )
        title_t.draw()

        self.draw_box(PARTY_L, SCREEN_R, PANEL_B, PANEL_T, scale)
        for i, m in enumerate(self.party):
            row_y = ROW_1 - i * ROW_GAP
            sprite_x = PARTY_L + SPRITE_OFF
            _sprite_atlas.draw(f"{m.name.lower()}_dn_{self._anim_frame}", sprite_x, row_y, scale)
            name_x = sprite_x + NAME_OFF
            c = COLORS["cursor"] if i == self.selection else COLORS["text"]
            if i == self.selection:
                draw_cursor(PARTY_L + CURSOR_OFF, row_y, scale, COLORS["cursor"])
            self.draw_text(m.name, name_x, row_y, c, FS)
            hp_y = row_y + HP_Y_OFF
            self.draw_text(f"HP{m.hp:4d}", name_x, hp_y + HP_CUR_OFF, COLORS["text"], FS_SM)
            self.draw_text(f"  {m.hp_max:4d}", name_x, hp_y + HP_MAX_OFF, COLORS["text"], FS_SM)

        help_t = self.text(
            "equip_cs_help", "[Z] Select  [X] Back",
            HELP_X, HELP_Y, HELP_COLOR, FS_HELP,
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
        # ── Sprite animation ──
        self._anim_interval = 8 / 60  # seconds between sprite toggles (~15fps); increase to slow down
        self._anim_next_toggle = time.monotonic() + self._anim_interval
        self._anim_frame = 0

    # ── helpers ──────────────────────────────────────────

    @property
    def _member(self):
        return self.party[self.char_idx]

    @staticmethod
    def _item_bonuses(item_id):
        """Return (atk_bonus, def_bonus, mag_bonus) for an item id or None."""
        if not item_id:
            return (0, 0, 0)
        from game.data import WEAPON_DATA, ARMOR_DATA
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
        now = time.monotonic()
        if now >= self._anim_next_toggle:
            self._anim_next_toggle = now + self._anim_interval
            self._anim_frame = 1 - self._anim_frame
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
            self.menu.set_state("main", phase="equip_char", char_idx=self.char_idx)

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

    # ── draw sub-methods ─────────────────────────────────

    def _draw_panel1_stats(self, scale):
        """Panel 1 — character stats (left 1/2, bottom 3/4)."""
        L = get_menu_layout()
        p1 = L.equip_detail.panel1
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(L.fonts.NORMAL6 * scale)  # stat label text

        # ──── Panel box ────
        BOX_L = p1.BOX_L * scale
        BOX_R = p1.BOX_R * scale
        BOX_B = p1.BOX_B * scale
        BOX_T = p1.BOX_T * scale

        # ──── Stat row positions ────
        TEXT_X = p1.TEXT_X * scale
        ROW_1_Y = p1.ROW_1_Y * scale
        ROW_2_Y = p1.ROW_2_Y * scale
        ROW_3_Y = p1.ROW_3_Y * scale
        ROW_4_Y = p1.ROW_4_Y * scale

        # ════════════════════════ DRAW ════════════════════════
        member = self._member
        self.draw_box(BOX_L, BOX_R, BOX_B, BOX_T, scale)
        if self._preview_stats:
            pa, pd, pm, da, dd, dm = self._preview_stats
            self.draw_text(f"STR: {member.atk} -> {pa}", TEXT_X, ROW_1_Y,
                           COLORS["text"], FS)
            self.draw_text(f"DEF: {member.def_} -> {pd}", TEXT_X, ROW_2_Y,
                           COLORS["text"], FS)
            self.draw_text(f"AGI: {member.spd}", TEXT_X, ROW_3_Y,
                           COLORS["text"], FS)
            self.draw_text(f"MAG: {member.mag} -> {pm}", TEXT_X, ROW_4_Y,
                           COLORS["text"], FS)
        else:
            self.draw_text(f"STR: {member.atk}", TEXT_X, ROW_1_Y,
                           COLORS["text"], FS)
            self.draw_text(f"DEF: {member.def_}", TEXT_X, ROW_2_Y,
                           COLORS["text"], FS)
            self.draw_text(f"AGI: {member.spd}", TEXT_X, ROW_3_Y,
                           COLORS["text"], FS)
            self.draw_text(f"MAG: {member.mag}", TEXT_X, ROW_4_Y,
                           COLORS["text"], FS)

    def _draw_panel2_identity(self, scale):
        """Panel 2 — character identifier (left 1/3, top 1/4)."""
        L = get_menu_layout()
        p2 = L.equip_detail.panel2
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(L.fonts.NORMAL6 * scale)  # character name
        FS_SM = int(L.fonts.SMALL * scale) # HP numbers

        # ──── Panel box ────
        BOX_L = p2.BOX_L * scale
        BOX_R = p2.BOX_R * scale
        BOX_B = p2.BOX_B * scale
        BOX_T = p2.BOX_T * scale

        # ──── Elements ────
        SPRITE_X = p2.SPRITE_X * scale
        SPRITE_Y = p2.SPRITE_Y * scale
        TEXT_X = p2.TEXT_X * scale
        NAME_Y = p2.NAME_Y * scale
        HP_CUR_Y = p2.HP_CUR_Y * scale
        HP_MAX_Y = p2.HP_MAX_Y * scale

        # ════════════════════════ DRAW ════════════════════════
        member = self._member
        self.draw_box(BOX_L, BOX_R, BOX_B, BOX_T, scale)
        _sprite_atlas.draw(f"{member.name.lower()}_dn_{self._anim_frame}", SPRITE_X, SPRITE_Y, scale)
        self.draw_text(member.name, TEXT_X, NAME_Y, COLORS["text"], FS)
        self.draw_text(f"HP{member.hp:4d}/", TEXT_X, HP_CUR_Y, COLORS["text"], FS_SM)
        self.draw_text(f"  {member.hp_max:4d}", TEXT_X, HP_MAX_Y, COLORS["text"], FS_SM)

    def _draw_panel3_equipped(self, scale):
        """Panel 3 — currently equipped slots (right 2/3, full height)."""
        L = get_menu_layout()
        p3 = L.equip_detail.panel3
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(L.fonts.NORMAL6 * scale)    # slot name
        FS_SM = int(L.fonts.SMALL * scale)   # equipped item name

        # ──── Panel box ────
        BOX_L = p3.BOX_L * scale
        BOX_R = p3.BOX_R * scale
        BOX_B = p3.BOX_B * scale
        BOX_T = p3.BOX_T * scale

        # ──── Slot rows ────
        ROW_1 = p3.ROW_1 * scale
        ROW_GAP = p3.ROW_GAP * scale
        CURSOR_X = p3.CURSOR_X * scale
        TEXT_X = p3.TEXT_X * scale
        NAME_Y_OFF = p3.NAME_Y_OFF * scale
        ITEM_Y_OFF = p3.ITEM_Y_OFF * scale

        # ════════════════════════ DRAW ════════════════════════
        member = self._member
        self.draw_box(BOX_L, BOX_R, BOX_B, BOX_T, scale)
        for i, slot_name in enumerate(self.slots):
            y = ROW_1 - i * ROW_GAP
            slot_key = self.slot_keys[i]
            curr_id = getattr(member, slot_key)
            curr_item = get_item(curr_id)
            curr_name = curr_item["name"] if curr_item else "None"
            if self.phase == "slots":
                c = COLORS["cursor"] if i == self.selection else COLORS["text"]
                if i == self.selection:
                    draw_cursor(CURSOR_X, y, scale, COLORS["cursor"])
            else:
                c = COLORS["text"]
            self.draw_text(f"{slot_name}:", TEXT_X, y + NAME_Y_OFF, c, FS)
            self.draw_text(curr_name, TEXT_X, y + ITEM_Y_OFF,
                           COLORS["text"], FS_SM)

    def _draw_items_overlay(self, scale):
        """Floating overlay — equipable item list (on top of panel 3)."""
        L = get_menu_layout()
        ol = L.equip_detail.overlay
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(L.fonts.NORMAL6 * scale)    # header (slot name)
        FS_SM = int(L.fonts.SMALL5 * scale)  # item name + bonuses

        # ──── Floating box (inset) ────
        BOX_L = ol.BOX_L * scale
        BOX_R = ol.BOX_R * scale
        BOX_B = ol.BOX_B * scale
        BOX_T = ol.BOX_T * scale
        OVERLAY_FILL = (248, 248, 248)

        # ──── Header (slot name) ────
        HEADER_X = ol.HEADER_X * scale
        HEADER_Y = ol.HEADER_Y * scale

        # ──── Item rows ────
        ROW_1 = ol.ROW_1 * scale
        ROW_GAP = ol.ROW_GAP * scale
        MAX_VISIBLE = ol.MAX_VISIBLE
        CURSOR_X = ol.CURSOR_X * scale
        TEXT_X = ol.TEXT_X * scale

        # ════════════════════════ DRAW ════════════════════════
        self.draw_box(BOX_L, BOX_R, BOX_B, BOX_T, scale, fill=OVERLAY_FILL)
        # Draw header
        slot_name = self.slots[self.selection]
        self.draw_text(f"Equip {slot_name}:", HEADER_X, HEADER_Y, COLORS["text"], FS)

        items = self._equip_items()
        if not items:
            return
        visible = min(len(items), MAX_VISIBLE)
        for i in range(visible):
            entry = items[i]
            item_def = get_item(entry["id"])
            if not item_def:
                continue
            y = ROW_1 - i * ROW_GAP
            c = COLORS["cursor"] if i == self.selection else COLORS["text"]
            if i == self.selection:
                draw_cursor(CURSOR_X, y, scale, COLORS["cursor"])
            parts = []
            if item_def.get("atk"):
                parts.append(f"ATK+{item_def['atk']}")
            if item_def.get("def"):
                parts.append(f"DEF+{item_def['def']}")
            if item_def.get("mag"):
                parts.append(f"MAG+{item_def['mag']}")
            stat_str = " ".join(parts)
            self.draw_text(f"{item_def['name']} {stat_str}", TEXT_X, y, c, FS_SM)

    def draw(self, w, h, scale):
        L = get_menu_layout()
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS_HELP = int(L.fonts.SMALL5 * scale)
        HELP_COLOR = (150, 150, 150)

        # ──── Help text ────
        HELP_X = L.equip_detail.HELP_X * scale
        HELP_Y = L.equip_detail.HELP_Y * scale

        # ════════════════════════ DRAW ════════════════════════
        # Draw order: Panel 1 → Panel 2 → Panel 3 → Items overlay (front)
        self._draw_panel1_stats(scale)
        self._draw_panel2_identity(scale)
        self._draw_panel3_equipped(scale)
        if self.phase == "items":
            self._draw_items_overlay(scale)


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
        L = get_menu_layout()

        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(L.fonts.NORMAL7 * scale)      # slot name
        FS2 = int(L.fonts.NORMAL6 * scale)     # play time text
        FS_TITLE = int(L.fonts.TITLE8 * scale) # "SAVE GAME" title
        FS_HELP = int(L.fonts.SMALL5 * scale)  # help text
        HELP_COLOR = (150, 150, 150)

        # ──── Title ────
        TITLE_X = L.save.TITLE_X * scale
        TITLE_Y = L.save.TITLE_Y * scale

        # ──── Slots ────
        SCREEN_L = L.save.SCREEN_L * scale
        SCREEN_R = L.save.SCREEN_R * scale
        SLOT_HEIGHTS = list(L.save.SLOT_HEIGHTS)
        TEXT_INDENT = L.save.TEXT_INDENT * scale

        # ──── Help text ────
        HELP_X = L.save.HELP_X * scale
        HELP_Y = L.save.HELP_Y * scale

        # ════════════════════════ DRAW ════════════════════════
        title_t = self.text(
            "save_title", "SAVE GAME",
            TITLE_X, TITLE_Y, COLORS["text"], FS_TITLE,
            anchor_x="center", anchor_y="center",
        )
        title_t.draw()

        slot_top = 0
        for i in range(3):
            sh = SLOT_HEIGHTS[i] * scale
            tb = slot_top * scale
            tt = tb + sh
            slot_top += SLOT_HEIGHTS[i]

            border = COLORS["cursor"] if i == self.selection else COLORS["box_border"]
            self.draw_box(SCREEN_L, SCREEN_R, int(tb), int(tt), scale, border=border)

            cy = int((tb + tt) // 2)
            exists = any(s["slot"] == i for s in self._saves)
            if exists:
                for s in self._saves:
                    if s["slot"] == i:
                        self.draw_text(f"Slot {i + 1}: {s['name']}", TEXT_INDENT,
                                       cy + 6 * scale, COLORS["text"], FS)
                        self.draw_text(f"Play Time: {int(s['play_time'])}s",
                                       TEXT_INDENT, cy - 7 * scale,
                                       COLORS["text"], FS2)
                        break
            else:
                self.draw_text(f"Slot {i + 1}: [Empty]", TEXT_INDENT, cy,
                               COLORS["text"], FS)

        help_t = self.text(
            "save_help", "[Z] Save  [X] Back",
            HELP_X, HELP_Y, HELP_COLOR, FS_HELP,
            anchor_x="center", anchor_y="center",
        )
        help_t.draw()
