import json
import os
import random
import arcade
from pyglet.window import key
from game.text import create_text
from game.ui import COLORS, draw_window
from game.sprites import get_sprite_atlas
from game.tiles import Tileset
from game.tilemap import Tilemap
from game.tiled_map_loader import load_tiled_map
from game.scenes.overworld_layout import get_overworld_layout
from game.renderer import SceneRenderer
from dataclasses import dataclass


@dataclass(frozen=True)
class OverworldRenderState:
    """Read-only snapshot of overworld model state for renderers."""
    current_map_id: str
    map_data: dict
    tile_defs: dict
    player_tile_x: int
    player_tile_y: int
    target_tile_x: int
    target_tile_y: int
    is_moving: bool
    move_progress: float
    player_sprite_id: str
    current_sprite_id: str
    npc_dialog: list[str] | None
    dialog_index: int


PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
MAPS_DIR = os.path.join(PROJECT_ROOT, "assets", "maps")
JSON_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "maps.json")
ENEMIES_PATH = os.path.join(PROJECT_ROOT, "data", "enemies.json")


def load_maps():
    """Load maps from .tmx files + tile_defs and scripts from maps.json."""
    # Load tile_defs, scripts, and original tile grids from maps.json
    tile_defs = {}
    scripts = {}
    json_maps = {}
    if os.path.exists(JSON_DATA_PATH):
        with open(JSON_DATA_PATH, "r") as f:
            data = json.load(f)
        tile_defs = data.get("tile_defs", {})
        scripts = data.get("scripts", {})
        json_maps = data.get("maps", {})

    # Load map grids from .tmx files (gids, npcs, exits)
    maps = {}
    if os.path.isdir(MAPS_DIR):
        for filename in sorted(os.listdir(MAPS_DIR)):
            if not filename.endswith(".tmx"):
                continue
            map_id = filename.replace(".tmx", "")
            tmx_path = os.path.join(MAPS_DIR, filename)
            try:
                map_data = load_tiled_map(tmx_path)
                # Override tiles with original logical tile IDs from maps.json
                # (GID→tile_id reverse mapping is lossy due to tree expansion)
                json_orig = json_maps.get(map_id)
                if json_orig and "tiles" in json_orig:
                    map_data["tiles"] = json_orig["tiles"]
                maps[map_id] = map_data
            except Exception as exc:
                print(f"Warning: failed to load {filename}: {exc}")

    return tile_defs, maps, scripts


def load_enemies():
    with open(ENEMIES_PATH, "r") as f:
        return json.load(f)


class OverworldModel:
    """Pure state + logic for overworld. No arcade dependencies."""

    FACING_MAP = {
        "down": "dn",
        "right": "rt",
        "up": "up",
        "left": "lf",
    }

    def __init__(self, engine, tile_defs, maps, scripts, enemy_data):
        self.tile_defs = tile_defs
        self.maps = maps
        self.scripts = scripts
        self.enemy_data = enemy_data
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
        self.class_name = engine.party[0].name.lower() if engine.party else "warrior"
        self.walk_frame = 0
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

    def get_current_sprite_id(self):
        """Return frame sprite ID based on facing and walk animation."""
        dir_code = self.FACING_MAP.get(self.facing, self.facing)
        return f"{self.class_name}_{dir_code}_{self.walk_frame}"

    def get_render_state(self) -> OverworldRenderState:
        """Return immutable snapshot of current model state for rendering."""
        return OverworldRenderState(
            current_map_id=self.current_map_id,
            map_data=self.map_data,
            tile_defs=self.tile_defs,
            player_tile_x=self.player_tile_x,
            player_tile_y=self.player_tile_y,
            target_tile_x=self.target_tile_x,
            target_tile_y=self.target_tile_y,
            is_moving=self.is_moving,
            move_progress=self.move_progress,
            player_sprite_id=self.player_sprite_id,
            current_sprite_id=self.get_current_sprite_id(),
            npc_dialog=self.npc_dialog,
            dialog_index=self.dialog_index,
        )

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
            self.walk_frame = 0 if self.move_progress < 0.5 else 1
            self.move_progress += dt * self.move_speed / 16.0
            if self.move_progress >= 1.0:
                self.walk_frame = 0
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


