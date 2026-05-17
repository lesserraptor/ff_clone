"""Tilemap renderer - draws a 2D grid of GID values using a Tileset"""

import arcade


class Tilemap:
    """Render a 2D grid of GID tile indices using a Tileset. Y-flipped: row 0 = top."""

    def __init__(self, tileset, gid_grid, width, height):
        self.tileset = tileset
        self.gid_grid = gid_grid
        self.width = width
        self.height = height

        self._sprites = []
        self._sprite_list = arcade.SpriteList()

        for ty in range(height):
            for tx in range(width):
                gid = gid_grid[ty][tx]
                texture = tileset.get_texture(gid)
                if texture is None:
                    self._sprites.append(None)
                else:
                    sprite = arcade.Sprite()
                    sprite.texture = texture
                    self._sprites.append(sprite)
                    self._sprite_list.append(sprite)

    def draw(self, offset_x, offset_y, scale):
        """Draw all visible tiles. Row 0 renders at the top of the screen."""
        tile_size = self.tileset.tile_w * scale

        for ty in range(self.height):
            for tx in range(self.width):
                idx = ty * self.width + tx
                sprite = self._sprites[idx]
                if sprite is None:
                    continue

                px = offset_x + tx * tile_size
                # Y-flip: gid_grid[0] = top row -> highest Y
                py = offset_y + (self.height - 1 - ty) * tile_size

                sprite.center_x = px + tile_size / 2
                sprite.center_y = py + tile_size / 2
                sprite.scale = scale

        self._sprite_list.draw(pixelated=True)
