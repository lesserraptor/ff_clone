import arcade
from game.input import UP, DOWN, LEFT, RIGHT, Z, X
from game.engine import register_scene, get_item
from game.text import create_text
from game.ui import COLORS, draw_window, draw_cursor


@register_scene("menu")
class MenuScene:
    def __init__(self, engine):
        self.engine = engine
        self.state = "main"
        self.sel_main = 0
        self.main_options = ["STATUS", "ITEMS", "MAGIC", "EQUIP", "SAVE", "LOAD"]
        self._prev_scale = 0
        self._text_cache = {}

    def _get_text(self, key, text, x, y, color, size, anchor_x="left", anchor_y="center"):
        scale = self.engine.get_scale()
        if scale not in self._text_cache:
            self._text_cache[scale] = {}
        cache = self._text_cache[scale]
        if key not in cache:
            cache[key] = create_text(text, x, y, color, size, anchor_x=anchor_x, anchor_y=anchor_y)
        else:
            cache[key].text = text
            cache[key].color = color
            cache[key].x = x
            cache[key].y = y
        return cache[key]

    def invalidate_cache(self):
        self._text_cache = {}

    def update(self, delta_time):
        inpt = self.engine.input
        if self.state == "main":
            self.update_main(inpt)
        elif self.state == "status":
            self.update_status(inpt)
        elif self.state == "status_char":
            self.update_status_char(inpt)
        elif self.state == "items":
            self.update_items(inpt)
        elif self.state == "items_use":
            self.update_items_use(inpt)
        elif self.state == "magic":
            self.update_magic(inpt)
        elif self.state == "magic_cast":
            self.update_magic_cast(inpt)
        elif self.state == "equip":
            self.update_equip(inpt)
        elif self.state == "equip_slot":
            self.update_equip_slot(inpt)
        elif self.state == "save":
            self.update_save(inpt)
        elif self.state == "load":
            self.update_load(inpt)

    def update_main(self, inpt):
        if inpt.is_just_pressed(DOWN):
            self.sel_main = (self.sel_main + 1) % len(self.main_options)
        elif inpt.is_just_pressed(UP):
            self.sel_main = (self.sel_main - 1) % len(self.main_options)
        elif inpt.is_just_pressed(Z):
            self.enter_submenu(self.main_options[self.sel_main])
        elif inpt.is_just_pressed(X):
            self.engine.set_scene("overworld")

    def enter_submenu(self, name):
        self.state = name.lower()
        self.invalidate_cache()
        if name == "STATUS":
            self.sel_char = 0
        elif name == "ITEMS":
            self.sel_item = 0
        elif name == "MAGIC":
            self.sel_char = 0
            self.sel_spell = 0
        elif name == "EQUIP":
            self.sel_char = 0
            self.sel_slot = 0
        elif name == "SAVE":
            self.sel_slot = 0
        elif name == "LOAD":
            self.sel_slot = 0

    def update_status(self, inpt):
        if inpt.is_just_pressed(DOWN):
            self.sel_char = (self.sel_char + 1) % len(self.engine.party)
        elif inpt.is_just_pressed(UP):
            self.sel_char = (self.sel_char - 1) % len(self.engine.party)
        elif inpt.is_just_pressed(Z):
            self.state = "status_char"
        elif inpt.is_just_pressed(X):
            self.state = "main"
            self.invalidate_cache()

    def update_status_char(self, inpt):
        if inpt.is_just_pressed(X):
            self.state = "status"
            self.invalidate_cache()

    def update_items(self, inpt):
        items = self.engine.inventory
        if not items:
            if inpt.is_just_pressed(X):
                self.state = "main"
                self.invalidate_cache()
            return
        if inpt.is_just_pressed(DOWN):
            self.sel_item = (self.sel_item + 1) % len(items)
        elif inpt.is_just_pressed(UP):
            self.sel_item = (self.sel_item - 1) % len(items)
        elif inpt.is_just_pressed(Z):
            entry = items[self.sel_item]
            item_def = get_item(entry["id"])
            if item_def and item_def.get("type") == "consumable":
                self.state = "items_use"
                self.sel_target = 0
                self.invalidate_cache()
            elif item_def:
                self.state = "main"
                self.invalidate_cache()
        elif inpt.is_just_pressed(X):
            self.state = "main"
            self.invalidate_cache()

    def update_items_use(self, inpt):
        party = self.engine.party
        alive = [i for i, p in enumerate(party) if p["hp"] > 0]
        if not alive:
            return
        if inpt.is_just_pressed(DOWN):
            self.sel_target = (self.sel_target + 1) % len(alive)
        elif inpt.is_just_pressed(UP):
            self.sel_target = (self.sel_target - 1) % len(alive)
        elif inpt.is_just_pressed(Z):
            self.use_item(self.sel_item, alive[self.sel_target])
        elif inpt.is_just_pressed(X):
            self.state = "items"
            self.invalidate_cache()

    def use_item(self, item_idx, target_idx):
        entry = self.engine.inventory[item_idx]
        item_def = get_item(entry["id"])
        if not item_def:
            return
        effect = item_def.get("effect")
        target = self.engine.party[target_idx]
        if effect == "heal":
            target["hp"] = min(target["hp_max"], target["hp"] + item_def["value"])
        elif effect == "mana":
            target["mp"] = min(target["mp_max"], target["mp"] + item_def["value"])
        elif effect == "revive":
            target["hp"] = item_def["value"]
            target["alive"] = True
        elif effect == "restore_all":
            target["hp"] = target["hp_max"]
            target["mp"] = target["mp_max"]
        elif effect == "full_restore":
            target["hp"] = target["hp_max"]
            target["mp"] = target["mp_max"]
            target["status"] = []
        elif effect == "cure_status":
            if target.get("status") and item_def["value"] in target["status"]:
                target["status"].remove(item_def["value"])
        self.engine.remove_item(entry["id"])
        self.state = "items"
        self.invalidate_cache()

    def update_magic(self, inpt):
        party = self.engine.party
        casters = [i for i, p in enumerate(party) if p.get("spells")]
        if not casters:
            if inpt.is_just_pressed(X):
                self.state = "main"
                self.invalidate_cache()
            return
        if inpt.is_just_pressed(DOWN):
            self.sel_char = (self.sel_char + 1) % len(casters)
        elif inpt.is_just_pressed(UP):
            self.sel_char = (self.sel_char - 1) % len(casters)
        elif inpt.is_just_pressed(Z):
            char_idx = casters[self.sel_char]
            spells = party[char_idx].get("spells", [])
            if spells:
                self.sel_char_idx = char_idx
                self.sel_spell = 0
                self.state = "magic_select"
                self.invalidate_cache()
        elif inpt.is_just_pressed(X):
            self.state = "main"
            self.invalidate_cache()

    def update_magic_cast(self, inpt):
        pass

    def update_equip(self, inpt):
        party = self.engine.party
        if inpt.is_just_pressed(DOWN):
            self.sel_char = (self.sel_char + 1) % len(party)
        elif inpt.is_just_pressed(UP):
            self.sel_char = (self.sel_char - 1) % len(party)
        elif inpt.is_just_pressed(Z):
            self.state = "equip_slot"
            self.sel_slot = 0
            self.invalidate_cache()
        elif inpt.is_just_pressed(X):
            self.state = "main"
            self.invalidate_cache()

    def update_equip_slot(self, inpt):
        slots = ["weapon", "armor", "helm", "shield"]
        if inpt.is_just_pressed(DOWN):
            self.sel_slot = (self.sel_slot + 1) % len(slots)
        elif inpt.is_just_pressed(UP):
            self.sel_slot = (self.sel_slot - 1) % len(slots)
        elif inpt.is_just_pressed(Z):
            self.state = "equip_item"
            self.sel_equip_item = 0
            self.invalidate_cache()
        elif inpt.is_just_pressed(X):
            self.state = "equip"
            self.invalidate_cache()

    def update_save(self, inpt):
        if inpt.is_just_pressed(DOWN):
            self.sel_slot = (self.sel_slot + 1) % 5
        elif inpt.is_just_pressed(UP):
            self.sel_slot = (self.sel_slot - 1) % 5
        elif inpt.is_just_pressed(Z):
            self.do_save()
        elif inpt.is_just_pressed(X):
            self.state = "main"
            self.invalidate_cache()

    def update_load(self, inpt):
        if inpt.is_just_pressed(DOWN):
            self.sel_slot = (self.sel_slot + 1) % 5
        elif inpt.is_just_pressed(UP):
            self.sel_slot = (self.sel_slot - 1) % 5
        elif inpt.is_just_pressed(Z):
            self.do_load()
        elif inpt.is_just_pressed(X):
            self.state = "main"
            self.invalidate_cache()

    def do_save(self):
        from game.save import save_game
        import time
        name = f"Slot {self.sel_slot + 1}"
        state = self.engine.get_state()
        save_game(self.sel_slot, name, state, int(self.engine.play_time))
        self.state = "main"
        self.invalidate_cache()

    def do_load(self):
        from game.save import load_game
        data = load_game(self.sel_slot)
        if data:
            self.engine.load_state(data["game_state"])
            self.engine.set_scene("overworld")

    def draw(self):
        w, h = self.engine.get_size()
        scale = self.engine.get_scale()

        arcade.draw_lrbt_rectangle_filled(0, w, 0, h, (0, 0, 50))

        if self.state == "main":
            self.draw_main(w, h, scale)
        elif self.state == "status":
            self.draw_status(w, h, scale)
        elif self.state == "status_char":
            self.draw_status_char(w, h, scale)
        elif self.state == "items":
            self.draw_items(w, h, scale)
        elif self.state == "items_use":
            self.draw_items_use(w, h, scale)
        elif self.state in ("magic", "magic_select"):
            self.draw_magic(w, h, scale)
        elif self.state == "equip":
            self.draw_equip(w, h, scale)
        elif self.state == "equip_slot":
            self.draw_equip_slot(w, h, scale)
        elif self.state == "save":
            self.draw_save(w, h, scale)
        elif self.state == "load":
            self.draw_load(w, h, scale)

        self._prev_scale = scale

    def draw_main(self, w, h, scale):
        box_w = 80 * scale
        box_h = 80 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        font_size = int(8 * scale)
        for i, opt in enumerate(self.main_options):
            y = box_y + box_h // 2 + (2 - i) * 12 * scale
            color = COLORS["cursor"] if i == self.sel_main else COLORS["text"]
            self.draw_text(opt, box_x + 12 * scale, y, color, font_size)
            if i == self.sel_main:
                draw_cursor(box_x + 4 * scale, y, scale)
        self.draw_text(f"GP: {self.engine.gold}", box_x + 8 * scale, box_y + 8 * scale, (255, 215, 0), font_size)

    def draw_status(self, w, h, scale):
        box_w = 100 * scale
        box_h = 90 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        font_size = int(6 * scale)
        self.draw_text("STATUS", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        for i, member in enumerate(self.engine.party):
            y = box_y + box_h - 28 * scale - i * 16 * scale
            color = COLORS["cursor"] if i == self.sel_char else (150, 150, 150)
            alive = member.get("hp", 0) > 0
            if not alive:
                color = (100, 100, 100)
            if i == self.sel_char:
                draw_cursor(box_x + 8 * scale, y, scale)
            self.draw_text(f"{member['name']}  LV{member.get('lvl', 1)}", box_x + 16 * scale, y, color, font_size)
            self.draw_text(f"HP {member.get('hp', 0)}/{member.get('hp_max', 0)}", box_x + box_w - 24 * scale, y, (0, 200, 0) if alive else (100, 100, 100), font_size)
        self.draw_text("[Z] Select  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)

    def draw_status_char(self, w, h, scale):
        member = self.engine.party[self.sel_char]
        self.draw_box(16 * scale, w - 16 * scale, 16 * scale, h - 16 * scale, scale)
        font_size = int(6 * scale)
        self.draw_text(member["name"], 24 * scale, h - 24 * scale, COLORS["text"], int(8 * scale))
        self.draw_text(f"LV{member.get('lvl', 1)}  EXP {member.get('exp', 0)}/{member.get('exp_next', 100)}", 24 * scale, h - 36 * scale, (150, 150, 150), font_size)
        self.draw_text(f"HP  {member.get('hp', 0):4d}/{member.get('hp_max', 0):4d}   MP  {member.get('mp', 0):4d}/{member.get('mp_max', 0):4d}", 24 * scale, h - 48 * scale, COLORS["text"], font_size)
        self.draw_text(f"ATK {member.get('atk', 0):4d}   DEF {member.get('def', 0):4d}   MAG {member.get('mag', 0):4d}", 24 * scale, h - 60 * scale, COLORS["text"], font_size)
        wpn = get_item(member.get("weapon")) or {}
        arm = get_item(member.get("armor")) or {}
        helm = get_item(member.get("helm")) or {}
        shld = get_item(member.get("shield")) or {}
        self.draw_text(f"WEAPON: {wpn.get('name', 'None'):20s}  ARMOR: {arm.get('name', 'None')}", 24 * scale, h - 76 * scale, COLORS["cursor"], font_size)
        self.draw_text(f"HELM: {helm.get('name', 'None'):20s}  SHIELD: {shld.get('name', 'None')}", 24 * scale, h - 88 * scale, COLORS["cursor"], font_size)
        spells = member.get("spells", [])
        self.draw_text(f"SPELLS: {', '.join(spells) if spells else 'None'}", 24 * scale, h - 100 * scale, (100, 200, 255), font_size)
        self.draw_text("[X] Back", w // 2, 16 * scale, (150, 150, 150), int(5 * scale), center=True)

    def draw_items(self, w, h, scale):
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
                color = COLORS["cursor"] if i == self.sel_item else COLORS["text"]
                item_def = get_item(entry["id"])
                name = item_def["name"] if item_def else entry["id"]
                if i == self.sel_item:
                    draw_cursor(box_x + 8 * scale, y, scale)
                self.draw_text(f"{name} x{entry['qty']}", box_x + 16 * scale, y, color, font_size)
                if item_def:
                    self.draw_text(item_def.get("description", ""), box_x + 70 * scale, y, (150, 150, 150), int(5 * scale))
        self.draw_text("[Z] Use  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)

    def draw_items_use(self, w, h, scale):
        entry = self.engine.inventory[self.sel_item]
        item_def = get_item(entry["id"])
        self.draw_box(16 * scale, w - 16 * scale, 16 * scale, h - 16 * scale, scale)
        self.draw_text(f"Use {item_def['name']}?", w // 2, h - 20 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        party = self.engine.party
        for i, member in enumerate(party):
            y = h - 36 * scale - i * 14 * scale
            alive = member.get("hp", 0) > 0
            color = COLORS["cursor"] if i == self.sel_target and alive else (150, 150, 150)
            self.draw_text(f"{member['name']}  HP {member.get('hp', 0)}/{member.get('hp_max', 0)}", 24 * scale, y, color, font_size)
        self.draw_text("[Z] Use  [X] Cancel", w // 2, 16 * scale, (150, 150, 150), int(5 * scale), center=True)

    def draw_magic(self, w, h, scale):
        box_w = 140 * scale
        box_h = 100 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        self.draw_text("MAGIC", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        casters = [i for i, p in enumerate(self.engine.party) if p.get("spells")]
        if not casters:
            self.draw_text("No spells available", w // 2, h // 2, (150, 150, 150), int(8 * scale), center=True)
        else:
            char_idx = casters[self.sel_char]
            member = self.engine.party[char_idx]
            self.draw_text(f"{member['name']}  MP {member.get('mp', 0)}/{member.get('mp_max', 0)}", box_x + 16 * scale, box_y + box_h - 24 * scale, (100, 200, 255), font_size)
            spells = member.get("spells", [])
            for i, sid in enumerate(spells[:5]):
                sdef = get_item(sid)
                name = sdef["name"] if sdef else sid
                mp_cost = sdef.get("mp_cost", 0) if sdef else 0
                y = box_y + box_h - 36 * scale - i * 12 * scale
                color = COLORS["cursor"] if i == self.sel_spell else COLORS["text"]
                can_cast = member.get("mp", 0) >= mp_cost
                if not can_cast:
                    color = (80, 80, 80)
                if i == self.sel_spell:
                    draw_cursor(box_x + 12 * scale, y, scale)
                self.draw_text(f"{name}  MP-{mp_cost}", box_x + 20 * scale, y, color, font_size)
                if sdef:
                    self.draw_text(sdef.get("description", ""), box_x + 70 * scale, y, (150, 150, 150), int(5 * scale))
        self.draw_text("[Z] Select  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)

    def draw_equip(self, w, h, scale):
        box_w = 120 * scale
        box_h = 80 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        self.draw_text("EQUIP", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        for i, member in enumerate(self.engine.party):
            y = box_y + box_h - 28 * scale - i * 16 * scale
            color = COLORS["cursor"] if i == self.sel_char else (150, 150, 150)
            if i == self.sel_char:
                draw_cursor(box_x + 8 * scale, y, scale)
            self.draw_text(f"{member['name']}", box_x + 16 * scale, y, color, font_size)
            wpn = get_item(member.get("weapon"))
            arm = get_item(member.get("armor"))
            self.draw_text(f"W:{wpn['name'] if wpn else 'None'}  A:{arm['name'] if arm else 'None'}", box_x + 16 * scale, y - 8 * scale, (150, 150, 150), font_size)
            self.draw_text("[Z] Select  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)

    def draw_equip_slot(self, w, h, scale):
        member = self.engine.party[self.sel_char]
        box_w = 100 * scale
        box_h = 80 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        self.draw_text(f"Equip: {member['name']}", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        slots = ["WEAPON", "ARMOR", "HELM", "SHIELD"]
        slot_keys = ["weapon", "armor", "helm", "shield"]
        font_size = int(6 * scale)
        for i, slot_name in enumerate(slots):
            y = box_y + box_h - 28 * scale - i * 14 * scale
            color = COLORS["cursor"] if i == self.sel_slot else COLORS["text"]
            if i == self.sel_slot:
                draw_cursor(box_x + 8 * scale, y, scale)
            curr = get_item(member.get(slot_keys[i]))
            self.draw_text(f"{slot_name}: {curr['name'] if curr else 'None'}", box_x + 16 * scale, y, color, font_size)
        self.draw_text("[Z] Change  [X] Back", w // 2, box_y + 12 * scale, (150, 150, 150), int(5 * scale), center=True)

    def draw_save(self, w, h, scale):
        box_w = 100 * scale
        box_h = 100 * scale
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2
        self.draw_box(box_x, box_x + box_w, box_y, box_y + box_h, scale)
        self.draw_text("SAVE GAME", w // 2, box_y + box_h - 12 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        from game.save import has_save, get_all_saves
        saves = get_all_saves()
        for i in range(4):
            exists = any(s["slot"] == i for s in saves)
            y = box_y + box_h - 28 * scale - i * 14 * scale
            color = COLORS["cursor"] if i == self.sel_slot else (150, 150, 150)
            if i == self.sel_slot:
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

    def draw_load(self, w, h, scale):
        self.draw_box(16 * scale, w - 16 * scale, 16 * scale, h - 16 * scale, scale)
        self.draw_text("LOAD GAME", w // 2, h - 20 * scale, COLORS["text"], int(8 * scale), center=True)
        font_size = int(6 * scale)
        from game.save import get_all_saves
        saves = get_all_saves()
        for i in range(5):
            exists = any(s["slot"] == i for s in saves)
            y = h - 40 * scale - i * 16 * scale
            color = COLORS["cursor"] if i == self.sel_slot and exists else (150, 150, 150)
            if i == self.sel_slot and exists:
                draw_cursor(20 * scale, y, scale)
            color = COLORS["cursor"] if i == self.sel_slot and exists else (150, 150, 150)
            if exists:
                for s in saves:
                    if s["slot"] == i:
                        self.draw_text(f"Slot {i + 1}: {s['name']}", 24 * scale, y, color, font_size)
                        self.draw_text(f"Play: {int(s['play_time'])}s", 130 * scale, y, (150, 150, 150), int(5 * scale))
                        break
            else:
                self.draw_text(f"Slot {i + 1}: [Empty]", 24 * scale, y, color, font_size)
        self.draw_text("[Z] Load  [X] Back", w // 2, 16 * scale, (150, 150, 150), int(5 * scale), center=True)

    def draw_box(self, l, r, b, t, scale, fill=(48, 48, 160), border=COLORS["box_border"]):
        draw_window(l, b, r - l, t - b, scale, fill, border)

    def draw_text(self, text, x, y, color, size, center=False, anchor_x="left"):
        if center:
            anchor_x = "center"
        t = self._get_text(f"{text[:8]}_{id(self)}", text, x, y, color, int(size), anchor_x=anchor_x, anchor_y="center")
        t.draw()