"""Menu layout configuration — all pixel/position constants in base 240x160 resolution.

Every value is an unscaled integer. Multiply by `scale` at use site.
"""

from dataclasses import dataclass, field
from typing import Tuple


# ── Common font sizes ──────────────────────────────────────────────

@dataclass(frozen=True)
class FontSizes:
    """Base font sizes (unscaled). Usage: int(N * scale)."""
    SMALL: int = 4          # equip detail HP numbers
    SMALL5: int = 5         # HP/MP numbers, help text
    NORMAL6: int = 6        # sub-text, stats
    NORMAL7: int = 7        # menu option text, character names
    TITLE8: int = 8         # section titles


# ── Screen / shared ────────────────────────────────────────────────

@dataclass(frozen=True)
class ScreenConfig:
    WIDTH: int = 240
    HEIGHT: int = 160
    CENTER_X: int = 120
    BOTTOM: int = 0
    LEFT: int = 0
    RIGHT: int = 240
    TOP: int = 160


# ── MainMenuState ──────────────────────────────────────────────────

@dataclass(frozen=True)
class MainMenuConfig:
    MENU_W: int = 80
    MENU_L: int = 0
    GOLD_H: int = 30
    GOLD_B: int = 0
    MENU_ROW_1: int = 146
    MENU_ROW_GAP: int = 16
    PARTY_ROW_1: int = 146
    PARTY_ROW_GAP: int = 32
    SPRITE_X_OFF: int = 24
    NAME_X_OFF: int = 16
    HP_Y_OFF: int = -16
    HP_CUR_Y_OFF: int = 5
    HP_MAX_Y_OFF: int = -5
    MP_COL_OFF: int = 64
    CURSOR_PARTY_OFF: int = 4
    TEXT_OFF: int = 12
    CURSOR_OFF: int = 4


# ── ItemsMenuState ─────────────────────────────────────────────────

@dataclass(frozen=True)
class ItemsMenuConfig:
    PANEL_L: int = 40
    PANEL_R: int = 200
    PANEL_B: int = 0
    PANEL_T: int = 160
    TITLE_X: int = 120
    TITLE_Y: int = 152
    EMPTY_X: int = 120
    EMPTY_Y: int = 80
    ITEM_ROW_1: int = 140
    ITEM_GAP: int = 17
    ITEM_CURSOR_OFF: int = 8
    ITEM_TEXT_OFF: int = 16
    ITEM_MAX_VISIBLE: int = 8
    HELP_X: int = 120
    HELP_Y: int = 8
    # Targeting overlay
    OL_L: int = 50
    OL_R: int = 190
    OL_B: int = 24
    OL_T: int = 120
    OL_TITLE_OFF: int = -10
    OL_FIRST_Y_OFF: int = -28
    OL_TARGET_GAP: int = 18
    OL_CURSOR_OFF: int = 8
    OL_NAME_OFF: int = 16
    OL_HP_OFF: int = 64
    OL_Y_ADJ: int = 3


# ── StatusMenuState ────────────────────────────────────────────────

@dataclass(frozen=True)
class StatusMenuConfig:
    PANEL_L: int = 4
    PANEL_R: int = 236
    PANEL_H: int = 34
    PANEL_GAP: int = 2
    TITLE_X: int = 120
    TITLE_Y: int = 155
    FIRST_PB: int = 14
    SPRITE_OFF: int = 12
    SPRITE_Y_OFF: int = 2
    TEXT_X_OFF: int = 24
    R1_OFF: int = 12
    R2_OFF: int = 4
    R3_OFF: int = -4
    R4_OFF: int = -12
    COL1_OFF: int = 64
    COL2_OFF: int = 124
    HELP_X: int = 120
    HELP_Y: int = 4


# ── EquipCharSelectState ───────────────────────────────────────────

