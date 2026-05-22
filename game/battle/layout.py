"""Battle layout configuration — proportional positions for all UI elements."""
from dataclasses import dataclass

# Base gameboy resolution
BW = 240
BH = 160


@dataclass(frozen=True)
class _ScaledBattleLayout:
    """Scaled pixel values for a given scale factor."""
    scale: float
    me: int  # int(scale), convenience multiplier

    @property
    def menu_h(self): return int(BH * 0.55) * self.me

    @property
    def char_box_w(self): return int(BW * 2 / 5) * self.me

    @property
    def enemy_box_x(self): return self.char_box_w

    @property
    def enemy_box_w(self): return (BW - int(BW * 2 / 5)) * self.me

    @property
    def border_px(self): return 6 * self.me

    @property
    def row_h(self): return self.menu_h // 4

    @property
    def enemy_cy_ratio(self): return 0.72  # enemy Y position as fraction of height

    @property
    def target_box_w(self): return int(BW * 3 / 5) * self.me  # left 3/5

    @property
    def action_box_w_scale(self): return 80  # action box width * scale

    @property
    def action_box_h_scale(self): return 40  # action box height * scale

    @property
    def cons_margin_scale(self): return 20

    @property
    def sprite_scale(self): return 1.2

    @property
    def char_sprite_scale(self): return 1.5

    @property
    def font_size_sm(self): return int(6 * self.scale)

    @property
    def font_size_md(self): return int(7 * self.scale)

    @property
    def font_size_lg(self): return int(8 * self.scale)

    @property
    def line_h_sm(self): return int(10 * self.scale)

    @property
    def line_h_md(self): return int(12 * self.scale)

    @property
    def char_spacing(self): return 14 * self.me

    @property
    def char_spacing2(self): return 10 * self.me  # smaller offset

    @property
    def hp_bar_offset(self): return 12 * self.me

    @property
    def char_sprite_offset(self): return 14 * self.me

    @property
    def cursor_offset(self): return 6 * self.me

    @property
    def menu_cursor_offset(self): return 4 * self.me

    @property
    def text_padding(self): return 8 * self.me

    @property
    def bottom_margin(self): return 14 * self.me

    @property
    def scy_mid(self): return self.char_sprite_offset + (self.menu_h - 2 * self.border_px) // 2

    @property
    def flash_sprite_sz(self): return 10 * self.me

    @property
    def flash_outline_sz(self): return 2 * self.me  # * scale for width

    @property
    def enemy_flash_sz(self): return 14 * self.me


def get_battle_layout(scale: float) -> _ScaledBattleLayout:
    """Get scaled battle layout for a given scale factor."""
    return _ScaledBattleLayout(scale=scale, me=int(scale))
