"""Tileset loader - slice a PNG into 16x16 tile textures indexed by GID"""

import arcade
import os
import io
from PIL import Image


class Tileset:
    """Load a tileset PNG and slice into 16x16 tiles, 1-based GID (row-major)."""

    def __init__(self, image_path, tile_w=16, tile_h=16, cols=10, rows=9):
        self._tile_w = tile_w
        self._tile_h = tile_h
        self._cols = cols
        self._rows = rows
        self.textures = {}

        # Resolve image path: try as-is first, then relative to project root
        path = image_path
        if not os.path.exists(path):
            # game/.. = project root
            alt = os.path.join(os.path.dirname(__file__), "..", image_path)
            if os.path.exists(alt):
                path = os.path.normpath(alt)

        if not os.path.exists(path):
            print(f"Tileset: file not found: {image_path}")
            return

        sheet = Image.open(path).convert("RGBA")
        filename = os.path.basename(path)

        for gid in range(1, cols * rows + 1):
            col = (gid - 1) % cols
            row = (gid - 1) // cols
            left = col * tile_w
            upper = row * tile_h
            right = left + tile_w
            lower = upper + tile_h
            tile_img = sheet.crop((left, upper, right, lower))

            buf = io.BytesIO()
            tile_img.save(buf, format="PNG")
            buf.seek(0)

            self.textures[gid] = arcade.load_texture(buf)

        print(f"Tileset: loaded {len(self.textures)} tiles from {filename}")

    def get_texture(self, gid):
        """Return arcade.Texture for given GID, or None if out of range."""
        return self.textures.get(gid)

    def has_texture(self, gid):
        """Return True if a texture exists for the given GID."""
        return gid in self.textures

    @property
    def tile_w(self):
        return self._tile_w

    @property
    def tile_h(self):
        return self._tile_h

    @property
    def cols(self):
        return self._cols

    @property
    def rows(self):
        return self._rows
