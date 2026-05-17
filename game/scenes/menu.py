import arcade
from pyglet.window import key
from game.engine import register_scene
from game.text import create_text
from game.ui import COLORS, draw_window


@register_scene("menu")
class MenuScene:
    """Thin coordinator for menu sub-states."""

    _state_classes = None

    @classmethod
    def _get_state_classes(cls):
        if cls._state_classes is None:
            from game.scenes.menu_states import (
                MainMenuState,
                ItemsMenuState,
                StatusMenuState,
                EquipCharSelectState,
                EquipDetailState,
                SaveMenuState,
            )
            cls._state_classes = {
                "main": MainMenuState,
                "items": ItemsMenuState,
                "status": StatusMenuState,
                "equip": EquipCharSelectState,
                "equip_detail": EquipDetailState,
                "save": SaveMenuState,
            }
        return cls._state_classes

    def __init__(self, engine):
        self.engine = engine
        self._prev_scale = 0
        self._text_cache = {}
        self.current_state = None
        self.set_state("main")

    # ── state management ─────────────────────────────────

    def set_state(self, name, **kwargs):
        """Transition to a named sub-state, passing optional kwargs."""
        classes = self._get_state_classes()
        cls = classes.get(name)
        if cls is None:
            raise ValueError(f"Unknown menu state: {name}")
        self.current_state = cls(self, **kwargs)
        self.invalidate_cache()

    def invalidate_cache(self):
        self._text_cache = {}

    # ── text helpers (used by states) ────────────────────

    def _get_text(self, key, text, x, y, color, size, anchor_x="left", anchor_y="center"):
        scale = self.engine.get_scale()
        if scale not in self._text_cache:
            self._text_cache[scale] = {}
        cache = self._text_cache[scale]
        if key not in cache:
            cache[key] = create_text(text, x, y, color, size, anchor_x=anchor_x, anchor_y=anchor_y)
        else:
            cache[key].text = text
            cache[key].color = color
            cache[key].x = x
            cache[key].y = y
        return cache[key]

    def draw_box(self, l, r, b, t, scale, fill=None, border=None):
        if fill is None:
            fill = COLORS["box_fill"]
        if border is None:
            border = COLORS["box_border"]
        draw_window(l, b, r - l, t - b, scale, fill, border)

    def draw_text(self, text, x, y, color, size, center=False, anchor_x="left"):
        if center:
            anchor_x = "center"
        t = self._get_text(f"{text[:8]}_{id(self)}", text, x, y, color, int(size), anchor_x=anchor_x, anchor_y="center")
        t.draw()

    # ── scene lifecycle ──────────────────────────────────

    def update(self, delta_time):
        if self.current_state:
            self.current_state.update(self.engine.input)

    def draw(self):
        w, h = self.engine.get_size()
        scale = self.engine.get_scale()

        arcade.draw_lrbt_rectangle_filled(0, w, 0, h, (0, 0, 50))

        if self.current_state:
            self.current_state.draw(w, h, scale)

        self._prev_scale = scale
