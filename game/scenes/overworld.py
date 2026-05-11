import json
import os
import random
import arcade
from game.input import UP, DOWN, LEFT, RIGHT, Z, X
from game.engine import register_scene
from game.text import create_text, draw_text
from game.ui import COLORS, draw_window


DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "maps.json")
ENEMIES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "enemies.json")


def load_maps():
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
    return data.get("tile_defs", {}), data.get("maps", {}), data.get("scripts", {})


def load_enemies():
    with open(ENEMIES_PATH, "r") as f:
        return json.load(f)


@register_scene("overworld")
class OverworldScene:
    def __init__(self, engine):
        self.engine = engine
        self.tile_defs, self.maps, self.scripts = load_maps()
        self.enemy_data = load_enemies()
        self.current_map_id = engine.current_map
        self.map_data = None
        self.player_tile_x = engine.player_x
        self.player_tile_y = engine.player_y
        self.target_tile_x = engine.player_x
        self.target_tile_y = engine.player_y
        self.player_pixel_x = 0
        self.player_pixel_y = 0
        self.target_pixel_x = 0
        self.target_pixel_y = 0
        self.move_speed = 120
        self.is_moving = False
        self.npc_dialog = None
        self.dialog_index = 0
        self._prev_scale = 0
        self._text_cache = {}
        self._map_name_text = None
        self._dialog_text = None
        self._arrow_text = None
        self._facing = "down"
        self._move_cooldown = 0
        self.load_map(self.current_map_id)

    def _get_text(self, key, text, x, y, color, size, anchor_x="left", anchor_y="center"):
        scale = self._prev_scale
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

    def load_map(self, map_id):
        self.current_map_id = map_id
        self.map_data = self.maps.get(map_id)
        if not self.map_data:
            return
        self.player_tile_x = self.engine.player_x
        self.player_tile_y = self.engine.player_y
        self.update_pixel_position()
        self.target_pixel_x = self.player_pixel_x
        self.target_pixel_y = self.player_pixel_y
        self.is_moving = False
        self._map_name_text = None

    def update_pixel_position(self):
        scale = self.engine.get_scale()
        tile_size = 16
        center_x = self.engine.get_size()[0] / 2
        center_y = self.engine.get_size()[1] / 2
        self.player_pixel_x = center_x + (self.player_tile_x - 7) * tile_size * scale
        self.player_pixel_y = center_y + (self.player_tile_y - 5) * tile_size * scale

    def get_tile_at(self, tx, ty):
        if not self.map_data:
            return None
        tiles = self.map_data.get("tiles", [])
        if ty < 0 or ty >= len(tiles) or tx < 0 or tx >= len(tiles[0]):
            return None
        return tiles[ty][tx]

    def is_walkable(self, tx, ty):
        tile_id = self.get_tile_at(tx, ty)
        if tile_id is None:
            return False
        tile_def = self.tile_defs.get(str(tile_id), {})
        return tile_def.get("walkable", False)

    def try_move(self, dx, dy):
        if self.is_moving:
            return
        new_tx = self.player_tile_x + dx
        new_ty = self.player_tile_y + dy
        if new_tx < 0 or new_tx >= self.map_data["width"] or new_ty < 0 or new_ty >= self.map_data["height"]:
            return
        if not self.is_walkable(new_tx, new_ty):
            return
        for npc in self.map_data.get("npcs", []):
            if npc["x"] == new_tx and npc["y"] == new_ty:
                return
        
        self.target_tile_x = new_tx
        self.target_tile_y = new_ty
        self.update_pixel_position()
        self.target_pixel_x = self.player_pixel_x + dx * 16 * self.engine.get_scale()
        self.target_pixel_y = self.player_pixel_y + dy * 16 * self.engine.get_scale()
        self.is_moving = True
        self.check_battle()

    def check_battle(self):
        if random.random() < 0.1:
            self.engine.set_scene("battle")

    def check_exits(self):
        for exit_data in self.map_data.get("exits", []):
            if self.player_tile_x == exit_data["x"] and self.player_tile_y == exit_data["y"]:
                target = exit_data.get("dest_map")
                if target:
                    self.engine.current_map = target
                    self.engine.player_x = exit_data.get("dest_x", 7)
                    self.engine.player_y = exit_data.get("dest_y", 5)
                    self.load_map(target)
                break

    def check_npc(self):
        facing = getattr(self, "facing", "down")
        check_x = self.player_tile_x
        check_y = self.player_tile_y
        if facing == "up":
            check_y -= 1
        elif facing == "down":
            check_y += 1
        elif facing == "left":
            check_x -= 1
        elif facing == "right":
            check_x += 1
        for npc in self.map_data.get("npcs", []):
            if npc["x"] == check_x and npc["y"] == check_y:
                return npc
        return None

    def start_dialog(self, npc):
        script_id = npc.get("script")
        if script_id and self.scripts.get(script_id):
            self.npc_dialog = self.scripts[script_id].get("dialog", [])
            self.dialog_index = 0

    def update(self, delta_time):
        self._move_cooldown = max(0, self._move_cooldown - delta_time)

        if self.npc_dialog:
            inpt = self.engine.input
            if inpt.is_just_pressed(Z):
                self.dialog_index += 1
                if self.dialog_index >= len(self.npc_dialog):
                    self.npc_dialog = None
                    self.dialog_index = 0
            return

        if self.is_moving:
            scale = self.engine.get_scale()
            speed = self.move_speed * scale * delta_time
            dx = self.target_pixel_x - self.player_pixel_x
            dy = self.target_pixel_y - self.player_pixel_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= speed:
                self.player_pixel_x = self.target_pixel_x
                self.player_pixel_y = self.target_pixel_y
                self.player_tile_x = self.target_tile_x
                self.player_tile_y = self.target_tile_y
                self.is_moving = False
                self.engine.player_x = self.player_tile_x
                self.engine.player_y = self.player_tile_y
                self.check_exits()
            else:
                self.player_pixel_x += (dx / dist) * speed
                self.player_pixel_y += (dy / dist) * speed
            return

        inpt = self.engine.input
        dir_x = 0
        dir_y = 0
        if inpt.is_pressed(UP):
            dir_y = 1
            self.facing = "up"
        elif inpt.is_pressed(DOWN):
            dir_y = -1
            self.facing = "down"
        elif inpt.is_pressed(LEFT):
            dir_x = -1
            self.facing = "left"
        elif inpt.is_pressed(RIGHT):
            dir_x = 1
            self.facing = "right"
        
        if dir_x != 0 or dir_y != 0:
            if self._move_cooldown <= 0:
                self.try_move(dir_x, dir_y)
                self._move_cooldown = 0.15
        elif inpt.is_just_pressed(Z):
            npc = self.check_npc()
            if npc:
                self.start_dialog(npc)
        elif inpt.is_just_pressed(X):
            self.engine.set_scene("menu")

    def draw_tile(self, x, y, tile_id, scale, offset_x, offset_y):
        tile_def = self.tile_defs.get(str(tile_id), {})
        color = tile_def.get("color", [128, 128, 128])
        tile_size = 16 * scale
        px = offset_x + x * tile_size
        py = offset_y + (self.map_data["height"] - 1 - y) * tile_size
        arcade.draw_lrbt_rectangle_filled(px, px + tile_size, py, py + tile_size, color)

    def draw(self):
        w, h = self.engine.get_size()
        scale = self.engine.get_scale()

        arcade.draw_lrbt_rectangle_filled(0, w, 0, h, (50, 50, 50))

        if not self.map_data:
            return

        tile_size = 16 * scale
        map_w = self.map_data["width"]
        map_h = self.map_data["height"]
        offset_x = (w - map_w * tile_size) / 2
        offset_y = (h - map_h * tile_size) / 2

        tiles = self.map_data.get("tiles", [])
        for ty in range(map_h):
            for tx in range(map_w):
                tile_id = tiles[ty][tx]
                self.draw_tile(tx, ty, tile_id, scale, offset_x, offset_y)

        for exit_data in self.map_data.get("exits", []):
            ex = exit_data["x"]
            ey = exit_data["y"]
            epx = offset_x + ex * tile_size
            epy = offset_y + (map_h - 1 - ey) * tile_size
            arcade.draw_lrbt_rectangle_outline(
                epx + 2, epx + tile_size - 2,
                epy + 2, epy + tile_size - 2,
                (255, 255, 0, 100), int(scale)
            )

        for npc in self.map_data.get("npcs", []):
            npc_px = offset_x + npc["x"] * tile_size + tile_size / 2
            npc_py = offset_y + (map_h - 1 - npc["y"]) * tile_size + tile_size / 2
            arcade.draw_lrbt_rectangle_filled(
                npc_px - 6 * scale, npc_px + 6 * scale,
                npc_py - 6 * scale, npc_py + 6 * scale,
                arcade.color.RED
            )

        for ty in range(map_h):
            for tx in range(map_w):
                tile_id = tiles[ty][tx]
                tile_def = self.tile_defs.get(str(tile_id), {})
                if not tile_def.get("walkable", True):
                    px = offset_x + tx * tile_size
                    py = offset_y + (map_h - 1 - ty) * tile_size
                    arcade.draw_lrbt_rectangle_outline(
                        px, px + tile_size, py, py + tile_size,
                        (255, 255, 255, 60), int(scale)
                    )

        player_size = int(10 * scale)
        arcade.draw_lrbt_rectangle_filled(
            self.player_pixel_x - player_size // 2,
            self.player_pixel_x + player_size // 2,
            self.player_pixel_y - player_size // 2,
            self.player_pixel_y + player_size // 2,
            arcade.color.WHITE
        )

        font_size = int(6 * scale)
        self._map_name_text = self._get_text("map_name", self.map_data["name"], w // 2, 8 * scale, COLORS["text"], font_size, anchor_x="center", anchor_y="center")
        self._map_name_text.draw()

        if self.npc_dialog:
            box_h = 40 * scale
            box_y = 20 * scale
            draw_window(16 * scale, box_y, w - 32 * scale, box_h, scale)
            dialog_text = self.npc_dialog[self.dialog_index]
            self._dialog_text = self._get_text(f"dialog_{self.dialog_index}", dialog_text, 24 * scale, box_y + 8 * scale, COLORS["text"], font_size, anchor_y="top")
            self._dialog_text.draw()
            if self.dialog_index < len(self.npc_dialog) - 1:
                self._arrow_text = self._get_text("arrow", "▼", w - 24 * scale, box_y + 4 * scale, COLORS["text"], font_size, anchor_x="center", anchor_y="center")
                self._arrow_text.draw()

        self._prev_scale = scale
