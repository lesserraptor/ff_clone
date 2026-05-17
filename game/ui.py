import arcade
import os
import json


COLORS = {
    "box_fill": (232, 232, 232),
    "box_border": (160, 160, 160),
    "text": (24, 24, 24),
    "cursor": (24, 24, 24),
    "enemy": (48, 48, 48),
    "player_hp": (48, 48, 48),
    "hp_fill": (48, 48, 48),
    "hp_empty": (160, 160, 160),
    "mp_fill": (80, 80, 80),
    "mp_empty": (160, 160, 160),
}


def _derive_border_colors(border_color):
    r, g, b = border_color[:3]
    w = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
    g_col = (min(255, r + 30), min(255, g + 30), min(255, b + 30))
    b_col = (max(0, r - 40), max(0, g - 40), max(0, b - 40))
    return w, g_col, b_col


_border_data = None


def _load_border_data():
    global _border_data
    if _border_data is not None:
        return _border_data
    
    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "ui_borders.json")
    try:
        with open(json_path, "r") as f:
            _border_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _border_data = {}
    return _border_data


def _get_border_patterns():
    data = _load_border_data()
    return {
        "top_left": data.get("top_left", []),
        "top_right": data.get("top_right", []),
        "bot_left": data.get("bot_left", []),
        "bot_right": data.get("bot_right", []),
        "top_border": data.get("top_border", []),
        "bot_border": data.get("bot_border", []),
        "left_edge": data.get("left_edge", ""),
        "right_edge": data.get("right_edge", ""),
    }


def draw_pixellated_border(x, y, w, h, scale, border_color):
    px = int(max(1, scale))
    
    w_col, g_col, b_col = _derive_border_colors(border_color)
    c = {"w": w_col, "g": g_col, "b": b_col}
    
    patterns = _get_border_patterns()
    border_px = 6 * px
    
    for row_idx, color in enumerate(patterns["top_border"]):
        for dy in range(px):
            for col_idx, ch in enumerate(patterns["top_left"][row_idx]):
                if ch != "t":
                    arcade.draw_lrbt_rectangle_filled(
                        x + col_idx * px, x + (col_idx + 1) * px,
                        y + row_idx * px, y + (row_idx + 1) * px,
                        c[ch]
                    )
            arcade.draw_lrbt_rectangle_filled(
                x + border_px, x + w - border_px,
                y + row_idx * px, y + (row_idx + 1) * px,
                c[color]
            )
            for col_idx, ch in enumerate(patterns["top_right"][row_idx]):
                if ch != "t":
                    arcade.draw_lrbt_rectangle_filled(
                        x + w - border_px + col_idx * px, x + w - border_px + (col_idx + 1) * px,
                        y + row_idx * px, y + (row_idx + 1) * px,
                        c[ch]
                    )
    
    for row_idx, color in enumerate(patterns["bot_border"]):
        for dy in range(px):
            for col_idx, ch in enumerate(patterns["bot_left"][row_idx]):
                if ch != "t":
                    arcade.draw_lrbt_rectangle_filled(
                        x + col_idx * px, x + (col_idx + 1) * px,
                        y + h - border_px + row_idx * px, y + h - border_px + (row_idx + 1) * px,
                        c[ch]
                    )
            arcade.draw_lrbt_rectangle_filled(
                x + border_px, x + w - border_px,
                y + h - border_px + row_idx * px, y + h - border_px + (row_idx + 1) * px,
                c[color]
            )
            for col_idx, ch in enumerate(patterns["bot_right"][row_idx]):
                if ch != "t":
                    arcade.draw_lrbt_rectangle_filled(
                        x + w - border_px + col_idx * px, x + w - border_px + (col_idx + 1) * px,
                        y + h - border_px + row_idx * px, y + h - border_px + (row_idx + 1) * px,
                        c[ch]
                    )
    
    middle_start_y = y + border_px
    middle_end_y = y + h - border_px
    
    for py in range(middle_start_y, middle_end_y):
        for i, color in enumerate(patterns["left_edge"]):
            if color != "t":
                arcade.draw_lrbt_rectangle_filled(
                    x + i * px, x + (i + 1) * px,
                    py, py + 1,
                    c[color]
                )
        for i, color in enumerate(patterns["right_edge"]):
            if color != "t":
                arcade.draw_lrbt_rectangle_filled(
                    x + w - border_px + i * px, x + w - border_px + (i + 1) * px,
                    py, py + 1,
                    c[color]
                )



