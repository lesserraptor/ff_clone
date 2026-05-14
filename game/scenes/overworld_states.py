import json
import os
import random
import arcade
from pyglet.window import key
from game.text import create_text
from game.ui import COLORS, draw_window
from game.sprites import get_sprite_atlas


DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "maps.json")
ENEMIES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "enemies.json")


def load_maps():
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
    return data.get("tile_defs", {}), data.get("maps", {}), data.get("scripts", {})


def load_enemies():
    with open(ENEMIES_PATH, "r") as f:
        return json.load(f)


class OverworldModel:
    """Pure state + logic for overworld. No arcade dependencies."""

    def __init__(self, engine):
        self.tile_defs, self.maps, self.scripts = load_maps()
        self.enemy_data = load_enemies()
        self.current_map_id = engine.current_map
        self.map_data = None

        self.player_tile_x = engine.player_x
        self.player_tile_y = engine.player_y
        self.target_tile_x = engine.player_x
        self.target_tile_y = engine.player_y

        self.is_moving = False
        self.move_progress = 0.0
        self.move_speed = 120
        self.facing = "down"
        self.player_sprite_id = engine.party[0].name.lower() if engine.party else "warrior"
        self._move_cooldown = 0

        self.npc_dialog = None
        self.dialog_index = 0

        self.load_map(self.current_map_id)

    # ── map loading ──────────────────────────────────────

    def load_map(self, map_id):
        """Load map data. Does NOT set player position — caller sets it first."""
        self.current_map_id = map_id
        self.map_data = self.maps.get(map_id)
        if not self.map_data:
            return
        self.is_moving = False
        self.move_progress = 0.0
        self.npc_dialog = None
        self.dialog_index = 0

    # ── tile helpers ─────────────────────────────────────

    def _get_tile(self, tx, ty):
        if not self.map_data:
            return None
        tiles = self.map_data.get("tiles", [])
        if ty < 0 or ty >= len(tiles) or tx < 0 or tx >= len(tiles[0]):
            return None
        return tiles[ty][tx]

    def _is_walkable(self, tx, ty):
        tile_id = self._get_tile(tx, ty)
        if tile_id is None:
            return False
        tile_def = self.tile_defs.get(str(tile_id), {})
        return tile_def.get("walkable", False)

    # ── battle / exit checks ─────────────────────────────

    def _check_battle(self):
        return random.random() < 0.1

    def _check_exits(self):
        if not self.map_data:
            return None
        for exit_data in self.map_data.get("exits", []):
            if self.player_tile_x == exit_data["x"] and self.player_tile_y == exit_data["y"]:
                return {
                    "type": "exit",
                    "dest_map": exit_data.get("dest_map"),
                    "dest_x": exit_data.get("dest_x", 7),
                    "dest_y": exit_data.get("dest_y", 5),
                }
        return None

    # ── NPC interaction ──────────────────────────────────

    def _check_npc(self):
        check_x = self.player_tile_x
        check_y = self.player_tile_y
        if self.facing == "up":
            check_y -= 1
        elif self.facing == "down":
            check_y += 1
        elif self.facing == "left":
            check_x -= 1
        elif self.facing == "right":
            check_x += 1
        for npc in self.map_data.get("npcs", []):
            if npc["x"] == check_x and npc["y"] == check_y:
                return npc
        return None

    def _start_dialog(self, npc):
        script_id = npc.get("script")
        if script_id and self.scripts.get(script_id):
            self.npc_dialog = self.scripts[script_id].get("dialog", [])
            self.dialog_index = 0

    # ── movement ─────────────────────────────────────────

    def _try_move(self, dx, dy):
        if not self.map_data:
            return False
        new_tx = self.player_tile_x + dx
        new_ty = self.player_tile_y + dy
        if new_tx < 0 or new_tx >= self.map_data["width"] or new_ty < 0 or new_ty >= self.map_data["height"]:
            return False
        if not self._is_walkable(new_tx, new_ty):
            return False
        for npc in self.map_data.get("npcs", []):
            if npc["x"] == new_tx and npc["y"] == new_ty:
                return False

        self.target_tile_x = new_tx
        self.target_tile_y = new_ty
        self.is_moving = True
        self.move_progress = 0.0

        return self._check_battle()

    # ── main update ──────────────────────────────────────

    def update(self, dt, inpt):
        """Returns event dict or None."""
        self._move_cooldown = max(0, self._move_cooldown - dt)

        # ── dialog mode ──
        if self.npc_dialog:
            if inpt.is_just_pressed(key.Z):
                self.dialog_index += 1
                if self.dialog_index >= len(self.npc_dialog):
                    self.npc_dialog = None
                    self.dialog_index = 0
            return None

        # ── movement in progress ──
        if self.is_moving:
            self.move_progress += dt * self.move_speed / 16.0
            if self.move_progress >= 1.0:
                self.player_tile_x = self.target_tile_x
                self.player_tile_y = self.target_tile_y
                self.is_moving = False
                self.move_progress = 0.0
                exit_event = self._check_exits()
                if exit_event:
                    return exit_event
            return None

        # ── input handling ──
        dir_x = 0
        dir_y = 0
        if inpt.is_pressed(key.UP):
            dir_y = 1
            self.facing = "up"
        elif inpt.is_pressed(key.DOWN):
            dir_y = -1
            self.facing = "down"
        elif inpt.is_pressed(key.LEFT):
            dir_x = -1
            self.facing = "left"
        elif inpt.is_pressed(key.RIGHT):
            dir_x = 1
            self.facing = "right"

        if dir_x != 0 or dir_y != 0:
            if self._move_cooldown <= 0:
                battle_triggered = self._try_move(dir_x, dir_y)
                self._move_cooldown = 0.15
                if battle_triggered:
                    return {"type": "battle"}
        elif inpt.is_just_pressed(key.Z):
            npc = self._check_npc()
            if npc:
                self._start_dialog(npc)
        elif inpt.is_just_pressed(key.X):
            return {"type": "menu"}

        return None


