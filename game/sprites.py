"""Sprite Atlas System - Load and draw sprites from sprite sheets"""

import arcade
import os
import json
import io
from PIL import Image


class SpriteAtlas:
    def __init__(self, assets_path=None):
        if assets_path is None:
            assets_path = os.path.join(os.path.dirname(__file__), "..", "assets")
        self.assets_path = assets_path
        self.sheets = {}
        self.definitions = {}
        self.sprite_textures = {}
        self._bg_colors = {}
        self._sheet_filenames = {}

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

        self._sheet_filenames = data.get("sheets", {})
        for sheet_name, filename in self._sheet_filenames.items():
            self.load_sheet(sheet_name, filename)

        self.definitions = data.get("sprites", {})
        self._preload_sprites()
        return True

    def _preload_sprites(self):
        # Detect background color per sheet from full-sheet corners
        for sheet_name, sheet in self.sheets.items():
            img = sheet.image
            w, h = img.size
            corners = [
                img.getpixel((0, 0)),
                img.getpixel((w - 1, 0)),
                img.getpixel((0, h - 1)),
                img.getpixel((w - 1, h - 1)),
            ]
            valid = [c for c in corners if c[3] == 255] if len(corners[0]) >= 4 else corners
            if valid:
                self._bg_colors[sheet_name] = max(set(valid), key=valid.count)

        # First pass: load all sprites with crop coordinates
        for sprite_id, sprite_def in self.definitions.items():
            if "mirror_of" in sprite_def:
                continue

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

            # Ensure RGBA for transparency support
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Remove sheet background color (detected from full sheet corners)
            bg_color = self._bg_colors.get(sheet_name)
            if bg_color is not None:
                pixels_list = list(img.getdata())
                new_data = []
                for pixel in pixels_list:
                    if pixel[:3] == bg_color[:3] and pixel[3] == 255:
                        new_data.append((*bg_color[:3], 0))
                    else:
                        new_data.append(pixel)
                img.putdata(new_data)

            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)

            self.sprite_textures[sprite_id] = arcade.load_texture(buf)

        # Second pass: create mirrored copies
        for sprite_id, sprite_def in self.definitions.items():
            mirror_of = sprite_def.get("mirror_of")
            if mirror_of is None:
                continue

            source = self.sprite_textures.get(mirror_of)
            if source is None:
                print(f"Warning: mirror_of source '{mirror_of}' not found for '{sprite_id}'")
                continue

            img = source.image
            flipped = img.transpose(Image.FLIP_LEFT_RIGHT)

            buf = io.BytesIO()
            flipped.save(buf, format='PNG')
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

    def get_texture(self, sprite_id: str):
        """Get the texture for a sprite, or None if not found."""
        return self.sprite_textures.get(sprite_id)


_atlas_instance = None


def get_sprite_atlas():
    global _atlas_instance
    if _atlas_instance is None:
        _atlas_instance = SpriteAtlas()
        json_path = os.path.join(os.path.dirname(__file__), "..", "data", "sprites.json")
        _atlas_instance.load_definitions(json_path)
    return _atlas_instance