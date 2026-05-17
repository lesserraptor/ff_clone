import os
import pyglet


def _get_assets_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


_font_registered = False


def _register_font():
    global _font_registered
    if _font_registered:
        return True
    
    font_path = os.path.join(_get_assets_path(), "onion-pixel.otf")
    
    if os.path.exists(font_path):
        pyglet.font.add_file(font_path)
        _font_registered = True
        return True
    
    return False


def load_font():
    _register_font()
    return "Onion Pixel"


def draw_text(text, x, y, color=(255, 255, 255), size=8, scale=1.0, anchor_x="left", anchor_y="top"):
    font_name = load_font()
    if font_name is None:
        return
    
    scaled_size = int(size * scale)
    import arcade
    arcade.draw_text(
        text,
        x, y,
        color,
        scaled_size,
        font_name=font_name,
        anchor_x=anchor_x,
        anchor_y=anchor_y
    )


def create_text(text, x, y, color=(255, 255, 255), size=8, anchor_x="left", anchor_y="center", width=None, multiline=False):
    font_name = load_font()
    import arcade
    return arcade.Text(
        text, x, y,
        color, size,
        font_name=font_name,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
        width=width,
        multiline=multiline
    )


def get_text_width(text, size=8, scale=1.0):
    return len(text) * size * 0.6 * scale


def get_text_height(size=8, scale=1.0):
    return size * scale


def wrap_text(text, max_width, font_size, scale=1.0):
    """Wrap text to fit within max_width pixels. Returns list of line strings."""
    char_w = font_size * 0.6 * scale
    max_chars = max(1, int(max_width / char_w))
    words = text.split(' ')
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if len(test) > max_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines if lines else [text]