@dataclass(frozen=True)
class EquipCharSelectConfig:
    PARTY_L: int = 40
    PANEL_B: int = 0
    PANEL_T: int = 150
    TITLE_X: int = 120
    TITLE_Y: int = 155
    ROW_1: int = 138
    ROW_GAP: int = 32
    SPRITE_OFF: int = 24
    NAME_OFF: int = 16
    CURSOR_OFF: int = 4
    HP_Y_OFF: int = -16
    HP_CUR_OFF: int = 5
    HP_MAX_OFF: int = -5
    HELP_X: int = 120
    HELP_Y: int = 8


# ── EquipDetailState ───────────────────────────────────────────────

@dataclass(frozen=True)
class EquipDetailPanel1Stats:
    BOX_L: int = 0
    BOX_R: int = 120
    BOX_B: int = 0
    BOX_T: int = 120
    TEXT_X: int = 8
    ROW_1_Y: int = 104
    ROW_2_Y: int = 92
    ROW_3_Y: int = 80
    ROW_4_Y: int = 68


@dataclass(frozen=True)
class EquipDetailPanel2Identity:
    BOX_L: int = 0
    BOX_R: int = 80
    BOX_B: int = 120
    BOX_T: int = 160
    SPRITE_X: int = 16
    SPRITE_Y: int = 140
    TEXT_X: int = 26
    NAME_Y: int = 150
    HP_CUR_Y: int = 142
    HP_MAX_Y: int = 134


@dataclass(frozen=True)
class EquipDetailPanel3Equipped:
    BOX_L: int = 80
    BOX_R: int = 240
    BOX_B: int = 0
    BOX_T: int = 160
    ROW_1: int = 148
    ROW_GAP: int = 22
    CURSOR_X: int = 88
    TEXT_X: int = 96
    NAME_Y_OFF: int = 5
    ITEM_Y_OFF: int = -5


@dataclass(frozen=True)
class EquipDetailItemsOverlay:
    BOX_L: int = 84
    BOX_R: int = 238
    BOX_B: int = 16
    BOX_T: int = 152
    HEADER_X: int = 92
    HEADER_Y: int = 144
    ROW_1: int = 132
    ROW_GAP: int = 14
    MAX_VISIBLE: int = 8
    CURSOR_X: int = 92
    TEXT_X: int = 100


@dataclass(frozen=True)
class EquipDetailConfig:
    panel1: EquipDetailPanel1Stats = field(default_factory=EquipDetailPanel1Stats)
    panel2: EquipDetailPanel2Identity = field(default_factory=EquipDetailPanel2Identity)
    panel3: EquipDetailPanel3Equipped = field(default_factory=EquipDetailPanel3Equipped)
    overlay: EquipDetailItemsOverlay = field(default_factory=EquipDetailItemsOverlay)
    HELP_X: int = 160
    HELP_Y: int = 6


# ── SaveMenuState ──────────────────────────────────────────────────

@dataclass(frozen=True)
class SaveMenuConfig:
    TITLE_X: int = 120
    TITLE_Y: int = 155
    SCREEN_L: int = 0
    SCREEN_R: int = 240
    SLOT_HEIGHTS: Tuple[int, int, int] = (53, 54, 53)
    TEXT_INDENT: int = 16
    HELP_X: int = 120
    HELP_Y: int = 4


# ── Top-level layout ───────────────────────────────────────────────

@dataclass(frozen=True)
class MenuLayoutConfig:
    fonts: FontSizes = field(default_factory=FontSizes)
    screen: ScreenConfig = field(default_factory=ScreenConfig)
    main: MainMenuConfig = field(default_factory=MainMenuConfig)
    items: ItemsMenuConfig = field(default_factory=ItemsMenuConfig)
    status: StatusMenuConfig = field(default_factory=StatusMenuConfig)
    equip_char: EquipCharSelectConfig = field(default_factory=EquipCharSelectConfig)
    equip_detail: EquipDetailConfig = field(default_factory=EquipDetailConfig)
    save: SaveMenuConfig = field(default_factory=SaveMenuConfig)


_LAYOUT = MenuLayoutConfig()


def get_menu_layout() -> MenuLayoutConfig:
    """Return singleton layout config (all values in base 240x160 pixels)."""
    return _LAYOUT
