from abc import ABC, abstractmethod
from pyglet.window import key
from game.engine import get_item
from game.ui import COLORS, draw_cursor


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


class MainMenuState(MenuState):
    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0
        self.options = ["STATUS", "ITEMS", "MAGIC", "EQUIP", "SAVE", "LOAD"]

    def update(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.options)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.options)
        elif inp.is_just_pressed(key.Z):
            self.menu.set_state(self.options[self.selection].lower())
        elif inp.is_just_pressed(key.X):
            self.engine.set_scene("overworld")

    def draw(self, w, h, scale):
        box_w = 80 * scale
        box_h = 80 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        font_size = int(8 * scale)
        for i, opt in enumerate(self.options):
            y = box_y + box_h // 2 + (2 - i) * 12 * scale
            color = COLORS["cursor"] if i == self.selection else COLORS["text"]
            self.draw_text(opt, box_x + 12 * scale, y, color, font_size)
            if i == self.selection:
                draw_cursor(box_x + 4 * scale, y, scale)
        self.draw_text(f"GP: {self.engine.gold}", box_x + 8 * scale, box_y + 8 * scale, (255, 215, 0), font_size)


class StatusMenuState(MenuState):
    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0

    def update(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.party)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.party)
        elif inp.is_just_pressed(key.Z):
            self.menu.set_state("status_char", char_idx=self.selection)
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def draw(self, w, h, scale):
        box_w = 100 * scale
        box_h = 90 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        font_size = int(6 * scale)
        self.draw_text("STATUS", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        for i, member in enumerate(self.party):
            y = box_y + box_h - 28 * scale - i * 16 * scale
            color = COLORS["cursor"] if i == self.selection else (150, 150, 150)
            alive = member.hp > 0
            if not alive:
                color = (100, 100, 100)
            if i == self.selection:
                draw_cursor(box_x + 8 * scale, y, scale)
            self.draw_text(f"{member.name}  LV{member.lvl}", box_x + 16 * scale, y, color, font_size)
            self.draw_text(f"HP {member.hp}/{member.hp_max}", box_x + box_w - 24 * scale, y, (0, 200, 0) if alive else (100, 100, 100), font_size)
        self.draw_text("[Z] Select  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)


class StatusCharMenuState(MenuState):
    def __init__(self, menu, char_idx=0):
        super().__init__(menu)
        self.char_idx = char_idx

    def update(self, inp):
        if inp.is_just_pressed(key.X):
            self.menu.set_state("status")

    def draw(self, w, h, scale):
        member = self.party[self.char_idx]
        self.draw_box(16 * scale, w - 16 * scale, 16 * scale, h - 16 * scale, scale)
        font_size = int(6 * scale)
        self.draw_text(member.name, 24 * scale, h - 24 * scale, COLORS["text"], int(8 * scale))
        self.draw_text(f"LV{member.lvl}  EXP {member.exp}/{member.exp_next}", 24 * scale, h - 36 * scale, (150, 150, 150), font_size)
        self.draw_text(f"HP  {member.hp:4d}/{member.hp_max:4d}   MP  {member.mp:4d}/{member.mp_max:4d}", 24 * scale, h - 48 * scale, COLORS["text"], font_size)
        self.draw_text(f"ATK {member.atk:4d}   DEF {member.def_:4d}   MAG {member.mag:4d}", 24 * scale, h - 60 * scale, COLORS["text"], font_size)
        wpn = get_item(member.weapon) or {}
        arm = get_item(member.armor) or {}
        helm = get_item(member.helm) or {}
        shld = get_item(member.shield) or {}
        self.draw_text(f"WEAPON: {wpn.get('name', 'None'):20s}  ARMOR: {arm.get('name', 'None')}", 24 * scale, h - 76 * scale, COLORS["cursor"], font_size)
        self.draw_text(f"HELM: {helm.get('name', 'None'):20s}  SHIELD: {shld.get('name', 'None')}", 24 * scale, h - 88 * scale, COLORS["cursor"], font_size)
        spells = member.spells
        self.draw_text(f"SPELLS: {', '.join(spells) if spells else 'None'}", 24 * scale, h - 100 * scale, (100, 200, 255), font_size)
        self.draw_text("[X] Back", w // 2, 16 * scale, (150, 150, 150), int(5 * scale), center=True)


class ItemsMenuState(MenuState):
    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0

    def update(self, inp):
        items = self.engine.inventory
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
                self.menu.set_state("items_use", item_idx=self.selection)
            elif item_def:
                self.menu.set_state("main")
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def draw(self, w, h, scale):
        box_w = 140 * scale
        box_h = 100 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        self.draw_text("ITEMS", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        items = self.engine.inventory
        if not items:
            self.draw_text("No items", w // 2, h // 2, (150, 150, 150), int(8 * scale), center=True)
        else:
            font_size = int(6 * scale)
            for i, entry in enumerate(items[:6]):
                y = box_y + box_h - 28 * scale - i * 12 * scale
                color = COLORS["cursor"] if i == self.selection else COLORS["text"]
                item_def = get_item(entry["id"])
                name = item_def["name"] if item_def else entry["id"]
                if i == self.selection:
                    draw_cursor(box_x + 8 * scale, y, scale)
                self.draw_text(f"{name} x{entry['qty']}", box_x + 16 * scale, y, color, font_size)
                if item_def:
                    self.draw_text(item_def.get("description", ""), box_x + 70 * scale, y, (150, 150, 150), int(5 * scale))
        self.draw_text("[Z] Use  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)


class ItemsUseMenuState(MenuState):
    def __init__(self, menu, item_idx=0):
        super().__init__(menu)
        self.item_idx = item_idx
        self.selection = 0

    def _alive_indices(self):
        return [i for i, p in enumerate(self.party) if p.hp > 0]

    def update(self, inp):
        alive = self._alive_indices()
        if not alive:
            return
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(alive)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(alive)
        elif inp.is_just_pressed(key.Z):
            self._use_item(alive[self.selection])
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("items")

    def _use_item(self, target_idx):
        entry = self.engine.inventory[self.item_idx]
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
        self.menu.set_state("items")

    def draw(self, w, h, scale):
        entry = self.engine.inventory[self.item_idx]
        item_def = get_item(entry["id"])
        self.draw_box(16 * scale, w - 16 * scale, 16 * scale, h - 16 * scale, scale)
        self.draw_text(f"Use {item_def['name']}?", w // 2, h - 20 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        alive = self._alive_indices()
        for i, idx in enumerate(alive):
            member = self.party[idx]
            y = h - 36 * scale - i * 14 * scale
            color = COLORS["cursor"] if i == self.selection else (150, 150, 150)
            self.draw_text(f"{member.name}  HP {member.hp}/{member.hp_max}", 24 * scale, y, color, font_size)
        self.draw_text("[Z] Use  [X] Cancel", w // 2, 16 * scale, (150, 150, 150), int(5 * scale), center=True)


class MagicMenuState(MenuState):
    def __init__(self, menu):
        super().__init__(menu)
        self.caster_selection = 0
        self.spell_selection = 0
        self.selected_caster_idx = None
        self.phase = "select_caster"  # "select_caster" | "select_spell"

    def _caster_indices(self):
        return [i for i, p in enumerate(self.party) if p.spells]

    def update(self, inp):
        casters = self._caster_indices()
        if not casters:
            if inp.is_just_pressed(key.X):
                self.menu.set_state("main")
            return

        if self.phase == "select_caster":
            if inp.is_just_pressed(key.DOWN):
                self.caster_selection = (self.caster_selection + 1) % len(casters)
            elif inp.is_just_pressed(key.UP):
                self.caster_selection = (self.caster_selection - 1) % len(casters)
            elif inp.is_just_pressed(key.Z):
                idx = casters[self.caster_selection]
                if self.party[idx].spells:
                    self.selected_caster_idx = idx
                    self.spell_selection = 0
                    self.phase = "select_spell"
            elif inp.is_just_pressed(key.X):
                self.menu.set_state("main")

        elif self.phase == "select_spell":
            member = self.party[self.selected_caster_idx]
            spells = member.spells
            if inp.is_just_pressed(key.DOWN):
                self.spell_selection = (self.spell_selection + 1) % len(spells)
            elif inp.is_just_pressed(key.UP):
                self.spell_selection = (self.spell_selection - 1) % len(spells)
            elif inp.is_just_pressed(key.Z):
                # Future: implement spell casting from menu
                pass
            elif inp.is_just_pressed(key.X):
                self.phase = "select_caster"

    def draw(self, w, h, scale):
        box_w = 140 * scale
        box_h = 100 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        self.draw_text("MAGIC", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        casters = self._caster_indices()
        if not casters:
            self.draw_text("No spells available", w // 2, h // 2, (150, 150, 150), int(8 * scale), center=True)
        else:
            char_idx = casters[self.caster_selection]
            member = self.party[char_idx]
            self.draw_text(f"{member.name}  MP {member.mp}/{member.mp_max}", box_x + 16 * scale, box_y + box_h - 24 * scale, (100, 200, 255), font_size)
            spells = member.spells
            for i, sid in enumerate(spells[:5]):
                sdef = get_item(sid)
                name = sdef["name"] if sdef else sid
                mp_cost = sdef.get("mp_cost", 0) if sdef else 0
                y = box_y + box_h - 36 * scale - i * 12 * scale
                is_selected = self.phase == "select_spell" and i == self.spell_selection
                color = COLORS["cursor"] if is_selected else COLORS["text"]
                can_cast = member.mp >= mp_cost
                if not can_cast:
                    color = (80, 80, 80)
                if i == self.spell_selection and self.phase == "select_caster":
                    color = COLORS["cursor"]
                if is_selected:
                    draw_cursor(box_x + 12 * scale, y, scale)
                self.draw_text(f"{name}  MP-{mp_cost}", box_x + 20 * scale, y, color, font_size)
                if sdef:
                    self.draw_text(sdef.get("description", ""), box_x + 70 * scale, y, (150, 150, 150), int(5 * scale))
        self.draw_text("[Z] Select  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)


class EquipMenuState(MenuState):
    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0

    def update(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.party)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.party)
        elif inp.is_just_pressed(key.Z):
            self.menu.set_state("equip_slot", char_idx=self.selection)
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def draw(self, w, h, scale):
        box_w = 120 * scale
        box_h = 80 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        self.draw_text("EQUIP", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        for i, member in enumerate(self.party):
            y = box_y + box_h - 28 * scale - i * 16 * scale
            color = COLORS["cursor"] if i == self.selection else (150, 150, 150)
            if i == self.selection:
                draw_cursor(box_x + 8 * scale, y, scale)
            self.draw_text(f"{member.name}", box_x + 16 * scale, y, color, font_size)
            wpn = get_item(member.weapon)
            arm = get_item(member.armor)
            self.draw_text(f"W:{wpn['name'] if wpn else 'None'}  A:{arm['name'] if arm else 'None'}", box_x + 16 * scale, y - 8 * scale, (150, 150, 150), font_size)
        self.draw_text("[Z] Select  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)


class EquipSlotMenuState(MenuState):
    def __init__(self, menu, char_idx=0):
        super().__init__(menu)
        self.char_idx = char_idx
        self.selection = 0
        self.slots = ["WEAPON", "ARMOR", "HELM", "SHIELD"]
        self.slot_keys = ["weapon", "armor", "helm", "shield"]

    def update(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.slots)
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.slots)
        elif inp.is_just_pressed(key.Z):
            self.menu.set_state("equip_item", char_idx=self.char_idx, slot_idx=self.selection)
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("equip")

    def draw(self, w, h, scale):
        member = self.party[self.char_idx]
        box_w = 100 * scale
        box_h = 80 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        self.draw_text(f"Equip: {member.name}", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        for i, slot_name in enumerate(self.slots):
            y = box_y + box_h - 28 * scale - i * 14 * scale
            color = COLORS["cursor"] if i == self.selection else COLORS["text"]
            if i == self.selection:
                draw_cursor(box_x + 8 * scale, y, scale)
            curr = getattr(member, self.slot_keys[i])
            self.draw_text(f"{slot_name}: {curr['name'] if curr else 'None'}", box_x + 16 * scale, y, color, font_size)
        self.draw_text("[Z] Change  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)


class SaveMenuState(MenuState):
    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0

    def update(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % 5
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % 5
        elif inp.is_just_pressed(key.Z):
            self._do_save()
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def _do_save(self):
        from game.save import save_game
        name = f"Slot {self.selection + 1}"
        state = self.engine.get_state()
        save_game(self.selection, name, state, int(self.engine.play_time))
        self.menu.set_state("main")

    def draw(self, w, h, scale):
        box_w = 100 * scale
        box_h = 100 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        self.draw_text("SAVE GAME", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        from game.save import get_all_saves
        saves = get_all_saves()
        for i in range(4):
            exists = any(s["slot"] == i for s in saves)
            y = box_y + box_h - 28 * scale - i * 14 * scale
            color = COLORS["cursor"] if i == self.selection else (150, 150, 150)
            if i == self.selection:
                draw_cursor(box_x + 8 * scale, y, scale)
            if exists:
                for s in saves:
                    if s["slot"] == i:
                        self.draw_text(f"Slot {i + 1}: {s['name']}", box_x + 16 * scale, y, color, font_size)
                        self.draw_text(f"Play: {int(s['play_time'])}s", box_x + box_w - 16 * scale, y, (150, 150, 150), int(5 * scale))
                        break
            else:
                self.draw_text(f"Slot {i + 1}: [Empty]", box_x + 16 * scale, y, color, font_size)
        self.draw_text("[Z] Save  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)


class LoadMenuState(MenuState):
    def __init__(self, menu):
        super().__init__(menu)
        self.selection = 0

    def update(self, inp):
        if inp.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % 5
        elif inp.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % 5
        elif inp.is_just_pressed(key.Z):
            self._do_load()
        elif inp.is_just_pressed(key.X):
            self.menu.set_state("main")

    def _do_load(self):
        from game.save import load_game
        data = load_game(self.selection)
        if data:
            self.engine.load_state(data["game_state"])
            self.engine.set_scene("overworld")

    def draw(self, w, h, scale):
        self.draw_box(16 * scale, w - 16 * scale, 16 * scale, h - 16 * scale, scale)
        self.draw_text("LOAD GAME", w // 2, h - 20 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        from game.save import get_all_saves
        saves = get_all_saves()
        for i in range(5):
            exists = any(s["slot"] == i for s in saves)
            y = h - 40 * scale - i * 16 * scale
            color = COLORS["cursor"] if i == self.selection and exists else (150, 150, 150)
            if i == self.selection and exists:
                draw_cursor(20 * scale, y, scale)
            if exists:
                for s in saves:
                    if s["slot"] == i:
                        self.draw_text(f"Slot {i + 1}: {s['name']}", 24 * scale, y, color, font_size)
                        self.draw_text(f"Play: {int(s['play_time'])}s", 130 * scale, y, (150, 150, 150), int(5 * scale))
                        break
            else:
                self.draw_text(f"Slot {i + 1}: [Empty]", 24 * scale, y, color, font_size)
        self.draw_text("[Z] Load  [X] Back", w // 2, 16 * scale, (150, 150, 150), int(5 * scale), center=True)
