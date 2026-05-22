"""Overworld layout configuration."""
from dataclasses import dataclass


@dataclass(frozen=True)
class _ScaledOverworldLayout:
    scale: float
    me: int

    @property
    def tile_size(self): return int(16 * self.scale)

    @property
    def npc_box_half(self): return int(6 * self.scale)

    @property
    def player_fallback_size(self): return int(10 * self.scale)

    @property
    def map_name_font_size(self): return int(6 * self.scale)

    @property
    def map_name_y(self): return int(8 * self.scale)

    @property
    def dialog_box_h(self): return int(40 * self.scale)

    @property
    def dialog_box_y(self): return int(20 * self.scale)

    @property
    def dialog_box_margin_x(self): return int(16 * self.scale)

    @property
    def dialog_text_x(self): return int(24 * self.scale)

    @property
    def dialog_text_y_offset(self): return int(8 * self.scale)

    @property
    def dialog_arrow_y_offset(self): return int(4 * self.scale)


def get_overworld_layout(scale: float):
    return _ScaledOverworldLayout(scale=scale, me=int(scale))
