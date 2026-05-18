"""Menu sub-states for the GBC-style menu system."""

import time
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
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(7 * scale)        # menu option text
        FS2 = int(6 * scale)       # sub-text / stats
        FS_SM = int(5 * scale)     # HP/MP numbers

        # ──── Screen / panel dimensions ────
        SCREEN_W = 240 * scale     # full screen width
        SCREEN_H = 160 * scale     # full screen height
        MENU_W = 80 * scale        # left menu panel width
        MENU_L = 0 * scale         # left edge of menu panel
        PARTY_L = MENU_W           # left edge of party panel (= right edge of menu)
        GOLD_H = 30 * scale        # gold bar height
        GOLD_B = 0 * scale         # gold bar bottom

        # ──── Menu panel rows ────
        MENU_ROW_1 = 146 * scale   # first option Y
        MENU_ROW_GAP = 16 * scale  # vertical space between options

        # ──── Party panel rows ────
        PARTY_ROW_1 = 146 * scale  # first party member Y
        PARTY_ROW_GAP = 32 * scale # vertical space between members

        # ──── Party panel offsets ────
        SPRITE_X_OFF = 24 * scale  # sprite X offset from panel left
        NAME_X_OFF = 16 * scale    # name X offset from sprite (sprite_x + 16)
        HP_Y_OFF = -16 * scale     # Y offset from row for HP/MP area
        HP_CUR_Y_OFF = 5 * scale   # current HP number Y offset from hp_y
        HP_MAX_Y_OFF = -5 * scale  # max HP number Y offset from hp_y
        MP_COL_OFF = 64 * scale    # MP column X offset from name_x
        CURSOR_PARTY_OFF = 4 * scale  # cursor X offset from party_l

        # ──── Menu panel offsets ────
        TEXT_OFF = 12 * scale      # menu text X offset from left
        CURSOR_OFF = 4 * scale     # cursor X offset from left

        # ──── Gold bar ────
        GOLD_TEXT_CX = MENU_W // 2  # gold text center X
        GOLD_TEXT_CY = GOLD_H // 2  # gold text center Y

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
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(7 * scale)        # heading / overlay title text
        FS2 = int(6 * scale)       # item names / sub-text
        FS_SM = int(5 * scale)     # help text
        FS_TITLE = int(8 * scale)  # "ITEMS" title

        # ──── Items panel ────
        PANEL_L = 40 * scale       # left edge of items panel
        PANEL_R = 200 * scale      # right edge of items panel
        PANEL_B = 0 * scale        # bottom edge of items panel
        PANEL_T = 160 * scale      # top edge of items panel

        # ──── Title ────
        TITLE_X = 120 * scale      # title center X
        TITLE_Y = 152 * scale      # title Y

        # ──── Empty state ────
        EMPTY_X = 120 * scale      # "No items" center X
        EMPTY_Y = 80 * scale       # "No items" center Y
        EMPTY_COLOR = (150, 150, 150)

        # ──── Item rows ────
        ITEM_ROW_1 = 140 * scale   # first item Y
        ITEM_GAP = 17 * scale      # gap between items
        ITEM_CURSOR_OFF = 8 * scale   # cursor X offset from panel left
        ITEM_TEXT_OFF = 16 * scale    # text X offset from panel left
        ITEM_MAX_VISIBLE = 8       # max items shown

        # ──── Help text ────
        HELP_X = 120 * scale       # help text center X
        HELP_Y = 8 * scale         # help text Y
        HELP_COLOR = (150, 150, 150)

        # ──── Targeting overlay ────
        OL_L = 50 * scale          # overlay left edge
        OL_R = 190 * scale         # overlay right edge
        OL_B = 24 * scale          # overlay bottom
        OL_T = 120 * scale         # overlay top
        OL_TITLE_OFF = -10 * scale # overlay title Y offset from top (ol_t + offset)
        OL_FIRST_Y_OFF = -28 * scale  # first target Y offset from ol_t
        OL_TARGET_GAP = 18 * scale    # gap between target rows
        OL_CURSOR_OFF = 8 * scale     # cursor X offset from ol_l
        OL_NAME_OFF = 16 * scale      # name X offset from ol_l
        OL_HP_OFF = 64 * scale        # HP column X offset from ol_l
        OL_Y_ADJ = 3 * scale          # small Y adjustment for text alignment

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
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(7 * scale)        # names / level
        FS2 = int(6 * scale)       # stats
        FS_TITLE = int(8 * scale)  # "STATUS" title
        FS_SM = int(5 * scale)     # help text

        # ──── Panel dimensions ────
        PANEL_L = 4 * scale        # left edge of each member panel
        PANEL_R = 236 * scale      # right edge of each member panel
        PANEL_H = 34 * scale       # height of each member panel
        PANEL_GAP = 2 * scale      # gap between panels

        # ──── Title ────
        TITLE_X = 120 * scale      # title center X
        TITLE_Y = 155 * scale      # title Y

        # ──── First panel bottom ────
        FIRST_PB = 14 * scale      # first panel bottom edge

        # ──── Within each member panel ────
        SPRITE_OFF = 12 * scale    # sprite X offset from panel left
        SPRITE_Y_OFF = 2 * scale   # sprite Y offset above row center
        TEXT_X_OFF = 24 * scale    # name text X offset from panel left

        # ──── Row Y offsets from panel vertical center (row_cy) ────
        R1_OFF = 12 * scale        # row 1 (name / HP / ATK) — above center
        R2_OFF = 4 * scale         # row 2 (HP max / DEF)
        R3_OFF = -4 * scale        # row 3 (MP / MAG)
        R4_OFF = -12 * scale       # row 4 (MP max / SPD)

        # ──── Column X offsets from text start (tx) ────
        COL1_OFF = 64 * scale      # HP/MP column
        COL2_OFF = 124 * scale     # ATK/DEF/MAG/SPD column

        # ──── Help text ────
        HELP_X = 120 * scale       # help center X
        HELP_Y = 4 * scale         # help Y
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
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(7 * scale)        # character names
        FS2 = int(6 * scale)       # (unused currently)
        FS_SM = int(5 * scale)     # HP numbers
        FS_TITLE = int(8 * scale)  # title
        FS_HELP = int(5 * scale)   # help text

        # ──── Panel / screen dimensions ────
        SCREEN_R = 240 * scale     # right edge of full screen
        PARTY_L = 40 * scale       # left edge of party list panel
        PANEL_B = 0 * scale        # panel bottom
        PANEL_T = 150 * scale      # panel top (leaves room for help)

        # ──── Title ────
        TITLE_X = 120 * scale      # title center X
        TITLE_Y = 155 * scale      # title Y

        # ──── Party rows ────
        ROW_1 = 138 * scale        # first member Y
        ROW_GAP = 32 * scale       # gap between rows
        SPRITE_OFF = 24 * scale    # sprite X offset from party_l
        NAME_OFF = 16 * scale      # name X offset from sprite (sprite_x + 16)
        CURSOR_OFF = 4 * scale     # cursor X offset from party_l
        HP_Y_OFF = -16 * scale     # Y offset from row for HP area
        HP_CUR_OFF = 5 * scale     # current HP Y offset from hp_y
        HP_MAX_OFF = -5 * scale    # max HP Y offset from hp_y

        # ──── Help text ────
        HELP_X = 120 * scale       # help center X
        HELP_Y = 8 * scale         # help Y
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
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(6 * scale)        # stat label text

        # ──── Panel box ────
        BOX_L = 0 * scale          # left edge
        BOX_R = 120 * scale        # right edge
        BOX_B = 0 * scale          # bottom edge
        BOX_T = 120 * scale        # top edge

        # ──── Stat row positions ────
        TEXT_X = 8 * scale         # X offset for all stat text
        ROW_1_Y = 104 * scale      # STR row
        ROW_2_Y = 92 * scale       # DEF row
        ROW_3_Y = 80 * scale       # AGI row
        ROW_4_Y = 68 * scale       # MAG row

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
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(6 * scale)        # character name
        FS_SM = int(4 * scale)     # HP numbers

        # ──── Panel box ────
        BOX_L = 0 * scale          # left edge
        BOX_R = 80 * scale         # right edge
        BOX_B = 120 * scale        # bottom edge
        BOX_T = 160 * scale        # top edge

        # ──── Elements ────
        SPRITE_X = 16 * scale      # sprite X
        SPRITE_Y = 140 * scale     # sprite Y
        TEXT_X = 26 * scale        # name / HP text X
        NAME_Y = 150 * scale       # name / sprite Y
        HP_CUR_Y = 142 * scale     # current HP Y
        HP_MAX_Y = 134 * scale     # max HP Y

        # ════════════════════════ DRAW ════════════════════════
        member = self._member
        self.draw_box(BOX_L, BOX_R, BOX_B, BOX_T, scale)
        _sprite_atlas.draw(f"{member.name.lower()}_dn_{self._anim_frame}", SPRITE_X, SPRITE_Y, scale)
        self.draw_text(member.name, TEXT_X, NAME_Y, COLORS["text"], FS)
        self.draw_text(f"HP{member.hp:4d}/", TEXT_X, HP_CUR_Y, COLORS["text"], FS_SM)
        self.draw_text(f"  {member.hp_max:4d}", TEXT_X, HP_MAX_Y, COLORS["text"], FS_SM)

    def _draw_panel3_equipped(self, scale):
        """Panel 3 — currently equipped slots (right 2/3, full height)."""
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(6 * scale)        # slot name
        FS_SM = int(4 * scale)     # equipped item name

        # ──── Panel box ────
        BOX_L = 80 * scale         # left edge
        BOX_R = 240 * scale        # right edge
        BOX_B = 0 * scale          # bottom edge
        BOX_T = 160 * scale        # top edge — full height

        # ──── Slot rows ────
        ROW_1 = 148 * scale        # first slot Y (more room with full height)
        ROW_GAP = 22 * scale       # gap between slot rows
        CURSOR_X = 88 * scale      # cursor X
        TEXT_X = 96 * scale        # text X
        NAME_Y_OFF = 5 * scale     # slot name Y offset from row Y
        ITEM_Y_OFF = -5 * scale    # item name Y offset from row Y

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
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(6 * scale)        # header (slot name)
        FS_SM = int(5 * scale)     # item name + bonuses

        # ──── Floating box (inset) ────
        BOX_L = 84 * scale
        BOX_R = 238 * scale
        BOX_B = 16 * scale
        BOX_T = 152 * scale
        OVERLAY_FILL = (248, 248, 248)  # slightly lighter than panel (232,232,232)

        # ──── Header (slot name) ────
        HEADER_X = 92 * scale
        HEADER_Y = 144 * scale

        # ──── Item rows ────
        ROW_1 = 132 * scale
        ROW_GAP = 14 * scale
        MAX_VISIBLE = 8
        CURSOR_X = 92 * scale
        TEXT_X = 100 * scale

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
        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS_HELP = int(5 * scale)   # help text
        HELP_COLOR = (150, 150, 150)

        # ──── Help text ────
        HELP_X = 160 * scale       # help center X
        HELP_Y = 6 * scale         # help Y

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

        # ══════════════════════════ LAYOUT ══════════════════════════
        # ──── Font sizes ────
        FS = int(7 * scale)        # slot name
        FS2 = int(6 * scale)       # play time text
        FS_TITLE = int(8 * scale)  # "SAVE GAME" title
        FS_HELP = int(5 * scale)   # help text
        HELP_COLOR = (150, 150, 150)

        # ──── Title ────
        TITLE_X = 120 * scale      # title center X
        TITLE_Y = 155 * scale      # title Y

        # ──── Slots ────
        SCREEN_L = 0 * scale       # left edge of slots
        SCREEN_R = 240 * scale     # right edge of slots
        SLOT_HEIGHTS = [53, 54, 53]  # heights of the 3 slots (sum = 160)
        TEXT_INDENT = 16 * scale   # text X indent from slot left

        # ──── Help text ────
        HELP_X = 120 * scale       # help center X
        HELP_Y = 4 * scale         # help Y

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