class OverworldRenderer(SceneRenderer):
    """All drawing for overworld. Caches text objects."""

    def __init__(self):
        self._prev_scale = 0
        self._text_cache = {}
        self._map_name_text = None
        self._dialog_text = None
        self._arrow_text = None
        self._tileset = None
        self._tilemap = None
        self._tilemap_map_id = None

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

    def _get_tileset(self):
        if self._tileset is None:
            self._tileset = Tileset("assets/extracted_hometown_tileset_rgb.png")
        return self._tileset

    def _get_tilemap(self, model):
        tileset = self._get_tileset()
        if self._tilemap_map_id != model.current_map_id or self._tilemap is None:
            self._tilemap = Tilemap(
                tileset,
                model.map_data["gids"],
                model.map_data["width"],
                model.map_data["height"],
            )
            self._tilemap_map_id = model.current_map_id
        return self._tilemap

    def draw(self, model, scale: float, width: int, height: int, **kwargs):
        layout = get_overworld_layout(scale)

        # ── background ──
        arcade.draw_lrbt_rectangle_filled(0, width, 0, height, (50, 50, 50))

        if not model.map_data:
            return

        tile_size = layout.tile_size
        map_w = model.map_data["width"]
        map_h = model.map_data["height"]
        offset_x = (width - map_w * tile_size) / 2
        offset_y = (height - map_h * tile_size) / 2
        tiles = model.map_data.get("tiles", [])

        # ── tiles (textured) ──
        tilemap = self._get_tilemap(model)
        tilemap.draw(offset_x, offset_y, scale)

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
                npc_px - layout.npc_box_half, npc_px + layout.npc_box_half,
                npc_py - layout.npc_box_half, npc_py + layout.npc_box_half,
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
        sprite_id = model.get_current_sprite_id()
        if atlas.has_sprite(sprite_id):
            atlas.draw(sprite_id, px, py, scale)
        elif atlas.has_sprite(model.player_sprite_id):
            # Fallback to old static sprite
            atlas.draw(model.player_sprite_id, px, py, scale)
        else:
            # Fallback: white rectangle
            player_size = layout.player_fallback_size
            arcade.draw_lrbt_rectangle_filled(
                px - player_size // 2, px + player_size // 2,
                py - player_size // 2, py + player_size // 2,
                arcade.color.WHITE,
            )

        # ── map name ──
        font_size = layout.map_name_font_size
        self._map_name_text = self._get_text(
            "map_name", model.map_data["name"],
            width // 2, layout.map_name_y,
            COLORS["text"], font_size,
            anchor_x="center", anchor_y="center",
        )
        self._map_name_text.draw()

        # ── dialog box ──
        if model.npc_dialog:
            box_h = layout.dialog_box_h
            box_y = layout.dialog_box_y
            draw_window(layout.dialog_box_margin_x, box_y, width - 2 * layout.dialog_box_margin_x, box_h, scale)
            dialog_text = model.npc_dialog[model.dialog_index]
            self._dialog_text = self._get_text(
                f"dialog_{model.dialog_index}", dialog_text,
                layout.dialog_text_x, box_y + layout.dialog_text_y_offset,
                COLORS["text"], font_size,
                anchor_y="top",
            )
            self._dialog_text.draw()
            if model.dialog_index < len(model.npc_dialog) - 1:
                self._arrow_text = self._get_text(
                    "arrow", "\u25bc",
                    width - layout.dialog_text_x, box_y + layout.dialog_arrow_y_offset,
                    COLORS["text"], font_size,
                    anchor_x="center", anchor_y="center",
                )
                self._arrow_text.draw()

        self._prev_scale = scale