class OverworldRenderer:
    """All drawing for overworld. Caches text objects."""

    def __init__(self):
        self._prev_scale = 0
        self._text_cache = {}
        self._map_name_text = None
        self._dialog_text = None
        self._arrow_text = None

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

    def draw(self, model, scale, width, height):
        # ── background ──
        arcade.draw_lrbt_rectangle_filled(0, width, 0, height, (50, 50, 50))

        if not model.map_data:
            return

        tile_size = 16 * scale
        map_w = model.map_data["width"]
        map_h = model.map_data["height"]
        offset_x = (width - map_w * tile_size) / 2
        offset_y = (height - map_h * tile_size) / 2
        tiles = model.map_data.get("tiles", [])

        # ── tiles ──
        for ty in range(map_h):
            for tx in range(map_w):
                tile_id = tiles[ty][tx]
                tile_def = model.tile_defs.get(str(tile_id), {})
                color = tile_def.get("color", [128, 128, 128])
                px = offset_x + tx * tile_size
                py = offset_y + (map_h - 1 - ty) * tile_size
                arcade.draw_lrbt_rectangle_filled(px, px + tile_size, py, py + tile_size, color)

        # ── exits ──
        for exit_data in model.map_data.get("exits", []):
            ex = exit_data["x"]
            ey = exit_data["y"]
            epx = offset_x + ex * tile_size
            epy = offset_y + (map_h - 1 - ey) * tile_size
            arcade.draw_lrbt_rectangle_outline(
                epx + 2, epx + tile_size - 2,
                epy + 2, epy + tile_size - 2,
                (255, 255, 0, 100), int(scale),
            )

        # ── NPCs ──
        for npc in model.map_data.get("npcs", []):
            npc_px = offset_x + npc["x"] * tile_size + tile_size / 2
            npc_py = offset_y + (map_h - 1 - npc["y"]) * tile_size + tile_size / 2
            arcade.draw_lrbt_rectangle_filled(
                npc_px - 6 * scale, npc_px + 6 * scale,
                npc_py - 6 * scale, npc_py + 6 * scale,
                arcade.color.RED,
            )

        # ── non-walkable outlines ──
        for ty in range(map_h):
            for tx in range(map_w):
                tile_id = tiles[ty][tx]
                tile_def = model.tile_defs.get(str(tile_id), {})
                if not tile_def.get("walkable", True):
                    px = offset_x + tx * tile_size
                    py = offset_y + (map_h - 1 - ty) * tile_size
                    arcade.draw_lrbt_rectangle_outline(
                        px, px + tile_size, py, py + tile_size,
                        (255, 255, 255, 60), int(scale),
                    )

        # ── player pixel position ──
        center_x = width / 2
        center_y = height / 2
        px = center_x + (model.player_tile_x - 7) * tile_size
        py = center_y + (model.player_tile_y - 5) * tile_size
        if model.is_moving:
            target_px = center_x + (model.target_tile_x - 7) * tile_size
            target_py = center_y + (model.target_tile_y - 5) * tile_size
            px += (target_px - px) * model.move_progress
            py += (target_py - py) * model.move_progress

        # ── player sprite ──
        atlas = get_sprite_atlas()
        if atlas.has_sprite(model.player_sprite_id):
            atlas.draw(model.player_sprite_id, px, py, scale)
        else:
            # Fallback: white rectangle
            player_size = int(10 * scale)
            arcade.draw_lrbt_rectangle_filled(
                px - player_size // 2, px + player_size // 2,
                py - player_size // 2, py + player_size // 2,
                arcade.color.WHITE,
            )

        # ── map name ──
        font_size = int(6 * scale)
        self._map_name_text = self._get_text(
            "map_name", model.map_data["name"],
            width // 2, 8 * scale,
            COLORS["text"], font_size,
            anchor_x="center", anchor_y="center",
        )
        self._map_name_text.draw()

        # ── dialog box ──
        if model.npc_dialog:
            box_h = 40 * scale
            box_y = 20 * scale
            draw_window(16 * scale, box_y, width - 32 * scale, box_h, scale)
            dialog_text = model.npc_dialog[model.dialog_index]
            self._dialog_text = self._get_text(
                f"dialog_{model.dialog_index}", dialog_text,
                24 * scale, box_y + 8 * scale,
                COLORS["text"], font_size,
                anchor_y="top",
            )
            self._dialog_text.draw()
            if model.dialog_index < len(model.npc_dialog) - 1:
                self._arrow_text = self._get_text(
                    "arrow", "\u25bc",
                    width - 24 * scale, box_y + 4 * scale,
                    COLORS["text"], font_size,
                    anchor_x="center", anchor_y="center",
                )
                self._arrow_text.draw()

        self._prev_scale = scale
