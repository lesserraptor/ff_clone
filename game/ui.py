import arcade


COLORS = {
    "box_fill": (48, 48, 160),
    "box_border": (160, 160, 160),
    "text": (255, 255, 255),
    "cursor": (255, 255, 0),
    "enemy": (255, 48, 48),
    "player_hp": (48, 112, 208),
    "hp_fill": (0, 200, 0),
    "hp_empty": (80, 80, 80),
    "mp_fill": (48, 48, 255),
    "mp_empty": (80, 80, 80),
}


def draw_window(x, y, w, h, scale=1.0, fill_color=None, border_color=None):
    if fill_color is None:
        fill_color = COLORS["box_fill"]
    if border_color is None:
        border_color = COLORS["box_border"]
    
    arcade.draw_lrbt_rectangle_filled(x, x + w, y, y + h, fill_color)
    arcade.draw_lrbt_rectangle_outline(x, x + w, y, y + h, border_color, int(scale))


def draw_window_centered(cx, cy, w, h, scale=1.0, fill_color=None, border_color=None):
    if fill_color is None:
        fill_color = COLORS["box_fill"]
    if border_color is None:
        border_color = COLORS["box_border"]
    
    x = cx - w / 2
    y = cy - h / 2
    draw_window(x, y, w, h, scale, fill_color, border_color)


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