"""Sprite Atlas System - Load and draw sprites from sprite sheets"""

import arcade
import os
import json
import io


class SpriteAtlas:
    def __init__(self, assets_path=None):
        if assets_path is None:
            assets_path = os.path.join(os.path.dirname(__file__), "..", "assets")
        self.assets_path = assets_path
        self.sheets = {}
        self.definitions = {}
        self.sprite_textures = {}

    def load_sheet(self, name: str, filename: str):
        path = os.path.join(self.assets_path, filename)
        if os.path.exists(path):
            self.sheets[name] = arcade.load_texture(path)
            return True
        print(f"Sprite sheet not found: {path}")
        return False

    def load_definitions(self, json_path: str):
        if not os.path.exists(json_path):
            print(f"Sprite definitions not found: {json_path}")
            return False

        with open(json_path, "r") as f:
            data = json.load(f)

        for sheet_name, filename in data.get("sheets", {}).items():
            self.load_sheet(sheet_name, filename)

        self.definitions = data.get("sprites", {})
        self._preload_sprites()
        return True

    def _preload_sprites(self):
        for sprite_id, sprite_def in self.definitions.items():
            sheet_name = sprite_def.get("sheet")
            if sheet_name not in self.sheets:
                continue

            sheet = self.sheets[sheet_name]
            sx = sprite_def["x"]
            sy = sprite_def["y"]
            sw = sprite_def["w"]
            sh = sprite_def["h"]

            cropped = sheet.crop(sx, sy, sw, sh)
            img = cropped.image

            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)

            self.sprite_textures[sprite_id] = arcade.load_texture(buf)

    def get_sprite(self, sprite_id: str):
        if sprite_id not in self.definitions:
            return None
        return self.definitions[sprite_id]

    def draw(self, sprite_id: str, x: float, y: float, scale: float = 1.0):
        if sprite_id not in self.sprite_textures:
            return False

        texture = self.sprite_textures[sprite_id]
        sprite = arcade.Sprite()
        sprite.texture = texture
        sprite.center_x = x
        sprite.center_y = y
        sprite.scale = scale

        sprite_list = arcade.SpriteList()
        sprite_list.append(sprite)
        sprite_list.draw(pixelated=True)
        return True

    def has_sprite(self, sprite_id: str) -> bool:
        return sprite_id in self.sprite_textures


_atlas_instance = None


def get_sprite_atlas():
    global _atlas_instance
    if _atlas_instance is None:
        _atlas_instance = SpriteAtlas()
        json_path = os.path.join(os.path.dirname(__file__), "..", "data", "sprites.json")
        _atlas_instance.load_definitions(json_path)
    return _atlas_instance