def draw_window(x, y, w, h, scale=1.0, fill_color=None, border_color=None):
    if fill_color is None:
        fill_color = COLORS["box_fill"]
    if border_color is None:
        border_color = COLORS["box_border"]
    
    border_w = 6 * int(max(1, scale))
    fill_x = x + border_w
    fill_y = y + border_w
    fill_w = w - border_w * 2
    fill_h = h - border_w * 2
    if fill_w > 0 and fill_h > 0:
        arcade.draw_lrbt_rectangle_filled(fill_x, fill_x + fill_w, fill_y, fill_y + fill_h, fill_color)
    draw_pixellated_border(x, y, w, h, scale, border_color)


def draw_window_centered(cx, cy, w, h, scale=1.0, fill_color=None, border_color=None):
    if fill_color is None:
        fill_color = COLORS["box_fill"]
    if border_color is None:
        border_color = COLORS["box_border"]
    
    x = cx - w / 2
    y = cy - h / 2
    border_w = 6 * int(max(1, scale))
    fill_x = x + border_w
    fill_y = y + border_w
    fill_w = w - border_w * 2
    fill_h = h - border_w * 2
    if fill_w > 0 and fill_h > 0:
        arcade.draw_lrbt_rectangle_filled(fill_x, fill_x + fill_w, fill_y, fill_y + fill_h, fill_color)
    draw_pixellated_border(x, y, w, h, scale, border_color)


def draw_cursor(x, y, scale=1.0, color=None):
    if color is None:
        color = COLORS["cursor"]
    
    size = 8 * scale
    p1 = (x, y + size / 2)
    p2 = (x + size, y)
    p3 = (x, y + size)
    
    arcade.draw_triangle_filled(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], color)


def draw_hp_bar(current, max_val, x, y, scale=1.0, width=None, height=None):
    if width is None:
        width = 40 * scale
    if height is None:
        height = 4 * scale
    
    arcade.draw_lrbt_rectangle_filled(x, x + width, y, y + height, COLORS["hp_empty"])
    
    if max_val > 0:
        fill_width = width * (current / max_val)
        if fill_width > 0:
            arcade.draw_lrbt_rectangle_filled(x, x + fill_width, y, y + height, COLORS["hp_fill"])
    
    arcade.draw_lrbt_rectangle_outline(x, x + width, y, y + height, COLORS["box_border"], int(scale))


def draw_mp_bar(current, max_val, x, y, scale=1.0, width=None, height=None):
    if width is None:
        width = 40 * scale
    if height is None:
        height = 4 * scale
    
    arcade.draw_lrbt_rectangle_filled(x, x + width, y, y + height, COLORS["mp_empty"])
    
    if max_val > 0:
        fill_width = width * (current / max_val)
        if fill_width > 0:
            arcade.draw_lrbt_rectangle_filled(x, x + fill_width, y, y + height, COLORS["mp_fill"])
    
    arcade.draw_lrbt_rectangle_outline(x, x + width, y, y + height, COLORS["box_border"], int(scale))


def draw_bordered_box(x, y, w, h, scale=1.0, fill_color=None, border_color=None):
    if fill_color is None:
        fill_color = (0, 0, 0)
    if border_color is None:
        border_color = COLORS["box_border"]
    
    arcade.draw_lrbt_rectangle_filled(x, x + w, y, y + h, fill_color)
    arcade.draw_lrbt_rectangle_outline(x, x + w, y, y + h, border_color, int(scale))